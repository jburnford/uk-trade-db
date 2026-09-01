#!/usr/bin/env python3
"""Extract the printed by-country multi-year series from the prefatory tables of each Trade & Navigation
volume (e.g. 'No. 5.—Value of Goods Entered for Consumption by Countries', 'No. 6.—Duty Collected',
'No. 4.—Value of Exports by Countries', 'Aggregate Trade by Countries').  Two orientations occur:
years as columns (1873-1877 volumes) and countries as columns with years as rows (1880s volumes).

These are printed truth at country x year level and serve as the authority for the origin shares;
every volume re-prints earlier years, so the same (measure, year, country) is usually attested by
several volumes — all attestations are kept.

Output: reference/canada_country_series.csv
        measure, fiscal_year, country, value, source_volume, source_fy, table_seq
"""
import csv, re, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ca_profile as P
import ca_parse_imports as I

OUT = P.ROOT / 'reference' / 'canada_country_series.csv'
YEAR_RE = re.compile(r'\b(18[5-9]\d)\b')


def measure_of(text):
    t = text.lower()
    if 'aggregate' in t: return 'aggregate'
    if 'duty' in t or 'duties' in t: return 'duty'
    if 'entered for consumption' in t or 'consumption' in t: return 'efc'
    if 'export' in t: return 'exports'
    if 'import' in t: return 'imports'
    return None


def parse_volume(tag, fy, md_path, out):
    text = md_path.read_text(errors='replace')
    start = 0
    for mm in P.TN_START_RE2.finditer(text):
        if re.search(r'COMPILED\s+FROM\s+OFFICIAL\s+RETURNS', text[mm.start(): mm.start() + 1500], re.I):
            start = mm.start(); break
    tn = text[start:]
    pos = 0; n = 0; last_measure = None; last_orient = None
    for seq, tm in enumerate(P.TABLE_RE.finditer(tn)):
        inter = tn[pos:tm.start()]; pos = tm.end()
        title = P.title_context(inter)[-300:]
        if re.search(r'GENERAL STATEMENT', title, re.I):
            break                                   # prefatory matter ends at the first general statement
        rows = P.parse_table(tm.group(0))
        if len(rows) < 3: continue
        ths = [r for r in rows if all(k == 'th' for k, _, _ in r)]
        body = [r for r in rows if not all(k == 'th' for k, _, _ in r)]
        hdr_cells = [c for r in ths for _, _, c in r]
        hdr = ' | '.join(hdr_cells)
        first_col = [r[0][2] for r in body if r]
        # orientation
        years_in_hdr = [y for c in hdr_cells for y in YEAR_RE.findall(c)]
        years_in_col = [YEAR_RE.search(c).group(1) for c in first_col if YEAR_RE.search(c)]
        orient = None
        if len(years_in_hdr) >= 2 and re.search(r'countr', hdr, re.I):
            orient = 'years_cols'
        elif len(years_in_col) >= 3 and re.search(r'great britain|united states', hdr, re.I):
            orient = 'years_rows'
        elif len(years_in_col) >= 3 and last_orient == 'years_rows' and hdr_cells and not YEAR_RE.search(hdr):
            orient = 'years_rows'                   # continuation table (more countries), untitled
        if not orient:
            continue
        measure = measure_of(title + ' ' + hdr) or (last_measure if not title.strip() or orient == last_orient else None)
        if orient == 'years_cols' and not measure:
            measure = measure_of(' '.join(first_col[:2]))
        if not measure:
            continue
        n += 1; last_measure = measure; last_orient = orient
        if orient == 'years_cols':
            # header: label + years (possibly across two header rows); map column index -> year
            yrow = None
            for r in ths:
                ys = [YEAR_RE.search(c) for _, _, c in r]
                if sum(1 for y in ys if y) >= 2: yrow = [y.group(1) if y else None for y in ys]
            if not yrow: continue
            for r in body:
                cells = [c for _, _, c in r]
                if not cells or not cells[0].strip(): continue
                country = I.norm_label(cells[0])
                if not country or YEAR_RE.search(country): continue
                vals = cells[1:]
                # align values to years from the right
                yrs = [y for y in yrow if y]
                vals = vals[-len(yrs):] if len(vals) >= len(yrs) else vals
                for y, v in zip(yrs[-len(vals):], vals):
                    num, f = I.parse_num(v, cents_ok=(measure == 'duty'))
                    if num is not None:
                        out.append(dict(measure=measure, fiscal_year=y, country=country, value=num, source_volume=tag, source_fy=fy, table_seq=seq))
        else:
            # header row with country names; rows: year | values
            crow = None
            for r in ths:
                cs = [c for _, _, c in r]
                if re.search(r'great britain|united states|belgium|newfoundland|west indies', ' '.join(cs), re.I): crow = cs
            if not crow: continue
            names = [I.norm_label(c) for c in crow[1:] if c.strip() and not c.strip().startswith('$')]
            for r in body:
                cells = [c for _, _, c in r]
                if not cells: continue
                ym = YEAR_RE.search(cells[0])
                if not ym: continue
                y = ym.group(1); vals = cells[1:]
                vals = vals[-len(names):] if len(vals) >= len(names) else vals
                for nm, v in zip(names[-len(vals):], vals):
                    num, f = I.parse_num(v, cents_ok=(measure == 'duty'))
                    if num is not None:
                        out.append(dict(measure=measure, fiscal_year=y, country=nm, value=num, source_volume=tag, source_fy=fy, table_seq=seq))
    return n


