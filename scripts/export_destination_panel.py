#!/usr/bin/env python3
"""Comparable UK-export series per destination, 1870-1900.

Puts Canada on the same axis as Australasia, British India, the United States
and the rest, so a Canadian trend can be read against its peers rather than in
isolation. Four things have to be right for that comparison to mean anything:

1. WITNESS. The 1897-99 volumes reprint up to five prior years. Only the
   volume's own year is counted (a volume is primary for its MAXIMUM year;
   tn_1871 is primary for 1870 and tn_1901 for 1900). Summing across volumes
   triple-counts the mid-1890s.
2. VOCABULARY. Labels are canonicalised through scripts/countrykey.py and then
   rolled to their root, so `British North America` (to 1896) and
   `Canada` + `Newfoundland` (from 1897) are one series, and the Australasian
   colonies do not fragment the Australasian one.
3. DOUBLE COUNTING. Within a printed section the compositor lists a partition.
   Where a fused block leaves both a node and its own ancestor inside one
   section, the ancestor is dropped and the finer partition kept.
4. CORROBORATION. Each cell inherits the closure verdict of the printed section
   it sits in, so every published figure carries the share of its value that the
   page itself proves.

Coverage warning: article coverage per destination-year is NOT constant (Canada
carries 107 articles in 1896 and 42 in 1897), so a fall in a destination's total
can be a fall in what the parser recovered. `articles` is reported beside every
figure and must be read with it.

Usage:
    python3 scripts/export_destination_panel.py [--flow export_uk]
        [--top 14] [--out reports/export_destination_panel.csv]
"""
import argparse, collections, csv, re, sys
import duckdb

sys.path.insert(0, __file__.rsplit('/', 1)[0])
import countrykey
from phantom_articles import fix_articles, load_splits, apply_splits

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


def is_total(s):
    return bool(s) and bool(TOTAL_RE.search(s))


def verdict(members, printed):
    if not printed:
        return None
    d = abs(sum(members) - printed) / abs(printed)
    return 'exact01' if d <= 0.001 else ('within5' if d <= 0.05 else 'off')


REPAIR_FILES = ('reference/export_cell_repairs.csv',
                'reference/malformed_cell_repairs.csv',
                'reference/edge_column_repairs.csv',
                'reference/row_slip_repairs.csv',
                'reference/scaled_block_repairs.csv',
                'reference/section_closure_repairs.csv')
NO_REPAIR = object()


