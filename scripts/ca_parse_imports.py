#!/usr/bin/env python3
"""Parse the Canadian 'General Statement of Imports' (Table No. 1) out of the Chandra OCR
of the Trade & Navigation volumes into one long table.

Regimes (detected per table from its header row, inherited by header-less continuations):
  C  1880-1889+  'by Countries and Provinces': article > country > province, 5 value cols
                 (qty imported, value imported, qty entered for consumption, value e.f.c., duty)
  B  1877        'by Provinces': province sections; article > country, same 5 value cols.
                 Chandra puts the first country label on the unit row, so labels are paired
                 with the NEXT value row (systematic one-row slip, corrected here).
  A  1869-1873   'by Provinces', 8 value cols (qty in British vessels / foreign vessels /
                 land carriage / total qty / total value / e.f.c. qty / value / duty). Best effort.
Earlier layouts (1868 per-province statements, 1866-67 ports x countries) are not handled yet.

Output: db/canada/imports_general_rows.csv (one row per printed line, with row_kind) and
reports/canada_imports_parse.md (diagnostics + closure checks).
"""
import csv, html, json, os, re, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ca_profile as P

ROOT = P.ROOT
OUT_DIR = ROOT / 'db' / 'canada'
OUT_CSV = OUT_DIR / 'imports_general_rows.csv'
OUT_MD = ROOT / 'reports' / 'canada_imports_parse.md'

PROVINCE_ORDER = ['Ontario', 'Quebec', 'Nova Scotia', 'New Brunswick', 'Manitoba', 'British Columbia', 'P. E. Island', 'N. W. Territories']
PROVINCE_KEYS = {
    'ontario': 'Ontario', 'quebec': 'Quebec', 'novascotia': 'Nova Scotia', 'newbrunswick': 'New Brunswick',
    'nbrunswick': 'New Brunswick', 'manitoba': 'Manitoba', 'britishcolumbia': 'British Columbia',
    'bcolumbia': 'British Columbia', 'britcolumbia': 'British Columbia', 'peisland': 'P. E. Island',
    'princeedwardisland': 'P. E. Island', 'pei': 'P. E. Island', 'nwterritories': 'N. W. Territories',
    'northwestterritories': 'N. W. Territories', 'nwt': 'N. W. Territories', 'territories': 'N. W. Territories',
}
UNIT_WORDS = r'(?:lbs?|galls?|gals?|no|tons?|cwts?|bush|brls?|bbls?|doz|pkgs?|yds?|m|ft|feet|pcs|pairs?|prs|oz|qrs?|grs|bxs|cases|bunches|sq\.? ?ft|c\. ?ft|number|gallons|pounds|barrels|bushels|dozen|cords|hhds)'
UNIT_RE = re.compile(r'^\s*' + UNIT_WORDS + r'\.?\s*', re.I)
LEADER_RE = re.compile(r'[.\s·]+$')
DITTO_RE = re.compile(r'^(?:[“"”\'‘’]+\s*)+')
NUM_RE = re.compile(r'^\d{1,3}(?:,\d{3})*$|^\d+$')


BANNER_RE = re.compile(r'DUTIABLE|DU[CT]\w{2,6}\s+GOODS|FREE\s+GOODS', re.I)      # 'DUCTILE GOODS', 'DUTLABLE GOODS' = DUTIABLE GOODS


def norm_label(s):
    s = DITTO_RE.sub('', s)
    s = LEADER_RE.sub('', s)
    return s.strip(' ,;')


_PROV_FUZZY = [
    (re.compile(r'^[a-z]{1,2}island$|^[a-z]{1,2}[a-z]?isla.?d+$|^p[a-z]{0,3}island+$|^p?e?edward$|^princeedward[a-z]*$'), 'P. E. Island'),   # 'P. R. Island', 'P. & Island', 'P. E. Isla. d', 'P. E. Islanddd'
    (re.compile(r'^n?w?territo[a-z]*$|^northwestterrit[a-z]*$'), 'N. W. Territories'),                     # 'N. W. Territoires', 'N.-W. Territo ies'
    (re.compile(r'^[a-z]{1,5}scotia$'), 'Nova Scotia'),                                                    # 'New Scotia', 'N. Scotia'
    (re.compile(r'^[a-z]{1,4}brunswick$'), 'New Brunswick'),                                               # 'Few Brunswick'
    (re.compile(r'^[a-z]{2,7}columbia$'), 'British Columbia'),                                             # 'Briti-b Columbia', 'P. tish Columbia'
    (re.compile(r'^quebe[a-z]?$'), 'Quebec'),
    (re.compile(r'^ontari[a-z]?$|^ontaio$'), 'Ontario'),
    (re.compile(r'^manitob[a-z]?$|^mantoba$'), 'Manitoba'),
]


def province_of(s):
    t = re.sub(r'\([^)]*\)', '', norm_label(s))
    k = re.sub(r'[^a-z]', '', t.lower().replace('é', 'e'))
    p = PROVINCE_KEYS.get(k)
    if p or not k: return p
    # OCR-damaged spellings: a province label is never a country, so tolerate one or two bad characters
    for rx, prov in _PROV_FUZZY:
        if rx.match(k): return prov
    return None


def split_trailing_province(s):
    """'United States... Quebec' -> ('United States', 'Quebec'); else (s, None)."""
    t = norm_label(s)
    for n in (3, 2, 1):                      # longest tail first: 'British Columbia' before a fuzzy 'Columbia'
        parts = t.rsplit(None, n)
        if len(parts) == n + 1:
            tail = ' '.join(parts[1:])
            if province_of(tail):
                return norm_label(parts[0]), province_of(tail)
    return t, None


SEED_COUNTRIES = ['Great Britain', 'United States', 'France', 'Germany', 'Belgium', 'China', 'Holland', 'Spain',
    'Italy', 'Switzerland', 'Austria', 'Portugal', 'Newfoundland', 'Japan', 'Brazil', 'Turkey', 'Egypt', 'Russia',
    'Norway', 'Sweden', 'Denmark', 'Greece', 'Mexico', 'Chili', 'Peru', 'Persia', 'India', 'Australia', 'Mauritius',
    'Hayti', 'Cuba', 'Venezuela', 'Argentine Republic', 'New Zealand', 'South Africa', 'British Africa', 'Gibraltar',
    'Malta', 'Madeira', 'Azores', 'Canary Islands', 'Cent. America', 'Central America', 'Sand. Islands',
    'Sandwich Islands', 'Society Islands', 'St. Pierre', 'B. W. Indies', 'S. W. Indies', 'F. W. Indies', 'D. W. Indies',
    'Dan. W. Indies', 'B. E. Indies', 'D. E. Indies', 'Dutch E. Indies', 'Brit. W. Indies', 'Brit. East Indies', 'Brit. E. Indies', 'Brit. Guiana', 'British Guiana',
    'Dutch Guiana', 'British West Indies', 'Spanish West Indies', 'French West Indies', 'Danish West Indies',
    'British East Indies', 'Dutch East Indies', 'Bermuda', 'British Columbia', 'Norway and Sweden', 'Total']


def fuzzy_jaccard(a, b):
    """Token-set overlap of two article names with OCR-tolerant token equality (ratio >= 0.85), '&c'/'N.E.S'
    and stop words dropped: 'Cotton, all other manuffactures of' ~ 'All other manufactures of cotton'."""
    import difflib
    def toks(x):
        x = re.sub(r'not (elsewhere|otherwise) (specified|provided for|enumerated)|not specially enumerated or provided for', ' nes ', re.sub(r'\\frac\{[^}]*\}\{[^}]*\}', ' ', (x or '').lower()))
        x = re.sub(r'(&c|\betc\b|\bn\.?\s*e\.?\s*s\b)\.?', '', x)
        return [t for t in re.findall(r'[a-z0-9]+', x) if t not in ('of', 'and', 'the', 'or', 'all', 'other', 'nes')]
    ta, tb = toks(a), toks(b)
    if not ta or not tb: return 0.0
    used = set(); hit = 0
    for t in ta:
        for i, u in enumerate(tb):
            if i in used: continue
            if t == u or (len(t) >= 4 and len(u) >= 4 and t[:3] == u[:3] and difflib.SequenceMatcher(None, t, u).ratio() >= 0.85):
                used.add(i); hit += 1; break
    return hit / (len(ta) + len(tb) - hit)


def wrapped_suffix(a, b):
    """'ages' (the tail of a hyphen-wrapped 'Pack- ages' whose head was lost) vs 'Packages': one name is a single
    lowercase-led token of 3+ letters that ends the other's last token."""
    ta = re.findall(r'[A-Za-z]+', a or ''); tb = re.findall(r'[A-Za-z]+', b or '')
    if not ta or not tb: return False
    for x, y in ((ta, tb), (tb, ta)):
        if len(x) == 1 and len(x[0]) >= 3 and x[0][0].islower() and (
                (y[-1].lower().endswith(x[0].lower()) and len(y[-1]) > len(x[0])) or                  # 'ages' / 'Packages'
                (len(y) >= 2 and len(x[0]) >= 5 and x[0].lower() in [t.lower() for t in y])):       # 'diameter' = the tail of a wrapped heading
            return True
    return False


def token_containment(short, long):
    """Share of the shorter name's content tokens found (fuzzily) in the longer: 'Bituminous' in 'Coal, bituminous',
    'Portland or Roman' in 'Cement, Portland or Roman', 'Gutta percha, all other' in 'Gutta percha and India rubber, all
    other' — the running-head forms of an open article."""
    import difflib
    QUAL = {'other', 'others', 'nes', 'nop', 'not', 'except', 'unenumerated', 'elsewhere', 'specified', 'provided',
            'otherwise', 'all', 'over', 'under', 'less', 'more', 'than', 'above', 'below', 'direct', 'refined', 'raw'}
    def toks(x):
        x = re.sub(r'(&c|\betc\b)\.?', '', re.sub(r'\\frac\{[^}]*\}\{[^}]*\}', ' ', (x or '').lower()))
        x = re.sub(r'not (elsewhere|otherwise) (specified|provided for|enumerated)|not specially enumerated or provided for', ' nes ', x)
        x = re.sub(r'\bn\.?\s*e\.?\s*s\b\.?', ' nes ', x); x = re.sub(r'\bn\.?\s*o\.?\s*p\b\.?', ' nop ', x)
        return [t for t in re.findall(r'[a-z0-9]+', x) if t not in ('of', 'and', 'the', 'or', 'con')]
    a, b = toks(short), toks(long)
    a = list(dict.fromkeys(a)); b = list(dict.fromkeys(b))          # duplicates ('wool ... wool') count once
    if not a or not b: return 0.0
    if len(a) > len(b): a, b = b, a
    used = set(); hit = 0
    for t in a:
        for i, u in enumerate(b):
            if i in used: continue
            if t == u or (len(t) >= 4 and len(u) >= 4 and t[:3] == u[:3] and difflib.SequenceMatcher(None, t, u).ratio() >= 0.85):
                used.add(i); hit += 1; break
    # tokens the longer name adds (or the shorter drops) must not change the meaning: 'Pig iron' is not
    # 'Pig iron, all other'; 'Feathers, dressed' is not 'Feathers, undressed'
    extra = [u for i, u in enumerate(b) if i not in used] + [t for t in a if t not in b and not any(t[:3] == u[:3] for u in b)]
    # a name cut off mid-phrase by the OCR ('... otherwise manufactured, over') is a prefix of the full name
    sraw = (short if len(toks(short)) <= len(toks(long)) else long) or ''
    last = re.findall(r'[a-z]+', sraw.lower())[-1:] 
    truncated = bool(last) and last[0] in ('over', 'under', 'of', 'and', 'or', 'for', 'the', 'in', 'to', 'not', 'than', 'with', 'by', 'on', 'at', 'from') \
        and all(i in used for i in range(len(a))) and sorted(used) == list(range(len(a)))
    if truncated: return 1.0
    abbreviated = bool(re.search(r'&c|\betc\b', (short or '').lower())) or bool(re.search(r'&c|\betc\b', (long or '').lower()))
    if not abbreviated and any(t in QUAL or t.isdigit() for t in extra): return 0.0
    if abbreviated and any(t in QUAL for t in [x for x in a if x not in b]): return 0.0   # the short form must not ADD a qualifier
    return hit / len(a)


def split_trailing_country(s, vocab):
    """'Valentines, &c. United States' -> ('Valentines, &c.', 'United States') when s ends with a known country."""
    t = norm_label(s)
    best = None
    for c in vocab:
        if t.lower().endswith(c.lower()) and len(t) > len(c) + 2:
            if best is None or len(c) > len(best): best = c
    if best is None:
        # A route qualifier may follow the country name, so the label no longer *ends* with a
        # country: 'Coal, anthracite— Great Britain... (Via Hudson Bay.)'. These volumes annotate
        # goods shipped via Hudson's Bay, and the printed Abstract has no such country -- they are
        # Great Britain. Retry against the stem, and keep the qualifier on the tail so the two runs
        # stay distinguishable in the rows (ca_check_abstract.ckey folds it away for arbitration).
        m = re.search(r'\s*(\([^()]*\))\s*$', t)
        if m:
            stem = t[:m.start()].rstrip(' .,—-–;:')
            for c in vocab:
                if stem.lower().endswith(c.lower()) and len(stem) > len(c) + 2:
                    if best is None or len(c) > len(best): best = c
            if best:
                head = stem[:-len(best)].rstrip(' .,—-–;:')
                return head, stem[-len(best):] + ' ' + m.group(1)
    if best:
        head = t[:-len(best)].rstrip(' .,—-–;:')
        tail = t[-len(best):]
        # 'Brit W. Indies' / 'Span. W. Indies': pull the abbreviation tokens back into the country name
        # (only when the matched tail is itself a fragment, never for a complete country name)
        while re.match(r'^(W\.?\s*|E\.?\s*)?(Indies|Ind\b|Africa|Guiana)', tail):
            mm = re.search(r'(?:^|\s)((?:Brit|Span|Sp|Fr|Fren|Dan|Dutch|B|S|F|D|W|E|N)\.?)$', head)
            if not mm: break
            tail = mm.group(1) + ' ' + tail
            head = head[:mm.start(1)].rstrip(' .,—-–;:')
        return head, tail
    return t, None


def is_unit_token(s):
    t = s.strip().rstrip('.').strip()
    return t in ('$', '$ cts', '$ cts.', 'cts') or bool(re.fullmatch(UNIT_WORDS + r'\.?', t, re.I))


def parse_num(s, cents_ok=True):
    """Return (value, flag). flag in {'', 'blank', 'unit', 'fused', 'unparsed'}."""
    t = s.strip()
    if not t or re.fullmatch(r'[.\s·…]+', t) or t in ('—', '-', '–'):
        return None, 'blank'
    t = UNIT_RE.sub('', t)          # 'No. 1,313' -> '1,313'
    t = t.replace('$', '').strip()
    if not t or re.fullmatch(r'[.\s]+', t):
        return None, 'blank'
    if is_unit_token(t) or not re.search(r'\d', t):
        return None, 'unit'            # 'Sq. Yds.', 'Cub. Ft.', 'M.' — any digit-free text in a value cell is a unit
    toks = t.split()
    if len(toks) == 1 and NUM_RE.match(toks[0]):
        return int(toks[0].replace(',', '')), ''
    if len(toks) == 2 and NUM_RE.match(toks[0]) and re.fullmatch(r'\d{2}', toks[1]) and cents_ok:
        return int(toks[0].replace(',', '')) + int(toks[1]) / 100.0, ''
    if all(NUM_RE.match(x) for x in toks):
        return None, 'fused'
    # OCR noise: 'l' for 1, 'O' for 0, stray chars
    t2 = re.sub(r'[^0-9,\s]', '', t).strip()
    if t2 and t2 != t:
        v, f = parse_num(t2, cents_ok)
        return v, (f or 'repaired')
    return None, 'unparsed'


NUMTOK_RE = re.compile(r'\d{1,3}(?:,\d{3})+|\d+')


def split_numeric_tokens(cell, cents_ok=False):
    """'Galls. 4,261 979' -> ['4,261', '979'];  '300 00 6 00 854 08' (cents) -> ['300 00', '6 00', '854 08'];
    '.....' -> ['.....'] ; returns None if the cell is not numeric-ish."""
    t = UNIT_RE.sub('', cell.strip()).replace('$', '').strip()
    if not t or re.fullmatch(r'[.\s·…]+', t):
        return ['.....']
    toks = t.split()
    if not all(NUMTOK_RE.fullmatch(x) for x in toks):
        return None
    if cents_ok and len(toks) >= 2 and len(toks) % 2 == 0 and all(re.fullmatch(r'\d{2}', toks[i]) for i in range(1, len(toks), 2)):
        return [toks[i] + ' ' + toks[i + 1] for i in range(0, len(toks), 2)]
    return toks


def split_names(cell, names):
    """Split a label cell holding several known names ('Great Britain..... United States.....') in order."""
    t = DITTO_RE.sub('', cell)
    found = []
    pos = 0
    low = t.lower()
    first = None
    while pos < len(t):
        best = None
        for n in names:
            i = low.find(n.lower(), pos)
            while i >= 0:
                # whole-word match only ('other' inside 'any other liquid' must not split the cell)
                if (i == 0 or not low[i - 1].isalpha()) and (i + len(n) >= len(low) or not low[i + len(n)].isalpha()):
                    break
                i = low.find(n.lower(), i + 1)
            if i >= 0 and (best is None or i < best[0] or (i == best[0] and len(n) > len(best[1]))):
                best = (i, n)
        if best is None: break
        if first is None: first = best[0]
        found.append(best[1]); pos = best[0] + len(best[1])
    # the text before the first name and after the last must be only leaders/punctuation
    rest = re.sub(r'[.\s·,;“"”]+', '', low[pos:])
    head = re.sub(r'[.\s·,;“"”]+', '', low[:first]) if first is not None else ''
    return found if len(found) >= 2 and not rest and not head else None


def unfuse_rows(body, names, label_cols, cents_col):
    """Expand rows whose label cell holds n names and whose numeric cells hold n tokens into n rows.
    label_cols: indices (from the left) that may hold the fused names; cents_col: index from the right of the duty column."""
    out = []
    for cells in body:
        texts = [c for _, _, c in cells]
        n = None; lab_i = None; parts = None
        for li in label_cols:
            if li < len(texts):
                sp = split_names(texts[li], names)
                if sp:
                    n = len(sp); lab_i = li; parts = sp; break
        if not n:
            out.append(cells); continue
        toks = []
        ok = True
        for ci, tx in enumerate(texts):
            if ci == lab_i: toks.append(None); continue
            if ci < max(label_cols) + 1 and ci != lab_i and not NUMTOK_RE.search(tx):
                toks.append(None); continue
            sp = split_numeric_tokens(tx, cents_ok=(ci == len(texts) - 1 - cents_col))
            if sp is None:
                toks.append(None)            # text cell (article etc.)
            elif len(sp) == n:
                toks.append(sp)
            elif len(sp) == 1:
                toks.append(sp * 1)          # single token: placed below
            else:
                ok = False; break
        # require at least one numeric cell actually split n ways, and names of one kind (all provinces or none)
        nsplit = sum(1 for t in toks if t is not None and len(t) == n)
        kinds = set(bool(province_of(x)) for x in parts)
        if not ok or nsplit == 0 or len(kinds) != 1:
            out.append(cells); continue
        # single-token numeric cells: give them to the LAST row unless the first row needs them (rare);
        # the caller's arithmetic cannot be checked here, so last row is the default (first rows print blanks)
        for r in range(n):
            new = []
            for ci, tx in enumerate(texts):
                kind = cells[ci][0]; span = cells[ci][1]
                if ci == lab_i:
                    new.append((kind, span, parts[r]))
                elif toks[ci] is None:
                    new.append((kind, span, tx if r == 0 else ''))
                elif len(toks[ci]) == n:
                    new.append((kind, span, toks[ci][r]))
                else:
                    new.append((kind, span, toks[ci][0] if r == n - 1 else '.....'))
            out.append(new)
    return out


def regime_of(header_rows):
    h = ' | '.join(' | '.join(c for _, _, c in r) for r in header_rows).upper()
    if 'PROVINCES INTO WHICH' in h or 'COUNTRIES WHENCE' in h:
        return 'C'
    if 'BRITISH VESSELS' in h:
        return 'A'
    if 'ARTICLES' in h and 'COUNTRIES' in h and 'DUTY' in h:
        return 'B'
    return None


def province_from_title(title):
    if re.search(r'dominion of canada', title, re.I) and re.search(r'general statement of imports', title, re.I):
        return 'Dominion'
    m = re.search(r'PROVINCE OF ([A-Z. \-]+?)(?:\.|—|$)', title.upper())
    if m:
        p = province_of(m.group(1))
        if p: return p
    m = re.search(r'—\s*([A-Za-z. \-]+?)\s*—\s*\*?Continued', title)
    if m:
        return province_of(m.group(1))
    return None


