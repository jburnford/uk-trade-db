#!/usr/bin/env python3
"""Export and re-export tables sitting in the import payload.

The Abstract prints, for the same commodity and year, an import table, a
table of British produce EXPORTED, and a table of foreign goods RE-EXPORTED.
They look identical — country column, quantity, value, printed Total — and
when a column-top heading is lost the parser files an export table as an
import one. Butter 1882 shows the shape: the import block closes exactly at
its printed 2,169,717 cwt, and a second block of six origins (Portugal,
Gibraltar, Malta, South Africa, Brazil) rides in beside it, adding 1.3% to
a commodity that was already complete.

The test is not a guess about which countries look like destinations —
that screen was tried on tallow and it tripped on Chile and the Channel
Islands, which are exactly where British tallow came from. The test is
arithmetic: **the block's own printed Total is the export_uk or reexport
national line, to the digit.** Butter 1882's intruding block totals 31,640
cwt and GBP219,726, and the export_uk Tier-1 line for butter 1882 is 31,640
and GBP219,726.

    python3 scripts/detect_flow_leakage.py [--family butter,oil]

  -> reports/flow_leakage.csv
"""
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reconcile import _sig                                # noqa: E402

BASE = Path(__file__).resolve().parent.parent
TOTAL_RE = re.compile(r'total', re.I)


def main():
    fam = None
    if '--family' in sys.argv:
        fam = [s.strip().lower()
               for s in sys.argv[sys.argv.index('--family') + 1].split(',')]

    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)

    # Tier-1 national lines by flow, keyed on the token signature of the
    # label so a block's own (group, article) can be looked up directly
    t1 = defaultdict(dict)          # (sig, year) -> {flow: (qty, value)}
    for flow, meas, g, a, y, v in con.execute(
            '''SELECT flow, measure, article_group, article, year, value
               FROM consensus WHERE value > 0''').fetchall():
        d = t1[(_sig(g, a), y)].setdefault(flow, [0, 0])
        d[0 if meas == 'quantity' else 1] = v

    # A misfiled block only matters if its cells reach the shipped table.
    # Most twoup blocks are skipped because consensus already carries the
    # commodity; the ones that get through are those whose stale label gives
    # them a DIFFERENT signature from the import commodity's, so the guard
    # never fires and the payload merges them back together later.
    shipped = set()
    for y, q, v in con.execute(
            '''SELECT year, quantity, value FROM country_year_final
               WHERE flow='import' ''').fetchall():
        shipped.add((y, round(float(q or 0)), round(float(v or 0))))

    rows = []
    for table in ('country_obs', 'country_obs_inf', 'country_obs_twoup'):
        has_seq = table != 'country_obs_twoup'
        order = 'row_seq' if has_seq else 'country_raw'
        blocks = defaultdict(list)
        for vol, g, a, c, y, q, v in con.execute(f'''
                SELECT volume, article_group, article, country_raw, year,
                       quantity, value
                FROM {table} WHERE flow='import' AND year IS NOT NULL
                ORDER BY volume, {order}''').fetchall():
            if fam and not any(f in f'{g} {a}'.lower() for f in fam):
                continue
            blocks[(vol, g, a or '', y)].append(
                (c or '', float(q or 0), float(v or 0)))

        for (vol, g, a, y), rs in blocks.items():
            tots = [(c, q, v) for c, q, v in rs if TOTAL_RE.search(c)]
            mem = [(c, q, v) for c, q, v in rs if not TOTAL_RE.search(c)]
            if not tots or len(mem) < 2:
                continue
            lines = t1.get((_sig(g, a), y)) or {}
            imp = lines.get('import')
            for c, tq, tv in tots:
                if not tq:
                    continue
                # the block's Total IS an export or re-export national line
                for flow in ('export_uk', 'reexport'):
                    fl = lines.get(flow)
                    if not fl or not fl[0]:
                        continue
                    if abs(tq - fl[0]) > 0.5:
                        continue
                    # ...and is NOT the import line, which is the whole point:
                    # for a commodity whose import and export totals happen to
                    # coincide there is nothing to conclude
                    if imp and imp[0] and abs(tq - imp[0]) <= 0.5:
                        continue
                    in_final = sum(
                        (y, round(qq), round(vv)) in shipped
                        for _c2, qq, vv in mem if qq)
                    rows.append({
                        'cells_in_final': in_final,
                        'flow_is_really': flow,
                        'qty': round(tq), 'value': round(tv),
                        'source_table': table, 'volume': vol, 'year': y,
                        'group': g, 'article': a,
                        'n_members': len(mem),
                        'members': ', '.join(
                            f'{cc} {qq:,.0f}' for cc, qq, _ in mem[:8]),
                        't1_import': round(imp[0]) if imp else '',
                        't1_that_flow': round(fl[0]),
                        'value_matches': bool(tv and fl[1]
                                              and abs(tv - fl[1]) <= 0.5),
                    })
                    break

    rows.sort(key=lambda r: (-r['cells_in_final'], -r['qty']))
    out = BASE / 'reports' / 'flow_leakage.csv'
    with open(out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ['qty'])
        w.writeheader()
        w.writerows(rows)
    both = [r for r in rows if r['value_matches']]
    live = [r for r in rows if r['cells_in_final']]
    print(f'blocks whose printed Total is an export/re-export national line: '
          f'{len(rows):,}  (both columns matching: {len(both):,})')
    print(f'  ...whose cells reach country_year_final: {len(live):,} '
          f'({sum(r["cells_in_final"] for r in live):,} cells)')
    for r in rows[:25]:
        print(f'  {r["volume"]} {r["year"]} {r["group"]}|{r["article"][:22]:24s} '
              f'{r["source_table"][12:] or "obs":9s} {r["qty"]:>12,} = '
              f'{r["flow_is_really"]}  {r["cells_in_final"]}/{r["n_members"]}'
              f' cells shipped'
              f'{"  [value too]" if r["value_matches"] else ""}')
    print(f'-> {out}')


if __name__ == '__main__':
    main()
