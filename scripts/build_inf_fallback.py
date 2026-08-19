#!/usr/bin/env python3
"""Sections the primary engine never read, taken whole from the second engine.

Every value overlay so far changes a cell that country_obs HAS. But obs loses
whole sections: as_1881 ZINC 'Manufactured' (Canada 256,297) is not in obs
under any heading, as_1887 PAINTERS' COLOURS, as_1888 SPIRITS, as_1876
COPPER 'Mixed or Yellow Metal', as_1875 BOOKS -- and each is a visible hole
in the Canada series (ZINC 1880-81 read 0, PAINTERS' 1887 0, SPIRITS 1888 0,
COPPER 1876 0, BOOKS 1875 0). country_obs_inf read those pages and its
sections CLOSE on their printed TOTALs, which is the same proof every other
repair rests on.

This emits, per own-year volume, the inf sections that
  * have >= MIN_MEMBERS destination rows and close on their TOTAL to 0.1 %;
  * sit under a block key (flow, group, article -- unit-less, normalised)
    that has NO rows in obs for that volume-year; and
  * whose member values are ABSENT from obs (fewer than SHARE_MAX of them
    occur anywhere in obs's rows for the volume-year, any heading) -- so a
    section obs holds under another heading, or garbled but recognisable,
    is never added twice;
  * and whose NAME the pipeline can place: the article is a known group
    heading (promote_headings will re-home it -- 'OIL' / "PAINTERS' COLOURS
    and MATERIALS"), or the (group, article) pair is attested in obs within
    two years. inf's group is often a captor ('Malt' holding cotton piece
    goods, STATIONERY holding tea's 'Total'), and a section under an
    unplaceable name would land in the wrong commodity.
Member rows and the closing TOTAL row are written with inf's group/article/
unit/country/value and row_seq + SEQ_OFFSET (so no obs-keyed row-range
overlay can touch them, and they sort after obs's rows).

Consumers append these rows to what they fetch from country_obs, BEFORE the
overlays and relabels (inf_fallback.load_rows(flow)); the rest of the
pipeline -- phantom relabel, heading promotion, reassign, folds, families --
applies to them by name like any obs row.

Output: reference/inf_fallback_rows.csv
Usage: python3 scripts/build_inf_fallback.py [--dry-run] [--verbose]
"""
import argparse, collections, csv, sys
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repair_edge_columns import TOTAL_RE, norm
from repair_section_closure import TARGETS, fetch_rows, table_for
from repair_row_slip import sections, closes
from phantom_articles import known_groups, _key