class Parser:
    def __init__(self):
        self.rows = []
        self.diag = Counter()
        self.unparsed = Counter()
        self.blank_rows = []          # province rows the OCR left without values (coverage loss, for re-OCR triage)
        self.vocab = set(SEED_COUNTRIES)

    def learn_vocab(self, tn):
        # a ditto-led label is a country only when it sits where countries sit: label | province | numbers
        # (learning every ditto-led short text put 'N.E.S', 'Tin, plate and sheets' into the vocab and they then
        #  hijacked headings and country order)
        for tm in P.TABLE_RE.finditer(tn):
            rows = P.parse_table(tm.group(0))
            has_prov = any(len(c) >= 3 and province_of(c[1][2]) for c in rows)
            for cells in rows:
                if len(cells) < 3 or not DITTO_RE.match(cells[0][2]): continue
                # regime C (province column present): label | province | numbers; regimes A/B: label | numbers
                if has_prov and not province_of(cells[1][2]): continue
                if not has_prov and not any(parse_num(c[2])[0] is not None for c in cells[1:]): continue
                t = norm_label(cells[0][2])
                if t and len(t) < 42 and not re.search(r'[—:\d$,"“”]', t) and not t[0].islower() \
                        and not re.fullmatch(r'(?:[A-Z]\.\s?)+[A-Z]?\.?', t) and re.search(r'[A-Za-z]{3}', t) \
                        and not is_unit_token(t):
                    # 'Ready made clothing Great Britain' / 'Spades and shovels. Great Britain': a heading fused with
                    # a country is not a country (it would hijack headings as labels); long names are allowed only
                    # for the possessions ('Spanish Possessions in Pacific Ocean')
                    head, tail = split_trailing_country(t, SEED_COUNTRIES)
                    if tail and head and tail != t and not re.search(r'(\band|&)$', head): continue       # keep 'Norway & Sweden'
                    if len(t) >= 30 and not re.search(r'possess', t, re.I): continue
                    self.vocab.add(t)
        self.vocab.discard('')

    # ---------------------------------------------------------------- regime C
    def parse_table_C(self, fy, vol, seq, body, ctx):
        n0 = len(body)
        n_start = len(self.rows)
        body = unfuse_rows(body, self.vocab | set(PROVINCE_KEYS.values()) | set(PROVINCE_ORDER), [0, 1], 0)
        if len(body) != n0: self.diag['unfused_rows'] += len(body) - n0
        NV = 5
        for ri, cells in enumerate(body):
            texts = [c for _, _, c in cells]
            spans = sum(cs for _, cs, _ in cells)
            dd_mark = False
            # quantity and value fused into one cell ('United States | Ontario | 29 126 | 29 126 | 14 75' — a whole
            # page of the 1884 flour tables reads like this): split every non-final cell holding two plain numbers
            # a phantom blank cell between the imported and entered-for-consumption pairs ('| Nova Scotia | | 112 | 37 |
            # | 112 | 37 | 7 40'): the row has one cell too many and the pairs repeat
            if len(texts) >= NV + 3:
                z = [t.strip() for t in texts[-6:]]
                if re.fullmatch(r'[\d,]+', z[0]) and re.fullmatch(r'[\d,]+', z[1]) and not z[2] and re.fullmatch(r'[\d,]+', z[3]) and re.fullmatch(r'[\d,]+', z[4]) \
                        and (re.fullmatch(r'[\d,]+ \d\d', z[5]) or not z[5] or re.fullmatch(r'[.\s·…]+', z[5])):
                    texts = texts[:-4] + texts[-3:]
                    self.diag['phantom_blank_cell_dropped'] += 1
            if len(texts) >= NV + 3:
                # a phantom dots cell BEFORE each pair ('Quebec | ..... | 90,546 | 67,838 | ..... | 89,848 | 67,189 |
                # 20,196 98' on the 1885 yarn page — read as country Quebec, province '90,546'): drop both
                z = [t.strip() for t in texts[-7:]]
                blank = lambda c: not c or re.fullmatch(r'[.\s·…]+', c)
                if blank(z[0]) and re.fullmatch(r'[\d,]+', z[1]) and re.fullmatch(r'[\d,]+', z[2]) and blank(z[3]) \
                        and re.fullmatch(r'[\d,]+', z[4]) and re.fullmatch(r'[\d,]+', z[5]) \
                        and (re.fullmatch(r'[\d,]+ \d\d', z[6]) or blank(z[6])) and len(texts) - 7 >= 1 \
                        and not any(re.fullmatch(r'[\d,]+', t.strip()) for t in texts[:-7]):
                    texts = texts[:-7] + texts[-6:-4] + texts[-3:]
                    self.diag['phantom_pair_cells_dropped'] += 1
            k_two = sum(1 for i, t in enumerate(texts) if i < len(texts) - 1 and re.fullmatch(r'[\d,]+ [\d,]+', t.strip()) and not re.fullmatch(r'[\d,]+ \d\d', t.strip()))
            n_real = len([t for t in texts if t.strip()]) if k_two else 0
            # ('19 534' alone is 19,534 with its comma lost — only a row short of cells with BOTH pairs fused is split)
            if len(texts) < NV + 2 and (k_two >= 2 or (k_two == 1 and len(texts) < NV)):
                new = []; changed = False
                for i, t in enumerate(texts):
                    tt = t.strip()
                    if i < len(texts) - 1 and re.fullmatch(r'[\d,]+ [\d,]+', tt) and not re.fullmatch(r'[\d,]+ \d\d', tt):
                        new.extend(tt.split()); changed = True
                    else:
                        new.append(t)
                if changed:
                    texts = new; self.diag['fused_qty_value_split'] += 1
                    while len(texts) > NV + 2 and not texts[-1].strip():     # the OCR's trailing empty cell
                        texts = texts[:-1]
            # both quantity cells dropped on a value-only article: 'Great Britain | Ontario | 4,143 | 4,684 | 936 87'
            # (label, province, value, value, duty) -> insert the blank quantity cells
            tt = [t.strip() for t in texts]
            while len(tt) > 3 and not tt[-1]: tt = tt[:-1]
            if ctx.get('unit') is None and len(tt) in (4, 5) and re.fullmatch(r'\d{1,3}(,\d{3})* \d\d', tt[-1]) \
                    and all(re.fullmatch(r'[\d,]+', c) for c in tt[-3:-1]) and province_of(tt[-4]) \
                    and (len(tt) == 4 or not re.fullmatch(r'[\d,]+', tt[0])):
                texts = tt[:-3] + ['', tt[-3], '', tt[-2], tt[-1]]
                self.diag['qty_cells_dropped'] += 1
            joined = ' '.join(texts).strip()
            # section banners
            if (len(cells) == 1 or spans >= 7 and len(cells) <= 2) and re.search(BANNER_RE, joined):
                self._section(ctx, joined); continue
            if len(cells) < NV:
                # short rows: full-width label cells (the 1880s volumes print article headings, country labels
                # and 'Total' as one spanning cell, often ditto-led: '“ Buckwheat—', '“ United States...'),
                # section banners, or junk (index lines, page furniture)
                j = norm_label(joined)
                if re.search(BANNER_RE, joined):
                    self._section(ctx, joined)
                elif not j or len(j) <= 2 or re.match(r'\d', j) or re.search(r'\d{4}|\d[,.]\d{3}', j) \
                        or (re.search(r'\d', j) and not re.search(r'[—–:;-]\s*$', j.rstrip('.'))):
                    # index lines, page furniture, numbers; headings may hold 'No. 9' / '17 gauge' only with a dash
                    self.diag['short_row'] += 1
                elif re.match(r'totals?\b', j, re.I):
                    ctx['country'] = 'TOTAL'; ctx['expect_label'] = False; ctx['article_buf'] = []
                    ctx['last_prov'] = None; self.diag['short_total_label'] += 1
                elif j in self.vocab or j.rstrip('—–- .') in SEED_COUNTRIES or split_trailing_country(j, self.vocab)[1] == j:
                    j = j.rstrip('—–- .') if j.rstrip('—–- .') in SEED_COUNTRIES else j     # '“ Great Britain—'
                    buf = ctx.get('article_buf') or []
                    rank = lambda c: 0 if c.startswith('Great Brit') else 1 if c.startswith('United Stat') else 2
                    prev = ctx.get('country')
                    if buf and len(' '.join(buf)) >= 4:
                        # '“ Indian or corn meal' (dash lost) straight before 'Great Britain...': the buffered fragment
                        # is a complete heading, not a wrapped half (1885 cornmeal \$330K was filed under buckwheat)
                        self._article(ctx, ' '.join(buf)); self.diag['heading_from_fragment_before_country'] += 1
                    elif prev in ('TOTAL',) or (prev and prev != '?' and rank(j) < 2 and rank(j) <= rank(prev)):
                        # GB or US re-occurring after a later country: the article heading was lost entirely
                        ctx['article_parents'] = ctx.get('article_parents') or []
                        ctx['article'] = '?'; ctx['block_id'] = ctx.get('block_id', 0) + 1
                        ctx['leaf_used'] = False; ctx['unit'] = None; ctx['article_closed'] = False
                        self.diag['article_heading_lost'] += 1
                    ctx['country'] = j; ctx['expect_label'] = False; ctx['article_buf'] = []
                    ctx['last_prov'] = None; self.diag['short_country_label'] += 1
                elif re.search(r'[—–:;-]\s*$', j.rstrip('.')) or re.search(r'viz\.?\s*$', j, re.I):
                    self._article(ctx, ' '.join(ctx.get('article_buf', []) + [j]))
                    ctx['article_buf'] = []; ctx['expect_label'] = False
                    self.diag['short_article_heading'] += 1
                elif split_trailing_country(j, self.vocab)[1] and len(split_trailing_country(j, self.vocab)[0].strip(' —–-.')) >= 4 \
                        and (split_trailing_country(j, self.vocab)[1] in SEED_COUNTRIES or '—' in j):
                    # '“ Chloride of lime— | Great Britain...' / '“ Chloralum or chloride of aluminium | Great Britain...'
                    # (two short cells): the heading and its first country on one row
                    head, tail = split_trailing_country(j, self.vocab)
                    self._article(ctx, ' '.join(ctx.get('article_buf', []) + [head.strip()]))
                    ctx['article_buf'] = []; ctx['country'] = tail; ctx['expect_label'] = False; ctx['last_prov'] = None
                    self.diag['short_heading_with_country'] += 1
                elif len(j) > 3 and not j.isupper():
                    # a wrapped fragment of an article name ('“ Buckwheat meal or' / 'flour—')
                    ctx.setdefault('article_buf', []).append(j)
                    self.diag['article_fragment'] += 1
                else:
                    self.diag['short_row'] += 1
                continue
            if len(texts) > NV + 2:
                # stray unit cells ('| Lbs. |') between the labels and the numbers: column-header remnants
                keep = [i for i, t in enumerate(texts) if not (is_unit_token(t) and i >= 2)]
                if len(keep) >= NV + 2 and len(keep) < len(texts):
                    texts = [texts[i] for i in keep]; self.diag['stray_unit_cells_dropped'] += 1
            if ctx.get('section') == 'DUTIABLE' and len(texts) == NV + 2 and not texts[-1].strip():
                # '| Ontario | 349,716 | 349,925 | 105,029 | 95 | ': the duty cell split into dollars | cents and a
                # trailing blank cell — value, value, duty on a value-only line (val_imp ~ val_efc, duty an ad valorem share)
                t4 = [t.strip() for t in texts[-5:-1]]
                if all(re.fullmatch(r'\d{1,3}(,\d{3})*|\d+', t) for t in t4) and re.fullmatch(r'\d\d', t4[3]) \
                        and all(parse_num(t, cents_ok=False)[0] is None for t in texts[:-5]):
                    a4, b4, c4, _ = [parse_num(t, cents_ok=False)[0] for t in t4]
                    if b4 > 0 and 0.02 <= c4 / b4 <= 0.6 and abs(a4 - b4) <= 0.15 * max(a4, b4):
                        texts = texts[:-5] + ['', t4[0], '', t4[1], t4[2] + ' ' + t4[3]]
                        self.diag['duty_cell_split_rejoined'] += 1
            if NV <= len(texts) <= NV + 2 and not re.search(r'\d \d\d$', texts[-1].strip()):
                # free-goods row whose trailing (blank) duty cell the OCR dropped: 'Quebec | 1,219,955 | 257,639 |
                # 1,219,955 | 257,639' (or 'heading | Great Britain | Ontario | Lbs. 2,518,083 | 644,463 | Lbs.
                # 2,518,083 | 644,463') is label(s) + qty + value + qty + value, not five values
                # DUTIABLE rows lose their duty cell too ('Nova Scotia | 379 | 190 | 67 | 32' on the 1884 whiskey page,
                # read as province-in-the-unit-slot + four shifted values): duty is always printed with cents, so a
                # province followed by four plain integers is qty, value, qty, value with the duty lost
                tail = texts[-4:]
                lab = texts[:-4]
                if all(parse_num(t, cents_ok=False)[0] is not None for t in tail) \
                        and lab and all(parse_num(t, cents_ok=False)[0] is None for t in lab):
                    if ctx.get('section') == 'FREE' and (province_of(lab[-1]) or not lab[-1].strip() or re.fullmatch(r'[.\s·…]+', lab[-1]) or len(lab) >= 2):
                        texts = texts + ['']
                        self.diag['duty_cell_dropped'] += 1
                    elif ctx.get('section') == 'DUTIABLE' and (province_of(lab[-1]) or not lab[-1].strip() or re.fullmatch(r'[.\s·…]+', lab[-1])) \
                            and all(re.fullmatch(r'\d{1,3}(,\d{3})*|\d+', t.strip()) for t in tail):
                        a4, b4, c4, d4 = [parse_num(t, cents_ok=False)[0] for t in tail]
                        if re.fullmatch(r'\d\d', tail[3].strip()) and b4 > 0 and 0.02 <= c4 / b4 <= 0.6 and abs(a4 - b4) <= 0.15 * max(a4, b4):
                            # 'Ontario | 34,088 | 34,079 | 10,223 | 70': value, value, duty dollars, duty cents (the duty
                            # cell split in two) on a value-only line
                            texts = lab + ['', tail[0], '', tail[1], tail[2].strip() + ' ' + tail[3].strip()]
                            self.diag['duty_cell_split_rejoined'] += 1
                        else:
                            texts = texts + ['']
                            dd_mark = True
                            self.diag['duty_cell_dropped_dutiable'] += 1
            vals_raw = texts[-NV:]
            labels = texts[:-NV]
            # banner in label position with blank values
            if labels and re.search(r'^(DUTIABLE|DU[CT]\w{2,6}|FREE) GOODS', norm_label(labels[0]), re.I):
                self._section(ctx, labels[0])
                labels = [''] + labels[1:]
                if not any(parse_num(v, cents_ok=(i == 4))[0] is not None for i, v in enumerate(vals_raw)):
                    continue
            parsed = [parse_num(v, cents_ok=(i == 4)) for i, v in enumerate(vals_raw)]
            nums = [p[0] for p in parsed]
            flags = [p[1] for p in parsed]
            if dd_mark: flags[4] = 'duty_dropped'
            numeric = any(v is not None for v in nums)
            units_only = not numeric and all(f in ('blank', 'unit') for f in flags)
            if os.environ.get('CA_DEBUG_TABLE') == f'{fy}:{seq}':
                print('ROW', ri, 'texts=', texts, 'nums=', nums, 'numeric=', numeric, file=sys.stderr)
            a = labels[0] if len(labels) >= 2 else None
            b = labels[-1] if labels else ''
            if len(labels) >= 3:
                # '" " | Spain..... | Quebec.....': the country is the last non-ditto cell before the province;
                # '“ Currants— | Great Britain... | Ontario': a heading cell precedes it
                heads = [x for x in labels[:-1] if re.search(r'[—:]\s*$', norm_label(x))]
                rest = [x for x in labels[:-1] if norm_label(x) and x not in heads]
                if heads:
                    self._article(ctx, ' '.join(ctx.get('article_buf', []) + [norm_label(h) for h in heads]))
                    ctx['article_buf'] = []
                a = rest[-1] if rest else (labels[0] if not heads else '')
            if len(labels) == 1 and b.strip() and not province_of(b) and not numeric:
                a, b = b, ''            # lone label with no values: treat as first-column text
            if len(labels) == 1 and b.strip() and not province_of(b) and numeric:
                # lone label with values: country+province fused, or a country whose province cell was dropped
                c2, p2 = split_trailing_province(b)
                if p2:
                    a, b = c2, p2; self.diag['split_country_province'] += 1
            if a is not None and len(labels) >= 2 and not province_of(b) and b.strip():
                c2, p2 = split_trailing_province(b)
                if p2:
                    b = p2
                    if c2 and not norm_label(a) and not re.match(r'totals?\b', c2, re.I):
                        a = c2              # '" | Holland..... Quebec.....': the country rode in the province slot
                    elif c2 and (c2 in self.vocab or re.match(r'totals?\b', c2, re.I)) and re.search(r'[—:]\s*$', norm_label(a)):
                        # '“ do do testing not over 96 degrees— | United States... Quebec.....': heading + fused country
                        self._article(ctx, ' '.join(ctx.get('article_buf', []) + [norm_label(a)])); ctx['article_buf'] = []
                        a = c2
            a_n = norm_label(a) if a is not None else None
            if a_n:
                if re.match(r'^\(.*\)$', a_n) or re.match(r'^\(?see also\b', a_n, re.I):
                    a_n = ''                                   # a cross-reference note, not a label
                elif province_of(a_n) and (not b.strip() or province_of(b) == province_of(a_n)):
                    b = a_n; a_n = ''                          # 'Ontario | Ontario': the label column repeats the province
                elif re.fullmatch(r'To(t|ta|tal?)?s?', a_n):
                    a_n = 'Total'                              # truncated 'Total'
            # ---- article header rows: text ending in a dash, values blank/units
            if a_n and not numeric:
                frag = a.strip()
                # 'Article— Country' (or 'Article Country') with the values on the following rows
                if a_n not in self.vocab and not re.match(r'totals?\b', a_n, re.I):
                    head, tail = split_trailing_country(a_n, self.vocab)
                    if tail:
                        # keep the leaf's dash ('Turpentine, spirits of— Great Britain' at a page top: without it the
                        # 'ends in of' parent-running-head test swallowed the new article into the open one)
                        if head: self._article(ctx, ' '.join(ctx.get('article_buf', []) + [head + ('—' if '—' in a_n else '')]))
                        ctx['article_buf'] = []
                        ctx['country'] = 'TOTAL' if re.match(r'totals?\b', tail, re.I) else tail
                        ctx['expect_label'] = False; ctx['last_prov'] = None
                        self._units(ctx, vals_raw)
                        continue
                if re.search(r'[—:;]\s*$', frag) or re.search(r'(viz\.?|—)\s*$', frag):
                    self._article(ctx, ' '.join(ctx.get('article_buf', []) + [frag]))
                    ctx['article_buf'] = []
                    self._units(ctx, vals_raw)
                    continue
                if re.match(r'totals?\b', a_n, re.I):
                    ctx['country'] = 'TOTAL'; ctx['expect_label'] = False; ctx['last_prov'] = None
                    ctx['pending_prov'] = province_of(b) if (b.strip() and any(is_unit_token(v) or f == 'unit' for v, f in zip(vals_raw, flags))) else None
                    continue
                if '—' in a_n and units_only:
                    # 'Hats, Straw, &c.— Great Brita'n...' on a units row: heading + (possibly misspelt) country
                    head, tail = a_n.rsplit('—', 1); tail = tail.strip(' .')
                    if tail and not province_of(tail) and (tail in self.vocab or (
                            re.fullmatch(r"[A-Z][A-Za-z.' ]{2,22}", tail) and len(tail.split()) <= 3 and not re.search(r'&c|,', tail))):
                        self._article(ctx, head + '—'); ctx['country'] = tail; ctx['article_buf'] = []
                        ctx['expect_label'] = False; ctx['last_prov'] = None
                        ctx['pending_prov'] = province_of(b) if b.strip() else None
                        self._units(ctx, vals_raw); self.diag['fused_article_country'] += 1
                        continue
                if a_n in self.vocab and units_only:
                    # a country label whose values are on the next row (or blank)
                    ctx['country'] = a_n; ctx['article_buf'] = []; ctx['expect_label'] = False; ctx['last_prov'] = None
                    ctx['pending_prov'] = province_of(b) if (b.strip() and any(is_unit_token(v) or f == 'unit' for v, f in zip(vals_raw, flags))) else None
                    continue
                if units_only and len(a_n) > 3 and (not ctx.get('article_buf')) and not frag.endswith('-') \
                        and any(is_unit_token(v) or f == 'unit' for v, f in zip(vals_raw, flags)):
                    # article name without trailing dash (OCR dropped it) followed by a units row
                    self._article(ctx, a); self._units(ctx, vals_raw); continue
                # a wrapped fragment of an article name: buffer it
                ctx.setdefault('article_buf', []).append(frag)
                self.diag['article_fragment'] += 1
                continue
            if a_n and numeric and ctx.get('article_buf'):
                # buffered fragments followed by a row with a label and values: the label completes the
                # article name only if it is not itself a country / total
                if a_n not in self.vocab and not re.match(r'totals?\b', a_n, re.I) and not split_trailing_country(a_n, self.vocab)[1]:
                    self._article(ctx, ' '.join(ctx['article_buf'] + [a_n])); ctx['article_buf'] = []
                    a_n = ''
                else:
                    self._article(ctx, ' '.join(ctx['article_buf'])); ctx['article_buf'] = []
            # ---- page-top continuation: the running heading repeated in the label cell of a data row whose country
            #      is the one carried over from the previous page ('Sugar, melado, &c.— do do not testing over 93
            #      degrees.. | Quebec | values', then 'Brazil | Quebec' starts the next country)
            if a_n and numeric and ctx.get('table_top') and a_n not in self.vocab and not re.match(r'totals?\b', a_n, re.I) \
                    and province_of(b) and ctx.get('country') not in (None, '', '?') \
                    and not split_trailing_country(a_n, self.vocab)[1] \
                    and (len(a_n) > 30 or re.search(r'[—:]|&c|^do\b', a_n)):
                carried = ctx['country']; old_blk = ctx.get('block_id', 0)
                self._article(ctx, a_n)
                if ctx.get('block_id', 0) == old_blk and ctx.get('article') is not None:
                    ctx['country'] = carried
                    a_n = ''; self.diag['page_top_heading_continuation'] += 1
                else:
                    # the heading is a NEW article's: this is its first data row and the country label is lost
                    # ('Builders' ... hardware | Ontario | 15,554', then 'Great Britain | Quebec' continues the run)
                    ctx['country'] = None; ctx['expect_label'] = False
                    a_n = ''; self.diag['page_top_heading_new_article'] += 1
            if a_n and numeric and a_n not in self.vocab and a_n.rstrip('—–- .') in self.vocab:
                a_n = a_n.rstrip('—–- .')                      # 'Great Britain— | Ontario | values'
            # ---- 'Article Country' fused without a dash
            if a_n and numeric and a_n not in self.vocab and not re.match(r'totals?\b', a_n, re.I):
                head, tail = split_trailing_country(a_n, self.vocab)
                if tail:
                    if head:
                        self._article(ctx, head)
                    a_n = tail; self.diag['fused_article_country_nodash'] += 1
            # ---- a heading wrapped over DATA rows: 'iron, plain, not | P. E. Island | 58' (fragment starts lowercase
            #      or the previous one ended with a hyphen) — the row's data continue the current block
            deferred = None
            if a_n and numeric and province_of(b) and a_n not in self.vocab and not re.match(r'totals?\b', a_n, re.I) \
                    and not split_trailing_country(a_n, self.vocab)[1] \
                    and (a_n[0].islower() or (ctx.get('article_buf') and ctx['article_buf'][-1].endswith('-'))) \
                    and not re.search(r'—\s*[A-Z]', a_n):
                if ctx.get('article_closed') or ctx.get('country') in (None, '', '?'):
                    # the previous article is closed: this row is the first data row of the new article (its
                    # country label lost); the heading applies now
                    self._article(ctx, ' '.join(ctx.get('article_buf', []) + [a_n])); ctx['article_buf'] = []
                    ctx['country'] = None; a_n = ''; self.diag['heading_fragment_starts_article'] += 1
                else:
                    ctx.setdefault('article_buf', []).append(a_n)
                    if a_n.endswith('—'):
                        deferred = ' '.join(ctx['article_buf']); ctx['article_buf'] = []
                    a_n = ''; self.diag['heading_fragment_on_data_row'] += 1
            # ---- fused 'Article— Country' in one cell
            if a_n and '—' in a_n and numeric and not re.match(r'total', a_n, re.I):
                head, tail = a_n.rsplit('—', 1)
                tail = tail.strip(' .')
                if not tail:
                    pv = province_of(b); lp = ctx.get('last_prov')
                    if pv and lp and pv in PROVINCE_ORDER and lp in PROVINCE_ORDER and ctx.get('country') not in (None, '', '?') \
                            and PROVINCE_ORDER.index(pv) > PROVINCE_ORDER.index(lp):
                        # the heading ends on a data row that still continues the current block: apply it after
                        deferred = ' '.join(ctx.get('article_buf', []) + [head + '—']); ctx['article_buf'] = []
                        a_n = ''; self.diag['heading_deferred_past_data_row'] += 1
                    else:
                        self._article(ctx, ' '.join(ctx.get('article_buf', []) + [head + '—'])); ctx['article_buf'] = []; a_n = ''
                        ctx['country'] = None; self.diag['country_label_lost'] += 1
                elif tail and not province_of(tail) and (tail in self.vocab or re.match(r'totals?\b', tail, re.I) or len(tail) < 25):
                    self._article(ctx, head + '—')
                    a_n = tail
                    self.diag['fused_article_country'] += 1
            if not a_n and not numeric and not province_of(b):
                cand = norm_label(b)
                if cand and (cand in self.vocab or re.match(r'totals?\b', cand, re.I)):
                    # '" | United States... | | | |': the country label rode in the province slot, values follow
                    ctx['country'] = 'TOTAL' if re.match(r'totals?\b', cand, re.I) else cand
                    ctx['expect_label'] = False; ctx['last_prov'] = None; ctx['article_buf'] = []
                    self.diag['country_label_in_province_slot'] += 1
                    continue
                # a units row / blank row with no label: nothing to emit, and it must not arm expect_label
                self.diag['blank_row_skipped'] += 1
                continue
            if not a_n and not numeric and province_of(b) and units_only and any(is_unit_token(v) or f == 'unit' for v, f in zip(vals_raw, flags)):
                # '| Quebec | Lbs. | | Lbs. |': the values of this province are on the next, label-less row
                # (an all-dots province row is a genuine nil line and must NOT capture the following total)
                ctx['pending_prov'] = province_of(b); self.diag['province_values_on_next_row'] += 1
                continue
            if not a_n and not numeric and province_of(b):
                ctx['pending_prov'] = None
                self.diag['nil_province_row'] += 1
                self.blank_rows.append(dict(fiscal_year=fy, volume=vol, table_seq=seq, row_seq=ri, section=ctx.get('section'),
                                            article=ctx.get('article'), country=ctx.get('country'), province=province_of(b), raw=' | '.join(texts)))
                continue
            if not a_n and not b.strip() and numeric and ctx.get('pending_prov'):
                b = ctx['pending_prov']
            ctx['pending_prov'] = None
            country = None; kind = None; prov = None
            if a_n:
                ctx['expect_label'] = False
            if a_n and not re.match(r'totals?\b', a_n, re.I):
                # countries are printed GB, US, then alphabetical: an order restart without a new heading
                # means the article heading was lost (or a Total row just closed the previous article)
                # (the printed country order after GB/US/France/Germany is a fixed list, not alphabetical, so
                #  only GB/US re-occurrence and a preceding Total row are used as evidence)
                rank = lambda c: 0 if c.startswith('Great Brit') else 1 if c.startswith('United Stat') else 2
                prev = ctx.get('country')
                if prev in ('TOTAL',) or (prev and prev != '?' and rank(a_n) < 2 and rank(a_n) <= rank(prev)):
                    ctx['article_parents'] = ctx.get('article_parents') or []
                    ctx['article'] = '?'; ctx['block_id'] = ctx.get('block_id', 0) + 1
                    ctx['leaf_used'] = False; ctx['unit'] = None; ctx['article_closed'] = False
                    self.diag['article_heading_lost'] += 1
            if a_n:
                if re.match(r'totals?\b', a_n, re.I):
                    kind = 'article_province_total'; ctx['country'] = 'TOTAL'
                    prov = province_of(b)
                    if not prov: kind = 'article_total'
                else:
                    country = a_n; ctx['country'] = country; kind = 'detail'
                    prov = province_of(b)
                    if not prov and b.strip():
                        # province cell unreadable
                        self.diag['province_unrecognised'] += 1; prov = b.strip()
                    if not prov: kind = 'country_noprov'
            else:
                # no first label: province row or subtotal
                prov = province_of(b) if b.strip() else None
                if prov:
                    kind = 'article_province_total' if ctx.get('country') == 'TOTAL' else 'detail'
                    if ctx.get('expect_label'):
                        # a subtotal/total row was just printed: the next row must carry a label; it did not
                        ctx['country'] = '?'; kind = 'detail_lostlabel'; self.diag['lost_label_after_total'] += 1
                    # province order restarting inside a country block => a label row was lost
                    elif kind == 'detail' and ctx.get('last_prov') and prov in PROVINCE_ORDER and ctx['last_prov'] in PROVINCE_ORDER \
                            and PROVINCE_ORDER.index(prov) <= PROVINCE_ORDER.index(ctx['last_prov']):
                        ctx['country'] = '?'; kind = 'detail_lostlabel'; self.diag['lost_label_block'] += 1
                    elif kind == 'detail' and ctx.get('country') == '?':
                        kind = 'detail_lostlabel'
                    elif kind == 'detail' and ctx.get('country') in (None, ''):
                        # a province row straight after a heading: the country label is missing
                        ctx['country'] = '?'; kind = 'detail_lostlabel'; self.diag['country_label_lost'] += 1
                elif b.strip():
                    # something in province position that is not a province: country row missing province?
                    cand = norm_label(b)
                    if re.match(r'totals?\b', cand, re.I):
                        kind = 'article_total'; ctx['country'] = 'TOTAL'
                    else:
                        if '—' in cand:
                            head, tail = cand.rsplit('—', 1); tail = tail.strip(' .')
                            if tail and (tail in self.vocab or split_trailing_country(tail, self.vocab)[1] == tail or len(tail) < 25):
                                self._article(ctx, head + '—'); cand = tail
                            elif not tail and head.strip() and head.strip() not in self.vocab and len(head.strip()) <= 22:
                                # '“ Wheat flour— | 93 | 395 | ...': the NEXT article's heading rode on this row, whose
                                # values are the current country's (or article's) total — emit the total, then the heading
                                kind = 'article_total' if ctx.get('country') in ('TOTAL', None, '') else 'country_total'
                                deferred = head.strip() + '—'
                                self.diag['heading_on_total_row'] += 1
                                cand = None
                        else:
                            head, tail = split_trailing_country(cand, self.vocab)
                            if tail:
                                if head: self._article(ctx, head)
                                cand = tail
                        if cand is not None:
                            ctx['country'] = cand; kind = 'country_noprov'; self.diag['label_in_province_slot'] += 1
                else:
                    kind = 'article_total' if ctx.get('country') == 'TOTAL' else 'country_total'
            if not numeric and kind in ('detail', 'article_province_total'):
                self.diag['label_row_no_values'] += 1
            # value column dropped, duty cell fused: 'Lbs. | 185,147 | Lbs. | 189,812 | 19,490 3,898 00' = qty_imp,
            # [val_imp lost], qty_efc, val_efc + duty in one cell (quantity slots hold unit tokens or blanks)
            if kind in ('detail', 'article_province_total', 'country_total', 'article_total') and nums[0] is None and nums[2] is None \
                    and nums[1] is not None and nums[3] is not None and flags[4] == 'fused':
                toks = split_numeric_tokens(vals_raw[4], cents_ok=True)
                if toks and len(toks) == 3 and re.fullmatch(r'\d\d', toks[2]):
                    toks = [toks[0], toks[1] + ' ' + toks[2]]                # '19,490 | 3,898 | 00' -> value + cents duty
                if toks and len(toks) == 2:
                    ve = parse_num(toks[0], cents_ok=False)[0]; du = parse_num(toks[1], cents_ok=True)[0]
                    if ve is not None and du is not None and ve > 0 and 0.003 <= du / ve <= 1.0:     # a real duty on that value
                        qi, qe = nums[1], nums[3]
                        vi = ve if abs(qi - qe) < 0.5 else None
                        nums = [qi, vi, qe, ve, du]
                        flags = list(flags); flags[1] = 'value_imp_from_efc' if vi is not None else 'value_lost'; flags[4] = ''
                        self.diag['fused_efc_duty_split'] += 1
            # value column lost: the unit token sits in the quantity slot and the QUANTITY was read as the value
            # ('Lbs. | 916,211 | Lbs. | 916,211 | 1,717 75'); on a dutiable line the duty/value ratio gives it away
            # values printed in the QUANTITY slots with the value slots blank ('| Quebec | 6,764 |  | 7,563 |  | 2,268 72'
            # on silk, a value-only article): the duty/value ratio is a plausible ad valorem rate, the article has no unit
            if kind in ('detail', 'article_province_total', 'country_total', 'article_total') and ctx.get('unit') is None \
                    and nums[1] is None and nums[3] is None and nums[0] is not None and nums[2] is not None and nums[2] > 0 \
                    and not vals_raw[1].strip().strip('.') and not vals_raw[3].strip().strip('.') \
                    and (ctx.get('section') == 'FREE' or (nums[4] is not None and 0.04 <= nums[4] / nums[2] <= 0.6)):
                nums = [None, nums[0], None, nums[2], nums[4]]
                flags = list(flags); flags[0] = flags[2] = 'blank'; flags[1] = flags[3] = 'value_in_qty_slot'
                self.diag['value_in_qty_slot'] += 1
            qty_shape = nums[0] is None and nums[1] is not None and nums[1] > 0 and ctx.get('section') == 'DUTIABLE' \
                and nums[4] is not None and nums[4] > 0 and nums[4] / nums[1] < 0.005
            def _not_ad_valorem(r):
                # a duty/value ratio that no ad valorem rate of the period explains (5 .. 40 %, by 2.5) — so the
                # 'value' must be a quantity (specific duty per lb/gal): 2c/lb on 67,855 lb = 2.0 %
                return r < 0.045 and all(abs(r - x / 100.0) > 0.004 for x in (5, 7.5, 10, 12.5, 15, 17.5, 20, 22.5, 25, 27.5, 30, 32.5, 35, 40))
            both_units = is_unit_token(vals_raw[0]) and is_unit_token(vals_raw[2]) and nums[1] is not None and nums[3] is not None \
                and nums[1] > 0 and nums[3] > 0 and nums[4] is not None and ctx.get('section') == 'DUTIABLE' \
                and _not_ad_valorem(nums[4] / nums[3]) and _not_ad_valorem(nums[4] / nums[1])
            rate = ctx.get('qty_only_rate')
            same_rate = rate is not None and ctx.get('qty_only_block') == ctx.get('block_id') and nums[1] is not None and nums[1] > 0 \
                and nums[4] is not None and nums[0] is None and nums[2] is None and not vals_raw[0].strip().strip('.') and not vals_raw[2].strip().strip('.') \
                and abs(nums[4] / nums[1] - rate) <= 0.25 * rate
            if kind in ('detail', 'article_province_total') and is_unit_token(vals_raw[0]) and (qty_shape or both_units):
                # 'Lbs. | 56,585 | Lbs. | 67,855 | 1,357 10' (starch, 2c/lb): unit tokens in BOTH quantity slots and the
                # numbers after them are the quantities; the value column is lost
                ctx['qty_only_rate'] = (nums[4] / nums[3]) if (nums[3] or 0) > 0 else (nums[4] / nums[1] if nums[4] is not None else None)
                nums = [nums[1], None, nums[3] if is_unit_token(vals_raw[2]) else nums[2], None, nums[4]]
                flags = list(flags); flags[1] = flags[3] = 'value_lost'
                self.diag['value_column_lost'] += 1
                ctx['qty_only_block'] = ctx.get('block_id')
            elif kind in ('detail', 'article_province_total', 'country_total', 'article_total') and (qty_shape or same_rate) \
                    and ctx.get('qty_only_block') == ctx.get('block_id') and not vals_raw[0].strip().strip('.') and not vals_raw[2].strip().strip('.'):
                # the rest of a block whose value column is blank throughout ('| | 337,647 | | 337,647 | 1,350 58':
                # strawboard 1889 — quantities in lbs, duty 0.4% of them): same shape, same block, same treatment
                nums = [nums[1], None, nums[3], None, nums[4]]
                flags = list(flags); flags[1] = flags[3] = 'value_lost'
                self.diag['value_column_lost_block'] += 1
            ctx['last_prov'] = prov if kind in ('detail', 'detail_lostlabel', 'article_province_total') else None
            ctx['expect_label'] = kind in ('country_total', 'article_total') and numeric
            self._emit(fy, vol, seq, ri, ctx, kind, prov, nums, flags, vals_raw, texts)
            if deferred:
                self._article(ctx, deferred); ctx['country'] = None
        self._fix_duty_slot(n_start)
        self._fix_free_scramble(n_start)

    def _fix_free_scramble(self, n_start):
        """FREE goods with a unit (1885 gums page): the OCR kept ONE number per printed row ('Ontario | Lbs. | 489 |
        Lbs. | 489') and appended the rest of the block's numbers as label-less rows, the last two being the block's
        printed qty and value totals (GB 68,881 lbs / \$9,490; US 651,628 / 114,435; grand 791,568 / 127,068 = the
        Summary Statement). Which labelled number is a quantity and which a value is unknowable, so the details are
        nulled and one province-'?' row carries the printed country value; the Total block likewise."""
        KINDS = ('detail', 'article_province_total')
        TAILS = ('country_total', 'article_total')
        rows = self.rows[n_start:]
        if not rows or rows[0].get('regime') != 'C': return
        def single(x):
            return x['qty_imp'] is None and x['qty_efc'] is None and x['val_imp'] is not None and x['val_imp'] == x['val_efc'] and x['duty'] is None
        def unit_in_qty(x):
            c = (x.get('raw') or '').split(' | ')
            return len(c) >= 5 and (is_unit_token(c[-5]) or is_unit_token(c[-3]))
        out = []; i = 0; changed = False; fixed_blocks = set()
        while i < len(rows):
            r = rows[i]
            if r.get('section') != 'FREE' or r['row_kind'] not in KINDS or r['province'] not in PROVINCE_ORDER:
                out.append(r); i += 1; continue
            j = i
            while j < len(rows) and rows[j].get('section') == 'FREE' and rows[j]['row_kind'] in KINDS \
                    and rows[j]['block_id'] == r['block_id'] and rows[j]['country'] == r['country']:
                j += 1
            k = j
            while k < len(rows) and rows[k]['row_kind'] in TAILS and rows[k]['block_id'] == r['block_id'] \
                    and (rows[k]['country'] == r['country'] or r['country'] == 'TOTAL'):
                k += 1
            det = rows[i:j]; tail = rows[j:k]
            ok = det and tail and all(single(x) for x in det + tail) and (any(unit_in_qty(x) for x in det) or r['block_id'] in fixed_blocks) \
                and (len(tail) >= 2 or len(det) == 1)
            qty_kept = False
            if ok and len(tail) >= 2:
                # a run of trailing rows that CLOSES on the first (country total then lost-label provinces) is the
                # lost-label class, not a scramble; a tail of exactly two where the first is the sum of the details is
                # the value column lost with the QUANTITIES kept (1880 seal oil: 99,750 + 4,866 = 104,616 galls, $52,327)
                sd = sum(x['val_imp'] for x in det); st = sum(x['val_imp'] for x in tail[1:])
                if abs(tail[0]['val_imp'] - (sd + st)) <= 0.005 * max(1.0, tail[0]['val_imp']): ok = False
                elif len(tail) == 2 and abs(tail[0]['val_imp'] - sd) <= 0.005 * max(1.0, sd): qty_kept = True
            if ok and len(tail) == 1 and len(det) == 1 and tail[0]['val_imp'] >= det[0]['val_imp']: ok = False
            if not ok:
                out.extend(rows[i:k]); i = k; continue
            fixed_blocks.add(r['block_id'])
            vtot = tail[-1]['val_imp']; qtot = tail[-2]['val_imp'] if len(tail) >= 2 else None
            for x in det:
                if qty_kept:
                    x['qty_imp'] = x['qty_efc'] = x['val_imp']
                else:
                    x['qty_imp'] = x['qty_efc'] = None
                x['val_imp'] = x['val_efc'] = None
                x['flags'] = (x['flags'] + ',' if x['flags'] else '') + ('value_column_lost_free' if qty_kept else 'qty_value_scrambled')
            syn = dict(det[0]); syn['province'] = '?'; syn['val_imp'] = syn['val_efc'] = vtot; syn['qty_imp'] = syn['qty_efc'] = None
            syn['flags'] = 'scrambled_block_total'; syn['raw'] = tail[-1]['raw']
            tot = dict(tail[-1]); tot['val_imp'] = tot['val_efc'] = vtot; tot['qty_imp'] = tot['qty_efc'] = qtot
            tot['flags'] = (tot['flags'] + ',' if tot['flags'] else '') + 'scrambled_block_total'
            out.extend(det); out.append(syn); out.append(tot)
            self.diag['qty_value_scrambled_block'] += 1; changed = True
            i = k
        if changed:
            self.rows[n_start:] = out

    def _fix_single_detail_chain(self, n_start):
        """A tail chain of single-detail countries whose 'country totals' fail closure: the unlabelled value
        row after each single-detail country is really the NEXT country's value, and the last country's
        on-row value is the article grand total (1889 diamonds: 'Belgium | N.B. | 920' then 128,105 —
        France Ontario's value; 'France | Ontario | 27' then 12,541 — Holland Ontario's; 'Holland |
        Ontario | 206,279' = the grand total; the on-row 27 is France's residual second detail).  Gate:
        the re-read block total equals the grand EXACTLY (<=0.5).  Verified by the abstract: France
        Ontario free 209,339 and Holland Ontario free 73,723 both close to the cent."""
        rows = self.rows[n_start:]
        if not rows or rows[0].get('regime') != 'C': return
        VAL = ('unit', 'qty_brit', 'qty_foreign', 'qty_land', 'qty_imp', 'val_imp', 'qty_efc', 'val_efc', 'duty')
        blocks = {}; order = []
        for r in rows:
            b = r['block_id']
            if b not in blocks: blocks[b] = []; order.append(b)
            blocks[b].append(r)
        for b in order:
            g = blocks[b]
            if any(x['row_kind'] in ('article_total', 'article_province_total', 'article_total_fused') for x in g):
                continue
            seq = []; cur = None; ok = True
            for r in g:
                k = r['row_kind']
                if k == 'detail' and r['country'] not in (None, '', '?', 'TOTAL'):
                    if cur and cur[0] == r['country']: cur[1].append(r)
                    else:
                        if cur: seq.append(cur)
                        cur = [r['country'], [r], None]
                elif k == 'country_total' and cur and r['country'] in (cur[0], None, ''):
                    cur[2] = r; seq.append(cur); cur = None
                elif k == 'summary':
                    continue
                else:
                    ok = False; break
            if cur: seq.append(cur)
            if not ok or len(seq) < 3: continue
            def tot_of(e):
                c, dets, t = e
                if t is not None and t['val_efc'] is not None: return t['val_efc']
                return sum(d['val_efc'] or 0 for d in dets)
            def bad_single(e):
                c, dets, t = e
                return len(dets) == 1 and t is not None and t['val_efc'] and dets[0]['val_efc'] is not None \
                    and abs(t['val_efc'] - dets[0]['val_efc']) > 0.05 * t['val_efc']
            last = seq[-1]
            if not (len(last[1]) == 1 and last[2] is None and last[1][0]['val_efc']): continue
            s = len(seq) - 2
            while s >= 0 and bad_single(seq[s]): s -= 1
            s += 1
            if s > len(seq) - 2: continue
            chain = seq[s:-1]; prior = seq[:s]; m = len(chain)
            grand = last[1][0]['val_efc']
            tot = sum(tot_of(e) for e in prior) + (chain[0][1][0]['val_efc'] or 0)
            for i in range(1, m):
                tot += (chain[i - 1][2]['val_efc'] or 0) + (chain[i][1][0]['val_efc'] or 0)
            tot += chain[m - 1][2]['val_efc'] or 0
            if grand <= 0 or abs(tot - grand) > 0.5: continue
            kill = []; ins = []
            for i in range(1, m):
                d = chain[i][1][0]
                x_pay = {c: d[c] for c in VAL}
                for c in VAL: d[c] = chain[i - 1][2][c]
                d['flags'] = (d['flags'] + ',' if d['flags'] else '') + 'single_detail_chain'
                extra = dict(d); extra.update(x_pay)
                extra['province'] = '?'; extra['row_kind'] = 'detail'; extra['flags'] = 'single_detail_chain_residual'
                ins.append((d, extra)); kill.append(chain[i - 1][2])
            d_last = last[1][0]
            grand_pay = {c: d_last[c] for c in VAL}
            for c in VAL: d_last[c] = chain[m - 1][2][c]
            d_last['flags'] = (d_last['flags'] + ',' if d_last['flags'] else '') + 'single_detail_chain'
            kill.append(chain[m - 1][2])
            at = dict(d_last); at.update(grand_pay)
            at['row_kind'] = 'article_total'; at['country'] = None; at['province'] = None
            at['flags'] = 'single_detail_chain_grand'
            ins.append((d_last, at))
            chain[0][1][0]['flags'] = (chain[0][1][0]['flags'] + ',' if chain[0][1][0]['flags'] else '') + 'single_detail_chain'
            killset = {id(x) for x in kill}
            self.rows = [r for r in self.rows if id(r) not in killset]
            for after, new in ins:
                self.rows.insert(self.rows.index(after) + 1, new)
            self.diag['single_detail_chain'] += 1

    def _fix_grand_total_on_country_row(self, n_start):
        """An article with no Total block whose LAST row is a country-labelled detail equal (within 5 %) to the sum
        of the other countries' totals: the grand total rode on that country's label ('“ Holland | Ontario | 206,279'
        on 1889 diamonds = GB 46,878 + US 17,808 + Belgium 128,105 + France 12,541 + Holland 947; the abstract gives
        Holland Ontario free 73,723 in all). The row becomes the article total; the residual is the country's own."""
        rows = self.rows[n_start:]
        if not rows or rows[0].get('regime') != 'C': return
        blocks = defaultdict(list)
        for x in rows: blocks[x['block_id']].append(x)
        for b, g in blocks.items():
            if any(x['row_kind'] in ('article_total', 'article_province_total', 'article_total_fused') for x in g): continue
            last = g[-1]
            if last['row_kind'] != 'detail' or last['val_efc'] is None or last['country'] in (None, '', '?', 'TOTAL') or not last['province']: continue
            others = defaultdict(list)
            for x in g:
                if x['country'] not in (last['country'], None, '', '?', 'TOTAL'): others[x['country']].append(x)
            if len(others) < 2: continue
            tot = 0.0
            for c, xs in others.items():
                ct = [x for x in xs if x['row_kind'] == 'country_total' and x['val_efc'] is not None]
                tot += ct[-1]['val_efc'] if ct else sum(x['val_efc'] or 0 for x in xs if x['row_kind'] == 'detail')
            if tot <= 0 or not (tot <= last['val_efc'] <= 1.05 * tot): continue
            resid = last['val_efc'] - tot
            own = dict(last); own['province'] = '?'; own['val_imp'] = own['val_efc'] = resid if resid > 0 else None
            own['qty_imp'] = own['qty_efc'] = None; own['flags'] = 'country_residual_from_grand_total'
            last['row_kind'] = 'article_total'; last['country'] = None; last['province'] = None
            last['flags'] = (last['flags'] + ',' if last['flags'] else '') + 'grand_total_on_country_row'
            self.diag['grand_total_on_country_row'] += 1
            if resid > 0:
                idx = self.rows.index(last)
                self.rows.insert(idx, own)

    def _fix_noprov_slip_down(self, n_start):
        """The label column slipped DOWN one row against the values, page-wide: the country label row
        (country_noprov) carries the FIRST province's values, each province label carries the PREVIOUS
        province's values, and the last province-labelled row is really the country total (1883 champagne
        page t433: France 'British Columbia' 5,868/60,974/58,438 = the France total; TOTAL block closes
        exactly in all three columns under this reading for GB, US, France, Germany).  Proof: the noprov
        values + all details but the last sum EXACTLY to the last detail in val_efc AND a second column
        (strong); efc-only blocks (Spain: qty/val cells ditto-damaged) accepted when the same table holds
        >=2 strong blocks.  Fix: shift payloads down one, append the country_total row."""
        rows = self.rows[n_start:]
        if not rows or rows[0].get('regime') != 'C': return
        rank = {p: i for i, p in enumerate(PROVINCE_ORDER)}
        VAL = ('unit', 'qty_brit', 'qty_foreign', 'qty_land', 'qty_imp', 'val_imp', 'qty_efc', 'val_efc', 'duty')
        cands = []
        i = 0
        while i < len(rows):
            r = rows[i]
            if r['row_kind'] != 'country_noprov' or r['country'] in (None, '', '?', 'TOTAL') or r['val_efc'] is None:
                i += 1; continue
            j = i + 1; details = []
            while j < len(rows) and rows[j]['row_kind'] == 'detail' and rows[j]['country'] == r['country'] \
                    and rows[j]['block_id'] == r['block_id'] and rows[j]['province'] in rank:
                details.append(rows[j]); j += 1
            # a printed country_total right after the run means the block is whole - not this class
            if j < len(rows) and rows[j]['row_kind'] == 'country_total' and rows[j]['block_id'] == r['block_id'] \
                    and rows[j]['country'] in (r['country'], None, '', '?'):
                i = j; continue
            rk = [rank[x['province']] for x in details]
            if len(details) >= 2 and rk == sorted(rk) and len(set(rk)) == len(rk):
                def ex(col):
                    L = details[-1][col]
                    if L is None or not isinstance(L, (int, float)) or L <= 0: return False
                    s = (r[col] or 0) + sum(d[col] or 0 for d in details[:-1] if isinstance(d[col], (int, float)) or d[col] is None)
                    return s > 0 and abs(s - L) <= 0.5
                if ex('val_efc'):
                    strong = ex('val_imp') or ex('qty_imp')
                    cands.append((r['table_seq'], strong, r, details))
            i = j
        n_strong = defaultdict(int)
        for tseq, strong, _, _ in cands:
            if strong: n_strong[tseq] += 1
        for tseq, strong, n0, details in cands:
            if not (strong or n_strong[tseq] >= 2): continue
            pay = [{c: x[c] for c in VAL} for x in [n0] + details[:-1]]
            tot_pay = {c: details[-1][c] for c in VAL}
            for d, p in zip(details, pay):
                for c in VAL: d[c] = p[c]
                d['flags'] = (d['flags'] + ',' if d['flags'] else '') + 'noprov_slip_down'
            tot = dict(details[-1]); tot.update(tot_pay)
            tot['row_kind'] = 'country_total'; tot['province'] = None
            tot['flags'] = 'noprov_slip_down_total'
            for c in VAL: n0[c] = None
            n0['flags'] = (n0['flags'] + ',' if n0['flags'] else '') + 'noprov_slip_down_label'
            self.rows.insert(self.rows.index(details[-1]) + 1, tot)
            self.diag['noprov_slip_down'] += 1

    def _fix_province_order(self, n_start):
        """The provinces are printed in one fixed order (Ontario, Quebec, N.S., N.B., Manitoba, B.C., P.E.I., N.W.T.).
        A block whose labels are that order with ONE adjacent pair swapped ('Quebec, Ontario, Nova Scotia, ...' on the
        1887 Spanish West Indies cigars block) has its labels scrambled by the OCR while the values stayed in printed
        order — the abstract confirms the first row is Ontario's. Swap the two labels back."""
        rows = self.rows[n_start:]
        if not rows or rows[0].get('regime') != 'C': return
        rank = {p: i for i, p in enumerate(PROVINCE_ORDER)}
        cands = []; dupcands = []
        i = 0
        while i < len(rows):
            r = rows[i]
            if r['row_kind'] not in ('detail', 'article_province_total') or r['province'] not in rank:
                i += 1; continue
            j = i
            while j < len(rows) and rows[j]['row_kind'] in ('detail', 'article_province_total') and rows[j]['province'] in rank \
                    and rows[j]['block_id'] == r['block_id'] and rows[j]['country'] == r['country']:
                j += 1
            grp = rows[i:j]
            # the swap itself makes the rows after it look like a new country with its label lost ('Quebec' then
            # 'Ontario, Nova Scotia, ...' -> detail_lostlabel '?'): include that run when a country total closes over all
            k = j; lost = []
            while k < len(rows) and rows[k]['row_kind'] == 'detail_lostlabel' and rows[k]['country'] in (None, '', '?') \
                    and rows[k]['province'] in rank and rows[k]['block_id'] == r['block_id']:
                lost.append(rows[k]); k += 1
            if lost and r['row_kind'] == 'detail' and r['country'] not in (None, '', '?', 'TOTAL'):
                tot = rows[k] if k < len(rows) and rows[k]['row_kind'] == 'country_total' and rows[k]['block_id'] == r['block_id'] \
                    and rows[k]['country'] in (r['country'], None, '', '?') else None
                comb = grp + lost
                def _sum(col): return sum(x[col] or 0 for x in comb)
                closes = tot is not None and any(tot[c] is not None and tot[c] > 0 and abs(_sum(c) - tot[c]) <= 0.005 * tot[c] for c in ('val_imp', 'val_efc'))
                rk2 = [rank[x['province']] for x in comb]
                swap_ok = False
                if closes and not (rk2 == sorted(rk2) and len(set(rk2)) == len(rk2)):
                    for a in range(len(rk2) - 1):
                        rr = rk2[:]; rr[a], rr[a + 1] = rr[a + 1], rr[a]
                        if rr == sorted(rr) and len(set(rr)) == len(rr): swap_ok = True; break
                if swap_ok:
                    for x in lost:
                        x['country'] = r['country']; x['row_kind'] = 'detail'
                        x['flags'] = (x['flags'] + ',' if x['flags'] else '') + 'lost_label_after_swap'
                    grp = comb; j = k
            rk = [rank[x['province']] for x in grp]
            if os.environ.get('CA_DEBUG_TABLE') == f"{r['fiscal_year']}:{r['table_seq']}":
                print('PROVGRP', [(x['row_seq'], x['row_kind'], x['block_id'], x['country'], x['province']) for x in grp], 'NEXT', [(x['row_seq'], x['row_kind'], x['country'], x['province']) for x in rows[j:j+3]], file=sys.stderr)
            if len(grp) >= 2 and not (rk == sorted(rk) and len(set(rk)) == len(rk)):
                for a in range(len(rk) - 1):
                    rr = rk[:]; rr[a], rr[a + 1] = rr[a + 1], rr[a]
                    if rr == sorted(rr) and len(set(rr)) == len(rr):
                        cands.append((r['block_id'], r['country'], grp[a], grp[a + 1]))
                        break
                else:
                    # one label DUPLICATED ('Ontario, Quebec, N.S., N.B., Ontario, B.C., ...' on the 1883 cassimeres
                    # Total block; 'Quebec, Quebec, N.S., ...' on 1880 steel rails): the copy that breaks the order is
                    # a misread of the one province that fits its slot
                    dups = [v for v in set(rk) if rk.count(v) == 2]
                    if len(dups) == 1 and len(rk) - 1 == len(set(rk)):
                        pos = [q for q, v in enumerate(rk) if v == dups[0]]
                        for bad in pos:
                            rest = rk[:bad] + rk[bad + 1:]
                            if rest != sorted(rest): continue
                            lo = rk[bad - 1] if bad > 0 else -1
                            hi = rk[bad + 1] if bad + 1 < len(rk) else len(PROVINCE_ORDER)
                            gap = [v for v in range(lo + 1, hi) if v not in rk]
                            if len(gap) == 1:
                                dupcands.append((r['block_id'], r['country'], grp[bad], PROVINCE_ORDER[gap[0]]))
                                break
            i = j
        for blk_id, country, x, newp in dupcands:
            verdict = self._relabel_verdict(rows, blk_id, country, x, newp)
            if verdict is True:
                x['province'] = newp
                x['flags'] = (x['flags'] + ',' if x['flags'] else '') + 'province_dup_relabelled'
                self.diag['province_dup_relabelled'] += 1
            else:
                x['flags'] = (x['flags'] + ',' if x['flags'] else '') + 'province_dup_unarbitrated'
                self.diag['province_dup_unarbitrated'] += 1
        # the OCR may have swapped the two LABELS (values in printed order: 1887 cigars, abstract-proven) or the two
        # whole ROWS (1883 salt, also abstract-proven) — arbitrate by the article's Total block: details per province
        # must sum to the printed province totals. Total-block candidates first (judged by the details of the
        # blocks that are NOT themselves candidates), then the country blocks against the corrected Totals.
        cand_ids = {id(x) for _, _, x1, x2 in cands for x in (x1, x2)}
        for blk_id, country, x1, x2 in sorted(cands, key=lambda c: 0 if c[1] == 'TOTAL' else 1):
            verdict = self._swap_verdict(rows, blk_id, country, x1, x2, cand_ids)
            if verdict is True:
                x1['province'], x2['province'] = x2['province'], x1['province']
                for x in (x1, x2):
                    x['flags'] = (x['flags'] + ',' if x['flags'] else '') + 'province_order_swapped'
                self.diag['province_order_swapped'] += 1
            else:
                for x in (x1, x2):
                    x['flags'] = (x['flags'] + ',' if x['flags'] else '') + ('province_rows_swapped' if verdict is False else 'province_order_unarbitrated')
                self.diag['province_rows_swapped' if verdict is False else 'province_order_unarbitrated'] += 1

    def _relabel_verdict(self, rows, block_id, country, x, newp):
        """x carries a duplicated province label; True when relabelling it newp closes the article's Total block
        better than leaving two rows under the old label."""
        blk = [b for b in rows if b['block_id'] == block_id]
        oldp = x['province']
        def val(b, c): return b[c] if b[c] is not None else 0.0
        COLS = ('val_imp', 'val_efc')
        if country == 'TOTAL':
            S = {P: {c: sum(val(b, c) for b in blk if b['row_kind'] == 'detail' and b['province'] == P) for c in COLS} for P in (oldp, newp)}
            if not any(b['row_kind'] == 'detail' and b['province'] in (oldp, newp) for b in blk): return None
            same = [b for b in blk if b['row_kind'] == 'article_province_total' and b['province'] == oldp and b is not x]
            keep = sum(abs(S[oldp][c] - sum(val(b, c) for b in same) - val(x, c)) + abs(S[newp][c]) for c in COLS)
            rel = sum(abs(S[oldp][c] - sum(val(b, c) for b in same)) + abs(S[newp][c] - val(x, c)) for c in COLS)
        else:
            T = {P: [b for b in blk if b['row_kind'] == 'article_province_total' and b['province'] == P] for P in (oldp, newp)}
            if not (T[oldp] or T[newp]): return None
            other = {P: {c: sum(val(b, c) for b in blk if b['row_kind'] == 'detail' and b['province'] == P and (b['country'] != country or b is not x) and b is not x) for c in COLS} for P in (oldp, newp)}
            def resid(lab):
                tot = 0.0
                for P in (oldp, newp):
                    if T[P]:
                        for c in COLS: tot += abs(val(T[P][0], c) - other[P][c] - (val(x, c) if lab == P else 0.0))
                return tot
            keep = resid(oldp); rel = resid(newp)
        if rel < keep * 0.5: return True
        return False

    def _swap_verdict(self, rows, block_id, country, x1, x2, cand_ids=()):
        """True = swap the labels (closes better), False = keep (rows were swapped whole), None = no arbiter."""
        blk = [x for x in rows if x['block_id'] == block_id]
        P1, P2 = x1['province'], x2['province']
        def val(x, c): return x[c] if x[c] is not None else 0.0
        COLS = ('val_imp', 'val_efc')
        if country == 'TOTAL':
            S = {P: {c: sum(val(x, c) for x in blk if x['row_kind'] == 'detail' and x['province'] == P and id(x) not in cand_ids) for c in COLS} for P in (P1, P2)}
            have = {P: any(x['row_kind'] == 'detail' and x['province'] == P and id(x) not in cand_ids for x in blk) for P in (P1, P2)}
            if not (have[P1] or have[P2]): return None
            keep = sum(abs(S[P1][c] - val(x1, c)) + abs(S[P2][c] - val(x2, c)) for c in COLS)
            swap = sum(abs(S[P2][c] - val(x1, c)) + abs(S[P1][c] - val(x2, c)) for c in COLS)
        else:
            T = {P: [x for x in blk if x['row_kind'] == 'article_province_total' and x['province'] == P] for P in (P1, P2)}
            if not (T[P1] or T[P2]): return None
            other = {P: {c: sum(val(x, c) for x in blk if x['row_kind'] == 'detail' and x['province'] == P and x['country'] != country) for c in COLS} for P in (P1, P2)}
            def resid(lab1, lab2):
                tot = 0.0
                for P, x in ((lab1, x1), (lab2, x2)):
                    if T[P]:
                        for c in COLS: tot += abs(val(T[P][0], c) - other[P][c] - val(x, c))
                return tot
            keep = resid(P1, P2); swap = resid(P2, P1)
        if swap < keep * 0.5: return True
        if keep <= swap: return False
        return None

    def _fix_duty_slot(self, n_start):
        """Regime C, DUTIABLE: the duty column is always printed with cents. A run of rows (one country block, or
        the Total block) whose 'duty' cells are ALL plain integers, with unit tokens in the quantity slots, is
        '[Feet.] qty | [blank] | qty | VALUE' — the value column lost and the value read into the duty slot (1889
        drawing tubing, brown blanks; 1880 boots and shoes Total block). The real duties sometimes follow as lone
        cents-bearing rows ('| | | | | 906 30' = 10 % of 9,063): one such row is the block total's duty, a run as long
        as the block gives every row its duty. A lone one- or two-digit cents-less 'duty' larger than the row's value
        ('| 2 | ..... | 2 | 60') is the cents with the '0 ' lost."""
        KINDS = ('detail', 'country_total', 'article_province_total', 'article_total', 'country_noprov')
        rows = self.rows[n_start:]
        if not rows or rows[0].get('regime') != 'C': return
        def dcell(x):
            c = (x.get('raw') or '').split(' | ')
            return c[-1].strip() if c else ''
        def nocents(x):
            return x['duty'] is not None and bool(re.fullmatch(r'\d{1,3}(,\d{3})*|\d+', dcell(x)))
        def duty_only(x):
            return x['duty'] is not None and all(x[c] is None for c in ('qty_imp', 'val_imp', 'qty_efc', 'val_efc')) \
                and re.fullmatch(r'[\d,]+ \d\d', dcell(x)) is not None
        def unit_in_qty(x):
            c = (x.get('raw') or '').split(' | ')
            return len(c) >= 5 and (is_unit_token(c[-5]) or is_unit_token(c[-3]))
        drop = set()
        fixed_blocks = set()
        i = 0
        while i < len(rows):
            r = rows[i]
            if r.get('section') != 'DUTIABLE' or r['row_kind'] not in KINDS:
                i += 1; continue
            j = i
            while j < len(rows) and rows[j].get('section') == 'DUTIABLE' and rows[j]['row_kind'] in KINDS \
                    and rows[j]['block_id'] == r['block_id'] and rows[j]['country'] == r['country']:
                j += 1
            k = j
            while k > i and duty_only(rows[k - 1]): k -= 1
            main = rows[i:k]; tail = rows[k:j]
            shape = [x for x in main if x['val_imp'] is not None and x['val_efc'] is not None and x['duty'] is not None
                     and x['qty_imp'] is None and x['qty_efc'] is None and nocents(x)]
            # a total row whose duty cell was dropped is already 'qty | value | qty | value' (duty None) and may close the run
            proper = [x for x in main if x not in shape and x['qty_imp'] is not None and x['val_imp'] is not None and x['duty'] is None
                      and x['row_kind'] in ('country_total', 'article_total', 'article_province_total')]
            both_units = any(is_unit_token(c[-5]) and is_unit_token(c[-3]) for c in [(x.get('raw') or '').split(' | ') for x in main] if len(c) >= 5)
            if main and shape and len(shape) + len(proper) == len(main) \
                    and (any(unit_in_qty(x) for x in main) or tail or r['block_id'] in fixed_blocks) \
                    and (len(main) >= 2 or tail or both_units):
                fixed_blocks.add(r['block_id'])
                for x in shape:
                    qi, qe, ve = x['val_imp'], x['val_efc'], x['duty']
                    x['qty_imp'], x['qty_efc'], x['val_efc'], x['duty'] = qi, qe, ve, None
                    x['val_imp'] = ve if qi == qe else None
                    x['flags'] = (x['flags'] + ',' if x['flags'] else '') + 'value_in_duty_slot'
                    self.diag['value_in_duty_slot'] += 1
                if tail:
                    if len(tail) == len(main):
                        for x, t in zip(main, tail): x['duty'] = t['duty']
                    elif main[-1]['row_kind'] in ('country_total', 'article_total', 'article_province_total', 'country_noprov'):
                        main[-1]['duty'] = tail[-1]['duty']
                    for t in tail: drop.add(id(t))
                    self.diag['value_in_duty_slot_duty_row'] += len(tail)
            else:
                for x in main:
                    if x['duty'] is not None and re.fullmatch(r'\d{1,2}', dcell(x)) and (x['val_efc'] is None or x['duty'] > x['val_efc']):
                        x['duty'] = x['duty'] / 100.0
                        x['flags'] = (x['flags'] + ',' if x['flags'] else '') + 'duty_cents_only'
                        self.diag['duty_cents_only'] += 1
            i = j
        if drop:
            self.rows[n_start:] = [x for x in rows if id(x) not in drop]

    # ---------------------------------------------------------------- shared A/B helpers
    @staticmethod
    def _trim_trailing_empty(texts, NV):
        # a trailing '' cell after a cents-looking duty cell is an OCR artefact, not the duty column
        while len(texts) > NV + 1 and texts[-1].strip() == '' and re.search(r'\d \d\d$', texts[-2].strip()):
            texts = texts[:-1]
        return texts

    def _expand_fused(self, vals_raw, NV, labels_avail):
        """vals_raw: NV value cells, some holding n whitespace-separated numbers (n country rows fused).
        Returns list of n value-lists when consistent and n <= labels available (+1 for the row's own), else None."""
        toks = [split_numeric_tokens(v, cents_ok=(i == NV - 1)) for i, v in enumerate(vals_raw)]
        if any(t is None for t in toks):
            return None
        ns = set(len(t) for t in toks if len(t) > 1)
        if len(ns) != 1:
            return None
        n = ns.pop()
        if n > labels_avail:
            return None
        rows = []
        for r in range(n):
            rows.append([t[r] if len(t) == n else (t[0] if r == n - 1 else '.....') for t in toks])
        self.diag['fused_rows_expanded'] += n
        return rows

    # ---------------------------------------------------------------- regime B (1877)
    def parse_table_B(self, fy, vol, seq, body, ctx):
        n0 = len(body)
        body = unfuse_rows(body, self.vocab | set(PROVINCE_KEYS.values()) | set(PROVINCE_ORDER), [0, 1], 0)
        if len(body) != n0: self.diag['unfused_rows'] += len(body) - n0
        NV = 5
        # First pass: collect rows as (labels, vals). Labels may be ['article', 'country'] / ['country'] / [''].
        pending_labels = []     # country labels waiting for value rows (slip correction)
        for ri, cells in enumerate(body):
            texts = [c for _, _, c in cells]
            joined = ' '.join(texts).strip()
            if len(cells) < NV:
                if re.search(r'DUTY|FREE GOODS|PER CENT|SPECIFIC|AD VALOREM', joined, re.I):
                    self._section(ctx, joined)
                else:
                    self.diag['short_row'] += 1
                continue
            texts = self._trim_trailing_empty(texts, NV)
            vals_raw = texts[-NV:]; labels = texts[:-NV]
            parsed = [parse_num(v, cents_ok=(i == 4)) for i, v in enumerate(vals_raw)]
            nums = [p[0] for p in parsed]; flags = [p[1] for p in parsed]
            numeric = any(v is not None for v in nums)
            if len(labels) >= 2 and labels[0].strip() and re.search(r'DUTY|FREE GOODS|PER CENT|SPECIFIC|AD VALOREM', labels[0], re.I) and not numeric:
                self._section(ctx, labels[0]); labels = [''] + labels[1:]
            art = norm_label(labels[0]) if len(labels) >= 2 and labels[0].strip() else None
            cty = norm_label(labels[-1]) if labels and labels[-1].strip() else None
            if art:
                self._article(ctx, labels[0]); pending_labels = []
                self._units(ctx, vals_raw)
            if cty and not re.match(r'totals?\b', cty, re.I):
                pending_labels.append(cty)
            if not numeric:
                continue
            # fused value row (n countries' values in each cell): expand with the pending labels
            if 'fused' in flags:
                exp = self._expand_fused(vals_raw, NV, len(pending_labels))
                if exp:
                    for vr in exp:
                        pr = [parse_num(v, cents_ok=(i == NV - 1)) for i, v in enumerate(vr)]
                        country = pending_labels.pop(0); ctx['country'] = country
                        self._emit(fy, vol, seq, ri, ctx, 'detail', ctx.get('province'), [p[0] for p in pr], [p[1] for p in pr], vr, texts)
                    continue
            # a value row: pair with the oldest pending label (slip) else it is a subtotal
            if pending_labels:
                country = pending_labels.pop(0); ctx['country'] = country; kind = 'detail'
            else:
                kind = 'article_total'
            self._emit(fy, vol, seq, ri, ctx, kind, ctx.get('province'), nums, flags, vals_raw, texts)

    # ---------------------------------------------------------------- regime A (1869-73)
    def parse_table_A(self, fy, vol, seq, body, ctx):
        """Vessel-split layout.  Cells are frequently dropped or duplicated, so columns are anchored from the
        right: duty (cents-style) | value e.f.c. | qty e.f.c. | total value | total qty | [vessel cols...]."""
        n0 = len(body)
        body = unfuse_rows(body, self.vocab | set(PROVINCE_KEYS.values()) | set(PROVINCE_ORDER), [0, 1], 0)
        if len(body) != n0: self.diag['unfused_rows'] += len(body) - n0
        pending_labels = []
        for ri, cells in enumerate(body):
            texts = [c for _, _, c in cells]
            joined = ' '.join(texts).strip()
            # leading label cells = leading cells that are not numeric-ish
            nl = 0
            while nl < len(texts) and nl < 2 and parse_num(texts[nl])[0] is None and parse_num(texts[nl])[1] not in ('fused',) \
                    and not (parse_num(texts[nl])[1] == 'blank' and nl >= 1 and len(texts) - nl <= 9):
                nl += 1
            labels = texts[:nl]; vals = texts[nl:]
            while vals and vals[-1].strip() == '': vals = vals[:-1]
            if len(vals) < 4:
                if re.search(r'DUTY|FREE GOODS|PER CENT|SPECIFIC|AD VALOREM', joined, re.I) and not any(parse_num(v)[0] is not None for v in vals):
                    self._section(ctx, joined)
                elif labels and labels[0].strip() and not any(parse_num(v)[0] is not None for v in vals):
                    self._article(ctx, labels[0]); pending_labels = []
                    if len(labels) >= 2 and labels[1].strip(): pending_labels.append(norm_label(labels[1]))
                else:
                    self.diag['short_row'] += 1
                continue
            if len(vals) > 10:
                self.diag['scrambled_row'] += 1; continue
            parsedv = [parse_num(v, cents_ok=True) for v in vals]
            numeric = any(p[0] is not None for p in parsedv)
            art = norm_label(labels[0]) if len(labels) >= 1 and labels[0].strip() else None
            cty = norm_label(labels[-1]) if len(labels) == 2 and labels[-1].strip() else None
            if len(labels) == 1 and art and (art in self.vocab or re.match(r'totals?\b', art, re.I)):
                cty, art = art, None
            if art:
                if re.search(r'DUTY|FREE GOODS|PER CENT|SPECIFIC|AD VALOREM', art, re.I):
                    m = re.match(r'(.*?(?:DUTY|DUTIES|GOODS|CENT\.?|AD VALOREM)[^A-Za-z]*(?:—\s*Continued\.?)?)(.*)', art, re.I)
                    if m:
                        self._section(ctx, m.group(1)); art = m.group(2).strip() or None
                if art:
                    self._article(ctx, art); pending_labels = []
                self._units(ctx, vals)
            if cty and not re.match(r'totals?\b', cty, re.I):
                pending_labels.append(cty)
            if not numeric:
                continue
            # ---- align from the right
            last = vals[-1].strip()
            duty = None; rest = vals
            if re.search(r'\d \d\d$', last) or (ctx.get('section') != 'FREE' and parse_num(last)[1] == 'blank' and len(vals) >= 8):
                duty = vals[-1]; rest = vals[:-1]
            elif ctx.get('section') == 'FREE' and parse_num(last)[1] == 'blank':
                rest = vals[:-1]
            tail = rest[-4:] if len(rest) >= 4 else ([''] * (4 - len(rest)) + rest)
            vessel = rest[:-4] if len(rest) > 4 else []
            vessel = [''] * (3 - len(vessel)) + vessel[-3:]
            vals_raw = vessel + tail + [duty if duty is not None else '']
            # fused value row: expand with pending labels
            flags_probe = [parse_num(v, cents_ok=(i == 7))[1] for i, v in enumerate(vals_raw)]
            if 'fused' in flags_probe:
                self.diag['fused_cells'] += 1
                exp = self._expand_fused(vals_raw, 8, len(pending_labels))
                if exp:
                    for vr in exp:
                        pr = [parse_num(v, cents_ok=(i == 7)) for i, v in enumerate(vr)]
                        country = pending_labels.pop(0); ctx['country'] = country
                        self._emit(fy, vol, seq, ri, ctx, 'detail', ctx.get('province'), [p[0] for p in pr], [p[1] for p in pr], vr, texts)
                    continue
            parsed = [parse_num(v, cents_ok=(i == 7)) for i, v in enumerate(vals_raw)]
            nums = [p[0] for p in parsed]; flags = [p[1] for p in parsed]
            if pending_labels:
                country = pending_labels.pop(0); ctx['country'] = country; kind = 'detail'
            else:
                kind = 'article_total'
            self._emit(fy, vol, seq, ri, ctx, kind, ctx.get('province'), nums, flags, vals_raw, texts)

    # ---------------------------------------------------------------- helpers
    def _section(self, ctx, text):
        t = norm_label(text)
        if re.search(r'free', t, re.I):
            ctx['section'] = 'FREE'
        elif re.search(r'dutiable|duty|per cent|ad valorem|specific|du[ct]\w{2,6}\s+goods', t, re.I):
            ctx['section'] = 'DUTIABLE'
        new_label = re.sub(r'\s*[—-]\s*Con(tinued)?\.?\s*$', '', t, flags=re.I).strip()
        is_con = bool(re.search(r'Con(tinued)?\.?\s*$', t, re.I))
        if not is_con and new_label != ctx.get('section_label'):
            ctx['article_parents'] = []
            ctx['article'] = None
            ctx['country'] = None
        ctx['section_label'] = new_label

    def _article(self, ctx, text):
        """Split a heading into parent segments (ending ':', ';' or 'viz.') and a leaf (ending in a plain dash).
        'Breadstuffs, &c., viz:— Grain and products of:—Beans—' -> parents [Breadstuffs, &c., Grain and products of], leaf Beans."""
        text = re.sub(r'(\w)- (?=[a-z])', r'\1', text)      # 'raspber- ries' -> 'raspberries'
        t = re.sub(r'\s+', ' ', norm_label(text)).strip()
        t = re.sub(r'\s*[—-]\s*Con(tinued)?\.?$', '', t, flags=re.I)
        t = re.sub(r'^.*?\bGOODS\s*[—-]\s*Con(tinued)?\.?\s*', '', t, flags=re.I)      # 'FREE GOODS—Continued Bolting Cloths—'
        t = re.sub(r'^(?:—\s*)?Continued\.?\s*[—:]?\s*', '', t, flags=re.I)        # '—Continued. Settlers' effects'
        t = re.sub(r'^Con\.?\s+(?=[A-Z])', '', t)                                   # 'Con Books, &c.' (Continued, truncated)
        # mark parent boundaries, then split on dashes
        t = re.sub(r',?\s*viz\.?\s*[:;]?\s*[—–-]?', ' :— ', t, flags=re.I)
        t = re.sub(r'\s*[:;]\s*[—–-]', ' :— ', t)
        t = re.sub(r'\s*[:;]\s*$', ' :— ', t)
        t = re.sub(r'([a-z,])\s?:\s+(?=[A-Z])', r'\1 :— ', t)     # 'Wool, manufactures of: Cassimeres, cloths, &c' (no dash)
        t = re.sub(r'^\$\s*cts\.?\s*', '', t)                        # '$ cts Brass manufactures of' (unit header glued on)
        segs = []
        for piece in re.split(r'(:—|—)', t):
            segs.append(piece)
        parents = []; leaf = None; cur = ''
        for piece in segs:
            if piece == ':—':
                if cur.strip(' ,.-'): parents.append(cur.strip(' ,.-'))
                cur = ''
            elif piece == '—':
                if cur.strip(' ,.-'):
                    if leaf is not None:
                        parents.append(leaf)      # two plain-dash segments: the first was a parent
                    leaf = cur.strip(' ,.-')
                cur = ''
            else:
                cur += piece
        if cur.strip(' ,.-'):
            if leaf is not None: parents.append(leaf)
            leaf = cur.strip(' ,.-')
        if leaf is not None:
            leaf = re.sub(r'^Continued\.?\s+', '', leaf, flags=re.I).strip() or None
        # 'Feathers, ostrich and vulture, dressed— Great Britain': the trailing segment is the first country, not the leaf
        pending_country = None
        vocab = getattr(self, 'vocab', None) or SEED_COUNTRIES
        lf = leaf.rstrip(' .') if leaf else ''
        if leaf is not None and parents and lf in SEED_COUNTRIES:      # learned vocab is too polluted ('Wheat Flour') for this
            pending_country = leaf.rstrip(' .'); leaf = parents.pop()
        if not parents and leaf is None:
            return
        if re.search(r'recapitulation', text, re.I):
            ctx['recap'] = True; ctx['recap_done'] = False
        elif ctx.get('recap') and ctx.get('recap_done') and leaf is not None and not re.match(r'^(by\b|total)', leaf, re.I):
            ctx['recap'] = False          # the recapitulation closed with its Total; a new article follows on the page
            # ('By Provinces' / 'By Grades' sub-tables of a recapitulation each carry a Total and stay inside it)
        old_leaf = ctx.get('article')
        page_top_running = ctx.get('table_top') and ctx.get('country') not in (None, '', '?')
        if page_top_running and leaf is not None and not parents and old_leaf not in (None, '?'):
            # 'Grain and products of' / 'Meats' at a page top: the running PARENT head of the open article, printed
            # without its colon — it is a parent of the open article (or ends in 'of'), not a new leaf
            lk = leaf.lower().rstrip(' :;,')
            ntok = len(re.findall(r'[A-Za-z]+', leaf))
            short_parent_head = not re.search(r'[—–:;]\s*$', text.strip()) and ntok <= 4 and (lk.endswith(' of') or (ntok == 1 and leaf[:1].isupper()))
            def _is_parent(pp):
                # the page-top text IS the parent (or a shorter form of it) — not a leaf that merely contains it
                if ntok > len(re.findall(r'[A-Za-z]+', pp)) + 1: return False
                return fuzzy_jaccard(leaf, pp) >= 0.75 or token_containment(leaf, pp) >= 0.9
            if short_parent_head or any(_is_parent(pp) for pp in (ctx.get('article_parents') or [])):
                ctx['leaf_used'] = False
                return
        if parents and leaf is None and page_top_running:
            # a parents-only running head at the page top ('Sugars, syrups, and molasses:—'): the open article
            # and its country block carry over; the leaf may be repeated on the next row and must still match
            ctx['article_parents'] = parents if not ctx.get('article_parents') else ctx['article_parents']
            ctx['leaf_used'] = False
            return
        if parents:
            if ctx.get('article_parents') and not ctx.get('leaf_used', True):
                # previous heading row had no data rows under it: nest beneath it
                ctx['article_parents'] = ctx['article_parents'] + parents
            elif ctx.get('article_parents') and ctx.get('article') is None and ctx.get('leaf_used', True) is False:
                ctx['article_parents'] = ctx['article_parents'] + parents
            else:
                ctx['article_parents'] = parents
            ctx['article'] = None
        if leaf is not None:
            import difflib
            def _nk(x):
                x = re.sub(r'(&c|\betc\b|\bn\.?\s*e\.?\s*s\b|\bn\.?\s*o\.?\s*p\b)\.?', '', x.lower()); return re.sub(r'\W', '', x)
            a, b = _nk(leaf), _nk(old_leaf or '')
            # a page-top repeat is only possible while the article is still OPEN (its Total not yet printed), and
            # sibling leaves that differ in their numbers ('over 89 degrees' / 'over 90 degrees') are never the same
            digits_same = re.findall(r'\d+', leaf) == re.findall(r'\d+', old_leaf or '') \
                or (ctx.get('table_top') and not re.search(r'\d', leaf) and bool(re.search(r'&c|\betc\b', leaf, re.I)))   # '&c.' running head drops the digits
            jac = fuzzy_jaccard(leaf, old_leaf or '')
            ta = [t for t in re.findall(r'[a-z0-9]+', leaf.lower()) if t not in ('of', 'and', 'the', 'or', 'all', 'other')]
            same = leaf == old_leaf or (old_leaf and old_leaf != '?' and not ctx.get('article_closed') and digits_same and (
                   difflib.SequenceMatcher(None, a, b).ratio() >= 0.85 or
                   (min(len(a), len(b)) >= 8 and (a.startswith(b) or b.startswith(a))) or      # running-head abbreviation 'X, &c.'
                   (ctx.get('table_top') and len(ta) >= 2 and jac >= 0.75) or                 # page-top running head, words reordered
                   (ctx.get('table_top') and token_containment(leaf, old_leaf) >= 0.9) or      # running head = parent+leaf or leaf+'&c.'
                   wrapped_suffix(leaf, old_leaf)))                                             # 'ages' / 'Packages'
            if same:
                leaf = old_leaf            # page-top repeat (possibly re-hyphenated): keep block and spelling
                ctx['article'] = leaf
                return                     # a continuation: the country block carries over the page break
            else:
                ctx['block_id'] = ctx.get('block_id', 0) + 1
            import os
            if os.environ.get('CA_DEBUG_ARTICLE') and leaf == os.environ['CA_DEBUG_ARTICLE']:
                print('DEBUG leaf set from:', repr(text), file=sys.stderr)
            if ctx.get('article') is not None and not ctx.get('leaf_used', True):
                # previous leaf never received data rows: it was a parent heading
                ctx['article_parents'] = (ctx.get('article_parents') or []) + [ctx['article']]
            ctx['article'] = leaf
            ctx['leaf_used'] = False
            ctx['article_closed'] = False
        else:
            ctx['leaf_used'] = False
            if ctx.get('table_top') and ctx.get('country') not in (None, '', '?'):
                return                     # page-top running head (parents only): the country block carries over
        ctx['country'] = pending_country
        ctx['unit'] = None
        ctx['last_prov'] = None
        ctx['expect_label'] = False

    def _units(self, ctx, vals_raw):
        for v in vals_raw[:1]:
            t = v.strip().rstrip('.')
            if t and is_unit_token(t) and t != '$':
                ctx['unit'] = t

    def _emit(self, fy, vol, seq, ri, ctx, kind, prov, nums, flags, vals_raw, texts):
        if ctx.get('recap'):
            kind = 'recap'
            if ctx.get('country') == 'TOTAL' or any(re.match(r'\s*[“"]?\s*Total', t) for t in texts[:2]):
                ctx['recap_done'] = True
        if kind in ('detail', 'country_total', 'detail_lostlabel') and not ctx.get('article'):
            ctx['article'] = '?'; ctx['block_id'] = ctx.get('block_id', 0) + 1; ctx['leaf_used'] = False
            self.diag['article_heading_lost'] += 1
        elif kind in ('detail', 'country_total', 'detail_lostlabel', 'country_noprov') and ctx.get('article_closed') and ctx.get('regime') == 'C':
            # data rows after the article's printed grand total with no heading read: a new article, heading lost
            ctx['article'] = '?'; ctx['block_id'] = ctx.get('block_id', 0) + 1; ctx['leaf_used'] = False
            ctx['article_closed'] = False; ctx['article_parents'] = []
            self.diag['article_heading_lost_after_total'] += 1
        if ctx.get('regime') == 'A':
            cols = ['qty_brit', 'qty_foreign', 'qty_land', 'qty_imp', 'val_imp', 'qty_efc', 'val_efc', 'duty']
        else:
            cols = ['qty_imp', 'val_imp', 'qty_efc', 'val_efc', 'duty']
        rec = dict(fiscal_year=fy, volume=vol, table_seq=seq, row_seq=ri, regime=ctx.get('regime'), block_id=ctx.get('block_id', 0),
                   section=ctx.get('section'), section_label=ctx.get('section_label'),
                   article_parent=' > '.join(ctx.get('article_parents') or []), article=ctx.get('article'),
                   country=None if kind in ('article_total',) else ctx.get('country'),
                   province=prov, row_kind=kind, unit=ctx.get('unit'), country_inferred=0)
        for c in ['qty_brit', 'qty_foreign', 'qty_land', 'qty_imp', 'val_imp', 'qty_efc', 'val_efc', 'duty']:
            rec[c] = None
        for c, v in zip(cols, nums):
            rec[c] = v
        rec['flags'] = ','.join(f for f in flags if f and f != 'blank')
        rec['raw'] = ' | '.join(texts)
        for f in flags:
            if f in ('unparsed', 'fused'): self.unparsed[f] += 1
        if kind in ('detail', 'country_total'): ctx['leaf_used'] = True
        if kind in ('article_total', 'article_total_fused', 'article_province_total'): ctx['article_closed'] = True
        ctx['table_top'] = False
        self.rows.append(rec)

    # ---------------------------------------------------------------- post-pass
    def resolve_lost_labels(self, start_idx):
        """Lost-label segments (detail_lostlabel rows + their trailing subtotal) are either the article's
        Total block (values == sum of the preceding country blocks, by province) or a country block whose
        label was dropped (kept as detail with country '?')."""
        rows = self.rows[start_idx:]
        # (a) page-top fusion: the previous article's unlabelled grand total merged into the next article's
        #     heading+first-country row.  Signature: the row's values equal the sum of the preceding Total-by-
        #     province rows, which themselves were not followed by a grand total.
        pend = None        # (val_imp sum, qty_imp sum, val_efc sum) of article_province_total rows awaiting a grand total
        pend_src = None    # the first of those Total rows (carries the article the grand total belongs to)
        for r in rows:
            k = r['row_kind']
            if k == 'article_province_total':
                if pend is None: pend = [0.0, 0.0, 0.0, False]; pend_src = r
                pend[0] += r['val_imp'] or 0; pend[1] += r['qty_imp'] or 0; pend[2] += r['val_efc'] or 0
            elif k == 'article_total':
                pend = None
            elif k == 'country_total' and pend is not None and r['block_id'] != pend_src['block_id']:
                # the grand total came right after the Total-by-province rows but a new heading (+ country) had
                # already been read: it was emitted as the new article's first country total with no rows.
                # Values equal to the province totals prove it the OLD article's grand total.
                def _close(x, y, tol):
                    return x is not None and y and abs(x - y) <= max(0.5, tol * y)
                if (pend[0] > 0 or pend[2] > 1000) and (_close(r['val_imp'], pend[0], 0) or (_close(r['val_efc'], pend[2], 0) and pend[2] > 1000)):
                    r['row_kind'] = 'article_total'; r['country'] = None; r['province'] = None
                    r['article'] = pend_src['article']; r['article_parent'] = pend_src['article_parent']; r['block_id'] = pend_src['block_id']
                    r['flags'] = (r['flags'] + ',' if r['flags'] else '') + 'grand_total_rejoined'
                    self.diag['grand_total_rejoined'] += 1
                pend = None
            elif k in ('detail', 'detail_lostlabel', 'country_noprov') and pend is not None:
                def _close(x, y, tol):
                    return x is not None and y and abs(x - y) <= max(0.5, tol * y)
                vi, ve, qi = r['val_imp'], r['val_efc'], r['qty_imp']
                exact = (_close(vi, pend[0], 0) and (qi is None or pend[1] == 0 or _close(qi, pend[1], 0))) \
                        or (_close(ve, pend[2], 0) and pend[2] > 1000)
                # an OCR digit slip in one column: val_imp within 0.5% and a second column within 0.5%
                near = _close(vi, pend[0], 0.005) and (_close(ve, pend[2], 0.005) or _close(qi, pend[1], 0.005)) and pend[0] > 1000
                if (pend[0] > 0 or pend[2] > 1000) and (exact or near):
                    r['row_kind'] = 'article_total_fused'; r['country'] = None; r['province'] = None
                    self.diag['page_top_total_fusion'] += 1
                pend = None
            elif k == 'country_total':
                pass
            else:
                pend = None
        # (s) summary lines of the sugar section ('Melado, &c., &c., direct, of all degrees by polariscope' = the sum
        #     of the 'not over N degrees' grades, repeated in the recapitulation that follows): never detail
        for r in rows:
            if r['article'] and re.search(r'\ball degrees\b', r['article'], re.I) and not re.search(r'testing', r['article'], re.I) \
                    and r['row_kind'] in ('detail', 'detail_lostlabel', 'country_total', 'article_province_total', 'article_total', 'country_noprov'):
                r['row_kind'] = 'summary'; self.diag['summary_line'] += 1
        # (a') the previous article's Total block continues past a heading that rode on one of its rows
        #      ('Earthenware, viz.: ... ware— | P. E. Island | 1,686' was emitted as the old article's PEI total, then
        #      'N.-W. Territories | 299' and the grand total 298,926 fell into the new article as '?' rows):
        #      unlabelled rows opening a block right after Total-by-province rows, provinces continuing the order,
        #      followed by a total equal to those Totals plus the rows -> they are the old article's Total tail
        i = 0; n = len(rows)
        while i < n:
            r = rows[i]
            if r['row_kind'] in ('detail', 'detail_lostlabel') and r['country'] in ('?', None, '') and i > 0 \
                    and rows[i - 1]['row_kind'] == 'article_province_total' and rows[i - 1]['block_id'] != r['block_id'] \
                    and r['province'] in PROVINCE_ORDER and rows[i - 1]['province'] in PROVINCE_ORDER \
                    and PROVINCE_ORDER.index(rows[i - 1]['province']) < PROVINCE_ORDER.index(r['province']):
                p = i - 1
                while p >= 0 and rows[p]['row_kind'] == 'article_province_total' and rows[p]['block_id'] == rows[i - 1]['block_id']: p -= 1
                tot_rows = rows[p + 1:i]
                j = i
                while j < n and rows[j]['row_kind'] in ('detail', 'detail_lostlabel') and rows[j]['country'] in ('?', None, '') \
                        and rows[j]['block_id'] == r['block_id']: j += 1
                seg = rows[i:j]
                provs = [x['province'] for x in tot_rows + seg]
                inorder = all(pv in PROVINCE_ORDER for pv in provs) and \
                    [PROVINCE_ORDER.index(pv) for pv in provs] == sorted(PROVINCE_ORDER.index(pv) for pv in provs)
                T = rows[j] if j < n and rows[j]['row_kind'] == 'country_total' and rows[j]['block_id'] == r['block_id'] else None
                ok = False
                if T is not None and inorder:
                    for col in ('val_imp', 'val_efc'):
                        tv = T[col]
                        if tv is None or tv <= 0: continue
                        sv = sum((x[col] or 0) for x in tot_rows) + sum((x[col] or 0) for x in seg)
                        if abs(sv - tv) <= max(1, 0.001 * tv): ok = True; break
                if ok:
                    prev = tot_rows[0]
                    for x in seg + [T]:
                        x['article'] = prev['article']; x['article_parent'] = prev['article_parent']; x['block_id'] = prev['block_id']
                        x['flags'] = (x['flags'] + ',' if x['flags'] else '') + 'total_tail_rejoined'
                    for x in seg:
                        x['row_kind'] = 'article_province_total'; x['country'] = 'TOTAL'
                    T['row_kind'] = 'article_total'; T['country'] = None
                    self.diag['total_tail_rejoined'] += 1
                    i = j + 1; continue
            i += 1
        # (b) label slip: the label column lost its first entry (usually 'Ontario') and shifted up one row, so
        #     'Quebec' carries Ontario's values and the last province ends up unlabelled just before the real
        #     country total.  Signature: a country run d1..dn, then TWO blank-label rows t1, t2 with
        #     sum(d) + t1 == t2.  If the run starts at Ontario the labels are intact and t1 is a trailing
        #     province whose label was lost.
        def _v(r): return r['val_imp'] if r['val_imp'] is not None else r['val_efc']
        slip_cands = []
        i = 0; n = len(rows)
        while i < n:
            r0 = rows[i]
            if r0['row_kind'] == 'detail' and r0['province'] and r0['country'] not in (None, 'TOTAL'):
                run_kind, tail_kind = 'detail', 'country_total'
            elif r0['row_kind'] == 'article_province_total' and r0['province']:
                run_kind, tail_kind = 'article_province_total', 'article_total'
            else:
                i += 1; continue
            j = i
            while j < n and rows[j]['row_kind'] == run_kind and rows[j]['country'] == r0['country'] \
                    and rows[j]['block_id'] == r0['block_id'] and rows[j]['province']: j += 1
            run = rows[i:j]
            # the tail: k unlabelled rows (read as totals) then the real total, k = 1..3 (smallest k that closes)
            q = j
            while q < n and q - j <= 3 and rows[q]['row_kind'] == tail_kind and rows[q]['block_id'] == r0['block_id'] \
                    and (tail_kind == 'article_total' or rows[q]['country'] == r0['country']): q += 1
            kmax = q - j - 1
            provs = [r['province'] for r in run]
            inorder = all(p in PROVINCE_ORDER for p in provs) and \
                [PROVINCE_ORDER.index(p) for p in provs] == sorted(PROVINCE_ORDER.index(p) for p in provs) and len(set(provs)) == len(provs)
            k = 0
            if kmax >= 1 and inorder:
                for kk in range(1, kmax + 1):
                    extras, T = rows[j:j + kk], rows[j + kk]
                    # any one column closes (values may be blank on quantity-and-duty lines: the duty then witnesses)
                    for col in ('val_imp', 'val_efc', 'duty'):
                        dsum = sum((r[col] or 0) for r in run); xs = sum((r[col] or 0) for r in extras); vT = T[col] or 0
                        dv = abs(dsum + xs - vT)
                        digit_slip = dv in (10, 100, 1000, 10000) and vT >= 20 * dv      # one OCR digit off in one cell
                        if vT > 0 and all(r[col] is not None for r in run) and (dv <= max(1, 0.001 * vT) or digit_slip) and abs(dsum - vT) > 1:
                            k = kk; break
                    if k: break
            if k >= 1:
                extras, T = rows[j:j + k], rows[j + k]
                idx0 = PROVINCE_ORDER.index(provs[0]); idxl = PROVINCE_ORDER.index(provs[-1])
                def _mark(r, f):
                    r['flags'] = (r['flags'] + ',' if r['flags'] else '') + f
                # two hypotheses: labels shifted UP by k (the k unknown provinces precede the first label) or the
                # trailing k labels lost (they follow the last label).  The block's printed province totals decide.
                hyps = []
                if idx0 >= k and idx0 > 0:
                    hyps.append(('shift', [PROVINCE_ORDER[idx0 - k + m] for m in range(k)] + provs))
                if idxl + k < len(PROVINCE_ORDER):
                    hyps.append(('trail', provs + [PROVINCE_ORDER[idxl + 1 + m] for m in range(k)]))
                if hyps:
                    # apply the historical default now (shift unless the run starts at Ontario); two-hypothesis runs
                    # are re-scored against the block's printed province totals in a second sweep, once every run
                    # and Total block of the table has had its default repair (scoring against unrepaired
                    # neighbours picks the wrong reading)
                    name, labels = hyps[0]
                    for x, pv in zip(run + extras, labels):
                        x['province'] = pv; _mark(x, ('label_slip' if name == 'shift' else 'trailing_label_lost') + ('' if k == 1 else str(k)))
                    for x in extras:
                        x['row_kind'] = run_kind; x['country'] = r0['country']
                    self.diag['label_slip_repaired' if name == 'shift' else 'trailing_label_lost'] += 1
                    if k > 1: self.diag[f'label_slip{k}_repaired'] += 1
                    if len(hyps) > 1:
                        slip_cands.append((run + extras, hyps, run_kind, r0['block_id'], i))
                i = j + k + 1
            else:
                i = max(j + max(kmax, 0) + 1, i + 1) if kmax >= 0 and j > i else max(j, i + 1)
        # second sweep: shift vs trailing, decided by the block's printed province totals (now that every run of
        # the block carries its default repair); flip only when the alternative is confirmed and the default is not
        by_block = defaultdict(list)
        for idx, r in enumerate(rows): by_block[r['block_id']].append(r)
        for rs, hyps, run_kind, blk, i0 in slip_cands:
            other_kind = 'article_province_total' if run_kind == 'detail' else 'detail'
            mine = set(id(x) for x in rs)
            col = next((c for c in ('val_imp', 'val_efc', 'duty') if all(x[c] is not None for x in rs)), 'val_imp')
            same = defaultdict(float); other = defaultdict(float); have_other = False
            for x in by_block[blk]:
                if id(x) in mine or not x['province'] or x[col] is None: continue
                if x['row_kind'] == run_kind: same[x['province']] += x[col]
                elif x['row_kind'] == other_kind: other[x['province']] += x[col]; have_other = True
            if not have_other: continue
            scores = {}
            for name, labels in hyps:
                contrib = defaultdict(float)
                for x, pv in zip(rs, labels): contrib[pv] += x[col] or 0
                match = miss = 0
                for pv in contrib:
                    if pv not in other: continue
                    a = same.get(pv, 0) + contrib[pv]; b = other[pv]
                    if abs(a - b) <= max(1, 0.001 * max(a, b)): match += 1
                    else: miss += 1
                scores[name] = (match, miss)
            cur = hyps[0][0]; alt = hyps[1][0]
            if scores[alt][0] >= 1 and scores[alt][0] > scores[cur][0] and scores[cur][0] == 0:
                labels = hyps[1][1]
                for x, pv in zip(rs, labels):
                    x['province'] = pv
                    x['flags'] = re.sub(r'(label_slip|trailing_label_lost)\d?', alt + '_by_totals', x['flags'] or '')
                self.diag['slip_hypothesis_flipped'] += 1
        # (b1) 'United States | 76,720 | 315,996' (a country label with values but no province) right before that
        #      country's province rows starting at Quebec: the Ontario row with its province label lost, when the
        #      country total closes with it
        i = 0; n = len(rows)
        while i < n:
            r = rows[i]
            if r['row_kind'] == 'country_noprov' and r['country'] not in (None, '', '?', 'TOTAL') and i + 1 < n \
                    and rows[i + 1]['row_kind'] == 'detail' and rows[i + 1]['country'] == r['country'] and rows[i + 1]['block_id'] == r['block_id'] \
                    and rows[i + 1]['province'] in PROVINCE_ORDER and rows[i + 1]['province'] != 'Ontario':
                j = i + 1
                while j < n and rows[j]['row_kind'] == 'detail' and rows[j]['country'] == r['country'] and rows[j]['block_id'] == r['block_id']: j += 1
                T = rows[j] if j < n and rows[j]['row_kind'] == 'country_total' and rows[j]['country'] == r['country'] and rows[j]['block_id'] == r['block_id'] else None
                if T is not None:
                    for col in ('val_imp', 'val_efc'):
                        tv = T[col]
                        if tv is None or tv <= 0: continue
                        sv = sum((x[col] or 0) for x in rows[i:j])
                        if abs(sv - tv) <= max(1, 0.001 * tv):
                            first = PROVINCE_ORDER.index(rows[i + 1]['province'])
                            r['province'] = PROVINCE_ORDER[first - 1] if first > 0 else 'Ontario'
                            r['row_kind'] = 'detail'; r['flags'] = (r['flags'] + ',' if r['flags'] else '') + 'province_label_lost'
                            self.diag['country_noprov_is_first_province'] += 1
                            break
            i += 1
        # (b2) a Total-by-province block whose labels are shifted up by one with NO unlabelled row left to trigger the
        #      slip test ('Quebec 375,531' = the block's Ontario details exactly): decide identity vs shift by how
        #      many provinces the two readings reconcile with the block's detail sums
        i = 0; n = len(rows)
        while i < n:
            r0 = rows[i]
            if r0['row_kind'] == 'article_province_total' and r0['province'] in PROVINCE_ORDER and r0['province'] != 'Ontario' \
                    and not (i > 0 and rows[i - 1]['row_kind'] == 'article_province_total' and rows[i - 1]['block_id'] == r0['block_id']):
                j = i
                while j < n and rows[j]['row_kind'] == 'article_province_total' and rows[j]['block_id'] == r0['block_id'] and rows[j]['province']: j += 1
                run = rows[i:j]; provs = [x['province'] for x in run]
                inorder = all(p in PROVINCE_ORDER for p in provs) and [PROVINCE_ORDER.index(p) for p in provs] == sorted(PROVINCE_ORDER.index(p) for p in provs) and len(set(provs)) == len(provs)
                if inorder and len(run) >= 2:
                    b0 = i
                    while b0 > 0 and rows[b0 - 1]['block_id'] == r0['block_id']: b0 -= 1
                    dets = [x for x in rows[b0:i] if x['row_kind'] == 'detail' and x['province']]
                    if dets and any(x['province'] == 'Ontario' for x in dets):
                        col = 'val_imp' if all(x['val_imp'] is not None for x in run) else 'val_efc'
                        acc = defaultdict(float)
                        for x in dets:
                            if x[col] is not None: acc[x['province']] += x[col]
                        def score(labels):
                            m = 0
                            for x, pv in zip(run, labels):
                                if x[col] is None or pv not in acc: continue
                                if abs(acc[pv] - x[col]) <= max(1, 0.001 * max(acc[pv], x[col])): m += 1
                            return m
                        shifted = [PROVINCE_ORDER[PROVINCE_ORDER.index(p) - 1] for p in provs]
                        s_id, s_sh = score(provs), score(shifted)
                        if s_sh >= 2 and s_sh > s_id:
                            for x, pv in zip(run, shifted):
                                x['province'] = pv; x['flags'] = (x['flags'] + ',' if x['flags'] else '') + 'total_labels_shifted'
                            self.diag['total_block_labels_shifted'] += 1
                i = j
            else:
                i += 1
        # (d) heading fused into a continuing Total-by-province row: 'Article— Great Britain | Manitoba | ...' where
        #     Manitoba continues the PREVIOUS article's Total block.  The rows up to the next blank-label total are
        #     that Total (their sum proves it); the new article's first country starts after it, label lost ('?').
        i = 0; n = len(rows)
        while i < n:
            r = rows[i]
            if r['row_kind'] == 'detail' and r['country'] not in (None, '', '?', 'TOTAL') and r['province'] in PROVINCE_ORDER \
                    and r['province'] != 'Ontario' and i > 0 and rows[i - 1]['row_kind'] == 'article_province_total' \
                    and rows[i - 1]['province'] in PROVINCE_ORDER \
                    and PROVINCE_ORDER.index(rows[i - 1]['province']) < PROVINCE_ORDER.index(r['province']):
                # the open Total block before
                p = i - 1
                while p >= 0 and rows[p]['row_kind'] == 'article_province_total': p -= 1
                tot_rows = rows[p + 1:i]
                j = i
                while j < n and rows[j]['row_kind'] == 'detail' and rows[j]['country'] == r['country']: j += 1
                run = rows[i:j]
                if j < n and rows[j]['row_kind'] == 'country_total' and rows[j]['country'] == r['country']:
                    T = rows[j]; ok = False
                    for col in ('val_imp', 'val_efc'):
                        tv = T[col]
                        if tv is None or tv <= 0: continue
                        sv = sum((x[col] or 0) for x in tot_rows) + sum((x[col] or 0) for x in run)
                        if abs(sv - tv) <= max(1, 0.001 * tv): ok = True; break
                    nxt = rows[j + 1] if j + 1 < n else None
                    cty = r['country']
                    is_heading = len(cty) > 22 and cty not in self.vocab and norm_label(cty) not in self.vocab and not split_trailing_country(cty, self.vocab)[1]
                    relabel = nxt is not None and nxt['row_kind'] in ('detail', 'detail_lostlabel') and nxt['country'] in ('?', None, '') and nxt['province'] == 'Ontario'
                    if ok and nxt is not None and (relabel or is_heading or (nxt['row_kind'] == 'detail' and nxt['country'] not in (None, '', '?', 'TOTAL'))):
                        prev_art = tot_rows[0]['article'] if tot_rows else r['article']
                        prev_par = tot_rows[0]['article_parent'] if tot_rows else r['article_parent']
                        prev_blk = tot_rows[0]['block_id'] if tot_rows else r['block_id']
                        for x in run:
                            x['row_kind'] = 'article_province_total'; x['country'] = 'TOTAL'
                            x['article'] = prev_art; x['article_parent'] = prev_par; x['block_id'] = prev_blk
                            x['flags'] = (x['flags'] + ',' if x['flags'] else '') + 'heading_fused_into_total'
                        T['row_kind'] = 'article_total'; T['country'] = None
                        T['article'] = prev_art; T['article_parent'] = prev_par; T['block_id'] = prev_blk
                        q = j + 1
                        if relabel and not is_heading:
                            # the lost-label rows that follow are the fused label's country
                            while q < n and rows[q]['row_kind'] in ('detail', 'detail_lostlabel', 'country_total') \
                                    and rows[q]['country'] in ('?', None, ''):
                                rows[q]['country'] = cty; rows[q]['country_inferred'] = 1
                                if rows[q]['row_kind'] == 'detail_lostlabel': rows[q]['row_kind'] = 'detail'
                                q += 1
                        elif is_heading:
                            # the fused label is the NEXT article's heading: name the '?' block that follows
                            head = re.sub(r'\s*[—–-]\s*$', '', norm_label(cty)).strip()
                            while q < n and rows[q]['article'] == '?' and rows[q]['block_id'] == nxt['block_id']:
                                rows[q]['article'] = head; rows[q]['flags'] = (rows[q]['flags'] + ',' if rows[q]['flags'] else '') + 'heading_from_fused_total'
                                q += 1
                        self.diag['heading_fused_into_total'] += 1
                        i = q; continue
            i += 1
        # (f) a heading read as a country label: 'Machinery for Worsted and Cotton-Mills ... | | 2,610' — a long,
        #     non-vocab label on a row whose values are the preceding run's total (country_noprov), followed by an
        #     article-'?' block.  The label names that block; the row is the previous run's country total when the
        #     sum proves it (else the previous article's grand total, else a bare heading row).
        i = 0; n = len(rows)
        while i < n:
            r = rows[i]
            lab = r['country'] or ''
            if r['row_kind'] == 'country_noprov' and len(lab) > 22 and lab not in self.vocab and norm_label(lab) not in self.vocab \
                    and not province_of(lab) and not split_trailing_country(lab, self.vocab)[1] \
                    and i + 1 < n and rows[i + 1]['article'] == '?' and rows[i + 1]['row_kind'] in ('detail', 'detail_lostlabel', 'country_total'):
                head = re.sub(r'\s*[—–-]\s*$', '', norm_label(lab)).strip()
                head = re.sub(r'(\w)- (?=[a-z])', r'\1', head)
                q = i + 1
                while q < n and rows[q]['article'] == '?': q += 1
                for x in rows[i + 1:q]:
                    x['article'] = head; x['flags'] = (x['flags'] + ',' if x['flags'] else '') + 'heading_from_label_row'
                # the row's own values
                p = i - 1
                while p >= 0 and rows[p]['row_kind'] == 'detail' and rows[p]['block_id'] == r['block_id'] \
                        and rows[p]['country'] == rows[i - 1]['country'] and rows[p]['country'] not in (None, '', '?', 'TOTAL'): p -= 1
                run = rows[p + 1:i]
                done = False
                if run:
                    for col in ('val_imp', 'val_efc'):
                        tv = r[col]
                        if tv is None or tv <= 0: continue
                        if abs(sum((x[col] or 0) for x in run) - tv) <= max(1, 0.001 * tv):
                            r['row_kind'] = 'country_total'; r['country'] = run[-1]['country']; done = True; break
                if not done:
                    p = i - 1
                    while p >= 0 and rows[p]['row_kind'] == 'article_province_total': p -= 1
                    tot = rows[p + 1:i]
                    if tot:
                        for col in ('val_imp', 'val_efc'):
                            tv = r[col]
                            if tv is None or tv <= 0: continue
                            if abs(sum((x[col] or 0) for x in tot) - tv) <= max(1, 0.001 * tv):
                                r['row_kind'] = 'article_total'; r['country'] = None; r['province'] = None
                                r['article'] = tot[0]['article']; r['article_parent'] = tot[0]['article_parent']; r['block_id'] = tot[0]['block_id']
                                done = True; break
                if not done:
                    r['row_kind'] = 'heading_row'; r['country'] = None
                r['flags'] = (r['flags'] + ',' if r['flags'] else '') + 'heading_label_row'
                self.diag['heading_from_label_row'] += 1
                i = q; continue
            i += 1
        # (e) article-heading '?' runs resolved by resumption or by closure: a run of rows whose article is '?'
        #     (an order restart fired, or a heading never arrived) belongs to the PRECEDING article P when P's name
        #     resumes right after it ('Wool, unmanufactured, N.E.S — United States' at the next page top) with no
        #     Total printed before the run, or when the run's own Total rows close only over P's open details plus
        #     the run; to the FOLLOWING article N when the run's details are needed to close N's Totals.
        def _tots(rs):
            """per-province Total-by-province values and the grand total of a row list (val_imp, val_efc)"""
            pv = {}; gt = None
            for x in rs:
                if x['row_kind'] == 'article_province_total' and x['province']:
                    pv[x['province']] = (x['val_imp'], x['val_efc'])
                elif x['row_kind'] in ('article_total', 'article_total_fused'):
                    gt = (x['val_imp'], x['val_efc'])
            return pv, gt
        def _runs(rs, col):
            """value of a row list for closure: each country's printed country_total when it has one (its detail
            rows may be partly on another page), else its detail rows"""
            has_t = set(x['country'] for x in rs if x['row_kind'] == 'country_total')
            v = 0.0
            for x in rs:
                if x['row_kind'] == 'country_total' or (x['row_kind'] in ('detail', 'country_noprov') and x['country'] not in has_t):
                    v += x[col] or 0
            return v
        def _closes(details, pv, gt):
            """details (list of rows) close the Totals: grand total within 0.1% in either column, or (no grand
            total) every printed province total matched by the per-province detail sums"""
            for ci, col in enumerate(('val_imp', 'val_efc')):
                if gt is not None and gt[ci] is not None and gt[ci] > 0:
                    sv = _runs(details, col)
                    if abs(sv - gt[ci]) <= max(1, 0.001 * gt[ci]): return True
            if gt is None and pv:
                for ci, col in enumerate(('val_imp', 'val_efc')):
                    acc = defaultdict(float)
                    for x in details:
                        if x['row_kind'] == 'detail' and x[col] is not None: acc[x['province']] += x[col]
                    ok = 0; tried = 0
                    for prov, t in pv.items():
                        if t[ci] is None or t[ci] <= 0: continue
                        tried += 1
                        if abs(acc.get(prov, 0) - t[ci]) <= max(1, 0.001 * t[ci]): ok += 1
                    if tried and ok == tried and sum(acc.values()) > 0: return True
            return False
        i = 0; n = len(rows)
        while i < n:
            if rows[i]['article'] != '?':
                i += 1; continue
            j = i
            while j < n and rows[j]['article'] == '?': j += 1
            run = rows[i:j]
            before = rows[i - 1] if i > 0 else None
            after = rows[j] if j < n else None
            P = before['article'] if before and before['article'] not in (None, '', '?') else None
            N = after['article'] if after and after['article'] not in (None, '', '?') else None
            assign = None; how = None
            run_det = [x for x in run if x['row_kind'] in ('detail', 'country_total', 'country_noprov')]
            run_pv, run_gt = _tots(run)
            if P is not None and before['row_kind'] not in ('article_total', 'article_total_fused'):
                # P's open block: its rows back to the previous article_total
                p = i - 1
                while p >= 0 and rows[p]['block_id'] == before['block_id'] and rows[p]['row_kind'] not in ('article_total', 'article_total_fused'): p -= 1
                p_rows = rows[p + 1:i]
                p_det = [x for x in p_rows if x['row_kind'] in ('detail', 'country_total', 'country_noprov')]
                p_pv, p_gt = _tots(p_rows)
                if N == P and p_gt is None:
                    assign, how = before, 'article_resumed'
                elif (run_pv or run_gt) and p_det and _closes(p_det + run_det, run_pv, run_gt) and not _closes(run_det, run_pv, run_gt):
                    assign, how = before, 'article_closed_with_prev'
            if assign is None and N is not None and not (run_pv or run_gt) and run_det:
                q = j
                while q < n and rows[q]['block_id'] == after['block_id']: q += 1
                n_rows = rows[j:q]
                n_det = [x for x in n_rows if x['row_kind'] in ('detail', 'country_total', 'country_noprov')]
                n_pv, n_gt = _tots(n_rows)
                if (n_pv or n_gt) and _closes(run_det + n_det, n_pv, n_gt) and not _closes(n_det, n_pv, n_gt):
                    assign, how = after, 'article_closed_with_next'
            if assign is not None:
                for x in run:
                    x['article'] = assign['article']; x['article_parent'] = assign['article_parent']; x['block_id'] = assign['block_id']
                    x['flags'] = (x['flags'] + ',' if x['flags'] else '') + how
                self.diag[how] += 1
            i = j
        self._infer_lost_countries_later = True
        # group by block_id preserving order
        i = 0; n = len(rows)
        while i < n:
            j = i
            while j < n and rows[j]['block_id'] == rows[i]['block_id']: j += 1
            blk = rows[i:j]
            acc = defaultdict(float)      # province -> val_imp of detail rows seen so far in the block
            acc_e = defaultdict(float)
            k = 0
            while k < len(blk):
                r = blk[k]
                if r['row_kind'] == 'article_total':
                    acc = defaultdict(float); acc_e = defaultdict(float)     # a printed Total closes the sum
                    k += 1; continue
                if r['row_kind'] == 'detail':
                    if r['val_imp'] is not None: acc[r['province']] += r['val_imp']
                    if r['val_efc'] is not None: acc_e[r['province']] += r['val_efc']
                    k += 1; continue
                if r['row_kind'] != 'detail_lostlabel':
                    k += 1; continue
                # segment of lost-label rows
                m = k
                while m < len(blk) and blk[m]['row_kind'] == 'detail_lostlabel': m += 1
                seg = blk[k:m]
                tail = blk[m] if m < len(blk) and blk[m]['row_kind'] in ('country_total', 'article_total') else None
                segv = {r['province']: r['val_imp'] for r in seg if r['val_imp'] is not None}
                sege = {r['province']: r['val_efc'] for r in seg if r['val_efc'] is not None}
                match = sum(1 for p, v in segv.items() if abs(acc.get(p, 0) - v) < 0.5)
                match_e = sum(1 for p, v in sege.items() if abs(acc_e.get(p, 0) - v) < 0.5)
                is_total = (segv and match >= max(1, len(segv) // 2 + 1)) or (sege and match_e >= max(1, len(sege) // 2 + 1))
                # alternative: the segment's grand total equals the sum of the block's country blocks so far
                if not is_total and tail is not None:
                    tot_v = sum(acc.values()); tot_e = sum(acc_e.values())
                    seg_v = sum(segv.values()); seg_e = sum(sege.values())
                    for tv, sv, tt in ((tot_v, seg_v, tail['val_imp']), (tot_e, seg_e, tail['val_efc'])):
                        if tv > 0 and ((tt is not None and abs(tt - tv) < 0.5) or abs(sv - tv) < 0.5):
                            is_total = True; self.diag['lost_label_total_by_sum'] += 1; break
                # structural criterion: the last segment of a block that already holds 2+ labelled country blocks
                # and no printed grand total is the article's Total block (the Total is always printed last)
                if not is_total:
                    rest = blk[m + (1 if tail else 0):]
                    later_detail = any(x['row_kind'] in ('detail', 'detail_lostlabel') for x in rest)
                    prior_total = any(x['row_kind'] in ('article_total', 'article_total_fused') for x in blk[:k])
                    labelled = set(x['country'] for x in blk[:k] if x['row_kind'] == 'detail' and x['country'] not in (None, '', '?'))
                    if not later_detail and not prior_total and len(labelled) >= 2 and sum(acc.values()) > 0:
                        is_total = True; self.diag['lost_label_total_structural'] += 1
                if is_total and sum(acc.values()) > 0:
                    for r in seg: r['row_kind'] = 'article_province_total'; r['country'] = 'TOTAL'
                    if tail: tail['row_kind'] = 'article_total'; tail['country'] = None
                    acc = defaultdict(float); acc_e = defaultdict(float)
                    self.diag['lost_label_resolved_total'] += 1
                else:
                    for r in seg:
                        r['row_kind'] = 'detail'; r['country'] = '?'
                        if r['val_imp'] is not None: acc[r['province']] += r['val_imp']
                        if r['val_efc'] is not None: acc_e[r['province']] += r['val_efc']
                    if tail: tail['country'] = '?'
                    self.diag['lost_label_resolved_detail'] += 1
                k = m + (1 if tail else 0)
            i = j
        # (b) infer lost country labels from the printed country order within the block:
        #     GB first, US second, then France, Germany, then the rest.  A '?' block between GB and a
        #     rank>=2 country is the US; a '?' block opening the article and followed by the US is GB.
        rank = lambda c: 0 if c.startswith('Great Brit') else 1 if c.startswith('United Stat') else 2 if c.startswith('France') else 3 if c.startswith('Germany') else 4
        i = 0
        while i < n:
            j = i
            while j < n and rows[j]['block_id'] == rows[i]['block_id']: j += 1
            blk = rows[i:j]
            # segments of '?' detail rows
            k = 0
            while k < len(blk):
                if blk[k]['row_kind'] == 'detail' and blk[k]['country'] == '?':
                    m = k
                    while m < len(blk) and blk[m]['row_kind'] in ('detail', 'country_total') and blk[m]['country'] == '?': m += 1
                    prev = next((x['country'] for x in reversed(blk[:k]) if x['row_kind'] == 'detail' and x['country'] not in (None, '', '?', 'TOTAL')), None)
                    nxt = next((x['country'] for x in blk[m:] if x['row_kind'] == 'detail' and x['country'] not in (None, '', '?', 'TOTAL')), None)
                    guess = None
                    # (c) the segment continues the preceding labelled country: no subtotal between them, and the
                    #     two runs together sum to the segment's trailing total (a misread province label — usually a
                    #     repeated 'Ontario' — made the order restart and cut the run)
                    tail = blk[m - 1] if m - 1 >= k and blk[m - 1]['row_kind'] == 'country_total' else None
                    if tail is not None and k > 0:
                        p = k - 1
                        while p >= 0 and blk[p]['row_kind'] == 'detail' and blk[p]['country'] not in (None, '', '?', 'TOTAL') \
                                and blk[p]['country'] == blk[k - 1]['country']: p -= 1
                        run = blk[p + 1:k]
                        if run:
                            seg = [x for x in blk[k:m - 1] if x['row_kind'] == 'detail']
                            for col in ('val_imp', 'val_efc'):
                                tv = tail[col]
                                if tv is None or tv <= 0: continue
                                sv = sum((x[col] or 0) for x in run) + sum((x[col] or 0) for x in seg)
                                if abs(sv - tv) <= max(1, 0.001 * tv):
                                    cty = run[-1]['country']
                                    for x in blk[k:m]:
                                        x['country'] = cty; x['country_inferred'] = 1
                                    last = run[-1]['province']
                                    if seg and seg[0]['province'] == last and last in PROVINCE_ORDER \
                                            and PROVINCE_ORDER.index(last) + 1 < len(PROVINCE_ORDER):
                                        seg[0]['province'] = PROVINCE_ORDER[PROVINCE_ORDER.index(last) + 1]
                                        seg[0]['flags'] = (seg[0]['flags'] + ',' if seg[0]['flags'] else '') + 'province_relabelled'
                                    self.diag['lost_label_joined_prev_country'] += 1
                                    guess = 'JOINED'; break
                    # (c') the segment OPENS the labelled run that follows: a page-top row whose country label was lost
                    #      ('heading | Ontario | 15,554', then 'Great Britain | Quebec | ...'): the run's country total
                    #      equals segment + run, and the provinces continue in order
                    if guess is None and tail is None and nxt is not None:
                        seg = [x for x in blk[k:m] if x['row_kind'] == 'detail']
                        q = m
                        while q < len(blk) and blk[q]['row_kind'] == 'detail' and blk[q]['country'] == nxt: q += 1
                        run = blk[m:q]
                        T = blk[q] if q < len(blk) and blk[q]['row_kind'] == 'country_total' and blk[q]['country'] == nxt else None
                        def _inorder(rs):
                            ps = [x['province'] for x in rs]
                            return all(p in PROVINCE_ORDER for p in ps) and \
                                [PROVINCE_ORDER.index(p) for p in ps] == sorted(PROVINCE_ORDER.index(p) for p in ps) and len(set(ps)) == len(ps)
                        def _sums_to(rs, T):
                            for col in ('val_imp', 'val_efc'):
                                tv = T[col]
                                if tv is None or tv <= 100: continue
                                sv = sum((x[col] or 0) for x in rs)
                                if abs(sv - tv) <= max(1, 0.001 * tv): return True
                            return False
                        if seg and run and T is not None and _inorder(seg + run) and _sums_to(seg + run, T):
                            for x in blk[k:m]:
                                x['country'] = nxt; x['country_inferred'] = 1
                            self.diag['lost_label_joined_next_country'] += 1
                            guess = 'JOINED'
                        elif seg and len(run) == 1 and T is None and q < len(blk) and blk[q]['row_kind'] == 'detail' \
                                and blk[q]['country'] not in (None, '', '?', 'TOTAL', nxt):
                            # label slipped DOWN one row past the heading: 'heading | Quebec | v1', 'Brazil | Quebec | v2',
                            # 'Germany | N.S. | v3', '| N.B.', '| | T' with T == v2 + v3 + ...: v2 is Germany's, v1 Brazil's
                            y = blk[q]['country']; q2 = q
                            while q2 < len(blk) and blk[q2]['row_kind'] == 'detail' and blk[q2]['country'] == y: q2 += 1
                            run2 = blk[q:q2]
                            T2 = blk[q2] if q2 < len(blk) and blk[q2]['row_kind'] == 'country_total' and blk[q2]['country'] == y else None
                            if T2 is not None and _inorder(run + run2) and _sums_to(run + run2, T2) and not _sums_to(run2, T2):
                                run[0]['country'] = y; run[0]['country_inferred'] = 1
                                run[0]['flags'] = (run[0]['flags'] + ',' if run[0]['flags'] else '') + 'label_slip_down'
                                for x in blk[k:m]:
                                    x['country'] = nxt; x['country_inferred'] = 1
                                self.diag['label_slip_down'] += 1
                                guess = 'JOINED'
                    if guess == 'JOINED':
                        k = m; continue
                    if prev is not None and rank(prev) == 0 and nxt is not None and rank(nxt) >= 2: guess = 'United States'
                    # article-opening '?' block: the previous article is closed by its printed grand total (the row
                    # just before the segment, possibly fused into this article's heading), no labelled country has
                    # appeared yet in this block and the next labelled country is not GB -> this is Great Britain
                    elif prev is None and nxt is not None and rank(nxt) == 1:
                        before = None
                        idx0 = i + k                      # the row preceding the segment, in volume order
                        if idx0 > 0:
                            before = rows[idx0 - 1]
                            # skip the heading-fused Total-by-province rows that carry this article's name
                            q = idx0 - 1
                            while q >= 0 and rows[q]['row_kind'] == 'article_province_total': q -= 1
                            before = rows[q] if q >= 0 else None
                        if before is not None and before['row_kind'] in ('article_total', 'article_total_fused'):
                            guess = 'Great Britain'
                    # (GB inference for article-opening '?' blocks was tried and over-assigns: such blocks are often
                    #  the previous article's unlabelled Total or a heading-less new article — left as '?')
                    elif prev is not None and rank(prev) == 0 and nxt is None and not any(x['row_kind'] in ('article_province_total',) for x in blk[m:]): guess = None
                    if guess:
                        for x in blk[k:m]:
                            x['country'] = guess; x['country_inferred'] = 1
                        self.diag['country_inferred_' + guess.split()[0]] += 1
                    k = m
                else:
                    k += 1
            i = j
        # (h) a 'country_total' right after a SINGLE detail row of its country whose value differs from that row:
        #     single-row countries carry no printed subtotal, so the row is the article's grand total with its
        #     'Total' label lost (China 7,246 then 614,444 = all of Furskins 1887) when the block's runs sum to it
        i = 0; n = len(rows)
        while i < n:
            r = rows[i]
            if r['row_kind'] == 'country_total' and i > 0 and rows[i - 1]['row_kind'] == 'detail' \
                    and rows[i - 1]['country'] == r['country'] and rows[i - 1]['block_id'] == r['block_id'] \
                    and not (i > 1 and rows[i - 2]['row_kind'] == 'detail' and rows[i - 2]['country'] == r['country'] and rows[i - 2]['block_id'] == r['block_id']):
                d0 = rows[i - 1]
                differs = any(r[c] is not None and d0[c] is not None and abs(r[c] - d0[c]) > max(1, 0.001 * r[c]) for c in ('val_imp', 'val_efc'))
                if differs:
                    p = i - 1
                    while p >= 0 and rows[p]['block_id'] == r['block_id'] and rows[p]['row_kind'] not in ('article_total', 'article_total_fused'): p -= 1
                    blk = rows[p + 1:i]
                    ok = False
                    for col in ('val_imp', 'val_efc'):
                        tv = r[col]
                        if tv is None or tv <= 0: continue
                        has_t = set(x['country'] for x in blk if x['row_kind'] == 'country_total')
                        sv = sum((x[col] or 0) for x in blk if x['row_kind'] == 'country_total' or (x['row_kind'] in ('detail', 'country_noprov') and x['country'] not in has_t))
                        if abs(sv - tv) <= max(1, 0.001 * tv): ok = True; break
                    if ok:
                        r['row_kind'] = 'article_total'; r['country'] = None
                        r['flags'] = (r['flags'] + ',' if r['flags'] else '') + 'grand_total_after_single_row'
                        self.diag['grand_total_after_single_row'] += 1
            i += 1
        # (e2) a lost heading between two articles: the rows of block P (no Total block of its own) are really the
        #      first country runs of the NEXT article N when N's printed province totals close exactly over
        #      P's details + N's details (≥2 provinces) and not over N's details alone — the heading of N was
        #      dropped and its opening runs fell under P's name (1885 carboys: GB/US/France/Germany under
        #      'lightning rod insulators')
        i = 0; n = len(rows)
        starts = []
        while i < n:
            j = i
            while j < n and rows[j]['block_id'] == rows[i]['block_id']: j += 1
            starts.append((i, j)); i = j
        for bi in range(1, len(starts)):
            p0, p1 = starts[bi - 1]; n0, n1 = starts[bi]
            P = rows[p0:p1]; N = rows[n0:n1]
            if P[0]['fiscal_year'] != N[0]['fiscal_year']: continue
            if any(x['row_kind'] in ('article_province_total', 'article_total', 'article_total_fused') for x in P): continue
            if N[0]['article'] in (None, '', '?') or P[0]['article'] in (None, '', '?'): continue
            na = norm_label(N[0]['article'])
            if na in self.vocab or na in SEED_COUNTRIES or split_trailing_country(na, self.vocab)[1] == na \
                    or (len(na.split()) <= 4 and re.search(r'possessions|indies|islands|guiana|africa|america', na, re.I)):
                continue                                   # N's 'article' is a country name that swallowed a heading: not a target
            ptrows = [x for x in N if x['row_kind'] == 'article_province_total' and x['province']]
            # TWO Total blocks inside N (province order restarts) = N spans two articles and the closure test
            # would mix their totals: the 1885 ginger page named the complete 'unground' article (own Total
            # block, grand 142,244) after the following 'ground' article - leave the run '?' for the
            # cross-volume order inference instead
            _rk = [PROVINCE_ORDER.index(x['province']) for x in ptrows if x['province'] in PROVINCE_ORDER]
            if any(b <= a for a, b in zip(_rk, _rk[1:])): continue
            ntot = {x['province']: x for x in ptrows}
            if len(ntot) < 2: continue
            pdet = [x for x in P if x['row_kind'] == 'detail' and x['province']]
            ndet = [x for x in N if x['row_kind'] == 'detail' and x['province']]
            if not pdet: continue
            ok_cols = 0
            for col in ('val_imp', 'val_efc'):
                accP = defaultdict(float); accN = defaultdict(float)
                for x in pdet:
                    if x[col] is not None: accP[x['province']] += x[col]
                for x in ndet:
                    if x[col] is not None: accN[x['province']] += x[col]
                match_both = match_alone = tried = 0
                for pv, t in ntot.items():
                    if t[col] is None or t[col] <= 0: continue
                    tried += 1
                    if abs(accP[pv] + accN[pv] - t[col]) <= max(1, 0.001 * t[col]): match_both += 1
                    if abs(accN[pv] - t[col]) <= max(1, 0.001 * t[col]): match_alone += 1
                if tried >= 2 and match_both >= max(2, tried - 1) and match_both > match_alone: ok_cols += 1
            if ok_cols >= 1:
                for x in P:
                    x['article'] = N[0]['article']; x['article_parent'] = N[0]['article_parent']; x['block_id'] = N[0]['block_id']
                    x['flags'] = (x['flags'] + ',' if x['flags'] else '') + 'lost_heading_closed_with_next'
                self.diag['lost_heading_closed_with_next'] += 1
        # (g) adjacent blocks carrying the same article (a page-top running head that the same-leaf test did not
        #     recognise) merge when the first has no printed grand total: one article, one block
        def _ak(x):
            x = re.sub(r'(&c|\betc\b|\bn\.?\s*e\.?\s*s\b)\.?', '', re.sub(r'\\frac\{[^}]*\}\{[^}]*\}', ' ', (x or '').lower()))
            return ' '.join(sorted(set(re.findall(r'[a-z0-9]+', x)) - {'of', 'and', 'the', 'or'}))
        i = 0; n = len(rows); prev_blk = None; prev_key = None; prev_closed = False; remap = {}
        while i < n:
            j = i
            while j < n and rows[j]['block_id'] == rows[i]['block_id']: j += 1
            blk = rows[i:j]
            key = blk[0]['article'] if blk[0]['article'] not in (None, '', '?') else None
            closed = any(x['row_kind'] in ('article_total', 'article_total_fused') for x in blk)
            if key and prev_key and not prev_closed and blk[0]['row_kind'] != 'recap' \
                    and (_ak(key) == _ak(prev_key) or fuzzy_jaccard(key, prev_key) >= 0.75 or token_containment(key, prev_key) >= 0.9
                         or wrapped_suffix(prev_key, key)) \
                    and re.findall(r'\d+', key) == re.findall(r'\d+', prev_key):
                for x in blk:
                    x['block_id'] = prev_blk; x['flags'] = (x['flags'] + ',' if x['flags'] else '') + 'block_merged'
                self.diag['adjacent_blocks_merged'] += 1
                prev_closed = closed
            else:
                prev_blk = blk[0]['block_id']; prev_key = key; prev_closed = closed
            i = j

    # ---------------------------------------------------------------- driver
    def parse_volume(self, tag, fy, md_path):
        text = md_path.read_text(errors='replace')
        start_rows = len(self.rows)
        start = 0
        for mm in P.TN_START_RE2.finditer(text):
            if re.search(r'COMPILED\s+FROM\s+OFFICIAL\s+RETURNS', text[mm.start(): mm.start() + 1500], re.I):
                start = mm.start(); break
        tn = text[start:]
        self.vocab = set(SEED_COUNTRIES)      # per volume: a label learned in 1871 must not steer 1887
        self.learn_vocab(tn)
        ctx = dict(regime=None, section=None, section_label=None, article_parents=[], article=None,
                   country=None, province=None, unit=None)
        pos = 0; in_general = False; n_tables = 0
        prev_fam = None
        for seq, tm in enumerate(P.TABLE_RE.finditer(tn)):
            inter = tn[pos:tm.start()]; pos = tm.end()
            title = P.title_context(inter)[-400:]
            chunks = re.split(r'(?<=[.])\s+(?=[A-Z(])', title)
            short = chunks[-1] if chunks else ''
            for ch in reversed(chunks):
                if re.search(r'statement|abstract|table|no\. ?\d+|continued|recapitulation', ch, re.I):
                    short = ch; break
            fam = P.family_of(short)
            rows = P.parse_table(tm.group(0))
            ths = [r for r in rows if r and all(k == 'th' for k, _, _ in r)]
            body = [r for r in rows if r and not all(k == 'th' for k, _, _ in r)]
            reg = regime_of(ths) if ths else None
            terminator = bool(re.search(r'recapitulation|abstract|summary statement|comparative statement|export', short, re.I))
            names_new = bool(re.search(r'no\. ?\d+\.?—', short, re.I))
            # decide whether this table belongs to the General Statement of Imports
            if fam == 'imports_general' and not terminator:
                in_general = True
            elif terminator:
                in_general = False
            elif fam in ('other', 'untitled') or re.search(r'continued', short, re.I):
                pass  # inherit
            elif names_new:
                in_general = False
            if re.search(r'general statement.*export|exports.*general statement', short, re.I):
                in_general = False
            if not in_general:
                continue
            if reg and (not ctx['regime'] or reg == ctx['regime']):
                ctx['regime'] = reg
            elif reg and ctx['regime']:
                # the layout is constant within a volume: a header misread ('ARTICLES | COUNTRIES | DUTY' on a
                # province table) must not flip a regime-C volume to B for one page (1883 t193 lost $1.1M that way)
                self.diag['regime_flip_ignored'] += 1
            if not ctx['regime']:
                self.diag['no_regime_yet'] += 1; continue
            pt = province_from_title(short)
            if pt: ctx['province'] = pt
            if ctx['regime'] == 'C':
                ctx['province'] = None
            ctx['article_parents'] = []          # page tops repeat the parent heading
            ctx['article_buf'] = []
            ctx['recap'] = False                 # embedded recapitulations (sugar, molasses) end with their page
            ctx['table_top'] = True              # until the first data row of this table has been emitted
            n_tables += 1
            getattr(self, 'parse_table_' + ctx['regime'])(fy, tag, seq, body, ctx)
        self._fix_province_order(start_rows)
        self._fix_noprov_slip_down(start_rows)
        self.resolve_lost_labels(start_rows)
        self._fix_single_detail_chain(start_rows)
        self._fix_grand_total_on_country_row(start_rows)
        return n_tables


def closure_report(rows):
    """Regime C closure:
       country level  - province rows of a country sum to its printed country_total (countries with a
                        single province row have no printed subtotal and are skipped);
       article level  - the per-country sums add up to the article's grand total (article_total row)."""
    out = []
    by_vol = defaultdict(list)
    for r in rows: by_vol[r['fiscal_year']].append(r)
    COLS = ('val_imp', 'val_efc', 'duty')
    for fy, rs in sorted(by_vol.items()):
        reg = Counter(r['regime'] for r in rs).most_common(1)[0][0]
        kinds = Counter(r['row_kind'] for r in rs)
        line = f"| {fy} | {reg} | {len(rs)} | " + ', '.join(f'{k} {n}' for k, n in kinds.most_common()) + ' |'
        if reg != 'C':
            ok = bad = 0; acc = defaultdict(float); n_det = 0; ex = []
            for r in rs:
                if r['row_kind'] == 'detail':
                    for c in COLS:
                        if r[c] not in (None, ''): acc[c] += float(r[c])
                    n_det += 1
                elif r['row_kind'] == 'article_total':
                    if n_det >= 2:
                        for c in COLS:
                            if r[c] not in (None, ''):
                                if abs(acc[c] - float(r[c])) < 0.011: ok += 1
                                else:
                                    bad += 1
                                    if len(ex) < 4: ex.append(f"{(r['article'] or '?')[:40]} {c}: rows {acc[c]:.2f} vs printed {float(r[c]):.2f}")
                    acc = defaultdict(float); n_det = 0
            line += f' article closure (details vs total, blocks with 2+ rows) {ok} ok / {bad} bad'
            out.append(line)
            for e in ex: out.append(f'    - {e}')
            continue
        c_ok = c_bad = a_ok = a_bad = 0; bad_ex = []
        # walk article blocks
        i = 0; n = len(rs)
        art_key = None; country_sums = {}; cur_key = None; cur = defaultdict(float); cur_n = 0
        def close_country():
            nonlocal cur, cur_n, cur_key
            if cur_key is not None and cur_n:
                country_sums[cur_key] = dict(cur)
            cur = defaultdict(float); cur_n = 0; cur_key = None
        for r in rs:
            k = r['row_kind']
            akey = (r['table_seq'], r['article_parent'], r['article']) if False else (r['article_parent'], r['article'])
            if k == 'detail':
                key = (akey, r['country'])
                if key != cur_key:
                    close_country(); cur_key = key
                for c in COLS:
                    if r[c] not in (None, ''): cur[c] += float(r[c])
                cur_n += 1
            elif k == 'country_total':
                for c in COLS:
                    if r[c] not in (None, '') and cur_n:
                        if abs(cur[c] - float(r[c])) < 0.011: c_ok += 1
                        else:
                            c_bad += 1
                            if len(bad_ex) < 6: bad_ex.append(f"{r['article'][:40] if r['article'] else '?'}/{r['country']} {c}: rows {cur[c]:.2f} vs printed {float(r[c]):.2f}")
                close_country()
            elif k == 'article_total':
                close_country()
                sums = defaultdict(float); have = False
                for (ak, cty), d in country_sums.items():
                    if ak == akey:
                        have = True
                        for c in COLS: sums[c] += d.get(c, 0.0)
                if have:
                    for c in COLS:
                        if r[c] not in (None, ''):
                            if abs(sums[c] - float(r[c])) < 0.011: a_ok += 1
                            else: a_bad += 1
                country_sums = {k2: v for k2, v in country_sums.items() if k2[0] != akey}
            elif k == 'article_province_total':
                close_country()
            else:
                close_country()
        # block-level: sum of detail rows vs the block's grand total (article_total with no province)
        blocks = defaultdict(list)
        for r in rs: blocks[r['block_id']].append(r)
        bc = Counter()
        for bid, brs in blocks.items():
            det = sum(float(r['val_imp']) for r in brs if r['row_kind'] == 'detail' and r['val_imp'] not in (None, ''))
            tots = [float(r['val_imp']) for r in brs if r['row_kind'] == 'article_total' and r['val_imp'] not in (None, '')]
            if not tots: bc['no_grand_total'] += 1; continue
            T = tots[-1]
            if T == 0: bc['zero'] += 1; continue
            q = det / T
            bc['exact' if abs(q - 1) < 1e-6 else 'within_1pct' if abs(q - 1) < 0.01 else 'double' if abs(q - 2) < 0.05 else 'under' if q < 1 else 'over'] += 1
        line += f' country closure {c_ok} ok / {c_bad} bad; article blocks (sum detail vs grand total, val_imp): ' + ', '.join(f'{k} {n}' for k, n in bc.most_common())
        out.append(line)
        for e in bad_ex: out.append(f'    - {e}')
    return out


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    index = list(csv.DictReader(open(P.RAW / 'INDEX.tsv'), delimiter='\t'))
    only = set(sys.argv[1:])
    p = Parser()
    per_vol = []
    for row in index:
        tag = row['volume_tag']; fy = row['fiscal_year']
        if only and fy not in only and tag not in only: continue
        md = P.RAW / tag / f'{tag}.md'
        if not md.exists(): continue
        before = len(p.rows)
        n = p.parse_volume(tag, fy, md)
        per_vol.append((fy, tag, n, len(p.rows) - before))
        print(f'{fy:8} {tag:24} tables={n:4} rows={len(p.rows)-before:6}', file=sys.stderr)
    fields = ['fiscal_year', 'volume', 'table_seq', 'row_seq', 'regime', 'block_id', 'section', 'section_label', 'article_parent',
              'article', 'country', 'country_inferred', 'province', 'row_kind', 'unit', 'qty_brit', 'qty_foreign', 'qty_land',
              'qty_imp', 'val_imp', 'qty_efc', 'val_efc', 'duty', 'flags', 'raw']
    with open(OUT_CSV, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in p.rows: w.writerow(r)
    L = ['# Canadian imports General Statement — parse diagnostics', '',
         f'`scripts/ca_parse_imports.py` → `{OUT_CSV.relative_to(ROOT)}` ({len(p.rows)} rows)', '',
         '| FY | volume | tables | rows |', '|---|---|---|---|']
    L += [f'| {fy} | {tag} | {n} | {m} |' for fy, tag, n, m in per_vol]
    L += ['', 'Diagnostics: ' + ', '.join(f'{k} {v}' for k, v in p.diag.most_common()),
          'Cell flags: ' + ', '.join(f'{k} {v}' for k, v in p.unparsed.most_common()), '',
          '| FY | regime | rows | row kinds |', '|---|---|---|---|']
    L += closure_report(p.rows)
    L += ['', '## National check: sum of province-level rows vs the printed Total Imports series', '',
          'Printed series: `reference/canada_printed_totals.csv`. Parsed = sum of `detail` rows (regime C: province rows; A/B: country rows, province statements only, Dominion recapitulation excluded).', '',
          '| FY | regime | parsed val_imp | printed imports | ratio | parsed val_efc | printed e.f.c. | ratio | parsed duty | printed duty | ratio |', '|---|---|---|---|---|---|---|---|---|---|---|']
    printed = {r['fiscal_year']: r for r in csv.DictReader(open(ROOT / 'reference' / 'canada_printed_totals.csv'))}
    agg = defaultdict(lambda: defaultdict(float)); regs = {}
    for r in p.rows:
        regs[r['fiscal_year']] = r['regime']
        if r['row_kind'] == 'detail' and r.get('province') != 'Dominion':
            for c in ('val_imp', 'val_efc', 'duty'):
                if r[c] is not None: agg[r['fiscal_year']][c] += r[c]
    for fy in sorted(agg):
        pr = printed.get(fy.split('-')[-1], {})
        cells = [fy, regs[fy]]
        for c, pc in (('val_imp', 'total_imports'), ('val_efc', 'entered_for_consumption'), ('duty', 'duty')):
            v = agg[fy][c]; pv = float(pr[pc]) if pr.get(pc) else None
            cells += [f'{v:,.0f}', f'{pv:,.0f}' if pv else '', f'{v/pv:.3f}' if pv else '']
        L.append('| ' + ' | '.join(cells) + ' |')
    OUT_MD.write_text('\n'.join(L) + '\n')
    with open(OUT_DIR / 'blank_rows.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['fiscal_year', 'volume', 'table_seq', 'row_seq', 'section', 'article', 'country', 'province', 'raw'])
        w.writeheader(); w.writerows(p.blank_rows)
    print(f'wrote {OUT_CSV} ({len(p.rows)} rows) and {OUT_MD}; {len(p.blank_rows)} blank province rows -> {OUT_DIR / "blank_rows.csv"}', file=sys.stderr)


if __name__ == '__main__':
    main()
