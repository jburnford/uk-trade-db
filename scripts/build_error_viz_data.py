#!/usr/bin/env python3
"""Build error-spotting viz data from the standardized wood country x year cells.

Reuses widen_country_year.build_cells() (the reviewed standardization) so the
viz sees exactly the published matrices. Computes per-cell anomaly flags aimed
at the known OCR failure modes:

  magnitude  — cell's value is a robust-z outlier within ITS OWN
               (commodity, country) series over time (glued digits, dropped
               figures). Uses log10 + MAD; needs >=5 points in the series.
  digit-glue — value has >=2 more digits than the series median (a stronger,
               explainable subset of magnitude).
  spike      — value is >=3x BOTH temporal neighbours (up) or <=1/3 of both
               (down): an isolated year, the signature of a one-off misread.
  lowconf    — voting tier C. Common, so it is a CONFIDENCE LENS, not an
               "anomaly ring"; it only *raises severity* of structural flags.

A cell is listed as an anomaly only if it has a STRUCTURAL flag
(magnitude/digit-glue/spike); severity scales by magnitude (loads/tons at
stake) and is bumped for tier C.

Output: exports/error_viz_data.json  (inlined into the HTML page).
"""
import json
import math
from collections import defaultdict
from pathlib import Path

import widen_country_year as W

BASE = Path('/home/jic823/uk_trade_db')
OUT = BASE / 'exports' / 'error_viz_data.json'
YEARS = list(range(1872, 1900))


def median(xs):
    s = sorted(xs)
    n = len(s)
    if not n:
        return 0.0
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def main():
    cell_q, cell_tier, cell_meta, maj_unit, _, _ = W.build_cells()
    commodities = sorted({k[0] for k in cell_q})

    out_commodities = []
    anomalies = []
    for com in commodities:
        keys = [k for k in cell_q if k[0] == com]
        # countries ordered by total volume desc (biggest series on top)
        totals = defaultdict(int)
        for k in keys:
            totals[k[1]] += cell_q[k]
        countries = sorted(totals, key=lambda c: -totals[c])
        cidx = {c: i for i, c in enumerate(countries)}
        yidx = {y: i for i, y in enumerate(YEARS)}

        cells = []
        for c in countries:
            series = sorted((k[2], cell_q[k]) for k in keys if k[1] == c)
            vals = [v for _, v in series]
            logs = [math.log10(v) for v in vals if v > 0]
            digs = [len(str(v)) for v in vals]
            mlog = median(logs)
            mad = median([abs(x - mlog) for x in logs]) if logs else 0.0
            mdig = median(digs)
            for i, (yr, v) in enumerate(series):
                flags = []
                lg = math.log10(v) if v > 0 else 0
                # magnitude (robust z within own series)
                if len(logs) >= 5:
                    if mad > 0:
                        z = 0.6745 * (lg - mlog) / mad
                        if abs(z) >= 3.5:
                            flags.append('magnitude')
                    elif abs(lg - mlog) >= 0.7:
                        flags.append('magnitude')
                # digit-glue
                if len(str(v)) - mdig >= 2:
                    if 'magnitude' not in flags:
                        flags.append('magnitude')
                    flags.append('digit-glue')
                # isolated spike vs immediate temporal neighbours
                prev_v = series[i - 1][1] if i > 0 else None
                next_v = series[i + 1][1] if i < len(series) - 1 else None
                if prev_v and next_v:
                    if v >= 3 * prev_v and v >= 3 * next_v:
                        flags.append('spike-up')
                    elif v * 3 <= prev_v and v * 3 <= next_v:
                        flags.append('spike-down')
                tier = cell_tier[(com, c, yr)]
                meta = cell_meta[(com, c, yr)]
                structural = [f for f in flags if f != 'lowconf']
                if tier == 'C':
                    flags.append('lowconf')
                cell = {'c': cidx[c], 'y': yidx[yr], 'v': v, 't': tier,
                        'vols': meta['vols'], 'nl': meta['n_labels']}
                if flags:
                    cell['f'] = flags
                cells.append(cell)
                if structural:
                    base = 0
                    if 'magnitude' in structural:
                        base += 3
                    if 'digit-glue' in structural:
                        base += 1
                    if 'spike-up' in structural or 'spike-down' in structural:
                        base += 2
                    if tier == 'C':
                        base += 0.7
                    sev = round(base * (lg / 6.0), 3)
                    anomalies.append({
                        'com': com, 'country': c, 'year': yr, 'v': v, 't': tier,
                        'vols': meta['vols'], 'labels': meta['labels'],
                        'flags': structural + (['lowconf'] if tier == 'C' else []),
                        'sev': sev})

        out_commodities.append({
            'id': com, 'unit': maj_unit.get(com, ''),
            'countries': countries, 'cells': cells,
        })

    anomalies.sort(key=lambda a: -a['sev'])
    data = {'years': YEARS, 'commodities': out_commodities,
            'anomalies': anomalies[:250],
            'n_anomalies': len(anomalies),
            'n_cells': sum(len(c['cells']) for c in out_commodities)}
    OUT.write_text(json.dumps(data, separators=(',', ':')))
    print(f'commodities: {len(out_commodities)}  cells: {data["n_cells"]:,}  '
          f'structural anomalies: {len(anomalies):,} (top 250 listed)')
    print('top 8 anomalies:')
    for a in anomalies[:8]:
        print(f'  sev {a["sev"]:.2f}  {a["com"]:<24} {a["country"]:<20} '
              f'{a["year"]}  {a["v"]:>12,}  tier {a["t"]}  {",".join(a["flags"])}')
    print(f'wrote {OUT}')


if __name__ == '__main__':
    main()
