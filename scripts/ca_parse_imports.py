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
        return head, t[-len(best):]
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
    if is_unit_token(t):
        return None, 'unit'
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
        for tm in P.TABLE_RE.finditer(tn):
            for cells in P.parse_table(tm.group(0)):
                if cells and DITTO_RE.match(cells[0][2]):
                    t = norm_label(cells[0][2])
                    if t and len(t) < 30 and not re.search(r'[—:]', t) and not t[0].islower():
                        self.vocab.add(t)
        self.vocab.discard('')

    # ---------------------------------------------------------------- regime C
    def parse_table_C(self, fy, vol, seq, body, ctx):
        NV = 5
        for ri, cells in enumerate(body):
            texts = [c for _, _, c in cells]
            spans = sum(cs for _, cs, _ in cells)
            joined = ' '.join(texts).strip()
            # section banners
            if (len(cells) == 1 or spans >= 7 and len(cells) <= 2) and re.search(r'DUTIABLE|FREE GOODS', joined, re.I):
                self._section(ctx, joined); continue
            if len(cells) < NV:
                # short rows: banner-ish or junk
                if re.search(r'DUTIABLE|FREE GOODS', joined, re.I):
                    self._section(ctx, joined)
                else:
                    self.diag['short_row'] += 1
                continue
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
            if len(labels) == 1 and b.strip() and not province_of(b) and not numeric:
                a, b = b, ''            # lone label with no values: treat as first-column text
            if len(labels) == 1 and b.strip() and not province_of(b) and numeric:
                # lone label with values: country+province fused, or a country whose province cell was dropped
                c2, p2 = split_trailing_province(b)
                if p2:
                    a, b = c2, p2; self.diag['split_country_province'] += 1
            if a is not None and len(labels) >= 2 and not province_of(b) and b.strip():
                c2, p2 = split_trailing_province(b)
                if p2: b = p2
            a_n = norm_label(a) if a is not None else None
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
                        self._units(ctx, vals_raw)
                        continue
                if re.search(r'[—:;]\s*$', frag) or re.search(r'(viz\.?|—)\s*$', frag):
                    self._article(ctx, ' '.join(ctx.get('article_buf', []) + [frag]))
                    ctx['article_buf'] = []
                    self._units(ctx, vals_raw)
                    continue
                if a_n in self.vocab and units_only:
                    # a country label whose values are on the next row (or blank)
                    ctx['country'] = a_n; ctx['article_buf'] = []
                    continue
                if re.match(r'totals?\b', a_n, re.I):
                    ctx['country'] = 'TOTAL'; continue
                if units_only and len(a_n) > 3 and (not ctx.get('article_buf')) and not frag.endswith('-') \
                        and any(is_unit_token(v) for v in vals_raw):
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
            # ---- 'Article Country' fused without a dash
            if a_n and numeric and a_n not in self.vocab and not re.match(r'totals?\b', a_n, re.I):
                head, tail = split_trailing_country(a_n, self.vocab)
                if tail:
                    if head:
                        self._article(ctx, head)
                    a_n = tail; self.diag['fused_article_country_nodash'] += 1
            # ---- fused 'Article— Country' in one cell
            if a_n and '—' in a_n and numeric and not re.match(r'total', a_n, re.I):
                head, tail = a_n.rsplit('—', 1)
                tail = tail.strip(' .')
                if not tail:
                    self._article(ctx, head + '—'); a_n = ''
                    ctx['country'] = None; self.diag['country_label_lost'] += 1
                elif tail and not province_of(tail) and (tail in self.vocab or re.match(r'totals?\b', tail, re.I) or len(tail) < 25):
                    self._article(ctx, head + '—')
                    a_n = tail
                    self.diag['fused_article_country'] += 1
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
                elif b.strip():
                    # something in province position that is not a province: country row missing province?
                    cand = norm_label(b)
                    if re.match(r'totals?\b', cand, re.I):
                        kind = 'article_total'; ctx['country'] = 'TOTAL'
                    else:
                        ctx['country'] = cand; kind = 'country_noprov'; self.diag['label_in_province_slot'] += 1
                else:
                    kind = 'article_total' if ctx.get('country') == 'TOTAL' else 'country_total'
            if not numeric and kind in ('detail', 'article_province_total'):
                self.diag['label_row_no_values'] += 1
            ctx['last_prov'] = prov if kind in ('detail', 'detail_lostlabel', 'article_province_total') else None
            ctx['expect_label'] = kind in ('country_total', 'article_total')
            self._emit(fy, vol, seq, ri, ctx, kind, prov, nums, flags, vals_raw, texts)

    # ---------------------------------------------------------------- regime B (1877)
    def parse_table_B(self, fy, vol, seq, body, ctx):
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
            # a value row: pair with the oldest pending label (slip) else it is a subtotal
            if pending_labels:
                country = pending_labels.pop(0); ctx['country'] = country; kind = 'detail'
            else:
                kind = 'country_total_or_article_total'
                kind = 'article_total'
            self._emit(fy, vol, seq, ri, ctx, kind, ctx.get('province'), nums, flags, vals_raw, texts)

    # ---------------------------------------------------------------- regime A (1869-73)
    def parse_table_A(self, fy, vol, seq, body, ctx):
        NV = 8
        pending_labels = []
        for ri, cells in enumerate(body):
            texts = [c for _, _, c in cells]
            joined = ' '.join(texts).strip()
            if len(cells) < NV:
                if re.search(r'DUTY|FREE GOODS|PER CENT|SPECIFIC|AD VALOREM', joined, re.I):
                    self._section(ctx, joined)
                else:
                    self.diag['short_row'] += 1
                continue
            vals_raw = texts[-NV:]; labels = texts[:-NV]
            parsed = [parse_num(v, cents_ok=(i == 7)) for i, v in enumerate(vals_raw)]
            nums = [p[0] for p in parsed]; flags = [p[1] for p in parsed]
            numeric = any(v is not None for v in nums)
            if 'fused' in flags:
                self.diag['fused_cells'] += 1
            art = norm_label(labels[0]) if len(labels) >= 2 and labels[0].strip() else None
            cty = norm_label(labels[-1]) if labels and labels[-1].strip() else None
            if art:
                if re.search(r'DUTY|FREE GOODS|PER CENT|SPECIFIC|AD VALOREM', art, re.I):
                    m = re.match(r'(.*?(?:DUTY|GOODS|CENT|AD VALOREM)[^A-Za-z]*(?:—Continued\.?)?)(.*)', art, re.I)
                    if m:
                        self._section(ctx, m.group(1)); art = m.group(2).strip() or None
                if art:
                    self._article(ctx, art); pending_labels = []
                self._units(ctx, vals_raw)
            if cty and not re.match(r'totals?\b', cty, re.I):
                pending_labels.append(cty)
            if not numeric:
                continue
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
            same = leaf == old_leaf or (old_leaf and old_leaf != '?' and (
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
        else:
            ctx['leaf_used'] = False
        ctx['country'] = None
        ctx['unit'] = None
        ctx['last_prov'] = None

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
            elif k in ('detail', 'detail_lostlabel') and pend is not None:
                if pend[0] > 0 and r['val_imp'] is not None and abs(r['val_imp'] - pend[0]) < 0.5 and \
                        (r['qty_imp'] is None or pend[1] == 0 or abs(r['qty_imp'] - pend[1]) < 0.5):
                    r['row_kind'] = 'article_total_fused'; r['country'] = None; r['province'] = None
                    self.diag['page_top_total_fusion'] += 1
                pend = None
            elif k == 'country_total':
                pass
            else:
                pend = None
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
                    if prev is not None and rank(prev) == 0 and nxt is not None and rank(nxt) >= 2: guess = 'United States'
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
