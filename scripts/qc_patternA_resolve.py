#!/usr/bin/env python3
"""Pattern-A resolver: blocks where obs and twoup hold IDENTICAL values but
pairings offset by one (obs extra head-label, twoup extra tail-label), and the
printed TOTAL (or T1) exceeds both sums by one lost member.

For each: residual R = TOTAL - sum. Hypothesis OBS (obs pairing right, lost
member = twoup's extra label, value R) vs hypothesis TWOUP (twoup pairing
right, lost member = obs's extra label, value R). Score each: pairing bracket
fit + residual bracket fit vs that label's own series. Print decision table.
"""
import math
import sys
from collections import Counter, defaultdict
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
import duckdb
import validate_gold as V

con = duckdb.connect('/home/jic823/uk_trade_db/db/uk_trade.duckdb', read_only=True)

fin_all = defaultdict(list)
series = defaultdict(dict)
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

t1q = defaultdict(Counter)
for fl, g, a, u, y, val in con.execute("""
        SELECT flow, article_group, article, unit, year, value
        FROM abstract_obs WHERE measure='quantity' AND value IS NOT NULL""").fetchall():
    a2 = (a or '').replace('&amp;', '&')
    g2 = (g or '').replace('&amp;', '&')
    asig = V.sig(a2) or V.sig(f"{g2} {a2}")
    if asig:
        t1q[(asig, int(y), fl)][round(val)] += 1


def brk(asig, cn, y, q):
    """Is q within 3x of geomean of nearest<=2 neighbour years?"""
    sr = series.get((asig, cn), {})
    neigh = sorted((abs(yy - y), vv) for yy, vv in sr.items() if yy != y and vv)
    if not neigh or not q or q <= 0:
        return None
    vals = [vv for _, vv in neigh[:2]]
    gm = math.exp(sum(math.log(v) for v in vals) / len(vals))
    return (gm / 3 <= q <= gm * 3), gm


def pair_score(asig, y, pairs):
    ok = tested = 0
    for cn, q in pairs:
        r = brk(asig, cn, y, q)
        if r is None:
            continue
        tested += 1
        ok += bool(r[0])
    return (ok / tested if tested else None), tested


for key, rows in sorted(fin_all.items(), key=lambda kv: str(kv[0])):
    frows = [(c, q, v) for src, g, a, c, u, q, v in rows if src == 'twoup']
    if len(frows) < 4:
        continue
    fmap = {}
    for c, q, v in frows:
        cn = V.cnorm(c or '')
        if cn and ' : ' not in (c or ''):
            fmap.setdefault(cn, (q, v))
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
                    if fmap[c][0] and bmap[c] and round(fmap[c][0]) == round(bmap[c]))
        valhit = sum(1 for c in shared if fmap[c][0] and round(fmap[c][0]) in bvals)
        rec = (agree / len(shared), valhit / len(shared), len(shared), blkkey)
        if best is None or rec[0] > best[0] or (rec[0] == best[0] and rec[1] > best[1]):
            best = rec
    if best is None or best[0] > 0.15 or best[1] < 0.5:
        continue
    asig, y = key
    agree, valhit, nsh, blkkey = best
    fl, vol, og, oa = blkkey
    brows = obs[key][blkkey]
    members = [(V.cnorm(c or ''), q, v, seq) for c, q, v, seq in brows
               if not (V.cnorm(c or '').startswith('total')
                       or (c or '').strip().upper() == 'TOTAL')]
    totals = [(q, v, seq) for c, q, v, seq in brows
              if V.cnorm(c or '').startswith('total')
              or (c or '').strip().upper() == 'TOTAL']
    oq = sum(q for _, q, _, _ in members if q)
    ov = sum(v for _, _, v, _ in members if v)
    tqv = [(q, v) for q, v in fmap.values()]
    tq = sum(q for q, v in tqv if q)
    ob_lab = [cn for cn, q, v, seq in members]
    only_obs = [l for l in ob_lab if l not in fmap]
    only_tw = [l for l in fmap if l not in set(ob_lab)]
    if not (abs(oq - tq) < 1 and len(only_obs) == 1 and len(only_tw) == 1):
        continue                       # not pattern A
    L_h, L_t = only_obs[0], only_tw[0]
    # residual from grand TOTAL (largest TOTAL row) or T1
    t1c = t1q.get((asig, y, fl), Counter())
    t1val = t1c.most_common(1)[0][0] if t1c else None
    grand = max((q for q, v, s in totals if q), default=None)
    tgt = grand if grand and grand > oq else t1val
    R = (tgt - oq) if tgt else None
    r_h = brk(asig, L_h, y, R) if R else None    # residual as L_h (twoup hyp)
    r_t = brk(asig, L_t, y, R) if R else None    # residual as L_t (obs hyp)
    s_obs, n_o = pair_score(asig, y, [(cn, q) for cn, q, v, s in members])
    s_tw, n_t = pair_score(asig, y, [(cn, q) for cn, (q, v) in fmap.items()])
    fmt = lambda r: 'n/a' if r is None else f"{'IN' if r[0] else 'OUT'}(gm={r[1]:,.0f})"
    print(f"== {y} {vol} [{og}|{oa}] head={L_h} tail={L_t}")
    print(f"   sum={oq:,.0f} grand={grand and f'{grand:,.0f}'} T1={t1val and f'{t1val:,.0f}'} R={R and f'{R:,.0f}'}")
    print(f"   pairing: obs={s_obs and f'{s_obs:.0%}'}/{n_o} twoup={s_tw and f'{s_tw:.0%}'}/{n_t}")
    print(f"   residual-as-{L_h} (TWOUP hyp): {fmt(r_h)}   residual-as-{L_t} (OBS hyp): {fmt(r_t)}")
