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
import csv
import json
import re
import sys
from collections import Counter, defaultdict
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
    # A label WHOLLY wrapped in brackets is the parenthesised variant of a
    # country ('(Straits Settlements)'). A TRAILING bracketed qualifier is
    # not: 'Gold Coast (including Lagos)'. strip('()') ate only the closing
    # bracket of the second kind, leaving 'Gold Coast (including Lagos' —
    # and an unbalanced '(' makes every consumer treat the cell as a
    # drill-down and drop it (palm oil 1885-90 lost its largest origin that
    # way, four years running). V.cnorm already removes the brackets on the
    # consensus path; this makes the raw-label paths agree with it.
    if c.startswith('(') and c.endswith(')'):
        c = c[1:-1].strip()
    else:
        c = c.replace('(', ' ').replace(')', ' ').strip()
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
    # 'Parts' is an OCR misread of 'Ports': as_1897 prints bacon's Russian
    # line as 'From Russia : / Northern Parts' (the parent row carries the
    # unit labels, so the parser dropped the colon parent) and as_1898/99
    # print the SAME figures as plain 'Russia' — 19,001/35,421 in 1896 and
    # 27,713/59,953 in 1897, to the digit. Without the fold it survives as a
    # phantom country that double-counts Russia. The string appears in
    # exactly 5 cells corpus-wide (BACON, as_1897, 1893-97); 'watches and
    # parts thereof' never matches — the pattern is fully anchored.
    m = re.match(r'^(?:russia[,:\s]+)?(northern|southern)\s+'
                 r'(?:ports?|parts?)(?:\s+of)?$', c, re.I)
    if m:
        p = _parent_norm(parent) if parent else 'Russia'
        return f'{p} ({m.group(1).title()} Ports)'
    # China scope labels fold to 'China': pre-1885 tables print the
    # inclusive 'China and Hong Kong' (plain-China years then mean the
    # same); from 1885 Hong Kong gets its own line, so 'China (exclusive
    # of Hong Kong)' means what plain 'China' means in the neighbouring
    # years (silk 1886: 1,217,002 excl. sits between 1885's 1,444,960 and
    # 1887's 1,416,660 — both exclusive-era plain-China lines)
    # 1884-era tables widen the scope label to 'China, Hong Kong, and Macao'
    # (tea): same fold — plain-China neighbours mean the same thing
    if re.match(r'^china(?:,| and) hong\s*kong(?:,? and macao)?$'
                r'|^china \(?exclusive of hong\s*kong\)?$', c, re.I):
        return 'China'
    # British India presidency labels: some volumes lose the parent colon
    # ('British India Bombay and Scinde' as one string) — strip the stale
    # prefix like the sub-entry split would. The Bombay customs region is
    # printed 'Bombay and Scinde' (Scinde shipped via Karachi under the
    # Bombay presidency) until ~1890, then plain 'Bombay': one entity —
    # the split showed as wool holes 1877/81. 'Bengal and Burmah' is NOT
    # folded to Bengal: Burma is printed separately in later regimes.
    c = re.sub(r'^british india[,:]?\s+'
               r'(?=(?:bombay|madras|bengal|burmah|scinde)\b)', '', c,
               flags=re.I)
    # 'soinde' = OCR garble of Scinde (wheat 1889); bare 'Scinde' = the
    # same row with 'Bombay and' truncated (wheat 1884) — never a
    # separate customs line in these tables.
    if re.match(r'^bombay(?: and s[co]inde)?$|^scinde$', c, re.I):
        return 'Bombay'
    # match the integrate-level alias: consensus rows already land as
    # 'canada'; groupfix/manual rows keep the printed 'British North
    # America' and must join the same series (seal skins 1876-86).
    if re.match(r'^british north america$', c, re.I):
        return 'Canada'
    # 'British West Indies' and 'British West India Islands' are the same
    # printed entity (short vs long form, era-dependent); 45 commodities
    # carried both as split series (cocoa raw 1887-90 vs 1891-99).
    if re.match(r'^british west ind(?:ies|ia islands?)$', c, re.I):
        return 'British West India Islands'
    return c.title() if c else '?'


