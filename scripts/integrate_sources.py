#!/usr/bin/env python3
"""Merge the three extraction sources into one pipeline output table.

country_year_consensus (tabular, voted) + country_obs_twoup (two-up layout) +
country_obs_runin (run-in text) -> country_year_final. Keyed by
(commodity article-sig, canonical country, year); prefer the voted consensus,
then two-up, then run-in (fills gaps the tabular parser missed). This turns the
staged recoveries into actual pipeline output the harness reads.
"""
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

import duckdb
import validate_gold as V

BASE = Path('/home/jic823/uk_trade_db')


def is_subtotal(c):
    """A printed subtotal row ("Total from Foreign Countries", "Total from
    British Possessions", "Total to ...") — NOT a country. parse_country folds
    these into 'TOTAL', but the two-up gap-fill parser keeps the descriptive
    label, so ~400 leaked in and were summed as countries. Any label whose
    first word is 'total' is a subtotal."""
    return not c or c == 'world' or c.split(' ', 1)[0] == 'total'


_COLONIAL = ('india', 'indies', 'ceylon', 'bengal', 'madras', 'bombay',
             'scinde', 'burmah', 'hong kong', 'straits', 'australas',
             'australia', 'new south wales', 'victoria', 'queensland',
             'zealand', 'tasmania', 'cape', 'natal', 'canada', 'possession',
             'mauritius', 'guiana', 'west india')


def subtotal_bucket(c):
    """For a leaked 'Total from X' subtotal, the aggregate bucket it stands for
    when its detail is missing: possessions vs foreign. None if not a subtotal
    we retain."""
    if 'possession' in c:
        return 'British Possessions'
    if 'foreign' in c:
        return 'Foreign Countries'
    return None


def is_colonial(c):
    return any(k in c for k in _COLONIAL)


