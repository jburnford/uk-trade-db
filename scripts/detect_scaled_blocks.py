#!/usr/bin/env python3
"""Blocks whose VALUE column is a power of ten off -- every member row and
the printed TOTAL alike, so section closure is exact and nothing else sees
it. as_1877 carpets: 9,812,106 for 6.45M yards (1.52 GBP/yd) against 0.13
in 1876 and 0.12 in 1878; the whole block is x10 (a digit glued onto the
value column). as_1881 carpets the same. Woollens to Canada read 3.75M
instead of ~2.2M that year.

Detector: per (volume, flow, year, group, article) block with quantities,
the median unit price over member rows; compared with the median unit price
of the same (family, article key) across all OTHER volumes. A ratio within
[7, 14] (or its inverse, or x100) on a block whose own rows agree (IQR of
row prices tight) is a scaled block. Value-only blocks: the block's printed
grand TOTAL against the median of the same section's TOTAL in the two
volumes either side.

Usage: python3 scripts/detect_scaled_blocks.py [--flow all|export_uk|reexport] [--out reference/scaled_block_repairs.csv]
"""
import argparse, collections, csv, math, re, statistics as st, sys
from pathlib import Path
import duckdb
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phantom_articles import fix_articles, known_groups, promote_headings, _key, load_splits, apply_splits
import build_capture_reassign as cap

TOTAL_RE = re.compile(r'\bTOTAL\b', re.I)
def is_total(c): return bool(c) and bool(TOTAL_RE.search(c))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='db/uk_trade.duckdb')
    ap.add_argument('--flow', default='all')
    ap.add_argument('--out', default=None)
    ap.add_argument('--min-rows', type=int, default=4)
    a = ap.parse_args()
    con = duckdb.connect(a.db, read_only=True)
    flows = ['export_uk', 'reexport'] if a.flow == 'all' else [a.flow]
    writer = None
    if a.out:
        fh = open(a.out, 'w', newline='')
        writer = csv.writer(fh)
        writer.writerow(['volume', 'year', 'flow', 'article_group', 'article', 'country_raw',
                         'old_value', 'new_value', 'witnesses'])
    for flow in flows:
        run(con, a, flow, writer)


