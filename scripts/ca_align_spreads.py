#!/usr/bin/env python3
"""Rejoin the two halves of a split spread into whole rows, and grade the join.

Reads reports/spread_pairs_<tag>.tsv (from ca_pair_spreads.py) and the volume markdown.

COLUMN MAP (No. 37 General Statement of Imports, FY1898-1908).  The page break runs
*through the middle of a column group*: the General Tariff group's Quantity is the last
column of the left page while its Value and Duty are the first columns of the right page.

  LEFT   article | country/province | TOTAL IMPORTS qty | TOTAL IMPORTS value | GT qty
  RIGHT  GT value | GT duty | PT qty | PT value | PT duty | TOTAL qty | TOTAL value | TOTAL duty

'TOTAL IMPORTS' (left) and 'Total' (right) are different measures -- goods imported vs goods
entered for home consumption -- so they coincide only when nothing was warehoused.  That is
why left-value == right-total-value is a useful but imperfect key.

KEYS used to score a candidate row match:
  K1 cross-page quantity   left.gt_qty + right.pt_qty == right.tot_qty     (strongest: spans the break)
  K2 value coincidence     left.tot_value == right.tot_value              (holds when nothing warehoused)
  K3 quantity coincidence  left.tot_qty  == right.tot_qty
A right row that fails its own closure (GT+PT == Total) is damaged and is penalised so it
cannot win a match on a corrupt number.

Usage:
    python3 scripts/ca_align_spreads.py --tag statcan_nibi_w2_1900 --fy 1900
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ca_profile as P
import ca_pair_spreads as PS

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / 'reports'
DB_DIR = ROOT / 'db' / 'canada'

TABLE_RE = re.compile(r'<table\b.*?</table>', re.S)
HAS_DIGIT = re.compile(r'\d')
INT_RE = re.compile(r'^\d{1,3}(?:,\d{3})*$|^\d+$')
CENTS_RE = re.compile(r'^(\d{1,3}(?:,\d{3})*|\d+)\s+(\d\d)$')
EPS_V, EPS_D = 0.5, 0.02


def num(cell):
    c = cell.replace('$', '').replace('£', '').strip()
    if not c or re.fullmatch(r'[.\s·…\-—–]*', c):
        return None
    if INT_RE.match(c):
        return int(c.replace(',', ''))
    m = CENTS_RE.match(c)
    if m:
        return int(m.group(1).replace(',', '')) + int(m.group(2)) / 100
    return None


def expand_rowspans(table_html, width=None):
    """Return body rows as full-width cell lists, carrying rowspan cells down.

    ca_profile.parse_table drops rowspan, so an article printed once over six rows leaves the
    next five rows a cell short and every column position shifts. This puts them back.

    `width` guards against the OCR's own rowspan errors. Chandra infers rowspans from the
    image and sometimes makes one too long; the stale carry then occupies column 0 while the
    row's real first cell is pushed right, so a 6-column row comes back with 7 or 8 cells and
    an article label sitting in the country slot ('Total > " Sheep > Great Britain'). Strict
    HTML semantics reproduce that faithfully, which is not what is wanted. When a row would
    exceed the printed width, the carried cells are dropped for that row and its explicit
    cells are used as printed.
    """
    rows = []
    pending = {}                                   # col index -> [text, rows_left]
    for tr in re.findall(r'<tr\b.*?</tr>', table_html, re.S):
        cells = re.findall(r'<(t[dh])\b([^>]*)>(.*?)</t[dh]>', tr, re.S)
        if not cells:
            continue
        if all(k == 'th' for k, _, _ in cells):
            continue
        out, ci, src = [], 0, iter(cells)
        while True:
            if ci in pending:
                text, left = pending[ci]
                out.append(text)
                pending[ci] = [text, left - 1]
                if pending[ci][1] <= 0:
                    del pending[ci]
                ci += 1
                continue
            try:
                _kind, attrs, bodytxt = next(src)
            except StopIteration:
                break
            text = P.clean(bodytxt)
            rs = re.search(r'rowspan="(\d+)"', attrs)
            out.append(text)
            if rs and int(rs.group(1)) > 1:
                pending[ci] = [text, int(rs.group(1)) - 1]
            ci += 1
        if width and len(out) > width:
            explicit = [P.clean(b) for _k, _a, b in cells]
            if len(explicit) <= width:
                out = explicit                  # stale carry: trust the row as printed
        rows.append(out)
    return rows


SURTAX_RE = re.compile(r'SURTAX', re.I)

# Where the printer put the break, by era. The tariff law moved it once.
#
#  'GP'  FY1898-1903  General + Preferential (or Reciprocal) tariff.
#        The break falls THROUGH the General Tariff group: its Quantity ends the left page,
#        its Value and Duty begin the right one.
#          LEFT  5 : article | country/province | TOT imports qty | TOT imports value | GT qty
#          RIGHT 8 : GT value | GT duty | PT qty | PT value | PT duty | TOT qty | TOT value | TOT duty
#
#  'SX'  FY1904-1908  Preferential + Surtax tariff, General moved to the left page.
#        The break falls cleanly BETWEEN groups, which is better: it leaves three independent
#        cross-page identities instead of one.
#          LEFT  7 : article | country | TOT qty | TOT value | GT qty | GT value | GT duty
#          RIGHT 9 : PT qty | PT value | PT duty | SX qty | SX value | SX duty | TOT qty | TOT value | TOT duty
ERA = {'GP': dict(left_vals=3, right_width=8,
                  right_fields=['gt_value', 'gt_duty', 'pt_qty', 'pt_value', 'pt_duty',
                                'tot_qty', 'tot_value', 'tot_duty'],
                  left_fields=['tot_qty', 'tot_value', 'gt_qty']),
       'SX': dict(left_vals=5, right_width=9,
                  right_fields=['pt_qty', 'pt_value', 'pt_duty', 'sx_qty', 'sx_value', 'sx_duty',
                                'tot_qty', 'tot_value', 'tot_duty'],
                  left_fields=['tot_qty', 'tot_value', 'gt_qty', 'gt_value', 'gt_duty'])}


def detect_era(right_html):
    flat, _has, _n = PS.header_signature(right_html)
    return 'SX' if SURTAX_RE.search(flat) else 'GP'


def left_rows(table_html, era='GP'):
    """Label cells plus the era's left-page value columns, for rows carrying a number."""
    spec = ERA[era]
    nv, fields = spec['left_vals'], spec['left_fields']
    out = []
    pending = []        # label-only rows (article heading, a dash-country opening a province run)
    for cells in expand_rowspans(table_html, 2 + nv):
        if not any(HAS_DIGIT.search(c) for c in cells[2:]):
            # an article heading / section banner / 'United States--' with no numbers: it is
            # not a row to align, but its label belongs to the NEXT value row (2026-09-01:
            # without this, FY1900 province runs under a dash-country had no article and no
            # country at all in the joined rows)
            pending.extend(c for c in cells if re.search(r'[A-Za-z]', c))    # '2 " Yeast cakes' keeps its item number
            continue
        cells = fold_cents(cells, 2 + nv)
        vals = cells[-nv:] if len(cells) >= nv else [''] * (nv - len(cells)) + cells
        labels = cells[:-nv] if len(cells) > nv else []
        if pending:
            labels = pending + [l for l in labels if l not in pending]
            pending = []
        rec = dict(labels=labels, raw=cells, era=era)
        for f, v in zip(fields, vals):
            rec[f] = num(v)
        for f in ('tot_qty', 'tot_value', 'gt_qty', 'gt_value', 'gt_duty'):
            rec.setdefault(f, None)
        out.append(rec)
    return out


