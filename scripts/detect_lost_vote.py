"""Near-miss years that close on a reading the pipeline already has.

`digit_repair_candidates.py` tests a printed BLOCK against its own foot-total
and proposes a digit. This tests the commodity-year against its TIER-1 ANCHOR,
and it proposes nothing at all — it only reports where some parse in the corpus
ALREADY carries a figure that closes the year:

    delta = anchor - sum(origin cells)
    for each origin cell c:
        does any reading of (article, country, year) in country_obs or
        country_obs_inf equal c + delta?

When one does, this is not a repair and not a guess. It is a **vote the
pipeline lost**: two engines or two volumes disagreed, the wrong reading won,
and the year has been sitting a fraction short ever since. Rosin 1872 was
exactly this shape — five readings said 827,836, the one that won said 527,536,
and the year read 0.67.

Ranked by how much the closure improves the year, then by GBP. The `n_support`
column says how many volume/engine readings carry the proposed figure and
`n_current` how many carry the one in use; where support is 5-to-1 the
adjudication is already done. Where it is 1-to-1 it is not, and the page
decides.

    python3 scripts/detect_lost_vote.py [--max-off 0.05] [--min-gbp 20000]

Writes reports/lost_vote.csv, best first.
"""
import argparse
import csv
from collections import defaultdict
from pathlib import Path

import duckdb

BASE = Path(__file__).resolve().parents[1]

_UNITS = (('CWT', ('cwt', 'cut', 'cct', 'cict', 'ciot')),
          ('LB', ('lb', 'ib')), ('TON', ('ton', 'tun')),
          ('GAL', ('gallon',)), ('NUM', ('number', 'no')),
          ('BUSH', ('bushel',)), ('QTR', ('quarter', 'qr')),
          ('YARD', ('yard',)), ('LOAD', ('load',)), ('PAIR', ('pair',)),
          ('VALUE', ('value', 'gbp', '£')))


def _ukey(u):
    s = ''.join(ch for ch in (u or '').lower() if ch.isalpha() or ch == '£')
    if not s:
        return ''
    for key, stems in _UNITS:
        if any(s.startswith(t) for t in stems):
            return key
    return s[:6].upper()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--max-off', type=float, default=0.05,
                    help='only years already within this of their anchor')
    ap.add_argument('--min-gbp', type=float, default=20_000)
    a = ap.parse_args()

    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)
    con.create_function('ukey', _ukey, ['VARCHAR'], 'VARCHAR')

    # near-miss commodity-years: origins present, close but not closing
    years = con.execute("""
        WITH q AS (
            SELECT lower(trim(article)) AS art, ukey(unit) AS uk, year,
                   max(value) AS t1, any_value(article_group) AS grp
            FROM consensus
            WHERE flow='import' AND measure='quantity' AND value > 0
            GROUP BY 1, 2, 3),
        o AS (
            SELECT lower(trim(article)) AS art, ukey(unit) AS uk, year,
                   sum(quantity) AS s, count(*) AS n
            FROM country_year_final
            WHERE quantity > 0 AND country NOT LIKE '%(%'
              AND lower(country) NOT LIKE 'total%' AND country NOT LIKE '%:%'
            GROUP BY 1, 2, 3)
        SELECT o.art, q.grp, o.uk, o.year, o.s, q.t1, o.n
        FROM o JOIN q ON o.art=q.art AND o.year=q.year
                     AND (o.uk=q.uk OR o.uk='' OR q.uk='')
        WHERE o.s > 0 AND abs(o.s - q.t1) > 0.001 * q.t1
          AND abs(o.s - q.t1) <= ? * q.t1
    """, [a.max_off]).fetchall()

    # every reading the corpus holds, keyed (article, country, year)
    readings = defaultdict(lambda: defaultdict(int))
    for tbl in ('country_obs', 'country_obs_inf'):
        for art, cty, y, qty in con.execute(f"""
                SELECT lower(trim(article)), lower(trim(country_raw)), year,
                       quantity
                FROM {tbl} WHERE quantity > 0 AND flow='import'""").fetchall():
            readings[(art, cty, y)][round(qty)] += 1

    cells = defaultdict(list)
    for art, cty, y, qty in con.execute("""
            SELECT lower(trim(article)), lower(trim(country)), year, quantity
            FROM country_year_final
            WHERE quantity > 0 AND country NOT LIKE '%(%'
              AND lower(country) NOT LIKE 'total%'
              AND country NOT LIKE '%:%'""").fetchall():
        cells[(art, y)].append((cty, qty))

    out = []
    for art, grp, uk, y, s, t1, n in years:
        delta = t1 - s
        for cty, q in cells.get((art, y), ()):
            want = round(q + delta)
            if want <= 0:
                continue
            seen = readings.get((art, cty, y)) or {}
            n_sup = seen.get(want, 0)
            if not n_sup:
                continue
            out.append({
                'gain': round(abs(s - t1) / t1, 5),
                'article': art, 'group': grp or '', 'unit': uk, 'year': y,
                'country': cty, 'current': round(q), 'proposed': want,
                'delta': round(delta), 'n_support': n_sup,
                'n_current': seen.get(round(q), 0),
                'ratio_now': round(s / t1, 5), 'n_countries': n})

    best = {}
    for r in out:
        k = (r['article'], r['year'])
        if k not in best or r['n_support'] > best[k]['n_support']:
            best[k] = r
    rows = sorted(best.values(), key=lambda r: -r['gain'])

    dest = BASE / 'reports' / 'lost_vote.csv'
    with open(dest, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ['article'])
        w.writeheader()
        w.writerows(rows)
    strong = [r for r in rows if r['n_support'] > r['n_current']]
    print(f'{len(years):,} near-miss commodity-years examined; '
          f'{len(best)} close on a reading the corpus already holds '
          f'({len(strong)} where the proposed figure has MORE support than the '
          f'one in use) -> reports/lost_vote.csv')
    for r in rows[:25]:
        flag = '  <-- better-supported' if r['n_support'] > r['n_current'] else ''
        print(f"   {r['ratio_now']:.4f} {r['article'][:30]:30} {r['year']} "
              f"{r['country'][:22]:22} {r['current']:>12,} -> {r['proposed']:>12,} "
              f"[{r['n_support']}v{r['n_current']}]{flag}")


if __name__ == '__main__':
    main()
