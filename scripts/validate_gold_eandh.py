#!/usr/bin/env python3
"""Validate the pipeline against the E&H British Imports Database.

This is an EXTERNAL check. Every other confidence instrument in this repo --
printed-subtotal closure, cross-engine label agreement, cross-volume anchor
votes, single-digit repair arithmetic -- tests the corpus against itself. The
E&H extract is an independent hand keying of the same HCPP pages, so where it
disagrees with us exactly one of the two readings is wrong, and the argument
about which can be settled by evidence neither transcription contains.

Complementary to validate_gold.py, which uses the Ghost Acres workbook: that
one is WIDE (603 commodities) and SHALLOW (6 quinquennial years); this one is
NARROW (tallow, rosin) and DEEP (annual, 1868-1900). Closure tests are per
year, so the Ghost Acres gold could only ever reach 5 of tallow's 28 country
years. This reaches all of them.

HOLD-OUT RULE: the gold is a test set, not a source of repairs. No pipeline
value may be changed because the gold says so -- otherwise the agreement rate
stops measuring anything. Where a disagreement is adjudicated against us, the
fix has to be justified by independent evidence (the page image, our own
printed subtotal, cross-engine agreement) and the adjudication report records
which. reference/gold_eandh.csv must never be cited as authority in
reference/group_repairs.csv or reference/manual_rows.csv.

CIRCULARITY: the E&H extract and the Ghost Acres workbook are both drawn from
the same underlying relational database, so 1876/1881/1886/1891/1896 have been
seen by validate_gold.py before. Every headline is reported twice -- all years,
and the never-benchmarked years only. The latter is the honest number.

The ladder:
  0  gold self-consistency   -- does the gold close against itself?
  1  national total          -- gold World vs our Tier-1 anchor, both columns
  2  country cell            -- after roll-up, cell by cell, both columns
  3  completeness            -- what does each side have that the other lacks
  4  adjudication            -- for each disagreement, what does third evidence say

Usage:
    python3 scripts/validate_gold_eandh.py [--commodity tallow|rosin|all]
"""
import argparse
import csv
import json
import collections
from pathlib import Path

import countrykey

BASE = Path(__file__).resolve().parent.parent
GOLD = BASE / 'reference' / 'gold_eandh.csv'
DEDUP = BASE / 'exports' / '_origin_dedup.csv'
SLIM = BASE / 'exports' / 'map_slim.json'
REPORTS = BASE / 'reports'

# the bands of record, from scripts/reconcile_baseline.py:63-64
EXACT01 = 0.001
WITHIN5 = 0.05

# gold COMMODITY_NAME -> pipeline commodity. The gold splits one series across
# two names and does not do it cleanly: in 1882 the World row is filed under
# 'Tallow' while every country row that year is under 'Tallow and Stearine',
# and 1880 and 1885 carry a World row under both. They are one printed line and
# are unioned here; the split is reported as a gold artifact, not a difference.
COMMODITY = {
    'tallow': ({'Tallow', 'Tallow and Stearine'}, 'Tallow And Stearine'),
    'rosin': ({'Rosin'}, 'Rosin'),
}

# years the Ghost Acres gold already benchmarked, so not naive for this test
BENCHMARKED = {1871, 1876, 1881, 1886, 1891, 1896}


def rel(a, b):
    return abs(a - b) / b if b else None


def bucket(p, g):
    d = rel(p, g)
    if d is None:
        return 'nogold'
    return 'exact01' if d <= EXACT01 else ('within5' if d <= WITHIN5 else 'off')


def digit_story(p, g):
    """How do two readings of the same printed figure differ?

    A disagreement between two independent transcriptions of one number is
    almost never random. Classifying it is what turns 'we differ' into a
    testable claim about WHICH side slipped, and it is cheap: the E&H
    disagreements are overwhelmingly one substituted digit or one lost leading
    digit, the same vocabulary scripts/digit_repair_candidates.py reasons about
    from arithmetic alone.
    """
    if p is None or g is None:
        return ''
    ps, gs = f'{int(round(p))}', f'{int(round(g))}'
    if ps == gs:
        return 'equal'
    if len(ps) == len(gs):
        diff = [i for i, (a, b) in enumerate(zip(ps, gs)) if a != b]
        if len(diff) == 1:
            i = diff[0]
            return f'one_digit[{i}] {gs[i]}->{ps[i]}'
        if sorted(ps) == sorted(gs):
            return 'transposition'
        return f'{len(diff)}_digits'
    if len(ps) == len(gs) + 1 and ps.endswith(gs):
        return f'lost_leading_digit {ps[0]}'
    if len(gs) == len(ps) + 1 and gs.endswith(ps):
        return f'lost_leading_digit {gs[0]}'
    return 'magnitude'


