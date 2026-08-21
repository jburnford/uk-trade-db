#!/usr/bin/env python3
"""Article-level check: General Statement blocks (sum of province rows over all countries) vs the
No. 2 Summary Statement article totals (Dominion).  Matches on the normalised leaf article name within
the same year and section.  Writes reports/canada_summary_check.md."""
import csv, re, sys, difflib
from collections import defaultdict, Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def nk(s):
    s = (s or '').lower()
    s = re.sub(r'\bn\.? ?e\.? ?s\b', 'nes', s); s = re.sub(r'\bn\.? ?o\.? ?p\b', 'nop', s)
    s = re.sub(r'&c', 'etc', s); s = re.sub(r'[^a-z0-9 ]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

imp = list(csv.DictReader(open(ROOT / 'db' / 'canada' / 'imports_general_rows.csv')))
summ = list(csv.DictReader(open(ROOT / 'db' / 'canada' / 'imports_summary_rows.csv')))
COLS = ('val_imp', 'val_efc', 'duty')
# general statement: per (fy, block) sums
G = {}
for r in imp:
    if r['regime'] != 'C' or r['row_kind'] != 'detail': continue
    k = (r['fiscal_year'], r['block_id'])
    if k not in G: G[k] = dict(article=r['article'], parent=r['article_parent'], section=r['section'], n=0, **{c: 0.0 for c in COLS})
    G[k]['n'] += 1
    for c in COLS:
        if r[c]: G[k][c] += float(r[c])
# summary: per (fy, article leaf, section) sums over rate lines
S = {}
for r in summ:
    if r['row_kind'] != 'article' or not r['article']: continue
    k = (r['fiscal_year'], nk(r['article']), r['section'])
    if k not in S: S[k] = dict(article=r['article'], parent=r['article_parent'], n=0, **{c: 0.0 for c in COLS})
    S[k]['n'] += 1
    for c in COLS:
        if r[c]: S[k][c] += float(r[c])
L = ['# General Statement blocks vs No. 2 Summary Statement (article totals, Dominion)', '',
     '| FY | summary articles | GS blocks | matched | val_imp exact | within 1% | GS>summary (×>1.01) | GS<summary | summary value matched | GS value of matched | ratio |',
     '|---|---|---|---|---|---|---|---|---|---|---|']
details = []; matched_rows = []
by_fy = defaultdict(list)
for k in S: by_fy[k[0]].append(k)
for fy in sorted(by_fy):
    gkeys = [k for k in G if k[0] == fy]
    gidx = defaultdict(list)
    for k in gkeys: gidx[(nk(G[k]['article']), G[k]['section'])].append(k)
    used = set(); m = ex = w1 = over = under = 0; sv = gv = 0.0
    for sk in by_fy[fy]:
        srow = S[sk]; cand = gidx.get((sk[1], sk[2])) or gidx.get((sk[1], None)) or []
        if not cand:
            # fuzzy on the same section
            names = [(nk(G[k]['article']), k) for k in gkeys if G[k]['section'] == sk[2] and k not in used]
            best = difflib.get_close_matches(sk[1], [n for n, _ in names], n=1, cutoff=0.92)
            if best: cand = [k for n, k in names if n == best[0]]
        cand = [k for k in cand if k not in used]
        if not cand: continue
        # choose the block whose val_imp is closest
        k = min(cand, key=lambda k: abs(G[k]['val_imp'] - srow['val_imp']))
        used.add(k); m += 1
        g = G[k]; sv += srow['val_imp']; gv += g['val_imp']
        if srow['val_imp'] > 0:
            q = g['val_imp'] / srow['val_imp']
            if abs(q - 1) < 1e-9: ex += 1
            elif abs(q - 1) < 0.01: w1 += 1
            elif q > 1.01: over += 1
            else: under += 1
            if abs(g['val_imp'] - srow['val_imp']) > 1000:
                details.append((fy, srow['article'], g['article'], g['val_imp'], srow['val_imp'], g['val_efc'], srow['val_efc'], g['duty'], srow['duty'], k[1]))
        matched_rows.append(dict(fiscal_year=fy, block_id=k[1], gs_article=g['article'], summary_article=srow['article'], section=sk[2] or '',
                                 gs_val_imp=round(g['val_imp'], 2), summary_val_imp=round(srow['val_imp'], 2), gs_val_efc=round(g['val_efc'], 2),
                                 summary_val_efc=round(srow['val_efc'], 2), gs_duty=round(g['duty'], 2), summary_duty=round(srow['duty'], 2)))
    L.append(f"| {fy} | {len(by_fy[fy])} | {len(gkeys)} | {m} | {ex} | {w1} | {over} | {under} | {sv:,.0f} | {gv:,.0f} | {gv/sv if sv else 0:.3f} |")
L += ['', '## Largest article discrepancies (|GS − summary| val_imp)', '',
      '| FY | summary article | GS article | GS val_imp | summary val_imp | GS efc | summary efc | GS duty | summary duty | block |', '|---|---|---|---|---|---|---|---|---|---|']
details.sort(key=lambda d: -abs(d[3] - d[4]))
for d in details[:60]:
    L.append(f"| {d[0]} | {d[1][:45]} | {d[2][:45]} | {d[3]:,.0f} | {d[4]:,.0f} | {d[5]:,.0f} | {d[6]:,.0f} | {d[7]:,.2f} | {d[8]:,.2f} | {d[9]} |")
(ROOT / 'reports' / 'canada_summary_check.md').write_text('\n'.join(L) + '\n')
with open(ROOT / 'db' / 'canada' / 'summary_match.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(matched_rows[0].keys())); w.writeheader(); w.writerows(matched_rows)
print('\n'.join(L[:14]))
