#!/usr/bin/env python3
"""Analysis exports from the parsed Canadian General Statement of Imports.

  exports/canada_imports_country_year.csv          fy x country (normalised) x section: value imported, value e.f.c., duty, rows
  exports/canada_imports_article_country_year.csv  fy x article (leaf, parent) x country x section: same, plus unit and quantities
  reports/canada_imports_origins.md                origin shares by year (Great Britain / United States / other named / unknown '?')

Regime C (1880+) uses province rows; regime B (1877) uses the province statements' country rows (Dominion
recapitulation excluded); regime A (1869-73, 1868) is included but flagged unreliable (column alignment open).
"""
import csv, re, sys

DOMINION_YEARS = {'1874', '1875'}
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import ca_parse_imports as I

CANON = {
    'great britain': 'Great Britain', 'united states': 'United States', 'france': 'France', 'germany': 'Germany',
    'b w indies': 'British West Indies', 'brit w indies': 'British West Indies', 'british w indies': 'British West Indies', 'british west indies': 'British West Indies',
    's w indies': 'Spanish West Indies', 'span w indies': 'Spanish West Indies', 'br w indies': 'British West Indies', 'sp w indies': 'Spanish West Indies', 'spanish w indies': 'Spanish West Indies', 'spanish west indies': 'Spanish West Indies',
    'f w indies': 'French West Indies', 'fr w indies': 'French West Indies', 'french w indies': 'French West Indies', 'french west indies': 'French West Indies',
    'd w indies': 'Danish West Indies', 'dan w indies': 'Danish West Indies', 'danish w indies': 'Danish West Indies', 'danish west indies': 'Danish West Indies',
    'b e indies': 'British East Indies', 'british e indies': 'British East Indies', 'british east indies': 'British East Indies',
    'd e indies': 'Dutch East Indies', 'dutch e indies': 'Dutch East Indies', 'dutch east indies': 'Dutch East Indies',
    'cent america': 'Central America', 'central american states': 'Central America', 'sand islands': 'Sandwich Islands', 'sandwich isds': 'Sandwich Islands',
    'st pierre': 'St. Pierre', 'st pierre et miquelon': 'St. Pierre', 'newfoundand': 'Newfoundland', 'newfoundland': 'Newfoundland',
    'norway & sweden': 'Norway and Sweden', 'norway and sweden': 'Norway and Sweden', 'b guiana': 'British Guiana', 'brit guiana': 'British Guiana',
    'chili': 'Chile', 'hayti': 'Haiti', 'united tates': 'United States', 'unted states': 'United States',
    # '“ “ Africa' under 'British West Indies' = British Africa (the ditto marks stand for 'British'); the abstract
    # prints it 'British Africa' / 'British Possessions in Africa' / 'B. Africa'
    'africa': 'British Africa', 'b africa': 'British Africa', 'brit africa': 'British Africa', 'british africa': 'British Africa',
    'british possessions in africa': 'British Africa', 'south africa': 'British Africa',
}

def canon(c):
    if c in (None, '', '?'): return '?'
    t = I.norm_label(c)
    t = re.sub(r'(\w)- (?=[a-z])', r'\1', t)
    k = re.sub(r'[^a-z& ]', ' ', t.lower().replace('-', ' ')).strip(); k = re.sub(r'\s+', ' ', k)
    if k in CANON: return CANON[k]
    k2 = k.replace('&', 'and')
    if k2 in CANON: return CANON[k2]
    if k.startswith('great brit') or (k.startswith('grea') and 'brit' in k): return 'Great Britain'
    if k.startswith('united st') or k in ('u s america', 'u s of america', 'u s', 'unired states'): return 'United States'
    if k.startswith('newfoundland'): return 'Newfoundland'                      # 'Newfoundland, includ- ing Labrador' (1891+)
    k = re.sub(r'\bposs?\b', 'possessions', k)
    if k.startswith('spanish possessions'):                                     # 1891+ abstract vs General Statement spellings
        if 'other' in k: return 'Spanish Possessions, all other'
        if 'pacific' in k: return 'Spanish Possessions, Pacific'
    m = re.match(r'^(west|east) indies (british|spanish|french|danish|dutch)$', k)
    if m: return m.group(2).capitalize() + ' ' + m.group(1).capitalize() + ' Indies'
    return t.strip(' .')

