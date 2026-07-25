#!/usr/bin/env python3
"""Value-column closure, as a first-class metric beside quantity.

Every block in the Abstract prints TWO columns and TWO printed totals, and
until now only the quantity one was ever tested. That leaves a whole class
invisible: margarine 1899's quantity closes to the digit while its value
column overshoots its printed total by GBP19,492, because a single misread
digit in a value cell changes no quantity.

The two columns are independent tests of the same block, so the interesting
signal is where they DISAGREE — a year that closes on quantity and not on
value has a value-column digit error, and the row to look at is the one whose
unit price is out of line with its neighbours (see within_block_price.py).

Reads exports/map_data.json, whose §TOTAL cells carry the printed national
value on their 4th element.

    python3 scripts/value_closure.py [--family oil,tallow,lard]

  -> reports/value_closure.csv
"""
import collections
import csv
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def modal_unit_series(t1):
    """The quantity anchor reconcile_baseline uses: modal unit, junk clamped."""
    units = {u: len(v) for u, v in t1.items()}
    if not units:
        return None, {}
    unit = max(units, key=units.get)
    vals = [row[1] for row in t1[unit] if row[1]]
    if not vals:
        return unit, {}
    med = sorted(vals)[len(vals) // 2]
    years = {}
    for row in t1[unit]:
        y, q = row[0], row[1]
        if q and not (med and q > 30 * med):
            years[y] = q
    return unit, years


def bucket(got, want):
    if not got:
        return 'nodata'
    d = abs(got - want) / want
    return ('exact01' if d <= 0.001 else 'within5' if d <= 0.05 else
            'under' if got < want else 'over')


def main():
    fam = None
    if '--family' in sys.argv:
        fam = [s.strip().lower()
               for s in sys.argv[sys.argv.index('--family') + 1].split(',')]

    payload = json.load(open(BASE / 'exports' / 'map_data.json'))
    rows, tot, gbp = [], collections.Counter(), collections.Counter()

    for name, entry in payload.items():
        if fam and not any(f in name.lower() for f in fam):
            continue
        c = entry.get('c') or {}
        t1 = c.get('§TOTAL')
        if not t1:
            continue
        # printed national VALUE per year (unit-independent: the same number
        # rides every unit's §TOTAL cell for that year)
        t1v = {}
        for unit, series in t1.items():
            for row in series:
                if len(row) > 3 and row[3]:
                    t1v.setdefault(row[0], row[3])
        if not t1v:
            continue
        # same junk clamp the quantity anchor gets: a value line 30x its own
        # median is an OCR run-together, not a year ('Hats Or Bonnets — Of
        # Felt' 1894 reads GBP64.9 BILLION and would otherwise carry three
        # quarters of the GBP weight on its own)
        vv = sorted(t1v.values())
        vmed = vv[len(vv) // 2]
        t1v = {y: v for y, v in t1v.items() if not (vmed and v > 30 * vmed)}
        if not t1v:
            continue
        qunit, t1q = modal_unit_series(t1)

        vsum = collections.Counter()
        qsum = collections.Counter()
        norig = collections.Counter()
        for ctry, byunit in c.items():
            if ctry == '§TOTAL' or '(' in ctry:
                continue
            for unit, series in byunit.items():
                for row in series:
                    y = row[0]
                    if len(row) > 3 and row[3] and y in t1v:
                        vsum[y] += row[3]
                        norig[y] += 1
                    if unit == qunit and row[1] and y in t1q:
                        qsum[y] += row[1]

        # Some printings put the quantity figure in the abstract's value
        # column and the vote copies it faithfully (flax and linseed 1885 is
        # its own quantity line, 2,046,352, in six volumes). Such a year is
        # not a failing test, it is an absent one — left in, it reports a
        # sound block as 2.14x its total. Tested on the commodity's own
        # price, so goods that genuinely cost about a pound a unit are safe.
        prices = sorted(vsum[y] / qsum[y] for y in qsum
                        if qsum[y] and vsum[y])
        if prices:
            price = prices[len(prices) // 2]
            if not 0.9 <= price <= 1.1:
                t1v = {y: v for y, v in t1v.items()
                       if not (t1q.get(y) and abs(v - t1q[y]) <= 0.01 * t1q[y])}

        for y, tv in sorted(t1v.items()):
            b = bucket(vsum[y], tv)
            tot[b] += 1
            gbp[b] += tv
            qb = bucket(qsum[y], t1q[y]) if y in t1q else 'noanchor'
            rows.append({
                'commodity': name, 'year': y,
                't1_value': round(tv), 'origin_value': round(vsum[y]),
                'v_ratio': round(vsum[y] / tv, 4) if tv else '',
                'v_bucket': b,
                't1_qty': round(t1q.get(y, 0)), 'origin_qty': round(qsum[y]),
                'q_ratio': (round(qsum[y] / t1q[y], 4)
                            if t1q.get(y) else ''),
                'q_bucket': qb, 'unit': qunit or '',
                'n_origins': norig[y],
                'split': ('VALUE-ONLY-DEFECT'
                          if qb == 'exact01' and b in ('under', 'over')
                          else 'QTY-ONLY-DEFECT'
                          if b == 'exact01' and qb in ('under', 'over')
                          else ''),
            })

    rows.sort(key=lambda r: (not r['split'], -r['t1_value']))
    out = BASE / 'reports' / 'value_closure.csv'
    with open(out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    n = sum(tot.values()) or 1
    G = sum(gbp.values()) or 1
    print(f'commodity-years with a printed national VALUE: {n:,}  '
          f'(GBP {G:,.0f})')
    for b in ('exact01', 'within5', 'under', 'over', 'nodata'):
        print(f'  {b:8s}: {tot[b]:6,} ({100*tot[b]/n:5.1f}%)   '
              f'GBP-weighted {100*gbp[b]/G:5.1f}%')
    print(f'  within 0.1%: {100*tot["exact01"]/n:.1f}% of commodity-years, '
          f'{100*gbp["exact01"]/G:.1f}% GBP-weighted')
    print(f'  within 5%  : {100*(tot["exact01"]+tot["within5"])/n:.1f}% of '
          f'commodity-years, {100*(gbp["exact01"]+gbp["within5"])/G:.1f}% '
          f'GBP-weighted')
    vo = [r for r in rows if r['split'] == 'VALUE-ONLY-DEFECT']
    qo = [r for r in rows if r['split'] == 'QTY-ONLY-DEFECT']
    print(f'quantity closes to the digit but value does NOT: {len(vo):,} '
          f'(GBP {sum(r["t1_value"] for r in vo):,})')
    print(f'value closes to the digit but quantity does NOT: {len(qo):,} '
          f'(GBP {sum(r["t1_value"] for r in qo):,})')
    for r in vo[:15]:
        print(f'  GBP{r["t1_value"]:>11,}  {r["year"]}  {r["commodity"][:50]:52s}'
              f' v {r["v_ratio"]}')
    print(f'-> {out}  ({len(rows):,} rows)')


if __name__ == '__main__':
    main()
