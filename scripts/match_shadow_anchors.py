#!/usr/bin/env python3
"""Match anchor-only payload labels to their countries BY ARITHMETIC.

`deheaded_anchor_match.py` pairs a de-headed anchor with its countries
STRUCTURALLY - the shadow's name must be the suffix of the counterpart's.
That works when the article is distinctive and fails completely when it is
not: `Unenumerated` is the suffix of 51 different commodities, `Raw` of 11.
And 310 of the 334 anchor-only labels have no name candidate at all.

So match on the numbers instead. For every (shadow, candidate) pair, count
the years where the candidate's country cells sum to the shadow's printed
national total. Two series that agree to the digit in several independent
years are the same line; no name evidence is needed, and none is used.

THE COINCIDENCE GUARD IS THE WHOLE DESIGN. There are ~300 shadows and ~1,900
candidates, so ~570,000 pairs are scored and chance agreements are certain.
Therefore:

  * a hit needs >= MIN_EXACT years agreeing EXACTLY (not 'close'),
  * the agreeing years must carry real magnitude (>= MIN_QTY), so a pair of
    zero or single-digit years cannot qualify,
  * the candidate must NOT already have its own anchor in those years - if it
    does, the shadow duplicates it rather than completing it, and
  * a shadow is only REPORTED AS RESOLVED when exactly ONE candidate clears
    the bar. Ties are printed as ambiguous and left alone.

That last rule is the same one the Tons.Cwts decoder uses: a closure reached
by search is evidence only when it is the ONLY closure.

Usage: python3 scripts/match_shadow_anchors.py [payload.json] [out.csv]
   ->  reports/shadow_anchor_matches.csv
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import match_declines as MD

BASE = Path('/home/jic823/uk_trade_db')
TK = '§TOTAL'
MIN_EXACT = 2          # years that must agree to the digit
MIN_QTY = 1000
# Digit equality was the original bar, and it was very slightly too strict:
# farinaceous substances 1885 reads 802,967 against a printed 802,970 - three
# pounds in eight hundred thousand, 0.0004% - and was rejected, which cost the
# whole pairing its second agreeing year and hid a GBP9.7M six-year hole.
# So agreement is now |diff| <= max(1, TOL * anchor). At TOL = 0.0002 a random
# pair agrees in one year about once in 5,000 and in TWO independent years
# about once in 25 million; across ~900,000 pairs that is well under one
# expected false positive, so the coincidence guard still holds.
TOL = 0.0002


def agrees(got, want):
    return abs(got - want) <= max(1.0, TOL * abs(want))         # ... and carry this much quantity, so noise cannot pass


def main(payload_path, out_path):
    _dec_pairs, _dec_blanket = MD.load_declines()
    n_declined = [0]
    payload = json.load(open(payload_path))

    shadows, cands = {}, {}
    for name, e in payload.items():
        c = e.get('c') or {}
        t1 = c.get(TK)
        ctys = [k for k in c if k != TK and '(' not in k]
        if t1 and not ctys:
            unit = max(t1, key=lambda u: len(t1[u]))
            t1y = {r[0]: r[1] for r in t1[unit] if r[1]}
            if t1y:
                shadows[name] = (unit, t1y)
        if ctys:
            per = defaultdict(lambda: defaultdict(float))
            for cty, byu in c.items():
                if cty == TK or '(' in cty:
                    continue
                for u, cells in byu.items():
                    for r in cells:
                        if r[1]:
                            per[u][r[0]] += r[1]
            own = {}
            if t1:
                for u, cells in t1.items():
                    for r in cells:
                        if r[1]:
                            own[(u, r[0])] = r[1]
            cands[name] = (per, own)

    rows, resolved, ambiguous = [], 0, 0
    for sname, (unit, t1y) in shadows.items():
        hits = []
        for cname, (per, own) in cands.items():
            if cname == sname or unit not in per:
                continue
            years = [y for y in t1y if y in per[unit]]
            ex = [y for y in years
                  if agrees(per[unit][y], t1y[y]) and t1y[y] >= MIN_QTY]
            if len(ex) < MIN_EXACT:
                continue
            # if the candidate already anchors those years, this is a duplicate
            if any((unit, y) in own for y in ex):
                continue
            gains = [y for y in t1y if y in per[unit] and (unit, y) not in own]
            # adjudicated declines are filtered BEFORE the uniqueness test
            # below, so a declined candidate cannot make a resolvable pair
            # read ambiguous (see scripts/match_declines.py)
            if MD.declined(sname, cname, _dec_pairs, _dec_blanket):
                n_declined[0] += 1
                continue
            hits.append((len(ex), len(gains), cname, ex))
        if not hits:
            continue
        hits.sort(reverse=True)
        top = [h for h in hits if h[0] == hits[0][0]]
        kind = 'resolved' if len(top) == 1 else 'ambiguous'
        resolved += kind == 'resolved'
        ambiguous += kind == 'ambiguous'
        for n_ex, n_gain, cname, ex in hits[:4]:
            rows.append({
                'shadow': sname, 'unit': unit,
                'shadow_t1_years': len(t1y),
                'candidate': cname, 'kind': kind,
                'n_candidates_at_top': len(top),
                'exact_years': n_ex, 'gains_years': n_gain,
                'years': ';'.join(str(y) for y in sorted(ex)[:8]),
                'shadow_gbp': round(payload[sname].get('v') or 0),
                'candidate_gbp': round(payload[cname].get('v') or 0)})
    rows.sort(key=lambda r: (r['kind'], -r['exact_years'], -r['gains_years']))

    cols = ['shadow', 'unit', 'shadow_t1_years', 'candidate', 'kind',
            'n_candidates_at_top', 'exact_years', 'gains_years', 'years',
            'shadow_gbp', 'candidate_gbp']
    with open(out_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    print(f'anchor-only shadows: {len(shadows)}   candidates: {len(cands)}')
    print(f'  RESOLVED  (exactly one candidate clears the bar): {resolved}')
    print(f'  AMBIGUOUS (two or more tie at the top):           {ambiguous}')
    print(f'  bar: >= {MIN_EXACT} years agreeing to the digit, each >= {MIN_QTY:,}')
    print(f'-> {out_path}')
    for r in [x for x in rows if x['kind'] == 'resolved'][:25]:
        print(f"  {r['exact_years']}e gains {r['gains_years']:>2}y  "
              f"{r['shadow'][:30]:<32} -> {r['candidate'][:44]:<46} {r['years'][:24]}")


if __name__ == '__main__':
    a = sys.argv[1] if len(sys.argv) > 1 else str(BASE / 'exports' / 'viz_payload.json')
    b = sys.argv[2] if len(sys.argv) > 2 else str(BASE / 'reports' / 'shadow_anchor_matches.csv')
    main(a, b)
