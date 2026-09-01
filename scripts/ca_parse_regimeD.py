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

UNIT_TOKEN_RE = re.compile(r'(?:' + I.UNIT_WORDS + r')\.?|\$(?:\s*cts\.?)?', re.I)
RECAP_RE = re.compile(r'^(recapitulation|by countries|by provinces|grand total|totals? (?:by|imports))', re.I)

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
           'pending': None}
    body = text[start:]
    last_end = 0
    nval = 5
    for seq, tm in enumerate(P.TABLE_RE.finditer(body)):
        inter = body[last_end:tm.start()]
        last_end = tm.end()
        if n_tab > 0 and END_RE.search(inter):
            break
        n_tab += 1
        # the RECAPITULATION tail (by provinces, no countries) is announced by its own header
        # row 'PROVINCES INTO WHICH IMPORTED' without 'COUNTRIES' -- its rows are not detail
        hdr = ' '.join(c for k, _, c in P.parse_table(tm.group(0))[0] if k == 'th').upper() if P.parse_table(tm.group(0)) else ''
        table_recap = 'PROVINCES INTO WHICH' in hdr and 'COUNTR' not in hdr
        if table_recap: diag['recap_table'] += 1
        for row in P.parse_table(tm.group(0)):
            if all(k == 'th' for k, _, _ in row):
                n = sum(1 for _, _, c in row if re.search(r'quantity|value|duty|^\$', c, re.I))
                if n in (4, 5): nval = n; break
        diag[f'nval_{nval}'] += 1
        for cells in P.parse_table(tm.group(0)):
            texts = [c for _, _, c in cells]
            joined = ' '.join(texts).upper()
            if 'FREE GOODS' in joined: ctx['section'] = 'FREE'
            if 'DUTIABLE GOODS' in joined: ctx['section'] = 'DUTIABLE'
            if all(k == 'th' for k, _, _ in cells): continue
            # COLUMN MAP FROM THE HEADER (v3): every table opens with a th row naming the value
            # columns -- 'Quantity. Value. Quantity. Value. Duty.' (5, dutiable) or the same
            # without Duty (4, free goods). The value cells are the LAST nval cells of a data
            # row; whatever precedes them is the label region. Only when a label token lands
            # inside the value region (an OCR-dropped cell) does the old heuristic apply.
            if len(texts) >= 2 and re.fullmatch(r'\d{1,2}', texts[-1].strip()) and I.parse_num(texts[-2])[0] is not None \
                    and not re.search(r'\d \d\d$', texts[-2].strip()):
                texts = texts[:-2] + [texts[-2].strip() + ' ' + texts[-1].strip()]   # split cents cell folded back
            labs = []; nums = []
            vals = None
            if len(texts) >= nval:
                region, labcells = texts[-nval:], texts[:-nval]
                rvals, bad = [], False
                for t in region:
                    if not t.strip():
                        rvals.append(None); continue
                    v, fl = I.parse_num(t)
                    if v is None and fl != 'blank':
                        if UNIT_TOKEN_RE.fullmatch(t.strip()): rvals.append(None)   # unit caption in a value column
                        else: bad = True
                    else:
                        rvals.append(v)
                if not bad:
                    vals = rvals + [None] * (5 - nval); diag['positional_row'] += 1
                    for t in labcells:
                        if t.strip() and not UNIT_TOKEN_RE.fullmatch(t.strip()):
                            labs.append(t)
            if vals is None:
                # fallback: label cells = non-numeric non-blank cells anywhere, numbers right-padded
                for t in texts:
                    if not t.strip():
                        continue
                    v, fl = I.parse_num(t)
                    if v is None and fl != 'blank':
                        if UNIT_TOKEN_RE.fullmatch(t.strip()):
                            continue
                        labs.append(t)
                    else:
                        nums.append([t, v, fl])
                vals = [v for t, v, fl in nums]
                while len(vals) > 5 and vals[0] is None: vals.pop(0)
                while len(vals) > 5 and vals[-1] is None: vals.pop()
                if len(vals) > 5:
                    diag['overwide_row'] += 1; vals = vals[-5:]
                if len(vals) == 3 and nval == 5 and vals[2] is not None and re.search(r'\d \d\d$|\.\d\d$', (texts[-1] or '').strip()):
                    vals = [None, vals[0], None, vals[1], vals[2]]; diag['value_only_row'] += 1   # value | value | duty-with-cents
                vals = (vals + [None] * 5)[:5] if len(vals) < 5 else vals
                diag['fallback_row'] += 1
            qi, vi, qe, ve, duty = vals[:5]
            art_cell = ''
            lab = ''
            if len(labs) >= 2:
                art_cell, lab = labs[0], labs[-1]
            elif len(labs) == 1:
                lab = labs[0]
            lab_n = I.norm_label(lab)
            unit_row = any(UNIT_TOKEN_RE.fullmatch(t.strip()) for t in texts if t.strip())
            section_total = bool(re.match(r'totals?,?\s+(dutiable|free)', lab_n, re.I)) or \
                (bool(art_cell.strip()) and bool(re.match(r'totals?,?\s+(dutiable|free)', I.norm_label(art_cell), re.I)))
            # banners inside label cells
            if re.search(r'FREE GOODS', lab, re.I): ctx['section'] = 'FREE'; lab_n = re.sub(r'FREE GOODS\W*(Con\.?)?', '', lab_n, flags=re.I).strip()
            if re.search(r'DUTIABLE GOODS', lab, re.I): ctx['section'] = 'DUTIABLE'; lab_n = re.sub(r'DUTIABLE GOODS\W*(Con\.?)?', '', lab_n, flags=re.I).strip()
            if art_cell.strip():
                a_n = I.norm_label(art_cell)
                if a_n and re.match(r'totals?\b', a_n, re.I):
                    ctx['in_total'] = True; ctx['country'] = None; ctx['pending'] = None   # 'Total | Ontario' -- Total sits in the article slot
                elif a_n:
                    if a_n != ctx['article']:
                        ctx['article'] = a_n; ctx['country'] = None; ctx['in_total'] = False; ctx['pending'] = None
            lab_p = re.sub(r'^(N\.?\s*W\.?\s*Ter\w*)\W*$', 'N. W. Territories', lab.strip())
            prov = I.province_of(lab_p)
            has_vals = any(v is not None for v in (vi, ve))
            def emit(kind, country, province):
                if table_recap or RECAP_RE.match(ctx['article'] or ''):
                    kind = 'recap'; diag['recap_row'] += 1      # every kind: the recap prints province totals too
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
                    # a province row with no country run open can only be the article's
                    # Total block whose 'Total' label the OCR dropped: counting it as
                    # detail double-counts the country rows above (v2 diagnosis, FY1891
                    # coal 'All other, N.E.S | Ontario 3,802,044')
                    ctx['in_total'] = True
                    emit('article_province_total', 'TOTAL', prov); diag['prov_no_country'] += 1
                continue
            if section_total:
                emit('section_total', None, ''); diag['section_total'] += 1     # 'Total, Dutiable Goods' -- the section grand
                ctx['in_total'] = False; ctx['country'] = None; ctx['pending'] = None
                continue
            if re.match(r'totals?\b', lab_n, re.I):
                ctx['in_total'] = True; ctx['country'] = None; ctx['pending'] = None
                if has_vals: emit('article_total', None, '')
                continue
            if lab_n and len(labs) == 1 and len(lab_n) > 22 and not is_country(lab_n) and not re.search(r'[—-]\s*$', lab.strip()):
                # a long non-country label alone on a value row is an ARTICLE heading that
                # carries numbers (a summary line such as 'Melado, &c., direct and not
                # direct' or a heading fused with the next line): open the article, keep
                # the numbers out of the country detail
                ctx['article'] = lab_n; ctx['country'] = None; ctx['in_total'] = False
                if has_vals: emit('article_total', None, ''); diag['heading_with_values'] += 1
                continue
            if lab_n:
                cname = re.sub(r'[—-]+\s*$', '', lab_n).strip()
                # THE SLIP: the unit line ('Tons.') is printed with the first country's label
                # and no numbers, and the OCR pairs label row k with number row k+1 from
                # there on, until an unlabelled number row re-syncs (regime B's systematic
                # slip, here conditional on the unit row). A country label on a unit row
                # with no values is PENDING: it takes the next value row's numbers, and that
                # row's own label becomes pending in turn.
                if unit_row and not has_vals and not re.search(r'[—-]\s*$', lab.strip()):
                    ctx['pending'] = cname; ctx['country'] = None; ctx['in_total'] = False
                    diag['pending_label'] += 1
                    continue
                if ctx.get('pending') and has_vals and not re.search(r'[—-]\s*$', lab.strip()):
                    emit('detail', ctx['pending'], ''); diag['slip_repaired'] += 1
                    ctx['pending'] = cname; ctx['country'] = None; ctx['in_total'] = False
                    continue
                # a country: dash opens a run; values make a one-line entry
                if re.search(r'[—-]\s*$', lab.strip()) or not has_vals:
                    ctx['country'] = cname; ctx['in_total'] = False; ctx['pending'] = None
                    if has_vals: emit('detail', cname, '')
                    continue
                ctx['in_total'] = False
                emit('detail', cname, ''); ctx['country'] = None
                continue
            # no label
            if has_vals:
                if ctx.get('pending'):
                    emit('detail', ctx['pending'], ''); ctx['pending'] = None; diag['slip_resynced'] += 1
                elif ctx['in_total']:
                    emit('article_total', None, ''); ctx['in_total'] = False
                elif ctx['country']:
                    emit('country_total', ctx['country'], ''); ctx['country'] = None
                else:
                    # a total with no home (usually the previous article's grand riding a page top):
                    # NEVER a detail row -- keep it out of every sum until a later pass places it
                    emit('orphan_total', None, ''); diag['orphan_total'] += 1
    return n_tab


