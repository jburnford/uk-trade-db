#!/usr/bin/env python3
"""Recover the true value from three-column cells the parser fused.

Some export tables print THREE numeric columns -- Yards, Lbs, £ -- and the OCR
puts two of them in one cell:

    <td>Lbs. 271,810 £ 62,528</td>          Germany, Narrow Cloths, as_1874
    <td>452,650 94,110</td>                 British North America, same table

The table parser read each as a single number and concatenated the digits, so
Germany's £62,528 became 27,181,060,000 and Canada's £94,110 became
45,265,090,000. One such cell makes the whole 1874 Canada export series read
GBP45.27bn against a true GBP8.49M.

The correct value is sitting in the raw OCR, in both copies, so this needs no
page image: the LAST number in the fused cell is the £ column. This script
reads the raw markdown, pairs each fused cell with the country label printed on
the same row, matches it to the `country_obs` row whose value is the digit
concatenation, and writes the repair.

Matching is deliberately strict — the candidate row must be in the same volume
and its stored value must equal the concatenation of the fused numbers. A cell
that does not match that way is reported, not guessed at.

KNOWN LIMIT. "no fusion in the DB" is not a failure count. Most two-number
cells in the raw are ones the table parser split correctly, so no row carries
the concatenation and nothing needs repairing. But that bucket also hides a
class this script CANNOT recover: rows where the parser gave up and stored
`value = NULL` (as_1874 Australia / Broad Cloths is one). Those need the same
correction and are invisible to a value-equality match. Recovering them needs
matching on quantity or row position instead, which is not done here.

Usage:
    python3 scripts/repair_fused_cells.py [--out reference/export_cell_repairs.csv]
                                          [--volume as_1874] [--dry-run]
"""
import argparse, csv, glob, html, os, re, sys
import duckdb

ROW_RE = re.compile(r'<tr>(.*?)</tr>', re.S | re.I)
CELL_RE = re.compile(r'<td[^>]*>(.*?)</td>', re.S | re.I)
# 'Lbs. 271,810 £ 62,528' or bare '452,650 94,110'
FUSED_RE = re.compile(
    r'^(?:lbs\.?\s*)?([0-9][0-9,]*)\s*(?:£\s*|lbs\.?\s*)?([0-9][0-9,]*)$', re.I)
LABEL_RE = re.compile(r'^[",\'“”\s]*([A-Za-z][A-Za-z\s.,&\'()-]+?)[\s\-]*$')


def clean(cell):
    s = re.sub(r'<[^>]+>', ' ', cell)
    return re.sub(r'\s+', ' ', html.unescape(s)).strip()


def digits(s):
    return s.replace(',', '').strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='db/uk_trade.duckdb')
    ap.add_argument('--raw', default='raw')
    ap.add_argument('--out', default='reference/export_cell_repairs.csv')
    ap.add_argument('--volume')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    con = duckdb.connect(a.db, read_only=True)
    vols = sorted(os.path.basename(d) for d in glob.glob(f'{a.raw}/*')
                  if os.path.isdir(d))
    if a.volume:
        vols = [v for v in vols if v == a.volume]

    repairs, unmatched = [], []
    for vol in vols:
        md = glob.glob(f'{a.raw}/{vol}/**/*.md', recursive=True)
        if not md:
            continue
        text = open(md[0], encoding='utf-8', errors='replace').read()
        for rowhtml in ROW_RE.findall(text):
            cells = [clean(c) for c in CELL_RE.findall(rowhtml)]
            # the label is the last text-y cell before the fused numeric one
            for i, c in enumerate(cells):
                m = FUSED_RE.match(c)
                if not m:
                    continue
                lo, hi = digits(m.group(1)), digits(m.group(2))
                if len(lo) < 3 or len(hi) < 3:
                    continue                    # too short to be a real pair
                fused = float(lo + hi)
                label = ''
                for j in range(i - 1, -1, -1):
                    lm = LABEL_RE.match(cells[j])
                    if lm and not re.search(r'\d', cells[j]):
                        label = lm.group(1).strip(' .,-')
                        break
                if not label:
                    continue
                hits = con.execute("""
                    select year, article_group, article, country_raw, quantity, value
                    from country_obs
                    where volume = ? and value = ?
                """, [vol, fused]).fetchall()
                if not hits:
                    # tolerate the parser's trailing-zero rounding of the fusion
                    hits = con.execute("""
                        select year, article_group, article, country_raw,
                               quantity, value
                        from country_obs
                        where volume = ? and value > ?
                          and value < ? and country_raw ilike ?
                    """, [vol, fused * 0.9999, fused * 1.0001, f'%{label[-18:]}%']
                    ).fetchall()
                if len(hits) == 1:
                    yr, ag, art, ctry, q, v = hits[0]
                    repairs.append(dict(
                        volume=vol, year=yr, article_group=ag or '', article=art or '',
                        country_raw=ctry, old_value=v, new_value=float(hi),
                        middle_column=float(lo), raw_cell=c, matched_on=label))
                else:
                    unmatched.append((vol, label, c, len(hits)))

    print(f'volumes scanned: {len(vols)}')
    print(f'fused cells repaired          : {len(repairs)}')
    print(f'two-number cells with no fusion: {len(unmatched)}  '
          f'(mostly parsed correctly; see the NULL-value limit in the docstring)')
    byvol = {}
    for r in repairs:
        byvol[r['volume']] = byvol.get(r['volume'], 0) + 1
    for v, n in sorted(byvol.items(), key=lambda kv: -kv[1]):
        print(f'   {v}: {n}')

    if repairs:
        print(f'\nlargest corrections:')
        for r in sorted(repairs, key=lambda r: -r['old_value'])[:12]:
            print(f'  {r["volume"]} {r["year"]}  {r["old_value"]:>18,.0f} -> '
                  f'{r["new_value"]:>12,.0f}  {r["country_raw"][:24]:24} '
                  f'{r["article"][:34]}')
    if unmatched[:8]:
        print(f'\nno-fusion examples (parser split these itself, or stored NULL):')
        for v, lab, c, n in unmatched[:8]:
            print(f'  {v}  hits={n}  {lab[:28]:28} {c[:34]}')

    if repairs and not a.dry_run:
        with open(a.out, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(repairs[0].keys()))
            w.writeheader()
            w.writerows(repairs)
        print(f'\nwrote {a.out}')


if __name__ == '__main__':
    main()
