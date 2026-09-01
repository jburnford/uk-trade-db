#!/usr/bin/env python3
"""Parse the 'ABSTRACT by Countries and Provinces' table of the Canadian Trade & Navigation volumes
(regime C years, 1880+): for each country x province, value ENTERED FOR HOME CONSUMPTION (dutiable,
free, total) and duty.  This is the volume's own cross-check for the General Statement (Table No. 1):
sum of the detail rows by country x province must reproduce it.

Output: db/canada/imports_abstract_rows.csv
"""
import csv, re, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ca_profile as P
import ca_parse_imports as I

OUT = P.ROOT / 'db' / 'canada' / 'imports_abstract_rows.csv'


def parse_volume(tag, fy, md_path, out):
    text = md_path.read_text(errors='replace')
    start = 0
    for mm in P.TN_START_RE2.finditer(text):
        if re.search(r'COMPILED\s+FROM\s+OFFICIAL\s+RETURNS', text[mm.start(): mm.start() + 1500], re.I):
            start = mm.start(); break
    tn = text[start:]
    pos = 0; in_abs = False; n = 0; country = None; diag = Counter()
    for seq, tm in enumerate(P.TABLE_RE.finditer(tn)):
        inter = tn[pos:tm.start()]; pos = tm.end()
        title = P.title_context(inter)[-300:]
        up = title.upper()
        if re.search(r'ABSTRACT\s+(BY|OF)\s+COUNTRIES\s+AND\s+PROVINCES', up):
            in_abs = True; country = None
        elif re.search(r'ABSTRACT|RECAPITULATION|SUMMARY|STATEMENT|TOTAL', up) and not re.search(r'continued', up, re.I):
            in_abs = False
        if not in_abs:
            continue
        rows = P.parse_table(tm.group(0))
        hdr = ' '.join(c for r in rows if r and all(k == 'th' for k, _, _ in r) for _, _, c in r).upper()
        if hdr and 'COUNTRIES' not in hdr and 'PROVINCES' not in hdr:
            in_abs = False; continue
        n += 1
        for cells in rows:
            if all(k == 'th' for k, _, _ in cells): continue
            texts = [c for _, _, c in cells]
            if len(texts) < 4: continue
            # layout: [country] [province] dutiable free total duty [cents]; leading label cells are decided
            # by recognising province / country text, because blank value cells make counting ambiguous
            c0 = texts[0]; c1 = texts[1] if len(texts) > 1 else ''
            p0 = I.province_of(c0); p1 = I.province_of(c1)
            def is_num(x):
                v, f = I.parse_num(x); return v is not None or f == 'fused'
            if p0:
                labels = [c0]; vals = texts[1:]
            elif p1 or (not c0.strip() and not c1.strip()) or (c0.strip() and not is_num(c0) and not is_num(c1)):
                labels = [c0, c1]; vals = texts[2:]
            elif not c0.strip():
                labels = [c0]; vals = texts[1:]
            else:
                labels = []; vals = texts
            if len(vals) >= 5 and (re.fullmatch(r'\d{2}', vals[4].strip()) or not vals[4].strip()) and not is_num(vals[4]) or (len(vals) >= 5 and re.fullmatch(r'\d{2}', vals[4].strip())):
                vals = vals[:3] + [(vals[3] + ' ' + vals[4]).strip()] + vals[5:]
            if len(vals) < 4:
                continue
            vals = vals[:4]
            nums = [I.parse_num(v, cents_ok=(i == 3)) for i, v in enumerate(vals)]
            if not any(v is not None for v, f in nums):
                continue
            prov = None
            if len(labels) == 2:
                c = I.norm_label(labels[0]); p = labels[1]
                if c: country = 'TOTAL' if re.match(r'totals?', c, re.I) else c
                prov = I.province_of(p) if p.strip() else None
                if not prov and not p.strip() and not c: pass       # country total row
            elif len(labels) == 1:
                lab = labels[0]
                prov = I.province_of(lab)
                if not prov and lab.strip():
                    c2, p2 = I.split_trailing_province(lab)
                    if p2: country = c2; prov = p2
                    elif re.match(r'totals?', I.norm_label(lab), re.I): country = 'TOTAL'
                    else: country = I.norm_label(lab); diag['label_not_province'] += 1
            kind = 'province' if prov else ('country_total' if country != 'TOTAL' else 'grand_total')
            if kind == 'grand_total':
                in_abs = False          # the Dominion total closes the abstract
            out.append(dict(fiscal_year=fy, volume=tag, table_seq=seq, country=country, province=prov, row_kind=kind,
                            efc_dutiable=nums[0][0], efc_free=nums[1][0], efc_total=nums[2][0], duty=nums[3][0],
                            flags=','.join(f for v, f in nums if f and f != 'blank'), raw=' | '.join(texts)))
    return n, diag


def main():
    index = list(csv.DictReader(open(P.RAW / 'INDEX.tsv'), delimiter='\t'))
    out = []
    for row in index:
        tag = row['volume_tag']; fy = row['fiscal_year']
        if row.get('note', '').startswith('NOPARSE'): continue   # registered but pending its parser (INDEX.tsv note says which phase)
        md = P.RAW / tag / f'{tag}.md'
        if not md.exists(): continue
        before = len(out)
        n, diag = parse_volume(tag, fy, md, out)
        if n:
            print(f'{fy:8} {tag:24} abstract tables={n:3} rows={len(out)-before:5} {dict(diag)}', file=sys.stderr)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader()
        for r in out: w.writerow(r)
    print(f'wrote {OUT} ({len(out)} rows)', file=sys.stderr)


if __name__ == '__main__':
    main()
