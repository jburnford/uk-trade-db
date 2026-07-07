#!/usr/bin/env python3
"""Repair the country-as-article defect in country_consensus.

The parser's sub-article branch promotes REGION HEADERS to articles when OCR
drops the colon/indent: 'From West Africa:' becomes article='West Africa', and
the region's member rows file under a phantom commodity —

    group='Fish'  article='West Africa'  country='The Gold Coast'

really means Fish, from West Africa : Gold Coast. The GROUP is the commodity;
the 'article' is a country context. ~40k rows (10% of the corpus) sit under
such phantom articles ('West Africa' spread across 69 groups).

Repair, per affected row:
  - article -> NULL (the group carries the commodity, as with TEA/COFFEE)
  - country: if the existing country label is itself a standalone country
    (seen frequently corpus-wide as a plain country row: 'Australasia',
    'British East Indies : Bombay') the region context was already stale --
    keep it unchanged. Otherwise ('Portuguese', 'Not designated', 'The Gold
    Coast') qualify it: 'West Africa : The Gold Coast', which the existing
    sub-entry machinery (vote_country_years.resolve_subentries) then treats
    exactly like the tea colonial breakdowns — admitted when they fill a gap
    against the grand total, dropped when the block already covers it.

Region detection is frequency-based, not a hand list: an article string whose
normalized form also occurs >=100 times as a plain country label corpus-wide
is a country, not a commodity. Run BEFORE anchor_tier1/grade/rescore/vote.
"""
import re
import unicodedata
from collections import Counter
from pathlib import Path

import duckdb

BASE = Path('/home/jic823/uk_trade_db')


def cnorm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii',
                                                      'ignore').decode()
    s = s.lower().replace('&', ' and ')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', s)).strip()


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'))

    # plain-country vocabulary with corpus frequencies, PLUS how often each
    # name occurs as the REGION PARENT of a 'Region : Sub' country label —
    # that is where region names actually live ('West Africa : Gold Coast'),
    # not as plain rows.
    cfreq = Counter()
    pfreq = Counter()
    for c, n in con.execute("""
            SELECT country_raw, count(*) FROM country_consensus
            WHERE country_raw IS NOT NULL AND country_raw != 'TOTAL'
            GROUP BY 1""").fetchall():
        if ' : ' in c:
            pfreq[cnorm(c.split(':', 1)[0])] += n
        else:
            cfreq[cnorm(c)] += n

    # phantom articles = article strings that are really country labels.
    # Guard: a real commodity article lives under 1-2 groups; a mis-promoted
    # region scatters across many ('West Africa' under 69). Requiring >=3
    # distinct groups protects any name that is both a country and a genuine
    # article somewhere (Turkey, Guinea...).
    arts = con.execute("""
        SELECT article, count(DISTINCT article_group) FROM country_consensus
        WHERE article IS NOT NULL GROUP BY 1""").fetchall()
    phantoms = {a for a, ng in arts
                if len(cnorm(a)) > 3 and ng >= 3
                and (cfreq.get(cnorm(a), 0) >= 100
                     or pfreq.get(cnorm(a), 0) >= 50)}
    if not phantoms:
        print('no phantom articles found')
        return
    print(f'phantom country-as-article strings: {len(phantoms)}')
    for a in sorted(phantoms)[:15]:
        print(f'   {a!r}')

    # standalone-country test for the member label
    def standalone(c):
        return ' : ' in (c or '') or cfreq.get(cnorm(c), 0) >= 100

    rows = con.execute(f"""
        SELECT rowid, article, country_raw FROM country_consensus
        WHERE article IN ({','.join('?' * len(phantoms))})
          AND country_raw IS NOT NULL AND country_raw != 'TOTAL'
        """, list(phantoms)).fetchall()
    requal, cleared = [], []
    for rid, art, ctry in rows:
        if standalone(ctry):
            cleared.append((rid,))               # stale context: just unfile
        else:
            requal.append((f'{art.strip()} : {ctry.strip()}', rid))
    con.executemany(
        'UPDATE country_consensus SET article=NULL WHERE rowid=?', cleared)
    con.executemany(
        'UPDATE country_consensus SET article=NULL, country_raw=? '
        'WHERE rowid=?', requal)
    # TOTAL rows under a phantom article: keep as the region's total? No —
    # they are the region subtotal, not a commodity total; unfile them too so
    # they can't masquerade as a commodity's printed total.
    nt = con.execute(f"""
        UPDATE country_consensus SET article=NULL
        WHERE article IN ({','.join('?' * len(phantoms))})
          AND country_raw='TOTAL'""", list(phantoms)).fetchone()[0] or 0
    con.commit()
    print(f'rows repaired: {len(cleared):,} unfiled (standalone country), '
          f'{len(requal):,} region-qualified, {nt:,} region subtotals unfiled')


if __name__ == '__main__':
    main()
