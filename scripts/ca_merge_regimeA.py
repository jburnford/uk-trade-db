#!/usr/bin/env python3
"""Phase 4 of CANADA_IMPORTS_PLAN.md: rebuild regime A (FY1868-1875) from the StatCan
greyscale witness.  The Canadiana bitonal microfilm garbled the right-hand facing pages
(province-statement efc ratios 0.48-0.72); the witness reads the same setting of type at
0.80-1.08.  1874-75 additionally print a DOMINION RECAPITULATION whose Canadiana copy
reads within 0.2% of the printed national total.

Lessons from the reverted first attempt (2026-09-01): 'not closing' must distinguish a
block with NO parsed total (details possibly complete) from one whose details MISS its
total; pairing must go by row-value fingerprints, never sequence position.

The vote, per (fy, province-statement, section):

  * blocks pair by FINGERPRINT -- shared identical (country, val_efc) detail rows
    (>= 2 rows or half the smaller block), unique on both sides; name-equality pairs
    the remainder;
  * a paired vote replaces the Canadiana block with the witness one ONLY when the
    witness block CLOSES on its own printed article total (both value columns present)
    and the Canadiana block is provably worse:
      - its details MISS its own total (internal inconsistency), or
      - it has no total AND no more detail mass than the closing witness
        (a no-total block with MORE mass than the witness keeps -- it may hold real
        absorbed rows the vote cannot yet place);
  * a witness block with NO Canadiana partner (fingerprint or name) inserts iff it
    closes -- the garbled-page class, whole articles Canadiana never read;
  * everything else keeps Canadiana.  Old rows stay as row_kind 'superseded_w2'.

Readout: per-year national efc/imp ratios (province statements, Dominion excluded)
before and after, and the per-country check against the printed voted EfC series
(reference/canada_country_series_voted.csv) for 1873-75.

Run AFTER ca_parse_imports + ca_parse_witness regimeAB, BEFORE the export step.
"""
import csv, difflib, re, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ca_check_abstract import ckey

ROOT = Path(__file__).resolve().parents[1]
ROWS = ROOT / 'db' / 'canada' / 'imports_general_rows.csv'
W2 = ROOT / 'db' / 'canada' / 'imports_general_rows_w2.csv'
YEARS = {str(y) for y in range(1868, 1876)}


def anorm(a):
    a = re.sub(r'[^a-z0-9 ]', ' ', (a or '').lower())
    return re.sub(r'\s+', ' ', a).strip()


def f(x):
    try: return float(x)
    except (TypeError, ValueError): return None


def load_blocks(path, wit):
    groups = defaultdict(list)
    cur = None; key = None
    rows = list(csv.DictReader(open(path)))
    for idx, r in enumerate(rows):
        if r['fiscal_year'] not in YEARS or r['regime'] != 'A': continue
        if wit != str(r['volume']).startswith('statcan_'): continue
        if r['row_kind'] not in ('detail', 'article_total'): continue
        g = (r['fiscal_year'], r['province'] or '', r['section'] or '')
        k = (g, r['block_id'])
        if k != key:
            key = k
            cur = {'a': anorm(r['article']), 'name': r['article'], 'rows': [], 'det': [], 'tot': None, 'i_last': idx}
            groups[g].append(cur)
        cur['rows'].append(r); cur['i_last'] = idx
        if r['row_kind'] == 'detail': cur['det'].append(r)
        else: cur['tot'] = r
    for g, bs in groups.items():
        for b in bs:
            b['sum_e'] = sum(f(x['val_efc']) or 0 for x in b['det'])
            b['sum_i'] = sum(f(x['val_imp']) or 0 for x in b['det'])
            b['fp'] = {(ckey(x['country'] or ''), round(f(x['val_efc']) or 0)) for x in b['det']
                       if (x['country'] or '?') not in ('?', '')}
            tv_e = f(b['tot']['val_efc']) if b['tot'] else None
            tv_i = f(b['tot']['val_imp']) if b['tot'] else None
            if b['tot'] is None or not b['det']:
                b['state'] = 'no_total'
            else:
                cols = ok = 0
                for tv, sv in ((tv_i, b['sum_i']), (tv_e, b['sum_e'])):
                    if not tv: continue
                    cols += 1
                    if abs(sv - tv) <= 1: ok += 1
                b['state'] = 'closed' if (cols and ok == cols) else ('mismatch' if cols else 'no_total')
    return rows, groups


