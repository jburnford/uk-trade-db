#!/usr/bin/env python3
"""Origin-reconciliation detector (generalised from the raw-cotton finding).

For every commodity, compare the naive SUM OF ORIGIN CELLS (dominant unit)
against the Tier-1 anchored national total (the §TOTAL series), per year:
  ratio > 1.4  -> OVER-count: a parent origin line AND its breakdown are both
                  present and being summed (US + Atlantic/Pacific; British East
                  Indies + Bombay/Madras/Bengal; ...). This inflates the total
                  and creates spurious 'jumps' where the breakdown switches on/
                  off. Fixed in build_map_slim.py by parent<->child de-dup when
                  the child is in the gazetteer hierarchy.
  ratio < 0.8  -> SHORT: origins are incomplete vs the anchor.
Reports, per over-counting commodity, whether the gazetteer hierarchy explains
it (=> de-dup fixes it) or not (=> other defect: outlier cell, glue, unit).

Usage: python3 scripts/detect_origin_overcount.py [exports/map_data.json]
Output: reports/origin_overcount.csv
"""
import json, csv, sys, collections

m = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'exports/map_data.json'))
gaz = json.load(open('reference/map_gazetteer.json'))
children_of = collections.defaultdict(set)
for k, v in gaz.items():
    if v.get('parent'):
        children_of[v['parent']].add(k)

def dom_unit(e):
    u = collections.Counter()
    for c, byu in e['c'].items():
        if c == '§TOTAL':
            continue
        for un, s in byu.items():
            if un != '?':
                u[un] += len(s)
    return u.most_common(1)[0][0] if u else '?'

rows = []
for name, e in m.items():
    if '§TOTAL' not in e['c']:
        continue
    du = dom_unit(e)
    t1 = collections.defaultdict(int)
    for un, s in e['c']['§TOTAL'].items():
        if un == du or du == '?':
            for cell in s:
                t1[cell[0]] += cell[1]
    if not t1:
        for un, s in e['c']['§TOTAL'].items():
            for cell in s:
                t1[cell[0]] += cell[1]
    csum = collections.defaultdict(int)
    present_by_year = collections.defaultdict(set)
    for c, byu in e['c'].items():
        if c == '§TOTAL':
            continue
        for cell in byu.get(du, []):
            csum[cell[0]] += cell[1]
            present_by_year[cell[0]].add(c)
    over = short = ok = 0
    maxr = 0
    hierarchy_years = 0
    for y, t in t1.items():
        if t < 1000:
            continue
        r = csum.get(y, 0) / t
        maxr = max(maxr, r)
        if r > 1.4:
            over += 1
            pres = present_by_year[y]
            if any(k in pres for pa in pres for k in children_of.get(pa, ())):
                hierarchy_years += 1
        elif r < 0.8:
            short += 1
        else:
            ok += 1
    tot = over + ok + short
    if tot >= 3 and over >= 2:
        cause = ('parent-child hierarchy' if hierarchy_years >= over / 2
                 else 'other (outlier/glue/unit)')
        rows.append(dict(commodity=name, over_years=over, total_years=tot,
                         max_ratio=round(maxr, 1), gbp_lifetime=round(e['v']),
                         likely_cause=cause))
rows.sort(key=lambda r: -r['gbp_lifetime'])
with open('reports/origin_overcount.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
hi = sum(1 for r in rows if r['likely_cause'].startswith('parent'))
print(f'{len(rows)} over-counting commodities -> reports/origin_overcount.csv')
print(f'  parent-child hierarchy (de-dup fixes): {hi}')
print(f'  other (outlier/glue/unit, needs review): {len(rows)-hi}')
