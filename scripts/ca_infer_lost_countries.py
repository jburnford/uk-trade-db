#!/usr/bin/env python3
"""Infer lost country labels from the volume's own Abstract by Countries and Provinces.

    python3 scripts/ca_infer_lost_countries.py [--dry-run]

For every segment of regime-C detail rows whose country is '?' (a label the OCR dropped), compute the
segment's value entered for consumption by province (in its section, dutiable/free) and look for the ONE
country whose abstract residual (printed − parsed, same year/province/section) matches the segment in every
province it touches.  The residual of the true owner is exactly the missing segment (plus noise from other
defects); any other country's residual is unrelated, so a per-province match across several provinces is
strong evidence, and uniqueness guards the rest.  Segments are processed largest first and the residuals
are updated after each assignment.

Writes the inferences to db/canada/country_inferences.csv and (unless --dry-run) applies them to
db/canada/imports_general_rows.csv in place: country := inferred, country_inferred := 2, flag
'abstract_inferred'.  Run after ca_parse_imports.py and before ca_export_country_year.py."""
import csv, sys
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from ca_check_abstract import ckey

ROWS = ROOT / 'db' / 'canada' / 'imports_general_rows.csv'
ABS = ROOT / 'db' / 'canada' / 'imports_abstract_rows.csv'
OUT = ROOT / 'db' / 'canada' / 'country_inferences.csv'
TOL_ABS = 100.0       # per-province tolerance, dollars (the residual carries noise from other defects)
MIN_PROV_VALUE = 300  # provinces below this are not required to match (but must not contradict wildly)


def tol(v):
    """match tolerance for a province value v: 1% above $1000, 5% below, never under $100"""
    return max(TOL_ABS, (0.01 if v >= 1000 else 0.05) * v)


def fits(R, v, printed):
    """The segment value v fits the residual R (printed − parsed) of a candidate cell: it may fall SHORT of
    the residual by up to 0.5% of the printed cell (the country's other coverage losses) but may not EXCEED
    it by more than the plain tolerance (nothing can be more missing than the residual)."""
    if R is None: return False
    slack = max(tol(v), 0.005 * (printed or 0))
    return -tol(v) <= R - v <= slack


def rank(c):
    return 0 if c.startswith('great brit') else 1 if c.startswith('united st') else 2


