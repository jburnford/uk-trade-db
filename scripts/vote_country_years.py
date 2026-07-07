#!/usr/bin/env python3
"""Cross-volume voting for country cells.

The late-era country tables (as_1897-99) print each statistical year as one
of 5 comparative columns, so year Y is read independently in every volume
whose 5-year window covers it (1893-1899 each appear in 2-3 volumes), and
each volume is itself double-keyed (Chandra + Infinity). That is up to 6
independent OCR reads of the same printed cell — enough to VOTE.

Per (flow, duty, norm-article, norm-country, unit, year) we collect all
volume readings from country_consensus and vote:
  tier A  — >=2 volumes agree on the value (robust to any single misread)
  tier B  — 1 volume, but that cell was block-verified or engine-agreed
  tier C  — only unverified single readings, or volumes disagree

Writes country_year_consensus (voted value + tier + provenance) and prints
how many cells the voting promotes over the single-volume grade.
"""
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

BASE = Path('/home/jic823/uk_trade_db')
GOOD = {'exact', 'inf_struct', 'inf_block', 'swap', 'anchor', 'digit_fix',
        'inf_only', 'human', 't1_anchor', 't1_near'}   # t1_*: block sum
        # matches the voted Tier-1 national total (anchor_tier1.py)


def norm(s):
    import re
    import unicodedata
    s = unicodedata.normalize('NFKD', s or '').encode('ascii',
                                                      'ignore').decode()
    s = s.lower().replace('&', ' and ')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', s)).strip()


# the same trading nation is labelled differently across the era; unify
# before voting so the readings land in one bucket (and vote together)
COUNTRY_ALIAS = {
    'british north america': 'canada',
    'dominion of canada': 'canada',
    'canada': 'canada',
    'russia northern ports': 'russia',
    'russia southern ports': 'russia',
    'united states': 'united states of america',
    'united states america': 'united states of america',
}


def canon_country(ctry):
    c = norm(ctry)
    return COUNTRY_ALIAS.get(c, c)


import re as _re

# a sub-entry country_raw ("British East Indies : Bengal") is a clean nested
# place only when it is a single "Region : Sub" with a short sub name. The
# other "% : %" rows are parser failures where a whole block collapsed into one
# cell (newlines, embedded "To X"/"From X" lists, chained colons) — those stay
# dropped.
_SUB_GARBAGE = _re.compile(r'\n|\bto\b|\bfrom\b', _re.I)


def is_clean_subentry(ctry):
    if not ctry or ctry.count(':') != 1:
        return False
    if len(ctry) > 50 or _SUB_GARBAGE.search(ctry):
        return False
    sub = ctry.split(':', 1)[1].strip()
    return bool(sub) and not NUMERICISH(sub)


def NUMERICISH(s):
    return bool(_re.fullmatch(r'[\d,.\s—–-]*', s or ''))


def load_grand_totals(con):
    """Grand printed TOTAL per block, from the RAW parse (country_obs +
    Infinity), not country_consensus — the reconciler keeps only one TOTAL row
    per block (often the foreign subtotal), but the raw parse preserves all of
    them (foreign subtotal, possessions subtotal, grand). The grand total is
    the largest, and it matches the gold national figure. Keyed like a block."""
    grand = defaultdict(float)
    for tbl in ('country_obs', 'country_obs_inf'):
        for flow, duty, grp, art, yr, vol, q in con.execute(f"""
                SELECT flow, duty, article_group, article, year, volume, quantity
                FROM {tbl} WHERE country_raw='TOTAL' AND quantity IS NOT NULL"""
                ).fetchall():
            b = (vol, flow, duty or '', norm(grp), norm(art), yr)
            grand[b] = max(grand[b], float(q))
    return grand


