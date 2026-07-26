#!/usr/bin/env python3
"""Ingest the E&H British Imports Database into a versioned reference CSV.

The other gold checks in this repo (validate_gold.py, validate_vs_gold.py,
validate_gold_tiers.py) each read a hard-coded /mnt/c/.../Dropbox path and
commit nothing, so none of them is reproducible from a clean checkout. This
one commits a normalised extract plus a provenance record, so the comparison
can be re-run and audited without the Dropbox file.

Source: BritishImportsDatabase_EandH.xls -- a hand-keyed extract from the
relational database built with students from 2014 onward off CUST 5/1B (Kew)
and the ProQuest HCPP 'Annual Statement of Trade' series. Two commodities:
Tallow and Stearine annually 1800-1909, Rosin quinquennially 1800-1906, at
country level, quantity in hundredweights and value in pounds sterling.

The two '(raw)' sheets are the source of record. The wide summary sheets
('Tallow 1800-1866', 'Tallow 1865-1901') are derived from them and are in
TONS, not hundredweights; they are used here only as a hygiene cross-check.

Gold defects are carried through, not cleaned. Some years carry more than one
FROM_LOCATION='World' row -- 1875 has two that disagree (967,396 and 987,396
cwt), and several years carry VALUE=0 placeholder rows. Those are flagged in
world_rank / value_is_zero and listed in reports/gold_eandh_hygiene.csv so the
comparison can decide what to do with them in the open.

Writes:
    reference/gold_eandh.csv               -- one row per gold observation
    reference/gold_eandh.provenance.json   -- source hashes and row counts
    reports/gold_eandh_hygiene.csv         -- the gold's own defects
"""
import csv
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

BASE = Path('/home/jic823/uk_trade_db')
SRC = Path('/mnt/c/Users/jic823/Dropbox/2026/BritishImportsDatabase_EandH.xls')
OUT = BASE / 'reference' / 'gold_eandh.csv'
PROV = BASE / 'reference' / 'gold_eandh.provenance.json'
HYGIENE = BASE / 'reports' / 'gold_eandh_hygiene.csv'

RAW_SHEETS = ['Tallow (raw)', 'Rosin (raw)']
WIDE_SHEETS = ['Tallow 1800-1866', 'Tallow 1865-1901']

# the '(raw)' sheets share this header; assert it rather than trusting order
EXPECTED_HDR = ['[Row]', 'YEAR', 'COMMODITY_NAME', 'FROM_LOCATION',
                'TO_LOCATION', 'AMOUNT', 'UNIT_NAME', 'VALUE',
                'CURRENCY_NAME', 'NOTE', 'SERIES_NAME']

FIELDS = ['year', 'commodity', 'country_raw', 'country_norm', 'to_location',
          'quantity', 'unit', 'value', 'currency', 'series', 'note',
          'is_world', 'world_rank', 'value_is_zero', 'sheet', 'src_row']


def country_norm(s):
    """Casefold/punctuation normalisation only.

    Deliberately NOT the full canonicalisation -- that belongs in
    gold_country.py, where it is applied to BOTH sides at once. This is just
    enough to make 'Other Foreign Countries ' (trailing space, in the source)
    and 'Other Foreign Countries' the same string.
    """
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode()
    s = s.lower().replace('&', ' and ')
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def load_workbook():
    try:
        import xlrd
    except ImportError:
        sys.exit(
            'xlrd is required to read this legacy .xls (BIFF) file.\n'
            'Install it with:\n'
            '    python3 -m pip install --break-system-packages xlrd\n')
    if not SRC.exists():
        sys.exit(f'gold source not found: {SRC}')
    return xlrd.open_workbook(str(SRC))


def num(v):
    """Excel numeric cell -> float or None. Blank strings become None."""
    if v == '' or v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def read_raw(book):
    rows = []
    for name in RAW_SHEETS:
        sh = book.sheet_by_name(name)
        hdr = [sh.cell_value(0, c) for c in range(sh.ncols)]
        if hdr != EXPECTED_HDR:
            sys.exit(f'unexpected header in {name!r}:\n  {hdr}\n'
                     f'expected:\n  {EXPECTED_HDR}')
        for r in range(1, sh.nrows):
            v = [sh.cell_value(r, c) for c in range(sh.ncols)]
            year = num(v[1])
            if year is None:
                continue
            country = str(v[3])
            rows.append({
                'year': int(year),
                'commodity': str(v[2]).strip(),
                'country_raw': country,
                'country_norm': country_norm(country),
                'to_location': str(v[4]).strip(),
                'quantity': num(v[5]),
                'unit': str(v[6]).strip(),
                'value': num(v[7]),
                'currency': str(v[8]).strip(),
                'series': str(v[10]).strip(),
                'note': str(v[9]).strip(),
                'is_world': int(country_norm(country) == 'world'),
                'world_rank': '',
                'value_is_zero': '',
                'sheet': name,
                'src_row': int(num(v[0]) or r),
            })
    return rows


def mark_world_rows(rows):
    """Rank the World rows within each (sheet, commodity, year), in file order.

    A year with world_rank > 1 has more than one national total in the gold.
    That is a defect in the gold, not in us, and the validator needs to see it
    rather than silently taking whichever row it hit first.
    """
    seen = {}
    hygiene = []
    for row in rows:
        if not row['is_world']:
            continue
        key = (row['sheet'], row['commodity'], row['year'])
        seen[key] = seen.get(key, 0) + 1
        row['world_rank'] = seen[key]
        row['value_is_zero'] = int(row['value'] == 0)
    dupes = {k: n for k, n in seen.items() if n > 1}
    for row in rows:
        if not row['is_world']:
            continue
        key = (row['sheet'], row['commodity'], row['year'])
        if key in dupes:
            hygiene.append({
                'sheet': row['sheet'], 'commodity': row['commodity'],
                'year': row['year'], 'world_rank': row['world_rank'],
                'n_world_rows': dupes[key], 'quantity': row['quantity'],
                'value': row['value'], 'src_row': row['src_row'],
                'defect': 'multiple World rows for this commodity-year',
            })
    return hygiene