_UNIT_ALIAS = {
    'cwt': 'Cwt', 'cwts': 'Cwt', 'cuts': 'Cwt', 'cts': 'Cwt', 'cwis': 'Cwt',
    'cwtts': 'Cwt', 'gwts': 'Cwt', 'owts': 'Cwt', 'wts': 'Cwt', 'cwt s': 'Cwt',
    'ccts': 'Cwt', 'cicts': 'Cwt', 'cets': 'Cwt', 'ccwts': 'Cwt',
    # Each of these was found sitting BESIDE its canonical form on the same
    # commodity, splitting one national series into two unit keys - which
    # matters because the map's anchor has to be a single unit, so the half in
    # the misread key was invisible. 'Cnts' carried the whole 1893-1900 anchor
    # for the beetroot, cane and glucose sugar lines while their origins were
    # in Cwt; it is the same figure to the digit where both are printed
    # ('Sugar - Other Sorts, Including Candy' 1896-98).
    'cnts': 'Cwt', 'cwtz': 'Cwt', 'cwtss': 'Cwt', 'ciots': 'Cwt',
    'lb': 'Lb', 'lbs': 'Lb', 'lbds': 'Lb',
    # compound column headers take the leading unit, as 'tons cwts' already does
    'lbs ozs': 'Lb', 'lbs oz': 'Lb',
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
    'dozen pairs': 'Dozen Pairs', 'doz pairs': 'Dozen Pairs',
    'doz prs': 'Dozen Pairs',   # 'Pairs' alone is NOT this: it is 12x smaller
    'tun': 'Tun', 'tuns': 'Tun',
    'great hundred': 'Great Hundred', 'great hundreds': 'Great Hundred',
    'gt hundreds': 'Great Hundred', 'gt hunds': 'Great Hundred',
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
    # refined-sugar subsection heading glue: the printed line is 'Other
    # Sorts, including Candy' under a 'Refined:—' (or 'Refined, or rendered
    # by any process equal thereto:') heading; several volumes glue the
    # heading — or the SIBLING subsection 'In Lumps and Loaves' — onto the
    # article, splitting one series across four sigs (Germany 1886/87/92
    # showed as holes). Only sugar prints this tail, so the fold is safe.
    # Done here (not sig_of) so the sticky-repair akey/art_toks fold too.
    if {'CANDY', 'SORTS', 'INCLUDING', 'OTHER'} <= out:
        out -= {'REFINED', 'RENDERED', 'ANY', 'BY', 'PROCESS', 'EQUAL',
                'THERETO', 'IN', 'LUMPS', 'LOAVES', 'SUGAR'}
    # OCR continuation markers ('Flax or Linseed Cont', 'COTTON
    # MANUFACTURES—con- tinued') are page furniture, never meaning
    if out & {'CONT', 'CONTD', 'CONTINUED', 'TINUED'}:
        if 'TINUED' in out:
            out.discard('CON')
        out -= {'CONT', 'CONTD', 'CONTINUED', 'TINUED'}
    # flax/linseed is ONE commodity: T1 prints it under 'Seeds' 1869-91
    # and groupless 1890+, the country tables carry a stale 'COTTON'
    # column-top group — the two-era T1 attestation made the article
    # look ambiguous, so the sticky repair never merged them (Bengal
    # showed as holes 1888/90/91/92)
    if {'FLAX', 'LINSEED'} <= out:
        out -= {'SEEDS', 'COTTON'}
    # sawn-wood section heading evolves: 'Sawn, Fir' (to 1891) vs 'Sawn
    # or Split, planed or dressed, Fir' (1893+) are the same printed
    # line under a grown heading — Sweden/Russia showed as 1893/95 holes
    if 'SAWN' in out:
        out -= {'SPLIT', 'PLANED', 'DRESSED'}
    # woollen-yarn label era: 'For Weaving' (1878-92) grows to 'For Weaving,
    # Mixed or not with Silk' (1893+) — same printed series (Belgium showed
    # as 1894/95 holes). Only yarn prints a WEAVING article, so this is safe.
    if 'WEAVING' in out:
        out -= {'MIXED', 'SILK'}
    # condensed-milk label era: 'Milk, Condensed' (1888-91 own-year tables,
    # 1892 manual rows) vs 'Milk, Condensed or Preserved' (1893+ comparative
    # era) are one printed series — France/Holland showed as 1892/93 holes.
    # The fresh-milk commodity ('Milk and Cream, Fresh or Preserved, other
    # than Condensed Milk') keeps its identity via CREAM/FRESH tokens.
    if {'MILK', 'CONDENSED'} <= out and 'CREAM' not in out:
        out.discard('PRESERVED')
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


# ---- shifted-duplicate dedupe: the SAME printed row parsed twice ----
# The dedupe above keys on (country, unit, year), so it cannot see a
# duplicate that landed under a different country or a different unit —
# and that is what a second parse of the same table produces. The unit
# header is lost, and the country column comes out misaligned:
#
#   teak 1876   Bengal And Burmah  Load 34,416 / 407,444
#               Straits Settlements   ?  34,416 / 407,444   <- same row
#   teak 1876   Straits Settlements Load    810 /   9,088
#               Other Countries       ?     810 /   9,088   <- same row
#
# Both the quantity AND the value match to the digit, which is what makes
# this safe to act on: two genuinely different origins agreeing on both
# numbers in the same year does not happen. The same fingerprint also
# catches the milder case where the country is merely spelled differently
# ('Mauritius' / 'Mauritius And Dependencies', 'French Possessions' /
# 'French') rather than slipped outright.
#
# The labelled copy is kept. It is the one that still has its unit, and
# where the two disagree about the country it is also the one that is
# right: teak's bulk belongs to Bengal And Burmah, not to the Straits
# entrepot or to Bombay on the wrong coast of India. Quantity was already
# safe (consumers take the dominant unit) but VALUE summed both copies.
def drop_shifted_duplicates(payload):
    """Drop '?'-unit cells that repeat a labelled cell's qty AND value in the
    same commodity-year. The country may be the same (the second parse only
    lost the unit header) or different (it lost the column alignment too);
    either way the row is already carried by the labelled copy. Returns the
    dropped rows for the audit log."""
    dropped = []
    for name, e in payload.items():
        cd = e.get('c') or {}
        seen = {}                    # (year, qty, value) -> country
        for cty, units in cd.items():
            if cty == '\u00a7TOTAL':
                continue
            for u, cells in units.items():
                if u == '?':
                    continue
                for c in cells:
                    if len(c) > 3 and c[1] and c[3]:
                        seen[(c[0], c[1], c[3])] = cty
        for cty, units in list(cd.items()):
            if cty == '\u00a7TOTAL' or '?' not in units:
                continue
            keep, out = [], []
            for c in units['?']:
                k = (c[0], c[1], c[3]) if len(c) > 3 else None
                dup = bool(k) and k in seen
                # Same country: a duplicate however small - it is the same
                # place, the same year, the same two numbers. A DIFFERENT
                # country needs the pair to be distinctive before it counts as
                # evidence, because two unrelated origins really can both ship
                # 1 unit for GBP5 in the same year; below the floor the pair
                # proves nothing and the cell is left alone.
                if dup and seen[k] != cty and (c[3] < 100 or c[1] < 10):
                    dup = False
                (out if dup else keep).append(c)
            if not out:
                continue
            dropped.extend((name, c[0], cty, seen[(c[0], c[1], c[3])], c[1], c[3])
                           for c in out)
            if keep:
                units['?'] = keep
            else:
                del units['?']
            if not units:
                del cd[cty]
    return dropped


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / 'exports' / 'viz_payload.json'
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)
    comms = {}          # sig -> {'v': gbp, 'labels': Counter, 'c': {cty:{unit:[cells]}}}

    def slot(sig):
        return comms.setdefault(sig, {'v': 0, 'labels': Counter(), 'c': {}})

    def add_cell(sig, label, cty, unit, y, q, r, v=0, weight=1):
        # cells carry a 4th element, per-country-year VALUE (GBP), used only
        # by the map export; viz_payload.json strips it back to [y,q,r].
        s = slot(sig)
        s['labels'][label] += weight
        s['c'].setdefault(cty, {}).setdefault(unit, []).append(
            [int(y), round(float(q)), int(r), round(float(v))])

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

    # ---- absorbed siblings: two printed sub-sorts collapsing to one key ----
    # sig_of unions the group and article tokens, so an article that only
    # repeats a word already in its group heading contributes NOTHING and
    # vanishes into the group. That is deliberate almost everywhere — it is
    # what makes 'Sawn, Fir' and 'Sawn : Fir' one commodity, and 104
    # signatures currently carry more than one printed article for exactly
    # that reason. It is catastrophic in the one case where the two absorbed
    # articles are DIFFERENT COMMODITIES: 'BACON AND HAMS | Bacon' and
    # 'BACON AND HAMS | Hams' both key on ('BACON','HAMS'), so the two tables
    # merge, and because add_cell dedupes on (country, unit, year) — and the
    # bacon and ham tables list the same origins in the same year — the ham
    # cell is DISCARDED. Twenty-three years of ham origin tables were being
    # destroyed, and the survivor was measured against the combined
    # 'Bacon and Hams' national total, so it read 0.75-0.93 for its whole
    # life and no flag could see why. (Proof it is one line split in two:
    # bacon + hams country sums equal the printed combined total to the digit
    # in thirteen years, and within 0.2% in six more.)
    #
    # The discriminator has to separate this from the 103 benign cases. Two
    # articles under one signature are the SAME printed line, spelled two
    # ways, iff their vocabularies overlap ("Sheep or Lambs'" vs "Sheep or
    # Lambs' Wool", 'Ore' vs 'Ore of'). They are different lines iff their
    # meaningful vocabularies are DISJOINT and the volumes print both IN THE
    # SAME YEAR. Run over the whole corpus that fires on BACON AND HAMS and
    # on nothing else; it is a general rule that currently has one member.
    split_sigs = set()
    _bysig = {}
    for g, a, y in con.execute("""
            SELECT DISTINCT article_group, coalesce(article, ''), year
            FROM country_year_final
            WHERE flow='import' AND coalesce(article_group, '') <> ''""").fetchall():
        base, qual = fold_group(g)
        _bysig.setdefault((base, qual, sig_of(base, qual, a)), {}).setdefault(
            frozenset(toks(a) - GENERIC), set()).add(y)
    for key, byvocab in _bysig.items():
        vocabs = [v for v in byvocab if v]
        for i, vi in enumerate(vocabs):
            for vj in vocabs[i + 1:]:
                if not (vi & vj) and len(byvocab[vi] & byvocab[vj]) >= 2:
                    split_sigs.add(key)

    def article_marker(a):
        """A token that keeps an absorbed article load-bearing, and only it."""
        return '~' + '+'.join(sorted(toks(a) - GENERIC))

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
        if (base, qual, sig) in split_sigs and toks(a) - GENERIC:
            sig = sig + (article_marker(a),)
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
        add_cell(sig, label, fold_country(c), norm_unit(u), y, q, r, v)

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

    # ---- the printed national VALUE line, carried on the §TOTAL cell ----
    # Every block in the Abstract prints two columns and two printed totals,
    # and until now only the quantity one was ever tested. The value anchor
    # rides on the §TOTAL cell's 4th element (the same slot the country cells
    # use for their value), so value closure can be measured in exactly the
    # curated space quantity closure is measured in. viz_payload.json strips
    # the 4th element, so its schema is unchanged.
    t1val, _vart = {}, {}
    for g, a, y, v in con.execute("""
            SELECT article_group, article, year, value FROM consensus
            WHERE flow='import' AND measure='value' AND value > 0""").fetchall():
        if (g or '').strip():
            base, qual = fold_group(g)
            vsig = sig_of(base, qual, a)
        else:
            base, qual = fold_group(a)
            vsig = sig_of(base, qual, None)
        # ALSO key every value line on its article's tokens alone. The two
        # columns of one printed line routinely land under different group
        # headings — essential oils are quantified under 'Oil | Chemical,
        # Essential, and Perfumed' and valued under a groupless 'Chemical,
        # Essential, and Perfumed' in almost every year — so a signature
        # built from the group can only pair them when both copies happen to
        # carry it. Restricted to article-years with ONE distinct value, so a
        # generic article printed under several commodities is never paired.
        akey_v = tuple(sorted(toks(a)))
        if akey_v:
            _vart.setdefault((akey_v, y), []).append(v)
        if vsig:
            t1val.setdefault((vsig, y), v)      # first printing wins, as before
    for k, vs in _vart.items():
        if len(set(vs)) == 1:                   # unambiguous article-year
            t1val.setdefault(k, vs[0])

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
        add_cell(sig, label, TK, norm_unit(u), y, q, RANK.get(tier, 3),
                 t1val.get((sig, y))
                 or t1val.get((tuple(sorted(toks(a))), y), 0))
        n_tot += 1

    # ---- sort key for T1-only commodities: voted national GBP value ----
    for (vsig, _y), v in t1val.items():
        if vsig in comms and comms[vsig]['v'] == 0:
            comms[vsig]['v'] += min(v, 50_000_000)

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
    synth = {}          # id(commodity) -> {(parent, unit, year)} the roll-up made
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
                    for y, q, r, *rest in cells:
                        if y in have.get(u, ()):
                            continue          # parent already carries it
                        a = agg.setdefault((u, y), [0, 1, 0])
                        a[0] += q
                        a[1] = max(a[1], r)
                        a[2] += rest[0] if rest else 0
            for (u, y), (q, r, v) in agg.items():
                pd.setdefault(u, []).append([y, round(q), r, round(v)])
                synth.setdefault(id(s), set()).add((parent, u, y))
                n_coast += 1

    # ---- the bare parent that is really one coast. Every consumer treats a
    # '(coast)' cell as drill-down detail inside its parent and sums the
    # parent only. That is right when the parent is the printed aggregate —
    # and wrong when the parser gave ONE coast its bare country name and
    # qualified the other, which is what 'Russia : Northern Ports / Southern
    # Ports' does in the 1880-83 flax tables: 'Russia' 597,454 IS the northern
    # row, and 'Russia (Southern Ports)' 442,058 was being dropped as
    # redundant to it. Flax and linseed read 0.82-0.92 for four years with
    # country_year_final summing to its printed total TO THE DIGIT.
    # Told apart the only way that cannot guess: fold the coasts into the
    # parent cell ONLY when doing so brings the year CLOSER to its printed
    # national total (heal_by_anchor's rule). A parent that really is the
    # aggregate overshoots and is left alone.
    n_sib = 0
    for s in comms.values():
        c = s['c']
        anch = {}
        for u, cells in (c.get(TK) or {}).items():
            for cell in cells:
                if cell[1]:
                    anch[(u, cell[0])] = cell[1]
        if not anch:
            continue
        groups = {}
        for cty in list(c):
            m = COAST_RE.match(cty)
            if m and m.group(1) in c:
                groups.setdefault(m.group(1), []).append(cty)
        if not groups:
            continue
        # the year's origin sum AS CONSUMERS SEE IT: parents only, drill-down
        # '(coast)' cells excluded. That, not the parent cell alone, is what
        # has to move closer to the printed total.
        seen = {}
        for cty, byu in c.items():
            if cty == TK or '(' in cty:
                continue
            for u, cells in byu.items():
                for cell in cells:
                    seen[(u, cell[0])] = seen.get((u, cell[0]), 0) + cell[1]
        for parent, coasts in groups.items():
            kid = {}
            for cc in coasts:
                for u, cells in c[cc].items():
                    for y, q, r, *rest in cells:
                        a = kid.setdefault((u, y), [0, 1, 0])
                        a[0] += q
                        a[1] = max(a[1], r)
                        a[2] += rest[0] if rest else 0
            for u, cells in c[parent].items():
                for cell in cells:
                    k = (u, cell[0])
                    add = kid.get(k)
                    t1 = anch.get(k)
                    tot = seen.get(k)
                    if not add or not t1 or not add[0] or not tot:
                        continue
                    if (parent, u, cell[0]) in synth.get(id(s), ()):
                        continue     # this parent cell IS the coast sum
                    if abs(cell[1] - add[0]) <= 0.01 * add[0]:
                        continue     # parent already equals its coasts
                    if abs(tot + add[0] - t1) < abs(tot - t1):
                        cell[1] += round(add[0])
                        cell[2] = max(cell[2], add[1])
                        if len(cell) > 3:
                            cell[3] += round(add[2])
                        seen[k] = tot + add[0]
                        n_sib += 1

    # ---- Tun and Ton are one OCR-confusable pair, not two units (u/o). The
    # oils are printed in TUNS and the two engines alternate almost year by
    # year — 'Oil: Olive' reads Ton in 1872, Tun in 1873, Ton in 1874 — so half
    # a commodity's origins never share a unit key with its own T1 line and the
    # map's quantity axis drops them without saying so. heal_units cannot see
    # it: the split is by YEAR across all countries, so no country has a
    # minority unit to fold. No article in these tables is printed in both, so
    # within ONE commodity the two spellings are the same unit. Fold to
    # whichever is better attested across the commodity, anchor included.
    def fold_tun_ton(store):
        n = 0
        for s in store.values():
            cnt = Counter()
            for cty, units in s['c'].items():
                for u in ('Tun', 'Ton'):
                    cnt[u] += len(units.get(u, ()))
            if not (cnt['Tun'] and cnt['Ton']):
                continue
            keep = 'Tun' if cnt['Tun'] >= cnt['Ton'] else 'Ton'
            drop_u = 'Ton' if keep == 'Tun' else 'Tun'
            for cty, units in s['c'].items():
                if drop_u in units:
                    # skip a year the keep-unit already has: where the
                    # national line was printed under BOTH spellings in one
                    # year, appending blindly leaves two §TOTAL cells for that
                    # year, and build_map_slim used to add them — which
                    # doubled the anchor and made 'Oil — Fish : Train Or
                    # Blubber' read exactly 0.500 in 1894, 1895 and 1896.
                    # Same contract as the curation fold: existing cell wins.
                    have = {row[0] for row in units.get(keep, ())}
                    units.setdefault(keep, []).extend(
                        r for r in units.pop(drop_u) if r[0] not in have)
                    n += 1
        return n

    n_tunton = fold_tun_ton(comms)

    # ---- unit healing: OCR loses/mangles the unit column, not the number.
    # Within a commodity x country, '?'-unit cells fold into the dominant
    # labeled unit when their magnitudes agree within 3x (cotton 1868-95 was
    # printed in Cwts but parsed unit-less). A LABELED minority unit folds
    # only when it is also small and clearly subordinate — a genuine unit
    # regime change (coffee's Lbs -> Cwts era, 200x apart) never folds.
    def median(vals):
        t = sorted(vals)
        return t[len(t) // 2]

    def heal_by_anchor(store):
        """Fold a year's unit-less cells into the dominant unit when that
        moves the year closer to its own printed national total.

        Run inside heal_units AND again after commodity curation: a fold
        brings in countries the target has no labelled cell for, so the
        per-country tests cannot reach them. Palm oil 1888 gained Lagos
        (which the target does have, so it was relabelled at fold time) but
        not 'Nated', 412,183 cwt of the same West African trade under a
        mangled name, and the year stopped at 0.56 instead of 1.00.
        """
        n_healed = 0
        for s in store.values():
            ucnt = Counter()
            for cty, units in s['c'].items():
                if cty == TK:
                    continue
                for u, cs in units.items():
                    if u != '?':
                        ucnt[u] += len(cs)
            dom_all = ucnt.most_common(1)[0][0] if ucnt else None
            # Last resort, decided a YEAR at a time against the commodity's own
            # printed national total. The per-country tests above compare a
            # country's unit-less cells with its own labelled ones, and a
            # genuine collapse in one origin's trade defeats them: palm oil's
            # Portuguese Possessions ships 878,548 unit-less in 1874 and 600 to
            # 42,100 labelled in the 1890s, two hundred times apart, so the
            # magnitude guard reads a unit change where there was only the
            # Niger and Lagos trade taking over. The year's arithmetic settles
            # it - 1874's labelled cells alone come to 32,633 against an anchor
            # of 1,067,767, and adding the unit-less ones gives 1,067,767 to the
            # digit. So: fold a year's unit-less cells into the dominant unit
            # when doing that moves the year CLOSER to its anchor, and not
            # otherwise. A cell that is really in some other unit overshoots and
            # is left alone.
            anchor = {}
            for cell in s['c'].get(TK, {}).get(dom_all, []) if dom_all else ():
                anchor[cell[0]] = anchor.get(cell[0], 0) + cell[1]
            if anchor:
                lab = Counter()
                unl = Counter()
                for cty, units in s['c'].items():
                    if cty == TK:
                        continue
                    for cell in units.get(dom_all, ()):
                        lab[cell[0]] += cell[1]
                    for cell in units.get('?', ()):
                        unl[cell[0]] += cell[1]
                fix = {y for y, q in unl.items()
                       if q and anchor.get(y, 0) > 0
                       and abs(lab[y] + q - anchor[y]) < abs(lab[y] - anchor[y])}
                for cty, units in s['c'].items():
                    if cty == TK or '?' not in units:
                        continue
                    move = [c for c in units['?'] if c[0] in fix and c[1] > 0]
                    if not move:
                        continue
                    rest = [c for c in units['?'] if c not in move]
                    units.setdefault(dom_all, []).extend(move)
                    n_healed += len(move)
                    if rest:
                        units['?'] = rest
                    else:
                        del units['?']
        return n_healed

    def heal_units(store):
        """Fold '?'-unit cells into the country's dominant labelled unit.

        Run once over the raw signatures and AGAIN after commodity curation:
        a fold can hand a commodity a country whose cells are unit-less while
        the target's are labelled, which is exactly this situation arriving
        late. "Wool - Sheep Or Lambs'" is the case that forced it - the
        colonial wool for 1897-99 (Australasia, New South Wales, New Zealand,
        the Cape) sits under the de-headed label 'Wool' with no unit, so
        folding alone moved the cells in but left them invisible to the
        quantity axis, which only counts the dominant unit.
        """
        n_healed = 0
        for s in store.values():
            # the commodity's dominant labelled unit, across every country -
            # the one the map's quantity axis will use
            ucnt = Counter()
            for cty, units in s['c'].items():
                if cty == TK:
                    continue
                for u, cs in units.items():
                    if u != '?':
                        ucnt[u] += len(cs)
            dom_all = ucnt.most_common(1)[0][0] if ucnt else None
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
                    if 'Value' in (u, dom):
                        # 'Value' is a MEASURE, not a unit: a GBP figure can
                        # sit within 3x of a quantity (any commodity priced
                        # near GBP1/unit), so the magnitude folds here would
                        # merge the two axes. Only the anchor-guarded
                        # heal_by_anchor may move '?' cells into a Value
                        # series — it demands the year's own arithmetic
                        # improve against the printed total.
                        continue
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
                        # per-cell rescue tests against the NEAREST labeled
                        # year, not the global median: butter Sweden's '?'
                        # cells are all 1872-81 (20-70k) while the labeled
                        # bucket's median sits in the 1890s (230k) — era-local
                        # comparison is the honest test
                        dom_by_year = {}
                        for cell in units[dom]:
                            dom_by_year.setdefault(cell[0], cell[1])
                        def _ref(y0):
                            for dy in range(4):
                                for yy in (y0 - dy, y0 + dy):
                                    if dom_by_year.get(yy):
                                        return dom_by_year[yy]
                            return dmed
                        keep, move = [], []
                        for cell in cells:
                            ref = _ref(cell[0])
                            (move if cell[1] > 0 and ref / 3 < cell[1] < ref * 3
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
            n_healed += heal_by_anchor({'x': s})
        return n_healed

    n_healed = heal_units(comms)

    # ---- the regional aggregate printed BESIDE its own members. The mirror
    # image of the roll-up above: 'British East Indies' is the printed total of
    # the presidencies, and where the parser loses the sub-entry colon the
    # members come through as plain countries, so the year counts India twice.
    # Indigo 1885 is the clean specimen — Bengal 64,629 + Madras 17,648 +
    # Bombay 134 + Ceylon 1,561 = 83,972 against a 'British East Indies' cell
    # of 83,979, and the year sums to 176,591 against a printed 94,314. Drop
    # the parent and it is 94,314 to the digit. Measured over the corpus: of
    # 302 commodity-years where the parent shares a year with a member and a
    # printed total exists, dropping the parent moves 290 CLOSER and 12
    # further, and years landing within 0.1% go from 5 to 116.
    # Told apart the only way that cannot guess — the same rule as the coast
    # fold above: drop the parent ONLY where doing so brings the year closer to
    # its own printed national total. A parent that really is an unenumerated
    # residual beside named members overshoots when removed and is left alone,
    # and a year with no printed total is never touched.
    AGGREGATES = {
        'British East Indies': ('Bengal', 'Bengal And Burmah', 'Bombay',
                                'Madras', 'Ceylon', 'Burmah',
                                'Straits Settlements',
                                'Other British East Indian Possessions'),
        'British Possessions In South Africa': ('Cape Of Good Hope', 'Natal'),
        'Australasia': ('New South Wales', 'Victoria', 'Queensland',
                        'South Australia', 'Western Australia', 'Tasmania',
                        'New Zealand'),
    }
    # Run TWICE: once here, and again after the curation folds, because the
    # pass is anchor-guarded and an ORPHAN has no anchor. `Dye Stuffs, And
    # Substances Used In Tanning — Indigo` reads 1.9x its true total for this
    # exact reason and cannot be cleaned until a fold has put its cells under
    # a label that carries a printed one.
    def drop_aggregate_beside_members(store):
        n = 0
        for s in store.values():
            c = s['c']
            anch = {}
            for u, cells in (c.get(TK) or {}).items():
                for cell in cells:
                    if cell[1]:
                        anch[(u, cell[0])] = cell[1]
            if not anch:
                continue
            seen = {}
            for cty, byu in c.items():
                if cty == TK or '(' in cty:
                    continue
                for u, cells in byu.items():
                    for cell in cells:
                        seen[(u, cell[0])] = seen.get((u, cell[0]), 0) + cell[1]
            for parent, members in AGGREGATES.items():
                if parent not in c:
                    continue
                kid = {}
                for m in members:
                    for u, cells in (c.get(m) or {}).items():
                        for cell in cells:
                            kid[(u, cell[0])] = kid.get((u, cell[0]), 0) + cell[1]
                for u, cells in list(c[parent].items()):
                    keep = []
                    for cell in cells:
                        k = (u, cell[0])
                        t1, tot = anch.get(k), seen.get(k)
                        if not kid.get(k) or not t1 or not tot:
                            keep.append(cell)
                            continue
                        if abs(tot - cell[1] - t1) < abs(tot - t1):
                            seen[k] = tot - cell[1]
                            n += 1
                        else:
                            keep.append(cell)
                    if keep:
                        c[parent][u] = keep
                    else:
                        del c[parent][u]
                if not c[parent]:
                    del c[parent]
        return n


    # ---- one printed table whose rows landed under several unit labels. The
    # year's cells are all in the SAME measure and only the labels differ, so
    # the raw sum across unit keys is the printed national total EXACTLY -
    # which is the proof, because genuinely mixed measures cannot do that (a
    # Ton figure is a twentieth of its Cwt equivalent; adding them and landing
    # on the total to the digit does not happen by chance). `Metal - Wrought Or
    # Manufactured` 1874 is the specimen: Cwt 119,515 + unitless 872,745 + Ton
    # 61,759 = 1,054,019, the printed figure, while the year reads 0.11 because
    # only the Cwt eighth is counted. `Jute` 1883 is the same shape and worse -
    # 116 against a printed 7,385,028.
    #
    # heal_units cannot see this: its magnitude test compares a country's
    # minority unit against that country's OWN majority, and here the whole
    # year is split, so no country has a majority to fold toward.
    #
    # EXACT equality only, never "close". A near miss is noise plus a
    # coincidence, and this pass rewrites units - the most expensive thing to
    # get wrong. Measured on the corpus: 14 commodity-years qualify, 5 more
    # come within 0.1% and are deliberately left alone.
    def heal_split_year_units(store):
        n = 0
        for s in store.values():
            c = s['c']
            t1 = c.get(TK)
            if not t1:
                continue
            unit = max(t1, key=lambda u: len(t1[u]))
            anch = {cell[0]: cell[1] for cell in t1[unit] if cell[1]}
            per_year = {}
            for cty, byu in c.items():
                if cty == TK or '(' in cty:
                    continue
                for u, cells in byu.items():
                    for cell in cells:
                        if cell[1]:
                            per_year.setdefault(cell[0], []).append((cty, u, cell))
            for y, items in per_year.items():
                t = anch.get(y)
                if not t or len({u for _, u, _ in items}) < 2:
                    continue
                in_unit = sum(cell[1] for _, u, cell in items if u == unit)
                total = sum(cell[1] for _, _, cell in items)
                if in_unit >= t or round(total) != round(t):
                    continue
                moves = [(cty, u, cell) for cty, u, cell in items if u != unit]
                # a country that already holds an anchor-unit cell for this
                # year would collide: two printed rows, not one mislabelled
                # one. Abandon the whole year rather than merge them.
                held = {cty for cty, u, _ in items if u == unit}
                if any(cty in held for cty, _, _ in moves):
                    continue
                for cty, u, cell in moves:
                    c[cty][u] = [x for x in c[cty][u] if x is not cell]
                    if not c[cty][u]:
                        del c[cty][u]
                    c[cty].setdefault(unit, []).append(cell)
                    n += 1
        return n

    n_agg = drop_aggregate_beside_members(comms)

    # ---- the anchor that lost its unit. `Bark - For Tanners' Or Dyers' Use`
    # prints a Tier-1 series with NO unit on it while its own country cells are
    # Cwt, so reconcile_baseline compares an unitless total against an unitless
    # origin sum of zero and the commodity scores nothing in any year - even
    # where the countries already sum to the printed figure exactly. Measured:
    # 15 commodities, 105 commodity-years, 16 of them already agreeing to the
    # digit behind the missing label.
    #
    # The origins' unit is real information (it was printed on the column); the
    # anchor's is what went missing. So the anchor takes the origins' unit -
    # never the reverse. Guarded by agreement: at least TWO years must already
    # match to the digit, the same refusal of single coincidences the orphan
    # matcher uses. A commodity whose countries do not agree with its own total
    # in two separate years has something else wrong with it and is left alone.
    def unit_the_anchor(store):
        n = 0
        for s in store.values():
            c = s['c']
            t1 = c.get(TK)
            if not t1 or '?' not in t1:
                continue
            if max(t1, key=lambda u: len(t1[u])) != '?':
                continue
            anch = {cell[0]: cell[1] for cell in t1['?'] if cell[1]}
            if not anch:
                continue
            org = {}
            for cty, byu in c.items():
                if cty == TK or '(' in cty:
                    continue
                for u, cells in byu.items():
                    if u == '?':
                        continue
                    d = org.setdefault(u, {})
                    for cell in cells:
                        if cell[1]:
                            d[cell[0]] = d.get(cell[0], 0) + cell[1]
            if not org:
                continue
            best = max(org, key=lambda u: len(org[u]))
            agree = sum(1 for y, q in anch.items()
                        if round(org[best].get(y, 0)) == round(q))
            # Second path, for a series that agrees CONSISTENTLY without ever
            # agreeing exactly. 'Ore Of (Including Chrome)' reads 1.0005,
            # 1.0244, 0.9877, 1.0042 and 1.0031 against its own printed totals -
            # never to the digit, so the exact test refuses it, and yet nothing
            # but the same measure produces that. A wrong unit is out by a
            # FACTOR (twenty, for Ton against Cwt), not by two per cent.
            # Requires EVERY overlapping year to hold, and at least three of
            # them: 'Ivory - Vegetable' is refused by this too, because its
            # 1899 matches to the digit while 1894-98 run 9x to 31x with no
            # consistent ratio at all - which says its printed total for those
            # years is not the total of these countries, a different defect
            # that a unit label cannot fix.
            both = [(q, org[best].get(y, 0)) for y, q in anch.items()
                    if org[best].get(y)]
            near = (len(both) >= 3
                    and all(abs(v - q) <= 0.05 * q for q, v in both))
            if agree < 2 and not near:
                continue
            have = {cell[0] for cell in t1.get(best, ())}
            move = [cell for cell in t1['?'] if cell[0] not in have]
            if not move:
                continue
            t1.setdefault(best, []).extend(move)
            rest = [cell for cell in t1['?'] if cell[0] in have]
            if rest:
                t1['?'] = rest
            else:
                del t1['?']
            n += len(move)
        return n

    n_split = heal_split_year_units(comms)
    n_unit = unit_the_anchor(comms)

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

    # distinct real words the edit-distance net would wrongly conflate
    # (WASTE->WHITE was homing Cotton-Waste Bombay cells into Wine-White)
    FALSE_PAIRS = {frozenset(p) for p in (
        ('WASTE', 'WHITE'), ('WHALE', 'WHITE'), ('BEADS', 'BEANS'),
        ('CANDY', 'CARDS'), ('PLAIN', 'PLATE'), ('SHEEP', 'SHEET'),
        # HORNS->HORSE homed the infinity engine's 1874 hops block (misfiled
        # under 'HIDES ... | Horns') into Horse Hair: 1874 ran 6.79x T1.
        ('HORNS', 'HORSE'),
        # STAVES->SLATES buried the whole Slates origin series inside Staves;
        # split out, Slates 1895/1898 close EXACTLY on their own printed T1.
        ('STAVES', 'SLATES'),
        # MANUFACTURED->MANUFACTURES put CORK's national line inside
        # CAOUTCHOUC. Both reach here as bare one-token articles because
        # 'Cork :' and 'Caoutchouc:' are abstract group heads printed on
        # their own rows, and at edit distance 1 the two merged. The merged
        # entry's plurality label is 'Manufactures Of', so the curation fold
        # to Caoutchouc carried Cork's cells in with it and Caoutchouc's
        # Tier-1 for 1892-98 became Cork's series verbatim (9,055,694 where
        # the page prints 3,448,727 for 1892). Split out, four Caoutchouc
        # years close to the digit and Cork gets its post-1891 anchor back.
        ('MANUFACTURED', 'MANUFACTURES'))}

    def fuzzy_same(s1, s2):
        if len(s1) != len(s2):
            return False
        rest = list(s2)
        for t in s1:
            if t in rest:
                rest.remove(t)
                continue
            hit = next((r for r in rest if len(t) >= 5 and len(r) >= 5
                        and t[0] == r[0]
                        and frozenset((t, r)) not in FALSE_PAIRS
                        and edist_le2(t, r)), None)
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

    # ---- report every fuzzy merge, and FLAG the ones that cannot be OCR ----
    # MANUFACTURED/MANUFACTURES (Cork's national line inside Caoutchouc) was
    # the fourth false pair found one commodity at a time. The discriminator
    # that would have caught all four without reading a page: a genuine OCR
    # variant is the SAME PRINTED LINE read two ways, so where both spellings
    # carry a Tier-1 figure for the same year and unit the two figures must
    # AGREE. Two different commodities disagree — Cork printed 9,055,694 for
    # 1892 where Caoutchouc printed 3,448,727. Report-only: nothing here
    # changes what merges. Conflicts are candidates for FALSE_PAIRS, to be
    # adjudicated against the page, not applied automatically.
    def _t1_by_unit(sig):
        out = {}
        for u, rows in (comms[sig]['c'].get(TK) or {}).items():
            for r in rows:
                if r[1]:
                    out.setdefault((u, r[0]), r[1])
        return out

    fuzzy_rows = []
    for src, dst in merged_into.items():
        a, b = _t1_by_unit(dst), _t1_by_unit(src)
        shared = sorted(set(a) & set(b))
        bad = [(u, y, a[(u, y)], b[(u, y)]) for u, y in shared
               if max(a[(u, y)], b[(u, y)])
               and abs(a[(u, y)] - b[(u, y)])
               > 0.01 * max(a[(u, y)], b[(u, y)])]
        diff = sorted(set(dst) ^ set(src))
        worst = max(bad, key=lambda r: abs(r[2] - r[3]) / max(r[2], r[3]),
                    default=None)
        fuzzy_rows.append({
            'conflict_years': len(bad),
            'shared_years': len(shared),
            'kept': comms[dst]['labels'].most_common(1)[0][0],
            'merged_in': comms[src]['labels'].most_common(1)[0][0],
            'differing_tokens': ' / '.join(diff),
            'worst_unit': worst[0] if worst else '',
            'worst_year': worst[1] if worst else '',
            'kept_t1': f'{worst[2]:,.0f}' if worst else '',
            'merged_t1': f'{worst[3]:,.0f}' if worst else '',
            'kept_gbp': round(comms[dst]['v']),
            'merged_gbp': round(comms[src]['v'])})
    fuzzy_rows.sort(key=lambda r: (-r['conflict_years'],
                                   -(r['kept_gbp'] + r['merged_gbp'])))
    with open(BASE / 'reports' / 'fuzzy_merges.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(fuzzy_rows[0])) \
            if fuzzy_rows else None
        if w:
            w.writeheader()
            w.writerows(fuzzy_rows)
    n_conf = sum(1 for r in fuzzy_rows if r['conflict_years'])
    print(f'  fuzzy merges: {n_fuzzy} ({n_conf} with Tier-1 CONFLICTS) '
          f'-> reports/fuzzy_merges.csv')

    for src, dst in merged_into.items():
        d, s = comms[dst], comms.pop(src)
        d['v'] += s['v']
        d['labels'].update(s['labels'])
        for cty, units in s['c'].items():
            for u, cells in units.items():
                d['c'].setdefault(cty, {}).setdefault(u, []).extend(cells)

    # ---- dedupe: a comparative-block groupfix can re-admit a (country,
    # year) the consensus already carries (maize 1895-97 showed every
    # Argentine/Canada/... cell twice, doubling year sums in the detectors).
    # Same sig+country+unit+year = pathological duplicate, never a split
    # segment (segments live under distinct labels/sigs). Keep the
    # best-ranked cell; on rank tie keep the first-assembled (consensus and
    # own-year sources are queried before gap-fill/groupfix copies).
    n_dedup = 0
    for s in comms.values():
        for cty, units in s['c'].items():
            for u, cells in units.items():
                best = {}
                for cell in cells:
                    y, q, r = cell[0], cell[1], cell[2]
                    if y not in best or r < best[y][2]:
                        if y in best:
                            n_dedup += 1
                        best[y] = cell
                    else:
                        n_dedup += 1
                if len(best) != len(cells):
                    units[u] = [best[y] for y in sorted(best)]

    # ---- kindred twins: ONE place printed under two names, same figure ----
    # The dedupe above keys on the country STRING, so it cannot see
    # 'Hayti And St Domingo' beside 'Hayti And St. Domingo', or 'Tunis' beside
    # 'Tunisia', or 'Mauritius' beside 'Mauritius And Dependencies'. Both cells
    # carry the SAME figure — they are one printed line read or restated twice —
    # and the year then counts that origin twice.
    #
    # reference/country_standardize.csv already maps most of these, but it is
    # consumed by countrykey.py and widen_country_year.py, not here; applying
    # the whole crosswalk would rename every country in the payload and, worse,
    # its `summed_subregion` rows would fold sub-regions into parents and change
    # real totals. So this is deliberately the narrowest rule that fixes the
    # double count and nothing else:
    #
    #   drop a cell only when another cell in the SAME commodity, unit and year
    #   holds an IDENTICAL non-zero figure AND its name is a prefix of, or is
    #   prefixed by, this one once punctuation and spacing are ignored.
    #
    # Identical figures are what makes it safe: two genuinely distinct origins
    # do not report the same quantity to the digit under kindred names. Keeps
    # the shorter name (the printed head; the longer is the restatement).
    # 33 instances across 13 name pairs when this was written — see
    # reports/redundant_country_findings.md.
    def _ckey(s):
        return re.sub(r'[^a-z]', '', (s or '').lower())

    n_twin = 0
    for s in comms.values():
        byname = {cty: {u: {c[0]: c[1] for c in cells}
                        for u, cells in units.items()}
                  for cty, units in s['c'].items() if cty != TK}
        for cty in sorted(byname, key=lambda x: (-len(x), x)):
            for u, yq in list(byname[cty].items()):
                doomed = set()
                for y, q in yq.items():
                    if not q:
                        continue
                    for other, ounits in byname.items():
                        if other == cty or '(' in other or '(' in cty:
                            continue
                        if ounits.get(u, {}).get(y) != q:
                            continue
                        ka, kb = _ckey(cty), _ckey(other)
                        if ka == kb or not (ka.startswith(kb)
                                            or kb.startswith(ka)):
                            continue
                        if len(cty) > len(other):      # keep the shorter name
                            doomed.add(y)
                        break
                if doomed:
                    keep = [c for c in s['c'][cty][u] if c[0] not in doomed]
                    n_twin += len(s['c'][cty][u]) - len(keep)
                    byname[cty][u] = {y: q for y, q in yq.items()
                                      if y not in doomed}
                    if keep:
                        s['c'][cty][u] = keep
                    else:
                        del s['c'][cty][u]
        for cty in [k for k, v in s['c'].items() if k != TK and not v]:
            del s['c'][cty]

    # ---- emit: display label = most common printed rendering ----
    payload = {}
    for sig, s in comms.items():
        label = s['labels'].most_common(1)[0][0]
        if label in payload:                     # rare display collision
            label = f'{label} ({" ".join(sig)[:24]})'
        payload[label] = {'v': round(s['v']), 'c': s['c']}

    # commodity curation (reference/commodity_curation.csv): adjudicated
    # actions from the triage queue (scripts/curate_commodities.py).
    #   drop            — phantom/junk commodity, remove entirely
    #   fold,<target>   — merge into target (target's cells win on conflict)
    #   rename,<target> — display-name fix / era-label unification
    cur_f = BASE / 'reference' / 'commodity_curation.csv'
    n_cur = 0
    n_comb = 0
    n_drop = 0
    if cur_f.exists():
        for r in csv.DictReader(open(cur_f)):
            name, act, tgt = r['commodity'], r['action'], (r.get('target') or '').strip()
            if name not in payload:
                continue
            # Optional 'years' scope ("1886-1892", or ';'-separated): a
            # de-headed label can be the only carrier of some years and pure
            # glue in others. 'Oil' holds palm oil's 1886-92 West African
            # origins, which nothing else has, and ALSO 1897-99 cells whose
            # 'countries' are commodity names (Petroleum Gallons, Potatoes,
            # Paper-Making Materials) that inflated palm's 1898 origin value
            # ninefold. Folding the whole label buys the good years at the
            # price of the bad ones; scoping takes only what it came for.
            yrs = None
            if (r.get('years') or '').strip():
                yrs = set()
                for part in re.split(r'[;,]', r['years']):
                    part = part.strip()
                    if '-' in part:
                        a, b = part.split('-', 1)
                        yrs.update(range(int(a), int(b) + 1))
                    elif part:
                        yrs.add(int(part))
            if act == 'drop':
                del payload[name]; n_cur += 1
            elif act == 'drop-country' and tgt:
                # One country's cells are not this commodity's at all. 'Ivory -
                # Vegetable' (corozo nuts, from Colombia and Ecuador) carries a
                # 'british east indies' row of 335,000-391,000 cwt in every year
                # 1894-98 against printed totals of 12,000-39,000; drop it and
                # the years go from 10x-31x to 1.02-1.08, and 1899 - the one
                # year with no such row - is already exact. A stable ~350,000
                # cwt East Indies series that belongs to some other line.
                # Anchor-guarded like every other pass here: a cell goes only
                # where the commodity prints a total for that (unit, year) AND
                # removing it brings the year CLOSER. So a mis-aimed rule
                # removes nothing, and a country that really belongs is kept by
                # the arithmetic rather than by trust.
                ent = payload[name]
                c = ent['c']
                if tgt in c:
                    # anch_y is the fallback for a commodity whose own anchor
                    # has lost its unit label - which is exactly the state a
                    # glued cell leaves it in, since unit_the_anchor refuses to
                    # label a series whose years do not agree, and they do not
                    # agree BECAUSE of the glued cell. Comparing the numbers
                    # across a missing label is what unit_the_anchor does too;
                    # the closer-to-the-total guard still has to hold.
                    anch, anch_y, seen = {}, {}, {}
                    for u, cells in (c.get(TK) or {}).items():
                        for cell in cells:
                            if cell[1]:
                                anch[(u, cell[0])] = cell[1]
                                anch_y[cell[0]] = cell[1]
                    for cty2, byu2 in c.items():
                        if cty2 == TK or '(' in cty2:
                            continue
                        for u, cells in byu2.items():
                            for cell in cells:
                                seen[(u, cell[0])] = seen.get(
                                    (u, cell[0]), 0) + cell[1]
                    for u, cells in list(c[tgt].items()):
                        keep = []
                        for cell in cells:
                            k = (u, cell[0])
                            t1v = anch.get(k) or anch_y.get(cell[0])
                            tot = seen.get(k)
                            if (yrs is not None and cell[0] not in yrs) or (
                                    not t1v or tot is None) or (
                                    abs(tot - cell[1] - t1v) >= abs(tot - t1v)):
                                keep.append(cell)
                                continue
                            seen[k] = tot - cell[1]
                            # 'v' is the size the map ranks and reports by, so
                            # a dropped cell has to leave it too - otherwise
                            # this commodity keeps advertising trade it no
                            # longer holds.
                            if len(cell) > 3:
                                # 'v' was accumulated as a sum of
                                # min(cell_value, 50,000,000) - the same cap the
                                # commodity roll-up applies - so a cell has to
                                # leave it capped the same way. Subtracting the
                                # raw figure zeroed `Silk - Raw` (GBP127.6M) and
                                # `Skins, Furs, And Pelts - Seal` (GBP63.4M) the
                                # first time this ran, because the garbage cell
                                # being removed carried a garbage VALUE too.
                                ent['v'] = max(0.0, (ent.get('v') or 0)
                                               - min(cell[3], 50_000_000))
                            n_drop += 1
                        if keep:
                            c[tgt][u] = keep
                        else:
                            del c[tgt][u]
                    if not c[tgt]:
                        del c[tgt]
            elif act in ('fold', 'rename', 'combine') and tgt:
                src = payload.pop(name); n_cur += 1
                if yrs is not None:
                    src = {**src, 'c': {c: {u: [x for x in cells if x[0] in yrs]
                                            for u, cells in byu.items()}
                                        for c, byu in (src.get('c') or {}).items()}}
                    src['c'] = {c: {u: v for u, v in byu.items() if v}
                                for c, byu in src['c'].items()}
                    src['c'] = {c: byu for c, byu in src['c'].items() if byu}
                if tgt not in payload:
                    payload[tgt] = src
                else:
                    dst = payload[tgt]
                    # Cells merge by (country, unit, YEAR) with the target
                    # winning, so a source year the target already has adds
                    # nothing. 'v' - the size the map ranks and reports by -
                    # must follow the cells rather than being added whole:
                    #   * a source carrying only §TOTAL (an era label that
                    #     published the national line and no origin table)
                    #     contributes no trade at all. It MEASURES trade the
                    #     target already counts, so adding its value would
                    #     inflate the commodity by its own anchor.
                    #   * a source overlapping the target's years contributes
                    #     only the years actually taken.
                    # 'v' is an accumulated sort key rather than the exact sum
                    # of surviving cells, so it is carried over in proportion
                    # to the cell value kept. A fully disjoint fold keeps all
                    # of it, which is what every fold adjudicated so far does.
                    src_v = kept_v = 0.0
                    adding = act == 'combine'
                    danch, dseen = {}, {}
                    if adding:
                        for u, cells in (dst['c'].get(TK) or {}).items():
                            for cell in cells:
                                if cell[1]:
                                    danch[(u, cell[0])] = cell[1]
                        for cty2, byu2 in dst['c'].items():
                            if cty2 == TK or '(' in cty2:
                                continue
                            for u, cells in byu2.items():
                                for cell in cells:
                                    dseen[(u, cell[0])] = dseen.get(
                                        (u, cell[0]), 0) + cell[1]
                    for ctry, byu in src['c'].items():
                        dbyu = dst['c'].setdefault(ctry, {})
                        # A source cell that lost its printed unit belongs to
                        # whatever unit the TARGET uses for this country, and
                        # has to be relabelled BEFORE the year check rather
                        # than after it. Otherwise it slides past under the
                        # '?' key and becomes a second copy of a row the
                        # target already holds - which is what folding the
                        # de-headed label 'Wool' into "Wool - Sheep Or Lambs'"
                        # did: its 1896 cells are digit-identical to the
                        # target's (New South Wales 163,717,080 either way)
                        # and were added again, while its 1897-99 cells, the
                        # only copy of the colonial wool for those years, were
                        # invisible to the quantity axis. Same magnitude guard
                        # heal_units uses: three times either way, or the two
                        # are not the same measure and the cells stay '?'.
                        lab = {u: cs for u, cs in dbyu.items() if u != '?'}
                        if '?' in byu and lab:
                            dt = max(lab, key=lambda u: len(lab[u]))
                            dv = sorted(c[1] for c in lab[dt] if c[1] > 0)
                            sv = sorted(c[1] for c in byu['?'] if c[1] > 0)
                            dm = dv[len(dv) // 2] if dv else 0
                            sm = sv[len(sv) // 2] if sv else 0
                            move = []
                            if dm and sm and dm / 3 < sm < dm * 3:
                                move = byu['?']          # whole bucket agrees
                            elif dm:
                                # ...or rescue cell by cell against the
                                # NEAREST labelled year, as heal_units does.
                                # A span median is the wrong yardstick for a
                                # growing series: Australasia's wool runs from
                                # 1872, so the target's median sits far below
                                # its 1897 cell and the bucket test rejects a
                                # cell that is 1.3x the neighbouring year.
                                near = {}
                                for c in lab[dt]:
                                    near.setdefault(c[0], c[1])
                                def _ref(y0):
                                    for dy in range(4):
                                        for yy in (y0 - dy, y0 + dy):
                                            if near.get(yy):
                                                return near[yy]
                                    return dm
                                move = [c for c in byu['?'] if c[1] > 0
                                        and _ref(c[0]) / 3 < c[1] < _ref(c[0]) * 3]
                            if move:
                                byu = dict(byu)
                                rest = [c for c in byu['?'] if c not in move]
                                byu[dt] = byu.get(dt, []) + move
                                if rest:
                                    byu['?'] = rest
                                else:
                                    byu.pop('?')
                        for u, series in byu.items():
                            idx = {row[0]: row for row in dbyu.get(u, [])}
                            new = [row for row in series if row[0] not in idx]
                            # 'combine': the source is a CONSTITUENT of the
                            # target, not a copy of it - 'Cutch And Gambier' is
                            # one printed line whose origin table is two, and a
                            # plain fold drops the second half's Other
                            # Countries row instead of adding it. Where both
                            # sides hold the same (country, unit, year), ADD.
                            # Anchor-guarded exactly like the other passes:
                            # only where the target prints a total for that
                            # (unit, year) AND adding brings the year closer to
                            # it. With no printed total to check against,
                            # 'combine' behaves as 'fold' - so it can turn a
                            # duplicate into a double count only if a human
                            # writes the action AND the arithmetic agrees.
                            if adding and ctry != TK:
                                for row in series:
                                    hit = idx.get(row[0])
                                    if hit is None:
                                        continue
                                    t1v = danch.get((u, row[0]))
                                    tot = dseen.get((u, row[0]))
                                    if not t1v or tot is None:
                                        continue
                                    if abs(tot + row[1] - t1v) >= abs(tot - t1v):
                                        continue
                                    hit[1] += row[1]
                                    hit[2] = max(hit[2], row[2])
                                    if len(hit) > 3 and len(row) > 3:
                                        hit[3] += row[3]
                                    dseen[(u, row[0])] = tot + row[1]
                                    kept_v += row[3] if len(row) > 3 else 0
                                    n_comb += 1
                            for row in new:
                                if ctry != TK:
                                    dseen[(u, row[0])] = dseen.get(
                                        (u, row[0]), 0) + row[1]
                            if ctry != '§TOTAL':
                                src_v += sum(row[3] for row in series)
                                kept_v += sum(row[3] for row in new)
                            dbyu.setdefault(u, []).extend(new)
                    dst['v'] = dst.get('v', 0) + (
                        src.get('v', 0) * kept_v / src_v if src_v else 0)
        if n_cur:
            print(f'  curation: {n_cur} commodities dropped/folded/renamed'
                  + (f'; {n_comb} constituent cells added' if n_comb else '')
                  + (f'; {n_drop} misfiled country cells dropped' if n_drop else ''))
    # ---- era-wording fold: one printed line, re-worded mid-series, is ONE
    # commodity. The abstract re-words lines ('For Fancy purposes' -> 'For
    # Fancy Purposes, including Berlin Wool and Zephyr Yarn' in 1893; 'Sago'
    # -> 'Sago, And Flour Or Meal Thereof' in 1893) and the country tables
    # follow, so one line becomes two or three payload commodities, each
    # carrying a fragment of the T1 span and a fragment of the origins —
    # and a changeover year printed under BOTH wordings is counted TWICE
    # (woollen yarn's fancy line read 1,320,619 under each name in 1893).
    # Discriminator ported from scripts/sibling_identity.py merge_era_variants
    # (validated session-10 iteration 4: 71 merges, 9 families stable), all
    # conditions necessary:
    #   * same head and same modal unit;
    #   * one article's vocabulary a PROPER SUBSET of the other's (disjoint
    #     vocabularies are siblings, not eras);
    #   * origin spans SUCCEED one another rather than nest;
    #   * where the spans overlap, both names carry the SAME figure within
    #     1% (disagreement refutes — 'Fruit — Oranges' vs '— Oranges and
    #     Lemons' diverge in 1893; silence does not refute);
    #   * no third label completes the superset's vocabulary (union parent,
    #     not an era — the guard that spared 'Fruit — Oranges').
    # Payload-grade additions, each refusing a known trap: a total label
    # never merges with a non-total (the sugar trap); an exclusion label
    # ('other than...') only merges with another exclusion label; and a
    # GROUPLESS pair must be a literal prefix re-wording ('Watches' ->
    # 'Watches, And Parts Thereof') because the headless bucket spans the
    # whole corpus and subset-of-vocabulary alone is too weak there.
    # The surviving key is the wording with more attested years; on an
    # overlap year the LATER era's cell wins (counted once) — that is the
    # era that continues, and the 1% agreement guard makes the choice
    # near-neutral numerically. T1 (§TOTAL) merges under the same rule, so
    # the anchor and the origins reunite on one key.
    # Differs from sibling_identity's FILLER: OTHER/SORTS/KINDS/ALL are
    # LOAD-BEARING here. That instrument analyses families; this pass merges
    # SHIPPED series, and 'Other Sorts' is what distinguishes a residual
    # sub-sort from its named siblings — with those words as noise,
    # 'Sparkling : Other Sorts' reads as an era-rewording of 'Sparkling :
    # Champagne' and two disjoint printed lines become one.
    _EW_FILLER = {'AND', 'OR', 'OF', 'THE', 'IN', 'FOR', 'NOT', 'TOTAL',
                  'UNENUMERATED', 'INCLUDING', 'VIZ', 'EXCEPT', 'THAN',
                  'BY', 'ANY', 'FROM', 'TO', 'ON', 'AS', 'WITH'}
    _EW_TOTAL = {'TOTAL', 'TOTALS'}

    def _ew_toks(s):
        return {t.upper() for t in re.split(r'[^A-Za-z0-9]+', s or '')
                if len(t) > 1}

    def _ew_head(n):
        return n.split(' — ')[0].strip() if ' — ' in n else ''

    def _ew_article(n):
        return n.split(' — ')[-1].strip()

    def _ew_vocab(n):
        return _ew_toks(_ew_article(n)) - _EW_FILLER

    def _ew_is_total(n):
        t = _ew_toks(_ew_article(n))
        if t & _EW_TOTAL:
            return True
        for k in (('ALL', 'KINDS'), ('ALL', 'SORTS'), ('EVERY', 'SORT')):
            if set(k) <= t:
                rest = (t - {'ALL', 'KINDS', 'SORTS', 'EVERY', 'SORT'}
                        - _EW_FILLER)
                if rest <= _ew_toks(_ew_head(n)):
                    return True
        return False

    def _ew_is_exclusion(n):
        return re.search(r'\b(other than|except|not being|excluding)\b',
                         n, re.I) is not None

    def _ew_norm(s):
        return re.sub(r'\s+', ' ',
                      re.sub(r'[^a-z0-9]+', ' ', (s or '').lower())).strip()

    def _ew_series(entry):
        c = entry.get('c') or {}
        ucnt = Counter()
        for u, rows in (c.get(TK) or {}).items():
            ucnt[u] += len([r for r in rows if r[1]])
        if not ucnt:
            for cty, byu in c.items():
                if cty == TK:
                    continue
                for u, rows in byu.items():
                    ucnt[u] += len([r for r in rows if r[1]])
        if not ucnt:
            return None, {}, {}
        unit = max(ucnt, key=ucnt.get)
        t1 = {r[0]: r[1] for r in (c.get(TK) or {}).get(unit, ()) if r[1]}
        orig = Counter()
        for cty, byu in c.items():
            if cty == TK or '(' in cty:
                continue
            for r in byu.get(unit, ()):
                if r[1]:
                    orig[r[0]] += r[1]
        return unit, t1, dict(orig)

    def fold_era_wordings(payload):
        ser = {}
        for n, e in payload.items():
            u, t1, orig = _ew_series(e)
            if u:
                ser[n] = (u, t1, orig)

        def _yrs(n):
            _, t1, o = ser[n]
            return set(t1) | set(o)

        def _completes_union(a, b, bucket):
            va, vb = _ew_vocab(a), _ew_vocab(b)
            for c3 in bucket:
                if c3 in (a, b) or c3 not in ser:
                    continue
                vc = _ew_vocab(c3)
                if vc and not (vc & va) and (va | vc) == vb:
                    return True
            return False

        def era_pair(a, b, bucket):
            ua, t1a, oa = ser[a]
            ub, t1b, ob = ser[b]
            if ua != ub:
                return None
            if _ew_is_total(a) != _ew_is_total(b):
                return None
            if _ew_is_exclusion(a) != _ew_is_exclusion(b):
                return None
            va, vb = _ew_vocab(a), _ew_vocab(b)
            if not va or not vb or not (va < vb or vb < va):
                return None
            if not _ew_head(a):
                # groupless: demand a literal prefix re-wording
                sa, sb = _ew_norm(_ew_article(a)), _ew_norm(_ew_article(b))
                short, long_ = (sa, sb) if len(sa) < len(sb) else (sb, sa)
                if not long_.startswith(short + ' '):
                    return None
            if (_completes_union(a, b, bucket)
                    or _completes_union(b, a, bucket)):
                return None
            ya, yb = _yrs(a), _yrs(b)
            if not ya or not yb:
                return None
            sa2 = set(oa) if (oa and ob) else ya
            sb2 = set(ob) if (oa and ob) else yb
            if not ((min(sa2) < min(sb2) and max(sa2) < max(sb2))
                    or (min(sb2) < min(sa2) and max(sb2) < max(sa2))):
                return None
            for y in ya & yb:
                for x, z in ((oa.get(y, 0), ob.get(y, 0)),
                             (t1a.get(y, 0), t1b.get(y, 0))):
                    if x and z:
                        if abs(x - z) > 0.01 * max(x, z):
                            return None
                        break
            canon = a if len(ya) >= len(yb) else b
            other = b if canon == a else a
            return canon, other, max(_yrs(other)) > max(_yrs(canon))

        def fold_pair(canon, other, other_is_later):
            dst, src = payload[canon], payload.pop(other)
            for ctry, byu in src['c'].items():
                dbyu = dst['c'].setdefault(ctry, {})
                for u, rows in byu.items():
                    idx = {row[0]: i for i, row in enumerate(dbyu.get(u, []))}
                    for row in rows:
                        if row[0] in idx:
                            if other_is_later:      # later era's cell wins,
                                old = dbyu[u][idx[row[0]]]   # counted once
                                dbyu[u][idx[row[0]]] = row
                                if ctry != TK and len(row) > 3 and len(old) > 3:
                                    dst['v'] = max(0.0, dst.get('v', 0)
                                                   - min(old[3], 50_000_000)
                                                   + min(row[3], 50_000_000))
                            continue
                        dbyu.setdefault(u, []).append(row)
                        if ctry != TK and len(row) > 3:
                            dst['v'] = dst.get('v', 0) + min(row[3], 50_000_000)
            u2, t12, o2 = _ew_series(dst)
            ser[canon] = (u2, t12, o2)

        buckets = defaultdict(list)
        for n in ser:
            buckets[(ser[n][0], _ew_head(n))].append(n)
        merges = []
        for names in buckets.values():
            if len(names) < 2:
                continue
            changed = True
            while changed:
                changed = False
                live = sorted(n for n in names if n in ser and n in payload)
                for i, a in enumerate(live):
                    for b in live[i + 1:]:
                        pair = era_pair(a, b, live)
                        if not pair:
                            continue
                        canon, other, later = pair
                        merges.append((canon, other,
                                       ser[canon][0], _ew_head(canon) or '(groupless)'))
                        fold_pair(canon, other, later)
                        changed = True
                        break
                    if changed:
                        break
        if merges:
            with open(BASE / 'reports' / 'era_wording_folds.csv', 'w',
                      newline='') as f:
                w = csv.writer(f)
                w.writerow(['kept', 'folded_in', 'unit', 'head'])
                w.writerows(sorted(merges))
            print(f'  era-wording folds: {len(merges)} '
                  f'-> reports/era_wording_folds.csv')
        return len(merges)

    n_era = fold_era_wordings(payload)

    # A fold brings in countries the target has no labelled cell for, so the
    # per-country unit tests inside the fold cannot reach them and they arrive
    # unit-less - invisible to the quantity axis. Only the ANCHOR pass is safe
    # to re-run here, and it is safe precisely because its test is the year's
    # arithmetic: it moves cells only when doing so brings the year CLOSER to
    # its own printed national total, so a duplicate (which overshoots) is
    # left alone. Re-running the whole of heal_units was tried and reverted -
    # its per-country magnitude tests have no such guard and doubled the years
    # a fold's two halves both covered.
    #
    # The aggregate-beside-members pass has to run again here for the same
    # reason and with the same licence. It is anchor-guarded, so it cannot
    # touch an ORPHAN - an orphan has no printed total of its own - and the
    # dye-stuffs orphans are exactly where the doubled India sits: `Dye Stuffs,
    # And Substances Used In Tanning - Indigo` reads 1.87-1.94x its target's
    # printed total in every year 1885-94 because `British East Indies` is in
    # it beside Bengal, Madras and Bombay. Only after a fold has put those
    # cells under a label that carries an anchor can the year's arithmetic see
    # them. Same guard, so re-running it cannot make a year worse.
    n_agg += drop_aggregate_beside_members(payload)
    n_split += heal_split_year_units(payload)
    n_unit += unit_the_anchor(payload)
    n_tunton += fold_tun_ton(payload)
    n_heal2 = heal_by_anchor(payload)
    if n_heal2:
        print(f'  unit-healed against the anchor after curation: {n_heal2}')
    shifted = drop_shifted_duplicates(payload)
    if shifted:
        with open(BASE / 'reports' / 'shifted_duplicate_cells.csv', 'w',
                  newline='') as f:
            w = csv.writer(f)
            w.writerow(['commodity', 'year', 'dropped_country', 'kept_country',
                        'qty', 'value'])
            w.writerows(sorted(shifted, key=lambda r: (-r[5], r[0], r[1])))
        print(f'  shifted duplicates dropped: {len(shifted)} '
              f'-> reports/shifted_duplicate_cells.csv')

    # map export: same structure, cells keep the per-country-year value
    # [year, qty, rank, value] for the public map's value/quantity toggle.
    map_out = out.with_name('map_data.json')
    map_js = json.dumps(payload, separators=(',', ':')).replace('</', '<\\/')
    map_out.write_text(map_js)
    # viz_payload.json: strip value back to [y, q, r] (back-compat schema)
    for e in payload.values():
        for byu in e['c'].values():
            for u in list(byu):
                byu[u] = [c[:3] for c in byu[u]]
    js = json.dumps(payload, separators=(',', ':')).replace('</', '<\\/')
    out.write_text(js)
    if cfix_log:
        print(f'country-cell sticky repairs ({n_cfixed:,} cells, '
              f'{len(cfix_log)} distinct label mappings):')
        for (old, new), n in cfix_log.most_common():
            print(f'  {n:5d}  {old}  ->  {new}')
    print(f'commodities: {len(payload)}  T1 cells: {n_tot:,} '
          f'(sticky repaired: {n_fixed:,}; fuzzy-merged: {n_fuzzy}; '
          f"unit-healed: {n_healed:,}; coast-rollup: {n_coast:,}; "
          f"coast-sibling folds: {n_sib:,}; aggregate-beside-members: {n_agg:,}; "
          f"split-year units: {n_split:,}; anchor-units restored: {n_unit:,}; "
          f"Tun/Ton: {n_tunton:,}; era folds: {n_era}; "
          f'deduped: {n_dedup:,})  '
          f'MB: {len(js) / 1e6:.2f}  -> {out}')


if __name__ == '__main__':
    main()
