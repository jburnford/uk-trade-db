#!/usr/bin/env python3
"""Cross-engine LABEL agreement — the row-slip detector.

Closure is blind to relabelling. The 1870s palm oil tables had every quantity
right, every country label one row out, and still summed to their printed
total; sixteen rounds of anchor reconciliation never saw it. Arithmetic
cannot reach that class of defect, so this instrument does not use
arithmetic. It uses the fact that we read every page TWICE.

For each block printed in both keys (Chandra `country_obs` and Infinity
`country_obs_inf`), align the two readings twice over:

    qty_offset   the row offset that best matches the NUMBER sequences
    lbl_offset   the row offset that best matches the COUNTRY sequences

When the two engines read the same numbers in the same order but attach them
to labels at a different offset, one of them has slipped a row — and the
difference between the offsets is the size of the slip. Direction is decided
by the other volumes: the same year is printed up to five times, so a third
and fourth independent reading of the same table votes on which pairing is
right.

    python3 scripts/cross_engine_labels.py [--group OILS] [--min-gbp 0]

  -> reports/cross_engine_label_slips.csv
"""
import csv
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

BASE = Path(__file__).resolve().parent.parent
MIN_PAIRS = 4          # blocks shorter than this cannot show an offset safely
TOTAL_RE = re.compile(r'total|^\s*$|^-+$', re.I)


def norm(s):
    s = (s or '').replace('&amp;', '&')
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = s.lower().replace('&', ' and ')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', s)).strip()


def akey(article):
    """Article key tolerant of the unit tokens and dash leaders that vary
    between engines ('Palm - - -' / 'Palm Cwts')."""
    t = [w for w in norm(article).split()
         if w not in ('cwt', 'cwts', 'tons', 'ton', 'lbs', 'lb', 'gallons',
                      'galls', 'number', 'value', 'qrs', 'quarters', 'tuns',
                      'tun', 'loads', 'pieces', 'yards')]
    return ' '.join(t)


def load_rows(con, table, where):
    sql = f'''SELECT volume, article_group, article, country_raw, unit, year,
                     quantity, value, row_seq
              FROM {table}
              WHERE flow='import' AND quantity IS NOT NULL AND quantity > 0
                    {where}'''
    out = []
    for vol, g, a, c, u, y, q, v, seq in con.execute(sql).fetchall():
        if not c or not akey(a):
            continue
        out.append((vol, norm(g), akey(a), y, seq if seq is not None else 0,
                    norm(c), u, float(q), float(v or 0), g, a, c,
                    bool(TOTAL_RE.search(c))))
    return out


def block_key(rows_ch, rows_inf):
    """Key blocks on (volume, article, year) — the two engines attach group
    headers differently, so the group cannot be part of the key. But an
    article like 'Unenumerated' is printed under a dozen groups in one volume,
    and merging those into one block invents slips out of nothing. So: key on
    the article alone where it is unambiguous in the volume, and fall back to
    including the group where it is not."""
    ambiguous = set()
    for rows in (rows_ch, rows_inf):
        seen = defaultdict(set)
        for vol, g, ak, y, *_ in rows:
            seen[(vol, ak, y)].add(g)
        ambiguous |= {k for k, gs in seen.items() if len(gs) > 1}

    def build(rows):
        blocks = defaultdict(list)
        for r in rows:
            vol, g, ak, y = r[0], r[1], r[2], r[3]
            k = (vol, ak, y, g) if (vol, ak, y) in ambiguous else (vol, ak, y, '')
            blocks[k].append(r[4:])
        for k in blocks:
            blocks[k].sort(key=lambda r: r[0])
        return blocks
    return build(rows_ch), build(rows_inf), len(ambiguous)


COAST_RE = re.compile(r'^(?:northern|southern) ports|^on the (?:atlantic|pacific)'
                      r'|^(?:atlantic|pacific)$', re.I)


def label_class(a, b):
    """Not every label disagreement is a slipped row. A country name that
    wrapped onto a second printed line reads as two labels in one engine and
    one in the other, and a coast sub-entry printed under its parent reads as
    a bare 'Southern Ports' in one engine and 'Russia : Southern Ports' in the
    other. Both shift every following label by one and would otherwise
    dominate the report."""
    if a.startswith(b) or b.startswith(a) or a in b or b in a:
        return 'wrap'
    if COAST_RE.match(a) or COAST_RE.match(b):
        return 'coast'
    return 'slip'


