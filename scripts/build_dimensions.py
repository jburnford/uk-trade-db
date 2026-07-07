#!/usr/bin/env python3
"""Build dimension tables with stable IDs for the UK trade database.

commodity_id: slug of normalized (group, article), stable across years and
re-parses because it derives from the text, not insertion order. Raw OCR
strings map to IDs via commodity_alias; human merge decisions live in
reference/commodity_merges.csv (alias_id -> canonical_id) and are applied on
top — same authority-file pattern as the TTJ port normalization.

country dim is created with the same design, populated in Tier 2 (country-
detail tables).
"""
import csv
import re
import unicodedata
from pathlib import Path

import duckdb

BASE = Path('/home/jic823/uk_trade_db')
MERGES = BASE / 'reference' / 'commodity_merges.csv'
COUNTRY_MERGES = BASE / 'reference' / 'country_merges.csv'


def norm(s):
    if not s:
        return ''
    s = s.replace('&amp;', '&')
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = s.lower()
    s = re.sub(r'&', ' and ', s)
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    s = re.sub(r'\b(viz|etc|ie|eg)\b', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def slug(group, article):
    g, a = norm(group), norm(article)
    base = f'{g} {a}'.strip() if g else a
    return re.sub(r'\s+', '-', base)[:80]


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'))
    rows = con.execute(
        'SELECT DISTINCT article_group, article FROM abstract_obs').fetchall()

    merges = {}
    if MERGES.exists():
        for r in csv.DictReader(open(MERGES)):
            merges[r['alias_id']] = r['canonical_id']

    # auto-merge IDs whose slugs differ only in word spacing
    # ("dye-woods-logwood" == "dyewoods-logwood")
    slugs = {}
    for g, a in rows:
        slugs[(g, a)] = slug(g, a)
    condensed = {}
    for cid in sorted(set(slugs.values())):
        condensed.setdefault(cid.replace('-', ''), cid)
    alias = []
    for g, a in rows:
        cid = condensed[slugs[(g, a)].replace('-', '')]
        cid = merges.get(cid, cid)
        alias.append((g, a, cid))

    con.execute('DROP TABLE IF EXISTS commodity_alias')
    con.execute('''CREATE TABLE commodity_alias (
        article_group VARCHAR, article VARCHAR, commodity_id VARCHAR)''')
    con.executemany('INSERT INTO commodity_alias VALUES (?,?,?)', alias)

    con.execute('DROP TABLE IF EXISTS commodity')
    con.execute('''CREATE TABLE commodity AS
        SELECT ca.commodity_id,
               min(coalesce(o.article_group || ' : ', '') || o.article) AS label,
               min(o.year) AS first_year, max(o.year) AS last_year,
               count(*) AS n_obs
        FROM abstract_obs o
        JOIN commodity_alias ca
          ON o.article IS NOT DISTINCT FROM ca.article
         AND o.article_group IS NOT DISTINCT FROM ca.article_group
        GROUP BY 1''')

    con.execute('DROP TABLE IF EXISTS country')
    con.execute('''CREATE TABLE country (
        country_id VARCHAR PRIMARY KEY, label VARCHAR,
        region VARCHAR, notes VARCHAR)''')
    con.execute('DROP TABLE IF EXISTS country_alias')
    con.execute('''CREATE TABLE country_alias (
        raw_name VARCHAR, volume VARCHAR, country_id VARCHAR)''')

    # populate from Tier 2 country_obs when present; port-breakdown rows
    # ("United States of America : On the Atlantic") map to the country
    has_cobs = con.execute("""SELECT count(*) FROM information_schema.tables
        WHERE table_name='country_obs'""").fetchone()[0]
    if has_cobs:
        cmerges = {}
        if COUNTRY_MERGES.exists():
            for r in csv.DictReader(open(COUNTRY_MERGES)):
                cmerges[r['alias_id']] = r['canonical_id']
        raw_names = [r[0] for r in con.execute(
            """SELECT DISTINCT country_raw FROM country_obs
               WHERE country_raw IS NOT NULL
                 AND country_raw != 'TOTAL'""").fetchall()]
        c_alias = []
        seen = {}
        for rn in raw_names:
            base = rn.split(' : ')[0]
            cid = re.sub(r'\s+', '-', norm(base))[:60]
            if not cid:
                continue
            cid = cmerges.get(cid, cid)
            c_alias.append((rn, '', cid))
            seen.setdefault(cid, base)
        con.executemany('INSERT INTO country_alias VALUES (?,?,?)', c_alias)
        con.executemany('INSERT INTO country VALUES (?,?,NULL,NULL)',
                        [(cid, lab) for cid, lab in sorted(seen.items())])
        print(f'countries: {len(seen)} canonical IDs from '
              f'{len(c_alias)} raw names')

    n_c = con.execute('SELECT count(*) FROM commodity').fetchone()[0]
    n_a = con.execute('SELECT count(*) FROM commodity_alias').fetchone()[0]
    print(f'commodities: {n_c} canonical IDs from {n_a} raw (group, article) strings')
    print('\nsample wood/timber commodity IDs:')
    for r in con.execute("""SELECT commodity_id, label, first_year, last_year, n_obs
            FROM commodity WHERE commodity_id LIKE '%wood%' OR
            commodity_id LIKE '%timber%' ORDER BY n_obs DESC LIMIT 12""").fetchall():
        print(' ', r)

    # cross-era continuity check: commodities observed in all three volumes
    span = con.execute('''SELECT count(*) FROM (
        SELECT ca.commodity_id FROM abstract_obs o JOIN commodity_alias ca
          ON o.article IS NOT DISTINCT FROM ca.article
         AND o.article_group IS NOT DISTINCT FROM ca.article_group
        GROUP BY 1 HAVING count(DISTINCT o.volume) = 3)''').fetchone()[0]
    print(f'\ncommodity IDs present in all of 1872/1881/1891 volumes: {span}')

    con.commit()


if __name__ == '__main__':
    main()
