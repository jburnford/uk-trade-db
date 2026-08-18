#!/usr/bin/env python3
"""Region headings absorbed as ARTICLE names in the late-era country tables.

The 1897-1901 volumes print regional sub-headings inside the country column
('West Africa :' over French/Portuguese Possessions and the Congo; 'East
Africa :' over Zanzibar and the territories under British influence; 'Dutch
Possessions in Indian Seas :' over Java and Other; 'South Africa :' in the
tn_ books). The parser reads such a heading as a SUB-ARTICLE header, and
from that row to the next real article header every country row is filed
under an article called 'West Africa'. In as_1899 that is 3,900 of the
21,000 export rows of a year, in as_1897 4,800 -- a fifth of the table.

Values are untouched by this defect; what it breaks is the BLOCK. CANDLES
becomes three blocks -- (CANDLES, None) holding Russia..Spanish Ports with no
TOTAL, (CANDLES, West Africa) holding the rest of the foreign half plus its
TOTAL, (CANDLES, East Africa) holding the British half and two TOTALs -- and
no section can close because every printed subtotal is separated from the
members it totals. That, not the page edge, is why 1897-1900 corroborate at
~20% while 1893-96 corroborate at 65-80%. It also defeats the cross-volume
vote (repair_edge_columns.py), whose key includes the article.

The repair is a relabel, not a value change: a phantom row takes the article
(and unit) of the nearest preceding NON-phantom row in the same group, in
print order; a phantom with no such row (single-article group whose only
heading is the group) takes article NULL. `East Africa : Portuguese
Possessions` and `Australasia : Victoria` -- headings the parser DID nest
correctly into the country label -- are country labels, not phantoms, and are
left alone.

Applied by the export-side consumers at load time; country_obs itself is not
rewritten (the import pipeline has its own, narrower repair for this class in
repair_country_as_article.py and is measured against a closed baseline).

    from phantom_articles import fix_articles, is_phantom
    rows = fix_articles(rows, vol=0, flow=1, year=2, group=3, art=4, unit=5, seq=6)
"""
import re
import unicodedata

_PHANTOM = {
    'west africa', 'east africa', 'south africa', 'foreign east africa',
    'east coast of africa', 'east coast africa', 'eastern coast of africa',
    'west coast of africa', 'western coast of africa',
    'dutch possessions in indian seas', 'possessions in indian seas',
    'dutch possessions in the indian seas',
    'british possessions in south africa',
}


def _norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode()
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', s.lower())).strip()


def is_phantom(article):
    return _norm(article) in _PHANTOM


def fix_articles(rows, *, vol, flow, year, group, art, unit, seq):
    """rows: list of tuples. Returns a new list (same order) with phantom
    articles relabelled to the nearest preceding real article of the same
    (volume, flow, year, group) in row_seq order, unit carried with it."""
    order = sorted(range(len(rows)),
                   key=lambda i: (rows[i][vol], rows[i][flow], rows[i][year] or 0,
                                  rows[i][seq] if rows[i][seq] is not None else -1))
    last = {}
    out = list(rows)
    for i in order:
        r = rows[i]
        k = (r[vol], r[flow], r[year], r[group])
        if is_phantom(r[art]):
            parent = last.get(k, (None, None))
            if parent[0] != r[art] or parent[1] != r[unit]:
                rr = list(r)
                rr[art], rr[unit] = parent
                out[i] = tuple(rr) if isinstance(r, tuple) else rr
        else:
            last[k] = (r[art], r[unit])
    return out
