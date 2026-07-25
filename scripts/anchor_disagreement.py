#!/usr/bin/env python3
"""Cross-volume ANCHOR disagreement report.

Every closure test in this project measures a country table against its
printed national total, so a wrong anchor is invisible to all of them: the
table can be perfect and still read 0.81, or be missing a section and still
read 1.000. Two wrong anchors were found by hand in one session (oil seed
cake 1890, flax and linseed 1899) and both had the same shape — the Abstract
prints a year up to five times (the 1893+ five-year comparative tables), the
printings do not agree, and reconcile.py's vote picked the wrong one.

This report keeps what the vote throws away. For every series-year it lists
every distinct reading with the volumes and engines behind it, ranks by the
year's own printed VALUE, and — the part that makes it actionable — scores
the payload's origin sum against each candidate. When the origins close on a
LOSING candidate the vote is probably wrong; that is the queue for
reference/manual_t1.csv.

    python3 scripts/anchor_disagreement.py [--measure quantity|value|both]

  -> reports/anchor_disagreements.csv
"""
import csv
import json
import pickle
import sys
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reconcile import build_series, _sig                 # noqa: E402

BASE = Path(__file__).resolve().parent.parent
CLOSE = 0.01        # origins "close on" a candidate within 1%
APART = 0.03        # ...and are meaningfully away from the winner beyond 3%


def payload_index(path):
    """(year, t1_value) -> [(commodity, unit)]. The payload's §TOTAL cells ARE
    the voted anchors, so an exact value match on the same year links a
    consensus series-year to the commodity the map ships without replaying
    curation. Deliberately NOT keyed on the unit: the payload normalizes unit
    spellings ('Cwts.' -> 'Cwt') and consensus keeps the printed one."""
    p = json.load(open(path))
    idx = defaultdict(list)
    for name, entry in p.items():
        c = entry.get('c') or {}
        t1 = c.get('§TOTAL') or {}
        for unit, rows in t1.items():
            for row in rows:
                y, q = row[0], row[1]
                if q:
                    idx[(y, round(float(q)))].append((name, unit))
    return p, idx


def origin_sum(payload, name, unit, year):
    tot, n = 0.0, 0
    for ctry, byunit in (payload[name].get('c') or {}).items():
        if ctry == '§TOTAL' or '(' in ctry:
            continue
        for row in byunit.get(unit, ()):
            if row[0] == year and row[1]:
                tot += row[1]
                n += 1
    return tot, n


def main():
    measures = {'quantity', 'value'}
    if '--measure' in sys.argv:
        m = sys.argv[sys.argv.index('--measure') + 1]
        if m != 'both':
            measures = {m}

    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)
    # the cell matcher is a 4-minute pass; --cache reuses it while iterating
    # on the report itself. Delete the file after re-parsing or re-voting.
    cache = Path(sys.argv[sys.argv.index('--cache') + 1]) \
        if '--cache' in sys.argv else None
    if cache and cache.exists():
        series = pickle.loads(cache.read_bytes())
        print(f'series loaded from cache: {cache}')
    else:
        series = build_series(con)
        if cache:
            cache.write_bytes(pickle.dumps(series))

    # voted result + tier, and the year's printed GBP for ranking. consensus
    # stores the PRINTED label of the first observation, not the canonical
    # series key, so join on that; the GBP side joins on the token signature
    # because the value line's printed label varies independently.
    voted, gbp = {}, {}
    for flow, meas, g, a, y, val, tier in con.execute(
            '''SELECT flow, measure, article_group, article, year, value, tier
               FROM consensus''').fetchall():
        voted[(flow, meas, g, a, y)] = (val, tier)
        if meas == 'value':
            gbp[(flow, y, _sig(g, a))] = val

    payload, idx = payload_index(BASE / 'exports' / 'viz_payload.json')

    rows = []
    seen = Counter()
    for (flow, meas, g, a, y), obs in series.items():
        if flow != 'import' or meas not in measures:
            continue
        reads = [(eng, v, o[5]) for o in obs for eng, v in o[6]]
        # readings are rounded to the pound/unit before comparison: the two
        # engines differ by <0.5 on cells the vote already calls verified
        cand = defaultdict(list)
        for eng, v, vol in reads:
            cand[round(v)].append(f'{vol}/{eng}')
        seen[meas] += 1
        if len(cand) < 2:
            continue
        seen[meas + '_dis'] += 1

        unit, grp, art = obs[0][2], obs[0][3], obs[0][4]
        win, tier = voted.get((flow, meas, grp, art, y), (None, ''))
        if win is None:
            continue
        win = round(win)
        lo, hi = min(cand), max(cand)
        spread = (hi - lo) / hi if hi else 0

        # link to the payload commodity via the anchor's own value
        names = idx.get((y, win), []) if meas == 'quantity' else []
        name, punit = names[0] if len(names) == 1 else ('', '')
        osum, n_orig = origin_sum(payload, name, punit, y) if name else (0, 0)

        verdict, favours = '', ''
        if osum:
            best = min(cand, key=lambda c: abs(osum - c) / max(c, 1))
            d_best = abs(osum - best) / max(best, 1)
            d_win = abs(osum - win) / max(win, 1)
            if d_best <= CLOSE and best != win and d_win > APART:
                verdict, favours = 'ORIGINS-FAVOUR-LOSER', best
            elif d_win <= CLOSE:
                verdict = 'origins-confirm-winner'

        rows.append({
            'gbp': round(gbp.get((flow, y, _sig(grp, art)), 0) or 0),
            'verdict': verdict,
            'measure': meas,
            'group': g, 'article': a, 'year': y, 'unit': unit,
            'winner': win, 'tier': tier,
            'favours': favours,
            'origin_sum': round(osum), 'n_origins': n_orig,
            'origin_ratio': round(osum / win, 4) if win else '',
            'spread_pct': round(100 * spread, 2),
            'n_readings': len(reads),
            'candidates': ' | '.join(
                f'{v:,} [{len(src)}: {",".join(sorted(src))}]'
                for v, src in sorted(cand.items(), key=lambda kv: -len(kv[1]))),
            'commodity': name or ('AMBIGUOUS' if len(names) > 1 else ''),
        })

    rows.sort(key=lambda r: (r['verdict'] != 'ORIGINS-FAVOUR-LOSER', -r['gbp']))
    out = BASE / 'reports' / 'anchor_disagreements.csv'
    with open(out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    for meas in sorted(measures):
        n, d = seen[meas], seen[meas + '_dis']
        print(f'{meas:9s}: {d:,} of {n:,} series-years have disagreeing '
              f'readings ({100 * d / max(n, 1):.1f}%)')
    bad = [r for r in rows if r['verdict'] == 'ORIGINS-FAVOUR-LOSER']
    ok = [r for r in rows if r['verdict'] == 'origins-confirm-winner']
    print(f'origins confirm the winner: {len(ok):,}')
    print(f'ORIGINS FAVOUR A LOSER:     {len(bad):,}   '
          f'(GBP {sum(r["gbp"] for r in bad):,})')
    for r in bad[:25]:
        print(f'  GBP{r["gbp"]:>12,}  {r["year"]}  {r["group"]} | '
              f'{r["article"]}  vote {r["winner"]:,} -> {r["favours"]:,} '
              f'(origins {r["origin_sum"]:,})')
    print(f'-> {out}  ({len(rows):,} rows)')


if __name__ == '__main__':
    main()
