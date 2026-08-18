#!/usr/bin/env python3
"""Per-destination export series with printed-page corroboration.

There is no gold transcription for the export flow. The substitute is the
printed page's own arithmetic: a destination cell that sits inside a section
whose members sum exactly to their printed subtotal has been corroborated by
the compositor. Layer the second engine on top and cells fall into tiers:

  A  section closes exact (<=0.1%) AND both engines agree  -- strongest
  B  section closes exact, single engine (no inf pairing)
  C  section closes loosely (<=5%), engines agree
  D  anything else the section anchors
  X  no enclosing printed section -- unanchored

Volume handling: the 1893-99 volumes reprint several prior years as
comparatives, so the same (year, article, country) appears in up to three
volumes. A volume is the primary witness for its *maximum* year -- as_1897
covers 1893-97 and is primary only for 1897; the tn_ volumes are named for
their publication year, so tn_1871 is primary for 1870 and tn_1901 for 1900.
The other volumes are comparative witnesses, usable for arbitration; summing
across volumes double-counts and this script never does it.

Usage:
    python3 scripts/export_country_series.py --country "British North America" \
        [--country Canada --country Newfoundland] [--flow export_uk] \
        [--out reports/canada_export_series.csv]

Aliases: pass --country once per printed spelling. Use --list-countries to see
the spellings actually present for a flow.
"""
import argparse, collections, csv, re, sys
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
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
ENGINES = {'obs': 'country_obs', 'inf': 'country_obs_inf'}


def is_total(s):
    return bool(s) and bool(TOTAL_RE.search(s))


def norm(s):
    """Loose article key so the two engines pair despite spelling drift."""
    return re.sub(r'[^a-z0-9]+', ' ', (s or '').lower()).strip()


def bucket(members, printed):
    if printed in (None, 0):
        return None
    d = abs(sum(members) - printed) / abs(printed)
    return 'exact01' if d <= 0.001 else ('within5' if d <= 0.05 else
           ('mod' if d <= 0.25 else 'gross'))


def load(con, tbl, flow):
    """Return {(vol, yr, ag, art, unit): [(seq, country, value, quantity)]}."""
    cols = {c[0] for c in con.execute(f'describe "{tbl}"').fetchall()}
    seq = 'row_seq' if 'row_seq' in cols else 'rowid'
    qty = 'quantity' if 'quantity' in cols else 'NULL'
    rows = con.execute(f"""
        select volume, flow, year, coalesce(article_group,'') ag, article,
               unit, {seq} seq, country_raw, value, {qty}
        from "{tbl}" where flow = ?
    """, [flow]).fetchall()
    # phantom-region relabel (phantom_articles.py): 'West Africa' as an
    # article is an absorbed heading; the row belongs to the article above.
    # Repairs are keyed on the RAW parse, so look them up before relabelling.
    fixed = fix_articles(apply_splits(rows, load_splits(flow=flow), vol=0,
                                      flow=1, year=2, group=3, art=4, seq=6, unit=5),
                         vol=0, flow=1, year=2, group=3, art=4, unit=5, seq=6)
    fix = load_repairs()
    b = collections.defaultdict(list)
    for r, f in zip(rows, fixed):
        vol, _, yr, ag, art, unit, sq, ctry, val, qt = r
        if val is not None:
            nv = fix.get((vol, yr, ag, art or '', ctry, round(val)), NO_REPAIR)
            if nv is not NO_REPAIR:
                val = nv                       # None = null-out, cell dropped
        b[(vol, yr, ag, f[4] or '', f[5] or '')].append((sq, ctry, val, qt))
    for k in b:
        b[k].sort(key=lambda t: t[0] if t[0] is not None else -1)
    return b


def section_verdicts(rws):
    """Map row_seq -> verdict of the enclosing printed member section."""
    out, members, seqs = {}, [], []
    for sq, label, val, _ in rws:
        if not is_total(label):
            if val is not None:
                members.append(val)
                seqs.append(sq)
            continue
        if members:
            v = bucket(members, val)
            for s in seqs:
                out[s] = v
            members, seqs = [], []
    return out


