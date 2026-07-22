#!/usr/bin/env python3
"""Round-22 stage 2: bracket adjudication for the 51 closure-defective
slipped-twoup candidates. For each candidate, score BOTH pairings (obs vs
final's twoup) against the commodity-country series in neighbouring years
(within 3x of the nearest-2-neighbour geometric mean = in-bracket). Obs
pairing decisively better -> emit groupfix + supersede (partial blocks =
honest tail gaps, noted). Ties / thin series stay queued.
"""
import csv
import math
import sys
from collections import Counter, defaultdict
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
import duckdb
import validate_gold as V

SCRATCH = '/tmp/claude-1000/-home-jic823-uk-trade-db/d5984194-844f-4fe0-9531-c1febfff6934/scratchpad'
con = duckdb.connect('/home/jic823/uk_trade_db/db/uk_trade.duckdb', read_only=True)

fin_all = defaultdict(list)
series = defaultdict(dict)           # (asig, cnorm) -> {year: qty}
for src, g, a, c, u, y, q, v in con.execute("""
        SELECT source, article_group, article, country, unit, year, quantity, value
        FROM country_year_final""").fetchall():
    asig = V.sig(a or '') or V.sig(f"{g or ''} {a or ''}")
    if not asig:
        continue
    fin_all[(asig, int(y))].append((src, g, a, c, u, q, v))
    cn = V.cnorm(c or '')
    if cn and q:
        series[(asig, cn)].setdefault(int(y), q)

obs = defaultdict(lambda: defaultdict(list))
for vol, fl, g, a, c, u, y, q, v, seq in con.execute("""
        SELECT volume, flow, article_group, article, country_raw, unit, year,
               quantity, value, row_seq
        FROM country_obs WHERE quantity IS NOT NULL
        ORDER BY volume, row_seq""").fetchall():
    asig = V.sig(a or '') or V.sig(f"{g or ''} {a or ''}")
    if asig:
        obs[(asig, int(y))][(fl, vol, g, a)].append((c, q, v, seq))


def bracket_score(asig, y, pairs, exclude_sources_year):
    """pairs: [(cnorm, qty)]. Score = fraction of testable pairs whose qty is
    within 3x of the geometric mean of the nearest <=2 neighbour-year values
    (neighbour years exclude y itself). Testable needs >=1 neighbour."""
    ok = tested = 0
    for cn, q in pairs:
        if not q:
            continue
        sr = series.get((asig, cn), {})
        neigh = sorted((abs(yy - y), vv) for yy, vv in sr.items()
                       if yy != y and vv)
        if not neigh:
            continue
        vals = [vv for _, vv in neigh[:2]]
        gm = math.exp(sum(math.log(v) for v in vals) / len(vals))
        tested += 1
        if gm / 3 <= q <= gm * 3:
            ok += 1
    return (ok / tested if tested else None), tested


candidates = []
for key, rows in fin_all.items():
    frows = [(c, q, v, g, a, u) for src, g, a, c, u, q, v in rows if src == 'twoup']
    if len(frows) < 4:
        continue
    fmap = {}
    for c, q, v, g, a, u in frows:
        cn = V.cnorm(c or '')
        if cn and ' : ' not in (c or ''):
            fmap.setdefault(cn, q)
    if len(fmap) < 4:
        continue
    best = None
    for blkkey, brows in obs.get(key, {}).items():
        bmap, bvals = {}, set()
        for c, q, v, seq in brows:
            cn = V.cnorm(c or '')
            if cn.startswith('total') or not cn:
                continue
            bmap.setdefault(cn, q)
            if q:
                bvals.add(round(q))
        shared = set(fmap) & set(bmap)
        if len(shared) < 4:
            continue
        agree = sum(1 for c in shared
                    if fmap[c] and bmap[c] and round(fmap[c]) == round(bmap[c]))
        valhit = sum(1 for c in shared if fmap[c] and round(fmap[c]) in bvals)
        rec = (agree / len(shared), valhit / len(shared), len(shared), blkkey)
        if best is None or rec[0] > best[0] or (rec[0] == best[0] and rec[1] > best[1]):
            best = rec
    if best is None or best[0] > 0.15 or best[1] < 0.5:
        continue
    candidates.append((key, best, fmap))

print(f"{len(candidates)} candidates for bracket adjudication")
auto, queue = [], []
for (asig, y), (agree, valhit, nsh, blkkey), fmap in candidates:
    fl, vol, og, oa = blkkey
    brows = obs[(asig, y)][blkkey]
    members = [(V.cnorm(c or ''), q, v, seq, c) for c, q, v, seq in brows
               if not (V.cnorm(c or '').startswith('total')
                       or (c or '').strip().upper() == 'TOTAL')]
    obs_pairs = [(cn, q) for cn, q, v, seq, c in members]
    two_pairs = list(fmap.items())
    s_obs, n_obs = bracket_score(asig, y, obs_pairs, None)
    s_two, n_two = bracket_score(asig, y, two_pairs, None)
    labels = sorted({((g or '').upper(), (a or '').strip(), src)
                     for src, g, a, c, u, q, v in fin_all[(asig, y)]
                     if src in ('twoup', 'runin', 'infonly')})
    seq_lo = min(seq for cn, q, v, seq, c in members)
    seq_hi = max(seq for c, q, v, seq in brows)
    rec = dict(asig=asig, y=y, fl=fl, vol=vol, og=og, oa=oa,
               s_obs=s_obs, n_obs=n_obs, s_two=s_two, n_two=n_two,
               labels=labels, seq_lo=seq_lo, seq_hi=seq_hi,
               nmem=len(members), nsh=nsh, valhit=valhit)
    # decisive: obs pairing fits brackets >=80% on >=4 testable pairs AND
    # beats the twoup pairing by >=25 points
    if (s_obs is not None and n_obs >= 4 and s_obs >= 0.8
            and (s_two is None or s_obs - s_two >= 0.25)):
        auto.append(rec)
    else:
        queue.append(rec)

print(f"auto (bracket-decisive): {len(auto)}, queued: {len(queue)}")
for r in auto:
    print(f"  AUTO {r['y']} {r['vol']} {r['fl']} [{r['og']}|{r['oa']}] "
          f"obs={r['s_obs']:.0%}/{r['n_obs']} twoup="
          f"{'-' if r['s_two'] is None else format(r['s_two'], '.0%')}/{r['n_two']}")
for r in queue:
    print(f"  Q    {r['y']} {r['vol']} {r['fl']} [{r['og']}|{r['oa']}] "
          f"obs={'-' if r['s_obs'] is None else format(r['s_obs'], '.0%')}/{r['n_obs']} "
          f"twoup={'-' if r['s_two'] is None else format(r['s_two'], '.0%')}/{r['n_two']}")

import json
with open(f'{SCRATCH}/bracket_auto.json', 'w') as f:
    json.dump([{k: v for k, v in r.items() if k != 'labels'} |
               {'labels': [list(l) for l in r['labels']]} for r in auto], f, indent=1)
