#!/usr/bin/env python3
"""Same-engine label slips, witnessed by the ADJACENT VOLUMES.

The class. The parser glues two printed country lines into one label
('British India: Bombay and Scinde Bengal and Burmah') but keeps both values,
so from that row on every value sits one label too LOW: as_1873 APPAREL reads
Australia 29,868 and British North America 1,419,720 where the print has
Bengal 29,868, Australia 1,419,720, BNA 245,933 -- and the last printed value
(Other Countries 226,457) falls off the end because it has no label left.
The section then fails closure by exactly that lost value, and BOTH engines
agree on every misplaced number, so repair_row_slip.py (cross-engine) cannot
see it. It made the largest spike left in the Canada series (APPAREL 1873
x4.9) and it is invisible to every arithmetic check but the shortfall.

The witness. The same countries in the neighbouring years. Under the
hypothesis "labels shifted from row k, the last label's value is the
shortfall D", each affected country takes a value; the hypothesis whose
values sit closest (log distance) to the same countries in the adjacent
own-year volumes -- canonicalised through countrykey, so 'British North
America' meets 'Canada' -- wins, and only by a margin (see ACCEPT below).
The no-shift reading competes on the same terms, so a merged label whose
second value the parser DROPPED (no shift) is left alone.

Where the label at k-1 is visibly two labels glued (its tail is itself a
label printed elsewhere in the volume), that row also takes the orphaned
value v_k, so the merged row carries both printed lines and the section
closes exactly. Otherwise the orphan stays lost (the same known cost as the
cross-engine class): the per-country values are right, the TOTAL is short by
one row nobody can name.

Output: reference/label_merge_repairs.csv -- the standard overlay (volume,
year, flow, article_group, article (raw), country_raw, old_value, new_value,
witnesses). Applied by every consumer after row_slip/scaled_block and before
section_closure_repairs (whose PRIOR includes it).

Usage: python3 scripts/repair_label_merge.py [--dry-run] [--verbose] [--flow F]
"""
import argparse, collections, csv, math, os, sys
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import countrykey
from repair_edge_columns import ENGINES, TOTAL_RE, norm
from repair_section_closure import TARGETS, fetch_rows, table_for
from repair_row_slip import sections, closes

PRIOR = ('reference/export_cell_repairs.csv',
         'reference/malformed_cell_repairs.csv',
         'reference/edge_column_repairs.csv',
         'reference/row_slip_repairs.csv',
         'reference/scaled_block_repairs.csv')
NO = object()

# the primary volume of each year (PRIMARY_OVERRIDE sends 1897/98 to as_1899)
PRIMARY = {1870: 'tn_1871', 1900: 'tn_1901', 1897: 'as_1899', 1898: 'as_1899',
           1899: 'as_1899'}
for _y in range(1872, 1897):
    PRIMARY[_y] = f'as_{_y}'

# ACCEPT: the shifted hypothesis must beat no-shift by this many nats in
# total over the rows that have a neighbour reading, with at least MIN_CMP
# such rows among the affected ones, and a majority of them individually
# closer to their neighbours.
MIN_GAIN = 2.5
MIN_CMP = 3


def load_prior():
    out = {}
    for path in PRIOR:
        if not os.path.exists(path):
            continue
        for r in csv.DictReader(open(path)):
            out[(r['volume'], int(r['year']), r['article_group'], r['article'],
                 r['country_raw'], round(float(r['old_value'])))] = (
                float(r['new_value']) if r['new_value'] != '' else None)
    return out


def apply_prior(rows, prior, vol, year):
    out = []
    for flow, ag, art, unit, ctry, v, ra, ru, sq in rows:
        if v is not None:
            nv = prior.get((vol, year, ag, ra, ctry, round(v)), NO)
            if nv is not NO:
                v = nv
        out.append((flow, ag, art, unit, ctry, v, ra, ru, sq))
    return out


