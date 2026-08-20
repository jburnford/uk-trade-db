#!/usr/bin/env python3
"""Structural profiler for the Canadian Trade & Navigation volumes (Chandra OCR).

Reads raw_canada/INDEX.tsv, and for every volume present:
  * locates the start of the Trade & Navigation block (its title page),
  * parses the volume's own statement index (statement no. / description / printed page),
  * enumerates every <table> after the T&N start with its title context, header rows,
    row count and column-count histogram, and a coarse family classification.

Outputs
  reports/canada_profile.md     human-readable per-volume summary
  reports/canada_tables.tsv     one row per table (volume, fy, seq, family, title, rows, shape...)

Re-runnable as new volumes land: nothing is hard-coded to a volume list.
"""
import csv, html, json, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'raw_canada'
OUT_MD = ROOT / 'reports' / 'canada_profile.md'
OUT_TSV = ROOT / 'reports' / 'canada_tables.tsv'

TAG_RE = re.compile(r'<[^>]+>')
TABLE_RE = re.compile(r'<table\b.*?</table>', re.S)
ROW_RE = re.compile(r'<tr\b[^>]*>(.*?)</tr>', re.S)
CELL_RE = re.compile(r'<(t[dh])\b([^>]*)>(.*?)</t[dh]>', re.S)
TN_START_RE = re.compile(r'T\s?A\s?B\s?L\s?E\s?S\s+OF\s+THE\s+TRADE\s+AND\s+NAVIGATION\s+OF\s+THE\s+(DOMINION|PROVINCE)', re.I)
TN_START_RE2 = re.compile(r'T\s?A\s?B\s?L\s?E\s?S\s+OF\s+THE\s+TRADE\s+AND\s+NAVIGATION', re.I)


def clean(s):
    s = html.unescape(TAG_RE.sub(' ', s))
    return re.sub(r'\s+', ' ', s).strip()


def parse_table(t):
    """Return (header_rows, body_rows) as lists of cell-text lists; also span info."""
    rows = []
    for r in ROW_RE.findall(t):
        cells = []
        for kind, attrs, body in CELL_RE.findall(r):
            cs = re.search(r'colspan="(\d+)"', attrs)
            cells.append((kind, int(cs.group(1)) if cs else 1, clean(body)))
        rows.append(cells)
    return rows


def family_of(title):
    t = title.lower()
    if not t:
        return 'untitled'
    if 'customs duties' in t and 'revenue' in t or 'statement of customs duties' in t:
        return 'revenue_by_port'
    if 'general statement' in t and 'import' in t:
        return 'imports_general'
    if 'general statement' in t and 'export' in t:
        return 'exports_general'
    if 'summary statement' in t and 'import' in t:
        return 'imports_summary'
    if 'summary statement' in t and 'export' in t:
        return 'exports_summary'
    if 'comparative statement' in t and 'import' in t and 'export' in t:
        return 'comparative_ie'
    if 'comparative statement' in t and 'import' in t:
        return 'imports_comparative'
    if 'comparative statement' in t and 'export' in t:
        return 'exports_comparative'
    if 'abstract' in t and 'import' in t:
        return 'imports_abstract'
    if 'abstract' in t and 'export' in t:
        return 'exports_abstract'
    if 'warehouse' in t:
        return 'warehouse'
    if 'west indies' in t:
        return 'west_indies'
    if 'in bond' in t or 'via the united states' in t or 'through the united states' in t:
        return 'transit'
    if 'st. lawrence' in t:
        return 'st_lawrence'
    if 'vessels' in t or 'shipping' in t or 'navigation' in t or 'tonnage' in t or 'coasting' in t:
        return 'shipping'
    if 'free goods' in t or 'free.' in t:
        return 'imports_free'
    if 'dutiable' in t:
        return 'imports_dutiable'
    if 'import' in t:
        return 'imports_other'
    if 'export' in t:
        return 'exports_other'
    return 'other'


def title_context(intertext):
    """The title of a table is the last meaningful text before it.  Strip markdown furniture."""
    s = intertext
    s = re.sub(r'!\[[^\]]*\]\([^)]*\)', ' ', s)          # images
    s = re.sub(r'^\s*-{3,}\s*$', ' ', s, flags=re.M)        # hr lines
    s = s.replace('---', ' ')
    s = clean(s)
    return s


def parse_statement_index(tables_after_start):
    """Find the table whose header mentions NUMBER OF STATEMENT and return rows."""
    for seq, (rows, _title) in enumerate(tables_after_start):
        if not rows:
            continue
        head = ' '.join(c[2] for c in rows[0]).upper()
        if 'STATEMENT' in head and ('NUMBER' in head or 'NO.' in head) and 'PAGE' in head:
            out = []
            for r in rows[1:]:
                cells = [c[2] for c in r]
                if len(cells) >= 2:
                    out.append(cells)
            return seq, out
    return None, []


