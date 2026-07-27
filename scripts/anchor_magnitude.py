#!/usr/bin/env python3
"""Anchors that are wrong on their own evidence, with no origin table needed.

Every closure test in this project measures a country table against its printed
national total, so a wrong anchor is invisible to all of them. `anchor_disagreement.py`
covers the case where the volumes disagree AND the payload's origins close on a
losing candidate -- but that test needs origins, and the anchors most likely to
be wrong are exactly the ones nothing else checks.

`Copper, Ore And Regulus` 1888 is the worked example. It read **3,562,071 tons**
between 169,511 in 1887 and 250,567 in 1889 -- wrong by a factor of fifteen, for
a commodity with **no origin table in any year**. It sat in `reconcile_baseline`'s
`nodata` bucket, where no closure metric can score it, and was found by hand.

This screen uses only the Tier-1 series itself:

  Signal QTY     the year against a robust median of its neighbours (a window,
                 so a genuine trend does not fire; the median, so one bad year
                 cannot define the baseline it is judged against).
  Signal PRICE   the year's implied unit price (printed value over printed
                 quantity) against the series' own price history. This is the
                 strong one, because quantity and value are separate columns on
                 the page and rarely fail together: copper 1888 implies
                 GBP1.40/ton against GBP14.80 in 1887 and GBP16.90 in 1889.
  Signal SIB     a sibling series -- the same commodity printed under another
                 label ('Copper, Ore and Regulus' beside 'Metals :Copper, Ore
                 and Regulus') -- carrying a different figure for that year.
                 Where it fires it usually supplies the answer outright.

A year is reported when at least two signals fire, or when PRICE alone fires
hard. One signal on its own is noise: real trade does jump, and a commodity can
genuinely triple in a year.

    python3 scripts/anchor_magnitude.py [--min-signals 2]

  -> reports/anchor_magnitude.csv
"""
import csv
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import duckdb

BASE = Path(__file__).resolve().parent.parent
DB = BASE / 'db' / 'uk_trade.duckdb'
OUT = BASE / 'reports' / 'anchor_magnitude.csv'

WINDOW = 3          # years either side that define "the neighbours"
QTY_HIGH, QTY_LOW = 4.0, 0.25
PRICE_HIGH, PRICE_LOW = 3.0, 1 / 3
PRICE_HARD = 8.0    # a price this far out is reportable on its own
FILLER = {'and', 'or', 'of', 'the', 'a', 'in', 'for', 'total', 'viz'}


def sig(group, article):
    txt = re.sub(r'[^a-z0-9 ]+', ' ', f'{group or ""} {article or ""}'.lower())
    return tuple(sorted(t for t in txt.split() if t and t not in FILLER))


def ratio(x, base):
    return (x / base) if base else None