# ---------------------------------------------------------------- load sides
def load_gold(names):
    """(year -> {country_id: [qty, value]}, year -> world row, artifacts)."""
    cells = collections.defaultdict(dict)
    raw = collections.defaultdict(list)
    world = {}
    world_rejected = collections.defaultdict(list)
    dupes = []
    ck = countrykey.load()
    seen = collections.defaultdict(list)
    for r in csv.DictReader(open(GOLD)):
        if r['commodity'] not in names:
            continue
        # a handful of rows are consigned to London/Liverpool rather than the
        # United Kingdom as a whole; they are a different measure
        if r['to_location'] != 'United Kingdom':
            continue
        y = int(r['year'])
        q = float(r['quantity']) if r['quantity'] else None
        v = float(r['value']) if r['value'] else None
        if r['is_world'] == '1':
            # the national total is the unique World row carrying a value.
            # The value-zero World rows appear only in quinquennial years and
            # are leftovers from the wider five-yearly pull this annual series
            # was merged into; they are not totals and must never be summed.
            if v:
                world[y] = (q, v, r['country_raw'])
            else:
                world_rejected[y].append(q)
            continue
        cid, lvl = ck.key(r['country_raw'])
        raw[y].append((r['country_raw'], cid, lvl, q, v))
        if cid == countrykey.DROP:
            continue
        seen[(y, cid)].append((q, v))
        cur = cells[y].setdefault(cid, [0.0, 0.0])
        cur[0] += q or 0
        cur[1] += v or 0
    for (y, cid), hits in seen.items():
        if len(hits) > 1 and cid != countrykey.RESIDUAL:
            dupes.append((y, cid, hits))
    return cells, world, {'world_rejected': dict(world_rejected),
                          'duplicate_rows': dupes, 'raw': raw}


def load_pipeline(commodity):
    """(year -> {country_id: [qty, value]}, raw rows) from the de-duped export.

    exports/_origin_dedup.csv is written by build_map_slim.py and carries the
    same keep/drop verdict the shipped map uses, so the parent/child double
    count (map_data.json holds both 'Australasia' and its six colonies -- a
    clean 2x in tallow 1883-86 and 1891-96) is already resolved, by the code
    that ships rather than by a second copy of it here.
    """
    cells = collections.defaultdict(dict)
    raw = collections.defaultdict(list)
    ck = countrykey.load()
    for r in csv.DictReader(open(DEDUP)):
        if r['commodity'] != commodity or r['kept'] != '1':
            continue
        y = int(r['year'])
        q = float(r['quantity']) if r['quantity'] else None
        v = float(r['value']) if r['value'] else None
        cid, lvl = ck.key(r['country'])
        raw[y].append((r['country'], cid, lvl, q, v))
        if cid == countrykey.DROP:
            continue
        cur = cells[y].setdefault(cid, [0.0, 0.0])
        cur[0] += q or 0
        cur[1] += v or 0
    return cells, raw


def load_t1(commodity):
    slim = json.loads(SLIM.read_text())['commodities']
    e = slim.get(commodity) or {}
    t1 = {int(k): v for k, v in (e.get('t1') or {}).items()}
    t1v = {int(k): v for k, v in (e.get('t1v') or {}).items()}
    return t1, t1v


