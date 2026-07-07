#!/usr/bin/env python3
"""Validate Tier-1 NATIONAL totals against gold — including the unexploited
early anchors 1866 and 1871.

Why: the gold data (Ghost Acres) is quinquennial 1856-1906, but the Tier-2
country-detail validation can only use 1876-96 — the country sections print
just the statement year, and the corpus starts at as_1872, so no country
detail exists for 1866/1871 at all (the scorecard's "1871: 0/336" is a
category error, not a data failure). Tier-1 national totals, however, DO
cover 1866-1900 via comparative columns — but unevenly: 1871 is a true
4-volume vote (as_1872-75), while 1866/1867 exist ONLY in tn_1871's columns
(single volume, single-keyed, no corroboration). The readings/cell column in
the report carries this distinction. tn_1901 is publication-year naming (it
holds trade of 1893-1900), so the gold 1901 anchor is out of reach.

Matching is collision-safe per the Cotton-Raw lesson: a gold commodity-year
counts as matched only when a Tier-1 article both SHARES A NAME TOKEN with
the gold commodity and lands within tolerance of the gold World total. A
bare-number match across ~1,000 articles proves nothing.

Per year, gold cells split into:
  exact (<=1%) / close (<=5%) / off (>5%, best name-matched ratio shown)
  no-name-match (no Tier-1 article shares a token — coverage gap, not error)
Matched cells are stratified by Tier-1 tier (A/B/C) to confirm the tiers
stratify accuracy. Writes reports/gold_tier1_validation.md (+ misses CSV).
"""
import csv
import re
from collections import defaultdict
from pathlib import Path

import duckdb
import validate_gold as V

BASE = Path('/home/jic823/uk_trade_db')
YEARS = [1866, 1871, 1876, 1881, 1886, 1891, 1896]
STOP = {'of', 'and', 'the', 'or', 'in', 'total', 'all', 'kinds', 'sorts',
        'other', 'unenumerated', 'none', 'from', 'to', 'not', 'for', 'raw'}


def toks(s):
    return {w for w in re.findall(r'[a-z]+', (s or '').lower())
            if w not in STOP and len(w) > 2}


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)
    V.OVERLAP = YEARS                       # widen the gold loader's window
    gcells, gworld, gunit = V.load_gold()

    # Tier-1 quantity rows: year -> [(name, toks, value, tier)]
    t1 = defaultdict(list)
    for grp, art, y, val, tier, nv in con.execute(f"""
            SELECT article_group, article, year, value, tier, n_volumes
            FROM consensus WHERE flow='import' AND measure='quantity'
              AND year IN ({','.join(map(str, YEARS))}) AND value > 0"""
            ).fetchall():
        name = f"{grp or ''} {art or ''}".strip()
        t1[int(y)].append((name, toks(name), float(val), tier, nv))

    per = defaultdict(lambda: defaultdict(int))   # year -> bucket counts
    tierhit = defaultdict(lambda: defaultdict(int))  # tier -> exact/close/off
    misses = []
    for (com, y), world in sorted(gworld.items()):
        if world <= 1000:
            continue
        gt = toks(com)
        cands = [(nm, v, tr, nv) for nm, nt, v, tr, nv in t1[y] if nt & gt]
        per[y]['gold'] += 1
        if not cands:
            per[y]['nomatch'] += 1
            misses.append((com, y, int(world), gunit.get(com, ''), 'no-name-match', ''))
            continue
        best = min(cands, key=lambda c: abs(c[1] - world) / max(c[1], world))
        ratio = best[1] / world
        err = abs(best[1] - world) / max(best[1], world)
        # >2x against a name-matched line is nearly always CATEGORY SCOPE —
        # gold transcribes finer lines than the source's summary table prints
        # (gold "Hams" vs source "Bacon and Hams"; "Calves" vs "Oxen, Bulls,
        # Cows, and Calves"; "Flint Glass" vs "Glass of all Kinds") — not a
        # misread digit. 0.5-2x is the genuine value-error zone.
        bucket = ('exact' if err <= 0.01 else 'close' if err <= 0.05
                  else 'off' if 0.5 <= ratio <= 2 else 'scope')
        per[y][bucket] += 1
        per[y]['nvol_sum'] += best[3]
        per[y]['nvol_n'] += 1
        tierhit[best[2]][bucket] += 1
        if bucket in ('off', 'scope'):
            misses.append((com, y, int(world), gunit.get(com, ''),
                           f'{bucket} ({ratio:.2f}x)', best[0]))

    lines = ['# Tier-1 national totals vs gold (incl. 1866/1871 early anchors)',
             '',
             'Gold cells matched by name-token + number (collision-safe).',
             '**scope** = best name-matched line is >2x apart: gold transcribes',
             'finer categories than the source summary prints (gold "Hams" vs',
             'source "Bacon and Hams", "Calves" vs "Oxen, Bulls, Cows, and',
             'Calves", "Flint Glass" vs "Glass of all Kinds") — a granularity',
             'difference, not a misread. **off** (0.5-2x) is the genuine',
             'value-error zone. no-name-match = coverage gap. 1896 scores',
             'highest because the late-era source prints the same fine',
             'categories gold uses.', '',
             '| year | gold cells | exact ≤1% | close ≤5% | off (0.5-2x) '
             '| scope (>2x) | no-name-match | ok% of comparable | readings/cell |',
             '|---|--:|--:|--:|--:|--:|--:|--:|--:|']
    for y in YEARS:
        d = per[y]
        g = d['gold']
        if not g:
            continue
        comparable = d['exact'] + d['close'] + d['off']
        okp = (d['exact'] + d['close']) / comparable if comparable else 0
        nv = d['nvol_sum'] / d['nvol_n'] if d['nvol_n'] else 0
        lines.append(f"| {y} | {g} | {d['exact']} | {d['close']} | {d['off']} "
                     f"| {d['scope']} | {d['nomatch']} | {okp:.0%} | {nv:.1f} |")
        print(f"{y}: {g:3} gold — exact {d['exact']:3} close {d['close']:2} "
              f"off {d['off']:3} scope {d['scope']:3} nomatch {d['nomatch']:2} "
              f"| ok {okp:.0%} of comparable | {nv:.1f} readings/cell")
    lines += ['', '## Matched cells by Tier-1 tier (do the tiers stratify?)',
              '', '| tier | exact | close | off | scope |', '|---|--:|--:|--:|--:|']
    for tr in ('A', 'B', 'C'):
        d = tierhit[tr]
        comp = d['exact'] + d['close'] + d['off']
        if comp:
            lines.append(f"| {tr} | {d['exact']} ({d['exact']/comp:.0%} of comparable) "
                         f"| {d['close']} | {d['off']} | {d['scope']} |")
            print(f"tier {tr}: exact {d['exact']}/{comp} comparable = "
                  f"{d['exact']/comp:.0%}  (+{d['scope']} scope)")

    (BASE / 'reports' / 'gold_tier1_validation.md').write_text(
        '\n'.join(lines) + '\n')
    with open(BASE / 'reports' / 'gold_tier1_misses.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['gold_commodity', 'year', 'gold_world', 'unit', 'status',
                    'best_tier1_match'])
        w.writerows(misses)
    print('-> reports/gold_tier1_validation.md, reports/gold_tier1_misses.csv')


if __name__ == '__main__':
    main()
