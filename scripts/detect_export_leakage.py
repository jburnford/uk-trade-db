#!/usr/bin/env python3
"""Find export tables sitting in the import payload.

The PHANTOM? adjudication (round 28) turned up 21 labels whose 'origins' are
plainly destinations of British produce - cotton yarn to Bombay/Madras/Straits,
woollens to Mexico/Peru, beer to Bermudas, machinery to British Guiana. Those
were caught by their broken labels. Nothing guarantees the same tables are not
also present under CLEAN labels, and 'Woollen And Worsted Manufactures — Broad
Cloths, Coatings, Duffs' (GBP1.0bn, measured in Yards, 'consigned' from Chile,
Gibraltar, Bombay and Australia) says they are.

Rather than hand-pick suspicious names, this scores every commodity against a
country profile learned from two sets of KNOWN export tables: the 21
adjudicated in reports/phantom_label_shift.csv, and every '— To <Place>'
label in the payload (the preposition is printed only on the export side, so
'Cotton Manufactures — To United States Of America' is self-identifying). For each country, compare how much of the
confirmed-export mass it carries against how much of the ANCHORED import mass
it carries (anchored = the commodity has a §TOTAL Tier-1 series, so it is a
real import line). Countries that are common in one and rare in the other are
the discriminator - British colonies and Latin American republics buy British
manufactures far more than they ship goods to Britain.

A commodity is a candidate when it has no Tier-1 anchor (nothing to check its
origins against) AND its country mix leans to the destination side. Output is
a ranked report for human adjudication, never an applied action: some of these
names are real import lines whose anchor is simply missing.

LIMITATION - the ranking is a screen, not a verdict, and the score should not
be read as a probability. The training set is small (44 tables) and the big
trading partners sit on both sides of the trade, so Holland/Belgium/France/
Germany carry almost no discriminating weight; what the log-odds does reward
is RARE countries, which floats obscure West African tables to the top
alongside the real exports. Genuine imports with no anchor ('Wine — Total Of
All Kinds', 'Sugar — Unrefined, Total') appear in the list and are not
leakage. Use it to find candidates, then judge each on the printed evidence:
a destination list that no importer could ship from (broadcloth 'consigned'
from Chile, Gibraltar and Bombay), export units (Yards for cloth where the
import tables use Cwt), and no §TOTAL anchor anywhere in the family.
"""
import json, sys, csv, re, collections, math

PAY = 'exports/viz_payload.json'
CONFIRMED = 'reports/phantom_label_shift.csv'
OUT = 'reports/export_leakage_candidates.csv'


def country_mass(p, names):
    """country -> number of cells, over the given commodities."""
    m = collections.Counter()
    for n in names:
        for c, byu in (p.get(n, {}).get('c') or {}).items():
            if c != '§TOTAL':
                m[c] += sum(len(s) for s in byu.values())
    return m


def main(scorepath=PAY, trainpath=None):
    # the confirmed export tables have since been DROPPED by curation, so the
    # profile is learned from a pre-curation snapshot of the payload while the
    # scoring runs on the current one:
    #   git show <pre-curation-rev>:exports/viz_payload.json > /tmp/train.json
    p = json.load(open(scorepath))
    train = json.load(open(trainpath)) if trainpath else p
    conf = [r['commodity'] for r in csv.DictReader(open(CONFIRMED))
            if r['klass'] == 'export-leakage']
    # plus every '— To <Place>' label: the preposition is printed only in the
    # export tables, so these are unambiguous training examples and they
    # survive curation, unlike the adjudicated ones
    conf += [n for n in train if re.search(r'— (\.\. )?To [A-Z]', n)]
    exp = country_mass(train, conf)
    anchored = [n for n, e in train.items() if (e.get('c') or {}).get('§TOTAL')]
    imp = country_mass(train, anchored)
    if not exp:
        print(f'none of the confirmed export tables are in {trainpath or scorepath}; '
              f'pass a pre-curation payload as the second argument')
        return
    E, I = sum(exp.values()), sum(imp.values())
    # log-odds of a country being on the destination side, smoothed
    score = {c: math.log(((exp[c] + 1) / (E + 1)) / ((imp[c] + 1) / (I + 1)))
             for c in set(exp) | set(imp)}

    rows = []
    for n, e in p.items():
        c = e.get('c') or {}
        if c.get('§TOTAL'):
            continue                     # anchored: a real import line
        cells = [(ctry, sum(len(s) for s in byu.values()))
                 for ctry, byu in c.items() if ctry != '§TOTAL']
        tot = sum(k for _, k in cells)
        if tot < 4:
            continue
        s = sum(score.get(ctry, 0) * k for ctry, k in cells) / tot
        if s <= 0:
            continue
        units = collections.Counter(u for byu in c.values() for u in byu)
        top = sorted(cells, key=lambda x: -x[1])[:5]
        rows.append(dict(commodity=n, gbp=int(e.get('v') or 0),
                         destination_score=round(s, 3), n_cells=tot,
                         unit=units.most_common(1)[0][0],
                         top_origins=' | '.join(t for t, _ in top)))
    rows.sort(key=lambda r: (-r['destination_score'], -r['gbp']))
    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f'{len(rows)} export-leakage candidates -> {OUT}')
    print(f'GBP at stake: {sum(r["gbp"] for r in rows):,}')


if __name__ == '__main__':
    main(*sys.argv[1:])
