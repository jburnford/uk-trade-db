#!/usr/bin/env python3
"""Flag destination cells that contradict their own printed subtotal.

A member row cannot exceed the section total it is printed under. When one
does, the page and the parse disagree and one of the two numbers is wrong --
almost always the member, because the fused-digit failure mode multiplies a
single cell while leaving the subtotal intact.

This is threshold-free: no "values above GBP100M are suspicious" rule, which
would miss a corrupted cell in a small commodity and libel a genuinely large
one. The test is pure arithmetic against what the compositor printed on the
same page.

It is a flag, not a verdict. If the *subtotal* is the corrupted number the
contradiction still fires, pointing at the right block but the wrong row, so
confirm which side moved before repairing.

Usage:
    python3 scripts/detect_impossible_cells.py [--flow export_uk] [--engine obs]
        [--measure value] [--out reports/impossible_cells.csv]
"""
import argparse, collections, csv, re
import duckdb

TOTAL_RE = re.compile(r'\bTOTAL\b', re.I)
ENGINES = {'obs': 'country_obs', 'inf': 'country_obs_inf', 'twoup': 'country_obs_twoup'}
# a member may legitimately equal the subtotal (a sole destination); allow a
# hair of rounding slack before calling it a contradiction
SLACK = 1.001


def is_total(s):
    return bool(s) and bool(TOTAL_RE.search(s))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='db/uk_trade.duckdb')
    ap.add_argument('--flow', default='export_uk',
                    choices=['export_uk', 'reexport', 'import'])
    ap.add_argument('--engine', default='obs', choices=sorted(ENGINES))
    ap.add_argument('--measure', default='value', choices=['value', 'quantity'])
    ap.add_argument('--out', default='reports/impossible_cells.csv')
    a = ap.parse_args()

    tbl = ENGINES[a.engine]
    con = duckdb.connect(a.db, read_only=True)
    cols = {c[0] for c in con.execute(f'describe "{tbl}"').fetchall()}
    seq = 'row_seq' if 'row_seq' in cols else 'rowid'

    rows = con.execute(f"""
        select volume, year, coalesce(article_group,'') ag, coalesce(article,'') art,
               coalesce(unit,'') unit, {seq} seq, country_raw, {a.measure} amt
        from "{tbl}" where flow = ? order by volume, ag, art, unit, seq
    """, [a.flow]).fetchall()

    blocks = collections.defaultdict(list)
    for vol, yr, ag, art, unit, sq, ctry, amt in rows:
        blocks[(vol, yr, ag, art, unit)].append((sq, ctry, amt))

    found = []
    n_sections = 0
    for (vol, yr, ag, art, unit), rws in blocks.items():
        members = []
        for sq, label, amt in rws:
            if not is_total(label):
                if amt is not None:
                    members.append((sq, label, amt))
                continue
            if members and amt:
                n_sections += 1
                for sq2, lb, v in members:
                    if abs(v) > abs(amt) * SLACK:
                        found.append(dict(
                            volume=vol, year=yr, article_group=ag, article=art,
                            unit=unit, row_seq=sq2, country=lb,
                            cell=v, printed_subtotal=amt,
                            ratio=round(v / amt, 2) if amt else None))
            members = []

    found.sort(key=lambda r: -abs(r['ratio'] or 0))
    print(f'flow={a.flow} engine={a.engine} measure={a.measure}')
    print(f'sections examined: {n_sections:,}')
    print(f'cells exceeding their own printed subtotal: {len(found):,}')
    if found:
        fam = collections.Counter((r['volume'], r['article_group']) for r in found)
        print('\nby volume and group:')
        for (v, g), n in fam.most_common(15):
            print(f'  {n:4}  {v}  {g[:56]}')
        print('\nworst 15 by ratio:')
        for r in found[:15]:
            print(f'  x{r["ratio"]:>12,.0f}  {r["volume"]} {r["year"]}  '
                  f'{r["country"][:26]:26}  {r["article"][:40]}')
        with open(a.out, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(found[0].keys()))
            w.writeheader()
            w.writerows(found)
        print(f'\nwrote {a.out}')


if __name__ == '__main__':
    main()
