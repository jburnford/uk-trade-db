#!/usr/bin/env python3
"""Quality audit of what the public map actually shows.

Every check is framed as "what would a reader see that is wrong?", so it runs
on exports/map_slim.json (the shipped dataset) rather than on the payload.

  ANCHOR    sum of mapped origins vs the Tier-1 national quantity for the
            same year. >1.15 means origins still double-count; <0.5 means the
            map shows a small slice of the trade as if it were the whole.
  NOUNIT    dominant unit is '?', so the quantity axis is unlabelled and
            quantities from different units may be added together.
  ONEYEAR   a single year of origin data - the sparkline and slider imply a
            series that does not exist.
  MONO      one origin holds >99% of every year; usually an aggregate label
            ('All Countries') masquerading as a place.
  NOVALUE   no value at all on the value measure, so the toggle shows blank.
  RESID     the unmapped residual dominates (>60% of value): most of the
            trade is in origins the gazetteer cannot place.

The same checks run inside build_map_slim.py, which attaches the flags to
each commodity so the map can show them; this script is the reader-facing
report over the shipped file. Nothing is auto-fixed.
"""
import json, csv, collections

m = json.load(open('exports/map_slim.json'))
C = m['commodities']
flags = collections.defaultdict(list)

for n, e in C.items():
    years = sorted({int(y) for byy in e['c'].values() for y in byy}
                   | {int(y) for y in e.get('res', {})})
    # per-year sum of mapped origins + residual, in the dominant unit
    qty = collections.defaultdict(float)
    val = collections.defaultdict(float)
    for c, byy in e['c'].items():
        for y, cell in byy.items():
            val[int(y)] += cell[0]
            qty[int(y)] += cell[1]
    for y, cell in e.get('res', {}).items():
        val[int(y)] += cell[0]
        qty[int(y)] += cell[1]
    t1 = {int(y): q for y, q in e.get('t1', {}).items() if q}

    ratios = [qty[y] / t1[y] for y in years if t1.get(y) and qty.get(y)]
    if ratios:
        r = sorted(ratios)[len(ratios) // 2]
        if r > 1.15:
            flags['ANCHOR-over'].append((r, n))
        elif r < 0.5:
            flags['ANCHOR-under'].append((r, n))
    if e['u'] == '?':
        flags['NOUNIT'].append((e['v'], n))
    if len(years) == 1:
        flags['ONEYEAR'].append((e['v'], n))
    if not sum(val.values()):
        flags['NOVALUE'].append((e['v'], n))
    share = {c: sum(cell[0] for cell in byy.values()) for c, byy in e['c'].items()}
    tot = sum(share.values()) or 1
    if share and max(share.values()) / tot > 0.99 and len(e['c']) == 1:
        flags['MONO'].append((e['v'], n))
    resid = sum(cell[0] for cell in e.get('res', {}).values())
    if tot and resid / (tot + resid) > 0.6:
        flags['RESID'].append((e['v'], n))

print(f'{len(C)} mapped commodities')
for k in ('ANCHOR-over', 'ANCHOR-under', 'NOUNIT', 'ONEYEAR', 'MONO',
          'NOVALUE', 'RESID'):
    rows = sorted(flags[k], reverse=True)
    gbp = sum(C[n]['v'] for _, n in rows)
    print(f'\n{k}: {len(rows)} commodities ({gbp:,} GBP)')
    for x, n in rows[:10]:
        print(f'   {x:>12,.2f}  {n[:66]}')

with open('reports/map_audit.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['check', 'metric', 'commodity', 'gbp'])
    for k, rows in flags.items():
        for x, n in sorted(rows, reverse=True):
            w.writerow([k, round(x, 3), n, C[n]['v']])
print('\n-> reports/map_audit.csv')
