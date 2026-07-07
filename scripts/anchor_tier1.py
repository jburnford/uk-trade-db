#!/usr/bin/env python3
"""Cross-tier anchoring: corroborate Tier-2 country blocks against the voted
Tier-1 national totals.

Tier-1 national totals are the strongest numbers in the corpus — each is read
in up to 5-6 volumes' comparative columns and cross-volume voted (tier A/B).
The country-detail triples, by contrast, are printed ONCE for 1872-92: their
only checks are two engines reading the same printing and the block's own
printed total (often itself misread or unparsed: 'nototal'). This stage adds
the missing independent check: if a block's member-sum equals a voted A/B
Tier-1 total for the same commodity-year, every member is corroborated by
numbers printed in OTHER volumes.

Matching is collision-safe (the Cotton-Raw lesson): the Tier-1 article must
share a name token with the block's article AND the numbers must agree —
  exact integer equality  -> q_block 't1_anchor'  (a digit error anywhere in
                             the block would break equality: A-grade logic)
  within 1%               -> q_block 't1_near'    (small-slip risk only: B)
Only rows not already block-verified are touched (GOOD statuses keep their
stronger provenance). Rerun grade_country -> rescore_value ->
vote_country_years -> integrate_sources after this.
"""
import re
from collections import defaultdict
from pathlib import Path

import duckdb

BASE = Path('/home/jic823/uk_trade_db')
GOOD = {'exact', 'inf_struct', 'inf_block', 'swap', 'anchor', 'digit_fix',
        'inf_only', 'human', 't1_anchor', 't1_near'}
STOP = {'of', 'and', 'the', 'or', 'in', 'total', 'all', 'kinds', 'sorts',
        'other', 'unenumerated', 'none', 'from', 'to', 'not', 'for'}
# Tier-1 flow labels vs Tier-2 flow labels
FLOWMAP = {'import': 'import', 'export_uk': 'export_uk', 'reexport': 'reexport'}


def toks(s):
    return {w for w in re.findall(r'[a-z]+', (s or '').lower())
            if w not in STOP and len(w) > 2}


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'))

    # voted Tier-1 totals: (flow, year) -> [(toks, value)]
    t1 = defaultdict(list)
    for flow, grp, art, y, val in con.execute("""
            SELECT flow, article_group, article, year, value FROM consensus
            WHERE measure='quantity' AND value > 0 AND tier IN ('A','B')
            """).fetchall():
        t1[(flow, int(y))].append((toks(f"{grp or ''} {art or ''}"),
                                   float(val)))

    # Tier-2 blocks: (volume, flow, duty, grp, art, year)
    rows = con.execute("""
        SELECT volume, flow, duty, article_group, article, year,
               country_raw, quantity, q_block
        FROM country_consensus WHERE quantity > 0""").fetchall()
    blocks = defaultdict(lambda: {'sum': 0.0, 'n': 0, 'weak': 0})
    for vol, flow, duty, grp, art, y, c, q, qb in rows:
        if c == 'TOTAL' or ' : ' in (c or ''):
            continue
        b = blocks[(vol, flow, duty, grp, art, int(y))]
        b['sum'] += q
        b['n'] += 1
        if qb not in GOOD:
            b['weak'] += 1

    upd_exact, upd_near = [], []
    for (vol, flow, duty, grp, art, y), b in blocks.items():
        if b['n'] < 3 or b['weak'] == 0 or b['sum'] <= 0:
            continue
        nt = toks(f"{grp or ''} {art or ''}")
        if not nt:
            continue
        best = None
        for tt, val in t1.get((FLOWMAP.get(flow, flow), y), ()):
            if not (nt & tt):
                continue
            err = abs(b['sum'] - val) / max(b['sum'], val)
            if best is None or err < best[0]:
                best = (err, val)
        if best is None:
            continue
        err, val = best
        if round(b['sum']) == round(val):
            upd_exact.append((vol, flow, duty, grp, art, y))
        elif err <= 0.01:
            upd_near.append((vol, flow, duty, grp, art, y))

    def apply(marks, status):
        n = 0
        for vol, flow, duty, grp, art, y in marks:
            n += con.execute(f"""
                UPDATE country_consensus SET q_block='{status}'
                WHERE volume=? AND flow=? AND duty IS NOT DISTINCT FROM ?
                  AND article_group IS NOT DISTINCT FROM ?
                  AND article IS NOT DISTINCT FROM ? AND year=?
                  AND country_raw != 'TOTAL' AND country_raw NOT LIKE '% : %'
                  AND quantity > 0
                  AND (q_block IS NULL OR q_block NOT IN
                       ('exact','inf_struct','inf_block','swap','anchor',
                        'digit_fix','inf_only','human','t1_anchor'))
                """, [vol, flow, duty, grp, art, y]).fetchone()[0] or 0
        return n

    ne = apply(upd_exact, 't1_anchor')
    nn = apply(upd_near, 't1_near')
    con.commit()
    print(f'T1-anchored blocks: {len(upd_exact):,} exact -> {ne:,} rows '
          f"marked 't1_anchor' (A-logic)")
    print(f'T1-near blocks:     {len(upd_near):,} within 1% -> {nn:,} rows '
          f"marked 't1_near' (B-logic)")


if __name__ == '__main__':
    main()
