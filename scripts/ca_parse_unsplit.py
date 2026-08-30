#!/usr/bin/env python3
"""Read the FY1891-1897 General Statement of Imports, which was printed on a single page.

Three layouts run consecutively, and only the middle one is handled here:

  FY1868-1890  'ARTICLES AND COUNTRIES WHENCE IMPORTED | PROVINCES INTO WHICH IMPORTED'
               regime C -- ca_parse_imports.py already does this. FY1890 has the identical
               header to FY1889, so it needs registering, not new code.
  FY1891-1897  'ARTICLES IMPORTED | COUNTRIES AND PROVINCES | IMPORTED | ENTERED FOR HOME
               CONSUMPTION'  -- seven columns on one page. THIS SCRIPT.
  FY1898-1908  the same statement, now too wide for the page after the preferential tariff
               added columns, printed across a spread -- ca_pair_spreads + ca_align_spreads.

**Why this is not left to ca_parse_imports.py.** `regime_of()` classifies the FY1891-1897
header as regime **B**, because it contains ARTICLES, COUNTRIES and DUTY. Regime B is the
1877 'by Provinces' layout, which has different columns and a deliberate one-row label slip.
Running it over these volumes would produce a full set of confident, wrong rows -- the same
failure mode that a mismatched document path produced earlier in this project. The layouts
are distinguished here by their full header signature rather than by keyword presence.

Output matches ca_align_spreads.py's schema so the two can be concatenated, with
`align_status='whole'`: these rows were never split, so no join can be wrong. That says
nothing about OCR damage to the digits themselves, which still needs a second witness or a
printed-total check.

Usage:
    python3 scripts/ca_parse_unsplit.py --fy 1893 --md ../sessional_papers/markdown/oocihm.9_08052_27_5.md
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ca_align_spreads as AL
import ca_pair_spreads as PS

ROOT = Path(__file__).resolve().parents[1]
DB_DIR = ROOT / 'db' / 'canada'
OUT_DIR = ROOT / 'reports'

# The full signature, not a keyword test -- see the module docstring.
UNSPLIT = re.compile(r'ARTICLES?\s+IMPORTED.*COUNTRIES\s+AND\s+PROVINCES.*IMPORTED.*'
                     r'ENTERED\s+FOR\s+HOME\s+CONSUMPTION', re.I | re.S)
# The split years share the first half of that signature, so they must be excluded explicitly:
# their left page says 'TOTAL IMPORTS' and carries no 'ENTERED FOR HOME CONSUMPTION' columns.
SPLIT_LEFT = re.compile(r'TOTAL\s+IMPORTS', re.I)

NCOL = 7        # article | country/province | imp qty | imp value | efc qty | efc value | duty
FIELDS = ['fiscal_year', 'volume', 'table_seq', 'row_seq', 'era', 'labels', 'align_status', 'key',
          'tot_imp_qty', 'tot_imp_value', 'gt_qty', 'gt_value', 'gt_duty',
          'pt_qty', 'pt_value', 'pt_duty', 'sx_qty', 'sx_value', 'sx_duty',
          'efc_qty', 'efc_value', 'efc_duty', 'closes']


def parse_volume(tag, fy, md_path):
    text = Path(md_path).read_text(errors='ignore')
    diag = Counter()
    out_rows = []
    carry = False                      # header-less continuation of an unsplit import table

    for seq, m in enumerate(AL.TABLE_RE.finditer(text)):
        html = m.group(0)
        flat, _has, nh = PS.header_signature(html)
        if nh:
            carry = bool(UNSPLIT.search(flat)) and not SPLIT_LEFT.search(flat)
            if carry:
                diag['tables_with_header'] += 1
        elif carry:
            diag['tables_continuation'] += 1
        if not carry:
            continue

        for ri, cells in enumerate(AL.expand_rowspans(html, NCOL)):
            if not any(AL.HAS_DIGIT.search(c) for c in cells[2:]):
                diag['skip_heading_row'] += 1
                continue
            cells = AL.fold_cents(cells, NCOL)
            if len(cells) < NCOL:
                cells = cells + [''] * (NCOL - len(cells))
                diag['row_short_padded'] += 1
            elif len(cells) > NCOL:
                diag['row_long_truncated'] += 1
            labels, vals = cells[:2], cells[2:NCOL]
            n = [AL.num(v) for v in vals]
            if all(x is None for x in n):
                diag['skip_no_numbers'] += 1
                continue
            diag['rows'] += 1
            out_rows.append(dict(
                fiscal_year=fy, volume=tag, table_seq=seq, row_seq=ri, era='UNSPLIT',
                labels=' > '.join(x for x in labels if x.strip()),
                align_status='whole', key='unsplit',
                tot_imp_qty=n[0], tot_imp_value=n[1],
                gt_qty=None, gt_value=None, gt_duty=None,
                pt_qty=None, pt_value=None, pt_duty=None,
                sx_qty=None, sx_value=None, sx_duty=None,
                efc_qty=n[2], efc_value=n[3], efc_duty=n[4], closes=''))

    DB_DIR.mkdir(parents=True, exist_ok=True)
    out = DB_DIR / f'unsplit_rows_{tag}.csv'
    with out.open('w', newline='') as fh:
        w = csv.DictWriter(fh, FIELDS)
        w.writeheader()
        w.writerows(out_rows)
    return out_rows, diag, out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--fy', required=True)
    ap.add_argument('--md', required=True)
    ap.add_argument('--tag')
    a = ap.parse_args()
    tag = a.tag or Path(a.md).stem
    rows, diag, out = parse_volume(tag, a.fy, a.md)
    print(f'=== FY{a.fy}  {tag}')
    print(f'  tables: {diag["tables_with_header"]} headed + {diag["tables_continuation"]} continuations')
    print(f'  rows:   {diag["rows"]}  -> {out.relative_to(ROOT)}')
    for k in sorted(diag):
        if k.startswith(('row_', 'skip_')):
            print(f'    {k}: {diag[k]}')
    filled = sum(1 for r in rows if r['efc_value'] is not None)
    print(f'  efc_value populated: {filled}/{len(rows)} ({filled / max(len(rows), 1) * 100:.1f}%)')


if __name__ == '__main__':
    main()
