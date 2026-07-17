#!/usr/bin/env python3
"""Reconcile country-table coverage against Tier-1 national totals.

Two detectors born from the 2026-07-16 tobacco / US-cotton recoveries,
operating on the coverage-explorer payload (which already folds label
variants, repairs sticky groups, heals units, and rolls up coast splits):

A) COVERAGE: for each commodity CLUSTER (payload commodities whose token
   signatures are related by subset — 'Wheat' <= 'Corn And Grain — Wheat'
   <= 'Corn, Grain, And Meal — Wheat' are one cluster), compare the summed
   country cells per year against the T1 national quantity (§TOTAL).
   Countries dedup by max across cluster members, so era-label overlap
   never double-counts. Low ratio = origin block missing or mislabelled
   (glue block, stale group) — the trap that hid raw tobacco for 9 years.

B) MISATTRIBUTION (row-slip fingerprint): a slipped block still sums to
   its printed total, so (A) misses it. Flag a country whose quantity in
   one year is >=20x its own median for that commodity AND >=25% of the
   year's total (as_1883 cotton: 'British North America' 11.07M was the
   US's number).

Usage: python3 scripts/build_viz_payload.py /tmp/payload.json
       python3 scripts/reconcile_country_vs_t1.py /tmp/payload.json [min_gbp]
Writes reports/country_t1_reconciliation.csv and
       reports/country_misattribution_flags.csv.
"""
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

BASE = Path('/home/jic823/uk_trade_db')
YEARS = range(1872, 1900)
TK = '§TOTAL'
COAST_RE = re.compile(r'^(.+) \((Atlantic|Pacific|Atlantic & Pacific)\)$')
STOP = {'AND', 'OR', 'THE', 'A', 'AN', 'OF'}


COMPOUND = {'WHEATMEAL': ('WHEAT', 'MEAL'), 'OATMEAL': ('OATS', 'MEAL')}


def toks(name):
    out = set()
    for t in re.split(r"[^A-Z0-9']+", name.upper()):
        if len(t) > 1 and t not in STOP:
            out.update(COMPOUND.get(t, (t,)))
    return frozenset(out)


