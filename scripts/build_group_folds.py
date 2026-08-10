#!/usr/bin/env python3
"""Fold the OCR spellings of each commodity-group heading into one identity.

The Statement's group headings are printed in capitals and frequently broken
across lines, and the OCR keeps the break. The parser then treats each surface
form as a different commodity, so one heading arrives as eight:

    1464  'HABERDASHERY and MILLINERY, including Embroidery and Needle-work'
     875  '... Embroidery and Needle- work'
     224  '... Em- broidery and Needlework'
      90  '... EMBROIDERY AND NEEDLE- WORK'
      43  '... Em- brodery and Needlework'      <- OCR, 1882
      42  '... Em- brassery and Needlework'     <- OCR, 1873

Two mechanisms are APPLIED, both purely mechanical and reversible:
  1. hyphenated line break   'Em- broidery' -> 'Embroidery'
  2. case and whitespace     'WOOD AND TIMBER' / 'WOOD and TIMBER' / stray NBSP

A third, near-miss OCR ('brodery' -> 'broidery'), is NOT applied. It is written
to a separate candidates file for review.

WHY EDIT DISTANCE IS NOT APPLIED AUTOMATICALLY
----------------------------------------------
A first version merged any family within edit distance 2 of a much larger one.
Commodity headings are short, and at that threshold nearly every four-letter
heading is a neighbour of several others. It produced, among 236 merges:

    OILS -> SILK  (1,923 rows)      LARD -> LEAD      RICE -> WINE
    HOPS -> HATS                    CORK -> PORK      ZINC -> WINE
    BRASS -> GLASS                  BARK -> PORK      Cows -> TOYS

Two of the 236 were right (ZINO -> ZINC, COALS -> COAL). Applying the rest would
have merged oils into silk. Length-relative thresholds only move the boundary;
the real discriminator is whether the two strings name the same commodity, which
is a judgement. So the candidates are emitted with their row counts and left for
a human, and only the mechanical folds ship.

WHERE THIS MAY AND MAY NOT BE USED
----------------------------------
This is a COMMODITY IDENTITY map, for aggregating series. It must NOT be used to
re-key printed blocks. Several spellings of one heading co-occur inside a single
volume (Needle-work and Needle- work both appear in as_1894..as_1898), so
merging them before walking a page's sections would splice unrelated row runs
together and corrupt the member/subtotal structure that every closure test
depends on. `reconcile_exports.py` and friends keep the raw group string.

The output is data, not code, so the folds can be reviewed and corrected by hand
-- the repo's existing convention for country aliases.

Usage:
    python3 scripts/build_group_folds.py [--out reference/group_name_folds.csv]
                                         [--min-rows 1] [--show 15]
"""
import argparse, collections, csv, re, unicodedata
import duckdb


def dehyphen(s):
    """'Em- broidery' -> 'Embroidery'. Also drops the newline the OCR leaves."""
    s = unicodedata.normalize('NFKC', s or '').replace(' ', ' ')
    s = s.replace('\n', ' ')
    s = re.sub(r'(\w)-\s+(\w)', r'\1\2', s)
    return re.sub(r'\s+', ' ', s).strip()


def canon_key(s):
    """Case/punctuation-insensitive identity key for a de-hyphenated heading."""
    return re.sub(r'[^a-z0-9]+', ' ', dehyphen(s).lower()).strip()


def edit1(a, b):
    """True when a and b are within a small edit distance (cheap, bounded)."""
    if abs(len(a) - len(b)) > 2:
        return False
    if a == b:
        return True
    # classic DP, but the strings here are short heading keys
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1] <= 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='db/uk_trade.duckdb')
    ap.add_argument('--out', default='reference/group_name_folds.csv')
    ap.add_argument('--min-rows', type=int, default=1)
    ap.add_argument('--show', type=int, default=15)
    a = ap.parse_args()

    con = duckdb.connect(a.db, read_only=True)
    rows = con.execute("""
        select flow, article_group, count(*) n, count(distinct volume) vols,
               min(year) y0, max(year) y1
        from country_obs
        where article_group is not null and trim(article_group) <> ''
        group by 1, 2
    """).fetchall()

    # stage 1+2: exact fold on the de-hyphenated, case-folded key
    fam = collections.defaultdict(list)
    for flow, g, n, vols, y0, y1 in rows:
        if n < a.min_rows:
            continue
        fam[(flow, canon_key(g))].append((g, n, vols, y0, y1))

    # stage 3 is REPORTED, NOT APPLIED -- see the docstring. Long keys only, so
    # the candidate list is worth reading rather than dominated by four-letter
    # collisions.
    by_flow = collections.defaultdict(list)
    for (flow, k), v in fam.items():
        by_flow[flow].append((k, sum(x[1] for x in v)))
    cands = []
    for flow, keys in by_flow.items():
        keys.sort(key=lambda kv: -kv[1])
        for i, (k, n) in enumerate(keys):
            if len(k) < 12:
                continue
            for big, bn in keys[:i]:
                if len(big) >= 12 and bn > n * 3 and edit1(k, big):
                    cands.append(dict(flow=flow, smaller=k, smaller_rows=n,
                                      larger=big, larger_rows=bn))
                    break

    merged = collections.defaultdict(list)
    for (flow, k), v in fam.items():
        merged[(flow, k)].extend(v)

    recs = []
    for (flow, k), variants in merged.items():
        variants.sort(key=lambda x: -x[1])
        canon = dehyphen(variants[0][0])
        for g, n, vols, y0, y1 in variants:
            method = ('identity' if g == canon else
                      'dehyphen' if dehyphen(g) != g else 'case')
            recs.append(dict(flow=flow, raw_group=g, canonical=canon,
                             method=method, rows=n, volumes=vols, y0=y0, y1=y1,
                             variants_in_family=len(variants)))

    recs.sort(key=lambda r: (-r['variants_in_family'], r['canonical'], -r['rows']))
    raw_n = collections.Counter(r['flow'] for r in recs)
    can_n = {f: len({r['canonical'] for r in recs if r['flow'] == f}) for f in raw_n}
    print(f'{"flow":>10} {"raw spellings":>14} {"canonical":>10} {"reduction":>10}')
    for f in sorted(raw_n):
        print(f'{f:>10} {raw_n[f]:>14,} {can_n[f]:>10,} '
              f'{100*(1-can_n[f]/raw_n[f]):>9.1f}%')
    m = collections.Counter(r['method'] for r in recs)
    print('\nby mechanism: ' + '  '.join(f'{k}={v}' for k, v in m.most_common()))

    print(f'\nlargest fold families')
    fams = collections.defaultdict(list)
    for r in recs:
        fams[(r['flow'], r['canonical'])].append(r)
    for (flow, canon), v in sorted(fams.items(),
                                   key=lambda kv: -len(kv[1]))[:a.show]:
        if len(v) < 3:
            continue
        print(f'  [{flow}] {canon[:58]}  ({len(v)} spellings, '
              f'{sum(x["rows"] for x in v):,} rows)')

    with open(a.out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(recs[0].keys()))
        w.writeheader()
        w.writerows(recs)
    print(f'\nwrote {a.out} ({len(recs):,} rows)')

    if cands:
        cf = 'reports/group_fold_candidates.csv'
        with open(cf, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(cands[0].keys()))
            w.writeheader()
            w.writerows(cands)
        print(f'wrote {cf} ({len(cands)} near-miss candidates, NOT applied)')


if __name__ == '__main__':
    main()