rows = list(csv.DictReader(open(ROOT / 'db' / 'canada' / 'imports_general_rows.csv')))
# regime D (FY1891-97) lives in its own staging file until the chain scripts learn its row shapes
# (ca_parse_regimeD.py -> --witness -> ca_merge_regimeD.py); its detail rows are national country
# rows (province '') plus the province rows of dash-country runs -- summing 'detail' is right,
# their unlabelled country_total is a separate kind
_d = ROOT / 'db' / 'canada' / 'imports_general_rows_d.csv'
if _d.exists():
    rows += [r for r in csv.DictReader(open(_d)) if r['regime'] == 'D']
CY = defaultdict(lambda: defaultdict(float)); ACY = defaultdict(lambda: defaultdict(float)); AU = {}
for r in rows:
    if r['row_kind'] != 'detail': continue
    # regime A years that print a Dominion recapitulation (1874-75): the national series comes
    # from it (Canadiana 1874 Dominion reads within 0.2% of the printed total; the province
    # statements manage 0.62) -- everywhere else the Dominion recap is excluded as a duplicate
    if r['regime'] == 'A' and r['fiscal_year'] in DOMINION_YEARS:
        if r['province'] != 'Dominion': continue
    elif r['province'] == 'Dominion':
        continue
    c = canon(r['country']); fy = r['fiscal_year']; sec = r['section'] or ''
    k = (fy, r['regime'], c, sec)
    CY[k]['n'] += 1
    for col in ('val_imp', 'val_efc', 'duty', 'qty_imp', 'qty_efc'):
        if r[col]: CY[k][col] += float(r[col])
    ak = (fy, r['regime'], r['article_parent'], r['article'], c, sec)
    ACY[ak]['n'] += 1
    for col in ('val_imp', 'val_efc', 'duty', 'qty_imp', 'qty_efc'):
        if r[col]: ACY[ak][col] += float(r[col])
    if r['unit'] and ak not in AU: AU[ak] = r['unit']
