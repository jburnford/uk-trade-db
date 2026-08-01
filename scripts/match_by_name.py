#!/usr/bin/env python3
"""Match a stale-headed source to its host by NAME, with arithmetic confirming.

The arithmetic matchers (`match_orphan_countries`, `match_shadow_anchors`)
require **two** years agreeing to the digit, and that bar is correct on its own
terms: across ~900,000 candidate pairs a single agreeing year is expected by
chance about 180 times. But it has two costs that only became visible once the
seam ran dry.

  * A source carrying only ONE year can never clear it, however perfect the
    match. There are 483 such nodes.
  * A source carrying many years but agreeing in only one is likewise rejected,
    even when the two names are the same commodity.

This tool inverts the evidence. **The name relation is the precondition and the
arithmetic is the confirmation**, so one agreeing year is enough:

  * the source's trailing article segment must be the same commodity as the
    host — by signature, or by normalised string equality of the trailing
    segments (which catches 'Unenumerated, Raw' against 'Unenumerated : Raw');
  * at least one year where the source's country cells sum to the host's
    Tier-1 within TOL, the host holding no country data that year and the
    source not anchoring it;
  * exactly one host clearing the bar.

Generic articles are the danger — 'Unenumerated' and 'Raw' name no commodity
and would match everything — so a signature-only match is required to be
non-empty, and the string-equality path is what admits the generic ones, since
identical generic articles under *different* groups still have to pass the
arithmetic and the uniqueness test.

Hand-adjudication is still required. The 2026-07-31 single-year run accepted 16
of 22 and declined 6, a 27% false-positive rate on arithmetic alone; every
decline is in reference/match_declines.csv with its reason.

Usage: python3 scripts/match_by_name.py [payload.json] [out.csv]
   ->  reports/name_matches.csv
"""
import csv
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import match_declines as MD
import validate_gold as V

BASE = Path('/home/jic823/uk_trade_db')
TK = '§TOTAL'
MIN_QTY = 1000
TOL = 0.0002


def tail(name):
    """The article segment: everything after the last ' — ' or ' : '."""
    s = name
    for sep in (' — ', ' : '):
        if sep in s:
            s = s.rsplit(sep, 1)[1]
    return s.strip()


def norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii',
                                                      'ignore').decode()
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', s.lower())).strip()


def related(sname, hname):
    st, ht = tail(sname), tail(hname)
    ss, hs = V.sig(st), V.sig(ht)
    if ss and ss == hs:
        return 'sig'
    if norm(st) and norm(st) == norm(ht):
        return 'string'
    # the host may BE the article, with no group prefix at all
    if ss and ss == V.sig(hname):
        return 'host-is-article'
    return ''


def main(payload_path, out_path):
    dec_pairs, dec_blanket = MD.load_declines()
    payload = json.load(open(payload_path))
    srcs, hosts = {}, {}
    for name, e in payload.items():
        c = e.get('c') or {}
        t1 = c.get(TK)
        per = defaultdict(lambda: defaultdict(float))
        for cty, byu in c.items():
            if cty == TK or '(' in cty:
                continue
            for u, cells in byu.items():
                for r in cells:
                    if r[1]:
                        per[u][r[0]] += r[1]
        if per:
            own = {(u, r[0]) for u, cells in (t1 or {}).items()
                   for r in cells if r[1]}
            srcs[name] = (per, own)
        if t1:
            u = max(t1, key=lambda x: len(t1[x]))
            ty = {r[0]: r[1] for r in t1[u] if r[1]}
            if ty:
                hosts[name] = (u, ty, {y for y in per.get(u, {}) if per[u][y]})

    rows, n_dec = [], 0
    for sn, (per, own) in srcs.items():
        hits = []
        for hn, (u, ty, have) in hosts.items():
            if hn == sn or u not in per:
                continue
            rel = related(sn, hn)
            if not rel:
                continue
            if MD.declined(sn, hn, dec_pairs, dec_blanket):
                n_dec += 1
                continue
            ex = [y for y in ty if y in per[u] and y not in have
                  and (u, y) not in own and ty[y] >= MIN_QTY
                  and abs(per[u][y] - ty[y]) <= max(1.0, TOL * ty[y])]
            if ex:
                gains = [y for y in ty if y in per[u] and y not in have
                         and (u, y) not in own]
                hits.append((len(ex), len(gains), hn, ex, sorted(gains), rel))
        if not hits:
            continue
        hits.sort(reverse=True)
        kind = 'resolved' if len(hits) == 1 else 'ambiguous'
        for n_ex, n_g, hn, ex, gains, rel in hits[:3]:
            rows.append({
                'source': sn, 'host': hn, 'kind': kind, 'relation': rel,
                'exact_years': n_ex, 'gains_years': n_g,
                'years': ';'.join(map(str, sorted(ex)[:8])),
                'safe_scope': ';'.join(map(str, gains)),
                'source_gbp': round(payload[sn].get('v') or 0)})
    rows.sort(key=lambda r: (r['kind'], -r['source_gbp']))
    with open(out_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ['source'])
        w.writeheader()
        w.writerows(rows)
    res = len({r['source'] for r in rows if r['kind'] == 'resolved'})
    amb = len({r['source'] for r in rows if r['kind'] == 'ambiguous'})
    print(f'sources with countries: {len(srcs)}   hosts: {len(hosts)}')
    print(f'  RESOLVED: {res}   AMBIGUOUS: {amb}   '
          f'(adjudicated declines filtered: {n_dec})')
    print(f'  bar: NAME RELATION required, then >= 1 year to the digit '
          f'(>= {MIN_QTY:,})')
    print(f'-> {out_path}')
    for r in [x for x in rows if x['kind'] == 'resolved'][:25]:
        print(f"  {r['source_gbp']:>11,} {r['exact_years']}e gains "
              f"{r['gains_years']:>2}y [{r['relation']:<14}] "
              f"{r['source'][:40]:<40} -> {r['host'][:32]}")


if __name__ == '__main__':
    a = sys.argv[1] if len(sys.argv) > 1 else str(BASE / 'exports' / 'viz_payload.json')
    b = sys.argv[2] if len(sys.argv) > 2 else str(BASE / 'reports' / 'name_matches.csv')
    main(a, b)