def country_sum_check(rows, hygiene):
    """Does each year's country detail sum to its World row? (gold-internal)

    This is the gold checking itself. Where it fails, the gold is internally
    inconsistent before our data enters the picture at all -- 1875 tallow is
    the clean case: the country rows sum to 967,396, agreeing with one of the
    two World rows and refuting the other.
    """
    by_year = {}
    for row in rows:
        key = (row['sheet'], row['commodity'], row['year'])
        by_year.setdefault(key, {'world': [], 'parts': []})
        by_year[key]['world' if row['is_world'] else 'parts'].append(row)
    for key, grp in sorted(by_year.items()):
        if not grp['world'] or not grp['parts']:
            continue
        sq = sum(r['quantity'] or 0 for r in grp['parts'])
        sv = sum(r['value'] or 0 for r in grp['parts'])
        for w in grp['world']:
            wq, wv = w['quantity'], w['value']
            dq = abs(sq - wq) / wq if wq else None
            dv = abs(sv - wv) / wv if wv else None
            if (dq is not None and dq > 0.001) or (dv is not None and dv > 0.001):
                hygiene.append({
                    'sheet': key[0], 'commodity': key[1], 'year': key[2],
                    'world_rank': w['world_rank'],
                    'n_world_rows': len(grp['world']),
                    'quantity': wq, 'value': wv, 'src_row': w['src_row'],
                    'defect': (f'country rows sum to q={sq:.0f} v={sv:.0f}, '
                               f'World row does not close'),
                })


def wide_sheet_check(book, rows):
    """Cross-check the ingest against the workbook's own wide summary sheets.

    The wide sheets are in TONS (20 cwt), carry their own 'Test'/'Error check'
    row, and are hand-maintained separately from the raw rows. Agreement is
    reassurance that the raw sheet was read correctly; disagreement is a note,
    not a failure -- the wide sheets are derived and lag the raw data.
    """
    world = {}
    for r in rows:
        if r['sheet'] == 'Tallow (raw)' and r['is_world'] and r['value']:
            world[r['year']] = r['quantity']
    notes = []
    for name in WIDE_SHEETS:
        try:
            sh = book.sheet_by_name(name)
        except Exception:
            continue
        years = [num(sh.cell_value(0, c)) for c in range(1, sh.ncols)]
        wrow = None
        for r in range(sh.nrows):
            lab = str(sh.cell_value(r, 0)).strip().lower()
            if lab.startswith('world'):
                wrow = r
                break
        if wrow is None:
            continue
        for i, y in enumerate(years):
            if y is None:
                continue
            tons = num(sh.cell_value(wrow, i + 1))
            cwt = world.get(int(y))
            if tons is None or cwt is None:
                continue
            if abs(tons * 20 - cwt) > max(20.0, 0.001 * cwt):
                notes.append(f'{name} {int(y)}: wide={tons * 20:.0f} cwt, '
                             f'raw={cwt:.0f} cwt')
    return notes


def main():
    book = load_workbook()
    rows = read_raw(book)
    hygiene = mark_world_rows(rows)
    country_sum_check(rows, hygiene)
    wide_notes = wide_sheet_check(book, rows)

    rows.sort(key=lambda r: (r['sheet'], r['year'], r['src_row']))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    HYGIENE.parent.mkdir(parents=True, exist_ok=True)
    hy_fields = ['sheet', 'commodity', 'year', 'world_rank', 'n_world_rows',
                 'quantity', 'value', 'src_row', 'defect']
    with open(HYGIENE, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=hy_fields)
        w.writeheader()
        w.writerows(sorted(hygiene, key=lambda h: (h['sheet'], h['year'])))

    st = SRC.stat()
    years = sorted({r['year'] for r in rows})
    prov = {
        'source_path': str(SRC),
        'source_sha256': sha256(SRC),
        'source_bytes': st.st_size,
        'source_mtime': st.st_mtime,
        'output_path': str(OUT.relative_to(BASE)),
        'output_sha256': sha256(OUT),
        'sheets_read': RAW_SHEETS,
        'n_rows': len(rows),
        'year_min': years[0],
        'year_max': years[-1],
        'commodities': sorted({r['commodity'] for r in rows}),
        'units': sorted({r['unit'] for r in rows}),
        'series': sorted({r['series'] for r in rows}),
        'n_world_rows': sum(r['is_world'] for r in rows),
        'n_hygiene_flags': len(hygiene),
        'wide_sheet_disagreements': wide_notes,
    }
    PROV.write_text(json.dumps(prov, indent=2) + '\n')

    print(f'{len(rows):,} gold rows -> {OUT.relative_to(BASE)}')
    print(f'  years {years[0]}-{years[-1]}, '
          f'{len(prov["commodities"])} commodities, '
          f'{prov["n_world_rows"]} World rows')
    print(f'  {len(hygiene)} hygiene flags -> {HYGIENE.relative_to(BASE)}')
    if wide_notes:
        print(f'  {len(wide_notes)} wide-sheet disagreements (see provenance):')
        for n in wide_notes[:10]:
            print(f'    {n}')
    print(f'  source sha256 {prov["source_sha256"][:16]}... '
          f'-> {PROV.relative_to(BASE)}')


if __name__ == '__main__':
    main()
