#!/usr/bin/env python3
"""Printed arithmetic identities: a parent line and the sub-sorts that sum to it.

Every closure test in this project measures one commodity-year against its own
printed national total, so a commodity-year with no anchor is never checked at
all. `reconcile_baseline.py` scores 9,935 commodity-years and skips the rest;
the map writes `noanchor` and moves on. But the volumes routinely print BOTH a
parent line and its sub-sorts, and where they do, the sub-sorts constrain each
other whether or not any of them carries an anchor:

    beetroot + cane and other sorts   =  sugar, unrefined, total
    bacon + hams                      =  bacon and hams
    oxen and bulls + cows + calves    =  oxen, bulls, cows, and calves

That test is STRICTLY STRONGER than an anchor where both exist, because it
constrains two or more series at once and says WHICH of them is short. Three
sessions found defects this way by hand -- eleven wrong years in sugar 1882-99,
twenty-three destroyed ham tables, four missing cow tables -- every one of them
inside years the flags called `noanchor`. This makes it a pass.

## Finding the identities without fitting them

The guardrail is that a subset-sum reached by trying combinations is
coincidence, not proof. So candidate families come from the PRINTED TAXONOMY --
from the labels -- and arithmetic only ever confirms or refutes them.

  Rule TOTAL   the parent's label says so ('... Total', '... of all kinds')
               and the children are its siblings under the same head, carrying
               its qualifier ('Unrefined, Total' governs 'Unrefined : Beetroot'
               and 'Unrefined : Cane', not the refined half).
  Rule UNION   the parent's name is the CONCATENATION of its children's
               ('Bacon and Hams' = 'Bacon' + 'Hams'; 'Oxen, Bulls, Cows, and
               Calves' = 'Oxen and Bulls' + 'Cows' + 'Calves'). Requires the
               children's vocabularies to be pairwise disjoint and to cover the
               parent's exactly, which is a very tight constraint on names.
  Rule HEAD    the group head is itself a commodity ('Cheese' beside
               'Cheese — ...'), which in this corpus usually means the volumes
               printed the family line and its sub-sorts under one heading.
  Rule SEARCH  the fallback, and the only one that looks at combinations. Run
               for every TOTAL and HEAD parent, because the named set is often
               untestable -- one sub-sort has no table in the years the others
               do -- while the identity still holds over the rest. Bounded
               hard: at most eight candidate siblings, ONE surviving family per
               parent (the subset closing in the most years), and three closing
               years demanded instead of two. A subset-sum found by trying
               combinations is coincidence until it repeats. Reported under its
               own rule name so a reader always knows which families were read
               off the printed labels and which were searched for.

A family is ACCEPTED only if the identity closes within 0.1% in at least two
years (three for SEARCH) on some measure. Everything else is discarded
unreported -- a family that never closes was never an identity.

Names are compared on the ARTICLE, not the whole label: the group head is a
section heading the children often do not repeat ('Animals, Living — Bulls,
Oxen, Cows, and Calves' = 'Oxen and Bulls' + 'Cows' + 'Calves', where only the
parent kept the head).

## What it reports

For each accepted family, per year, both sides of the identity on both
measures:

    anchors  parent T1        vs  sum of children T1
    origins  parent origins   vs  sum of children origins

and the cross-check that has no anchor in it at all -- children's origins
against the parent's printed total.

Both sides' OWN closure is carried beside the identity (`parent_ratio`,
`children_ratio`), because the two failure modes look identical otherwise. If
the children overshoot the parent's printed total AND the parent's own origin
table overshoots it by the same margin, the family is double-counting a
drill-down beside its parent country -- a known class the map de-duplicates and
`detect_origin_overcount.py` already owns. If the parent closes on its anchor
and the children do not, the identity has found something new. Sugar unrefined
1895 is the first kind (parent 1.36 of its own anchor); woollen yarn 1874 is
the second.

Source of truth is `exports/viz_payload.json`, the same pre-de-duplication view
`reconcile_baseline.py` scores, NOT the map's de-duplicated `map_slim.json`.

    python3 scripts/sibling_identity.py [--min-gbp N]

  -> reports/sibling_identity.csv     one row per family-year
  -> reports/sibling_families.csv     one row per family, with its scorecard
"""
import collections
import csv
import itertools
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CLOSE = 0.001          # "closes": within 0.1%, the baseline's exact01 bucket
LOOSE = 0.01           # "near": within 1%

