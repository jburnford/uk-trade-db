#!/usr/bin/env python3
"""Tier 2: parse the country-detail sections of the Annual Statements into
country_obs — article x country x (quantity, value) for the statement year.

Sections (each printed A-Z by article, countries as rows under each):
  GENERAL IMPORTS  1. ARTICLES FREE OF DUTY        two-up (label,qty,val)x2
                   2. ARTICLES SUBJECT TO DUTY     single: label, import qty,
                       declared value, home-consumption qty, duty received,
                       duty rate (rate not kept)
  GENERAL EXPORTS  1. PRODUCE OF THE UNITED KINGDOM   two-up
                   2. FOREIGN AND COLONIAL PRODUCE    two-up

Section state is sticky across tables (running page headers appear on only
some pages, and OCR drops some theads): text zones switch it via section
titles/running headers, other table families (abstract captions, ports,
transhipment...) reset it. A table's own thead ("WHENCE IMPORTED" / "TO
WHICH EXPORTED"; "CONSUMP" marks the duty layout) is authoritative when
present; thead-less tables must look like the layout (mostly 3/6-cell rows
with From/To/ditto labels) to be fed to the sticky section.

Row model per logical column: bold flush-left "ARTICLE :" headers open a
group; indented/ditto "sub-article :" headers open a sub; "From X"/"To X"/
ditto rows are countries; printed 'Total' rows are kept (country_raw=
'TOTAL') — sum(countries) vs printed total is the arithmetic check.
Units ride in the first quantity cell of a block ("Cwts. 3,159") or in a
header row's cells ("Gallons." / "£").

Usage: python3 parse_country.py [as_dir ...]   (tn_* monthly volumes skipped)
"""
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).parent))
from parse_abstract import BASE, CELL_RE, ROW_RE, TAG_RE, clean, parse_num

UNIT_PREFIX_RE = re.compile(
    r'^\s*([A-Za-z][A-Za-z .]{1,25}?)\.?\s*(?=[\d,—–-]|$)')
CONTD_RE = re.compile(
    r'\s*\(Cont\s*[d.]*\s*\)?[.:]?\s*'          # "(Contd):"
    r'|\s*[—\-–]\s*cont(?:inue)?d\s*[.:]?\s*', re.I)   # "—continued."
SEE_RE = re.compile(r'\bSee\b', re.I)
NUMERICISH_RE = re.compile(r'^[\d,.\s—–\-]*$')
DITTO_RE = re.compile(r'^\s*[”“‟"„«»\'’‘‚]+')
# ditto marks encode DEPTH in the printed hierarchy: one token repeats the
# group ("  \" Sawn or Split:"), two repeat group + sub-article
# ("  \" \" Fir:" = Sawn or Split : Fir). Tokens may be spaced quotes,
# double commas or double periods, per OCR mood.
DITTO_TOKEN_RE = re.compile(r'^\s*([”“‟"„«»\'’‘‚]+|,,|\.\.)')


def strip_dittos(s):
    """-> (depth, remainder)"""
    depth = 0
    while True:
        m = DITTO_TOKEN_RE.match(s)
        if not m:
            return depth, s.strip()
        depth += 1
        s = s[m.end():]


def _vocab_norm(s):
    import unicodedata
    s = unicodedata.normalize('NFKD', s or '').encode(
        'ascii', 'ignore').decode()
    s = s.lower().replace('&', ' and ')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', s)).strip()


def build_vocab(seeds):
    """From pass-1 outputs across ALL volumes: names that consistently
    appear as groups vs sub-articles. A name qualifies when it shows up in
    >=3 volumes and >=3x more often in one role than the other."""
    g_vols, s_vols = defaultdict(set), defaultdict(set)
    g_cnt, s_cnt = Counter(), Counter()
    for o in seeds:
        if o[3]:
            k = _vocab_norm(o[3])
            g_vols[k].add(o[0])
            g_cnt[k] += 1
        if o[4]:
            k = _vocab_norm(o[4])
            s_vols[k].add(o[0])
            s_cnt[k] += 1
    groups, subs = set(), set()
    for k in set(g_vols) | set(s_vols):
        if not k:
            continue
        g, s = g_cnt[k], s_cnt[k]
        if len(g_vols[k]) >= 3 and g >= 3 * max(s, 1):
            groups.add(k)
        elif len(s_vols[k]) >= 3 and s >= 3 * max(g, 1):
            subs.add(k)
    return frozenset(groups), frozenset(subs)

