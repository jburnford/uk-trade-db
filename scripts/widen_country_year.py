#!/usr/bin/env python3
"""Widen the voted wood-by-country series into standardized country x year matrices.

Input : exports/wood_country_year_voted.csv (canonical-country voted, long)
Output: exports/wood_wide/<commodity>.csv        per-commodity quantity matrix
        exports/wood_country_wide.csv             master (all commodities stacked)
        exports/wood_country_wide_tier.csv        master, worst-tier per cell
        reference/country_standardize.csv         source_label -> standard, reviewable
        reports/wood_country_wide.md              decisions + caveats + coverage

Standardization goal: fixed country COLUMNS and a complete 1872-1899 year GRID
per commodity, so a series is comparable across years. The historical source was
NOT standard, so we reconcile explicitly and flag what we merged:
  * Label drift            united states of america -> United States;
                           british india bombay and scinde -> British India & Burma
  * Sub-region SUMMING     the US "On the Atlantic / On the Pacific / (residual)"
                           split, colonial West-Africa variants, and the
                           Australasian colonies are summed into one standard
                           country (distinct source labels -> one column).
  * Duplicate collapse     identical source labels repeated in a year (e.g. the
                           stray 386,003 'united states of america' in sawn-fir
                           1896) keep only the best-attested row (n_volumes,
                           n_agree, tier) BEFORE summing, so a bad duplicate does
                           not inflate the total.
  * 0 == missing           a zero from a major origin means "not separately
                           returned / not parsed that year", not zero trade ->
                           rendered blank.
  * Cell tier              worst (A<B<C) tier among the rows summed into the cell.
Every cell's confidence lives in the *_tier companion; the quantity matrices are
numbers only so they drop straight into a spreadsheet.
"""
import csv
from collections import defaultdict
from pathlib import Path

BASE = Path('/home/jic823/uk_trade_db')
SRC = BASE / 'exports' / 'wood_country_year_voted.csv'
WIDE_DIR = BASE / 'exports' / 'wood_wide'
XWALK = BASE / 'reference' / 'country_standardize.csv'
REPORT = BASE / 'reports' / 'wood_country_wide.md'

YEARS = list(range(1872, 1900))          # full standardized grid
TIER_RANK = {'A': 0, 'B': 1, 'C': 2, '': 3}