def main(min_signals=2):
    con = duckdb.connect(str(DB), read_only=True)
    rows = con.execute("""SELECT article_group, article, measure, unit, year, value
        FROM consensus WHERE flow='import' AND value IS NOT NULL AND value > 0
        """).fetchall()

    # The UNIT is part of the series key, not a label on it. The volumes
    # re-denominate lines mid-series (see reports/unit_change_findings.md), and
    # 'Oil: Train or Blubber, and Sperm' is printed in Tons to 1886 and Cwts
    # from 1887. Keyed without the unit, its 1886 tonnage is judged against a
    # neighbour median made of hundredweights and reads 0.033 of it, with a
    # price ratio of 59 -- the detector's own first false positive, and the
    # same class it exists to find.
    qty, val, units = defaultdict(dict), defaultdict(dict), {}
    for g, a, meas, unit, y, v in rows:
        key = (g or '', a or '', unit or '')
        (qty if meas == 'quantity' else val)[key][y] = v
        if meas == 'quantity':
            units[key] = unit

    # sibling index: the same token signature under a different printed label,
    # AND the same unit -- a sibling denominated differently is not comparable
    by_sig = defaultdict(list)
    for key in qty:
        by_sig[(sig(key[0], key[1]), key[2])].append(key)

    out = []
    for key, series in qty.items():
        if len(series) < 5:
            continue
        years = sorted(series)
        # the value series is printed in GBP, so its own 'unit' differs;
        # match it on (group, article) across whatever unit it carries
        vkeys = [k for k in val if k[0] == key[0] and k[1] == key[1]]
        vser = {}
        for vk in vkeys:
            vser.update(val[vk])
        prices = {y: vser[y] / series[y] for y in years if vser.get(y) and series[y]}
        for y in years:
            near = [series[o] for o in years
                    if o != y and abs(o - y) <= WINDOW]
            if len(near) < 3:
                continue
            qr = ratio(series[y], statistics.median(near))
            sig_qty = qr is not None and (qr >= QTY_HIGH or qr <= QTY_LOW)

            pr = None
            if y in prices:
                pnear = [prices[o] for o in years
                         if o != y and abs(o - y) <= WINDOW and o in prices]
                if len(pnear) >= 3:
                    pr = ratio(prices[y], statistics.median(pnear))
            sig_price = pr is not None and (pr >= PRICE_HIGH or pr <= PRICE_LOW)
            hard_price = pr is not None and (pr >= PRICE_HARD or pr <= 1 / PRICE_HARD)

            sib_val = ''
            for other in by_sig[(sig(key[0], key[1]), key[2])]:
                if other != key and other in qty and y in qty[other]:
                    if abs(qty[other][y] - series[y]) > 0.01 * max(qty[other][y], series[y]):
                        sib_val = qty[other][y]
                        break
            sig_sib = bool(sib_val)

            n = sum((sig_qty, sig_price, sig_sib))
            if n < min_signals and not hard_price:
                continue
            out.append({
                'article_group': key[0], 'article': key[1], 'unit': units.get(key, ''),
                'year': y, 'value': round(series[y]),
                'neighbour_median': round(statistics.median(near)),
                'qty_ratio': f'{qr:.3f}' if qr else '',
                'price': f'{prices[y]:.2f}' if y in prices else '',
                'price_ratio': f'{pr:.3f}' if pr else '',
                'sibling_says': sib_val,
                'signals': ''.join(c for c, on in
                                   (('Q', sig_qty), ('P', sig_price), ('S', sig_sib)) if on),
                'n_signals': n,
            })

    out.sort(key=lambda r: (-r['n_signals'],
                            -abs((float(r['qty_ratio']) if r['qty_ratio'] else 1) - 1)))
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]) if out else ['article_group'])
        w.writeheader()
        w.writerows(out)

    print(f'series screened: {len(qty):,}   candidates: {len(out)}')
    by_n = defaultdict(int)
    for r in out:
        by_n[r['signals']] += 1
    for k in sorted(by_n, key=lambda s: -by_n[s]):
        print(f'   signals {k:3s}  {by_n[k]:4d}')
    print(f'-> {OUT}')
    for r in out[:12]:
        print(f"   {r['article_group'][:18]:18s}|{r['article'][:26]:26s} {r['year']} "
              f"{r['value']:>12,} (nbr {r['neighbour_median']:>10,}) "
              f"x{r['qty_ratio']:>7s} price x{r['price_ratio'] or '-':>7s} {r['signals']}")


def selftest():
    """The case this screen was written for, kept as a guard.

    `Copper, Ore And Regulus` 1888 read 3,562,071 tons before it was corrected
    in reference/manual_t1.csv, so the live data can no longer demonstrate it.
    These are the voted figures as they stood, and all three signals must fire:
    a tuning change that silences this has broken the detector."""
    q = {1885: 189573, 1886: 152415, 1887: 169511, 1888: 3562071,
         1889: 250567, 1890: 215935, 1891: 212327}
    v = {1885: 2116615, 1886: 2116615, 1887: 2501198, 1888: 4975790,
         1889: 4234619, 1890: 3910968, 1891: 3910968}
    y = 1888
    near = [q[o] for o in q if o != y and abs(o - y) <= WINDOW]
    qr = q[y] / statistics.median(near)
    price = {o: v[o] / q[o] for o in q}
    pn = [price[o] for o in q if o != y and abs(o - y) <= WINDOW]
    pr = price[y] / statistics.median(pn)
    sib = 230319                      # 'Metals :Copper, Ore and Regulus'
    checks = [('QTY', qr >= QTY_HIGH or qr <= QTY_LOW, f'x{qr:.1f}'),
              ('PRICE', pr >= PRICE_HIGH or pr <= PRICE_LOW, f'x{pr:.3f}'),
              ('SIB', abs(sib - q[y]) > 0.01 * max(sib, q[y]), f'{sib:,}')]
    for name, ok, detail in checks:
        print(f'  {name:6s} {detail:>12s}  {"fires" if ok else "SILENT"}')
    bad = [n for n, ok, _ in checks if not ok]
    print('SELFTEST FAIL: ' + ', '.join(bad) if bad
          else 'SELFTEST PASS: copper 1888 fires all three signals')
    return 1 if bad else 0


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        sys.exit(selftest())
    n = 2
    if '--min-signals' in sys.argv:
        n = int(sys.argv[sys.argv.index('--min-signals') + 1])
    main(n)
