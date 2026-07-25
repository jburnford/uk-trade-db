#!/usr/bin/env python3
"""One-digit repairs that close a block's own printed total.

The fats-and-oils review turned up the same misreading four times in one
session — a printed 8 read as 5 — and every one was caught the same way: the
block's members fell exactly 300,000 or 500,000 short of the total printed at
the foot of the same page. That is not a heuristic, it is a proof, and it is
mechanical:

    delta = printed TOTAL - sum(members)
    if some member's quantity + delta differs from what was read in exactly
    ONE digit position, that member is the misread row and delta is the
    missing digit.

Corroboration, in the order it is worth having:
  * the other engine already reads the repaired number (then it is not even
    a repair, it is a vote the pipeline lost);
  * the repaired row's unit price moves TOWARDS its own block's median rate
    (a within-block test only — prices are not comparable across years, the
    Australian tallow flood halved them in the 1890s).

Runs on both columns: a quantity short by a digit and a value short by a
digit are the same defect in different columns, and value_closure.py says
the value column is the one nobody has been testing.

    python3 scripts/digit_repair_candidates.py [--family oil,tallow]

  -> reports/digit_repair_candidates.csv
"""
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cross_engine_labels import akey                     # noqa: E402

BASE = Path(__file__).resolve().parent.parent
TOTAL_RE = re.compile(r'total', re.I)
# the OCR confusion pairs these tables actually produce, most common first
PAIRS = {('5', '8'), ('3', '8'), ('0', '9'), ('6', '5'), ('1', '4'),
         ('1', '7'), ('0', '6'), ('2', '7'), ('3', '9'), ('4', '9'),
         ('0', '8'), ('6', '8'), ('2', '3'), ('1', '2'), ('7', '9')}


def one_digit_apart(a, b):
    """(position, from, to) when the two numbers differ in exactly one digit
    and have the same length; None otherwise."""
    sa, sb = str(int(a)), str(int(b))
    if len(sa) != len(sb):
        return None
    diff = [i for i in range(len(sa)) if sa[i] != sb[i]]
    if len(diff) != 1:
        return None
    i = diff[0]
    return (i, sa[i], sb[i])


def segments(rows):
    """Split a block into printed segments: the member rows that precede each
    TOTAL row. Nested totals (a grand total straight after a subtotal) have
    no members of their own and are skipped."""
    out, acc = [], []
    for r in rows:
        if r['is_total']:
            if acc:
                out.append((acc, r))
            acc = []
        else:
            acc.append(r)
    return out