# ------------------------------------------------------------------- rung 0
def rung0(name, world, arte, gcells, rows):
    """Does the gold close against itself, before our data enters at all?"""
    out = []
    for y in sorted(world):
        wq, wv, _lab = world[y]
        sq = sum(c[0] for c in gcells.get(y, {}).values())
        sv = sum(c[1] for c in gcells.get(y, {}).values())
        if not gcells.get(y):
            continue
        out.append({'commodity': name, 'year': y, 'world_q': wq, 'world_v': wv,
                    'country_sum_q': round(sq), 'country_sum_v': round(sv),
                    'q_closes': int(rel(sq, wq) is not None and rel(sq, wq) <= EXACT01),
                    'v_closes': int(rel(sv, wv) is not None and rel(sv, wv) <= EXACT01),
                    'n_rejected_world_rows': len(arte['world_rejected'].get(y, [])),
                    'n_duplicate_country_rows':
                        sum(1 for d in arte['duplicate_rows'] if d[0] == y)})
    rows.extend(out)
    return out


# ------------------------------------------------------------------- rung 1
def rung1(name, world, t1, t1v, rows):
    out = []
    for y in sorted(world):
        if y not in t1 and y not in t1v:
            continue
        gq, gv, _ = world[y]
        pq, pv = t1.get(y), t1v.get(y)
        out.append({
            'commodity': name, 'year': y, 'naive': int(y not in BENCHMARKED),
            'gold_q': gq, 'pipe_q': pq, 'q_bucket': bucket(pq, gq) if pq else 'nopipe',
            'q_story': digit_story(pq, gq),
            'gold_v': gv, 'pipe_v': pv, 'v_bucket': bucket(pv, gv) if pv else 'nopipe',
            'v_story': digit_story(pv, gv)})
    rows.extend(out)
    return out


# ---------------------------------------------------------------- rungs 2-3
def rungs23(name, gcells, pcells, graw, praw, cell_rows, cov_rows, ledger):
    ck = countrykey.load()
    for y in sorted(set(gcells) & set(pcells)):
        G, P = gcells[y], pcells[y]
        cut = countrykey.coarsest_common_cut(ck, G, P)
        gl, gmap = countrykey.lift(ck, G, cut)
        pl, pmap = countrykey.lift(ck, P, cut)

        for side, rawrows, mapping in (('gold', graw[y], gmap),
                                       ('pipeline', praw[y], pmap)):
            for lab, cid, lvl, q, v in rawrows:
                if cid == countrykey.DROP:
                    disp = 'dropped_junk'
                elif cid == countrykey.RESIDUAL:
                    disp = 'residual_bucket'
                elif mapping.get(cid, cid) != cid:
                    disp = 'rolled_up'
                else:
                    disp = 'matched' if cid in (pl if side == 'gold' else gl) \
                        else 'unmatched_other_side_lacks_it'
                ledger.append({'commodity': name, 'side': side, 'year': y,
                               'raw_label': lab, 'country_id': cid,
                               'level': lvl, 'cut_member': mapping.get(cid, cid),
                               'disposition': disp, 'quantity': q, 'value': v})

        gn = collections.Counter(gmap.values())
        pn = collections.Counter(pmap.values())
        for cid in sorted(cut):
            g, p = gl.get(cid), pl.get(cid)
            if g and p:
                # digit shapes only mean something for a cell that is ONE
                # printed row on both sides. Where the roll-up summed several
                # rows, a 'one digit differs' reading of the total would be
                # numerology, so say what it actually is.
                agg = gn[cid] > 1 or pn[cid] > 1
                shape = (lambda a, b: f'aggregate[{gn[cid]}g+{pn[cid]}p]'
                         if agg else digit_story(a, b))
                cell_rows.append({
                    'commodity': name, 'year': y, 'naive': int(y not in BENCHMARKED),
                    'country': cid, 'n_gold_rows': gn[cid], 'n_pipe_rows': pn[cid],
                    'gold_q': g[0], 'pipe_q': p[0],
                    'q_bucket': bucket(p[0], g[0]), 'q_story': shape(p[0], g[0]),
                    'gold_v': g[1], 'pipe_v': p[1],
                    'v_bucket': bucket(p[1], g[1]) if g[1] else 'nogold',
                    'v_story': shape(p[1], g[1]) if g[1] else ''})
            else:
                have = g or p
                cov_rows.append({
                    'commodity': name, 'year': y, 'country': cid,
                    'side_with_data': 'gold' if g else 'pipeline',
                    'quantity': have[0], 'value': have[1]})


