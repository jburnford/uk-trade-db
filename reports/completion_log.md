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

## A1 step 1–2 — regime D parser v3, the StatCan witness, the vote, and the Abstract oracle (2026-09-01)

`ca_parse_regimeD.py` v3 (Canadiana primary AND `--witness` for StatCan, same state machine):
- **The mass was never lost, it was mis-slotted.** The v1 parser right-padded rows' numbers, so a
  value-only article (`| value | | value | duty`) put its consumption value in the qty slot: a third of
  FY1896 vanished from every sum. v3 maps columns from each table's header (`Quantity Value Quantity
  Value Duty` = 5 cells, free-goods tables 4) and takes the LAST n cells positionally; the old
  heuristic is only the fallback (6% of rows).
- The one-row label slip: the unit line (`Tons.`) carries the first country's label with no numbers,
  and the OCR pairs label k with numbers k+1 until an unlabelled row re-syncs — a pending-label
  cascade (regime B's rule, conditional on the unit row). Recapitulation tables (header `PROVINCES
  INTO WHICH IMPORTED` without countries), recap sub-tables (`By Provinces` labels), section grands
  (`Total, Dutiable Goods`), long non-country headings carrying numbers, duplicated OCR rows — each
  its own row_kind or skip, none of it counted as detail. 1891's old 0.987 was inflated by ~20M of
  sugar recapitulation counted as detail.
- Instrument C (block closure) is in the report: ~700 blocks/yr (60–70M) close exactly on their own
  Total block.

`ca_parse_abstract.py` now reads the 1891–97 abstracts (same layout as regime C, two label variants
folded): **1891–94 sum to print exactly, 1895–96 at 0.999, 1897 0.977** — the per-country oracle.
`ca_check_abstract.ckey` gained the 1891+ spellings (U.S. America, Newfoundland incl. Labrador,
Spanish Poss., East Indies Dutch).

`ca_merge_regimeD.py`: block vote (fingerprint pairing; closed / mismatch / no_total semantics; witness
replaces only where it closes and Canadiana provably fails; superset rule for no-total pairs; whole
articles inserted only when closed, absent, and within BOTH the national and the per-country Abstract
room; duplicate blocks dropped; 6,475 blocks flagged `witnessD_agree` where both imagings read every
row identically).

| FY | primary v1 | primary v3 | witness v3 | **after vote** | corpus/abstract by country | GB | US |
|---|---|---|---|---|---|---|---|
| 1891 | 0.987* | 0.933 | 0.902 | **0.944** | 0.917 | 0.898 | 0.949 |
| 1892 | 0.819 | 0.883 | 0.940 | **0.901** | 0.896 | 0.848 | 0.919 |
| 1893 | 0.787 | 0.903 | 0.940 | **0.917** | 0.901 | 0.974 | 0.941 |
| 1894 | 0.861 | 0.956 | 0.972 | **0.980** | 0.971 | 0.981 | 0.974 |
| 1895 | 0.714 | 0.928 | 0.959 | **0.953** | 0.951 | 0.950 | 0.954 |
| 1896 | 0.691 | 0.907 | 1.035 | **0.929** | 0.915 | 0.974 | 0.881 |
| 1897 | 0.756 | 1.028 | 0.951 | **1.015** | 1.016 | 1.122 | 0.981 |

(*inflated by recap rows.) Staging only — `imports_general_rows_d.csv` is NOT yet promoted.

**Open for A1 close-out (next session):** the under is now concentrated in Great Britain and the
United States (1892 GB 0.848, 1896 US 0.881) — the 1,076 unpaired witness `no_total` blocks and the
2,788 no-total pairs are where it sits; admitting them needs the per-country room gate plus an
order-pairing repair for slipped Total blocks. 1897 GB reads 1.12 against an abstract that itself
lost 2.3% — locate the excess block. Then promotion: the chain scripts (infer, export, check) must
accept regime D rows (national = detail rows; province runs under dash-countries are detail, their
country_total is not).

## A1 step 3 — absorption guard, cross-closure, promotion; the mirror reaches the 1890s (2026-09-01)

- **A double count inside the vote**: a witness block that pairs with one Canadiana block can also
  contain every row of a second, unpaired Canadiana fragment (the same printed run split by a heading
  slip); the fragment survived beside the replacement (FY1891 'On all such goods costing 14 cts',
  Great Britain 1,976,017 twice). `absorb()` now supersedes any unpaired Canadiana block whose
  fingerprint is contained in an entering witness block (41 cases). 1891 fell from .944 to .925 —
  the honest number.
- **Exact cross-closure**: Canadiana kept the printed total but lost every country row, the
  witness's rows sum to Canadiana's own total to the dollar → the witness rows enter (15 blocks);
  fuzzy name pairing (≥0.85) for blocks one side read without country rows.
- **Promoted**: `ca_export_country_year.py` reads `imports_general_rows_d.csv` beside the main
  corpus; `exports/canada_imports_country_year.csv` and the origins report now run FY1868–1897,
  with the regime D caveat inline. National after vote: **1891 .925 / 1892 .896 / 1893 .917 /
  1894 .982 / 1895 .952 / 1896 .923 / 1897 1.015**; by country against the Abstract, GB
  .847/.839/.973/.981/.949/.973/1.122 and US .949/.914/.933/.977/.953/.869/.981. The residue is
  diffuse and two-sided (the two scans fail on different blocks; witness no-total blocks cannot be
  admitted without a proof) — third-engine territory per the plan, filed, not slogged.
- **The mirror, CY1890–1896 now covered: every year passes** (0.93–1.05 single, 0.97–1.03 three-
  year). 26 years, 22 pass; the four flags are unchanged (1870/72 Canadian regime A; 1873/74 UK
  side under). **A UK-side defect the mirror caught first**: CY1896 read 0.60 because as_1896's
  re-export TEA 'Total'-by-destination section carries QUANTITIES (lbs; TOTAL 34,027,806 = the
  year's tea re-exports in lbs) in the value column — British North America 4,842,458 lbs posed as
  £4.84M. Ten null-outs in `reference/export_manual_repairs.csv` (column-crossing class, whole
  section); the mirror now skips printed subtotal articles like the explorer does. Explorer
  per-cell diff: 0 changed (it never summed 'Total' rows).

## A2 — FY1898–1908 promoted (2026-09-01)

- **The aligner dropped every label-only left-page row** (article headings, and `United
  States—` opening a province run) because it aligns rows carrying numbers; FY1900 province
  runs then had no article and no country. `ca_align_spreads.left_rows` now folds pending
  heading labels onto the next value row (item-numbered headings included). All 13 spread
  files re-aligned (1 s each).
- `ca_promote_spreads.py`: the regime D state machine over the joined rows → regime `S` in
  the rows schema, tariff-group columns (GT / PT-Reciprocal / SX) kept, `align_status` and
  the right row's closure carried in `flags`.
- **Half the statement was never a spread.** The free-goods part has no tariff columns, fits
  on one page, and was never paired — dutiable-only sums read 0.48–0.59 of print. The regime
  D parser gained `only_free` mode (single-page four-column tables under the nearest
  `GENERAL STATEMENT OF IMPORTS` caption; export tables and spread halves excluded by their
  own header) and the promotion pulls them in as `single_page` rows.
- **N (val_efc) 1898–1908: .864 / .948 / .901 / .926 / .868 / .956 / .948 / .959 / .940 /
  .960 / .968**; val_imp .90–1.04. Single witness, no Abstract oracle yet (the 1898+ abstracts
  are not registered), 1898's `?` mass $8.7M (right-only rows without a left label).
- Origins report and `exports/canada_imports_country_year.csv` now run **FY1868–1908**. The
  mirror covers CY1870–1900: **30 years, 26 pass**, 1897–1900 at 0.95–1.10 single / 0.98–1.04
  three-year on the promoted data.
- Open for A2 close-out: the second witness for 1898/99 (StatCan) and 1900 (Canadiana, a
  fetch-and-OCR item); the 1898 `?` mass; the Abstract by Countries for 1898–1908 as oracle
  (`ca_parse_abstract` needs the StatCan volumes registered); FY1907 `fy_months`=9 in the
  exports (the mirror already scales it).
