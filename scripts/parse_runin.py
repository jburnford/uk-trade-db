#!/usr/bin/env python3
"""Extract the RUN-IN country-detail format the tabular parser misses.

Some Annual-Statement pages print country detail not as <tr><td> tables but as
flowing text: a bold article header, optional ditto sub-article, then
'From <Country> ... <Unit>. <qty> £ <value>' lines with '„' ditto marks for
subsequent countries. parse_country.py only handles tables, so every commodity
in this format is silently dropped (Bacon/Asphalt/Bark in as_1881, etc.) — a
major recall gap the gold exposed. Flow is self-labelling: 'From' = import,
'To' = export.

Emits exports/runin_country.csv (country_obs schema) and validates a sample
against the Ghost Acres gold.
"""
import csv
import re
from collections import defaultdict
from pathlib import Path

BASE = Path('/home/jic823/uk_trade_db')
RAW = BASE / 'raw'

VOL_YEAR = re.compile(r'as_(\d{4})')
BOLD_HDR = re.compile(r'<b>\s*([A-Za-z][^:<]{1,80}?)\s*:?\s*</b>')
# a run-in country row: [From|„|"] Country  --leaders--  [Unit.] qty [£] value
ROW = re.compile(
    r'^\s*(?:(From|To)\s+|[„"”]\s*)?'
    r'([A-Z][A-Za-z .,\'()&-]{1,40}?)\s*'
    r'[-–—.\s]{3,}\s*'
    r'(?:([A-Za-z][A-Za-z. ]{0,10}?)\.?\s+)?'
    # qty, then an optional £ marker (which OCRs as a STANDALONE 1/l/I —
    # require trailing space so it can't eat a real leading digit of the
    # value, e.g. '90,048 190,991' keeps value 190,991), then value
    r'([\d,]{2,})\s*(?:£\s*|[1lI]\s+)?([\d,]{2,})?\s*$')
NUM = re.compile(r'[\d,]+')


def num(s):
    if not s:
        return None
    try:
        return int(s.replace(',', ''))
    except ValueError:
        return None


def flatten(text):
    """HTML-ish -> lines, keeping <b> headers on their own line."""
    text = re.sub(r'(?i)<br\s*/?>', '\n', text)
    text = re.sub(r'(?i)</?(td|tr|table|p|div)[^>]*>', '\n', text)
    # keep bold markers as sentinels
    text = re.sub(r'(?i)<b>', '\x01', text)
    text = re.sub(r'(?i)</b>', '\x02', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    return text


def parse_volume(md_path, year):
    rows = []
    txt = flatten(md_path.read_text(errors='ignore'))
    group = sub = unit = None
    flow = 'import'
    for raw_line in txt.split('\n'):
        line = raw_line.strip()
        if not line:
            continue
        # bold header (group) -- may be wrapped in \x01..\x02 sentinels
        mb = re.match(r'\x01\s*([A-Za-z][^:\x02]{1,80}?)\s*:?\s*\x02', line)
        if mb:
            group = re.sub(r'\s+', ' ', mb.group(1)).strip()
            sub = None
            unit = None
            # a header line may be followed on the same line by more content
            line = line.split('\x02', 1)[1].strip()
            if not line:
                continue
        line = line.replace('\x01', '').replace('\x02', '').strip()
        # ditto sub-article header: „ Something:  (no numbers)
        ms = re.match(r'^[„"”]\s*([A-Za-z][A-Za-z .,\'&()-]{1,50}?):\s*$', line)
        if ms and not NUM.search(line):
            sub = ms.group(1).strip()
            unit = None
            continue
        m = ROW.match(line)
        if not m:
            continue
        fromto, country, u, q, v = m.groups()
        if fromto == 'From':
            flow = 'import'
        elif fromto == 'To':
            flow = 'export'
        country = re.sub(r'\s+', ' ', country).strip(' .,')
        if u and u.strip(' .'):
            unit = u.strip(' .')
        qv, vv = num(q), num(v)
        if qv is None:
            continue
        # value-only blocks: qty column blank, single number is the value
        if vv is None and unit is None and country.lower() == 'total':
            vv, qv = qv, None
        if group is None:
            continue
        rows.append({
            'volume': f'as_{year}', 'flow': flow, 'duty': '',
            'article_group': group.upper(),
            'article': sub or '', 'country_raw': country,
            'unit': unit or '', 'year': year,
            'quantity': qv if qv is not None else '', 'value': vv if vv is not None else '',
        })
    return rows


def main():
    all_rows = []
    per_vol = defaultdict(int)
    for d in sorted(RAW.glob('as_*')):
        m = VOL_YEAR.search(d.name)
        if not m:
            continue
        year = int(m.group(1))
        mds = list(d.glob('*/*.md'))
        if not mds:
            continue
        r = parse_volume(mds[0], year)
        all_rows.extend(r)
        per_vol[year] = len(r)

    out = BASE / 'exports' / 'runin_country.csv'
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['volume', 'flow', 'duty', 'article_group',
                          'article', 'country_raw', 'unit', 'year', 'quantity', 'value'])
        w.writeheader()
        w.writerows(all_rows)
    print(f'run-in rows extracted: {len(all_rows):,}  -> {out}')
    print('by volume (top):', dict(sorted(per_vol.items(), key=lambda x: -x[1])[:8]))

    # ---- validate a sample against gold
    imp = [r for r in all_rows if r['flow'] == 'import']
    print(f'\nimport rows: {len(imp):,}')
    print('\n=== sample: as_1881 Bacon / Asphalt / Bark (gold: Bacon 3,876,053) ===')
    for r in all_rows:
        if r['year'] == 1881 and r['country_raw'] == 'TOTAL' and \
                any(k in r['article_group'] for k in ('BACON', 'ASPHALT', 'BARK')):
            print(f"  {r['article_group']:<22} {r['article']:<10} TOTAL "
                  f"q={r['quantity']} v={r['value']} unit={r['unit']}")


if __name__ == '__main__':
    main()