def resolve_subentries(rows, grand):
    """Re-admit the colonial sub-entries the old ' : ' filter dropped.

    Rows are (flow, duty, grp, art, ctry, unit, year, vol, q, v, qb,vb,qc,vc).
    Colonial sources are printed as nested "Region : Sub" rows ("British East
    Indies : Ceylon"); the old filter dropped every one, losing e.g. 70% of
    tea. But some blocks ALSO print a possessions subtotal as a plain row (the
    wool "Australasia" = 614M line that already totals its own detail), so
    blindly adding the subs double-counts.

    The printed grand TOTAL row is the arbiter — the parser captures it and it
    matches the gold national figure. We admit a block's clean sub-entries only
    when the plain country rows fall materially SHORT of that grand total (a
    real gap the colonial detail should fill, as in tea); if the plain rows
    already reach it (a subtotal is standing in for the detail, as in wool) we
    keep the old drop-the-subs behaviour. A sub whose parent region is itself a
    plain row (the "United States : Atlantic/Pacific" port split) is always
    redundant. Kept subs are relabelled to the subplace alone so they vote in
    the same bucket as any plain reading of the same place.
    """
    plain_global = defaultdict(set)            # (article-year, no vol) -> {plain}
    plain_sum = defaultdict(float)             # block -> sum of plain quantities

    def blockkey(r):
        return (r[7], r[0], r[1] or '', norm(r[2]), norm(r[3]), r[6])

    def cykey(r):    # commodity-year, across volumes AND duty tags, for parent
        # detection: the same year is read as duty='duty' in the primary volume
        # and duty='free' in the late-era comparative columns, so duty must be
        # out of the key or the flattened parent and its subs never meet.
        return (r[0], norm(r[2]), norm(r[3]), r[6])

    for r in rows:
        ctry, q = r[4], (r[8] or 0)
        if ctry == 'TOTAL':
            continue
        if ' : ' not in (ctry or ''):
            # parent detection spans ALL volumes: the late-era comparative
            # columns (as_1897-99) read a year that the primary volume also
            # printed, and one may flatten a region ("British East Indies" as a
            # 226M plain row) while another lists its subs. Detecting the parent
            # only within a volume would let the subs double-count the region.
            plain_global[cykey(r)].add(canon_country(ctry))
            plain_sum[blockkey(r)] += q

    kept, dropped_garbage, dropped_parent, dropped_covered, admitted = \
        [], 0, 0, 0, 0
    for r in rows:
        ctry = r[4]
        if ctry == 'TOTAL':
            continue                            # totals are not countries
        if ' : ' not in (ctry or ''):
            kept.append(r)                      # plain country row — unchanged
            continue
        if not is_clean_subentry(ctry):
            dropped_garbage += 1                # collapsed-block parse failure
            continue
        b = blockkey(r)
        parent = canon_country(ctry.split(':', 1)[0])
        if parent in plain_global[cykey(r)]:
            dropped_parent += 1                 # parent row present -> redundant
            continue
        # grand-total gate: only fill a genuine shortfall. No total captured ->
        # can't validate, stay conservative and drop (old behaviour).
        g = grand.get(b, 0.0)
        if g <= 0 or plain_sum[b] >= 0.9 * g:
            dropped_covered += 1
            continue
        sub = ctry.split(':', 1)[1].strip()
        kept.append(r[:4] + (sub,) + r[5:])     # colonial sub filling the gap
        admitted += 1
    print(f'sub-entries: admitted {admitted:,} colonial rows, '
          f'dropped {dropped_parent:,} (parent present), '
          f'{dropped_covered:,} (total already covered), '
          f'{dropped_garbage:,} (garbage)')
    return kept


def load_group_authority():
    """article-sig -> canonical group, from repair_groups.py's cross-volume
    vote (reference/article_group_authority.csv). The parser's sticky group
    state scatters one commodity across bogus groups (Raisins under CARDS
    PLAYING; wine articles under TEA); keying and labelling by the canonical
    group merges those readings back onto one commodity. Low-confidence
    (<50% plurality, flag=REVIEW) rows are not applied."""
    import csv
    import validate_gold as V
    auth = {}
    f = BASE / 'reference' / 'article_group_authority.csv'
    if f.exists():
        for r in csv.DictReader(open(f)):
            if r['flag'] != 'REVIEW' and V.sig(r['article']):
                auth[V.sig(r['article'])] = r['canonical_group']
    return auth


