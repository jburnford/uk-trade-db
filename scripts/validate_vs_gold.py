#!/usr/bin/env python3
"""Validate the Chandra-parsed abstract tables against Jim's hand-transcribed
Full British Imports Database (the gold standard; carefully single-keyed).

Matching: gold national totals (World row where present, else sum of country
rows) x (commodity, year, unit) against abstract_obs import totals. Commodity
names crosswalked by normalized text (gold names are flat, abstract names are
group:article). Values compared only where units are compatible.

Outputs match-rate + agreement stats + reports/gold_mismatches.csv.
"""
import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from statistics import median

import duckdb

BASE = Path('/home/jic823/uk_trade_db')
GOLD = "/mnt/c/Users/jic823/Dropbox/2026/Full British Imports Database.xlsx - Sheet1.csv"

UNIT_MAP = {
    'cwts (hundredweights)': 'cwts', 'lbs (pounds)': 'lbs', 'number': 'number',
    'tons': 'tons', 'gallons': 'gallons', 'qrs (quarters)': 'qrs',
    'loads': 'loads', 'bushels': 'bushels', 'great hundreds': 'great hundreds',
    'tuns (whale oil)': 'tuns', 'barrels': 'barrels', 'value': 'value',
}
ABS_UNIT = {
    'cwts': 'cwts', 'cwt': 'cwts', 'lbs': 'lbs', 'number': 'number',
    'no': 'number', 'tons': 'tons', 'gallons': 'gallons', 'galls': 'gallons',
    'qrs': 'qrs', 'quarters': 'qrs', 'loads': 'loads', 'bushels': 'bushels',
    'tuns': 'tuns', 'barrels': 'barrels', 'bls': 'barrels',
    'proof gallons': 'gallons',
}


def norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode()
    s = s.lower().replace('&', ' and ')
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    s = re.sub(r'\b(unenumerated|other sorts|all sorts|viz|etc)\b', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def norm_unit(u):
    u = re.sub(r'[.\s]+$', '', (u or '').lower().strip())
    u = re.sub(r'\.', '', u)
    return ABS_UNIT.get(u, UNIT_MAP.get(u, u))


def main():
    # ---- gold national totals
    gold = defaultdict(float)
    gold_has_world = set()
    rows = list(csv.DictReader(open(GOLD)))
    for r in rows:
        y = int(r['YEAR'])
        if not (1868 <= y <= 1898):
            continue
        key = (norm(r['COMMODITY_NAME']), y, norm_unit(r['UNIT_NAME']))
        if r['SOURCE_LOCATION_NAME'].strip() == 'World':
            gold_has_world.add(key)
            gold[key] = float(r['AMOUNT'] or 0)
        elif key not in gold_has_world:
            gold[key] += float(r['AMOUNT'] or 0)

    # ---- parsed abstract totals (median across volumes per year)
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)
    obs = con.execute("""
        SELECT coalesce(article_group || ' ', '') || article AS name,
               article, year, unit, list(value)
        FROM abstract_obs
        WHERE flow='import' AND measure='quantity' AND value IS NOT NULL
        GROUP BY 1, 2, 3, 4""").fetchall()
    parsed = {}
    for full, art, y, unit, vals in obs:
        for key_name in (norm(full), norm(art)):
            parsed[(key_name, y, norm_unit(unit))] = (median(vals),
                                                      sorted(vals), full)

    matched = agree = close = 0
    mism = []
    unmatched_gold = defaultdict(int)
    for (gname, y, gunit), gval in gold.items():
        if gval <= 0:
            continue
        hit = parsed.get((gname, y, gunit))
        if not hit:
            unmatched_gold[gname] += 1
            continue
        pval, allvals, full = hit
        matched += 1
        if abs(pval - gval) < 0.5 or any(abs(v - gval) < 0.5 for v in allvals):
            agree += 1
        elif abs(pval - gval) / max(gval, 1) < 0.005:
            close += 1
        else:
            mism.append((gname, y, gunit, gval, pval, full))

    print(f'gold national cells 1868-98: {len([1 for v in gold.values() if v > 0]):,}')
    print(f'matched to parsed DB:        {matched:,}')
    print(f'  exact agreement (any volume): {agree:,} ({agree / max(matched,1):.1%})')
    print(f'  within 0.5%:                  {close:,}')
    print(f'  disagree:                     {len(mism):,} ({len(mism) / max(matched,1):.1%})')

    out = BASE / 'reports' / 'gold_mismatches.csv'
    with open(out, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['gold_name', 'year', 'unit', 'gold_value',
                    'parsed_median', 'parsed_label'])
        for m in sorted(mism, key=lambda m: -abs(m[3] - m[4]) / max(m[3], 1)):
            w.writerow(m)
    print(f'mismatches -> {out}')
    print('\nlargest relative mismatches:')
    for m in sorted(mism, key=lambda m: -abs(m[3] - m[4]) / max(m[3], 1))[:12]:
        print(f'  {m[0][:40]:<40} {m[1]} {m[2]:<8} gold {m[3]:>14,.0f} '
              f'parsed {m[4]:>14,.0f}')
    print('\nmost-frequent unmatched gold commodities (crosswalk gaps):')
    for n, c in sorted(unmatched_gold.items(), key=lambda x: -x[1])[:12]:
        print(f'  {c:>3}x {n[:70]}')


if __name__ == '__main__':
    main()
