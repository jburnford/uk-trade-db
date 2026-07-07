#!/usr/bin/env python3
"""Parse the numbered abstract tables (article x 5-year) from Chandra OCR
markdown of the UK Annual Statements of Trade into DuckDB.

Tier 1 of the UK trade database: national totals per article per year,
imports / UK-produce exports / re-exports, quantities and values.
Five-year comparative columns mean each statistical year is usually observed
in up to five volumes — kept as separate observations for cross-volume
validation (reconciliation happens in a later stage).

Usage: python3 parse_abstract.py [raw_dir ...]
Writes db/uk_trade.duckdb (table: abstract_obs) and a parse report.
"""
import re
import sys
from pathlib import Path

import duckdb

BASE = Path('/home/jic823/uk_trade_db')

CAPTIONS = [
    # (regex on caption text, flow, measure) — wording drifts across eras:
    # 1870s: "PRINCIPAL ARTICLES IMPORTED"; 1890s: "PRINCIPAL ARTICLES of
    # FOREIGN and COLONIAL MERCHANDISE IMPORTED"; exports gain "and
    # MANUFACTURES" late.
    (r'TOTAL QUANTITIES of (?:the )?(?:PRINCIPAL )?ARTICLES(?: of FOREIGN and COLONIAL MERCHANDISE)? IMPORTED',
     'import', 'quantity'),
    (r'TOTAL VALUE of (?:the )?(?:PRINCIPAL and OTHER )?ARTICLES(?:,? of FOREIGN and COLONIAL MERCHANDISE)? IMPORTED',
     'import', 'value'),
    (r'TOTAL QUANTITIES of (?:the )?(?:PRINCIPAL )?ARTICLES,?.{0,10}the PRODUCE(?: and MANUFACTURES)? of the UNITED KINGDOM,?.{0,10}EXPORTED',
     'export_uk', 'quantity'),
    (r'TOTAL VALUE of (?:the )?(?:PRINCIPAL and OTHER )?ARTICLES,?.{0,10}the PRODUCE(?: and MANUFACTURES)? of the UNITED KINGDOM,?.{0,10}EXPORTED',
     'export_uk', 'value'),
    (r'TOTAL QUANTITIES of (?:the )?(?:PRINCIPAL )?ARTICLES of FOREIGN and COLONIAL (?:MERCHANDISE|PRODUCE).{0,20}EXPORTED',
     'reexport', 'quantity'),
    (r'TOTAL VALUE of (?:the )?(?:PRINCIPAL and OTHER )?ARTICLES of FOREIGN and COLONIAL (?:MERCHANDISE|PRODUCE).{0,20}EXPORTED',
     'reexport', 'value'),
]

TABLE_RE = re.compile(r'<table[^>]*>(.*?)</table>', re.S)
ROW_RE = re.compile(r'<tr[^>]*>(.*?)</tr>', re.S)
CELL_RE = re.compile(r'<t[hd][^>]*>(.*?)</t[hd]>', re.S)
TAG_RE = re.compile(r'<[^>]+>')
YEAR_RE = re.compile(r'\b(18[3-9]\d|19[0-4]\d)\b')
# label like "Bacon and Hams - - - - - Cwts."  (dash leaders before unit)
LEADER_RE = re.compile(r'\s*[-‐-―](?:\s*[-‐-―])+\s*')
FOOTNOTE_RE = re.compile(r'[*†‡§¶‖]|<sup>.*?</sup>')

NIL = {'', '-', '—', '–', '...', '..', '. .', '&nbsp;', 'Nil', 'nil'}

# unit words as printed in quantity-table labels (measure sanity check)
UNIT_WORD_RE = re.compile(
    r'(C[wviu]ts?|Tons?|Lbs|Number|No|Gall?on?s|Galls|Qrs|Quarters|Loads?'
    r'|Yards|Yds|Bushels|Barrels|Doz(en)?|Pairs|Value\s*£|Gross|Feet|Pieces'
    r'|Packs|Mille|Tale|Tonnage|Cases|Boxes|Bundles|Hhds)\.?\s*$', re.I)