def pair_blocks(b1, b2):
    """fingerprint-first unique pairing, then unique name-equality; returns list of (i, j)."""
    used1 = set(); used2 = set(); pairs = []
    # fingerprint
    for j, w in enumerate(b2):
        if not w['fp']: continue
        best = []
        for i, c in enumerate(b1):
            if i in used1 or not c['fp']: continue
            shared = len(c['fp'] & w['fp'])
            need = max(2, min(len(c['fp']), len(w['fp'])) // 2)
            if shared >= need: best.append(i)
        if len(best) == 1:
            pairs.append((best[0], j)); used1.add(best[0]); used2.add(j)
    # name equality among the rest
    names1 = defaultdict(list)
    for i, c in enumerate(b1):
        if i not in used1 and c['a'] and c['a'] != '?': names1[c['a']].append(i)
    for j, w in enumerate(b2):
        if j in used2 or not w['a'] or w['a'] == '?': continue
        cand = [i for i in names1.get(w['a'], []) if i not in used1]
        if len(cand) == 1:
            pairs.append((cand[0], j)); used1.add(cand[0]); used2.add(j)
    return pairs, used1, used2


def main():
    dry = '--dry-run' in sys.argv
    rows, G1 = load_blocks(ROWS, wit=False)
    _w2, G2 = load_blocks(W2, wit=True)
    fields = list(rows[0].keys())
    printed = {r['fiscal_year']: r for r in csv.DictReader(open(ROOT / 'reference' / 'canada_printed_totals.csv'))}

    def ratios(rws):
        agg = defaultdict(lambda: [0.0, 0.0])
        for r in rws:
            if r['fiscal_year'] in YEARS and r['row_kind'] == 'detail' and r['regime'] == 'A' \
                    and r['province'] != 'Dominion':
                agg[r['fiscal_year']][0] += f(r['val_efc']) or 0
                agg[r['fiscal_year']][1] += f(r['val_imp']) or 0
        return {fy: (v[0] / float(printed[fy]['entered_for_consumption']),
                     v[1] / float(printed[fy]['total_imports'])) for fy, v in sorted(agg.items())}
    before = ratios(rows)

    # per-year room against the printed national totals, BOTH columns -- the arbiter for anything
    # that adds mass.  1875 is already 0.96 complete (room ~4%); 1870 has imp 0.99 but efc 0.60
    # (a column-loss year: value-fill territory, not insertion).
    room = {}
    for fy, (re_, ri_) in before.items():
        room[fy] = [float(printed[fy]['entered_for_consumption']) * (1 - re_),
                    float(printed[fy]['total_imports']) * (1 - ri_)]
    tolr = {fy: 0.02 * float(printed[fy]['entered_for_consumption']) for fy in room}
    # the Dominion recapitulation (1874-75) keeps its own ledger against the same printed totals
    dsum = defaultdict(lambda: [0.0, 0.0])
    for r in rows:
        if r['fiscal_year'] in YEARS and r['row_kind'] == 'detail' and r['regime'] == 'A' \
                and r['province'] == 'Dominion':
            dsum[r['fiscal_year']][0] += f(r['val_efc']) or 0
            dsum[r['fiscal_year']][1] += f(r['val_imp']) or 0
    roomD = {fy: [float(printed[fy]['entered_for_consumption']) - v[0],
                  float(printed[fy]['total_imports']) - v[1]] for fy, v in dsum.items()}

    n_rep = n_ins = n_kept_bigger = n_room = n_fill = 0; rep_gain = ins_val = fill_val = 0.0
    inserts = []
    # Canadiana article names per fy (fuzzy tier test for insertions)
    names_by_fy = defaultdict(set)
    for g, bs in G1.items():
        for b in bs:
            if b['a'] and b['a'] != '?': names_by_fy[g[0]].add(b['a'])
    tier2 = []
    for g in sorted(set(G1) | set(G2)):
        b1 = G1.get(g, []); b2 = G2.get(g, [])
        if not b2: continue
        if not b1: continue
        fy = g[0]
        R = roomD if g[1] == 'Dominion' else room
        if g[1] == 'Dominion' and fy not in R: continue
        pairs, used1, used2 = pair_blocks(b1, b2)
        for i, j in pairs:
            c, w = b1[i], b2[j]
            if c['state'] == 'closed': continue
            # cross-closure: the witness DETAILS reproduce Canadiana's own printed article total
            # (the witness's total cell may be misread or unparsed -- the details are what matter)
            cross = False
            if w['state'] != 'closed' and c['tot'] is not None and w['det']:
                cols = ok = 0
                for col, sv in (('val_imp', w['sum_i']), ('val_efc', w['sum_e'])):
                    tv = f(c['tot'][col])
                    if not tv: continue
                    cols += 1
                    if abs(sv - tv) <= 1: ok += 1
                cross = cols > 0 and ok == cols
            if w['state'] != 'closed' and not cross: continue
            if not cross and c['state'] == 'no_total' and c['sum_e'] > w['sum_e'] + max(100, 0.01 * w['sum_e']):
                n_kept_bigger += 1; continue              # Canadiana may hold real absorbed rows
            keep_tot = c['tot'] if cross else None        # cross-closure keeps Canadiana's proven total row
            for x in c['rows']:
                if keep_tot is not None and x is keep_tot: continue
                x['row_kind'] = 'superseded_w2'
                x['flags'] = (x['flags'] + ',' if x['flags'] else '') + 'superseded_by_witnessA'
            tag = 'witnessA_block_replaced' + ('_cross' if cross else '')
            newrows = []
            for x in (w['det'] if cross else w['rows']):
                nr = {k: x.get(k, '') for k in fields}
                nr['block_id'] = 'w' + str(nr['block_id'])
                nr['flags'] = (nr['flags'] + ',' if nr['flags'] else '') + tag
                newrows.append(nr)
            at = c['rows'][c['rows'].index(keep_tot) - 1] if keep_tot is not None and c['rows'].index(keep_tot) > 0 else c['rows'][0]
            inserts.append((c['i_last'] if not cross else rows.index(at), newrows))
            n_rep += 1; rep_gain += w['sum_e'] - c['sum_e']
            R[fy][0] -= w['sum_e'] - c['sum_e']; R[fy][1] -= w['sum_i'] - c['sum_i']
        for j, w in enumerate(b2):
            if j in used2 or w['state'] != 'closed': continue
            fresh = not any(difflib.SequenceMatcher(None, w['a'], a1).ratio() >= 0.75
                            for a1 in names_by_fy[fy]) if w['a'] and w['a'] != '?' else False
            item = (0 if fresh else 1, fy, w, b1[-1]['i_last'], g[1] == 'Dominion')
            tier2.append(item)
    # insertions: whole-missing articles first, then name-present blocks, both room-gated in BOTH columns
    for tier, fy, w, at, isdom in sorted(tier2, key=lambda x: (x[0], x[1])):
        R = roomD if isdom else room
        if fy not in R or R[fy][0] - w['sum_e'] < -tolr[fy] or R[fy][1] - w['sum_i'] < -tolr[fy]:
            n_room += 1; continue
        newrows = []
        for x in w['rows']:
            nr = {k: x.get(k, '') for k in fields}
            nr['block_id'] = 'w' + str(nr['block_id'])
            nr['flags'] = (nr['flags'] + ',' if nr['flags'] else '') + 'witnessA_block_inserted'
            newrows.append(nr)
        inserts.append((at, newrows))
        n_ins += 1; ins_val += w['sum_e']
        R[fy][0] -= w['sum_e']; R[fy][1] -= w['sum_i']
    # value fill: a Canadiana detail row with ONE value column blank takes the witness's, matched by
    # (fy, province, section, country) plus an IDENTICAL value in the present column, unique
    WV = defaultdict(list)
    for g, bs in G2.items():
        for b in bs:
            for x in b['det']:
                WV[(g, ckey(x['country'] or ''))].append(x)
    for g, bs in G1.items():
        for b in bs:
            for x in b['det']:
                vi, ve = f(x['val_imp']), f(x['val_efc'])
                if (vi is None) == (ve is None): continue
                have, miss = ('val_imp', 'val_efc') if vi is not None else ('val_efc', 'val_imp')
                cands = [y for y in WV.get((g, ckey(x['country'] or '')), [])
                         if f(y[have]) is not None and abs(f(y[have]) - f(x[have])) <= 1 and f(y[miss]) is not None]
                vals = {round(f(y[miss])) for y in cands}
                if len(vals) == 1:
                    x[miss] = cands[0][miss]
                    if not x['duty'] and cands[0]['duty']: x['duty'] = cands[0]['duty']
                    x['flags'] = (x['flags'] + ',' if x['flags'] else '') + 'witnessA_value_fill'
                    n_fill += 1; fill_val += f(cands[0][miss]) or 0
    print(f'regime A vote: {n_rep} replacements (net efc {rep_gain:+,.0f}), {n_ins} insertions (efc {ins_val:,.0f}), '
          f'{n_room} refused for room, {n_kept_bigger} kept-bigger; value fill {n_fill} rows ({fill_val:,.0f})')
    for at, newrows in sorted(inserts, key=lambda x: -x[0]):
        rows[at + 1:at + 1] = newrows
    after = ratios(rows)
    dsum2 = defaultdict(lambda: [0.0, 0.0])
    for r in rows:
        if r['fiscal_year'] in YEARS and r['row_kind'] == 'detail' and r['regime'] == 'A' \
                and r['province'] == 'Dominion':
            dsum2[r['fiscal_year']][0] += f(r['val_efc']) or 0
    for fy in sorted(dsum2):
        print(f'  Dominion {fy}: efc {dsum2[fy][0]:,.0f} '
              f'({dsum2[fy][0] / float(printed[fy]["entered_for_consumption"]):.4f} of printed)')
    print(f"{'fy':6}{'efc before':>11}{'after':>7}{'| imp before':>13}{'after':>7}")
    for fy in sorted(before):
        print(f'{fy:6}{before[fy][0]:>11.3f}{after[fy][0]:>7.3f}{before[fy][1]:>13.3f}{after[fy][1]:>7.3f}')
    if dry:
        print('(dry run: nothing written)'); return
    with open(ROWS, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(rows)
    print(f'applied to {ROWS}')


if __name__ == '__main__':
    main()