# Words that make a label a TOTAL rather than a member of the family.
TOTAL_WORDS = {'TOTAL', 'TOTALS'}
ALLKINDS = (('ALL', 'KINDS'), ('ALL', 'SORTS'), ('EVERY', 'SORT'))
# Vocabulary that carries no commodity meaning, so it cannot make two labels
# "different lines" under rule UNION and must not be required to match.
FILLER = {'AND', 'OR', 'OF', 'THE', 'IN', 'FOR', 'NOT', 'OTHER', 'SORTS',
          'KINDS', 'ALL', 'TOTAL', 'UNENUMERATED', 'INCLUDING', 'VIZ',
          'EXCEPT', 'THAN', 'BY', 'ANY', 'FROM', 'TO', 'ON', 'AS', 'WITH'}


def toks(s):
    out = set()
    for t in re.split(r'[^A-Za-z0-9]+', s or ''):
        t = t.upper()
        if len(t) > 1:
            out.add(t)
    return out


def head_of(name):
    """The printed group head, i.e. everything left of the em-dash separator."""
    return name.split(' — ')[0].strip() if ' — ' in name else ''


def article_of(name):
    return name.split(' — ')[-1].strip()


def vocab(name):
    """The tokens that identify the LINE, not the section it is printed under.

    Comparing whole labels would demand that every child repeat the parent's
    group head, which the volumes do not do -- 'Cows' and 'Calves' are printed
    groupless while their parent kept 'Animals, Living'."""
    return toks(article_of(name)) - FILLER


def is_total_label(name):
    """'Wine — Total of all kinds' is a family total. 'Silk Manufactures —
    Ribbons of all kinds' is NOT: 'of all kinds' there qualifies the ribbons,
    not the family. The test is whether anything is left of the article once
    the total-vocabulary and the head's own words are removed."""
    t = toks(article_of(name))
    if t & TOTAL_WORDS:
        return True
    if any(set(k) <= t for k in ALLKINDS):
        rest = t - {'ALL', 'KINDS', 'SORTS', 'EVERY', 'SORT'} - FILLER
        return rest <= toks(head_of(name))
    return False


def is_exclusion_label(name):
    """'Salted (other than Bacon and Hams)' names what it LEAVES OUT, so its
    vocabulary is the union of things that are not its parts. Never a union
    parent."""
    return re.search(r'\b(other than|except|not being|excluding)\b',
                     name, re.I) is not None


# --------------------------------------------------------------- payload side
def modal_unit(t1):
    units = {u: len([r for r in v if r[1]]) for u, v in (t1 or {}).items()}
    units = {u: n for u, n in units.items() if n}
    return max(units, key=units.get) if units else None


def series(entry):
    """(unit, {year: t1}, {year: origin_sum}) for one payload commodity.

    The origin side excludes '§TOTAL' and parenthesised drill-downs, exactly as
    reconcile_baseline.py does, so the two agree about what an origin sum is."""
    c = entry.get('c') or {}
    unit = modal_unit(c.get('§TOTAL')) or modal_unit(
        {u: rows for cty, byu in c.items() if cty != '§TOTAL'
         for u, rows in byu.items()})
    if not unit:
        return None, {}, {}
    t1 = {r[0]: r[1] for r in (c.get('§TOTAL') or {}).get(unit, ()) if r[1]}
    orig = collections.Counter()
    for cty, byu in c.items():
        if cty == '§TOTAL' or '(' in cty:
            continue
        for r in byu.get(unit, ()):
            if r[1]:
                orig[r[0]] += r[1]
    return unit, t1, dict(orig)


# ------------------------------------------------------------ family proposal
MAX_SEARCH_SIBLINGS = 8


