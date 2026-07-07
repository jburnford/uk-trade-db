#!/usr/bin/env python3
"""Validate country_obs (Tier 2) two ways:

1. Internal arithmetic: within each printed block, sum(country rows) must
   equal the printed 'Total' row — for quantity and value independently.
   Port-breakdown rows ("United States of America : On the Atlantic") are
   excluded from block sums (their country's total row carries the value).
   Blocks are consumed sequentially in row_seq order; a 'Total' closes one.

2. Wood reference test: country-level wood imports vs Jim's hand-keyed
   decennial Full British Imports Database at 1871/1881/1891 (national wood
   totals already validate digit-perfect, so country rows should too).

Writes reports/country_block_flags.csv (blocks failing the arithmetic).
"""
import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import duckdb

BASE = Path('/home/jic823/uk_trade_db')
GOLD = "/mnt/c/Users/jic823/Dropbox/2026/Full British Imports Database.xlsx - Sheet1.csv"


def norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode()
    s = s.lower().replace('&', ' and ')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', s)).strip()


# UK statements name vs gold-DB name (gold modernizes some)
GOLD_COUNTRY = {
    'british north america': 'canada',
    'russia northern ports': 'russia', 'russia southern ports': 'russia',
    'sweden and norway': 'sweden and norway',
    'united states of america': 'united states of america',
}


def main():
    import sys
    table = sys.argv[1] if len(sys.argv) > 1 else 'country_obs'
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)
    print(f'validating table: {table}')
    rows = con.execute(f"""
        SELECT volume, flow, duty, article_group, article, country_raw,
               unit, year, quantity, value
        FROM {table} ORDER BY volume, flow, duty, row_seq""").fetchall()

    # ---- 1. block arithmetic
    stats = defaultdict(lambda: [0, 0, 0])   # volume -> [exact, small, big]
    flags = []
    sq = sv = 0.0
    n = 0
    prev = None
    for vol, flow, duty, grp, art, ctry, unit, y, q, v in rows:
        key = (vol, flow, duty, grp, art)
        if key != prev:
            sq = sv = 0.0
            n = 0
            prev = key
        if ctry == 'TOTAL':
            if n >= 2:
                worst = 0.0
                for tot, s in ((v, sv), (q, sq)):
                    if tot and tot > 0 and s > 0:
                        worst = max(worst, abs(s - tot) / tot)
                if worst < 1e-9:
                    stats[vol][0] += 1
                elif worst < 0.02:
                    stats[vol][1] += 1
                else:
                    stats[vol][2] += 1
                if worst >= 1e-9:
                    flags.append([vol, flow, duty, grp, art, y,
                                  q, sq, v, sv, f'{worst:.4f}'])
            sq = sv = 0.0
            n = 0
        elif ' : ' not in (ctry or ''):
            n += 1
            sq += q or 0
            sv += v or 0
    print('block arithmetic (sum of countries vs printed Total):')
    te = ts = tb = 0
    for vol in sorted(stats):
        e, s, b = stats[vol]
        tot = e + s + b
        te, ts, tb = te + e, ts + s, tb + b
        print(f'  {vol}: {tot:4} blocks  exact {e / max(tot,1):6.1%}  '
              f'<2% {s / max(tot,1):6.1%}  structural {b / max(tot,1):6.1%}')
    tot = te + ts + tb
    print(f'  ALL: {tot:,} blocks  exact {te / max(tot,1):.1%}  '
          f'<2% {ts / max(tot,1):.1%}  structural {tb / max(tot,1):.1%}')
    out = BASE / 'reports' / 'country_block_flags.csv'
    with open(out, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['volume', 'flow', 'duty', 'group', 'article', 'year',
                    'total_qty', 'sum_qty', 'total_val', 'sum_val',
                    'worst_rel_err'])
        w.writerows(flags)
    print(f'  flags -> {out}')

    # ---- 2. wood reference vs gold decennial (country level)
    gold = defaultdict(float)
    for r in csv.DictReader(open(GOLD)):
        y = int(r['YEAR'])
        if y not in (1871, 1881, 1891):
            continue
        cname = norm(r['COMMODITY_NAME'])
        if not cname.startswith('wood and timber'):
            continue
        loc = norm(r['SOURCE_LOCATION_NAME'])
        if loc == 'world':
            continue
        gold[(cname, y, loc)] += float(r['AMOUNT'] or 0)

    ours = defaultdict(float)
    for vol, flow, duty, grp, art, ctry, unit, y, q, v in rows:
        if flow != 'import' or y not in (1871, 1881, 1891):
            continue
        if not (grp and norm(grp).startswith('wood')):
            continue
        if ctry == 'TOTAL' or ' : ' in (ctry or ''):
            continue
        c = norm(ctry)
        c = GOLD_COUNTRY.get(c, c)
        # gold splits e.g. "Wood and Timber Hewn Fir"; ours is
        # group="WOOD and TIMBER", article="Hewn, Fir"
        aname = norm(f'wood and timber {art or ""}')
        ours[(aname, y, c)] += q or 0

    matched = agree = 0
    mism = []
    for k, gv in gold.items():
        if gv <= 0:
            continue
        if k in ours:
            matched += 1
            if abs(ours[k] - gv) < 0.5:
                agree += 1
            else:
                mism.append((k, gv, ours[k]))
    print(f'\nwood x country x decennial-year cells: gold {len(gold):,}, '
          f'matched {matched:,}, exact {agree:,} '
          f'({agree / max(matched, 1):.1%})')
    for k, gv, ov in sorted(mism, key=lambda m: -abs(m[1] - m[2]))[:12]:
        print(f'  {str(k)[:60]:<60} gold {gv:>12,.0f} ours {ov:>12,.0f}')


if __name__ == '__main__':
    main()
