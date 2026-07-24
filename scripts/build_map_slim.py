#!/usr/bin/env python3
"""Slim, self-contained dataset for the public trade-origins map artifact.
Reads the curated map_data.json (cells [year,qty,rank,value]) + the whitelist
(KEEP bucket + adjudicated fold/rename targets) + the gazetteer, and emits a
compact per-commodity structure: mapped-origin series (value + dominant-unit
quantity), an unmapped residual, and the national total per year.
"""
import json, csv, collections
from pathlib import Path

CAP = 50_000_000          # per-cell value plausibility cap (matches payload sort cap)
m = json.load(open('exports/map_data.json'))
gaz = json.load(open('reference/map_gazetteer.json'))
rows = list(csv.DictReader(open('reports/commodity_curation_queue.csv')))
keep = {r['commodity'] for r in rows if r['bucket'] == 'KEEP'}
cur = list(csv.DictReader(open('reference/commodity_curation.csv')))
targets = {r['target'] for r in cur if r['action'] in ('fold', 'rename') and r['target']}
wl = sorted((keep | targets) & set(m), key=lambda n: -m[n]['v'])

# commodity category (ordered keyword rules, first match wins) — a browsing
# aid for the picker, not a scientific taxonomy.
# Several keywords need explicit word boundaries: as bare substrings they
# matched inside unrelated words and mis-filed the commodity in the picker —
# 'rug' put every Drugs line under Textiles, 'fur' put Furniture under Animal
# products, 'ale' put Whale Fisheries under Food, 'rum' put Musical
# Instruments there too, and 'oat' would catch Coatings. Plural-only matches
# ('wool' in 'woollen', 'skin' in 'skins') are left alone: those are correct.
CAT_RULES = [
 ('Textiles, fibres & apparel', r'cotton|wool|worsted|silk|flax|linseed|jute|hemp|yarn|cloth|linen|muslin|manufactures of|piece goods|lace|carpet|hosiery|alpaca|mohair|vicu|thread|twist|apparel|haberdash|blanket|flannel|duffel|ribbon|velvet|tissue|embroider|felt|boot|shoe|hat|bonnet|glove|straw plat|coating|drawers|shawl|\brugs?\b'),
 ('Food, drink & tobacco', r'sugar|molasses|treacle|glucose|tea\b|coffee|cocoa|chocolate|wine|spirit|brandy|geneva|\brum\b|beer|\bales?\b|liqueur|corn|grain|wheat|maize|barley|\boats?\b|rye|rice|flour|meal|bread|biscuit|fruit|raisin|currant|orange|lemon|apple|prune|fig|nut|almond|meat|beef|pork|bacon|ham|mutton|fish|herring|salmon|oyster|butter|cheese|milk|egg|lard|tallow|stearine|margarine|spice|pepper|ginger|cinnamon|tobacco|cigar|snuff|salt|vinegar|sauce|honey|hops|potato|onion|vegetable|succade|confection|provision|yeast|chicory|sago|tapioca|arrowroot|coco.?nut|cured|preserved|pickle|seed'),
 ('Animals & animal products', r'animal|cattle|ox\b|oxen|sheep|lamb|swine|horse|cow|bull|hide|skin|\bfurs?\b|pelt|leather|horn|hoof|bone|bristle|feather|ivory|hair|isinglass|glue|gut|sponge|shell|coral|pearl'),
 ('Chemicals, dyes & oils', r'chemical|acid|alkali|soda|potash|saltpetre|nitre|nitrate|ammonia|sulphur|dye|madder|indigo|logwood|cochineal|cutch|gambier|tanning|bark|drug|medicin|oil\b|petroleum|paraffin|naphtha|resin|rosin|gum|varnish|paint|colour|manure|guano|phosphate|soap|candle|collodi|caoutchouc|rubber|gutta|wax|bleaching|regulus|precipitate'),
 ('Metals & ores', r'iron|steel|copper|lead|tin\b|zinc|brass|bronze|gold\b|silver\b|platina|mercury|quicksilver|ore\b|metal|nickel|antimony|ingot|pig and|hardware|cutlery|nail|wire|anchor|chain|anvil'),
 ('Wood, forest & paper', r'wood|timber|deal|batten|stave|log\b|mahogany|oak|fir|teak|pine|cork|rattan|cane\b|osier|bamboo|paper|pulp|millboard|book|stationer|card'),
 ('Minerals, stone & glass', r'coal|coke|culm|cinder|stone|marble|slate|granite|clay|earthenware|china|porcelain|glass|cement|lime\b|chalk|flint|sand|gravel|asphalt|mineral|diamond'),
 ('Machinery & manufactures', r'machin|engine|locomot|apparatus|instrument|clock|watch|arms|ammunition|gun|rifle|carriage|vehicle|ship|furniture|toy|brush|jewel|fancy|musical'),
]
_catre = [(c, __import__('re').compile(p)) for c, p in CAT_RULES]
def classify(n):
    l = n.lower()
    for cat, rx in _catre:
        if rx.search(l):
            return cat
    return 'Other & miscellaneous'

