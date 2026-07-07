#!/usr/bin/env python3
"""Merge the three extraction sources into one pipeline output table.

country_year_consensus (tabular, voted) + country_obs_twoup (two-up layout) +
country_obs_runin (run-in text) -> country_year_final. Keyed by
(commodity article-sig, canonical country, year); prefer the voted consensus,
then two-up, then run-in (fills gaps the tabular parser missed). This turns the
staged recoveries into actual pipeline output the harness reads.
"""
import csv
from collections import defaultdict
from pathlib import Path

import duckdb
import validate_gold as V

BASE = Path('/home/jic823/uk_trade_db')


def is_subtotal(c):
    """A printed subtotal row ("Total from Foreign Countries", "Total from
    British Possessions", "Total to ...") — NOT a country. parse_country folds
    these into 'TOTAL', but the two-up gap-fill parser keeps the descriptive
    label, so ~400 leaked in and were summed as countries. Any label whose
    first word is 'total' is a subtotal."""
    return not c or c == 'world' or c.split(' ', 1)[0] == 'total'


_COLONIAL = ('india', 'indies', 'ceylon', 'bengal', 'madras', 'bombay',
             'scinde', 'burmah', 'hong kong', 'straits', 'australas',
             'australia', 'new south wales', 'victoria', 'queensland',
             'zealand', 'tasmania', 'cape', 'natal', 'canada', 'possession',
             'mauritius', 'guiana', 'west india')


def subtotal_bucket(c):
    """For a leaked 'Total from X' subtotal, the aggregate bucket it stands for
    when its detail is missing: possessions vs foreign. None if not a subtotal
    we retain."""
    if 'possession' in c:
        return 'British Possessions'
    if 'foreign' in c:
        return 'Foreign Countries'
    return None


def is_colonial(c):
    return any(k in c for k in _COLONIAL)


def load_csv(path, src):
    # pass 1: which (asig, year) blocks already carry colonial / foreign DETAIL,
    # so we know whether a leaked "Total from Possessions/Foreign" subtotal is a
    # redundant double-count (detail present -> drop) or the only carrier of
    # that volume (detail absent -> keep as one aggregate bucket).
    has_col, has_for = set(), set()
    recs = list(csv.DictReader(open(path)))
    for r in recs:
        if r.get('flow') != 'import':
            continue
        art = (r['article'] or '').lstrip(',»„"”„ ').strip()
        grp = r['article_group'] or ''
        asig = V.sig(art) or V.sig(f"{grp} {art}")
        c = V.cnorm(r['country_raw'])
        if not asig or is_subtotal(c) or ' : ' in (r['country_raw'] or ''):
            continue
        key = (asig, int(r['year']))
        (has_col if is_colonial(c) else has_for).add(key)

    for r in recs:
        if r.get('flow') != 'import':
            continue
        art = (r['article'] or '').lstrip(',»„"”„ ').strip()
        grp = r['article_group'] or ''
        asig = V.sig(art) or V.sig(f"{grp} {art}")   # generic article -> group fallback
        if not asig:
            continue
        c = V.cnorm(r['country_raw'])
        country = r['country_raw']
        if ' : ' in (r['country_raw'] or ''):
            continue
        if is_subtotal(c):
            bucket = subtotal_bucket(c)              # retain only as a fallback
            key = (asig, int(r['year']))
            covered = key in (has_col if bucket == 'British Possessions'
                              else has_for)
            if bucket is None or covered:
                continue                             # detail present -> drop
            c, country = V.cnorm(bucket), bucket     # keep as aggregate bucket
        try:
            q = float(r['quantity'] or 0)
        except ValueError:
            q = 0.0
        if q <= 0:
            continue
        yield (asig, c, int(r['year'])), {
            'group': grp.upper(), 'article': art, 'country': country,
            'unit': r['unit'] or '', 'qty': q, 'year': int(r['year']),
            'value': float(r['value'] or 0) if (r['value'] or '').strip() else None,
            'src': src}


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'))
    out_rows = []                                # keep consensus rows AS-IS
    consensus_commod = set()                     # (article-sig, year) present in consensus

    # 1) consensus (voted) — keep every row, no collapsing
    rows = con.execute("""SELECT article_group, article, country, unit, year,
        quantity, value FROM country_year_consensus WHERE flow='import'""").fetchall()
    for grp, art, ctry, unit, y, q, v in rows:
        a = (art or '').strip()
        asig = V.sig(a) or V.sig(f"{grp or ''} {a}")   # generic article -> group fallback
        c = V.cnorm(ctry)
        if not asig or is_subtotal(c) or ' : ' in (ctry or ''):
            continue
        if not q or float(q) <= 0:
            continue
        consensus_commod.add((asig, int(y)))
        out_rows.append({'group': (grp or '').upper(), 'article': a, 'country': ctry,
            'unit': unit or '', 'qty': float(q), 'value': float(v) if v else None,
            'year': int(y), 'src': 'consensus'})

    # 2) two-up, 3) run-in — add ONLY commodity-years absent from consensus
    #    (dedup within the added source by (article-sig, country, year))
    added = defaultdict(int)
    seen_added = set()
    for path, src in [(BASE / 'exports' / 'twoup_country.csv', 'twoup'),
                      (BASE / 'exports' / 'runin_country.csv', 'runin')]:
        for (asig, c, y), rec in load_csv(path, src):
            if (asig, y) in consensus_commod:
                continue                          # consensus already has this commodity
            if (asig, c, y) in seen_added:
                continue
            seen_added.add((asig, c, y))
            out_rows.append(rec)
            added[src] += 1

    # dedup near-duplicate country rows within a commodity-year: merged engines
    # and summary+detail double-prints inflate over-counted commodities (e.g.
    # Woollen Manufactures had France 74,576,609 AND 74,576,600).
    dedup, seen = [], set()
    for r in out_rows:
        k = (r['group'], r['article'], r['year'], V.cnorm(r['country']),
             round(r['qty'] / 1000))
        if k in seen:
            continue
        seen.add(k)
        dedup.append(r)
    out_rows = dedup
    cells = {i: r for i, r in enumerate(out_rows)}   # keep interface below

    # write country_year_final via CSV -> CREATE TABLE (fast path; executemany
    # is pathologically slow on this DB)
    tmp = BASE / 'exports' / '_country_year_final.csv'
    with open(tmp, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['article_group', 'article', 'country', 'unit', 'flow',
                    'year', 'quantity', 'value', 'source'])
        for r in cells.values():
            w.writerow([r['group'], r['article'], r['country'], r['unit'],
                        'import', r['year'] if 'year' in r else r.get('y', ''),
                        r['qty'], r['value'] if r['value'] is not None else '', r['src']])
    con.execute("DROP TABLE IF EXISTS country_year_final")
    con.execute(f"CREATE TABLE country_year_final AS "
                f"SELECT * FROM read_csv_auto('{tmp}', header=true)")
    n = con.execute("SELECT count(*), count(DISTINCT source) FROM country_year_final").fetchone()
    bysrc = con.execute("SELECT source, count(*) FROM country_year_final GROUP BY source").fetchall()
    con.close()
    print(f'country_year_final: {n[0]:,} rows')
    print(f'  by source: {dict(bysrc)}')
    print(f'  gap-fill added: {dict(added)}')


if __name__ == '__main__':
    main()
