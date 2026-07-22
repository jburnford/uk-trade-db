#!/usr/bin/env python3
"""Round-23 value-integrity verdicts for round-22/23 groupfix blocks.

Per block-year:
  anchors: inf grand TOTAL value row (from the qty-matched inf copy),
           ch grand TOTAL value row, T1 value (relaxed sig match incl a few
           hand aliases). Anchor = agreeing pair, else any single.
  ch_vsum / inf_vsum = member value sums (truncated blocks compared by RATE
  vs anchor rate where T1 qty known, else by sum when block has own grand).
Verdicts: CH-OK, SWITCH-INF (inf members sane, ch phantom), STRIP (both
phantom), NO-ANCHOR.
"""
import csv
import sys
from collections import Counter, defaultdict
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
import duckdb
import validate_gold as V

con = duckdb.connect('/home/jic823/uk_trade_db/db/uk_trade.duckdb', read_only=True)
TAGS = ('round 22', 'BRACKET ADJUDICATION', 'EXPORT-TWOUP WHOLE-BLOCK SLIP')

ALIAS = {  # country-table article -> abstract article (sig-level bridges)
    'Carpets, not being Rugs': 'Carpets and Druggets',
    'Rugs, Coverlets, or Wrappers': 'Rugs, Coverlets or Wrappers',
}

t1 = {}
for fl, g, a, m, y, val in con.execute("""
        SELECT flow, article_group, article, measure, year, value
        FROM abstract_obs WHERE value IS NOT NULL""").fetchall():
    a2 = (a or '').replace('&amp;', '&').replace(' - - - - -', '').strip(' -—')
    g2 = (g or '').replace('&amp;', '&')
    asig = V.sig(a2) or V.sig(f"{g2} {a2}")
    if asig:
        t1.setdefault((asig, int(y), fl, m), Counter())[round(val)] += 1


def t1maj(asig, y, fl, m):
    c = t1.get((asig, y, fl, m))
    return c.most_common(1)[0][0] if c else None


def split(rows_):
    mem, tot = [], []
    for c, y, q, v in rows_:
        cn = V.cnorm(c or '')
        (tot if cn.startswith('total') or (c or '').strip().upper() == 'TOTAL'
         else mem).append((cn, int(y), q, v))
    return mem, tot


rows = list(csv.DictReader(open('/home/jic823/uk_trade_db/reference/group_repairs.csv')))
seen = set()
out = Counter()
for gr in rows:
    if not any(t in (gr.get('note') or '') for t in TAGS) or gr['seq_start'] == '0':
        continue
    key = (gr['volume'], gr['article_group'], gr['article'], gr['seq_start'], gr['seq_end'])
    if key in seen:
        continue
    seen.add(key)
    ch = con.execute("""SELECT country_raw, year, quantity, value FROM country_obs
        WHERE volume=? AND flow=? AND article_group=? AND article IS NOT DISTINCT FROM ?
          AND row_seq BETWEEN ? AND ? ORDER BY row_seq""",
        [gr['volume'], gr['flow'], gr['article_group'], gr['article'] or None,
         int(gr['seq_start']), int(gr['seq_end'])]).fetchall()
    mem, tot = split(ch)
    inf = con.execute("""SELECT country_raw, year, quantity, value FROM country_obs_inf
        WHERE volume=? AND flow=? AND article_group=? AND article IS NOT DISTINCT FROM ?""",
        [gr['volume'], gr['flow'], gr['article_group'], gr['article'] or None]).fetchall()
    imem, itot = split(inf)
    # sig for T1: prefer clean new label + alias bridge
    art = ALIAS.get(gr['new_article'], gr['new_article'])
    asig = V.sig(art) or V.sig(f"{gr['new_group']} {art}")
    years = sorted({y for _, y, _, _ in mem})
    for y in years:
        m_y = [(cn, q, v) for cn, yy, q, v in mem if yy == y]
        ch_vs = sum(v for _, _, v in m_y if v)
        ch_qs = sum(q for _, q, _ in m_y if q)
        ch_tot_v = max((v for _, yy, q, v in tot if yy == y and v), default=None)
        chq = {cn: q for cn, q, v in m_y}
        i_match = [(cn, q, v) for cn, yy, q, v in imem
                   if yy == y and cn in chq and q and chq[cn] and abs(q - chq[cn]) < 1]
        inf_vs = sum(v for _, _, v in i_match if v)
        inf_tot_v = max((v for cn, yy, q, v in itot if yy == y and v), default=None)
        t1v = t1maj(asig, y, gr['flow'], 'value')
        t1q = t1maj(asig, y, gr['flow'], 'quantity')
        # anchor: prefer agreeing pair among (inf_tot_v, t1v, ch_tot_v)
        cands = [x for x in (inf_tot_v, t1v, ch_tot_v) if x]
        anchor = None
        for i in range(len(cands)):
            for j in range(i + 1, len(cands)):
                if abs(cands[i] - cands[j]) <= 0.02 * max(cands[i], cands[j]):
                    anchor = cands[i]
        if anchor is None and t1v:
            anchor = t1v
        if anchor is None and inf_tot_v:
            anchor = inf_tot_v
        if anchor is None:
            out['NO-ANCHOR'] += 1
            print(f"NO-ANCHOR   {gr['volume']} {y} [{gr['new_group']}|{gr['new_article']}] "
                  f"ch_vs={ch_vs:,.0f} chTOT={ch_tot_v} infTOT={inf_tot_v} T1v={t1v}")
            continue
        # completeness: full block if qty sum ~ T1 qty (or no T1q)
        frac = ch_qs / t1q if t1q else None
        exp_v = anchor * (min(frac, 1.0) if frac and frac < 0.98 else 1.0)
        def ok(vs):
            return vs and 0.55 * exp_v <= vs <= 1.45 * exp_v
        if ok(ch_vs):
            out['CH-OK'] += 1
            continue
        if len(i_match) >= max(3, 0.6 * len(chq)) and ok(inf_vs * (len(chq) / max(1, len(i_match)))):
            out['SWITCH-INF'] += 1
            print(f"SWITCH-INF  {gr['volume']} {y} [{gr['new_group']}|{gr['new_article']}] "
                  f"ch_vs={ch_vs:,.0f} inf_vs={inf_vs:,.0f} anchor={anchor:,.0f} (exp {exp_v:,.0f})")
        else:
            out['STRIP'] += 1
            print(f"STRIP       {gr['volume']} {y} [{gr['new_group']}|{gr['new_article']}] "
                  f"ch_vs={ch_vs:,.0f} inf_vs={inf_vs:,.0f}/{len(i_match)} anchor={anchor:,.0f} "
                  f"(exp {exp_v:,.0f}, qfrac={frac and round(frac,2)})")
print(out)