def segment_closure(rows):
    """How many of the block's printed segments its member rows add up to.

    When the two engines pair the same numbers with labels at different
    offsets, one of them is carrying a row the other is not — an extra line
    dragged in from the table above, or a line dropped. That is an arithmetic
    difference, not a labelling one, and the printed segment totals can see
    it even in a year that only one volume ever printed. The engine whose
    ROW SET closes is the engine that read the right rows.

    Returns (segments_closing, segments_tested)."""
    ok = tested = 0
    acc = 0.0
    for seq, c, u, q, v, g, a, craw, is_tot in rows:
        if is_tot:
            if acc:
                tested += 1
                ok += abs(acc - q) <= max(1.0, 0.001 * q)
            acc = 0.0
        else:
            acc += q
    return ok, tested


def best_offset(a, b, span=3):
    """Offset k maximizing |{i: a[i] == b[i+k]}|, and that count."""
    best, bn = 0, -1
    for k in range(-span, span + 1):
        n = sum(1 for i, x in enumerate(a)
                if 0 <= i + k < len(b) and x and x == b[i + k])
        if n > bn:
            best, bn = k, n
    return best, bn


def main():
    grp_filter = None
    if '--group' in sys.argv:
        grp_filter = sys.argv[sys.argv.index('--group') + 1].lower()
    min_gbp = 0
    if '--min-gbp' in sys.argv:
        min_gbp = float(sys.argv[sys.argv.index('--min-gbp') + 1])

    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)
    where = ''
    if grp_filter:
        where = (f" AND (lower(article_group) LIKE '%{grp_filter}%'"
                 f" OR lower(article) LIKE '%{grp_filter}%')")
    ch, inf, n_amb = block_key(load_rows(con, 'country_obs', where),
                               load_rows(con, 'country_obs_inf', where))
    print(f'blocks: chandra {len(ch):,}  infinity {len(inf):,}  '
          f'shared {len(set(ch) & set(inf)):,}  '
          f'(group-qualified because the article repeats: {n_amb:,})')

    # what the SHIPPED data says. A slip only matters if the engine that
    # slipped is the one country_year_final took the cell from, so look the
    # number up in the final table and see which engine's label it carries.
    final = defaultdict(set)                # (year, qty) -> {norm country}
    for y, q, c in con.execute(
            '''SELECT year, quantity, country FROM country_year_final
               WHERE flow='import' AND quantity > 0''').fetchall():
        final[(y, round(float(q)))].add(norm(c))

    # Corpus index for the third voice. It has to be cross-VOLUME *and*
    # cross-ENGINE to be worth anything: a parser that takes the country
    # column one row out on a given table shape takes it one row out in every
    # volume that prints that shape, so "as_1898's Chandra reading agrees
    # with as_1897's Chandra reading" is not a second opinion. Support for
    # Chandra's pairing means INFINITY, somewhere else, read it that way.
    pairing = defaultdict(Counter)      # (akey, year, qty) -> {(vol,eng,c): n}
    vols_printing = defaultdict(set)
    for src, eng in ((ch, 'ch'), (inf, 'inf')):
        for (vol, ak, y, _g), rows in src.items():
            vols_printing[(ak, y)].add(vol)
            for _s, c, _u, q, *_ in rows:
                pairing[(ak, y, round(q))][(vol, eng, c)] += 1

    rows_out = []
    for key in sorted(set(ch) & set(inf)):
        vol, ak, y, _g = key
        blkA, blkB = ch[key], inf[key]
        A = [r for r in blkA if not r[8]]
        B = [r for r in blkB if not r[8]]
        if len(A) < MIN_PAIRS or len(B) < MIN_PAIRS:
            continue
        qa = [round(r[3]) for r in A]
        qb = [round(r[3]) for r in B]
        ca = [r[1] for r in A]
        cb = [r[1] for r in B]
        qk, qn = best_offset(qa, qb)
        lk, ln = best_offset(ca, cb)
        # need both sequences to align well enough to trust either offset
        if qn < MIN_PAIRS or ln < MIN_PAIRS or qk == lk:
            continue

        # the disagreeing pairs, and the other volumes' verdict on each
        ex, votes, klass, ships = [], Counter(), Counter(), Counter()
        for i, q in enumerate(qa):
            j = i + qk
            if not (0 <= j < len(qb)) or qb[j] != q:
                continue
            if ca[i] == cb[j]:
                continue
            klass[label_class(ca[i], cb[j])] += 1
            v_ch = sum(n for (v2, e2, c2), n in pairing[(ak, y, q)].items()
                       if v2 != vol and e2 == 'inf' and c2 == ca[i])
            v_inf = sum(n for (v2, e2, c2), n in pairing[(ak, y, q)].items()
                        if v2 != vol and e2 == 'ch' and c2 == cb[j])
            votes['ch'] += v_ch
            votes['inf'] += v_inf
            fin = final.get((y, q), ())
            ships['ch'] += any(f == ca[i] or f.startswith(ca[i]) or
                               ca[i].startswith(f) for f in fin)
            ships['inf'] += any(f == cb[j] or f.startswith(cb[j]) or
                                cb[j].startswith(f) for f in fin)
            if len(ex) < 6:
                ex.append(f'{q:,}: ch={A[i][7]}({v_ch}) inf={B[j][7]}({v_inf})')

        if not ex:
            continue
        gbp = sum(r[4] for r in A)
        if gbp < min_gbp:
            continue
        n_vols = len(vols_printing[(ak, y)])
        ok_a, n_a = segment_closure(blkA)
        ok_b, n_b = segment_closure(blkB)
        closes = ('chandra' if ok_a > ok_b else
                  'infinity' if ok_b > ok_a else '')
        third = ('chandra' if votes['ch'] > votes['inf'] else
                 'infinity' if votes['inf'] > votes['ch'] else
                 'UNSETTLEABLE (printed once)' if n_vols < 2 else
                 'engines systematically differ')
        rows_out.append({
            'class': klass.most_common(1)[0][0],
            'gbp': round(gbp),
            'n_volumes': n_vols,
            'volume': vol, 'year': y,
            'group': A[0][5], 'article': A[0][6],
            'n_rows_ch': len(A), 'n_rows_inf': len(B),
            'qty_offset': qk, 'qty_matched': qn,
            'lbl_offset': lk, 'lbl_matched': ln,
            'slip': lk - qk,
            'n_disagree': len(ex),
            'third_voice': third,
            'row_set_closes': closes,
            'closure_ch': f'{ok_a}/{n_a}', 'closure_inf': f'{ok_b}/{n_b}',
            'shipped': ('chandra' if ships['ch'] > ships['inf'] else
                        'infinity' if ships['inf'] > ships['ch'] else ''),
            'ships_wrong': (third in ('chandra', 'infinity') and any(ships.values())
                            and (third == 'chandra') != (ships['ch'] >= ships['inf'])),
            'votes_ch': votes['ch'], 'votes_inf': votes['inf'],
            'ships_ch': ships['ch'], 'ships_inf': ships['inf'],
            'examples': ' ; '.join(ex),
        })

    rows_out.sort(key=lambda r: (not r['ships_wrong'], r['class'] != 'slip',
                                 -r['gbp']))
    out = BASE / 'reports' / 'cross_engine_label_slips.csv'
    with open(out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows_out[0]) if rows_out else
                           ['gbp'])
        w.writeheader()
        w.writerows(rows_out)
    by_class = Counter(r['class'] for r in rows_out)
    print(f'label-disagreeing blocks: {len(rows_out):,}  ' +
          '  '.join(f'{k} {v}' for k, v in by_class.most_common()))
    ship_bad = [r for r in rows_out if r['ships_wrong']]
    print(f'  other volumes contradict the engine the FINAL table used: '
          f'{len(ship_bad)}  (GBP {sum(r["gbp"] for r in ship_bad):,})')
    clo = [r for r in rows_out if r['row_set_closes']]
    clo_bad = [r for r in clo if r['shipped']
               and r['row_set_closes'] != r['shipped']]
    print(f'  segment arithmetic picks an engine: {len(clo)}  '
          f'and contradicts the shipped one in {len(clo_bad)} '
          f'(GBP {sum(r["gbp"] for r in clo_bad):,})')
    for r in rows_out[:20]:
        print(f'  GBP{r["gbp"]:>11,}  {r["volume"]} {r["year"]}  '
              f'{r["group"]} | {r["article"]}  slip {r["slip"]:+d}  '
              f'third voice: {r["third_voice"] or "tied"}')
        print(f'      {r["examples"][:150]}')
    print(f'-> {out}')


if __name__ == '__main__':
    main()