def main():
    payload_path = sys.argv[1]
    min_gbp = float(sys.argv[2]) if len(sys.argv) > 2 else 500_000
    p = json.load(open(payload_path))

    # junk labels (dash-leader OCR residue, absurd magnitudes) never anchor
    names = [n for n in p
             if ' - -' not in n and len(toks(n)) > 0
             and max((q for c in p[n]['c'].values()
                      for cells in c.values() for _, q, _ in cells),
                     default=0) < 1e11]

    # ---- cluster commodities by token-subset relation (union-find) ----
    tk = {n: toks(n) for n in names}
    parent = {n: n for n in names}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    by_first = defaultdict(list)             # cheap blocking on shared token
    for n in names:
        for t in tk[n]:
            by_first[t].append(n)
    for _, group in by_first.items():
        if len(group) > 400:
            continue                          # generic token, skip blocking
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                if tk[a] <= tk[b] or tk[b] <= tk[a]:
                    union(a, b)

    clusters = defaultdict(list)
    for n in names:
        clusters[find(n)].append(n)

    # ---- gather per-cluster T1 series and country cells ----
    rows_a, rows_b = [], []
    for members in clusters.values():
        t1_cells = []                         # (year, unit, qty)
        unit_votes = Counter()
        cty = defaultdict(dict)               # (country, unit) -> {year: qty}
        gbp = sum(p[m].get('v') or 0 for m in members)
        for m in members:
            for country, units in p[m]['c'].items():
                for u, cells in units.items():
                    for y, q, r in cells:
                        if y not in YEARS:
                            continue
                        if country == TK:
                            t1_cells.append((y, u, q))
                            unit_votes[u] += 1
                        else:
                            k = (country, u)
                            cty[k][y] = max(cty[k].get(y, 0), q)
        if len(t1_cells) < 4 or gbp < min_gbp:
            continue
        t1u = unit_votes.most_common(1)[0][0]
        # T1 in the modal unit only, junk-clamped: a lone 72-billion 'Lbs'
        # misread must not become the yardstick
        t1 = {}
        for y, u, q in t1_cells:
            if u == t1u:
                t1[y] = max(t1.get(y, 0), q)
        if len(t1) < 4:
            continue
        med0 = median(t1.values())
        t1 = {y: q for y, q in t1.items() if q <= 30 * med0}
        if len(t1) < 4:
            continue
        label = max(members, key=lambda m: p[m].get('v') or 0)

        # country sum per year, strictly in the T1 unit — after healing,
        # a surviving '?' cell means magnitude-incompatible, i.e. a
        # different measure; coast children skipped when their parent
        # country carries the year
        csum = defaultdict(float)
        for (country, u), ys in cty.items():
            if u != t1u:
                continue
            m = COAST_RE.match(country)
            for y, q in ys.items():
                if m:
                    par = m.group(1)
                    if any(y in cty.get((par, uu), {}) for uu in (t1u, '?')):
                        continue              # parent carries it (roll-up)
                csum[y] += q

        med_t1 = median(t1.values())
        for y, tq in sorted(t1.items()):
            if tq <= 0 or tq < 0.05 * med_t1:
                continue                      # T1 misread, not coverage
            ratio = csum.get(y, 0) / tq
            if ratio < 0.6 or ratio > 1.9:
                rows_a.append({'commodity': label, 'year': y,
                               'kind': 'missing/short' if ratio < 0.6 else 'overcount',
                               'ratio': round(ratio, 3), 't1_qty': round(tq),
                               'country_sum': round(csum.get(y, 0)),
                               'cluster_gbp': round(gbp)})

        # ---- detector B on the same cluster ----
        tot_by_year = defaultdict(float)
        for (country, u), ys in cty.items():
            if u in (t1u, '?'):
                for y, q in ys.items():
                    tot_by_year[y] += q
        for (country, u), ys in cty.items():
            if u not in (t1u, '?') or len(ys) < 4 or COAST_RE.match(country):
                continue
            med = median(ys.values())
            if med <= 0:
                continue
            for y, q in ys.items():
                if (q >= 20 * med and q >= 0.25 * tot_by_year.get(y, q)
                        and q > 100_000):
                    rows_b.append({'commodity': label, 'year': y,
                                   'country': country, 'qty': round(q),
                                   'median_other_years': round(med),
                                   'spike_x': round(q / med, 1),
                                   'cluster_gbp': round(gbp)})

    rows_a.sort(key=lambda r: (r['kind'] != 'missing/short', -r['cluster_gbp']))
    rows_b.sort(key=lambda r: -r['cluster_gbp'])
    outa = BASE / 'reports' / 'country_t1_reconciliation.csv'
    with open(outa, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['commodity', 'year', 'kind', 'ratio',
                                          't1_qty', 'country_sum', 'cluster_gbp'])
        w.writeheader()
        w.writerows(rows_a)
    outb = BASE / 'reports' / 'country_misattribution_flags.csv'
    with open(outb, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['commodity', 'year', 'country', 'qty',
                                          'median_other_years', 'spike_x',
                                          'cluster_gbp'])
        w.writeheader()
        w.writerows(rows_b)
    short = [r for r in rows_a if r['kind'] == 'missing/short']
    print(f'detector A: {len(short)} missing/short + '
          f'{len(rows_a) - len(short)} overcount (cluster GBP >= {min_gbp:,.0f})'
          f' -> {outa}')
    print(f'detector B: {len(rows_b)} spike flags -> {outb}')


if __name__ == '__main__' and '--series' not in sys.argv:
    main()


