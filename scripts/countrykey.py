#!/usr/bin/env python3
"""One country canonicaliser, applied identically to both sides of a comparison.

The repo already had three country vocabularies -- validate_gold.py::cnorm,
reference/country_standardize.csv, and the private ALIAS dict inside
build_map_slim.py -- and a gold comparison that used any one of them lost
cells to nothing worse than spelling. Against the E&H gold, 27% of tallow
country-year cells failed to match on label form alone while 96% of the cells
that DID match agreed to the digit. That is not missing data, it is missing
matches, and it is what this module exists to stop.

Three things have to happen before two country vectors can be compared:

  1. NORMALISE the string (case, accents, punctuation, the trailing spaces the
     gold ships on 'Other Foreign Countries ').
  2. RESOLVE it to a canonical id, collapsing the three surface forms the same
     place takes -- 'Australasia : Victoria' (country_year_final),
     'Australasia Victoria' (gold), and bare 'Victoria' (map payload).
  3. ROLL UP to the coarsest partition BOTH sides can express THAT YEAR. The
     gold names 'Australasia' as one line in 1890 and its six colonies in 1895;
     our corpus does the opposite in other years. Comparing leaf to leaf loses
     every such cell.

The hierarchy is read from reference/map_gazetteer.json (the tree the map
already ships) plus reference/gold_country_crosswalk.csv for the edges the
gazetteer lacks. Exceptions live in the crosswalk, not in code, so they can be
reviewed as data.

Deliberately NOT handled here: the parent/child double count WITHIN one side
(a printed table carrying both 'Australasia' and its colonies, which sums to
2x). That is resolved upstream by build_map_slim.py's anchor-scored dedup and
published per cell in exports/_origin_dedup.csv. Re-deriving it here would be
a second implementation of a hard rule, free to drift from the one that ships.
"""
import csv
import json
import re
import unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GAZ = BASE / 'reference' / 'map_gazetteer.json'
CROSSWALK = BASE / 'reference' / 'gold_country_crosswalk.csv'
STANDARDIZE = BASE / 'reference' / 'country_standardize.csv'

RESIDUAL = '§RESIDUAL'
DROP = '§DROP'


def prenorm(s):
    """NFKD -> ASCII, lowercase, & -> and, non-alphanumeric -> space, strip.

    Matches build_dimensions.py::norm, plus the strip() the gold needs.
    """
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode()
    s = s.lower().replace('&', ' and ')
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def _titlecase(s):
    return ' '.join(w.capitalize() for w in s.split())