def main():
    witness = '--witness' in sys.argv
    out = []; diag = Counter(); per = []
    if witness:
        # the StatCan second witness (raw_canada/INDEX_W2.tsv role post1890, FY1891-97) through the
        # same state machine; separate staging file, merged by ca_merge_regimeD.py
        index = [r for r in csv.DictReader(open(P.RAW / 'INDEX_W2.tsv'), delimiter='\t')
                 if r['role'] == 'post1890' and 1891 <= int(r['fiscal_year']) <= 1897]
        out_csv = OUT_CSV.with_name('imports_general_rows_d_w2.csv')
        out_md = OUT_MD.with_name('canada_regimeD_witness_parse.md')
    else:
        index = [r for r in csv.DictReader(open(P.RAW / 'INDEX.tsv'), delimiter='\t')
                 if r.get('note', '').startswith('NOPARSE')]
        out_csv, out_md = OUT_CSV, OUT_MD
    for row in index:
        tag, fy = row['volume_tag'], row['fiscal_year']
        md = Path(row['md_path']) if witness else P.RAW / tag / f'{tag}.md'
        if not md.exists(): continue
        before = len(out)
        n = parse_volume(tag, fy, md, out, diag)
        per.append((fy, tag, n, len(out) - before))
        print(f'{fy:8} {tag:24} tables={n:4} rows={len(out)-before:6}', file=sys.stderr)
    if not out:
        print('nothing parsed', file=sys.stderr); return
    fields = list(out[0].keys())
    with open(out_csv, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(out)
    printed = {r['fiscal_year']: r for r in csv.DictReader(open(ROOT / 'reference' / 'canada_printed_totals.csv'))}
    agg = defaultdict(lambda: defaultdict(float))
    for r in out:
        if r['row_kind'] == 'detail' and r['province']:
            pass
    L = ['# Regime D (FY1891-1897) parse diagnostics' + (' -- StatCan WITNESS' if witness else ''), '',
         f'{len(out)} rows -> `{out_csv.relative_to(ROOT)}`', '',
         '| FY | tables | rows | detail efc | printed efc | ratio | country-? |', '|---|---|---|---|---|---|---|']
    for fy, tag, n, m in per:
        det = [r for r in out if r['fiscal_year'] == fy and r['row_kind'] == 'detail']
        # avoid double counting: a country run (province rows) AND its country_total both exist;
        # detail rows only (country totals excluded) -- one-line countries carry province ''
        s = sum(r['val_efc'] or 0 for r in det)
        q = sum(r['val_efc'] or 0 for r in det if (r['country'] or '?') == '?')
        pr = float(printed[fy]['entered_for_consumption'])
        L.append(f'| {fy} | {n} | {m} | {s:,.0f} | {pr:,.0f} | {s/pr:.3f} | {q:,.0f} |')
    L += ['', '## Block closure (instrument C): country rows vs the article\'s own Total block', '',
          'A block = consecutive rows of one (section, article). grand = the article_total row, else the sum of its',
          'province totals. closes = |sum(country rows) - grand| <= $1. Masses in $ of val_efc.', '',
          '| FY | blocks | closes | det_under (missing) | no_detail (grand only) | det_over (excess) | unanchored (no grand) | sum apt | sum article_total |',
          '|---|---|---|---|---|---|---|---|---|']
    for fy, tag, n, m in per:
        R = [r for r in out if r['fiscal_year'] == fy]
        blocks = []; cur = None
        for r in R:
            k = (r['section'], r['article'])
            if cur is None or cur['k'] != k:
                cur = {'k': k, 'det': 0.0, 'apt': 0.0, 'at': []}; blocks.append(cur)
            v = r['val_efc'] or 0
            if r['row_kind'] == 'detail': cur['det'] += v
            elif r['row_kind'] == 'article_province_total': cur['apt'] += v
            elif r['row_kind'] == 'article_total': cur['at'].append(v)
        cls = Counter(); mass = defaultdict(float)
        for b in blocks:
            grand = b['at'][-1] if b['at'] else (b['apt'] if b['apt'] else None)
            if grand is None: c = 'unanchored'; mass[c] += b['det']
            elif abs(b['det'] - grand) <= 1: c = 'closes'; mass[c] += b['det']
            elif b['det'] == 0: c = 'no_detail'; mass[c] += grand
            elif b['det'] < grand: c = 'det_under'; mass[c] += grand - b['det']
            else: c = 'det_over'; mass[c] += b['det'] - grand
            cls[c] += 1
        cell = lambda c: f"{cls[c]} ({mass[c]:,.0f})"
        L.append(f"| {fy} | {len(blocks)} | {cell('closes')} | {cell('det_under')} | {cell('no_detail')} | {cell('det_over')} | {cell('unanchored')} | "
                 f"{sum(b['apt'] for b in blocks):,.0f} | {sum(b['at'][-1] for b in blocks if b['at']):,.0f} |")
    L += ['', 'Diagnostics: ' + ', '.join(f'{k} {v}' for k, v in diag.most_common())]
    out_md.write_text('\n'.join(L) + '\n')
    print(out_md.read_text(), file=sys.stderr)


if __name__ == '__main__':
    main()
