#!/usr/bin/env python3
"""Data-quality validation for the UK trade database.

Detector 1 — cross-volume disagreement: each statistical year appears in up
to five volumes (5-year comparative columns). Where independent printings/
scans/OCR of the same figure disagree, flag it; majority vote suggests the
likely-correct value.

Detector 2 — wild outliers in runs: per (flow, measure, commodity) series,
flag values >RATIO x or <1/RATIO x BOTH neighbours (median across volumes
per year first). Catches digit slips that survive cross-volume voting
because they replicate from a single bad printing, and genuine data-entry
scale errors (Cwts vs Tons switches show up here too).

Output: reports/validation_flags.csv + console summary.
"""
import csv
from collections import defaultdict
from pathlib import Path
from statistics import median

import duckdb

BASE = Path('/home/jic823/uk_trade_db')
RATIO = 4.0          # neighbour-jump threshold
MIN_VAL = 100        # ignore tiny series where jumps are legitimate


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)
    rows = con.execute('''
        SELECT ca.commodity_id, o.flow, o.measure, o.year, o.volume, o.value
        FROM abstract_obs o
        JOIN commodity_alias ca
          ON o.article IS NOT DISTINCT FROM ca.article
         AND o.article_group IS NOT DISTINCT FROM ca.article_group
        WHERE o.value IS NOT NULL''').fetchall()

    series = defaultdict(dict)       # (cid, flow, measure) -> year -> {vol: v}
    for cid, flow, measure, year, vol, val in rows:
        series[(cid, flow, measure)].setdefault(year, {})[vol] = val

    flags = []

    # -------- detector 1: cross-volume disagreement
    n_multi = n_disagree = 0
    for key, ys in series.items():
        for y, byvol in ys.items():
            if len(byvol) < 2:
                continue
            n_multi += 1
            vals = list(byvol.values())
            if max(vals) - min(vals) > 0.5:          # any real difference
                n_disagree += 1
                med = median(vals)
                for vol, v in byvol.items():
                    if abs(v - med) > 0.5:
                        flags.append((*key, y, vol, v, med,
                                      'cross_volume_disagreement'))

    # -------- detector 2: neighbour-jump outliers
    n_jump = 0
    for key, ys in series.items():
        yearly = {y: median(bv.values()) for y, bv in ys.items()}
        yrs = sorted(yearly)
        for i in range(1, len(yrs) - 1):
            y0, y1, y2 = yrs[i - 1], yrs[i], yrs[i + 1]
            if y1 - y0 > 3 or y2 - y1 > 3:
                continue                     # only within contiguous runs
            a, b, c = yearly[y0], yearly[y1], yearly[y2]
            if b < MIN_VAL and a < MIN_VAL and c < MIN_VAL:
                continue
            lo = min(x for x in (a, c) if x > 0) if (a > 0 or c > 0) else 0
            hi = max(a, c)
            if b > 0 and hi > 0:
                if (b > RATIO * hi) or (b * RATIO < lo):
                    n_jump += 1
                    flags.append((*key, y1, 'series', b,
                                  (a + c) / 2, 'neighbour_jump'))

    out = BASE / 'reports' / 'validation_flags.csv'
    with open(out, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['commodity_id', 'flow', 'measure', 'year', 'volume',
                    'value', 'reference', 'flag'])
        w.writerows(sorted(flags))

    n_obs = len(rows)
    print(f'observations checked: {n_obs:,}')
    print(f'year-cells with multiple volume observations: {n_multi:,}')
    print(f'  disagreeing: {n_disagree:,} '
          f'({n_disagree / max(n_multi, 1):.1%})')
    print(f'neighbour-jump outliers: {n_jump:,}')
    print(f'flags written: {len(flags):,} -> {out}')
    print('\nworst neighbour-jumps (value vs neighbour mean):')
    jumps = [f for f in flags if f[-1] == 'neighbour_jump']
    jumps.sort(key=lambda f: -max(f[5] / max(f[6], 1), f[6] / max(f[5], 1)))
    for f in jumps[:12]:
        print(f'  {f[0]:<45} {f[1]}/{f[2]} {f[3]}: '
              f'{f[5]:>14,.0f} vs ~{f[6]:>12,.0f}')


if __name__ == '__main__':
    main()
