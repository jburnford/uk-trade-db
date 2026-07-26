#!/usr/bin/env python3
"""Slim, self-contained dataset for the public trade-origins map artifact.
Reads the curated map_data.json (cells [year,qty,rank,value]) + the whitelist
(KEEP bucket + adjudicated fold/rename targets) + the gazetteer, and emits a
compact per-commodity structure: mapped-origin series (value + dominant-unit
quantity), an unmapped residual, and the national total per year.
"""
import json, csv, collections, re
from pathlib import Path

CAP = 50_000_000          # per-cell value plausibility cap (matches payload sort cap)
m = json.load(open('exports/map_data.json'))
gaz = json.load(open('reference/map_gazetteer.json'))
rows = list(csv.DictReader(open('reports/commodity_curation_queue.csv')))
keep = {r['commodity'] for r in rows if r['bucket'] == 'KEEP'}
cur = list(csv.DictReader(open('reference/commodity_curation.csv')))
targets = {r['target'] for r in cur if r['action'] in ('fold', 'rename') and r['target']}
# commodities whose 'country' column is a list of commodities, not places
# (scripts/detect_transposed_tables.py). The ones with no national series are
# dropped outright by curation; these still publish a real §TOTAL, so the
# commodity stays and only its bogus origins are suppressed - the map then
# shows the national series with 'no origin breakdown published', which is
# what the source actually supports.
try:
    TRANSPOSED = {r['commodity'] for r in
                  csv.DictReader(open('reports/transposed_tables.csv'))}
except FileNotFoundError:
    TRANSPOSED = set()
# (commodity, year, origin) cells whose origin appears in no other year of the
# commodity and carries most of that year — a glued block from a neighbouring
# table (scripts/detect_profile_outliers.py). The impossible-origin filter
# below cannot see these: it needs a Tier-1 anchor to measure against, and
# these land in years that have none. Teak 1873 is the case in point, reading
# 138,645 loads against ~30,000 either side because Canada, Sweden, Russia and
# Norway - the hewn-softwood trade - were glued into it.
try:
    PROFILE_OUT = {(r['commodity'], int(r['year']), r['origin']) for r in
                   csv.DictReader(open('reports/origin_profile_outliers.csv'))}
except FileNotFoundError:
    PROFILE_OUT = set()

# ---- per-cell junk-origin filter -------------------------------------------
# The transposed-table detector asks whether a WHOLE commodity's country column
# is really a list of commodities. It cannot see the commoner case: a genuine
# origin table with a handful of commodity names mixed into it, left behind by
# a fold or a glued block. Palm oil carried 'Petroleum Gallons' (GBP97.6M),
# 'Potatoes', 'Onions Raw Bushels' and 'Paper Including Strawboard' for
# 1897-99. Those cells lost their unit, so they never reached the quantity
# axis and looked harmless — but VALUE has no unit to lose, and they inflated
# palm oil's 1898 origin value ninefold.
#
# The detector's SUBSET test ('Hewn Of All Sorts' sits inside 'Wood And Timber
# — Hewn Of All Sorts') is safe only in aggregate, where it has to hold for 60%
# of a commodity's labels. Per cell it eats real places, because the corpus is
# full of country-as-article phantoms whose names contain place tokens: it
# dropped 'West Coast Of Africa (Foreign' — palm oil's own region — for sitting
# inside 'Nuts And Kernels — From West Coast Of Africa (Foreign)', and 'United
# States' likewise. So per cell the tokens must match a commodity name EXACTLY,
# and anything the gazetteer recognises is a place whatever it resembles.
# Unit words INCLUDING the OCR garbles the payload already aliases (Cwts reads
# as Cicts / Ccts / Cwis / Gwts / Cnts...). Without them a glued cell keeps its
# unit token and reads as an ordinary name: 'Paper Including Strawboard And C
# Cicts' survived the first pass while '... And C Ccts' did not.
_UNITW = re.compile(r'\b(lbs?|lbds|cwts?|cuts?|ccts?|cts?|cicts|ciots|cwis'
                    r'|cwtts|cwtss|cwtz|ccwts|cnts|cets|gwts|owts|wts'
                    r'|tons?|fons|tuns?|gallons?|galls?|gals?|bushels?'
                    r'|numbers?|yards?|yds|loads?|louds|quarters?|qrs'
                    r'|pairs?|prs|doz|dozen|gross|carats?|centals?'
                    r'|packages?|barrels?|proof)\b', re.I)


