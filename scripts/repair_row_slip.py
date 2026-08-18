#!/usr/bin/env python3
"""Row-slip repairs: a section whose VALUES are right but whose country
LABELS are shifted by one row, taken from the engine that has them aligned.

as_1881 LEATHER 'Wrought, Boots and Shoes': country_obs lost the first
label ('Holland') and the last row, so every value sits against the
PREVIOUS country's name -- Australasia's 590,215 is filed under British
North America, Canada's 9,462 under the West Indies. country_obs_inf reads
the same page with the labels aligned and closes on the printed TOTAL to the
pound. as_1880 MEDICINES the same (obs 176,918 for Canada is Australia's;
Canada is 37,117). LEATHER 1881 x10, MEDICINES 1880 x5, STATIONERY 1873,
PLATED 1875, ARMS 1874/77, EARTHEN 1881/82, COPPER 1880 in the Canada series
are all this.

Nothing arithmetic sees it: the value multiset is the same in both engines
(minus a dropped row), so the section closes -- or misses by one row -- in
both. Only the cross-engine LABEL comparison does. Rule, per printed
section (members up to a TOTAL) of an own-year volume:

  * find the same section in the other engine (same block key after the
    phantom relabel, same ordinal within the block);
  * the other engine's section closes on its printed TOTAL to 0.1 % and the
    own section does not (or both close but the own is a slipped
    permutation: see below);
  * the two sections are the same page: >= 60 % of the own member values
    occur in the other engine's section, and >= 60 % of THOSE occur against
    a DIFFERENT country label -- a slip, not a different reading;
  * then every own member whose country the other engine also lists takes
    the other engine's value for that country (a change only where they
    differ); own members whose country the other engine does not list are
    nulled (blank new_value = drop), since their value belongs to some
    other country. Countries the other engine lists but the own parse
    lacks entirely cannot be inserted by an overlay and are lost (a known
    cost: the first row of the section, usually).

Output: reference/row_slip_repairs.csv -- the standard overlay (volume,
year, flow, article_group, article, country_raw, old_value, new_value,
witnesses), RAW article, applied by every consumer with the other value
overlays (before section_closure_repairs, which then starts from the
relabelled state).

Usage: python3 scripts/repair_row_slip.py [--dry-run] [--verbose]
"""
import argparse, collections, csv, os, re, sys
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repair_edge_columns import ENGINES, TN_TABLES, TOTAL_RE, norm
from repair_section_closure import TARGETS, fetch_rows, table_for

PRIOR = ('reference/export_cell_repairs.csv',
         'reference/malformed_cell_repairs.csv',
         'reference/edge_column_repairs.csv',
         'reference/scaled_block_repairs.csv')
NO = object()


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


def sections(rows):
    """rows of one (vol, year) as fetch_rows returns them, block-ordered ->
    {block key: [ (members [(idx, ctry, value)], total_value or None) ]}"""
    blocks = collections.OrderedDict()
    for i, r in enumerate(rows):
        blocks.setdefault(r[:4], []).append(i)
    out = {}
    for bk, idxs in blocks.items():
        secs, mem = [], []
        for i in idxs:
            ctry, v = rows[i][4], rows[i][5]
            if ctry and TOTAL_RE.search(ctry):
                if mem:
                    secs.append((mem, v))
                mem = []
            elif v is not None:
                mem.append((i, ctry, v))
        if mem:
            secs.append((mem, None))
        out[bk] = secs
    return out


def closes(mem, tot):
    return (tot is not None and tot and
            abs(sum(v for _, _, v in mem) - tot) <= 0.001 * abs(tot))


MIN_RUN = 4            # rows in a constant-offset run before it is a slip
MIN_RUN_TAIL = 3       # ...or 3 when the run reaches the section's end


