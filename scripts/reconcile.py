#!/usr/bin/env python3
"""Reconcile the two OCR keys (Chandra abstract_obs vs Infinity infinity_obs)
cell-by-cell, then vote across volumes into a consensus table.

Cell matching (within volume, flow, measure, year) runs in passes:
  P1 exact          — group + article normalized text identical
  P2 stripped       — group + article after trailing-unit-token stripping
  P3 article-only   — group ignored (engines attach group headers
                      differently: "Metals : Unenumerated" vs bare
                      "Unenumerated"); only unambiguous 1:1 candidates
  P4 art-stripped   — P3 with unit stripping
  P5 grp-glued      — one engine glued the group into the article text
All fallback passes require an unambiguous 1:1 candidate on both sides.

Cell verdicts:
  verified   — both engines read the same number
  engine_dis — engines disagree (one misread; review with both values)
  single     — only one engine produced the cell

Consensus per canonical (article, flow, measure, year) across volumes:
  tier A — >=2 volume-cells verified and agreeing
  tier B — 1 verified cell, or >=2 unverified cells agreeing
  tier C — everything else (review queue)

Series keys are canonicalized (unit tokens stripped from articles; bare
articles promoted into their group when the Chandra corpus shows exactly
one) so the same printed series lands in one key across volumes/engines.
"""
import csv
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

BASE = Path('/home/jic823/uk_trade_db')

# unit words that leak from the unit column into article captions
UNIT_TOKENS = {
    'cwts', 'cwt', 'gallons', 'gallon', 'galls', 'tons', 'ton', 'lbs', 'lb',
    'number', 'no', 'value', 'qrs', 'quarters', 'loads', 'load', 'pieces',
    'yards', 'dozens', 'doz', 'pairs', 'bushels', 'boxes', 'bundles',
    'barrels', 'brls', 'oz', 'ounces', 'gross', 'sq', 'feet', 'ft',
    'hhds', 'packs', 'mille', 'great', 'hundreds', 'ccts', 'cvts', 'cwis',
}


def _sig(group, article):
    """Token signature of a Tier-1 label, for matching manual overrides.
    Punctuation, dash leaders, ditto marks and case all vary between
    printings of the same line ('" Flax or Linseed', '„ Flax or Linseed',
    'Oil Seed Cake - - - - -'), so match on the token SET."""
    txt = f"{group or ''} {article or ''}".lower()
    txt = re.sub(r'[^a-z0-9 ]+', ' ', txt)
    return tuple(sorted(t for t in txt.split()
                        if t and t not in ('and', 'or', 'the', 'of', 'a')))


def norm(s):
    s = (s or '').replace('&amp;', '&').replace('&AMP;', '&')
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = s.lower().replace('&', ' and ')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', s)).strip()


def strip_units(a):
    toks = a.split()
    while toks and toks[-1] in UNIT_TOKENS:
        toks.pop()
    return ' '.join(toks)


def load(con, table):
    cells = {}
    for vol, flow, meas, grp, art, unit, y, v in con.execute(
            f'''SELECT volume, flow, measure, article_group, article, unit,
                year, value FROM {table} WHERE value IS NOT NULL''').fetchall():
        key = (vol, flow, meas, norm(grp), norm(art), y)
        cells.setdefault(key, (v, unit, grp, art))
    return cells


