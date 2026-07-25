#!/usr/bin/env python3
"""Re-base the row_seq ranges in reference/group_repairs.csv after a re-parse.

Every repair addresses rows by (volume, flow, row_seq range) into country_obs
or country_obs_inf. row_seq is a running counter per section, so any parser
change that adds or drops a single row renumbers everything after it and each
repair silently starts relabelling different rows. This finds each repair's
rows in the new numbering by CONTENT and rewrites the range.

The old numbering has to be available as snap_country_obs / snap_country_obs_inf
(`CREATE TABLE snap_x AS SELECT * FROM x` before re-parsing).

Matching is on the (quantity, value) sequence, not the country labels: a
label_shift repair exists precisely because the labels were wrong, and a
parser fix may have corrected them. Verdicts:

  same      range still covers the same rows — untouched
  rebased   found the same rows at a new range — range rewritten
  premise-gone
            the rows are no longer as the repair found them (usually the
            parser now emits the reading the repair was hand-applying).
            Left ALONE and reported: applying it again would double-fix.
  lost      rows not found — reported for adjudication

Run it ONCE per re-parse, against the ranges as they were when the snapshot was
taken. A second --write compares the already-rewritten ranges to the old table
and will move them again.

Usage: python3 scripts/rebase_group_repairs.py [--write]
"""
import csv
import sys
from pathlib import Path

import duckdb

BASE = Path(__file__).resolve().parent.parent
REPAIRS = BASE / 'reference' / 'group_repairs.csv'


def table_for(row, old):
    t = ('country_obs_inf' if (row['obs_source'] or '').strip() == 'inf'
         else 'country_obs')
    return ('snap_' + t) if old else t


def rows_in(con, row, old):
    """The (quantity, value) sequence a repair's range covers, with the table
    it sits in, so a re-based range can be required to stay in that table."""
    a, b = int(row['seq_start']), int(row['seq_end'])
    return con.execute(f'''
        SELECT row_seq, article_group, article, quantity, value, country_raw
        FROM {table_for(row, old)}
        WHERE volume = ? AND flow = ? AND row_seq BETWEEN ? AND ?
        -- row_seq is not unique (the two-up halves share the counter), so a
        -- bare ORDER BY row_seq compares tied rows in arbitrary order and a
        -- range that never changed looks changed.
        ORDER BY row_seq, article_group, article, country_raw, quantity''',
        [row['volume'], row['flow'], a, b]).fetchall()


def sub(c):
    """A country label without the region it sits under, so 'British East
    Indies : Madras' and bare 'Madras' compare equal."""
    return (c or '').rsplit(' : ', 1)[-1].strip().casefold()


def shift_already_applied(old, new):
    """True when the parser now emits what label_shift was hand-applying.

    label_shift moves every figure to the NEXT label down, so the corrected
    reading pairs the old value sequence with old countries [1:]. If the new
    parse already reads that way, applying the repair again shifts a second
    time and destroys a block that is now correct."""
    if len(old) < 3 or len(new) < 2:
        return False
    want = [sub(r[5]) for r in old][1:]
    got = [sub(r[5]) for r in new][:len(want)]
    return len(want) >= 2 and got == want


def find_run(con, row, want):
    """Locate the same (quantity, value) run in the new numbering. Anchored on
    the repair's own source table/group/article so a coincidental numeric match
    elsewhere in the volume cannot win."""
    if not want:
        return None
    nums = [(r[3], r[4]) for r in want]
    grp, art = want[0][1], want[0][2]
    # Anchored search first. The fallback drops the anchor because a glue-block
    # repair deliberately spans rows whose group/article is the stale label it
    # exists to correct, so the range's first row need not share them.
    for anchored in (True, False):
        where = ('AND article_group IS NOT DISTINCT FROM ? '
                 'AND article IS NOT DISTINCT FROM ?') if anchored else ''
        args = [row['volume'], row['flow']] + ([grp, art] if anchored else [])
        cand = con.execute(f'''
            SELECT row_seq, quantity, value FROM {table_for(row, False)}
            WHERE volume = ? AND flow = ? {where}
            ORDER BY row_seq, article_group, article, country_raw, quantity''',
            args).fetchall()
        seqs = [c[0] for c in cand]
        vals = [(c[1], c[2]) for c in cand]
        hits = [i for i in range(len(vals) - len(nums) + 1)
                if vals[i:i + len(nums)] == nums]
        if len(hits) == 1:
            i = hits[0]
            return seqs[i], seqs[i + len(nums) - 1]
    return None                         # absent, or ambiguous — do not guess


def main(write=False):
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)
    reps = list(csv.DictReader(open(REPAIRS)))
    fields = list(reps[0])
    verdicts = []
    for r in reps:
        try:
            a, b = int(r['seq_start']), int(r['seq_end'])
        except ValueError:
            verdicts.append(('same', r, None))
            continue
        if a == 0 and b == 0:
            verdicts.append(('same', r, None))       # supersede-only, no range
            continue
        old = rows_in(con, r, True)
        new = rows_in(con, r, False)
        if r['label_shift'] == '1' and shift_already_applied(old, new):
            verdicts.append(('premise-gone', r, None))
            continue
        if [(x[3], x[4]) for x in old] == [(x[3], x[4]) for x in new] \
                and [x[1:3] for x in old] == [x[1:3] for x in new] \
                and [sub(x[5]) for x in old] == [sub(x[5]) for x in new]:
            verdicts.append(('same', r, None))
            continue
        run = find_run(con, r, old)
        if run and (run[0], run[1]) != (a, b):
            verdicts.append(('rebased', r, run))
        elif run:
            verdicts.append(('same', r, None))
        else:
            kind = 'premise-gone' if r['label_shift'] == '1' else 'lost'
            verdicts.append((kind, r, None))
    counts = {}
    for v, _, _ in verdicts:
        counts[v] = counts.get(v, 0) + 1
    print('verdicts:', counts)
    for v, r, run in verdicts:
        if v == 'same':
            continue
        tag = f'{r["volume"]} {r["flow"]} {r["article_group"]}|{r["article"]}'
        extra = f' -> {run[0]}-{run[1]}' if run else ''
        print(f'  {v:13s} {tag} seq {r["seq_start"]}-{r["seq_end"]}{extra}'
              f'  src={r["obs_source"] or "ch"}'
              f'{"  label_shift" if r["label_shift"] == "1" else ""}')
    if write:
        for v, r, run in verdicts:
            if v == 'rebased':
                r['seq_start'], r['seq_end'] = str(run[0]), str(run[1])
        with open(REPAIRS, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(reps)
        print(f'\nrewrote {REPAIRS} ({counts.get("rebased", 0)} ranges)')
    else:
        print('\n(dry run — pass --write to rewrite the ranges)')


if __name__ == '__main__':
    main('--write' in sys.argv)