def load_price_signal(con):
    """Per-cell verdicts from the value-as-signal rescore (rescore_value.py):
    price_flag='ok' means the independently printed VALUE corroborates this
    quantity (unit price sits in its series' band) — verification the OCR vote
    alone can't supply. v_review=1 means the value is the flagged suspect.
    Keyed exactly like country_consensus rows."""
    sig = {}
    try:
        for r in con.execute("""
                SELECT flow, duty, article_group, article, country_raw, unit,
                       year, volume, row_seq, price_flag, v_review
                FROM country_rescored""").fetchall():
            sig[r[:9]] = (r[9] == 'ok', bool(r[10]))
    except duckdb.CatalogException:
        pass                    # rescore not run yet — signal simply absent
    return sig


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'))
    rows = con.execute("""
        SELECT flow, duty, article_group, article, country_raw, unit, year,
               volume, quantity, value, q_block, v_block, q_cell, v_cell,
               row_seq
        FROM country_consensus
    """).fetchall()
    price = load_price_signal(con)
    grand = load_grand_totals(con)    # printed grand totals from the raw parse
    rows = resolve_subentries(rows, grand)
    auth = load_group_authority()
    import validate_gold as V
    def canon_group(grp, art):
        return auth.get(V.sig(art), grp) if art else grp

    # ---- key canonicalization: the same printed cell is read in up to 4
    # volumes (statement year + comparative columns), but string drift
    # splits the readings into singleton buckets and voting never happens
    # (1896 measured: 27% votable on raw keys, 48% once names align).
    def canon_article(art):
        """Order/punctuation-insensitive article key: 'Hewn, Fir' == 'Fir :
        Hewn'. sig() drops stopwords; fall back to norm for generic labels
        ('Unenumerated') whose sig is empty."""
        s = V.sig(art)
        return ' '.join(sorted(s)) if s else norm(art)

    UNIT_ALIAS = {'cuts': 'cwt', 'cwts': 'cwt', 'cwt': 'cwt',
                  'lbs': 'lb', 'lb': 'lb', 'tons': 'ton', 'ton': 'ton',
                  'loads': 'load', 'load': 'load', 'galls': 'gallon',
                  'gallons': 'gallon', 'gallon': 'gallon', 'no': 'number',
                  'number': 'number', 'doz': 'dozen', 'dozen': 'dozen'}
    def canon_unit(u):
        k = norm(u).rstrip('s') if norm(u) else ''
        return UNIT_ALIAS.get(norm(u), UNIT_ALIAS.get(k, norm(u)))

    # bucket every reading by the cross-volume key
    buckets = defaultdict(list)
    for (flow, duty, grp, art, ctry, unit, yr, vol, q, v,
         qb, vb, qc, vc, seq) in rows:
        cgrp = canon_group(grp, art)      # heal sticky-group misfilings
        key = (flow, duty or '', norm(cgrp) + '|' + norm(art),
               canon_country(ctry), canon_unit(unit), yr)
        # NOTE measured on 1896: sig-token article keys and duty-agnostic
        # keys both over-merge (gold reproduction 1231 -> 1223); the safe
        # canonicalizations are group authority + unit alias. Deeper key
        # alignment needs value-aware matching, not looser strings.
        # value-as-signal: 'ok' price corroborates the quantity independently
        # of OCR agreement; a v_review'd value loses its verified status
        p_ok, v_bad = price.get(
            (flow, duty, grp, art, ctry, unit, yr, vol, seq), (False, False))
        buckets[key].append({
            'vol': vol, 'duty': duty, 'grp': cgrp, 'art': art, 'ctry': ctry,
            'unit': unit,
            'q': q, 'v': v,
            'q_ok': (qb in GOOD or qc in ('agree', 'repaired', 'human')
                     or p_ok),
            'v_ok': (vb in GOOD or vc in ('agree', 'repaired', 'human'))
                    and not v_bad,
        })

    con.execute('DROP TABLE IF EXISTS country_year_consensus')
    con.execute("""CREATE TABLE country_year_consensus (
        flow VARCHAR, duty VARCHAR, article_group VARCHAR, article VARCHAR,
        country VARCHAR, unit VARCHAR, year INTEGER,
        quantity DOUBLE, value DOUBLE,
        n_volumes INTEGER, n_agree_value INTEGER,
        q_tier VARCHAR, v_tier VARCHAR, volumes VARCHAR)""")

    def vote(readings, field, ok_field):
        """-> (value, tier, n_agree). Rounds to nearest int for the tally so
        1,234.0 vs 1234 agree."""
        vals = [round(r[field]) for r in readings if r[field] is not None]
        if not vals:
            return None, 'C', 0
        tally = Counter(vals)
        val, n = tally.most_common(1)[0]
        n_vols = len({r['vol'] for r in readings if r[field] is not None})
        if n >= 2:
            return float(val), 'A', n
        # single reading: lean on its per-cell verification
        any_ok = any(r[ok_field] for r in readings
                     if r[field] is not None and round(r[field]) == val)
        return float(val), ('B' if any_ok else 'C'), n

    ins = []
    promo_v = same_v = 0
    for key, readings in buckets.items():
        flow, duty, ga, nc, nu, yr = key
        qv, qt, qn = vote(readings, 'q', 'q_ok')
        vv, vt, vn = vote(readings, 'v', 'v_ok')
        rep = readings[0]
        vols = ','.join(sorted({r['vol'] for r in readings}))
        ins.append([flow, duty, rep['grp'], rep['art'], nc,
                    rep['unit'], yr, qv, vv, len(readings), vn, qt, vt, vols])
        # did voting lift the value cell above what any single volume gave?
        best_single = max((r['v_ok'] for r in readings), default=False)
        if vt == 'A' and not best_single:
            promo_v += 1
        elif vt == 'A':
            same_v += 1
    import pandas as pd
    df = pd.DataFrame(ins, columns=[
        'flow', 'duty', 'article_group', 'article', 'country', 'unit',
        'year', 'quantity', 'value', 'n_volumes', 'n_agree_value',
        'q_tier', 'v_tier', 'volumes'])
    con.execute('INSERT INTO country_year_consensus SELECT * FROM df')
    con.commit()

    n = len(ins)
    tv = Counter(r[12] for r in ins)
    print(f'country_year_consensus cells: {n:,}')
    print(f'  value tier A {tv["A"]:,} ({tv["A"]/n:.1%})  '
          f'B {tv["B"]:,} ({tv["B"]/n:.1%})  '
          f'C {tv["C"]:,} ({tv["C"]/n:.1%})')
    print(f'  value cells promoted to A by cross-volume agreement alone '
          f'(no single-volume verification): {promo_v:,}')
    multi = sum(1 for r in ins if r[9] >= 2)
    print(f'  cells with >=2 volume readings (votable): {multi:,} '
          f'({multi/n:.1%})')

    # wood spot-check
    print('\nwood hewn/sawn fir, cells with multi-volume votes:')
    for r in con.execute("""SELECT article, country, year, quantity, v_tier,
            n_volumes, n_agree_value FROM country_year_consensus
            WHERE flow='import' AND lower(article_group) LIKE '%wood%timber%'
            AND (lower(article) LIKE '%hewn%fir%' OR lower(article) LIKE '%sawn%fir%')
            AND lower(country)='canada' AND n_volumes >= 2
            ORDER BY year""").fetchall():
        print(f'  {r[0][:16]:16} {r[1]:8} {r[2]}  q={r[3] or 0:>9,.0f}  '
              f'v_tier={r[4]}  {r[6]}/{r[5]} vols agree')


if __name__ == '__main__':
    main()
