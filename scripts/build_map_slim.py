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
# aid for the picker, not a scientific taxonomy
CAT_RULES = [
 ('Textiles, fibres & apparel', r'cotton|wool|worsted|silk|flax|linseed|jute|hemp|yarn|cloth|linen|muslin|manufactures of|piece goods|lace|carpet|hosiery|alpaca|mohair|vicu|thread|twist|apparel|haberdash|blanket|flannel|duffel|ribbon|velvet|tissue|embroider|felt|boot|shoe|hat|bonnet|glove|straw plat|coating|drawers|shawl|rug'),
 ('Food, drink & tobacco', r'sugar|molasses|treacle|glucose|tea\b|coffee|cocoa|chocolate|wine|spirit|brandy|geneva|rum|beer|ale|liqueur|corn|grain|wheat|maize|barley|oat|rye|rice|flour|meal|bread|biscuit|fruit|raisin|currant|orange|lemon|apple|prune|fig|nut|almond|meat|beef|pork|bacon|ham|mutton|fish|herring|salmon|oyster|butter|cheese|milk|egg|lard|tallow|stearine|margarine|spice|pepper|ginger|cinnamon|tobacco|cigar|snuff|salt|vinegar|sauce|honey|hops|potato|onion|vegetable|succade|confection|provision|yeast|chicory|sago|tapioca|arrowroot|coco.?nut|cured|preserved|pickle|seed'),
 ('Animals & animal products', r'animal|cattle|ox\b|oxen|sheep|lamb|swine|horse|cow|bull|hide|skin|fur|pelt|leather|horn|hoof|bone|bristle|feather|ivory|hair|isinglass|glue|gut|sponge|shell|coral|pearl'),
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
# label-variant duplicates: the same place printed two ways would be summed
# twice. Canonicalise to one origin key.
ALIAS = {'Chili': 'Chile', 'Portugal, Azores, And Madeira': 'Portugal'}
outliers = []            # origin cells that exceed the national anchor (log)
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
    t1 = collections.defaultdict(int)
    for u, s in e['c'].get('§TOTAL', {}).items():
        if u == dom or dom == '?':
            for cell in s:
                t1[cell[0]] += cell[1]
    if not t1:
        for u, s in e['c'].get('§TOTAL', {}).items():
            for cell in s:
                t1[cell[0]] += cell[1]
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
                cell[0] += min(v, CAP)
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
    yrs = sorted(set(nat) | set(t1))
    out[n] = {
        'u': dom,
        'v': round(e['v']),
        'cat': classify(n),
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
print(f'impossible-origin cells dropped: {len(outliers)} -> reports/origin_outliers.csv')
print(f'map_slim.json: {sz/1e6:.2f} MB')
