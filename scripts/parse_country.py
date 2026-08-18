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

Two-up GEOMETRY varies by OCR run, esp. 1872-82: besides the plain
(label,qty,val)x2 6-cell rows, tables print 8 slots (label, dash-leader,
qty, val)x2, 10/12-slot export variants with extra quantity columns
(Yards+Lbs), colspan-2 labels, and pages where one half is entirely blank
colspan cells. A fixed (0,3)/(3,6) slice loses the whole right half (the
British Possessions continuation of big origin tables lands there) and
shifts the left half's quantity into value. Tables whose modal expanded
width is >=7 therefore get per-table geometry: colspan-aware slot
expansion, the second label column found by alpha-dominance, and qty/val
slots picked by digit-dominance within each half (first=qty, last=val).

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
UNIT_WORD_RE = re.compile(
    r'(?:Cwts?|Tons?|Loads?|Gall?on?s?|Lbs?|Number|No|Pieces?|Qrs?'
    r'|Quarters?|Bushels?|Yards?|Doz(?:en)?s?|Ozs?|Value)\s*\.?', re.I)
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
    'Argentine Republic', 'Uruguay', 'Peru', 'Mexico', 'New Granada',
    'United States of Colombia',
))


def cell_text(c):
    return clean(c.replace('<br/>', ' ').replace('<br>', ' '))


TD_ATTR_RE = re.compile(r'<t[hd]([^>]*)>(.*?)</t[hd]>', re.S)
COLSPAN_RE = re.compile(r'colspan\s*=\s*"?(\d+)')
LEADERISH_RE = re.compile(r'^[\s\-‐-―—–.·°]*$')


def expand_slots(row_html):
    """Cells with colspan expanded to column slots (raw HTML kept: the
    label classifier needs <b>/indent)."""
    slots = []
    for attrs, content in TD_ATTR_RE.findall(row_html):
        m = COLSPAN_RE.search(attrs)
        slots.append(content)
        slots.extend([''] * ((int(m.group(1)) if m else 1) - 1))
    return slots