class Neighbours:
    """Per neighbouring volume-year: the sections of each (flow, group,
    article[, unit]) block as {cid: value}. lookup() picks, in each
    neighbour, the section whose label set overlaps the target's most (a
    block holds several printed sections -- per unit, per sub-article, per
    'To' page in the wide tables -- and 'first section wins' matched cordage
    to the wrong one), and combines the neighbours' readings by weighted
    geometric mean."""

    def __init__(self, ck):
        self.ck = ck
        self.vols = []           # [(weight, {block key: [ {cid: v} ]})]

    def add(self, rows, weight):
        by_block = collections.OrderedDict()
        for flow, ag, art, unit, ctry, v, ra, ru, sq in rows:
            by_block.setdefault((flow, norm(ag), norm(art), norm(unit)), []).append((ctry, v))
        # only sections that CLOSE on their printed TOTAL may testify: a
        # neighbour carrying the same slip fails closure by its own lost
        # value (as_1881 and as_1883 both shift COTTON 'Piece Goods, Plain'
        # and would have "confirmed" the same wrong shift in as_1882 at 25
        # nats -- Aden wearing Bombay's 4.6M)
        blocks = {}
        for bk, lst in by_block.items():
            secs, cur, csum = [], {}, 0.0
            for ctry, v in lst:
                if ctry and TOTAL_RE.search(ctry):
                    if cur and v and abs(csum - v) <= 0.001 * abs(v):
                        secs.append(cur)
                    cur, csum = {}, 0.0
                    continue
                if v is None or not ctry:
                    continue
                csum += v
                cid = self.ck.key(ctry)[0]
                if cid == countrykey.DROP:
                    continue
                cur.setdefault(cid, v)
            # a trailing section without a TOTAL cannot testify
            blocks[bk] = secs
            blocks.setdefault(bk[:3], []).extend(secs)     # unit-less fallback
        self.vols.append((weight, blocks))

    def lookup(self, flow, ag, art, unit, cids):
        """cids: the target section's canonical labels -> {cid: value}."""
        want = set(cids)
        acc = collections.defaultdict(list)
        for weight, blocks in self.vols:
            secs = blocks.get((flow, norm(ag), norm(art), norm(unit))) or \
                blocks.get((flow, norm(ag), norm(art))) or []
            best, bo = None, 0.0
            for sec in secs:
                o = len(want & set(sec)) / max(len(want | set(sec)), 1)
                if o > bo:
                    best, bo = sec, o
            if best is None or len(want & set(best)) < 0.5 * len(want):
                continue
            for cid, v in best.items():
                acc[cid].append((v, weight))
        out = {}
        for cid, lst in acc.items():
            w = sum(x[1] for x in lst)
            out[cid] = math.exp(sum(math.log(v + 1) * wt for v, wt in lst) / w) - 1
        return out


def err(v, nb):
    return abs(math.log((v + 1) / (nb + 1)))


def hypotheses(mem, D):
    """mem: [(idx, ctry, v)]; yields (k, [(idx, ctry, new_v)]) for k in
    0..n-2: rows k..n-2 take the next row's value, row n-1 takes D."""
    n = len(mem)
    for k in range(0, n - 1):
        new = []
        for t in range(n):
            if t < k:
                new.append((mem[t][0], mem[t][1], mem[t][2]))
            elif t < n - 1:
                new.append((mem[t][0], mem[t][1], mem[t + 1][2]))
            else:
                new.append((mem[t][0], mem[t][1], D))
        yield k, new


def score(vals, nbs, ck, rows_from=0):
    """sum of log errors and count over rows >= rows_from with a neighbour."""
    s, n, per = 0.0, 0, []
    for t, (idx, c, v) in enumerate(vals):
        if t < rows_from:
            continue
        cid = ck.key(c)[0]
        if cid in nbs:
            e = err(v, nbs[cid])
            s += e
            n += 1
            per.append(e)
        else:
            per.append(None)
    return s, n, per


