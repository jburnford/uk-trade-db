#!/usr/bin/env python3
"""Canada's ghost acres, whole period 1870-1900: WHERE in the world was the
land and labour behind what Canada consumed by way of Britain?

Two layers, both from the UK Annual Statement of Trade, both allocated over
the UK's import origins (exports/map_slim.json, curated, whole-period sums):

  THROUGH BRITAIN   foreign and colonial goods re-exported to Canada, each
                    commodity spread over the UK's import origins for it
                    (analyze_canada_reach.py does this by year; here summed).
  EMBODIED          British and Irish produce shipped to Canada, each
                    commodity spread over the origins of its RAW MATERIAL --
                    cotton goods over raw-cotton origins, woollens over wool,
                    refined sugar over unrefined sugar (beet and cane), linens
                    over flax, silks over raw silk, telegraph cable over copper
                    and gutta percha -- with an explicit DOMESTIC share where
                    Britain grew or mined part of the material itself (its own
                    wool clip, iron ore, hides, flax, lead, tin), and an
                    UNTRACED share where the Statement cannot follow the input
                    (paper's esparto and rags, chemicals). Value is the
                    measure; British labour and coal ride with the material
                    (a woollen coat is counted where its wool grew).

This is an allocation under stated assumptions, not an observation. The
Statement records destination for exports and origin for imports and never
both on one line; the material shares below are period-typical figures from
the trade literature, rounded, and are meant to be argued with.

Outputs: reports/canada_ghost_acres.json, reports/canada_ghost_acres.csv
Usage:   python3 scripts/analyze_ghost_acres.py
"""
import collections, csv, json, sys
sys.path.insert(0, 'scripts')
from analyze_canada_reach import CROSSWALK, region_of

EXPL = 'reports/canada_explorer.json'
MAP = 'exports/map_slim.json'

# raw-material import groups in map_slim: name -> (group prefixes, article prefixes or None)
MATERIALS = {
    'cotton':   (['Cotton'], ['Raw']),
    'wool':     (['Wool'], ['Sheep']),
    'sugar':    (['Sugar'], None),                       # unrefined cane and beet, refined foreign
    'flax':     (['Flax', 'Flax, Dressed Or Undressed'], None),
    'jute':     (['Jute'], None),
    'hemp':     (['Hemp', 'Hemp, Dressed Or Undressed'], None),
    'silk':     (['Silk'], ['Raw', 'Thrown', 'Knubs', 'Waste']),
    'hides':    (['Hides', 'Hides, Not Tanned, Tawed, Curried, Or In Any Way Dressed',
                  'Hides, Raw, And Pieces Thereof'], None),
    'tallow':   (['Tallow And Stearine'], None),
    'palm oil': (['Oil'], ['Palm']),
    'linseed':  (['Seeds'], ['Flax', 'Linseed']),
    'iron ore': (['Iron', 'Iron Ore'], ['Ore']),
    'copper':   (['Copper', 'Copper, Ore Of'], None),
    'zinc':     (['Zinc', 'Zinc Or Spelter'], None),
    'lead':     (['Lead'], None),
    'tin':      (['Tin'], None),
    'gutta percha': (['Gutta Percha'], None),
    'caoutchouc': (['Caoutchouc'], None),
    'gum':      (['Gum'], None),
    'tea':      (['Tea'], None),
    'timber':   (['Wood And Timber'], None),
}