def match_cells(ch, inf):
    """Multi-pass matcher; returns [(ch_key, inf_key)], leftover key sets."""
    ch_un, inf_un = dict(ch), dict(inf)
    pairs = []

    def take(new_pairs, name):
        for ck, ik in new_pairs:
            del ch_un[ck]
            del inf_un[ik]
        pairs.extend(new_pairs)
        agree = sum(1 for ck, ik in new_pairs
                    if abs(ch[ck][0] - inf[ik][0]) < 0.5)
        print(f'  {name:24} pairs {len(new_pairs):6,}  '
              f'value-agree {agree / max(len(new_pairs), 1):6.1%}')

    take([(k, k) for k in list(ch_un) if k in inf_un], 'P1 exact')

    def unambiguous(keyfn_ch, keyfn_inf, name):
        ci, ii = defaultdict(list), defaultdict(list)
        for k in ch_un:
            kk = keyfn_ch(k)
            if kk:
                ci[kk].append(k)
        for k in inf_un:
            kk = keyfn_inf(k)
            if kk:
                ii[kk].append(k)
        take([(cks[0], ii[kk][0]) for kk, cks in ci.items()
              if len(cks) == 1 and len(ii.get(kk, ())) == 1], name)

    def art(k, strip=False):
        vol, flow, meas, g, a, y = k
        a = strip_units(a) if strip else a
        return (vol, flow, meas, a, y) if a else None

    def glued(k):
        vol, flow, meas, g, a, y = k
        if not g:
            return None
        return (vol, flow, meas, strip_units(f'{g} {a}'.strip()), y)

    unambiguous(lambda k: (*k[:4], strip_units(k[4]), k[5]),
                lambda k: (*k[:4], strip_units(k[4]), k[5]), 'P2 stripped')
    unambiguous(art, art, 'P3 article-only')
    unambiguous(lambda k: art(k, True), lambda k: art(k, True),
                'P4 art-stripped')
    unambiguous(glued, lambda k: art(k, True), 'P5a ch-grp-glued')
    unambiguous(lambda k: art(k, True), glued, 'P5b inf-grp-glued')
    return pairs, ch_un, inf_un


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'))
    ch = load(con, 'abstract_obs')
    inf = load(con, 'infinity_obs')
    print(f'chandra cells: {len(ch):,}   infinity cells: {len(inf):,}')

    print('matching passes:')
    pairs, ch_un, inf_un = match_cells(ch, inf)

    # verdicts keyed by the Chandra cell key (canonical label source);
    # Infinity-single cells keep their own key
    verdict = {}
    n = Counter()
    for ck, ik in pairs:
        cv, unit, grp, art = ch[ck]
        iv = inf[ik][0]
        if abs(cv - iv) < 0.5:
            verdict[ck] = ('verified', cv, unit, grp, art)
            n['verified'] += 1
        else:
            verdict[ck] = ('engine_dis', cv, unit, grp, art)
            n['engine_dis'] += 1
    for k, (v, unit, grp, art) in ch_un.items():
        verdict[k] = ('single', v, unit, grp, art)
        n['single_chandra'] += 1
    for k, (v, unit, grp, art) in inf_un.items():
        verdict.setdefault(k, ('single', v, unit, grp, art))
        n['single_infinity'] += 1
    both = n['verified'] + n['engine_dis']
    print(f'cells in both keys: {both:,}  '
          f'verified {n["verified"]:,} ({n["verified"] / max(both, 1):.1%})  '
          f'disagree {n["engine_dis"]:,} ({n["engine_dis"] / max(both, 1):.2%})')
    print(f'single-key cells: chandra {n["single_chandra"]:,}, '
          f'infinity {n["single_infinity"]:,}')

    # ---------------- canonical series keys
    # group promotion: bare article -> group, when the Chandra corpus shows
    # exactly one non-empty group for that article within a flow+measure
    grp_of = defaultdict(set)
    for (vol, flow, meas, g, a, y) in ch:
        grp_of[(flow, meas, strip_units(a) or a)].add(g)

    def canon(flow, meas, g, a):
        sa = strip_units(a) or a
        if not g:
            gs = {x for x in grp_of.get((flow, meas, sa), ()) if x}
            if len(gs) == 1:
                g = next(iter(gs))
        return g, sa

    series = defaultdict(list)
    for (vol, flow, meas, g, a, y), (st, v, unit, grp, art) in verdict.items():
        cg, ca = canon(flow, meas, g, a)
        series[(flow, meas, cg, ca, y)].append((st, v, unit, grp, art, vol))

    # ---------------- page-adjudicated Tier-1 overrides
    t1_override, _override_hit = {}, set()
    ovf = BASE / 'reference' / 'manual_t1.csv'
    if ovf.exists():
        for r in csv.DictReader(open(ovf)):
            t1_override[(r['flow'], r['measure'], int(r['year']),
                         _sig(r['article_group'], r['article']))] = {
                'value': float(r['value']), 'tier': (r.get('tier') or 'A')}

    # ---------------- consensus across volumes
    con.execute('DROP TABLE IF EXISTS consensus')
    con.execute('''CREATE TABLE consensus (
        flow VARCHAR, measure VARCHAR, article_group VARCHAR,
        article VARCHAR, unit VARCHAR, year INTEGER, value DOUBLE,
        n_volumes INTEGER, n_verified INTEGER, tier VARCHAR,
        volumes VARCHAR)''')
    tiers = Counter()
    review = []
    for (flow, meas, g, a, y), obs in series.items():
        ver = [v for st, v, *_ in obs if st == 'verified']
        allv = [v for st, v, *_ in obs]
        unit, grp, art = obs[0][2], obs[0][3], obs[0][4]
        vols = ','.join(sorted({o[5] for o in obs}))
        vc = Counter(ver)
        ac = Counter(allv)
        if ver and vc.most_common(1)[0][1] >= 2:
            tier, val = 'A', vc.most_common(1)[0][0]
        elif len(ver) == 1 or (ac and ac.most_common(1)[0][1] >= 2):
            tier = 'B'
            val = ver[0] if ver else ac.most_common(1)[0][0]
        else:
            tier, val = 'C', ac.most_common(1)[0][0]
            review.append((flow, meas, grp, art, y,
                           '|'.join(f'{v:,.0f}' for v in set(allv))))
        # ---- page-adjudicated Tier-1 override (reference/manual_t1.csv).
        # The vote can be wrong in the one way no amount of voting fixes: a
        # broken digit copied forward. as_1890, as_1892 and as_1893 all print
        # oil seed cake 1890 as 282,616 Tons and as_1894/tn_1895 print
        # 229,616; the origin table sums to 282,582. Flax and linseed 1899 is
        # the mirror image — the majority reading is the wrong one, and only
        # the country block's own arithmetic says so. country_obs has
        # manual_rows.csv for exactly this; Tier 1 had nothing, so a provably
        # wrong national total dragged its year's ratio with it forever.
        # Matched on the token signature of group+article, so an OCR variant
        # of the label on re-parse still resolves.
        okey = (flow, meas, y, _sig(grp, art))
        ov = t1_override.get(okey)
        if ov:
            val, tier = ov['value'], ov['tier']
            vols += ',manual'
            _override_hit.add(okey)
        tiers[tier] += 1
        con.execute('INSERT INTO consensus VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                    [flow, meas, grp, art, unit, y, val,
                     len(obs), len(ver), tier, vols])
    con.commit()
    if t1_override:
        print(f'manual T1 overrides applied: {len(_override_hit)} '
              f'of {len(t1_override)} rules')
        for k in t1_override:
            if k not in _override_hit:
                print(f'  UNMATCHED RULE (nothing to override): {k}')
    total = sum(tiers.values())
    print(f'\nconsensus series-years: {total:,}')
    for t in 'ABC':
        print(f'  tier {t}: {tiers[t]:,} ({tiers[t] / total:.1%})')
    out = BASE / 'reports' / 'review_queue.csv'
    with open(out, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['flow', 'measure', 'group', 'article', 'year', 'values'])
        w.writerows(sorted(review, key=lambda r: tuple(str(x or "") for x in r)))
    print(f'tier-C review queue -> {out}')


if __name__ == '__main__':
    main()
