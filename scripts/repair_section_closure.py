#!/usr/bin/env python3
"""Single-cell repairs proven by the printed section TOTAL.

The cross-volume vote (repair_edge_columns.py) needs two witnesses that AGREE
on a value; for 1898-1900 that leaves most cells untouched, because the only
reprint (tn_1901) is a different publication whose group headings and capture
accidents differ from as_1899's, so 40% of cells align with no witness at all
and another third with a lone one. After the vote and the phantom relabel,
the late-era own-year columns still close in only ~25% of sections -- but
another ~45% close WITHIN 5%, i.e. one member (or the anchor) is off by a
digit and everything else is right.

Those sections carry their own proof. If substituting ONE cell with a value
that some other reading offers makes the section close to 0.1%, the printed
TOTAL has arbitrated: the candidate is right and the own reading was wrong.
The reading that offers the candidate does not need to be trusted on its own
-- a lone witness, or the SECOND ENGINE reading the same damaged page edge
(rejected as a sole witness by the vote because two engines misread the same
scan the same way ~2/3 of the time) is admissible here, because the section
arithmetic, not the source, is the evidence.

Candidate sources per cell, in order tried (all admitted equally; the
closure test decides):
  * the other engine's reading of the same volume-year, aligned on the full
    key + occurrence (same print, so keys align)
  * every witness volume-year of that year in either engine, aligned as the
    vote aligns (full key + occurrence, or group-free unique article)

Rules:
  * a section is repairable when it has a printed TOTAL, is NOT already
    exact, and exactly ONE single-cell substitution (member or anchor)
    closes it to <=0.1%; two different closing substitutions = ambiguous,
    skip
  * a substitution must change the cell (candidate != own value)
  * cells already repaired by an earlier overlay are taken as repaired
    (the earlier overlays are applied first, and a section closed by them
    is left alone)
  * output rows use the RAW article, like every other overlay, so consumers
    apply them to the raw parse before the phantom relabel

Output: reference/section_closure_repairs.csv (provenance-safe overlay,
keyed on the bad value).

Usage: python3 scripts/repair_section_closure.py [--dry-run]
"""
import argparse, collections, csv, os, re, sys
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phantom_articles import fix_articles
from repair_edge_columns import (ENGINES, TN_TABLES, TOTAL_RE, index_rows,
                                 norm)

# (volume, year) columns to repair -> witness volumes offering candidates.
# The primary witnesses of the series (PRIMARY_OVERRIDE sends 1897/98 to
# as_1899) plus the own-year columns nothing else reads. Same-volume other-
# engine readings are always candidates and need no listing.
TARGETS = {('as_1899', 1897): ['as_1897', 'as_1898', 'tn_1899', 'tn_1901'],
           ('as_1899', 1898): ['as_1898', 'tn_1899', 'tn_1901'],
           ('as_1899', 1899): ['tn_1901'],
           ('tn_1901', 1900): [],
           ('as_1897', 1897): ['as_1898', 'as_1899', 'tn_1899', 'tn_1901'],
           ('as_1898', 1898): ['as_1899', 'tn_1899', 'tn_1901'],
           # 2026-08-18: EVERY own-year volume. The single-year annuals have
           # no reprint, but the second engine reading the same page is a
           # candidate source, and the section arithmetic is the proof: the
           # 1870s-80s spikes in the Canada series (LEATHER 1881 590,215
           # against inf's 9,462; carpets 1877/1881 x10 across a block;
           # MEDICINES 1880, EARTHEN 1881/82, STATIONERY 1873, PLATED 1875)
           # are single-engine misreads that the other engine has right.
           ('tn_1871', 1870): [],
           ('as_1893', 1893): ['as_1897'],
           ('as_1894', 1894): ['as_1897', 'as_1898', 'tn_1895', 'tn_1899'],
           ('as_1895', 1895): ['as_1897', 'as_1898', 'as_1899', 'tn_1899'],
           ('as_1896', 1896): ['as_1897', 'as_1898', 'as_1899', 'tn_1899', 'tn_1901']}
