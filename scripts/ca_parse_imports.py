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
import csv, html, json, re, sys
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


def norm_label(s):
    s = DITTO_RE.sub('', s)
    s = LEADER_RE.sub('', s)
    return s.strip(' ,;')


def province_of(s):
    t = re.sub(r'\([^)]*\)', '', norm_label(s))
    k = re.sub(r'[^a-z]', '', t.lower().replace('é', 'e'))
    return PROVINCE_KEYS.get(k)


def split_trailing_province(s):
    """'United States... Quebec' -> ('United States', 'Quebec'); else (s, None)."""
    t = norm_label(s)
    for n in range(1, 4):
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
    'Dan. W. Indies', 'B. E. Indies', 'D. E. Indies', 'Dutch E. Indies', 'Brit. W. Indies', 'British Guiana',
    'Dutch Guiana', 'British West Indies', 'Spanish West Indies', 'French West Indies', 'Danish West Indies',
    'British East Indies', 'Dutch East Indies', 'Bermuda', 'British Columbia', 'Norway and Sweden', 'Total']


def split_trailing_country(s, vocab):
    """'Valentines, &c. United States' -> ('Valentines, &c.', 'United States') when s ends with a known country."""
    t = norm_label(s)
    best = None
    for c in vocab:
        if t.lower().endswith(c.lower()) and len(t) > len(c) + 2:
            if best is None or len(c) > len(best): best = c
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
                if t and len(t) < 30 and not re.search(r'[—:\d$,]', t) and not t[0].islower() \
                        and not re.fullmatch(r'(?:[A-Z]\.\s?)+[A-Z]?\.?', t) and re.search(r'[A-Za-z]{3}', t) \
                        and not is_unit_token(t):
                    self.vocab.add(t)
        self.vocab.discard('')

    # ---------------------------------------------------------------- regime C
    def parse_table_C(self, fy, vol, seq, body, ctx):
        n0 = len(body)
        body = unfuse_rows(body, self.vocab | set(PROVINCE_KEYS.values()) | set(PROVINCE_ORDER), [0, 1], 0)
        if len(body) != n0: self.diag['unfused_rows'] += len(body) - n0
        NV = 5
        for ri, cells in enumerate(body):
            texts = [c for _, _, c in cells]
            spans = sum(cs for _, cs, _ in cells)
            joined = ' '.join(texts).strip()
            # section banners
            if (len(cells) == 1 or spans >= 7 and len(cells) <= 2) and re.search(r'DUTIABLE|FREE GOODS', joined, re.I):
                self._section(ctx, joined); continue
            if len(cells) < NV:
                # short rows: full-width label cells (the 1880s volumes print article headings, country labels
                # and 'Total' as one spanning cell, often ditto-led: '“ Buckwheat—', '“ United States...'),
                # section banners, or junk (index lines, page furniture)
                j = norm_label(joined)
                if re.search(r'DUTIABLE|FREE GOODS', joined, re.I):
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
                    ctx['country'] = j; ctx['expect_label'] = False; ctx['article_buf'] = []
                    ctx['last_prov'] = None; self.diag['short_country_label'] += 1
                elif re.search(r'[—–:;-]\s*$', j.rstrip('.')) or re.search(r'viz\.?\s*$', j, re.I):
                    self._article(ctx, ' '.join(ctx.get('article_buf', []) + [j]))
                    ctx['article_buf'] = []; ctx['expect_label'] = False
                    self.diag['short_article_heading'] += 1
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
            vals_raw = texts[-NV:]
            labels = texts[:-NV]
            # banner in label position with blank values
            if labels and re.search(r'^(DUTIABLE|FREE) GOODS', norm_label(labels[0]), re.I):
                self._section(ctx, labels[0])
                labels = [''] + labels[1:]
                if not any(parse_num(v, cents_ok=(i == 4))[0] is not None for i, v in enumerate(vals_raw)):
                    continue
            parsed = [parse_num(v, cents_ok=(i == 4)) for i, v in enumerate(vals_raw)]
            nums = [p[0] for p in parsed]
            flags = [p[1] for p in parsed]
            numeric = any(v is not None for v in nums)
            units_only = not numeric and all(f in ('blank', 'unit') for f in flags)
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
                        if head: self._article(ctx, ' '.join(ctx.get('article_buf', []) + [head]))
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
                carried = ctx['country']
                self._article(ctx, a_n)
                ctx['country'] = carried
                a_n = ''; self.diag['page_top_heading_continuation'] += 1
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
                    ctx['leaf_used'] = False; ctx['unit'] = None
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
                        else:
                            head, tail = split_trailing_country(cand, self.vocab)
                            if tail:
                                if head: self._article(ctx, head)
                                cand = tail
                        ctx['country'] = cand; kind = 'country_noprov'; self.diag['label_in_province_slot'] += 1
                else:
                    kind = 'article_total' if ctx.get('country') == 'TOTAL' else 'country_total'
            if not numeric and kind in ('detail', 'article_province_total'):
                self.diag['label_row_no_values'] += 1
            # value column lost: the unit token sits in the quantity slot and the QUANTITY was read as the value
            # ('Lbs. | 916,211 | Lbs. | 916,211 | 1,717 75'); on a dutiable line the duty/value ratio gives it away
            if kind in ('detail', 'article_province_total') and is_unit_token(vals_raw[0]) and nums[0] is None and nums[1] is not None and nums[1] > 0 \
                    and ctx.get('section') == 'DUTIABLE' and nums[4] is not None and nums[4] > 0 and nums[4] / nums[1] < 0.005:
                nums = [nums[1], None, nums[3] if is_unit_token(vals_raw[2]) else nums[2], None, nums[4]]
                flags = list(flags); flags[1] = flags[3] = 'value_lost'
                self.diag['value_column_lost'] += 1
            ctx['last_prov'] = prov if kind in ('detail', 'detail_lostlabel', 'article_province_total') else None
            ctx['expect_label'] = kind in ('country_total', 'article_total') and numeric
            self._emit(fy, vol, seq, ri, ctx, kind, prov, nums, flags, vals_raw, texts)
            if deferred:
                self._article(ctx, deferred); ctx['country'] = None

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
        elif re.search(r'dutiable|duty|per cent|ad valorem|specific', t, re.I):
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
        # mark parent boundaries, then split on dashes
        t = re.sub(r',?\s*viz\.?\s*[:;]?\s*[—–-]?', ' :— ', t, flags=re.I)
        t = re.sub(r'\s*[:;]\s*[—–-]', ' :— ', t)
        t = re.sub(r'\s*[:;]\s*$', ' :— ', t)
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
        if not parents and leaf is None:
            return
        if re.search(r'recapitulation', text, re.I):
            ctx['recap'] = True
        old_leaf = ctx.get('article')
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
                x = re.sub(r'(&c|\betc\b)\.?', '', x.lower()); return re.sub(r'\W', '', x)
            a, b = _nk(leaf), _nk(old_leaf or '')
            # a page-top repeat is only possible while the article is still OPEN (its Total not yet printed), and
            # sibling leaves that differ in their numbers ('over 89 degrees' / 'over 90 degrees') are never the same
            digits_same = re.findall(r'\d+', leaf) == re.findall(r'\d+', old_leaf or '')
            same = leaf == old_leaf or (old_leaf and old_leaf != '?' and not ctx.get('article_closed') and digits_same and (
                   difflib.SequenceMatcher(None, a, b).ratio() >= 0.85 or
                   (min(len(a), len(b)) >= 8 and (a.startswith(b) or b.startswith(a)))))   # running-head abbreviation 'X, &c.'
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
        ctx['country'] = None
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
        if kind in ('detail', 'country_total', 'detail_lostlabel') and not ctx.get('article'):
            ctx['article'] = '?'; ctx['block_id'] = ctx.get('block_id', 0) + 1; ctx['leaf_used'] = False
            self.diag['article_heading_lost'] += 1
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
        for r in rows:
            k = r['row_kind']
            if k == 'article_province_total':
                if pend is None: pend = [0.0, 0.0, 0.0, False]
                pend[0] += r['val_imp'] or 0; pend[1] += r['qty_imp'] or 0; pend[2] += r['val_efc'] or 0
            elif k == 'article_total':
                pend = None
            elif k in ('detail', 'detail_lostlabel', 'country_noprov') and pend is not None:
                def _close(x, y, tol):
                    return x is not None and y and abs(x - y) <= max(0.5, tol * y)
                vi, ve, qi = r['val_imp'], r['val_efc'], r['qty_imp']
                exact = (_close(vi, pend[0], 0) and (qi is None or pend[1] == 0 or _close(qi, pend[1], 0))) \
                        or (_close(ve, pend[2], 0) and pend[2] > 1000)
                # an OCR digit slip in one column: val_imp within 0.5% and a second column within 0.5%
                near = _close(vi, pend[0], 0.005) and (_close(ve, pend[2], 0.005) or _close(qi, pend[1], 0.005)) and pend[0] > 1000
                if pend[0] > 0 and (exact or near):
                    r['row_kind'] = 'article_total_fused'; r['country'] = None; r['province'] = None
                    self.diag['page_top_total_fusion'] += 1
                pend = None
            elif k == 'country_total':
                pass
            else:
                pend = None
        # (b) label slip: the label column lost its first entry (usually 'Ontario') and shifted up one row, so
        #     'Quebec' carries Ontario's values and the last province ends up unlabelled just before the real
        #     country total.  Signature: a country run d1..dn, then TWO blank-label rows t1, t2 with
        #     sum(d) + t1 == t2.  If the run starts at Ontario the labels are intact and t1 is a trailing
        #     province whose label was lost.
        def _v(r): return r['val_imp'] if r['val_imp'] is not None else r['val_efc']
        i = 0; n = len(rows)
        while i < n:
            if rows[i]['row_kind'] != 'detail' or not rows[i]['province'] or rows[i]['country'] in (None, 'TOTAL'):
                i += 1; continue
            j = i
            while j < n and rows[j]['row_kind'] == 'detail' and rows[j]['country'] == rows[i]['country'] \
                    and rows[j]['block_id'] == rows[i]['block_id'] and rows[j]['province']: j += 1
            run = rows[i:j]
            if j + 1 < n and rows[j]['row_kind'] == 'country_total' and rows[j + 1]['row_kind'] == 'country_total' \
                    and rows[j]['block_id'] == rows[i]['block_id'] and rows[j + 1]['block_id'] == rows[i]['block_id']:
                t1, t2 = rows[j], rows[j + 1]
                provs = [r['province'] for r in run]
                inorder = all(p in PROVINCE_ORDER for p in provs) and \
                    [PROVINCE_ORDER.index(p) for p in provs] == sorted(PROVINCE_ORDER.index(p) for p in provs)
                dsum = sum(_v(r) or 0 for r in run); v1 = _v(t1) or 0; v2 = _v(t2) or 0
                if inorder and v2 > 0 and abs(dsum + v1 - v2) <= max(1, 0.001 * v2) and abs(dsum - v1) > 1:
                    if provs[0] != 'Ontario':
                        first = PROVINCE_ORDER[PROVINCE_ORDER.index(provs[0]) - 1]
                        shifted = [first] + provs[:-1]
                        for r, pv in zip(run, shifted):
                            r['province'] = pv; r['flags'] = (r['flags'] + ',' if r['flags'] else '') + 'label_slip'
                        t1['row_kind'] = 'detail'; t1['province'] = provs[-1]
                        t1['flags'] = (t1['flags'] + ',' if t1['flags'] else '') + 'label_slip'
                        self.diag['label_slip_repaired'] += 1
                    elif v1 > 0 and PROVINCE_ORDER.index(provs[-1]) + 1 < len(PROVINCE_ORDER):
                        t1['row_kind'] = 'detail'; t1['province'] = PROVINCE_ORDER[PROVINCE_ORDER.index(provs[-1]) + 1]
                        t1['flags'] = (t1['flags'] + ',' if t1['flags'] else '') + 'trailing_label_lost'
                        self.diag['trailing_label_lost'] += 1
                i = j + 2
            else:
                i = max(j, i + 1)
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
                    if ok and nxt is not None and nxt['row_kind'] in ('detail', 'detail_lostlabel') \
                            and nxt['country'] in ('?', None, '') and nxt['province'] == 'Ontario':
                        cty = r['country']
                        prev_art = tot_rows[0]['article'] if tot_rows else r['article']
                        prev_par = tot_rows[0]['article_parent'] if tot_rows else r['article_parent']
                        prev_blk = tot_rows[0]['block_id'] if tot_rows else r['block_id']
                        for x in run:
                            x['row_kind'] = 'article_province_total'; x['country'] = 'TOTAL'
                            x['article'] = prev_art; x['article_parent'] = prev_par; x['block_id'] = prev_blk
                            x['flags'] = (x['flags'] + ',' if x['flags'] else '') + 'heading_fused_into_total'
                        T['row_kind'] = 'article_total'; T['country'] = None
                        T['article'] = prev_art; T['article_parent'] = prev_par; T['block_id'] = prev_blk
                        # the lost-label rows that follow are the fused label's country
                        q = j + 1
                        while q < n and rows[q]['row_kind'] in ('detail', 'detail_lostlabel', 'country_total') \
                                and rows[q]['country'] in ('?', None, ''):
                            rows[q]['country'] = cty; rows[q]['country_inferred'] = 1
                            if rows[q]['row_kind'] == 'detail_lostlabel': rows[q]['row_kind'] = 'detail'
                            q += 1
                        self.diag['heading_fused_into_total'] += 1
                        i = q; continue
            i += 1
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
            if reg:
                ctx['regime'] = reg
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
        self.resolve_lost_labels(start_rows)
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
    print(f'wrote {OUT_CSV} ({len(p.rows)} rows) and {OUT_MD}', file=sys.stderr)


if __name__ == '__main__':
    main()