# ------------------------------------------------------------------- rung 4
def rung4(cells, selfcheck, adj, t1, t1v):
    """For each disagreement, what does evidence outside both readings say?

    Four arbiters, none of which is either transcription's own assertion about
    the disputed cell:

      gold_internal -- does the gold's own country sum close on its own World
                       row once this cell is replaced by ours? If it only
                       closes with our reading, the gold slipped here.
      our_anchor    -- same substitution, but measured against OUR Tier-1
                       anchor, which was printed on a different page from the
                       country table and read by two OCR engines. This is the
                       arbiter that settles 1898, where the gold slipped on the
                       country cell AND on its own World row, so the gold's
                       internal test cannot see either.
      cross_field   -- does the OTHER column agree? When the values match to a
                       pound and only the quantities differ, both sides plainly
                       read the same printed row and the difference is keying.
      shape         -- what digit_story says the difference is.

    A year whose gold column fails its own self-check is not adjudicated at
    all: the gold is missing rows there (1894 is short GBP1.1M of country
    value), so every cell in it would be scored against a broken denominator.
    """
    sc = {(r['commodity'], r['year']): r for r in selfcheck}
    for r in cells:
        for col in ('q', 'v'):
            if r[f'{col}_bucket'] != 'off':
                continue
            g, p = r[f'gold_{col}'], r[f'pipe_{col}']
            story = r[f'{col}_story']
            other = 'v' if col == 'q' else 'q'
            other_agrees = r[f'{other}_bucket'] == 'exact01'
            verdict, why = 'unresolved', 'needs the page image'
            s = sc.get((r['commodity'], r['year']))
            anchor = (t1 if col == 'q' else t1v).get(r['year'])
            if s:
                csum = s[f'country_sum_{col}']
                fixed = csum - g + p
                world = s[f'world_{col}']
                gold_closes_now = world and abs(csum - world) <= EXACT01 * world
                gold_closes_ours = world and abs(fixed - world) <= EXACT01 * world
                if gold_closes_ours and not gold_closes_now:
                    verdict = 'gold_error'
                    why = (f"gold's own country rows close on its own World row "
                           f"only with our reading ({fixed:,.0f} = {world:,.0f})")
                elif gold_closes_now:
                    verdict = 'pipeline_error'
                    why = ("gold's own country rows already close on its own "
                           "World row with the gold's reading")
                elif anchor and abs(fixed - anchor) <= EXACT01 * anchor:
                    # the gold is broken on both its cell and its own total,
                    # but substituting our reading reconciles its country rows
                    # with OUR independently-printed anchor
                    verdict = 'gold_error'
                    why = (f"gold's country rows reconcile with our Tier-1 anchor "
                           f"only with our reading ({fixed:,.0f} = {anchor:,.0f}); "
                           f"the gold's own World row ({world:,.0f}) is wrong too")
                elif anchor and abs(csum - anchor) <= EXACT01 * anchor:
                    verdict = 'pipeline_error'
                    why = ("gold's country rows already reconcile with our own "
                           "Tier-1 anchor using the gold's reading")
                elif not gold_closes_now:
                    verdict = 'gold_year_unreliable'
                    why = (f"the gold's own {col} column does not close this year "
                           f"({csum:,.0f} vs World {world:,.0f}), so this cell "
                           f"cannot be adjudicated against it")
            if verdict == 'unresolved' and other_agrees and story.startswith(
                    ('lost_leading_digit', 'one_digit')):
                why = (f'the {other} column agrees exactly, so both sides read the '
                       f'same printed row; the difference is {story}')
            adj.append({'commodity': r['commodity'], 'year': r['year'],
                        'country': r['country'], 'column': col,
                        'gold': g, 'pipeline': p, 'shape': story,
                        'other_column_agrees': int(other_agrees),
                        'verdict': verdict, 'evidence': why})


