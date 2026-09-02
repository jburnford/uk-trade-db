#!/usr/bin/env python3
"""Phase 6 of CANADA_IMPORTS_PLAN.md (workstream A2 of COMPLETION_PLAN.md): promote the
FY1898-1908 spread-joined rows (ca_pair_spreads.py + ca_align_spreads.py) into the
imports_general_rows schema, regime 'S', keeping the tariff-group columns.

    python3 scripts/ca_promote_spreads.py

Input   db/canada/spread_rows_<tag>.csv for the PRIMARY witness of each year:
        FY1898/99 the Canadiana volume (cdn_33_5 / cdn_34_5), FY1900-1908 StatCan nibi_w2
        (the only imaging on disk for those years).  Rows are in print order (pair_id,
        row_seq); `labels` carries the left page's label cells joined by ' > ', article
        heading rows folded onto the next value row by the aligner.
Output  db/canada/imports_general_rows_s.csv (schema of imports_general_rows.csv + gt_qty,
        gt_value, gt_duty, pt_qty, pt_value, pt_duty, sx_qty, sx_value, sx_duty, align_status,
        closes), reports/canada_spreads_promote.md.

The layout is the regime D marginal design through FY1900 -- per article: country rows
(national), a dash-suffixed country opening a province run, a Total block by province, an
unlabelled grand -- and from FY1901 an article x country table with a printed 'Total' row
and no provinces.  The state machine is ca_parse_regimeD's, on already-joined rows.

Value columns: val_imp = TOTAL IMPORTS value, val_efc = TOTAL (entered for consumption)
value, duty = TOTAL duty; the tariff groups (General / Preferential-Reciprocal / Surtax) ride
along as extra fields.  Row provenance: align_status (joined = keyed join, joined_weak =
positional, left_only = no right half -> val_efc blank, right_only = no label -> country '?')
and the right row's own closure `closes` (2 = GT+PT==Total in value and duty).

National ratio N (sum of detail val_efc vs reference/canada_printed_totals.csv) and the
block-closure instrument are reported per year.  FY1907 is a nine-month year.
"""
import csv, re, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ca_parse_imports as I
import ca_parse_regimeD as D
from ca_parse_regimeD import is_country, RECAP_RE

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'db' / 'canada'
OUT_CSV = DB / 'imports_general_rows_s.csv'
OUT_MD = ROOT / 'reports' / 'canada_spreads_promote.md'
PRIMARY = {'1898': 'cdn_33_5_1898', '1899': 'cdn_34_5_1899'}
for _y in range(1900, 1909):
    PRIMARY[str(_y)] = f'statcan_nibi_w2_{_y}'

FIELDS = ['fiscal_year', 'volume', 'table_seq', 'row_seq', 'regime', 'block_id', 'section', 'section_label',
          'article_parent', 'article', 'country', 'country_inferred', 'province', 'row_kind', 'unit',
          'qty_brit', 'qty_foreign', 'qty_land', 'qty_imp', 'val_imp', 'qty_efc', 'val_efc', 'duty', 'flags', 'raw',
          'gt_qty', 'gt_value', 'gt_duty', 'pt_qty', 'pt_value', 'pt_duty', 'sx_qty', 'sx_value', 'sx_duty',
          'align_status', 'closes']
TOTAL_RE = re.compile(r'^totals?\b', re.I)
DASH_RE = re.compile(r'[—–-]\s*$')
DITTO_RE = re.compile(r'^[„"“”\'‟\s]+')


def f(x):
    try: return float(x)
    except (TypeError, ValueError): return None


def classify(part):
    """'article' | 'province' | 'total' | 'dash_country' | 'country' for one label cell."""
    t = part.strip()
    n = I.norm_label(t)
    if not n: return None, ''
    if I.province_of(re.sub(r'^(N\.?\s*W\.?\s*Ter\w*)\W*$', 'N. W. Territories', t)):
        return 'province', I.province_of(re.sub(r'^(N\.?\s*W\.?\s*Ter\w*)\W*$', 'N. W. Territories', t))
    if re.match(r'^yukon', n, re.I): return 'province', 'Yukon'
    if TOTAL_RE.match(n): return 'total', n
    if DASH_RE.search(t): return 'dash_country', DASH_RE.sub('', n).strip()
    if re.match(r'^\d+\s', t) or DITTO_RE.match(t) or len(n) > 40: return 'article', n
    if is_country(n) and len(n) <= 40: return 'country', n
    return 'article', n