SECTION_MARKERS = [
    # (regex on upper-cased zone text, section) — last marker in zone wins.
    # Markers must look like section TITLES (digit-prefixed) or running page
    # headers (parenthesized): the bare phrases also occur inside abstract
    # captions ("TOTAL VALUE of ARTICLES, the PRODUCE ... EXPORTED") and the
    # late-era italics note ("Articles subject to Duty are printed in
    # Italics"), which must not hijack the section state.
    (re.compile(r'\d\s*\.?\s*[—\-–]?\s*(IMPORTS OF )?ARTICLES,? FREE OF DUTY'
                r'|\(ARTICLES FREE OF DUTY'), ('import', 'free')),
    (re.compile(r'\d\s*\.?\s*[—\-–]?\s*(IMPORTS AND CONSUMPTION OF )?'
                r'ARTICLES,? SUBJECT TO DUTY(?!\s+ARE)'
                r'|\(ARTICLES SUBJECT TO DUTY'), ('import', 'duty')),
    (re.compile(r'\d\s*\.?\s*[—\-–]?\s*(EXPORTS OF )?(ARTICLES,? THE )?'
                r'PRODUCE AND MANUFACTURES? OF THE UNITED KINGDOM'
                r'|\(PRODUCE OF THE UNITED KINGDOM'), ('export_uk', '')),
    (re.compile(r'\d\s*\.?\s*[—\-–]?\s*(EXPORTS OF )?ARTICLES OF FOREIGN AND'
                r' COLONIAL (PRODUCE|MERCHANDISE)'
                r'|\(FOREIGN AND COLONIAL (PRODUCE|MERCHANDISE)'),
     ('reexport', '')),
]
RESET_RE = re.compile(
    r'TOTAL QUANTITIES|TOTAL VALUE|AT EACH PORT|TRANSHIPPED|TRANSSHIPPED'
    r'|COIN AND BULLION|CUSTOMS DUTIES RECEIVED'
    r'|IMPORTS AND EXPORTS FROM AND TO|NAVIGATION'
    r'|IMPORTS THEREFROM|EXPORTS THERETO')   # per-country section family

# regions that head origin-breakdowns under an article but appear too
# rarely per volume for the pass-1 frequency harvest to catch them
SEED_COUNTRIES = frozenset(n.casefold() for n in (
    'Western Coast of Africa', 'Eastern Africa', 'British East Indies',
    'British North America', 'United States of America', 'Australasia',
    'British India', 'Channel Islands', 'British West India Islands',
))

# top-level trading nations: when one of these appears under an open region
# context ("From Australasia: ... „ Canada"), it is a SIBLING country, not a
# sub-entry — the ditto repeats "From", it is not "Australasia's Canada".
# Genuine sub-divisions (Victoria, "On the Atlantic", "Bombay") are NOT here
# and stay nested.
TOP_COUNTRIES = frozenset(n.casefold() for n in (
    'Canada', 'British North America', 'Newfoundland', 'United States',
    'United States of America', 'Russia', 'Sweden', 'Norway', 'Germany',
    'France', 'Denmark', 'Holland', 'Belgium', 'Spain', 'Portugal', 'Italy',
    'Austrian Territories', 'Roumania', 'Greece', 'Turkey', 'Egypt',
    'British India', 'Australasia', 'China', 'Japan', 'Brazil', 'Chili',
    'Argentine Republic', 'Uruguay', 'Peru', 'Mexico',
))


def cell_text(c):
    return clean(c.replace('<br/>', ' ').replace('<br>', ' '))