def propose(names_by_unit, voc):
    """Yield (rule, parent, [children]) candidates from the LABELS alone."""
    for unit, names in names_by_unit.items():
        byhead = collections.defaultdict(list)
        for n in names:
            byhead[head_of(n)].append(n)

        # ---- rules TOTAL / HEAD / SEARCH: a parent and its siblings
        for head, members in byhead.items():
            if not head:
                continue
            totals = [m for m in members if is_total_label(m)]
            # the head printed as a commodity in its own right is a parent
            # candidate too -- 'Cheese' beside 'Cheese — ...'
            if head in names and head not in totals and len(members) >= 2:
                totals = totals + [head]
            kids = [m for m in members if not is_total_label(m) and m != head]
            if len(kids) < 2:
                continue
            for p in totals:
                need = toks(article_of(p)) - TOTAL_WORDS - FILLER
                sel = [k for k in kids if need <= toks(k)]
                if len(sel) >= 2:
                    yield ('HEAD' if p == head else 'TOTAL'), p, sel
                # ---- rule SEARCH: the bounded fallback, tried for every
                # parent -- the named set is often untestable because ONE
                # sub-sort has no table in the years the others do, and the
                # identity still holds over the rest. Bounded to a handful of
                # siblings so this is a short list of tries rather than a
                # fishing expedition; the extra closing year demanded
                # downstream is what keeps a coincidence out.
                if 2 <= len(kids) <= MAX_SEARCH_SIBLINGS:
                    for r in range(2, len(kids) + 1):
                        for combo in itertools.combinations(sorted(kids), r):
                            yield 'SEARCH', p, list(combo)

        # ---- rule UNION: the parent's name IS its children's, concatenated
        for p in names:
            if is_exclusion_label(p):
                continue
            pv = voc[p]
            if len(pv) < 2:
                continue
            cands = [n for n in names if n != p and voc[n] and voc[n] < pv]
            # greedy exact cover by pairwise-disjoint children, largest first
            sel, covered = [], set()
            for n in sorted(cands, key=lambda n: (-len(voc[n]), n)):
                if voc[n] & covered:
                    continue
                sel.append(n)
                covered |= voc[n]
            if len(sel) >= 2 and covered == pv:
                yield 'UNION', p, sel