def glued_tail(label, labels_norm):
    """Two printed labels glued: the tail is itself a label of this volume
    AND the head (before it, stripped of ':,-') is too, and the tail does
    not follow 'and'/'&' ('Sweden and Norway' is one label; 'British India:
    Bombay and Scinde Bengal and Burmah' is two)."""
    s = (label or '').strip()
    words = s.split()
    for i in range(1, len(words)):
        if words[i - 1].lower() in ('and', '&', 'of', 'the'):
            continue
        tail = ' '.join(words[i:])
        head = ' '.join(words[:i]).rstrip(':,-').strip()
        if len(tail) >= 5 and norm(tail) in labels_norm and \
                len(head) >= 4 and norm(head) in labels_norm:
            return tail
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='db/uk_trade.duckdb')
    ap.add_argument('--out', default='reference/label_merge_repairs.csv')
    ap.add_argument('--flow', default='export_uk,reexport',
                    help='comma list; the import side has its own machinery')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--verbose', '-v', action='count', default=0,
                    help='-v per section, -vv per row (label old -> new | neighbours)')
    a = ap.parse_args()
    con = duckdb.connect(a.db, read_only=True)
    prior = load_prior()
    ck = countrykey.load()

    cache = {}

    def rows_for(vol, year):
        if (vol, year) not in cache:
            cache[(vol, year)] = apply_prior(
                fetch_rows(con, 'country_obs', vol, year), prior, vol, year)
        return cache[(vol, year)]

    def one_pass(prior, done):
        """One sweep over TARGETS with the given prior overlays; sections
        already repaired (done: set of (vol, year, block key, si)) are
        skipped. Returns (repairs, stats)."""
        cache.clear()
        repairs, stats = [], collections.Counter()
        for (vol, year), _w in sorted(TARGETS.items(), key=lambda t: t[0][1]):
            own = rows_for(vol, year)
            flows = {f.strip() for f in a.flow.split(',') if f.strip()}
            own = [r for r in own if r[0] in flows]
            labels_norm = {norm(r[4]) for r in own if r[4]}
            # neighbours: nearest own-year volume on each side (two on one side
            # when the other is missing), nearer weighted double
            nb = Neighbours(ck)
            sides = []
            for d in (1, 2):
                for sgn in (-1, 1):
                    y2 = year + sgn * d
                    if y2 in PRIMARY and (PRIMARY[y2], y2) in TARGETS:
                        sides.append((y2, 2.0 if d == 1 else 1.0))
            got = set()
            for y2, w in sides:
                if len(got) >= 2 or y2 in got:
                    continue
                nb.add(rows_for(PRIMARY[y2], y2), w)
                got.add(y2)
            # the other engine's TOTALs are candidate printed totals too
            other = fetch_rows(con, table_for('inf', vol, year), vol, year)
            oth_secs = sections(other)
            oth_by_norm = collections.defaultdict(list)
            for bk, secs in oth_secs.items():
                oth_by_norm[tuple(norm(x) for x in bk[:3])].append(secs)

            own_secs = sections(own)
            for bk, secs in own_secs.items():
                flow, ag, art, unit = bk
                cands = oth_by_norm.get(tuple(norm(x) for x in bk[:3]))
                osecs = cands[0] if cands and len(cands) == 1 else None
                for si, (mem, tot) in enumerate(secs):
                    if len(mem) < 4 or (vol, year, bk, si) in done:
                        continue
                    if closes(mem, tot):
                        continue
                    S = sum(v for _, _, v in mem)
                    totals = []
                    if tot is not None and tot > S * 1.001:
                        totals.append(('obs', tot))
                    if osecs is not None and si < len(osecs):
                        otot = osecs[si][1]
                        if otot is not None and otot > S * 1.001 and \
                                all(abs(otot - t) > 0.5 for _, t in totals):
                            totals.append(('inf', otot))
                    if not totals:
                        continue
                    nbs = nb.lookup(flow, ag, art, unit,
                                    [ck.key(c)[0] for _, c, _ in mem])
                    if len(nbs) < MIN_CMP:
                        continue
                    base_s, base_n, base_per = score(mem, nbs, ck)
                    best = None
                    near = None
                    passing = []
                    for eng, T in totals:
                        D = T - S
                        for k, new in hypotheses(mem, D):
                            s, n, per = score(new, nbs, ck)
                            # compare over the affected rows only
                            aff = [(bp, hp) for bp, hp in zip(base_per[k:], per[k:])
                                   if bp is not None]
                            if len(aff) < MIN_CMP:
                                continue
                            gain = sum(bp - hp for bp, hp in aff)
                            better = sum(1 for bp, hp in aff if hp < bp - 0.3)
                            worse = sum(1 for bp, hp in aff if hp > bp + 0.3)
                            # a real slip moves (nearly) every affected row
                            # towards its neighbours; a mixed verdict is noise
                            reject = None
                            if (gain < MIN_GAIN or better < MIN_CMP or
                                    worse > (1 if better >= 8 else 0) or
                                    better < 0.6 * len(aff)):
                                reject = f'mixed verdict {better}b/{worse}w of {len(aff)}'
                            # the row that takes D (the shortfall) is the
                            # hypothesis' own prediction: it must be checkable
                            # and land near its neighbour, else D is a misread
                            # TOTAL or a digit error, not a lost row
                            elif per[-1] is None:
                                reject = 'D row has no neighbour'
                            elif per[-1] > 1.0 or per[-1] > base_per[-1] + 0.3:
                                reject = (f'D row {D:.0f} vs nb '
                                          f'{nbs.get(ck.key(mem[-1][1])[0], 0):.0f}')
                            else:
                                # the neighbour must be THIS section: under the
                                # winning reading the typical row sits near it
                                # (a sub-section at another scale matched on
                                # label overlap floats a false shift)
                                errs = sorted(e for e in per if e is not None)
                                med = errs[len(errs) // 2]
                                if med > 0.7:
                                    reject = f'neighbour off-scale (median {med:.2f} nats)'
                            if reject:
                                if gain >= 5 and (near is None or gain > near[0]):
                                    near = (gain, k, reject, eng, T, D)
                                continue
                            cand = (gain, k, new, eng, T, D, len(aff), better, worse)
                            passing.append(cand)
                            if best is None or gain > best[0]:
                                best = cand
                    if best is None:
                        stats['sections short, no winning shift'] += 1
                        if near and a.verbose:
                            print(f'  NEAR-MISS {vol} {year} {flow} {ag[:28]}/{art[:24]} sec {si}: '
                                  f'gain {near[0]:.1f} at row {near[1]}/{len(mem)}, '
                                  f'{near[3]} TOTAL {near[4]:.0f} short {near[5]:.0f}: {near[2]}')
                        continue
                    # structural preference: a visibly glued label at row j
                    # says the shift starts at j+1; take that reading when it
                    # is within 1 nat of the best (the neighbours rarely
                    # separate k=j from k=j+1 -- only row j's value differs)
                    for cand in passing:
                        kk = cand[1]
                        if kk >= 1 and glued_tail(mem[kk - 1][1], labels_norm) and \
                                cand[0] >= best[0] - 1.0 and cand[1] != best[1]:
                            best = cand
                            break
                    gain, k, new, eng, T, D, ncmp, better, worse = best
                    # the glued-label bonus: row k-1 takes the orphan v_k
                    glued = None
                    if k >= 1:
                        glued = glued_tail(mem[k - 1][1], labels_norm)
                    fixes = []
                    for t in range(k, len(mem)):
                        idx, c, ov = mem[t]
                        nv = new[t][2]
                        if abs(nv - ov) >= 0.5:
                            fixes.append((idx, nv))
                    if glued:
                        idx, c, ov = mem[k - 1]
                        fixes.append((idx, ov + mem[k][2]))
                    if not fixes:
                        continue
                    why = (f'neighbours: labels shifted from row {k}/{len(mem)}, '
                           f'{eng} TOTAL {T:.0f} short {D:.0f}, gain {gain:.1f} nats '
                           f'over {ncmp} rows ({better} better/{worse} worse)'
                           + (f'; glued label takes orphan {mem[k][2]:.0f}' if glued else ''))
                    for idx, nv in fixes:
                        flow_, ag_, art_, unit_, cty, ov, ra, ru, sq = own[idx]
                        repairs.append(dict(volume=vol, year=year, flow=flow_,
                                            article_group=ag_, article=ra,
                                            country_raw=cty, old_value=ov,
                                            new_value=nv, witnesses=why))
                    done.add((vol, year, bk, si))
                    stats[f'{vol}-{year} sections repaired'] += 1
                    stats[f'{vol}-{year} cells changed'] += len(fixes)
                    if a.verbose:
                        print(f'  {vol} {year} {flow} {ag[:28]}/{art[:24]} sec {si}: '
                              f'{len(fixes)} cells  [{why}]')
                    if a.verbose > 1:
                        for t, (idx, c, ov) in enumerate(mem):
                            nv = new[t][2]
                            cid = ck.key(c)[0]
                            nbv = nbs.get(cid)
                            mark = '' if t < k else ('*' if abs(nv - ov) >= 0.5 else '=')
                            print(f'      {mark:1} {c[:40]:40} {ov:>12,.0f} -> {nv:>12,.0f}'
                                  f'   nb {"" if nbv is None else f"{nbv:,.0f}":>12}')

            # overlay-key ambiguity guard, per volume-year
            key_count = collections.Counter(
                (ag, ra, ctry, round(v)) for _, ag, art, unit, ctry, v, ra, ru, sq in own
                if v is not None)
            grouped = collections.defaultdict(list)
            for r in repairs:
                if r['volume'] == vol and r['year'] == year:
                    grouped[(r['article_group'], r['article'], r['country_raw'],
                             round(r['old_value']))].append(r)
            for gk, grp in grouped.items():
                if len({g['new_value'] for g in grp}) > 1 or len(grp) != key_count[gk]:
                    for g in grp:
                        repairs.remove(g)
                    stats[f'{vol}-{year} dropped: overlay key ambiguous'] += len(grp)
                else:
                    for g in grp[1:]:
                        repairs.remove(g)
            # re-key onto a prior overlay's old value where the same raw key
            # already carries a repair
            by_new = {}
            for (pv, py, pag, part, pc, pold), pnew in prior.items():
                if pv == vol and py == year and pnew is not None:
                    by_new[(pag, part, pc, round(pnew))] = pold
            for r in repairs:
                if r['volume'] == vol and r['year'] == year:
                    kk = (r['article_group'], r['article'], r['country_raw'],
                          round(r['old_value']))
                    if kk in by_new:
                        r['old_value'] = by_new[kk]
                        stats[f'{vol}-{year} rekeyed onto prior'] += 1
        return repairs, stats

    # iterate: a repaired section closes (glued label) or at least carries
    # the right per-country values, and becomes a witness for its
    # neighbours in the next pass -- as_1880 SPIRITS needs as_1879 SPIRITS,
    # itself slipped, repaired first
    repairs, stats, done = [], collections.Counter(), set()
    for it in range(4):
        new, st = one_pass(prior, done)
        if not new:
            break
        repairs.extend(new)
        stats.update(st)
        for r in new:
            prior[(r['volume'], int(r['year']), r['article_group'], r['article'],
                   r['country_raw'], round(float(r['old_value'])))] = float(r['new_value'])
        if a.verbose:
            print(f'-- pass {it + 1}: {len(new)} cells')

    tot_sec = sum(v for k, v in stats.items() if k.endswith('sections repaired'))
    tot_ch = sum(v for k, v in stats.items() if k.endswith('cells changed'))
    print(f'{tot_sec} shifted sections, {tot_ch} cells re-valued; '
          f"{stats['sections short, no winning shift']} short sections left alone")
    for k in sorted(stats):
        if k.endswith('sections repaired'):
            print(f'  {k:40} {stats[k]:4}')
    if not a.dry_run:
        with open(a.out, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['volume', 'year', 'flow', 'article_group',
                                              'article', 'country_raw', 'old_value',
                                              'new_value', 'witnesses'])
            w.writeheader()
            w.writerows(repairs)
        print(f'wrote {len(repairs)} repairs -> {a.out}')


if __name__ == '__main__':
    main()