def promote(fy, tag, out, diag):
    path = DB / f'spread_rows_{tag}.csv'
    if not path.exists():
        print(f'{fy}: missing {path}', file=sys.stderr); return 0
    rows = list(csv.DictReader(open(path)))
    rows.sort(key=lambda r: (int(r['pair_id']), int(r['row_seq'])))
    ctx = {'article': None, 'country': None, 'in_total': False, 'block': 0}
    n = 0
    for r in rows:
        parts = [p for p in r['labels'].split(' > ') if p.strip()]
        kinds = [classify(p) for p in parts]
        kinds = [k for k in kinds if k[0]]
        vi, ve = f(r['tot_imp_value']), f(r['efc_value'])
        has_vals = vi is not None or ve is not None
        flags = [r['align_status']]
        if r['closes']: flags.append(f"closes={r['closes']}")
        # article parts open a new block
        arts = [v for k, v in kinds if k == 'article']
        if arts:
            a = ' '.join(arts)
            if a != ctx['article']:
                ctx['article'] = a; ctx['country'] = None; ctx['in_total'] = False; ctx['block'] += 1
        prov = next((v for k, v in kinds if k == 'province'), None)
        tot = any(k == 'total' for k, v in kinds)
        dash = next((v for k, v in kinds if k == 'dash_country'), None)
        cty = next((v for k, v in kinds if k == 'country'), None)

        def emit(kind, country, province):
            nonlocal n
            if RECAP_RE.match(ctx['article'] or ''): kind = 'recap'
            out.append({'fiscal_year': fy, 'volume': tag, 'table_seq': r['pair_id'], 'row_seq': len(out), 'regime': 'S',
                        'block_id': f"s{ctx['block']}", 'section': 'DUTIABLE' if (f(r['efc_duty']) or 0) > 0 else '',
                        'section_label': r['era'], 'article_parent': '', 'article': ctx['article'] or '?',
                        'country': country, 'country_inferred': '', 'province': province, 'row_kind': kind, 'unit': '',
                        'qty_brit': None, 'qty_foreign': None, 'qty_land': None,
                        'qty_imp': f(r['tot_imp_qty']), 'val_imp': vi, 'qty_efc': f(r['efc_qty']), 'val_efc': ve,
                        'duty': f(r['efc_duty']), 'flags': ';'.join(flags), 'raw': r['labels'][:200],
                        'gt_qty': r['gt_qty'], 'gt_value': r['gt_value'], 'gt_duty': r['gt_duty'],
                        'pt_qty': r['pt_qty'], 'pt_value': r['pt_value'], 'pt_duty': r['pt_duty'],
                        'sx_qty': r['sx_qty'], 'sx_value': r['sx_value'], 'sx_duty': r['sx_duty'],
                        'align_status': r['align_status'], 'closes': r['closes']})
            n += 1

        if dash:
            ctx['country'] = dash; ctx['in_total'] = False
            if prov:
                emit('detail', dash, prov); continue
            if has_vals:
                emit('detail', dash, ''); ctx['country'] = None
            continue
        if tot:
            ctx['in_total'] = True; ctx['country'] = None
            if prov:
                emit('article_province_total', 'TOTAL', prov)
            elif has_vals:
                emit('article_total', None, ''); ctx['in_total'] = False
            continue
        if prov:
            if ctx['in_total']:
                emit('article_province_total', 'TOTAL', prov)
            elif ctx['country']:
                emit('detail', ctx['country'], prov)
            else:
                ctx['in_total'] = True                      # a Total block whose 'Total' label was not printed/read
                emit('article_province_total', 'TOTAL', prov); diag['prov_no_country'] += 1
            continue
        if cty:
            ctx['in_total'] = False
            if has_vals:
                emit('detail', cty, ''); ctx['country'] = None
            else:
                ctx['country'] = cty                        # a country opening a run without the dash
            continue
        if arts and has_vals and not cty:
            # the article row carries the first country's numbers with its label lost
            emit('detail', '?', ''); diag['article_row_values_no_country'] += 1
            continue
        if has_vals:
            if ctx['in_total']:
                emit('article_total', None, ''); ctx['in_total'] = False
            elif ctx['country']:
                emit('country_total', ctx['country'], ''); ctx['country'] = None
            else:
                emit('orphan_total', None, ''); diag['orphan_total'] += 1
    return n