# ------------------------------------------------------------------------ run
def main():
    mingbp = 0
    if '--min-gbp' in sys.argv:
        mingbp = float(sys.argv[sys.argv.index('--min-gbp') + 1])

    payload = json.load(open(BASE / 'exports' / 'viz_payload.json'))
    ser, gbp = {}, {}
    for name, entry in payload.items():
        unit, t1, orig = series(entry)
        if unit and (t1 or orig):
            ser[name] = (unit, t1, orig)
            gbp[name] = float(entry.get('v') or 0)

    voc = {n: vocab(n) for n in ser}
    names_by_unit = collections.defaultdict(list)
    for n, (u, _, _) in ser.items():
        names_by_unit[u].append(n)

    seen, families, best_search = set(), [], {}
    for rule, parent, kids in propose(names_by_unit, voc):
        key = (parent, tuple(sorted(kids)))
        if key in seen:
            continue
        seen.add(key)
        pu, pt1, porig = ser[parent]
        years = sorted(set(pt1) | set(porig)
                       | {y for k in kids for y in ser[k][1]}
                       | {y for k in kids for y in ser[k][2]})
        rows, nclose = [], collections.Counter()
        for y in years:
            kt1 = sum(ser[k][1].get(y, 0) for k in kids)
            kor = sum(ser[k][2].get(y, 0) for k in kids)
            nk_t1 = sum(1 for k in kids if ser[k][1].get(y))
            nk_or = sum(1 for k in kids if ser[k][2].get(y))
            row = {'rule': rule, 'parent': parent, 'unit': pu, 'year': y,
                   'n_children': len(kids),
                   'parent_t1': pt1.get(y, ''), 'children_t1': kt1 or '',
                   'parent_origins': porig.get(y, ''), 'children_origins': kor or '',
                   'n_children_t1': nk_t1, 'n_children_origins': nk_or}
            for tag, a, b in (('anchor', pt1.get(y), kt1 if nk_t1 == len(kids) else 0),
                              ('origin', porig.get(y), kor if nk_or == len(kids) else 0),
                              # the test with no anchor on the child side and
                              # no origin table on the parent's: the printed
                              # parent total against the children's origins
                              ('cross', pt1.get(y), kor if nk_or == len(kids) else 0)):
                r = (b / a) if (a and b) else ''
                row[f'{tag}_ratio'] = f'{r:.4f}' if r else ''
                if r and abs(r - 1) <= CLOSE:
                    nclose[tag] += 1
            pr = (porig.get(y, 0) / pt1[y]) if pt1.get(y) and porig.get(y) else ''
            cr = (kor / kt1) if (kt1 and kor and nk_or == len(kids)
                                 and nk_t1 == len(kids)) else ''
            row['parent_ratio'] = f'{pr:.4f}' if pr else ''
            row['children_ratio'] = f'{cr:.4f}' if cr else ''
            rows.append(row)
        # ACCEPT only if the identity actually closes somewhere, twice --
        # three times for a family found by trying combinations rather than
        # read off the printed labels.
        if max(nclose.values() or [0]) < (3 if rule == 'SEARCH' else 2):
            continue
        fam_gbp = gbp.get(parent, 0) + sum(gbp.get(k, 0) for k in kids)
        if fam_gbp < mingbp:
            continue
        rec = (fam_gbp, rule, parent, kids, rows, nclose)
        if rule in ('SEARCH', 'HEAD'):
            # 247 subsets of eight siblings will throw up a coincidence sooner
            # or later, so a searched parent gets exactly ONE family: the
            # subset that closes in the most years, then the largest. Ties are
            # broken toward more children because a sub-sort left out of the
            # sum is the commoner error.
            score = (max(nclose.values()), len(kids))
            cur = best_search.get((rule, parent))
            if cur is None or score > cur[0]:
                best_search[(rule, parent)] = (score, rec)
        else:
            families.append(rec)
    families.extend(rec for _, rec in best_search.values())

    families.sort(key=lambda f: -f[0])

    # ---- outputs
    # Scored per MEASURE, not pooled. `cross` -- the children's origin tables
    # against the parent's printed national total -- is the one that carries
    # new information, because it is available to families where no sub-sort
    # has an anchor of its own, which is exactly the population every other
    # test in this project skips.
    MEAS = ('anchor', 'origin', 'cross')
    fcols = (['gbp', 'rule', 'parent', 'children', 'unit']
             + [f'{m}_{s}' for m in MEAS for s in ('years', 'close', 'off1pct')]
             + ['worst_ratio', 'worst_year', 'worst_measure',
                'worst_parent_ratio'])
    frows, allrows = [], []
    for fam_gbp, rule, parent, kids, rows, nclose in families:
        allrows.extend(rows)
        rec = {'gbp': f'{fam_gbp:.0f}', 'rule': rule, 'parent': parent,
               'children': ' + '.join(kids), 'unit': rows[0]['unit']}
        worst = (1.0, '', '')
        for m in MEAS:
            vals = [(float(r[f'{m}_ratio']), r['year'])
                    for r in rows if r[f'{m}_ratio']]
            rec[f'{m}_years'] = len(vals)
            rec[f'{m}_close'] = nclose[m]
            rec[f'{m}_off1pct'] = sum(1 for v, _ in vals if abs(v - 1) > LOOSE)
            for v, y in vals:
                if abs(v - 1) > abs(worst[0] - 1):
                    worst = (v, y, m)
        rec['worst_ratio'] = f'{worst[0]:.4f}' if worst[1] else ''
        rec['worst_year'], rec['worst_measure'] = worst[1], worst[2]
        rec['worst_parent_ratio'] = next(
            (r['parent_ratio'] for r in rows if r['year'] == worst[1]), '')
        frows.append(rec)

    out1 = BASE / 'reports' / 'sibling_families.csv'
    with open(out1, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fcols)
        w.writeheader()
        w.writerows(frows)
    out2 = BASE / 'reports' / 'sibling_identity.csv'
    cols = ['rule', 'parent', 'unit', 'year', 'n_children', 'parent_t1',
            'children_t1', 'parent_origins', 'children_origins',
            'n_children_t1', 'n_children_origins',
            'anchor_ratio', 'origin_ratio', 'cross_ratio',
            'parent_ratio', 'children_ratio']
    with open(out2, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(allrows)

    byrule = collections.Counter(f[1] for f in families)
    print(f'{len(families)} confirmed printed identities  '
          + '  '.join(f'{r}:{n}' for r, n in sorted(byrule.items())))
    print(f'family-years written: {len(allrows)}')
    def noff(r):
        return sum(int(r[f'{m}_off1pct']) for m in MEAS)
    bad = sorted((r for r in frows if noff(r)), key=lambda r: -float(r['gbp']))
    tot_years = sum(int(r[f'{m}_years']) for r in frows for m in MEAS)
    print(f'family-year tests: {tot_years} '
          f'(anchor {sum(int(r["anchor_years"]) for r in frows)}, '
          f'origin {sum(int(r["origin_years"]) for r in frows)}, '
          f'cross {sum(int(r["cross_years"]) for r in frows)})')
    print(f'\nfamilies with at least one year off by more than 1%: {len(bad)}')
    for r in bad[:25]:
        det = '  '.join(f'{m} {r[f"{m}_off1pct"]}/{r[f"{m}_years"]}'
                        for m in MEAS if int(r[f'{m}_years']))
        pr = r['worst_parent_ratio']
        print(f"  GBP{float(r['gbp']):>14,.0f}  off: {det}   worst "
              f"{r['worst_ratio']} in {r['worst_year']} ({r['worst_measure']})"
              + (f"  [parent itself {pr} of its anchor -> over-count, not the "
                 f"identity]" if pr and abs(float(pr) - 1) > LOOSE else '')
              + f"\n      {r['parent']}")
        print(f"      = {r['children']}")
    print(f'\n-> {out1}\n-> {out2}')


if __name__ == '__main__':
    main()
