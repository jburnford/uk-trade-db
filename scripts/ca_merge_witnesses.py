#!/usr/bin/env python3
"""Phase 3b of CANADA_IMPORTS_PLAN.md: merge the StatCan witness into the main corpus,
per-cell, arbitrated by printed totals (user decision 2026-08-28: a VOTE, never
pick-the-better-scan).

Two passes:

PASS L -- label transfer.  A Canadiana '?' country-run whose rows match a witness country
block value-for-value (same provinces, same val_efc to $1, val_imp agreeing where both
carry one) takes the witness's country LABEL.  No values move, nothing is double-counted;
the 1884 peaches case is the type specimen (the '?' run 47,458/20,340/... = the witness's
United States block exactly).  The label must be unique among witness blocks matching the
run, and the article must not already hold that country on the Canadiana side.

PASS I -- coverage insertion: an article x country block the witness carries and the
Canadiana parse lacks entirely.  A block is inserted only when EVERY gate holds:

  G1  the article exists in the Canadiana parse for that year (matched on a normalised
      name, unique on both sides) -- we complete articles, we do not invent them;
  G2  the Canadiana article block has NO rows for that country (ckey);
  G3  the witness block closes in-table: sum(details) == its own country_total to $1
      in val_efc (and in val_imp when the total carries one);
  G4  the printed Abstract has room: for every (province, section) cell the block
      touches, the Canadiana residual (printed - parsed) must cover the inserted value
      -- short by at most 0.5% of the printed cell, never exceeded by more than $50 --
      and at least one touched cell must have a residual >= $100 (else nothing to fix).

PASS F -- value fill.  A Canadiana detail row with a country and province but BOTH value
cells blank (the 1883 GB machinery class: labels present, values never read) takes the
witness's values when exactly one witness row matches (fy, article, country, province),
the witness row's own block closes in-table, and the abstract cell has room for the
amount.  val_imp, val_efc and duty fill together; flag witness_value_fill.

Witness rows enter db/canada/imports_general_rows.csv verbatim (volume = the statcan tag
= the provenance), flagged witness_block_inserted.  db/canada/witness_patches.csv logs
every accepted and rejected candidate with the gate that stopped it.

Run AFTER ca_parse_imports, BEFORE the inference scripts.
"""
import csv, re, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ca_check_abstract import ckey

ROOT = Path(__file__).resolve().parents[1]
ROWS = ROOT / 'db' / 'canada' / 'imports_general_rows.csv'
W2 = ROOT / 'db' / 'canada' / 'imports_general_rows_w2.csv'
ABS = ROOT / 'db' / 'canada' / 'imports_abstract_rows.csv'
OUT = ROOT / 'db' / 'canada' / 'witness_patches.csv'


def anorm(a):
    a = re.sub(r'[^a-z0-9 ]', ' ', (a or '').lower())
    return re.sub(r'\s+', ' ', a).strip()


def blocks_of(rows):
    """(fy) -> list of blocks; a block = consecutive rows sharing (block_id, ckey(country) for
    detail/country_total rows).  Returns per-fy dicts: article -> {ckey -> block rows} and
    article occurrence counts."""
    out = defaultdict(lambda: defaultdict(dict))
    counts = defaultdict(lambda: defaultdict(int))
    for r in rows:
        if r['regime'] != 'C': continue
        a = anorm(r['article'])
        if not a or a == '?': continue
        counts[r['fiscal_year']][a] += 0    # touch
    cur_key = None; cur = None
    for r in rows:
        if r['regime'] != 'C' or r['row_kind'] not in ('detail', 'country_total'): continue
        a = anorm(r['article']); c = ckey(r['country'] or '')
        if not a or a == '?' or not c or c in ('total',): cur_key = None; continue
        k = (r['fiscal_year'], r['block_id'], a, c)
        if k != cur_key:
            cur_key = k; cur = []
            out[r['fiscal_year']][a].setdefault(c, []).append(cur)
        cur.append(r)
    return out


def f(x):
    try: return float(x)
    except (TypeError, ValueError): return None