def twoup_geometry(exp_rows, width):
    """For a wide (>=7-slot) two-up table, locate the right half's label
    column by alpha-dominance and, per half, the qty/val slots by digit-
    dominance. Returns (mid, [(qty_i, val_i), (qty_i, val_i)]) with slot
    indexes relative to each half's start (None = column absent)."""
    n_rows = 0
    alpha = [0] * width
    digit = [0] * width
    pound = [0] * width
    for e in exp_rows:
        texts = [cell_text(c) if i < len(e) else ''
                 for i, c in enumerate(e[:width])]
        if not any(texts):
            continue
        n_rows += 1
        for i, t in enumerate(texts):
            if i >= len(e):
                continue
            if re.search(r'\d', t):
                digit[i] += 1
            elif not LEADERISH_RE.match(t) \
                    and sum(c.isalpha() for c in t) >= 3:
                alpha[i] += 1
            if '£' in t:
                pound[i] += 1
    # the right half starts at the second label column; blank-half pages
    # (alpha nowhere) fall back to the midpoint
    cand = range(2, width - 1)
    mid = max(cand, key=lambda i: alpha[i]) if cand else width // 2
    if alpha[mid] < 2:
        mid = width // 2
    halves = [(0, mid), (mid, width)]
    picks = []
    thresh = max(2, 0.15 * n_rows)
    for lo, hi in halves:
        slots = [i for i in range(lo + 1, hi) if digit[i] >= thresh]
        if len(slots) >= 2:
            picks.append((slots[0] - lo, slots[-1] - lo))
        elif len(slots) == 1:
            s = slots[0]
            picks.append((None, s - lo) if pound[s] else (s - lo, None))
        else:
            picks.append((1, 2) if hi - lo >= 3 else (None, None))
    return mid, picks


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
        self.pending = []         # row-slip cascade (see feed)
        self.slip_colon = False   # cascade came from a `From X :` heading, so
        self.slip_rows = []       # it is provisional until the block ends
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
            # When the row's cells hold a bare unit ("Lbs." | "£") the
            # reading is AMBIGUOUS and only the end of the block settles it:
            #   * the heading legitimately carries the block's unit caption
            #     ("From West Coast of Africa (Foreign) : | Cwts. | £" over
            #     indented Fernando Po / Portuguese Possessions / ...) — by
            #     far the common case, 82 blocks of 83 corpus-wide; or
            #   * the OCR pushed every value one row down (as_1882 wool,
            #     "From Russia:" a plain sibling of "„ Denmark"), the
            #     ROW-SLIP signature, since units never print without their
            #     figures.
            # Only the slip leaves an orphan label-less numbers row at the
            # block's end. So shift provisionally and mark the block: if it
            # drains at the printed Total instead of at an orphan row, feed()
            # un-shifts it in place (_unshift_colon_block).
            m_from = re.match(r'^(?:from|to)\s+(.*)', stripped, re.I)
            if m_from:
                if self._unit_only(unit_probe):
                    self._queue_colon_slip(m_from.group(1).strip(),
                                           unit_probe)
                    return None
                self.cctx = m_from.group(1).strip()
                self.cctx_sum = 0.0
                return None
            if stripped.casefold() in self.country_names:
                if self._unit_only(unit_probe):
                    self._queue_colon_slip(stripped, unit_probe)
                    return None
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
            # slip cascade never crosses blocks; an unresolved colon-path
            # shift ended without a Total, so it never earned its orphan
            self._drain_colon_slip()
            self.pending.clear()
            # header rows can carry the block's units ("Gallons." | "£")
            self.unit = None
            if unit_probe is not None:
                u = cell_text(unit_probe).strip(' .')
                if u and not re.search(r'\d', u) and u != '£' and len(u) < 26:
                    self.unit = u
            return None
        if not has_vals:
            # colon-less row-slip signature ("From Russia" | "Loads." | "£"
            # — left column of the same slipped pages)
            m = re.match(r'^(?:from|to)\s+(.*)', stripped, re.I)
            if m and self.group is not None \
                    and self._unit_only(unit_probe):
                self.pending.append(m.group(1).strip(' -'))
                self.slip_colon = False    # colon-less: the slip is real
            return None
        if self.group is None:
            return None
        low = stripped.lower()
        m = re.match(r'^(?:from|to)\s+(.*)', stripped, re.I)
        if low.startswith('total'):
            return 'TOTAL'
        if m:
            return m.group(1).strip(' -') or None
        return stripped or None          # ditto row / wrapped continuation

    def _queue_colon_slip(self, name, unit_probe):
        """Open a provisional row-slip cascade for a `From X :` heading whose
        cells hold only the block's unit caption. Take the unit from the
        caption — it is the block's unit whichever reading wins, and these
        blocks otherwise parse unit-less."""
        self.pending.append(name)
        self.slip_colon = True
        self.slip_rows = []
        u = cell_text(unit_probe).strip(' .')
        if u and u != '£' and not re.search(r'\d', u) and len(u) < 26:
            self.unit = u

    def _unshift_colon_block(self, leftover):
        """Undo a provisional colon-path shift: the block drained at its
        printed Total, so no orphan numbers row existed and the values were
        never slipped. Every emitted row holds the label of the row ABOVE
        it, and `leftover` is the last label, whose numbers were dropped.
        Re-pair each row with its own label and reopen the heading as the
        port/coast context so members read 'Parent : Child'.

        Only rows the cascade itself shifted are touched: the multi-year
        layout (feed_multiyear, as_1897-99) never consumes `pending`, so its
        rows were paired normally and must be left alone."""
        rows = self.slip_rows
        if not rows:
            return
        head, labels = rows[0][5], [r[5] for r in rows[1:]] + [leftover]
        self.cctx, self.cctx_sum = head, 0.0
        for row, label in zip(rows, labels):
            row[5] = self._apply_cctx(label, row[9])
        self.cctx, self.cctx_sum = None, 0.0   # never rename the Total row

    def _drain_colon_slip(self):
        """Resolve an open colon-path shift as un-slipped (the common case)."""
        if self.slip_colon and self.pending:
            self._unshift_colon_block(self.pending[0])
        self.slip_colon = False

    def _resolve_colon_slip(self, total_nums):
        """Settle a provisional colon-path shift at the block's printed Total.

        A 'Total' SMALLER than the block's largest member cannot be a block
        total: there the OCR really did push every value down a row, and the
        Total row holds the last member's own figures while the true total
        prints below it (as_1874 palm oil — 'Total 10,193' is Other
        Countries, the real total 1,067,767 follows). Keep the shift and
        emit the queued label with these numbers; return True so the caller
        does not also record a Total row. Otherwise the block was never
        slipped — un-shift it."""
        self.slip_colon = False
        qtys = [r[8] for r in self.slip_rows if r[8] is not None]
        if qtys and total_nums[0] is not None \
                and total_nums[0] < max(qtys):
            self._emit(self.pending[0], total_nums)
            return True
        self._unshift_colon_block(self.pending[0])
        return False

    @staticmethod
    def _unit_only(probe):
        """True when the cell holds a bare unit ('Lbs.' / 'Loads.' / '£')
        with no number — the row-slip signature (units never print without
        their figures). Known units only: a looser match would queue false
        pendings and mis-shift a healthy block."""
        if probe is None:
            return False
        t = cell_text(probe).strip()
        return t == '£' or UNIT_WORD_RE.fullmatch(t) is not None

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
        """Single-year two-up row: label + [quantity, value].

        Row-slip cascade: once _classify has queued a unit-only country
        label (self.pending), each following row's numbers belong to the
        label ONE ROW UP — emit the queued label with this row's numbers
        and queue this row's label in its place. The orphan label-less
        numbers row at the block's end drains the queue, after which rows
        pair normally again; draining at the printed Total instead means a
        provisional colon-path shift was wrong and gets undone."""
        has_vals = any(re.search(r'\d', cell_text(v) or '') for v in values)
        country = self._classify(label_raw, values[0] if values else None,
                                 has_vals)
        if country is None:
            if self.pending and has_vals \
                    and not cell_text(label_raw).strip():
                nums = [self._num(v, set_unit=(i == 0))
                        for i, v in enumerate(values)]
                nums += [None] * (4 - len(nums))
                self._emit(self.pending.pop(0), nums)
                self.slip_colon = False   # the orphan row proves the slip
            return
        nums = [self._num(v, set_unit=(i == 0))
                for i, v in enumerate(values)]
        nums += [None] * (4 - len(nums))
        if self.pending:
            if country == 'TOTAL':
                # No orphan numbers row ever came. For a colon-path heading
                # that usually settles the ambiguity the other way — the
                # block was never slipped, so re-pair it. For the colon-less
                # signature the slipped label's own numbers were never
                # printed on a reachable row; drop it — the block-sum check
                # will flag.
                if self.slip_colon and self._resolve_colon_slip(nums):
                    self.pending.clear()
                    return
                self._drain_colon_slip()
                self.pending.clear()
            else:
                slipped, self.pending[:] = self.pending[0], \
                    self.pending[1:] + [country]
                self._emit(slipped, nums)
                if self.slip_colon:
                    self.slip_rows.append(self.out[-1])
                return
        country = self._apply_cctx(country, nums[1])
        self._emit(country, nums)

    def _emit(self, country, nums):
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