# ------------------------------------------------------------------ crosswalk
# source label (as in voted file) -> standardized country column.
# Anything not listed is Title-cased as-is and logged as UNMAPPED for review.
COUNTRY_MAP = {
    # majors -----------------------------------------------------------------
    'canada': 'Canada',
    'newfoundland': 'Newfoundland',
    'sweden': 'Sweden',
    'norway': 'Norway',
    'sweden and norway': 'Sweden & Norway',   # rare combined print; kept distinct
    'russia': 'Russia',                        # NB: includes Finland (unlike TTJ)
    'germany': 'Germany',
    'france': 'France',
    'holland': 'Netherlands',
    'belgium': 'Belgium',
    'denmark': 'Denmark',
    'portugal': 'Portugal',
    'spain': 'Spain',
    'italy': 'Italy',
    'greece': 'Greece',
    'turkey': 'Turkey', 'turkey european': 'Turkey',
    'roumania': 'Romania',
    'austrian territories': 'Austria-Hungary',
    'gibraltar': 'Gibraltar', 'malta': 'Malta', 'madeira': 'Madeira',
    'channel islands': 'Channel Islands',
    # United States (siblings that SUM: coast splits + residual) --------------
    'united states of america': 'United States',
    'on the atlantic': 'United States',
    'on the pacific': 'United States',
    'southern ports': 'United States',
    # Latin America / Caribbean ---------------------------------------------
    'brazil': 'Brazil', 'argentine republic': 'Argentina', 'uruguay': 'Uruguay',
    'chili': 'Chile', 'peru': 'Peru', 'mexico': 'Mexico',
    'central america': 'Central America', 'costa rica': 'Costa Rica',
    'nicaragua': 'Nicaragua', 'venezuela': 'Venezuela',
    'new granada': 'Colombia', 'republic of colombia': 'Colombia',
    'united states of colombia': 'Colombia',
    'cuba and porto rico': 'Cuba & Puerto Rico',
    'hayti': 'Haiti & Santo Domingo', 'hayti and st domingo': 'Haiti & Santo Domingo',
    'danish west india islands': 'Danish West Indies',
    'spanish west india islands': 'Spanish West Indies',
    'british west india islands': 'British West Indies',
    'british west indian islands': 'British West Indies',
    'british west indies': 'British West Indies',
    'british guiana': 'British Guiana', 'dutch guiana': 'Dutch Guiana',
    'british honduras': 'British Honduras', 'honduras not british': 'Honduras',
    'bermudas': 'Bermuda', 'falkland islands': 'Falkland Islands',
    # Asia ------------------------------------------------------------------
    'british india and burma': 'British India & Burma',
    'british india bombay and scinde': 'British India & Burma',
    'british ea indies': 'British East Indies',
    'ceylon': 'Ceylon', 'china': 'China', 'hong kong': 'Hong Kong',
    'japan': 'Japan', 'java': 'Java', 'siam': 'Siam',
    'philippine islands': 'Philippines',
    # Africa (West-Africa colonial variants SUM into one) --------------------
    'cape of good hope': 'Cape of Good Hope',
    'british possessions in south africa': 'Cape of Good Hope',
    'mauritius': 'Mauritius', 'madagascar': 'Madagascar', 'egypt': 'Egypt',
    'morocco': 'Morocco', 'east coast of africa': 'East Africa',
    'gold coast colony': 'Gold Coast', 'the gold coast': 'Gold Coast',
    'the gold coast colony': 'Gold Coast', 'niger protectorate': 'Niger Protectorate',
    # French Empire — kept distinct from British possessions
    'french possessions in west ern africa': 'French West Africa',
    'french possessions in west ern africa senegambia': 'French West Africa',
    'french possessions in western africa': 'French West Africa',
    'french west africa': 'French West Africa',
    # non-attributable ("foreign"/undesignated) — cannot be assigned to an empire
    'west africa not distinguished': 'West Africa (unspecified)',
    'west coast of africa foreign': 'West Africa (unspecified)',
    'west coast of africa not particularly designated': 'West Africa (unspecified)',
    'western africa': 'West Africa (unspecified)',
    'western coast of africa': 'West Africa (unspecified)',
    'western coast of africa not particularly designated': 'West Africa (unspecified)',
    'the west coast of africa': 'West Africa (unspecified)',
    # Australasian colonies SUM ---------------------------------------------
    'australasia': 'Australasia', 'australia': 'Australasia',
    'west australia': 'Australasia', 'new south wales': 'Australasia',
    'new zealand': 'Australasia', 'victoria': 'Australasia',
    # residual buckets (kept as explicit categories) -------------------------
    'other countries': 'Other foreign countries',
    'other foreign countries': 'Other foreign countries',
    'oth foreign countries': 'Other foreign countries',
    'unenumerated': 'Other foreign countries',
    'other british possessions': 'Other British possessions',
    'other british posses sions': 'Other British possessions',
}
# clearly-not-a-country OCR bleed -> drop
JUNK = {'mahogany', 'lbs 314 385', 'lbs 810 980', 'sheep and lambs'}

# which standard countries are formed by summing >1 distinct source geography
SUMMED = {'United States', 'French West Africa', 'West Africa (unspecified)',
          'Australasia', 'British India & Burma', 'Cape of Good Hope', 'Colombia'}

MAJOR_ORDER = ['Canada', 'Newfoundland', 'United States', 'Sweden', 'Norway',
               'Sweden & Norway', 'Russia', 'Germany', 'France', 'Netherlands',
               'Belgium', 'Denmark', 'Portugal', 'Spain', 'Italy',
               'Austria-Hungary']
REAL_UNITS = {'loads', 'tons'}


def col_order(countries):
    majors = [c for c in MAJOR_ORDER if c in countries]
    rest = sorted(c for c in countries if c not in majors)
    return majors + rest