def main():
    dry = '--dry-run' in sys.argv
    rows = list(csv.DictReader(open(ROWS)))
    w2 = list(csv.DictReader(open(W2)))
    fields = list(rows[0].keys())
    A = defaultdict(dict)
    for r in csv.DictReader(open(ABS)):
        if r['row_kind'] == 'province' and r['country'] != 'TOTAL':
            for col, sec in (('efc_dutiable', 'dut'), ('efc_free', 'free')):
                if r[col]: A[r['fiscal_year']][(ckey(r['country']), r['province'], sec)] = float(r[col])
    P = defaultdict(lambda: defaultdict(float))
    for r in rows:
        if r['row_kind'] != 'detail' or r['regime'] != 'C': continue
        sec = 'free' if r['section'] == 'FREE' else 'dut'
        P[r['fiscal_year']][(ckey(r['country'] or ''), r['province'], sec)] += f(r['val_efc']) or 0

    # ---------- PASS L: label transfer onto '?' runs ----------
    W = defaultdict(lambda: defaultdict(list))   # (fy, anorm) -> ckey -> [ [(prov, vi, ve)...] per block ]
    wname = {}                                   # (fy, ckey) -> witness's printed country name
    cur = None; key = None
    for r in w2:
        if r['regime'] != 'C' or r['row_kind'] != 'detail': continue
        a = anorm(r['article']); c = ckey(r['country'] or '')
        if not a or a == '?' or not c or c == '?': key = None; continue
        k = (r['fiscal_year'], r['block_id'], a, c)
        if k != key:
            key = k; cur = []
            W[(r['fiscal_year'], a)][c].append(cur)
            wname[(r['fiscal_year'], c)] = r['country']
        cur.append((r['province'], f(r['val_imp']), f(r['val_efc'])))
    def sig(rows_):
        return sorted((p or '', round(ve or 0)) for p, vi, ve in rows_)
    n_lab = 0; lab_val = 0.0
    i = 0; n = len(rows)
    while i < n:
        r = rows[i]
        if not (r['regime'] == 'C' and r['row_kind'] == 'detail' and (r['country'] or '?') == '?'
                and anorm(r['article']) not in ('', '?')):
            i += 1; continue
        j = i
        while j < n and rows[j]['fiscal_year'] == r['fiscal_year'] and rows[j]['block_id'] == r['block_id'] \
                and rows[j]['row_kind'] in ('detail', 'country_total') and (rows[j]['country'] or '?') == '?': j += 1
        run = [x for x in rows[i:j] if x['row_kind'] == 'detail' and x['province']]
        fy = r['fiscal_year']; a = anorm(r['article'])
        if run and sum(f(x['val_efc']) or 0 for x in run) >= 10:
            rsig = sorted((x['province'] or '', round(f(x['val_efc']) or 0)) for x in run)
            cands = []
            for c, blks in W.get((fy, a), {}).items():
                for blk in blks:
                    if sig(blk) == rsig: cands.append(c); break
            # unique label, and the article must not already hold that country in Canadiana
            if len(set(cands)) == 1:
                c = cands[0]
                have = any(x['regime'] == 'C' and x['fiscal_year'] == fy and anorm(x['article']) == a
                           and ckey(x['country'] or '') == c and x['row_kind'] == 'detail' for x in rows)
                # abstract gate: the transfer must not push any touched cell past printed (the 1880
                # silk-raw case: US Quebec free was exact before the transfer, +57K over after -> the
                # witness's own label is suspect there; leave '?')
                room = True
                for x in run:
                    sec = 'free' if x['section'] == 'FREE' else 'dut'
                    a_cell = A[fy].get((c, x['province'], sec))
                    if a_cell is None: room = False; break
                    if (f(x['val_efc']) or 0) - (a_cell - P[fy][(c, x['province'], sec)]) > max(50, 0.002 * a_cell):
                        room = False; break
                if not have and room:
                    label = wname[(fy, c)]
                    for x in rows[i:j]:
                        x['country'] = label; x['country_inferred'] = '3'
                        x['flags'] = (x['flags'] + ',' if x['flags'] else '') + 'witness_label_transfer'
                    for x in run:
                        sec = 'free' if x['section'] == 'FREE' else 'dut'
                        P[fy][(c, x['province'], sec)] += f(x['val_efc']) or 0
                    n_lab += 1; lab_val += sum(f(x['val_efc']) or 0 for x in run)
        i = j
    print(f"pass L: {n_lab} '?' runs labelled from the witness (efc {lab_val:,.0f})")
    # rebuild the parsed-cell sums with the new labels before pass I
    P.clear()
    for r in rows:
        if r['row_kind'] != 'detail' or r['regime'] != 'C': continue
        sec = 'free' if r['section'] == 'FREE' else 'dut'
        P[r['fiscal_year']][(ckey(r['country'] or ''), r['province'], sec)] += f(r['val_efc']) or 0

    # ---------- PASS R: row completion by the Canadiana block's OWN printed total ----------
    # A Canadiana block whose details under-sum its own printed country_total by EXACTLY the value
    # of the provinces the witness block carries and Canadiana lacks -- in val_efc AND val_imp where
    # the total prints one -- takes those witness rows (the strongest proof in the toolbox: the
    # 1884 US beef block is short 84,889 and the witness's five missing province rows sum to
    # 84,889/84,889 in both columns).
    WB = defaultdict(list)                     # (fy, anorm, ckey) -> closing witness blocks
    curb = None; keyb = None
    w2blocks = []
    for r in w2:
        if r['regime'] != 'C' or r['row_kind'] not in ('detail', 'country_total'): continue
        a = anorm(r['article']); c = ckey(r['country'] or '')
        if not a or a == '?' or not c or c == '?': keyb = None; continue
        k = (r['fiscal_year'], r['block_id'], a, c)
        if k != keyb:
            keyb = k; curb = {'fy': r['fiscal_year'], 'a': a, 'c': c, 'det': [], 'tot': None}
            w2blocks.append(curb)
        if r['row_kind'] == 'detail' and r['province']: curb['det'].append(r)
        else: curb['tot'] = r
    for b in w2blocks:
        if b['tot'] is None or not b['det']: continue
        tv = f(b['tot']['val_efc'])
        if tv and abs(sum(f(x['val_efc']) or 0 for x in b['det']) - tv) <= 1:
            WB[(b['fy'], b['a'], b['c'])].append(b)
    n_comp = 0; comp_val = 0.0
    i = 0; n = len(rows)
    while i < n:
        r = rows[i]
        if not (r['regime'] == 'C' and r['row_kind'] == 'detail' and r['province']
                and (r['country'] or '?') not in ('?', '') and anorm(r['article']) not in ('', '?')
                and not str(r['volume']).startswith('statcan_')):
            i += 1; continue
        fy = r['fiscal_year']; a = anorm(r['article']); c = ckey(r['country'] or '')
        j = i
        while j < n and rows[j]['fiscal_year'] == fy and rows[j]['block_id'] == r['block_id'] \
                and rows[j]['row_kind'] == 'detail' and ckey(rows[j]['country'] or '') == c: j += 1
        det = [x for x in rows[i:j] if x['province']]
        T = rows[j] if j < n and rows[j]['row_kind'] == 'country_total' and rows[j]['block_id'] == r['block_id'] \
            and ckey(rows[j]['country'] or '') == c else None
        i2 = j + (1 if T else 0)
        if T is not None and det:
            tv = f(T['val_efc']); tvi = f(T['val_imp'])
            sv = sum(f(x['val_efc']) or 0 for x in det); svi = sum(f(x['val_imp']) or 0 for x in det)
            gap = (tv - sv) if tv else 0
            m = WB.get((fy, a, c))
            if gap > 1 and m and len(m) == 1:
                have = {x['province'] for x in det}
                miss = [x for x in m[0]['det'] if x['province'] not in have]
                mv = sum(f(x['val_efc']) or 0 for x in miss)
                mvi = sum(f(x['val_imp']) or 0 for x in miss)
                gapi = (tvi - svi) if tvi is not None and tvi > 0 else None
                if miss and abs(mv - gap) <= 1 and (gapi is None or abs(mvi - gapi) <= 1):
                    newrows = []
                    for x in miss:
                        nr = {k2: x.get(k2, '') for k2 in fields}
                        nr['block_id'] = r['block_id']            # joins the host block
                        nr['flags'] = (nr['flags'] + ',' if nr['flags'] else '') + 'witness_row_completed'
                        newrows.append(nr)
                        sec = 'free' if x['section'] == 'FREE' else 'dut'
                        P[fy][(c, x['province'], sec)] += f(x['val_efc']) or 0
                    rows[j:j] = newrows
                    n = len(rows)
                    n_comp += 1; comp_val += mv
                    i = j + len(newrows) + 1; continue
        i = i2
    print(f'pass R: {n_comp} blocks completed against their own printed totals (efc {comp_val:,.0f})')

    # ---------- PASS B: block replacement for structurally broken blocks ----------
    # A Canadiana block is BROKEN when its rows were shattered by the OCR: two or more
    # country_total rows in one country block (the label column died and every row closed as a
    # total -- 1884 US beef, 1885 US pianofortes), or a single total its details miss by >1%.
    # When the witness carries a UNIQUE closing block for the same (fy, article, country), the
    # witness rows replace the Canadiana ones (old rows -> row_kind 'superseded_w2', kept for
    # audit), gated per touched cell: the replacement must not push any (province, section)
    # cell past the printed abstract by more than max($50, 0.2%).  1887 Switzerland watches
    # (5,393 -> 92,786 = the t505 missing rows) is the type specimen.
    n_rep = 0; rep_val = 0.0
    i = 0; n = len(rows)
    while i < n:
        r = rows[i]
        if not (r['regime'] == 'C' and r['row_kind'] in ('detail', 'country_total')
                and (r['country'] or '?') not in ('?', '') and ckey(r['country'] or '') not in ('total',)
                and anorm(r['article']) not in ('', '?')
                and not str(r['volume']).startswith('statcan_')):
            i += 1; continue
        fy = r['fiscal_year']; a = anorm(r['article']); c = ckey(r['country'] or '')
        j = i
        while j < n and rows[j]['fiscal_year'] == fy and rows[j]['block_id'] == r['block_id'] \
                and rows[j]['row_kind'] in ('detail', 'country_total') and ckey(rows[j]['country'] or '') == c: j += 1
        seg = rows[i:j]
        det = [x for x in seg if x['row_kind'] == 'detail' and x['province']]
        tots = [x for x in seg if x['row_kind'] == 'country_total']
        broken = len(tots) >= 2
        if not broken and len(tots) == 1 and det:
            tv = f(tots[0]['val_efc']); sv = sum(f(x['val_efc']) or 0 for x in det)
            broken = bool(tv) and abs(sv - tv) > max(1, 0.01 * tv)
        m = WB.get((fy, a, c))
        if not (broken and m and len(m) == 1):
            i = j; continue
        wb = m[0]
        # per-cell delta gate
        delta = defaultdict(float)
        for x in det:
            sec = 'free' if x['section'] == 'FREE' else 'dut'
            delta[(c, x['province'], sec)] -= f(x['val_efc']) or 0
        for x in wb['det']:
            sec = 'free' if x['section'] == 'FREE' else 'dut'
            delta[(c, x['province'], sec)] += f(x['val_efc']) or 0
        ok = True
        for cell, d in delta.items():
            a_cell = A[fy].get(cell)
            if a_cell is None: ok = False; break
            if P[fy][cell] + d - a_cell > max(50, 0.002 * a_cell): ok = False; break
        if not ok:
            i = j; continue
        for x in seg:
            x['row_kind'] = 'superseded_w2'
            x['flags'] = (x['flags'] + ',' if x['flags'] else '') + 'superseded_by_witness'
        newrows = []
        for x in wb['det'] + ([wb['tot']] if wb.get('tot') else []):
            if x is None: continue
            nr = {k2: x.get(k2, '') for k2 in fields}
            nr['block_id'] = r['block_id']
            nr['flags'] = (nr['flags'] + ',' if nr['flags'] else '') + 'witness_block_replaced'
            newrows.append(nr)
        rows[j:j] = newrows
        n = len(rows)
        for cell, d in delta.items(): P[fy][cell] += d
        n_rep += 1; rep_val += sum(f(x['val_efc']) or 0 for x in wb['det'])
        i = j + len(newrows)
    print(f'pass B: {n_rep} broken blocks replaced by the witness (efc {rep_val:,.0f})')

    # ---------- PASS I: coverage insertion ----------
    B1 = blocks_of(rows); B2 = blocks_of(w2)
    # article names known to Canadiana in ANY regime-C year: an article absent from one year but
    # printed in a neighbour (1881 'The following articles being the Natural Products...' exists in
    # 1882) may be inserted whole -- the closure and abstract gates still apply, plus a value floor
    ALLARTS = set()
    for r in rows:
        if r['regime'] == 'C': ALLARTS.add(anorm(r['article']))
    last_row_of_fy = {}
    # '?' detail mass per (fy, anorm): any sizable unlabelled mass blocks insertion outright
    Q1 = defaultdict(float)
    for r in rows:
        if r['regime'] == 'C' and r['row_kind'] == 'detail' and (r['country'] or '?') == '?':
            Q1[(r['fiscal_year'], anorm(r['article']))] += f(r['val_efc']) or 0
    # article-level detail mass per (fy, anorm) on each side, '?' rows INCLUDED -- a block Canadiana
    # holds unlabelled must not be inserted again from the witness (the jute-yarn double-count)
    M1 = defaultdict(float); M2 = defaultdict(float)
    for r in rows:
        if r['regime'] == 'C' and r['row_kind'] == 'detail':
            M1[(r['fiscal_year'], anorm(r['article']))] += f(r['val_efc']) or 0
    for r in w2:
        if r['regime'] == 'C' and r['row_kind'] == 'detail':
            M2[(r['fiscal_year'], anorm(r['article']))] += f(r['val_efc']) or 0
    # (fy, ckey) -> list of (anorm, country block efc sum) on the Canadiana side, for variant-name dupes
    V1 = defaultdict(list)
    acc = defaultdict(float)
    for r in rows:
        if r['regime'] == 'C' and r['row_kind'] == 'detail':
            acc[(r['fiscal_year'], anorm(r['article']), ckey(r['country'] or ''))] += f(r['val_efc']) or 0
    for (fy_, a_, c_), v_ in acc.items(): V1[(fy_, c_)].append((a_, v_))
    import difflib
    log = []; inserts = []   # (anchor row index hint, list of witness rows)
    # index of main rows by (fy, article) for insertion anchoring
    last_row_of_article = {}
    for i, r in enumerate(rows):
        if r['regime'] == 'C':
            last_row_of_article[(r['fiscal_year'], anorm(r['article']))] = i
            last_row_of_fy[r['fiscal_year']] = i

    for fy in sorted(B2):
        if fy not in B1: continue
        for a, by_c in B2[fy].items():
            crossyear = a not in B1[fy]
            if crossyear and a not in ALLARTS:
                continue                                   # G1: article unknown to the whole Canadiana corpus
            for c, blks in by_c.items():
                if not crossyear and c in B1[fy][a]:
                    continue                               # G2: country present already
                if len(blks) != 1:
                    log.append((fy, a, c, 0, 'ambiguous: multiple witness blocks')); continue
                blk = blks[0]
                det = [r for r in blk if r['row_kind'] == 'detail' and r['province']]
                tot = [r for r in blk if r['row_kind'] == 'country_total']
                if not det: continue
                sv = sum(f(r['val_efc']) or 0 for r in det)
                svi = sum(f(r['val_imp']) or 0 for r in det)
                if tot:
                    tv, tvi = f(tot[0]['val_efc']), f(tot[0]['val_imp'])
                    if tv is None or abs(sv - tv) > 1 or (tvi is not None and abs(svi - tvi) > 1):
                        log.append((fy, a, c, sv, 'G3 fail: block does not close')); continue
                elif len(det) > 1:
                    log.append((fy, a, c, sv, 'G3 fail: no country_total to close against')); continue
                ok = True; strong = False
                for r in det:
                    sec = 'free' if r['section'] == 'FREE' else 'dut'
                    key = (c, r['province'], sec)
                    a_cell = A[fy].get(key)
                    if a_cell is None: ok = False; why = f'no abstract cell {key}'; break
                    resid = a_cell - P[fy][key]
                    v = f(r['val_efc']) or 0
                    if v - resid > max(50, 0):             # G4: would exceed printed
                        ok = False; why = f'G4 fail: {key} resid {resid:.0f} < row {v:.0f}'; break
                    if resid >= 100: strong = True
                if not ok:
                    log.append((fy, a, c, sv, why)); continue
                if not strong:
                    log.append((fy, a, c, sv, 'G4: no touched cell has resid >= 100')); continue
                if Q1[(fy, a)] >= 0.25 * sv:
                    log.append((fy, a, c, sv, f"G2c fail: article holds '?' mass {Q1[(fy, a)]:.0f} (label transfer territory)")); continue
                # G2b: the Canadiana article must actually be MISSING this much mass ('?' rows count)
                gap = M2[(fy, a)] - M1[(fy, a)]
                if gap < sv - max(50, 0.005 * sv):
                    log.append((fy, a, c, sv, f'G2b fail: article gap {gap:.0f} < block {sv:.0f} (mass present, maybe unlabelled)')); continue
                # G5: the same country block under a VARIANT article name on the Canadiana side
                dupe = None
                for a1, v1 in V1[(fy, c)]:
                    if a1 == a or abs(v1 - sv) > max(2, 0.01 * sv): continue
                    if difflib.SequenceMatcher(None, a1, a).ratio() >= 0.7: dupe = a1; break
                if dupe:
                    log.append((fy, a, c, sv, f'G5 fail: present under variant name {dupe[:40]!r}')); continue
                if crossyear and sv < 1000:
                    log.append((fy, a, c, sv, 'G1 cross-year: below the $1,000 floor')); continue
                if crossyear and any(a2 != a and a2.endswith(a) for a2 in ALLARTS):
                    log.append((fy, a, c, sv, 'G1 cross-year: name is a fragment (suffix of another article)')); continue
                # accept
                anchor = last_row_of_article.get((fy, a), last_row_of_fy.get(fy))
                if anchor is None: continue
                newrows = []
                for r in blk:
                    nr = {k: r.get(k, '') for k in fields}
                    nr['block_id'] = 'w' + str(nr['block_id'])          # never collide with a host block key
                    nr['flags'] = (nr['flags'] + ',' if nr['flags'] else '') + 'witness_block_inserted'
                    newrows.append(nr)
                inserts.append((anchor, newrows))
                for r in det:
                    sec = 'free' if r['section'] == 'FREE' else 'dut'
                    P[fy][(c, r['province'], sec)] += f(r['val_efc']) or 0
                log.append((fy, a, c, sv, 'INSERTED'))

    # ---------- PASS F: value fill for blank-value labelled rows ----------
    # witness rows keyed (fy, anorm, ckey, province), only from blocks that close in-table
    WF = defaultdict(list)
    blk_rows = defaultdict(list)
    for r in w2:
        if r['regime'] == 'C' and r['row_kind'] in ('detail', 'country_total'):
            blk_rows[(r['fiscal_year'], r['block_id'], anorm(r['article']), ckey(r['country'] or ''))].append(r)
    for bk, rr in blk_rows.items():
        det = [x for x in rr if x['row_kind'] == 'detail' and x['province']]
        tot = [x for x in rr if x['row_kind'] == 'country_total']
        if not det: continue
        if tot:
            tv = f(tot[0]['val_efc'])
            if tv is None or abs(sum(f(x['val_efc']) or 0 for x in det) - tv) > 1: continue
        elif len(det) > 1:
            continue
        for x in det:
            WF[(bk[0], bk[2], bk[3], x['province'])].append(x)
    n_fill = 0; fill_val = 0.0
    for r in rows:
        if not (r['regime'] == 'C' and r['row_kind'] == 'detail' and r['province']
                and not r['val_efc'] and not r['val_imp']
                and (r['country'] or '?') not in ('?', '') and not str(r['volume']).startswith('statcan_')):
            continue
        k = (r['fiscal_year'], anorm(r['article']), ckey(r['country'] or ''), r['province'])
        m = WF.get(k)
        if not m or len(m) != 1: continue
        wrow = m[0]
        ve = f(wrow['val_efc'])
        if not ve: continue
        sec = 'free' if r['section'] == 'FREE' else 'dut'
        cell = (k[2], r['province'], sec)
        a_cell = A[r['fiscal_year']].get(cell)
        if a_cell is None: continue
        if ve - (a_cell - P[r['fiscal_year']][cell]) > max(50, 0.002 * a_cell): continue
        r['val_imp'] = wrow['val_imp']; r['val_efc'] = wrow['val_efc']
        if not r['duty'] and wrow['duty']: r['duty'] = wrow['duty']
        for q in ('qty_imp', 'qty_efc', 'unit'):
            if not r[q] and wrow.get(q): r[q] = wrow[q]
        r['flags'] = (r['flags'] + ',' if r['flags'] else '') + 'witness_value_fill'
        P[r['fiscal_year']][cell] += ve
        n_fill += 1; fill_val += ve
    print(f'pass F: {n_fill} blank-value rows filled from the witness (efc {fill_val:,.0f})')

    with open(OUT, 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['fiscal_year', 'article', 'country', 'val_efc', 'outcome'])
        for e in sorted(log): w.writerow(e)
    ins_val = sum(e[3] for e in log if e[4] == 'INSERTED')
    n_ins = sum(1 for e in log if e[4] == 'INSERTED')
    print(f'candidates {len(log)}; inserted {n_ins} blocks (efc {ins_val:,.0f}); log -> {OUT}')
    if dry: return
    for anchor, newrows in sorted(inserts, key=lambda x: -x[0]):
        rows[anchor + 1:anchor + 1] = newrows
    with open(ROWS, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(rows)
    print(f'applied to {ROWS}')


if __name__ == '__main__':
    main()
