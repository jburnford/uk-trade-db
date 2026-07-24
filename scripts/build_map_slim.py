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
# child -> parent (coast, presidency, colony) from the gazetteer, inverted to
# parent -> {children} for the parent<->child origin de-duplication
children_of = collections.defaultdict(set)
for k, v in gaz.items():
    if v.get('parent'):
        children_of[v['parent']].add(k)
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
    # ---- aggregate to (label, year) -> [value, qty(dom unit), bestRank] ----
    ly = {}
    for c, byu in e['c'].items():
        if c == '§TOTAL':
            continue
        for u, s in byu.items():
            for y, q, r, v in s:
                cell = ly.setdefault((c, y), [0, 0, r])
                cell[0] += min(v, CAP)
                if u == dom:
                    cell[1] += q
                cell[2] = min(cell[2], r)
    # ---- parent<->child de-duplication (the coast/subtotal double-count) ----
    # A printed origin table often carries BOTH a parent total ('United States
    # Of America') AND its breakdown ('United States (Atlantic/Pacific)', or
    # 'Bombay/Madras/Bengal' under 'British East Indies'). Summing both double-
    # counts (raw cotton read ~1.8x its Tier-1 anchor). Per year, when a parent
    # and >=1 child both appear, keep the GRANULAR children and drop the parent
    # when they account for it (>=85% of parent value); if the parent is much
    # larger (extra un-itemised sub-regions), keep the parent and drop the
    # partial children instead. Either way the label-year is counted once.
    drop = set()
    years = {y for (_c, y) in ly}
    for y in years:
        present = {c for (c, yy) in ly if yy == y}
        for pa in present:
            kids = [k for k in children_of.get(pa, ()) if k in present]
            if not kids:
                continue
            pv = ly[(pa, y)][0] or 1
            kv = sum(ly[(k, y)][0] for k in kids)
            if kv >= 0.85 * pv:
                drop.add((pa, y))                 # children cover parent
            else:
                for k in kids:
                    drop.add((k, y))              # parent is the fuller total
    # ---- build per-origin / residual / national total from de-duped cells --
    per = {}
    res = collections.defaultdict(lambda: [0, 0])
    nat = collections.defaultdict(lambda: [0, 0])       # de-duped sum of origins
    for (c, y), (v, q, r) in ly.items():
        if (c, y) in drop:
            continue
        nat[y][0] += v
        nat[y][1] += q
        if c in located:
            per.setdefault(c, {})[y] = [v, q, r]
            cov_num += v
        else:
            res[y][0] += v
            res[y][1] += q
        cov_den += v
    # Tier-1 anchor quantity per year (authoritative national total)
    t1 = collections.defaultdict(int)
    for u, s in e['c'].get('§TOTAL', {}).items():
        if u == dom or dom == '?':
            for cell in s:
                t1[cell[0]] += cell[1]
    if not t1:
        for u, s in e['c'].get('§TOTAL', {}).items():
            for cell in s:
                t1[cell[0]] += cell[1]
    if not per and not res:
        continue
    yrs = sorted(set(nat) | set(t1))
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
        't1': {str(y): round(q) for y, q in t1.items() if q},
    }

payload = {
    'meta': {
        'source': 'UK Annual Statement of Trade, imports 1872-1899',
        'measure_note': 'Origins are the country/port whence goods were '
                        'CONSIGNED (shipped) to the UK, NOT the place of '
                        'production. Entrepots (Holland, Belgium, Gibraltar, '
                        'Hong Kong) therefore overstate as "origins".',
        'quantity_note': 'National totals are the Tier-1 anchor. Origin cells '
                         'are de-duplicated: where a parent line and its '
                         'breakdown (e.g. United States + its Atlantic/Pacific '
                         'coasts) both appear, only the finer level is counted, '
                         'so origins no longer double-count against the anchor. '
                         'Per-origin values remain provisional.',
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
