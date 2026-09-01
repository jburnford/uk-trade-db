#!/usr/bin/env python3
"""Phase 5 of CANADA_IMPORTS_PLAN.md: parse the FY1891-1897 General Statement (regime D).

The design (all seven volumes, verified in the raw): TWO label columns --
'ARTICLES IMPORTED' and 'COUNTRIES AND PROVINCES' -- then five value columns
(qty imported, value imported, qty EfC, value EfC, duty).  The label column carries,
in print order within an article:

    Country—            a DASH-suffixed country opens a province run (the cross-tab
    Province..            LIVES ON after 1890 -- 277 'United States—' headers in 1893)
    Province..
    <no label, values>  the country's total
    Country.....        a dash-less country with values = a one-line national entry
    Total.....          opens the article's Total-by-province block (or carries the
    Province..            article grand when no provinces follow)

Output rows use the imports_general_rows.csv schema with regime='D':
  detail (country x province, or country-only with province=''), country_total,
  article_province_total (country='TOTAL'), article_total.

Diagnostics: country-run and Total-block closures, per-year national ratios vs
reference/canada_printed_totals.csv.  Output: db/canada/imports_general_rows_d.csv +
reports/canada_regimeD_parse.md.
"""
import csv, re, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ca_profile as P
import ca_parse_imports as I

ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / 'db' / 'canada' / 'imports_general_rows_d.csv'
OUT_MD = ROOT / 'reports' / 'canada_regimeD_parse.md'

START_RE = re.compile(r'No\.\s*(?:1|37)\.?\s*[—-]\s*GENERAL STATEMENT\s*\(by Countries and Provinces\)', re.I)
END_RE = re.compile(r'ABSTRACT of the Value of Goods entered|ABSTRACT BY COUNTRIES|RECAPITULATION BY PROVINCES|Aggregate Trade of the Dominion|SUMMARY STATEMENT', re.I)

SEED_COUNTRIES = {'great britain', 'united states', 'france', 'germany', 'spain', 'portugal', 'italy',
                  'holland', 'belgium', 'newfoundland', 'china', 'japan', 'switzerland', 'austria',
                  'greece', 'turkey', 'russia', 'denmark', 'sweden', 'norway', 'mexico', 'brazil',
                  'peru', 'chili', 'egypt', 'persia', 'siam', 'st pierre', 'hayti', 'cuba', 'iceland',
                  'australia', 'new zealand', 'mauritius', 'gibraltar', 'malta', 'bermuda'}


def is_country(txt):
    q = re.sub(r'[^a-z ]', ' ', txt.lower()); q = re.sub(r'\s+', ' ', q).strip()
    if not q: return False
    if any(q.startswith(s) or s.startswith(q[:10]) for s in SEED_COUNTRIES if len(q) >= 4): return True
    for w in ('indies', 'india', 'possessions', 'guiana', 'africa', 'colombia', 'republic',
              'islands', 'american', 'sandwich', 'aust', 'w i', 'norway'):
        if w in q: return True
    return False


