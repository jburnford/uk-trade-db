#!/usr/bin/env python3
"""Cluster commodity labels that are OCR variants of the SAME printed line.

The dupe-cell fingerprint in curate_commodities.py only catches variants that
share printed cells. It misses the large class where two spellings of one line
carry DIFFERENT year-ranges ('Woollen ... Duffs, &C.' 1872-84 and
'... Duffels, &C.' 1885-99 never overlap, so neither looks like a dupe) - yet
they are one commodity and must be one series.

Matching a printed line across spellings needs more than string similarity:
'Petroleum — Refined' / '— Unrefined' and 'Caoutchouc — East Africa' /
'— West Africa' are >=0.93 similar as strings but are different commodities.
So the test is token-structural, not character-level: every token of one name
must pair with a token of the other under a rule that admits OCR damage and
rejects meaning changes.

  equal                       'Bark'      == 'Bark'
  near-miss (>=0.85)          'Brimston'  ~= 'Brimstone'      (dropped glyph)
  shared >=4-char prefix      'Peilts'    ~= 'Pelts'          (mangled tail)
  concatenation of 2 tokens   'Andwaste'  == 'And' + 'Waste'  (lost space)

Both fuzzy tests need tokens of >=5 characters: below that they stop being
OCR damage and start being different words ('Metal'~'Meal', 'Wool'~'Woollen',
'Rook'~'Rock'). The prefix test additionally caps the length gap at 2, or a
short word matches a long one that merely starts the same
('Manufactures'~'Manures', 'Tanning'~'Tanningunenumerated'). A concatenation must match EXACTLY, or a long merged token
swallows a short neighbour ('Sawn'+'Unenumerated' scored 0.86 against
'Unenumerated' and folded 'Wood And Timber — Sawn, Unenumerated' into the
plain '— Unenumerated' line).

  NEGATION VETO: 'Refined'/'Unrefined', 'Manufactured'/'Unmanufactured' and
  'Enumerated'/'Unenumerated' pass the >=0.85 near-miss test but invert the
  meaning, so an un-/in-/non- prefix is never a match.

Any token left unpaired on either side breaks the cluster ('East'/'West',
'Hewn'/'Sawn', 'Broad'/'Narrow', the export 'To' in 'To United States' all
survive as distinct commodities this way).

Two further restraints, both learned from what a first cut merged:

  ANCHOR RULE - a pair may use AT MOST ONE fuzzy (non-equal) token match, and
  only when some other token matches exactly. Without it the fuzzy tests eat
  short names whole: 'Ice'~'Rice', 'Wool'~'Woollen', 'Butterine'~'Butter',
  'Seeds'~'Seed'. Single-token garbles ('Liard'/'Lard', 'Ntre'/'Nitre' when
  alone) are deliberately left to the dupe-cell fingerprint in
  curate_commodities.py, which catches them from shared cells instead. The two
  tools are complementary: this one needs no cell overlap but needs a spelling
  anchor; that one needs no spelling match but needs overlapping cells.

  NO TRANSITIVE CHAINING - clusters are seeded from the heaviest member and
  admit only names matching THAT seed. Union-find let A~B~C drag unrelated
  ends together ('Iron — Unenumerated' reached 'Ore, Unenumerated' through a
  chain of 'X — Unenumerated' labels).

Canonical member = the CLEANEST spelling, not the heaviest one: the fold
merges both series either way, so the only thing the choice decides is the
name the public map prints. Cleanliness is measured against the corpus itself
- a token no other label uses ('Peilts') is damage, one many labels share
('Pelts') is the printed word - with cell count as the tiebreak. A cell-less
heading can win: it still ends up carrying the whole merged series. Output is
a fold proposal, NOT an applied action: reports/ocr_variant_clusters.csv is
reviewed by hand and the accepted rows go to reference/commodity_curation.csv.
"""
import json, sys, csv, re, math, collections, difflib

NEG = ('UN', 'IN', 'NON')


def tokens(name):
    """Tokens with hyphen-linebreaks repaired ('In- Cluding' -> 'Including')."""
    return [w for w in re.split(r'[^A-Za-z0-9]+', re.sub(r'-\s+', '', name).upper()) if w]


def tok_match(a, b):
    """0 = no match, 1 = exact, 2 = fuzzy (OCR damage)."""
    if a == b:
        return 1
    for p in NEG:                                  # negation veto
        if a == p + b or b == p + a:
            return 0
    if min(len(a), len(b)) < 5:
        return 0
    if difflib.SequenceMatcher(None, a, b).ratio() >= 0.85:
        return 2
    return 2 if a[:4] == b[:4] and abs(len(a) - len(b)) <= 2 else 0


