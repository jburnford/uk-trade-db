#!/usr/bin/env python3
"""Fused sections: one (group, article) block holding two or more complete
TOTAL hierarchies.

When a heading is lost WITHOUT leaving an article marker, the parser does
not open a new block: the whole next section is appended to the previous
block, member rows, printed TOTALs and all. as_1888's (GLASS, 'GREASE,
TALLOW, AND ANIMAL FAT') block is 69 rows: grease's foreign half, TOTAL,
British half, TOTAL, TOTAL -- and then, still under the same key, all of
HABERDASHERY AND MILLINERY (value-only, no quantity) with its own three
TOTALs. HABERDASHERY reads zero in 1886-91 and 1894 for that reason, and
GREASE reads GBP8M instead of GBP2M. as_1887 fuses three sections into
GLASS 'Other Manufactures, Unenumerated'.

promote_headings() cannot see this (there is no heading text to promote)
and build_capture_reassign.py cannot either (it moves whole article blocks
by name; here the rows to move share the block's name). The repair is a
ROW-RANGE relabel:

  1. segment every block, in row_seq order, into TOTAL hierarchies. A
     hierarchy closes at a TOTAL row that is a GRAND total (immediately after
     another TOTAL, and equal to the sum of the two half-TOTALs before it,
     within tolerance), or at the last TOTAL before a member country that
     already appeared in the current segment (a section never lists a
     destination twice; the next section starts over from Russia/Sweden).
     A candidate segment must hold >= MIN_SEG_ROWS rows and a TOTAL row, or
     it is merged back -- one OCR-duplicated line is not a section.
  2. name segments 2..k from the reference volume (build_capture_reassign's
     nearest single-year annual): the reference headings that lie strictly
     between the block's own position and the position of the target's NEXT
     block. The Statement is alphabetical and the print order is the
     reference's print order, so if the reference shows exactly k-1 headings
     in that gap they name the segments in order. Where the count differs
     the block is reported and left alone; a segment whose hierarchy carries
     quantities is matched to a reference heading that carries a unit and a
     value-only segment to a value-only heading, which resolves most 2-vs-1
     ambiguities.

Output: reference/fused_section_splits.csv -- flow, volume, year, group,
article (RAW keys, before the phantom relabel), seq_from, seq_to, to_group,
to_article, rows, value, method. Consumers apply it with the other overlays,
BEFORE the phantom relabel and promote_headings (a row inside a named range
takes to_group/to_article; everything else is untouched).

Usage: python3 scripts/build_fused_splits.py [--dry-run] [--verbose]
"""
import argparse, collections, csv, re, sys
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phantom_articles import fix_articles, known_groups, promote_headings, _key
import build_capture_reassign as cap

TOTAL_RE = re.compile(r'\bTOTAL\b', re.I)
FLOWS = ['export_uk', 'reexport']
MIN_SEG_ROWS = 4       # members + totals in a segment before it counts
GRAND_TOL = 0.005      # grand = half + half within 0.5 %


def is_total(c):
    return bool(c) and bool(TOTAL_RE.search(c))


def ckey(c):
    return _key(c)