def _toks(s):
    return frozenset(w for w in re.split(r'[^A-Za-z0-9]+', s.upper())
                     if len(w) > 2 and w not in
                     ('AND', 'THE', 'FOR', 'NOT', 'ALL', 'ANY', 'OF', 'OR', 'IN'))


_use = collections.Counter()
for _n, _e in m.items():
    for _c in (_e.get('c') or {}):
        if _c != '§TOTAL':
            _use[_c] += 1
PLACE_LIKE = {c for c, k in _use.items() if k >= 5}
# Only commodities that publish a national line contribute to the vocabulary.
# The corpus is full of country-as-article phantoms ('Tar — West Coast Of
# Africa, Foreign', 'Dye Woods — Spanish Possessions', 'Cotton Manufactures —
# United States'); left in, each teaches the filter that a real place is a
# commodity name and it deletes that place's cells. None of them carries a
# §TOTAL, and every real commodity does. The cost is a few junk labels going
# unrecognised ('Bar', from the anchorless 'Iron — Bar') — the right way to be
# wrong, since a missed junk cell only clutters, while a false positive
# silently deletes trade.
COM_VOCAB = set()
for _n, _e in m.items():
    if '§TOTAL' not in (_e.get('c') or {}):
        continue
    COM_VOCAB.add(_toks(_n))
    if '—' in _n:
        # both halves: a glued cell may carry the family head alone ('Oil Seed
        # Cake', 'Paper-Making Materials') or the article alone ('Olive')
        COM_VOCAB.add(_toks(_n.split('—', 1)[1]))
        COM_VOCAB.add(_toks(_n.split('—', 1)[0]))


def junk_origin(c):
    """True when this 'country' is really a commodity name."""
    if c == '§TOTAL' or c in PLACE_LIKE or c in gaz or ALIAS.get(c) in gaz:
        return False
    if _UNITW.search(c):
        return True                      # no country carries a unit word
    return _toks(_UNITW.sub('', c)) in COM_VOCAB


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
    # ---- found by the re-parsed-row log: the same printed row read under two
    # spellings of one place, which without these lines is counted twice ----
    'Gold Coast Colony': 'The Gold Coast',
    'British Maduras': 'British Honduras',        # OCR: H read as M
    'Algoria': 'Algeria',
    'East Coast Of Africa, Native States': 'East Coast Of Africa',
    'Canada (Atlantic)': 'Canada',                # Canada prints no Pacific side
    # the Spanish West Indies WERE Cuba and Puerto Rico; the later volumes
    # simply name them instead of the grouping
    'Cuba And Porto Rico': 'Spanish West India Islands',
    'British East Indies Bengal': 'Bengal',
    'The Cape Of Good Hope': 'Cape Of Good Hope',
}
outliers = []
junk = []
totals_as_origin = []            # origin cells that exceed the national anchor (log)
value_dropped = []       # per-cell values over CAP (corrupt, not large)
quantity_as_value = []   # national VALUE lines that are really the quantity
quality = []             # (commodity, [flag,...]) for the audit report
unit_alias = []          # origin/anchor unit labels that measure the same thing
unit_mismatch = []       # ...and those that do not, so the anchor is dropped
unit_era = []            # a printed unit CHANGE mid-series, converted (below)

# Definitional conversions between printed units. Only these: an exact,
# by-definition factor is arithmetic, anything else would be an estimate.
UNIT_FACTOR = {('Cwt', 'Ton'): 20, ('Lb', 'Cwt'): 112, ('Lb', 'Ton'): 2240,
               ('Pairs', 'Dozen Pairs'): 12, ('Oz Troy', 'Lb'): 12}


def unit_factor(frm, to):
    """Multiplier taking a quantity in `frm` to one in `to`, or None."""
    if frm == to:
        return 1.0
    if (frm, to) in UNIT_FACTOR:
        return 1.0 / UNIT_FACTOR[(frm, to)]
    if (to, frm) in UNIT_FACTOR:
        return float(UNIT_FACTOR[(to, frm)])
    return None