def parse_volume(tag, fy, md_path, out, diag):
    text = md_path.read_text(errors='ignore')
    m = START_RE.search(text)
    if not m:
        print(f'{fy}: GS caption not found', file=sys.stderr); return 0
    start = m.start()
    n_tab = 0
    ctx = {'article': None, 'parent': '', 'country': None, 'in_total': False, 'section': 'DUTIABLE',
           'pending_country': None}
    body = text[start:]
    last_end = 0
    for seq, tm in enumerate(P.TABLE_RE.finditer(body)):
        inter = body[last_end:tm.start()]
        last_end = tm.end()
        if n_tab > 0 and END_RE.search(inter):
            break
        n_tab += 1
        for cells in P.parse_table(tm.group(0)):
            texts = [c for _, _, c in cells]
            joined = ' '.join(texts).upper()
            if 'FREE GOODS' in joined: ctx['section'] = 'FREE'
            if 'DUTIABLE GOODS' in joined: ctx['section'] = 'DUTIABLE'
            if all(k == 'th' for k, _, _ in cells): continue
            # split label cells (leading) from value cells (trailing 5)
            nums = []
            labs = []
            for t in texts:
                if not t.strip():
                    continue                              # a truly EMPTY cell is a structural artifact
                v, fl = I.parse_num(t)                    # (a '.....' blank is a real column placeholder)
                if v is None and fl != 'blank':
                    labs.append(t)
                else:
                    nums.append([t, v, fl])
            # fold a split duty ('128 | 25' -> 128.25) BEFORE positioning -- the split adds a sixth
            # cell that otherwise shifts every value one column left (the v1 7x-28x disaster)
            if len(nums) >= 2 and re.fullmatch(r'\d{1,2}', nums[-1][0].strip()) and nums[-2][1] is not None:
                nums[-2][1] = nums[-2][1] + float(nums[-1][0]) / 100.0
                nums.pop()
            vals = [v for t, v, fl in nums]
            while len(vals) > 5 and vals[0] is None: vals.pop(0)
            while len(vals) > 5 and vals[-1] is None: vals.pop()
            if len(vals) > 5:
                diag['overwide_row'] += 1; vals = vals[-5:]
            vals = (vals + [None] * 5)[:5] if len(vals) < 5 else vals
            qi, vi, qe, ve, duty = vals[:5]
            art_cell = ''
            lab = ''
            if len(labs) >= 2:
                art_cell, lab = labs[0], labs[-1]
            elif len(labs) == 1:
                lab = labs[0]
            lab_n = I.norm_label(lab)
            # banners inside label cells
            if re.search(r'FREE GOODS', lab, re.I): ctx['section'] = 'FREE'; lab_n = re.sub(r'FREE GOODS\W*(Con\.?)?', '', lab_n, flags=re.I).strip()
            if re.search(r'DUTIABLE GOODS', lab, re.I): ctx['section'] = 'DUTIABLE'; lab_n = re.sub(r'DUTIABLE GOODS\W*(Con\.?)?', '', lab_n, flags=re.I).strip()
            if art_cell.strip():
                a_n = I.norm_label(art_cell)
                if a_n and re.match(r'totals?\b', a_n, re.I):
                    ctx['in_total'] = True; ctx['country'] = None      # 'Total | Ontario' -- Total sits in the article slot
                elif a_n:
                    if a_n != ctx['article']:
                        ctx['article'] = a_n; ctx['country'] = None; ctx['in_total'] = False
            lab_p = re.sub(r'^(N\.?\s*W\.?\s*Ter\w*)\W*$', 'N. W. Territories', lab.strip())
            prov = I.province_of(lab_p)
            has_vals = any(v is not None for v in (vi, ve))
            def emit(kind, country, province):
                out.append(dict(fiscal_year=fy, volume=tag, table_seq=seq, row_seq=len(out), regime='D',
                                block_id=f'd{len(out)}', section=ctx['section'], section_label='',
                                article_parent=ctx['parent'], article=ctx['article'] or '?',
                                country=country, country_inferred='', province=province, row_kind=kind,
                                unit='', qty_brit=None, qty_foreign=None, qty_land=None,
                                qty_imp=qi, val_imp=vi, qty_efc=qe, val_efc=ve, duty=duty,
                                flags='', raw=' | '.join(texts)[:200]))
            if prov:
                if ctx['in_total']:
                    emit('article_province_total', 'TOTAL', prov)
                elif ctx['country']:
                    emit('detail', ctx['country'], prov)
                else:
                    emit('detail', '?', prov); diag['prov_no_country'] += 1
                continue
            if re.match(r'totals?\b', lab_n, re.I):
                ctx['in_total'] = True; ctx['country'] = None
                if has_vals: emit('article_total', None, '')
                continue
            if lab_n:
                cname = re.sub(r'[—-]+\s*$', '', lab_n).strip()
                # a country: dash opens a run; values make a one-line entry
                if re.search(r'[—-]\s*$', lab.strip()) or not has_vals:
                    ctx['country'] = cname; ctx['in_total'] = False
                    if has_vals: emit('detail', cname, '')
                    continue
                ctx['in_total'] = False
                emit('detail', cname, ''); ctx['country'] = None
                continue
            # no label
            if has_vals:
                if ctx['in_total']:
                    emit('article_total', None, ''); ctx['in_total'] = False
                elif ctx['country']:
                    emit('country_total', ctx['country'], ''); ctx['country'] = None
                else:
                    # a total with no home (usually the previous article's grand riding a page top):
                    # NEVER a detail row -- keep it out of every sum until a later pass places it
                    emit('orphan_total', None, ''); diag['orphan_total'] += 1
    return n_tab


def main():
    index = list(csv.DictReader(open(P.RAW / 'INDEX.tsv'), delimiter='\t'))
    out = []; diag = Counter(); per = []
    for row in index:
        if not row.get('note', '').startswith('NOPARSE'): continue
        tag, fy = row['volume_tag'], row['fiscal_year']
        md = P.RAW / tag / f'{tag}.md'
        if not md.exists(): continue
        before = len(out)
        n = parse_volume(tag, fy, md, out, diag)
        per.append((fy, tag, n, len(out) - before))
        print(f'{fy:8} {tag:24} tables={n:4} rows={len(out)-before:6}', file=sys.stderr)
    if not out:
        print('nothing parsed', file=sys.stderr); return
    fields = list(out[0].keys())
    with open(OUT_CSV, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(out)
    printed = {r['fiscal_year']: r for r in csv.DictReader(open(ROOT / 'reference' / 'canada_printed_totals.csv'))}
    agg = defaultdict(lambda: defaultdict(float))
    for r in out:
        if r['row_kind'] == 'detail' and r['province']:
            pass
    L = ['# Regime D (FY1891-1897) parse diagnostics', '',
         f'{len(out)} rows -> `{OUT_CSV.relative_to(ROOT)}`', '',
         '| FY | tables | rows | detail efc | printed efc | ratio | country-? |', '|---|---|---|---|---|---|---|']
    for fy, tag, n, m in per:
        det = [r for r in out if r['fiscal_year'] == fy and r['row_kind'] == 'detail']
        # avoid double counting: a country run (province rows) AND its country_total both exist;
        # detail rows only (country totals excluded) -- one-line countries carry province ''
        s = sum(r['val_efc'] or 0 for r in det)
        q = sum(r['val_efc'] or 0 for r in det if (r['country'] or '?') == '?')
        pr = float(printed[fy]['entered_for_consumption'])
        L.append(f'| {fy} | {n} | {m} | {s:,.0f} | {pr:,.0f} | {s/pr:.3f} | {q:,.0f} |')
    L += ['', 'Diagnostics: ' + ', '.join(f'{k} {v}' for k, v in diag.most_common())]
    OUT_MD.write_text('\n'.join(L) + '\n')
    print(OUT_MD.read_text(), file=sys.stderr)


if __name__ == '__main__':
    main()
