#!/usr/bin/env python3
"""Per-cell diff of two viz_payload.json files, using reconcile_baseline's rule.

Usage: python3 scripts/diff_payload_cells.py OLD.json NEW.json [--all]

reconcile_baseline.py answers "where does the corpus stand"; this answers "what
did my change actually do", which is a different question and the one that
decides whether a change ships. It reports the bucket totals for both payloads,
the exact01 delta, and then every (commodity, year) that changed bucket, split
into BETTER and WORSE with the before/after ratios.

WHY IT EXISTS. On 2026-08-03 a change raised the GBP-weighted headline from
54.1% to 55.3% while FOUR cells got worse and NONE got better: that metric
weights by commodity value, and the change had renamed a GBP283M node, moving
its weight. The headline alone would have shipped a regression. A GBP-weighted
gain with no per-cell gain is a weighting artefact. ALWAYS read this diff first.

Snapshot the payload before touching anything (`cp exports/viz_payload.json
/tmp/base.json`), rebuild, then diff against it. Cells that appear in only one
side are listed separately - a commodity can leave the measured set entirely,
which is neither better nor worse but is never what you intended.
"""
import json, sys, collections

ORDER = {'exact01': 0, 'within5': 1, 'under': 2, 'over': 3, 'nodata': 4}


def cells(path):
    p = json.load(open(path))
    out = {}
    for name, entry in p.items():
        c = entry.get('c') or {}
        t1 = c.get('§TOTAL')
        if not t1:
            continue
        units = {u: len(v) for u, v in t1.items()}
        unit = max(units, key=units.get)
        vals = [row[1] for row in t1[unit] if row[1]]
        if not vals:
            continue
        med = sorted(vals)[len(vals) // 2]
        t1_years = {}
        for row in t1[unit]:
            y, q = row[0], row[1]
            if q and med and q > 30 * med:
                continue
            if q:
                t1_years[y] = q
        if not t1_years:
            continue
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
        for y, tq in t1_years.items():
            if y not in has_any:
                b, ratio = 'nodata', None
            else:
                d = abs(csum[y] - tq) / tq
                b = ('exact01' if d <= 0.001 else 'within5' if d <= 0.05
                     else 'under' if csum[y] < tq else 'over')
                ratio = csum[y] / tq
            out[(name, y)] = (b, ratio)
    return out


def summary(d, tag):
    t = collections.Counter(v[0] for v in d.values())
    n = sum(t.values())
    print(f'{tag}: {n:,} cells  exact01 {t["exact01"]:,} ({100*t["exact01"]/n:.1f}%) '
          f'within5 {t["within5"]:,} under {t["under"]:,} over {t["over"]:,} '
          f'nodata {t["nodata"]:,}')
    return t


a, b = cells(sys.argv[1]), cells(sys.argv[2])
ta = summary(a, 'OLD')
tb = summary(b, 'NEW')
print(f'  delta exact01 {tb["exact01"]-ta["exact01"]:+,}   '
      f'within5+ {tb["exact01"]+tb["within5"]-ta["exact01"]-ta["within5"]:+,}   '
      f'nodata {tb["nodata"]-ta["nodata"]:+,}')

better, worse, gone, new = [], [], [], []
for k in set(a) | set(b):
    va, vb = a.get(k), b.get(k)
    if va is None:
        new.append((k, vb))
        continue
    if vb is None:
        gone.append((k, va))
        continue
    if va[0] == vb[0]:
        continue
    (better if ORDER[vb[0]] < ORDER[va[0]] else worse).append((k, va, vb))
print(f'\nBETTER {len(better)}   WORSE {len(worse)}   '
      f'cells only in OLD {len(gone)}   only in NEW {len(new)}')

lim = None if '--all' in sys.argv else 40


def fmt(r):
    return f'{r:.4f}' if r is not None else '  -   '


for tag, rows in (('BETTER', better), ('WORSE', worse)):
    print(f'\n--- {tag} ---')
    for (name, y), va, vb in sorted(rows)[:lim]:
        print(f'  {name[:60]:60s} {y}  {va[0]:8s} {fmt(va[1])} -> '
              f'{vb[0]:8s} {fmt(vb[1])}')
    if lim and len(rows) > lim:
        print(f'  ... {len(rows)-lim} more')
for tag, rows in (('ONLY IN OLD', gone), ('ONLY IN NEW', new)):
    if rows:
        print(f'\n--- {tag} ({len(rows)}) ---')
        for (name, y), v in sorted(rows)[:lim]:
            print(f'  {name[:60]:60s} {y}  {v[0]:8s} {fmt(v[1])}')
        if lim and len(rows) > lim:
            print(f'  ... {len(rows)-lim} more')