def load_csv(path, src):
    # pass 1: which (asig, year) blocks already carry colonial / foreign DETAIL,
    # so we know whether a leaked "Total from Possessions/Foreign" subtotal is a
    # redundant double-count (detail present -> drop) or the only carrier of
    # that volume (detail absent -> keep as one aggregate bucket).
    has_col, has_for = set(), set()
    recs = list(csv.DictReader(open(path)))
    for r in recs:
        if r.get('flow') != 'import':
            continue
        art = (r['article'] or '').lstrip(',»„"”„ ').strip()
        grp = r['article_group'] or ''
        asig = V.sig(art) or V.sig(f"{grp} {art}")
        c = V.cnorm(r['country_raw'])
        if not asig or is_subtotal(c) or ' : ' in (r['country_raw'] or ''):
            continue
        key = (asig, int(r['year']))
        (has_col if is_colonial(c) else has_for).add(key)

    for r in recs:
        if r.get('flow') != 'import':
            continue
        art = (r['article'] or '').lstrip(',»„"”„ ').strip()
        grp = r['article_group'] or ''
        asig = V.sig(art) or V.sig(f"{grp} {art}")   # generic article -> group fallback
        if not asig:
            continue
        c = V.cnorm(r['country_raw'])
        country = r['country_raw']
        if ' : ' in (r['country_raw'] or ''):
            continue
        if is_subtotal(c):
            bucket = subtotal_bucket(c)              # retain only as a fallback
            key = (asig, int(r['year']))
            covered = key in (has_col if bucket == 'British Possessions'
                              else has_for)
            if bucket is None or covered:
                continue                             # detail present -> drop
            c, country = V.cnorm(bucket), bucket     # keep as aggregate bucket
        try:
            q = float(r['quantity'] or 0)
        except ValueError:
            q = 0.0
        if q <= 0:
            continue
        yield (asig, c, int(r['year'])), {
            'group': grp.upper(), 'article': art, 'country': country,
            'unit': r['unit'] or '', 'qty': q, 'year': int(r['year']),
            'value': float(r['value'] or 0) if (r['value'] or '').strip() else None,
            'src': src, 'q_tier': 'C', 'v_tier': 'C'}


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'))
    out_rows = []                                # keep consensus rows AS-IS
    consensus_commod = set()                     # (article-sig, year) present in consensus
    consensus_triples = set()                    # (article-sig, country, year)
    consensus_triples_ga = set()                 # (group-aware sig, country, year)

    # group-repair manifest loads FIRST: a repair may declare supersede_years
    # — the block's original consensus reading was wrong wholesale (as_1883
    # cotton row-slip; as_1899 hay parsed as hats) — and those consensus rows
    # must be dropped BEFORE the presence-guards are built, or the guards
    # would block the repaired rows from re-entering.
    grepairs = []
    grf = BASE / 'reference' / 'group_repairs.csv'
    if grf.exists():
        grepairs = list(csv.DictReader(open(grf)))
    # a repair with new_country is ROW-level (fixes a slipped country label):
    # it must not suppress its whole block from step 4 — collect the exact
    # (volume, group, article, country_raw) rows it replaces instead
    repaired_blocks = {(gr['volume'], gr['article_group'], gr['article'] or None)
                       for gr in grepairs if not (gr.get('new_country') or '').strip()}
    repaired_rows = set()
    for gr in grepairs:
        if (gr.get('new_country') or '').strip():
            for (ctry,) in con.execute("""SELECT DISTINCT country_raw
                    FROM country_obs
                    WHERE volume = ? AND flow = ? AND article_group = ?
                      AND article IS NOT DISTINCT FROM ?
                      AND row_seq BETWEEN ? AND ?""",
                    [gr['volume'], gr['flow'], gr['article_group'],
                     gr['article'] or None,
                     int(gr['seq_start']), int(gr['seq_end'])]).fetchall():
                repaired_rows.add((gr['volume'], gr['article_group'],
                                   gr['article'] or None, ctry))
    # manual_rows with replace=1: a page-adjudicated hand-keyed CELL replaces
    # the pipeline's reading everywhere (as_1883 BPSA sheep wool printed a
    # broken digit — 18,870,981 for 48,870,981; the column total, exactly
    # 30,000,000 short, plus the GBP/lb rate pin the true value). Collected
    # up front so step 1 can drop the superseded cells.
    manual_replace = set()     # (group-aware sig, cnorm country, year)
    mrf0 = BASE / 'reference' / 'manual_rows.csv'
    if mrf0.exists():
        for mr in csv.DictReader(open(mrf0)):
            if (mr.get('replace') or '').strip() == '1':
                g0 = (mr['article_group'] or '').strip()
                a0 = (mr['article'] or '').strip()
                ga0 = V.sig(f"{g0.upper()} {a0}") or V.sig(a0)
                manual_replace.add((ga0, V.cnorm(mr['country']),
                                    int(mr['year'])))

    supersede = set()          # (WRONG group, article, year) to drop —
                               # applied to consensus AND the gap-fill
                               # sources (infonly/twoup/runin/subentry): a
                               # superseded label's rows are wrong in EVERY
                               # parse of the page (as_1874 twoup wine is
                               # label-slipped where the obs copy glued)
    for gr in grepairs:
        for y_sup in (gr.get('supersede_years') or '').split(';'):
            if y_sup.strip():
                supersede.add((gr['article_group'].upper(),
                               (gr['article'] or '').strip(), int(y_sup)))

    # cells a group repair already supplies (step 6). The repair names ONE
    # engine's copy of a glue block; the OTHER engine's copy of the same
    # printed table is Infinity-only under its own stale group, so step 2
    # admits it a second time and the year doubles. as_1899 oats is printed
    # once and reached country_year_final twice — CORDAGE|Oats repaired to
    # CORN AND GRAIN (Chandra) plus CHEESE|Oats (Infinity) — reading 1.02 of
    # its printed total only because the sub-entry rows were dropped from one
    # of them. A hand-adjudicated repair outranks a stale-group re-print, but
    # only CELL BY CELL: the two engines rarely lose the same row, and the
    # Infinity copy is often the only carrier of what the repair concedes
    # (as_1873 LARD's repair note says "Germany stays lost (honest)" — the
    # Infinity copy has it, 21,848 cwt).
    repaired_cells = set()
    for gr in grepairs:
        tbl = ('country_obs_inf' if (gr.get('obs_source') or '').strip() == 'inf'
               else 'country_obs')
        asig_r = (V.sig((gr['new_article'] or '').strip())
                  or V.sig(f"{gr['new_group']} {gr['new_article'] or ''}"))
        if not asig_r or not (gr['seq_start'] or '').strip():
            continue
        rrows = con.execute(f"""SELECT country_raw, year FROM {tbl}
                WHERE volume = ? AND flow = ? AND article_group = ?
                  AND article IS NOT DISTINCT FROM ?
                  AND row_seq BETWEEN ? AND ? AND year IS NOT NULL
                ORDER BY row_seq""",
                [gr['volume'], gr['flow'], gr['article_group'],
                 gr['article'] or None,
                 int(gr['seq_start']), int(gr['seq_end'])]).fetchall()
        if (gr.get('label_shift') or '').strip() == '1':
            # the repair re-pairs label(i+1) with numbers(i), so the FIRST
            # label keeps nothing — it is precisely the row the repair note
            # concedes as lost, and the other engine may still carry it
            # (as_1873 LARD Germany, 21,848 cwt)
            rrows = rrows[1:]
        for ctry_r, y_r in rrows:
            cr = V.cnorm(gr['new_country'] or ctry_r)
            repaired_cells.add((gr['volume'], asig_r, cr, int(y_r)))
            if ' : ' in (ctry_r or ''):
                repaired_cells.add((gr['volume'], asig_r,
                                    V.cnorm(ctry_r.partition(' : ')[2]), int(y_r)))

    # 1) consensus (voted) — keep every row, no collapsing
    rows = con.execute("""SELECT article_group, article, country, unit, year,
        quantity, value, q_tier, v_tier
        FROM country_year_consensus WHERE flow='import'""").fetchall()
    n_sup = 0
    for grp, art, ctry, unit, y, q, v, qt, vt in rows:
        if ((grp or '').upper(), (art or '').strip(), int(y)) in supersede:
            n_sup += 1
            continue
        a = (art or '').strip()
        asig = V.sig(a) or V.sig(f"{grp or ''} {a}")   # generic article -> group fallback
        c = V.cnorm(ctry)
        if not asig or is_subtotal(c) or ' : ' in (ctry or ''):
            continue
        # Value-only origin tables: the volumes print a good many origin
        # tables with NO quantity column at all (Toys, Watches, Lace, Silk
        # Manufactures...) where the only figure per country is GBP value.
        # The voter keeps those cells with real v_tiers; this quantity guard
        # used to discard every one of them, which left the 56 commodities
        # whose Tier-1 line is a Value series (GBP71.3M) at nodata forever.
        # Admit them under the literal unit 'Value' with the GBP figure in
        # the quantity slot — the SAME convention the abstract's Tier-1
        # Value series already uses — so downstream consumers reconcile
        # them against the Value anchor and never mistake them for
        # quantities. 246 of the 586 value-only blocks with a T1 value
        # anchor close exactly (reports/value_only_origins_findings.md).
        valonly = not q or float(q) <= 0
        if valonly and not (v and float(v) > 0):
            continue
        consensus_commod.add((asig, int(y)))
        consensus_triples.add((asig, c, int(y)))
        # group-aware key: a generic article ('Raw') gives every commodity
        # the same article-first sig, so COTTON|Raw|ceylon would block the
        # COFFEE|Raw|ceylon sub-entry — step 4 checks this set instead
        ga = V.sig(f"{(grp or '').strip()} {a}") or asig
        if (ga, c, int(y)) in manual_replace:
            n_sup += 1
            continue           # cell replaced by a page-adjudicated manual row
        consensus_triples_ga.add((ga, c, int(y)))
        if valonly:
            out_rows.append({'group': (grp or '').upper(), 'article': a,
                'country': ctry, 'unit': 'Value', 'qty': float(v),
                'value': float(v), 'year': int(y), 'src': 'consensus',
                'q_tier': vt or 'C', 'v_tier': vt or 'C'})
            continue
        out_rows.append({'group': (grp or '').upper(), 'article': a, 'country': ctry,
            'unit': unit or '', 'qty': float(q), 'value': float(v) if v else None,
            'year': int(y), 'src': 'consensus',
            'q_tier': qt or 'C', 'v_tier': vt or 'C'})

    # 2) Infinity-only blocks — the two OCR engines fail on DIFFERENT pages
    #    (measured 2026-07-15: 4,493 import blocks only in Chandra, 3,279 only
    #    in Infinity, 4,663 shared; Chandra is the better engine overall —
    #    75.1% vs 66.1% printed-total arithmetic — so it stays primary, but
    #    reconcile_country arbitrates only blocks the primary found, so
    #    Infinity-only pages (cheese 1885, tobacco 1879, late-era tea) never
    #    entered the pipeline). Admit their member rows for commodity-years
    #    absent from consensus; a year-block whose members sum to its own
    #    printed Total (0.5%) enters at tier B, else C.
    added = defaultdict(int)
    seen_added = set()

    def bnorm(s):
        return re.sub(r'[^a-z0-9 ]', '', (s or '').lower()).strip()

    ch_keys = {(v, bnorm(g), bnorm(a)) for v, g, a in con.execute(
        """SELECT DISTINCT volume, article_group, article
           FROM country_obs WHERE flow='import'""").fetchall()}
    inf_blocks = defaultdict(list)
    for v, g, a, c, u, y, q, val in con.execute(
            """SELECT volume, article_group, article, country_raw, unit,
               year, quantity, value FROM country_obs_inf
               WHERE flow='import' ORDER BY volume, row_seq""").fetchall():
        inf_blocks[(v, bnorm(g), bnorm(a), int(y))].append((g, a, c, u, q, val))
    for (v, gk, ak, y), rows in inf_blocks.items():
        if (v, gk, ak) in ch_keys:
            continue
        total_q = next((q for _, _, c, _, q, _ in rows if c == 'TOTAL'), None)
        total_v = next((vv for _, _, c, _, _, vv in rows if c == 'TOTAL'), None)
        # 'Parent : Sub' members: dropping them outright loses the only copy of
        # a segment whenever the block prints its detail region-qualified and
        # never prints the parent aggregate — as_1897 TALLOW's whole American
        # section is three 'United States of America : On the Atlantic/Pacific'
        # rows (260,602 cwt in 1897 alone), so tallow read 0.82/0.73/0.74 of
        # its printed total for 1897-99. Keep them unless the SAME PRINTED
        # SEGMENT also carries a plain 'Parent' row, which is the case where
        # the sub-entries only re-state an aggregate the voter already has.
        # Segment, not block: an Infinity glue block runs several commodities
        # under one stale article, and as_1899's next commodity contributes a
        # plain 'United States of America' that has nothing to do with the
        # tallow table's Atlantic/Pacific split. Label stays literal
        # ('Region : Sub'), the step-4 convention: every validator skips ' : '
        # countries, so gold numbers are untouched.
        seg_plain, seg_of, seg = [], {}, set()
        for i, (_, _, c, _, _, _) in enumerate(rows):
            if (c or 'TOTAL') == 'TOTAL':
                seg_plain.append(seg)
                seg = set()
            elif c and ' : ' not in c:
                seg.add(V.cnorm(c))
            seg_of[i] = len(seg_plain)
        seg_plain.append(seg)
        members = []
        for i, (g, a, c, u, q, val) in enumerate(rows):
            if (c or 'TOTAL') == 'TOTAL':
                continue
            if ' : ' in c:
                parent, _, sub = c.partition(' : ')
                sub = sub.strip()
                if (V.cnorm(parent) in seg_plain[seg_of[i]]
                        or c.count(':') != 1
                        or not sub or len(sub) > 60 or re.search(r'\d', sub)
                        or is_subtotal(V.cnorm(sub))):
                    continue
            cn = V.cnorm(c)
            if (is_subtotal(cn) or re.search(r'\d', c) or len(c) > 60
                    or not q or q <= 0 or q > 1e12):
                continue
            # abstract/duty rows leak with article labels as "countries"
            # ('Unmanufactured - - - ”', 'Wine - - - Gallons'): reject
            # dash-leader residue, ditto/quote marks, and unit words
            if (re.search(r'-\s*-', c) or re.search(r'[”“„"»«]', c)
                    or re.search(r'\b(Cwts?|Tons?|Loads?|Gallons?|Lbs?|'
                                 r'Number|Pieces?|Qrs?|Bushels?|Yards?|'
                                 r'Ozs?|Galls?)\.?\s*$', c, re.I)):
                continue
            members.append((g, a, c, u, q, val))
        if len(members) < 2:
            continue
        q_sum = sum(m[4] for m in members)
        v_sum = sum(m[5] or 0 for m in members)
        q_ok = total_q and abs(q_sum - total_q) <= 0.005 * total_q
        v_ok = total_v and v_sum and abs(v_sum - total_v) <= 0.005 * total_v
        for g, a, c, u, q, val in members:
            art = (a or '').lstrip(',»„"”° ').strip()
            if ((g or '').upper(), art, y) in supersede:
                continue
            asig = V.sig(art) or V.sig(f"{g or ''} {art}")
            if not asig or (asig, y) in consensus_commod:
                continue
            # dedup key: a 'Region : Sub' member and a bare 'Sub' member are
            # the same printed line read out of two volumes' copies of the
            # five-year table (as_1897 tallow prints 'Australasia : New South
            # Wales', as_1899 prints it bare), so both must compete for ONE
            # slot or the year doubles.
            ckey = V.cnorm(c.partition(' : ')[2]) if ' : ' in c else V.cnorm(c)
            if ((v, asig, V.cnorm(c), y) in repaired_cells
                    or (v, asig, ckey, y) in repaired_cells):
                continue          # step 6 already supplies this printed cell
            if (asig, ckey, y) in seen_added or (asig, V.cnorm(c), y) in seen_added:
                continue
            # honor page-adjudicated manual replaces the way step 1 does
            # (maize Canada 1893: the infonly cell reads 8,260,851/786,614,
            # both digits S-form-broken; the manual row carries the page
            # truth and must not be shadowed by the broken infonly copy)
            ga2 = V.sig(f"{(g or '').upper()} {art}") or asig
            if ((ga2, V.cnorm(c), y) in manual_replace
                    or (asig, V.cnorm(c), y) in manual_replace):
                continue
            seen_added.add((asig, V.cnorm(c), y))
            seen_added.add((asig, ckey, y))
            out_rows.append({'group': (g or '').upper(), 'article': art,
                'country': c, 'unit': u or '', 'qty': float(q),
                'value': float(val) if val else None, 'year': y,
                'src': 'infonly', 'q_tier': 'B' if q_ok else 'C',
                'v_tier': 'B' if v_ok else 'C'})
            added['infonly'] += 1

    # ---- gap-fill blocks that are really EXPORT tables -------------------
    # The Abstract prints an import table, a table of British produce
    # EXPORTED and a table of foreign goods RE-EXPORTED for the same
    # commodity and year, and they are typographically identical. When a
    # column-top heading is lost the parser files an export table as an
    # import one, and the gap-fill sources admit it because its stale label
    # gives it a different signature from the import commodity's — which is
    # exactly why the "consensus already has this commodity" guard misses.
    # Butter 1882's import block closes to the digit at its printed 2,169,717
    # cwt and a second block of six origins rides in beside it, adding 1.3%.
    #
    # The test is arithmetic, not a guess about which countries look like
    # destinations (that screen was tried on tallow and tripped on Chile and
    # the Channel Islands, which is where British tallow came from): the
    # block's own printed Total IS the export_uk or reexport national line,
    # to the digit. Butter 1882's intruder totals 31,640 cwt / GBP219,726 and
    # the export_uk Tier-1 line is 31,640 / GBP219,726.
    #
    # A block is only rejected when NONE of its Totals is the import line.
    # Some volumes print all three tables under one lost heading — butter
    # 1880 has three Total rows, 2,326,305 import, 31,408 export, 43,125
    # re-export — and dropping that block would take the import table with
    # it. Those are logged by scripts/detect_flow_leakage.py for per-cell
    # work, not handled here.
    t1_flow = defaultdict(dict)
    for flow, g0, a0, y0, v0 in con.execute(
            """SELECT flow, article_group, article, year, value FROM consensus
               WHERE measure='quantity' AND value > 0""").fetchall():
        a0 = (a0 or '').strip()
        s0 = V.sig(a0) or V.sig(f"{(g0 or '').strip()} {a0}")
        if s0:
            t1_flow[(s0, int(y0))].setdefault(flow, v0)
    # Member sums of every PRIMARY-parse block, keyed by the number they come
    # to. Used for the mixed case below: if some block in the same year
    # already adds up to the import national total, that table is parsed and
    # a gap-fill copy of the page has nothing to contribute to it.
    obs_closes = set()
    for tbl in ('country_obs', 'country_obs_inf'):
        bsum = defaultdict(float)
        for g0, a0, y0, c0, q0 in con.execute(
                f"""SELECT article_group, article, year, country_raw, quantity
                    FROM {tbl} WHERE flow='import' AND year IS NOT NULL
                      AND quantity > 0""").fetchall():
            if 'total' in (c0 or '').lower():
                continue
            bsum[((g0 or ''), (a0 or ''), int(y0))] += q0
        obs_closes |= {(k[2], round(s)) for k, s in bsum.items()}

    leak_blocks, n_leak = set(), 0
    for tbl in ('country_obs_twoup', 'country_obs_runin'):
        btot = defaultdict(list)
        for g0, a0, y0, q0 in con.execute(
                f"""SELECT article_group, article, year, quantity FROM {tbl}
                    WHERE flow='import' AND year IS NOT NULL AND quantity > 0
                      AND lower(country_raw) LIKE '%total%'""").fetchall():
            btot[((g0 or '').upper(), (a0 or '').strip(), int(y0))].append(q0)
        for (g0, a0, y0), qs in btot.items():
            sig0 = V.sig(a0) or V.sig(f"{g0} {a0}")
            fl = t1_flow.get((sig0, y0)) or {}
            imp = fl.get('import')
            other = any(fl.get(f) and abs(q0 - fl[f]) < 0.5
                        for q0 in qs for f in ('export_uk', 'reexport'))
            if imp and any(abs(q0 - imp) < 0.5 for q0 in qs):
                # MIXED: all three tables under one lost heading (butter 1880
                # has three Total rows, 2,326,305 import / 31,408 export /
                # 43,125 re-export). Rejecting the block would take the import
                # table with it — unless the primary parse already carries
                # that table and closes on it, in which case the gap-fill copy
                # can only contribute the export rows. A gap-filler with no
                # gap to fill is all surplus.
                if other and (y0, round(imp)) in obs_closes:
                    leak_blocks.add((g0, a0, y0))
                continue
            if other:
                leak_blocks.add((g0, a0, y0))

    # 3) two-up, 4) run-in — add ONLY commodity-years absent from consensus
    #    (dedup within the added source by (article-sig, country, year))
    for path, src in [(BASE / 'exports' / 'twoup_country.csv', 'twoup'),
                      (BASE / 'exports' / 'runin_country.csv', 'runin')]:
        for (asig, c, y), rec in load_csv(path, src):
            if (rec['group'], (rec['article'] or '').strip(), y) in supersede:
                continue
            if (rec['group'], (rec['article'] or '').strip(), y) in leak_blocks:
                n_leak += 1
                continue
            if (asig, y) in consensus_commod:
                continue                          # consensus already has this commodity
            if (asig, c, y) in seen_added:
                continue
            seen_added.add((asig, c, y))
            out_rows.append(rec)
            added[src] += 1

    # 4) colonial sub-entry detail ('Australasia : New South Wales').
    #    (step 4 must NOT admit sub-entry rows from a block the group-repair
    #    manifest relabels — the as_1899 CORDAGE|Raw block is really
    #    COTTON|Raw, and its 'United States of America : On the Atlantic'
    #    rows would otherwise enter as 'Cordage' sub-entries AND again as
    #    repaired cotton in step 6.)
    #    vote_country_years admits these into the consensus only when the
    #    block's grand total falls short without them (tea/Ceylon); when a
    #    parent aggregate row is present the subs are dropped as redundant —
    #    correct for NATIONAL totals, but they are the only carrier of
    #    per-state / per-presidency origin detail. Recover them under their
    #    literal 'Region : Sub' label: every validator skips ' : ' countries,
    #    so gold numbers are untouched, and analysts cannot confuse them with
    #    plain countries. Mini-vote across volumes like vote_country_years.
    GOOD = {'exact', 'inf_struct', 'inf_block', 'swap', 'anchor', 'digit_fix',
            'inf_only', 't1_anchor'}
    subrows = con.execute("""SELECT volume, article_group, article, country_raw,
            unit, year, quantity, value, q_block, q_cell, v_block, v_cell,
            price_flag
        FROM country_rescored
        WHERE flow='import' AND country_raw LIKE '% : %'
          AND quantity IS NOT NULL AND quantity > 0""").fetchall()
    subbuckets = defaultdict(list)
    for vol, grp, art, ctry, unit, y, q, v, qb, qc, vb, vc, pf in subrows:
        if (vol, grp, art or None) in repaired_blocks:
            continue                  # block relabelled by step 6 instead
        if (vol, grp, art or None, ctry) in repaired_rows:
            continue                  # row's country label fixed by step 6
        if ctry.count(':') != 1:
            continue
        parent, sub = (s.strip() for s in ctry.split(':', 1))
        if (not parent or not sub or re.search(r'\d', sub)
                or sub.split()[0].lower() == 'total' or len(sub) > 60):
            continue
        art = (art or '').lstrip(',»„"”° ').strip()
        if ((grp or '').upper(), art, int(y)) in supersede:
            continue
        # GROUP-AWARE sig: an article-first sig conflates every commodity
        # printing the same generic article — COTTON|Raw|ceylon in consensus
        # was blocking the COFFEE|Raw|ceylon sub-entries (Ceylon coffee
        # 1893/95/98 silently dropped)
        asig = V.sig(f"{grp or ''} {art}") or V.sig(art)
        if not asig:
            continue
        # a page-adjudicated manual replace supersedes the sub-entry too —
        # steps 1 and 2 already honour it, and without this a replace=1 row
        # aimed at a 'Region : Sub' cell (palm oil 1878's West African
        # 'Not particularly designated') is ADDED BESIDE the broken reading
        # instead of instead of it
        # ...and the SUB half has to be tested on its own, because
        # V.cnorm('Australasia : Victoria') is 'australasia': a manual row
        # naming Victoria never matched the sub-entry cell it was written to
        # replace, so butter 1899 kept the GBP1,651,338 reading beside the
        # hand-adjudicated 1,051,338 and the value column stayed 3.5% over.
        if any((s, cn, int(y)) in manual_replace
               for s in (asig, V.sig(art))
               for cn in (V.cnorm(ctry), V.cnorm(sub))):
            continue
        key = (asig, V.cnorm(parent), V.cnorm(sub), (unit or '').strip(), int(y))
        subbuckets[key].append({
            'grp': grp, 'art': art, 'ctry': f'{parent} : {sub}', 'q': q, 'v': v,
            'q_ok': qb in GOOD or qc in ('agree', 'repaired', 'human') or pf == 'ok',
            'v_ok': vb in GOOD or vc in ('agree', 'repaired', 'human')})
    n_sub = 0
    for (asig, _p, csub, unit, y), readings in subbuckets.items():
        if (asig, csub, y) in consensus_triples_ga:
            continue          # vote already admitted & relabelled this sub
        tally = Counter(round(r['q']) for r in readings)
        qval, n = tally.most_common(1)[0]
        winners = [r for r in readings if round(r['q']) == qval]
        q_tier = 'A' if n >= 2 else ('B' if any(r['q_ok'] for r in winners) else 'C')
        vvals = [round(r['v']) for r in winners if r['v'] is not None]
        vval = Counter(vvals).most_common(1)[0][0] if vvals else None
        v_tier = ('A' if len(vvals) >= 2 and Counter(vvals).most_common(1)[0][1] >= 2
                  else ('B' if any(r['v_ok'] for r in winners if r['v'] is not None)
                        else 'C'))
        rep = winners[0]
        out_rows.append({'group': (rep['grp'] or '').upper(), 'article': rep['art'],
                         'country': rep['ctry'], 'unit': unit, 'qty': float(qval),
                         'value': float(vval) if vval is not None else None,
                         'year': y, 'src': 'subentry',
                         'q_tier': q_tier, 'v_tier': v_tier})
        n_sub += 1

    # 5) flow repairs (reference/flow_repairs.csv): human-attested blocks the
    #    parser filed under the wrong flow (as_1892 "Wool'd)" — the wool
    #    IMPORT origin table read as export_uk). Rows come in at tier C:
    #    single printing, no independent check survives the misfile.
    n_flowfix = 0
    frf = BASE / 'reference' / 'flow_repairs.csv'
    if frf.exists():
        for fr in csv.DictReader(open(frf)):
            if fr['flow_to'] != 'import':
                continue
            fixed_rows = con.execute("""SELECT article_group, article,
                    country_raw, unit, year, quantity, value
                FROM country_rescored
                WHERE volume = ? AND article_group = ? AND year = ?
                  AND flow = ? AND quantity IS NOT NULL AND quantity > 0
                  AND country_raw != 'TOTAL'""",
                [fr['volume'], fr['article_group'], int(fr['year']),
                 fr['flow_from']]).fetchall()
            for grp, art, ctry, unit, y, q, v in fixed_rows:
                out_rows.append({
                    'group': (grp or '').upper(), 'article': (art or '').strip(),
                    'country': ctry, 'unit': unit or '', 'qty': float(q),
                    'value': float(v) if v is not None else None,
                    'year': int(y), 'src': 'flowfix',
                    'q_tier': 'C', 'v_tier': 'C'})
                n_flowfix += 1

    # 6) group repairs (reference/group_repairs.csv): human-attested SEGMENTS of
    #    OCR "glue blocks" — multi-page runs the parser concatenated under one
    #    stale (group, article) when column-top headings were lost (as_1878 raw
    #    tobacco under SPIRITS|Unmanufactured; as_1887 a 213-row block under
    #    SPIRITS|Rum spanning rum+tea+tobacco+cigars+wine). Each CSV row names
    #    an obs row_seq range and the true (group, article). Sourced from
    #    country_obs (country_rescored drops rows, so seq ranges only align
    #    there). Tier C: single printing, no independent check survives.
    n_groupfix = 0
    # ---- why-rejected accounting. A group_repairs block that is
    # arithmetically right can still deliver NOTHING to the payload, and
    # nothing said which gate ate it: session 11 lost caoutchouc 1885/1887
    # and flax 1872 that way, three years across two iterations, each time
    # guessing. Count every row's disposition per repair and write it out.
    gf_audit = []
    if grepairs:
        for gr in grepairs:
            why = Counter()
            # obs_source='inf': pull the segment from the OTHER engine —
            # used when the primary's copy is label-slipped beyond repair
            # (as_1893 oats lost its leading 'Russia' label so every
            # foreign-half value sits one country up; Infinity's copy is
            # complete and sums to the printed TOTAL exactly)
            obs_table = ('country_obs_inf'
                         if (gr.get('obs_source') or '').strip() == 'inf'
                         else 'country_obs')
            fixed_rows = con.execute(f"""SELECT country_raw, unit, year,
                    quantity, value
                FROM {obs_table}
                WHERE volume = ? AND flow = ? AND article_group = ?
                  AND article IS NOT DISTINCT FROM ?
                  AND row_seq BETWEEN ? AND ?
                ORDER BY row_seq""",
                [gr['volume'], gr['flow'], gr['article_group'],
                 gr['article'] or None,
                 int(gr['seq_start']), int(gr['seq_end'])]).fetchall()
            # label_shift=1: a row-slipped block — every quantity belongs to
            # the label ONE ROW DOWN (as_1883 cotton: 'British North America'
            # carries the US's 11,066,166). Re-pair label(i+1) with
            # numbers(i); the first label (its number precedes the block) and
            # the last number (its label follows the block) drop out.
            if (gr.get('label_shift') or '').strip() == '1':
                fixed_rows = [(fixed_rows[i + 1][0],) + fixed_rows[i][1:]
                              for i in range(len(fixed_rows) - 1)]
            why['selected'] = len(fixed_rows)
            fixed_rows = [r for r in fixed_rows
                          if r[3] is not None and r[3] > 0]
            why['drop_null_qty'] = why['selected'] - len(fixed_rows)
            new_grp, new_art = gr['new_group'].upper(), gr['new_article']
            # the true commodity is human-attested: sig from group+article,
            # NOT the article-first convention (a bare 'Unmanufactured' sig
            # collides with every other commodity printing that article)
            asig = V.sig(f"{new_grp} {new_art}") or V.sig(new_art)
            for ctry, unit, y, q, v in fixed_rows:
                if (gr.get('new_country') or '').strip():
                    ctry = gr['new_country']
                # run-in section headers absorb into the first country label
                # ('COFFEE: From France', 'COCOA : From Germany') — keep the
                # country, drop the heading residue
                mrun = re.match(r'^[^:]*:\s*From\s+(.+)$', ctry or '')
                if mrun:
                    ctry = mrun.group(1).strip()
                c = V.cnorm(ctry)
                if is_subtotal(c):
                    why['drop_subtotal'] += 1
                    continue
                # ' : ' sub-entries stay, with their literal 'Parent : Sub'
                # label (same contract as source='subentry': validators skip
                # them, the viz folds them) — in the 1893+ multiyear layout
                # they are the SOLE carrier ('United States of America : On
                # the Atlantic' raw cotton 1898-99)
                if ' : ' in (ctry or ''):
                    parent, sub = (s.strip() for s in ctry.split(':', 1))
                    if not sub or re.search(r'\d', sub) or len(sub) > 60:
                        why['drop_bad_subentry'] += 1
                        continue
                    # key sub-entries by parent+sub, not the cnorm-folded
                    # parent alone: cnorm('Russia : Northern Ports') is
                    # 'russia', so a ports row admitted by one repair was
                    # blocking the plain-Russia row of another (as_1893
                    # oats) — parent and sub-detail must coexist, same
                    # contract as step 4
                    c = f'{V.cnorm(parent)} :: {V.cnorm(sub)}'
                if not asig:
                    why['drop_no_sig'] += 1
                    continue
                if (asig, c, int(y)) in consensus_triples_ga:
                    why['drop_consensus_holds_triple'] += 1
                    continue
                if (asig, c, int(y)) in seen_added:
                    why['drop_already_added'] += 1
                    continue
                seen_added.add((asig, c, int(y)))
                # strip_values=1: the block's quantity column is proven
                # (closure/brackets) but its value column is a PHANTOM — a
                # neighbouring table's column both engines swallowed (the
                # as_1882 leather 'values' fail every rate/total check in
                # BOTH engines while the qtys bracket cleanly). Admit the
                # quantities, drop the values.
                strip = (gr.get('strip_values') or '').strip() == '1'
                out_rows.append({
                    'group': new_grp, 'article': new_art,
                    'country': ctry,
                    'unit': gr.get('new_unit') or unit or '', 'qty': float(q),
                    'value': None if strip else (
                        float(v) if v is not None else None),
                    'year': int(y), 'src': 'groupfix',
                    'q_tier': 'C', 'v_tier': 'C'})
                n_groupfix += 1
                why['admitted'] += 1
            gf_audit.append({
                'volume': gr['volume'], 'article_group': gr['article_group'],
                'article': gr.get('article') or '',
                'seq_start': gr['seq_start'], 'seq_end': gr['seq_end'],
                'obs_source': (gr.get('obs_source') or '').strip() or 'ch',
                'target_sig': '+'.join(asig) if asig else '',
                **{k: why.get(k, 0) for k in (
                    'selected', 'admitted', 'drop_null_qty', 'drop_subtotal',
                    'drop_bad_subentry', 'drop_no_sig',
                    'drop_consensus_holds_triple', 'drop_already_added')}})

    # 6b) manual rows (reference/manual_rows.csv): page-attested hand-keyed
    #    data for tables NO parse carries (as_1892 wheat: printed p.53 was
    #    scanned fine but Chandra dropped the block and Infinity OCR'd it as
    #    <br>-run text inside a two-up td — invisible to both table
    #    extractors). Tiers come from the CSV: A when every printed segment
    #    total reconciles to the digit and digits were adjudicated against
    #    the page image.
    n_manual = 0
    mrf = BASE / 'reference' / 'manual_rows.csv'
    if mrf.exists():
        for mr in csv.DictReader(open(mrf)):
            # export_uk manual rows are admitted the same way (the final
            # table already mixes flows via the twoup gap-fill; the 1883
            # piece-goods Aden cell is export-flow and page-attested)
            if mr['flow'] not in ('import', 'export_uk'):
                continue
            grp = (mr['article_group'] or '').strip()
            art = (mr['article'] or '').strip()
            ctry = mr['country']
            asig = V.sig(f"{grp.upper()} {art}") or V.sig(art)
            c = V.cnorm(ctry)
            if ' : ' in (ctry or ''):
                parent, sub = (s.strip() for s in ctry.split(':', 1))
                c = f'{V.cnorm(parent)} :: {V.cnorm(sub)}'
            y = int(mr['year'])
            if not asig or is_subtotal(V.cnorm(ctry)):
                continue
            replacing = (asig, V.cnorm(ctry), y) in manual_replace
            if not replacing and ((asig, c, y) in consensus_triples_ga
                                  or (asig, c, y) in seen_added):
                continue
            seen_added.add((asig, c, y))
            out_rows.append({
                'group': grp.upper(), 'article': art, 'country': ctry,
                'unit': mr['unit'] or '', 'qty': float(mr['quantity']),
                'value': float(mr['value']) if (mr['value'] or '').strip() else None,
                'year': y, 'src': 'human',
                'q_tier': mr.get('q_tier') or 'B',
                'v_tier': mr.get('v_tier') or 'B'})
            n_manual += 1

    # 7) group aliases (reference/group_aliases.csv): unambiguous OCR garbles
    #    of a group heading ('HORS' = HOPS, 'BRIINSTONE' = BRIMSTONE) —
    #    relabel IN PLACE across every source and year; the garbled string
    #    never names a real commodity so this cannot collide.
    n_alias = 0
    gaf = BASE / 'reference' / 'group_aliases.csv'
    if gaf.exists():
        alias = {r['wrong_group'].upper(): r['right_group'].upper()
                 for r in csv.DictReader(open(gaf))}
        for r in out_rows:
            if r['group'] in alias:
                r['group'] = alias[r['group']]
                n_alias += 1

    # dedup near-duplicate country rows within a commodity-year: merged engines
    # and summary+detail double-prints inflate over-counted commodities (e.g.
    # Woollen Manufactures had France 74,576,609 AND 74,576,600).
    # Sort best-verified first (stable, consensus already precedes gap-fill)
    # so the surviving duplicate carries the strongest tier.
    RANK = {'A': 1, 'B': 2, 'C': 3}
    out_rows.sort(key=lambda r: (r['src'] != 'consensus',
                                 RANK.get(r['q_tier'], 3)))
    dedup, seen = [], set()
    for r in out_rows:
        k = (r['group'], r['article'], r['year'], V.cnorm(r['country']),
             round(r['qty'] / 1000))
        if k in seen:
            continue
        seen.add(k)
        dedup.append(r)
    out_rows = dedup
    cells = {i: r for i, r in enumerate(out_rows)}   # keep interface below

    # write country_year_final via CSV -> CREATE TABLE (fast path; executemany
    # is pathologically slow on this DB)
    tmp = BASE / 'exports' / '_country_year_final.csv'
    with open(tmp, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['article_group', 'article', 'country', 'unit', 'flow',
                    'year', 'quantity', 'value', 'source',
                    'q_tier', 'v_tier', 'q_rank', 'v_rank'])
        for r in cells.values():
            w.writerow([r['group'], r['article'], r['country'], r['unit'],
                        'import', r['year'] if 'year' in r else r.get('y', ''),
                        r['qty'], r['value'] if r['value'] is not None else '', r['src'],
                        r['q_tier'], r['v_tier'],
                        RANK.get(r['q_tier'], 3), RANK.get(r['v_tier'], 3)])
    con.execute("DROP TABLE IF EXISTS country_year_final")
    con.execute(f"CREATE TABLE country_year_final AS "
                f"SELECT * FROM read_csv_auto('{tmp}', header=true)")
    n = con.execute("SELECT count(*), count(DISTINCT source) FROM country_year_final").fetchone()
    bysrc = con.execute("SELECT source, count(*) FROM country_year_final GROUP BY source").fetchall()
    con.close()
    print(f'country_year_final: {n[0]:,} rows')
    print(f'  by source: {dict(bysrc)}')
    print(f'  gap-fill cells rejected as export/re-export tables: {n_leak:,} '
          f'({len(leak_blocks)} blocks)')
    print(f'  gap-fill added: {dict(added)}')
    print(f'  colonial sub-entries recovered: {n_sub:,}')
    print(f'  flow-repaired rows: {n_flowfix:,}')
    print(f'  group-repaired rows: {n_groupfix:,}')
    if gf_audit:
        af = BASE / 'reports' / 'groupfix_rejects.csv'
        with open(af, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(gf_audit[0].keys()))
            w.writeheader()
            w.writerows(gf_audit)
        dead = [a for a in gf_audit
                if a['seq_start'] != '0' and a['admitted'] == 0]
        print(f'  groupfix audit -> {af}  '
              f'({len(dead)} non-supersede repairs admitted NOTHING)')
        for a in dead[:10]:
            top = max(((k, v) for k, v in a.items()
                       if k.startswith('drop_') and v),
                      key=lambda kv: kv[1], default=('(no rows selected)', 0))
            print(f"      {a['volume']} {a['article_group'][:22]}|"
                  f"{a['article'][:22]} sel={a['selected']} -> {top[0]}")

    print(f'  manual (hand-keyed) rows: {n_manual:,}')
    print(f'  superseded consensus rows dropped: {n_sup:,}')
    print(f'  group-alias relabels: {n_alias:,}')


if __name__ == '__main__':
    main()
