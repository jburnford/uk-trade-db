#!/usr/bin/env python3
"""Malformed comma groups in the raw OCR — the 1897-1900 mechanism.

A comma-grouped figure must carry exactly three digits after every comma.
`39,94` is not a printing that exists; it is `39,940` (or `39,94x`) with a digit
lost at the page edge. The table parser strips commas before converting, so it
reads that cell as 3,994 — an order of magnitude too small, with no error and
no warning.

That is what breaks 1897-1900. The rate of malformed groups is 0.00-0.05% in
every single-year volume and jumps to 0.33-0.39% in as_1897, as_1898 and
tn_1899, and **92-95% of those sit in the last numeric column of their row.**
The comparative volumes print ten numeric columns (five quantity, five value,
one per year), so the rightmost column is at the page edge and loses digits.

That also explains the finding that looked paradoxical: the volume's OWN year
closes worse than the prior years it reprints (as_1897 own-year 8.2% against
21.0% for its comparatives). The own year is the rightmost column. It is a
column-position effect, not anything about reprinting.

Worked example, as_1897 ALKALI, Germany:

    raw 1893-1897 values:  49,133  42,492  22,249  34,577  39,94
    parsed 1897 value:     3,994
    as_1898 and as_1899 both print:  40,904

Repair path is cross-witness, not arithmetic: for 1893-96 the later volumes
carry the same year in a non-edge column, and for 1897/98 a later volume does
too. 1899 and 1900 have no later witness and cannot be repaired this way.

Usage:
    python3 scripts/detect_malformed_numbers.py [--raw raw]
        [--out reports/malformed_numbers.csv] [--volume as_1897]
"""
import argparse, collections, csv, glob, html, os, re

ROW_RE = re.compile(r'<tr>(.*?)</tr>', re.S | re.I)
CELL_RE = re.compile(r'<td[^>]*>(.*?)</td>', re.S | re.I)
NUM_RE = re.compile(r'^-?\d{1,3}(?:,\d+)+$')


def clean(c):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', c))).strip()


def malformed(s):
    if not NUM_RE.match(s):
        return False
    return any(len(g) != 3 for g in s.split(',')[1:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw', default='raw')
    ap.add_argument('--out', default='reports/malformed_numbers.csv')
    ap.add_argument('--volume')
    a = ap.parse_args()

    tot, bad, last = collections.Counter(), collections.Counter(), collections.Counter()
    recs = []
    for d in sorted(glob.glob(f'{a.raw}/*')):
        if not os.path.isdir(d):
            continue
        vol = os.path.basename(d)
        if a.volume and vol != a.volume:
            continue
        md = glob.glob(f'{d}/**/*.md', recursive=True)
        if not md:
            continue
        text = open(md[0], encoding='utf-8', errors='replace').read()
        for rowhtml in ROW_RE.findall(text):
            cells = [clean(c) for c in CELL_RE.findall(rowhtml)]
            nums = [(i, c) for i, c in enumerate(cells) if NUM_RE.match(c)]
            for rank, (i, c) in enumerate(nums):
                tot[vol] += 1
                if not malformed(c):
                    continue
                bad[vol] += 1
                is_last = (rank == len(nums) - 1)
                last[vol] += int(is_last)
                recs.append(dict(volume=vol, label=cells[0][:60] if cells else '',
                                 raw=c, parsed_as=int(c.replace(',', '')),
                                 col=rank + 1, of=len(nums),
                                 last_column=int(is_last)))

    print(f'{"volume":>9} {"numeric cells":>14} {"malformed":>10} {"rate":>7} '
          f'{"in LAST col":>12}')
    for vol in sorted(tot):
        t, b = tot[vol], bad[vol]
        print(f'{vol:>9} {t:>14,} {b:>10,} {100*b/t if t else 0:>6.2f}% '
              f'{100*last[vol]/b if b else 0:>11.1f}%')

    if recs:
        with open(a.out, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(recs[0].keys()))
            w.writeheader()
            w.writerows(recs)
        print(f'\nwrote {a.out} ({len(recs):,} rows)')


if __name__ == '__main__':
    main()
