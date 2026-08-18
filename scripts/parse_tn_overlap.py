#!/usr/bin/env python3
"""The tn_ annuals' comparative years, parsed into SEPARATE tables.

parse_country.py admits the Trade-and-Navigation annuals (tn_1895, tn_1899,
tn_1901) only for years OUTSIDE the as_* span, because dropping their
overlapping years straight into country_obs was measured DESTRUCTIVE for the
import pipeline, which neither dedupes nor arbitrates a second witness
(reports/tn_volumes_findings.md). That leaves the overlap unread even where it
is the best print of a year anyone has:

    tn_1901 prints 1896-1900 five years per row. Its 1900 column is at the
    page edge (already ingested, weak); its 1899 column is MID-TABLE -- the
    only non-edge print of 1899 in the corpus, and the year the export series
    cannot otherwise rescue (as_1899's own edge column, ~20% corroborated).
    tn_1899 prints 1894-98: a further mid-table witness for 1894-97.
    tn_1895 is a single-year annual for 1894.

This script parses exactly those overlapping rows -- with the SAME corpus
vocabulary the main parsers use (seeded from as_* only, so nothing about the
existing parse changes) -- into

    country_obs_tn       Chandra   (raw/)
    country_obs_tn_inf   Infinity  (raw_infinity/)

country_obs / country_obs_inf are NOT touched. Consumers that know how to
arbitrate witnesses (the export series scripts, via PRIMARY_OVERRIDE and the
edge-column vote) opt in by unioning these tables; the import pipeline does
not see them.

Usage: python3 scripts/parse_tn_overlap.py
"""
import sys
import tempfile
from collections import Counter
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from parse_abstract import BASE
from parse_country import (AS_SPAN, COLS, MONTHLY, build_vocab,
                           parse_volume_countries, volume_year)
from parse_infinity import pseudo_md

DDL = '''CREATE TABLE {} (
        volume VARCHAR, flow VARCHAR, duty VARCHAR,
        article_group VARCHAR, article VARCHAR, country_raw VARCHAR,
        unit VARCHAR, year INTEGER, quantity DOUBLE, value DOUBLE,
        consumption DOUBLE, duty_received DOUBLE, row_seq INTEGER)'''


def overlap_rows(rows):
    yi = COLS.index('year')
    return [r for r in rows if r[yi] and AS_SPAN[0] <= r[yi] <= AS_SPAN[1]]


def run(con, table, sources):
    """sources: [(md_path, volume)] for every wanted volume, as_* and tn_*."""
    con.execute(f'DROP TABLE IF EXISTS {table}')
    con.execute(DDL.format(table))
    vols, all_seeds = [], []
    for md, volume in sources:
        year = volume_year(volume)
        seed = []
        parse_volume_countries(md, volume, year, seed)
        if volume.startswith('as_'):
            all_seeds.extend(seed)          # vocabulary from as_* ONLY
            continue
        freq = Counter(o[5].casefold() for o in seed
                       if o[5] and o[5] != 'TOTAL' and ' : ' not in o[5])
        names = frozenset(n for n, c in freq.items() if c >= 4)
        vols.append((md, volume, year, names))
    group_vocab, sub_vocab = build_vocab(all_seeds)
    print(f'{table}: vocabulary {len(group_vocab)} groups, '
          f'{len(sub_vocab)} sub-articles')
    total = 0
    for md, volume, year, names in vols:
        out = []
        nt = parse_volume_countries(md, volume, year, out, names,
                                    group_vocab, sub_vocab)
        keep = overlap_rows(out)
        if keep:
            df = pd.DataFrame(keep, columns=COLS)   # noqa: F841
            con.execute(f'INSERT INTO {table} SELECT * FROM df')
        total += len(keep)
        by = Counter(o[COLS.index('year')] for o in keep)
        print(f'  {volume}: {nt} tables, {len(out):,} rows, '
              f'{len(keep):,} in overlap  {dict(sorted(by.items()))}')
    con.commit()
    print(f'  {table}: {total:,} rows\n')


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'))

    def wanted(name):
        return name.startswith('as_') or (name.startswith('tn_')
                                          and name not in MONTHLY)

    # Chandra
    ch = []
    for p in sorted((BASE / 'raw').iterdir()):
        if wanted(p.name):
            mds = list(p.rglob('*.md'))
            if mds:
                ch.append((mds[0], p.name))
    run(con, 'country_obs_tn', ch)

    # Infinity: pseudo-markdown from result.json, via temp files
    tmps, inf = [], []
    for p in sorted((BASE / 'raw_infinity').iterdir()):
        if not wanted(p.name):
            continue
        rjs = list(p.rglob('result.json'))
        if not rjs:
            continue
        tf = tempfile.NamedTemporaryFile('w', suffix='.md', delete=False)
        tf.write(pseudo_md(str(rjs[0])))
        tf.close()
        tmps.append(Path(tf.name))
        inf.append((Path(tf.name), p.name))
    try:
        run(con, 'country_obs_tn_inf', inf)
    finally:
        for t in tmps:
            t.unlink()


if __name__ == '__main__':
    main()