reparse_dropped = []     # one printed row read twice under two spellings
twin_origins = []        # ...and read twice under two DIFFERENT places (logged)
gap_log = []             # years inside the origin span with no origin table
origin_dedup = []        # every origin cell + its keep/drop verdict (see below)
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
    # ---- a printed unit CHANGE mid-series ----------------------------------
    # The volumes re-denominate a line and go on printing it: jute moves from
    # hundredweights to tons in the 1887 volume, flax and hemp the other way in
    # 1893, boots and gloves from pairs to dozen pairs in 1878. The quantity
    # axis takes only the DOMINANT unit, so the other era's cells were silently
    # dropped -- jute showed fifteen years of value (GBP2.5-4.5M a year) with no
    # tonnage at all, and its 1868-86 anchor went with them.
    #
    # Converting is arithmetic, not estimation: twenty hundredweight ARE a ton.
    # But it is only applied to years the dominant unit does not reach, so a
    # year holding both units -- which means a garbled header rather than a
    # regime change -- is left exactly as it was and logged. That guard is what
    # keeps this from double-counting the overlap (jute's 1883-86 Ton cells sit
    # inside the Cwt era and come to 922 tons against a 5.9M cwt year).
    dom_years = set()
    for c, byu in e['c'].items():
        if c == '§TOTAL' or '(' in c:
            continue
        for cell in byu.get(dom, ()):
            if cell[1]:
                dom_years.add(cell[0])
    conv = {}                       # unit -> factor, for foreign-unit years
    if dom != '?':
        for u in ucnt:
            f = unit_factor(u, dom)
            if u != dom and f:
                conv[u] = f
    # ---- Tier-1 anchor quantity per year (authoritative national total) ----
    # The anchor must be ONE unit. The old code summed every §TOTAL unit
    # whenever the origins carried no unit, which added a value series to a
    # tonnage ('Nuts And Kernels' has both), and fell back to summing them all
    # whenever the origin unit was absent from §TOTAL, which produced an
    # anchor in Tons for origins measured in Cwts.
    t1_by_u = collections.defaultdict(dict)
    t1v = {}
    for u, ser in e['c'].get('§TOTAL', {}).items():
        if u == 'Value':          # a value line is not a quantity anchor
            continue
        for cell in ser:
            # take one reading per year, never the SUM of two. A national
            # total is one printed line; two §TOTAL cells for the same unit
            # and year are two readings of it, and adding them doubles the
            # anchor, which halves the commodity on the map without tripping
            # any flag. The larger is kept because the failure that produces
            # a pair is a fold, and a folded-in zero must not win.
            t1_by_u[u][cell[0]] = max(t1_by_u[u].get(cell[0], 0), cell[1])
            if len(cell) > 3 and cell[3]:
                t1v.setdefault(cell[0], cell[3])
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
    # ...and the national line changes unit in the same volume the country
    # tables do, so the anchor needs the same treatment: jute's 1868-86 total
    # is printed in hundredweights and was being thrown away with them, which
    # left the recovered origin years unanchored and still unmeasurable. Fill
    # only years the dominant unit does not already print - a year with two
    # readings keeps the one in its own unit.
    #
    # The two sides have to be guarded the SAME way or the fix invents a
    # defect: jute 1883 holds 922 junk tons beside 7.4M hundredweights, so the
    # origin side (rightly) declines to convert it, and an anchor filled from
    # the hundredweight line would have made a year that merely had no anchor
    # read 0.0025 of one. A year printing both units is left wholly alone.
    mixed = {y for y in dom_years
             if any(cell[0] == y and cell[1]
                    for c2, byu2 in e['c'].items()
                    if c2 != '§TOTAL' and '(' not in c2
                    for u2 in conv for cell in byu2.get(u2, ()))}
    #
    # And the label is not evidence. 'Metal — Unenumerated, Unwrought' prints
    # 2,699 under a "Cwt" header for 1892 beside 2,469 under a "Ton" header for
    # 1896, with origins of 2,878 tons: the header is an OCR error and the
    # figures were always tons, so dividing by twenty invents a 21x
    # over-count out of a commodity that had no flag at all. Decide by the
    # numbers -- take whichever reading, converted or as printed, the origin
    # tables of those same years actually support, and if neither does, leave
    # the year unanchored rather than mis-scale it.
    if t1 and dom != '?':
        t1, added = dict(t1), []
        oq = collections.Counter()
        for c2, byu2 in e['c'].items():
            if c2 == '§TOTAL' or '(' in c2:
                continue
            for u2, ser2 in byu2.items():
                fo = 1.0 if u2 == dom else conv.get(u2)
                for cell in ser2:
                    if cell[1] and fo:
                        oq[cell[0]] += cell[1] * fo
        for u, ser in t1_by_u.items():
            f = unit_factor(u, dom) if u not in ('?', 'Value') else None
            if u == dom or not f or f == 1.0:
                continue
            # Decided PER YEAR, because an era header outlives the change it
            # marks: coffee's "Lbs" national line runs 127-192 million for
            # 1866-72 and then prints 1,637,523 for 1873, which is already
            # hundredweights under a stale header. One verdict for the whole
            # unit gets that year wrong by a factor of 112 whichever way it
            # falls. Years with no origin table of their own follow the
            # majority verdict of the years that have one.
            fill = [y for y, q in ser.items()
                    if y not in t1 and q and y not in mixed]
            verdict, votes = {}, collections.Counter()
            for y in fill:
                if not oq.get(y):
                    continue
                rc, rr = oq[y] / (ser[y] * f), oq[y] / ser[y]
                pick = f if abs(rc - 1) < abs(rr - 1) else 1.0
                if abs((rc if pick != 1.0 else rr) - 1) <= 0.25:
                    verdict[y] = pick
                    votes[pick] += 1
            if not votes:
                # keep this out of unit_reconciliation.csv, which is about
                # origin-vs-anchor labels; this is an era anchor with no
                # origin table in any of its years to judge it by
                unit_era.append((n, dom, f'anchor {u} (REJECTED, nothing to '
                                 f'judge it by)', '', 0))
                continue
            default = votes.most_common(1)[0][0]
            for y in fill:
                t1[y] = ser[y] * verdict.get(y, default)
            added.extend(fill)
            for pick, tag in ((f, f'/{1/f:g}'),
                              (1.0, f'label only, figures already {dom}')):
                ys = sorted(y for y in fill if verdict.get(y, default) == pick)
                if ys:
                    unit_era.append((n, dom, f'anchor {u} ({tag})',
                                     ';'.join(str(y) for y in ys), len(ys)))
    if conv:
        recovered = sorted(y for y in set().union(
            *[{cell[0] for c2, byu2 in e['c'].items()
               if c2 != '§TOTAL' and '(' not in c2
               for cell in byu2.get(u2, ()) if cell[1]} for u2 in conv])
            if y not in dom_years)
        if recovered:
            unit_era.append((n, dom, '+'.join(sorted(conv)),
                             ';'.join(str(y) for y in recovered), len(recovered)))
            unit_note = ((unit_note + '; ') if unit_note else '') + (
                f'the printed unit changes mid-series - '
                f'{", ".join(sorted(conv))} converted to {dom} for '
                f'{min(recovered)}-{max(recovered)}')
    # ---- aggregate to (label, year) -> [value, qty(dom unit), bestRank] ----
    # label-variant duplicates are canonicalised (Chili -> Chile) so the same
    # place is never summed under two spellings.
    ly = {}
    # One printed row read twice. Canonicalising spellings makes this WORSE
    # rather than better: 'Turkey European' and 'Turkey, European' both alias
    # to Turkey and were then summed, so Oats 1893 counted the same 110,047
    # quarters as two shipments. The fingerprint is the one the teak work
    # established - the quantity AND the value match to the digit, which two
    # genuine rows do not do - and here it is decisive, because after aliasing
    # the two cells claim the same place in the same year as well.
    # Rows that stay two DIFFERENT places after aliasing are a harder case
    # (which of the two is the misread?) and are logged, not dropped.
    reparsed = set()
    twins = {}
    for c, byu in ({} if n in TRANSPOSED else e['c']).items():
        if c == '§TOTAL':
            continue
        c = ALIAS.get(c, c)
        for u, s in byu.items():
            for y, q, r, v in s:
                if q and v:
                    if (c, y, q, v) in reparsed:
                        reparse_dropped.append((n, y, c, round(q), round(v)))
                        continue
                    reparsed.add((c, y, q, v))
                    twin = twins.get((y, q, v))
                    # A parent and its sole child legitimately carry the same
                    # figure ('United States Of America' and 'United States Of
                    # America (Atlantic)' when the Pacific shipped none), and
                    # the parent<->child pass below already counts that once.
                    if (twin and twin != c and v >= 100 and q >= 10
                            and c not in children_of.get(twin, ())
                            and twin not in children_of.get(c, ())):
                        twin_origins.append((n, y, twin, c, round(q), round(v)))
                    twins[(y, q, v)] = c
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
                elif u in conv and y not in dom_years:
                    cell[1] += q * conv[u]
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
    # Where the year has a Tier-1 anchor, that share test is second-best
    # evidence and the anchor is first-best: it was printed on another page and
    # says what the year's origins have to add up to. So try both readings and
    # keep whichever lands closer to it. Wool is the case that forced this. Its
    # 'Australasia' row runs 1.22-1.28x the colonies listed under it in some
    # years and equals them in others, and the 85% share test therefore flipped
    # its verdict from year to year - 1888, 1889 and 1896 dropped the parent and
    # closed at 1.00 while 1890-93, 1895 and 1898 kept it and sat at 1.15-1.20.
    # Worse, the share was measured on VALUE while the map displays QUANTITY,
    # and the parent's value cells are the unreliable ones (Australasia 1897:
    # GBP2.0M against GBP21.8M in 1893 for a similar tonnage), so the test was
    # deciding the quantity axis on a number it never shows.
    drop = set()
    # ---- printed-Total-as-origin filter: an "origin" whose quantity is the
    # year's whole national total is the table's Total row, parsed as a
    # country. The parser renames a Total to whatever region context is open
    # ('From West Coast of Africa (Foreign):' over palm oil's 1875 members),
    # and its guard - Total more than twice the context's own sum - cannot
    # fire when the context spans the entire block. The impossible-origin
    # filter below steps over it too, because it only looks above 1.15x.
    #
    # Self-validating, so it cannot misfire on a commodity that genuinely has
    # one origin: the cell goes only when the REMAINING cells already account
    # for most of the anchor, i.e. only when dropping it makes the year close.
    # It runs BEFORE the parent/child de-duplication below, which weighs each
    # parent against its children by how close the year then lands to the
    # anchor: with the phantom still in the sum that comparison is made against
    # a total twice its true size and picks the wrong side (palm oil 1875 lost
    # The Gold Coast, 123,166 cwt, that way).
    for y in sorted({yy for (_, yy) in ly}):
        t = t1.get(y, 0)
        if t <= 1000:
            continue
        cells = [(c, v) for (c, yy), v in ly.items()
                 if yy == y and (c, y) not in drop]
        for c, cell in cells:
            # EXACT, not approximate: a printed Total row carries the anchor
            # to the digit. At 0.5% the test also swept up genuine dominant
            # origins that merely sit near the total (jute's Bengal, hops from
            # the United States), which are the parent/child pass's business,
            # not this one.
            if not cell[1] or abs(cell[1] - t) > 0.0005 * t:
                continue
            rest = sum(v[1] for cc, v in cells if cc != c)
            if rest >= 0.5 * t:
                totals_as_origin.append(
                    {'commodity': n, 'year': y, 'origin': c,
                     'qty': round(cell[1]), 'anchor': round(t),
                     'others_sum': round(rest)})
                drop.add((c, y))
                break

    years = {y for (_c, y) in ly}
    for y in years:
        # cells already dropped above must not weigh in here: a phantom Total
        # left in `present` doubles the year's sum and flips the parent/child
        # choice below
        present = {c for (c, yy) in ly if yy == y and (c, y) not in drop}
        groups = [(pa, kids) for pa in present
                  if (kids := [k for k in children_of.get(pa, ()) if k in present])]
        if not groups:
            continue
        t = t1.get(y, 0)
        # measure on the axis the map shows, falling back to value where the
        # year carries no dominant-unit quantity at all
        ix = 1 if (t > 1000 and any(ly[(c, y)][1] for c in present)) else 0
        if t > 1000 and ix == 1 and len(groups) <= 10:
            # Choose the groups TOGETHER, not one after another. Deciding each
            # against a running total that still holds the other groups'
            # duplicates biases every choice but the last: wool 1894 has both
            # an Australasia group and a South Africa one, and judged first
            # against the uncleaned total Australasia's parent looked 4.8M
            # from the anchor when the honest comparison was 75M. A commodity
            # rarely has more than three or four such groups in a year, so
            # every combination can simply be tried. Overlapping groups (a
            # child that is itself a parent) come out right because each
            # combination is scored on the set it actually keeps.
            # THREE options per group, not two: drop the parent, drop the
            # children, or KEEP BOTH. The printed table sometimes carries a
            # parent line that is a genuine remainder beside children that do
            # not cover it — 'British East Indies' beside Bombay, Madras and
            # Bengal, which between them are 88% of it — and forcing a binary
            # choice there throws away whichever side is smaller. It was
            # costing exact years: tea 1885-92 fell to 0.96, silk 1886-92 to
            # 0.79-0.91, palm oil eleven years to 0.98. Adding the third
            # option is safe precisely because the score is the distance to
            # the Tier-1 anchor: a genuine duplicate kept twice overshoots and
            # loses, which is the same evidence that made the anchor the
            # arbiter here in the first place.
            #
            # Ties keep the DROPPING reading, so nothing that used to be
            # de-duplicated stops being de-duplicated on a coin toss.
            best = None
            for mask in range(3 ** len(groups)):
                dropped, rem = set(), mask
                for pa, kids in groups:
                    choice, rem = rem % 3, rem // 3
                    if choice == 0:
                        dropped.update(kids)      # parent is the fuller total
                    elif choice == 1:
                        dropped.add(pa)           # children cover the parent
                kept_cells = [c for c in present if c not in dropped]
                kept = sum(ly[(c, y)][ix] for c in kept_cells)
                score = (abs(kept - t), len(kept_cells))
                if best is None or score < best[0]:
                    best = (score, dropped)
            drop.update((c, y) for c in best[1])
        else:
            for pa, kids in groups:
                pv = ly[(pa, y)][0] or 1
                kv = sum(ly[(k, y)][0] for k in kids)
                if kv >= 0.85 * pv:
                    drop.add((pa, y))             # children cover parent
                else:
                    for k in kids:
                        drop.add((k, y))          # parent is the fuller total
    # ---- impossible-origin filter: one origin cannot exceed the whole
    # national total. A cell whose quantity tops the Tier-1 anchor (x1.15
    # tolerance for anchor noise) is corrupt — country-column glue from another
    # commodity or a magnitude error (Burma 2.79M cwt "potatoes"; Russia 3.5M
    # ton "logwood"; Greece 1.3M gal "collodion"). Drop it and log for a
    # source-level fix. Only applied where the anchor is itself substantial.
    # the year's de-duplicated origin sum, for the anchor test below
    ysum = collections.defaultdict(float)
    for (c, y), cell in ly.items():
        if (c, y) not in drop:
            ysum[y] += cell[1]
    for (c, y), cell in list(ly.items()):
        if junk_origin(c):
            junk.append({'commodity': n, 'year': y, 'origin': c,
                         'value': round(cell[0]), 'qty': round(cell[1])})
            drop.add((c, y))
            continue
        if (n, y, c) in PROFILE_OUT:
            # The profile test asks whether an origin looks like it belongs to
            # this commodity, and it exists for years with NO anchor — that is
            # its stated remit. Where there IS one, the year's own arithmetic
            # outranks the resemblance, and it has to, because the origin most
            # likely to look unfamiliar is the one that dominates a single
            # year: Bengal was being suppressed from Indigo 1882 (60,888 of a
            # printed 95,272) and United States Of Colombia from Peruvian bark
            # 1881 (70,944 of 125,358) — the archetypal source of each. Keep
            # the cell whenever dropping it moves the year AWAY from its
            # printed national total.
            t = t1.get(y, 0)
            if t > 1000 and abs(ysum[y] - cell[1] - t) >= abs(ysum[y] - t):
                continue
            outliers.append({'commodity': n, 'year': y, 'origin': c,
                             'unit': dom, 'qty': round(cell[1]),
                             'anchor': round(t1.get(y, 0)),
                             'x_anchor': 'foreign to this commodity'})
            drop.add((c, y))
            continue
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
        # Export every cell with its keep/drop verdict. map_data.json still
        # carries parent AND children (Australasia beside its six colonies, a
        # clean 2x double count in tallow 1883-86 and 1891-96) and map_slim
        # resolves that but folds every unlocated origin into an anonymous
        # residual, losing 'Other Foreign Countries' as a label. Anything that
        # needs de-duplicated cells WITH their labels -- the gold comparisons,
        # notably -- had no source for them. This is that source, and it comes
        # from the same drop set the map ships, so the two cannot drift.
        origin_dedup.append((n, y, c, q, v, int((c, y) not in drop),
                             int(c in located)))
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
    if not per and not res and n not in TRANSPOSED:
        continue          # a suppressed table still has its national series
    # slider range = years that actually have ORIGIN data (bubbles/residual),
    # NOT the wider Tier-1 anchor span (1866-1900): otherwise the slider lands
    # on years with a national total but no origin breakdown -> empty map.
    yrs = sorted(nat) or sorted(t1)
    # ---- a value anchor that is really the QUANTITY line ------------------
    # Some printings put the quantity figure in the value column of the
    # abstract, and the cross-volume vote copies it faithfully: the flax and
    # linseed value line for 1885 IS its quantity line, 2,046,352, in six
    # volumes, while the origins come to GBP4.4M at 2.1 a quarter. Left in, it
    # does not merely fail the value test, it reports a real block as 2.14x
    # its total. Detected on the commodity's OWN price, so a commodity whose
    # goods genuinely cost about a pound a unit is never touched.
    prices = sorted(v / q for v, q in nat.values() if q and v)
    if prices and t1v:
        price = prices[len(prices) // 2]
        if not 0.9 <= price <= 1.1:
            for y, v in list(t1v.items()):
                if t1.get(y) and abs(v - t1[y]) <= 0.01 * t1[y]:
                    quantity_as_value.append(
                        {'commodity': n, 'year': y, 'value_line': round(v),
                         'quantity_line': round(t1[y]),
                         'price': round(price, 2)})
                    del t1v[y]
    # ---- per-commodity quality flags, shown on the map itself ------------
    # A reader cannot tell a well-measured series from a one-year fragment of
    # a mislabelled table by looking at bubbles, so the limits travel with the
    # data instead of living in a caveats paragraph nobody opens.
    fl = []
    if n in TRANSPOSED:
        fl.append('transposed')
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
        else:
            # There IS a national total and there ARE origins, but no single
            # year carries both, so nothing has ever been checked against
            # anything. Teak read as unflagged this way: origins ran to 1893
            # and the anchor started at 1893, overlapping on one year in which
            # the origin quantity happened to be zero.
            fl.append('nooverlap')
    # A HOLE: the national total says thousands of tons crossed the quay and no
    # origin table is published for it. The ratio tests above cannot see this -
    # a median ignores however many zeroes you give it - so 'Butter' read as
    # perfectly measured while 1882-85 were blank in the middle of a continuous
    # 1872-99 series, its origins for those years sitting under the era label
    # 'Butter And Butterine'.
    # The window is the one in which the source publishes origin tables at all,
    # 1872-1899, NOT the commodity's own span. Restricting it to the span was
    # the obvious thing and it was wrong: it can only see holes a sibling year
    # happens to bracket. Coffee's origins stopped in 1890 with the anchor
    # running to 1897 - nine blank years at the END, the same split-label defect
    # as butter's, and invisible to a span-bounded test. Outside 1872-1899 there
    # are no origin tables to be missing, so nothing there is a defect.
    oyrs = [y for y in nat if nat[y][1]]
    if t1 and len(oyrs) >= 3:
        gaps = [y for y in t1 if 1872 <= y <= 1899 and t1[y] > 1000
                and nat.get(y, [0, 0])[1] < 0.1 * t1[y]]
        if gaps:
            fl.append('gapyears')
            gap_log.append((n, round(e['v']), len(gaps),
                            ' '.join(str(y) for y in sorted(gaps))))
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
        # the printed national VALUE, carried on the §TOTAL cell's 4th
        # element by build_viz_payload. Unit-independent, so it needs none of
        # the unit reconciliation above: it exists so value closure can be
        # measured on the DE-DUPLICATED numbers the map actually shows,
        # rather than on the raw payload where a parent line and its children
        # are both still present.
        't1v': {str(y): round(v) for y, v in sorted(t1v.items()) if v},
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
            'transposed': 'the printed page was a list of commodities, not of '
                          'origins, so the origin column has been suppressed — '
                          'only the national total is shown',
            'noval': 'no value figures — only the quantity measure works',
            'nounit': 'the printed unit was not captured, so quantities may '
                      'mix units and the axis is unlabelled',
            'oneyear': 'origins for a single year only',
            'noanchor': 'no national total published for this line, so the '
                        'origins cannot be checked against one',
            'gapyears': 'some years inside the series have a national total '
                        'but no origin table at all - the map goes blank for '
                        'them while the trade was real',
            'nooverlap': 'the national total and the origin tables cover '
                         'different years, so neither has ever been checked '
                         'against the other',
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
outliers.sort(key=lambda r: (isinstance(r['x_anchor'], str), -r['qty']))
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
with open('reports/quantity_as_value.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['commodity', 'year', 'value_line',
                                      'quantity_line', 'price'])
    w.writeheader()
    w.writerows(sorted(quantity_as_value,
                       key=lambda r: -r['quantity_line']))
