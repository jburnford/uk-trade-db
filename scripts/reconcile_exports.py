#!/usr/bin/env python3
"""Export/re-export reconciliation baseline — the in-block printed-TOTAL metric.

The export country tables carry their own anchor. Each printed table is a
three-level hierarchy:

    Russia … Other Foreign Countries      <- member rows
    TOTAL                                 <- section subtotal (Foreign)
    Gibraltar … Other British Possessions <- member rows
    TOTAL                                 <- section subtotal (British Possessions)
    TOTAL                                 <- grand total = Foreign + British

That makes every destination cell provable *without* joining to the abstract
national line and without any external gold: a member section closes against
its own printed subtotal, and the subtotals close against the grand total.
87% of export blocks carry at least one such anchor, which is denser coverage
than the import side's Tier-1 anchor.

The parser fuses adjacent printed tables into one (volume, group, article)
block — a block with 6 or 9 TOTAL rows is two or three tables run together.
This script splits on the rollup pattern rather than assuming one table per
block, so fused blocks are still scored.

WITNESS ROLE MATTERS AND IS REPORTED SEPARATELY. The 1897-99 volumes reprint
up to five years each as comparatives. For 1893-96 those reprints close at
roughly half the rate of the contemporary volume (1895: 75.1% own-year against
25.7% reprint), so pooling them manufactures a spurious quality collapse at
1893. There is no 1893 break in either flow; there is a real one at 1897.

Do NOT turn that into a blanket "prefer the own-year witness" rule. For 1897
and 1898 the ordering inverts -- the comparative reprints close better than the
contemporary volume (1897: 21.0% comp against 8.2% own). What degrades is a
particular column position in the five-year comparative layout, not reprinting
as such, and the volume's own year sits in the worst position. Choose the
witness per year on measured closure, not on role.

Usage:
    python3 scripts/reconcile_exports.py [--flow export_uk] [--engine obs]
                                         [--measure value] [--db db/uk_trade.duckdb]
                                         [--country-report]

--country-report additionally reports, per destination, how many of its cells
sit inside a section that closes exactly. A cell inside an exact-closing
section is corroborated by the printed page itself; that is the export-side
substitute for a gold transcription.
"""
import argparse, collections, re, sys
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phantom_articles import fix_articles, load_splits, apply_splits

TOTAL_RE = re.compile(r'\bTOTAL\b', re.I)
ENGINES = {'obs': 'country_obs', 'inf': 'country_obs_inf', 'twoup': 'country_obs_twoup',
           # the tn_ annuals' comparative years (parse_tn_overlap.py)
           'tn': 'country_obs_tn', 'tn_inf': 'country_obs_tn_inf'}


def is_total(label):
    return bool(label) and bool(TOTAL_RE.search(label))


def score(members, printed):
    """Relative deviation of a member sum against its printed anchor."""
    if printed is None or printed == 0:
        return None
    return (sum(members) - printed) / abs(printed)


def bucket(dev):
    a = abs(dev)
    if a <= 0.001:
        return 'exact01'
    if a <= 0.05:
        return 'within5'
    if a <= 0.25:
        return 'mod'
    return 'gross'