def main():
    dry = '--dry-run' in sys.argv
    rows = list(csv.DictReader(open(ROWS)))
    fields = rows[0].keys()
    # printed abstract: (fy, ckey, prov) -> {dut, free, duty}
    A = {}
    names = defaultdict(dict)           # (fy, ckey) -> printed name
    for r in csv.DictReader(open(ABS)):
        if r['row_kind'] != 'province' or r['country'] == 'TOTAL': continue
        k = (r['fiscal_year'], ckey(r['country']), r['province'])
        A[k] = {'dut': float(r['efc_dutiable']) if r['efc_dutiable'] else None,
                'free': float(r['efc_free']) if r['efc_free'] else None,
                'duty': float(r['duty']) if r['duty'] else None}
        names[(r['fiscal_year'], ckey(r['country']))] = r['country']
    # parsed sums per (fy, ckey, prov) -> {dut, free, duty}
    P = defaultdict(lambda: {'dut': 0.0, 'free': 0.0, 'duty': 0.0})
    for r in rows:
        if r['row_kind'] != 'detail' or r['regime'] != 'C' or r['country'] in ('', '?'): continue
        k = (r['fiscal_year'], ckey(r['country']), r['province'])
        sec = 'free' if r['section'] == 'FREE' else 'dut'
        if r['val_efc']: P[k][sec] += float(r['val_efc'])
        if r['duty']: P[k]['duty'] += float(r['duty'])
    def resid(fy, c, prov, col):
        a = A.get((fy, c, prov))
        if a is None or a[col] is None: return None
        return a[col] - P[(fy, c, prov)][col]
    # '?' segments: consecutive rows in one block with country '?' (detail rows carry the values)
    segs = []
    i = 0; n = len(rows)
    while i < n:
        r = rows[i]
        if r['regime'] == 'C' and r['country'] == '?' and r['row_kind'] in ('detail', 'country_total'):
            j = i
            while j < n and rows[j]['country'] == '?' and rows[j]['row_kind'] in ('detail', 'country_total') \
                    and rows[j]['block_id'] == r['block_id'] and rows[j]['fiscal_year'] == r['fiscal_year']: j += 1
            det = [x for x in rows[i:j] if x['row_kind'] == 'detail' and x['province']]
            if det:
                segs.append((i, j, det))
            i = j
        else:
            i += 1
    # largest first
    def segval(det): return sum(float(x['val_efc'] or 0) for x in det)
    segs.sort(key=lambda s: -segval(s[2]))
    countries_by_fy = defaultdict(set)
    for (fy, c, prov) in A: countries_by_fy[fy].add(c)
    out = []; applied = 0
    for i, j, det in segs:
        fy = det[0]['fiscal_year']
        sec = 'free' if det[0]['section'] == 'FREE' else 'dut'
        by_prov = defaultdict(lambda: {'efc': 0.0, 'duty': 0.0})
        for x in det:
            if x['val_efc']: by_prov[x['province']]['efc'] += float(x['val_efc'])
            if x['duty']: by_prov[x['province']]['duty'] += float(x['duty'])
        provs = [p for p, v in by_prov.items() if v['efc'] > 0]
        big = [p for p in provs if by_prov[p]['efc'] >= MIN_PROV_VALUE]
        if not big: continue
        # print order gate: countries are printed GB, US, then the rest; the labelled neighbours of the segment
        # in its block bound the candidates
        blk = [x for x in rows[max(0, i - 80):i] if x['block_id'] == det[0]['block_id'] and x['fiscal_year'] == fy]
        prev = next((ckey(x['country']) for x in reversed(blk) if x['row_kind'] == 'detail' and x['country'] not in ('', '?', 'TOTAL')), None)
        after = [x for x in rows[j:j + 80] if x['block_id'] == det[0]['block_id'] and x['fiscal_year'] == fy]
        nxt = next((ckey(x['country']) for x in after if x['row_kind'] == 'detail' and x['country'] not in ('', '?', 'TOTAL')), None)
        def allowed(c):
            r = rank(c)
            if prev is not None and r < 2 and r <= rank(prev): return False   # GB/US cannot follow a later-ranked country
            if nxt is not None and rank(nxt) == 0: return False             # nothing precedes GB in an article
            if nxt is not None and rank(nxt) == 1 and r != 0: return False  # only GB precedes the US
            if nxt is not None and rank(nxt) == 2 and prev is None and r == 2: return True
            return True
        matches = []
        for c in countries_by_fy[fy]:
            if not allowed(c): continue
            ok = True; score = 0.0; n_match = 0
            for p in provs:
                v = by_prov[p]['efc']
                R = resid(fy, c, p, sec); pr = A.get((fy, c, p), {}).get(sec)
                if R is None:
                    if v >= MIN_PROV_VALUE: ok = False; break
                    continue
                if fits(R, v, pr):
                    n_match += 1; score += abs(R - v)
                elif v >= MIN_PROV_VALUE:
                    ok = False; break
            need = 2 if len(big) >= 2 else 1
            if ok and n_match >= need:
                # the duty column must not contradict (when both printed and parsed carry duty)
                dbad = False
                for p in big:
                    dv = by_prov[p]['duty']
                    if dv <= 0: continue
                    Rd = resid(fy, c, p, 'duty')
                    if Rd is not None and abs(Rd - dv) > max(5.0, 0.03 * dv): dbad = True; break
                if not dbad: matches.append((c, n_match, score))
        rec = dict(fiscal_year=fy, table_seq=det[0]['table_seq'], block_id=det[0]['block_id'],
                   row_seq_first=det[0]['row_seq'], row_seq_last=det[-1]['row_seq'], article=det[0]['article'],
                   section=sec, provinces=';'.join(provs), value_efc=round(segval(det), 2),
                   n_candidates=len(matches), candidates=';'.join(m[0] for m in matches), inferred='', evidence='')
        if len(matches) == 1:
            c, n_match, score = matches[0]
            rec['inferred'] = names[(fy, c)]; rec['evidence'] = f'{n_match} province(s) match, sum|dev|={score:.0f}'
            # apply and update the parsed sums so later segments see the corrected residuals
            for x in rows[i:j]:
                if x['country'] == '?':
                    x['country'] = names[(fy, c)]; x['country_inferred'] = '2'
                    x['flags'] = (x['flags'] + ',' if x['flags'] else '') + 'abstract_inferred'
            for p in provs:
                P[(fy, c, p)][sec] += by_prov[p]['efc']; P[(fy, c, p)]['duty'] += by_prov[p]['duty']
            applied += 1
        out.append(rec)
    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()) if out else ['fiscal_year'])
        w.writeheader(); w.writerows(out)
    tot = sum(r['value_efc'] for r in out); inf = sum(r['value_efc'] for r in out if r['inferred'])
    amb = sum(r['value_efc'] for r in out if r['n_candidates'] > 1)
    print(f"segments {len(out)} (efc {tot:,.0f}); inferred {applied} ({inf:,.0f}); ambiguous {sum(1 for r in out if r['n_candidates'] > 1)} ({amb:,.0f}); "
          f"no match {sum(1 for r in out if r['n_candidates'] == 0)}")
    if not dry:
        with open(ROWS, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
        print('applied to', ROWS)
    for r in sorted(out, key=lambda r: -r['value_efc'])[:30]:
        print(f"  {r['fiscal_year']} t{r['table_seq']} b{r['block_id']} {r['value_efc']:>12,.0f} {r['section']:4s} {r['provinces'][:40]:40s} -> {r['inferred'] or '(' + str(r['n_candidates']) + ': ' + r['candidates'][:50] + ')'}  {str(r['article'])[:40]}")


if __name__ == '__main__':
    main()