print(f'national value lines that are really the quantity: '
      f'{len(quantity_as_value)} '
      f'({len({r["commodity"] for r in quantity_as_value})} commodities) '
      f'-> reports/quantity_as_value.csv')
with open('reports/junk_origin_cells.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['commodity', 'year', 'origin',
                                      'value', 'qty'])
    w.writeheader()
    w.writerows(sorted(junk, key=lambda r: -r['value']))
with open('reports/total_row_as_origin.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['commodity', 'year', 'origin', 'qty',
                                      'anchor', 'others_sum'])
    w.writeheader()
    w.writerows(sorted(totals_as_origin, key=lambda r: -r['qty']))
print(f'printed-Total rows parsed as origins: {len(totals_as_origin)}'
      f' -> reports/total_row_as_origin.csv')
with open('exports/_origin_dedup.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['commodity', 'year', 'country', 'quantity', 'value',
                'kept', 'located'])
    w.writerows(sorted(origin_dedup, key=lambda r: (r[0], r[1], r[2])))
_kept = sum(r[5] for r in origin_dedup)
print(f'origin cells: {len(origin_dedup):,} ({_kept:,} kept after de-duplication)'
      f' -> exports/_origin_dedup.csv')
print(f'junk-origin cells dropped (commodity names as countries): {len(junk)}'
      f' -> reports/junk_origin_cells.csv')
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
with open('reports/unit_era_changes.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['commodity', 'unit_shown', 'converted_from', 'years', 'n_years'])
    w.writerows(sorted(unit_era, key=lambda r: (r[0], r[2])))
print(f'printed unit changes converted: {len(unit_era)} series '
      f'({sum(r[4] for r in unit_era)} year-cells) '
      f'-> reports/unit_era_changes.csv')
print(f'over-cap value cells dropped: {len(value_dropped)} '
      f'({len({r[0] for r in value_dropped})} commodities) -> reports/value_cap_cells.csv')
with open('reports/reparsed_origin_cells.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['class', 'commodity', 'year', 'origin', 'twin_origin',
                'qty', 'value'])
    w.writerows(['same place, dropped', n, y, c, '', q, v]
                for n, y, c, q, v in sorted(reparse_dropped,
                                            key=lambda r: -r[4]))
    w.writerows(['two places, kept', n, y, a, b, q, v]
                for n, y, a, b, q, v in sorted(twin_origins,
                                               key=lambda r: -r[5]))
with open('reports/origin_gap_years.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['commodity', 'gbp', 'n_gap_years', 'years'])
    w.writerows(sorted(gap_log, key=lambda r: (-r[2], -r[1])))
print(f'blank years inside a series: {sum(r[2] for r in gap_log)} across '
      f'{len(gap_log)} commodities -> reports/origin_gap_years.csv')
print(f're-parsed origin rows: {len(reparse_dropped)} dropped as one place '
      f'read twice, {len(twin_origins)} logged as two places sharing a row '
      f'-> reports/reparsed_origin_cells.csv')
print(f'map_slim.json: {sz/1e6:.2f} MB')