def clean(s):
    s = FOOTNOTE_RE.sub('', s)
    s = TAG_RE.sub('', s)
    return (s.replace('&amp;', '&').replace('&nbsp;', ' ')
             .replace('\xa0', ' ').strip())


def parse_num(s):
    s = clean(s).replace('£', '').strip()
    if s in NIL:
        return None, s
    t = s.replace(',', '').replace(' ', '')
    if re.fullmatch(r'\d+(\.\d+)?', t):
        v = float(t)
        if v > 1e11:            # two OCR-merged numbers glued together
            return None, s
        return v, s
    return None, s          # unparseable -> keep raw for review


def split_label(cell):
    """'  Oxen, Bulls - - - - - Number' -> (indent, name, unit_or_None)."""
    raw = cell.replace('&nbsp;', ' ').replace('\xa0', ' ')
    raw = TAG_RE.sub('', raw)
    indent = len(raw) - len(raw.lstrip(' '))
    txt = FOOTNOTE_RE.sub('', raw).strip()
    parts = LEADER_RE.split(txt)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) >= 2 and len(parts[-1]) <= 30:
        return indent, ' '.join(parts[:-1]), parts[-1]
    return indent, txt, None


def classify_caption(text):
    # late volumes emphasize caption words ("TOTAL **Quantities** of ...");
    # strip markdown emphasis or the regexes miss and the sticky flow/measure
    # from the previous plain caption mislabels whole pages
    text = text.replace('*', '')
    for rx, flow, measure in CAPTIONS:
        # captions wrap across source lines: let spaces match any whitespace
        if re.search(rx.replace(' ', r'\s+'), text, re.S | re.I):
            return flow, measure
    return None, None


