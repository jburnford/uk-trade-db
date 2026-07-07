#!/usr/bin/env python3
"""Extract two-up (side-by-side) country-detail tables the parser mishandles.

KEY STRUCTURE (learned from the OCR): a two-up table is TWO INDEPENDENT
vertical streams printed side by side; they are NOT row-aligned by commodity
(the left column can be finishing WINE while the right is mid-way through
Worsted Yarn). So we split each row into a left half and a right half by
COLUMN position (expanding colspan), concatenate each column top-to-bottom,
and parse each stream LINEARLY as an ordinary single-column country detail.

Header detection does not trust OCR <b> markup: a group header is an
ALL-CAPS label ending ':' ; a sub-article is a mixed-case label ending ':' ;
a data row is 'From|To|»|„ Country ... qty [£] value'. Flow is sticky:
'To'=export, 'From'=import, '»'/'„' inherit the column's current flow.

Emits exports/twoup_country.csv; validates import TOTALs vs the gold.
"""
import csv
import re
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

BASE = Path('/home/jic823/uk_trade_db')
RAW = BASE / 'raw'
NUM = re.compile(r'^[\d,]+$')
UNIT = re.compile(r'\b(Cwts?|Tons?|Loads?|Gallons?|Lbs?|Number|Pieces?|Qrs?|Bushels?)\b', re.I)
DITTO = '»„"”'


class Tables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables, self.tbl, self.row, self.buf, self.span = [], None, None, [], 1

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.tbl = []
        elif tag == 'tr' and self.tbl is not None:
            self.row = []
        elif tag == 'td' and self.row is not None:
            self.buf = []
            self.span = int(dict(attrs).get('colspan', 1) or 1)

    def handle_endtag(self, tag):
        if tag == 'td' and self.row is not None:
            txt = re.sub(r'\s+', ' ', ''.join(self.buf)).strip()
            self.row.append((txt, self.span))
        elif tag == 'tr' and self.row is not None:
            if self.row:
                self.tbl.append(self.row)
            self.row = None
        elif tag == 'table' and self.tbl is not None:
            if self.tbl:
                self.tables.append(self.tbl)
            self.tbl = None

    def handle_data(self, data):
        if self.row is not None:
            self.buf.append(data)


def expand(row):
    """Expand colspan -> flat list of column slots (text in first slot)."""
    slots = []
    for txt, span in row:
        slots.append(txt)
        slots.extend([''] * (span - 1))
    return slots


def is_abstract(table):
    """5-year abstract table: rows carry a label + ~5 numeric cells."""
    numcount = []
    for row in table:
        n = sum(1 for txt, _ in row if NUM.match(txt.replace(' ', '')))
        if any(txt.strip() for txt, _ in row):
            numcount.append(n)
    if not numcount:
        return True
    big = sum(1 for n in numcount if n >= 4)
    return big > 0.4 * len(numcount)


def triples_from_half(cells):
    """From a half-row's ordered cells -> (label, [nums]) or None."""
    label, nums = None, []
    for c in cells:
        c = c.strip()
        if not c:
            continue
        cc = c.replace(' ', '')
        if NUM.match(cc):
            nums.append(cc.replace(',', ''))
        elif c in ('-', '£') or UNIT.fullmatch(c):
            continue
        elif label is None:
            label = c
        else:
            break
    return (label, nums) if label else None


