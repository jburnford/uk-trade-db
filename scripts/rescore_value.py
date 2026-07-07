#!/usr/bin/env python3
"""Rescore the whole country database with value-as-signal.

Quantity and value are two independently printed numbers; value ≈ quantity ×
price, and within a series the unit price (value/quantity) drifts only slowly.
So a cell whose unit price sits far from its series median has a
quantity/value MISMATCH — a likely digit-slip in one column, even where OCR
voting passed it. A cell whose unit price is in line is CORROBORATED by its
value, independently of OCR/vote agreement.

Series = (flow, duty, norm-article, norm-country, norm-unit); price checked
across years. TOTAL rows and port sub-details ("X : Canada") are excluded —
their parent carries the figure.

Robust to MARKET-WIDE PRICE SHOCKS: a real shock (wartime cotton, a failed
harvest) lifts the unit price of EVERY origin for that commodity that year,
together — that is not an error. So each cell is compared not to a flat
series median but to its own baseline SCALED by that commodity-year's market
level (median unit price across all origins). A shared shock cancels; only a
single cell standing out from its same-year peers flags. Where the peer
cross-section is thin (can't establish the year level), the band widens so
an unmodelled shock is not mistaken for a slip. Deliberately conservative —
it should miss a small slip before it ever flags real data.

Rescore is ASYMMETRIC — a mismatch condemns only the weak side:
  price ok  → corroborated: a tier-C quantity is promoted to B (value backs it)
  price off + quantity already tier A → the quantity is well verified, so the
              VALUE is the suspect: quantity kept A, value flagged for review
  price off + quantity tier B/C → the quantity is the suspect: sent to review

Adds columns q_conf / v_review / price_flag / unit_price to a new
country_rescored table, and regenerates the review queue ranked by the value
now at stake. Reports corpus-wide rescues and newly-caught errors.
"""
import csv
import re
import unicodedata
from collections import defaultdict
from statistics import median
from pathlib import Path

import duckdb
import pandas as pd

BASE = Path('/home/jic823/uk_trade_db')
LO, HI = 0.5, 2.0          # unit-price band vs series median
CEIL = 50_000_000          # value plausibility ceiling (placement junk)


def norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii',
                                                      'ignore').decode()
    s = s.lower().replace('&', ' and ')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', s)).strip()


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'))
    rows = con.execute("""
        SELECT volume, flow, duty, article_group, article, country_raw, unit,
               year, quantity, value, q_block, v_block, q_cell, v_cell,
               row_seq, q_grade, v_grade
        FROM country_graded""").fetchall()

    def skey(r):
        return (r[1], r[2] or '', norm(r[3]) + '|' + norm(r[4]),
                norm(r[5]), norm(r[6]))

    # ---- two-way (origin x year) price model. For each commodity the
    # market level per year is the cross-origin median unit price; each
    # origin has a stable OFFSET from that level (its grade/quality). A cell
    # flags only when it departs from its OWN usual position relative to the
    # market that year — so a market-wide shock (shared, any duration) and a
    # persistently cheap or dear origin both pass; a lone outlier flags.
    # S=(flow,duty,artkey,country,unit); commodity F drops the country.
    spy = defaultdict(dict)     # series -> {year: unit price}
    tmp = defaultdict(lambda: defaultdict(list))
    for r in rows:
        c = r[5]
        if c == 'TOTAL' or ' : ' in (c or ''):
            continue
        q, v = r[8], r[9]
        if q and v and q >= 200 and v > 0 and v <= CEIL:
            tmp[skey(r)][r[7]].append(v / q)
    for s, yrs in tmp.items():
        spy[s] = {y: median(ps) for y, ps in yrs.items()}
    # market level per commodity-year (only where >=3 origins priced it)
    fy = defaultdict(lambda: defaultdict(list))
    for s, d in spy.items():
        F = (s[0], s[1], s[2], s[4])
        for y, p in d.items():
            fy[F][y].append(p)
    mkt = {F: {y: median(ps) for y, ps in yd.items() if len(ps) >= 3}
           for F, yd in fy.items()}
    # origin offset = median over years of (origin price / market price)
    offset = {}
    for s, d in spy.items():
        F = (s[0], s[1], s[2], s[4])
        rs = [d[y] / mkt[F][y] for y in d
              if F in mkt and y in mkt[F] and mkt[F][y] > 0]
        if len(rs) >= 3:
            offset[s] = median(rs)
    # own-series median as the fallback when no market model is available
    sp = {s: median(list(d.values())) for s, d in spy.items() if len(d) >= 3}

    # ---- per-row price flag + asymmetric rescore
    out = []
    st = defaultdict(int)
    for r in rows:
        q, v, qg, vg = r[8], r[9], r[15], r[16]
        c = r[5]
        pflag, up = 'na', None
        if (q and v and q > 0 and v > 0 and v <= CEIL
                and c != 'TOTAL' and ' : ' not in (c or '')):
            price = v / q
            up = round(price, 2)
            S = skey(r)
            F = (S[0], S[1], S[2], S[4])
            yr = r[7]
            exp, wide = None, False
            if S in offset and F in mkt and yr in mkt[F] and mkt[F][yr] > 0:
                exp = mkt[F][yr] * offset[S]        # market that year × grade
                st['shock_adjusted'] += 1
            elif S in sp:
                exp, wide = sp[S], True             # no market model: widen
            if exp and exp > 0:
                ratio = price / exp
                lo, hi = (0.4, 2.5) if wide else (LO, HI)
                pflag = 'ok' if lo <= ratio <= hi else ('hi' if ratio > hi
                                                        else 'lo')
        q_conf, v_review = qg, 0
        if pflag == 'ok':
            q_conf = 'B' if qg == 'C' else qg        # value corroborates
            if qg == 'C':
                st['rescued'] += 1
        elif pflag in ('hi', 'lo'):
            if qg == 'A':
                v_review = 1                          # quantity solid → value
                st['value_suspect'] += 1              #   is the suspect
            else:
                q_conf = 'C'                          # weak q + mismatch
                st['qty_suspect'] += 1
        out.append([*r[:17], q_conf, v_review, pflag, up])
        st['total'] += 1

    con.execute('DROP TABLE IF EXISTS country_rescored')
    con.execute("""CREATE TABLE country_rescored (
        volume VARCHAR, flow VARCHAR, duty VARCHAR, article_group VARCHAR,
        article VARCHAR, country_raw VARCHAR, unit VARCHAR, year INTEGER,
        quantity DOUBLE, value DOUBLE, q_block VARCHAR, v_block VARCHAR,
        q_cell VARCHAR, v_cell VARCHAR, row_seq INTEGER, q_grade VARCHAR,
        v_grade VARCHAR, q_conf VARCHAR, v_review INTEGER, price_flag VARCHAR,
        unit_price DOUBLE)""")
    cols = ['volume', 'flow', 'duty', 'article_group', 'article',
            'country_raw', 'unit', 'year', 'quantity', 'value', 'q_block',
            'v_block', 'q_cell', 'v_cell', 'row_seq', 'q_grade', 'v_grade',
            'q_conf', 'v_review', 'price_flag', 'unit_price']
    df = pd.DataFrame(out, columns=cols)
    con.execute('INSERT INTO country_rescored SELECT * FROM df')
    con.commit()

    # ---- corpus report
    n = st['total']
    print(f'rescored {n:,} country cells')
    print(f'  price-corroborated (£/unit in series norm): '
          f"{sum(1 for o in out if o[19]=='ok'):,}")
    print(f'  value mismatch (q≠v, one column suspect):   '
          f"{sum(1 for o in out if o[19] in ('hi','lo')):,}")
    print(f'  no price signal (nil/short series/junk):    '
          f"{sum(1 for o in out if o[19]=='na'):,}")
    print(f'\n  tier-C quantities RESCUED by value:  {st["rescued"]:,}')
    print(f'  quantity errors flagged (weak q + off):{st["qty_suspect"]:,}')
    print(f'  value errors flagged (A-grade q, off): {st["value_suspect"]:,}')

    # how many quantity errors were caught that voting had NOT flagged
    caught_ab = sum(1 for o in out if o[19] in ('hi', 'lo')
                    and o[15] in ('A', 'B'))
    print(f'\n  q/v mismatches sitting in a tier-A/B cell (voting missed): '
          f'{caught_ab:,}')

    # ---- review queue: mismatches first (ranked by value at stake),
    # then remaining un-corroborated tier-C
    q1 = [o for o in out if o[19] in ('hi', 'lo')]
    q2 = [o for o in out if o[19] not in ('hi', 'lo') and o[17] == 'C'
          and o[5] != 'TOTAL' and ' : ' not in (o[5] or '')]
    q1.sort(key=lambda o: -(min(o[9] or 0, CEIL)))
    q2.sort(key=lambda o: -(min(o[9] or 0, CEIL)))
    out_csv = BASE / 'reports' / 'country_review_queue.csv'
    with open(out_csv, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['reason', 'volume', 'flow', 'duty', 'group', 'article',
                    'country', 'unit', 'year', 'quantity', 'value',
                    'unit_price', 'price_flag', 'q_grade', 'v_grade',
                    'q_conf', 'q_block', 'v_block', 'q_cell', 'v_cell'])
        for o in q1:
            w.writerow(['value_mismatch', o[0], o[1], o[2], o[3], o[4], o[5],
                        o[6], o[7], o[8], o[9], o[20], o[19], o[15], o[16],
                        o[17], o[10], o[11], o[12], o[13]])
        for o in q2:
            w.writerow(['tier_c', o[0], o[1], o[2], o[3], o[4], o[5], o[6],
                        o[7], o[8], o[9], o[20], o[19], o[15], o[16], o[17],
                        o[10], o[11], o[12], o[13]])
    print(f'\n  review queue -> {out_csv} '
          f'({len(q1):,} mismatches + {len(q2):,} tier-C)')


if __name__ == '__main__':
    main()
