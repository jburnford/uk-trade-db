# Completion plan — working log

One entry per workstream step of `COMPLETION_PLAN.md`: what ran, the numbers, what was
decided. The Canadian-imports phases keep their own log in `canada_completion_log.md`.

## G-now — push, PIPELINE.md, DATA_DICTIONARY.md (2026-09-01, commits 9086a9b, 1st doc commit)

27 unpushed commits pushed. `PIPELINE.md` encodes the three chains (UK imports, the UK
export overlay recipe, Canadian imports) with their ship tests and QC battery;
`DATA_DICTIONARY.md` documents every analysis table's columns, the fiscal-year and
valuation conventions, and the `row_kind` / `flags` / `source` / tier vocabularies.

## B1 — one loader for the export overlay recipe (2026-09-01)

`scripts/export_overlays.py`: `load_repairs` (the eight value-overlay CSVs, keyed on the
raw parse and the bad value), `repair_value`, `load_flow_rows` (country_obs + the
inf-only closing sections), `relabel` (fused splits → phantom relabel → optional heading
promotion), `load_folds` / `load_reassign` / `load_families`, `PRIMARY_OVERRIDE`,
`is_primary`, `CANADA_LABELS`. Five copies folded in (`export_country_series`,
`export_destination_panel`, `build_canada_explorer_data`, `reconcile_exports`,
`build_fused_splits`). **Regression: all four consumers' outputs byte-identical
before/after** (explorer JSON, Canada series CSV, destination panel CSV, reconcile log).

## C1 — the aggregate mirror (2026-09-01)

`scripts/mirror_canada_uk.py` → `reports/mirror_canada_uk.md` + `.csv`. UK side = own-year
British produce + re-exports to British North America / Canada (Newfoundland excluded
where printed separately), at $4.8666; Canadian side = parsed value imported from Great
Britain, blended 0.5·FY(y) + 0.5·FY(y+1); three-year sums as the stricter test; the
printed prefatory EfC series as the Canadian side at print.

**Result: 19 years with both sides, 15 pass, 4 flag.** 1875–1889 every year passes:
single-year ratios 0.85–1.11, three-year ratios 0.94–1.06, and the printed-series
ratio agrees with the parsed one to ±0.02 in every year. Two independently built
databases, two governments' books, one ocean — this is the strongest external check
either database has.

The flags, and what they say:
- **1870 (0.56), 1872 (0.80)**: the Canadian side is regime A at 0.62–0.83 of print
  (both scans fail). Expected; nothing to do on the UK side.
- **1873 (1.19; printed 1.47), 1874 (1.39; printed 1.42)**: the Canadian side is at
  print (Dominion recapitulation; printed series agrees), so **the UK export side reads
  roughly 30% under in 1873–74** — about £3M a year missing. First look by group: IRON
  drops from £2.45M (1872) to £1.7M (1873–74) while Canada's railway-iron boom peaked;
  and 1872 carries £1.5M under GLASS with HABERDASHERY at 0 (the lost-heading-as-group
  class; 1873–76 haberdashery is £1.0–1.1M) — a label defect, not the missing mass.
  Filed for **B4**; the missing £3M is not yet located.

No Canadian side yet for CY1890–1900 (FY1891+ not in the exports; A1/A2).
