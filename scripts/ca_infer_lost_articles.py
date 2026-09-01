#!/usr/bin/env python3
"""Name the article-'?' blocks from the other volumes' article order.

    python3 scripts/ca_infer_lost_articles.py [--dry-run]

The General Statement prints its articles in a stable order year after year.  A block whose heading the OCR
dropped (article '?') sits between a known predecessor P and a known successor N; in another volume the
same P' and N' (fuzzy name match) enclose exactly the missing article(s).  When the volumes that carry
both anchors agree, the block is named (article := that name, flag article_inferred, article_inferred=1)
and the evidence is written to db/canada/article_inferences.csv.  Run after ca_parse_imports.py."""
import csv, re, sys, difflib
from collections import defaultdict, Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ROWS = ROOT / 'db' / 'canada' / 'imports_general_rows.csv'
OUT = ROOT / 'db' / 'canada' / 'article_inferences.csv'


def nk(s):
    s = (s or '').lower()
    s = re.sub(r'\((from|to|old|new)[^)]*\)', ' ', s)          # '(from 20th April)' / '(old tariff)'
    s = re.sub(r'&c\.?|\betc\b\.?|\bn\.?\s*e\.?\s*s\.?\b|\bviz\b', ' ', s)
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def sim(a, b):
    a, b = nk(a), nk(b)
    if not a or not b: return 0.0
    if a == b: return 1.0
    r = difflib.SequenceMatcher(None, a, b).ratio()
    ta, tb = set(a.split()), set(b.split())
    j = len(ta & tb) / len(ta | tb)
    return max(r, j)