located = {k for k, v in gaz.items() if v['lat'] is not None}
# parent -> {children} for parent<->child origin de-duplication, built from
# BOTH directions: child->parent pointers AND the umbrella 'children' lists
# (umbrellas like 'Australia' / 'Sweden And Norway' / 'British West India
# Islands' list children that don't carry a reciprocal parent pointer).
children_of = collections.defaultdict(set)
for k, v in gaz.items():
    if v.get('parent'):
        children_of[v['parent']].add(k)
    for ch in v.get('children', ()):
        children_of[k].add(ch)
# label-variant duplicates AND OCR/era variants of a mapped place: the same
# origin printed several ways would be summed as separate residual, never a
# bubble. Canonicalise each to one gazetteer key so it lands on the map.
ALIAS = {
    'Chili': 'Chile', 'Portugal, Azores, And Madeira': 'Portugal',
    'Madeira': 'Portugal', 'Azores': 'Portugal',
    # Ottoman variants -> Turkey
    'Turkey European': 'Turkey', 'Turkey, European': 'Turkey',
    'Turkey Asiatic': 'Turkey', 'Turkey, Asiatic': 'Turkey',
    'Wallachia And Moldavia': 'Roumania',
    # Colombia (many historic names)
    'Republic Of Colombia': 'United States Of Colombia',
    'New Granada': 'United States Of Colombia',
    'United States Of Colombia (New Granada': 'United States Of Colombia',
    'United States Of Colombia (Newgranada': 'United States Of Colombia',
    # India presidencies / OCR-glued lists -> Bombay or the India umbrella
    'Bombay And Seinde': 'Bombay', 'Bombay And Scinde': 'Bombay',
    'Bombay And Soinde': 'Bombay',
    'Bombay And Scindemadras': 'British East Indies',
    'Bombay And Scinde Bengal And Burmah': 'British East Indies',
    'Bombay And Scindebengal And Burmah': 'British East Indies',
    'Other British East Indian Possessions': 'British East Indies',
    'Native States': 'British East Indies',
    # Australia / South Africa / Mauritius variants
    'West Australia': 'Western Australia',
    'South Africa': 'British Possessions In South Africa',
    'British Possessions In Southafrica': 'British Possessions In South Africa',
    'British Possessions In South Africamauritius': 'British Possessions In South Africa',
    'Mauritius And Dependencies': 'Mauritius',
    'Australasia New Zealand': 'New Zealand',
    # Spain + islands, West Indies + Guiana, Aden, Guiana
    'Spain And Canaries': 'Spain', 'Spain And Canary Islands': 'Spain',
    'British West India Islands And British Guiana': 'British West India Islands',
    'British West India Islands And Britishguiana': 'British West India Islands',
    'British West India Islands And British': 'British West India Islands',
    'British West Indies And Guiana': 'British West India Islands',
    'Aden And Dependencies': 'Aden',
    'Guiana': 'British Guiana',
    'Hayti And St. Domingo': 'Hayti And St Domingo',
    # ---- third-wave residual audit: variants of the regional groupings ----
    # West Africa, British and foreign, is printed a dozen ways
    'Western Africa (British': 'British West Africa',
    'West Africa Settlements': 'British West Africa',
    'Western Africa British Settlements': 'British West Africa',
    'British Possessions On The Gold Coast': 'British West Africa',
    'British Possessions In Western Africa': 'British West Africa',
    'West Coast Of Africa Not Particularly Designated': 'Western Africa (Foreign',
    'West Coast Of Africa Foreign': 'Western Africa (Foreign',
    'West Africa (Foreign': 'Western Africa (Foreign',
    'West Africa Foreign': 'Western Africa (Foreign',
    'West Coast Of Africa (Foreign)': 'Western Africa (Foreign',
    'West Coast Of Africa': 'Western Africa (Foreign',
    'Portuguese Possessions': 'Portuguese Possessions In Western Africa',
    'West Africa Portuguese Possessions Not Particularly Design Nated':
        'Portuguese Possessions In Western Africa',
    'East Coast Of Africa Native States': 'East Coast Of Africa',
    'Eastern Coast Of Africa': 'East Coast Of Africa',
    'Eastern Africa': 'East Coast Of Africa',
    # spelling / comma variants of places already on the map
    'United States Of Columbia': 'United States Of Colombia',
    'Portugal Azores And Madeira': 'Portugal',
    'British India And Burmah': 'British India',
    'British East Indies Bengal': 'Bengal',
    'The Cape Of Good Hope': 'Cape Of Good Hope',
}
outliers = []            # origin cells that exceed the national anchor (log)
value_dropped = []       # per-cell values over CAP (corrupt, not large)
quality = []             # (commodity, [flag,...]) for the audit report
unit_alias = []          # origin/anchor unit labels that measure the same thing
unit_mismatch = []       # ...and those that do not, so the anchor is dropped
cov_num = cov_den = 0
out = {}
for n in wl:
    e = m[n]
    # dominant unit across country cells (for the quantity display)
    ucnt = collections.Counter()
    for c, byu in e['c'].items():
        if c == '§TOTAL':
            continue
        for u, s in byu.items():
            if u != '?':
                ucnt[u] += len(s)
    dom = ucnt.most_common(1)[0][0] if ucnt else '?'
    # ---- Tier-1 anchor quantity per year (authoritative national total) ----
    # The anchor must be ONE unit. The old code summed every §TOTAL unit
    # whenever the origins carried no unit, which added a value series to a
    # tonnage ('Nuts And Kernels' has both), and fell back to summing them all
    # whenever the origin unit was absent from §TOTAL, which produced an
    # anchor in Tons for origins measured in Cwts.
    t1_by_u = collections.defaultdict(dict)
    for u, ser in e['c'].get('§TOTAL', {}).items():
        if u == 'Value':          # a value line is not a quantity anchor
            continue
        for cell in ser:
            t1_by_u[u][cell[0]] = t1_by_u[u].get(cell[0], 0) + cell[1]
    unit_note = None
    if dom != '?' and dom in t1_by_u:
        t1 = t1_by_u[dom]
    elif dom == '?' and t1_by_u:
        # Origins lost their unit but the national line may have kept one, so
        # adopt it: that both anchors the series and labels the quantity axis.
        # Prefer a LABELLED §TOTAL unit even when the unlabelled one has more
        # years - matching '?' to '?' is what let "Wool — Other Goats' Wool Or
        # Hair" anchor its 1896-99 unlabelled series and ignore the Lb series
        # covering 1893-95, giving a 4.95x ratio out of two different regimes.
        dom = max(t1_by_u, key=lambda u: (u != '?', len(t1_by_u[u])))
        t1 = t1_by_u[dom]
        unit_note = (None if dom == '?' else
                     'the origins carry no printed unit; the unit shown is '
                     'the one on the national total')
    elif t1_by_u:
        # origins and anchor are labelled with DIFFERENT units. Decide by the
        # numbers, not by the labels: 'Oil — Olive' origins in "Tun" against a
        # "Ton" anchor come out at ratio 1.00, so those are one unit OCR'd two
        # ways, while a genuine Ton/Cwt regime difference lands near 20. Only
        # an exact-definition factor is applied; anything else means the two
        # series are not comparable and the anchor is dropped rather than
        # silently mis-scaling the map's national total.
        au = max(t1_by_u, key=lambda u: len(t1_by_u[u]))
        osum = collections.defaultdict(float)
        for c2, byu2 in e['c'].items():
            if c2 == '§TOTAL':
                continue
            for u2, ser2 in byu2.items():
                for cell in ser2:
                    osum[cell[0]] += cell[1]
        rr = sorted(osum[y] / t1_by_u[au][y] for y in t1_by_u[au]
                    if t1_by_u[au].get(y) and osum.get(y))
        med = rr[len(rr) // 2] if rr else 0
        FACT = {20: 'Cwt per Ton', 112: 'Lb per Cwt', 12: 'per dozen'}
        if 0.95 <= med <= 1.05:
            t1 = t1_by_u[au]
            unit_note = (f'the national total is labelled "{au}" and the '
                         f'origins "{dom}", but the figures are the same '
                         f'series - one label is an OCR error')
            unit_alias.append((n, dom, au, round(med, 3)))
        elif any(0.95 <= med / f <= 1.05 for f in FACT):
            f = next(f for f in FACT if 0.95 <= med / f <= 1.05)
            t1 = {y: q * f for y, q in t1_by_u[au].items()}
            unit_note = f'national total converted from {au} ({FACT[f]})'
        else:
            t1 = {}
            unit_note = (f'the national total is printed in "{au}" while the '
                         f'origins are in "{dom}" - not comparable, so no '
                         f'anchor is used')
            unit_mismatch.append((n, dom, au, round(med, 2)))
    else:
        t1 = {}
    # ---- aggregate to (label, year) -> [value, qty(dom unit), bestRank] ----
    # label-variant duplicates are canonicalised (Chili -> Chile) so the same
    # place is never summed under two spellings.
    ly = {}
    for c, byu in e['c'].items():
        if c == '§TOTAL':
            continue
        c = ALIAS.get(c, c)
        for u, s in byu.items():
            for y, q, r, v in s:
                cell = ly.setdefault((c, y), [0, 0, r])
                # A value over the cap is a corrupt cell (a whole column read
                # as one number), not a large one. Clamping it to the cap
                # FABRICATES a GBP50M figure and, repeated across a table,
                # floats the commodity to the top of the value ranking - three
                # woollen export tables reached GBP0.75-1.0bn that way. Drop
                # the cell and log it instead; the quantity side is unaffected
                # because it is anchored separately.
                if v > CAP:
                    value_dropped.append((n, c, y, v))
                    v = 0
                cell[0] += v
                if u == dom:
                    cell[1] += q
                cell[2] = min(cell[2], r)
    # ---- parent<->child de-duplication (the coast/subtotal double-count) ----
    # A printed origin table often carries BOTH a parent total ('United States
    # Of America') AND its breakdown ('United States (Atlantic/Pacific)', or
    # 'Bombay/Madras/Bengal' under 'British East Indies'). Summing both double-
    # counts (raw cotton read ~1.8x its Tier-1 anchor). Per year, when a parent
    # and >=1 child both appear, keep the GRANULAR children and drop the parent
    # when they account for it (>=85% of parent value); if the parent is much
    # larger (extra un-itemised sub-regions), keep the parent and drop the
    # partial children instead. Either way the label-year is counted once.
    drop = set()
    years = {y for (_c, y) in ly}
    for y in years:
        present = {c for (c, yy) in ly if yy == y}
        for pa in present:
            kids = [k for k in children_of.get(pa, ()) if k in present]
            if not kids:
                continue
            pv = ly[(pa, y)][0] or 1
            kv = sum(ly[(k, y)][0] for k in kids)
            if kv >= 0.85 * pv:
                drop.add((pa, y))                 # children cover parent
            else:
                for k in kids:
                    drop.add((k, y))              # parent is the fuller total
    # ---- impossible-origin filter: one origin cannot exceed the whole
    # national total. A cell whose quantity tops the Tier-1 anchor (x1.15
    # tolerance for anchor noise) is corrupt — country-column glue from another
    # commodity or a magnitude error (Burma 2.79M cwt "potatoes"; Russia 3.5M
    # ton "logwood"; Greece 1.3M gal "collodion"). Drop it and log for a
    # source-level fix. Only applied where the anchor is itself substantial.
    for (c, y), cell in list(ly.items()):
        t = t1.get(y, 0)
        if t > 1000 and cell[1] > t * 1.15:
            outliers.append({'commodity': n, 'year': y, 'origin': c,
                             'unit': dom, 'qty': round(cell[1]),
                             'anchor': round(t),
                             'x_anchor': round(cell[1] / t, 1)})
            drop.add((c, y))
    # ---- build per-origin / residual / national total from de-duped cells --
    per = {}
    res = collections.defaultdict(lambda: [0, 0])
    nat = collections.defaultdict(lambda: [0, 0])       # de-duped sum of origins
    for (c, y), (v, q, r) in ly.items():
        if (c, y) in drop:
            continue
        nat[y][0] += v
        nat[y][1] += q
        if c in located:
            per.setdefault(c, {})[y] = [v, q, r]
            cov_num += v
        else:
            res[y][0] += v
            res[y][1] += q
        cov_den += v
    if not per and not res:
        continue
    # slider range = years that actually have ORIGIN data (bubbles/residual),
    # NOT the wider Tier-1 anchor span (1866-1900): otherwise the slider lands
    # on years with a national total but no origin breakdown -> empty map.
    yrs = sorted(nat)
    # ---- per-commodity quality flags, shown on the map itself ------------
    # A reader cannot tell a well-measured series from a one-year fragment of
    # a mislabelled table by looking at bubbles, so the limits travel with the
    # data instead of living in a caveats paragraph nobody opens.
    fl = []
    if not per:
        fl.append('noorig')          # nothing the gazetteer can place: blank map
    if not sum(v for v, _q in nat.values()):
        fl.append('noval')           # value toggle would show an empty map
    if dom == '?':
        fl.append('nounit')          # quantity axis unlabelled; units may be mixed
    if len(yrs) == 1:
        fl.append('oneyear')         # slider/sparkline imply a series of one point
    if not t1:
        fl.append('noanchor')        # no national total to check the origins against
    else:
        rr = sorted(nat[y][1] / t1[y] for y in yrs if t1.get(y) and nat[y][1])
        if rr:
            med = rr[len(rr) // 2]
            if med > 1.15:
                fl.append('overanchor')   # origins still double-count
            elif med < 0.5:
                fl.append('underanchor')  # map shows a slice as if it were the whole
    rv = sum(a for a, _b in res.values())
    tv = sum(v for v, _q in nat.values())
    if tv and rv / tv > 0.6:
        fl.append('resid')           # most of the trade is in unplaceable origins
    quality.append((n, fl))
    out[n] = {
        'u': dom,
        **({'un': unit_note} if unit_note else {}),
        'v': round(e['v']),
        'cat': classify(n),
        'q': fl,
        'y': [yrs[0], yrs[-1]] if yrs else [0, 0],
        'c': {c: {str(y): [round(vv[0]), round(vv[1]), vv[2]]
                  for y, vv in d.items()}
              for c, d in per.items()},
        'res': {str(y): [round(a), round(b)] for y, (a, b) in res.items()
                if a or b},
        'nat': {str(y): [round(a), round(b)] for y, (a, b) in nat.items()},
        't1': {str(y): round(q) for y, q in t1.items() if q},
    }

payload = {
    'meta': {
        'source': 'UK Annual Statement of Trade, imports 1872-1899',
        'measure_note': 'Origins are the country/port whence goods were '
                        'CONSIGNED (shipped) to the UK, NOT the place of '
                        'production. Entrepots (Holland, Belgium, Gibraltar, '
                        'Hong Kong) therefore overstate as "origins".',
        'quantity_note': 'National totals are the Tier-1 anchor. Origin cells '
                         'are de-duplicated: where a parent line and its '
                         'breakdown (e.g. United States + its Atlantic/Pacific '
                         'coasts) both appear, only the finer level is counted, '
                         'so origins no longer double-count against the anchor. '
                         'Per-origin values remain provisional.',
        'n_commodities': len(out),
        'flag_note': {
            'noorig': 'no origin the gazetteer can place — the map stays blank',
            'noval': 'no value figures — only the quantity measure works',
            'nounit': 'the printed unit was not captured, so quantities may '
                      'mix units and the axis is unlabelled',
            'oneyear': 'origins for a single year only',
            'noanchor': 'no national total published for this line, so the '
                        'origins cannot be checked against one',
            'overanchor': 'origins add up to more than the national total — '
                          'residual double-counting',
            'underanchor': 'origins add up to less than half the national '
                           'total — the map shows part of the trade',
            'resid': 'most of the trade is consigned from origins the '
                     'gazetteer cannot place',
        },
    },
    'gaz': gaz,
    'commodities': out,
}
Path('exports/map_slim.json').write_text(
    json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
sz = Path('exports/map_slim.json').stat().st_size
# log the impossible-origin cells for source-level follow-up
outliers.sort(key=lambda r: -r['x_anchor'])
with open('reports/origin_outliers.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['commodity', 'year', 'origin', 'unit',
                                      'qty', 'anchor', 'x_anchor'])
    w.writeheader()
    w.writerows(outliers)
print(f'commodities embedded: {len(out)}  gaz located: {len(located)}')
print(f'mapped-origin value coverage: {100*cov_num/(cov_den or 1):.1f}% of located+residual value')
with open('reports/value_cap_cells.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['commodity', 'origin', 'year', 'value'])
    w.writerows(sorted(value_dropped, key=lambda r: -r[3]))
print(f'impossible-origin cells dropped: {len(outliers)} -> reports/origin_outliers.csv')
with open('reports/map_quality.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['commodity', 'gbp', 'flags'])
    w.writerows(sorted(((n, out[n]['v'], ' '.join(fl)) for n, fl in quality),
                       key=lambda r: (-len(r[2].split()) if r[2] else 0, -r[1])))
clean = sum(1 for _n, fl in quality if not fl)
print(f'quality: {clean}/{len(quality)} unflagged -> reports/map_quality.csv')
with open('reports/unit_reconciliation.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['commodity', 'origin_unit', 'anchor_unit', 'ratio', 'verdict'])
    w.writerows([r + ('same unit, OCR variant',) for r in unit_alias]
                + [r + ('not comparable, anchor dropped',) for r in unit_mismatch])
print(f'unit labels reconciled: {len(unit_alias)} same-unit, '
      f'{len(unit_mismatch)} incomparable -> reports/unit_reconciliation.csv')
print(f'over-cap value cells dropped: {len(value_dropped)} '
      f'({len({r[0] for r in value_dropped})} commodities) -> reports/value_cap_cells.csv')
print(f'map_slim.json: {sz/1e6:.2f} MB')