def indent_of(c):
    raw = TAG_RE.sub('', c.replace('&nbsp;', ' ').replace('\xa0', ' '))
    return len(raw) - len(raw.lstrip(' '))


class SectionState:
    """Article/sub-article state; persists across pages of one section."""

    def __init__(self, volume, flow, duty, year, out, country_names=(),
                 group_vocab=(), sub_vocab=()):
        self.volume, self.flow, self.duty, self.year = volume, flow, duty, year
        self.group = None
        self.sub = None
        self.sub1 = None          # level-1 sub (parent of ditto-depth-2)
        self.cctx = None          # country whose port/coast rows follow
        self.cctx_sum = 0.0       # value sum of the context's sub-rows
        self.unit = None
        self.country_names = frozenset(country_names) | SEED_COUNTRIES
        self.group_vocab = group_vocab    # names known corpus-wide as groups
        self.sub_vocab = sub_vocab        # ... as sub-articles
        self.out = out
        self.seq = 0

    def _classify(self, label_raw, unit_probe, has_vals):
        """Update group/sub/cctx state from a row label. Return the resolved
        country string for a data row, or None if the row was a header /
        cross-ref / context opener / skip. `unit_probe` is the first value
        cell, consulted only for header-row unit detection."""
        label = cell_text(label_raw)
        name = CONTD_RE.sub('', label).strip()
        if not name or NUMERICISH_RE.match(name):
            return None
        if SEE_RE.search(name) and not has_vals:
            return None                              # cross-reference line
        depth, name = strip_dittos(name)
        ditto = depth > 0
        # trailing dash/dot leaders ("Germany . . . . ." / "Holland - - -")
        name = re.sub(r'(?:\s*[.·])+\s*$|[\s\-‐-―]+$', '', name)
        stripped = name.rstrip(' :').strip()
        if not stripped:
            return None
        if name.endswith(':') and not has_vals:
            # a known country with a colon opens a port/coast breakdown
            # ("” United States of America :" -> On the Atlantic ... Total),
            # not a new sub-article. "From X :" is a country header by
            # construction ("Teak: From British East Indies: Bombay ...").
            m_from = re.match(r'^(?:from|to)\s+(.*)', stripped, re.I)
            if m_from:
                self.cctx = m_from.group(1).strip()
                self.cctx_sum = 0.0
                return None
            if stripped.casefold() in self.country_names:
                self.cctx = stripped
                self.cctx_sum = 0.0
                return None
            bold = '<b>' in label_raw or '<strong>' in label_raw
            letters = [c for c in stripped if c.isalpha()]
            caps = sum(c.isupper() for c in letters) / max(len(letters), 1)
            # corpus vocabulary first: the same article names repeat across
            # 28 volumes, so a name known corpus-wide as a group (or sub)
            # overrides the local bold/indent/A-Z heuristics that OCR noise
            # defeats
            nk = _vocab_norm(stripped)
            if nk in self.group_vocab:
                is_group = True
            elif nk in self.sub_vocab:
                is_group = False
            else:
                # top articles are printed in caps and run A-Z; sub-articles
                # are indented/ditto'd — but OCR drops indents, so a mixed-
                # case bold header ("Hewn, Fir:" under "WOOD and TIMBER")
                # only opens a group when it barely advances the A-Z
                # sequence ("Wool" after "WOOD and TIMBER"), never on a big
                # jump ("Unenumerated" under "COTTON" is a sub)
                is_group = bold and not ditto and indent_of(label_raw) <= 1 \
                    and (caps >= 0.5 or self.group is None
                         or (stripped.casefold() >= self.group.casefold()
                             and ord(stripped.casefold()[0])
                             - ord(self.group.casefold()[0]) <= 2))
            if is_group:
                self.group, self.sub, self.sub1 = stripped, None, None
            elif depth >= 2 and self.sub1:
                # "  \" \" Fir:" under "  \" Sawn or Split:" — a child of
                # the level-1 sub, not its sibling
                self.sub = f'{self.sub1} : {stripped}'
            else:
                self.sub = stripped
                self.sub1 = stripped
            self.cctx = None
            self.cctx_sum = 0.0
            # header rows can carry the block's units ("Gallons." | "£")
            self.unit = None
            if unit_probe is not None:
                u = cell_text(unit_probe).strip(' .')
                if u and not re.search(r'\d', u) and u != '£' and len(u) < 26:
                    self.unit = u
            return None
        if self.group is None or not has_vals:
            return None
        low = stripped.lower()
        m = re.match(r'^(?:from|to)\s+(.*)', stripped, re.I)
        if low.startswith('total'):
            return 'TOTAL'
        if m:
            return m.group(1).strip(' -') or None
        return stripped or None          # ditto row / wrapped continuation

    def _num(self, cell, set_unit=False):
        txt = cell_text(cell).replace('£', '').strip()
        mu = UNIT_PREFIX_RE.match(txt)
        if mu:
            if set_unit:
                self.unit = mu.group(1).strip(' .')
            txt = txt[mu.end():].strip()
        return parse_num(txt)[0]

    def _apply_cctx(self, country, ref_val):
        """Rename a country row inside an open port/coast context; ref_val
        is the row's value (last year for multi-year) for the block-total
        guard. Returns the (possibly renamed) country."""
        if not self.cctx:
            return country
        if country == 'TOTAL':
            if ref_val is not None and self.cctx_sum > 0 \
                    and ref_val > 2 * self.cctx_sum:
                self.cctx = None       # this is the BLOCK total, not the
                self.cctx_sum = 0.0    # context country's own total
                return country
            country = self.cctx
            self.cctx = None
            self.cctx_sum = 0.0
            return country
        # a full top-level nation under a region header is a SIBLING, not a
        # sub-entry ("From Australasia: ... „ Canada" = From Canada). Close
        # the context and treat it as its own country.
        if country.casefold() in TOP_COUNTRIES:
            self.cctx = None
            self.cctx_sum = 0.0
            return country
        self.cctx_sum += ref_val or 0
        return f'{self.cctx} : {country}'

    def feed(self, label_raw, values):
        """Single-year two-up row: label + [quantity, value]."""
        has_vals = any(re.search(r'\d', cell_text(v) or '') for v in values)
        country = self._classify(label_raw, values[0] if values else None,
                                 has_vals)
        if country is None:
            return
        nums = [self._num(v, set_unit=(i == 0))
                for i, v in enumerate(values)]
        nums += [None] * (4 - len(nums))
        country = self._apply_cctx(country, nums[1])
        self.seq += 1
        self.out.append([self.volume, self.flow, self.duty,
                         self.group, self.sub, country, self.unit, self.year,
                         nums[0], nums[1], nums[2], nums[3], self.seq])

    def feed_multiyear(self, label_raw, qty_cells, val_cells, years):
        """Late-era wide row: label + N quantity cols + N value cols, one
        column per year (as_1897-99). Emits one record per year."""
        cells = list(qty_cells) + list(val_cells)
        has_vals = any(re.search(r'\d', cell_text(v) or '') for v in cells)
        country = self._classify(label_raw, qty_cells[0] if qty_cells
                                 else None, has_vals)
        if country is None:
            return
        qtys = [self._num(c, set_unit=(i == 0))
                for i, c in enumerate(qty_cells)]
        vals = [self._num(c) for c in val_cells]
        ref = next((v for v in reversed(vals) if v is not None), None)
        country = self._apply_cctx(country, ref)
        for yr, q, v in zip(years, qtys, vals):
            if q is None and v is None:
                continue
            self.seq += 1
            self.out.append([self.volume, self.flow, self.duty,
                             self.group, self.sub, country, self.unit, yr,
                             q, v, None, None, self.seq])


