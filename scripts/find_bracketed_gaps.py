#!/usr/bin/env python3
"""Bracketed-gap screen: data, then a hole, then data again.

A commodity-year run where the origin/anchor ratio collapses (or the origin
table vanishes) BETWEEN years that close well is a parse defect signature,
not a trade story — trade declines taper, parses fall off cliffs. This is
the pattern behind palm oil 1884/85 (stale FISH head), kernels 1894
(phantom-region articles), coffee's 1890s, flax 1872-74, and gutta percha
1876-80 — every one found by hand. This screen finds them by rule.

For every payload commodity with a Tier-1 series (modal unit), each year is
classed good (|ratio-1| <= 0.10), bad (ratio < 0.5), or hole (T1 year with
no origin sum). Maximal bad/hole runs bracketed by a good year on BOTH
sides are reported, scored by the anchor quantity missing across the run
valued at the commodity's own implied price (v / total anchored qty).

Usage: python3 scripts/find_bracketed_gaps.py exports/viz_payload.json
   ->  reports/bracketed_gaps.csv
"""
import csv
import json
from collections import defaultdict
import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).resolve().parent))
import match_by_name as MB
import sys
from pathlib import Path

BASE = Path('/home/jic823/uk_trade_db')
TK = '§TOTAL'


def _closing_index(p):
    """(year, rounded anchor) -> nodes whose countries close that year.

    A ranked "gap" is often ILLUSORY: the year already closes under a SIBLING
    LABEL carrying the same anchor, because one printed line reached the
    payload as two commodities. Brass, stones and pyrites were three
    consecutive items of exactly that shape, each worth 0 or -1 to the corpus
    count. This screen looks at one node at a time and cannot see it, so the
    check is bolted on here.
    """
    idx = defaultdict(set)
    for name, entry in p.items():
        c = entry.get('c') or {}
        t1 = c.get(TK)
        if not t1:
            continue
        unit = max(t1, key=lambda u: len(t1[u]))
        ty = {r[0]: r[1] for r in t1[unit] if r[1]}
        cs = defaultdict(float)
        for cty, byu in c.items():
            if cty == TK or '(' in cty:
                continue
            for uu, cells in byu.items():
                for r in cells:
                    if r[1]:
                        cs[r[0]] += r[1]
        for y, a in ty.items():
            if cs.get(y) and abs(cs[y] - a) <= 0.05 * a:
                idx[(y, round(a))].add(name)
    return idx


def main(path):
    p = json.load(open(path))
    closing = _closing_index(p)
    anchors = {}
    rows = []
    for name, entry in p.items():
        c = entry.get('c') or {}
        t1 = c.get(TK)
        if not t1:
            continue
        unit = max(t1, key=lambda u: len(t1[u]))
        vals = [r[1] for r in t1[unit] if r[1]]
        if len(vals) < 4:
            continue
        med = sorted(vals)[len(vals) // 2]
        t1y = {r[0]: r[1] for r in t1[unit]
               if r[1] and not (med and r[1] > 30 * med)}
        anchors[name] = t1y
        csum = {}
        for cty, byu in c.items():
            if cty == TK or '(' in cty:
                continue
            for r in byu.get(unit, []):
                if r[1]:
                    csum[r[0]] = csum.get(r[0], 0) + r[1]
        if not csum:
            continue                      # nothing anchored at all: not a gap
        years = sorted(t1y)
        state = {}
        for y in years:
            ratio = csum.get(y, 0) / t1y[y]
            state[y] = ('good' if abs(ratio - 1) <= 0.10 else
                        'bad' if ratio < 0.5 else 'mid')
        # implied price from the anchored years the commodity does close
        good_q = sum(t1y[y] for y in years if state[y] == 'good')
        price = (entry.get('v') or 0) / good_q if good_q else 0
        # maximal runs of bad years bracketed by good on both sides
        i = 0
        while i < len(years):
            if state[years[i]] != 'bad':
                i += 1
                continue
            j = i
            while j + 1 < len(years) and state[years[j + 1]] == 'bad':
                j += 1
            left = years[i - 1] if i > 0 else None
            right = years[j + 1] if j + 1 < len(years) else None
            if (left is not None and state[left] == 'good'
                    and right is not None and state[right] == 'good'):
                run = years[i:j + 1]
                miss_q = sum(t1y[y] - csum.get(y, 0) for y in run)
                rows.append({
                    'commodity': name, 'unit': unit,
                    'gap_start': run[0], 'gap_end': run[-1],
                    'n_years': len(run),
                    'kind': 'hole' if all(csum.get(y, 0) == 0 for y in run)
                            else 'collapse',
                    'ratios': ' '.join(f'{csum.get(y,0)/t1y[y]:.2f}'
                                       for y in run),
                    'missing_qty': round(miss_q),
                    'gbp_at_stake': round(miss_q * price),
                    'commodity_gbp': round(entry.get('v') or 0),
                })
            i = j + 1
    # Flag gap-years already closed by a NAME-RELATED sibling on the same
    # anchor. The name guard is essential: 'Manganese, Ore Of' 1891 and
    # 'Manures - Phosphate Of Lime And Rock' share an anchor value that year
    # and are entirely unrelated commodities, so anchor agreement ALONE is
    # coincidence-grade evidence - the same lesson the single-year matcher
    # taught.
    for r in rows:
        t1y = anchors[r['commodity']]
        dup, by = [], set()
        for y in range(r['gap_start'], r['gap_end'] + 1):
            a = t1y.get(y)
            if not a:
                continue
            for o in closing.get((y, round(a)), ()):
                if o != r['commodity'] and MB.related(o, r['commodity']):
                    dup.append(y)
                    by.add(o)
                    break
        r['dup_years'] = ';'.join(map(str, dup))
        r['dup_by'] = '; '.join(sorted(by))[:120]
        r['all_dup'] = 'YES' if dup and len(dup) == r['n_years'] else ''
    rows.sort(key=lambda r: (r['all_dup'] == 'YES', -r['gbp_at_stake']))
    out = BASE / 'reports' / 'bracketed_gaps.csv'
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    n_dup = sum(1 for r in rows if r['all_dup'] == 'YES')
    print(f'{len(rows)} bracketed gaps in '
          f'{len({r["commodity"] for r in rows})} commodities -> {out}')
    print(f'  of these, {n_dup} are ILLUSORY - every gap-year already closes '
          f'under a name-related sibling on the same anchor (sorted last)')
    for r in [x for x in rows if x['all_dup'] != 'YES'][:25]:
        print(f'  £{r["gbp_at_stake"]:>10,}  {r["commodity"][:44]:44} '
              f'{r["gap_start"]}-{r["gap_end"]} ({r["n_years"]}y {r["kind"]}) '
              f'ratios {r["ratios"][:40]}')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'exports/viz_payload.json')