def main():
    fam = None
    if '--family' in sys.argv:
        fam = [s.strip().lower()
               for s in sys.argv[sys.argv.index('--family') + 1].split(',')]

    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'), read_only=True)
    blocks = {}
    for eng, table in (('chandra', 'country_obs'), ('infinity', 'country_obs_inf')):
        for vol, g, a, c, u, y, q, v, seq in con.execute(f'''
                SELECT volume, article_group, article, country_raw, unit, year,
                       quantity, value, row_seq
                FROM {table} WHERE flow='import' AND country_raw IS NOT NULL
                ORDER BY volume, row_seq''').fetchall():
            if fam and not any(f in f'{g} {a}'.lower() for f in fam):
                continue
            blocks.setdefault((eng, vol, g, a, y), []).append({
                'seq': seq or 0, 'country': c, 'unit': u,
                'q': float(q or 0), 'v': float(v or 0),
                'is_total': bool(TOTAL_RE.search(c))})

    # Does the SHIPPED table carry the misread number? When the other engine
    # already reads it right, the cross-volume vote has usually picked the
    # right one on its own and there is nothing to repair — so the queue that
    # matters is the one where the wrong reading survived into
    # country_year_final. Matched on the (quantity, value) PAIR, which
    # identifies a cell far more tightly than either column alone.
    shipped = set()
    for y, q, v in con.execute(
            '''SELECT year, quantity, value FROM country_year_final
               WHERE flow='import' ''').fetchall():
        shipped.add((y, round(float(q or 0)), round(float(v or 0))))

    # What the other engine reads for the SAME LINE. Scoped to the article,
    # not just the volume: 'Germany' appears in two hundred blocks of one
    # volume, so an unscoped lookup calls a five-cwt coincidence in the tar
    # table corroboration for a seed-oil row. The article is normalized (unit
    # tokens and punctuation stripped) because the two engines disagree about
    # group headers constantly and about article text rarely.
    other = defaultdict(set)
    for (eng, vol, g, a, y), rows in blocks.items():
        for r in rows:
            other[(eng, vol, y, akey(a), r['country'])].add((r['q'], r['v']))

    out = []
    for (eng, vol, g, a, y), rows in blocks.items():
        for members, tot in segments(rows):
            if len(members) < 3:
                continue
            for col in ('q', 'v'):
                printed = tot[col]
                if not printed:
                    continue
                s = sum(m[col] for m in members)
                delta = printed - s
                if delta == 0 or abs(delta) >= printed:
                    continue
                # THE AMBIGUITY: if the member sum is itself one digit away
                # from the printed total, the misreading may be the TOTAL,
                # not a member. Margarine 1898 is 900,291 against a printed
                # 909,291 — either France is 9,000 short or the total is.
                # Only the within-block price test separates the two (France
                # at GBP3.48/cwt against a block rate of 2.68 is the outlier,
                # so the member is wrong), which is why a candidate flagged
                # here must not be applied on closure alone.
                total_alt = one_digit_apart(printed, s) is not None
                # a within-block rate, for the corroborating price test
                rates = sorted(m['v'] / m['q'] for m in members
                               if m['q'] and m['v'])
                rate = rates[len(rates) // 2] if rates else 0
                for m in members:
                    if not m[col]:
                        continue
                    cand = m[col] + delta
                    if cand <= 0:
                        continue
                    d = one_digit_apart(m[col], cand)
                    if not d:
                        continue
                    pos, was, now = d
                    oq, ov = (cand, m['v']) if col == 'q' else (m['q'], cand)
                    peer = 'infinity' if eng == 'chandra' else 'chandra'
                    corrob = any(abs(pq - oq) < 0.5 and abs(pv - ov) < 0.5
                                 for pq, pv in
                                 other.get((peer, vol, y, akey(a),
                                            m['country']), ()))
                    price_before = (m['v'] / m['q']) if m['q'] and m['v'] else 0
                    price_after = (ov / oq) if oq and ov else 0
                    price_helps = (rate and price_before and price_after and
                                   abs(price_after - rate) <
                                   abs(price_before - rate))
                    as_read = (y, round(m['q']), round(m['v'])) in shipped
                    as_fixed = (y, round(oq), round(ov)) in shipped
                    out.append({
                        'shipped_as_read': as_read and not as_fixed,
                        'total_may_be_the_error': total_alt,
                        # peer agreement outranks uniqueness. When the other
                        # engine already reads the number that closes the
                        # block, the repair is not a hypothesis about a digit
                        # — it is a reading of the page that the vote lost,
                        # and it stands even where two members could
                        # arithmetically absorb the delta (butter 1889:
                        # Russia, Sweden, Germany and Holland are all one
                        # digit from closing, and only Russia's 8,393 is
                        # actually printed on the page in the other key).
                        'score': (4 * corrob + bool(price_helps) +
                                  ((was, now) in PAIRS or (now, was) in PAIRS)),
                        'column': col, 'engine': eng, 'volume': vol,
                        'year': y, 'group': g, 'article': a,
                        'country': m['country'], 'unit': m['unit'],
                        'reads': round(m[col]), 'should_be': round(cand),
                        # the whole cell, both columns, before and after: a
                        # repair has to name the pair to find the shipped row
                        'q_read': round(m['q']), 'v_read': round(m['v']),
                        'q_fixed': round(oq), 'v_fixed': round(ov),
                        'delta': round(delta), 'digit': f'{was}->{now}',
                        'n_members': len(members),
                        'printed_total': round(printed),
                        'other_engine_agrees': corrob,
                        'price_improves': bool(price_helps),
                        'price_before': round(price_before, 2),
                        'price_after': round(price_after, 2),
                        'block_rate': round(rate, 2),
                    })

    # one block can offer several rows that would close it; keep them all but
    # mark how many, because a unique candidate is a proof and three are a
    # choice
    per_block = defaultdict(int)
    for r in out:
        per_block[(r['engine'], r['volume'], r['year'], r['group'],
                   r['article'], r['column'], r['delta'])] += 1
    for r in out:
        r['candidates_in_block'] = per_block[
            (r['engine'], r['volume'], r['year'], r['group'], r['article'],
             r['column'], r['delta'])]
        r['unique'] = r['candidates_in_block'] == 1

    for r in out:
        r['strong'] = bool(r['shipped_as_read'] and
                           (r['other_engine_agrees'] or
                            (r['unique'] and r['price_improves'])))
    out.sort(key=lambda r: (not r['strong'], -r['score'], not r['unique'],
                            -abs(r['delta'])))
    # Written out: only candidates that are the block's ONLY one-digit way to
    # close, or that the other engine actually prints. The rest — a member
    # that happens to sit one digit from a delta three other members could
    # absorb just as well — are arithmetic coincidences, and they outnumber
    # the real ones roughly thirty to one.
    keep = [r for r in out if r['unique'] or r['other_engine_agrees']]
    dest = BASE / 'reports' / 'digit_repair_candidates.csv'
    with open(dest, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(keep)

    strong = [r for r in out if r['strong']]
    print(f'blocks scanned: {len(blocks):,}')
    print(f'one-digit closures found: {len(out):,}  '
          f'unique-in-block: {sum(1 for r in out if r["unique"]):,}  '
          f'other engine reads the repair: '
          f'{sum(1 for r in out if r["other_engine_agrees"]):,}  '
          f'corroborated AND the misreading is what ships: {len(strong):,}')
    for r in strong[:30]:
        print(f'  {r["volume"]} {r["year"]} {r["column"]} {r["group"]}|'
              f'{(r["article"] or "")[:26]:28s} {r["country"][:22]:24s} '
              f'{r["reads"]:>12,} -> {r["should_be"]:>12,}  {r["digit"]}'
              f'{"  [other engine agrees]" if r["other_engine_agrees"] else ""}')
    print(f'-> {dest}  ({len(keep):,} of {len(out):,} written; the rest are '
          f'coincidences — neither unique nor printed by the other engine)')


if __name__ == '__main__':
    main()
