#!/usr/bin/env python3
"""Canonical-level cross-volume voted wood series.

Votes at the CANONICAL commodity level (wood-hewn-fir, wood-sawn-fir, ...),
not the raw article text — so era label variants of the same series
("Sawn, Fir" in the 1890s single-year volumes vs "Sawn or Split, Planed or
Dressed : Fir" in the 5-year volumes) VOTE together across volumes instead
of summing into a double count.

Per (canonical, canon-country, year, unit): collect one reading per volume
(the summed value of that volume's rows mapping to the canonical), then
vote the most-common value across volumes.
  tier A  — >=2 volumes agree
  tier B  — 1 volume, block-verified or engine-agreed
  tier C  — single unverified, or volumes disagree

Reads country_graded (per-volume, per-cell grades). Port sub-details
("United States : On the Atlantic") are excluded — their parent country
aggregate carries the total. Writes exports/wood_country_year_voted.csv.
"""
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).parent))
from map_wood_commodities import canon_wood, norm

BASE = Path('/home/jic823/uk_trade_db')
GOOD = {'exact', 'inf_struct', 'inf_block', 'swap', 'anchor', 'digit_fix',
        'inf_only', 'human'}
COUNTRY_ALIAS = {
    'british north america': 'canada', 'dominion of canada': 'canada',
    'russia northern ports': 'russia', 'russia southern ports': 'russia',
    'united states': 'united states of america',
    # British India incl. Burma — the teak source — is split across many
    # presidency/province labels in the returns; roll them into one series.
    # Burma (Rangoon/Moulmein) supplied most teak but was administered under
    # British India and lumped with Bengal in the tables.
    'british east indies': 'british india and burma',
    'british india': 'british india and burma',
    'british india bengal and burmah': 'british india and burma',
    'bengal and burmah': 'british india and burma',
    'bengal': 'british india and burma', 'burmah': 'british india and burma',
    'burma': 'british india and burma', 'bombay': 'british india and burma',
    'madras': 'british india and burma',
    'bombay and scinde': 'british india and burma',
    'straits settlements': 'british india and burma',
}


def canon_country(c):
    c = norm(c)
    return COUNTRY_ALIAS.get(c, c)


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)
    # country_rescored = country_graded + value-as-signal verdicts; q_conf is
    # the price-aware grade (a C quantity whose independently-printed value
    # backs it is promoted to B; a price-contradicted cell is demoted)
    rows = con.execute("""
        SELECT volume, article, country_raw, unit, year, quantity, value,
               q_conf AS q_grade, v_grade, q_cell, v_cell
        FROM country_rescored
        WHERE flow='import'
          AND (
            (lower(article_group) LIKE '%wood%' AND lower(article_group) LIKE '%timber%')
            -- article_group is often mis-OCR'd/dropped (wiped 1882 & 1884
            -- entirely); also admit rows whose ARTICLE is unambiguously wood.
            -- canon_wood() + the stone/bark guard reject non-wood that slips in.
            OR regexp_matches(lower(article),
                 'fir|oak|teak|mahog|stave|deal|batten|lath|wainscot|hewn|sawn')
          )
          AND country_raw != 'TOTAL'
          AND country_raw NOT LIKE '% : %'""").fetchall()

    # per (canonical, country, year, unit): {volume: [qty, val, q_ok, v_ok]}
    # summing a volume's rows that map to the same canonical (e.g. two
    # sub-species labels that both canon to the same id within one volume)
    pervol = defaultdict(lambda: defaultdict(
        lambda: [0.0, 0.0, False, False]))
    for (vol, art, ctry, unit, yr, q, v, qg, vg, qc, vc) in rows:
        cid, _ = canon_wood(art or '')
        if not cid:
            continue
        c = canon_country(ctry)
        u = {'load': 'loads', 'lds': 'loads', 'ton': 'tons'}.get(
            norm(unit), norm(unit))
        slot = pervol[(cid, c, yr, u)][vol]
        slot[0] += q or 0
        slot[1] += v or 0
        slot[2] = slot[2] or qg == 'A'
        slot[3] = slot[3] or vg == 'A'

    def vote(volmap, idx, ok_idx):
        vals = [round(s[idx]) for s in volmap.values() if s[idx]]
        if not vals:
            return None, 'C', 0, len(volmap)
        val, n = Counter(vals).most_common(1)[0]
        if n >= 2:
            return float(val), 'A', n, len(volmap)
        ok = any(s[ok_idx] for s in volmap.values() if round(s[idx]) == val)
        return float(val), ('B' if ok else 'C'), n, len(volmap)

    out_rows = []
    for (cid, c, yr, u), volmap in sorted(pervol.items()):
        qv, qt, qn, nv = vote(volmap, 0, 2)
        vv, vt, vn, _ = vote(volmap, 1, 3)
        out_rows.append([cid, c, yr, u, f'{qv or 0:.0f}', f'{vv or 0:.0f}',
                         qt, vt, nv, vn])
    out = BASE / 'exports' / 'wood_country_year_voted.csv'
    with open(out, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['commodity', 'country', 'year', 'unit', 'quantity',
                    'value', 'q_tier', 'v_tier', 'n_volumes', 'n_agree'])
        w.writerows(out_rows)
    print(f'-> {out} ({len(out_rows):,} canonical cells)')

    print('\nCanada fir imports (loads), canonical-voted:')
    print('year   hewn-fir (tier,vols)      sawn-fir (tier,vols)')
    by_year = defaultdict(dict)
    for r in out_rows:
        cid, c, yr, u = r[0], r[1], int(r[2]), r[3]
        if c == 'canada' and u == 'loads' and cid in (
                'wood-hewn-fir', 'wood-sawn-fir'):
            by_year[yr][cid] = (r[4], r[6], r[8])
    for yr in sorted(by_year):
        h = by_year[yr].get('wood-hewn-fir')
        s = by_year[yr].get('wood-sawn-fir')
        hs = f'{int(h[0]):>8,} ({h[1]},{h[2]}v)' if h else ' ' * 18
        ss = f'{int(s[0]):>9,} ({s[1]},{s[2]}v)' if s else ''
        print(f'{yr}   {hs}   {ss}')


if __name__ == '__main__':
    main()
