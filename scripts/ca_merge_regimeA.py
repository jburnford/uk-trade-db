#!/usr/bin/env python3
"""Phase 4 of CANADA_IMPORTS_PLAN.md -- EXPERIMENTAL, DO NOT RUN AGAINST THE LIVE CSV YET.

First attempt 2026-09-01: the block vote below LOSES mass (1868 efc ratio 0.716 -> 0.613)
because (a) a Canadiana block with complete details but no parsed article_total counts as
'not closing' and gets superseded by a smaller closing witness block, and (b) index-aligned
pairing inside 'replace' opcodes mis-pairs articles when one side dropped blocks mid-run.
The run was REVERTED.  What the survey established, for the real phase-4 session:

  * the witness's province statements are wholesale better for 1868-73
    (efc ratios 0.797/0.911/1.080/0.949/0.913/0.933 vs Canadiana 0.72/0.69/0.60/0.48/0.55/0.53);
  * 1874-75 carry a DOMINION RECAPITULATION -- a national article x country statement --
    and Canadiana's 1874 Dominion reads 127,607,261 vs printed 127,404,169 (1.0016!):
    the national series for those years should come from it, not the province statements;
  * a correct vote needs (i) 'not closing' split into no-total vs total-mismatch,
    (ii) pairing by row-value fingerprints not sequence position, (iii) per-statement
    printed grand totals as the arbiter (the print carries one per province statement).

Original design notes follow.

Phase 4 of CANADA_IMPORTS_PLAN.md: rebuild regime A (FY1868-1875) from the StatCan
greyscale witness.  The Canadiana bitonal microfilm garbled the right-hand facing pages;
the witness closes roughly TWICE as many article blocks in every regime-A year
(1871: 433 vs 157).

The vote, per (fy, province-statement, section), in print order:

  * block sequences from both witnesses are aligned by article-name sequence matching
    (difflib over normalised names -- same setting of type, so the order is shared);
  * a matched pair votes by ARTICLE-TOTAL CLOSURE (sum of country details vs the block's
    own printed article_total, val_imp and val_efc where present):
      witness closes, Canadiana does not  -> the witness block replaces the Canadiana one
      (old rows kept as row_kind 'superseded_w2');  anything else -> Canadiana stays;
  * a witness-only block (Canadiana never read the article -- the garbled-page class)
    is inserted iff it closes, with a name-similarity guard against mid-run mispairing.

National anchor read AFTER the merge: reference/canada_printed_totals.csv ratios, and the
printed by-country EfC series (reference/canada_country_series_voted.csv) for 1873-75.

Run AFTER ca_parse_imports (and ca_parse_witness regimeAB), BEFORE the export step.
"""
import csv, difflib, re, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

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
    """(fy, province, section) -> ordered blocks; block = dict(a, name, rows, det, tot, i0)."""
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
            cur = {'a': anorm(r['article']), 'name': r['article'], 'rows': [], 'det': [], 'tot': None, 'i0': idx}
            groups[g].append(cur)
        cur['rows'].append(r); 
        if r['row_kind'] == 'detail': cur['det'].append(r)
        else: cur['tot'] = r
    return rows, groups


def closes(b):
    if b['tot'] is None or not b['det']: return False
    ok = 0; cols = 0
    for col in ('val_imp', 'val_efc'):
        tv = f(b['tot'][col])
        if not tv: continue
        cols += 1
        if abs(sum(f(x[col]) or 0 for x in b['det']) - tv) <= 1: ok += 1
    return cols > 0 and ok == cols


def main():
    dry = '--dry-run' in sys.argv
    rows, G1 = load_blocks(ROWS, wit=False)
    _w2rows, G2 = load_blocks(W2, wit=True)
    fields = list(rows[0].keys())
    printed = {r['fiscal_year']: r for r in csv.DictReader(open(ROOT / 'reference' / 'canada_printed_totals.csv'))}
    def ratios(rws):
        agg = defaultdict(float)
        for r in rws:
            if r['fiscal_year'] in YEARS and r['row_kind'] == 'detail' and r['regime'] == 'A' \
                    and r['province'] != 'Dominion':
                agg[r['fiscal_year']] += f(r['val_efc']) or 0
        return {fy: agg[fy] / float(printed[fy]['entered_for_consumption']) for fy in sorted(agg)}
    before = ratios(rows)                       # BEFORE the vote loop -- it mutates rows in place
    n_rep = n_ins = 0; rep_val = ins_val = 0.0
    inserts = []                      # (host row index, new rows)
    for g in sorted(set(G1) | set(G2)):
        b1 = G1.get(g, []); b2 = G2.get(g, [])
        if not b2: continue
        if not b1:
            continue                  # whole statement missing on the Canadiana side: too coarse to anchor -- skip
        sm = difflib.SequenceMatcher(None, [b['a'] for b in b1], [b['a'] for b in b2], autojunk=False)
        for tag, i1, j1, i2, j2 in sm.get_opcodes():
            if tag == 'equal':
                pairs = list(zip(range(i1, j1), range(i2, j2)))
            elif tag == 'replace':
                pairs = list(zip(range(i1, j1), range(i2, j2)))     # index-aligned within the run
            elif tag == 'insert':
                # witness-only blocks: insert if they close; anchor after the previous Canadiana block
                host = b1[i1 - 1] if i1 > 0 else b1[0]
                at = host['rows'][-1]
                for w in b2[i2:j2]:
                    if not closes(w): continue
                    sim_guard = True
                    newrows = []
                    for x in w['rows']:
                        nr = {k: x.get(k, '') for k in fields}
                        nr['block_id'] = 'w' + str(nr['block_id'])
                        nr['flags'] = (nr['flags'] + ',' if nr['flags'] else '') + 'witnessA_block_inserted'
                        newrows.append(nr)
                    inserts.append((rows.index(at), newrows))
                    n_ins += 1; ins_val += sum(f(x['val_efc']) or 0 for x in w['det'])
                continue
            else:
                continue
            for k1, k2 in pairs:
                c, w = b1[k1], b2[k2]
                if tag == 'replace' and difflib.SequenceMatcher(None, c['a'], w['a']).ratio() < 0.5:
                    continue
                if closes(w) and not closes(c):
                    for x in c['rows']:
                        x['row_kind'] = 'superseded_w2'
                        x['flags'] = (x['flags'] + ',' if x['flags'] else '') + 'superseded_by_witnessA'
                    newrows = []
                    for x in w['rows']:
                        nr = {k: x.get(k, '') for k in fields}
                        nr['block_id'] = 'w' + str(nr['block_id'])
                        nr['flags'] = (nr['flags'] + ',' if nr['flags'] else '') + 'witnessA_block_replaced'
                        newrows.append(nr)
                    inserts.append((rows.index(c['rows'][-1]), newrows))
                    n_rep += 1; rep_val += sum(f(x['val_efc']) or 0 for x in w['det'])
    print(f'regime A vote: {n_rep} blocks replaced (efc {rep_val:,.0f}), {n_ins} witness-only blocks inserted (efc {ins_val:,.0f})')
    if not dry:
        for at, newrows in sorted(inserts, key=lambda x: -x[0]):
            rows[at + 1:at + 1] = newrows
        after = ratios(rows)
        for fy in sorted(before): print(f'  {fy}: efc ratio {before[fy]:.3f} -> {after[fy]:.3f}')
        with open(ROWS, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(rows)
        print(f'applied to {ROWS}')
    else:
        for fy in sorted(before): print(f'  {fy}: efc ratio before {before[fy]:.3f}')


if __name__ == '__main__':
    main()
