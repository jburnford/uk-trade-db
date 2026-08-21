#!/usr/bin/env python3
"""Per-cell ship test for the Canadian imports parser.

    python3 scripts/ca_diff_abstract_cells.py OLD_rows.csv NEW_rows.csv

Sums regime-C detail rows per (fiscal year, country, province) in both files, compares each cell's
distance to the printed Abstract by Countries and Provinces (db/canada/imports_abstract_rows.csv), and
lists the cells that got BETTER / WORSE (efc dutiable, efc free, duty), plus the '?' masses.  Read it
before believing any headline ratio."""
import csv, sys
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from ca_check_abstract import ckey


def cells(path):
    S = defaultdict(lambda: defaultdict(float)); Q = defaultdict(float)
    for r in csv.DictReader(open(path)):
        if r['row_kind'] != 'detail' or r['regime'] != 'C': continue
        v = float(r['val_imp']) if r['val_imp'] else 0.0
        if r['country'] in ('', '?'): Q[('country', r['fiscal_year'])] += v
        if r['article'] in ('', '?'): Q[('article', r['fiscal_year'])] += v
        k = (r['fiscal_year'], ckey(r['country']), r['province'])
        sec = 'free' if r['section'] == 'FREE' else 'dut'
        if r['val_efc']: S[k][sec] += float(r['val_efc'])
        if r['duty']: S[k]['duty'] += float(r['duty'])
    return S, Q


def main():
    old, new = sys.argv[1:3]
    A = {}
    for r in csv.DictReader(open(ROOT / 'db' / 'canada' / 'imports_abstract_rows.csv')):
        if r['row_kind'] != 'province' or r['country'] == 'TOTAL': continue
        A[(r['fiscal_year'], ckey(r['country']), r['province'])] = r
    So, Qo = cells(old); Sn, Qn = cells(new)
    print("'?' mass (val_imp, regime C):")
    for kind in ('country', 'article'):
        fo = sum(v for (k, fy), v in Qo.items() if k == kind); fn = sum(v for (k, fy), v in Qn.items() if k == kind)
        print(f"  {kind:8s} OLD {fo:>12,.0f}  NEW {fn:>12,.0f}  ({fn - fo:+,.0f})")
        for fy in sorted(set(fy for (k, fy) in list(Qo) + list(Qn) if k == kind)):
            a = Qo.get((kind, fy), 0); b = Qn.get((kind, fy), 0)
            if abs(a - b) > 0.5: print(f"      {fy}: {a:>12,.0f} -> {b:>12,.0f}  ({b - a:+,.0f})")
    better = []; worse = []; moved = []
    for k in set(So) | set(Sn):
        r = A.get(k)
        for col, acol in (('dut', 'efc_dutiable'), ('free', 'efc_free'), ('duty', 'duty')):
            o = So[k][col] if k in So else 0.0; n = Sn[k][col] if k in Sn else 0.0
            if abs(o - n) < 0.011: continue
            if r is None or r[acol] in ('', None):
                moved.append((k, col, o, n)); continue
            a = float(r[acol]); do = abs(o - a); dn = abs(n - a)
            (better if dn < do - 0.01 else worse if dn > do + 0.01 else moved).append((k, col, o, n, a))
    for name, lst in (('BETTER', better), ('WORSE', worse)):
        lst.sort(key=lambda x: -abs(x[3] - x[2]))
        print(f"\n{name}: {len(lst)} cells")
        for k, col, o, n, a in lst[:40]:
            print(f"  {k[0]} {k[1]:<28s} {k[2]:<18s} {col:5s} {o:>13,.2f} -> {n:>13,.2f}   printed {a:>13,.2f}")
    if moved:
        print(f"\nMOVED with no printed anchor (or equidistant): {len(moved)} cells, largest:")
        moved.sort(key=lambda x: -abs(x[3] - x[2]))
        for x in moved[:15]:
            k, col, o, n = x[:4]
            print(f"  {k[0]} {k[1]:<28s} {k[2]:<18s} {col:5s} {o:>13,.2f} -> {n:>13,.2f}")


if __name__ == '__main__':
    main()