FLOWS = ('export_uk', 'reexport')
MIN_MEMBERS = 4
SHARE_MAX = 0.4
SEQ_OFFSET = 1_000_000
CANADA = ('British North America', 'Canada', 'Newfoundland')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='db/uk_trade.duckdb')
    ap.add_argument('--out', default='reference/inf_fallback_rows.csv')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--verbose', '-v', action='store_true')
    a = ap.parse_args()
    con = duckdb.connect(a.db, read_only=True)

    recs, stats = [], collections.Counter()
    known = {flow: known_groups(con, flow) for flow in FLOWS}
    # (flow, norm group, norm article) pairs obs attests, per volume-year
    attested = {}
    for (vol, year) in TARGETS:
        attested[(vol, year)] = {(r[0], norm(r[1]), norm(r[2]))
                                 for r in fetch_rows(con, 'country_obs', vol, year)}
    by_year = collections.defaultdict(list)
    for (vol, year) in TARGETS:
        by_year[year].append((vol, year))
    # obs's spelling of each heading, corpus-wide (most frequent), for
    # headings the volume itself lost
    spell_count = collections.Counter()
    for (vol, year) in TARGETS:
        for r in fetch_rows(con, 'country_obs', vol, year):
            spell_count[(r[0], norm(r[1]), r[1])] += 1
    corpus_spelling = {}
    for (flow, nk, sp), n in spell_count.most_common():
        corpus_spelling.setdefault((flow, nk), sp)

    def placeable(flow, ag, art, year):
        if _key(art) in known[flow]:
            return True
        for y2 in range(year - 2, year + 3):
            for vy in by_year.get(y2, ()):
                if (flow, norm(ag), norm(art)) in attested[vy]:
                    return True
        return False

    for (vol, year) in sorted(TARGETS, key=lambda t: t[1]):
        own = fetch_rows(con, 'country_obs', vol, year)
        oth = fetch_rows(con, table_for('inf', vol, year), vol, year)
        own_keys = {(r[0], norm(r[1]), norm(r[2])) for r in own}
        own_vals = collections.Counter(round(r[5]) for r in own if r[5] is not None)
        # inf spells headings its own way ('IMPLEMENTs AND TOOLS'); use obs's
        # spelling of the same heading in this volume so the folds/families
        # keyed on obs spellings apply
        own_spelling = {}
        for r in own:
            own_spelling.setdefault((r[0], norm(r[1])), r[1])
        # inf rows by (flow, ag, art, unit) with the raw article carried,
        # in row_seq order, split into sections at TOTAL rows
        oth_secs = sections(oth)
        for bk, secs in oth_secs.items():
            flow, ag, art, unit = bk
            if flow not in FLOWS:
                continue
            ag = own_spelling.get((flow, norm(ag)),
                                  corpus_spelling.get((flow, norm(ag)), ag))
            if (flow, norm(ag), norm(art)) in own_keys:
                continue
            for mem, tot in secs:
                if len(mem) < MIN_MEMBERS or not closes(mem, tot):
                    continue
                if not placeable(flow, ag, oth[mem[0][0]][6] or '', year):
                    stats['skipped: name not placeable'] += 1
                    continue
                share = sum(1 for _, c, v in mem if own_vals.get(round(v))) / len(mem)
                if share >= SHARE_MAX:
                    stats['skipped: values present in obs'] += 1
                    continue
                # the TOTAL row that closes this section is the row after
                # the last member in inf's block order
                last_idx = mem[-1][0]
                tot_row = None
                for r in oth[last_idx + 1:last_idx + 3]:
                    if r[0:4] == bk[0:4] and r[4] and TOTAL_RE.search(r[4]):
                        tot_row = r
                        break
                can = sum(v for _, c, v in mem if c in CANADA)
                for idx, c, v in mem:
                    r = oth[idx]
                    recs.append(dict(volume=vol, year=year, flow=flow,
                                     article_group=ag, article=r[6], unit=r[7],
                                     row_seq=r[8] + SEQ_OFFSET, country_raw=c,
                                     value=v, source='inf',
                                     section_total=tot, section_rows=len(mem),
                                     canada=round(can)))
                if tot_row is not None:
                    recs.append(dict(volume=vol, year=year, flow=flow,
                                     article_group=ag, article=tot_row[6],
                                     unit=tot_row[7], row_seq=tot_row[8] + SEQ_OFFSET,
                                     country_raw=tot_row[4], value=tot_row[5],
                                     source='inf', section_total=tot,
                                     section_rows=len(mem), canada=round(can)))
                stats[f'{vol}-{year} sections'] += 1
                stats['canada value'] += can
                if a.verbose:
                    print(f'  {vol} {year} {flow:9} {ag[:30]:30}/{art[:24]:24} '
                          f'{len(mem):3} rows TOTAL {tot:>12,.0f} canada {can:>9,.0f}')
    nsec = sum(v for k, v in stats.items() if k.endswith(' sections'))
    print(f'{nsec} inf-only sections, {len(recs)} rows, Canada GBP{stats["canada value"]:,.0f}; '
          f'{stats["skipped: values present in obs"]} skipped (values present in obs), '
          f'{stats["skipped: name not placeable"]} skipped (name not placeable)')
    if not a.dry_run:
        with open(a.out, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['volume', 'year', 'flow', 'article_group',
                                              'article', 'unit', 'row_seq', 'country_raw',
                                              'value', 'source', 'section_total',
                                              'section_rows', 'canada'])
            w.writeheader()
            w.writerows(recs)
        print(f'wrote {a.out}')


if __name__ == '__main__':
    main()
