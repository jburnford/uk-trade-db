"""Column-crossing detector: quantity from one two-up column, value from the other.

Boots and Shoes 1883 is the specimen (reports/boots_1883_findings.md). The page
was two-up; the parser paired the RIGHT column's country labels and VALUES with
the LEFT column's QUANTITIES. The year then held 15,780 dozen pairs against a
123,058 anchor while its value column still matched the printed value total to
0.1%, and boot DESTINATIONS appeared as origins. No existing screen looks for
that, because every quantity-side instrument sees only a short year and every
value-side instrument sees a clean one.

The signature is sharp: a commodity-year whose ORIGIN QUANTITY sum falls far
short of its Tier-1 quantity while its ORIGIN VALUE sum MATCHES the printed
Tier-1 value. A genuinely incomplete block loses both columns in proportion; a
crossed block loses only one.

Reported both ways round — value-complete/quantity-short and the mirror — since
either column can be the one that survives.

    python3 scripts/detect_column_crossing.py [--max-qty 0.8] [--val-tol 0.02]

Writes reports/column_crossing.csv, worst first.
"""
import argparse
import csv
from pathlib import Path

import duckdb

BASE = Path(__file__).resolve().parents[1]

# OCR folds the abstract's unit column badly — 'Cwts.', 'Cwts', 'Cuts.',
# 'Ccts.', 'Cicts.' are all hundredweights. Coarse key; '' matches anything.
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
    ap.add_argument('--max-qty', type=float, default=0.8,
                    help='flag when the quantity side is at or below this')
    ap.add_argument('--val-tol', type=float, default=0.02,
                    help='how close the value side must be to 1.0')
    ap.add_argument('--min-gbp', type=float, default=20_000,
                    help='ignore commodity-years smaller than this')
    a = ap.parse_args()

    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)

    # Tier-1 anchors. Two joins are impossible as printed and have to be
    # normalised, or the screen sees almost nothing:
    #   * the country side often carries a STALE GROUP (boots 1883 sits under
    #     'JUTE'), so the join is on ARTICLE + year, not group + article;
    #   * the unit is OCR-variable on the anchor side ('Cwts.', 'Cwts',
    #     'Cuts.', 'Ccts.' are all hundredweights) and frequently NULL on the
    #     country side, so it is folded to a coarse key and a NULL matches
    #     anything. Joining on the literal unit string cut coverage from
    #     ~3,000 commodity-years to 362.
    con.create_function('ukey', _ukey, ['VARCHAR'], 'VARCHAR')
    rows = con.execute("""
        WITH q AS (
            SELECT lower(trim(article)) AS art, ukey(unit) AS uk, year,
                   max(value) AS qty_t1, min(tier) AS q_tier,
                   any_value(article_group) AS grp
            FROM consensus
            WHERE flow='import' AND measure='quantity' AND value > 0
            GROUP BY 1, 2, 3),
        v AS (
            SELECT lower(trim(article)) AS art, year,
                   max(value) AS val_t1, min(tier) AS v_tier
            FROM consensus
            WHERE flow='import' AND measure='value' AND value > 0
            GROUP BY 1, 2),
        o AS (
            SELECT lower(trim(article)) AS art, ukey(unit) AS uk, year,
                   sum(quantity) AS qty_sum, sum(value) AS val_sum,
                   count(*) AS n_countries
            FROM country_year_final
            WHERE quantity > 0 AND value > 0
              AND country NOT LIKE '%(%'
              AND lower(country) NOT LIKE 'total%'
              AND country NOT LIKE '%:%'
            GROUP BY 1, 2, 3)
        SELECT o.art, q.grp, o.uk, o.year, o.n_countries,
               o.qty_sum, q.qty_t1, o.val_sum, v.val_t1, q.q_tier, v.v_tier
        FROM o JOIN q ON o.art = q.art AND o.year = q.year
                     AND (o.uk = q.uk OR o.uk = '' OR q.uk = '')
               JOIN v ON o.art = v.art AND o.year = v.year
        WHERE v.val_t1 >= ?
    """, [a.min_gbp]).fetchall()

    out = []
    for (art, grp, unit, year, n, qs, qt1, vs, vt1, qtier, vtier) in rows:
        qr, vr = qs / qt1, vs / vt1
        # value column intact, quantity column short — or the mirror
        if qr <= a.max_qty and abs(vr - 1) <= a.val_tol:
            side = 'value-intact/qty-short'
        elif vr <= a.max_qty and abs(qr - 1) <= a.val_tol:
            side = 'qty-intact/value-short'
        else:
            continue
        out.append({'side': side, 'article': art, 'group': grp or '',
                    'unit': unit, 'year': year, 'n_countries': n,
                    'qty_ratio': round(qr, 4), 'val_ratio': round(vr, 4),
                    'qty_sum': round(qs), 'qty_t1': round(qt1),
                    'val_sum': round(vs), 'val_t1': round(vt1),
                    'gbp_missing': round(abs(1 - qr) * vt1),
                    'q_tier': qtier, 'v_tier': vtier})

    out.sort(key=lambda r: -r['gbp_missing'])
    dest = BASE / 'reports' / 'column_crossing.csv'
    with open(dest, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]) if out else ['side'])
        w.writeheader()
        w.writerows(out)
    print(f'{len(rows):,} commodity-years with BOTH a quantity and a value '
          f'anchor; {len(out)} flagged -> reports/column_crossing.csv')
    for r in out[:25]:
        print(f"  {r['gbp_missing']:>10,}  {r['article'][:38]:38} {r['year']} "
              f"{r['unit'][:12]:12} qty {r['qty_ratio']:.3f} "
              f"val {r['val_ratio']:.3f}  [{r['side']}]")


if __name__ == '__main__':
    main()
