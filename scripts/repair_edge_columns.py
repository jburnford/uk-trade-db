#!/usr/bin/env python3
"""Cross-volume vote repair for the page-edge own-year columns, 1897-98.

The malformed-comma detector (detect_malformed_numbers.py) proved the
mechanism — the comparative volumes print ten columns and the rightmost, the
volume's OWN year, is at the page edge and loses digits — but its signature
only catches the cells where a comma SURVIVED in an inconsistent position:
0.33% of cells, against an own-year section closure of 8.2%, which implies
roughly 15% of the own-year column is wrong. Most of the damage loses the
comma along with the digits and parses as a plausible number, silently.

The repair that reaches those cells is a vote. 1897 is reprinted in a
non-edge column by BOTH as_1898 and as_1899, in both OCR engines; 1898 is
reprinted by as_1899 in both engines. Per own-year cell:

  * the cell's key is (flow, group, article, unit, country), punctuation-
    blind, plus an OCCURRENCE index — the i-th printed line carrying a key
    matches the i-th line carrying it in the witness, but only when both
    sides carry the key the same number of times (fused blocks legitimately
    print one country twice; a count mismatch means rows were dropped and
    alignment would be a guess);
  * TOTAL rows are voted on the same footing. They are the section anchors,
    they sit in the same damaged edge column, and a section whose anchor is
    broken can never close however many members are repaired;
  * a witness engine x volume gets one vote per key; if TWO OR MORE
    witnesses agree exactly on a value that differs from the own-column
    value, repair to the witness value;
  * when the full key finds nothing in a witness (group headings differ
    across volumes — the capture classes), a group-free key is tried,
    admitted only if it is unique on both sides;
  * never touch a cell whose enclosing member section closes exactly against
    its printed TOTAL, and never touch a TOTAL whose section closes exactly:
    the page's own arithmetic corroborates those cells and outranks any
    reprint.

For 1898 the two witnesses are necessarily the same BOOK read by two engines
(only as_1899 reprints 1898). Two engines agreeing proves what that book
printed, not that the book is right — weaker than the 1897 two-book vote,
accepted with that caveat because the alternative is a read at the damaged
page edge. 1899 and 1900 own columns have no reprint anywhere: not
repairable by any witness, left to the malformed-cell null-outs.

Output: reference/edge_column_repairs.csv, same provenance-safe overlay
format as the other repair files (keyed on the BAD value as well as the
coordinates).

Usage:
    python3 scripts/repair_edge_columns.py [--dry-run]
        [--out reference/edge_column_repairs.csv]
"""
import argparse, collections, csv, re
import duckdb

# (volume, year) column to repair -> witness volumes. A volume must NEVER
# witness its own maximum year: that column is at the damaged page edge, and
# two engines agreeing on the same damaged print is not corroboration — the
# digits are lost in the scan, so both engines read the same wrong number.
# as_1899's 1897/98 columns are repaired because the per-year witness override
# in the series scripts makes them PRIMARY for those years (measured closure:
# they corroborate ~3x more value than the repaired own-year edge columns).
TARGETS = {('as_1897', 1897): ['as_1898', 'as_1899'],
           ('as_1898', 1898): ['as_1899'],
           ('as_1899', 1897): ['as_1898']}
# NOT targeted: as_1899's 1898 column (its only witness would be as_1898's
# edge column) and mutual pairs like as_1898's 1897 column, which would let
# two disagreeing volumes simply swap values.
ENGINES = {'obs': 'country_obs', 'inf': 'country_obs_inf'}
TOTAL_RE = re.compile(r'\bTOTAL\b', re.I)


def norm(s):
    return re.sub(r'[^A-Z0-9]', '', (s or '').upper())


def fetch(con, tbl, vol, year):
    """Block-ordered rows: (flow, ag, art, unit, country_raw, value)."""
    return con.execute(f"""
        select flow, coalesce(article_group,''), coalesce(article,''),
               coalesce(unit,''), country_raw, value
        from "{tbl}" where volume = ? and year = ?
        order by flow, 2, 3, 4, row_seq
    """, [vol, year]).fetchall()


def index_rows(rows):
    """Two indexes over one volume's rows for a year.

    full[key+occ] -> value, where occ is the occurrence rank of the key in
    row order; count[key] -> total occurrences (alignment is only trusted
    when both sides agree on the count). nogroup collapses the group level
    for the capture classes, single-occurrence unique keys only.
    """
    full, count = {}, collections.Counter()
    nogroup = {}
    for flow, ag, art, unit, ctry, v in rows:
        k = (flow, norm(ag), norm(art), norm(unit), norm(ctry))
        full[k + (count[k],)] = v
        count[k] += 1
    for k, c in count.items():
        if c == 1:
            gk = (k[0],) + k[2:]
            nogroup[gk] = None if gk in nogroup else full[k + (0,)]
    nogroup = {k: v for k, v in nogroup.items() if v is not None}
    return full, count, nogroup