def segment(rows):
    """rows: list of (row_seq, country_raw, unit, quantity, value) sorted by
    row_seq. Returns a list of segments (lists of rows)."""
    segs, cur, seen = [], [], set()
    totals = []            # TOTAL rows in cur, in order
    last_total_idx = None  # index in cur of the last TOTAL row
    i = 0
    while i < len(rows):
        r = rows[i]
        c = r[1]
        if is_total(c):
            cur.append(r)
            totals.append(r)
            last_total_idx = len(cur) - 1
            # grand total: previous row also TOTAL and this = sum of the two
            # half totals before it
            if (len(cur) >= 3 and is_total(cur[-2][1]) and len(totals) >= 3
                    and r[4] and totals[-2][4] is not None
                    and totals[-3][4] is not None):
                s = totals[-2][4] + totals[-3][4]
                if s and abs(r[4] - s) <= GRAND_TOL * s:
                    segs.append(cur)
                    cur, seen, totals, last_total_idx = [], set(), [], None
            i += 1
            continue
        k = ckey(c)
        if k in seen and last_total_idx is not None:
            # a repeated destination after a TOTAL: the rows after the last
            # TOTAL belong to a new hierarchy
            head, tail = cur[:last_total_idx + 1], cur[last_total_idx + 1:]
            segs.append(head)
            cur = tail
            seen = {ckey(x[1]) for x in cur if not is_total(x[1])}
            totals, last_total_idx = [], None
        elif k in seen and len(cur) >= MIN_SEG_ROWS and shape_flip(cur, r):
            # a repeated destination with NO TOTAL yet, where the rows stop
            # (or start) carrying quantities: a section whose TOTALs the
            # parse lost, followed by the next section (as_1894 grease has
            # members but no TOTAL; haberdashery starts over from Sweden,
            # value-only)
            segs.append(cur)
            cur, seen, totals, last_total_idx = [], set(), [], None
        cur.append(r)
        seen.add(k)
        i += 1
    if cur:
        segs.append(cur)
    # merge back segments that are not hierarchies
    out = []
    for s in segs:
        if out and (len(s) < MIN_SEG_ROWS or not any(is_total(x[1]) for x in s)):
            out[-1].extend(s)
        else:
            out.append(s)
    # a leading non-hierarchy fragment merges FORWARD -- unless it is a
    # TOTAL-less section of its own (>= MIN_SEG_ROWS members whose quantity
    # shape differs from what follows)
    if (len(out) >= 2 and not any(is_total(x[1]) for x in out[0])
            and not (len(out[0]) >= MIN_SEG_ROWS and shape_flip(out[0], out[1][0]))):
        out[1] = out[0] + out[1]
        out = out[1:]
    return out


def shape_flip(cur, r):
    """the incoming member row carries a quantity where the current segment's
    members do not, or vice versa (a section keeps one unit throughout)"""
    mem = [x for x in cur if not is_total(x[1])]
    if len(mem) < 3:
        return False
    q = sum(1 for x in mem if x[3] is not None) / len(mem)
    return (q >= 0.8 and r[3] is None) or (q <= 0.2 and r[3] is not None)


def is_closed(seg):
    """ends on a grand total (TOTAL, TOTAL) -- a complete hierarchy"""
    return (len(seg) >= 2 and is_total(seg[-1][1]) and is_total(seg[-2][1]))


CANADA = ('British North America', 'Canada', 'Newfoundland')
PRIMARY_OVERRIDE = {1897: 'as_1899', 1898: 'as_1899'}


def seg_total(seg):
    """the section's size for a value comparison: its printed grand total
    when the hierarchy closes (member rows can be lost in the parse while
    the TOTAL survives -- as_1887's grease has no foreign members at all),
    else the sum of its member rows"""
    if is_closed(seg) and seg[-1][4]:
        return seg[-1][4]
    return sum((r[4] or 0) for r in seg if not is_total(r[1]))


def has_qty(seg):
    return sum(1 for r in seg if r[3] is not None and not is_total(r[1])) >= 2


REASSIGN = {}          # flow -> {(volume, from_group, article): to_group}
FAMILY = {}            # flow -> {canonical group spelling: family}


def load_family(flow):
    """group_name_folds (raw -> canonical) then export_group_families
    (canonical -> family): the level at which the explorer keys a commodity"""
    folds, fam = {}, {}
    if Path('reference/group_name_folds.csv').exists():
        for r in csv.DictReader(open('reference/group_name_folds.csv')):
            if r['flow'] == flow:
                folds[r['raw_group']] = r['canonical']
    if Path('reference/export_group_families.csv').exists():
        for r in csv.DictReader(open('reference/export_group_families.csv')):
            if r['flow'] == flow:
                fam[r['canonical']] = r['family']
    def f(g):
        c = folds.get(g, g)
        return fam.get(c, c)
    return f


