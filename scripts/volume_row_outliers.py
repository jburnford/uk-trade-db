#!/usr/bin/env python3
"""Find commodities where ONE volume absorbed a whole section under its heading.

Rounds 55-58 repaired the same defect three times. A late volume loses a column
heading and the parser files everything that follows under the commodity above
it, so one `(article_group, article)` acquires hundreds of rows in that volume
while every other volume has a handful:

    Dye Woods — Logwood              as_1898  621 rows   others 4-27
    Collodium                        as_1897  381 rows   others none
    Oil-Seed Cake — Of Other Sorts   as_1898  355 rows   others 1-6

The payload then reads the commodity at 3x to 1,349x its printed total, and in
every case the REAL table turned out to be a short run at the HEAD of the block
whose printed grand totals match Tier 1 to the digit.

That is a shape, not a coincidence, and it is cheap to look for: per
`(article_group, article)`, compare the busiest volume's row count against the
median of the others. A printed origin table is 4-30 rows in a single-year
volume and 30-90 in a five-year comparative one; ten times the median, with a
hundred rows or more in absolute terms, is not a bigger table.

The output is a QUEUE, not a verdict — each candidate still needs the real
table located and its totals checked against Tier 1 before anything is written.

Usage: python3 scripts/volume_row_outliers.py [out.csv]
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

import duckdb

BASE = Path('/home/jic823/uk_trade_db')

MIN_ROWS = 100        # absolute floor: below this a "big" block is a real table
MIN_RATIO = 10        # times the median of the other volumes
MIN_VOLUMES = 2       # need something to compare against


def main(out_path):
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)
    rows = con.execute("""
        SELECT article_group, coalesce(article, '') AS article, volume,
               count(*) AS n, min(row_seq) AS s0, max(row_seq) AS s1,
               min(year) AS y0, max(year) AS y1
        FROM country_obs
        WHERE flow = 'import'
        GROUP BY 1, 2, 3
    """).fetchall()

    by_comm = defaultdict(list)
    for grp, art, vol, n, s0, s1, y0, y1 in rows:
        by_comm[(grp, art)].append((n, vol, s0, s1, y0, y1))

    out = []
    for (grp, art), vols in by_comm.items():
        if len(vols) < MIN_VOLUMES:
            continue
        vols.sort(reverse=True)
        top = vols[0]
        rest = sorted(v[0] for v in vols[1:])
        med = rest[len(rest) // 2]
        if top[0] < MIN_ROWS or top[0] < MIN_RATIO * max(med, 1):
            continue
        out.append({
            'article_group': grp, 'article': art,
            'volume': top[1], 'rows': top[0],
            'median_other_volumes': med,
            'ratio': round(top[0] / max(med, 1), 1),
            'other_volumes': len(vols) - 1,
            'seq_start': top[2], 'seq_end': top[3],
            'years': f'{top[4]}-{top[5]}',
            'span': top[3] - top[2] + 1,
        })
    out.sort(key=lambda r: -r['rows'])

    with open(out_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]) if out else ['article_group'])
        w.writeheader()
        w.writerows(out)

    print(f'commodities scanned: {len(by_comm):,}')
    print(f'one-volume outliers (>= {MIN_ROWS} rows AND >= {MIN_RATIO}x the '
          f'median of the other volumes): {len(out)}')
    print(f'-> {out_path}')
    print()
    print(f"{'article_group':<26}{'article':<30}{'volume':<9}{'rows':>6}"
          f"{'med':>5}{'ratio':>7}  seq")
    for r in out[:25]:
        print(f"{r['article_group'][:24]:<26}{r['article'][:28]:<30}"
              f"{r['volume']:<9}{r['rows']:>6}{r['median_other_volumes']:>5}"
              f"{r['ratio']:>7}  {r['seq_start']}-{r['seq_end']}")


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1
         else str(BASE / 'reports' / 'volume_row_outliers.csv'))