def thead_kind(piece, rows):
    headm = re.search(r'<thead[^>]*>(.*?)</thead>', piece, re.S)
    src = headm.group(1) if headm else ' '.join(
        r for r in rows[:2] if '<th' in r)
    t = re.sub(r'\s+', ' ', TAG_RE.sub(' ', src)).upper()
    if 'TRANSHIP' in t or 'TRANSSHIP' in t:
        return None            # transhipment family, not country detail
    if 'ARTICLES AND COUNTRIES' not in t and 'ARTICLES AND COUNTIES' not in t:
        return None   # "COUNTRIES WHENCE IMPORTED" alone = country-totals
    if 'WHENCE IMPORTED' in t:
        return ('import', 'duty') if 'CONSUMP' in t else ('import', 'free')
    if 'TO WHICH EXPORTED' in t:
        return ('export', None)
    return None


def looks_like_country_table(body_rows):
    if len(body_rows) < 5:
        return False
    ok = sum(1 for cells in body_rows if len(cells) >= 3)
    if ok / len(body_rows) < 0.6:
        return False
    labels = [cell_text(c[0]) for c in body_rows if c]
    hits = sum(1 for lab in labels if re.match(
        r'\s*(From |To |Total|[”"„])', lab))
    return hits >= 3


# a YEAR-COLUMN header cell is a bare year ("1894." / "1895"), not a year
# embedded in a comma-formatted trade figure ("1,858" loads) — matching the
# latter false-positives on real country values in the 1830-1949 range
BARE_YEAR_RE = re.compile(r'^\s*(18[3-9]\d|19[0-4]\d)\s*[.,]?\s*$')