def same_heading(a, b):
    """two reference spellings of one heading: same family, or the shorter
    name's content words are >= 60% contained in the longer's"""
    if a == b:
        return True
    ta, tb = cap.norm_tokens(a), cap.norm_tokens(b)
    if not ta or not tb:
        return False
    return len(ta & tb) / min(len(ta), len(tb)) >= 0.6


def load_reassign(flow):
    out = {}
    for path in ('reference/group_reassign.csv',
                 'reference/capture_reassign.csv'):
        if not Path(path).exists():
            continue
        for r in csv.DictReader(open(path)):
            if r['flow'] == flow:
                out[(r['volume'], r['from_group'], r['article'])] = r['to_group']
    return out


def load_volume(con, vol, flow):
    """rows after the label passes the consumers apply BEFORE this overlay
    is looked up: phantom relabel, heading promotion, then the two reassign
    tables (so a block WOOD AND TIMBER/'Ore' that capture_reassign has
    already re-homed to ZINC is positioned as ZINC). raw = row_seq ->
    (group, article) as parsed, which is what the overlay is keyed on."""
    rows = con.execute("""
        select volume, flow, year, coalesce(article_group,''), article, unit,
               row_seq, country_raw, value, quantity
        from country_obs where volume = ? and flow = ?
        order by year, row_seq""", [vol, flow]).fetchall()
    raw = {r[6]: (r[3], r[4]) for r in rows}
    fixed = fix_articles(rows, vol=0, flow=1, year=2, group=3, art=4, unit=5, seq=6)
    fixed = promote_headings(fixed, cap.KNOWN[flow], vol=0, flow=1, year=2,
                             group=3, art=4)
    ra = REASSIGN.get(flow, {})
    if ra:
        out = []
        for r in fixed:
            tgt = ra.get((vol, r[3], r[4] or ''))
            if tgt:
                rr = list(r)
                rr[3] = tgt
                r = tuple(rr)
            out.append(r)
        fixed = out
    return fixed, raw


def year_sequence(fixed, year):
    """ordered distinct (group, article) blocks of one year with their rows"""
    blocks = collections.OrderedDict()
    for r in fixed:
        if r[2] != year:
            continue
        k = (r[3], r[4] or '')
        blocks.setdefault(k, []).append((r[6], r[7], r[5], r[9], r[8]))
    return blocks


def ref_positions(ref_pairs):
    pos, gfirst, glast = {}, {}, {}
    for i, (g, a) in enumerate(ref_pairs):
        pos.setdefault((cap.gnorm(g), _key(a)), i)
        gfirst.setdefault(cap.gnorm(g), i)
        glast[cap.gnorm(g)] = i
    return pos, gfirst, glast


COUNTRIES = set()      # normalised country_raw seen in >= 5 volumes
MIN_COUNTRY_SHARE = 0.6
VALUE_BAND = 4.0       # segment total within 4x of the reference section
VALUE_FLOOR = 10000    # ...unless both are below this


def load_countries(con):
    for c, in con.execute("""
        select country_raw from country_obs
        where flow in ('export_uk','reexport') and country_raw is not null
        group by 1 having count(distinct volume) >= 5""").fetchall():
        if not is_total(c):
            COUNTRIES.add(_key(c))


def country_share(seg):
    mem = [r for r in seg if not is_total(r[1])]
    if not mem:
        return 0.0
    return sum(1 for r in mem if _key(r[1]) in COUNTRIES) / len(mem)


FURNITURE = re.compile(r'parcel post|^value of', re.I)


