#!/usr/bin/env python3
"""Internal arithmetic validation: printed subtotal rows vs the sum of their
group's sub-articles, within each volume/flow/measure/year.

The Annual Statement value tables print a 'Total' row under multi-line
groups (e.g. Iron group -> Total). Where OCR read every cell correctly,
sum(sub-articles) == printed Total exactly. A mismatch localizes an error
to one group in one volume — and the amount of the discrepancy often
identifies WHICH cell is wrong (difference = digit-slip delta).

Quantities are checked only when all group members share one unit.
"""
from collections import defaultdict
from pathlib import Path

import duckdb

BASE = Path('/home/jic823/uk_trade_db')
TOL = 0.5


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)
    rows = con.execute("""
        SELECT volume, flow, measure, article_group, article, unit, year, value
        FROM abstract_obs
        WHERE article_group IS NOT NULL""").fetchall()

    # value NULL = the cell printed but didn't parse (raw_unparsed): the
    # group's sum is incomplete, so its subtotal check would false-fail
    # (Cotton Manufactures: two unparsed Piece Goods rows hid 50M GBP)
    groups = defaultdict(list)
    incomplete = set()
    for vol, flow, meas, grp, art, unit, y, v in rows:
        if v is None:
            incomplete.add((vol, flow, meas, grp, y))
        else:
            groups[(vol, flow, meas, grp, y)].append((art, unit, v))

    n_check = n_ok = n_bad = 0
    bad = []
    for key, members in groups.items():
        totals = [m for m in members
                  if m[0].strip("'\" ").lower().startswith('total')]
        subs = [m for m in members
                if not m[0].strip("'\" ").lower().startswith('total')]
        if len(totals) != 1 or len(subs) < 2 or key in incomplete:
            continue
        vol, flow, meas, grp, y = key
        sub_units = {u for _, u, _ in subs if u}
        tot_unit = totals[0][1]
        if meas == 'quantity':
            if len(sub_units) > 1:
                continue
            # unit-aware: quantity tables print value-only members and value
            # totals under mixed groups (Cotton Manufactures: yards members,
            # "Value £" total) — a yards-sum vs a £-total is a false
            # failure, not an OCR error
            if tot_unit and sub_units and tot_unit not in sub_units:
                continue
            if any('value' in (u or '').lower()
                   for u in sub_units | {tot_unit or ''}):
                continue
        n_check += 1
        s = sum(v for _, _, v in subs)
        t = totals[0][2]
        if abs(s - t) <= TOL:
            n_ok += 1
        else:
            n_bad += 1
            bad.append((vol, flow, meas, grp, y, t, s, s - t))

    print(f'group-subtotal checks: {n_check:,}')
    print(f'  exact: {n_ok:,} ({n_ok / max(n_check, 1):.1%})')
    print(f'  mismatch: {n_bad:,}')
    print('\nlargest mismatches (printed total vs sum; delta):')
    for b in sorted(bad, key=lambda b: -abs(b[7]) / max(b[5], 1))[:15]:
        print(f'  {b[0]} {b[1]}/{b[2]} {b[4]} {b[3][:38]:<38} '
              f'total {b[5]:>13,.0f} sum {b[6]:>13,.0f} Δ {b[7]:>+12,.0f}')

    # how often does the same group/year check out in OTHER volumes?
    # (localizes error to one printing vs a systematic parse problem)
    byg = defaultdict(list)
    for b in bad:
        byg[(b[1], b[2], b[3], b[4])].append(b[0])
    multi = {k: v for k, v in byg.items() if len(v) >= 2}
    print(f'\nmismatching group-years appearing in >=2 volumes '
          f'(suggests parse issue, not print/OCR): {len(multi)} '
          f'of {len(byg)}')


if __name__ == '__main__':
    main()
