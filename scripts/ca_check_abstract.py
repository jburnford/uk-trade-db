#!/usr/bin/env python3
"""Cross-check the parsed General Statement of Imports against the volume's own Abstract by Countries
and Provinces: for every (fiscal year, country, province) the sum of detail rows' value entered for
consumption (dutiable / free) and duty must equal the abstract's printed figures.
Writes reports/canada_abstract_check.md."""
import csv, re, sys
from collections import defaultdict, Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import ca_parse_imports as I

def ckey(c):
    c = I.norm_label(c or '')
    c = re.sub(r'\bBrit\.?\b', 'British', c); c = re.sub(r'\bBrt\.\s*', 'British ', c); c = re.sub(r'\bW\.\s*Indies', 'West Indies', c); c = re.sub(r'\bE\.\s*Indies', 'East Indies', c)
    c = re.sub(r'\bSpan?\.\s*', 'Spanish ', c); c = re.sub(r'\bFr(en)?\.\s*', 'French ', c); c = re.sub(r'\bDan\.\s*', 'Danish ', c)
    c = re.sub(r'\bW\.\s*Ind\b\.?', 'West Indies', c); c = re.sub(r'\bE\.\s*Ind\b\.?', 'East Indies', c)
    c = re.sub(r'\bB\.\s*(?=West|East)', 'British ', c); c = re.sub(r'\bS\.\s*(?=West)', 'Spanish ', c); c = re.sub(r'\bF\.\s*(?=West)', 'French ', c)
    c = re.sub(r'\bD(an)?\.\s*(?=West)', 'Danish ', c); c = re.sub(r'\bD\.\s*(?=East)', 'Dutch ', c)
    c = re.sub(r'\bCent\.\s*', 'Central ', c); c = re.sub(r'\bSand\.\s*', 'Sandwich ', c)
    c = re.sub(r'(\w)- (?=[a-z])', r'\1', c)                      # 'posses- sions' -> 'possessions'
    c = re.sub(r'\bB\.\s*(?=Africa|Guiana|Honduras)', 'British ', c)
    c = re.sub(r'[^A-Za-z ]', '', c).lower().strip()
    c = re.sub(r'\b(in|and|the|of)\b', ' ', c)                       # 'Spanish possessions in Pacific Ocean', 'Norway & Sweden'
    c = re.sub(r'\s+', ' ', c).strip()
    m = re.match(r'^(west|east) indies (british|spanish|french|danish|dutch)$', c)      # 'West Indies, Spanish'
    if m: c = m.group(2) + ' ' + m.group(1) + ' indies'
    if (c.startswith('grea') or c.startswith('gt ')) and 'brit' in c: c = 'great britain'   # 'Gt. Britain ( via Hudson Bay)'
    if c.startswith('united st'): c = 'united states'
    if c in ('africa', 'british possessions africa', 'south africa'): c = 'british africa'     # '“ “ Africa' = British Africa
    if c.startswith('sp west indies'): c = 'spanish west indies'                                # 'Sp. W. Indies'
    if c in ('brit w indies', 'british w indies'): c = 'british west indies'
    if c == 'e guiana': c = 'british guiana'                                                    # 'B.' misread as 'E.' (1889, sugar to NS)
    if c in ('spanish possessions other', 'spanish possessions all other'): c = 'spanish possessions all other'
    if c in ('central am states', 'central american states'): c = 'central american states'
    if c in ('norway sweden', 'norway and sweden'): c = 'norway sweden'                         # '&' vs 'and' (the & is stripped)
    return c

def main():
    imp = list(csv.DictReader(open(ROOT / 'db' / 'canada' / 'imports_general_rows.csv')))
    ab = list(csv.DictReader(open(ROOT / 'db' / 'canada' / 'imports_abstract_rows.csv')))
    S = defaultdict(lambda: defaultdict(float)); D = defaultdict(lambda: defaultdict(float)); V = defaultdict(lambda: defaultdict(float))
    for r in imp:
        if r['row_kind'] != 'detail' or r['regime'] != 'C': continue
        k = (r['fiscal_year'], ckey(r['country']), r['province'])
        sec = 'free' if r['section'] == 'FREE' else 'dut'
        if r['val_efc']: S[k][sec] += float(r['val_efc'])
        if r['duty']: D[k]['duty'] += float(r['duty'])
        if r['val_imp']: V[k]['imp'] += float(r['val_imp'])
    A = {}
    for r in ab:
        if r['row_kind'] != 'province' or r['country'] == 'TOTAL': continue
        A[(r['fiscal_year'], ckey(r['country']), r['province'])] = r
    L = ['# General Statement vs Abstract by Countries and Provinces', '',
         'Per (fiscal year, country, province): parsed sum of detail rows vs the printed abstract. `efc` = value entered for home consumption.', '']
    by_fy = defaultdict(list)
    for k, r in A.items(): by_fy[k[0]].append(k)
    L += ['| FY | abstract cells | matched keys | efc dutiable exact | efc free exact | duty exact | abstract efc total | parsed efc total | ratio | unmatched abstract value |', '|---|---|---|---|---|---|---|---|---|---|']
    details = []
    for fy in sorted(by_fy):
        keys = by_fy[fy]; n = len(keys); m = 0; ex = Counter(); tot_ab = 0; tot_p = 0; unm = 0
        for k in keys:
            r = A[k]; t = float(r['efc_total']) if r['efc_total'] else 0; tot_ab += t
            if k in S or k in D:
                m += 1
                p = S[k]['dut'] + S[k]['free']; tot_p += p
                for col, pv, av in (('dut', S[k]['dut'], r['efc_dutiable']), ('free', S[k]['free'], r['efc_free']), ('duty', D[k]['duty'], r['duty'])):
                    if av not in ('', None) and abs(pv - float(av)) < 0.011: ex[col] += 1
                if abs(p - t) > max(1, 0.002 * t):
                    details.append((fy, k[1], k[2], p, t, S[k]['dut'], r['efc_dutiable'], S[k]['free'], r['efc_free']))
            else:
                unm += t
        L.append(f"| {fy} | {n} | {m} | {ex['dut']} | {ex['free']} | {ex['duty']} | {tot_ab:,.0f} | {tot_p:,.0f} | {tot_p/tot_ab if tot_ab else 0:.3f} | {unm:,.0f} |")
    # parsed keys not in abstract (country name mismatches)
    extra = Counter()
    for k in S:
        if k not in A: extra[(k[0], k[1])] += S[k]['dut'] + S[k]['free']
    L += ['', '## Largest discrepancies (|parsed − abstract| efc total)', '', '| FY | country | province | parsed | abstract | parsed dut | abs dut | parsed free | abs free |', '|---|---|---|---|---|---|---|---|---|']
    details.sort(key=lambda d: -abs(d[3] - d[4]))
    for d in details[:40]:
        L.append(f"| {d[0]} | {d[1]} | {d[2]} | {d[3]:,.0f} | {d[4]:,.0f} | {d[5]:,.0f} | {d[6]} | {d[7]:,.0f} | {d[8]} |")
    L += ['', '## Parsed (country, year) with no abstract counterpart (name mismatch or abstract parse gap), by value', '']
    for (fy, c), v in extra.most_common(25): L.append(f'- {fy} {c!r}: {v:,.0f}')
    (ROOT / 'reports' / 'canada_abstract_check.md').write_text('\n'.join(L) + '\n')
    print('\n'.join(L[:16]))


if __name__ == '__main__':
    main()
