#!/usr/bin/env python3
"""Match ORPHAN COUNTRY TABLES to their anchor by arithmetic.

The mirror of `match_shadow_anchors.py`. That tool scans one direction: a
label holding a national total and NO countries, looking for the commodity
that holds the countries. This one scans the other: a label holding
COUNTRIES AND NO TOTAL, looking for the commodity that holds the total.

Both directions are produced by the same underlying defect - a stale or
misread group heading splits one printed line into two payload commodities -
but which half keeps the anchor depends on where the heading was lost, so a
scanner that only looks one way misses about half the population. This
direction was invisible until a hand repair of silver ore turned up four
years' worth of it in a single commodity (`Silk Manufactures — Silver ONE,
or ONE of which...`, ORE misread as ONE, holding the 1876 and 1879 tables).

Same evidence bar as the forward scan, and for the same reason - 1,194
orphans x 755 hosts is ~900,000 pairs, so chance agreement is certain:

  * >= MIN_EXACT years where the orphan's country cells sum EXACTLY to the
    host's national total,
  * each such year carrying >= MIN_QTY,
  * the host having NO country data of its own in those years, so nothing
    can double-count, and
  * exactly ONE host clearing the bar. Ties are reported and left alone.

A CAUTION LEARNED THE HARD WAY: the arithmetic vouches only for the years it
matched, but `commodity_curation`'s fold brings the WHOLE source unless it is
year-scoped. Folding `Bark — Sumach` into `Sumach` unscoped carried a 1893
cell (12,036) into a target that already held a better 1893 reading (11,515,
closing exactly on its own anchor) and pushed that year off exact01. Scope
the fold to the years the host actually lacks.

Usage: python3 scripts/match_orphan_countries.py [payload.json] [out.csv]
   ->  reports/orphan_country_matches.csv
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
MIN_EXACT = 2
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
    return abs(got - want) <= max(1.0, TOL * abs(want))


def main(payload_path, out_path):
    _dec_pairs, _dec_blanket = MD.load_declines()
    n_declined = [0]
    payload = json.load(open(payload_path))
    orphans, hosts = {}, {}
    for name, e in payload.items():
        c = e.get('c') or {}
        t1 = c.get(TK)
        ctys = [k for k in c if k != TK and '(' not in k]
        per = defaultdict(lambda: defaultdict(float))
        for cty, byu in c.items():
            if cty == TK or '(' in cty:
                continue
            for u, cells in byu.items():
                for r in cells:
                    if r[1]:
                        per[u][r[0]] += r[1]
        # ANY node with countries is a source. Requiring the source to have no
        # anchor AT ALL (the original rule) missed a whole population: a node
        # can hold an anchor for one era and countries for another, with the
        # other era's anchor in a differently-named node. Staves is the proof -
        # `Wood And Timber — Staves` held countries plus Tier-1 for 1890-91
        # while `Staves, Of All Dimensions` held Tier-1 for 1892-94, and the
        # first node's own sums for 1892 and 1893 WERE the second's anchors.
        # The per-year test below (source must not anchor the matched year)
        # is what keeps this safe.
        if ctys:
            own_t1 = {}
            if t1:
                for u, cells in t1.items():
                    for r in cells:
                        if r[1]:
                            own_t1[(u, r[0])] = r[1]
            orphans[name] = (per, own_t1)
        if t1:
            u = max(t1, key=lambda x: len(t1[x]))
            t1y = {r[0]: r[1] for r in t1[u] if r[1]}
            if t1y:
                hosts[name] = (u, t1y, {y for y in per.get(u, {}) if per[u][y]})

    rows, res, amb = [], 0, 0
    for oname, (per, own_t1) in orphans.items():
        hits = []
        for hname, (u, t1y, have) in hosts.items():
            if hname == oname or u not in per:
                continue
            # the source must NOT anchor the matched year itself - otherwise
            # the two nodes disagree about that year rather than completing
            # each other, and folding would be a duplicate merge
            ex = [y for y in t1y if y in per[u] and y not in have
                  and (u, y) not in own_t1
                  and agrees(per[u][y], t1y[y]) and t1y[y] >= MIN_QTY]
            if len(ex) >= MIN_EXACT:
                # an adjudicated decline is filtered HERE, before the
                # uniqueness test below — a declined candidate still occupies
                # a slot in "exactly one candidate clears the bar", so leaving
                # it in can make an otherwise-resolvable pair read ambiguous
                if MD.declined(oname, hname, _dec_pairs, _dec_blanket):
                    n_declined[0] += 1
                    continue
                gains = [y for y in t1y if y in per[u] and y not in have
                         and (u, y) not in own_t1]
                hits.append((len(ex), len(gains), hname, ex, sorted(gains)))
        if not hits:
            continue
        hits.sort(reverse=True)
        top = [h for h in hits if h[0] == hits[0][0]]
        kind = 'resolved' if len(top) == 1 else 'ambiguous'
        res += kind == 'resolved'
        amb += kind == 'ambiguous'
        for n_ex, n_g, hname, ex, gains in hits[:3]:
            rows.append({
                'orphan': oname, 'host': hname, 'kind': kind,
                'source_kind': 'orphan' if not own_t1 else 'era-split',
                'exact_years': n_ex, 'gains_years': n_g,
                'years': ';'.join(map(str, sorted(ex)[:8])),
                'safe_scope': ';'.join(map(str, gains)),
                'orphan_gbp': round(payload[oname].get('v') or 0)})
    rows.sort(key=lambda r: (r['kind'], -r['exact_years'], -r['gains_years']))

    cols = ['orphan', 'host', 'kind', 'source_kind', 'exact_years',
            'gains_years', 'years', 'safe_scope', 'orphan_gbp']
    with open(out_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    n_era = len({r['orphan'] for r in rows if r['source_kind'] == 'era-split'})
    print(f'country-bearing sources: {len(orphans)}   anchor-holding hosts: {len(hosts)}')
    print(f'  of the matches, sources that ALSO hold an anchor elsewhere: {n_era}')
    print(f'  RESOLVED: {res}   AMBIGUOUS: {amb}'
          f'   (adjudicated declines filtered: {n_declined[0]})')
    print(f'  bar: >= {MIN_EXACT} years to the digit, each >= {MIN_QTY:,}')
    print(f'  `safe_scope` is the years the host LACKS - use it as the fold\'s year scope')
    print(f'-> {out_path}')
    for r in [x for x in rows if x['kind'] == 'resolved'][:20]:
        print(f"  {r['exact_years']}e gains {r['gains_years']:>2}y "
              f"[{r['source_kind'][:9]:9}] {r['orphan'][:38]:<40} -> {r['host'][:34]}")


if __name__ == '__main__':
    a = sys.argv[1] if len(sys.argv) > 1 else str(BASE / 'exports' / 'viz_payload.json')
    b = sys.argv[2] if len(sys.argv) > 2 else str(BASE / 'reports' / 'orphan_country_matches.csv')
    main(a, b)