def same_line(ta, tb):
    """True if every token pairs up, allowing 2-token concatenations (a lost
    space) and at most one fuzzy pair anchored by at least one exact pair."""
    i = j = exact = fuzzy = 0
    while i < len(ta) and j < len(tb):
        m = tok_match(ta[i], tb[j])
        if m:
            i, j = i + 1, j + 1
        elif j + 1 < len(tb) and ta[i] == tb[j] + tb[j + 1]:
            m, i, j = 1, i + 1, j + 2
        elif i + 1 < len(ta) and ta[i] + ta[i + 1] == tb[j]:
            m, i, j = 1, i + 2, j + 1
        else:
            return False
        exact, fuzzy = exact + (m == 1), fuzzy + (m == 2)
    return i == len(ta) and j == len(tb) and fuzzy <= 1 and (exact or not fuzzy)


def main(path, out='reports/ocr_variant_clusters.csv'):
    p = json.load(open(path))
    info = {}
    for n, e in p.items():
        c = e.get('c') or {}
        cells = sum(len(s) for byu in c.values() for s in byu.values())
        info[n] = dict(gbp=e.get('v') or 0, t1=int('§TOTAL' in c), cells=cells,
                       toks=tokens(n))
    # only names of comparable token count can pair up; bucket to keep the
    # pairwise sweep near-linear on the ~2,400 labels
    by_len = collections.defaultdict(list)
    for n, d in info.items():
        by_len[len(d['toks'])].append(n)

    # seed clusters from the heaviest labels down; a cluster admits only names
    # that match its SEED directly, so no chain of near-misses can link two
    # unrelated ends
    # corpus token frequencies: the spelling most labels agree on is the
    # printed one
    freq = collections.Counter(t for d in info.values() for t in set(d['toks']))
    for n, d in info.items():
        # hapax first: a token no other label uses ('Peilts', 'Processequal',
        # 'Lookingglasses') is the signature of damage, and counting them beats
        # any aggregate of frequencies - summing rewards the spelling that lost
        # a space (two cheap tokens outscore one good one), averaging rewards
        # the one that gained one.
        hapax = sum(1 for t in set(d['toks']) if freq[t] < 2)
        # display damage the token repair hides: stray brace/quote, a lone
        # dash, and the hyphen-linebreak itself ('Re-Manu- Factured')
        junk = len(re.findall(r'[{}"|~]|(?<= )-(?= )|\w-\s+\w', n))
        d['clean'] = (-hapax, -junk,
                      sum(math.log1p(freq[t]) for t in d['toks'] if len(t) > 2))
    order = sorted(info, key=lambda n: (-info[n]['cells'], -info[n]['gbp'], n))
    taken, clusters = set(), []
    for seed in order:
        if seed in taken:
            continue
        k = len(info[seed]['toks'])
        pool = by_len[k] + by_len.get(k - 1, []) + by_len.get(k + 1, [])
        members = [seed] + [n for n in pool if n not in taken and n != seed
                            and same_line(info[seed]['toks'], info[n]['toks'])]
        taken.update(members)
        if len(members) > 1:
            members.sort(key=lambda n: (tuple(-x for x in info[n]['clean']),
                                        -info[n]['cells']))
            clusters.append(members)

    rows = []
    for members in clusters:
        canon = members[0]
        for m in members[1:]:
            rows.append(dict(commodity=m, action='fold', target=canon,
                             gbp=info[m]['gbp'], cells=info[m]['cells'],
                             t1=info[m]['t1'], target_gbp=info[canon]['gbp'],
                             target_cells=info[canon]['cells'],
                             target_t1=info[canon]['t1'],
                             cluster_size=len(members)))
    rows.sort(key=lambda r: -r['gbp'])
    cols = ['commodity', 'action', 'target', 'gbp', 'cells', 't1', 'target_gbp',
            'target_cells', 'target_t1', 'cluster_size']
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)                    # empty once the folds are applied
    n_cl = len(clusters)
    print(f'{n_cl} clusters, {len(rows)} fold proposals -> {out}')
    print(f'GBP on the folded side: {sum(r["gbp"] for r in rows):,}')


if __name__ == '__main__':
    main(*sys.argv[1:])
