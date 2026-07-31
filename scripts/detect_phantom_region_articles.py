#!/usr/bin/env python3
"""Region headers absorbed as the ARTICLE inside a MULTI-ARTICLE group.

`repair_country_as_article.py` already handles the simple form of this defect:
a printed region heading ('From West Africa:') becomes the article, and since
the GROUP is the commodity (TEA, COFFEE) the repair is article -> NULL.

That repair is wrong, and silently so, whenever the group has real sub-sorts.
`FEATHERS AND DOWN` prints two lines, 'For Beds' and 'Ornamental'; when the
heading 'British Possessions in South Africa' was absorbed in as_1895 the
rows did not belong to the group, they belonged to **Ornamental**, the article
immediately above. Nulling the article would have merged them into a
commodity that does not exist. Found by hand in as_1895 and as_1896 (feathers
1895 and 1896, the latter closing on its anchor to the digit); this screen
looks for the rest.

The test, in order:

  1. the article normalises to a label used as a plain COUNTRY by at least
     MIN_COMMODS distinct commodities — i.e. it is a place, not a good;
  2. the group has at least two distinct non-place articles in that volume,
     so article -> NULL is NOT the right repair;
  3. a real article exists immediately above it in row order — the candidate
     parent;
  4. arithmetic: parent members + phantom members, against the parent's
     Tier-1 for that year.

(4) is the decisive column and (1)-(3) only decide what to test. A block
that closes is a repair; a block that does not is a lead, because the
phantom may hold only part of the table (in as_1896 it swallowed the tail of
the foreign section as well as the whole British half).

Usage: python3 scripts/detect_phantom_region_articles.py
   ->  reports/phantom_region_articles.csv
"""
import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import duckdb
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
import validate_gold as V

BASE = Path('/home/jic823/uk_trade_db')
MIN_COMMODS = 5      # distinct commodities using the label as a country
MAX_AS_ARTICLE = 2   # ...and used as an ARTICLE in at most this many groups
MAX_ROWS = 80        # a printed origin block; anything larger is the
                     # volume-scale sticky-article class (as_1897 spans
                     # seq 1828-24254 under one article name) - a different
                     # defect that a range relabel would make far worse
TOL = 0.002          # 0.2% — these are sums of many cells, not single digits


