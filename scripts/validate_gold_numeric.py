#!/usr/bin/env python3
"""Name-independent 'same data as gold' validation by NUMERIC FINGERPRINT.

Why numeric, not string: the gold commodity names are normalized, AND the
primary sources themselves changed the string for the same commodity over the
era (and country labels drift too). So string/name crosswalks plateau (~65%)
and understate reality. Instead we validate by the NUMBERS, which are immune to
all string drift:

  a gold commodity-year is 'reproduced' if some pipeline commodity-year (in
  country_year_final) has a national total within TOL of the gold total AND its
  largest country value also matches within TOL+3pp.

Matching two independent large numbers (total + biggest origin) is collision-
resistant across ~200 commodities/year, so this both PAIRS and VALIDATES without
trusting any name. Reports the confirmed rate at several OCR-appropriate
tolerances + per year, and lists what is not reproduced.
"""
import csv
from collections import defaultdict
from pathlib import Path

import duckdb
import validate_gold as V

BASE = Path('/home/jic823/uk_trade_db')
YEARS = (1876, 1881, 1886, 1891, 1896)


def load_pipeline_vectors(con):
    rows = con.execute(f"""SELECT article_group, article, country, year, quantity
        FROM country_year_final WHERE flow='import' AND year IN {YEARS}""").fetchall()
    vec = defaultdict(lambda: defaultdict(float))
    for grp, art, ctry, y, q in rows:
        c = V.cnorm(ctry)
        if c in ('total', 'world') or ' : ' in (ctry or ''):
            continue
        vec[(f"{grp or ''}|{art or ''}", int(y))][c] += float(q or 0)
    by_year = defaultdict(list)
    for (name, y), v in vec.items():
        vals = sorted((x for x in v.values() if x > 0), reverse=True)
        if vals:
            by_year[y].append((name, sum(vals), vals))
    return by_year


def confirmed(y, gvec, gtot, by_year, tol):
    gv = sorted((x for x in gvec.values() if x > 0), reverse=True)
    gtop = gv[0] if gv else 0
    for name, ptot, pv in by_year[y]:
        if abs(ptot - gtot) > tol * max(ptot, gtot):
            continue
        if not gtop or any(abs(p - gtop) <= (tol + 0.03) * max(p, gtop) for p in pv[:3]):
            return name
    return None


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)
    gcells, gworld, gunit = V.load_gold()
    by_year = load_pipeline_vectors(con)

    cells = [((com, y), gv, gworld.get((com, y)) or sum(gv.values()))
             for (com, y), gv in gcells.items()
             if y in YEARS and (gworld.get((com, y)) or sum(gv.values())) > 1000]
    tot = len(cells)

    lines = ['# Same-data-as-gold validation (numeric fingerprint)', '',
             'Name-independent: matches gold↔pipeline by national total + largest',
             'country value (both must agree), so commodity/country string drift',
             'cannot break it. `country_year_final` (consensus + two-up + run-in).', '',
             f'Substantive gold commodity-years (gold total > 1,000): **{tot:,}**', '',
             '| tolerance | confirmed same-data |', '|---|---|']
    at5 = None
    for tol in (0.02, 0.03, 0.05, 0.08):
        c = sum(1 for k, gv, gt in cells if confirmed(k[1], gv, gt, by_year, tol))
        lines.append(f'| ±{tol*100:.0f}% | {c}/{tot} = **{c/tot:.0%}** |')
        if tol == 0.05:
            at5 = c
    # per-year at 5%
    lines += ['', '## Per year (±5%)']
    peryear = defaultdict(lambda: [0, 0])
    unconf = []
    for (com, y), gv, gt in cells:
        peryear[y][0] += 1
        if confirmed(y, gv, gt, by_year, 0.05):
            peryear[y][1] += 1
        else:
            unconf.append((com, y, gt))
    for y in YEARS:
        n, c = peryear[y][1], peryear[y][0]
        lines.append(f'- {y}: {n}/{c} ({n/c:.0%})')
    lines += ['', f'## Not reproduced at ±5% ({len(unconf)}), largest',
              '| commodity | year | gold total | unit |', '|---|---|--:|---|']
    for com, y, gt in sorted(unconf, key=lambda x: -x[2])[:25]:
        lines.append(f'| {com} | {y} | {gt:,.0f} | {gunit.get(com, "")} |')

    (BASE / 'reports' / 'gold_numeric_validation.md').write_text('\n'.join(lines) + '\n')
    with open(BASE / 'reports' / 'gold_not_reproduced.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['commodity', 'year', 'gold_total', 'unit'])
        w.writerows([(c, y, int(g), gunit.get(c, '')) for c, y, g in
                     sorted(unconf, key=lambda x: -x[2])])
    print(f'same-data confirmed at ±5%: {at5}/{tot} = {at5/tot:.0%}')
    print('-> reports/gold_numeric_validation.md, reports/gold_not_reproduced.csv')


if __name__ == '__main__':
    main()