def parse_column_stream(stream, year, out, carry=None):
    """stream: list of (label,[nums]); parse linearly with sticky state.
    `carry` seeds the group/sub/flow from the previous table's SAME column so a
    commodity block that runs past a page break keeps its header (which prints
    once). Returns the ending state to carry into the next table."""
    grp = carry['grp'] if carry else None
    sub = carry['sub'] if carry else None
    unit = carry['unit'] if carry else None
    flow = carry['flow'] if carry else 'import'
    for label, nums in stream:
        lab = label.strip()
        is_ditto = lab[:1] in DITTO or lab[:2] == ',,'
        core = re.sub(r'^[' + DITTO + r',\s]+', '', lab).strip()
        m_ft = re.match(r'^(From|To)\s+(.*)$', core, re.I)
        # header?  (no numbers, ends with ':')
        if core.endswith(':') and not nums:
            name = core.rstrip(': ').strip()
            letters = [c for c in name if c.isalpha()]
            caps = sum(c.isupper() for c in letters) / max(len(letters), 1)
            if caps >= 0.6 and not is_ditto:            # ALL-CAPS group header
                name = re.sub(r'\s*\(cont.*?\)\s*$', '', name, flags=re.I)  # merge (Cont'd)
                grp, sub, unit = name.upper(), None, None
            else:                                        # sub-article
                sub = name
                unit = None
            continue
        if not nums or grp is None:
            continue
        um = UNIT.search(lab)
        if um:
            unit = um.group(1)
        if m_ft:
            flow = 'import' if m_ft.group(1).lower() == 'from' else 'export'
            country = m_ft.group(2)
        else:
            country = core
        country = UNIT.sub('', country)
        country = re.sub(r'[-–—.\s]+$', '', country).strip(' .')
        if not country:
            continue
        q = int(nums[0]) if nums else None
        v = int(nums[1]) if len(nums) > 1 else None
        if q is not None and q > 1e12:           # OCR-glued junk (overflows BIGINT)
            continue
        out.append({'volume': f'as_{year}', 'flow': flow, 'duty': '',
                    'article_group': grp, 'article': sub or '',
                    'country_raw': country, 'unit': unit or '', 'year': year,
                    'quantity': q if q is not None else '',
                    'value': v if v is not None else ''})
    return {'grp': grp, 'sub': sub, 'unit': unit, 'flow': flow}


def parse_volume(md_path, year):
    p = Tables()
    p.feed(md_path.read_text(errors='ignore'))
    out = []
    cl = cr = None                       # carry group state per column across tables
    for table in p.tables:
        if is_abstract(table):
            continue
        widths = [len(expand(r)) for r in table if any(t for t, _ in r)]
        if not widths:
            continue
        width = max(set(widths), key=widths.count)
        left, right = [], []
        for row in table:
            slots = expand(row)
            if width >= 6:                       # two-up: split at midpoint
                mid = width // 2
                lt = triples_from_half(slots[:mid])
                rt = triples_from_half(slots[mid:])
                if lt:
                    left.append(lt)
                if rt:
                    right.append(rt)
            else:                                # single column
                t = triples_from_half(slots)
                if t:
                    left.append(t)
        # NOTE: naive cross-page group carry (passing cl/cr) recovers Tea but
        # regresses Wool etc. (wrong group carries when a new commodity's header
        # isn't ALL-CAPS-detected) → net -1%. Left per-table until a British-
        # Possessions-continuation-specific detector is added.
        parse_column_stream(left, year, out)
        if right:
            parse_column_stream(right, year, out)
    return out


def main():
    allr = []
    for d in sorted(RAW.glob('as_*')):
        m = re.search(r'as_(\d{4})', d.name)
        mds = list(d.glob('*/*.md'))
        if not m or not mds:
            continue
        allr.extend(parse_volume(mds[0], int(m.group(1))))
    out = BASE / 'exports' / 'twoup_country.csv'
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['volume', 'flow', 'duty', 'article_group',
                          'article', 'country_raw', 'unit', 'year', 'quantity', 'value'])
        w.writeheader(); w.writerows(allr)
    imp = [r for r in allr if r['flow'] == 'import']
    print(f'two-up rows: {len(allr):,} ({len(imp):,} import) -> {out}')

    # ---- validate: as_1881 import TOTALs vs gold for missing families
    tot = defaultdict(lambda: [None, None])
    for r in allr:
        if r['year'] == 1881 and r['flow'] == 'import' and \
                r['country_raw'].lower().startswith('total'):
            tot[(r['article_group'], r['article'])] = [r['quantity'], r['value']]
    print('\n=== as_1881 import TOTALs for Wine/Silk/Copper/Dye/Iron/Paper ===')
    for (g, a), (q, v) in sorted(tot.items()):
        if any(k in g for k in ('WINE', 'SILK', 'COPPER', 'DYE', 'IRON', 'PAPER',
                                'SKIN', 'SPIRIT')):
            print(f"  {g[:26]:<26} {a[:22]:<22} q={q} v={v}")


if __name__ == '__main__':
    main()
