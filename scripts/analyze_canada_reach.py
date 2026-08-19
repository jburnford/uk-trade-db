#!/usr/bin/env python3
"""Preliminary analysis: the global reach of Canadian consumption seen
through what the United Kingdom sent it, 1870-1900.

Two lenses, both from the UK Annual Statement of Trade:

  export_uk  British and Irish PRODUCE shipped to Canada -- made in Britain
  reexport   colonial and foreign goods landed in Britain and shipped on to
             Canada -- Britain as entrepot

The re-export tables record the DESTINATION only; the Statement never says
where the tea Canada bought through London had been grown. But the same
volumes' IMPORT tables record where Britain got each commodity that year. So
Canada's via-UK re-export of a commodity in a year is distributed over the
UK's import origins for that commodity-year -- an ESTIMATE of provenance
under the assumption that what was re-shipped to Canada drew on the same
sources as Britain's imports of that commodity as a whole. Origins are
consignment points (the map product's own caveat): Holland/Belgium/Hong Kong
overstate as "origins".

Inputs
  reports/canada_explorer.json      Canada value by commodity-year, both flows
                                    (own-year witnesses, all repairs applied)
  exports/map_slim.json             UK import origins per 'Group -- Article',
                                    per country, per year [value, qty, rank]

Outputs
  reports/canada_reach.json                 everything the report needs
  reports/canada_reach_origins.csv          year x region (re-export value)
  reports/canada_reach_commodities.csv      re-export commodity x top origins

Usage: python3 scripts/analyze_canada_reach.py
"""
import collections, csv, json, re

EXPL = 'reports/canada_explorer.json'
MAP = 'exports/map_slim.json'

# explorer re-export commodity name -> import-side group prefixes in map_slim
CROSSWALK = {
    'TEA': ['Tea'], 'FRUIT': ['Fruit', 'Fruit (Not Liable To Duty)'],
    'SILK MANUFACTURES': ['Silk Manufactures'],
    'SKINS, FURS AND PELTS': ['Skins, Furs, And Pelts', 'Skins', 'Skins And Furs'],
    'HEMP': ['Hemp', 'Hemp, Dressed Or Undressed'], 'WOOL': ['Wool'],
    'WOOLLEN MANUFACTURES': ['Woollen And Worsted Manufactures', 'Woollen Manufactures'],
    'RICE': ['Rice'], 'ZINC AND ZINC ORE': ['Zinc', 'Zinc Or Spelter'],
    'SPICES': ['Spices'], 'WINE': ['Wine'], 'IRON AND STEEL': ['Iron', 'Iron And Steel'],
    'SILK, RAW AND THROWN': ['Silk'], 'TALLOW and STEARINE': ['Tallow And Stearine'],
    'SPIRITS': ['Spirits'], 'HAMS': ['Hams', 'Bacon And Hams'], 'COFFEE': ['Coffee'],
    'WOOLLEN YARN': ['Woollen Yarn', 'Woollen And Worsted Yarn'],
    'EMBROIDERY AND NEEDLEWORK': ['Embroidery And Needlework'],
    'FISH': ['Fish', 'Fish (Including Turtle)', 'Fish, Fresh And Cured'],
    'SUGAR': ['Sugar'], 'COTTON, RAW': ['Cotton'],
    'GOODS UNENUMERATED': ['Goods, Unenumerated, Unmanufactured'],
    'LACE, and Articles thereof': ['Lace, And Articles Thereof', 'Lace'],
    'CHEMICAL MANUFACTURES AND PRODUCTS': ['Chemical Manufactures And Products, Unenumerated'],
    'HATS OR BONNETS': ['Hats Or Bonnets'], 'DRUGS': ['Drugs'],
    'LEATHER AND LEATHER MANUFACTURES': ['Leather Manufactures', 'Leather', 'Leather, Undressed'],
    'FARINACEOUS SUBSTANCES': ['Farinaceous Substances And Manufactures Thereof', 'Farinaceous Substances'],
    'HIDES, RAW': ['Hides, Not Tanned, Tawed, Curried, Or In Any Way Dressed', 'Hides, Raw, And Pieces Thereof', 'Hides'],
    'LIQUORICE': ['Liquorice'], 'OIL': ['Oil'],
    "PAINTERS' Colours and Pigments, Unenumerated": ["Painters' Colours And Pigments", "Painters' Colours And Materials"],
    'TOBACCO': ['Tobacco', 'Tobacco And Snuff'], 'GLASS': ['Glass'],
    'FLAX': ['Flax, Dressed Or Undressed', 'Flax'],
    'DYE STUFFS AND DYE WOODS': ['Dye Stuffs, And Substances Used In Tanning', 'Dye Stuffs'],
    'TIN': ['Tin', 'Tin Ore And Regulus'], 'BRISTLES': ['Bristles'],
    'FEATHERS AND DOWN': ['Feathers And Down', 'Feathers'], 'CAOUTCHOU': ['Caoutchouc'],
    'FLOWERS, Artificial': ['Flowers, Artificial'], 'COPPER, Ore of': ['Copper', 'Copper, Ore Of'],
    'COCOA': ['Cocoa'], 'SALTPETRE': ['Saltpetre', 'Saltpetre (Nitrate Of Potash)'],
    'CORK': ['Cork'], 'SEEDS': ['Seeds'], 'GUANO': ['Guano'], 'GUTTA PERCHA': ['Gutta Percha'],
    'JUTE': ['Jute'], 'INDIGO': ['Indigo'], 'OPIUM': ['Opium'], 'BARK': ['Bark'],
    'CLOCKS AND WATCHES': ['Clocks', 'Watches'], 'PAPER': ['Paper'],
    'TOYS': ['Toys'], 'MUSICAL INSTRUMENTS': ['Musical Instruments'],
    'CANDLES': ['Candles'], 'CHEESE': ['Cheese'], 'BUTTER': ['Butter'],
    'EGGS': ['Eggs'], 'MEAT': ['Meat'], 'BACON': ['Bacon'], 'LARD': ['Lard'],
    'CORN, GRAIN, MEAL AND FLOUR': ['Corn And Grain', 'Corn, Grain, Meal, And Flour', 'Corn'],
    'MOLASSES': ['Molasses'], 'HOPS': ['Hops'], 'ONIONS': ['Onions'],
    'CAOUTCHOUC': ['Caoutchouc'], 'FURNITURE AND HARDWOODS': ['Wood And Timber'],
    'WOOD AND TIMBER': ['Wood And Timber'], 'GUM': ['Gum'], 'IVORY': ['Ivory'],
    'QUICKSILVER': ['Quicksilver'], 'MANURES': ['Manures', 'Guano'],
    'LINEN MANUFACTURES': ['Linen Manufactures'], 'COTTON MANUFACTURES': ['Cotton Manufactures'],
    'GLOVES': ['Gloves'], 'ARMS AND AMMUNITION': ['Ammunition', 'Arms'],
    'SILK': ['Silk'],
}

