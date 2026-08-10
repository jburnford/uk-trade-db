#!/usr/bin/env python3
"""Data for the UK->Canada commodity explorer.

Applies, in this order:
  * own-year witnesses only (a volume is primary for its MAXIMUM year, so the
    1897-99 comparative reprints do not triple-count the mid-1890s)
  * the group-name folds from reference/group_name_folds.csv, so one printed
    heading is one commodity rather than up to eight
  * the fused-cell repairs from reference/export_cell_repairs.csv, keyed on the
    bad value so a correction can only replace the number it came from

Per commodity-year it emits the value, the number of contributing cells, and the
share of value sitting in a printed section that closes exactly -- the
corroboration measure that stands in for a gold set on the export side.

Known-bad years are marked so the chart can show them rather than hide them:
1871 has no volume at all, and 1897-1900 come from wide comparative tables whose
right-hand column loses digits at the page edge.

Usage:
    python3 scripts/build_canada_explorer_data.py [--out reports/canada_explorer.json]
"""
import argparse, collections, csv, json, os, re
import duckdb

TOTAL_RE = re.compile(r'\bTOTAL\b', re.I)
CANADA = ('British North America', 'Canada', 'Newfoundland')

# Defects found but NOT yet repaired, surfaced on the chart so a reader is not
# quietly misled by a series the project already knows is wrong.
ISSUES = {
    'WOOD AND TIMBER': [
        (1898, 1899, 'holds the whole WOOL section: this is woollens, not wood')],
    'WOOLLEN AND WORSTED MANUFACTURES': [
        (1898, 1899, 'understated: its rows were captured by WOOD AND TIMBER')],
    'GLASS': [(1886, 1895, 'holds GREASE, TALLOW AND ANIMAL FAT as an article')],
    'COTTON MANUFACTURES': [
        (1882, 1882, 'Thread for Sewing reads GBP605,600 at 20x its usual unit '
                     'price; ~GBP575k of this year is that one cell'),
        (1883, 1883, 'much of this year sits under an article named '
                     '"United States" - a destination read as a commodity')],
    'IMPLEMENTS AND TOOLS': [
        (1897, 1899, 'holds iron and steel articles, and 2,180 rows of '
                     '"West Africa" as an article name')],
}


def is_total(s):
    return bool(s) and bool(TOTAL_RE.search(s))


def load_folds(path, flow):
    if not os.path.exists(path):
        return {}
    return {r['raw_group']: r['canonical']
            for r in csv.DictReader(open(path)) if r['flow'] == flow}


def load_repairs(path):
    if not os.path.exists(path):
        return {}
    return {(r['volume'], r['article_group'], r['article'], r['country_raw'],
             round(float(r['old_value']))): float(r['new_value'])
            for r in csv.DictReader(open(path))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='db/uk_trade.duckdb')
    ap.add_argument('--flow', default='export_uk')
    ap.add_argument('--out', default='reports/canada_explorer.json')
    a = ap.parse_args()

    fold = load_folds('reference/group_name_folds.csv', a.flow)
    fix = load_repairs('reference/export_cell_repairs.csv')
    con = duckdb.connect(a.db, read_only=True)

    rows = con.execute("""
        select volume, year, coalesce(article_group,'') ag, coalesce(article,'') art,
               coalesce(unit,'') unit, row_seq, country_raw, value
        from country_obs where flow = ?
        order by volume, ag, art, unit, row_seq
    """, [a.flow]).fetchall()

    blocks = collections.defaultdict(list)
    n_fixed = 0
    for vol, yr, ag, art, unit, sq, ctry, val in rows:
        if val is not None:
            nv = fix.get((vol, ag, art, ctry, round(val)))
            if nv is not None:
                val, n_fixed = nv, n_fixed + 1
        blocks[(vol, yr, ag, art, unit)].append((ctry, val))

    own = {}
    for (vol, yr, *_) in blocks:
        own[vol] = max(own.get(vol, 0), yr)

    # commodity -> year -> [value, cells, proven_value]
    series = collections.defaultdict(lambda: collections.defaultdict(
        lambda: [0.0, 0, 0.0]))
    for (vol, yr, ag, art, unit), rws in blocks.items():
        if own.get(vol) != yr:
            continue
        canon = fold.get(ag, ag) or '(no group)'
        sect, buf = [], []
        for ctry, val in rws:
            if is_total(ctry):
                if buf:
                    sect.append((buf, val))
                buf = []
            elif val is not None:
                buf.append((ctry, val))
        if buf:
            sect.append((buf, None))
        for members, printed in sect:
            exact = False
            if printed:
                tot = sum(v for _, v in members)
                exact = abs(tot - printed) <= 0.001 * abs(printed)
            for ctry, val in members:
                if ctry not in CANADA:
                    continue
                cell = series[canon][yr]
                cell[0] += val
                cell[1] += 1
                if exact:
                    cell[2] += val

    years = list(range(1870, 1901))
    out = {'years': years, 'flow': a.flow,
           'bad_years': {'1871': 'no volume covers this year',
                         '1897': 'page-edge digit loss', '1898': 'page-edge digit loss',
                         '1899': 'page-edge digit loss', '1900': 'page-edge digit loss'},
           'commodities': []}
    for name, byyear in series.items():
        vals = [round(byyear[y][0]) if y in byyear else None for y in years]
        prov = [round(100 * byyear[y][2] / byyear[y][0]) if y in byyear and byyear[y][0]
                else (0 if y in byyear else None) for y in years]
        seen = [y for y in years if y in byyear]
        if not seen:
            continue
        out['commodities'].append({
            'name': name, 'v': vals, 'p': prov,
            'total': round(sum(x for x in vals if x)),
            'years': len(seen),
            'issues': [{'y0': y0, 'y1': y1, 'text': tx}
                       for y0, y1, tx in ISSUES.get(name, [])]})
    out['commodities'].sort(key=lambda c: -c['total'])

    json.dump(out, open(a.out, 'w'), separators=(',', ':'))
    print(f'commodities: {len(out["commodities"]):,}   '
          f'fused-cell repairs applied: {n_fixed}')
    print(f'with 20+ years: {sum(1 for c in out["commodities"] if c["years"] >= 20)}')
    print(f'total value: GBP {sum(c["total"] for c in out["commodities"]):,}')
    print(f'wrote {a.out}')


if __name__ == '__main__':
    main()
