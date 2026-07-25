#!/usr/bin/env python3
"""Find commodities printed under two labels, one holding the origins and the
other the national total.

The teak case is the pattern: `Wood And Timber — Hewn, Teak` carried origins
1873-99 and no anchor, `Wood And Timber — Teak` carried the 1893-1900 Tier-1
anchor and origins only to 1893. Each half looked like a different defect; they
are one commodity under two era labels, and folding them makes the origins
track the independently printed national total at 1.00.

`build_map_slim.py` already names the symptom — the `nooverlap` flag, raised
when a commodity has BOTH an anchor and origins but no single year carries
both, so nothing has ever been checked against anything. This script takes
each such commodity and looks for the label holding the missing half.

A candidate must:
  * share the commodity's distinguishing name tokens (the head or the article),
  * supply the years the flagged label lacks, without contradicting the years
    it has (an overlap where both print a national total must AGREE),
  * measure in the same unit.

The proof is the same self-validating test teak passed: merge the two, then
compare summed origins against the Tier-1 anchor year by year. If the ratio
sits at 1.0 the two halves are one commodity, because the origin tables and the
national total were printed on different pages and are independent witnesses.
A merge that lands at 2.0 or 0.3 is two different things and is rejected.

Writes reports/split_commodity_candidates.csv. Nothing is folded automatically:
the ratio evidence goes in the CSV and the adjudication is a human call
recorded in reference/commodity_curation.csv.
"""
import json, csv, re, collections
from pathlib import Path

m = json.load(open('exports/map_data.json'))
cur = list(csv.DictReader(open('reference/commodity_curation.csv')))
# already-adjudicated labels: folded/dropped ones no longer exist as separate
# commodities downstream, so they are neither flagged nor offered as partners.
resolved = {r['commodity'] for r in cur if r['action'] in ('fold', 'drop')}
qrows = list(csv.DictReader(open('reports/commodity_curation_queue.csv')))
bucket = {r['commodity']: r['bucket'] for r in qrows}


def halves(name):
    """(anchor years by unit, origin years by unit, origin qty by (unit, year))."""
    e = m.get(name)
    if not e:
        return {}, {}, {}
    anc = collections.defaultdict(dict)
    for u, ser in e['c'].get('§TOTAL', {}).items():
        if u == 'Value':
            continue
        for cell in ser:
            anc[u][cell[0]] = anc[u].get(cell[0], 0) + cell[1]
    org = collections.defaultdict(dict)
    for c, byu in e['c'].items():
        if c == '§TOTAL':
            continue
        for u, ser in byu.items():
            for cell in ser:
                org[u][cell[0]] = org[u].get(cell[0], 0) + cell[1]
    return dict(anc), dict(org), e['v']


def dominant(d):
    """The unit carrying the most years, preferring a labelled one."""
    return max(d, key=lambda u: (u != '?', len(d[u]))) if d else None


STOP = {'and', 'or', 'of', 'the', 'for', 'in', 'other', 'all', 'not', 'sorts',
        'kinds', 'unenumerated', 'total', 'manufactures', 'raw', 'sundry'}


def toks(name):
    return {t for t in re.split(r'[^a-z0-9]+', name.lower())
            if len(t) > 2 and t not in STOP}


def head(name):
    """Text before the em-dash/colon separator - the printed family line."""
    return re.split(r'\s*[—:·]\s*', name)[0].strip().lower()


def headtoks(name):
    return toks(head(name))


# document frequency of every token, so 'timber' can be told from 'teak'
DF = collections.Counter()
for n in m:
    for t in toks(n):
        DF[t] += 1

rows = []
allnames = [n for n in m if n not in resolved]
tokcache = {n: toks(n) for n in allnames}
headcache = {n: head(n) for n in allnames}
headtokcache = {n: headtoks(n) for n in allnames}