def main():
    printed = {r['fiscal_year']: r for r in csv.DictReader(open(ROOT / 'reference' / 'canada_printed_totals.csv'))}
    out = []; diag = Counter(); per = []
    for fy in sorted(PRIMARY):
        before = len(out)
        promote(fy, PRIMARY[fy], out, diag)
        n_dut = len(out) - before
        # the FREE goods: single-page four-column tables in the regime-D layout, never spreads
        pairs = DB.parent.parent / 'reports' / f'spread_pairs_{PRIMARY[fy]}.tsv'
        md = next((Path(r['md_path']) for r in csv.DictReader(pairs.open(), delimiter='\t') if r.get('md_path')), None)
        free = []
        if md and md.exists():
            D.parse_volume(PRIMARY[fy], fy, md, free, diag, only_free=True, regime='S')
        for r in free:
            r.update({k: '' for k in FIELDS if k not in r}); r['row_seq'] = len(out); r['align_status'] = 'single_page'
            r['flags'] = (r['flags'] + ';' if r['flags'] else '') + 'single_page'
            out.append(r)
        per.append((fy, PRIMARY[fy], len(out) - before))
        print(f'{fy} {PRIMARY[fy]:26} dutiable(spread) rows={n_dut:6}  free(single-page) rows={len(free):6}', file=sys.stderr)
    with open(OUT_CSV, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS); w.writeheader(); w.writerows(out)
    L = ['# FY1898-1908 spread rows promoted into the schema (regime S)', '',
         f'{len(out)} rows -> `{OUT_CSV.relative_to(ROOT)}` (primary witness per year; `flags` carries align_status and the right row\'s closure)', '',
         '| FY | witness | rows | detail efc | printed efc | N | detail imp | printed imp | N imp | efc in joined | joined_weak | left_only | right_only | country ? |',
         '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for fy, tag, m in per:
        R = [r for r in out if r['fiscal_year'] == fy]
        det = [r for r in R if r['row_kind'] == 'detail']
        se = sum(r['val_efc'] or 0 for r in det); si = sum(r['val_imp'] or 0 for r in det)
        pe = float(printed[fy]['entered_for_consumption']); pi = float(printed[fy]['total_imports'])
        st = defaultdict(float)
        for r in det: st[r['align_status']] += r['val_efc'] or 0
        st['joined'] += st['single_page']            # single-page free tables are whole rows
        q = sum(r['val_efc'] or 0 for r in det if (r['country'] or '?') == '?')
        L.append(f"| {fy} | {tag} | {m} | {se:,.0f} | {pe:,.0f} | {se/pe:.3f} | {si:,.0f} | {pi:,.0f} | {si/pi:.3f} | "
                 f"{st['joined']/se if se else 0:.3f} | {st['joined_weak']/se if se else 0:.3f} | {st['left_only']/se if se else 0:.3f} | {st['right_only']/se if se else 0:.3f} | {q:,.0f} |")
    # block closure
    L += ['', '## Block closure (instrument C)', '', '| FY | blocks | closes | det_under | no_detail | det_over | unanchored |', '|---|---|---|---|---|---|---|']
    for fy, tag, m in per:
        R = [r for r in out if r['fiscal_year'] == fy]
        blocks = []; cur = None
        for r in R:
            if cur is None or cur['k'] != r['block_id']:
                cur = {'k': r['block_id'], 'det': 0.0, 'apt': 0.0, 'at': []}; blocks.append(cur)
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
        L.append(f"| {fy} | {len(blocks)} | {cell('closes')} | {cell('det_under')} | {cell('no_detail')} | {cell('det_over')} | {cell('unanchored')} |")
    L += ['', 'Diagnostics: ' + ', '.join(f'{k} {v}' for k, v in diag.most_common())]
    OUT_MD.write_text('\n'.join(L) + '\n')
    print(OUT_MD.read_text(), file=sys.stderr)


if __name__ == '__main__':
    main()
