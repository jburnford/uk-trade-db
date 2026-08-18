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
  * the positional capture repairs from reference/capture_reassign.csv
    (build_capture_reassign.py): a lost heading files the next section(s)
    under the previous group -- IMPLEMENTS AND TOOLS holding all of IRON AND
    STEEL, LEAD holding LEATHER, LINEN and MACHINERY in 1897-99 -- and the
    articles are put back by aligning the captor's print order onto as_1896's
  * the family table reference/export_group_families.csv: era wordings, OCR
    variants and continuation suffixes of one heading become one commodity
    (IRON + IRON AND STEEL, seven spellings of CAOUTCHOUC, "...'d)" pages)
  * the fused-section splits from reference/fused_section_splits.csv
    (build_fused_splits.py): one block holding two or more complete TOTAL
    hierarchies because a heading was lost with no article marker -- GLASS
    'GREASE, TALLOW...' holding all of HABERDASHERY 1886-94, BAGS AND SACKS
    holding BEER AND ALE in as_1897/98, PAPER holding PICKLES 1897-1900 --
    and the second hierarchy takes the heading the reference volume prints
    next; keyed on the raw parse and a row_seq range, applied first
  * the phantom-region relabel (scripts/phantom_articles.py): 'West Africa' /
    'East Africa' / 'Dutch Possessions in Indian Seas' as an ARTICLE is a
    printed country sub-heading the parser absorbed; the rows go back to the
    article above them, which is what lets their printed TOTALs close
  * suppression of printed SUBTOTAL lines ingested as article names -- but only
    where the components they total are also present (see below)

SUBTOTAL ROWS INGESTED AS ARTICLES
----------------------------------
The Statement prints 'Total of all kinds' under a commodity that has sub-sorts,
and the parser sometimes stores that as the ARTICLE name against a real
destination. Summing it beside its own components double-counts. Tea re-exported
to Canada in 1896 read GBP5,042,495 against a steady GBP300-500k for that reason
-- and the offending row's 'value' was in fact the quantity in Lbs (4,842,458),
so it was both a duplicate and a column shift.

3,364 such rows exist across the three flows. They are NOT dropped wholesale:
993 of them are the only reading for their commodity-year-destination, because
the component lines did not parse, and dropping those would be data loss. A
subtotal row is suppressed only when at least one non-subtotal row exists for
the same (volume, year, group, destination). That leaves 2,371 suppressed,
GBP246.5M of double counting, and keeps the 993 that carry real information.

Per commodity-year it emits the value, the number of contributing cells, and the
share of value sitting in a printed section that closes exactly -- the
corroboration measure that stands in for a gold set on the export side.

Known-bad years are marked so the chart can show them rather than hide them:
1871 has no volume at all, and 1897-1900 come from wide comparative tables whose
right-hand column loses digits at the page edge.

Usage:
    python3 scripts/build_canada_explorer_data.py [--out reports/canada_explorer.json]