def load_repairs(paths=REPAIR_FILES):
    """Provenance-safe overlay of repair_fused_cells.py and
    repair_malformed_cells.py corrections.

    Keyed on the BAD value as well as the coordinates, so a correction can only
    ever replace the exact number it was derived from. If the parse changes
    upstream the key stops matching and the repair drops out rather than
    silently overwriting a different figure. A BLANK new_value is a null-out:
    the cell is malformed with no witness anywhere and must be dropped, not
    trusted.
    """
    import csv as _csv, os as _os
    out = {}
    for path in paths:
        if not _os.path.exists(path):
            continue
        for r in _csv.DictReader(open(path)):
            out[(r['volume'], int(r['year']), r['article_group'], r['article'],
                 r['country_raw'], round(float(r['old_value'])))] = (
                float(r['new_value']) if r['new_value'] != '' else None)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='db/uk_trade.duckdb')
    ap.add_argument('--flow', default='export_uk',
                    choices=['export_uk', 'reexport', 'import'])
    ap.add_argument('--top', type=int, default=14)
    ap.add_argument('--out', default='reports/export_destination_panel.csv')
    a = ap.parse_args()

    ck = countrykey.load()
    con = duckdb.connect(a.db, read_only=True)
    rows = con.execute("""
        select volume, flow, year, coalesce(article_group,'') ag, article,
               unit, row_seq, country_raw, value
        from country_obs where flow = ?
    """, [a.flow]).fetchall()
    # phantom-region relabel (phantom_articles.py): 'West Africa' as an
    # article is an absorbed heading; the row belongs to the article above.
    # Repairs are keyed on the RAW parse, so look them up before relabelling.
    fixed = fix_articles(apply_splits(rows, load_splits(flow=a.flow), vol=0,
                                      flow=1, year=2, group=3, art=4, seq=6, unit=5),
                         vol=0, flow=1, year=2, group=3, art=4, unit=5, seq=6)

    fix = load_repairs()
    n_fixed = 0
    blocks = collections.defaultdict(list)
    for r, f in zip(rows, fixed):
        vol, _, yr, ag, art, unit, sq, ctry, val = r
        if val is not None:
            nv = fix.get((vol, yr, ag, art or '', ctry, round(val)), NO_REPAIR)
            if nv is not NO_REPAIR:
                val, n_fixed = nv, n_fixed + 1   # None = null-out, dropped
        blocks[(vol, yr, ag, f[4] or '', f[5] or '')].append((sq, ctry, val))
    for k in blocks:
        blocks[k].sort(key=lambda t: t[0] if t[0] is not None else -1)
        blocks[k] = [(c, v) for _, c, v in blocks[k]]
    own = {}
    for (vol, yr, *_) in blocks:
        own[vol] = max(own.get(vol, 0), yr)

    # destination -> year -> [value, cells, proven_value, articles]
    panel = collections.defaultdict(lambda: collections.defaultdict(
        lambda: [0.0, 0, 0.0, set()]))
    # Only nodes the gazetteer actually declares are admitted. Everything else
    # is an id invented by titlecasing, and those are not merely obscure places
    # -- they include column headers ingested as destinations ('Piece Goods
    # . . . . . Yards', bare years) carrying GBP80M+ apiece, which outrank every
    # real destination on any value ranking. They are counted and reported as a
    # single residual instead of being allowed to pose as countries.
    known_ids = set(ck.alias.values()) | set(ck.parent) | set(ck.parent.values())
    dropped = [0.0, 0]

    for (vol, yr, ag, art, unit), rws in blocks.items():
        primary = (vol == PRIMARY_OVERRIDE[yr] if yr in PRIMARY_OVERRIDE
                   else own.get(vol) == yr)
        if not primary:
            continue                      # comparative reprint: not a witness
        sect, buf = [], []
        for ctry, val in rws:
            if is_total(ctry):
                if buf:
                    sect.append((buf, val))
                buf = []
            elif val is not None:
                buf.append((ctry, val))
        if buf:
            # members after the last printed TOTAL have no anchor; they still
            # belong in the series, they just cannot be proven. Dropping them
            # silently understates a destination-year (Canada 1897 read 1.61M
            # against 4.78M) and would look like a collapse in the data.
            sect.append((buf, None))
        for members, printed in sect:
            v = verdict([m[1] for m in members], printed)
            # Resolve, then decide parent-vs-children ARITHMETICALLY. Being an
            # ancestor in the gazetteer is not evidence of double counting: the
            # 1897-1900 tables print Canada and Newfoundland as two sibling
            # destinations, and the gazetteer declares Newfoundland a child of
            # Canada, so a blanket ancestor-drop deletes Canada's own cells and
            # reads 1.61M where the printed page says 4.78M.
            # A parent is only dropped when its value actually looks like the
            # sum of the children present beside it (within 5%), which is what
            # a genuine parent-plus-breakdown double count looks like.
            resolved = [(ck.key(c)[0], val) for c, val in members]
            byid = collections.defaultdict(float)
            for cid, val in resolved:
                byid[cid] += val
            redundant = set()
            for cid, pval in byid.items():
                kids = [v for o, v in byid.items()
                        if o != cid and ck.is_ancestor(cid, o)]
                if kids and pval > 0 and abs(sum(kids) - pval) <= 0.05 * pval:
                    redundant.add(cid)
            keep = [(cid, val) for cid, val in resolved if cid not in redundant]
            for cid, val in keep:
                if cid == countrykey.DROP:
                    continue
                if cid not in known_ids and cid != countrykey.RESIDUAL:
                    dropped[0] += val
                    dropped[1] += 1
                    continue
                root = (ck.ancestors(cid) or [cid])[-1]
                cell = panel[root][yr]
                cell[0] += val
                cell[1] += 1
                if v == 'exact01':
                    cell[2] += val
                cell[3].add(f'{ag}|{art}')

    recs = []
    for dest, byyear in panel.items():
        for yr, (val, n, proven, arts) in byyear.items():
            recs.append(dict(destination=dest, year=yr, value=round(val),
                             cells=n, articles=len(arts),
                             proven_value=round(proven),
                             proven_share=round(100 * proven / val, 1) if val else 0))
    recs.sort(key=lambda r: (r['destination'], r['year']))

    # rank on the MEDIAN annual value, not the total: a single fused-digit cell
    # puts a destination in the GBP billions (1874 alone reads GBP42,523M for
    # the United States) and a total-based ranking just sorts by corruption
    import statistics
    med = {d: statistics.median([v[0] for v in yrs.values()])
           for d, yrs in panel.items() if yrs}
    top = sorted(med, key=med.get, reverse=True)[:a.top]

    print(f'flow={a.flow}   own-year witnesses only   '
          f'destinations={len(panel)}   rows={len(recs):,}')
    print(f'excluded as unresolved labels: {dropped[1]:,} cells, '
          f'GBP {dropped[0]:,.0f}')
    print(f'fused-cell repairs applied: {n_fixed}')
    print(f'\ntop {a.top} destinations by MEDIAN annual value')
    print(f'{"destination":>34} {"median/yr":>14} {"years":>6} {"proven%":>8}')
    for d in top:
        yrs = panel[d]
        pv = sum(v[2] for v in yrs.values())
        tv = sum(v[0] for v in yrs.values())
        print(f'{d[:34]:>34} {med[d]:>14,.0f} {len(yrs):>6} '
              f'{100*pv/tv if tv else 0:>7.1f}%')

    print(f'\nannual series, GBP (proven share in brackets) — '
          f'articles in the second table')
    hdr = [d[:11] for d in top[:7]]
    print(f'{"yr":>4} ' + ' '.join(f'{h:>15}' for h in hdr))
    for yr in sorted({r['year'] for r in recs}):
        cells = []
        for d in top[:7]:
            e = panel[d].get(yr)
            cells.append(f'{e[0]/1e6:>8.2f}M[{e[2]/e[0]*100 if e[0] else 0:>3.0f}]'
                         if e else f'{"-":>15}')
        print(f'{yr:>4} ' + ' '.join(f'{c:>15}' for c in cells))

    print(f'\narticles recovered per destination-year')
    print(f'{"yr":>4} ' + ' '.join(f'{h:>11}' for h in hdr))
    for yr in sorted({r['year'] for r in recs}):
        cells = [str(panel[d][yr][3].__len__()) if yr in panel[d] else '-'
                 for d in top[:7]]
        print(f'{yr:>4} ' + ' '.join(f'{c:>11}' for c in cells))

    with open(a.out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(recs[0].keys()))
        w.writeheader()
        w.writerows(recs)
    print(f'\nwrote {a.out} ({len(recs):,} rows)')


if __name__ == '__main__':
    main()
