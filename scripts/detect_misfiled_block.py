"""A commodity-year reads nodata; its block is sitting under another group.

`reports/late_era_group_staleness.md` established the mechanism: the parser
carries a sticky group that goes stale, so from as_1897 the article `Dry` is
filed under GLASS / HATS OR BONNETS / HEMP instead of HIDES. The rows are
parsed. They are simply attached to the wrong commodity, and the real one reads
`nodata`.

Two fixes were tried and reverted (regenerating the group authority, -130
cells; containment matching in the sticky repair, -20). Both failed for the same
reason: they decide the group from LABELS, and the labels are what is broken.

This decides it from ARITHMETIC instead, and from both sides at once:

    for a commodity-year with an anchor and NO origin data,
    find country_obs rows with the SAME ARTICLE in the SAME YEAR under a
    DIFFERENT group, and ask whether they sum to that anchor.

The article is the reliable half of the label — that is the premise
`repair_groups.py` is built on — and the anchor is an independently printed
figure the misfiled rows cannot have been fitted to. A block that closes an
anchor it is not currently attached to is a misfile, not a coincidence.

Reports the volume and row_seq range so the repair can be written as a
`group_repairs.csv` `new_group` row over exactly that span.

    python3 scripts/detect_misfiled_block.py [--tol 0.02] [--min-gbp 20000]

Writes reports/misfiled_blocks.csv, best first.
"""
import argparse
import csv
from collections import defaultdict
from pathlib import Path

import duckdb

BASE = Path(__file__).resolve().parents[1]

_UNITS = (('CWT', ('cwt', 'cut', 'cct', 'cict', 'ciot')),
          ('LB', ('lb', 'ib')), ('TON', ('ton', 'tun')),
          ('GAL', ('gallon',)), ('NUM', ('number', 'no')),
          ('BUSH', ('bushel',)), ('QTR', ('quarter', 'qr')),
          ('YARD', ('yard',)), ('LOAD', ('load',)), ('PAIR', ('pair',)),
          ('VALUE', ('value', 'gbp', '£')))


def _ukey(u):
    s = ''.join(ch for ch in (u or '').lower() if ch.isalpha() or ch == '£')
    if not s:
        return ''
    for key, stems in _UNITS:
        if any(s.startswith(t) for t in stems):
            return key
    return s[:6].upper()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tol', type=float, default=0.02)
    ap.add_argument('--min-gbp', type=float, default=20_000)
    a = ap.parse_args()

    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)
    con.create_function('ukey', _ukey, ['VARCHAR'], 'VARCHAR')

    # NOTE (2026-08-03): the orphan list MUST come from the PAYLOAD, not from
    # country_year_final. The first version of this screen read the database
    # and reported 312 "misfiled blocks" - Tea 1894-97 under SPIRITS,
    # Petroleum under PARAFFINE, Potatoes under PORK. Every one of them is
    # ALREADY re-homed by build_viz_payload's country-cell sticky repair, and
    # every one of those commodity-years reads 1.0000 in the payload. The
    # database keeps the stale group; the payload fixes it. Same trap recorded
    # for detect_column_crossing.py and detect_lost_vote.py in
    # reports/lost_vote_findings.md: a DB-level screen measures something the
    # baseline does not. Run scripts/misfiled_from_payload.py instead.
    orphans = con.execute("""
        WITH q AS (
            SELECT lower(trim(article)) AS art, ukey(unit) AS uk, year,
                   max(value) AS t1, any_value(article_group) AS grp
            FROM consensus
            WHERE flow='import' AND measure='quantity' AND value > 0
            GROUP BY 1, 2, 3),
        have AS (
            SELECT DISTINCT lower(trim(article)) AS art, year
            FROM country_year_final WHERE quantity > 0)
        SELECT q.art, q.grp, q.uk, q.year, q.t1
        FROM q LEFT JOIN have ON q.art = have.art AND q.year = have.year
        WHERE have.art IS NULL AND q.t1 > 0
    """).fetchall()

    # every parsed block, keyed (article, year), with its volume/group/seq span
    blocks = defaultdict(list)
    for tbl in ('country_obs', 'country_obs_inf'):
        for art, y, vol, grp, uk, s, n, lo, hi in con.execute(f"""
                SELECT lower(trim(article)), year, volume,
                       upper(trim(coalesce(article_group,''))), ukey(unit),
                       sum(quantity), count(*), min(row_seq), max(row_seq)
                FROM {tbl}
                WHERE flow='import' AND quantity > 0
                  AND lower(trim(coalesce(country_raw,''))) NOT LIKE 'total%'
                GROUP BY 1, 2, 3, 4, 5""").fetchall():
            blocks[(art, y)].append((vol, grp, uk, s, n, lo, hi, tbl))

    out = []
    for art, grp, uk, y, t1 in orphans:
        for vol, bgrp, buk, s, n, lo, hi, tbl in blocks.get((art, y), ()):
            if buk and uk and buk != uk:
                continue
            if not s or abs(s - t1) > a.tol * t1:
                continue
            out.append({'ratio': round(s / t1, 5), 'article': art,
                        'anchor_group': grp or '', 'filed_under': bgrp,
                        'unit': uk, 'year': y, 'volume': vol, 'engine': tbl,
                        'block_sum': round(s), 't1': round(t1),
                        'n_rows': n, 'seq_start': lo, 'seq_end': hi})

    # one row per (article, year): the closest-closing block
    best = {}
    for r in out:
        k = (r['article'], r['year'])
        if k not in best or abs(r['ratio'] - 1) < abs(best[k]['ratio'] - 1):
            best[k] = r
    rows = sorted(best.values(), key=lambda r: -r['t1'])

    dest = BASE / 'reports' / 'misfiled_blocks.csv'
    with open(dest, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ['article'])
        w.writeheader()
        w.writerows(rows)
    print(f'{len(orphans):,} anchors with no origin data in their year; '
          f'{len(best)} have a block under ANOTHER group that closes them '
          f'-> reports/misfiled_blocks.csv')
    for r in rows[:25]:
        print(f"   {r['ratio']:.4f} {r['article'][:28]:28} {r['year']} "
              f"{r['anchor_group'][:16]:16} <- filed under "
              f"{r['filed_under'][:22]:22} {r['volume']} seq {r['seq_start']}-{r['seq_end']}")


if __name__ == '__main__':
    main()