"""
import argparse, collections, csv, json, os, re, sys
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phantom_articles import (fix_articles, known_groups, promote_headings,
                              load_splits, apply_splits)

TOTAL_RE = re.compile(r'\bTOTAL\b', re.I)

# Per-year primary-witness OVERRIDE. A volume's own maximum year sits in the
# damaged page-edge column of the ten-column comparative layout, so for 1897
# and 1898 the volume-of-record is the WORST witness: measured closure says
# as_1899's mid-table reprint columns corroborate roughly 3x more value than
# the vote-repaired edge columns (Canada 1897: 22.0% of value against 2.1%).
# Those years are therefore read from as_1899. 1899 stays on as_1899's own
# edge column -- the one reprint, tn_1901's mid-table 1899 column
# (parse_tn_overlap.py -> country_obs_tn), closes no better and is a
# different publication whose headings align poorly, so it serves as a
# WITNESS to repair as_1899 (repair_edge_columns.py, repair_section_closure.py)
# rather than as the primary.
PRIMARY_OVERRIDE = {1897: 'as_1899', 1898: 'as_1899'}
# an ARTICLE name that is really a printed subtotal line
SUBTOTAL_ART = re.compile(r'^\s*(total|sum|grand total)\b', re.I)
CANADA = ('British North America', 'Canada', 'Newfoundland')

# Defects found but NOT yet repaired, surfaced on the chart so a reader is not
# quietly misled by a series the project already knows is wrong.
ISSUES = {
    # keys are FAMILY names (after folds and export_group_families.csv)
    # (GREASE / HABERDASHERY 1886-91, 1894 and GLASS 1887 -- the fused
    # HABERDASHERY section -- were repaired by build_fused_splits.py)
    'TELEGRAPHIC WIRES AND APPARATUS': [
        (1884, 1884, 'GBP1.03M in a single block: not yet checked against '
                     'the printed page'),
        (1894, 1894, 'GBP0.85M in a single block: not yet checked against '
                     'the printed page')],
    'COTTON MANUFACTURES': [
        (1882, 1882, 'Thread for Sewing reads GBP605,600 at 20x its usual unit '
                     'price; ~GBP575k of this year is that one cell'),
        (1883, 1883, 'much of this year sits under an article named '
                     '"United States" - a destination read as a commodity')],
}


def is_total(s):
    return bool(s) and bool(TOTAL_RE.search(s))


def load_folds(path, flow):
    if not os.path.exists(path):
        return {}
    return {r['raw_group']: r['canonical']
            for r in csv.DictReader(open(path)) if r['flow'] == flow}


def load_reassign(paths, flow):
    out = {}
    for path in paths:
        if not os.path.exists(path):
            continue
        for r in csv.DictReader(open(path)):
            if r['flow'] == flow:
                out[(r['volume'], r['from_group'], r['article'])] = r['to_group']
    return out


def load_families(path, flow):
    """Era wordings, OCR variants and continuation suffixes of one printed
    heading -> one family label (reference/export_group_families.csv), applied
    after the group-name folds. IRON (to 1890) and IRON AND STEEL (from 1891)
    are one series; CAOUTCHOUC has seven spellings; "IRON AND STEEL'd)" is a
    page continuation."""
    if not os.path.exists(path):
        return {}
    return {r['canonical']: r['family']
            for r in csv.DictReader(open(path)) if r['flow'] == flow}


NO_REPAIR = object()


def load_repairs(paths):
    # blank new_value = null-out: malformed cell with no witness, drop it
    out = {}
    for path in paths:
        if not os.path.exists(path):
            continue
        for r in csv.DictReader(open(path)):
            out[(r['volume'], int(r['year']), r['article_group'], r['article'],
                 r['country_raw'], round(float(r['old_value'])))] = (
                float(r['new_value']) if r['new_value'] != '' else None)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='db/uk_trade.duckdb')
    ap.add_argument('--flows', default='export_uk,reexport')
    ap.add_argument('--out', default='reports/canada_explorer.json')
    a = ap.parse_args()

    fix = load_repairs(('reference/export_cell_repairs.csv',
                        'reference/malformed_cell_repairs.csv',
                        'reference/edge_column_repairs.csv',
                'reference/section_closure_repairs.csv'))
    con = duckdb.connect(a.db, read_only=True)
    flows = [f.strip() for f in a.flows.split(',') if f.strip()]

    blocks = collections.defaultdict(list)
    subtotal_keys, component_keys = {}, set()
    n_fixed = 0
    folds = {}
    reassign = {}
    families = {}
    n_moved = 0
    n_sub = 0
    for flow in flows:
        folds[flow] = load_folds('reference/group_name_folds.csv', flow)
        reassign[flow] = load_reassign(('reference/group_reassign.csv',
                                        'reference/capture_reassign.csv'), flow)
        families[flow] = load_families('reference/export_group_families.csv',
                                       flow)
        rows = con.execute("""
            select volume, flow, year, coalesce(article_group,'') ag,
                   article, unit, row_seq, country_raw, value
            from country_obs where flow = ?
        """, [flow]).fetchall()
        # phantom-region relabel (phantom_articles.py): 'West Africa' as an
        # article is an absorbed heading; the row belongs to the article
        # above. Repairs are keyed on the RAW parse: look up, then relabel.
        # fused sections first (build_fused_splits.py): the second TOTAL
        # hierarchy inside a block takes the heading the reference prints
        # next -- keyed on the raw parse and a row_seq range
        split = apply_splits(rows, load_splits(flow=flow), vol=0, flow=1,
                             year=2, group=3, art=4, seq=6, unit=5)
        fixed = fix_articles(split, vol=0, flow=1, year=2, group=3, art=4,
                             unit=5, seq=6)
        # then a lost heading stored as the ARTICLE becomes its own group
        # (GLASS holding 'GREASE, TALLOW, AND ANIMAL FAT' 1886-94)
        fixed = promote_headings(fixed, known_groups(con, flow), vol=0,
                                 flow=1, year=2, group=3, art=4)
        for r, f in zip(rows, fixed):
            vol, _, yr, ag, art, unit, sq, ctry, val = r
            if val is not None:
                nv = fix.get((vol, yr, ag, art or '', ctry, round(val)),
                             NO_REPAIR)
                if nv is not NO_REPAIR:
                    val, n_fixed = nv, n_fixed + 1   # None = null-out
            ag, art, unit = f[3], f[4] or '', f[5] or ''
            blocks[(flow, vol, yr, ag, art, unit)].append((sq, ctry, val))
            if val is not None and ctry and not TOTAL_RE.search(ctry):
                k = (flow, vol, yr, ag, ctry)
                if SUBTOTAL_ART.match(art or ''):
                    subtotal_keys.setdefault(k, []).append((ag, art, unit, ctry))
                else:
                    component_keys.add(k)

    for k in blocks:
        blocks[k].sort(key=lambda t: t[0] if t[0] is not None else -1)
        blocks[k] = [(c, v) for _, c, v in blocks[k]]

    # own-year is per flow: a volume is primary for the max year it carries
    own = {}
    for (flow, vol, yr, *_) in blocks:
        own[(flow, vol)] = max(own.get((flow, vol), 0), yr)

    # (flow, commodity) -> year -> [value, cells, proven_value]
    series = collections.defaultdict(lambda: collections.defaultdict(
        lambda: [0.0, 0, 0.0]))
    for (flow, vol, yr, ag, art, unit), rws in blocks.items():
        primary = (vol == PRIMARY_OVERRIDE[yr] if yr in PRIMARY_OVERRIDE
                   else own.get((flow, vol)) == yr)
        if not primary:
            continue
        tgt = reassign[flow].get((vol, ag, art))
        if tgt:
            n_moved += 1
        canon = (folds[flow].get(tgt or ag, tgt or ag) or '(no group)')
        canon = families[flow].get(canon, canon)
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
                if (SUBTOTAL_ART.match(art or '')
                        and (flow, vol, yr, ag, ctry) in component_keys):
                    n_sub += 1
                    continue          # its own components are present; skip
                cell = series[(flow, canon)][yr]
                cell[0] += val
                cell[1] += 1
                if exact:
                    cell[2] += val

    years = list(range(1870, 1901))
    out = {'years': years, 'flows': flows,
           'bad_years': {'1871': 'no volume covers this year',
                         '1897': 'read from the as_1899 reprint, repaired '
                                 'against as_1898/tn_1899/tn_1901; ~39% of '
                                 'value page-corroborated',
                         '1898': 'read from the as_1899 reprint, repaired '
                                 'against tn_1901; ~40% page-corroborated',
                         '1899': 'as_1899 page-edge column, repaired against '
                                 'tn_1901 (the only reprint); ~32% '
                                 'page-corroborated',
                         '1900': 'tn_1901 page-edge column, no reprint '
                                 'anywhere; ~25% page-corroborated'},
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
    print(f'   subtotal-as-article rows suppressed: {n_sub}')
    for f in flows:
        v = sum(c['total'] for c in out['commodities'] if c['flow'] == f)
        print(f'   {f:>10}: {byflow[f]:>4} commodities, GBP {v:,}')
    print(f'with 20+ years: {sum(1 for c in out["commodities"] if c["years"] >= 20)}')
    print(f'total value: GBP {sum(c["total"] for c in out["commodities"]):,}')
    print(f'wrote {a.out}')


if __name__ == '__main__':
    main()