def parse_volume(md_path, con, volume_id, table='abstract_obs'):
    md = md_path.read_text(encoding='utf-8', errors='replace')
    # segment: text before each table = caption zone of that table
    pieces = re.split(r'(<table[^>]*>.*?</table>)', md, flags=re.S)
    n_obs = n_tables = 0
    cur = None                       # (flow, measure) sticky across -Continued
    for i, piece in enumerate(pieces):
        if not piece.startswith('<table'):
            # caption zone: only look at trailing 500 chars before a table
            zone = piece[-500:]
            flow, measure = classify_caption(zone)
            if flow:
                cur = (flow, measure)
            elif not re.search(r'Continued', zone, re.I) and re.search(
                    r'(No\.\s*\d+|ACCOUNT|ARTICLES? (FREE|SUBJECT)|GENERAL '
                    r'(IMPORTS|EXPORTS)|COIN and BULLION|TRANSHIPPED|## '
                    r'|PRINCIPAL PORTS|[Aa]t [Ee]ach [Pp]ort|CUSTOMS DUTIES'
                    r'|Parcel Post|PARCEL POST)',
                    zone.replace('*', '')):
                cur = None           # a different table family starts
            continue
        if cur is None:
            continue
        flow, measure = cur
        rows = ROW_RE.findall(piece)
        if not rows:
            continue
        # find year columns from first header-ish row containing >=3 years
        years = []
        for r in rows[:4]:
            cells = [clean(c) for c in CELL_RE.findall(r)]
            ys = [int(YEAR_RE.search(c).group(1)) for c in cells
                  if YEAR_RE.search(c)]
            if len(ys) >= 3:
                years = ys
                break
        if not years:
            continue
        n_tables += 1
        # measure sanity check: facing-page layouts alternate Quantities |
        # Value pages, and one missed caption leaves the sticky measure
        # wrong for a whole page. Quantity pages carry unit words (or ditto
        # marks) in their labels/unit column; value pages carry none. Must
        # collapse dash-leader cells first — some OCR emits each leader dash
        # as its own cell, hiding the unit from a naive scan.
        n_lab = n_unit = 0
        for r in rows:
            cells = CELL_RE.findall(r)
            if not cells:
                continue
            merged, seen_num = [cells[0]], False
            for c in cells[1:]:
                cc = clean(c)
                if (not seen_num and cc
                        and re.fullmatch(r'[-‐-―\s.]+', cc)):
                    continue
                if re.search(r'\d', cc):
                    seen_num = True
                merged.append(c)
            _, name, u_in = split_label(merged[0])
            if not name or YEAR_RE.search(name):
                continue
            n_lab += 1
            if len(merged) == len(years) + 2 and not u_in:
                u_in = re.sub(r'[-‐-―.\s]+', ' ', clean(merged[1])).strip()
            if u_in and (UNIT_WORD_RE.search(u_in)
                         or u_in in ('"', '„', '”', "''")):
                n_unit += 1
        if n_lab >= 10:
            frac = n_unit / n_lab
            if measure == 'value' and frac >= 0.2:
                measure = 'quantity'
            elif measure == 'quantity' and frac < 0.02:
                measure = 'value'
        group = None
        unit = None
        for ri, r in enumerate(rows):
            cells = CELL_RE.findall(r)
            if not cells:
                continue
            # collapse dash-leader cells that some OCR engines emit as
            # separate columns ('- - - Loads' -> many cells); only before
            # the first numeric cell so nil value-cells are untouched
            merged, seen_num = [cells[0]], False
            for c in cells[1:]:
                cc = clean(c)
                if (not seen_num and cc
                        and re.fullmatch(r'[-\u2010-\u2015\s.]+', cc)):
                    continue
                if re.search(r'\d', cc):
                    seen_num = True
                merged.append(c)
            cells = merged
            indent, name, u_inline = split_label(cells[0])
            if not name or YEAR_RE.search(name):
                continue
            rest = cells[1:]
            # group header: label ends with ':' and no numeric values
            if name.endswith(':') and all(clean(v) in NIL for v in rest):
                group = name.rstrip(':').strip()
                unit = None
                continue
            if len(rest) < len(years):
                continue
            unit_src = u_inline
            if len(rest) == len(years) + 1:
                # layout B: dash-leader/unit lives in its own cell
                uc = re.sub(r'[-‐-―.\s]+', ' ', clean(rest[0])).strip()
                if uc and not unit_src:
                    unit_src = uc
                vals = rest[1:]
            elif len(rest) == len(years):
                vals = rest
            else:
                continue        # unexpected layout; leave for review pass
            if unit_src and unit_src != '"':
                unit = unit_src
            # group membership is purely indentation-based: sub-articles are
            # indented under their "Foo :" header; any flush-left data row
            # ends the group
            if indent == 0:
                group = None
            top = group if indent > 0 else None
            article = name.rstrip(':').strip()
            for y, v in zip(years, vals):
                num, raw = parse_num(v)
                if num is None and clean(v) in NIL:
                    continue
                con.execute(
                    f'INSERT INTO {table} VALUES (?,?,?,?,?,?,?,?,?,?)',
                    [volume_id, flow, measure, top, article,
                     unit if measure == 'quantity' else 'GBP',
                     y, num, raw if num is None else None, ri])
                n_obs += 1
    return n_tables, n_obs


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'))
    con.execute('DROP TABLE IF EXISTS abstract_obs')
    con.execute('''CREATE TABLE abstract_obs (
        volume VARCHAR, flow VARCHAR, measure VARCHAR,
        article_group VARCHAR, article VARCHAR, unit VARCHAR,
        year INTEGER, value DOUBLE, raw_unparsed VARCHAR, row_seq INTEGER)''')
    raws = sys.argv[1:] or sorted(str(p) for p in (BASE / 'raw').iterdir())
    for rd in raws:
        rd = Path(rd)
        mds = list(rd.rglob('*.md'))
        if not mds:
            continue
        vol = rd.name
        nt, no = parse_volume(mds[0], con, vol)
        print(f'{vol}: {nt} abstract tables, {no:,} observations')
    con.commit()
    print('\n== summary ==')
    for row in con.execute('''SELECT volume, flow, measure, count(*),
            count(DISTINCT article), min(year), max(year)
            FROM abstract_obs GROUP BY 1,2,3 ORDER BY 1,2,3''').fetchall():
        print(' ', row)
    print('\nunparseable cells:',
          con.execute('SELECT count(*) FROM abstract_obs '
                      'WHERE value IS NULL').fetchone()[0])


if __name__ == '__main__':
    main()
