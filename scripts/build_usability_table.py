#!/usr/bin/env python3
"""Per-commodity usability table: how far each commodity can be trusted.

Two honest signals per commodity, both built to be collision-resistant, checked
against the independent Ghost Acres gold data at the five gold overlap years:

  TOTAL      — is the national total right? A pipeline commodity-year whose total
               lands within 5% of gold AND that shares a NAME token with the gold
               commodity. The name gate matters: matching a bare total is NOT
               collision-safe (Cotton Raw's total coincides with Barley, Sheep-
               skins, even Raisins), and that false positive is what wrecked trust
               in the first cut. Requiring a shared word kills the coincidences
               while still allowing the legitimate case.
  BY-COUNTRY — do the total AND the largest origin BOTH match (the numeric
               fingerprint)? Two independent numbers is collision-resistant on its
               own. Stricter than TOTAL, and can miss when the pipeline aggregates
               origins coarser than gold (wool -> "Australasia" vs gold's per-state
               NSW/Victoria) even though the national series is fine — hence the
               two signals disagree exactly where that happens.

Identity (which pipeline article this is) is pinned from the matches, tie-broken
toward real name overlap so a numeric coincidence (Sugar Refined ~ Cheese) can't
win the label. Tier from reproduced years:
  SOLID   >=3 gold years, reproduces ALL             MOSTLY  all but one
  MIXED   some         WEAK  <= half         SPARSE  <2 years to judge
  UNVERIFIED  identity never independently confirmed -> can't vouch for it

Rule of thumb: trust a national series when TOTAL is SOLID/MOSTLY; trust its
by-country split only when BY-COUNTRY is too. A WEAK by-country with a strong
TOTAL usually means coarser-than-gold origins, not wrong data — eyeball it.
Wood/timber is validated separately (26/26 country cells exact) and not re-graded.

Writes exports/commodity_usability.csv. ADVICE table — nothing in the DB changes.
"""
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

import duckdb
import validate_gold as V
from validate_gold_numeric import load_pipeline_vectors, YEARS

BASE = Path('/home/jic823/uk_trade_db')
TOL = 0.05
STOP = {'of', 'and', 'the', 'or', 'in', 'total', 'all', 'kinds', 'sorts',
        'other', 'unenumerated', 'none', 'from', 'to', 'not', 'for'}


def toks(s):
    return {w for w in re.findall(r'[a-z]+', (s or '').lower())
            if w not in STOP and len(w) > 2}


def tier(n_years, n_repro):
    if n_years < 2:
        return 'SPARSE'
    if n_years >= 3 and n_repro == n_years:
        return 'SOLID'
    if n_years >= 3 and n_repro == n_years - 1:
        return 'MOSTLY'
    if n_repro <= n_years / 2:
        return 'WEAK'
    return 'MIXED'


def matches(y, gv, gtot, gtoks, by_year, tol):
    """Two lists of pipeline names in year y: (total-only + name-token overlap)
    and (total + largest-origin fingerprint)."""
    gtop = max(gv.values()) if gv else 0
    tot_ok, att_ok = [], []
    for name, ptot, pv in by_year[y]:
        if abs(ptot - gtot) > tol * max(ptot, gtot):
            continue
        if toks(name) & gtoks:
            tot_ok.append(name)                      # total right, same commodity
        if not gtop or any(abs(p - gtop) <= (tol + 0.03) * max(p, gtop)
                           for p in pv[:3]):
            att_ok.append(name)                      # total + largest origin
    return tot_ok, att_ok


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)
    gcells, gworld, gunit = V.load_gold()
    by_year = load_pipeline_vectors(con)

    rows = []
    for com in {c for c, _ in gcells}:
        years = {}
        for y in YEARS:
            gv = gcells.get((com, y))
            if gv is None:
                continue
            gtot = gworld.get((com, y)) or sum(gv.values())
            if gtot > 1000:
                years[y] = (gv, gtot)
        if not years:
            continue
        n = len(years)
        gt_toks = toks(com)
        gmax = int(max(gt for _, gt in years.values()))
        benchmark = ';'.join(map(str, sorted(years)))

        tot_c, att_c = {}, {}
        for y, (gv, gt) in years.items():
            tot_c[y], att_c[y] = matches(y, gv, gt, gt_toks, by_year, TOL)
        votes = Counter(nm for names in list(tot_c.values()) + list(att_c.values())
                        for nm in names)
        if not votes:
            rows.append({
                'gold_commodity': com, 'unit': gunit.get(com, ''),
                'total_tier': 'UNVERIFIED', 'bycountry_tier': 'UNVERIFIED',
                'gold_years': n, 'benchmark_years': benchmark,
                'total_ok_years': '', 'bycountry_ok_years': '',
                'gold_peak_total': gmax, 'pipeline_match': ''})
            continue
        anchor = max(votes, key=lambda nm: (len(toks(nm) & gt_toks), votes[nm]))
        tot_y = sorted(y for y in years if anchor in tot_c[y])
        att_y = sorted(y for y in years if anchor in att_c[y])
        rows.append({
            'gold_commodity': com, 'unit': gunit.get(com, ''),
            'total_tier': tier(n, len(tot_y)),
            'bycountry_tier': tier(n, len(att_y)),
            'gold_years': n, 'benchmark_years': benchmark,
            'total_ok_years': ';'.join(map(str, tot_y)),
            'bycountry_ok_years': ';'.join(map(str, att_y)),
            'gold_peak_total': gmax, 'pipeline_match': anchor.rstrip('|')})

    order = {'SOLID': 0, 'MOSTLY': 1, 'MIXED': 2, 'WEAK': 3, 'SPARSE': 4,
             'UNVERIFIED': 5}
    rows.sort(key=lambda r: (order[r['total_tier']], order[r['bycountry_tier']],
                             -r['gold_peak_total']))

    out = BASE / 'exports' / 'commodity_usability.csv'
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    tot = Counter(r['total_tier'] for r in rows)
    att = Counter(r['bycountry_tier'] for r in rows)
    print(f'commodity_usability.csv: {len(rows)} commodities')
    print(f'  {"tier":11} {"TOTAL":>6} {"BY-COUNTRY":>11}')
    for t in ('SOLID', 'MOSTLY', 'MIXED', 'WEAK', 'SPARSE', 'UNVERIFIED'):
        print(f'  {t:11} {tot[t]:>6} {att[t]:>11}')
    print(f'-> {out}')


if __name__ == '__main__':
    main()
