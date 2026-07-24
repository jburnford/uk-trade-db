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

# generic country-column labels: OCR glue drops these junk 'countries'
# ('Unenumerated', 'Foreign', 'Total of', 'Other Sorts') into >=5 commodities,
# so they pass the place-vocab frequency gate and wrongly mark real qualifier
# articles ('Iron — Unenumerated') as place-article phantoms. A label whose
# tokens are ALL generic is never a place.
# 'MANUFACTURES'/'MANUFACTURED' earn their place here for the opposite reason:
# they never occur in a country label, but 'Manufactures Of' IS a legitimate
# commodity article ('Caoutchouc — Manufactures Of' = rubber goods). It reached
# the place vocabulary only because the same string is also a junk country
# label in >=5 commodities, which then marked three real commodities PHANTOM?.
GENERIC_PLACE = {'UNENUMERATED', 'UNENUMBERED', 'FOREIGN', 'TOTAL', 'OTHER',
                 'SORTS', 'KINDS', 'UNSPECIFIED', 'DESCRIPTIONS', 'ARTICLES',
                 'GOODS', 'SUNDRIES', 'DECLARED', 'SUCH', 'VALUE', 'ENUMERATED',
                 'NULL', 'NONE', 'MISCELLANEOUS', 'MANUFACTURES', 'MANUFACTURED'}


def real_place(label):
    """True if the label carries at least one token that is not generic
    junk-country vocab (so 'British India' is a place, 'Unenumerated' is not)."""
    return bool(toks(label) - GENERIC_PLACE)

def main(path):
    p = json.load(open(path))
    # cell fingerprint index
    cell_owner = collections.defaultdict(set)   # (country,unit,year,qty) -> names
    # UNIT-BLIND index (country,year,qty). A label-shift copy of a printed
    # origin table usually loses its unit header, so the duplicate cells carry
    # unit '?' while the host carries 'Cwt' — the unit-aware fingerprint then
    # scores 0% dupe and the copy looks like a genuine tail commodity
    # ('Cotton — British India' is an exact '?'-unit copy of Cotton — Raw's
    # 1883/84 table and scored dupe=0). Matching on (country, year, qty) alone
    # catches these; a >100 qty triple colliding by chance across two labels is
    # rare enough to be worth the false-positive risk.
    cell_owner_ub = collections.defaultdict(set)
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
            cell_owner_ub[(k[0], k[2], k[3])].add(name)
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
    countries = {k for k, n in cfreq.items() if n >= 5 and real_place(k)}
    t1_names = {n: toks(n) for n, s in stats.items() if s['has_t1']}

    # standalone commodity vocabulary for the name-as-article check: a
    # commodity printed as a bare head (no ' — ' article) that is itself
    # T1-attested is a genuine independent top-level commodity. When such a
    # name appears as ANOTHER commodity's article ('Cards, Playing — Molasses',
    # 'Iron — Leather Manufacturers', 'Jute — Boots And Shoes'), the article's
    # cells are that standalone commodity's rows glued under a stale host label.
    # Keyed by token signature so 'Molasses' the head matches 'Molasses' the
    # article. Requiring the head to be T1-attested is what keeps out glue
    # bare-heads like 'In Blocks, Ingots, Bars' or 'Manufactures, Unenumerated'
    # (article fragments that only exist as truncation artifacts, never printed
    # as their own abstract line). Multi-token heads only (single-token
    # 'Iron'/'Wool' collide with legitimate compound articles).
    heads = {}
    for name, s in stats.items():
        if ' — ' in name or not s['has_t1']:
            continue
        sig = toks(name)
        if sig and sig not in heads:
            heads[sig] = name

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
        # unit-blind pass: same measures on (country, year, qty)
        ub_keys = [(k[0], k[2], k[3]) for k in s['cells']]
        dupes_ub = sum(1 for k in ub_keys if len(cell_owner_ub[k]) > 1)
        dupe_score_ub = dupes_ub / s['n_cells'] if s['n_cells'] else 0
        co_ub = collections.Counter()
        for k in ub_keys:
            for o in cell_owner_ub[k]:
                if o != name:
                    co_ub[o] += 1
        co_top_ub, co_top_ub_n = co_ub.most_common(1)[0] if co_ub else ('', 0)
        # host share: what fraction of THIS commodity's cells the single
        # biggest co-owner accounts for. >=0.5 means the label is essentially
        # a re-print of that host's table, not an overlapping neighbour.
        host_share = co_top_ub_n / s['n_cells'] if s['n_cells'] else 0
        place_article = ''
        name_article = ''            # article IS a standalone commodity name
        m = re.match(r'^(.*?) — (.+)$', name)
        if m:
            art = re.sub(r'^[.\s]+', '', m.group(2)).upper()
            if art in countries:
                place_article = m.group(2)
            # only when the host—article combo is NOT itself T1-attested: a
            # printed abstract commodity ('Wool — Sheep or Lambs'',
            # 'Animals, Living — Oxen and Bulls') is real, not glue, even
            # though its article fragment recurs as a bare head elsewhere.
            art_sig = toks(m.group(2))
            host_sig = toks(m.group(1))
            if (not s['has_t1'] and len(art_sig) >= 2 and art_sig in heads
                    and art_sig != host_sig and heads[art_sig] != name):
                name_article = heads[art_sig]
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
        elif name_article:
            bucket = 'NAME-ART?'
        elif dupe_score > 0.5 and co_top and stats.get(co_top, {}).get('gbp', 0) >= s['gbp']:
            bucket = 'DUPE-FAM'
        elif (host_share > 0.5 and co_top_ub
                and stats.get(co_top_ub, {}).get('gbp', 0) >= s['gbp']):
            bucket = 'DUPE-FAM'      # unit-lost re-print of a single host
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
                         dupe_partner=co_top,
                         dupe_pct_ub=round(100*dupe_score_ub),
                         host_share=round(100*host_share),
                         dupe_partner_ub=co_top_ub, place_article=place_article,
                         name_article=name_article, fold_candidate=frag))
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
    for b in ('KEEP', 'FOLD?', 'DUPE-FAM', 'NAME-ART?', 'PHANTOM?', 'REVIEW',
              'EMPTY'):
        print(f'  {b:9s}: {cnt[b]:5d}  ({100*gbp[b]/G:5.1f}% of GBP)')

if __name__ == '__main__':
    main(sys.argv[1])