# British-produce commodity -> [(material or DOMESTIC or UNTRACED, weight)]
# weights sum to 1; DOMESTIC = the material Britain grew/mined itself
W_WOOL = [('wool', 0.67), ('DOMESTIC', 0.33)]              # British clip ~1/3 of wool used
W_COTTON = [('cotton', 1.0)]
W_MIXED = [('cotton', 0.45), ('wool', 0.30), ('silk', 0.10), ('DOMESTIC', 0.15)]
W_IRON = [('iron ore', 0.25), ('DOMESTIC', 0.75)]           # ore imports ~1/4 by the 1890s; coal domestic
RULES = {
    'WOOLLEN AND WORSTED MANUFACTURES': W_WOOL, 'WOOLLEN YARN': W_WOOL, 'CARPETS': W_WOOL,
    'WOOL': [('DOMESTIC', 1.0)],
    'COTTON MANUFACTURES': W_COTTON, 'COTTON YARN AND TWIST': W_COTTON,
    'HABERDASHERY AND MILLINERY': W_MIXED,
    'APPAREL AND SLOPS': [('wool', 0.45), ('cotton', 0.35), ('flax', 0.05), ('DOMESTIC', 0.15)],
    'HATS': [('wool', 0.45), ('silk', 0.15), ('DOMESTIC', 0.40)],
    'UMBRELLAS and PARASOLS': [('cotton', 0.35), ('silk', 0.30), ('DOMESTIC', 0.35)],
    'LINEN MANUFACTURES': [('flax', 0.85), ('DOMESTIC', 0.15)],
    'JUTE MANUFACTURES': [('jute', 1.0)],
    'CORDAGE, CABLES, ROPES AND TWINE': [('hemp', 0.9), ('DOMESTIC', 0.1)],
    'SILK MANUFACTURES': [('silk', 1.0)],
    'SUGAR, REFINED': [('sugar', 1.0)],
    'IRON AND STEEL': W_IRON, 'HARDWARES AND CUTLERY': W_IRON, 'MACHINERY AND MILLWORK': W_IRON,
    'IMPLEMENTS AND TOOLS': W_IRON, 'ARMS, AMMUNITION AND MILITARY STORES': W_IRON,
    'TELEGRAPHIC WIRES AND APPARATUS': [('copper', 0.4), ('gutta percha', 0.2), ('iron ore', 0.1), ('DOMESTIC', 0.3)],
    'ZINC OR SPELTER': [('zinc', 1.0)],
    'LEAD': [('lead', 0.5), ('DOMESTIC', 0.5)],
    'TIN, UNWROUGHT': [('tin', 0.6), ('DOMESTIC', 0.4)],
    'COPPER': [('copper', 0.9), ('DOMESTIC', 0.1)],
    'BRASS MANUFACTURES': [('copper', 0.6), ('zinc', 0.3), ('DOMESTIC', 0.1)],
    'PLATED AND GILT WARES': [('copper', 0.5), ('DOMESTIC', 0.5)],
    'LEATHER': [('hides', 0.5), ('DOMESTIC', 0.5)], 'SADDLERY AND HARNESS': [('hides', 0.5), ('DOMESTIC', 0.5)],
    'SKINS AND FURS': [('hides', 0.5), ('DOMESTIC', 0.5)],
    'OIL, OTHER THAN ESSENTIAL': [('linseed', 0.8), ('DOMESTIC', 0.2)],
    "PAINTERS' COLOURS AND MATERIALS": [('lead', 0.3), ('linseed', 0.3), ('DOMESTIC', 0.4)],
    'SOAP': [('tallow', 0.5), ('palm oil', 0.3), ('DOMESTIC', 0.2)],
    'CANDLES': [('tallow', 0.6), ('palm oil', 0.2), ('DOMESTIC', 0.2)],
    'GREASE, TALLOW AND ANIMAL FAT': [('tallow', 0.7), ('DOMESTIC', 0.3)],
    'CAOUTCHOUC MANUFACTURES': [('caoutchouc', 1.0)],
    'GUM': [('gum', 1.0)],
    'TEA': [('tea', 1.0)],
    'PAPER': [('UNTRACED', 0.5), ('DOMESTIC', 0.5)],
    'BOOKS, PRINTED': [('UNTRACED', 0.3), ('DOMESTIC', 0.7)],
    'STATIONERY, other than Paper': [('UNTRACED', 0.4), ('DOMESTIC', 0.6)],
    'FURNITURE (HOUSEHOLD)': [('timber', 0.6), ('DOMESTIC', 0.4)],
    'WOOD AND TIMBER': [('timber', 1.0)],
    'HIDES, RAW': [('DOMESTIC', 1.0)],
    'CHEMICAL PRODUCTS AND PREPARATIONS': [('UNTRACED', 0.3), ('DOMESTIC', 0.7)],
    'MEDICINES': [('UNTRACED', 0.4), ('DOMESTIC', 0.6)],
}
# everything else (earthenware, glass, coal, alkali, salt, cement, beer, spirits,
# animals, pickles, corn, books...) is DOMESTIC


