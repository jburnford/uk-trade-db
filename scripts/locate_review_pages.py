#!/usr/bin/env python3
"""For every row in reports/country_review_queue.csv, find the PDF page
that printed the cell, via the Infinity result.json page index: a page
matches when it contains the row's formatted quantity or value AND the
country name (article text as tiebreak). Writes
reports/review_pages.json: row_key -> {pdf, page, bbox, hits}.

Row key = volume|flow|duty|group|article|country|year (matches the app
and grade integration).
"""
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_infinity import load_elements
from parse_abstract import BASE


def row_key(r):
    return '|'.join([r['volume'], r['flow'], r['duty'] or '', r['group'],
                     r['article'] or '', r['country'], str(r['year'])])


def page_index(volume):
    """[(page_no_1based, full_text, [(bbox, text), ...])] for a volume."""
    vdir = BASE / 'raw_infinity' / volume
    rjs = list(vdir.rglob('result.json'))
    if not rjs:
        return None, None
    pdf_stem = rjs[0].parent.name.replace('.pdf', '')
    pages = []
    for i, page in enumerate(load_elements(str(rjs[0]))):
        parts = []
        for el in page:
            t = el.get('text') or ''
            if t:
                parts.append((el.get('bbox'), t))
        pages.append((i + 1, ' '.join(t for _, t in parts), parts))
    return pdf_stem, pages


def fmt(v):
    try:
        f = float(v)
        return f'{f:,.0f}' if f == int(f) else None
    except (TypeError, ValueError):
        return None


def main():
    rows = list(csv.DictReader(open(BASE / 'reports' /
                                    'country_review_queue.csv')))
    by_vol = defaultdict(list)
    for r in rows:
        by_vol[r['volume']].append(r)

    out = {}
    for vol in sorted(by_vol):
        pdf_stem, pages = page_index(vol)
        if pages is None:
            continue
        n_found = 0
        for r in by_vol[vol]:
            qs = fmt(r['quantity'])
            vs = fmt(r['value'])
            country = (r['country'] or '').split(' : ')[0][:24]
            art = (r['article'] or r['group'] or '')[:18]
            best = None
            for pno, text, parts in pages:
                score = 0
                for s in (qs, vs):
                    if s and len(s) >= 4 and s in text:
                        score += 2
                if not score:
                    continue
                if country and country.lower() in text.lower():
                    score += 1
                if art and art.lower() in text.lower():
                    score += 1
                if best is None or score > best[0]:
                    # bbox of the element containing the number
                    bbox = None
                    for bb, t in parts:
                        if (qs and qs in t) or (vs and vs in t):
                            bbox = bb
                            break
                    best = (score, pno, bbox)
            if best and best[0] >= 2:
                out[row_key(r)] = {'pdf': pdf_stem, 'page': best[1],
                                   'bbox': best[2], 'score': best[0]}
                n_found += 1
        print(f'{vol}: located {n_found}/{len(by_vol[vol])}')

    dst = BASE / 'reports' / 'review_pages.json'
    json.dump(out, open(dst, 'w'))
    print(f'\n{len(out):,}/{len(rows):,} rows located -> {dst}')


if __name__ == '__main__':
    main()
