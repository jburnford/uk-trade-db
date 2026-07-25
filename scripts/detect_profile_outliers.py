#!/usr/bin/env python3
"""Flag years whose origins do not belong to the commodity.

The impossible-origin filter in build_map_slim only fires where there is a
Tier-1 anchor to measure a cell against, so a whole block of foreign cells
glued into an un-anchored year passes untouched. Teak in 1873 is the case that
prompted this: the year reads 138,645 loads against ~30,000 either side, and
the extra is Canada 61,599, Sweden 10,487, Russia 8,349, Norway 7,103 - the
hewn-unenumerated softwood trade, not teak, which ships from Burma and Siam.

A commodity's origins are stable: teak comes from the same handful of places
every year. So build each commodity's PROFILE - the origins carrying most of
its quantity across all years - and flag a year whose quantity comes mostly
from outside it. What the year has in common with itself matters more than any
single cell's size, which is why this catches blocks that per-cell tests miss.

Two guards against false alarms:
  - the profile is built from the OTHER years, so a year cannot vote itself in
    and a commodity with only a few years is skipped entirely;
  - a genuine trade shift (a new supplier arriving and staying) shows up in
    several consecutive years, so a year is only flagged when the intruding
    origins appear in that year ALONE.

One row per intruding cell, so build_map_slim can suppress exactly those from
the map the way it already suppresses impossible origins. The payload itself
is left alone: the repair belongs in the source tables.
"""
import json, sys, csv, collections

PAY = 'exports/viz_payload.json'
OUT = 'reports/origin_profile_outliers.csv'
MIN_YEARS = 5             # fewer, and "the other years" is not a profile
SHARE = 0.5               # majority of the year's quantity from outside it
MIN_QTY = 500             # ignore trivia


def main(path=PAY, out=OUT):
    p = json.load(open(path))
    rows = []
    for n, e in p.items():
        byyear = collections.defaultdict(dict)     # year -> {origin: qty}
        for c, byu in (e.get('c') or {}).items():
            if c == '§TOTAL':
                continue
            for u, ser in byu.items():
                for y, q, *_ in ser:
                    if q:
                        byyear[y][c] = byyear[y].get(c, 0) + q
        if len(byyear) < MIN_YEARS:
            continue
        years_of = collections.Counter()
        for y, d in byyear.items():
            for c in d:
                years_of[c] += 1
        for y, d in byyear.items():
            tot = sum(d.values())
            if tot < MIN_QTY:
                continue
            # profile = origins this commodity uses in some OTHER year
            outside = {c: q for c, q in d.items() if years_of[c] == 1}
            share = sum(outside.values()) / tot
            if share < SHARE or not outside:
                continue
            for c, q in sorted(outside.items(), key=lambda kv: -kv[1]):
                rows.append(dict(commodity=n, year=y, origin=c,
                                 qty=round(q), year_qty=round(tot),
                                 outside_share=round(share, 2),
                                 n_outside=len(outside),
                                 gbp=int(e.get('v') or 0)))
    rows.sort(key=lambda r: (-r['gbp'], r['year'], -r['qty']))
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    ny = len({(r['commodity'], r['year']) for r in rows})
    print(f'{ny} commodity-years ({len(rows)} cells) whose origins are foreign '
          f'to the commodity -> {out}')
    seen = set()
    for r in rows:
        k = (r['commodity'], r['year'])
        if k in seen:
            continue
        seen.add(k)
        if len(seen) > 15:
            break
        print(f'  {r["gbp"]:>12,} {r["year"]}  {r["outside_share"]:.0%} of '
              f'{r["year_qty"]:>9,}  {r["commodity"][:34]:34s} '
              f'{r["origin"][:26]}:{r["qty"]:,}')


if __name__ == '__main__':
    main(*sys.argv[1:])