REPAIR_FILES = ('reference/export_cell_repairs.csv',
                'reference/malformed_cell_repairs.csv',
                'reference/edge_column_repairs.csv',
                'reference/row_slip_repairs.csv',
                'reference/scaled_block_repairs.csv',
                'reference/label_merge_repairs.csv',
                'reference/export_manual_repairs.csv',
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
    ap.add_argument('--country', action='append', default=[])
    ap.add_argument('--out')
    ap.add_argument('--list-countries', action='store_true')
    a = ap.parse_args()

    con = duckdb.connect(a.db, read_only=True)

    if a.list_countries:
        for c, n, y0, y1 in con.execute("""
                select country_raw, count(*), min(year), max(year)
                from country_obs where flow = ? and length(country_raw) <= 45
                group by 1 order by count(*) desc limit 60""", [a.flow]).fetchall():
            print(f'{n:7,}  {y0}-{y1}  {c}')
        return

    if not a.country:
        sys.exit('give at least one --country (or --list-countries)')
    want = {c.strip().lower() for c in a.country}

    blocks = {e: load(con, t, a.flow) for e, t in ENGINES.items()}

    # a volume is the primary witness for its maximum year (as_1897 covers
    # 1893-97 but is primary only for 1897; tn_1871 is primary for 1870)
    own_year = {}
    for (vol, yr, *_), in ((k,) for k in blocks['obs']):
        own_year[vol] = max(own_year.get(vol, 0), yr)

    # inf lookup on a normalised article key, with a group-free fallback, so
    # the engines pair despite spelling drift (otherwise everything lands in
    # tier B for want of a partner rather than for want of agreement)
    inf_val, inf_alt = {}, {}
    for (vol, yr, ag, art, unit), rws in blocks['inf'].items():
        for sq, ctry, val, qt in rws:
            if ctry and ctry.strip().lower() in want:
                c = ctry.strip()
                inf_val[(vol, yr, unit, norm(ag + ' ' + art), c)] = val
                inf_alt.setdefault((vol, yr, unit, norm(art), c), val)

    recs = []
    for (vol, yr, ag, art, unit), rws in blocks['obs'].items():
        hits = [(sq, c, v, q) for sq, c, v, q in rws
                if c and c.strip().lower() in want]
        if not hits:
            continue
        verd = section_verdicts(rws)
        own = (vol == PRIMARY_OVERRIDE[yr] if yr in PRIMARY_OVERRIDE
               else own_year.get(vol) == yr)
        for sq, ctry, val, qt in hits:
            label = ctry.strip()
            iv = inf_val.get((vol, yr, unit, norm(ag + ' ' + art), label))
            if iv is None:
                iv = inf_alt.get((vol, yr, unit, norm(art), label))
            agree = (iv is not None and val is not None
                     and abs(val - iv) <= 0.001 * max(abs(val), 1))
            sv = verd.get(sq)
            if sv is None:
                tier = 'X'
            elif sv == 'exact01':
                tier = 'A' if agree else ('B' if iv is None else 'D')
            elif sv == 'within5':
                tier = 'C' if agree else 'D'
            else:
                tier = 'D'
            recs.append(dict(year=yr, country=label, article_group=ag,
                             article=art, unit=unit, value=val, quantity=qt,
                             value_inf=iv, engines_agree=int(bool(agree)),
                             section=sv or 'none', tier=tier, volume=vol,
                             own_year=int(own), row_seq=sq))

    recs.sort(key=lambda r: (r['year'], r['article_group'], r['article']))
    print(f'flow={a.flow}  destinations={sorted(want)}')
    print(f'cells found: {len(recs):,}   own-year: '
          f'{sum(r["own_year"] for r in recs):,}')

    own = [r for r in recs if r['own_year']]
    print()
    print('OWN-YEAR SERIES (the primary witness; comparatives excluded)')
    print(f'{"yr":>4} {"label":>22} {"arts":>5} {"value GBP":>14} '
          f'{"A":>4} {"B":>4} {"C":>4} {"D":>4} {"X":>4}  {"tierA%":>6}')
    byyl = collections.defaultdict(list)
    for r in own:
        byyl[(r['year'], r['country'])].append(r)
    for (y, lb) in sorted(byyl):
        g = byyl[(y, lb)]
        t = collections.Counter(r['tier'] for r in g)
        v = sum(r['value'] or 0 for r in g)
        print(f'{y:>4} {lb[:22]:>22} {len(g):>5} {v:>14,.0f} '
              f'{t["A"]:>4} {t["B"]:>4} {t["C"]:>4} {t["D"]:>4} {t["X"]:>4} '
              f'{100*t["A"]/len(g):>5.1f}%')

    print()
    print('annual total on tier A+B+C cells only (corroborated subset)')
    print(f'{"yr":>4} {"corrob GBP":>14} {"all GBP":>14} {"cov":>6}')
    byy = collections.defaultdict(list)
    for r in own:
        byy[r['year']].append(r)
    for y in sorted(byy):
        g = byy[y]
        good = sum(r['value'] or 0 for r in g if r['tier'] in 'ABC')
        allv = sum(r['value'] or 0 for r in g)
        print(f'{y:>4} {good:>14,.0f} {allv:>14,.0f} '
              f'{100*good/allv if allv else 0:>5.1f}%')

    if a.out:
        with open(a.out, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(recs[0].keys()))
            w.writeheader()
            w.writerows(recs)
        print(f'\nwrote {a.out} ({len(recs):,} rows)')


if __name__ == '__main__':
    main()
