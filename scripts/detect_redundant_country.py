"""One-redundant-cell screen: a commodity-year that closes exactly if you
remove a single country.

Generalised from reports/turkey_parent_child_findings.md, where `Turkey` was
carried as a flat sibling of its own printed parts (`Turkey European`,
`Asiatic`) and every affected year ran ~2% over. That was found only because a
rebuild happened to expose it. Nothing swept for the shape.

Name-matching cannot find this class — `Asiatic` does not contain `Turkey`. The
arithmetic can: if a year is over its anchor and removing exactly ONE country
lands it inside 0.1%, that country is almost certainly not an independent
origin. It catches at least three known defects at once:

  * a parent line carried beside its own sub-entries (the Turkey case);
  * a subtotal wearing a country's name;
  * a foreign cell (export leakage, a neighbouring block's row) riding in.

Coincidence is the thing to guard against, so the report carries what is needed
to judge it: the excess, the candidate's own figure, and how exactly they match.
A real redundant cell matches the excess almost to the digit. Adjudicate against
the page before acting — this screen proposes, it does not decide.

    python3 scripts/detect_redundant_country.py [--tol 0.001] [--min-gbp 50000]

Writes reports/redundant_country.csv, worst first by GBP.
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('payload', nargs='?',
                    default=str(BASE / 'exports' / 'viz_payload.json'))
    ap.add_argument('--tol', type=float, default=0.001,
                    help='how close removal must land (default exact01)')
    ap.add_argument('--min-gbp', type=float, default=50_000)
    a = ap.parse_args()

    payload = json.load(open(a.payload))
    out = []
    for name, e in payload.items():
        c = e.get('c') or {}
        t1 = c.get('§TOTAL')
        if not t1:
            continue
        units = {u: len([r for r in v if r[1]]) for u, v in t1.items()}
        if not units:
            continue
        unit = max(units, key=units.get)
        vals = [r[1] for r in t1[unit] if r[1]]
        med = sorted(vals)[len(vals) // 2]
        ty = {r[0]: r[1] for r in t1[unit] if r[1] and not r[1] > 30 * med}
        if not ty:
            continue
        per = e.get('v', 0) / max(1, len(ty))
        if per < a.min_gbp:
            continue

        byyear = {}
        for cty, bu in c.items():
            if cty == '§TOTAL' or '(' in cty:
                continue
            for r in bu.get(unit, []):
                if r[1] and r[0] in ty:
                    byyear.setdefault(r[0], {})[cty] = r[1]

        for y, tq in ty.items():
            cells = byyear.get(y) or {}
            s = sum(cells.values())
            if not s or abs(s - tq) <= a.tol * tq:
                continue          # already closes
            excess = s - tq
            if excess <= 0:
                continue          # short, not over — a different defect
            for cty, q in cells.items():
                if abs(s - q - tq) > a.tol * tq:
                    continue
                # how well does this cell explain the excess?
                match = abs(q - excess) / max(q, excess)
                out.append({
                    'commodity': name, 'year': y, 'unit': unit,
                    'drop_country': cty, 'country_qty': round(q),
                    'excess': round(excess), 'match': round(match, 5),
                    'ratio_now': round(s / tq, 5),
                    'ratio_after': round((s - q) / tq, 5),
                    'n_countries': len(cells), 'gbp_per_year': round(per)})

    # one row per commodity-year: the candidate that explains the excess best
    best = {}
    for r in out:
        k = (r['commodity'], r['year'])
        if k not in best or r['match'] < best[k]['match']:
            best[k] = r
    rows = sorted(best.values(), key=lambda r: -r['gbp_per_year'])

    dest = BASE / 'reports' / 'redundant_country.csv'
    with open(dest, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ['commodity'])
        w.writeheader()
        w.writerows(rows)
    dupes = sum(1 for r in out if (r['commodity'], r['year']) in best) - len(best)
    print(f'{len(best)} commodity-years close exactly by removing ONE country '
          f'({dupes} had more than one candidate — read those with suspicion) '
          f'-> reports/redundant_country.csv')
    freq = Counter(r['drop_country'] for r in rows)
    print('\nmost frequent candidates (a repeated name is a class, not a fluke):')
    for cty, n in freq.most_common(12):
        print(f'   {n:>4}  {cty[:56]}')
    print('\nbiggest by GBP/yr:')
    for r in rows[:15]:
        print(f"   GBP{r['gbp_per_year']:>11,}  {r['commodity'][:40]:40} {r['year']} "
              f"drop {r['drop_country'][:26]:26} {r['ratio_now']:.4f} -> "
              f"{r['ratio_after']:.4f}")


if __name__ == '__main__':
    main()