def looks_like_twoup(exp_rows, mid):
    """Wide-table gate: country labels may live in EITHER half's label slot
    (pages whose left half is blank colspan filler hide the whole block
    from the cell-0-only check above)."""
    if len(exp_rows) < 5:
        return False
    labels = []
    for e in exp_rows:
        if e:
            labels.append(cell_text(e[0]))
        if len(e) > mid:
            labels.append(cell_text(e[mid]))
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


# ---- which volumes carry country tables, and what year they are FOR -------
# `tn_*` used to be skipped wholesale as "monthly volumes". That is true of
# exactly two of the six. Their own title pages say so:
#     tn_1872  "For each Month during the Year 1872"          -> monthly
#     tn_1900  "For each Month during the Year 1900"          -> monthly
#     tn_1871  "ANNUAL STATEMENT ... IN THE YEAR 1870"        -> annual, 1870
#     tn_1895  "ANNUAL STATEMENT ... FOR THE YEAR 1894"       -> annual, 1894
#     tn_1899  "ANNUAL STATEMENT ... 1898, COMPARED WITH THE FOUR PRECEDING"
#     tn_1901  "ANNUAL STATEMENT ... 1900 COMPARED WITH THE FOUR PRECEDING
#               YEARS. VOLUME I. (Abstract and Detailed Tables ...)"
# The four annuals were already trusted as Tier-1 sources (parse_abstract
# reads them); only the country side excluded them, which left 1870 and 1900
# with no origin data at all — 1,121 of the 1,789 real gap cells.
# See reports/tn_volumes_findings.md.
MONTHLY = {'tn_1872', 'tn_1900'}


