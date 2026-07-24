#!/usr/bin/env python3
"""Find commodities whose 'country' column is actually a list of commodities.

Some pages are not origin tables at all - they are commodity summaries, one
line per article. When one is parsed as an origin table the article names land
in the country column, so the entry looks like a commodity with a rich set of
origins and is in fact a whole table read sideways:

  Silk — Skins        'origins': Sheep And Lamb Number, Sheep And Lambs Number
  Wine — Provisions   'origins': Beef Salted And Fresh, Pork Salted And Fresh
  Tobacco — Wood      'origins': Hewn Of All Sorts, Sawn Of All Sorts, Staves
  Woollen             'origins': Yarn Of All Kinds, Yeast, Rags Not For Manure

The test is what the labels ARE, not whether they can be placed on a map: a
label is place-like when it is used as a country by at least five different
commodities, and commodity-like when it either carries a UNIT word - no
country is called 'Roots And Shoes Doz Pairs' or 'Manganese Ore Of Tons' - or
its tokens, once unit words are stripped, are those of a commodity name or the
article of one, or a subset of them ('Hewn Of All Sorts' sits inside 'Wood And
Timber — Hewn Of All Sorts'). An entry whose labels are commodity-like and
never place-like is a transposed table.

That distinction matters, because "no mappable origin" alone does not mean
junk. Plenty of real commodities publish nothing but 'Other Countries' or 'All
Countries' - unmappable, but true. Those must be kept and explained, not
dropped.

Output is a candidate list for adjudication. The rows are worth recovering at
source: a transposed table is a national commodity summary, which is data we
want, just not as origins.
"""
import json, sys, csv, re, collections

PAY = 'exports/viz_payload.json'
OUT = 'reports/transposed_tables.csv'
MIN_LABELS = 3            # below this there is not enough evidence either way


UNITW = re.compile(r'\b(lbs?|cwts?|cuts?|tons?|tuns?|gallons?|bushels?|numbers?'
                   r'|yards?|loads?|quarters?|pairs?|prs|doz|dozen|carats?'
                   r'|centals?|packages?|barrels?|proof)\b', re.I)


def toks(s):
    return frozenset(w for w in re.split(r'[^A-Za-z0-9]+', s.upper())
                     if len(w) > 2 and w not in
                     ('AND', 'THE', 'FOR', 'NOT', 'ALL', 'ANY', 'OF', 'OR', 'IN'))


def main(path=PAY, out=OUT):
    p = json.load(open(path))
    freq = collections.Counter()
    for e in p.values():
        for c in (e.get('c') or {}):
            if c != '§TOTAL':
                freq[c] += 1
    place_like = {c for c, k in freq.items() if k >= 5}

    # vocabulary of commodity text: full names and the article half of each
    com_vocab = set()
    for n in p:
        t = toks(n)
        if t:
            com_vocab.add(t)
        m = re.match(r'^(.*?) — (.+)$', n)
        if m and toks(m.group(2)):
            com_vocab.add(toks(m.group(2)))

    def commodity_like(c):
        if UNITW.search(c):
            return True                       # no country carries a unit word
        t = toks(UNITW.sub('', c))
        if not t:
            return False
        return t in com_vocab or any(t < v for v in com_vocab)

    rows = []
    for n, e in p.items():
        labs = [c for c in (e.get('c') or {}) if c != '§TOTAL']
        if len(labs) < MIN_LABELS:
            continue
        pl = [c for c in labs if c in place_like]
        cl = [c for c in labs if commodity_like(c)]
        # a stray real country among 39 commodity lines does not make the page
        # an origin table ('Leather Manufactures' has exactly one), so allow a
        # tenth of the labels to be place-like when the rest are commodities
        if len(pl) > len(labs) * 0.1 or len(cl) < len(labs) * 0.6:
            continue
        rows.append(dict(commodity=n, gbp=int(e.get('v') or 0), n_labels=len(labs),
                         commodity_like=len(cl), place_like=len(pl),
                         has_t1=int(bool((e.get('c') or {}).get('§TOTAL'))),
                         sample=' | '.join(cl[:4])))
    rows.sort(key=lambda r: -r['gbp'])
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['commodity', 'gbp', 'n_labels',
                                          'commodity_like', 'place_like',
                                          'has_t1', 'sample'])
        w.writeheader()
        w.writerows(rows)
    print(f'{len(rows)} transposed-table candidates -> {out}')
    print(f'GBP misfiled as origins: {sum(r["gbp"] for r in rows):,}')
    for r in rows[:15]:
        print(f'  {r["gbp"]:>12,}  {r["commodity_like"]}/{r["n_labels"]} '
              f'{"T1" if r["has_t1"] else "  "}  '
              f'{r["commodity"][:34]:34s} {r["sample"][:46]}')


if __name__ == '__main__':
    main(*sys.argv[1:])