def walk_block(rows):
    """Split one (volume, group, article, unit) block into printed tables.

    Yields ('section', members, printed) for each member section and
    ('rollup', section_totals, printed) for each grand total.
    Rows are (row_seq, country_raw, amount).
    """
    members = []          # amounts since the last TOTAL
    pending = []          # section subtotals not yet rolled up
    for _, label, amt in rows:
        if not is_total(label):
            if amt is not None:
                members.append(amt)
            continue
        # a TOTAL row
        if members:
            yield ('section', list(members), amt)
            if amt is not None:
                pending.append(amt)
            members = []
        else:
            # no members since the last TOTAL -> this is a rollup
            if pending:
                yield ('rollup', list(pending), amt)
            pending = []
    # trailing members with no closing TOTAL are unanchored; ignored


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='db/uk_trade.duckdb')
    ap.add_argument('--flow', default='export_uk',
                    choices=['export_uk', 'reexport', 'import'])
    ap.add_argument('--engine', default='obs', choices=sorted(ENGINES))
    ap.add_argument('--measure', default='value', choices=['value', 'quantity'])
    ap.add_argument('--country-report', action='store_true')
    ap.add_argument('--dump', help='write one line per scored member section '
                    '(vol, year, group, article, total_seq, n, bucket)')
    ap.add_argument('--min-year', type=int, default=0)
    ap.add_argument('--max-year', type=int, default=9999)
    ap.add_argument('--repairs', action='store_true',
                    help='apply the cell-repair overlays before scoring. The '
                         'closure gain is an INDEPENDENT check: repairs come '
                         'from cross-volume witnesses, never from the printed '
                         'subtotal the section is scored against')
    a = ap.parse_args()

    tbl = ENGINES[a.engine]
    con = duckdb.connect(a.db, read_only=True)
    cols = con.execute(f'describe "{tbl}"').fetchall()
    names = {c[0] for c in cols}
    if a.measure not in names:
        sys.exit(f'{tbl} has no {a.measure} column')
    seq = 'row_seq' if 'row_seq' in names else 'rowid'

    q = f"""
      select volume, flow, year, coalesce(article_group,'') ag, article,
             unit, {seq} seq, country_raw, {a.measure} amt
      from "{tbl}"
      where flow = ? and year between ? and ?
    """
    raw = con.execute(q, [a.flow, a.min_year, a.max_year]).fetchall()
    if not raw:
        sys.exit(f'no rows for flow={a.flow} in {tbl}')
    # --repairs also applies the phantom-region relabel (phantom_articles.py):
    # a label repair, not a value repair, but the same kind of thing -- it is
    # what the export consumers see, and the closure it restores comes from
    # re-uniting members with the printed TOTAL that the absorbed heading
    # had split them from. Repairs are keyed on the RAW article.
    fixed = (fix_articles(apply_splits(raw, load_splits(flow=a.flow), vol=0,
                                       flow=1, year=2, group=3, art=4, seq=6, unit=5),
                          vol=0, flow=1, year=2, group=3, art=4, unit=5, seq=6)
             if a.repairs else raw)
    # (vol, year, group, raw article, article, unit, seq, country, value):
    # the group is the relabelled one (a fused-section split moves rows to
    # another heading) but repairs are looked up on the raw group, so both
    # are carried
    rows = [(r[0], r[2], f[3], r[3], r[4] or '', f[4] or '', f[5] or '', r[6], r[7], r[8])
            for r, f in zip(raw, fixed)]
    rows.sort(key=lambda t: (t[0], t[2], t[5], t[6], t[7] if t[7] is not None else -1))

    fix, no_repair = {}, object()
    if a.repairs and a.measure == 'value' and a.engine == 'obs':
        import csv, os
        for path in ('reference/export_cell_repairs.csv',
                     'reference/malformed_cell_repairs.csv',
                     'reference/edge_column_repairs.csv',
                'reference/section_closure_repairs.csv'):
            if not os.path.exists(path):
                continue
            for r in csv.DictReader(open(path)):
                fix[(r['volume'], int(r['year']), r['article_group'], r['article'],
                     r['country_raw'], round(float(r['old_value'])))] = (
                    float(r['new_value']) if r['new_value'] != '' else None)
        print(f'applying {len(fix)} cell repairs/null-outs')

    blocks = collections.defaultdict(list)
    n_fixed = 0
    for vol, yr, ag, raw_ag, raw_art, art, unit, seq, ctry, amt in rows:
        if amt is not None and fix:
            nv = fix.get((vol, yr, raw_ag, raw_art, ctry, round(amt)), no_repair)
            if nv is not no_repair:
                amt, n_fixed = nv, n_fixed + 1
        blocks[(vol, yr, ag, art, unit)].append((seq, ctry, amt))
    if fix:
        print(f'cell repairs applied: {n_fixed}')

    # a volume is the own-year witness for its maximum year; every other year
    # it carries is a comparative reprint
    own_year = {}
    for (vol, yr, *_) in blocks:
        own_year[vol] = max(own_year.get(vol, 0), yr)

    sec = collections.Counter()
    rol = collections.Counter()
    by_year = collections.defaultdict(collections.Counter)
    by_role = collections.defaultdict(collections.Counter)
    n_blocks = len(blocks)
    n_anchored = 0
    n_tables = 0
    # destination -> counter of cells by the verdict of their enclosing section
    ctry_stat = collections.defaultdict(collections.Counter)

    dump = open(a.dump, 'w') if a.dump else None
    for (vol, yr, ag, art, unit), rws in blocks.items():
        anchored = False
        role = 'own' if own_year.get(vol) == yr else 'comp'
        # re-walk carrying labels so we can attribute cells to their section
        members, labels, pending = [], [], []
        for tseq, label, amt in rws:
            if not is_total(label):
                if amt is not None:
                    members.append(amt)
                    labels.append(label)
                continue
            if members:
                d = score(members, amt)
                if d is not None:
                    b = bucket(d)
                    sec[b] += 1
                    by_year[yr][b] += 1
                    by_role[(role, yr)][b] += 1
                    anchored = True
                    if dump:
                        dump.write(f'{vol}\t{yr}\t{ag}\t{art}\t{tseq}\t{len(members)}\t{b}\t{role}\n')
                    if a.country_report:
                        for lb in labels:
                            ctry_stat[lb][b] += 1
                    if amt is not None:
                        pending.append(amt)
                members, labels = [], []
            else:
                if pending:
                    d = score(pending, amt)
                    if d is not None:
                        rol[bucket(d)] += 1
                        n_tables += 1
                        anchored = True
                pending = []
        if anchored:
            n_anchored += 1

    ns = sum(sec.values()) or 1
    nr = sum(rol.values()) or 1
    print(f'flow={a.flow}  engine={a.engine}({tbl})  measure={a.measure}')
    print(f'blocks: {n_blocks:,}   with a printed anchor: {n_anchored:,} '
          f'({100*n_anchored/n_blocks:.1f}%)   printed tables closed: {n_tables:,}')
    print()
    print(f'MEMBER SECTIONS  (destination rows vs their printed subtotal)  n={ns:,}')
    for b in ('exact01', 'within5', 'mod', 'gross'):
        print(f'  {b:8s}: {sec[b]:6,}  ({100*sec[b]/ns:5.1f}%)')
    print(f'  within 5%: {100*(sec["exact01"]+sec["within5"])/ns:.1f}%')
    print()
    print(f'ROLLUPS  (section subtotals vs the printed grand total)  n={nr:,}')
    for b in ('exact01', 'within5', 'mod', 'gross'):
        print(f'  {b:8s}: {rol[b]:6,}  ({100*rol[b]/nr:5.1f}%)')

    own_tot = collections.Counter()
    for (role, _y), cc in by_role.items():
        if role == 'own':
            own_tot.update(cc)
    no = sum(own_tot.values()) or 1
    print()
    print(f'OWN-YEAR WITNESSES ONLY  n={no:,}   exact01 '
          f'{100*own_tot["exact01"]/no:.1f}%   within 5% '
          f'{100*(own_tot["exact01"]+own_tot["within5"])/no:.1f}%')
    print('  (this is the number to quote; the pooled figure above is dragged '
          'down by comparative reprints)')

    print()
    print('member-section closure by year and witness role')
    print(f'{"yr":>4} | {"own n":>6} {"exact":>7} {"w5":>7} | '
          f'{"comp n":>7} {"exact":>7} {"w5":>7}')
    for y in sorted(by_year):
        o, c = by_role[('own', y)], by_role[('comp', y)]
        n_o, n_c = sum(o.values()), sum(c.values())
        po = (f'{100*o["exact01"]/n_o:>6.1f}% {100*(o["exact01"]+o["within5"])/n_o:>6.1f}%'
              if n_o else f'{"-":>7} {"-":>7}')
        pc = (f'{100*c["exact01"]/n_c:>6.1f}% {100*(c["exact01"]+c["within5"])/n_c:>6.1f}%'
              if n_c else f'{"-":>7} {"-":>7}')
        print(f'{y:>4} | {n_o:>6} {po} | {n_c:>7} {pc}')

    if a.country_report:
        print()
        print('destinations by the verdict of their enclosing section '
              '(top 40 by cell count)')
        print(f'{"cells":>7} {"in exact sec":>12} {"pct":>6}  destination')
        ranked = sorted(ctry_stat.items(), key=lambda kv: -sum(kv[1].values()))
        for lb, cc in ranked[:40]:
            n = sum(cc.values())
            print(f'{n:>7} {cc["exact01"]:>12} {100*cc["exact01"]/n:>5.1f}%  {lb[:60]}')


if __name__ == '__main__':
    main()
