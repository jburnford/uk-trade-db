#!/usr/bin/env python3
"""Group headings the parser demoted to article names, leaving the previous
group sticky over rows that belong to the new one.

The Statement prints group headings in capitals. When the parser misses the
promotion it stores the heading as the *article* and keeps the previous group,
so every row underneath is filed under the wrong commodity:

    article_group = GLASS
    article       = GREASE, TALLOW, AND ANIMAL FAT      <- a group, not an article
    (445 rows, 1886-1895, 7 volumes)

Detection is two-stage, because the capitals rule alone over-fires — `LINEN` /
`MANUFACTURES` and `MANURES` / `GUANO` are real article names that happen to be
printed in capitals.

  1. the article is entirely upper-case and differs from its group;
  2. **that same string is used as an `article_group` somewhere else in the
     corpus.** A heading that names a group elsewhere is a heading here.

Stage 2 is what makes this a finding rather than a guess. A corroborating
signal, not required: the Statement is alphabetical, so a lost heading is
usually the alphabetical successor of the group it is filed under (GLASS ->
GREASE, ICE -> INDIGO, ONIONS -> OPIUM, CHEESE -> CLOCKS). That is reported as
`alpha_next` so a reviewer can see it, but it is not part of the test — a
volume can skip a group that has no trade that year.

This is flow-agnostic and fires on all three flows, including the mature import
dataset.

Usage:
    python3 scripts/detect_lost_group_heading.py [--flow all]
        [--out reports/lost_group_headings.csv]
"""
import argparse, collections, csv
import duckdb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='db/uk_trade.duckdb')
    ap.add_argument('--flow', default='all',
                    choices=['all', 'export_uk', 'reexport', 'import'])
    ap.add_argument('--out', default='reports/lost_group_headings.csv')
    a = ap.parse_args()

    con = duckdb.connect(a.db, read_only=True)

    # every string ever used as a group, in any flow or volume
    groups = {g.strip().upper() for (g,) in con.execute(
        "select distinct article_group from country_obs where article_group is not null"
    ).fetchall() if g and g.strip()}

    where = '' if a.flow == 'all' else 'and flow = ?'
    args = [] if a.flow == 'all' else [a.flow]
    rows = con.execute(f"""
        select flow, article_group, article, count(*) n, count(distinct volume) vols,
               min(year) y0, max(year) y1, sum(coalesce(value, 0)) v
        from country_obs
        where article is not null and length(trim(article)) > 4
          and article = upper(article)
          and article_group is not null
          and upper(trim(article_group)) <> upper(trim(article))
          {where}
        group by 1, 2, 3
    """, args).fetchall()

    recs = []
    for flow, ag, art, n, vols, y0, y1, v in rows:
        key = art.strip().upper()
        if key not in groups:
            continue                      # capitals alone is not evidence
        recs.append(dict(flow=flow, article_group=ag, lost_heading=art, rows=n,
                         volumes=vols, y0=y0, y1=y1, value=round(v),
                         alpha_next=int(key[:2] > (ag or '').strip().upper()[:2])))

    recs.sort(key=lambda r: -r['rows'])
    byflow = collections.Counter()
    rowsflow = collections.Counter()
    for r in recs:
        byflow[r['flow']] += 1
        rowsflow[r['flow']] += r['rows']

    print(f'confirmed lost group headings: {len(recs)} labels, '
          f'{sum(r["rows"] for r in recs):,} rows')
    for f in sorted(byflow):
        print(f'  {f:10} {byflow[f]:4} labels  {rowsflow[f]:6,} rows')
    alpha = sum(1 for r in recs if r['alpha_next'])
    print(f'  alphabetical successor of their group: {alpha}/{len(recs)} '
          f'({100*alpha/len(recs) if recs else 0:.0f}%) — corroborating, not required')

    print(f'\ntop 20 by rows')
    print(f'{"flow":>10} {"rows":>6} {"vols":>5} {"years":>10}  group -> lost heading')
    for r in recs[:20]:
        print(f'{r["flow"]:>10} {r["rows"]:>6} {r["volumes"]:>5} '
              f'{str(r["y0"])+"-"+str(r["y1"]):>10}  {r["article_group"][:26]} '
              f'-> {r["lost_heading"][:34]}')

    if recs:
        with open(a.out, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(recs[0].keys()))
            w.writeheader()
            w.writerows(recs)
        print(f'\nwrote {a.out}')


if __name__ == '__main__':
    main()