# --------------------------------------------------------------------- main
def write(path, rows, fields):
    with open(path, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--commodity', default='all',
                    choices=['all'] + list(COMMODITY))
    args = ap.parse_args()
    todo = list(COMMODITY) if args.commodity == 'all' else [args.commodity]

    selfcheck, national, cells, coverage, ledger, adj = [], [], [], [], [], []
    summary = {}
    for key in todo:
        names, pipe_name = COMMODITY[key]
        gcells, world, arte = load_gold(names)
        pcells, praw = load_pipeline(pipe_name)
        t1, t1v = load_t1(pipe_name)
        sc = rung0(pipe_name, world, arte, gcells, selfcheck)
        rung1(pipe_name, world, t1, t1v, national)
        before = len(cells)
        rungs23(pipe_name, gcells, pcells, arte['raw'], praw,
                cells, coverage, ledger)
        rung4(cells[before:], sc, adj, t1, t1v)
        _check_ledger(pipe_name, arte['raw'], praw, ledger)
        summary[pipe_name] = {'gold_years': len(gcells), 'world_years': len(world)}

    REPORTS.mkdir(exist_ok=True)
    write(REPORTS / 'gold_eandh_selfcheck.csv', selfcheck,
          ['commodity', 'year', 'world_q', 'world_v', 'country_sum_q',
           'country_sum_v', 'q_closes', 'v_closes', 'n_rejected_world_rows',
           'n_duplicate_country_rows'])
    write(REPORTS / 'gold_eandh_national.csv', national,
          ['commodity', 'year', 'naive', 'gold_q', 'pipe_q', 'q_bucket',
           'q_story', 'gold_v', 'pipe_v', 'v_bucket', 'v_story'])
    write(REPORTS / 'gold_eandh_country.csv', cells,
          ['commodity', 'year', 'naive', 'country', 'n_gold_rows', 'n_pipe_rows',
           'gold_q', 'pipe_q', 'q_bucket', 'q_story',
           'gold_v', 'pipe_v', 'v_bucket', 'v_story'])
    write(REPORTS / 'gold_eandh_coverage.csv',
          sorted(coverage, key=lambda r: -(r['value'] or 0)),
          ['commodity', 'year', 'country', 'side_with_data', 'quantity', 'value'])
    write(REPORTS / 'gold_eandh_label_ledger.csv',
          sorted(ledger, key=lambda r: -(r['value'] or 0)),
          ['commodity', 'side', 'year', 'raw_label', 'country_id', 'level',
           'cut_member', 'disposition', 'quantity', 'value'])
    write(REPORTS / 'gold_eandh_adjudication.csv',
          sorted(adj, key=lambda r: -abs((r['gold'] or 0) - (r['pipeline'] or 0))),
          ['commodity', 'year', 'country', 'column', 'gold', 'pipeline',
           'shape', 'other_column_agrees', 'verdict', 'evidence'])

    report(selfcheck, national, cells, coverage, ledger, adj)


def _check_ledger(commodity, graw, praw, ledger):
    """The invariant that actually proves nothing was silently dropped.

    A residual report you forget to read proves nothing. Every input label on
    both sides emits exactly one ledger row, so the ledger's value has to
    reproduce each side's input value, year by year. Raise on any shortfall --
    a label that vanishes between input and ledger is a bug in the
    canonicaliser, and the whole point of this exercise is that such a label
    would look like a data gap in the result.
    """
    want = collections.defaultdict(float)
    for side, raw in (('gold', graw), ('pipeline', praw)):
        for y, rows in raw.items():
            for _lab, _cid, _lvl, _q, v in rows:
                want[(side, y)] += v or 0
    got = collections.defaultdict(float)
    for r in ledger:
        if r['commodity'] != commodity:
            continue
        got[(r['side'], r['year'])] += r['value'] or 0
    for key, target in want.items():
        if key[1] not in {y for (_s, y) in got}:
            continue                      # year not comparable on both sides
        if abs(got[key] - target) > 0.5:
            raise AssertionError(
                f'{commodity} {key[0]} {key[1]}: ledger holds '
                f'{got[key]:,.2f} but the input was {target:,.2f} -- '
                f'a label was dropped between input and ledger')


def _rate(rows, col):
    n = collections.Counter(r[col] for r in rows)
    return n


