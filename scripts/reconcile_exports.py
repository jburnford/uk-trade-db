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
import duckdb

TOTAL_RE = re.compile(r'\bTOTAL\b', re.I)
ENGINES = {'obs': 'country_obs', 'inf': 'country_obs_inf', 'twoup': 'country_obs_twoup'}


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
    ap.add_argument('--min-year', type=int, default=0)
    ap.add_argument('--max-year', type=int, default=9999)
    a = ap.parse_args()

    tbl = ENGINES[a.engine]
    con = duckdb.connect(a.db, read_only=True)
    cols = con.execute(f'describe "{tbl}"').fetchall()
    names = {c[0] for c in cols}
    if a.measure not in names:
        sys.exit(f'{tbl} has no {a.measure} column')
    seq = 'row_seq' if 'row_seq' in names else 'rowid'

    q = f"""
      select volume, year, coalesce(article_group,'') ag, coalesce(article,'') art,
             coalesce(unit,'') unit, {seq} seq, country_raw, {a.measure} amt
      from "{tbl}"
      where flow = ? and year between ? and ?
      order by volume, ag, art, unit, seq
    """
    rows = con.execute(q, [a.flow, a.min_year, a.max_year]).fetchall()
    if not rows:
        sys.exit(f'no rows for flow={a.flow} in {tbl}')

    blocks = collections.defaultdict(list)
    for vol, yr, ag, art, unit, seq, ctry, amt in rows:
        blocks[(vol, yr, ag, art, unit)].append((seq, ctry, amt))

    sec = collections.Counter()
    rol = collections.Counter()
    by_year = collections.defaultdict(collections.Counter)
    n_blocks = len(blocks)
    n_anchored = 0
    n_tables = 0
    # destination -> counter of cells by the verdict of their enclosing section
    ctry_stat = collections.defaultdict(collections.Counter)

    for (vol, yr, ag, art, unit), rws in blocks.items():
        anchored = False
        # re-walk carrying labels so we can attribute cells to their section
        members, labels, pending = [], [], []
        for _, label, amt in rws:
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
                    anchored = True
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

    print()
    print('member-section closure by year')
    print(f'{"yr":>4} {"sections":>8} {"exact01":>8} {"pct":>6} {"w5 pct":>7}')
    for y in sorted(by_year):
        r = by_year[y]
        n = sum(r.values()) or 1
        w5 = r['exact01'] + r['within5']
        print(f'{y:>4} {n:>8} {r["exact01"]:>8} {100*r["exact01"]/n:>5.1f}% '
              f'{100*w5/n:>6.1f}%')

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
