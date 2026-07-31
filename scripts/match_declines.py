#!/usr/bin/env python3
"""Adjudicated declines, shared by the arithmetic matchers.

A match that has been looked at and rejected must stay rejected. Before this
existed the decline lived only in a findings report, so every re-run of
`match_orphan_countries` re-proposed `Gum — Unenumerated -> Of Other Sorts`,
which iteration 23 had already declined for a stated reason. That is not just
noise: a declined candidate still occupies a slot in the "exactly one
candidate clears the bar" uniqueness test, so **leaving it in can make an
otherwise-resolvable pair read `ambiguous`**. Filter declines out BEFORE
scoring, not after.

reference/match_declines.csv columns: source, host, reason, declined_on.
A blank `host` declines the source against EVERY host — use it for a source
that should never be folded anywhere (a generic de-headed label).

This file records judgements, never data. Deleting a row re-opens the match.
"""
import csv
from pathlib import Path

BASE = Path('/home/jic823/uk_trade_db')
PATH = BASE / 'reference' / 'match_declines.csv'


def load_declines(path=PATH):
    """-> (set of (source, host) pairs, set of blanket-declined sources)."""
    pairs, blanket = set(), set()
    if not Path(path).exists():
        return pairs, blanket
    for r in csv.DictReader(open(path)):
        src = (r.get('source') or '').strip()
        host = (r.get('host') or '').strip()
        if not src:
            continue
        if host:
            pairs.add((src, host))
        else:
            blanket.add(src)
    return pairs, blanket


def declined(src, host, pairs, blanket):
    return src in blanket or (src, host) in pairs