def main():
    D = json.load(open(EXPL))
    m = json.load(open(MAP))
    gaz, comms = m['gaz'], m['commodities']

    ALIAS = {'Australia': 'Australasia', 'British India': 'British East Indies',
             'Chili': 'Chile', 'Portugal, Azores, And Madeira': 'Portugal',
             'Turkey Proper': 'Turkey', 'Sweden And Norway': 'Sweden',
             'United States Of Colombia (Newgranada': 'United States Of Colombia',
             'West Africa Portuguese Possessions Not Particularly Design Nated': 'Portuguese Possessions In Western Africa',
             'Western Africa (Foreign': 'British West Africa'}

    def parent(label):
        g = gaz.get(label) or {}
        p = g.get('parent') or label
        return ALIAS.get(p, p)

    # whole-period origin mix for a set of import groups: {consignor label: value}
    def mix(prefixes, arts=None):
        tot = collections.Counter()
        for name, c in comms.items():
            g, _, a = name.partition(' — ')
            if g in prefixes and (arts is None or any(a.startswith(x) for x in arts)):
                for co, by in (c.get('c') or {}).items():
                    for y, cell in by.items():
                        v = cell[0] if isinstance(cell, list) else None
                        if v:
                            tot[co] += v
        s = sum(tot.values())
        return {k: v / s for k, v in tot.items()} if s else {}

    mat_mix = {k: mix(*v) for k, v in MATERIALS.items()}

    ex = [c for c in D['commodities'] if c['flow'] == 'export_uk']
    rx = [c for c in D['commodities'] if c['flow'] == 'reexport']

    # layer 1: through Britain
    through = collections.Counter()      # label -> value
    through_by_comm = {}
    unmapped_rx = 0.0
    for c in rx:
        pref = CROSSWALK.get(c['name'])
        sh = mix(pref) if pref else {}
        if not sh:
            unmapped_rx += c['total']
            through['UNTRACED'] += c['total']
            continue
        through_by_comm[c['name']] = c['total']
        for lab, s in sh.items():
            through[lab] += c['total'] * s
    # layer 2: embodied
    embodied = collections.Counter()
    emb_by_material = collections.Counter()
    place_material = collections.defaultdict(collections.Counter)   # parent place -> material -> value
    emb_by_comm = {}
    for c in ex:
        rule = RULES.get(c['name'], [('DOMESTIC', 1.0)])
        emb_by_comm[c['name']] = rule
        for mat, w in rule:
            v = c['total'] * w
            if mat in ('DOMESTIC', 'UNTRACED'):
                embodied[mat] += v
                emb_by_material[mat] += v
                continue
            emb_by_material[mat] += v
            sh = mat_mix.get(mat) or {}
            if not sh:
                embodied['UNTRACED'] += v
                continue
            for lab, s in sh.items():
                embodied[lab] += v * s
                place_material[parent(lab)][mat] += v * s
    place_through_comm = collections.defaultdict(collections.Counter)  # place -> re-export commodity
    for c in rx:
        pref = CROSSWALK.get(c['name'])
        sh = mix(pref) if pref else {}
        for lab, s in sh.items():
            place_through_comm[parent(lab)][c['name']] += c['total'] * s

    # roll consignors up to the gazetteer parent, then to regions
    def rollup(counter):
        out = collections.Counter()
        for lab, v in counter.items():
            out[lab if lab in ('DOMESTIC', 'UNTRACED') else parent(lab)] += v
        return out
    thr_p, emb_p = rollup(through), rollup(embodied)
    places = sorted(set(thr_p) | set(emb_p), key=lambda k: -(thr_p[k] + emb_p[k]))
    rows = []
    for p in places:
        g = gaz.get(p) or {}
        reg = ('Britain' if p == 'DOMESTIC' else 'Untraced' if p == 'UNTRACED'
               else region_of(p, gaz))
        rows.append(dict(place=p, region=reg, lat=g.get('lat'), lon=g.get('lon'),
                         through=round(thr_p[p]), embodied=round(emb_p[p]),
                         total=round(thr_p[p] + emb_p[p]),
                         materials=[(k, round(v)) for k, v in place_material[p].most_common(4)],
                         through_goods=[(k, round(v)) for k, v in place_through_comm[p].most_common(4)]))
    reg_tot = collections.defaultdict(lambda: [0.0, 0.0])
    for r in rows:
        reg_tot[r['region']][0] += r['through']
        reg_tot[r['region']][1] += r['embodied']
    T_thr, T_emb = sum(thr_p.values()), sum(emb_p.values())
    out = dict(
        total_through=round(T_thr), total_embodied=round(T_emb),
        places=rows,
        regions=[dict(region=k, through=round(v[0]), embodied=round(v[1]), total=round(v[0] + v[1]))
                 for k, v in sorted(reg_tot.items(), key=lambda kv: -(kv[1][0] + kv[1][1]))],
        materials=[(k, round(v)) for k, v in emb_by_material.most_common()],
        material_mix={k: [(lab, round(s, 3)) for lab, s in sorted(v.items(), key=lambda kv: -kv[1])[:8]]
                      for k, v in mat_mix.items()},
        rules={k: v for k, v in RULES.items()},
        export_commodities=[(c['name'], c['total']) for c in sorted(ex, key=lambda c: -c['total'])],
        reexport_commodities=[(c['name'], c['total']) for c in sorted(rx, key=lambda c: -c['total'])],
        unmapped_reexport=round(unmapped_rx),
    )
    json.dump(out, open('reports/canada_ghost_acres.json', 'w'), indent=1)
    with open('reports/canada_ghost_acres.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['place', 'region', 'lat', 'lon', 'through', 'embodied', 'total'],
                           extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)
    print(f'through Britain £{T_thr:,.0f}   embodied in British goods £{T_emb:,.0f}')
    for r in out['regions']:
        print(f"  {r['region']:30} through {r['through']:>12,}  embodied {r['embodied']:>12,}  total {r['total']:>12,}")
    print('top places:')
    for r in rows[:25]:
        print(f"  {r['place']:40} {r['region']:28} thr {r['through']:>10,} emb {r['embodied']:>11,}")


if __name__ == '__main__':
    main()