def report(selfcheck, national, cells, coverage, ledger, adj):
    def pr(*a):
        print(*a)

    pr('\n=== rung 0: does the gold close against itself? ===')
    for com in sorted({r['commodity'] for r in selfcheck}):
        rs = [r for r in selfcheck if r['commodity'] == com]
        pr(f'  {com}: {sum(r["q_closes"] for r in rs)}/{len(rs)} years the gold\'s own '
           f'country rows close on its own World row (quantity), '
           f'{sum(r["v_closes"] for r in rs)}/{len(rs)} (value)')
        bad = [r for r in rs if not r['q_closes'] or not r['v_closes']]
        for r in bad:
            pr(f'      {r["year"]}: World q={r["world_q"]:,.0f} v={r["world_v"]:,.0f} | '
               f'countries q={r["country_sum_q"]:,} v={r["country_sum_v"]:,}')

    pr('\n=== rung 1: national total vs our Tier-1 anchor ===')
    for com in sorted({r['commodity'] for r in national}):
        for label, sel in (('all years', lambda r: True),
                           ('naive only', lambda r: r['naive'])):
            rs = [r for r in national if r['commodity'] == com and sel(r)]
            if not rs:
                continue
            q = _rate(rs, 'q_bucket')
            v = _rate(rs, 'v_bucket')
            pr(f'  {com} [{label}] n={len(rs)}  '
               f'quantity exact {q["exact01"]}  within5 {q["within5"]}  off {q["off"]}  |  '
               f'value exact {v["exact01"]}  within5 {v["within5"]}  off {v["off"]}')
        for r in national:
            if r['commodity'] == com and (r['q_bucket'] == 'off' or r['v_bucket'] == 'off'):
                pr(f'      {r["year"]}: q gold {r["gold_q"]:,.0f} vs ours '
                   f'{r["pipe_q"] or 0:,.0f} [{r["q_story"]}]; v gold {r["gold_v"]:,.0f} '
                   f'vs ours {r["pipe_v"] or 0:,.0f} [{r["v_story"]}]')

    pr('\n=== rung 2: country cells after roll-up ===')
    for com in sorted({r['commodity'] for r in cells}):
        for label, sel in (('all years', lambda r: True),
                           ('naive only', lambda r: r['naive'])):
            rs = [r for r in cells if r['commodity'] == com and sel(r)]
            if not rs:
                continue
            q, v = _rate(rs, 'q_bucket'), _rate(rs, 'v_bucket')
            pr(f'  {com} [{label}] {len(rs)} comparable cells  '
               f'quantity exact {q["exact01"]} within5 {q["within5"]} off {q["off"]}  |  '
               f'value exact {v["exact01"]} within5 {v["within5"]} off {v["off"]}')

    pr('\n=== rung 3: completeness ===')
    d = _rate(ledger, 'disposition')
    for k, n in d.most_common():
        pr(f'  {k:34} {n:5}')
    unm = [r for r in ledger if r['disposition'] == 'unmatched_other_side_lacks_it']
    gbp = sum(r['value'] or 0 for r in unm)
    tot = sum(r['value'] or 0 for r in ledger)
    pr(f'  unmatched GBP {gbp:,.0f} of {tot:,.0f} ({100*gbp/(tot or 1):.2f}%)')
    for r in sorted(unm, key=lambda r: -(r['value'] or 0))[:10]:
        pr(f'      {r["side"]:8} {r["year"]} {r["country_id"]:34} '
           f'q={r["quantity"] or 0:>10,.0f} v={r["value"] or 0:>10,.0f}')

    pr('\n=== rung 4: adjudication of disagreements ===')
    vd = _rate(adj, 'verdict')
    for k, n in vd.most_common():
        pr(f'  {k:14} {n}')
    for r in sorted(adj, key=lambda r: -abs((r['gold'] or 0) - (r['pipeline'] or 0)))[:12]:
        pr(f'      {r["year"]} {r["country"]:26} {r["column"]}  gold {r["gold"]:>12,.0f}  '
           f'ours {r["pipeline"]:>12,.0f}  [{r["shape"]}]  -> {r["verdict"]}')
    pr('')
    for p in ('selfcheck', 'national', 'country', 'coverage', 'label_ledger',
              'adjudication'):
        pr(f'  reports/gold_eandh_{p}.csv')


if __name__ == '__main__':
    main()