def slip_repairs(mem, omem, own_slipped):
    """mem, omem: [(idx, country, value)] of the own and the other engine's
    reading of ONE printed section. Returns [(own idx, new value or None,
    evidence)] or [].

    Same page: >= 60 % of the own values occur in the other engine's list at
    one consistent position offset (the value base). Each own row's LABEL
    offset (nearest occurrence of the same country in the other list) minus
    that base is 0 when label and value travel together and non-zero when
    the label has slipped. A slip is a run of >= MIN_RUN consecutive rows
    (>= MIN_RUN_TAIL if it reaches the end) at one constant non-zero
    relative offset; every row in the run takes the other engine's value for
    its own label, or is nulled when the other engine has no such label.
    A row whose label duplicates another row of the section, where the
    other engine's value for that label equals the OTHER row's value, is a
    mislabelled row and is nulled."""
    if len(mem) < 4 or len(omem) < 4:
        return []
    opos_v = collections.defaultdict(list)
    opos_l = collections.defaultdict(list)
    ov_by_c = {}
    for j, (_, c, v) in enumerate(omem):
        opos_v[round(v)].append(j)
        opos_l[norm(c)].append(j)
        ov_by_c.setdefault(norm(c), v)
    # value base offset
    voffs = collections.Counter()
    for k, (_, c, v) in enumerate(mem):
        for j in opos_v.get(round(v), []):
            voffs[j - k] += 1
    if not voffs:
        return []
    (base, nb), = voffs.most_common(1)
    if nb < 0.5 * len(mem) or nb < 3:
        return []
    # per-row relative offset: where this row's LABEL sits in the other list
    # minus where this row's VALUE sits (both nearest to the aligned
    # position). Label and value travelling together (a merged or split
    # row shifts both) is 0; a slipped label is non-zero.
    rel, at = [], []
    for k, (_, c, v) in enumerate(mem):
        tgt = k + base
        vj = opos_v.get(round(v))
        vpos = min(vj, key=lambda j: abs(j - tgt)) if vj else tgt
        js = opos_l.get(norm(c))
        if not js:
            rel.append(None)
            at.append(None)
        else:
            lpos = min(js, key=lambda j: abs(j - tgt))
            rel.append(lpos - vpos)
            at.append(lpos)
    fixes = {}
    # runs of constant non-zero relative offset (None rows may sit inside)
    k = 0 if own_slipped else len(rel)
    while k < len(rel):
        if rel[k] in (None, 0):
            k += 1
            continue
        d = rel[k]
        e = k
        while e + 1 < len(rel) and rel[e + 1] in (d, None):
            e += 1
        while rel[e] is None:
            e -= 1
        n = e - k + 1
        if n >= MIN_RUN or (n >= MIN_RUN_TAIL and e == len(rel) - 1):
            for t in range(k, e + 1):
                idx, c, v = mem[t]
                if at[t] is None:
                    fixes[idx] = (None, f'slip run {n} rows offset {d:+d}')
                else:
                    nv = omem[at[t]][2]     # the other engine's value AT the label
                    if abs(nv - v) >= 0.5:
                        fixes[idx] = (nv, f'slip run {n} rows offset {d:+d}')
        k = e + 1
    # a label duplicated inside a run: both rows would take the other
    # engine's value for it -- keep the row whose own value is nearest that
    # value (it is the real one), null the rest
    dup = collections.defaultdict(list)
    for t, (idx, c, v) in enumerate(mem):
        dup[norm(c)].append((idx, v))
    for c, lst in dup.items():
        if len(lst) < 2:
            continue
        nvs = {fixes[idx][0] for idx, v in lst if idx in fixes and fixes[idx][0] is not None}
        if len(nvs) != 1:
            continue
        nv = nvs.pop()
        keep = min(lst, key=lambda x: abs(x[1] - nv) / max(nv, 1))
        for idx, v in lst:
            if idx != keep[0]:
                fixes[idx] = (None, 'duplicate label inside slip run')
            elif idx in fixes:
                del fixes[idx]
    # duplicate labels
    by_c = collections.defaultdict(list)
    for t, (idx, c, v) in enumerate(mem):
        by_c[norm(c)].append((idx, v))
    for c, lst in by_c.items():
        if len(lst) < 2 or c not in ov_by_c:
            continue
        good = [idx for idx, v in lst if abs(v - ov_by_c[c]) < 0.5]
        if len(good) == 1:
            for idx, v in lst:
                if idx not in good and idx not in fixes:
                    fixes[idx] = (None, 'duplicate label, value belongs elsewhere')
    return [(idx, nv, why) for idx, (nv, why) in sorted(fixes.items())]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='db/uk_trade.duckdb')
    ap.add_argument('--out', default='reference/row_slip_repairs.csv')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--verbose', '-v', action='store_true')
    a = ap.parse_args()
    con = duckdb.connect(a.db, read_only=True)
    prior = load_prior()

    repairs, stats = [], collections.Counter()
    for (vol, year), _w in TARGETS.items():
        own_raw = fetch_rows(con, 'country_obs', vol, year)
        own = []
        for flow, ag, art, unit, ctry, v, ra, ru, sq in own_raw:
            if v is not None:
                nv = prior.get((vol, year, ag, ra, ctry, round(v)), NO)
                if nv is not NO:
                    v = nv
            own.append((flow, ag, art, unit, ctry, v, ra, ru, sq))
        own_secs = sections(own)
        for eng in ENGINES:
            if eng == 'obs':
                continue
            other = fetch_rows(con, table_for(eng, vol, year), vol, year)
            oth_secs = sections(other)
            # match blocks on normalised key
            # match blocks WITHOUT the unit (the engines disagree on it:
            # obs '' against inf 'Dozen Pairs' for the same block)
            oth_by_norm = collections.defaultdict(list)
            for bk, secs in oth_secs.items():
                oth_by_norm[tuple(norm(x) for x in bk[:3])].append(secs)
            # content index: value -> other sections holding it (the other
            # engine files whole groups under another heading in some
            # volumes -- as_1874 BEER, as_1879 SPIRITS, as_1883 PICKLES are
            # absent from inf under any spelling -- but the page's values
            # identify the section regardless of its label)
            by_value = collections.defaultdict(set)
            all_osecs = []
            for bk, secs in oth_secs.items():
                for omem, otot in secs:
                    sid = len(all_osecs)
                    all_osecs.append((omem, otot))
                    for _, c, v in omem:
                        by_value[round(v)].add(sid)
            def by_content(mem):
                hits = collections.Counter()
                for _, c, v in mem:
                    for sid in by_value.get(round(v), ()):
                        hits[sid] += 1
                if not hits:
                    return None
                best = hits.most_common(2)
                sid, n = best[0]
                if n < 0.6 * len(mem) or n < 4:
                    return None
                if len(best) > 1 and best[1][1] >= 0.6 * len(mem):
                    return None            # two candidates: ambiguous
                return all_osecs[sid]
            for bk, secs in own_secs.items():
                cands = oth_by_norm.get(tuple(norm(x) for x in bk[:3]))
                osecs = cands[0] if cands and len(cands) == 1 else None
                if cands and len(cands) > 1:
                    # the other engine split the same block on unit ('' for
                    # a one-line 'all Countries' row, 'Dozens' for the
                    # hierarchy after it -- as_1874 ARMS 'Swords'): take the
                    # candidate list whose sections share the most values
                    # with ours (a plurality, at least a third)
                    own_vals = {round(v) for m, t in secs for _, c, v in m}
                    scored = sorted(
                        ((sum(1 for m, t in cs for _, c, v in m if round(v) in own_vals), i)
                         for i, cs in enumerate(cands)), reverse=True)
                    if scored[0][0] >= len(own_vals) / 3 and \
                            (len(scored) < 2 or scored[0][0] > scored[1][0]):
                        osecs = cands[scored[0][1]]
                for si, (mem, tot) in enumerate(secs):
                    if len(mem) < 4:
                        continue
                    if osecs is not None and si < len(osecs):
                        omem, otot = osecs[si]
                    else:
                        found = by_content(mem)
                        if not found:
                            continue
                        omem, otot = found
                        stats[f'{vol}-{year} matched by content'] += 1
                    # direction: the engine that slipped dropped a label
                    # row -- it has FEWER rows and does not close. Repair
                    # only when the other engine closes and the own does
                    # not, or when neither/both close but the own has fewer
                    # rows; the duplicate-label rule stands on its own.
                    oc, wc = closes(omem, otot), closes(mem, tot)
                    osum, wsum = sum(v for _, _, v in omem), sum(v for _, _, v in mem)
                    # a "TOTAL" far below its own members' sum is a member
                    # row wearing the TOTAL's label: that engine slipped
                    o_misplaced = otot is not None and otot < 0.5 * osum
                    w_misplaced = tot is not None and tot < 0.5 * wsum
                    if o_misplaced != w_misplaced:
                        own_slipped = w_misplaced
                    elif otot is None or len(omem) > 2 * len(mem):
                        # no TOTAL to judge the other by (a fused block):
                        # the own section must at least fail its own
                        own_slipped = not wc
                    elif oc != wc:
                        own_slipped = oc
                    else:
                        # neither (or both) close: the engine that slipped
                        # LOST a label -- its label set lacks one the other
                        # has (fragments like 'Guiana' are not labels)
                        ol = {norm(c) for _, c, v in omem}
                        wl = {norm(c) for _, c, v in mem}
                        def frag(x, universe):
                            # a fragment or a variant of a label the other
                            # has ('Guiana'; 'British India : Straits
                            # Settlements' vs 'Straits Settlements')
                            return any(x != u and (x in u or u in x) for u in universe)
                        miss_own = sum(1 for x in ol - wl if not frag(x, wl))
                        miss_oth = sum(1 for x in wl - ol if not frag(x, ol))
                        own_slipped = (miss_own > miss_oth or
                                       (miss_own == miss_oth and len(mem) < len(omem)))
                    fixes = slip_repairs(mem, omem, own_slipped)
                    if not fixes:
                        continue
                    n_ch = n_drop = 0
                    for i, new, why in fixes:
                        flow, ag, art, unit, cty, ov, ra, ru, sq = own[i]
                        if new is None:
                            n_drop += 1
                        else:
                            n_ch += 1
                        repairs.append(dict(volume=vol, year=year, flow=flow,
                                            article_group=ag, article=ra,
                                            country_raw=cty, old_value=ov,
                                            new_value='' if new is None else new,
                                            witnesses=f'{eng}:{vol} {why}'))
                    stats[f'{vol}-{year} sections repaired'] += 1
                    stats[f'{vol}-{year} cells changed'] += n_ch
                    stats[f'{vol}-{year} cells dropped'] += n_drop
                    if a.verbose:
                        print(f'  {vol} {year} {bk[1][:28]}/{bk[2][:24]} sec {si}: '
                              f'{n_ch} changed, {n_drop} dropped  [{fixes[0][2]}]')

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
                k = (r['article_group'], r['article'], r['country_raw'],
                     round(r['old_value']))
                if k in by_new:
                    r['old_value'] = by_new[k]
                    stats[f'{vol}-{year} rekeyed onto prior'] += 1

    tot_sec = sum(v for k, v in stats.items() if k.endswith('sections repaired'))
    tot_ch = sum(v for k, v in stats.items() if k.endswith('cells changed'))
    tot_dr = sum(v for k, v in stats.items() if k.endswith('cells dropped'))
    print(f'{tot_sec} slipped sections, {tot_ch} cells re-valued, {tot_dr} nulled')
    for k in sorted(stats):
        if k.endswith('sections repaired'):
            print(f'  {k:40} {stats[k]:4}')
    if not a.dry_run:
        with open(a.out, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=['volume', 'year', 'flow', 'article_group',
                                               'article', 'country_raw', 'old_value',
                                               'new_value', 'witnesses'])
            w.writeheader()
            w.writerows(repairs)
        print(f'wrote {a.out} ({len(repairs)} rows)')


if __name__ == '__main__':
    main()