# consignment label -> world region. Rules by the gazetteer's coordinates,
# with the overrides that geography gets wrong (Malta/Gibraltar/Cyprus are
# European ports of the Mediterranean trade; Bermuda is Atlantic; Persia is
# West Asia). 'Other' catches the Statement's residual lines.
def region_of(label, gaz):
    OVR = {'Malta': 'Mediterranean & Levant', 'Gibraltar': 'Mediterranean & Levant',
           'Cyprus': 'Mediterranean & Levant', 'Turkey': 'Mediterranean & Levant',
           'Turkey Proper': 'Mediterranean & Levant', 'Egypt': 'Mediterranean & Levant',
           'Greece': 'Mediterranean & Levant', 'Persia': 'Mediterranean & Levant',
           'Morocco': 'Mediterranean & Levant', 'Algeria': 'Mediterranean & Levant',
           'Tunis': 'Mediterranean & Levant', 'Tripoli': 'Mediterranean & Levant',
           'Tripoli And Tunis': 'Mediterranean & Levant', 'Canary Islands': 'Europe',
           'Bermudas': 'North America', 'Newfoundland': 'North America',
           'Canada': 'North America', 'Mexico': 'Caribbean & Central America',
           'Islands In The Pacific': 'Australasia & Pacific',
           'Falkland Islands': 'South America', 'Mauritius': 'Africa',
           'Madagascar': 'Africa', 'Zanzibar And Pemba': 'Africa',
           'East Coast Of Africa': 'Africa'}
    if label in OVR:
        return OVR[label]
    g = gaz.get(label)
    if not g or g.get('lat') is None:
        return 'Other / unplaced'
    lat, lon = g['lat'], g['lon']
    if lon > 100 and lat < -8:
        return 'Australasia & Pacific'
    if lon > 100 and lat >= 15:
        return 'China & Japan'
    if 60 <= lon <= 130:
        return 'India & Southeast Asia'
    if -30 <= lon <= 45 and lat >= 35:
        return 'Europe'
    if -20 <= lon <= 55 and lat < 35:
        return 'Africa'
    if lon < -30 and lat >= 24:
        return 'North America'
    if lon < -30 and 7 <= lat < 24:
        return 'Caribbean & Central America'
    if lon < -30:
        return 'South America'
    return 'Other / unplaced'