BARE_CENTS = re.compile(r'^\d\d$')
DOLLARS = re.compile(r'^\d{1,3}(?:,\d{3})*$|^\d+$')


def fold_cents(cells, target):
    """Merge a cents cell back onto its dollars cell: ['26,857', '14'] -> ['26,857 14'].

    The two witnesses disagree about this. The StatCan scan puts a duty in one cell
    ('26,857 14'); the Canadiana scan usually splits it in two. Both do it inconsistently
    (853 of 1,531 sampled StatCan right rows are split too), so the row has to be folded
    back to its printed width before columns can be anchored from the right -- otherwise
    every column shifts and the row silently reads as a different set of measures.

    Only ever folds a bare two-digit cell onto a preceding plain integer, rightmost first,
    and only while the row is wider than the printed table. A wrong fold cannot hide: the
    row then fails its own GT + PT == Total closure.
    """
    if len(cells) <= target:
        return cells
    out = list(cells)
    i = len(out) - 1
    while len(out) > target and i > 0:
        if BARE_CENTS.match(out[i].strip()) and DOLLARS.match(out[i - 1].strip()):
            out[i - 1] = out[i - 1].strip() + ' ' + out[i].strip()
            del out[i]
            i -= 1
        i -= 1
    return out


def header_width(table_html):
    """Leaf column count, from the LAST header row.

    Not the first: the StatCan tables carry a spurious trailing <th></th> on the top header
    row (and a junk cell at the end of every body row to match), so the top row implies nine
    columns where the table prints eight. The bottom header row names the actual leaf columns
    ('Value | Duty | Quantity | Value | Duty | Quantity | Value | Duty Collected').
    """
    rows = P.parse_table(table_html)
    ths = [r for r in rows if r and all(k == 'th' for k, _, _ in r)]
    # Count NAMED leaf headers, not colspan units. Two artefacts inflate the colspan sum to 9
    # on a table that prints 8 columns, and both must be ignored: 'Duty Collected' carries
    # colspan="2" where the OCR split the duty's dollars and cents into separate cells, and a
    # trailing empty <th> pads the StatCan tables.
    #
    # Take the MAXIMUM across header rows, not the last one: the bottom row is often the units
    # row ('$ | $ cts. | | $ | $ cts. | | $ | $ cts.'), whose quantity columns are blank, so it
    # names only six of the eight columns and would understate the width.
    best = 0
    for r in ths:
        named = [c for _k, _cs, c in r if c.strip()]
        if 4 <= len(named) <= 12:
            best = max(best, len(named))
    return best or 8