class CountryKey:
    def __init__(self):
        gaz = json.loads(GAZ.read_text())
        self.gaz = gaz
        # canonical id -> parent id, single-valued. The gazetteer's `children`
        # lists and `parent` pointers disagree in one place: 'Australia' lists
        # the six colonies as children while each colony's own parent points at
        # 'Australasia'. A walk to the root has to be single-valued, so the
        # parent pointers win and Australia is treated as an aggregate sitting
        # under Australasia beside them.
        self.parent = {}
        for k, v in gaz.items():
            if v.get('parent'):
                self.parent[k] = v['parent']
        self.parent.setdefault('Australia', 'Australasia')

        # label -> canonical id. Built widest-first so the crosswalk wins.
        self.alias = {}
        self.level = {}
        self.note = {}
        for r in csv.DictReader(open(STANDARDIZE)):
            src, std = prenorm(r['source_label']), (r['standard_country'] or '').strip()
            if not src or not std or std == 'DROP':
                continue
            # summed_subregion rows are a ROLL-UP, not a synonym: that file
            # folds 'victoria' and 'new south wales' into 'Australasia' on
            # purpose, because it was built for a coarser question. Taking
            # them as aliases destroys the leaf level and makes every colony
            # compare as its parent. The roll-up they encode is already in the
            # tree as parent edges, applied per year where both sides need it.
            if (r.get('summed_subregion') or '').strip().lower() == 'yes':
                continue
            self.alias.setdefault(src, std)
        for r in csv.DictReader(open(CROSSWALK)):
            src = prenorm(r['source_label'])
            if not src:
                continue
            self.alias[src] = r['country_id'].strip()      # crosswalk overrides
            self.level[src] = (r['level'] or '').strip()
            self.note[src] = (r['note'] or '').strip()
            if r.get('parent_id', '').strip():
                self.parent[r['country_id'].strip()] = r['parent_id'].strip()

        # the known-parent set used to split glued 'Parent Child' labels
        self._parents = {prenorm(p): p for p in set(self.parent.values())}
        self._children = {}
        for c, p in self.parent.items():
            self._children.setdefault(p, set()).add(c)

    # -- resolution ---------------------------------------------------------
    def _split_hierarchy(self, s):
        """'Parent : Child' / 'Parent (Child)' / glued 'Parent Child' -> child.

        The glued form is the risky one, so it splits only when the remainder
        is itself a declared child of that parent. Without that guard
        'united states of colombia' splits on 'united states' and becomes a US
        port; with it, 'of colombia' is no child of the United States and the
        string stays whole.
        """
        if ' : ' in s:
            return s.split(' : ')[-1].strip()
        m = re.match(r'^(.*?)\s*\((.+?)\)?$', s)
        if m and m.group(2):
            return m.group(2).strip()
        for pre, parent in self._parents.items():
            if s.startswith(pre + ' ') and len(s) > len(pre) + 1:
                rest = s[len(pre) + 1:].strip()
                cand = self.alias.get(rest, _titlecase(rest))
                if cand in self._children.get(parent, ()):
                    return rest
        return s

    def key(self, label):
        """Raw label -> (canonical_id, level).

        level is one of country/colony/port/aggregate/residual/junk.
        """
        s = prenorm(label)
        if not s:
            return DROP, 'junk'
        if s in self.alias:
            cid = self.alias[s]
            return cid, self.level.get(s) or self._level_of(cid)
        # 'Parent : Child' and friends are resolved AFTER a direct hit, so a
        # crosswalk row for the full string always wins over the split.
        inner = self._split_hierarchy(s)
        if inner != s:
            cid = self.alias.get(inner, _titlecase(inner))
            return cid, self.level.get(inner) or self._level_of(cid)
        return _titlecase(s), self._level_of(_titlecase(s))

    def _level_of(self, cid):
        if cid == RESIDUAL:
            return 'residual'
        if cid == DROP:
            return 'junk'
        if cid in self.parent:
            return 'port' if '(' in cid else 'colony'
        return 'country'

    # -- hierarchy ----------------------------------------------------------
    def ancestors(self, cid):
        out, seen = [], {cid}
        while cid in self.parent:
            cid = self.parent[cid]
            if cid in seen:
                break                    # cycle guard; the tree is hand-edited
            seen.add(cid)
            out.append(cid)
        return out

    def is_ancestor(self, a, c):
        return a in self.ancestors(c)


def coarsest_common_cut(ck, gold, pipe):
    """The finest partition BOTH sides can express, given what each names.

    For every node on either side, walk up to the HIGHEST ancestor that either
    side names as a line of its own; that ancestor is the level at which the
    two can honestly be compared. Then drop any cut member that is a descendant
    of another, so nothing is counted twice.

    1890: gold names Australasia, we name Australasia -> cut {Australasia}.
    1895: gold names six colonies, we name Australasia -> every colony walks up
          and finds Australasia present, so the six are summed against our one.
    1885: both name the six colonies and neither names Australasia -> the cut
          stays at the six. The roll-up coarsens only where it must.
    """
    present = set(gold) | set(pipe)
    cut = set()
    for n in present:
        best = n
        for a in ck.ancestors(n):
            if a in present:
                best = a                 # keep climbing: highest present wins
        cut.add(best)
    return {c for c in cut
            if not any(ck.is_ancestor(d, c) for d in cut if d != c)}


def lift(ck, vec, cut):
    """Sum a vector up to the cut. Returns (lifted, mapping node->cut member)."""
    out, mapping = {}, {}
    for node, qv in vec.items():
        target = node
        if node not in cut:
            for a in ck.ancestors(node):
                if a in cut:
                    target = a
                    break
        mapping[node] = target
        cur = out.setdefault(target, [0.0, 0.0])
        cur[0] += qv[0] or 0
        cur[1] += qv[1] or 0
    return out, mapping


_singleton = None


def load():
    global _singleton
    if _singleton is None:
        _singleton = CountryKey()
    return _singleton


if __name__ == '__main__':
    ck = load()
    for lab in ('Australasia : Victoria', 'Australasia Victoria', 'Victoria',
                'West Australia', 'Wales', 'British North America', 'Canada',
                'United States of America Atlantic Ports',
                'United States Of America (Atlantic)',
                'United States of Colombia', 'Other Foreign Countries ',
                'Holland', 'Turkey European', 'Russia (Northern Ports)'):
        cid, lvl = ck.key(lab)
        print(f'{lab!r:45} -> {cid!r:38} [{lvl}]  ancestors={ck.ancestors(cid)}')