def country_series_anomalies(payload_path, min_gbp=500_000,
                             out=BASE / 'reports' / 'country_series_anomalies.csv'):
    """Detectors C+D — the checks the user kept doing by historical intuition:

    C) HOLES: a country that supplies a commodity for a long run should not
       vanish for interior years (Ceylon coffee 1879/82/86-88; SA wool 1877
       before repair). Flag interior missing years of series with >= 6
       observed years, weighted by the country's median share.
    D) DIPS/SPIKES: a single year < 1/4 or > 4x the series median with
       normal neighbours is a digit-slip or misattribution, not trade
       history (SA wool 1883 = 18.9M between 53.9M and 51.3M; Ceylon
       coffee 1874 = 30,195 between ~750k years).

    Ranked by commodity GBP x country share. Run after every integrate.
    """
    p = json.load(open(payload_path))
    # human adjudications: flags investigated and CLOSED (genuine trade
    # swings, display artifacts, printed-regime chips) stop resurfacing;
    # open items are never listed here
    adjudicated = set()
    adjf = BASE / 'reference' / 'anomaly_adjudications.csv'
    if adjf.exists():
        for r in csv.DictReader(open(adjf)):
            adjudicated.add((r['kind'], r['commodity'], r['country'],
                             int(r['year'])))
    # coast/port drill-down series ('United States Of America (Atlantic)',
    # 'Russia (Southern Ports)') hole structurally in years the table
    # printed the parent line only — not a data loss when the parent
    # covers the year
    coastish = re.compile(r'^(.+) \((?:Atlantic|Pacific|Atlantic & Pacific|'
                          r'Northern Ports|Southern Ports|'
                          r'Exclusive Of Hong Kong)\)$')
    n_sup = 0
    rows = []
    for name, d in p.items():
        gbp = d.get('v') or 0
        if gbp < min_gbp or ' - -' in name:
            continue
        # commodity totals per (unit, year) to weight countries by SHARE —
        # the user-found errors were all top suppliers; minor origins are
        # genuinely volatile and must not swamp the report
        tot = {}
        series = {}
        for cty, units in d['c'].items():
            if cty == TK or ' : ' in cty:
                continue
            for u, cells in units.items():
                by_y = {}
                for y, q, r in cells:
                    if y in YEARS and q > 0:
                        by_y[y] = max(by_y.get(y, 0), q)
                if by_y:
                    series[(cty, u)] = by_y
                    for y, q in by_y.items():
                        tot[(u, y)] = tot.get((u, y), 0) + q
        for (cty, u), by_y in series.items():
            if len(by_y) < 6:
                continue
            shares = [q / tot[(u, y)] for y, q in by_y.items() if tot[(u, y)] > 0]
            weight = median(shares) if shares else 0
            if weight < 0.04:
                continue                      # minor origin: skip
            ys = sorted(by_y)
            med = median(by_y.values())
            if med <= 0:
                continue
            prio = round(gbp * weight)
            # holes only for CONSISTENT suppliers (>=70% of span present)
            span = ys[-1] - ys[0] + 1
            cm = coastish.match(cty)
            if len(by_y) / span >= 0.7:
                for y in range(ys[0] + 1, ys[-1]):
                    if y not in by_y:
                        if cm and y in series.get((cm.group(1), u), ()):
                            n_sup += 1        # parent covers the year
                            continue
                        if ('hole', name, cty, y) in adjudicated:
                            n_sup += 1
                            continue
                        rows.append({'kind': 'hole', 'commodity': name,
                                     'country': cty, 'unit': u, 'year': y,
                                     'series_median': round(med),
                                     'value': '', 'ratio_to_median': '',
                                     'gbp': prio})
            for y in ys:
                q = by_y[y]
                lo, hi = med / 4, med * 4
                if q < lo or q > hi:
                    nb = [by_y.get(y - 1), by_y.get(y + 1)]
                    nb = [v for v in nb if v is not None]
                    if nb and all(lo <= v <= hi for v in nb):
                        kind = 'dip' if q < lo else 'spike'
                        if (kind, name, cty, y) in adjudicated:
                            n_sup += 1
                            continue
                        rows.append({'kind': kind,
                                     'commodity': name, 'country': cty,
                                     'unit': u, 'year': y,
                                     'series_median': round(med),
                                     'value': round(q),
                                     'ratio_to_median': round(q / med, 3),
                                     'gbp': prio})
    rows.sort(key=lambda r: -r['gbp'])
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['kind', 'commodity', 'country',
                                          'unit', 'year', 'value',
                                          'series_median', 'ratio_to_median',
                                          'gbp'])
        w.writeheader()
        w.writerows(rows)
    n = Counter(r['kind'] for r in rows)
    print(f"detector C/D: {n.get('hole',0)} holes, {n.get('dip',0)} dips, "
          f"{n.get('spike',0)} spikes "
          f"({n_sup} suppressed: adjudicated/structural) -> {out}")


if __name__ == '__main__' and '--series' in sys.argv:
    country_series_anomalies(sys.argv[1],
                             float(sys.argv[3]) if len(sys.argv) > 3 else 500_000)
