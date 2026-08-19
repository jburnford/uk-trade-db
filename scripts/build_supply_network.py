#!/usr/bin/env python3
"""The probable supply network behind Canadian consumption via Britain,
1870-1900 -- a geography, not a quantification.

Nodes are places; edges say "this commodity reached Canada from this place by
this route". Suppliers are the MAJOR consignors in the UK's own import tables
for the commodity (re-exports) or for its raw material (British-made goods):
any origin carrying >= MIN_SHARE of the whole-period import mix, up to MAX_PER,
ordered by rank. No values are emitted -- only rank -- because the ranking is
the sturdy part of the import tables and the values are not the point.

Routes:
  forwarded    landed in Britain and re-exported unchanged (tea, silks, wine)
  worked       raw material worked up in a British industry, with the
               conventional British centre named (Lancashire cotton, Yorkshire
               wool, Dundee jute, Belfast linen, Middlesbrough iron...)
  home         the material Britain grew or mined itself (its wool clip, ore
               and coal, hides), or goods with no traceable input

Outputs
  reports/canada_supply_network_edges.csv   commodity, family, route, hub,
                                            supplier, region, rank, note
  reports/canada_supply_network.json        the same plus node coordinates
Usage: python3 scripts/build_supply_network.py
"""
import collections, csv, json, sys
sys.path.insert(0, 'scripts')
from analyze_canada_reach import CROSSWALK, region_of
from analyze_ghost_acres import MATERIALS, RULES

EXPL = 'reports/canada_explorer.json'
MAP = 'exports/map_slim.json'
MIN_SHARE = 0.05
MAX_PER = 6
MIN_CANADA = 400_000       # commodities below this (whole period) are left out of the network

FAMILY = {  # export-side commodity/material -> family
    'textiles': ['WOOLLEN AND WORSTED MANUFACTURES', 'COTTON MANUFACTURES', 'HABERDASHERY AND MILLINERY',
                 'APPAREL AND SLOPS', 'LINEN MANUFACTURES', 'SILK MANUFACTURES', 'HATS', 'JUTE MANUFACTURES',
                 'COTTON YARN AND TWIST', 'WOOLLEN YARN', 'CORDAGE, CABLES, ROPES AND TWINE', 'UMBRELLAS and PARASOLS',
                 'WOOL', 'HEMP', 'FLAX', 'EMBROIDERY AND NEEDLEWORK', 'LACE, and Articles thereof', 'SILK, RAW AND THROWN',
                 'WOOLLEN MANUFACTURES', 'HATS OR BONNETS'],
    'food & drink': ['SUGAR, REFINED', 'TEA', 'FRUIT', 'RICE', 'SPICES', 'WINE', 'COFFEE', 'SPIRITS', 'HAMS', 'FISH',
                     'SUGAR', 'COCOA', 'FARINACEOUS SUBSTANCES', 'LIQUORICE', 'CORN, GRAIN, MEAL AND FLOUR',
                     'PICKLES, VINEGAR, SAUCES AND CONDIMENTS', 'BEER AND ALE', 'SPIRITS, BRITISH AND IRISH', 'SALT'],
    'metals & minerals': ['IRON AND STEEL', 'ZINC OR SPELTER', 'TELEGRAPHIC WIRES AND APPARATUS', 'HARDWARES AND CUTLERY',
                          'MACHINERY AND MILLWORK', 'COPPER', 'LEAD', 'TIN, UNWROUGHT', 'ARMS, AMMUNITION AND MILITARY STORES',
                          'ZINC AND ZINC ORE', 'TIN', 'COALS, CINDERS, &c.', 'BRASS MANUFACTURES', 'PLATED AND GILT WARES'],
    'animal products': ['LEATHER', 'SKINS AND FURS', 'SKINS, FURS AND PELTS', 'TALLOW and STEARINE', 'HIDES, RAW',
                        'GREASE, TALLOW AND ANIMAL FAT', 'SOAP', 'CANDLES', 'SADDLERY AND HARNESS', 'ANIMALS, LIVING',
                        'BRISTLES', 'FEATHERS AND DOWN'],
    'oils, gums & dyes': ['OIL, OTHER THAN ESSENTIAL', "PAINTERS' COLOURS AND MATERIALS", 'CAOUTCHOUC MANUFACTURES',
                          'CAOUTCHOU', 'GUM', 'DYE STUFFS AND DYE WOODS', 'DRUGS', 'CHEMICAL PRODUCTS AND PREPARATIONS',
                          'MEDICINES', 'ALKALI', 'OIL', 'CHEMICAL MANUFACTURES AND PRODUCTS', 'GUTTA PERCHA', 'SALTPETRE',
                          "PAINTERS' Colours and Pigments, Unenumerated"],
    'manufactures, other': ['EARTHEN AND CHINA WARE', 'GLASS', 'PAPER', 'BOOKS, PRINTED', 'STATIONERY, other than Paper',
                            'CEMENT', 'FURNITURE (HOUSEHOLD)', 'WOOD AND TIMBER', 'GOODS UNENUMERATED', 'CLOCKS AND WATCHES',
                            'MUSICAL INSTRUMENTS', 'TOYS', 'FLOWERS, Artificial'],
}
FAM_OF = {c: f for f, cs in FAMILY.items() for c in cs}