def right_rows(table_html, era='GP', width=None):
    """Right-page rows, anchored from the LEFT.

    The right page has no label column, so its first cell is the first value column. The
    junk, where there is any, is at the END of the row (the spurious StatCan column). Taking
    the first `width` cells is therefore correct for both witnesses; taking the last `width`
    silently drops the leading General-Tariff Value and shifts every measure one place --
    and that shift is invisible to the closure check, because the duty triple satisfies
    GT + PT == Total exactly as the value triple does.
    """
    spec = ERA[era]
    nf = len(spec['right_fields'])
    width = width or header_width(table_html)
    if not 6 <= width <= 11:
        width = spec['right_width']
    out = []
    for cells in expand_rowspans(table_html, max(width, nf)):
        if not any(HAS_DIGIT.search(c) for c in cells):
            continue
        cells = fold_cents(cells, width)
        v = cells[:nf] if len(cells) >= nf else cells + [''] * (nf - len(cells))
        r = dict(raw=cells, width=width, ncells=len(cells), era=era)
        for f, x in zip(spec['right_fields'], v):
            r[f] = num(x)
        for f in ('gt_value', 'gt_duty', 'pt_qty', 'pt_value', 'pt_duty',
                  'sx_qty', 'sx_value', 'sx_duty', 'tot_qty', 'tot_value', 'tot_duty'):
            r.setdefault(f, None)
        r['closes'] = closure(r, era)
        out.append(r)
    return out


def closure(r, era='GP'):
    """Can the right row be judged sound on its own?

    Era GP: yes -- GT + PT == Total sits entirely on the right page, on value and on duty.
    Era SX: no -- the General Tariff moved to the left page, so the identity spans the break
    and cannot pre-screen a right row. All that is testable alone is that the Total is not
    smaller than the parts printed beside it.
    """
    ok = 0
    if era == 'GP':
        if r['tot_value'] is not None:
            ok += 1 if abs((r['gt_value'] or 0) + (r['pt_value'] or 0) - r['tot_value']) < EPS_V else -1
        if r['tot_duty'] is not None:
            ok += 1 if abs((r['gt_duty'] or 0) + (r['pt_duty'] or 0) - r['tot_duty']) < EPS_D else -1
        return ok
    for parts, tot, eps in ((('pt_value', 'sx_value'), 'tot_value', EPS_V),
                            (('pt_duty', 'sx_duty'), 'tot_duty', EPS_D)):
        if r[tot] is not None:
            s = sum(r[k] or 0 for k in parts)
            ok += 0 if s <= r[tot] + eps else -1        # parts exceeding the total = damaged
    return ok