def wanted_volume(name):
    return (name.startswith('as_')
            or (name.startswith('tn_') and name not in MONTHLY))


def volume_year(volume):
    """Data year of a volume. `as_1899` publishes 1899; the Trade-and-
    Navigation annuals are named for their PUBLICATION year and report the
    year before (`tn_1899` carries 1898 — consensus already dates it that
    way). Multi-year comparative tables override this from their own printed
    year sub-header via year_header(); this is the single-year fallback."""
    y = int(volume[-4:])
    return y - 1 if volume.startswith('tn_') else y


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
        exp_rows = [expand_slots(r) for r in rows if '<th' not in r]
        exp_rows = [e for e in exp_rows if e]
        w_counts = Counter(len(e) for e in exp_rows
                           if any(cell_text(c) for c in e))
        width = w_counts.most_common(1)[0][0] if w_counts else 0
        wide = width >= 7
        if wide:
            mid, picks = twoup_geometry(exp_rows, width)
        if kind:
            flow, duty = kind
            if flow == 'import':
                cur = (flow, duty)
            elif cur in (('export_uk', ''), ('reexport', '')):
                pass                       # which export: keep sticky state
            else:
                cur = ('export_uk', '')
        elif not (cur and (looks_like_country_table(body_rows)
                           or (wide and looks_like_twoup(exp_rows, mid)))):
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
        elif wide:
            # geometry-mapped two-up: whole left column, then right column
            for (lo, hi), (qi, vi) in zip(((0, mid), (mid, width)), picks):
                for cells, e in zip(body_rows, exp_rows):
                    row = cells if len(e) != width \
                        and len(cells) == width else e
                    part = row[lo:hi]
                    if not part or not cell_text(part[0]).strip():
                        # A label-less numbers row is meaningful in exactly
                        # one place: it drains an open row-slip cascade (it
                        # carries the last queued label's figures — as_1872
                        # CHEESE, 'Other Countries' 4,039). Feed it only
                        # then; otherwise there is nothing to classify.
                        if part and st.pending:
                            vals = [part[i] if i is not None and i < len(part)
                                    else '' for i in (qi, vi)]
                            st.feed(part[0] if part else '', vals)
                        continue
                    vals = [part[i] if i is not None and i < len(part)
                            else '' for i in (qi, vi)]
                    st.feed(part[0], vals)
        else:
            # two-up: run the whole left column, then the right column.
            # A row is read via its colspan-EXPANDED slots when those hit
            # the table's modal width (colspan'd headers otherwise collapse
            # into the left slice and the right column's header vanishes —
            # as_1877 Wool under "Mahogany"); rows already at width, or off
            # width either way, keep the raw cell list.
            for lo, hi in ((0, 3), (3, 6)):
                for cells, e in zip(body_rows, exp_rows):
                    row = e if len(e) == width else cells
                    part = row[lo:hi]
                    if part:
                        st.feed(part[0], part[1:3])
    return n_tables


