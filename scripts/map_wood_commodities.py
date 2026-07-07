#!/usr/bin/env python3
"""Map every wood/timber article label variant (1872-1899, both tiers) to
a stable canonical commodity ID, so series read continuously across the
era's label drift:

  1870s   "Hewn, Fir" / bare "Oak" / ditto-depth "Sawn or Split : Fir"
  1880s   "Hewn : Fir" / "Sawn, Fir" / "Sawn, Unenumerated"
  1897+   "Rough, Hewn, Sawn, or Split" (hewn+sawn CONSOLIDATED — a real
          category break, mapped to wood-rough-combined, never merged
          into either component)

Writes reference/wood_commodity_map.csv (raw label -> canonical, editable;
rerunning regenerates rule-based rows but preserves human 'confirmed'
rows), plus a review list of unmapped variants. Then exports stitched
series with grades: exports/wood_country_year.csv (Tier 2) and
exports/wood_national_year.csv (Tier 1 consensus), and checks continuity
at label-transition years.
"""
import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import duckdb

BASE = Path('/home/jic823/uk_trade_db')
MAP = BASE / 'reference' / 'wood_commodity_map.csv'


def norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii',
                                                      'ignore').decode()
    s = s.lower().replace('&', ' and ')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', s)).strip()


def canon_wood(raw):
    """Rule-based canonical ID for a wood article path (raw label, may be
    a composed ditto path "Hewn, Fir : Unenumerated"). Species/kind lives
    in the LAST path segment; the processing category (hewn/sawn) anywhere
    in the path. Returns (canonical_id, rule) or (None, None) -> review."""
    segs = (raw or '').split(':')
    last = norm(segs[-1])
    whole = norm(raw)
    in_last = lambda *ws: any(w in last for w in ws)
    in_whole = lambda *ws: any(w in whole for w in ws)
    # guard: non-wood materials that share wood keywords ("STONE ... Rough,
    # Hewn"; "Bark for Tanning Oak") must not be pulled into a wood series
    # unless a genuine wood species/form word is present.
    WOODY = ('fir', 'oak', 'teak', 'mahog', 'stave', 'deal', 'batten', 'lath',
             'wainscot', 'timber', 'wood', 'veneer', 'spar', 'plank')
    if in_whole('stone', 'marble', 'slate', 'granite', 'bark', 'metal',
                'glass', 'coal', 'tanning') and not in_whole(*WOODY):
        return None, None
    hewn = 'hewn' in whole
    sawn = in_whole('sawn', 'split', 'planed', 'dressed', 'deals',
                    'battens')
    if hewn and sawn and 'rough' in whole:
        return 'wood-rough-combined', 'rough+hewn+sawn (1897+ consolidation)'
    if in_whole('stave'):
        return 'wood-staves', 'staves'
    if in_whole('lathwood', 'lath wood'):
        return 'wood-lathwood', 'lathwood'
    if in_last('mahogany'):
        return 'wood-mahogany', 'mahogany'
    if in_whole('house frame', 'joiner', 'cabinet'):
        return 'wood-house-frames', 'house frames/joinery'
    if in_last('unenumerated', 'other sorts', 'all other'):
        if sawn:
            return 'wood-sawn-unenumerated', 'sawn+unenumerated'
        if hewn:
            return 'wood-hewn-unenumerated', 'hewn+unenumerated'
        if in_whole('furniture', 'veneer', 'hardwood'):
            return 'wood-furniture-hardwoods', 'furniture/hardwoods residual'
        return 'wood-unenumerated', 'unenumerated (unqualified)'
    if in_whole('furniture', 'veneer', 'hardwood'):
        return 'wood-furniture-hardwoods', 'furniture/hardwoods'
    if in_last('teak'):
        # teak is imported hewn throughout the era
        return 'wood-hewn-teak', 'teak (hewn category)'
    if in_last('oak'):
        return 'wood-hewn-oak', 'oak (hewn category)'
    if in_last('fir'):
        if sawn:
            return 'wood-sawn-fir', 'sawn+fir'
        if hewn:
            return 'wood-hewn-fir', 'hewn+fir'
        return None, None                     # bare "Fir": context unknown
    if hewn:
        return 'wood-hewn-fir', 'bare hewn (fir is the default species)'
    if sawn:
        return 'wood-sawn-fir', 'bare sawn (fir is the default species)'
    return None, None


