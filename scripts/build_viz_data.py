#!/usr/bin/env python3
"""Assemble a compact JSON payload for the research visualization: voted
wood-by-country (loads), Tier-1 national wood totals, TTJ calibrated shares,
and the triangulation. Written to exports/viz_data.json for embedding."""
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import median

UK = Path('/home/jic823/uk_trade_db')
TD = Path('/home/jic823/timber_data')

MAJORS = ['canada', 'russia', 'sweden', 'norway', 'france',
          'united states of america', 'germany']
COMMS = ['wood-hewn-fir', 'wood-sawn-fir', 'wood-hewn-oak', 'wood-hewn-teak',
         'wood-staves', 'wood-hewn-unenumerated', 'wood-sawn-unenumerated',
         'wood-mahogany']


def num(s):
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


# ---- voted wood by country (loads only; the timber unit)
wood = []
for r in csv.DictReader(open(UK / 'exports' / 'wood_country_year_voted.csv')):
    if r['unit'] != 'loads':
        continue
    q = num(r['quantity'])
    if not q:
        continue
    wood.append({
        'c': r['commodity'].replace('wood-', ''),
        'k': r['country'], 'y': int(r['year']),
        'q': round(q), 'qt': r['q_tier'],
        'v': round(num(r['value']) or 0), 'vt': r['v_tier'],
        'nv': int(r['n_volumes']),
    })

# ---- value-as-signal: within each commodity x country series the unit
# price (value / quantity) drifts only slowly, so a cell whose unit price
# sits far from the series median has a quantity/value MISMATCH — one column
# is a likely digit-slip. A tier-C quantity whose unit price is in line is
# CORROBORATED by its value (independent of OCR/vote agreement).
# two-way (origin x year) price model — matches rescore_value.py so a
# market-wide shock or a persistently cheaper grade does not false-flag;
# only a lone outlier does.
priced = [d for d in wood if d['q'] and d['v'] and d['q'] >= 200]
cyr = defaultdict(lambda: defaultdict(list))         # commodity-year prices
for d in priced:
    cyr[d['c']][d['y']].append(d['v'] / d['q'])
mkt = {c: {y: median(ps) for y, ps in yd.items() if len(ps) >= 3}
       for c, yd in cyr.items()}
offs = defaultdict(list)                              # origin offset vs market
for d in priced:
    if d['c'] in mkt and d['y'] in mkt[d['c']] and mkt[d['c']][d['y']] > 0:
        offs[(d['c'], d['k'])].append((d['v'] / d['q']) / mkt[d['c']][d['y']])
offset = {k: median(v) for k, v in offs.items() if len(v) >= 3}
own = defaultdict(list)                               # own-series fallback
for d in priced:
    own[(d['c'], d['k'])].append(d['v'] / d['q'])
sp = {k: median(v) for k, v in own.items() if len(v) >= 3}
for d in wood:
    d['up'], d['pr'] = None, None
    if not (d['q'] and d['v'] and d['q'] > 0):
        continue
    p = d['v'] / d['q']
    d['up'] = round(p, 1)
    S = (d['c'], d['k'])
    exp, wide = None, False
    if S in offset and d['c'] in mkt and d['y'] in mkt[d['c']] \
            and mkt[d['c']][d['y']] > 0:
        exp = mkt[d['c']][d['y']] * offset[S]
    elif S in sp:
        exp, wide = sp[S], True
    if exp and exp > 0:
        r = p / exp
        lo, hi = (0.4, 2.5) if wide else (0.5, 2.0)
        d['pr'] = 'ok' if lo <= r <= hi else ('hi' if r > hi else 'lo')

# ---- Tier-1 national wood totals (import quantity = loads where present)
nat = defaultdict(dict)
for r in csv.DictReader(open(UK / 'exports' / 'wood_national_year.csv')):
    if r['flow'] != 'import':
        continue
    key = (r['commodity'].replace('wood-', ''), int(r['year']))
    nat[f"{key[0]}|{key[1]}|{r['measure']}"] = {
        'val': round(num(r['value']) or 0), 'tier': r['tier']}

# ---- TTJ calibrated shares
ttj = defaultdict(dict)
for r in csv.DictReader(open(TD / 'exports' / 'country_shares_calibrated.csv')):
    ttj[int(r['year'])][r['country'].lower()] = {
        'count': round(num(r['count_share']) or 0, 4),
        'cal': round(num(r['calibrated_volume_share']) or 0, 4)}

# ---- triangulation
tri = []
for r in csv.DictReader(open(TD / 'exports' /
                             'canada_annual_triangulation.csv')):
    tri.append({k: num(v) if k != 'year' else int(v)
                for k, v in r.items()})

payload = {
    'wood': wood,
    'majors': MAJORS,
    'commodities': [c.replace('wood-', '') for c in COMMS],
    'national': nat,
    'ttj': {str(y): d for y, d in ttj.items()},
    'triangulation': tri,
    'meta': {
        'wood_cells': len(wood),
        'years': [min(w['y'] for w in wood), max(w['y'] for w in wood)],
    },
}
out = UK / 'exports' / 'viz_data.json'
json.dump(payload, open(out, 'w'), separators=(',', ':'))
print(f'-> {out}  ({out.stat().st_size // 1024} KB, {len(wood)} wood cells)')