def build_ref(con, rv, flow):
    # the RAW reference sequence: build_capture_reassign's clean_reference()
    # re-homes generic article names ('Other Manufactures, Unenumerated') to
    # their dominant host group, which here deletes the very candidate a gap
    # needs (as_1876 GLASS lost its Other Manufactures and the 1874 glass
    # segment was named GREASE)
    ref = cap.sequence(con, rv, flow)
    ref_pairs = [(g, art) for (g, art), n, v in ref]
    rfixed, _ = load_volume(con, rv, flow)
    ryr = max(r[2] for r in rfixed) if rfixed else None
    rq, rval = {}, {}
    for k, rws in year_sequence(rfixed, ryr).items():
        rws = sorted(rws)
        kk = (cap.gnorm(k[0]), _key(k[1]))
        rq[kk] = has_qty(rws)
        # the reference block's own first hierarchy only (it may be fused too)
        rval[kk] = seg_total(segment(rws)[0])
    return ref_pairs, ref_positions(ref_pairs), rq, rval


def locate(ref_pairs, rpos, key, first=True, after=None):
    """reference index of a (group, article) key: exact, else the best
    name-similar article of the same group (sim >= 0.6, positions after
    `after` preferred), else the group's first (or last) position; None if
    the group is absent"""
    pos, gfirst, glast = rpos
    gk = cap.gnorm(key[0])
    q = pos.get((gk, _key(key[1])))
    if q is not None:
        return q
    if gk not in gfirst:
        return None
    if key[1]:
        gt = frozenset(cap.norm_tokens(key[0]))
        best = None
        for i in range(gfirst[gk], glast[gk] + 1):
            if cap.gnorm(ref_pairs[i][0]) != gk or not ref_pairs[i][1]:
                continue
            sc = cap.sim(key[1], ref_pairs[i][1], gt)
            if sc >= 0.6:
                pref = (after is None or i > after)
                if best is None or (pref, sc) > best[:2]:
                    best = (pref, sc, i)
        if best:
            return best[2]
    return (gfirst if first else glast).get(gk)