def is_year_column_table(piece, rows):
    """Abstract summary tables (article x 5 years) leak into the country
    parser when their thead lacks 'WHENCE IMPORTED'. They are identifiable
    by >=3 bare-year column cells — country-detail tables have
    QUANTITIES/VALUE columns, never year columns."""
    for r in rows[:4]:
        cells = [cell_text(c) for c in CELL_RE.findall(r)]
        years = {c for c in cells if BARE_YEAR_RE.match(c)}
        if len(years) >= 3:
            return True
    return False


def year_header(rows):
    """Late-era country tables (as_1897-99) carry a year sub-header row
    ('1893. 1894. 1895. 1896. 1897.' x2, for QUANTITIES then VALUE).
    Return the distinct years in order, or None if absent."""
    for r in rows[:5]:
        cells = [cell_text(c) for c in CELL_RE.findall(r)]
        yrs = [int(BARE_YEAR_RE.match(c).group(1))
               for c in cells if BARE_YEAR_RE.match(c)]
        if len(yrs) >= 4:
            seen = []
            for y in yrs:
                if y not in seen:
                    seen.append(y)
            if len(seen) >= 2:
                return seen
    return None


def parse_volume_countries(md_path, volume, year, out, country_names=(),
                           group_vocab=(), sub_vocab=()):
    md = md_path.read_text(encoding='utf-8', errors='replace')
    pieces = re.split(r'(<table[^>]*>.*?</table>)', md, flags=re.S)
    cur = None
    states = {}
    n_tables = 0
    for piece in pieces:
        if not piece.startswith('<table'):
            z = re.sub(r'\s+', ' ', piece.replace('*', '')).upper()
            best, pos = None, -1
            for rx, section in SECTION_MARKERS:
                for m in rx.finditer(z):
                    if m.start() > pos:
                        best, pos = section, m.start()
            reset = RESET_RE.search(z)
            reset_pos = max((m.start() for m in RESET_RE.finditer(z)),
                            default=-1)
            if reset_pos > pos:
                cur = None
            elif best:
                cur = best
            continue
        rows = ROW_RE.findall(piece)
        if not rows:
            continue
        # ABSTRACT summary tables (article x 5 years, thead lacks 'ARTICLES
        # AND COUNTRIES') leak into late-era country sections; ingesting them
        # files article labels as countries and bleeds groups (Wood->Wool).
        # Reject only these — real country tables (thead has 'ARTICLES AND
        # COUNTRIES') keep parsing, even in the late-era 5-year layout, which
        # is handled downstream. A country table without any thead is matched
        # by looks_like_country_table below.
        kind = thead_kind(piece, rows)
        if kind is None and is_year_column_table(piece, rows):
            continue        # skip the abstract table; keep the sticky section
        body_rows = [CELL_RE.findall(r) for r in rows if '<th' not in r]
        body_rows = [c for c in body_rows if c]
        if kind:
            flow, duty = kind
            if flow == 'import':
                cur = (flow, duty)
            elif cur in (('export_uk', ''), ('reexport', '')):
                pass                       # which export: keep sticky state
            else:
                cur = ('export_uk', '')
        elif not (cur and looks_like_country_table(body_rows)):
            continue
        if cur is None:
            continue
        flow, duty = cur
        skey = (flow, duty)
        if skey not in states:
            states[skey] = SectionState(volume, flow, duty, year, out,
                                        country_names, group_vocab,
                                        sub_vocab)
        st = states[skey]
        n_tables += 1
        years5 = year_header(rows)
        if years5:
            # late-era wide layout: label + N quantity cols + N value cols,
            # one column per year (as_1897-99). Route only rows wide enough
            # to carry the full year block; narrower rows (page furniture)
            # fall through harmlessly.
            n = len(years5)
            for cells in body_rows:
                if len(cells) >= 1 + n:
                    st.feed_multiyear(cells[0], cells[1:1 + n],
                                      cells[1 + n:1 + 2 * n], years5)
        elif duty == 'duty':
            for cells in body_rows:
                if len(cells) >= 2:
                    st.feed(cells[0], cells[1:5])
        else:
            # two-up: run the whole left column, then the right column
            for lo, hi in ((0, 3), (3, 6)):
                for cells in body_rows:
                    part = cells[lo:hi]
                    if part:
                        st.feed(part[0], part[1:3])
    return n_tables


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'))
    con.execute('DROP TABLE IF EXISTS country_obs')
    con.execute('''CREATE TABLE country_obs (
        volume VARCHAR, flow VARCHAR, duty VARCHAR,
        article_group VARCHAR, article VARCHAR, country_raw VARCHAR,
        unit VARCHAR, year INTEGER, quantity DOUBLE, value DOUBLE,
        consumption DOUBLE, duty_received DOUBLE, row_seq INTEGER)''')
    raws = sys.argv[1:] or sorted(
        str(p) for p in (BASE / 'raw').iterdir() if p.name.startswith('as_'))
    # pass 1 over ALL volumes: harvest country names (per volume) and the
    # corpus-wide group/sub vocabulary for pass 2's header classification
    vols = []
    all_seeds = []
    for rd in raws:
        rd = Path(rd)
        mds = list(rd.rglob('*.md'))
        if not mds:
            continue
        volume = rd.name
        year = int(volume[-4:])
        seed = []
        parse_volume_countries(mds[0], volume, year, seed)
        freq = Counter(o[5].casefold() for o in seed
                       if o[5] and o[5] != 'TOTAL' and ' : ' not in o[5])
        names = frozenset(n for n, c in freq.items() if c >= 4)
        vols.append((mds[0], volume, year, names))
        all_seeds.extend(seed)
    group_vocab, sub_vocab = build_vocab(all_seeds)
    print(f'vocabulary: {len(group_vocab)} group names, '
          f'{len(sub_vocab)} sub-article names\n')
    for md, volume, year, names in vols:
        out = []
        nt = parse_volume_countries(md, volume, year, out, names,
                                    group_vocab, sub_vocab)
        if out:
            con.executemany(
                'INSERT INTO country_obs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                out)
        n_tot = sum(1 for o in out if o[5] == 'TOTAL')
        print(f'{volume}: {nt} country tables, {len(out):,} rows '
              f'({n_tot:,} printed totals)')
    con.commit()
    print('\n== summary ==')
    for row in con.execute('''SELECT flow, duty, count(*),
            count(DISTINCT article_group), count(DISTINCT country_raw)
            FROM country_obs GROUP BY 1,2 ORDER BY 1,2''').fetchall():
        print(' ', row)


if __name__ == '__main__':
    main()
