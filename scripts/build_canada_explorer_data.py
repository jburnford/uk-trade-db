#!/usr/bin/env python3
"""Data for the UK->Canada commodity explorer.

COVERS BOTH FLOWS. What Canada recorded as imports from the United Kingdom is
the sum of two things the Statement keeps in separate tables:

  export_uk  exports of British and Irish PRODUCE
  reexport   colonial and foreign goods landed in Britain and shipped on

Showing only the first loses GBP31.9M for Canada, and loses tea entirely -- tea
is not British produce, so it appears only as a re-export, where at GBP14.1M
over 24 years it is larger than every British-produce commodity except woollens,
iron and cotton. The same is true of the rest of the colonial basket: fruit,
spices, coffee, rice, wine, silk, hemp.

Commodities are kept separate per flow rather than summed, because
"TEA (re-export)" and a same-named British-produce line are different goods
moving for different reasons.

Applies, in this order:
  * own-year witnesses only (a volume is primary for its MAXIMUM year, so the
    1897-99 comparative reprints do not triple-count the mid-1890s)
  * the group-name folds from reference/group_name_folds.csv, so one printed
    heading is one commodity rather than up to eight
  * the fused-cell repairs from reference/export_cell_repairs.csv, keyed on the
    bad value so a correction can only replace the number it came from
  * the section-capture reassignments from reference/group_reassign.csv, which
    move a captured article back to the group it belongs to (as_1898/99 filed
    the whole wool section under WOOD AND TIMBER)

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
    # the WOOD/WOOL capture is REPAIRED (reference/group_reassign.csv); what is
    # left under WOOD in 1899 is phantom-region rows, a different defect
    'WOOD AND TIMBER': [
        (1898, 1899, 'residual: still holds "West Africa" rows filed as an '
                     'article name; the wool capture itself is now repaired')],
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


def load_reassign(path, flow):
    if not os.path.exists(path):
        return {}
    return {(r['volume'], r['from_group'], r['article']): r['to_group']
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
    ap.add_argument('--flows', default='export_uk,reexport')
    ap.add_argument('--out', default='reports/canada_explorer.json')
    a = ap.parse_args()

    fix = load_repairs('reference/export_cell_repairs.csv')
    con = duckdb.connect(a.db, read_only=True)
    flows = [f.strip() for f in a.flows.split(',') if f.strip()]

    blocks = collections.defaultdict(list)
    n_fixed = 0
    folds = {}
    reassign = {}
    n_moved = 0
    for flow in flows:
        folds[flow] = load_folds('reference/group_name_folds.csv', flow)
        reassign[flow] = load_reassign('reference/group_reassign.csv', flow)
        rows = con.execute("""
            select volume, year, coalesce(article_group,'') ag,
                   coalesce(article,'') art, coalesce(unit,'') unit,
                   row_seq, country_raw, value
            from country_obs where flow = ?
            order by volume, ag, art, unit, row_seq
        """, [flow]).fetchall()
        for vol, yr, ag, art, unit, sq, ctry, val in rows:
            if val is not None:
                nv = fix.get((vol, ag, art, ctry, round(val)))
                if nv is not None:
                    val, n_fixed = nv, n_fixed + 1
            blocks[(flow, vol, yr, ag, art, unit)].append((ctry, val))

    # own-year is per flow: a volume is primary for the max year it carries
    own = {}
    for (flow, vol, yr, *_) in blocks:
        own[(flow, vol)] = max(own.get((flow, vol), 0), yr)

    # (flow, commodity) -> year -> [value, cells, proven_value]
    series = collections.defaultdict(lambda: collections.defaultdict(
        lambda: [0.0, 0, 0.0]))
    for (flow, vol, yr, ag, art, unit), rws in blocks.items():
        if own.get((flow, vol)) != yr:
            continue
        tgt = reassign[flow].get((vol, ag, art))
        if tgt:
            n_moved += 1
        canon = (folds[flow].get(tgt or ag, tgt or ag) or '(no group)')
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
                cell = series[(flow, canon)][yr]
                cell[0] += val
                cell[1] += 1
                if exact:
                    cell[2] += val

    years = list(range(1870, 1901))
    out = {'years': years, 'flows': flows,
           'bad_years': {'1871': 'no volume covers this year',
                         '1897': 'page-edge digit loss', '1898': 'page-edge digit loss',
                         '1899': 'page-edge digit loss', '1900': 'page-edge digit loss'},
           'commodities': []}
    for (flow, name), byyear in series.items():
        vals = [round(byyear[y][0]) if y in byyear else None for y in years]
        prov = [round(100 * byyear[y][2] / byyear[y][0]) if y in byyear and byyear[y][0]
                else (0 if y in byyear else None) for y in years]
        seen = [y for y in years if y in byyear]
        if not seen:
            continue
        out['commodities'].append({
            'name': name, 'flow': flow, 'v': vals, 'p': prov,
            'total': round(sum(x for x in vals if x)),
            'years': len(seen),
            'issues': [{'y0': y0, 'y1': y1, 'text': tx}
                       for y0, y1, tx in (ISSUES.get(name, [])
                                          if flow == 'export_uk' else [])]})
    out['commodities'].sort(key=lambda c: -c['total'])

    json.dump(out, open(a.out, 'w'), separators=(',', ':'))
    byflow = collections.Counter(c['flow'] for c in out['commodities'])
    print(f'commodities: {len(out["commodities"]):,}   '
          f'fused-cell repairs applied: {n_fixed}   '
          f'capture reassignments applied: {n_moved} blocks')
    for f in flows:
        v = sum(c['total'] for c in out['commodities'] if c['flow'] == f)
        print(f'   {f:>10}: {byflow[f]:>4} commodities, GBP {v:,}')
    print(f'with 20+ years: {sum(1 for c in out["commodities"] if c["years"] >= 20)}')
    print(f'total value: GBP {sum(c["total"] for c in out["commodities"]):,}')
    print(f'wrote {a.out}')


if __name__ == '__main__':
    main()
