#!/usr/bin/env python3
"""Round-22 systematic audit: twoup-vs-obs agreement test (round-19 test,
generalized). For every twoup-sourced block in country_year_final, compare
against country_obs blocks (import / export_uk / reexport) with the same
article-sig + year:
  - agree  = fraction of shared countries whose quantity matches exactly
  - valhit = fraction of twoup quantities present ANYWHERE in the obs block
             (values exist but on wrong countries -> slip signature)
Flag: agree ~ 0 but valhit high, >=4 shared countries.
"""
import sys
from collections import defaultdict
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
import duckdb
import validate_gold as V

con = duckdb.connect('/home/jic823/uk_trade_db/db/uk_trade.duckdb', read_only=True)

# final twoup blocks keyed by (asig, year)
fin = defaultdict(list)
for g, a, c, u, y, q, v in con.execute("""
        SELECT article_group, article, country, unit, year, quantity, value
        FROM country_year_final WHERE source='twoup'""").fetchall():
    asig = V.sig(a or '') or V.sig(f"{g or ''} {a or ''}")
    if not asig:
        continue
    fin[(asig, int(y))].append((c, q, v, g, a, u))

# obs blocks per flow keyed by (asig, year); keep per (volume, group, article)
obs = defaultdict(lambda: defaultdict(list))
for vol, fl, g, a, c, u, y, q, v in con.execute("""
        SELECT volume, flow, article_group, article, country_raw, unit, year,
               quantity, value
        FROM country_obs WHERE quantity IS NOT NULL""").fetchall():
    asig = V.sig(a or '') or V.sig(f"{g or ''} {a or ''}")
    if not asig:
        continue
    obs[(asig, int(y))][(fl, vol, g, a)].append((c, q, v))

rows_out = []
for key, frows in fin.items():
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
        bmap = {}
        bvals = set()
        for c, q, v in brows:
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
        valhit = sum(1 for c in shared
                     if fmap[c] and round(fmap[c]) in bvals)
        rec = (agree / len(shared), valhit / len(shared), len(shared), blkkey)
        if best is None or rec[0] > best[0] or (rec[0] == best[0] and rec[1] > best[1]):
            best = rec
    if best is None:
        continue
    agree, valhit, nsh, blkkey = best
    if agree <= 0.15 and valhit >= 0.5:
        asig, y = key
        g0, a0 = frows[0][3], frows[0][4]
        rows_out.append((valhit, agree, nsh, y, g0, a0, blkkey[0], blkkey[1],
                         blkkey[3]))

rows_out.sort(key=lambda r: (str(r[5] or ''), r[3]))
print(f"{len(rows_out)} candidate slipped twoup blocks "
      f"(agree<=15%, values present >=50%, >=4 shared countries):")
for valhit, agree, nsh, y, g0, a0, fl, vol, aobs in rows_out:
    print(f"  {y} twoup[{g0}|{a0}] vs obs[{fl} {vol}|{aobs}] "
          f"shared={nsh} agree={agree:.0%} valhit={valhit:.0%}")