def main():
    D = json.load(open(EXPL))
    years = D['years']
    m = json.load(open(MAP))
    gaz, comms = m['gaz'], m['commodities']

    # import origins per group prefix per year: {group: {year: {country: value}}}
    origins = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for name, c in comms.items():
        g = name.split(' — ')[0]
        for country, byyear in (c.get('c') or {}).items():
            for y, cell in byyear.items():
                v = cell[0] if isinstance(cell, list) else None
                if v:
                    origins[g][int(y)][country] += v

    def origin_shares(prefixes, year, span=2):
        """value shares by country for the given import groups, using the
        nearest year(s) with data within +-span"""
        for d in range(0, span + 1):
            for y in {year - d, year + d}:
                tot = collections.Counter()
                for p in prefixes:
                    tot.update(origins.get(p, {}).get(y, {}))
                s = sum(tot.values())
                if s > 0:
                    return {k: v / s for k, v in tot.items()}, y
        return None, None

    ex = [c for c in D['commodities'] if c['flow'] == 'export_uk']
    rx = [c for c in D['commodities'] if c['flow'] == 'reexport']
    tot_ex = [sum((c['v'][i] or 0) for c in ex) for i in range(len(years))]
    tot_rx = [sum((c['v'][i] or 0) for c in rx) for i in range(len(years))]

    region_year = collections.defaultdict(lambda: collections.Counter())
    country_all = collections.Counter()
    comm_rows, unmapped = [], collections.Counter()
    comm_region = collections.defaultdict(collections.Counter)
    for c in sorted(rx, key=lambda c: -c['total']):
        pref = CROSSWALK.get(c['name'])
        top_countries = collections.Counter()
        mapped_v = 0
        for i, y in enumerate(years):
            v = c['v'][i] or 0
            if not v:
                continue
            sh, ysrc = origin_shares(pref, y) if pref else (None, None)
            if not sh:
                unmapped[c['name']] += v
                region_year[y]['Unmapped'] += v
                comm_region[c['name']]['Unmapped'] += v
                continue
            mapped_v += v
            for country, s in sh.items():
                reg = region_of(country, gaz)
                region_year[y][reg] += v * s
                country_all[country] += v * s
                top_countries[country] += v * s
                comm_region[c['name']][reg] += v * s
        comm_rows.append(dict(commodity=c['name'], total=c['total'], mapped=round(mapped_v),
                              years=c['years'],
                              top_origins=[(k, round(v)) for k, v in top_countries.most_common(6)],
                              regions={k: round(v) for k, v in comm_region[c['name']].most_common()}))

    regions = sorted({r for y in region_year for r in region_year[y]},
                     key=lambda r: -sum(region_year[y][r] for y in region_year))
    out = dict(
        years=years, total_export_uk=tot_ex, total_reexport=tot_rx,
        regions=regions,
        region_year={str(y): {r: round(v) for r, v in region_year[y].items()} for y in years},
        region_total={r: round(sum(region_year[y][r] for y in years)) for r in regions},
        top_origin_countries=[(k, round(v)) for k, v in country_all.most_common(25)],
        reexport_commodities=comm_rows,
        export_uk_top=[dict(commodity=c['name'], total=c['total'], years=c['years'],
                            v=c['v']) for c in sorted(ex, key=lambda c: -c['total'])[:30]],
        reexport_top=[dict(commodity=c['name'], total=c['total'], v=c['v'])
                      for c in sorted(rx, key=lambda c: -c['total'])[:15]],
        unmapped={k: round(v) for k, v in unmapped.most_common()},
        bad_years=D['bad_years'],
        method=('re-export value x UK import-origin value shares of the same '
                'commodity-year (nearest year within 2 if the year is missing); '
                'origins are consignment points'),
    )
    json.dump(out, open('reports/canada_reach.json', 'w'), indent=1)
    with open('reports/canada_reach_origins.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['year', 'region', 'reexport_value_est'])
        for y in years:
            for r in regions:
                w.writerow([y, r, round(region_year[y][r])])
    with open('reports/canada_reach_commodities.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['commodity', 'total', 'mapped', 'top_origins', 'regions'])
        for r in comm_rows:
            w.writerow([r['commodity'], r['total'], r['mapped'],
                        '; '.join(f'{k} {v}' for k, v in r['top_origins']),
                        '; '.join(f'{k} {v}' for k, v in r['regions'].items())])
    T = sum(tot_rx)
    print(f'export_uk total GBP{sum(tot_ex):,.0f}  reexport total GBP{T:,.0f} '
          f'({100*T/(T+sum(tot_ex)):.1f}% of the two)')
    print('re-export by origin region (all years):')
    for r in regions:
        print(f'  {r:30} {out["region_total"][r]:>12,}  {100*out["region_total"][r]/T:5.1f}%')
    print('unmapped:', sum(unmapped.values()), list(unmapped.items())[:8])
    print('top origin countries:', out['top_origin_countries'][:12])


if __name__ == '__main__':
    main()