def page_confirmed_cells(rows):
    """(flow, ag, art, unit, country_raw, value) of every cell — member OR
    anchor — inside a member section that closes exactly. The page itself
    corroborates these; no vote may touch them."""
    confirmed = set()
    blocks = collections.defaultdict(list)
    for flow, ag, art, unit, ctry, v in rows:
        blocks[(flow, ag, art, unit)].append((ctry, v))
    for bk, seq in blocks.items():
        members = []
        for ctry, v in seq:
            if ctry and TOTAL_RE.search(ctry):
                if members and v is not None and \
                        abs(sum(x for _, x in members) - v) <= 0.001 * abs(v):
                    for c, x in members:
                        confirmed.add(bk + (c, x))
                    confirmed.add(bk + (ctry, v))
                members = []
                continue
            if v is not None:
                members.append((ctry, v))
    return confirmed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='db/uk_trade.duckdb')
    ap.add_argument('--out', default='reference/edge_column_repairs.csv')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    con = duckdb.connect(a.db, read_only=True)

    repairs = []
    stats = collections.Counter()
    for (vol, year), wvols in TARGETS.items():
        own_rows = fetch(con, 'country_obs', vol, year)
        confirmed = page_confirmed_cells(own_rows)
        own_full, own_count, _ = index_rows(own_rows)

        wit = {}          # name -> (full, count, nogroup)
        for eng, tbl in ENGINES.items():
            for wv in wvols:
                wit[f'{eng}:{wv}'] = index_rows(fetch(con, tbl, wv, year))

        occ_seen = collections.Counter()
        for flow, ag, art, unit, ctry, v in own_rows:
            k = (flow, norm(ag), norm(art), norm(unit), norm(ctry))
            occ = occ_seen[k]
            occ_seen[k] += 1
            if v is None:
                continue
            stats[f'{vol} cells'] += 1
            votes = collections.Counter()
            voters = {}
            for name, (wfull, wcount, wng) in wit.items():
                wv_val = None
                if wcount.get(k) == own_count[k]:
                    wv_val = wfull.get(k + (occ,))
                elif own_count[k] == 1 and k not in wcount:
                    wv_val = wng.get((k[0],) + k[2:])
                if wv_val is not None:
                    votes[wv_val] += 1
                    voters[name] = wv_val
            if not votes:
                stats[f'{vol} no witness'] += 1
                continue
            best, n = votes.most_common(1)[0]
            if n < 2:
                stats[f'{vol} lone witness'] += 1
                continue
            if best == v:
                stats[f'{vol} witnesses confirm'] += 1
                continue
            if (flow, ag, art, unit, ctry, v) in confirmed:
                stats[f'{vol} page-confirmed, kept'] += 1
                continue
            is_anchor = bool(ctry and TOTAL_RE.search(ctry))
            stats[f'{vol} REPAIRED ' + ('anchor' if is_anchor else 'member')] += 1
            repairs.append(dict(
                volume=vol, year=year, flow=flow, article_group=ag,
                article=art, country_raw=ctry, old_value=v, new_value=best,
                witnesses='; '.join(sorted(nm for nm, val in voters.items()
                                           if val == best))))

        # APPLICATION-GRANULARITY GUARD. The overlay key the consumers use is
        # (volume, year, group, article, country, old_value) — no unit, no
        # flow, no occurrence. If that key matches more rows in the volume-
        # year than this vote repaired, or the repairs disagree on the new
        # value, applying the overlay would rewrite rows the vote never saw.
        # Such groups are dropped entirely.
        own_key_count = collections.Counter(
            (ag, art, ctry, round(v)) for _, ag, art, unit, ctry, v in own_rows
            if v is not None)
        grouped = collections.defaultdict(list)
        for r in repairs:
            if r['volume'] != vol:
                continue
            grouped[(r['article_group'], r['article'], r['country_raw'],
                     round(r['old_value']))].append(r)
        for gk, grp in grouped.items():
            if len({g['new_value'] for g in grp}) > 1 or \
                    len(grp) != own_key_count[gk]:
                for g in grp:
                    repairs.remove(g)
                stats[f'{vol} dropped: overlay key ambiguous'] += len(grp)
            else:
                for g in grp[1:]:              # one CSV row serves all matches
                    repairs.remove(g)

    for k in sorted(stats):
        print(f'{k:38} {stats[k]:>7,}')

    print('\nlargest corrections:')
    for r in sorted(repairs, key=lambda r: -abs(r['new_value'] - r['old_value']))[:15]:
        print(f'  {r["volume"]} {r["flow"]:9} {r["old_value"]:>13,.0f} -> '
              f'{r["new_value"]:>13,.0f}  {r["country_raw"][:24]:24} '
              f'{r["article"][:30]}')

    if repairs and not a.dry_run:
        cols = ['volume', 'year', 'flow', 'article_group', 'article',
                'country_raw', 'old_value', 'new_value', 'witnesses']
        with open(a.out, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(repairs)
        print(f'\nwrote {a.out} ({len(repairs)} rows)')


if __name__ == '__main__':
    main()