def score(l, r):
    """Match score and the key that carried it."""
    s, key = 0, ''
    era = r.get('era', 'GP')
    if era == 'SX':
        # Three independent identities span the break: GT (left) + PT + SX (right) == Total
        # (right), separately on quantity, value and duty. Each is worth a key on its own.
        for lf, pf, xf, tf, eps, name in (
                ('gt_qty', 'pt_qty', 'sx_qty', 'tot_qty', EPS_V, 'xpage_qty'),
                ('gt_value', 'pt_value', 'sx_value', 'tot_value', EPS_V, 'xpage_value'),
                ('gt_duty', 'pt_duty', 'sx_duty', 'tot_duty', EPS_D, 'xpage_duty')):
            if r[tf] is None:
                continue
            got = (l[lf] or 0) + (r[pf] or 0) + (r[xf] or 0)
            if abs(got - r[tf]) < eps and (l[lf] is not None or r[pf] is not None or r[xf] is not None):
                s += 5; key = key or name
        if s == 0 and l['tot_qty'] is None and r['tot_qty'] is None:
            s, key = 1, 'shape'
        s += r['closes']
        return s, key
    if l['gt_qty'] is not None and r['tot_qty'] is not None:            # K1 spans the page break
        if abs(l['gt_qty'] + (r['pt_qty'] or 0) - r['tot_qty']) < EPS_V:
            s += 6; key = 'xpage_qty'
    if l['tot_value'] is not None and r['tot_value'] is not None:        # K2
        if abs(l['tot_value'] - r['tot_value']) < EPS_V:
            s += 4; key = key or 'value'
    if l['tot_qty'] is not None and r['tot_qty'] is not None:            # K3
        if abs(l['tot_qty'] - r['tot_qty']) < EPS_V:
            s += 3; key = key or 'qty'
    if s == 0:
        # both sides ad-valorem (no quantities at all): weak positional compatibility only
        if l['tot_qty'] is None and r['tot_qty'] is None:
            s, key = 1, 'shape'
    s += r['closes']                                # a self-inconsistent right row cannot win
    return s, key