def profile_volume(tag, fy, md_path):
    text = md_path.read_text(errors='replace')
    m = TN_START_RE.search(text) or TN_START_RE2.search(text)
    start = m.start() if m else 0
    # there may be several matches (index entries); take the first that is followed soon by a table title page
    # heuristic: choose the match after which 'COMPILED FROM OFFICIAL RETURNS' appears within 1500 chars
    for mm in TN_START_RE2.finditer(text):
        win = text[mm.start(): mm.start() + 1500]
        if re.search(r'COMPILED\s+FROM\s+OFFICIAL\s+RETURNS', win, re.I):
            start = mm.start(); break
    tn = text[start:]
    tables = []
    pos = 0
    for tm in TABLE_RE.finditer(tn):
        inter = tn[pos:tm.start()]
        pos = tm.end()
        rows = parse_table(tm.group(0))
        tables.append((rows, title_context(inter), len(inter), tm.start() + start))
    idx_seq, idx_rows = parse_statement_index([(r, t) for r, t, _, _ in tables])
    recs = []
    for seq, (rows, ctx, interlen, off) in enumerate(tables):
        ths = [r for r in rows if r and all(k == 'th' for k, _, _ in r)]
        body = [r for r in rows if r and not all(k == 'th' for k, _, _ in r)]
        shape = Counter(sum(cs for _, cs, _ in r) for r in body)
        ncells = Counter(len(r) for r in body)
        title = ctx[-400:]
        # a "continued" title is the last sentence-ish chunk
        short = re.split(r'(?<=[.])\s+(?=[A-Z(])', title)[-1] if title else ''
        # prefer the chunk that contains the statement phrasing
        for chunk in reversed(re.split(r'(?<=[.])\s+(?=[A-Z(])', title)):
            if re.search(r'statement|abstract|table|no\. ?\d+|continued|recapitulation', chunk, re.I):
                short = chunk; break
        header_txt = ' || '.join(' | '.join(c for _, _, c in r) for r in ths)[:300]
        first = ' | '.join(c for _, _, c in body[0])[:200] if body else ''
        fam = family_of(short)
        inherited = False
        if recs and (fam in ('other', 'untitled') or re.search(r'continued', short, re.I)) and not re.search(r'no\. ?\d+\.?—|recapitulation', short, re.I):
            # continuation of the previous statement unless the title names a new statement
            if fam in ('other', 'untitled') or re.search(r'continued', short, re.I):
                fam = recs[-1]['family']; inherited = True
        recs.append(dict(volume=tag, fiscal_year=fy, seq=seq, offset=off, family=fam, inherited=int(inherited),
                         title=short[:300], intertext_len=interlen, n_header_rows=len(ths), n_body_rows=len(body),
                         cells_hist=json.dumps(sorted(ncells.items())), span_hist=json.dumps(sorted(shape.items())),
                         header=header_txt, first_row=first))
    return dict(tag=tag, fy=fy, size=len(text), tn_start=start, tn_found=bool(m),
                n_tables=len(recs), idx_seq=idx_seq, idx_rows=idx_rows, recs=recs)


def main():
    index = list(csv.DictReader(open(RAW / 'INDEX.tsv'), delimiter='\t'))
    vols = []
    for row in index:
        tag = row['volume_tag']; fy = row['fiscal_year']
        md = RAW / tag / f'{tag}.md'
        if not md.exists():
            print(f'missing {md}', file=sys.stderr); continue
        v = profile_volume(tag, fy, md)
        vols.append(v)
        print(f"{fy:8} {tag:24} size={v['size']/1e6:5.1f}MB tn_start={v['tn_start']:>8} tables={v['n_tables']:4} idx={'y' if v['idx_rows'] else 'n'}", file=sys.stderr)
    # TSV
    fields = list(vols[0]['recs'][0].keys())
    with open(OUT_TSV, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter='\t')
        w.writeheader()
        for v in vols:
            for r in v['recs']:
                w.writerow(r)
    # MD
    L = ['# Canadian Trade & Navigation volumes — structural profile', '',
         f'Generated by `scripts/ca_profile.py` from `raw_canada/INDEX.tsv` ({len(vols)} volumes present).', '']
    L += ['| FY | volume | MB | T&N start (char) | tables after start | statement index |', '|---|---|---|---|---|---|']
    for v in vols:
        L.append(f"| {v['fy']} | {v['tag']} | {v['size']/1e6:.1f} | {v['tn_start']} | {v['n_tables']} | {len(v['idx_rows'])} rows |")
    L.append('')
    for v in vols:
        L += [f"## FY {v['fy']} — {v['tag']}", '']
        fam = Counter(r['family'] for r in v['recs'])
        L.append('Families: ' + ', '.join(f'{k} {n}' for k, n in fam.most_common()))
        L.append('')
        if v['idx_rows']:
            L += ['Statement index (as printed):', '', '| No. | Description | Page |', '|---|---|---|']
            for r in v['idx_rows']:
                cells = [c.replace('|', '/') for c in r]
                while len(cells) < 3: cells.append('')
                L.append(f'| {cells[0]} | {cells[1][:140]} | {cells[-1]} |')
            L.append('')
        L += ['First table of each family (seq, body rows, cell-count histogram, title):', '']
        seen = set()
        for r in v['recs']:
            if r['family'] in seen: continue
            seen.add(r['family'])
            L.append(f"- **{r['family']}** seq {r['seq']}, {r['n_body_rows']} rows, cells {r['cells_hist']} — {r['title'][:160]}")
        L.append('')
    OUT_MD.write_text('\n'.join(L))
    print(f'wrote {OUT_MD} and {OUT_TSV}', file=sys.stderr)


if __name__ == '__main__':
    main()