def main():
    dry = '--dry-run' in sys.argv
    rows = list(csv.DictReader(open(ROWS)))
    fields = rows[0].keys()
    # ordered article sequence per volume: one entry per block (block_id order), regime C only
    seq = defaultdict(list)            # fy -> [(block_id, article, section, first_row_index)]
    seen = {}
    for idx, r in enumerate(rows):
        if r['regime'] != 'C' or r['row_kind'] in ('recap', 'summary'): continue
        if str(r['volume']).startswith('statcan_'): continue   # witness-inserted blocks are not part of the Canadiana print order
        k = (r['fiscal_year'], r['block_id'])
        if k in seen: continue
        seen[k] = len(seq[r['fiscal_year']])
        seq[r['fiscal_year']].append(dict(block=r['block_id'], article=r['article'] or '', section=r['section'] or '', idx=idx, parent=r['article_parent'] or ''))
    # val_imp per (fy, block) over detail rows, for the value sanity check
    bval = defaultdict(float)
    for r in rows:
        if r['regime'] == 'C' and r['row_kind'] == 'detail' and r['val_imp']:
            bval[(r['fiscal_year'], r['block_id'])] += float(r['val_imp'])
    for fy in seq:
        for e in seq[fy]: e['val'] = bval[(fy, e['block'])]
    years = sorted(seq)
    out = []; applied = 0
    for fy in years:
        S = seq[fy]
        i = 0
        while i < len(S):
            if S[i]['article'] != '?':
                i += 1; continue
            j = i
            while j < len(S) and S[j]['article'] == '?': j += 1
            gap = S[i:j]                                   # consecutive '?' blocks
            # anchors: nearest named blocks before and after (skip further '?')
            P = next((S[k] for k in range(i - 1, -1, -1) if S[k]['article'] not in ('?', '')), None)
            N = next((S[k] for k in range(j, len(S)) if S[k]['article'] not in ('?', '')), None)
            votes = []   # (other_fy, [names between])
            if P and N:
                for oy in years:
                    if oy == fy: continue
                    T = seq[oy]
                    # best match for P in T, then the best match for N after it within 12 blocks
                    best = None
                    for a, e in enumerate(T):
                        sp = sim(P['article'], e['article'])
                        if sp < 0.72: continue
                        for b in range(a + 1, min(a + 14, len(T))):
                            sn = sim(N['article'], T[b]['article'])
                            if sn >= 0.72:
                                sc = sp + sn
                                if best is None or sc > best[0]: best = (sc, a, b)
                                break
                    if best:
                        between = [(T[k]['article'], T[k]['val']) for k in range(best[1] + 1, best[2]) if T[k]['article'] not in ('?', '')]
                        between_d = []
                        for x, v in between:
                            if not between_d or sim(x, between_d[-1][0]) < 0.9: between_d.append((x, v))
                            else: between_d[-1] = (between_d[-1][0], between_d[-1][1] + v)
                        votes.append((oy, [x for x, v in between_d], best[0], [v for x, v in between_d]))
            # decide: volumes whose gap has exactly len(gap) articles, agreeing by name
            cands = Counter(); rep = {}
            gap_vals = [sum(float(r['val_imp'] or 0) for r in rows[g['idx']:g['idx'] + 400]
                            if r['block_id'] == g['block'] and r['fiscal_year'] == fy and r['row_kind'] == 'detail') for g in gap]
            for oy, between, sc, bvals in votes:
                if len(between) == len(gap):
                    # value sanity: the candidate's value in the other volume must be within a factor of 5 of the
                    # block's (articles come and go between years: 'Manuscripts' is not a $225K machinery block)
                    if any(gv >= 1000 and not (bv > 0 and 0.1 <= gv / bv <= 10) for gv, bv in zip(gap_vals, bvals)):
                        continue
                    key = tuple(nk(x) for x in between)
                    # merge near-identical spellings
                    merged = None
                    for k2 in cands:
                        if all(sim(a, b) >= 0.85 for a, b in zip(k2, key)): merged = k2; break
                    key = merged or key
                    cands[key] += 1; rep.setdefault(key, (between, oy))
            decision = None; why = ''
            if cands:
                key, n = cands.most_common(1)[0]
                agree = n; total = sum(cands.values())
                # accept when the surviving same-size votes agree (one dissenter tolerated among 3+); the two
                # name anchors within 14 blocks plus the value check carry the inference, support is recorded
                if agree == total or (agree >= 2 and agree >= total - 1):
                    decision = rep[key][0]; why = f'{agree}/{total} volumes agree ({", ".join(str(v[0]) for v in votes if len(v[1]) == len(gap))}); e.g. {rep[key][1]}'
            for g, name in zip(gap, decision or [None] * len(gap)):
                val = sum(float(r['val_imp'] or 0) for r in rows[g['idx']:g['idx'] + 400]
                          if r['block_id'] == g['block'] and r['fiscal_year'] == fy and r['row_kind'] == 'detail')
                out.append(dict(fiscal_year=fy, block_id=g['block'], prev_article=P['article'] if P else '', next_article=N['article'] if N else '',
                                gap_size=len(gap), value_imp=round(val), inferred=name or '',
                                votes='; '.join(f"{oy}:{len(b)}:{' | '.join(f'{x[:40]}={v:,.0f}' for x, v in zip(b, bv))}" for oy, b, sc, bv in votes)[:400], evidence=why))
                if name and not dry:
                    for r in rows[g['idx']:g['idx'] + 400]:
                        if r['block_id'] == g['block'] and r['fiscal_year'] == fy and r['article'] == '?':
                            r['article'] = name; r['flags'] = (r['flags'] + ',' if r['flags'] else '') + 'article_inferred'
                    applied += 1
                elif name:
                    applied += 1
            i = j
    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    tot = sum(o['value_imp'] for o in out); inf = sum(o['value_imp'] for o in out if o['inferred'])
    print(f"'?' blocks {len(out)} (val_imp {tot:,.0f}); named {applied} ({inf:,.0f})")
    if not dry:
        with open(ROWS, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    for o in sorted(out, key=lambda o: -o['value_imp'])[:40]:
        print(f"  {o['fiscal_year']} b{o['block_id']:>5} {o['value_imp']:>10,.0f} gap{o['gap_size']} [{o['prev_article'][:28]:28s} .. {o['next_article'][:28]:28s}] -> {o['inferred'][:45] if o['inferred'] else '-'}   {o['evidence'][:40]}")
        if not o['inferred']: print(f"        votes: {o['votes'][:230]}")


if __name__ == '__main__':
    main()
