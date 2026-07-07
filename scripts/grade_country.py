#!/usr/bin/env python3
"""Grade every country_consensus member row for analytical usability.

The criterion is MAGNITUDE safety (a 9M-vs-1M first-digit error is fatal;
being off by small amounts is not), so:

  grade A — first-digit error effectively impossible:
            the row's block passes printed-total arithmetic (exact or
            repaired), OR both OCR engines independently read the same
            number (coinciding misreads of the same digit are rare)
  grade B — small-error risk only: block sums to within 2% of the printed
            total (one small slip somewhere among ~10 cells), and this
            cell isn't the prime suspect (engines don't disagree on it)
  grade C — review: structurally flagged blocks with single-engine or
            disagreeing cells; near-blocks where THIS cell is the engine
            disagreement; unchecked single-engine cells

Magnitude screen: within each article x country series across years, a
non-block-verified cell that jumps >3x against both neighbours is
downgraded to C (block-verified cells keep their grade — arithmetic
proof beats a trend heuristic; real trade swings exist).

Writes: country_graded (table) and reports/country_review_queue.csv
(grade-C rows ranked by GBP value, biggest exposure first).
"""
import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import duckdb

BASE = Path('/home/jic823/uk_trade_db')
GOOD = {'exact', 'inf_struct', 'inf_block', 'swap', 'anchor', 'digit_fix',
        'inf_only', 't1_anchor'}   # t1_anchor: member-sum EQUALS the voted
        # Tier-1 national total (anchor_tier1.py) — digit error impossible
# no genuine single article x country flow in this era exceeds ~40M GBP
# (peak: cotton piece goods to British India ~25M). Values above are OCR
# glue ("94,998,024,832") or a quantity that landed in the value column
# (1.2B *yards* of cotton) — a failure mode BOTH engines share, so
# cross-engine agreement cannot catch it; a plausibility ceiling can.
VALUE_CEILING = 50_000_000


def norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii',
                                                      'ignore').decode()
    s = s.lower().replace('&', ' and ')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', s)).strip()


def grade(block_st, cell_st):
    if cell_st == 'human':                # confirmed against the scan
        return 'A'
    if block_st in GOOD or cell_st == 'agree' or cell_st == 'repaired':
        return 'A'
    if block_st in ('near', 't1_near') and cell_st != 'differ':
        return 'B'                        # t1_near: sum within 1% of the
    return 'C'                            # voted Tier-1 total — small-slip risk


