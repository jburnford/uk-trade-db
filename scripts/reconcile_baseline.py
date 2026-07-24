#!/usr/bin/env python3
"""Reconciliation-coverage baseline (round-16b metric, made permanent).

For every payload commodity-year with a T1 national line (§TOTAL, modal
unit): compare the country-cell sum (same unit; paren drill-downs like
'United States Of America (Atlantic)' excluded) against T1.

Buckets: within 0.1%% / within 5%% / off / no-country-data.
Weights: unweighted commodity-year counts + GBP-weighted (commodity total
GBP 'v' spread uniformly over its T1 years — same crude weighting the
round-16b transcript used).

Usage: python3 scripts/reconcile_baseline.py /path/payload.json
"""
import json, sys, collections

def main(path):
    p = json.load(open(path))
    tot = collections.Counter()
    gbp = collections.Counter()
    n_cy = 0
    for name, entry in p.items():
        c = entry.get('c') or {}
        t1 = c.get('§TOTAL')
        if not t1:
            continue
        # modal unit of the T1 series
        units = {u: len(v) for u, v in t1.items()}
        unit = max(units, key=units.get)
        t1_years = {}
        vals = [row[1] for row in t1[unit] if row[1]]
        if not vals:
            continue
        med = sorted(vals)[len(vals)//2]
        for row in t1[unit]:
            y, q = row[0], row[1]
            if q and med and q > 30*med:      # junk clamp (detector-A rule)
                continue
            if q:
                t1_years[y] = q
        if not t1_years:
            continue
        # country sums in the T1 unit, paren drill-downs excluded
        csum = collections.Counter()
        has_any = set()
        for ctry, byunit in c.items():
            if ctry == '§TOTAL' or '(' in ctry:
                continue
            series = byunit.get(unit)
            if not series:
                continue
            for row in series:
                y, q = row[0], row[1]
                if q and y in t1_years:
                    csum[y] += q
                    has_any.add(y)
        w = (entry.get('v') or 0) / max(1, len(t1_years))
        for y, tq in t1_years.items():
            n_cy += 1
            if y not in has_any:
                b = 'nodata'
            else:
                d = abs(csum[y] - tq) / tq
                b = 'exact01' if d <= 0.001 else ('within5' if d <= 0.05 else
                    ('under' if csum[y] < tq else 'over'))
            tot[b] += 1
            gbp[b] += w
    G = sum(gbp.values()) or 1
    print(f'commodity-years with T1 line: {n_cy:,}')
    for b in ('exact01', 'within5', 'under', 'over', 'nodata'):
        print(f'  {b:8s}: {tot[b]:5,}  ({100*tot[b]/n_cy:5.1f}%)   GBP-weighted {100*gbp[b]/G:5.1f}%')
    print(f'  within 0.1%: {100*tot["exact01"]/n_cy:.1f}% of commodity-years, '
          f'{100*gbp["exact01"]/G:.1f}% GBP-weighted')
    print(f'  within 5%  : {100*(tot["exact01"]+tot["within5"])/n_cy:.1f}% of commodity-years, '
          f'{100*(gbp["exact01"]+gbp["within5"])/G:.1f}% GBP-weighted')

if __name__ == '__main__':
    main(sys.argv[1])