COLS = ('volume', 'flow', 'duty', 'article_group', 'article', 'country_raw',
        'unit', 'year', 'quantity', 'value', 'consumption', 'duty_received',
        'row_seq')


# The `as_*` annuals publish country tables for 1872-1899. The tn_ annuals
# are admitted ONLY for years outside that span, i.e. 1870 and 1900.
#
# Admitting their overlapping years as well was tried (2026-08-03) and is
# DESTRUCTIVE, not merely noisy. tn_1899 and tn_1901 print five years per row,
# so the same (commodity, country, year) arrives twice with different
# provenance, and the pipeline neither dedupes nor arbitrates it: `Cotton — Raw`
# 1895 double-counted to 1.79x its printed total and 1887 lost all 23 of its
# cells outright. Across the corpus that run was 438 cells better, 233 worse,
# 180 previously-exact cells broken, and GBP-weighted agreement fell 51.9% ->
# 46.5%. Restricted to the non-overlapping years the same volumes are purely
# additive — no existing cell can move. See reports/tn_volumes_findings.md.
# The overlapping years ARE parsed, into separate tables (country_obs_tn /
# country_obs_tn_inf) by parse_tn_overlap.py, for consumers that arbitrate
# witnesses themselves (the export series scripts).
AS_SPAN = (1872, 1899)


def keep_row(volume, year):
    if not volume.startswith('tn_'):
        return True
    return not (AS_SPAN[0] <= (year or 0) <= AS_SPAN[1])


def bulk_insert(con, table, rows):
    """Append parsed rows in one shot. executemany binds row by row (~2s per
    thousand here — over ten minutes for a corpus pass), so hand DuckDB an
    Arrow-backed frame and let it scan that instead."""
    import pandas as pd
    yi, vi = COLS.index('year'), COLS.index('volume')
    rows = [r for r in rows if keep_row(r[vi], r[yi])]
    if not rows:
        return
    df = pd.DataFrame(rows, columns=COLS)      # noqa: F841 - read by DuckDB
    con.execute(f'INSERT INTO {table} SELECT * FROM df')


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'))
    con.execute('DROP TABLE IF EXISTS country_obs')
    con.execute('''CREATE TABLE country_obs (
        volume VARCHAR, flow VARCHAR, duty VARCHAR,
        article_group VARCHAR, article VARCHAR, country_raw VARCHAR,
        unit VARCHAR, year INTEGER, quantity DOUBLE, value DOUBLE,
        consumption DOUBLE, duty_received DOUBLE, row_seq INTEGER)''')
    raws = sys.argv[1:] or sorted(
        str(p) for p in (BASE / 'raw').iterdir() if wanted_volume(p.name))
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
        year = volume_year(volume)
        seed = []
        parse_volume_countries(mds[0], volume, year, seed)
        freq = Counter(o[5].casefold() for o in seed
                       if o[5] and o[5] != 'TOTAL' and ' : ' not in o[5])
        names = frozenset(n for n, c in freq.items() if c >= 4)
        vols.append((mds[0], volume, year, names))
        # The vocabulary is CORPUS-WIDE and drives pass 2's header
        # classification for every volume, so seeding it from a newly added
        # volume silently re-parses all the others. Admitting the tn_ annuals
        # here moved 93 payload cells the wrong way and broke 69 that had been
        # exact — `Cotton — Raw` lost eight years outright — while the tn rows
        # themselves were confined to 1870 and 1900 and could not have touched
        # them. Seed from the `as_*` volumes only: the tn_ volumes are still
        # parsed in pass 2, against the same vocabulary the corpus already had.
        if volume.startswith('as_'):
            all_seeds.extend(seed)
    group_vocab, sub_vocab = build_vocab(all_seeds)
    print(f'vocabulary: {len(group_vocab)} group names, '
          f'{len(sub_vocab)} sub-article names\n')
    for md, volume, year, names in vols:
        out = []
        nt = parse_volume_countries(md, volume, year, out, names,
                                    group_vocab, sub_vocab)
        if out:
            bulk_insert(con, 'country_obs', out)
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
