#!/usr/bin/env python3
"""Compare two witnesses' joined spread rows for the same fiscal year.

The Canadiana sessional-paper scan and the StatCan departmental scan are two independent
imagings of the same printed tables. This asks the question the whole two-witness design
rests on: when a row's arithmetic fails in one witness, does the other one rescue it?

A row "closes" when its own printed columns add up: GT value + PT value == Total value.
That check needs no cross-page assumption and no second witness -- it is the row calling
itself correct or damaged.

Rows are keyed on their normalised label (article > country/province), which both witnesses
print identically; OCR noise in the label is stripped rather than matched fuzzily, and keys
that are ambiguous within a witness are dropped rather than guessed.

Usage:
    python3 scripts/ca_compare_witnesses.py --a <tag> --b <tag> [--out reports/...md]
"""
from __future__ import annotations

import argparse
import csv
import re
import difflib
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_DIR = ROOT / 'db' / 'canada'

VALUE_FIELDS = ['gt_value', 'gt_duty', 'pt_value', 'pt_duty', 'efc_value', 'efc_duty']


def norm_label(s):
    """'1 Ale, beer and porter in bottles > Great Britain.....' -> 'alebeerandporterinbottlesgreatbritain'"""
    s = re.sub(r'^\s*\d+\s+', '', s or '')          # leading tariff item number
    s = re.sub(r'[^A-Za-z]', '', s).lower()
    return s


def load(tag):
    """Joined rows of one witness, in document order."""
    path = DB_DIR / f'spread_rows_{tag}.csv'
    return [r for r in csv.DictReader(path.open()) if r['align_status'].startswith('joined')]


def match(A, B):
    """Pair rows of two witnesses by aligning their label SEQUENCES.

    Keying on (label, occurrence) does not work: the label alone is not unique -- the 1898+
    layout puts countries and provinces in one column, so 'Iron > Ontario' recurs under every
    country that shipped iron -- and one dropped row then shifts every later occurrence of
    that label, mispairing rows wholesale. Mispaired rows look exactly like disagreeing
    scans, which is how a 75%-of-cells-differ figure arises between two scans that in fact
    agree.

    Both witnesses are the same book in the same order, so the honest matching is a sequence
    alignment. difflib finds the maximal runs of identical labels; only rows inside those
    runs are compared, and rows in a replace/insert/delete block are left unmatched rather
    than guessed.
    """
    la = [norm_label(r['labels']) for r in A]
    lb = [norm_label(r['labels']) for r in B]
    sm = difflib.SequenceMatcher(a=la, b=lb, autojunk=False)
    pairs = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal':
            for k in range(i2 - i1):
                if len(la[i1 + k]) >= 4:          # skip empty/stub labels
                    pairs.append((A[i1 + k], B[j1 + k]))
    return pairs


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def closes(r):
    tv, gv, pv = fnum(r['efc_value']), fnum(r['gt_value']), fnum(r['pt_value'])
    if tv is None:
        return None                                  # nothing to check
    return abs((gv or 0) + (pv or 0) - tv) < 0.5


