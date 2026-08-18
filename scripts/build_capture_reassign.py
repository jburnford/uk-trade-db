#!/usr/bin/env python3
"""Positional repair of section captures in the late-era volumes.

When a group heading is lost, the previous group runs on and every article
of the next section (or the next several) is filed under it. In as_1899
LEAD holds, in print order, its own Ore/Pig/Rolled and then LEATHER's
Unwrought/Boots/Wrought, LINEN's Piece Goods/Sailcloth/Thread and
MACHINERY's Steam Engines/Sewing Machines/Textile/Other Descriptions --
three lost headings in a row. IMPLEMENTS AND TOOLS holds the whole IRON AND
STEEL section. For Canada that misfiles ~GBP1M a year of iron and ~GBP0.4M
of linen, leather and machinery in each of 1897-99, and the same class sits
in tn_1901 (1900) under INSTRUMENTS AND APPARATUS.

build_group_reassign.py decides membership by ARTICLE NAME (dominant host in
other volumes, or family vocabulary). That works for wool under WOOD but not
here, because the captured names are generic: 'Pig' is hosted by IRON in 21
volumes and by LEAD in 26; 'Other Descriptions' by MANURE, MACHINERY and
LINEN; 'Unwrought' by LEATHER and TIN. A name vote either mis-assigns them or
leaves the section half-moved.

What settles them is POSITION. The Statement is alphabetical and the print
order of articles inside a captured span is the print order of the healthy
volume, so the captor's article sequence aligns monotonically onto the
reference volume's (group, article) sequence starting at the captor's own
place in it. A standard monotone alignment (LCS weighted by article-name
similarity) then labels every article with the reference group at its
aligned position, and an unaligned article between two aligned neighbours of
the SAME group takes that group. 'Pig' between 'Ore' and 'Rolled, Sheet' is
LEAD; 'Other Descriptions' after 'Sewing Machines' and 'Textile' is
MACHINERY.

Reference: the nearest of six single-year annuals (as_1876/80/84/88/92/96)
that is not the target itself, per flow -- article vocabulary drifts by
decade. Every volume 1870-1900 is a target; the older ones yield mostly
name-variant folds plus a handful of real captures (HATS holding IRON in
as_1873, HOPS holding IRON in as_1886, JUTE holding LEAD in as_1884, Slates
holding SUGAR in as_1895). Articles are compared
after the phantom-region relabel (phantom_articles.py) and on the same
normalisation the explorer keys on, so the output keys match what the
consumer looks up.

Output: reference/capture_reassign.csv -- flow, volume, from_group, article,
to_group, method (aligned|interpolated), sim, rows, value. Same shape as
group_reassign.csv (which stays as the adjudicated WOOD->WOOL record); the
explorer loads both, this file second.

Usage: python3 scripts/build_capture_reassign.py [--dry-run]
"""
import argparse, collections, csv, re, sys, unicodedata
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phantom_articles import fix_articles, known_groups, promote_headings

# reference volumes: single-year annuals, one per four years; a target is
# aligned onto the nearest one that is not itself (article vocabulary drifts
# by decade, so as_1896 is a poor reference for as_1874)
REFS = ['as_1876', 'as_1880', 'as_1884', 'as_1888', 'as_1892', 'as_1896']
KNOWN = {}             # flow -> known group headings (filled in main)
TARGETS = (['tn_1871'] + [f'as_{y}' for y in range(1872, 1900)] + ['tn_1901'])


def ref_for(vol):
    y = 1900 if vol == 'tn_1901' else 1870 if vol == 'tn_1871' else int(vol[-4:])
    cands = [r for r in REFS if r != vol]
    return min(cands, key=lambda r: (abs(int(r[-4:]) - y), -int(r[-4:])))
FLOWS = ['export_uk', 'reexport']
MIN_SIM = 0.6          # article-name similarity to count as aligned
MIN_FOREIGN = 2        # a captor needs >=2 aligned articles in other groups
MIN_RUN = 2            # ...and a foreign group needs a RUN of >=2 aligned
                       # articles: one word coincidence is not a section