def align(L, R, gap=-1):
    """Monotone Needleman-Wunsch. Returns list of (li|None, ri|None, key)."""
    n, m = len(L), len(R)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    bt = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] + gap; bt[i][0] = 1
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] + gap; bt[0][j] = 2
    sc = [[score(L[i], R[j])[0] for j in range(m)] for i in range(n)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            diag = dp[i - 1][j - 1] + sc[i - 1][j - 1]
            up, lf = dp[i - 1][j] + gap, dp[i][j - 1] + gap
            best = max(diag, up, lf)
            dp[i][j] = best
            bt[i][j] = 0 if best == diag else (1 if best == up else 2)
    out, i, j = [], n, m
    while i > 0 or j > 0:
        b = bt[i][j]
        if i > 0 and j > 0 and b == 0:
            out.append((i - 1, j - 1, score(L[i - 1], R[j - 1])[1])); i -= 1; j -= 1
        elif i > 0 and (b == 1 or j == 0):
            out.append((i - 1, None, '')); i -= 1
        else:
            out.append((None, j - 1, '')); j -= 1
    return out[::-1]


def run(tag, fy, md_path=None):
    pairs_path = OUT_DIR / f'spread_pairs_{tag}.tsv'
    all_pairs = list(csv.DictReader(pairs_path.open(), delimiter='\t'))
    pairs = [r for r in all_pairs if r['family'] == 'imports_37']

    # The document must be the one the offsets were measured against. ca_pair_spreads records
    # it in the TSV for exactly this reason; an explicit md_path may only confirm it.
    recorded = {r.get('md_path') for r in all_pairs if r.get('md_path')}
    if recorded:
        if len(recorded) > 1:
            raise SystemExit(f'{pairs_path} names multiple source documents: {sorted(recorded)}')
        rec = Path(recorded.pop())
        if md_path and Path(md_path).resolve() != rec.resolve():
            raise SystemExit(f'--md {md_path} does not match the document these offsets were '
                             f'measured against ({rec}); refusing to index one book into another')
        md_path = rec
    elif md_path is None:
        raise SystemExit(f'{pairs_path} predates md_path recording; re-run ca_pair_spreads.py, '
                         f'or pass --md explicitly')
    text = Path(md_path).read_text(errors='ignore')
    diag, grades = Counter(), Counter()
    DB_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = DB_DIR / f'spread_rows_{tag}.csv'
    resid = OUT_DIR / f'spread_residue_{tag}.csv'
    fields = ['fiscal_year', 'volume', 'pair_id', 'row_seq', 'era', 'labels', 'align_status', 'key',
              'tot_imp_qty', 'tot_imp_value', 'gt_qty', 'gt_value', 'gt_duty',
              'pt_qty', 'pt_value', 'pt_duty', 'sx_qty', 'sx_value', 'sx_duty',
              'efc_qty', 'efc_value', 'efc_duty', 'closes']
    fh, rh = out_csv.open('w', newline=''), resid.open('w', newline='')
    w, wr = csv.DictWriter(fh, fields), csv.DictWriter(rh, fields)
    w.writeheader(); wr.writeheader()

    for p in pairs:
        def tbl(off):
            return TABLE_RE.search(text[int(off):]).group(0)
        r_html = tbl(p['r_offset'])
        era = detect_era(r_html)
        L = left_rows(tbl(p['l_offset']), era)
        R = right_rows(r_html, era)
        diag[f'era_{era}'] += 1
        if not L or not R:
            grades['FAIL_empty'] += 1
            continue
        al = align(L, R)
        matched = sum(1 for li, ri, _ in al if li is not None and ri is not None)
        frac = matched / max(len(L), 1)
        grade = 'PASS' if frac >= 0.95 else ('PARTIAL' if frac >= 0.7 else 'FAIL')
        grades[grade] += 1
        for k, (li, ri, key) in enumerate(al):
            l = L[li] if li is not None else {}
            r = R[ri] if ri is not None else {}
            status = ('joined' if li is not None and ri is not None
                      else ('left_only' if li is not None else 'right_only'))
            if status == 'joined' and not key:
                status, key = 'joined_weak', 'position'
            diag[status if status != 'joined' else f'joined_{key}'] += 1
            # In era SX the General Tariff columns are printed on the LEFT page, so they come
            # from l; in era GP they are on the right. Take whichever side actually holds them.
            def pick(f):
                v = l.get(f)
                return r.get(f) if v is None else v
            rec = dict(fiscal_year=fy, volume=tag, pair_id=p['pair_id'], row_seq=k, era=era,
                       labels=' > '.join(x for x in l.get('labels', []) if x),
                       align_status=status, key=key,
                       tot_imp_qty=l.get('tot_qty'), tot_imp_value=l.get('tot_value'),
                       gt_qty=pick('gt_qty'), gt_value=pick('gt_value'), gt_duty=pick('gt_duty'),
                       pt_qty=r.get('pt_qty'), pt_value=r.get('pt_value'), pt_duty=r.get('pt_duty'),
                       sx_qty=r.get('sx_qty'), sx_value=r.get('sx_value'), sx_duty=r.get('sx_duty'),
                       efc_qty=r.get('tot_qty'), efc_value=r.get('tot_value'),
                       efc_duty=r.get('tot_duty'), closes=r.get('closes'))
            w.writerow(rec)
            if status != 'joined':
                wr.writerow(rec)
    fh.close(); rh.close()

    joined = sum(v for k, v in diag.items() if k.startswith('joined'))
    total_l = joined + diag['left_only']
    print(f'\n=== {tag}  ({len(pairs)} imports_37 pairs)')
    print(f'  left rows: {total_l};  joined: {joined} ({joined / max(total_l, 1) * 100:.1f}%)')
    for k in sorted(diag):
        print(f'    {k}: {diag[k]}')
    print('  pair grades:', dict(grades))
    print(f'  rows -> {out_csv.relative_to(ROOT)};  residue -> {resid.relative_to(ROOT)}')
    return diag, grades


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tag', required=True)
    ap.add_argument('--fy', required=True)
    ap.add_argument('--md', help='markdown path; REQUIRED for any witness that is not the '
                                 'StatCan preferred source for --fy. Without it the volume is '
                                 'resolved from the StatCan manifest by fiscal year, which for a '
                                 'Canadiana tag silently reads the wrong document while using this '
                                 'tag\'s table offsets.')
    a = ap.parse_args()
    run(a.tag, a.fy, Path(a.md) if a.md else None)


if __name__ == '__main__':
    main()