def cnorm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii',
                                                      'ignore').decode()
    s = s.lower().replace('&', ' and ')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', s)).strip()


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)

    # Place vocabulary. Being used as a country by many commodities is NOT
    # sufficient: 'Unenumerated', 'Other Sorts' and friends leak into the
    # country column often enough to clear any such bar, and the first cut of
    # this screen duly reported 682 candidates almost all of which were the
    # word 'Unenumerated'. The discriminator that actually separates them is
    # the OTHER column — a real place is used as a country constantly and as
    # an ARTICLE almost never, whereas a commodity descriptor is an article in
    # dozens of groups. So both conditions, and the second does the work.
    as_country = {cnorm(r[0]): r[1] for r in con.execute("""
        SELECT lower(trim(country_raw)), count(DISTINCT article_group || '|' ||
               coalesce(article, ''))
        FROM country_obs WHERE country_raw IS NOT NULL GROUP BY 1""").fetchall()}
    as_article = defaultdict(int)
    for a, n in con.execute("""
            SELECT lower(trim(article)), count(DISTINCT article_group)
            FROM country_obs WHERE article IS NOT NULL GROUP BY 1""").fetchall():
        as_article[cnorm(a)] = max(as_article[cnorm(a)], n)
    places = {p for p, n in as_country.items()
              if p and n >= MIN_COMMODS and as_article.get(p, 0) <= MAX_AS_ARTICLE}

    # The country column alone still misses the ones that matter, and the
    # reference cases proved it: the printed HEADING form ('South Africa',
    # 'East Coast of Africa') is what gets absorbed as the article, while the
    # country column spells it 'British Possessions in South Africa'. So also
    # accept anything that overlaps the map gazetteer by containment in either
    # direction. Without this the screen missed BOTH known positives — which
    # is the whole reason a screen must be tested against cases already solved
    # by hand before its output is believed.
    gaz = set()
    gz = BASE / 'reference' / 'map_gazetteer.json'
    if gz.exists():
        import json
        g = json.load(open(gz))
        for k, v in g.items():
            gaz.add(cnorm(k))
            for ch in (v.get('children') or []):
                gaz.add(cnorm(ch))
    gaz -= {''}

    def is_place(s):
        # NO frequency guard here, and that is the whole lesson of building
        # this screen. The obvious guard — "a commodity descriptor is an
        # ARTICLE in many groups, a place is not" — is exactly INVERTED for
        # the class being hunted: 'South Africa' is an article in 39 different
        # groups precisely BECAUSE it is a phantom in 39 different groups. The
        # guard rejected both known positives. Placehood is a semantic
        # question and the gazetteer answers it directly; 'Unenumerated' has
        # no gazetteer overlap and needs no frequency test to exclude it.
        c = cnorm(s)
        if not c:
            return False
        # gazetteer containment ONLY. The country-frequency set was tried
        # and rejected: BUTTER, BRISTLES and 'MILK, CONDENSED' all leak into
        # the country column often enough (row-slips) to clear it, and none
        # of them is a place. Gazetteer overlap is strict and it is what the
        # two reference cases actually need.
        return any(c == g or (len(c) > 6 and c in g) or
                   (len(g) > 6 and g in c) for g in gaz)

    grp_articles = {}
    for g, n in con.execute("""
            SELECT article_group, count(DISTINCT article) FROM country_obs
            WHERE article IS NOT NULL AND article_group IS NOT NULL
            GROUP BY 1""").fetchall():
        grp_articles[g] = n

    # Tier-1 keyed by (signature, year), best tier first.
    t1_by_sig = {}
    for g, a, y, v, t in con.execute("""
            SELECT article_group, article, year, value, tier FROM consensus
            WHERE flow = 'import' AND measure = 'quantity'
            ORDER BY CASE tier WHEN 'A' THEN 0 WHEN 'B' THEN 1 ELSE 2 END""").fetchall():
        k = (V.sig(f'{g or ""} {a or ""}') or V.sig(a or ''), y)
        if k[0] and k not in t1_by_sig:
            t1_by_sig[k] = v

    # per (signature, year) closure as the payload currently stands
    payload_ratio = {}
    pp = BASE / 'exports' / 'viz_payload.json'
    if pp.exists():
        import json as _j
        for nm, e in _j.load(open(pp)).items():
            cc = e.get('c') or {}
            tt = cc.get('§TOTAL')
            if not tt:
                continue
            uu = max(tt, key=lambda x: len(tt[x]))
            ty = {r[0]: r[1] for r in tt[uu] if r[1]}
            if not ty:
                continue
            ss = defaultdict(float)
            for cty, byu in cc.items():
                if cty == '§TOTAL' or '(' in cty:
                    continue
                for r in byu.get(uu, []):
                    if r[1]:
                        ss[r[0]] += r[1]
            sg = V.sig(nm.replace(' — ', ' ').replace(' : ', ' '))
            for y, tv in ty.items():
                if sg and tv:
                    payload_ratio.setdefault((sg, y), ss.get(y, 0) / tv)

    rows = []
    for tbl, eng in (('country_obs', 'ch'), ('country_obs_inf', 'inf')):
        blocks = con.execute(f"""
            SELECT volume, flow, article_group, article,
                   min(row_seq), max(row_seq), count(*), min(year)
            FROM {tbl} WHERE flow = 'import' AND article_group IS NOT NULL
            GROUP BY 1,2,3,4""").fetchall()
        by_grp = defaultdict(list)
        for b in blocks:
            by_grp[(b[0], b[2])].append(b)
        for k in by_grp:
            by_grp[k].sort(key=lambda b: b[4])

        for (vol, grp), bs in by_grp.items():
            # Whether the GROUP or the ARTICLE carries the commodity is a
            # property of the group corpus-wide, not of this one volume's
            # parse: as_1895 renders only 'Ornamental' beside the phantom, so
            # a per-volume count of real articles was 1 and skipped the exact
            # case this screen exists to find.
            if grp_articles.get(grp, 0) < 2:
                continue            # article -> NULL is the right repair here
            for i, b in enumerate(bs):
                art = b[3]
                if not art or not is_place(art):
                    continue
                if b[6] > MAX_ROWS:
                    continue
                prev = [p for p in bs[:i] if p[3] and not is_place(p[3])]
                if not prev:
                    continue
                parent = prev[-1]
                year = b[7] or parent[7]
                # arithmetic: parent members + phantom members vs parent T1
                def members(bl):
                    return con.execute(f"""
                        SELECT sum(quantity) FROM {tbl}
                        WHERE volume = ? AND article_group = ?
                          AND article IS NOT DISTINCT FROM ?
                          AND row_seq BETWEEN ? AND ?
                          AND upper(coalesce(country_raw,'')) NOT LIKE 'TOTAL%'
                        """, [vol, grp, bl[3], bl[4], bl[5]]).fetchone()[0] or 0
                combined = members(parent) + members(b)

                # SECTION PROOF — the test that actually matters, and the one
                # every hand adjudication in this class has used. Concatenate
                # the parent block and the phantom block in row order and walk
                # them: each printed TOTAL should equal either the members
                # since the previous TOTAL (a section subtotal) or the members
                # from the start (the grand total). If they all reconcile, the
                # concatenation is right — and this needs NO anchor, so unlike
                # the Tier-1 column it still works on a PARTIAL swallow, where
                # the phantom took only part of a table and parent + phantom
                # therefore does NOT equal Tier-1. 80 of the 102 candidates are
                # in exactly that state.
                seq_rows = con.execute(f"""
                    SELECT country_raw, quantity FROM {tbl}
                    WHERE volume = ? AND article_group = ?
                      AND ((article IS NOT DISTINCT FROM ?
                            AND row_seq BETWEEN ? AND ?)
                        OR (article IS NOT DISTINCT FROM ?
                            AND row_seq BETWEEN ? AND ?))
                    ORDER BY row_seq""",
                    [vol, grp, parent[3], parent[4], parent[5],
                     b[3], b[4], b[5]]).fetchall()
                run_sec = run_all = 0.0
                n_tot = n_ok = 0
                for cty, q in seq_rows:
                    if (cty or '').strip().upper().startswith('TOTAL'):
                        if q is None:
                            continue
                        n_tot += 1
                        if (abs(run_sec - q) <= max(5.0, TOL * q)
                                or abs(run_all - q) <= max(5.0, TOL * q)):
                            n_ok += 1
                        run_sec = 0.0
                    else:
                        run_sec += q or 0
                        run_all += q or 0
                # Tier-1 is looked up by SIGNATURE, not by string equality.
                # The first cut matched article_group literally and found a
                # Tier-1 for exactly zero of 102 candidates, because
                # country_obs says 'FEATHERS AND DOWN' where consensus says
                # 'Feathers'. Same reconciliation the pipeline itself uses.
                t1 = t1_by_sig.get((V.sig(f'{grp} {parent[3]}')
                                    or V.sig(parent[3]), year))
                # What the PAYLOAD already reads for this parent-year. Without
                # it the closure column is unusable as a ranking: a block that
                # has already been repaired still satisfies
                # parent + phantom == Tier-1, so OIL | West Africa -> Palm sat
                # at the top of the list as 13 blocks at ratio 1.0000 while
                # Oil - Palm was reading 1.00 in the payload. country_obs is
                # the INPUT to the repair pipeline, not its output, so a screen
                # over it is blind to every repair already applied.
                pay_ratio = payload_ratio.get(
                    (V.sig(f'{grp} {parent[3]}') or V.sig(parent[3]), year))
                ratio = (combined / t1) if (t1 and combined) else None
                rows.append({
                    'engine': eng, 'volume': vol, 'group': grp,
                    'phantom_article': art, 'parent_article': parent[3],
                    'year': year, 'seq_start': b[4], 'seq_end': b[5],
                    'n_rows': b[6], 'parent_plus_phantom': round(combined),
                    'parent_t1': round(t1) if t1 else '',
                    'ratio': f'{ratio:.4f}' if ratio else '',
                    'closes': 'YES' if ratio and abs(ratio - 1) <= TOL else '',
                    'payload_now': (f'{pay_ratio:.2f}' if pay_ratio is not None
                                    else ''),
                    # 'live' means: closes AND the payload demonstrably still
                    # falls short. A MISSING payload ratio is not evidence the
                    # work is undone — it usually means the parent has no
                    # Tier-1 in the payload at all, so the metric could not see
                    # a repair even if one landed. Treating None as live gave
                    # exactly one false positive (as_1893 HEMP | Australia),
                    # whose cells consensus was already filing correctly:
                    # selected 4, admitted 0, drop_consensus_holds_triple 2.
                    'sections': f'{n_ok}/{n_tot}' if n_tot else '',
                    'sections_all_ok': 'YES' if n_tot >= 2 and n_ok == n_tot
                                       else '',
                    'live': ('YES' if (ratio and abs(ratio - 1) <= TOL
                                       and pay_ratio is not None
                                       and pay_ratio < 0.95) else '')})

    # rank by the SECTION proof and by whether the payload still falls short;
    # the Tier-1 closure column is kept but is no longer the primary sort,
    # since it cannot see a partial swallow at all.
    def _pay(r):
        try:
            return float(r['payload_now'])
        except (TypeError, ValueError):
            return 9.0
    rows.sort(key=lambda r: (r['sections_all_ok'] != 'YES', _pay(r),
                             -r['n_rows']))
    out = BASE / 'reports' / 'phantom_region_articles.csv'
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else
                           ['engine', 'volume', 'group', 'phantom_article'])
        w.writeheader()
        w.writerows(rows)
    n_close = sum(1 for r in rows if r['closes'] == 'YES')
    n_live = sum(1 for r in rows if r['live'] == 'YES')
    print(f'place labels: {len(places):,}   candidates: {len(rows)}   '
          f'closing on the parent Tier-1: {n_close}   '
          f'LIVE (closing AND the payload still reads < 0.95): {n_live}')
    n_sec = sum(1 for r in rows if r['sections_all_ok'] == 'YES')
    n_sec_live = sum(1 for r in rows if r['sections_all_ok'] == 'YES'
                     and _pay(r) < 0.95)
    print(f'  every printed subtotal reconciles: {n_sec}   '
          f'...and the payload still reads < 0.95: {n_sec_live}')
    print(f'-> {out}')
    for r in rows[:20]:
        print(f"  [{r['closes'] or '  '}] {r['engine']:3} {r['volume']} "
              f"{r['group'][:22]:<22} | {r['phantom_article'][:26]:<26} "
              f"-> {str(r['parent_article'])[:22]:<22} {r['n_rows']:>3}r "
              f"sec {r['sections'] or '-':>5}  payload_now={r['payload_now'] or '-'}")


if __name__ == '__main__':
    main()