def build_cells():
    """Reproduce the standardized cells from the voted source.

    Returns cell_q, cell_tier (as main writes) plus cell_meta (provenance:
    max n_volumes/n_agree and the source labels summed into the cell) and the
    per-commodity majority unit. Shared by main() and the viz-data build so
    both use exactly one standardization.
    """
    rows = list(csv.DictReader(open(SRC)))
    unmapped = defaultdict(int)

    # ---- commodity -> majority real unit (loads/tons); blank/junk unit = majority
    unit_votes = defaultdict(lambda: defaultdict(int))
    for r in rows:
        if r['unit'] in REAL_UNITS:
            unit_votes[r['commodity']][r['unit']] += 1
    maj_unit = {c: max(v, key=v.get) if v else '' for c, v in unit_votes.items()}

    # ---- group source rows -> (commodity, std_country, year) -> {source_label -> best row}
    # keeping only the BEST row per identical source_label (dedup) so a stray
    # duplicate can't inflate; distinct labels survive to be summed later.
    grp = defaultdict(lambda: defaultdict(dict))   # key -> label -> {q,tier,vols,agree}
    dropped_unit = 0
    for r in rows:
        c, raw, y = r['commodity'], r['country'].strip(), int(r['year'])
        if raw in JUNK or not raw:
            continue
        std = COUNTRY_MAP.get(raw)
        if std is None:
            unmapped[raw] += 1
            std = raw.title()
        # unit gate: skip rows carrying a DIFFERENT real measure than the commodity
        if r['unit'] in REAL_UNITS and r['unit'] != maj_unit.get(c, r['unit']):
            dropped_unit += 1
            continue
        try:
            q = int(float(r['quantity'] or 0))
        except ValueError:
            q = 0
        tier = (r.get('q_tier') or '').strip()
        vols = int(r.get('n_volumes') or 0)
        agree = int(r.get('n_agree') or 0)
        key = (c, std, y)
        cur = grp[key].get(raw)
        cand = {'q': q, 'tier': tier, 'vols': vols, 'agree': agree}
        # best row for an identical label: more volumes, then more agreement, then better tier
        if cur is None or (vols, agree, -TIER_RANK.get(tier, 3)) > \
                (cur['vols'], cur['agree'], -TIER_RANK.get(cur['tier'], 3)):
            grp[key][raw] = cand

    # ---- collapse to one cell per (commodity, std_country, year): SUM distinct labels
    cell_q, cell_tier, cell_meta = {}, {}, {}
    for key, labels in grp.items():
        tot = sum(d['q'] for d in labels.values())
        if tot <= 0:                      # 0 == missing (not zero trade)
            continue
        worst = max((d['tier'] for d in labels.values() if d['tier']),
                    key=lambda t: TIER_RANK.get(t, 3), default='')
        cell_q[key] = tot
        cell_tier[key] = worst
        cell_meta[key] = {
            'vols': max(d['vols'] for d in labels.values()),
            'agree': max(d['agree'] for d in labels.values()),
            'labels': sorted(labels),           # source labels summed
            'n_labels': len(labels),
        }
    return cell_q, cell_tier, cell_meta, maj_unit, unmapped, dropped_unit


