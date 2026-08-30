#!/usr/bin/env python3
"""Pair the two halves of tables printed across facing pages and scanned as single pages.

From FY1897 the wide statements were printed across a spread. Each page was scanned on its
own, so Chandra emits two tables: a LEFT page carrying the row labels and the first value
columns, and a RIGHT page carrying the remaining value columns and no labels at all.

Classification is by HEADER SIGNATURE, not by how numeric the body looks: a right-hand page
has column headers but no label column (no ARTICLES / COUNTRIES / PROVINCE / PORT ...).
A table with no header rows is a continuation and inherits the previous table's side.

Emits reports/spread_pairs_<fy>.tsv and a summary to stdout.

Usage:
    python3 scripts/ca_pair_spreads.py --fy 1900 [--fy 1898 ...]
    python3 scripts/ca_pair_spreads.py --md <path> --tag <name>
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ca_profile as P

ROOT = Path(__file__).resolve().parents[1]
STATCAN = ROOT.parent / 'sessional_papers' / 'statcan_trade' / 'ocr'
MANIFEST = STATCAN / 'MANIFEST.tsv'
OUT_DIR = ROOT / 'reports'

TABLE_RE = re.compile(r'<table\b.*?</table>', re.S)

# A label column names the row: which article, country, province, port, year.
LABEL_COL = re.compile(r'ARTICLE|COUNTR|PROVINCE|PORT|NATIONALITY|NAME|DESCRIPTION|'
                       r'FISCAL YEAR|YEARS?\.|MONTH|OUTPORT|WHENCE|TO WHICH|NUMBER\.', re.I)

# Statement families we can pair. Each entry: (key, left signature, right signature).
FAMILIES = [
    # No. 37 General Statement of Imports: article x country x province.
    ('imports_37',
     re.compile(r'ARTICLES?\s+IMPORTED.*COUNTRIES.*TOTAL\s+IMPORTS', re.I | re.S),
     None),
    # No. 17 Summary Statement: article-level, ordinal Number column, no country.
    ('summary_17',
     re.compile(r'NUMBER\..*ARTICLES\..*(RATES\s+OF\s+DUTY|TOTAL\s+IMPORTS)', re.I | re.S),
     None),
]

# Both families share one right-page signature, but the tariff columns are renamed twice
# across the run, following the tariff law rather than the printer:
#   FY1898        General Tariff + Reciprocal Tariff
#   FY1899-1903   General Tariff + Preferential Tariff   ('Prefential' in a few OCR'd heads)
#   FY1904-1908   Preferential Tariff + Surtax Tariff    (General moves to the left page)
# So the signature is "two tariff columns of any of these names", not a fixed pair.
TARIFF = r'(?:GENERAL|PREFERENTIAL|PREFENTIAL|PREFERENTAIL|RECIPROCAL|SURTAX)\s+TARIFF'
RIGHT_SIG = re.compile(TARIFF + r'.*' + TARIFF, re.I | re.S)


def header_signature(table_html):
    """(flat header text, has_label_column, n_header_rows)."""
    rows = P.parse_table(table_html)
    ths = [r for r in rows if r and all(k == 'th' for k, _, _ in r)]
    flat = ' | '.join(c for r in ths for _, _, c in r if c.strip())
    return flat, bool(LABEL_COL.search(flat)), len(ths)


def running_head(text, start, end):
    """The intertext before a table — carries 'No. N.—TITLE' when the running head OCR'd."""
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', text[max(0, start - 400):end])).strip()


def statement_no(inter):
    m = re.findall(r'No\.\s*(\d+)\s*\.?\s*—', inter)
    return m[-1] if m else ''


def classify(flat, has_label):
    """Return (side, family) for a table: side in {'L','R',''}.

    A right-hand page has no family of its own -- the two families share a right-page
    layout -- so it takes the family of the left page it gets paired with."""
    if has_label:
        for key, lsig, _rsig in FAMILIES:
            if lsig.search(flat):
                return 'L', key
    elif RIGHT_SIG.search(flat):
        return 'R', ''
    return '', ''


