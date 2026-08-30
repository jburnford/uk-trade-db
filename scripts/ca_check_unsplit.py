#!/usr/bin/env python3
"""Verify the FY1891-1897 unsplit rows against the arithmetic the printer left in the table.

`ca_parse_unsplit.py` marks its rows `align_status='whole'`, which says only that no join
could have gone wrong. It says nothing about the digits. This supplies that check.

Each article is printed **twice over**, which is what makes the check possible:

    Ale, beer and porter, in bottles  > Great Britain     122,775
                                     > France                   7
                                     > Germany               1,312   } by COUNTRY
                                     > Norway                    9
                                     > United States        30,087
    Total                            > Ontario              15,218
                                     > Quebec               40,143   } the same money,
                                     > ...                            broken by PROVINCE
    Total                                                  154,190   } printed grand total

So three independent numbers must agree per article: the country rows sum to the province
rows sum to the printed total. Two OCR errors would have to coincide exactly to pass, and a
column misread cannot pass at all -- which is the property the closure check on the split
years turned out to lack (there, the duty triple satisfied the same identity as the value
triple, so a one-column shift went undetected).

Checked on value imported, value entered for consumption, and duty.

Usage:
    python3 scripts/ca_check_unsplit.py                 # every unsplit_rows_*.csv
    python3 scripts/ca_check_unsplit.py --tag cdn_27_5_1893
"""
from __future__ import annotations

import argparse
import csv
import glob
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_DIR = ROOT / 'db' / 'canada'
OUT_MD = ROOT / 'reports' / 'canada_unsplit_check.md'

TOTAL_RE = re.compile(r'^\s*total\b', re.I)
CHECKS = [('tot_imp_value', 'value imported', 0.5),
          ('efc_value', 'value entered for consumption', 0.5),
          ('efc_duty', 'duty', 0.02)]


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def split_labels(s):
    parts = [p.strip() for p in (s or '').split(' > ')]
    return (parts + ['', ''])[:2]


def norm_article(s):
    return re.sub(r'[^a-z0-9]', '', re.sub(r'^\s*\d+\s+', '', (s or '').lower()))


def blocks(rows):
    """Yield (country_rows, province_rows, grand_total_row) per article.

    A block must be closed when the ARTICLE NAME changes, not only when a total is printed.
    Most articles get neither a province breakdown nor a grand total -- the printer gave those
    to the larger ones only -- so splitting on totals alone silently lumps dozens of
    consecutive articles into one block and compares their combined sum against a single
    article's total.
    """
    cty, prov, tot, art = [], [], None, None

    def flush():
        if cty or prov or tot is not None:
            return [(cty, prov, tot)]
        return []

    for r in rows:
        a, b = split_labels(r['labels'])
        if TOTAL_RE.match(a):
            if b:
                prov.append(r)                  # 'Total > Ontario' : the province breakdown
            else:
                tot = r                         # 'Total' alone : the printed grand total
                yield cty, prov, tot
                cty, prov, tot, art = [], [], None, None
            continue
        key = norm_article(a)
        if key and art is not None and key != art:
            yield cty, prov, tot                # previous article ended without a total
            cty, prov, tot = [], [], None
        if key:
            art = key
        cty.append(r)
    if cty or prov or tot is not None:
        yield cty, prov, tot


def check_volume(path):
    rows = list(csv.DictReader(Path(path).open()))
    tag = Path(path).stem.replace('unsplit_rows_', '')
    fy = rows[0]['fiscal_year'] if rows else '?'
    c = Counter()
    checkable_rows = 0
    for cty, prov, tot in blocks(rows):
        # Not every article gets both breakdowns. The printer gave the province split only to
        # the larger articles, and a printed grand total to fewer still (72 of 835 blocks in
        # FY1893). So a block is checked on whatever comparisons it actually offers, and the
        # coverage is reported rather than the unusable blocks being silently dropped.
        has_pair = bool(cty and prov)
        has_tot = tot is not None and bool(cty or prov)
        if not (has_pair or has_tot):
            c['block_unverifiable'] += 1
            continue
        c['block_checked'] += 1
        checkable_rows += len(cty) + len(prov)
        verdicts = []
        for field, _label, eps in CHECKS:
            sc = sum(fnum(r[field]) or 0 for r in cty) if cty else None
            sp = sum(fnum(r[field]) or 0 for r in prov) if prov else None
            tv = fnum(tot[field]) if tot is not None else None
            if sc is None and sp is None:
                continue
            if has_pair and sc is not None and sp is not None:
                agree = abs(sc - sp) < eps
                c[f'{field}:breakdowns_' + ('agree' if agree else 'differ')] += 1
                verdicts.append(agree)
            if tv is not None:
                hit = any(s is not None and abs(s - tv) < eps for s in (sc, sp))
                c[f'{field}:total_' + ('matched' if hit else 'missed')] += 1
                verdicts.append(hit)
        if verdicts and all(verdicts):
            c['block_pass'] += 1
        elif any(verdicts):
            c['block_partial'] += 1
        else:
            c['block_fail'] += 1
    return tag, fy, len(rows), checkable_rows, c


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tag')
    a = ap.parse_args()
    paths = ([DB_DIR / f'unsplit_rows_{a.tag}.csv'] if a.tag
             else sorted(glob.glob(str(DB_DIR / 'unsplit_rows_*.csv'))))

    lines = ['# FY1891-1897 unsplit rows: printed-arithmetic check\n',
             'Larger articles are printed twice -- once broken by country, once by province --',
             'and some carry a printed grand total. Where two of those exist they must agree.',
             'Articles with only one breakdown and no total cannot be checked this way.\n',
             '| volume | FY | rows | rows in a checkable block | blocks checked | pass | partial | fail |',
             '|---|---|---:|---:|---:|---:|---:|---:|']
    tot_ck = tot_pass = tot_rows = tot_ckrows = 0
    detail = []
    for p in paths:
        tag, fy, nrows, ckrows, c = check_volume(p)
        n, ok = c['block_checked'], c['block_pass']
        tot_ck += n; tot_pass += ok; tot_rows += nrows; tot_ckrows += ckrows
        lines.append(f"| {tag} | {fy} | {nrows:,} | {ckrows:,} ({ckrows / max(nrows,1) * 100:.0f}%) "
                     f"| {n:,} | {ok:,} ({ok / max(n,1) * 100:.0f}%) | {c['block_partial']:,} | {c['block_fail']:,} |")
        detail.append((tag, c))
    lines.append(f'\n**{tot_pass:,} of {tot_ck:,} checkable article blocks ({tot_pass / max(tot_ck,1) * 100:.1f}%) '
                 f'pass every comparison available to them.** Those blocks cover {tot_ckrows:,} of '
                 f'{tot_rows:,} rows ({tot_ckrows / max(tot_rows,1) * 100:.0f}%); the rest are articles '
                 f'the printer gave only one breakdown and no total, which this check cannot reach.\n')
    lines.append('## Per-measure detail\n')
    lines.append('| volume | measure | breakdowns agree | breakdowns differ | total matched | total missed |')
    lines.append('|---|---|---:|---:|---:|---:|')
    for tag, c in detail:
        for field, label, _eps in CHECKS:
            lines.append(f"| {tag} | {label} | {c[f'{field}:breakdowns_agree']:,} "
                         f"| {c[f'{field}:breakdowns_differ']:,} | {c[f'{field}:total_matched']:,} "
                         f"| {c[f'{field}:total_missed']:,} |")
    text = '\n'.join(lines)
    OUT_MD.write_text(text + '\n')
    print(text)
    print(f'\n-> {OUT_MD.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