def main():
    cell_q, cell_tier, cell_meta, maj_unit, unmapped, dropped_unit = build_cells()
    commodities = sorted({k[0] for k in cell_q})
    WIDE_DIR.mkdir(parents=True, exist_ok=True)

    # ---- per-commodity matrices + master ----------------------------------
    master_rows, master_tier_rows = [], []
    all_countries = set()
    for com in commodities:
        countries = sorted({k[1] for k in cell_q if k[0] == com})
        all_countries |= set(countries)
        cols = col_order(countries)
        with open(WIDE_DIR / f'{com}.csv', 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['year'] + cols + ['Total'])
            for y in YEARS:
                vals = [cell_q.get((com, c, y), '') for c in cols]
                tot = sum(v for v in vals if isinstance(v, int))
                if not tot:
                    continue                # skip empty year rows in per-commodity file
                w.writerow([y] + vals + [tot])
        for y in YEARS:
            qrow = {'commodity': com, 'unit': maj_unit.get(com, ''), 'year': y}
            trow = dict(qrow)
            has = False
            for c in countries:
                q = cell_q.get((com, c, y))
                if q:
                    qrow[c] = q
                    trow[c] = cell_tier.get((com, c, y), '')
                    has = True
            if has:
                master_rows.append(qrow)
                master_tier_rows.append(trow)

    master_cols = col_order(all_countries)
    fieldnames = ['commodity', 'unit', 'year'] + master_cols
    for path, data in [(BASE / 'exports' / 'wood_country_wide.csv', master_rows),
                       (BASE / 'exports' / 'wood_country_wide_tier.csv', master_tier_rows)]:
        with open(path, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for r in data:
                w.writerow(r)

    # ---- crosswalk (reviewable) -------------------------------------------
    XWALK.parent.mkdir(exist_ok=True)
    with open(XWALK, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['source_label', 'standard_country', 'summed_subregion', 'note'])
        seen = set()
        for raw, std in sorted(COUNTRY_MAP.items(), key=lambda kv: (kv[1], kv[0])):
            note = 'combined print (cannot split)' if std == 'Sweden & Norway' else ''
            w.writerow([raw, std, 'yes' if std in SUMMED else '', note])
            seen.add(raw)
        for raw in sorted(JUNK):
            w.writerow([raw, 'DROP', '', 'OCR bleed, not a country'])
        for raw in sorted(unmapped):
            w.writerow([raw, raw.title(), '', f'UNMAPPED — review ({unmapped[raw]} rows)'])

    # ---- report ------------------------------------------------------------
    write_report(commodities, cell_q, cell_tier, maj_unit, all_countries,
                 unmapped, dropped_unit)

    print(f'commodities: {len(commodities)}   standard countries: {len(all_countries)}')
    print(f'cells: {len(cell_q):,}   dropped conflicting-unit rows: {dropped_unit}')
    if unmapped:
        print('UNMAPPED source labels (review reference/country_standardize.csv):')
        for raw, n in sorted(unmapped.items(), key=lambda kv: -kv[1]):
            print(f'  {raw!r}: {n}')
    print(f'wrote {len(commodities)} per-commodity matrices to {WIDE_DIR}')
    print('wrote exports/wood_country_wide.csv (+_tier), reference/country_standardize.csv,',
          'reports/wood_country_wide.md')


def write_report(commodities, cell_q, cell_tier, maj_unit, all_countries,
                 unmapped, dropped_unit):
    lines = ['# Wood imports by country, standardized wide (1872–1899)', '',
             'Widened from `exports/wood_country_year_voted.csv` (cross-volume, ',
             'cross-engine voted) by `scripts/widen_country_year.py`. Fixed country ',
             'columns + a complete 1872–1899 year grid per commodity, so series are ',
             'comparable across years. Values are in each commodity’s native unit ',
             '(loads or tons); a **blank means the origin was not separately returned ',
             'that year** (source zeros are treated as missing, not zero trade).', '',
             '## Files', '',
             '- `exports/wood_wide/<commodity>.csv` — per-commodity matrix (year rows × country cols + Total).',
             '- `exports/wood_country_wide.csv` — all commodities stacked (one row per commodity×year).',
             '- `exports/wood_country_wide_tier.csv` — same shape, cell = worst contributing tier (A/B/C).',
             '- `reference/country_standardize.csv` — the source-label → standard-country crosswalk (reviewable).', '',
             '## The world was not standard — what we reconciled', '',
             '- **United States** is summed from the coast split the source introduced in ',
             '  1893 (*On the Atlantic* + *On the Pacific* + an unspecified *United States* ',
             '  residual); pre-1893 it is the single *United States of America* line. A stray ',
             '  duplicate (sawn-fir 1896, 386,003) is dropped by keeping only the best-attested ',
             '  row per identical label before summing.',
             '- **Empires kept distinct.** *French West Africa* (the explicitly French ',
             '  possessions/Senegambia) is a separate column from British African possessions ',
             '  (*Gold Coast*, *Niger Protectorate*, *Cape of Good Hope*); the residual ',
             '  *West Africa (unspecified)* holds only the non-attributable "foreign / not ',
             '  distinguished" labels that cannot be assigned to any empire. **Australasia** ',
             '  sums the British colonies (Victoria, NSW, New Zealand, West Australia).',
             '- **British India & Burma** absorbs the 1877 *Bombay and Scinde* variant.',
             '- **Russia** follows the UK returns and **includes Finland** — unlike the TTJ ',
             '  count series, which lists Finland separately. Do not compare the two Russias naively.',
             '- **Sweden & Norway** is kept as its own column for the rare years the source ',
             '  printed them combined; in every other year Sweden and Norway are already split.',
             '- Cell **confidence** = the worst voting tier (A<B<C) of the rows summed into it; ',
             '  see the `_tier` companion. Tier ≠ attribution: a digit-perfect number filed under ',
             '  the wrong year/commodity is still its tier.', '',
             f'Dropped {dropped_unit} rows carrying a unit different from their commodity’s ',
             'majority measure (genuine measure confusion, not summable).', '']
    if unmapped:
        lines += ['**Unmapped source labels needing review:** ' +
                  ', '.join(f'`{r}`' for r in sorted(unmapped)), '']
    lines += ['## Per-commodity coverage', '',
              '| commodity | unit | years | countries | cells | %A | %B | %C |',
              '|---|---|--:|--:|--:|--:|--:|--:|']
    for com in commodities:
        ks = [k for k in cell_q if k[0] == com]
        yrs = sorted({k[2] for k in ks})
        cty = len({k[1] for k in ks})
        tiers = [cell_tier[k] for k in ks]
        n = len(tiers)
        pa = sum(t == 'A' for t in tiers) / n
        pb = sum(t == 'B' for t in tiers) / n
        pc = sum(t == 'C' for t in tiers) / n
        span = f'{yrs[0]}–{yrs[-1]}' if yrs else '—'
        lines.append(f'| {com} | {maj_unit.get(com, "")} | {span} | {cty} | {n} '
                     f'| {pa:.0%} | {pb:.0%} | {pc:.0%} |')
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