def agree(a, b):
    """Do the two witnesses print the same numbers where both have one?"""
    same = diff = 0
    for f in VALUE_FIELDS:
        x, y = fnum(a[f]), fnum(b[f])
        if x is None or y is None:
            continue
        if abs(x - y) < 0.02:
            same += 1
        else:
            diff += 1
    return same, diff


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--a', required=True, help='witness A tag')
    ap.add_argument('--b', required=True, help='witness B tag')
    ap.add_argument('--out')
    args = ap.parse_args()

    A = load(args.a)
    B = load(args.b)
    matched = match(A, B)
    na, nb = len(A), len(B)

    c = Counter()
    rescued_examples = []
    for a, b in matched:
        k = norm_label(a['labels'])
        ca, cb = closes(a), closes(b)
        same, diff = agree(a, b)
        if diff == 0 and same > 0:
            c['cells_identical'] += 1
        elif same and diff:
            c['cells_partly_differ'] += 1
        elif diff:
            c['cells_differ'] += 1
        else:
            c['no_comparable_cells'] += 1

        if ca is None and cb is None:
            c['neither_checkable'] += 1
        elif ca and cb:
            c['both_close'] += 1
        elif ca and not cb:
            c['A_closes_B_fails'] += 1
            if len(rescued_examples) < 5:
                rescued_examples.append(('A', k, a, b))
        elif cb and not ca:
            c['B_closes_A_fails'] += 1
            if len(rescued_examples) < 5:
                rescued_examples.append(('B', k, a, b))
        elif ca is False and cb is False:
            c['both_fail'] += 1
        else:
            c['one_uncheckable'] += 1

    rescued = c['A_closes_B_fails'] + c['B_closes_A_fails']
    checkable = c['both_close'] + rescued + c['both_fail']

    lines = []
    P = lines.append
    P(f'# Two-witness comparison: {args.a}  vs  {args.b}\n')
    P(f'| | {args.a} | {args.b} |')
    P('|---|---:|---:|')
    P(f'| joined rows | {na:,} | {nb:,} |')
    P(f'\n**Rows matched by label-sequence alignment: {len(matched):,}** '
      f'({len(matched) / max(min(na, nb), 1) * 100:.0f}% of the smaller witness)\n')

    P('## Do the two scans print the same numbers?\n')
    tot = sum(c[k] for k in ('cells_identical', 'cells_partly_differ', 'cells_differ', 'no_comparable_cells'))
    for k, label in [('cells_identical', 'every comparable cell identical'),
                     ('cells_partly_differ', 'some cells agree, some differ'),
                     ('cells_differ', 'all comparable cells differ'),
                     ('no_comparable_cells', 'nothing comparable')]:
        P(f'- {label}: **{c[k]:,}** ({c[k] / max(tot, 1) * 100:.1f}%)')

    P('\n## Does a second witness rescue a damaged row?\n')
    P('A row "closes" when its own printed columns add up (GT + PT == Total).\n')
    P(f'- both witnesses close: **{c["both_close"]:,}**')
    P(f'- only {args.a} closes (B damaged): **{c["A_closes_B_fails"]:,}**')
    P(f'- only {args.b} closes (A damaged): **{c["B_closes_A_fails"]:,}**')
    P(f'- neither closes: **{c["both_fail"]:,}**')
    P(f'- not checkable: {c["neither_checkable"] + c["one_uncheckable"]:,}')
    if checkable:
        P(f'\n**Of {checkable:,} checkable rows, {rescued:,} ({rescued / checkable * 100:.1f}%) '
          f'are damaged in one witness and sound in the other — recoverable only because there '
          f'are two scans.** Single-witness good rate '
          f'{(c["both_close"] + c["A_closes_B_fails"]) / checkable * 100:.1f}% '
          f'-> two-witness {(c["both_close"] + rescued) / checkable * 100:.1f}%.')
    if c['both_fail']:
        P(f'\n{c["both_fail"]:,} rows are damaged in both and need a third source or a human.')

    if rescued_examples:
        P('\n## Sample rescues\n')
        P('| good witness | label | A: GT+PT / Total | B: GT+PT / Total |')
        P('|---|---|---|---|')
        for who, k, a, b in rescued_examples:
            def s(r):
                gv, pv, tv = fnum(r['gt_value']), fnum(r['pt_value']), fnum(r['efc_value'])
                return f'{(gv or 0) + (pv or 0):,.0f} / {tv:,.0f}' if tv is not None else '—'
            P(f'| {who} | {(a["labels"] or "")[:52]} | {s(a)} | {s(b)} |')

    text = '\n'.join(lines)
    print(text)
    if args.out:
        Path(args.out).write_text(text + '\n')
        print(f'\n-> {args.out}')


if __name__ == '__main__':
    main()
