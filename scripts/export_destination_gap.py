#!/usr/bin/env python3
"""Which export destination labels the gazetteer cannot resolve, ranked by value.

`scripts/countrykey.py` already canonicalises the IMPORT-side country
vocabulary, and it already knows the two facts the Canada series needs:
`British North America` resolves to `Canada`, and `Newfoundland` is a child of
`Canada` — so the 1897 vocabulary change (BNA splits into Canada + Newfoundland)
rolls up correctly without a bespoke splice.

The export destination vocabulary is a different matter. Export tables print
`Parent : Sub` forms the import tables never use, and the gazetteer has no
entries for them, so `countrykey.key()` falls through to a titlecased
passthrough with no ancestors:

    'British India : Bombay and Scinde' -> 'British India Bombay And Scinde'  (invented)
    'Eastern Africa : Java'             -> 'Eastern Africa Java'              (invented)

An invented node cannot roll up, so any cross-destination comparison silently
drops those cells or double-counts them beside their parent. This script
measures that gap and ranks it, so the entries get added to
`reference/gold_country_crosswalk.csv` in value order rather than alphabetically.

A resolution is counted as REAL when the canonical id `key()` returns is a node
the gazetteer actually knows — an alias target or either end of a parent edge.
Testing instead whether the *label* is an alias key is wrong and badly
overstates the gap: canonical spellings such as `United States of America`,
`Australasia` and `Madras` carry no alias row of their own because titlecasing
already produces the right id, and an earlier version of this script scored all
of them unresolved.

Usage:
    python3 scripts/export_destination_gap.py [--flow export_uk]
        [--out reports/export_destination_gap.csv]
"""
import argparse, collections, csv, sys
import duckdb

sys.path.insert(0, __file__.rsplit('/', 1)[0])
import countrykey


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='db/uk_trade.duckdb')
    ap.add_argument('--flow', default='export_uk',
                    choices=['export_uk', 'reexport', 'import'])
    ap.add_argument('--out', default='reports/export_destination_gap.csv')
    ap.add_argument('--max-label', type=int, default=60,
                    help='ignore longer labels; those are unparsed run-in blocks')
    a = ap.parse_args()

    ck = countrykey.load()
    con = duckdb.connect(a.db, read_only=True)
    rows = con.execute("""
        select country_raw, count(*) n, sum(coalesce(value,0)) v,
               min(year) y0, max(year) y1
        from country_obs
        where flow = ? and country_raw is not null
          and length(country_raw) <= ?
          and upper(country_raw) not like '%TOTAL%'
        group by 1
    """, [a.flow, a.max_label]).fetchall()

    # every node the gazetteer/crosswalk actually declares
    known_ids = set(ck.alias.values()) | set(ck.parent) | set(ck.parent.values())

    def resolved(label, cid):
        """True when key() landed on a declared node rather than inventing one."""
        return cid in known_ids or cid in (countrykey.RESIDUAL, countrykey.DROP)

    recs = []
    for label, n, v, y0, y1 in rows:
        cid, lvl = ck.key(label)
        recs.append(dict(label=label, canonical=cid, level=lvl,
                         resolved=int(resolved(label, cid)), cells=n, value=v,
                         y0=y0, y1=y1,
                         parent=(ck.ancestors(cid) or [''])[0]))

    tot_cells = sum(r['cells'] for r in recs) or 1
    tot_val = sum(r['value'] for r in recs) or 1
    bad = [r for r in recs if not r['resolved']]
    bad.sort(key=lambda r: -r['value'])

    print(f'flow={a.flow}   distinct destination labels: {len(recs):,}')
    print(f'  resolved by the gazetteer : {len(recs)-len(bad):,} labels, '
          f'{100*(tot_cells-sum(r["cells"] for r in bad))/tot_cells:.1f}% of cells, '
          f'{100*(tot_val-sum(r["value"] for r in bad))/tot_val:.1f}% of value')
    print(f'  UNRESOLVED (invented ids) : {len(bad):,} labels, '
          f'{100*sum(r["cells"] for r in bad)/tot_cells:.1f}% of cells, '
          f'{100*sum(r["value"] for r in bad)/tot_val:.1f}% of value')

    print(f'\ntop 30 unresolved labels by declared value:')
    print(f'{"cells":>7} {"value GBP":>16} {"years":>11}  label')
    for r in bad[:30]:
        print(f'{r["cells"]:>7} {r["value"]:>16,.0f} '
              f'{str(r["y0"])+"-"+str(r["y1"]):>11}  {r["label"][:52]}')

    with open(a.out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(recs[0].keys()))
        w.writeheader()
        w.writerows(sorted(recs, key=lambda r: (r['resolved'], -r['value'])))
    print(f'\nwrote {a.out} ({len(recs):,} labels)')


if __name__ == '__main__':
    main()
