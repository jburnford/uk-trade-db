#!/usr/bin/env python3
"""Sub-entry loss screen: origin rows the pipeline drops because their
country label is a 'Parent : Sub' drill-down.

`integrate_sources` step 1 skips every consensus row whose country contains
' : '. Step 4 recovers most of them (6,880 cells), but when a block prints
ONLY drill-downs under a parent heading and step 4 does not fire, the trade
is simply gone, and the commodity-year reads short by exactly their total.

Three defects in three consecutive /next-defect iterations turned on this:
iron manufactures 1892 (Canada 4,703, one row), drugs unenumerated 1891
(77,052 of a 112,486 shortfall), and it is the residual in drugs 1892-94.

THE SCREEN IS ANCHORED ON THE COMMODITY-YEAR, NOT THE BLOCK. An earlier
block-anchored version reported 91 blocks whose own plain rows fell short of
their own printed total — and its top hits (brandy 1886, cotton raw 1893,
tea 1895) were all already closing at 1.00 because ANOTHER volume's copy of
the same table supplied the trade. A block being short proves nothing; only
the commodity-year is the unit of loss.

So: for each (article signature, year),

    T1              = the voted national total (consensus, quantity)
    got             = what country_year_final actually holds
    lost_subentry   = ' : ' rows in country_obs / country_obs_inf whose
                      (sig, country, year) reached NEITHER table

and report where `got` is short but `got + lost_subentry` lands within 0.5%
of T1 — i.e. the drill-downs are exactly what is missing, so nothing
double-counts if they are admitted.

WHAT IT FOUND, AND WHAT THAT MEANS (first run, 2026-07-29): FOUR
commodity-years, of which two were real. That is the headline — step 4
already recovers 6,880 drill-down cells and the residual class is nearly
exhausted. Do not expect a rich seam here.

Two known false-positive modes, both worth understanding before trusting a
row:

1. SIG-LEVEL ATTRIBUTION INSIDE A GLUE RUN. The screen keys on the article
   signature, so drill-downs sitting under a stale label are credited to
   whatever commodity that label signs to. `as_1898 ORE, unenumerated |
   PARAFFINE` is a 496-row sticky run holding several commodities; its
   `British East Indies : …` rows belong to the block at seq 16114-16211,
   not to paraffine's at 16073-16109. Check that the drill-downs sit in the
   SAME printed block as the plain rows before repairing.

2. THE T1 IS IN A DIFFERENT PAYLOAD NODE. The screen compares against
   `consensus`, keyed by signature; `reconcile_baseline` compares against
   the payload, keyed by display label. When a commodity's anchor is
   de-headed into its own node (feathers `Ornamental` 1892-1900 vs
   `Feathers And Down — Ornamental` 1868-1891) the two disagree about what
   the year even reads, and closing the sub-entry gap moves no bucket.

Usage: python3 scripts/detect_subentry_loss.py
   ->  reports/subentry_loss.csv
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).parent))
import validate_gold as V

BASE = Path('/home/jic823/uk_trade_db')


def is_total(c):
    return (c or '').strip().lower().startswith('total')


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)

    # ---- T1 per (sig, year): the best-tier quantity reading
    RANK = {'A': 0, 'B': 1, 'C': 2}
    t1 = {}
    for g, a, unit, y, val, tier in con.execute(
            """SELECT article_group, article, unit, year, value, tier
               FROM consensus WHERE flow='import' AND measure='quantity'
                 AND value IS NOT NULL AND value > 0""").fetchall():
        sig = V.sig(a or '') or V.sig(f"{g or ''} {a or ''}")
        if not sig:
            continue
        k = (sig, int(y))
        if k not in t1 or RANK.get(tier, 3) < RANK.get(t1[k][1], 3):
            t1[k] = (float(val), tier, unit)

    # ---- what the final table holds, per (sig, year), and which cells exist
    got = defaultdict(float)
    have = set()
    for g, a, ctry, y, q in con.execute(
            """SELECT article_group, article, country, year, quantity
               FROM country_year_final WHERE flow='import'""").fetchall():
        sig = V.sig(a or '') or V.sig(f"{g or ''} {a or ''}")
        if not sig:
            continue
        have.add((sig, V.cnorm(ctry), int(y)))
        if ' : ' not in (ctry or ''):
            got[(sig, int(y))] += float(q or 0)
        else:
            # a recovered drill-down counts too - the payload folds it to a
            # top-level country
            got[(sig, int(y))] += float(q or 0)
            have.add((sig, V.cnorm(ctry.split(' : ', 1)[1]), int(y)))

    # ---- drill-down rows that reached neither
    lost = defaultdict(float)
    detail = defaultdict(list)
    for tbl in ('country_obs', 'country_obs_inf'):
        for vol, g, a, ctry, y, q in con.execute(
                f"""SELECT volume, article_group, article, country_raw, year, quantity
                    FROM {tbl} WHERE flow='import' AND quantity > 0
                      AND country_raw LIKE '% : %'""").fetchall():
            if is_total(ctry):
                continue
            sig = V.sig(a or '') or V.sig(f"{g or ''} {a or ''}")
            if not sig:
                continue
            sub = ctry.split(' : ', 1)[1].strip()
            k = (sig, int(y))
            if (sig, V.cnorm(ctry), int(y)) in have or (sig, V.cnorm(sub), int(y)) in have:
                continue
            if any(d[0] == vol and d[1] == ctry for d in detail[k]):
                continue          # same row from both engines - count once
            lost[k] += float(q)
            detail[k].append((vol, ctry, float(q), g or '', a or ''))

    out = []
    for k, miss in lost.items():
        if k not in t1 or miss <= 0:
            continue
        anchor = t1[k][0]
        g0 = got.get(k, 0.0)
        if g0 >= anchor * 0.995:
            continue                      # already closes
        if not (anchor * 0.995 <= g0 + miss <= anchor * 1.005):
            continue                      # drill-downs are not the whole gap
        sig, y = k
        d = detail[k]
        out.append({
            'sig': '+'.join(sig), 'year': y,
            'article_group': d[0][3], 'article': d[0][4],
            'volumes': ';'.join(sorted({x[0] for x in d})),
            'unit': t1[k][2] or '', 't1': f'{anchor:.0f}', 't1_tier': t1[k][1],
            'got': f'{g0:.0f}', 'lost_subentry': f'{miss:.0f}',
            'ratio_now': f'{g0 / anchor:.4f}',
            'ratio_after': f'{(g0 + miss) / anchor:.4f}',
            'rows': '; '.join(f'{x[1]}={x[2]:,.0f}' for x in d[:10])})
    out.sort(key=lambda r: -float(r['lost_subentry']))

    dest = BASE / 'reports' / 'subentry_loss.csv'
    cols = ['sig', 'year', 'article_group', 'article', 'volumes', 'unit', 't1',
            't1_tier', 'got', 'lost_subentry', 'ratio_now', 'ratio_after', 'rows']
    with open(dest, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out)
    print(f'{len(out)} commodity-years would close if their orphan '
          f'drill-downs were admitted -> {dest}')
    for r in out[:30]:
        print(f"  {float(r['lost_subentry']):>12,.0f}  {r['year']} "
              f"{r['article_group'][:22]:22}|{r['article'][:24]:24} "
              f"{r['ratio_now']} -> {r['ratio_after']}  [{r['volumes']}]")


if __name__ == '__main__':
    main()
