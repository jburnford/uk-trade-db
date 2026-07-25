#!/usr/bin/env python3
"""Second key for Tier 2: run the Infinity-Parser2 output through the SAME
country-section parser (parse_country.parse_volume_countries) via the
pseudo-markdown stream, into country_obs_inf.

Usage: python3 parse_country_infinity.py [volume_name ...]   (as_* only)
"""
import sys
import tempfile
from collections import Counter
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).parent))
from parse_abstract import BASE
from parse_country import build_vocab, bulk_insert, parse_volume_countries
from parse_infinity import pseudo_md


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'))
    con.execute('DROP TABLE IF EXISTS country_obs_inf')
    con.execute('''CREATE TABLE country_obs_inf (
        volume VARCHAR, flow VARCHAR, duty VARCHAR,
        article_group VARCHAR, article VARCHAR, country_raw VARCHAR,
        unit VARCHAR, year INTEGER, quantity DOUBLE, value DOUBLE,
        consumption DOUBLE, duty_received DOUBLE, row_seq INTEGER)''')
    wanted = set(sys.argv[1:])
    # pass 1 over all volumes -> country names per volume + corpus vocab
    vols = []
    all_seeds = []
    for vdir in sorted((BASE / 'raw_infinity').iterdir()):
        if not vdir.name.startswith('as_') or (wanted and vdir.name not in wanted):
            continue
        rjs = list(vdir.rglob('result.json'))
        if not rjs:
            continue
        volume = vdir.name
        year = int(volume[-4:])
        md = pseudo_md(str(rjs[0]))
        with tempfile.NamedTemporaryFile('w', suffix='.md',
                                         delete=False) as tf:
            tf.write(md)
            tmp = Path(tf.name)
        seed = []
        parse_volume_countries(tmp, volume, year, seed)
        freq = Counter(o[5].casefold() for o in seed
                       if o[5] and o[5] != 'TOTAL' and ' : ' not in o[5])
        names = frozenset(n for n, c in freq.items() if c >= 4)
        vols.append((tmp, volume, year, names))
        all_seeds.extend(seed)
    group_vocab, sub_vocab = build_vocab(all_seeds)
    print(f'vocabulary: {len(group_vocab)} group names, '
          f'{len(sub_vocab)} sub-article names\n')
    for tmp, volume, year, names in vols:
        try:
            out = []
            nt = parse_volume_countries(tmp, volume, year, out, names,
                                        group_vocab, sub_vocab)
        finally:
            tmp.unlink()
        if out:
            bulk_insert(con, 'country_obs_inf', out)
        print(f'{volume}: {nt} tables, {len(out):,} rows')
    con.commit()
    print('\ntotal country_obs_inf:',
          con.execute('SELECT count(*) FROM country_obs_inf').fetchone()[0])


if __name__ == '__main__':
    main()