def main():
    index = list(csv.DictReader(open(P.RAW / 'INDEX.tsv'), delimiter='\t'))
    out = []
    for row in index:
        tag = row['volume_tag']; fy = row['fiscal_year']
        if row.get('note', '').startswith('NOPARSE'): continue   # registered but pending its parser (INDEX.tsv note says which phase)
        md = P.RAW / tag / f'{tag}.md'
        if not md.exists(): continue
        if tag == 'oocihm.9_08052_13_10': continue          # not a T&N volume (railway returns); its tables are junk here
        before = len(out)
        n = parse_volume(tag, fy, md, out)
        yrs = sorted(set(r['fiscal_year'] for r in out[before:]))
        print(f'{fy:8} {tag:24} tables={n:2} rows={len(out)-before:5} years {yrs[0] if yrs else ""}-{yrs[-1] if yrs else ""} measures {sorted(set(r["measure"] for r in out[before:]))}', file=sys.stderr)
    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['measure', 'fiscal_year', 'country', 'value', 'source_volume', 'source_fy', 'table_seq']); w.writeheader()
        for r in out: w.writerow(r)
    print(f'wrote {OUT} ({len(out)} rows)', file=sys.stderr)
    # majority vote across attestations (same measure/year/country key); country names normalised lightly
    def ck(c):
        c = re.sub(r'[^A-Za-z ]', '', c).strip().lower(); c = re.sub(r'\s+', ' ', c)
        c = c.replace('new foundland', 'newfoundland').replace('newfound land', 'newfoundland')
        return c
    from collections import defaultdict
    votes = defaultdict(list)
    for r in out:
        if r['value'] < 100 and r['measure'] != 'duty': continue        # junk fragments
        votes[(r['measure'], r['fiscal_year'], ck(r['country']))].append((r['value'], r['source_fy']))
    OUTV = OUT.with_name('canada_country_series_voted.csv')
    with open(OUTV, 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['measure', 'fiscal_year', 'country', 'value', 'n_attest', 'n_agree', 'sources'])
        for k in sorted(votes):
            vs = votes[k]; c = Counter(v for v, _ in vs); val, n = c.most_common(1)[0]
            # prefer the latest volume on ties
            if list(c.values()).count(n) > 1:
                val = max((v for v, s in vs if c[v] == n), key=lambda v: max(s for vv, s in vs if vv == v))
            w.writerow([k[0], k[1], k[2], val, len(vs), n, ';'.join(sorted(set(s for _, s in vs)))])
    print(f'wrote {OUTV} ({len(votes)} keys)', file=sys.stderr)


if __name__ == '__main__':
    main()
