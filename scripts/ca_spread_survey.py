#!/usr/bin/env python3
"""Survey the split-spread problem in the Canadian Trade & Navigation OCR.

A "split spread" is a table printed across two facing pages that the scan cut into two
images, so Chandra emits a LEFT table (row labels + first value columns) and a RIGHT table
(numbers only). See SPREAD_ALIGNMENT_PLAN.md.

Modes
  (default)            per-volume count of number-only tables, all Canadian + UK volumes
  --align MD [MD ...]  crude value-key alignment of left/right pairs (the baseline in the plan)
  --show MD --pair N   print the N-th left/right pair of a volume for eyeballing

The "number-only" test: first two cells numeric or blank in >=85% of body rows, >=8 rows.
It is a survey heuristic, not the pairing rule the real aligner should use.
"""
import argparse
import glob
import html as H
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATCAN = ROOT.parent / 'sessional_papers' / 'statcan_trade' / 'ocr'

NUM_OR_BLANK = re.compile(r'^[\s$£]*[\d,]+(?:\s\d\d)?\s*$|^[.\s…]*$')
PLAIN_INT = re.compile(r'^\$?\s*\d{1,3}(?:,\d{3})+$|^\$?\s*\d+$')
TABLE_RE = re.compile(r'<table\b.*?</table>', re.S)
ROW_RE = re.compile(r'<tr\b.*?</tr>', re.S)
CELL_RE = re.compile(r'<t[dh]\b[^>]*>(.*?)</t[dh]>', re.S)


def rows_of(table_html):
    rows = []
    for tr in ROW_RE.findall(table_html):
        cells = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', H.unescape(c))).strip() for c in CELL_RE.findall(tr)]
        if any(cells):
            rows.append(cells)
    return rows


def number_only(rows):
    body = [r for r in rows if len(r) >= 4][2:]
    if len(body) < 8:
        return False
    hits = sum(1 for r in body if NUM_OR_BLANK.match(r[0]) and (len(r) < 2 or NUM_OR_BLANK.match(r[1])))
    return hits / len(body) >= 0.85


def tables_of(md_path):
    text = Path(md_path).read_text(errors='ignore')
    return text, [(m.start(), rows_of(m.group(0))) for m in TABLE_RE.finditer(text)]


def volume_files():
    files = sorted(glob.glob(str(ROOT / 'raw_canada' / '*' / '*.md')))
    files += sorted(glob.glob(str(STATCAN / '**' / '*.md'), recursive=True))
    for d in sorted(glob.glob(str(ROOT / 'raw' / 'as_*'))) + sorted(glob.glob(str(ROOT / 'raw' / 'tn_*'))):
        mds = glob.glob(d + '/**/*.md', recursive=True)
        if mds:
            files.append(mds[0])
    return files


def survey():
    for f in volume_files():
        _, tabs = tables_of(f)
        big = [rows for _, rows in tabs if len(rows) >= 8]
        n_only = sum(number_only(r) for r in big)
        label = Path(f).parent.name if 'raw_canada' in f or 'statcan' in f else Path(f).parents[0].name
        pct = n_only / len(big) * 100 if big else 0
        print(f'{label[:30]:30s} tables={len(big):5d} number_only={n_only:4d} ({pct:4.1f}%)')


def pairs_of(tabs):
    """Crude pairing: a labelled table (>20 rows) immediately followed by a number-only one."""
    return [i for i in range(1, len(tabs))
            if number_only(tabs[i][1]) and not number_only(tabs[i - 1][1]) and len(tabs[i - 1][1]) > 20]


def ints(row):
    return [int(c.replace('$', '').replace(',', '')) for c in row if PLAIN_INT.match(c.strip())]


def lcs_sets(a, b):
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n):
        for j in range(m):
            dp[i + 1][j + 1] = dp[i][j] + 1 if (a[i] and b[j] and a[i] & b[j]) else max(dp[i][j + 1], dp[i + 1][j])
    return dp[n][m]


def align(md_path):
    """Baseline: a left row matches a right row when any plain integer on the left equals any
    plain integer, or any pairwise sum of two integers, on the right (I1/I6 of the plan)."""
    _, tabs = tables_of(md_path)
    pairs = pairs_of(tabs)
    bands, total, hit = Counter(), 0, 0
    for i in pairs:
        left = [set(ints(r)) for r in tabs[i - 1][1]]
        right = []
        for r in tabs[i][1]:
            v = ints(r)
            s = set(v)
            for a in range(len(v)):
                for b in range(a + 1, len(v)):
                    s.add(v[a] + v[b])
            right.append(s)
        n = sum(1 for x in left if x)
        if not n:
            continue
        k = lcs_sets(left, right)
        total += n
        hit += k
        f = k / n
        bands['>=90%' if f >= .9 else '70-90%' if f >= .7 else '50-70%' if f >= .5 else '<50%'] += 1
    print(f'{Path(md_path).name}: pairs={len(pairs)} left_value_rows={total} aligned={hit} '
          f'({hit / max(total, 1) * 100:.1f}%) per-pair={dict(bands)}')


def show(md_path, n):
    text, tabs = tables_of(md_path)
    pairs = pairs_of(tabs)
    if not pairs:
        sys.exit('no pairs found')
    i = pairs[min(n, len(pairs) - 1)]
    print(f'{len(pairs)} pairs; showing pair {n} (tables {i - 1} and {i})')
    for j in (i - 1, i):
        off, rows = tabs[j]
        pre = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', text[max(0, off - 250):off])).strip()[-140:]
        print(f'\n##### table {j}  rows={len(rows)}  text before: {pre!r}')
        for r in rows[:16]:
            print('   ', ' | '.join(c[:28] for c in r)[:220])
        if len(rows) > 19:
            print('    ...')
        for r in rows[-3:]:
            print('   ', ' | '.join(c[:28] for c in r)[:220])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--align', nargs='+', metavar='MD')
    ap.add_argument('--show', metavar='MD')
    ap.add_argument('--pair', type=int, default=0)
    a = ap.parse_args()
    if a.align:
        for f in a.align:
            align(f)
    elif a.show:
        show(a.show, a.pair)
    else:
        survey()


if __name__ == '__main__':
    main()