def load_confirmed():
    """Human-confirmed rows survive regeneration."""
    keep = {}
    if MAP.exists():
        for r in csv.DictReader(open(MAP)):
            if r.get('status') == 'confirmed':
                keep[(r['scope'], r['raw_norm'])] = r
    return keep


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'),
                         read_only=True)

    # ---- collect label variants from both tiers
    variants = {}                     # (scope, raw_norm) -> info
    for grp, art, y0, y1, n in con.execute("""
            SELECT article_group, article, min(year), max(year), count(*)
            FROM country_graded
            WHERE lower(article_group) LIKE '%wood%'
              AND lower(article_group) LIKE '%timber%'
              AND country_raw != 'TOTAL'
            GROUP BY 1, 2""").fetchall():
        key = ('tier2', norm(art) or '(blank)')
        v = variants.setdefault(key, {'example': art or '(blank)',
                                      'y0': y0, 'y1': y1, 'n': 0})
        v['n'] += n
        v['y0'], v['y1'] = min(v['y0'], y0), max(v['y1'], y1)
    for grp, art, y0, y1, n in con.execute("""
            SELECT article_group, article, min(year), max(year), count(*)
            FROM consensus
            WHERE lower(coalesce(article_group,'')) LIKE '%wood%'
              AND lower(coalesce(article_group,'')) LIKE '%timber%'
            GROUP BY 1, 2""").fetchall():
        key = ('tier1', norm(art) or '(blank)')
        v = variants.setdefault(key, {'example': art or '(blank)',
                                      'y0': y0, 'y1': y1, 'n': 0})
        v['n'] += n
        v['y0'], v['y1'] = min(v['y0'], y0), max(v['y1'], y1)

    confirmed = load_confirmed()
    rows = []
    n_mapped = n_review = 0
    for (scope, rn), v in sorted(variants.items()):
        if (scope, rn) in confirmed:
            rows.append(confirmed[(scope, rn)])
            n_mapped += 1
            continue
        cid, rule = canon_wood(v['example'])
        if cid:
            n_mapped += 1
        else:
            n_review += 1
        rows.append({'scope': scope, 'raw_norm': rn,
                     'example': v['example'], 'years': f"{v['y0']}-{v['y1']}",
                     'n_rows': v['n'], 'canonical_id': cid or '',
                     'rule': rule or 'UNMAPPED - needs review',
                     'status': 'auto' if cid else 'review'})
    MAP.parent.mkdir(exist_ok=True)
    with open(MAP, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['scope', 'raw_norm', 'example',
                                           'years', 'n_rows', 'canonical_id',
                                           'rule', 'status'])
        w.writeheader()
        w.writerows(rows)
    print(f'wood label variants: {len(variants)} '
          f'({n_mapped} mapped, {n_review} for review) -> {MAP}')
    for r in rows:
        if r['status'] == 'review' and int(r['n_rows']) >= 10:
            print(f"  REVIEW {r['scope']} {r['example'][:50]!r:52} "
                  f"{r['years']} n={r['n_rows']}")

    cmap = {(r['scope'], r['raw_norm']): r['canonical_id']
            for r in rows if r['canonical_id']}

    # ---- Tier 2 stitched export (imports, member rows, with grades)
    out2 = BASE / 'exports' / 'wood_country_year.csv'
    out2.parent.mkdir(exist_ok=True)
    all_rows = con.execute("""
            SELECT article, country_raw, year, unit, quantity, value,
                   q_grade, v_grade
            FROM country_graded
            WHERE flow='import'
              AND lower(article_group) LIKE '%wood%'
              AND lower(article_group) LIKE '%timber%'
              AND country_raw != 'TOTAL'""").fetchall()

    def ckey(ctry):
        c = norm(ctry)
        if c in ('british north america', 'dominion of canada'):
            c = 'canada'
        return c

    # parent country rows present per (cid, parent, year): port/region
    # sub-rows ("British North America : Canada") normally duplicate their
    # parent's total row and are skipped — but when OCR lost the parent row
    # the sub-rows are the only copy of the data, so include them then
    parents = set()
    for art, ctry, y, unit, q, v, qg, vg in all_rows:
        if ' : ' not in (ctry or ''):
            cid = cmap.get(('tier2', norm(art) or '(blank)'))
            if cid:
                parents.add((cid, ckey(ctry), y))

    series = defaultdict(lambda: [0.0, 0.0, None])   # qty, val, worst grade
    n_orphan = 0
    for art, ctry, y, unit, q, v, qg, vg in all_rows:
        cid = cmap.get(('tier2', norm(art) or '(blank)'))
        if not cid:
            continue
        if ' : ' in (ctry or ''):
            parent = ckey(ctry.split(' : ')[0])
            if (cid, parent, y) in parents:
                continue                     # parent total carries the data
            c = parent
            n_orphan += 1
        else:
            c = ckey(ctry)
        u = norm(unit)
        u = {'load': 'loads', 'lds': 'loads', 'ton': 'tons'}.get(u, u)
        s = series[(cid, c, y, u)]
        s[0] += q or 0
        s[1] += v or 0
        g = max(qg or 'C', vg or 'C')       # worst of the two grades
        s[2] = g if s[2] is None else max(s[2], g)
    print(f'orphan sub-rows folded into their parent country: {n_orphan}')
    with open(out2, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['commodity', 'country', 'year', 'unit', 'quantity',
                    'value', 'grade'])
        for (cid, c, y, u), (q, v, g) in sorted(series.items()):
            w.writerow([cid, c, y, u, f'{q:.0f}', f'{v:.0f}', g])
    print(f'\ntier 2 stitched series -> {out2} ({len(series):,} cells)')

    # ---- Tier 1 stitched export (national totals with tiers)
    out1 = BASE / 'exports' / 'wood_national_year.csv'
    nat = defaultdict(lambda: defaultdict(float))
    nat_tier = {}
    for art, flow, meas, y, v, tier in con.execute("""
            SELECT article, flow, measure, year, value, tier
            FROM consensus
            WHERE lower(coalesce(article_group,'')) LIKE '%wood%'
              AND lower(coalesce(article_group,'')) LIKE '%timber%'
            """).fetchall():
        cid = cmap.get(('tier1', norm(art) or '(blank)'))
        if not cid:
            continue
        k = (cid, flow, meas, y)
        nat[k]['v'] += v
        nat_tier[k] = max(nat_tier.get(k, 'A'), tier)   # worst contributing
    with open(out1, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['commodity', 'flow', 'measure', 'year', 'value', 'tier'])
        for k in sorted(nat):
            w.writerow([*k, f"{nat[k]['v']:.0f}", nat_tier[k]])
    print(f'tier 1 stitched series -> {out1} ({len(nat):,} cells)')

    # ---- continuity check at label transitions (tier 2, quantity,
    # same-unit comparisons only)
    print('\ncontinuity check (canonical x country x unit, qty jumps >3x '
          'between adjacent observed years):')
    bych = defaultdict(list)
    for (cid, c, y, u), (q, v, g) in series.items():
        if q > 0 and g in 'AB':      # grade-C cells are already quarantined
            bych[(cid, c, u)].append((y, q))
    n_jump = 0
    for (cid, c, u), pts in sorted(bych.items()):
        pts.sort()
        for (y1, q1), (y2, q2) in zip(pts, pts[1:]):
            if y2 - y1 <= 2 and max(q1, q2) > 5000 \
                    and (q2 > 3 * q1 or q1 > 3 * q2):
                n_jump += 1
                if n_jump <= 12:
                    print(f'  {cid:<26} {c[:22]:<22} {u[:8]:<8} '
                          f'{y1}:{q1:>12,.0f} -> {y2}:{q2:>12,.0f}')
    print(f'  total adjacent-year jumps: {n_jump}')


if __name__ == '__main__':
    main()
