#!/usr/bin/env python3
"""Slim, self-contained dataset for the public trade-origins map artifact.
Reads the curated map_data.json (cells [year,qty,rank,value]) + the whitelist
(KEEP bucket + adjudicated fold/rename targets) + the gazetteer, and emits a
compact per-commodity structure: mapped-origin series (value + dominant-unit
quantity), an unmapped residual, and the national total per year.
"""
import json, csv, collections
from pathlib import Path

CAP = 50_000_000          # per-cell value plausibility cap (matches payload sort cap)
m = json.load(open('exports/map_data.json'))
gaz = json.load(open('reference/map_gazetteer.json'))
rows = list(csv.DictReader(open('reports/commodity_curation_queue.csv')))
keep = {r['commodity'] for r in rows if r['bucket'] == 'KEEP'}
cur = list(csv.DictReader(open('reference/commodity_curation.csv')))
targets = {r['target'] for r in cur if r['action'] in ('fold', 'rename') and r['target']}
wl = sorted((keep | targets) & set(m), key=lambda n: -m[n]['v'])

located = {k for k, v in gaz.items() if v['lat'] is not None}
cov_num = cov_den = 0
out = {}
for n in wl:
    e = m[n]
    # dominant unit across country cells (for the quantity display)
    ucnt = collections.Counter()
    for c, byu in e['c'].items():
        if c == '§TOTAL':
            continue
        for u, s in byu.items():
            if u != '?':
                ucnt[u] += len(s)
    dom = ucnt.most_common(1)[0][0] if ucnt else '?'
    per = {}              # label -> {year -> [value, qty, bestRank]}
    res = collections.defaultdict(lambda: [0, 0])   # unmapped residual
    nat = collections.defaultdict(lambda: [0, 0])   # national total (all origins)
    for c, byu in e['c'].items():
        if c == '§TOTAL':
            continue
        for u, s in byu.items():
            for y, q, r, v in s:
                v = min(v, CAP)
                nat[y][0] += v
                if u == dom:
                    nat[y][1] += q
                if c in located:
                    d = per.setdefault(c, {})
                    cell = d.setdefault(y, [0, 0, r])
                    cell[0] += v
                    if u == dom:
                        cell[1] += q
                    cell[2] = min(cell[2], r)     # best (lowest) rank wins
                    cov_num += v
                else:
                    res[y][0] += v
                    if u == dom:
                        res[y][1] += q
                cov_den += v
    if not per and not res:
        continue
    yrs = sorted(nat)
    out[n] = {
        'u': dom,
        'v': round(e['v']),
        'y': [yrs[0], yrs[-1]] if yrs else [0, 0],
        'c': {c: {str(y): [round(vv[0]), round(vv[1]), vv[2]]
                  for y, vv in d.items()}
              for c, d in per.items()},
        'res': {str(y): [round(a), round(b)] for y, (a, b) in res.items()
                if a or b},
        'nat': {str(y): [round(a), round(b)] for y, (a, b) in nat.items()},
    }

payload = {
    'meta': {
        'source': 'UK Annual Statement of Trade, imports 1872-1899',
        'measure_note': 'Origins are the country/port whence goods were '
                        'CONSIGNED (shipped) to the UK, NOT the place of '
                        'production. Entrepots (Holland, Belgium, Gibraltar, '
                        'Hong Kong) therefore overstate as "origins".',
        'quantity_note': 'Quantities are anchored to Tier-1 national totals; '
                         'per-origin values are provisional (value-side '
                         'reconciliation pending).',
        'n_commodities': len(out),
    },
    'gaz': gaz,
    'commodities': out,
}
Path('exports/map_slim.json').write_text(
    json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
sz = Path('exports/map_slim.json').stat().st_size
print(f'commodities embedded: {len(out)}  gaz located: {len(located)}')
print(f'mapped-origin value coverage: {100*cov_num/(cov_den or 1):.1f}% of located+residual value')
print(f'map_slim.json: {sz/1e6:.2f} MB')
