#!/usr/bin/env python3
"""Build the JSON payload for the coverage-explorer artifact.

Every distinct COMMODITY is its own series — no umbrella families. Two
printed labels are the same commodity only when their token signatures are
identical after stopword/punctuation/possessive normalization:

  'Wool | Sheep and Lambs''  ==  'Sheep or Lambs' Wool'   {LAMBS,SHEEP,WOOL}
  'Goats' Hair or Wool'      ==  'Wool | Goats' Wool or Hair'  (one goats series)
  ...but goats {GOATS,HAIR,WOOL} never merges with sheep {LAMBS,SHEEP,WOOL}.

Sticky-group repair (Tier-1 abstract rows only): when a row's ARTICLE alone
is the exact signature of a known commodity and is not pure qualifier vocab,
trust the article — 'Animals, Living | Butter' is Butter; 'Tobacco | Raw'
stays Tobacco — Raw because RAW is qualifier vocabulary.

Countries fold colonial sub-entry labels ('British East Indies : Straits
Settlements' -> Straits Settlements), parenthesized/hyphenation variants,
and '-Other ...' composites. Units fold OCR aliases (Cwts./Cuts./Ccts. ->
Cwt). Tier-1 voted national totals (1866-1900) attach to their commodity
under the pseudo-country '§TOTAL'; tiers map A/B/C -> rank 1/2/3.

Usage: python3 scripts/build_viz_payload.py [out.json]
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

import duckdb

BASE = Path('/home/jic823/uk_trade_db')
TK = '§TOTAL'
QUALS = {'RAW', 'MANUFACTURES OF', 'MANUFACTURED', 'UNMANUFACTURED', 'REFINED',
         'UNREFINED', 'WROUGHT', 'UNWROUGHT', 'PARTLY MANUFACTURED'}
STOP = {'AND', 'OR', 'THE', 'A', 'AN', 'OF'}
# pure qualifier vocabulary: an article made ONLY of these never names a
# commodity on its own, so it must stay with its printed group
GENERIC = {'RAW', 'UNENUMERATED', 'OTHER', 'TOTAL', 'GOODS', 'ARTICLES',
           'HEWN', 'STAVES', 'SAWN', 'SPLIT', 'DRESSED', 'UNDRESSED',
           'MANUFACTURED', 'UNMANUFACTURED', 'REFINED', 'UNREFINED',
           'WROUGHT', 'UNWROUGHT', 'MANUFACTURES', 'KINDS', 'SORTS',
           'UNSPECIFIED', 'FRESH', 'SALTED', 'DRIED', 'PRESERVED'}


def fold_group(group):
    g = re.sub(r'\s+', ' ', (group or '').strip().upper()).rstrip(' .,:;')
    # one printed section, many captured headings: 'Corn and Grain:' and
    # 'Meal and Flour:' are SUBSECTIONS of 'CORN, GRAIN, MEAL, AND FLOUR' —
    # the parser keeps whichever heading is nearest, splitting wheat-flour
    # (etc.) across six group labels. Fold to the TOKEN-MINIMAL member of
    # the family: with MEAL/FLOUR in the group tokens, 'Wheat' and 'Wheat
    # Meal or Flour' would collapse to the same token SET (set-union
    # absorption) — 'CORN AND GRAIN' keeps the article tokens load-bearing.
    # Articles are disjoint between the subsections, so the fold is
    # collision-free, and grouped T1 labels ('Corn, Grain, and Meal |
    # Wheat') land on the same sig as the country data.
    if re.match(r'^CORN\b.*\bGRAIN\b', g) or g == 'MEAL AND FLOUR':
        g = 'CORN AND GRAIN'
    if ',' in g:
        base, suf = g.split(',', 1)
        if suf.strip() in QUALS:
            return base.strip(), suf.strip()
    return g, None


def _parent_norm(p):
    p = re.sub(r'\s+', ' ', p.replace('-', ' ').strip(' -,')).upper()
    if p.startswith('UNITED STATES') and 'COLOMBIA' not in p:
        return 'United States Of America'
    return p.title()


def fold_country(c):
    c = (c or '?').strip()
    c = re.sub(r'\s*:\s*', ' : ', c)        # normalize colon spacing
    parent = None
    if ' : ' in c:                          # sub-entry: remember the parent
        parent, c = (x.strip() for x in c.split(' : ', 1))
    c = c.strip('()').strip()               # '(Straits Settlements)'
    c = re.sub(r'(\w)- (\w)', r'\1\2', c)   # 'In- dian' hyphenation breaks
    c = re.sub(r'\s*-\s*Other\s.*$', '', c)  # 'X-Other British...' composites
    c = re.sub(r'\s+', ' ', c)
    # coastal-split origin regime: 'United States of America : On the
    # Atlantic', 'United States: Atlantic', bare 'on the Atlantic' -> one
    # label per (country, coast). Bare forms are US in practice (the only
    # origin printed coast-split without a parent in these tables).
    # 'Islands in the Pacific' never matches: the pattern is fully anchored.
    m = re.match(r'^[-\s]*(?:on the\s+)?(atlantic|pacific)(?:\s+ports?)?$', c, re.I)
    if m:
        p = _parent_norm(parent) if parent else 'United States Of America'
        return f'{p} ({m.group(1).title()})'
    m = re.match(r'^[-\s]*atlantic\s*(?:&|and)?\s*pacific$', c, re.I)
    if m:
        p = _parent_norm(parent) if parent else 'United States Of America'
        return f'{p} (Atlantic & Pacific)'
    m = re.match(r'^(.*?)[,\s]+on the (atlantic|pacific)$', c, re.I)
    if m:
        return f'{_parent_norm(m.group(1))} ({m.group(2).title()})'
    # port-split origin regime: Russian grain/flax/hemp is printed 'Russia :
    # Northern Ports' / 'Southern Ports' (Baltic vs Black Sea shipping), often
    # with NO parent-Russia row. Bare forms are Russia in practice (the only
    # origin printed port-split in these tables); 'Ports in Northern Africa'
    # never matches — the pattern is fully anchored.
    m = re.match(r'^(?:russia[,:\s]+)?(northern|southern)\s+ports?(?:\s+of)?$',
                 c, re.I)
    if m:
        p = _parent_norm(parent) if parent else 'Russia'
        return f'{p} ({m.group(1).title()} Ports)'
    # China scope labels fold to 'China': pre-1885 tables print the
    # inclusive 'China and Hong Kong' (plain-China years then mean the
    # same); from 1885 Hong Kong gets its own line, so 'China (exclusive
    # of Hong Kong)' means what plain 'China' means in the neighbouring
    # years (silk 1886: 1,217,002 excl. sits between 1885's 1,444,960 and
    # 1887's 1,416,660 — both exclusive-era plain-China lines)
    if re.match(r'^china (?:and hong\s*kong|\(?exclusive of hong\s*kong\)?)$',
                c, re.I):
        return 'China'
    return c.title() if c else '?'


_UNIT_ALIAS = {
    'cwt': 'Cwt', 'cwts': 'Cwt', 'cuts': 'Cwt', 'cts': 'Cwt', 'cwis': 'Cwt',
    'cwtts': 'Cwt', 'gwts': 'Cwt', 'owts': 'Cwt', 'wts': 'Cwt', 'cwt s': 'Cwt',
    'ccts': 'Cwt', 'cicts': 'Cwt', 'cets': 'Cwt', 'ccwts': 'Cwt',
    'lb': 'Lb', 'lbs': 'Lb', 'lbds': 'Lb',
    'ton': 'Ton', 'tons': 'Ton', 'fons': 'Ton', 'tons cwts': 'Ton',
    'load': 'Load', 'loads': 'Load', 'louds': 'Load',
    'gallon': 'Gallon', 'gallons': 'Gallon', 'galls': 'Gallon', 'gals': 'Gallon',
    'proof gallon': 'Proof Gallon', 'proof gallons': 'Proof Gallon',
    'oz troy': 'Oz Troy', 'ozs troy': 'Oz Troy',
    'number': 'Number', 'no': 'Number', 'nos': 'Number',
    'yard': 'Yard', 'yards': 'Yard', 'yds': 'Yard',
    'quarter': 'Quarter', 'quarters': 'Quarter', 'qrs': 'Quarter',
    'bushel': 'Bushel', 'bushels': 'Bushel',
    'barrel': 'Barrel', 'barrels': 'Barrel',
    'dozen': 'Dozen', 'dozens': 'Dozen',
    'tun': 'Tun', 'tuns': 'Tun',
    'great hundred': 'Great Hundred', 'great hundreds': 'Great Hundred',
    'gt hundreds': 'Great Hundred',
}


def norm_unit(u):
    s = re.sub(r'\s+', ' ', re.sub(r'[^a-z ]', ' ', (u or '').lower())).strip()
    if not s:
        return '?'
    return _UNIT_ALIAS.get(s, s.title())


def toks(*parts):
    """Signature tokens: upper, alnum only ('Lambs'' -> LAMBS), stopwords out.
    Single-character tokens are OCR shrapnel ("Wool'd)" -> WOOL + D), never
    meaning — dropped."""
    out = set()
    for p in parts:
        for t in re.split(r'[^A-Za-z0-9]+', p or ''):
            t = t.upper()
            if len(t) > 1 and t not in STOP:
                # the abstract prints 'Wheatmeal' where the country tables
                # print 'Wheat Meal' — same commodity, one token vs two
                if t == 'WHEATMEAL':
                    out.update(('WHEAT', 'MEAL'))
                else:
                    out.add(t)
    return out


def sig_of(g_base, qual, article):
    t = toks(g_base, qual, article)
    # stale sibling-heading glue: teak rows print as 'Hewn : Fir : Teak' /
    # 'Hewn, Fir : Teak' in many volumes (the parser drags the neighbouring
    # Fir heading in). No real 'fir teak' commodity exists — drop the stale
    # token so the teak series is one commodity 1874-99.
    if 'TEAK' in t:
        t.discard('FIR')
    return tuple(sorted(t))


def display(g_base, qual, article):
    a = (article or '').strip().lstrip(',»„"”° ').strip()
    tail = ' · '.join(x for x in (qual, a.upper()) if x).title()
    g = g_base.strip(' ,.:;"„”“«»\'').title() if g_base else ''
    if g and tail:
        return f'{g} — {tail}'
    return g or tail or '(unlabelled)'


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / 'exports' / 'viz_payload.json'
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)
    comms = {}          # sig -> {'v': gbp, 'labels': Counter, 'c': {cty:{unit:[cells]}}}

    def slot(sig):
        return comms.setdefault(sig, {'v': 0, 'labels': Counter(), 'c': {}})

    def add_cell(sig, label, cty, unit, y, q, r, weight=1):
        s = slot(sig)
        s['labels'][label] += weight
        s['c'].setdefault(cty, {}).setdefault(unit, []).append(
            [int(y), round(float(q)), int(r)])

    # ---- T1 label authority (fetched early: pass 1 repair needs it) ----
    t1_rows = con.execute("""
            SELECT article_group, article, unit, year, value, tier
            FROM consensus
            WHERE flow='import' AND measure='quantity' AND value > 0""").fetchall()
    # every printed abstract label is an attested commodity; additionally map
    # each grouped label's ARTICLE tokens to its commodity so a country row
    # whose group went stale ('TOBACCO | Red, in Casks' = wine rows under a
    # stale column-top group) can be re-homed when the article alone is an
    # unambiguous fingerprint of exactly one abstract commodity.
    t1_attested = set()
    art2commod = {}          # akey -> {(full sig, label): set(years)}
    for g, a, _u, y, *_ in t1_rows:
        if (g or '').strip():
            base, qual = fold_group(g)
            full = sig_of(base, qual, a)
            akey = tuple(sorted(toks(a)))
            lab = display(base, qual, a)
        else:
            base, qual = fold_group(a)
            full = akey = sig_of(base, qual, None)
            lab = display(base, qual, None)
            # late-era abstract prints wine colours as bare groupless lines;
            # 'Red' / 'White' alone are unreadable in the picker
            if full in (('red',), ('white',), ('RED',), ('WHITE',)) or lab in ('Red', 'White'):
                lab = f'Wine — {lab}'
        if full:
            t1_attested.add(full)
            if akey:
                art2commod.setdefault(akey, {}).setdefault(
                    (full, lab), set()).add(y)
    # phantom grouped labels: abstract OCR glue puts an article under a stale
    # group for a couple of volumes ('Animals, Living | Butter', 3 year-rows
    # vs groupless Butter's 32) — such a label both self-attests and makes the
    # article "ambiguous", vetoing the re-home of every stale-group butter
    # block. De-attest and drop as candidate any grouped label with <=3 years
    # of T1 support when a 5x-better-supported candidate exists. Genuinely
    # dual-labelled articles (Wheat: grouped 24 yrs + groupless 9) are
    # untouched.
    for akey, cands in art2commod.items():
        if len(cands) < 2:
            continue
        best = max(len(v) for v in cands.values())
        for (full, lab), yrs in list(cands.items()):
            if full != akey and len(yrs) <= 3 and best >= 5 * len(yrs):
                del cands[(full, lab)]
                t1_attested.discard(full)

    # ---- pass 1: country-level cells (imports, per-cell ranks) ----
    n_cfixed = 0
    cfix_log = Counter()
    for g, a, c, u, y, q, v, r in con.execute("""
            SELECT article_group, article, country, unit, year,
                   quantity, coalesce(value, 0), q_rank
            FROM country_year_final""").fetchall():
        base, qual = fold_group(g)
        sig = sig_of(base, qual, a)
        label = display(base, qual, a)
        # sticky-group repair, country edition: fires ONLY when the printed
        # group+article is NOT an abstract-attested commodity but the article
        # alone unambiguously names exactly one (and isn't pure qualifier
        # vocab). Ambiguous articles (Wheat: grouped-era + groupless-era both
        # attested; Cotton: fibre vs Seeds—Cotton) are left as printed.
        if sig and sig not in t1_attested and (g or '').strip() and (a or '').strip():
            art_toks = toks(a)
            cands = art2commod.get(tuple(sorted(art_toks)))
            if cands:
                # label variants of ONE commodity ('Wheatmeal and Flour' /
                # 'Wheatmeal or Flour' — same sig) are not ambiguity:
                # collapse candidates by sig, keep each sig's best-
                # supported label
                by_sig = {}
                for (csig, clabel), yrs in cands.items():
                    cur = by_sig.get(csig)
                    if cur is None or len(yrs) > cur[1]:
                        by_sig[csig] = (clabel, len(yrs))
                if len(by_sig) == 1 and art_toks - GENERIC:
                    csig, (clabel, _) = next(iter(by_sig.items()))
                    if csig != sig:
                        cfix_log[(label, clabel)] += 1
                        sig, label = csig, clabel
                        n_cfixed += 1
        if not sig:
            sig = ('(UNLABELLED)',)
        slot(sig)['v'] += min(v, 50_000_000)     # plausibility cap, sort key
        add_cell(sig, label, fold_country(c), norm_unit(u), y, q, r)

    country_sigs = set(comms)

    # ---- pass 2: Tier-1 national totals (1866-1900) ----
    RANK = {'A': 1, 'B': 2, 'C': 3}
    # groupless T1 labels are commodities in their own right
    t1_sigs = set()
    for g, a, *_ in t1_rows:
        if not (g or '').strip() and (a or '').strip():
            b, ql = fold_group(a)
            t1_sigs.add(sig_of(b, ql, None))
    known = country_sigs | t1_sigs

    n_tot = n_fixed = 0
    for g, a, u, y, q, tier in t1_rows:
        grouped = bool((g or '').strip())
        if grouped:
            base, qual = fold_group(g)
            art_toks = toks(a)
            art_sig = tuple(sorted(art_toks))
            # sticky-group repair: fires ONLY when group+article together is
            # NOT a known commodity ('Animals, Living | Butter') but the
            # article alone is, and isn't pure qualifier vocab. A correct
            # group ('Wool | Sheep and Lambs'', a known commodity) is never
            # overridden.
            if (art_sig and art_sig in known and art_toks - GENERIC
                    and sig_of(base, qual, a) not in known):
                sig, label = art_sig, display('', None, a)
                n_fixed += 1
            else:
                sig = sig_of(base, qual, a)
                label = display(base, qual, a)
        else:
            base, qual = fold_group(a)
            sig = sig_of(base, qual, None)
            label = display(base, qual, None)
        if not sig:
            continue
        add_cell(sig, label, TK, norm_unit(u), y, q, RANK.get(tier, 3))
        n_tot += 1

    # ---- sort key for T1-only commodities: voted national GBP value ----
    for g, a, y, v in con.execute("""
            SELECT article_group, article, year, value FROM consensus
            WHERE flow='import' AND measure='value' AND value > 0""").fetchall():
        if (g or '').strip():
            base, qual = fold_group(g)
            sig = sig_of(base, qual, a)
        else:
            base, qual = fold_group(a)
            sig = sig_of(base, qual, None)
        if sig in comms and comms[sig]['v'] == 0:
            comms[sig]['v'] += min(v, 50_000_000)

    # ---- coastal roll-up: some origins are printed split by shipping coast
    # ('United States of America : On the Atlantic / On the Pacific', US raw
    # cotton 1876-99) with NO parent-country row in those years, so the
    # explorer's 'United States Of America' series showed holes while the
    # data sat under the coast entries. Synthesize the parent cell as the
    # SUM of its coasts per (unit, year) wherever the parent lacks that year
    # in that unit; rank = worst component. Coast entries stay visible as
    # their own countries (drill-down detail).
    COAST_RE = re.compile(r'^(.+) \((Atlantic|Pacific|Atlantic & Pacific'
                          r'|Northern Ports|Southern Ports)\)$')
    # origin-regime changes: some aggregates stop being printed and their
    # constituent colonies take over (South African wool: 'British
    # Possessions in South Africa' 1872-90, then 'Cape of Good Hope' +
    # 'Natal' 1891+). Synthesize the aggregate from its complete
    # constituent set in years it lacks, same rules as the coast roll-up.
    CONSTITUENTS = {
        'British Possessions In South Africa': ('Cape Of Good Hope', 'Natal'),
        # per-state era (1883+): the Australasia aggregate line is not printed
        # in every table; synthesize it from the states in years it lacks.
        # NB the misfiled BP-subtotal cells (wool 1886/91/96-98, where an
        # 'Australasia' cell actually carries the whole British-Possessions
        # subtotal) are untouched by this: the roll-up only fills years where
        # the parent has NO cell at all.
        'Australasia': ('New South Wales', 'Victoria', 'Queensland',
                        'South Australia', 'Western Australia', 'Tasmania',
                        'New Zealand'),
    }
    n_coast = 0
    for s in comms.values():
        c = s['c']
        groups = {}
        for cty in list(c):
            m = COAST_RE.match(cty)
            if m:
                groups.setdefault(m.group(1), []).append(cty)
        for parent, kids in CONSTITUENTS.items():
            # kids[0] is the aggregate's defining member: require it, so a
            # lone secondary cell never synthesizes a phantom parent (a
            # commodity with only 'Hong Kong' cells must not mint a
            # 'China' series)
            present = [k for k in kids if k in c]
            if present and kids[0] in c:
                groups.setdefault(parent, []).extend(present)
        for parent, coasts in groups.items():
            pd = c.setdefault(parent, {})
            have = {u: {cell[0] for cell in cells} for u, cells in pd.items()}
            agg = {}
            for cc in coasts:
                for u, cells in c[cc].items():
                    for y, q, r in cells:
                        if y in have.get(u, ()):
                            continue          # parent already carries it
                        a = agg.setdefault((u, y), [0, 1])
                        a[0] += q
                        a[1] = max(a[1], r)
            for (u, y), (q, r) in agg.items():
                pd.setdefault(u, []).append([y, round(q), r])
                n_coast += 1

    # ---- unit healing: OCR loses/mangles the unit column, not the number.
    # Within a commodity x country, '?'-unit cells fold into the dominant
    # labeled unit when their magnitudes agree within 3x (cotton 1868-95 was
    # printed in Cwts but parsed unit-less). A LABELED minority unit folds
    # only when it is also small and clearly subordinate — a genuine unit
    # regime change (coffee's Lbs -> Cwts era, 200x apart) never folds.
    def median(vals):
        t = sorted(vals)
        return t[len(t) // 2]

    n_healed = 0
    for s in comms.values():
        for cty, units in s['c'].items():
            labeled = {u: cs for u, cs in units.items() if u != '?'}
            if not labeled:
                continue
            dom = max(labeled, key=lambda u: len(labeled[u]))
            domvals = [c[1] for c in units[dom] if c[1] > 0]
            if not domvals:
                continue
            dmed = median(domvals)
            for u in [x for x in units if x != dom]:
                cells = units[u]
                if u == '?':
                    # whole-bucket fold first (a growing series' early '?'
                    # cells sit far below the global median but share its
                    # unit — 1873 US flour is 8x below the 1890s median);
                    # if the bucket fails, rescue individual cells inside
                    # the window (jute Bengal mixed a Cwt-era 1883 cell
                    # with a Ton-era 1892 cell — only the latter folds)
                    vals = [c[1] for c in cells if c[1] > 0]
                    m = median(vals) if vals else 0
                    if m and dmed / 3 < m < dmed * 3:
                        units[dom].extend(cells)
                        del units[u]
                        n_healed += len(cells)
                        continue
                    keep, move = [], []
                    for cell in cells:
                        (move if cell[1] > 0 and dmed / 3 < cell[1] < dmed * 3
                         else keep).append(cell)
                    if move:
                        units[dom].extend(move)
                        n_healed += len(move)
                        if keep:
                            units[u] = keep
                        else:
                            del units[u]
                    continue
                vals = [c[1] for c in cells if c[1] > 0]
                if not vals:
                    continue
                m = median(vals)
                if not (dmed / 3 < m < dmed * 3):
                    continue
                if not (len(cells) <= 5
                        and len(units[dom]) >= 2 * len(cells)):
                    continue
                units[dom].extend(cells)
                del units[u]
                n_healed += len(cells)
    for s in comms.values():                     # better rank first per year
        for units in s['c'].values():
            for cells in units.values():
                cells.sort(key=lambda c: (c[0], c[2]))

    # ---- fuzzy merge: same commodity, OCR-mangled token ----
    # two signatures merge when they have the same token count and every
    # token pairs up either exactly or within edit distance 2 (len >= 5):
    # {ALPACA,LLAMA,VICUNA,WOOL} == {ALPACA,LLAMA,VLONNA,WOOL}.
    def edist_le2(a, b):
        if abs(len(a) - len(b)) > 2:
            return False
        prev = list(range(len(b) + 1))
        for i, ca in enumerate(a, 1):
            cur = [i]
            for j, cb in enumerate(b, 1):
                cur.append(min(prev[j] + 1, cur[-1] + 1,
                               prev[j - 1] + (ca != cb)))
            if min(cur) > 2:
                return False
            prev = cur
        return prev[-1] <= 2

    def fuzzy_same(s1, s2):
        if len(s1) != len(s2):
            return False
        rest = list(s2)
        for t in s1:
            if t in rest:
                rest.remove(t)
                continue
            hit = next((r for r in rest if len(t) >= 5 and len(r) >= 5
                        and t[0] == r[0] and edist_le2(t, r)), None)
            if hit is None:
                return False
            rest.remove(hit)
        return True

    by_shape = {}
    for sig in comms:
        by_shape.setdefault((len(sig), tuple(sorted(len(t) // 3 for t in sig))),
                            []).append(sig)
    merged_into = {}
    for bucket in by_shape.values():
        bucket.sort(key=lambda s: -comms[s]['v'])
        for i, s1 in enumerate(bucket):
            if s1 in merged_into:
                continue
            for s2 in bucket[i + 1:]:
                if s2 in merged_into or s1 == s2:
                    continue
                if fuzzy_same(s1, s2):
                    merged_into[s2] = s1
    n_fuzzy = len(merged_into)
    for src, dst in merged_into.items():
        d, s = comms[dst], comms.pop(src)
        d['v'] += s['v']
        d['labels'].update(s['labels'])
        for cty, units in s['c'].items():
            for u, cells in units.items():
                d['c'].setdefault(cty, {}).setdefault(u, []).extend(cells)

    # ---- emit: display label = most common printed rendering ----
    payload = {}
    for sig, s in comms.items():
        label = s['labels'].most_common(1)[0][0]
        if label in payload:                     # rare display collision
            label = f'{label} ({" ".join(sig)[:24]})'
        payload[label] = {'v': round(s['v']), 'c': s['c']}
    js = json.dumps(payload, separators=(',', ':')).replace('</', '<\\/')
    out.write_text(js)
    if cfix_log:
        print(f'country-cell sticky repairs ({n_cfixed:,} cells, '
              f'{len(cfix_log)} distinct label mappings):')
        for (old, new), n in cfix_log.most_common():
            print(f'  {n:5d}  {old}  ->  {new}')
    print(f'commodities: {len(payload)}  T1 cells: {n_tot:,} '
          f'(sticky repaired: {n_fixed:,}; fuzzy-merged: {n_fuzzy}; '
          f'unit-healed: {n_healed:,}; coast-rollup: {n_coast:,})  '
          f'MB: {len(js) / 1e6:.2f}  -> {out}')


if __name__ == '__main__':
    main()