def run(con, a, flow, writer):
    rows = con.execute("""select volume, flow, year, coalesce(article_group,''), article, unit,
                          row_seq, country_raw, value, quantity from country_obs where flow=?""", [flow]).fetchall()
    fixed = apply_splits(rows, load_splits(flow=flow), vol=0, flow=1, year=2, group=3, art=4, seq=6, unit=5)
    fixed = fix_articles(fixed, vol=0, flow=1, year=2, group=3, art=4, unit=5, seq=6)
    fixed = promote_headings(fixed, known_groups(con, flow), vol=0, flow=1, year=2, group=3, art=4)
    # family fold for comparison keys
    folds, fam = {}, {}
    for r in csv.DictReader(open('reference/group_name_folds.csv')):
        if r['flow'] == flow: folds[r['raw_group']] = r['canonical']
    for r in csv.DictReader(open('reference/export_group_families.csv')):
        if r['flow'] == flow: fam[r['canonical']] = r['family']
    def family(g):
        c = folds.get(g, g); return fam.get(c, c)
    blocks = collections.defaultdict(list)
    for r, f in zip(rows, fixed):
        blocks[(f[0], f[2], f[3], f[4] or '', f[5] or '')].append((f[6], f[7], f[9], f[8], r[3], r[4]))
    # own-year only
    own = {}
    for (vol, yr, *_ ) in blocks: own[vol] = max(own.get(vol, 0), yr)
    # per block: median price; block total (grand) ; members
    info = {}
    for k, rws in blocks.items():
        vol, yr, g, art, unit = k
        rws.sort()
        mem = [r for r in rws if not is_total(r[1]) and r[3]]
        prices = [r[3] / r[2] for r in mem if r[2]]
        tot = [r[3] for r in rws if is_total(r[1]) and r[3]]
        info[k] = dict(n=len(mem), prices=prices, total=max(tot) if tot else None,
                       msum=sum(r[3] for r in mem), fam=family(g), akey=_key(art), rows=rws)
    # neighbours: the same (family, article key) in the nearest own-year
    # volumes either side (within 3 years), price and section total
    def yr_of(v): return 1900 if v == 'tn_1901' else 1870 if v == 'tn_1871' else int(v[-4:])
    byk = collections.defaultdict(dict)   # (fam, akey) -> vol -> info (own-year blocks)
    for k, i in info.items():
        vol, yr, g, art, unit = k
        if yr != own[vol]:
            continue
        # a bare-group block is heterogeneous when the group has other
        # articles in this volume: skip it as a comparison unit
        if art == '' and any(kk[0] == vol and kk[1] == yr and kk[2] == g and kk[3] for kk in info):
            continue
        byk[(i['fam'], i['akey'])][vol] = i
    def neighbours(fam, akey, vol):
        y = yr_of(vol)
        vs = [(abs(yr_of(v) - y), v) for v in byk.get((fam, akey), {}) if v != vol and abs(yr_of(v) - y) <= 3]
        before = sorted((d, v) for d, v in vs if yr_of(v) < y)[:2]
        after = sorted((d, v) for d, v in vs if yr_of(v) > y)[:2]
        return [v for _, v in before], [v for _, v in after]
    def med(xs): return st.median(xs) if xs else None
    out = []
    for k, i in info.items():
        vol, yr, g, art, unit = k
        if yr != own[vol] or (i['fam'], i['akey']) not in byk or vol not in byk[(i['fam'], i['akey'])]:
            continue
        if i['n'] < a.min_rows:
            continue
        bef, aft = neighbours(i['fam'], i['akey'], vol)
        if not bef or not aft:
            continue
        # an ISLAND: the block is x10 (or x0.1) against the neighbours on
        # BOTH sides, and the two sides agree with each other within x2 --
        # a unit change (x12 dozen, x20 ton, x1000 thousands) is persistent
        # and fails the two-sides test; a boom year is x2-3, not x6+
        def island(x, before, after):
            if not before or not after or not x:
                return None
            b, f = med(before), med(after)
            if not b or not f or not (0.5 <= b / f <= 2):
                return None
            for scale in (10, 0.1):
                if all(0.6 * scale <= x / y <= 1.6 * scale for y in before + after):
                    return scale
            return None
        verdicts = []
        K = (i['fam'], i['akey'])
        if len(i['prices']) >= a.min_rows:
            mp = st.median(i['prices'])
            agree = sum(1 for p in i['prices'] if 0.5 <= p / mp <= 2) / len(i['prices'])
            pb = [st.median(byk[K][v]['prices']) for v in bef if len(byk[K][v]['prices']) >= 3]
            pa = [st.median(byk[K][v]['prices']) for v in aft if len(byk[K][v]['prices']) >= 3]
            sc = island(mp, pb, pa) if agree >= 0.8 else None
            if sc:
                verdicts.append(('price', sc, round(mp, 4), round(med(pb + pa), 4)))
        sb = [byk[K][v]['msum'] for v in bef if byk[K][v]['msum']]
        sa = [byk[K][v]['msum'] for v in aft if byk[K][v]['msum']]
        sc = island(i['msum'], sb, sa)
        if sc:
            verdicts.append(('members', sc, round(i['msum']), round(med(sb + sa))))
        if verdicts:
            scales = {v[1] for v in verdicts}
            # repairable only when the WHOLE block is scaled: x10 (a glued
            # digit inflates; the x0.1 direction is lost rows or a mixed unit
            # and is only reported) and, if a TOTAL is printed, the members
            # sum to it -- members x10 against a correct TOTAL is a fusion
            consistent = i['total'] is None or 0.8 <= i['msum'] / i['total'] <= 1.25
            if len(scales) == 1:
                out.append((vol, yr, g, art, unit, i['n'], verdicts, i['msum'], i['total'], i['rows'],
                            scales.pop() == 10 and consistent))
    out.sort(key=lambda t: -t[7])
    print(f'{len(out)} scaled blocks (own-year, both neighbours agree); '
          f'{sum(1 for t in out if t[10])} repairable (x10, whole block)')
    for t in out:
        print(f'  {"REPAIR" if t[10] else "report"} {t[0]} {t[1]} {t[2][:30]:30}/{t[3][:28]:28} n={t[5]:2} members {t[7]:>12,.0f} total {t[8]}  ' + '; '.join(f'{v[0]} x{v[1]} {v[2]} vs {v[3]}' for v in t[6]))
    if writer:
        w = writer
        # REPAIR: the other engine's reading of the block, when it closes on
        # its own printed TOTAL and sits at the neighbours' level (within
        # x2 of their median). obs's x10 blocks are not a glued digit --
        # carpets 1877: obs France 1,274,468 against inf 104,315, 1876
        # 107,830 -- so dividing would be wrong; the other engine IS the
        # page. Per-country substitution, obs countries the other engine
        # lacks are nulled.
        n = 0
        if True:
            for vol, yr, g, art, unit, nn, verdicts, msum, total, rws, ok in out:
                if not ok:
                    continue
                rg0, ra0 = rws[0][4], rws[0][5]
                oth = con.execute("""select country_raw, value from country_obs_inf
                    where volume=? and flow=? and year=? and coalesce(article_group,'')=?
                    and coalesce(article,'')=? order by row_seq""",
                    [vol, flow, yr, rg0, ra0 or '']).fetchall()
                if not oth:
                    oth = con.execute("""select country_raw, value from country_obs_inf
                        where volume=? and flow=? and year=? and upper(coalesce(article_group,''))=upper(?)
                        and upper(coalesce(article,''))=upper(?) order by row_seq""",
                        [vol, flow, yr, rg0, ra0 or '']).fetchall()
                omem = [(c, v) for c, v in oth if c and not is_total(c) and v]
                otot = [v for c, v in oth if c and is_total(c) and v]
                if not omem or not otot:
                    print(f'  no other-engine block for {vol} {g}/{art}')
                    continue
                osum = sum(v for _, v in omem)
                if abs(osum - max(otot)) > 0.005 * max(otot):
                    print(f'  other engine does not close for {vol} {g}/{art}: {osum} vs {otot}')
                    continue
                ref = [v for v in verdicts if v[0] == 'members']
                if ref and not (0.5 <= osum / ref[0][3] <= 2):
                    print(f'  other engine off the neighbours for {vol} {g}/{art}: {osum} vs {ref[0][3]}')
                    continue
                ov = {_key(c): v for c, v in omem}
                otots = [v for c, v in oth if c and is_total(c) and v]
                ev = 'inf block (closes on its TOTAL); obs block ' + '; '.join(
                    f'{v[0]} x{v[1]} {v[2]} vs {v[3]}' for v in verdicts)
                ti = 0
                for seq, ctry, qty, val, rg, ra in rws:
                    if val is None:
                        continue
                    if is_total(ctry):
                        # TOTAL rows in print order take the other engine's
                        nv = otots[ti] if ti < len(otots) else None
                        ti += 1
                    else:
                        nv = ov.get(_key(ctry))
                    if nv is not None and abs(nv - val) < 0.5:
                        continue
                    w.writerow([vol, yr, flow, rg, ra or '', ctry, round(val),
                                '' if nv is None else round(nv), ev])
                    n += 1
        print(f'{flow}: {n} cell repairs -> {a.out}')

if __name__ == '__main__':
    main()
