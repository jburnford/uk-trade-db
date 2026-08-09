#!/usr/bin/env python3
"""Whole sections captured by the preceding group when a heading is lost.

`detect_lost_group_heading.py` catches the case where the parser stores the
missed heading as an ARTICLE (article_group=GLASS, article=GREASE, TALLOW...).
It cannot see the worse variant, where the heading is dropped entirely: the
previous group simply runs on and absorbs the whole next section, and every
article underneath keeps its own normal-case name.

That is what happened to wool in as_1898/as_1899. WOOD comes immediately before
WOOL in the alphabetical listing:

    volume    WOOL rows   WOOD rows
    as_1897       4,805         735
    as_1898         137       5,609      <- the wool section became "WOOD AND TIMBER"
    as_1899          67       6,560

THE TEST IS VOCABULARY, NOT ROW COUNTS. An earlier version of this script paired
groups that swelled with groups that shrank in the same volume and returned
5,938 candidates -- a cartesian product in which one big captor paired with every
small victim, and no pair carried evidence. Row arithmetic cannot tell which
collapse goes with which swell.

What settles it is that a captured section brings its own article names with it.
So for each (volume, group), take the distinct articles filed under it and ask
what share of them are attested under a DIFFERENT group in other volumes. If most
of a group's articles belong to somebody else, that somebody else is the victim,
and the capture is named directly rather than inferred.

Alphabetical adjacency is reported but NOT required: the Statement is
alphabetical so the captor is usually the victim's predecessor, but a volume can
order or skip sections in ways that break it.

KNOWN LIMIT -- TRUST THE CAPTOR, VERIFY THE VICTIM. The `share` column is
reliable: it says a group is holding articles that are attested under some other
group, and that finding held up on every case checked. The `victim` column is
NOT reliable. Article strings drift between volumes ('Iron, Bar' one year, 'Bar'
the next), so the attribution vote often lands on a spurious majority. In
as_1898 this script named IMPLEMENTS AND TOOLS -> INSTRUMENTS AND APPARATUS,
but the articles actually sitting there are iron and steel (Iron, Pig; Steel
Bar; Hoops and Hoop Iron). The capture was real; the named victim was wrong.
Always read the captor's article list before writing a repair.

A second class shows up in the same lists and is not a capture: region names
ingested as article names ('West Africa' with 2,180 rows under IMPLEMENTS AND
TOOLS in as_1898). Those inflate a group's row count without belonging to any
other group, and need the phantom-region treatment instead.

Usage:
    python3 scripts/detect_group_capture.py [--flow all] [--min-rows 100]
        [--min-share 0.35] [--out reports/group_capture.csv]
"""
import argparse, collections, csv, re
import duckdb

STOP = {'and', 'of', 'or', 'the', 'not', 'in', 'for', 'all'}


def toks(s):
    s = re.sub(r'[^a-z0-9]+', ' ', (s or '').lower())
    return {w for w in s.split() if w not in STOP and len(w) > 2}


def same_group(a, b):
    """True when two group strings are spellings of one group, not a capture.

    OCR splits a single heading many ways -- CARRIAGES / CARRIAGES, &C. and
    PAINTERS' COLOURS AND MATERIALS / PAINTERS' COLOURS AND MA- TERIALS both
    surface as high-share 'captures' of themselves. A capture is only
    interesting when the two names are genuinely different commodities.
    """
    ta, tb = toks(a), toks(b)
    if not ta or not tb:
        return False
    return len(ta & tb) / min(len(ta), len(tb)) >= 0.6


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='db/uk_trade.duckdb')
    ap.add_argument('--flow', default='all',
                    choices=['all', 'export_uk', 'reexport', 'import'])
    ap.add_argument('--min-rows', type=int, default=100,
                    help='ignore groups smaller than this in the volume')
    ap.add_argument('--min-share', type=float, default=0.35,
                    help='share of a group\'s articles that must belong elsewhere')
    ap.add_argument('--out', default='reports/group_capture.csv')
    a = ap.parse_args()

    con = duckdb.connect(a.db, read_only=True)
    cond = ["article_group is not null", "trim(article_group) <> ''",
            "article is not null", "trim(article) <> ''"]
    args = []
    if a.flow != 'all':
        cond.append('flow = ?')
        args.append(a.flow)
    rows = con.execute(f"""
        select flow, volume, upper(trim(article_group)) g, lower(trim(article)) art,
               count(*) n
        from country_obs where {' and '.join(cond)}
        group by 1, 2, 3, 4
    """, args).fetchall()

    # article -> group -> set of volumes it is attested in (per flow)
    home = collections.defaultdict(lambda: collections.defaultdict(set))
    cell = collections.defaultdict(lambda: collections.defaultdict(int))
    arts = collections.defaultdict(set)
    for flow, vol, g, art, n in rows:
        home[(flow, art)][g].add(vol)
        cell[(flow, vol, g)][art] += n
        arts[(flow, vol, g)].add(art)

    recs = []
    for (flow, vol, g), byart in cell.items():
        nrows = sum(byart.values())
        if nrows < a.min_rows:
            continue
        foreign = collections.Counter()
        n_art = 0
        for art in byart:
            n_art += 1
            others = {og: vs for og, vs in home[(flow, art)].items()
                      if og != g and (vs - {vol})}
            if not others:
                continue
            # attribute the article to whichever other group hosts it most widely
            best = max(others, key=lambda og: len(others[og]))
            foreign[best] += 1
        if not n_art or not foreign:
            continue
        victim, cnt = None, 0
        for cand, k in foreign.most_common():
            if not same_group(g, cand):      # skip spelling variants of itself
                victim, cnt = cand, k
                break
        if victim is None:
            continue
        share = cnt / n_art
        if share < a.min_share:
            continue
        recs.append(dict(
            flow=flow, volume=vol, captor=g, victim=victim,
            rows=nrows, articles=n_art, articles_belonging_to_victim=cnt,
            share=round(share, 3),
            alpha_adjacent=int(g[:3] < victim[:3])))

    recs.sort(key=lambda r: -r['rows'])
    print(f'candidate section captures: {len(recs)}')
    if recs:
        print(f'\n{"flow":>10} {"volume":>9} {"rows":>6} {"share":>6}  captor -> victim')
        for r in recs[:22]:
            adj = ' (alpha)' if r['alpha_adjacent'] else ''
            print(f'{r["flow"]:>10} {r["volume"]:>9} {r["rows"]:>6} '
                  f'{r["share"]*100:>5.0f}%  {r["captor"][:28]} -> {r["victim"][:26]}{adj}')
        with open(a.out, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(recs[0].keys()))
            w.writeheader()
            w.writerows(recs)
        print(f'\nwrote {a.out}')


if __name__ == '__main__':
    main()
