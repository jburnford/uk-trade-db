#!/usr/bin/env python3
"""Ground-truth test of the spread joiner, using FY1897 -- the last year printed unsplit.

FY1897 is the last fiscal year whose General Statement of Imports fits on a single page:
five value columns (Imported qty/value, Entered for consumption qty/value, Duty). In FY1898
the preferential tariff added three more columns, the table outgrew the page, and from then
on it was printed across a spread and scanned as two pages. Both witnesses agree on this --
324 unsplit tables in StatCan CS4-4-1897, 323 in Canadiana oocihm.9_08052_32_5.

That gives a test no real split year can give: cut the 1897 tables at the column boundary
ourselves, feed the halves to the same aligner, and check whether it puts back exactly the
rows that were together to begin with. Every answer is known in advance.

Two conditions are measured:
  clean    the halves as cut -- the aligner should be perfect, and if it is not, the scoring
           is wrong rather than the data
  damaged  rows deleted from the right half at the rate the real scans lose them (the real
           1898-1900 right pages come up 2-4 rows short per page), which is what the aligner
           actually has to survive

Usage:
    python3 scripts/ca_validate_split.py [--drop 0.03] [--trials 3] [--tables 120]
"""
from __future__ import annotations

import argparse
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ca_align_spreads as AL
import ca_pair_spreads as PS

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'statcan_1897': ROOT.parent / 'sessional_papers/statcan_trade/ocr/statcan_plato_may/CS4-4-1897-eng/CS4-4-1897-eng.md',
    'canadiana_1897': ROOT.parent / 'sessional_papers/markdown/oocihm.9_08052_32_5.md',
}
UNSPLIT_HEAD = re.compile(r'ARTICLES?\s+IMPORTED.*COUNTRIES\s+AND\s+PROVINCES.*IMPORT', re.I | re.S)


def unsplit_tables(md_path, limit):
    """Body rows of the unsplit FY1897 import tables: labels + 5 value cells."""
    text = Path(md_path).read_text(errors='ignore')
    out = []
    for m in AL.TABLE_RE.finditer(text):
        flat, has_label, nh = PS.header_signature(m.group(0))
        if nh == 0 or not has_label or not UNSPLIT_HEAD.search(flat):
            continue
        rows = []
        for cells in AL.expand_rowspans(m.group(0)):
            cells = AL.fold_cents(cells, 6)            # labels(1) + 5 values
            if len(cells) < 6:
                continue
            if not any(AL.HAS_DIGIT.search(c) for c in cells[1:]):
                continue                                # heading / banner: no counterpart when split
            rows.append(cells)
        if len(rows) >= 8:
            out.append(rows)
        if len(out) >= limit:
            break
    return out


def cut(rows):
    """Split each whole row the way the printer did in 1898: labels + first value columns on
    the left page, the remaining value columns on the right page."""
    L, R = [], []
    for cells in rows:
        vals = cells[-5:]
        labels = cells[:-5]
        L.append(dict(labels=labels,
                      tot_qty=AL.num(vals[0]),          # Imported quantity
                      tot_value=AL.num(vals[1]),        # Imported value
                      gt_qty=AL.num(vals[2])))          # Entered-for-consumption quantity
        R.append(dict(efc_value=AL.num(vals[3]), duty=AL.num(vals[4])))
    return L, R


def score_1897(l, r):
    """Keys actually available across an 1897-shaped cut.

    The 1898+ cross-page quantity identity does not exist here (no split tariff), so this
    uses the two that do: value coincidence between goods imported and goods entered for
    consumption, and the constant ad-valorem duty rate within an article.
    """
    s, key = 0, ''
    if l['tot_value'] is not None and r['efc_value'] is not None:
        if abs(l['tot_value'] - r['efc_value']) < 0.5:
            s += 4; key = 'value'
    if l['tot_value'] and r['duty'] and r['efc_value']:
        rate = r['duty'] / r['efc_value'] if r['efc_value'] else None
        if rate and 0.05 <= rate <= 0.60:               # a plausible printed duty rate
            s += 1; key = key or 'rate'
    if s == 0 and l['tot_value'] is None and r['efc_value'] is None:
        s, key = 1, 'shape'
    return s, key


def align_1897(L, R, gap=-1):
    orig = AL.score
    AL.score = score_1897
    try:
        return AL.align(L, R, gap)
    finally:
        AL.score = orig


def evaluate(tables, drop_rate, rng):
    """Returns (correct, wrong, missed) over all tables, against known truth."""
    correct = wrong = missed = 0
    for rows in tables:
        L, R = cut(rows)
        truth = list(range(len(R)))                     # right index i belongs to left index i
        keep = [i for i in truth if drop_rate == 0 or rng.random() >= drop_rate]
        Rk = [R[i] for i in keep]
        if not Rk:
            continue
        al = align_1897(L, Rk)
        got = {}
        for li, ri, _key in al:
            if li is not None and ri is not None:
                got[li] = keep[ri]
        for li in range(len(L)):
            if li in got:
                if got[li] == li:
                    correct += 1
                else:
                    wrong += 1
            elif li in keep:
                missed += 1                             # its partner was present and not found
    return correct, wrong, missed


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--drop', type=float, default=0.05, help='fraction of right rows to delete')
    ap.add_argument('--trials', type=int, default=3)
    ap.add_argument('--tables', type=int, default=120)
    a = ap.parse_args()
    rng = random.Random(20260830)

    for name, path in SOURCES.items():
        tables = unsplit_tables(path, a.tables)
        nrows = sum(len(t) for t in tables)
        print(f'\n=== {name}: {len(tables)} unsplit tables, {nrows} data rows')
        c, w, m = evaluate(tables, 0.0, rng)
        tot = c + w + m
        print(f'  clean cut          : {c}/{tot} correct ({c / max(tot,1) * 100:.2f}%), '
              f'{w} joined to the WRONG row, {m} not joined')
        for t in range(a.trials):
            c, w, m = evaluate(tables, a.drop, rng)
            tot = c + w + m
            print(f'  {a.drop:.0%} of right rows deleted (trial {t + 1}): '
                  f'{c}/{tot} correct ({c / max(tot,1) * 100:.2f}%), '
                  f'{w} WRONG, {m} not joined')


if __name__ == '__main__':
    main()
