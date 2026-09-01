#!/usr/bin/env python3
"""Parse the SECOND WITNESS (StatCan CS4-4 departmental-edition scans, Chandra OCR) with the
same regime parser as the Canadiana corpus.  Phase 3 of CANADA_IMPORTS_PLAN.md.

Reads raw_canada/INDEX_W2.tsv (fiscal_year, volume_tag, md_path, role); parses the roles given
on the command line (default: regimeC only), writes db/canada/imports_general_rows_w2.csv and
reports/canada_witness_parse.md (national ratios + abstract ratios per year, beside the
Canadiana corpus figures so the two witnesses can be read together).

The manual-repair channel and Canadiana-specific sweeps in ca_parse_imports.main() are NOT
applied here -- repairs are witness-specific by construction.
"""
import csv, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ca_profile as P
import ca_parse_imports as I
from ca_check_abstract import ckey

ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / 'db' / 'canada' / 'imports_general_rows_w2.csv'
OUT_MD = ROOT / 'reports' / 'canada_witness_parse.md'


def main():
    roles = set(a for a in sys.argv[1:] if not a.startswith('-')) or {'regimeC'}
    index = list(csv.DictReader(open(P.RAW / 'INDEX_W2.tsv'), delimiter='\t'))
    p = I.Parser()
    per_vol = []
    for row in index:
        if row['role'] not in roles: continue
        tag, fy = row['volume_tag'], row['fiscal_year']
        md = Path(row['md_path'])
        if not md.exists():
            print(f'{fy}: MISSING {md}', file=sys.stderr); continue
        before = len(p.rows)
        n = p.parse_volume(tag, fy, md)
        per_vol.append((fy, tag, n, len(p.rows) - before))
        print(f'{fy:8} {tag:26} tables={n:4} rows={len(p.rows)-before:6}', file=sys.stderr)
    I.sweep_junk_country_labels(p.rows, p.diag)
    fields = ['fiscal_year', 'volume', 'table_seq', 'row_seq', 'regime', 'block_id', 'section', 'section_label',
              'article_parent', 'article', 'country', 'country_inferred', 'province', 'row_kind', 'unit',
              'qty_brit', 'qty_foreign', 'qty_land', 'qty_imp', 'val_imp', 'qty_efc', 'val_efc', 'duty', 'flags', 'raw']
    with open(OUT_CSV, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in p.rows: w.writerow(r)

    # national ratios
    printed = {r['fiscal_year']: r for r in csv.DictReader(open(ROOT / 'reference' / 'canada_printed_totals.csv'))}
    agg = defaultdict(lambda: defaultdict(float))
    for r in p.rows:
        if r['row_kind'] == 'detail' and r.get('province') != 'Dominion':
            for c in ('val_imp', 'val_efc', 'duty'):
                if r[c] is not None: agg[r['fiscal_year']][c] += r[c]
    # abstract ratios (the same printed oracle as the Canadiana check)
    A = defaultdict(lambda: defaultdict(float))
    for r in csv.DictReader(open(ROOT / 'db' / 'canada' / 'imports_abstract_rows.csv')):
        if r['row_kind'] == 'province' and r['country'] != 'TOTAL':
            for col, sec in (('efc_dutiable', 'dut'), ('efc_free', 'free')):
                if r[col]: A[r['fiscal_year']][(ckey(r['country']), r['province'], sec)] = float(r[col])
    cur = defaultdict(lambda: defaultdict(float))
    for r in p.rows:
        if r['row_kind'] != 'detail': continue
        sec = 'free' if r['section'] == 'FREE' else 'dut'
        cur[r['fiscal_year']][(ckey(r['country'] or ''), r['province'], sec)] += r['val_efc'] or 0

    L = ['# Second witness (StatCan CS4-4) — parse diagnostics', '',
         f'`scripts/ca_parse_witness.py` → `{OUT_CSV.relative_to(ROOT)}` ({len(p.rows)} rows)', '',
         '| FY | witness volume | tables | rows | national efc ratio | abstract efc ratio | abstract cells exact |',
         '|---|---|---|---|---|---|---|']
    for fy, tag, n, m in per_vol:
        pr = printed.get(fy, {})
        nat = ''
        if pr.get('entered_for_consumption'):
            nat = f"{agg[fy]['val_efc'] / float(pr['entered_for_consumption']):.3f}"
        aa = A.get(fy, {})
        tot_a = sum(aa.values()); tot_c = sum(cur[fy][k] for k in aa)
        exact = sum(1 for k, v in aa.items() if abs(cur[fy][k] - v) < 0.5)
        ab = f'{tot_c / tot_a:.3f}' if tot_a else ''
        L.append(f'| {fy} | {tag} | {n} | {m} | {nat} | {ab} | {exact}/{len(aa)} |')
    L += ['', 'Diagnostics: ' + ', '.join(f'{k} {v}' for k, v in p.diag.most_common(40))]
    OUT_MD.write_text('\n'.join(L) + '\n')
    print(f'wrote {OUT_CSV} and {OUT_MD}', file=sys.stderr)


if __name__ == '__main__':
    main()
