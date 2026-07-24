#!/usr/bin/env python3
"""Commodity triage for public curation: separate genuine (obscure but real)
tail commodities from glue-noise, without hand-reviewing all ~2,500.

Signals per commodity:
  - T1 attestation (§TOTAL series present) and its span
  - dupe_score: fraction of country-cells (country, unit, year, qty) that
    appear identically inside ANOTHER commodity (phantom/dupe fingerprint —
    stale-label glue admits the same printed cells under two labels)
  - place_article: display name ends '— <place>' where <place> is a known
    country label (article-drift phantom class: seal 1886 'Whale Fisheries')
  - fragment_of: no T1, but name tokens are a subset of a T1-attested
    commodity's tokens (era-split fold candidate)

Buckets: KEEP / PHANTOM? / FOLD? / REVIEW, ranked by GBP.
Output: reports/commodity_curation_queue.csv

Curation actions live in reference/commodity_curation.csv
(commodity, action[keep|drop|fold], target, note) — consumed by
build_viz_payload.py as the final pass.
"""
import json, sys, csv, collections, re

def toks(name):
    return frozenset(w for w in re.split(r'[^A-Za-z]+', name.upper())
                     if len(w) > 2 and w not in
                     ('AND','THE','FOR','NOT','ALL','ANY','WAY','SORTS','OTHER',
                      'OF','OR','IN'))

def main(path):
    p = json.load(open(path))
    # cell fingerprint index
    cell_owner = collections.defaultdict(set)   # (country,unit,year,qty) -> names
    stats = {}
    for name, e in p.items():
        c = e.get('c') or {}
        cells = []
        for ctry, byu in c.items():
            if ctry == '§TOTAL':
                continue
            for u, series in byu.items():
                for row in series:
                    if row[1] and row[1] > 100:      # tiny cells collide by chance
                        cells.append((ctry, u, row[0], row[1]))
        for k in cells:
            cell_owner[k].add(name)
        stats[name] = dict(gbp=e.get('v') or 0, has_t1='§TOTAL' in c,
                           n_cells=len(cells), cells=cells,
                           n_countries=sum(1 for k in c if k != '§TOTAL'))
    # place vocabulary: only labels that appear as a country in >=5
    # commodities (one-off junk 'countries' like a stray 'Raw' cell would
    # otherwise poison the article-drift check)
    cfreq = collections.Counter()
    for name, e in p.items():
        for k in (e.get('c') or {}):
            if k != '§TOTAL':
                cfreq[k.upper()] += 1
    countries = {k for k, n in cfreq.items() if n >= 5}
    t1_names = {n: toks(n) for n, s in stats.items() if s['has_t1']}

    rows = []
    for name, s in stats.items():
        dupes = sum(1 for k in s['cells'] if len(cell_owner[k]) > 1)
        dupe_score = dupes / s['n_cells'] if s['n_cells'] else 0
        # who do the dupe cells belong to (biggest co-owner)?
        co = collections.Counter()
        for k in s['cells']:
            for o in cell_owner[k]:
                if o != name:
                    co[o] += 1
        co_top = co.most_common(1)[0][0] if co else ''
        place_article = ''
        m = re.match(r'^(.*?) — (.+)$', name)
        if m:
            art = re.sub(r'^[.\s]+', '', m.group(2)).upper()
            if art in countries:
                place_article = m.group(2)
        frag = ''
        if not s['has_t1'] and s['n_cells']:
            t = toks(name)
            if t:
                cands = [(n2, stats[n2]['gbp']) for n2, t2 in t1_names.items()
                         if n2 != name and t and t < t2]
                if cands:
                    frag = max(cands, key=lambda x: x[1])[0]
        if s['n_cells'] == 0:
            bucket = 'EMPTY'
        elif place_article:
            bucket = 'PHANTOM?'
        elif dupe_score > 0.5 and co_top and stats.get(co_top, {}).get('gbp', 0) >= s['gbp']:
            bucket = 'DUPE-FAM'
        elif frag:
            bucket = 'FOLD?'
        elif s['has_t1'] and dupe_score < 0.2:
            bucket = 'KEEP'
        elif dupe_score < 0.1:
            bucket = 'KEEP'          # no T1 but no dupe evidence: genuine tail
        else:
            bucket = 'REVIEW'
        rows.append(dict(commodity=name, bucket=bucket, gbp=int(s['gbp']),
                         has_t1=int(s['has_t1']), n_cells=s['n_cells'],
                         n_countries=s['n_countries'],
                         dupe_pct=round(100*dupe_score),
                         dupe_partner=co_top, place_article=place_article,
                         fold_candidate=frag))
    rows.sort(key=lambda r: (r['bucket'], -r['gbp']))
    out = 'reports/commodity_curation_queue.csv'
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    cnt = collections.Counter(r['bucket'] for r in rows)
    gbp = collections.Counter()
    for r in rows:
        gbp[r['bucket']] += r['gbp']
    G = sum(gbp.values()) or 1
    print(f'{len(rows)} commodities -> {out}')
    for b in ('KEEP', 'FOLD?', 'DUPE-FAM', 'PHANTOM?', 'REVIEW', 'EMPTY'):
        print(f'  {b:8s}: {cnt[b]:5d}  ({100*gbp[b]/G:5.1f}% of GBP)')

if __name__ == '__main__':
    main(sys.argv[1])