def load_human():
    """reference/human_review.csv from the review app: key -> decision.
    Last decision per key wins."""
    f = BASE / 'reference' / 'human_review.csv'
    out = {}
    if f.exists():
        for d in csv.DictReader(open(f)):
            out[d['key']] = d
    return out


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'))
    rows = con.execute("""
        SELECT volume, flow, duty, article_group, article, country_raw,
               unit, year, quantity, value, q_block, v_block,
               q_cell, v_cell, row_seq
        FROM country_consensus
        WHERE country_raw != 'TOTAL'""").fetchall()

    human = load_human()
    if human:
        applied = 0
        fixed = []
        for r in rows:
            k = '|'.join([r[0], r[1], r[2] or '', r[3] or '', r[4] or '',
                          r[5] or '', str(r[7])])
            d = human.get(k)
            if not d:
                fixed.append(r)
                continue
            applied += 1
            if d['decision'] == 'junk':
                continue                          # drop the row entirely
            if d['decision'] in ('confirm', 'correct'):
                q = float(d['quantity']) if d['quantity'] else None
                v = float(d['value']) if d['value'] else None
                r = (*r[:8], q, v, r[10], r[11], 'human', 'human', r[14])
            fixed.append(r)                       # notfound: unchanged
        rows = fixed
        print(f'human review decisions applied: {applied:,}')

    graded = []
    series = defaultdict(list)
    n_ceiling = 0
    for r in rows:
        qg = grade(r[10], r[12])
        vg = grade(r[11], r[13])
        if r[9] is not None and r[9] > VALUE_CEILING:
            vg = 'C'
            n_ceiling += 1
        graded.append([*r[:15], qg, vg])
        if r[9] is not None and ' : ' not in (r[5] or ''):
            key = (r[1], r[2], norm(r[3]), norm(r[4]), norm(r[5]))
            series[key].append((r[7], r[9], len(graded) - 1))

    # magnitude screen on the value field across years
    n_jump = 0
    for key, pts in series.items():
        if len(pts) < 3:
            continue
        pts.sort()
        for i in range(1, len(pts) - 1):
            y, v, gi = pts[i]
            pv, nv = pts[i - 1][1], pts[i + 1][1]
            if v < 5000 or pv <= 0 or nv <= 0:
                continue
            if (v > 3 * pv and v > 3 * nv) or (v < pv / 3 and v < nv / 3):
                if graded[gi][16] != 'A' or graded[gi][11] not in GOOD:
                    if graded[gi][16] != 'C':
                        graded[gi][16] = 'C'
                        n_jump += 1

    con.execute('DROP TABLE IF EXISTS country_graded')
    con.execute('''CREATE TABLE country_graded (
        volume VARCHAR, flow VARCHAR, duty VARCHAR,
        article_group VARCHAR, article VARCHAR, country_raw VARCHAR,
        unit VARCHAR, year INTEGER, quantity DOUBLE, value DOUBLE,
        q_block VARCHAR, v_block VARCHAR, q_cell VARCHAR, v_cell VARCHAR,
        row_seq INTEGER, q_grade VARCHAR, v_grade VARCHAR)''')
    import pandas as pd
    gdf = pd.DataFrame(graded, columns=[
        'volume', 'flow', 'duty', 'article_group', 'article', 'country_raw',
        'unit', 'year', 'quantity', 'value', 'q_block', 'v_block', 'q_cell',
        'v_cell', 'row_seq', 'q_grade', 'v_grade'])
    con.execute('INSERT INTO country_graded SELECT * FROM gdf')
    con.commit()
    print(f'graded rows: {len(graded):,}  '
          f'(series-jump downgrades: {n_jump:,}; '
          f'over value ceiling: {n_ceiling:,})')

    # GBP shares over PLAUSIBLE values only, or the junk monsters dominate
    def pv(g):
        v = g[9] or 0
        return v if v <= VALUE_CEILING else 0

    tot_v = sum(pv(g) for g in graded)
    print('\nvalue-field grades (member rows; GBP share of plausible value):')
    for gr in 'ABC':
        n = sum(1 for g in graded if g[16] == gr)
        v = sum(pv(g) for g in graded if g[16] == gr)
        print(f'  {gr}: {n:7,} rows ({n / len(graded):5.1%})   '
              f'GBP share {v / max(tot_v, 1):5.1%}')

    print('\nby era (value field, share of rows / share of GBP):')
    for lo, hi in ((1872, 1876), (1877, 1884), (1885, 1896), (1897, 1899)):
        sub = [g for g in graded if lo <= (g[7] or 0) <= hi]
        tv = sum(pv(g) for g in sub)
        parts = []
        for gr in 'ABC':
            n = sum(1 for g in sub if g[16] == gr)
            v = sum(pv(g) for g in sub if g[16] == gr)
            parts.append(f'{gr} {n / max(len(sub), 1):5.1%}/'
                         f'{v / max(tv, 1):5.1%}')
        print(f'  {lo}-{hi}:  ' + '   '.join(parts))

    wood = [g for g in graded
            if norm(g[3]).startswith('wood') and g[1] == 'import']
    tv = sum(pv(g) for g in wood)
    print(f'\nwood imports ({len(wood):,} rows):')
    for gr in 'ABC':
        n = sum(1 for g in wood if g[16] == gr)
        v = sum(pv(g) for g in wood if g[16] == gr)
        print(f'  {gr}: {n:5,} rows ({n / max(len(wood), 1):5.1%})   '
              f'GBP share {v / max(tv, 1):5.1%}')

    # ---- review queue, biggest PLAUSIBLE exposure first (junk monsters
    # sort by capped value so real big flows outrank obvious glue)
    out = BASE / 'reports' / 'country_review_queue.csv'
    cq = sorted((g for g in graded if g[16] == 'C'),
                key=lambda g: -pv(g))
    with open(out, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['volume', 'flow', 'duty', 'group', 'article', 'country',
                    'unit', 'year', 'quantity', 'value',
                    'q_block', 'v_block', 'q_cell', 'v_cell'])
        for g in cq:
            w.writerow(g[:14])
    print(f'\nreview queue: {len(cq):,} rows -> {out}')
    top = sum(pv(g) for g in cq[:2000])
    allc = sum(pv(g) for g in cq)
    print(f'  top 2,000 rows cover {top / max(allc, 1):.0%} of the flagged '
          f'plausible GBP value')


if __name__ == '__main__':
    main()
