#!/usr/bin/env python3
"""Second key: run the Infinity-Parser2 output through the SAME abstract-table
parser as the Chandra markdown, into infinity_obs.

Infinity's result.json is a list of pages, each a list of
{bbox, category, text} elements. We rebuild a pseudo-markdown stream per
volume (titles/headers/text as caption zones, table elements as <table>
blocks, in reading order) so parse_abstract.parse_volume applies identical
caption classification and row logic — differences between the two keys then
reflect OCR, not parser asymmetry.
"""
import json
import tempfile
from pathlib import Path

import duckdb

import sys
sys.path.insert(0, str(Path(__file__).parent))
from parse_abstract import parse_volume, BASE


def load_elements(result_json):
    """Load pages; on malformed JSON (dropped bytes in 5 of 34 files),
    salvage every well-formed {bbox, category, text} object in order."""
    raw = open(result_json).read()
    try:
        return json.load(open(result_json))
    except json.JSONDecodeError:
        dec = json.JSONDecoder()
        els, i, n = [], 0, len(raw)
        while True:
            j = raw.find('{"bbox"', i)
            if j < 0:
                break
            try:
                obj, end = dec.raw_decode(raw, j)
                els.append(obj)
                i = end
            except json.JSONDecodeError:
                i = j + 7
        print(f'  [salvaged {len(els)} elements from malformed JSON]')
        return [els]                    # single pseudo-page, order preserved


def pseudo_md(result_json):
    parts = []
    for page in load_elements(result_json):
        for el in page:
            cat, text = el.get('category'), el.get('text') or ''
            if not text:
                continue
            if cat == 'table':
                if not text.lstrip().startswith('<table'):
                    text = '<table border="1">' + text + '</table>'
                parts.append(text)
            elif cat in ('title', 'header', 'text'):
                parts.append(text)
    return '\n\n'.join(parts)


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'))
    con.execute('DROP TABLE IF EXISTS infinity_obs')
    con.execute('''CREATE TABLE infinity_obs (
        volume VARCHAR, flow VARCHAR, measure VARCHAR,
        article_group VARCHAR, article VARCHAR, unit VARCHAR,
        year INTEGER, value DOUBLE, raw_unparsed VARCHAR, row_seq INTEGER)''')
    for vdir in sorted((BASE / 'raw_infinity').iterdir()):
        results = list(vdir.rglob('result.json'))
        if not results:
            continue
        md = pseudo_md(results[0])
        with tempfile.NamedTemporaryFile('w', suffix='.md',
                                         delete=False) as f:
            f.write(md)
            tmp = f.name
        nt, no = parse_volume(Path(tmp), con, vdir.name,
                              table='infinity_obs')
        Path(tmp).unlink()
        print(f'{vdir.name}: {nt} tables, {no:,} obs')
    con.commit()
    print('\ntotal infinity_obs:',
          con.execute('SELECT count(*) FROM infinity_obs').fetchone()[0])


if __name__ == '__main__':
    main()
