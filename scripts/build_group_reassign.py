#!/usr/bin/env python3
"""Turn adjudicated section captures into per-article reassignments.

`detect_group_capture.py` finds groups holding articles that are not theirs. It
is a screen: its `share` column is reliable, its `victim` column is not, because
article spellings drift between volumes and the attribution vote can land on a
spurious majority. So the captures themselves are adjudicated by hand and live
in `reference/captures.csv`; this script only decides, WITHIN an adjudicated
capture, which articles move.

Why that split matters, concretely. The detector also reported
as_1897 WOOLLEN -> WOOD at 54%. Inspection refuted it: as_1897's WOOLLEN group
holds Shawls, Worsted Stuffs and Woollen Tissues, which are correct. The false
direction arises because as_1897 is a comparative volume whose article spellings
match as_1898/99 -- where wool really does sit under WOOD -- more closely than
they match the single-year volumes. Acting on the screen would have moved a
correct section into the wrong group.

An article moves when either test passes, and the reason is recorded per row:
  home      across all OTHER volumes of this flow, the victim is the group that
            hosts this article name in the most volumes -- i.e. the victim is
            the article's usual home, not merely one place it has been seen
  vocab     the name matches the victim family's vocabulary

"Usual home" rather than "seen at least once", and rather than "seen at least
twice", because a captured section leaves the victim as a husk full of junk
(as_1898's WOOLLEN retains 62 rows of 'Metals') and the damaged volumes agree
with each other. Both weaker tests moved 'Ore' (256 rows) into WOOLLEN AND
WORSTED: Ore does appear under WOOLLEN in tn_1901 and as_1897, which are
themselves damaged. Ore's real home is LEAD, which hosts it in 26 volumes
against WOOLLEN's 2, so the dominant-host test leaves it alone.

Both are needed. `attested` alone misses articles whose spelling is unique to
the damaged volumes; `vocab` alone cannot see articles whose names carry no
family word. Rows failing both stay put, and are reported as residue rather
than swept along -- a captured section usually sits beside a few genuine rows of
the captor (as_1898's WOOD really does contain 'Rough, Hewn, Sawn, or Split').

Output is a reviewable CSV, not an in-place edit. Consumers apply it the same
way as the fused-cell repairs: keyed on the coordinates it was derived from.

Usage:
    python3 scripts/build_group_reassign.py [--out reference/group_reassign.csv]
"""
import argparse, collections, csv, re
import duckdb

VOCAB = {
    'WOOLLEN AND WORSTED MANUFACTURES':
        r'wool|worsted|carpet|hosiery|flannel|blanket|shawl|yarn|tissue|stuff|'
        r'noil|rug|plush|damask|waste|coating|cloth|serge|alpaca|mohair|'
        # raw-wool lines carry no family word of their own
        r'sheep|lamb|fleece|\btops?\b|combed|carded|shoddy|mungo|flock',
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='db/uk_trade.duckdb')
    ap.add_argument('--captures', default='reference/captures.csv')
    ap.add_argument('--out', default='reference/group_reassign.csv')
    a = ap.parse_args()

    con = duckdb.connect(a.db, read_only=True)
    caps = list(csv.DictReader(open(a.captures)))

    # article -> set of groups hosting it, per flow, excluding the damaged volume
    recs, residue = [], []
    for cap in caps:
        flow, vol = cap['flow'], cap['volume']
        captor, victim = cap['captor'], cap['victim']
        rx = re.compile(VOCAB.get(victim.upper(), r'(?!)'), re.I)

        # for every article name, which group hosts it in the most OTHER volumes
        host = {}
        for art_l, grp, nv in con.execute("""
            select lower(trim(article)) a, upper(trim(article_group)) g,
                   count(distinct volume) nv
            from country_obs
            where flow = ? and volume <> ? and article is not null
              and trim(article) <> '' and article_group is not null
            group by 1, 2
        """, [flow, vol]).fetchall():
            if art_l not in host or nv > host[art_l][1]:
                host[art_l] = (grp, nv)
        attested = {a for a, (g, _) in host.items() if g == victim.upper()}

        rows = con.execute("""
            select coalesce(article,'') art, count(*) n, sum(coalesce(value,0)) v,
                   count(distinct country_raw) dests
            from country_obs
            where flow = ? and volume = ? and upper(trim(article_group)) = ?
            group by 1
        """, [flow, vol, captor.upper()]).fetchall()

        for art, n, v, dests in rows:
            key = art.strip().lower()
            why = ('home' if key and key in attested else
                   'vocab' if art and rx.search(art) else None)
            if why:
                recs.append(dict(flow=flow, volume=vol, from_group=captor,
                                 article=art, to_group=victim, reason=why,
                                 rows=n, value=round(v), destinations=dests))
            else:
                residue.append((flow, vol, captor, art, n, round(v)))

    print(f'adjudicated captures: {len(caps)}')
    moved = sum(r['rows'] for r in recs)
    stay = sum(x[4] for x in residue)
    print(f'articles reassigned : {len(recs):,} ({moved:,} rows)')
    print(f'articles left alone : {len(residue):,} ({stay:,} rows)')
    by = collections.Counter(r['reason'] for r in recs)
    print(f'  by reason: ' + '  '.join(f'{k}={v}' for k, v in by.most_common()))

    print(f'\nlargest reassignments')
    for r in sorted(recs, key=lambda r: -r['rows'])[:10]:
        print(f'  {r["volume"]} {r["rows"]:>5} rows  {r["reason"]:>8}  '
              f'{r["article"][:52]}')
    print(f'\nleft under the captor (should be genuinely its own)')
    for f, v, c, art, n, val in sorted(residue, key=lambda x: -x[4])[:10]:
        print(f'  {v} {n:>5} rows  {art[:56] or "(blank)"}')

    with open(a.out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(recs[0].keys()))
        w.writeheader()
        w.writerows(recs)
    print(f'\nwrote {a.out}')


if __name__ == '__main__':
    main()
