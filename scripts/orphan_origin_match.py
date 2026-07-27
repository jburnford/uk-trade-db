#!/usr/bin/env python3
"""Find origin tables that belong to a DIFFERENT commodity's printed anchor.

The round-34 shape, generalised. `Animals, Living — Horses` published a Tier-1
national line for every year 1866-1891 and carried origin data for one of them;
the missing tables were sitting under `Cows — Horses` and `Animals — Horses`,
two labels the parser minted from a drifting section head. They were provable
because the orphan's origin sum equalled the target's printed T1 **to the
digit**, year after year.

That test needs no page image, no second engine and no vote: a national total is
published independently of the origin table, so an orphan whose countries sum to
some other commodity's printed total in two or more years is that commodity's
table. One coincidence is possible; two is not.

Method
------
For every payload commodity: T1 by year (modal unit), and the origin sum by year
as consumers see it (paren drill-downs and §TOTAL excluded, same rule as
`reconcile_baseline.py`). A commodity-year is a GAP when T1 exists and the
origin sum is zero. Then join every OTHER commodity's origin-sum years against
those gaps on the value itself, and keep pairs that agree in enough years.

A match is EXACT when the sums are equal to the digit, NEAR when within 0.1%
(single-cell OCR noise: round 34's ten horse-years included a -30 and a -3).

Ranking is by exact matches first, because that is what carries the proof.

Usage: python3 scripts/orphan_origin_match.py [payload.json] [out.csv]
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path('/home/jic823/uk_trade_db')

MIN_YEARS = 2          # one value coincidence is possible; two is not
MIN_VALUE = 100        # tiny totals collide by chance (many commodities print 1)
NEAR = 0.001           # 0.1%, the reconcile_baseline "exact" band


# a regional aggregate printed BESIDE its own members doubles the region, and
# an ORPHAN cannot be caught at it because it has no printed total of its own
# (round 38). Such a source reads ~1.9x its true target and the value-join below
# would never see it. So each source is offered TWICE: as parsed, and with the
# aggregate cell removed wherever its members are present in the same year.
AGGREGATES = {
    'British East Indies': ('Bengal', 'Bengal And Burmah', 'Bombay', 'Madras',
                            'Ceylon', 'Burmah', 'Straits Settlements',
                            'Other British East Indian Possessions'),
    'British Possessions In South Africa': ('Cape Of Good Hope', 'Natal'),
    'Australasia': ('New South Wales', 'Victoria', 'Queensland',
                    'South Australia', 'Western Australia', 'Tasmania',
                    'New Zealand'),
}


def series(entry):
    """(t1 by year, origin sum by year, aggregate-adjusted sum, unit)."""
    c = entry.get('c') or {}
    t1 = c.get('§TOTAL')
    unit = None
    t1y = {}
    if t1:
        unit = max(t1, key=lambda u: len(t1[u]))
        t1y = {r[0]: r[1] for r in t1[unit] if r[1]}
    origin = defaultdict(float)
    for ctry, byu in c.items():
        if ctry == '§TOTAL' or '(' in ctry:
            continue
        for u, cells in byu.items():
            if unit and u != unit:
                continue
            for r in cells:
                if r[1]:
                    origin[r[0]] += r[1]
    adj = dict(origin)
    for parent, members in AGGREGATES.items():
        if parent not in c:
            continue
        kid_years = set()
        for m in members:
            for u, cells in (c.get(m) or {}).items():
                if unit and u != unit:
                    continue
                kid_years.update(r[0] for r in cells if r[1])
        for u, cells in c[parent].items():
            if unit and u != unit:
                continue
            for r in cells:
                if r[1] and r[0] in kid_years and adj.get(r[0]):
                    adj[r[0]] -= r[1]
    return t1y, dict(origin), adj, unit


def main(payload_path, out_path):
    payload = json.load(open(payload_path))
    t1s, origins, adjs, units = {}, {}, {}, {}
    for name, entry in payload.items():
        t1y, org, adj, unit = series(entry)
        t1s[name], origins[name], adjs[name], units[name] = t1y, org, adj, unit

    # gaps: a printed national line with no origin table under this label
    gaps = defaultdict(dict)                 # target -> {year: t1}
    by_year = defaultdict(list)              # year -> [(target, t1)]
    for name, t1y in t1s.items():
        org = origins[name]
        for y, q in t1y.items():
            if q and q >= MIN_VALUE and not org.get(y):
                gaps[name][y] = q
                by_year[y].append((name, q))

    # join every other label's origin sums onto those gaps, on the value
    pairs = defaultdict(list)                # (source, target) -> [(y, src, t1, kind)]
    for src, org in origins.items():
        adj = adjs[src]
        for y, v0 in org.items():
            for v, tag in ((v0, ''), (adj.get(y, v0), '*')):
                if not v or v < MIN_VALUE or (tag and v == v0):
                    continue
                for tgt, q in by_year.get(y, ()):
                    if tgt == src:
                        continue
                    if round(v) == round(q):
                        kind = 'exact' + tag
                    elif abs(v - q) / q <= NEAR:
                        kind = 'near' + tag
                    else:
                        continue
                    pairs[(src, tgt)].append((y, v, q, kind))

    rows = []
    for (src, tgt), hits in pairs.items():
        n_exact = sum(1 for h in hits if h[3].startswith('exact'))
        n_adj = sum(1 for h in hits if h[3].endswith('*'))
        if len(hits) < MIN_YEARS or not n_exact:
            continue
        # a source whose OWN anchor already covers these years is a rival
        # series, not an orphan: say so rather than silently ranking it high
        src_anchored = bool(t1s.get(src))
        overlap = sorted(set(origins[src]) & set(origins[tgt]))
        hits.sort()
        rows.append({
            'source': src, 'target': tgt,
            'n_exact': n_exact, 'n_near': len(hits) - n_exact,
            'n_via_aggregate_drop': n_adj,
            'years': ';'.join(str(h[0]) for h in hits),
            'source_has_own_t1': int(src_anchored),
            'overlap_years': ';'.join(str(y) for y in overlap),
            'source_unit': units.get(src) or '?',
            'target_unit': units.get(tgt) or '?',
            'target_gap_years': len(gaps[tgt]),
            'source_gbp': round(payload[src].get('v') or 0),
            'target_gbp': round(payload[tgt].get('v') or 0),
            'detail': ';'.join(f'{y}:{round(v)}v{round(q)}{k[-1] if k.endswith("*") else ""}'
                               for y, v, q, k in hits),
        })
    rows.sort(key=lambda r: (-r['n_exact'], -r['n_near'], -r['source_gbp']))

    with open(out_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ['source'])
        w.writeheader()
        w.writerows(rows)

    clean = [r for r in rows if not r['overlap_years'] and not r['source_has_own_t1']]
    print(f'commodities: {len(payload):,}   gap commodity-years: '
          f'{sum(len(v) for v in gaps.values()):,} in {len(gaps):,} commodities')
    print(f'candidate pairs: {len(rows)}   of which clean '
          f'(no year overlap, source has no T1 of its own): {len(clean)}')
    print(f'-> {out_path}')
    for r in clean[:25]:
        print(f"  {r['n_exact']}x exact {r['n_near']}x near  "
              f"{r['source'][:44]:<46} -> {r['target'][:44]:<46} {r['years']}")


if __name__ == '__main__':
    p = sys.argv[1] if len(sys.argv) > 1 else str(BASE / 'exports' / 'viz_payload.json')
    o = sys.argv[2] if len(sys.argv) > 2 else str(BASE / 'reports' / 'orphan_origin_matches.csv')
    main(p, o)