JUMP = 0.15            # alignment penalty per reference group crossed
JUMP_CAP = 1.0
WINDOW = 400           # reference positions searched beyond the captor's own
STOP = {'and', 'of', 'or', 'the', 'in', 'for', 'not', 'being', 'other',
        'all', 'kinds', 'kind', 'sorts', 'sort', 'viz', 'unenumerated',
        'thereof', 'parts', 'including', 'except', 'descriptions', 'ii',
        'iii', 'cont', 'continued',
        # packaging / customs-status words shared by wine, spirits, tobacco
        'total', 'imported', 'bond', 'mixed', 'casks', 'cask', 'bottles',
        'bottle', 'tested', 'sweetened'}


def norm_tokens(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode()
    s = re.sub(r'(?<=[a-z])-\s+(?=[a-z])', '', s.lower())    # 'tex- tile'
    toks = [t for t in re.findall(r'[a-z]+', s) if t not in STOP]
    return set(toks)


# words that name a STATE of a good rather than the good: alone they match
# every metal, hide, sugar and textile, so a one-word name made of one of
# these aligns only to an equal one-word name (after the reference group's
# own words are removed: 'Iron, Pig' vs Iron/'Pig' is equal)
GENERIC = {'manufactured', 'unmanufactured', 'manufactures', 'wrought',
           'unwrought', 'refined', 'unrefined', 'ore', 'pig', 'bar', 'bars',
           'sheets', 'sheet', 'plates', 'plate', 'rolled', 'cast', 'old',
           'scrap', 'crude', 'cakes', 'ingots', 'blocks', 'slabs', 'yarn',
           'goods', 'piece', 'articles', 'wares'}


def sim(a, b, group_tokens=frozenset()):
    """Token containment: shared content words over the SHORTER name, so
    'Agricultural' matches 'Steam Engines : Agricultural' (the reference
    carries the parent heading in the sub-article) and 'Steel Bar, of all
    kinds' matches 'Bar' -- the jump penalty and the run guard carry the
    risk that containment is loose. group_tokens (the reference group's own
    words) are discounted on both sides, so 'Iron, Pig' is Iron's 'Pig'."""
    ta, tb = norm_tokens(a) - group_tokens, norm_tokens(b) - group_tokens
    if not ta or not tb:
        # an empty article (the group's own bare line) or a name made only
        # of stop-words ('Other Sorts', 'Unenumerated') is no evidence of
        # position: two blank lines align in every group. Such rows are
        # labelled by interpolation between real neighbours only.
        return 0.0
    short = ta if len(ta) <= len(tb) else tb
    if len(short) == 1 and next(iter(short)) in GENERIC:
        return 1.0 if ta == tb else 0.0
    return len(ta & tb) / min(len(ta), len(tb))


def gnorm(g):
    return re.sub(r'[^A-Z0-9]', '', (g or '').upper())


def sequence(con, vol, flow):
    """Ordered distinct (group, article) of a volume-flow after the phantom
    relabel, with row counts and value; year = the volume's max year."""
    rows = con.execute("""
        select volume, flow, year, coalesce(article_group,''), article, unit,
               row_seq, country_raw, value
        from country_obs where volume = ? and flow = ?
    """, [vol, flow]).fetchall()
    if not rows:
        return []
    yr = max(r[2] for r in rows)
    rows = [r for r in rows if r[2] == yr]
    rows = fix_articles(rows, vol=0, flow=1, year=2, group=3, art=4,
                        unit=5, seq=6)
    # lost headings stored as articles become their own group first, so the
    # alignment sees the section under its own name (the explorer applies
    # the same promotion before it looks a reassignment up)
    rows = promote_headings(rows, KNOWN[flow], vol=0, flow=1, year=2,
                            group=3, art=4)
    rows.sort(key=lambda r: r[6])
    seq = []
    for r in rows:
        k = (r[3], r[4] or '')
        if seq and seq[-1][0] == k:
            seq[-1][1] += 1
            seq[-1][2] += r[8] or 0
        elif not seq or seq[-1][0] != k:
            # a (group, article) may recur non-adjacently (fused tables);
            # keep the first occurrence only
            if any(s[0] == k for s in seq):
                for s in seq:
                    if s[0] == k:
                        s[1] += 1
                        s[2] += r[8] or 0
                continue
            seq.append([k, 1, r[8] or 0])
    return seq


def align(cap_arts, ref, start):
    """Monotone alignment of cap_arts (list of article strings) onto
    ref[start:start+WINDOW] (list of (group, article)). Returns list of ref
    index or None per captor article.

    State: best[i][j] = best score for the first i captor articles with the
    LAST MATCH exactly at reference position j (j=0: no match yet). A match
    (i, j) is reached from any state (i-1, k), k<j, and pays JUMP per
    reference group crossed between k and j (capped), so a single word
    coincidence several groups ahead does not pay while a real captured
    section (many consecutive matches) does. Skipping a captor article keeps
    the last-match position, which is what makes the penalty honest --
    an earlier version let unmatched reference positions advance the state
    for free and repaired COPPER into IRON on one 'Ore'."""
    R = ref[start:start + WINDOW]
    n, m = len(cap_arts), len(R)
    gid, cur = [0] * (m + 1), 0          # gid[j] for 1-based j; gid[0] = 0
    for j in range(1, m + 1):
        if j > 1 and gnorm(R[j - 1][0]) != gnorm(R[j - 2][0]):
            cur += 1
        gid[j] = cur
    G = cur + 1
    gtok = [frozenset()] + [frozenset(norm_tokens(R[j - 1][0])) for j in range(1, m + 1)]
    NEG = float('-inf')
    best = [[NEG] * (m + 1) for _ in range(n + 1)]
    back = [[None] * (m + 1) for _ in range(n + 1)]
    best[0][0] = 0.0
    for i in range(1, n + 1):
        art = cap_arts[i - 1]
        sims = [0.0] + [sim(art, R[j - 1][1], gtok[j]) for j in range(1, m + 1)]
        # per-group running max of best[i-1][k] over k < j, built as j grows
        gmax = [NEG] * G
        garg = [0] * G
        for j in range(0, m + 1):
            # skip captor article i
            b, bk = best[i - 1][j], j
            if j >= 1 and sims[j] >= MIN_SIM:
                gj = gid[j]
                for g in range(gj, -1, -1):
                    if gmax[g] == NEG:
                        continue
                    # the first match pays relative to the captor's own group
                    # (gid 0): a sequence that opens with a jump is a
                    # sequence whose own articles found nothing at home
                    pen = min(JUMP * (gj - g), JUMP_CAP)
                    cand = gmax[g] + sims[j] - pen
                    if cand > b:
                        b, bk = cand, garg[g]
            best[i][j], back[i][j] = b, bk
            # now position j is available as a predecessor for j' > j
            if best[i - 1][j] > gmax[gid[j]]:
                gmax[gid[j]] = best[i - 1][j]
                garg[gid[j]] = j
    j = max(range(m + 1), key=lambda jj: best[n][jj])
    out = [None] * n
    for i in range(n, 0, -1):
        k = back[i][j]
        if k != j:                       # a match at (i, j)
            out[i - 1] = start + j - 1
        j = k
    return out


def group_start(g, gstart, ref_pairs):
    """Where the captor's own group begins in the reference: exact
    normalised name, else the reference group sharing the most name tokens
    (containment >= 0.6, ties to the longer overlap). tn_1901's 'INSTRUMENTS
    AND APPARATUS, SURGICAL, ANATOMICAL, AND SCIENTIFIC' is as_1896's
    'INSTRUMENTS AND APPARATUS'."""
    if gnorm(g) in gstart:
        return gstart[gnorm(g)]
    best, best_s = None, 0.0
    tg = norm_tokens(g)
    if not tg:
        return None
    for gg, i in gstart.items():
        name = next(x[0] for x in ref_pairs if gnorm(x[0]) == gg)
        tr = norm_tokens(name)
        if not tr:
            continue
        sc = len(tg & tr) / min(len(tg), len(tr))
        if sc >= 0.6 and (sc, len(tg & tr)) > (best_s, 0):
            best, best_s = i, sc
    if best is not None:
        return best
    # a heading the reference volume never printed (tn_1901's 'GOODS NOT
    # ENUMERATED ...' holding ZINC): the Statement is alphabetical, so start
    # at the first reference group that sorts after it
    key = gnorm(g)
    later = sorted((gg, i) for gg, i in gstart.items() if gg > key)
    return later[0][1] if later else None


def clean_reference(con, ref, flow):
    """The reference volume has captures of its own (as_1896 files SEEDS
    under 'Cotton', COCOA husks under 'Butter', SOAP under SLATES). Where an
    article's dominant host across the single-year volumes (as_1872-96, by
    volume count, majority and >=3 volumes) is a different group, the
    reference position takes that group."""
    host = collections.defaultdict(collections.Counter)
    for art, grp, nv in con.execute("""
        select lower(trim(article)), upper(trim(article_group)),
               count(distinct volume)
        from country_obs
        where flow = ? and volume between 'as_1872' and 'as_1896'
          and article is not null and trim(article) <> ''
          and article_group is not null
        group by 1, 2""", [flow]).fetchall():
        host[art][grp] += nv
    out, n_fixed = [], 0
    for (g, art), n, v in ref:
        h = host.get((art or '').strip().lower())
        if h and norm_tokens(art):
            (top, nv), = h.most_common(1)
            if nv >= 3 and nv > sum(h.values()) / 2 and gnorm(top) != gnorm(g):
                out.append([(top, art), n, v])
                n_fixed += 1
                continue
        out.append([(g, art), n, v])
    print(f'reference {flow}: {n_fixed} positions re-homed by dominant host', file=sys.stderr)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='db/uk_trade.duckdb')
    ap.add_argument('--out', default='reference/capture_reassign.csv')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    con = duckdb.connect(a.db, read_only=True)

    recs = []
    for flow in FLOWS:
        KNOWN[flow] = known_groups(con, flow)
        refs = {}
        for vol in TARGETS:
            rv = ref_for(vol)
            if rv not in refs:
                ref = clean_reference(con, sequence(con, rv, flow), flow)
                ref_pairs = [(g, art) for (g, art), n, v in ref]
                gstart = {}
                for i, (g, art) in enumerate(ref_pairs):
                    gstart.setdefault(gnorm(g), i)
                refs[rv] = (ref_pairs, gstart)
            ref_pairs, gstart = refs[rv]
            seq = sequence(con, vol, flow)
            bygroup = collections.OrderedDict()
            for (g, art), n, v in seq:
                bygroup.setdefault(g, []).append((art, n, v))
            for g, arts in bygroup.items():
                if gnorm(g).startswith('ALLOTHERARTICLES'):
                    # the residual heading at the foot of the table: what
                    # follows it is totals and page furniture, not a section
                    continue
                start = group_start(g, gstart, ref_pairs)
                if start is None:
                    continue
                names = [x[0] for x in arts]
                hit = align(names, ref_pairs, start)
                # label: aligned -> reference group; interpolate between
                # equal neighbours
                labels = [None] * len(names)
                for i, h in enumerate(hit):
                    if h is not None:
                        labels[i] = (ref_pairs[h][0], 'aligned',
                                     round(sim(names[i], ref_pairs[h][1],
                                               frozenset(norm_tokens(ref_pairs[h][0]))), 2))
                for i in range(len(names)):
                    if labels[i] is None:
                        prev = next((labels[k] for k in range(i - 1, -1, -1)
                                     if labels[k]), None)
                        nxt = next((labels[k] for k in range(i + 1, len(names))
                                    if labels[k]), None)
                        if prev and nxt and gnorm(prev[0]) == gnorm(nxt[0]):
                            labels[i] = (prev[0], 'interpolated', 0.0)
                        elif prev is None and nxt and gnorm(nxt[0]) == gnorm(g):
                            labels[i] = (g, 'interpolated', 0.0)
                # run guard: among ALIGNED labels in order, a foreign group
                # must occur in a run of >= MIN_RUN consecutive aligned
                # articles; singletons are dropped (and their interpolations).
                # Exception: the LAST aligned label, exact-named, after >= 3
                # foreign labels -- deep in captured territory the tail of the
                # sequence is a fused block ('Ore' holding all of ZINC, 195
                # rows) and one exact name is what a fused block leaves.
                al = [(i, gnorm(l[0]), l[2]) for i, l in enumerate(labels)
                      if l and l[1] == 'aligned']
                keep = set()
                r0 = 0
                while r0 < len(al):
                    r1 = r0
                    while r1 + 1 < len(al) and al[r1 + 1][1] == al[r0][1]:
                        r1 += 1
                    n_foreign_before = sum(1 for k in range(r0) if al[k][1] != gnorm(g))
                    tail_exact = (r1 == len(al) - 1 and al[r0][2] >= 1.0
                                  and n_foreign_before >= 3)
                    if (r1 - r0 + 1 >= MIN_RUN or al[r0][1] == gnorm(g)
                            or tail_exact):
                        keep.update(al[k][0] for k in range(r0, r1 + 1))
                    r0 = r1 + 1
                for i, l in enumerate(labels):
                    if l and l[1] == 'aligned' and i not in keep:
                        labels[i] = None
                # re-interpolate after the guard: between equal neighbours
                # take that group; between two DIFFERENT foreign neighbours
                # the article is certainly not the captor's, so take the
                # neighbour whose group name shares more words with it (ties
                # to the previous); after the last aligned label, if that
                # label is foreign, the captured section is still running --
                # a trailing unaligned article ('Steel Bar, of all kinds'
                # holding the whole steel section, 264 rows) inherits it.
                for i in range(len(names)):
                    if labels[i] and labels[i][1] == 'interpolated':
                        labels[i] = None
                for i in range(len(names)):
                    if labels[i] is None:
                        prev = next((labels[k] for k in range(i - 1, -1, -1)
                                     if labels[k]), None)
                        nxt = next((labels[k] for k in range(i + 1, len(names))
                                    if labels[k]), None)
                        if prev and nxt and gnorm(prev[0]) == gnorm(nxt[0]):
                            labels[i] = (prev[0], 'interpolated', 0.0)
                        elif (prev and nxt and gnorm(prev[0]) != gnorm(g)
                              and gnorm(nxt[0]) != gnorm(g)):
                            ta = norm_tokens(names[i])
                            sp = len(ta & norm_tokens(prev[0]))
                            sn = len(ta & norm_tokens(nxt[0]))
                            labels[i] = ((nxt if sn > sp else prev)[0],
                                         'interpolated', 0.0)
                        elif prev and nxt is None and gnorm(prev[0]) != gnorm(g):
                            labels[i] = (prev[0], 'trailing', 0.0)
                foreign = [i for i, l in enumerate(labels)
                           if l and gnorm(l[0]) != gnorm(g)]
                if len([i for i in foreign if labels[i][1] == 'aligned']) < MIN_FOREIGN:
                    continue
                for i in foreign:
                    art, n, v = arts[i]
                    recs.append(dict(flow=flow, volume=vol, from_group=g,
                                     article=art, to_group=labels[i][0],
                                     method=labels[i][1], sim=labels[i][2],
                                     rows=n, value=round(v), reference=rv))

    by = collections.Counter((r['flow'], r['volume'], r['from_group']) for r in recs)
    print(f'{len(recs)} article reassignments in {len(by)} captor groups')
    for k, n in sorted(by.items()):
        tos = collections.Counter(r['to_group'] for r in recs
                                  if (r['flow'], r['volume'], r['from_group']) == k)
        print(f'  {k[0]:9} {k[1]} {k[2][:40]:40} {n:3} -> '
              + ', '.join(f'{t[:28]}({c})' for t, c in tos.most_common()))
    if not a.dry_run:
        with open(a.out, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(recs[0].keys()))
            w.writeheader()
            w.writerows(recs)
        print(f'wrote {a.out}')


if __name__ == '__main__':
    main()