(ROOT / 'exports').mkdir(exist_ok=True)
with open(ROOT / 'exports' / 'canada_imports_country_year.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['fiscal_year', 'regime', 'country', 'section', 'rows', 'qty_imp', 'val_imp', 'qty_efc', 'val_efc', 'duty'])
    for k in sorted(CY): d = CY[k]; w.writerow([*k, int(d['n']), round(d['qty_imp']), round(d['val_imp']), round(d['qty_efc']), round(d['val_efc']), round(d['duty'], 2)])
with open(ROOT / 'exports' / 'canada_imports_article_country_year.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['fiscal_year', 'regime', 'article_parent', 'article', 'country', 'section', 'unit', 'rows', 'qty_imp', 'val_imp', 'qty_efc', 'val_efc', 'duty'])
    for k in sorted(ACY, key=lambda k: (k[0], k[1], k[2], k[3] or '', k[4], k[5])):
        d = ACY[k]; w.writerow([*k, AU.get(k, ''), int(d['n']), round(d['qty_imp']), round(d['val_imp']), round(d['qty_efc']), round(d['val_efc']), round(d['duty'], 2)])
# origin shares
L = ['# Canadian imports by origin, fiscal years ending 30 June', '',
     'From `exports/canada_imports_country_year.csv` (value imported, $; `?` = country label lost in OCR). Regime A 1874-75 are sourced from the DOMINION RECAPITULATION (1874 within 1% of print; GB/US/Germany EfC within 1.5% of the printed country series); 1868-73 remain INCOMPLETE (0.62-0.83 of print after the witness vote - both scans fail there). Regime D FY1891-97 (new marginal layout, parsed by ca_parse_regimeD + the StatCan witness vote) reads 0.90-0.98 of print (1897 1.015): the remaining loss is diffuse and two-sided, concentrated in Great Britain and the United States - see reports/canada_regimeD_merge.md for the per-country check against the Abstract.', '',
     '| FY | regime | total $ | Great Britain | United States | France | Germany | B.W. Indies | other named | ? | GB % | US % | other % (incl ?) |', '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
by = defaultdict(lambda: defaultdict(float)); regs = {}
for (fy, reg, c, sec), d in CY.items():
    by[fy][c] += d['val_imp']; regs[fy] = reg
for fy in sorted(by):
    d = by[fy]; tot = sum(d.values()) or 1
    named = {'Great Britain', 'United States', 'France', 'Germany', 'British West Indies', '?'}
    other = sum(v for c, v in d.items() if c not in named)
    L.append(f"| {fy} | {regs[fy]} | {tot:,.0f} | {d['Great Britain']:,.0f} | {d['United States']:,.0f} | {d['France']:,.0f} | {d['Germany']:,.0f} | {d['British West Indies']:,.0f} | {other:,.0f} | {d['?']:,.0f} | {100*d['Great Britain']/tot:.1f} | {100*d['United States']/tot:.1f} | {100*(tot-d['Great Britain']-d['United States'])/tot:.1f} |")
# check against the Abstract by Countries (value entered for consumption, printed country totals)
try:
    ab = list(csv.DictReader(open(ROOT / 'db' / 'canada' / 'imports_abstract_rows.csv')))
    A = defaultdict(lambda: defaultdict(float))
    for r in ab:
        if r['row_kind'] == 'province' and r['country'] != 'TOTAL' and r['efc_total']:
            A[r['fiscal_year']][canon(r['country'])] += float(r['efc_total'])
    E = defaultdict(lambda: defaultdict(float))
    for (fy, reg, c, sec), d in CY.items(): E[fy][c] += d['val_efc']
    L += ['', '## Check on the value entered for consumption: parsed vs the printed Abstract by Countries', '',
          '| FY | GB parsed | GB abstract | ratio | US parsed | US abstract | ratio | all other named parsed | all other abstract | ratio | ? parsed |', '|---|---|---|---|---|---|---|---|---|---|---|']
    for fy in sorted(A):
        e = E[fy]; a = A[fy]
        og = sum(v for c, v in e.items() if c not in ('Great Britain', 'United States', '?'))
        oa = sum(v for c, v in a.items() if c not in ('Great Britain', 'United States'))
        rt = lambda x, y: f'{x / y:.3f}' if y else '-'
        L.append(f"| {fy} | {e['Great Britain']:,.0f} | {a['Great Britain']:,.0f} | {rt(e['Great Britain'], a['Great Britain'])} | {e['United States']:,.0f} | {a['United States']:,.0f} | {rt(e['United States'], a['United States'])} | {og:,.0f} | {oa:,.0f} | {rt(og, oa)} | {e['?']:,.0f} |")
except FileNotFoundError:
    pass
# the printed, majority-voted by-country series (prefatory tables of every volume): the authority for origin shares
try:
    ser = list(csv.DictReader(open(ROOT / 'reference' / 'canada_country_series_voted.csv')))
    PS = defaultdict(dict)
    for r in ser:
        if r['measure'] == 'efc': PS[r['fiscal_year']][r['country']] = float(r['value'])
    E2 = defaultdict(lambda: defaultdict(float))
    for (fy, reg, c, sec), d in CY.items(): E2[fy][c] += d['val_efc']
    L += ['', '## PRINTED series: value entered for consumption by country, 1873-1889 (prefatory tables, majority-voted across volumes)', '',
          'Source: `reference/canada_country_series_voted.csv`. This is the authoritative origin table; the parsed General Statement (columns on the right) is the article-level layer beneath it.', '',
          '| FY | printed total | GB | US | France | Germany | West Indies | other | GB % | US % | other % | parsed GB | parsed US | parsed ? |', '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for fy in sorted(PS):
        d = PS[fy]; tot = d.get('total') or sum(v for k, v in d.items() if k != 'total')
        gb = d.get('great britain', 0); us = d.get('united states', 0)
        oth = tot - gb - us
        e = E2.get(fy, {})
        L.append(f"| {fy} | {tot:,.0f} | {gb:,.0f} | {us:,.0f} | {d.get('france',0):,.0f} | {d.get('germany',0):,.0f} | {d.get('west indies',0):,.0f} | {oth:,.0f} | {100*gb/tot:.1f} | {100*us/tot:.1f} | {100*oth/tot:.1f} | {e.get('Great Britain',0):,.0f} | {e.get('United States',0):,.0f} | {e.get('?',0):,.0f} |")
except FileNotFoundError:
    pass
L += ['', '## Top 15 origins by value, regime C years pooled (1880-89)', '']
pool = defaultdict(float)
for (fy, reg, c, sec), d in CY.items():
    if reg == 'C': pool[c] += d['val_imp']
tot = sum(pool.values())
for c, v in sorted(pool.items(), key=lambda x: -x[1])[:15]: L.append(f'- {c}: {v:,.0f} ({100*v/tot:.1f}%)')
(ROOT / 'reports' / 'canada_imports_origins.md').write_text('\n'.join(L) + '\n')
print('\n'.join(L[:22]))
