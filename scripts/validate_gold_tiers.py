#!/usr/bin/env python3
"""Validate the consensus table against Jim's hand-keyed Full British
Imports Database, stratified by confidence tier. Confirms the tiers
calibrate (A should be near-perfect) after reconciliation changes.

Matching mirrors validate_vs_gold.py: gold national totals (World row where
present, else country sum) x (commodity, year, unit) against consensus
import-quantity series, names crosswalked by normalized text.
"""
import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

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


def norm(s, loose=False):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode()
    s = s.lower().replace('&', ' and ')
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    if loose:
        # only true filler: "unenumerated"/"other sorts" name a residual
        # sub-series, not the total — stripping them matched gold
        # "Hewn Unenumerated" to the consensus parent "Hewn" (30x apart)
        s = re.sub(r'\b(all sorts|viz|etc)\b', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def norm_unit(u):
    u = re.sub(r'[.\s]+$', '', (u or '').lower().strip())
    u = re.sub(r'\.', '', u)
    return ABS_UNIT.get(u, UNIT_MAP.get(u, u))


def main():
    # gold national totals keyed by raw commodity name
    gold = defaultdict(float)
    gold_has_world = set()
    for r in csv.DictReader(open(GOLD)):
        y = int(r['YEAR'])
        if not (1868 <= y <= 1898):
            continue
        key = (r['COMMODITY_NAME'].strip(), y, norm_unit(r['UNIT_NAME']))
        if r['SOURCE_LOCATION_NAME'].strip() == 'World':
            gold_has_world.add(key)
            gold[key] = float(r['AMOUNT'] or 0)
        elif key not in gold_has_world:
            gold[key] += float(r['AMOUNT'] or 0)

    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)
    rows = con.execute("""
        SELECT article_group, article, year, unit, value, tier
        FROM consensus
        WHERE flow='import' AND measure='quantity'""").fetchall()

    # 4 lookup levels, strictest first: strict norm before loose norm
    # (loose strips "other sorts" etc. and can collide sub-series onto their
    # parent), full group+article name before bare article. Gold and
    # consensus keys colliding at a level make it unusable for that key.
    levels = []
    for loose in (False, True):
        for use_full in (True, False):
            gd, cd = defaultdict(set), defaultdict(dict)
            levels.append((gd, cd, loose, use_full))
    for (gname, y, gunit) in gold:
        for gd, cd, loose, _ in levels:
            gd[(norm(gname, loose), y, gunit)].add(gname)
    for grp, art, y, unit, val, tier in rows:
        full = f'{grp} {art}' if grp else art
        u = norm_unit(unit)
        for gd, cd, loose, use_full in levels:
            key = (norm(full if use_full else art, loose), y, u)
            cd[key][norm(full)] = (val, tier)

    stats = defaultdict(lambda: [0, 0])   # tier -> [matched, exact]
    mism = []
    for (gname, y, gunit), gval in gold.items():
        if gval <= 0:
            continue
        hit = None
        for gd, cd, loose, _ in levels:
            key = (norm(gname, loose), y, gunit)
            if len(gd.get(key, ())) > 1:
                continue                     # gold-side collision
            series = cd.get(key, {})
            if len(series) == 1:
                hit = next(iter(series.values()))
                break
        if not hit:
            continue
        val, tier = hit
        stats[tier][0] += 1
        if abs(val - gval) < 0.5:
            stats[tier][1] += 1
        else:
            mism.append((tier, gname, y, gunit, gval, val))

    tot_m = sum(m for m, _ in stats.values())
    tot_e = sum(e for _, e in stats.values())
    print(f'gold cells matched to consensus: {tot_m:,}  '
          f'exact {tot_e:,} ({tot_e / max(tot_m, 1):.1%})')
    for t in 'ABC':
        m, e = stats[t]
        print(f'  tier {t}: {m:4,} matched, exact {e:4,} ({e / max(m, 1):.1%})')
    print('\ndisagreements (worst relative first):')
    for t, gn, y, gu, gv, cv in sorted(
            mism, key=lambda m: -abs(m[4] - m[5]) / max(m[4], 1))[:15]:
        print(f'  [{t}] {gn[:38]:<38} {y} {gu:<8} '
              f'gold {gv:>14,.0f} consensus {cv:>14,.0f}')


if __name__ == '__main__':
    main()