# the conventional British centre where a material was worked up
HUB = {'cotton': 'Lancashire (Manchester, Oldham, Blackburn)', 'wool': 'West Riding (Bradford, Leeds, Huddersfield)',
       'flax': 'Belfast and Dundee', 'jute': 'Dundee', 'hemp': 'Bridport, Hull, Glasgow rope-walks',
       'silk': 'Macclesfield, Coventry, Spitalfields', 'sugar': 'Greenock, Liverpool, London refineries',
       'iron ore': 'Middlesbrough (Cleveland), South Wales, Cumberland', 'copper': 'Swansea',
       'zinc': 'Swansea, Birmingham', 'lead': 'Newcastle, Chester', 'tin': 'Cornwall, Liverpool',
       'hides': 'Bermondsey, Leeds, Bristol tanneries', 'tallow': 'Liverpool, London soapers and candlers',
       'palm oil': 'Liverpool (Port Sunlight, Widnes)', 'linseed': 'Hull crushers',
       'gutta percha': 'Silvertown, Greenwich cable works', 'caoutchouc': 'Silvertown, Manchester',
       'gum': 'London', 'tea': 'London', 'timber': 'London and Liverpool docks'}


def main():
    D = json.load(open(EXPL))
    m = json.load(open(MAP))
    gaz, comms = m['gaz'], m['commodities']

    ALIAS = {'Australia': 'Australasia', 'British India': 'British East Indies', 'Chili': 'Chile',
             'Bengal And Burmah': 'Bengal', 'Philippine And Ladrone Islands': 'Philippine Islands',
             'Western Australia': 'West Australia', 'Cape Of Good Hope': 'British Possessions In South Africa',
             'Natal': 'British Possessions In South Africa',
             'Portugal, Azores, And Madeira': 'Portugal', 'Turkey Proper': 'Turkey', 'Sweden And Norway': 'Sweden',
             'United States Of Colombia (Newgranada': 'United States Of Colombia',
             'West Africa Portuguese Possessions Not Particularly Design Nated': 'Portuguese Possessions In Western Africa',
             'Western Africa (Foreign': 'British West Africa'}
    # keep sub-national detail where it is the geography (Australian colonies,
    # Indian presidencies, US coasts) -- these are the nodes the narrative wants
    KEEP_CHILD = True

    def node_of(label):
        g = gaz.get(label) or {}
        if KEEP_CHILD and g.get('parent') and g.get('kind') in ('colony', 'port'):
            return ALIAS.get(label, label)
        p = g.get('parent') or label
        return ALIAS.get(p, p)

    ENTREPOT = {'Holland', 'Belgium', 'Hong Kong', 'Gibraltar', 'Malta'}
    AGG_OF = {}      # child node -> aggregate node it belongs to
    for lab, g in gaz.items():
        if g.get('parent') and g.get('kind') in ('colony', 'port'):
            AGG_OF[ALIAS.get(lab, lab)] = ALIAS.get(g['parent'], g['parent'])

    def mix(prefixes, arts=None):
        tot = collections.Counter()
        for name, c in comms.items():
            g, _, a = name.partition(' — ')
            if g in prefixes and (arts is None or any(a.startswith(x) for x in arts)):
                for co, by in (c.get('c') or {}).items():
                    for y, cell in by.items():
                        v = cell[0] if isinstance(cell, list) else None
                        if v:
                            tot[node_of(co)] += v
        s = sum(tot.values())
        return [(k, v / s) for k, v in tot.most_common()] if s else []

    def majors(mx):
        out = [(k, s) for k, s in mx if s >= MIN_SHARE and not k.startswith('Other') and k != 'UNTRACED']
        out = out[:MAX_PER]
        # an aggregate ('Australasia', 'British East Indies') alongside its own
        # members says nothing the members do not: drop it
        members = {AGG_OF[k] for k, _ in out if k in AGG_OF and AGG_OF[k] != k}
        return [(k, s) for k, s in out if k not in members]

    edges, nodes = [], {}

    def add_node(name):
        if name in nodes:
            return
        g = gaz.get(name) or {}
        nodes[name] = dict(name=name, lat=g.get('lat'), lon=g.get('lon'), region=region_of(name, gaz),
                           kind='entrepot' if name in ENTREPOT else g.get('kind'))

    ex = {c['name']: c['total'] for c in D['commodities'] if c['flow'] == 'export_uk'}
    rx = {c['name']: c['total'] for c in D['commodities'] if c['flow'] == 'reexport'}
    # forwarded goods
    SUSPECT = {'ZINC AND ZINC ORE', 'IRON AND STEEL'}     # export tables misfiled as re-exports
    for name, tot in sorted(rx.items(), key=lambda kv: -kv[1]):
        if tot < MIN_CANADA or name in SUSPECT:
            continue
        pref = CROSSWALK.get(name)
        if not pref:
            continue
        for rank, (place, s) in enumerate(majors(mix(pref)), 1):
            add_node(place)
            edges.append(dict(commodity=name.title(), family=FAM_OF.get(name, 'other'), route='forwarded',
                              material='', hub='London / Liverpool warehouses', supplier=place,
                              region=nodes[place]['region'], rank=rank,
                              note='re-exported to Canada unchanged; supplier = major consignor to Britain'))
    # British-made goods, by material
    mat_mix = {k: majors(mix(*v)) for k, v in MATERIALS.items()}
    for name, tot in sorted(ex.items(), key=lambda kv: -kv[1]):
        if tot < MIN_CANADA:
            continue
        rule = RULES.get(name, [('DOMESTIC', 1.0)])
        for mat, w in rule:
            if w < 0.2 and mat not in ('DOMESTIC',):
                continue            # a minor ingredient is not a supply line worth drawing
            if mat == 'DOMESTIC':
                add_node('Britain')
                nodes['Britain'].update(lat=53.0, lon=-2.0, region='Britain', kind='home')
                edges.append(dict(commodity=name.title(), family=FAM_OF.get(name, 'other'), route='home',
                                  material='', hub='', supplier='Britain', region='Britain', rank=0,
                                  note='home-grown or mined material, or no traceable input'))
                continue
            if mat == 'UNTRACED':
                continue
            for rank, (place, s) in enumerate(mat_mix.get(mat, []), 1):
                add_node(place)
                edges.append(dict(commodity=name.title(), family=FAM_OF.get(name, 'other'), route='worked',
                                  material=mat, hub=HUB.get(mat, ''), supplier=place,
                                  region=nodes[place]['region'], rank=rank,
                                  note=f'{mat} worked up in Britain; supplier = major consignor of {mat} to Britain'))
    add_node('Canada')
    nodes['Canada'].update(lat=45.5, lon=-73.6, region='North America', kind='destination')
    with open('reports/canada_supply_network_edges.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(edges[0].keys()))
        w.writeheader()
        w.writerows(edges)
    json.dump(dict(nodes=list(nodes.values()), edges=edges,
                   families=list(FAMILY.keys()), hubs=HUB,
                   method=('suppliers = consignors with >= 5% of the UK whole-period import mix for the '
                           'commodity (forwarded) or its raw material (worked), up to 6, ranked; no values')),
              open('reports/canada_supply_network.json', 'w'), indent=1)
    by_route = collections.Counter(e['route'] for e in edges)
    print(f'{len(nodes)} nodes, {len(edges)} edges', dict(by_route))
    # a readable digest: material -> suppliers, commodity -> suppliers
    seen = set()
    for mat, mx in mat_mix.items():
        if mx:
            print(f'  {mat:13} <- ' + ', '.join(k for k, s in mx))
    print('  forwarded:')
    for e in edges:
        if e['route'] == 'forwarded' and e['commodity'] not in seen:
            seen.add(e['commodity'])
            print(f'  {e["commodity"]:34} <- ' + ', '.join(x['supplier'] for x in edges if x['route'] == 'forwarded' and x['commodity'] == e['commodity']))


if __name__ == '__main__':
    main()
