#!/usr/bin/env python3
"""Find where a country block actually ENDS, so a stale label's extra tables
can be cut off by row_seq.

THE RULE (session 11, iteration 56; first proved on glucose in iteration 57):

    inside one label's row_seq range, a TOTAL row whose quantity equals the
    commodity-year's Tier-1 figure is the END of that block. Everything after
    it belongs to a different printed table.

Why it works. The volumes print a table per commodity, each closing on a grand
TOTAL that IS the national total the abstract publishes. When the parser loses a
group heading, one label swallows the tables that follow, and the swallowed
countries are then read as origins of the wrong commodity — caoutchouc's label
covers four tables, coffee 1880's covers a whole multi-commodity duty page, tea's
covers five including tobacco and wine. Every one of those was found by hand.
The T1-matching TOTAL finds the same edge in one query, because the printed
grand total of the RIGHT table is the only number in the block guaranteed to
equal the anchor.

Two signals come out of it:

  * boundary_seq — the last row of the real block. Feeds straight into a
    `group_repairs` seq range.
  * rows_after   — how much of the label lies beyond that row. A label with
    rows after its boundary is covering more than one commodity, and the size
    of the tail says how much.

A label carrying MORE THAN ONE T1-matching TOTAL for the same year is the same
finding stated more strongly: two grand totals means two commodities.

Usage:
    python3 scripts/block_boundary.py                 # -> reports/block_boundaries.csv
    python3 scripts/block_boundary.py --selftest      # replay glucose + tea
    python3 scripts/block_boundary.py --label TEA     # explain one label
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

import duckdb
import validate_gold as V

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / 'reports' / 'block_boundaries.csv'

# a printed subtotal/total row, same test integrate_sources.is_subtotal uses
def is_total(c):
    c = (c or '').strip().lower()
    return bool(c) and c.split(' ', 1)[0] == 'total'


def load_t1(con):
    """Two lookups, because a block's label may not sig to its own anchor.

      own[(sig, year)]  -> {quantities}   the direct test
      any_[(year, qty)] -> {label}        the fallback

    The fallback is needed more often than it looks: `Glucose, Solid or Liquid`
    sigs to ('glucose','liquid','solid') while its own Tier-1 line is printed
    `.. Glucose (Solid or Liquid)`, and V.sig DROPS parenthesised content — so
    the anchor sits under ('glucose',) and the direct test misses it. A TOTAL
    row equal to SOME commodity's anchor for that year is a table edge whether
    or not the label admits which commodity it is; the matched label is
    reported so the call can be judged rather than trusted.
    """
    own = defaultdict(set)
    any_ = defaultdict(set)
    rows = con.execute("""
        SELECT article_group, article, year, value FROM consensus
        WHERE flow='import' AND measure='quantity' AND value > 0""").fetchall()
    for g, a, y, v in rows:
        y, v = int(y), float(v)
        for s in (V.sig(a or ''), V.sig(f"{g or ''} {a or ''}")):
            if s:
                own[(s, y)].add(v)
        any_[(y, v)].add(f"{g or ''}|{a or ''}".strip('|'))
    return own, any_


def scan(con, t1, only_label=None):
    own, any_ = t1
    out = []
    for table in ('country_obs', 'country_obs_inf'):
        rows = con.execute(f"""
            SELECT volume, flow, article_group, article, row_seq, country_raw,
                   year, quantity
            FROM {table}
            WHERE flow='import' AND quantity IS NOT NULL AND quantity > 0
            ORDER BY volume, article_group, article, row_seq""").fetchall()
        blocks = defaultdict(list)
        for vol, flow, g, a, seq, c, y, q in rows:
            blocks[(vol, g, a)].append((seq, c, int(y), float(q)))
        for (vol, g, a), rs in blocks.items():
            if only_label and only_label.lower() not in f'{g} {a}'.lower():
                continue
            if len(rs) < 4:
                continue
            sigs = {s for s in (V.sig(a or ''), V.sig(f"{g or ''} {a or ''}")) if s}
            hits, how = [], ''
            for seq, c, y, q in rs:
                if not is_total(c):
                    continue
                if any(q in own.get((s, y), ()) for s in sigs):
                    hits.append((seq, y, q))
                    how = how or 'own'
                elif (y, q) in any_:
                    hits.append((seq, y, q))
                    how = how or ';'.join(sorted(any_[(y, q)]))[:60]
            if not hits:
                continue
            # Group the hits into RUNS. A comparative block prints one grand
            # total per year column, consecutively, so a run is a stretch of
            # hits whose years do not repeat; a repeat means a second table's
            # totals have started. Foreign SUBtotals can also match — glucose
            # 1895 has no British half, so its foreign total equals T1 — which
            # is why the longest run is taken rather than the first: the grand
            # totals cover every year column, a stray subtotal covers one.
            hits.sort()
            runs, cur, seen = [], [], set()
            for h in hits:
                if h[1] in seen:
                    runs.append((cur, seen))
                    cur, seen = [], set()
                cur.append(h)
                seen.add(h[1])
            runs.append((cur, seen))
            best = max(runs, key=lambda r: len(r[1]))
            boundary = best[0][-1][0]
            years = best[1]
            after = [r for r in rs if r[0] > boundary]
            out.append({
                'table': table, 'volume': vol,
                'article_group': g or '', 'article': a or '',
                'n_rows': len(rs), 'seq_min': rs[0][0], 'seq_max': rs[-1][0],
                'boundary_seq': boundary,
                'boundary_years': ';'.join(str(y) for y in sorted(years)),
                'n_t1_totals': len(hits),
                'rows_after': len(after),
                'qty_after': f'{sum(r[3] for r in after):.0f}',
                'first_after': (after[0][1] if after else ''),
                'matched': how,
            })
    out.sort(key=lambda r: -r['rows_after'])
    return out


def selftest(con, t1):
    """Replay the two blocks the rule was derived from and then proved on."""
    ok = True
    cases = [
        # (volume, group, article, expected boundary_seq, what it is)
        ('country_obs', 'as_1899', 'SUGAR', 'Glucose, Solid or Liquid', 21728,
         'glucose: grand totals 21724-21728 are T1 for 1895-99 (iteration 57)'),
        ('country_obs', 'as_1896', 'TEA', None, 289,
         'tea: row 289 TOTAL = 265,394,122 = T1 1896 (iteration 56)'),
    ]
    rows = scan(con, t1)
    idx = {(r['table'], r['volume'], r['article_group'], r['article']): r
           for r in rows}
    for tbl, vol, g, a, want, why in cases:
        got = idx.get((tbl, vol, g or '', a or ''))
        if not got:
            print(f'  FAIL {tbl} {vol} {g}|{a}: label not reported at all')
            ok = False
            continue
        if got['boundary_seq'] != want:
            print(f"  FAIL {tbl} {vol} {g}|{a}: boundary {got['boundary_seq']}, want {want}")
            ok = False
        else:
            print(f"  ok   {tbl} {vol} {g}|{a} -> {want}  ({got['rows_after']} rows after)")
        print(f'       {why}')
    return ok


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)
    t1 = load_t1(con)
    print(f'Tier-1 keys: own {len(t1[0]):,}, by (year,qty) {len(t1[1]):,}')
    if '--selftest' in sys.argv:
        sys.exit(0 if selftest(con, t1) else 1)
    only = None
    if '--label' in sys.argv:
        only = sys.argv[sys.argv.index('--label') + 1]
    rows = scan(con, t1, only)
    print(f'labels with a T1-matching TOTAL: {len(rows):,}')
    over = [r for r in rows if r['rows_after'] > 0]
    print(f'  ...of which carry rows BEYOND their boundary: {len(over):,}')
    multi = [r for r in rows if r['n_t1_totals'] > len(r['boundary_years'])]
    print(f'  ...labels with more than one grand-total run: {len(multi):,}')
    if only:
        for r in rows[:20]:
            print('   ', r)
        return
    with open(OUT, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f'-> {OUT}')
    print('\ntop 15 by rows beyond the boundary:')
    for r in rows[:15]:
        print(f"  {r['rows_after']:5d} after  {r['volume']} {r['article_group'][:26]:28s}"
              f"| {(r['article'] or '')[:26]:28s} boundary {r['boundary_seq']}")


if __name__ == '__main__':
    main()
