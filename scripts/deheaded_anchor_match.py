#!/usr/bin/env python3
"""Find abstract rows that lost their group head and became their own commodity.

Round 41's shape. The payload names a commodity `GROUP — ARTICLE`. When the
abstract row's group heading is lost, the article alone becomes the name — so
`Oil — Olive` acquires a shadow called `Olive`, `Caoutchouc — Manufactures Of`
one called `Manufactures Of`. The shadow carries the printed national totals and
**no country cells at all**; the real label carries the countries.

Measured on a 1,987-commodity payload: **381 such labels holding 3,263
commodity-years**, which is 56% of every remaining "no origin data" year in the
corpus. They are not a long tail; they are the largest single block left.

The relationship is structural, not numeric, so this looks for it structurally:
a candidate is any commodity whose name ends with `— <the shadow's name>`. That
is the de-heading operation run backwards, and it does not require the countries
to sum to anything — which matters, because a reunion is worth making even where
the origin table is incomplete.

Two outcomes, and they want opposite treatment:

  REUNION   the counterpart has NO anchor of its own. Two halves of one line;
            folding the shadow into it ADDS measured years. Round 41 did three.

  DUPLICATE the counterpart HAS its own anchor. The same printed line reached
            the payload twice and the shadow is a phantom that publishes a
            national total it cannot substantiate. Folding it away removes a
            series that was never real.

**DUPLICATE folds shrink `reconcile_baseline`'s denominator.** Removing a
phantom's years raises every percentage without a single number improving, so
the two kinds must be counted and reported separately. This tool prints the
denominator effect so it cannot be taken silently.

Usage: python3 scripts/deheaded_anchor_match.py [payload.json] [out.csv]
"""
import csv
import json
import sys
from pathlib import Path

BASE = Path('/home/jic823/uk_trade_db')
TK = '§TOTAL'


def profile(entry):
    c = entry.get('c') or {}
    t1 = c.get(TK)
    unit, t1y = None, {}
    if t1:
        unit = max(t1, key=lambda u: len(t1[u]))
        t1y = {r[0]: r[1] for r in t1[unit] if r[1]}
    ctys = [k for k in c if k != TK and '(' not in k]
    return t1y, unit, ctys, c


def main(payload_path, out_path):
    payload = json.load(open(payload_path))
    prof = {n: profile(e) for n, e in payload.items()}

    shadows = {n: p for n, p in prof.items() if p[0] and not p[2]}
    rows = []
    for name, (t1y, unit, _, _) in shadows.items():
        suffix = f'— {name}'
        for cand, (ct1, cunit, cctys, cc) in prof.items():
            if cand == name or not cand.endswith(suffix) or not cctys:
                continue
            # how the shadow's anchor compares with the candidate's countries
            org = {}
            for cty, byu in cc.items():
                if cty == TK or '(' in cty:
                    continue
                for u, cells in byu.items():
                    if unit and u != unit:
                        continue
                    for r in cells:
                        if r[1]:
                            org[r[0]] = org.get(r[0], 0) + r[1]
            both = sorted(set(t1y) & set(org))
            exact = sum(1 for y in both if round(org[y]) == t1y[y])
            near = sum(1 for y in both
                       if round(org[y]) != t1y[y]
                       and abs(org[y] - t1y[y]) <= 0.001 * t1y[y])
            rows.append({
                'shadow': name,
                'shadow_t1_years': len(t1y),
                'shadow_unit': unit or '?',
                'shadow_gbp': round(payload[name].get('v') or 0),
                'counterpart': cand,
                'kind': 'duplicate' if ct1 else 'reunion',
                'counterpart_gbp': round(payload[cand].get('v') or 0),
                'counterpart_countries': len(cctys),
                'overlap_years': len(both),
                'exact': exact, 'near': near,
                'unit_agrees': int(bool(unit) and (cunit == unit or not cunit)),
            })
    rows.sort(key=lambda r: (r['kind'], -r['exact'], -r['shadow_t1_years']))

    with open(out_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ['shadow'])
        w.writeheader()
        w.writerows(rows)

    matched = {r['shadow'] for r in rows}
    reunion = [r for r in rows if r['kind'] == 'reunion']
    dup = [r for r in rows if r['kind'] == 'duplicate']
    dup_years = sum(prof[s][0] and len(prof[s][0]) for s in {r['shadow'] for r in dup})
    print(f'anchor-only labels: {len(shadows)}   holding '
          f'{sum(len(p[0]) for p in shadows.values()):,} commodity-years')
    print(f'  with a structural counterpart: {len(matched)}')
    print(f'  REUNION rows (counterpart has no anchor):   {len(reunion)}')
    print(f'  DUPLICATE rows (counterpart has an anchor): {len(dup)}')
    print(f'  -- folding every DUPLICATE would remove ~{dup_years:,} '
          f'commodity-years from reconcile_baseline\'s DENOMINATOR.')
    print(f'     Report that separately: a smaller denominator raises every')
    print(f'     percentage without one number getting better.')
    print(f'-> {out_path}')
    for r in reunion[:20]:
        print(f"  reunion  {r['exact']:>2}e/{r['near']:>2}n  "
              f"{r['shadow'][:34]:<36} + {r['counterpart'][:44]:<46} "
              f"{r['shadow_t1_years']:>2}y")


if __name__ == '__main__':
    p = sys.argv[1] if len(sys.argv) > 1 else str(BASE / 'exports' / 'viz_payload.json')
    o = sys.argv[2] if len(sys.argv) > 2 else str(BASE / 'reports' / 'deheaded_anchors.csv')
    main(p, o)