for _y in range(1872, 1893):
    TARGETS[(f'as_{_y}', _y)] = []
PRIOR = ('reference/export_cell_repairs.csv',
         'reference/malformed_cell_repairs.csv',
         'reference/edge_column_repairs.csv',
         'reference/row_slip_repairs.csv',
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


def fetch_rows(con, tbl, vol, year):
    """(flow, ag, art, unit, ctry, value, raw_art, raw_unit, seq) block
    ordered, phantom relabel applied to art/unit."""
    rows = con.execute(f"""
        select volume, flow, year, coalesce(article_group,''), article, unit,
               row_seq, country_raw, value
        from "{tbl}" where volume = ? and year = ?
    """, [vol, year]).fetchall()
    fixed = fix_articles(rows, vol=0, flow=1, year=2, group=3, art=4,
                         unit=5, seq=6)
    out = [(f[1], f[3], f[4] or '', f[5] or '', f[7], f[8],
            r[4] or '', r[5] or '', f[6]) for f, r in zip(fixed, rows)]
    out.sort(key=lambda t: (t[0], t[1], t[2], t[3], t[8]))
    return out


def table_for(eng, vol, year):
    tbl = ENGINES[eng]
    if vol.startswith('tn_') and 1872 <= year <= 1899:
        tbl = TN_TABLES[eng]
    return tbl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='db/uk_trade.duckdb')
    ap.add_argument('--out', default='reference/section_closure_repairs.csv')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    con = duckdb.connect(a.db, read_only=True)
    prior = load_prior()

    repairs, stats = [], collections.Counter()
    for (vol, year), wvols in TARGETS.items():
        own = fetch_rows(con, 'country_obs', vol, year)
        # apply prior overlays (raw key) so we start from the repaired state
        cur = []
        for flow, ag, art, unit, ctry, v, ra, ru, sq in own:
            if v is not None:
                nv = prior.get((vol, year, ag, ra, ctry, round(v)), NO)
                if nv is not NO:
                    v = nv
            cur.append((flow, ag, art, unit, ctry, v, ra, ru, sq))
        own_full, own_count, _ = index_rows(cur)

        # candidate sources
        sources = {}
        for eng in ENGINES:
            if eng != 'obs':
                sources[f'{eng}:{vol}'] = index_rows(
                    fetch_rows(con, table_for(eng, vol, year), vol, year))
            for wv in wvols:
                sources[f'{eng}:{wv}'] = index_rows(
                    fetch_rows(con, table_for(eng, wv, year), wv, year))

        # candidates per own row index
        occ_seen = collections.Counter()
        cands = {}
        for i, (flow, ag, art, unit, ctry, v, ra, ru, sq) in enumerate(cur):
            k = (flow, norm(ag), norm(art), norm(unit), norm(ctry))
            occ = occ_seen[k]
            occ_seen[k] += 1
            cs = {}
            for name, (wfull, wcount, wng) in sources.items():
                wv_val = None
                if wcount.get(k) == own_count[k]:
                    wv_val = wfull.get(k + (occ,))
                elif own_count[k] == 1 and k not in wcount and k[2]:
                    wv_val = wng.get((k[0],) + k[2:])
                if wv_val is not None and wv_val != v:
                    cs.setdefault(wv_val, []).append(name)
            cands[i] = cs

        # walk sections
        blocks = collections.defaultdict(list)
        for i, r in enumerate(cur):
            blocks[r[:4]].append(i)
        for bk, idxs in blocks.items():
            mem = []
            for i in idxs:
                ctry, v = cur[i][4], cur[i][5]
                if ctry and TOTAL_RE.search(ctry):
                    if mem and v:
                        s = sum(cur[j][5] for j in mem)
                        stats[f'{vol}-{year} sections'] += 1
                        if abs(s - v) <= 0.001 * abs(v):
                            stats[f'{vol}-{year} already exact'] += 1
                        else:
                            closers = []
                            for j in mem:
                                for cv, names in cands[j].items():
                                    s2 = s - cur[j][5] + cv
                                    if abs(s2 - v) <= 0.001 * abs(v):
                                        closers.append((j, cv, names))
                            for cv, names in cands[i].items():
                                if abs(s - cv) <= 0.001 * abs(cv):
                                    closers.append((i, cv, names))
                            chosen = None
                            if len(closers) == 1:
                                chosen = closers
                            elif len(closers) > 1:
                                stats[f'{vol}-{year} ambiguous'] += 1
                            else:
                                # two-cell substitutions: every pair of
                                # candidates on DISTINCT cells (members
                                # and/or the anchor); unique closing pair only
                                allc = [(j, cv, nm) for j in mem
                                        for cv, nm in cands[j].items()]
                                allc += [(i, cv, nm) for cv, nm in cands[i].items()]
                                pairs = []
                                for x in range(len(allc)):
                                    j1, c1, n1 = allc[x]
                                    for y in range(x + 1, len(allc)):
                                        j2, c2, n2 = allc[y]
                                        if j1 == j2:
                                            continue
                                        s2, t2 = s, v
                                        for j, c in ((j1, c1), (j2, c2)):
                                            if j == i:
                                                t2 = c
                                            else:
                                                s2 = s2 - cur[j][5] + c
                                        if abs(s2 - t2) <= 0.001 * abs(t2):
                                            pairs.append([(j1, c1, n1), (j2, c2, n2)])
                                if len(pairs) == 1:
                                    chosen = pairs[0]
                                    stats[f'{vol}-{year} closed by a PAIR'] += 1
                                elif len(pairs) > 1:
                                    stats[f'{vol}-{year} ambiguous pair'] += 1
                                else:
                                    stats[f'{vol}-{year} no closer'] += 1
                            for j, cv, names in (chosen or []):
                                flow, ag, art, unit, cty, ov, ra, ru, sq = cur[j]
                                stats[f'{vol}-{year} REPAIRED '
                                      + ('anchor' if j == i else 'member')] += 1
                                repairs.append(dict(
                                    volume=vol, year=year, flow=flow,
                                    article_group=ag, article=ra,
                                    country_raw=cty, old_value=ov,
                                    new_value=cv,
                                    witnesses='; '.join(sorted(names))))
                    mem = []
                elif v is not None:
                    mem.append(i)

        # overlay-key ambiguity guard, per volume-year (as in the vote)
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
        # a prior overlay must not be re-keyed: if the same raw key already
        # has a prior repair, our old_value is the prior's NEW value and the
        # consumers would never see it. Re-key on the prior's old value.
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

    for k in sorted(stats):
        print(f'{k:44} {stats[k]:>7,}')
    src = collections.Counter()
    for r in repairs:
        for n in r['witnesses'].split('; '):
            src[n] += 1
    print('\ncandidate sources of applied repairs:')
    for n, c in src.most_common():
        print(f'  {n:16} {c:6}')
    print('\nlargest corrections:')
    for r in sorted(repairs, key=lambda r: -abs(r['new_value'] - r['old_value']))[:12]:
        print(f'  {r["volume"]} {r["year"]} {r["flow"]:9} {r["old_value"]:>13,.0f} -> '
              f'{r["new_value"]:>13,.0f}  {r["country_raw"][:24]:24} {r["article"][:30]}')
    if repairs and not a.dry_run:
        cols = ['volume', 'year', 'flow', 'article_group', 'article',
                'country_raw', 'old_value', 'new_value', 'witnesses']
        with open(a.out, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(repairs)
        print(f'\nwrote {a.out} ({len(repairs)} rows)')


if __name__ == '__main__':
    main()