for n in allnames:
    anc, org, gbp = halves(n)
    ou = dominant(org)
    if not ou:
        continue
    ay, oy = set(anc.get(ou, {})), set(org.get(ou, {}))
    if not oy or (ay & oy):
        continue     # no origins at all, or already checkable: not a split
    # what is left is every commodity whose origins have never been measured
    # against a national total - `nooverlap` (an anchor exists but in other
    # years) and `noanchor` (none printed under this label at all). Teak's
    # origin half was the second kind.
    mine = tokcache[n]
    for p in allnames:
        if p == n or not (tokcache[p] & mine):
            continue
        # The shared tokens must name the same GOODS, not merely a shared
        # modifier. Rarity alone is not enough: 'Pork — Salted' and 'Beef —
        # Salted' share a rare token and a plausible ratio, and are two animals.
        # Accept only when the two labels are plainly the same printed line seen
        # at different depths:
        #   * the same printed head ('Wood And Timber — Hewn, Oak' / '— Oak'),
        #   * one label's words contained in the other's ('Wine' / 'Wine —
        #     Total Of All Kinds' — the shorter is the family line), or
        #   * a shared token that heads one of them, which is how a de-headed
        #     fragment attaches ('Metals And Ores — Pig' / 'Pig And Puddled').
        shared = tokcache[p] & mine
        if not (headcache[p] == headcache[n]
                or tokcache[p] <= mine or mine <= tokcache[p]
                or shared & headtokcache[p] or shared & headtokcache[n]):
            continue
        panc, porg, pgbp = halves(p)
        # Everything is measured in the origins' unit `ou`: the test compares
        # summed origins against the national total, so a partner series in a
        # different unit is not evidence about this commodity at all.
        gain_anchor = bool(set(panc.get(ou, {})) & oy)
        gain_origin = bool(set(porg.get(ou, {})) & ay)
        if not (gain_anchor or gain_origin):
            continue
        # ---- the test: does the merged commodity check out against itself? --
        mo = dict(org.get(ou, {}))
        for y, q in porg.get(ou, {}).items():
            mo[y] = mo.get(y, 0) + q
        ma = dict(anc.get(ou, {}))
        conflict = 0
        for y, q in panc.get(ou, {}).items():
            if y in ma and ma[y] and abs(ma[y] - q) / max(ma[y], q) > 0.02:
                conflict += 1        # both print a national total and disagree
            ma[y] = max(ma.get(y, 0), q)
        # Only years THIS commodity's unmeasured half reaches are evidence. A
        # year carried entirely by the partner measures the partner against
        # itself and always reads 1.0: 'Sugar — Unrefined, Total' scored a
        # perfect median against 'Sugar — Molasses' on sixteen such years,
        # while the five years that actually touched its own origins ran to 60.
        test = [y for y in ma if ma[y] and mo.get(y) and (y in oy or y in ay)]
        if not test:
            continue
        rr = sorted(mo[y] / ma[y] for y in test)
        med = rr[len(rr) // 2]
        near = sum(1 for x in rr if 0.9 <= x <= 1.1) / len(rr)
        rows.append({
            'commodity': n, 'gbp': round(gbp), 'bucket': bucket.get(n, ''),
            'partner': p, 'partner_gbp': round(pgbp),
            'partner_bucket': bucket.get(p, ''),
            'unit': ou, 'holds': 'anchor' if gain_anchor else 'origins',
            'shared_tokens': ' '.join(sorted(shared)),
            # Two labels whose ORIGIN tables cover the same years are rival
            # copies of one table, not the two halves of a split line - a
            # different defect (the dupe fingerprint's business), so say which.
            'origin_years_shared': len(set(porg.get(ou, {})) & oy),
            'own_origin_years': f'{min(oy)}-{max(oy)}',
            'own_anchor_years': f'{min(ay)}-{max(ay)}' if ay else 'none',
            'merged_checked_years': len(rr),
            'ratio_median': round(med, 3),
            'ratio_range': f'{round(rr[0], 2)}-{round(rr[-1], 2)}',
            'pct_near_1': round(near, 2),
            'anchor_conflicts': conflict,
            # A good merge is right in MOST years, not on average: a median of
            # 1.0 over a range of 0.3-4 is two series crossing, not one.
            'verdict': ('CONFIRMS' if 0.9 <= med <= 1.1 and near >= 0.6
                        and not conflict else
                        'partial' if 0.75 <= med <= 1.3 and not conflict else
                        'rejects'),
        })

# document frequency of every token, so 'timber' can be told from 'teak'
DF = collections.Counter()
for n in m:
    for t in toks(n):
        DF[t] += 1

if __name__ == '__main__':
    rows.sort(key=lambda r: (r['verdict'] != 'CONFIRMS', -r['gbp']))
    fn = list(rows[0].keys()) if rows else []
    with open('reports/split_commodity_candidates.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fn)
        w.writeheader()
        w.writerows(rows)
    print(f'{len(rows)} candidate pairs')
    for v in ('CONFIRMS', 'partial', 'rejects'):
        print(f'  {v}: {sum(1 for r in rows if r["verdict"] == v)}')
