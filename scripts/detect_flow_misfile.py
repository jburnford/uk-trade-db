#!/usr/bin/env python3
"""Find origin tables parsed under the wrong FLOW.

`parse_country` assigns each block a flow from the page heading. When that
heading is lost or OCR-mangled the block keeps the previous section's flow, so
an IMPORT origin table lands under `export_uk` or `reexport` and never reaches
the import side at all.

Two were found by hand in `as_1892` alone - the `ZINC'd)` block (iteration 10)
and `WOOD and TIMBER | Mahogany` (iteration 21) - both under a mangled or stale
group head, and both closing on the import Tier-1 to the digit. This screens
for the rest.

The test is the block's own printed grand TOTAL against the import Tier-1 for
the same commodity-year. Two guards, because export and import tables of the
same commodity are often the same order of magnitude and will collide by
chance:

  * the import commodity-year must currently be EMPTY or SHORT. A block whose
    total matches a year that already closes is a coincidence by construction -
    that year's origins are accounted for.
  * agreement must be within TOL of the anchor.

Everything surviving both still needs hand adjudication, and the decisive
evidence is usually the COUNTRY LIST: an export table names destinations
(Australia, British India, Hong Kong, the Straits Settlements), an import table
names sources. Mahogany 1892 was settled that way - Mexico, British West
Indies, Hayti and St. Domingo are where mahogany came from, not where Britain
sent it.

Usage: python3 scripts/detect_flow_misfile.py
   ->  reports/flow_misfile_candidates.csv
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).parent))
import validate_gold as V

BASE = Path('/home/jic823/uk_trade_db')
TOL = 0.0005


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)

    # import Tier-1 per (sig, year), best tier
    RANK = {'A': 0, 'B': 1, 'C': 2}
    t1 = {}
    for g, a, unit, y, val, tier in con.execute(
            """SELECT article_group, article, unit, year, value, tier FROM consensus
               WHERE flow='import' AND measure='quantity' AND value > 0""").fetchall():
        sig = V.sig(a or '') or V.sig(f"{g or ''} {a or ''}")
        if not sig:
            continue
        k = (sig, int(y))
        if k not in t1 or RANK.get(tier, 3) < RANK.get(t1[k][1], 3):
            t1[k] = (float(val), tier, unit, g, a)

    # what the import side already holds per (sig, year)
    got = defaultdict(float)
    for g, a, y, q in con.execute(
            """SELECT article_group, article, year, quantity FROM country_year_final
               WHERE flow='import'""").fetchall():
        sig = V.sig(a or '') or V.sig(f"{g or ''} {a or ''}")
        if sig:
            got[(sig, int(y))] += float(q or 0)

    rows = []
    for tbl in ('country_obs', 'country_obs_inf'):
        blocks = defaultdict(list)
        for vol, fl, g, a, ctry, unit, y, q in con.execute(
                f"""SELECT volume, flow, article_group, article, country_raw, unit, year, quantity
                    FROM {tbl} WHERE flow <> 'import' AND quantity > 0""").fetchall():
            blocks[(vol, fl, g or '', a or '', unit or '', int(y))].append((ctry or '', float(q)))
        for (vol, fl, g, a, unit, y), cells in blocks.items():
            tots = [q for c, q in cells if c.strip().upper().startswith('TOTAL')]
            if not tots:
                continue
            grand = max(tots)
            sig = V.sig(a) or V.sig(f'{g} {a}')
            if not sig:
                continue
            anchor = t1.get((sig, y))
            if not anchor:
                continue
            if abs(grand - anchor[0]) > TOL * anchor[0]:
                continue
            have = got.get((sig, y), 0.0)
            if have >= 0.9 * anchor[0]:
                continue                      # that year is already accounted for
            names = [c for c, q in cells if not c.strip().upper().startswith('TOTAL')]
            rows.append({
                'engine': 'ch' if tbl == 'country_obs' else 'inf',
                'volume': vol, 'flow_as_parsed': fl, 'article_group': g,
                'article': a, 'unit': unit, 'year': y,
                'block_total': f'{grand:.0f}',
                'import_t1': f'{anchor[0]:.0f}', 't1_tier': anchor[1],
                'import_has': f'{have:.0f}',
                'ratio_now': f'{have / anchor[0]:.4f}',
                'n_rows': len(cells),
                'countries': '; '.join(names[:10])})
    rows.sort(key=lambda r: -float(r['import_t1']))

    dest = BASE / 'reports' / 'flow_misfile_candidates.csv'
    cols = ['engine', 'volume', 'flow_as_parsed', 'article_group', 'article', 'unit',
            'year', 'block_total', 'import_t1', 't1_tier', 'import_has', 'ratio_now',
            'n_rows', 'countries']
    with open(dest, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f'{len(rows)} candidate flow-misfiled blocks -> {dest}')
    for r in rows[:25]:
        print(f"  {int(r['import_t1']):>12,}  {r['volume']} {r['engine']:3} "
              f"{r['flow_as_parsed']:9} {r['article_group'][:20]:20}|{r['article'][:20]:20} "
              f"{r['year']} now={r['ratio_now']}")


if __name__ == '__main__':
    main()