def pair_volume(tag, fy, md_path):
    text = Path(md_path).read_text(errors='ignore')
    tables = [(m.start(), m.end(), m.group(0)) for m in TABLE_RE.finditer(text)]

    marks = []          # (idx, start, end, side, family, nrows, stmt_no, inherited)
    prev_side = prev_fam = ''
    for i, (s, e, tbl) in enumerate(tables):
        flat, has_label, n_head = header_signature(tbl)
        side, fam = classify(flat, has_label)
        inherited = 0
        if n_head == 0 and prev_side:
            side, fam, inherited = prev_side, prev_fam, 1      # header-less continuation
        body = [r for r in P.parse_table(tbl) if r and not all(k == 'th' for k, _, _ in r)]
        inter = running_head(text, s, s)
        marks.append(dict(idx=i, start=s, end=e, side=side, family=fam, nrows=len(body),
                          stmt=statement_no(inter), inherited=inherited))
        if side:
            prev_side, prev_fam = side, fam

    # pair each L with the next R of the same family, with nothing pairable in between
    pairs, diag = [], Counter()
    i = 0
    while i < len(marks):
        m = marks[i]
        if m['side'] != 'L':
            i += 1
            continue
        j = i + 1
        while j < len(marks) and marks[j]['side'] != 'R':
            if marks[j]['side'] == 'L':
                break
            j += 1
        if j < len(marks) and marks[j]['side'] == 'R':
            if j != i + 1:
                diag['gap_between_halves'] += 1
            marks[j]['family'] = m['family']
            pairs.append((m, marks[j]))
            diag[f"paired_{m['family']}"] += 1
            i = j + 1
        else:
            diag[f"unpaired_left_{m['family']}"] += 1
            i += 1
    diag['unpaired_right'] = sum(1 for m in marks if m['side'] == 'R') - len(pairs)

    OUT_DIR.mkdir(exist_ok=True)
    out = OUT_DIR / f'spread_pairs_{tag}.tsv'
    with out.open('w', newline='') as fh:
        w = csv.writer(fh, delimiter='\t')
        # md_path travels with the offsets on purpose. The offsets are byte positions into
        # one specific document; resolving the document separately downstream (by tag, or by
        # fiscal year) lets the two drift apart and indexes one book's offsets into another.
        # That bug produced a full set of plausible, wrong Canadiana results before it was
        # caught. Consumers read md_path from here rather than resolving it themselves.
        w.writerow(['pair_id', 'fiscal_year', 'volume', 'md_path', 'family', 'stmt_no',
                    'l_idx', 'l_offset', 'l_rows', 'l_inherited',
                    'r_idx', 'r_offset', 'r_rows', 'r_inherited', 'row_delta'])
        for n, (l, r) in enumerate(pairs):
            w.writerow([n, fy, tag, str(md_path), l['family'], l['stmt'] or r['stmt'],
                        l['idx'], l['start'], l['nrows'], l['inherited'],
                        r['idx'], r['start'], r['nrows'], r['inherited'],
                        r['nrows'] - l['nrows']])
    return pairs, diag, out


def resolve(fy):
    """Manifest md_path for a fiscal year (preferred source)."""
    for row in csv.DictReader(MANIFEST.open(), delimiter='\t'):
        if row['fiscal_year'] == str(fy):
            return STATCAN / row['md_path'], row['preferred_source']
    raise SystemExit(f'fiscal year {fy} not in {MANIFEST}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--fy', action='append', default=[], help='fiscal year (resolved via MANIFEST.tsv)')
    ap.add_argument('--md', help='explicit markdown path')
    ap.add_argument('--tag', help='name for --md output')
    a = ap.parse_args()

    jobs = []
    for fy in a.fy:
        md, src = resolve(fy)
        jobs.append((f'{src}_{fy}', fy, md))
    if a.md:
        jobs.append((a.tag or Path(a.md).stem, '', Path(a.md)))

    for tag, fy, md in jobs:
        pairs, diag, out = pair_volume(tag, fy, md)
        deltas = Counter(r['nrows'] - l['nrows'] for l, r in pairs)
        print(f'\n=== {tag}  ({md.name})')
        print(f'  pairs: {len(pairs)}   -> {out.relative_to(ROOT)}')
        for k, v in sorted(diag.items()):
            print(f'    {k}: {v}')
        equal = deltas.get(0, 0)
        print(f'    row-count equal: {equal}/{len(pairs)} '
              f'({equal / max(len(pairs), 1) * 100:.0f}%); |delta|<=2: '
              f'{sum(v for d, v in deltas.items() if abs(d) <= 2)}')


if __name__ == '__main__':
    main()