def resolve(ref, g, art, keys, bi, extra):
    """Name the extra segments of block keys[bi] from one reference.
    Returns (names, method) or (None, why)."""
    ref_pairs, rpos, rq, rval = ref
    p0 = locate(ref_pairs, rpos, (g, art), first=False)
    if p0 is None:
        return None, 'block group absent from reference'
    weak = ''
    if art and p0 == rpos[2].get(cap.gnorm(g)) and \
            not (rpos[0].get((cap.gnorm(g), _key(art))) == p0 or
                 (ref_pairs[p0][1] and cap.sim(art, ref_pairs[p0][1],
                                              frozenset(cap.norm_tokens(g))) >= 0.6)):
        # the block's own article is not in this reference (only the
        # group's last position came back): its place inside the group is a
        # guess, so this reference's answer is WEAK -- it needs a second
        # reference to agree (as_1876 has no GLASS 'Common Bottles' and
        # alone would name the 1874 glass tail GREASE)
        weak = '~'
    p1 = None
    for nk in keys[bi + 1:]:
        if cap.gnorm(nk[0]).startswith('ALLOTHERARTICLES'):
            break
        q = locate(ref_pairs, rpos, nk, first=True, after=p0)
        if q is not None and q > p0:
            p1 = q
            break
        if q is not None and cap.gnorm(nk[0]) == cap.gnorm(g):
            # a same-group article the reference does not carry: the fused
            # segments still lie inside the group's span
            p1 = rpos[2][cap.gnorm(g)] + 1
            break
    if p1 is None:
        p1 = len(ref_pairs)
    # candidate headings in the gap: a foreign group counts once (its
    # bare heading), an article of the block's own group counts by name
    cands = []
    for i in range(p0 + 1, p1):
        rg, ra = ref_pairs[i]
        if cap.gnorm(rg) == cap.gnorm(g):
            cands.append((rg, ra, rq.get((cap.gnorm(rg), _key(ra)))))
        elif not cands or cap.gnorm(cands[-1][0]) != cap.gnorm(rg):
            cands.append((rg, None, rq.get((cap.gnorm(rg), _key(ra)))))
    shapes = [has_qty(s) for s in extra]
    # heading-row rule: a segment whose first row is the NAME of a
    # reference article in the span (the article line read as a country)
    fixed_names = {}
    span = list(range(p0 + 1, min(p1 + 1, len(ref_pairs))))
    for j, s in enumerate(extra):
        first = s[0][1]
        for i in span:
            rg, ra = ref_pairs[i]
            if ra and _key(ra) and _key(ra) == _key(first):
                fixed_names[j] = (rg, ra, rq.get((cap.gnorm(rg), _key(ra))))
                break
    def plausible(names):
        for s, (tg, ta, _) in zip(extra, names):
            sv = seg_total(s)
            rv = rval.get((cap.gnorm(tg), _key(ta)))
            if rv is None:
                # a foreign group named by its bare heading: its first block
                rv = next((rval[k] for k in rval if k[0] == cap.gnorm(tg)), None)
            if rv is None:
                continue
            if max(sv, rv) < VALUE_FLOOR:
                continue
            if sv <= 0 or rv <= 0 or max(sv / rv, rv / sv) > VALUE_BAND:
                return False
        return True

    if len(fixed_names) == len(extra):
        names = [fixed_names[j] for j in range(len(extra))]
        return (names, 'heading-row' + weak) if plausible(names) else (None, 'heading-row implausible value')

    def pick(cands, method):
        free = [j for j in range(len(extra)) if j not in fixed_names]
        # remove candidates already taken by heading rows
        taken = {(cap.gnorm(c[0]), _key(c[1])) for c in fixed_names.values()}
        cands = [c for c in cands if (cap.gnorm(c[0]), _key(c[1])) not in taken]
        if len(cands) == len(free):
            names = list(cands)
        elif len(cands) > len(free) and len(cands) <= len(free) + 6:
            import itertools
            opts = [combo for combo in itertools.combinations(range(len(cands)), len(free))
                    if all(cands[c][2] == shapes[free[k]] for k, c in enumerate(combo))]
            if len(opts) != 1:
                return None
            names = [cands[c] for c in opts[0]]
            method += '+shape'
        else:
            return None
        out = []
        it = iter(names)
        for j in range(len(extra)):
            out.append(fixed_names[j] if j in fixed_names else next(it))
        if not plausible(out):
            return None
        return out, method

    r = pick(cands, 'gap' + weak)
    if r:
        return r
    # continuation: the last extra segment does not close (its British half
    # and TOTALs sit in the NEXT block, which the parser opened late), so
    # the next block's own heading names it
    if extra and not is_closed(extra[-1]) and p1 < len(ref_pairs):
        rg, ra = ref_pairs[p1]
        cont = (rg, ra if cap.gnorm(rg) == cap.gnorm(g) else
                (ra if keys[bi + 1:] and not (keys[bi + 1][1] or '') else None),
                rq.get((cap.gnorm(rg), _key(ra))))
        # the next block's raw key names the segment when it is a bare
        # group heading; keep the reference article otherwise
        cont = (rg, ra, rq.get((cap.gnorm(rg), _key(ra))))
        r = pick(cands + [cont], 'continuation' + weak)
        if r:
            return r
    return None, (f'gap has {len(cands)} headings for {len(extra)} segments: '
                  + ' | '.join(f'{c[0]}/{c[1]}' for c in cands))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='db/uk_trade.duckdb')
    ap.add_argument('--out', default='reference/fused_section_splits.csv')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--verbose', '-v', action='store_true')
    a = ap.parse_args()
    con = duckdb.connect(a.db, read_only=True)

    recs, unresolved = [], []
    load_countries(con)
    for flow in FLOWS:
        cap.KNOWN[flow] = known_groups(con, flow)
        REASSIGN[flow] = load_reassign(flow)
        FAMILY[flow] = load_family(flow)
        refs = {}
        for vol in cap.TARGETS:
            y = 1900 if vol == 'tn_1901' else 1870 if vol == 'tn_1871' else int(vol[-4:])
            order = sorted((r for r in cap.REFS if r != vol),
                           key=lambda r: (abs(int(r[-4:]) - y), -int(r[-4:])))
            fixed, raw = load_volume(con, vol, flow)
            if not fixed:
                continue
            own_year = max(r[2] for r in fixed)
            for year in sorted({r[2] for r in fixed}):
                primary = (vol == PRIMARY_OVERRIDE[year] if year in PRIMARY_OVERRIDE
                           else year == own_year)
                blocks = year_sequence(fixed, year)
                keys = list(blocks.keys())
                for bi, k in enumerate(keys):
                    rows = sorted(blocks[k])
                    segs = segment(rows)
                    if len(segs) < 2:
                        continue
                    g, art = k
                    if cap.gnorm(g).startswith('ALLOTHERARTICLES'):
                        continue
                    extra = segs[1:]
                    if any(country_share(s) < MIN_COUNTRY_SHARE for s in extra):
                        # not destination rows: a summary table, a year
                        # column, article names read as countries (the
                        # leakage class) -- not this repair
                        continue
                    tot_v = sum((r[4] or 0) for s in extra for r in s
                                if not is_total(r[1]))
                    can_v = sum((r[4] or 0) for s in extra for r in s
                                if r[1] in CANADA)
                    info = dict(flow=flow, volume=vol, year=year, group=g,
                                article=art, nseg=len(segs), rows=len(rows),
                                extra_value=round(tot_v), canada=round(can_v),
                                primary=int(primary), closed=int(is_closed(extra[-1])))
                    # every reference that can resolve the block must agree:
                    # a reference sharing the defect merely fails to resolve,
                    # but two references naming the segments differently is
                    # an ambiguity, not a repair
                    names, method, used = None, None, None
                    whys, answers = [], []
                    for rv in order:
                        if rv not in refs:
                            refs[rv] = build_ref(con, rv, flow)
                        nm, mt = resolve(refs[rv], g, art, keys, bi, extra)
                        if nm:
                            answers.append((rv, nm, mt))
                        else:
                            whys.append(f'{rv}: {mt}')
                    if answers:
                        # agreement at GROUP level, as the explorer keys it:
                        # family of the canonical spelling, else name
                        # containment (references spell one heading many ways)
                        def gsig(tg):
                            return FAMILY[flow](cap.KNOWN[flow].get(_key(tg), tg))
                        base = answers[0][1]
                        ok = [len(nm) == len(base) and all(
                                  gsig(x[0]) == gsig(y[0]) or same_heading(x[0], y[0])
                                  for x, y in zip(nm, base))
                              for _, nm, _ in answers]
                        # unanimous; or a majority that includes every
                        # reference nearer than the first dissenter (a
                        # distant decade's vocabulary is the usual dissenter)
                        first_bad = ok.index(False) if False in ok else len(ok)
                        agree = (all(ok) or
                                 (sum(ok) * 3 >= len(ok) * 2 and first_bad >= 2
                                  and not any(ok[first_bad:])))
                        if agree and '~' in answers[0][2] and sum(ok) < 2:
                            agree = False
                            whys = ['only a weak answer (block article absent from '
                                    f'the reference): {answers[0][0]}'] + whys
                        if agree:
                            used, names, method = answers[0]
                            if len(answers) > 1:
                                method += f'x{sum(ok)}' + ('' if all(ok) else f'-{len(ok)-sum(ok)}')
                        else:
                            whys = [f'refs disagree: ' + ' vs '.join(
                                f"{rv}=" + '+'.join(f'{tg[:20]}/{ta or ""}' for tg, ta, _ in nm)
                                for rv, nm, _ in answers)] + whys
                    if not names:
                        info['why'] = ' || '.join(whys)
                        unresolved.append(info)
                        continue
                    for s, (tg, ta, _) in zip(extra, names):
                        tg_c = cap.KNOWN[flow].get(_key(tg), tg)
                        # one unit for the whole segment: the phantom rows
                        # inside it used to inherit their parent's unit, so
                        # the consumers' unit-keyed blocks must not shatter
                        uc = collections.Counter(r[2] for r in s if not is_total(r[1]))
                        to_unit = uc.most_common(1)[0][0] if uc else None
                        if ta and FURNITURE.search(ta):
                            # a table title the reference carries as an
                            # article (the parcel-post table after ZINC):
                            # its own heading, not the group's; drop the
                            # 'to the under-mentioned Countries during ...'
                            tg_c, ta = re.split(r'\s+to the\b', ta, 1)[0].strip(), None
                        # one record per raw (group, article) sub-range: the
                        # overlay is keyed on the parse, and a promoted or
                        # reassigned block may span two raw keys
                        runs = []
                        for r in s:
                            rk = raw[r[0]]
                            if runs and runs[-1][0] == rk:
                                runs[-1][1].append(r)
                            else:
                                runs.append((rk, [r]))
                        for (rg, ra), rr in runs:
                            seg_v = sum((r[4] or 0) for r in rr if not is_total(r[1]))
                            recs.append(dict(flow=flow, volume=vol, year=year,
                                             group=rg, article=ra or '',
                                             seq_from=rr[0][0], seq_to=rr[-1][0],
                                             to_group=tg_c, to_article=ta or '',
                                             to_unit=to_unit or '',
                                             rows=len(rr), value=round(seg_v),
                                             canada=round(sum((r[4] or 0) for r in rr
                                                              if r[1] in CANADA)),
                                             primary=int(primary),
                                             method=method, reference=used,
                                             from_block=f'{g}/{art}'))
                            if a.verbose:
                                print(f'  {flow} {vol} {year} {g[:30]}/{(art or "")[:30]} '
                                      f'seq {rr[0][0]}-{rr[-1][0]} ({len(rr)} rows, '
                                      f'{seg_v:,.0f}) -> {tg_c[:40]}/{ta or ""} [{method} {used}]')

    by = collections.Counter((r['flow'], r['volume']) for r in recs)
    print(f'{len(recs)} segment relabels in {len(by)} volume-flows; '
          f'{len(unresolved)} fused blocks unresolved '
          f'(GBP{sum(u["extra_value"] for u in unresolved)/1e6:.1f}M extra, '
          f'Canada GBP{sum(u["canada"] for u in unresolved if u["primary"])/1e6:.2f}M primary)')
    print(f'resolved: GBP{sum(r["value"] for r in recs)/1e6:.1f}M, '
          f'Canada primary GBP{sum(r["canada"] for r in recs if r["primary"])/1e6:.2f}M')
    for k, n in sorted(by.items()):
        v = sum(r['value'] for r in recs if (r['flow'], r['volume']) == k)
        tos = collections.Counter(r['to_group'] for r in recs
                                  if (r['flow'], r['volume']) == k)
        print(f'  {k[0]:9} {k[1]} {n:3} segs GBP{v/1e6:6.2f}M -> '
              + ', '.join(f'{t[:24]}({c})' for t, c in tos.most_common(6)))
    if unresolved:
        print('unresolved, by Canada primary value:')
        for u in sorted(unresolved, key=lambda u: (-u['primary'], -u['canada']))[:40]:
            print(f"  {u['flow']:9} {u['volume']} {u['year']} "
                  f"{u['group'][:28]:28}/{(u['article'] or '')[:28]:28} "
                  f"nseg={u['nseg']} rows={u['rows']} GBP{u['extra_value']:>10,} "
                  f"can={u['canada']:>8,} {u['why'][:110]}")
        with open('reports/fused_sections_unresolved.csv', 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(unresolved[0].keys()))
            w.writeheader()
            w.writerows(unresolved)
    if not a.dry_run and recs:
        with open(a.out, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(recs[0].keys()))
            w.writeheader()
            w.writerows(recs)
        print(f'wrote {a.out}')


if __name__ == '__main__':
    main()
