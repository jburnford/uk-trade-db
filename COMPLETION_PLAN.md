# Completion plan — from three datasets to one linked trade database

*Drafted 2026-09-01 at HEAD 6408384 after a full review of the corpus. This is the
top-level plan; `CANADA_IMPORTS_PLAN.md` (imports, phases 5–8 still open) and
`EXPORT_CAMPAIGN_PLAN.md` (UK exports, never executed as phases) sit beneath it and are
NOT superseded — this plan says in what order they get finished and what joins them.
Written to be executed by fresh sessions: read §0 and §1 first.*

## 0. The goal, restated

Identify Canada's economic relationship with the rest of the world in 1868–1908 even
where the goods flowed through Britain — and, in doing so, leave behind a database other
historians can use for different questions. That needs three datasets and two joins:

| dataset | source | state (2026-09-01) |
|---|---|---|
| **UK imports by origin** 1866–1900 | Annual Statements + T&N Accounts, two OCR engines | mature: 52.9% of judgeable commodity-years close exactly on print; a third of the corpus structurally cannot close |
| **UK exports + re-exports by destination** 1870–1900 | same volumes | a recipe, not a table: eight repair CSVs applied in a documented order inside four consumer scripts; `country_year_final` still carries only flow='import' |
| **Canadian imports by origin** FY1868–1908 | Canadiana + StatCan scans, two witnesses | regime C 1880–90 anchored to the Abstract at .985–1.004; 1868–73 capped at .62–.83 (both scans fail); 1891–97 parsed but unpromoted (.69–.99); 1898–1908 aligned but not in the schema |
| join 1: **mirror** (UK→Canada vs Canada←UK) | — | never built |
| join 2: **cross-national commodity key** | — | a dict inside `analyze_canada_reach.py`, UK-export→UK-import only; no Canadian article maps to anything British |

The end product is a fourth layer built on the joins: per commodity, what Canada
consumed, how much of it was British produce vs foreign goods forwarded through Britain,
and where the foreign goods (and the raw materials inside British goods) came from —
with the Canadian data itself closing the entrepôt lens's blind spot on direct trade.

## 1. Time and money: the rules that govern every cross-national comparison

**Fiscal years.** The Canadian returns run 1 July – 30 June for FY1868 through FY1906.
FY1907 is a nine-month year (1 July 1906 – 31 March 1907). FY1908 onward runs
1 April – 31 March. The UK Statements are calendar years. Nothing on the two sides
covers the same twelve months, so **no cross-national comparison is a closure proof**.
It is a ratio-band instrument. The rules:

- **T1 — blend, never shift.** UK calendar year *y* is compared with
  `0.5·FY(y) + 0.5·FY(y+1)` (FY1868–1906). The blend covers the same twelve months as
  CY(y) on the assumption of uniform flow within the year; St Lawrence navigation
  closes in winter, so the assumption is wrong at the margin and the tolerance must
  absorb it. For 1907 scale the nine-month year by 12/9 before blending and mark it;
  from CY1908 the blend is `0.25·FY(y) + 0.75·FY(y+1)`.
- **T2 — the trend test is the stricter one.** Three-year sums (UK CY y..y+2 vs the
  blended FYs) cancel most of the seasonal and lag error; use them to confirm any
  single-year flag before acting on it.
- **T3 — tolerance.** Single-year blended ratio within ±15% = pass; three-year sum within
  ±8% = pass. Outside both = a flag on whichever side is NOT at print (the side with
  the exact printed-total closure wins).
- **T4 — never re-key a Canadian FY into a calendar year in any export.** Canadian
  tables keep `fiscal_year` and a `fy_months` column (12, or 9 for 1907); the blend is
  computed only inside the mirror script.

**Money.** Canadian customs values are declared in dollars at the statutory
£1 = $4.8666. UK exports are declared value f.o.b. British port; Canadian imports are
"fair market value in the country whence exported" — near enough to f.o.b. that the
mirror band above holds. Use `val_imp` (value imported) on the Canadian side for the
mirror; `val_efc` (entered for consumption) is the consumption measure for analysis.

**Geography.** On the UK side "British North America" includes Newfoundland through
1896; from 1897 Canada and Newfoundland are printed separately. The mirror therefore
carries an upward bias on the UK side before 1897 (Newfoundland's imports from Britain,
not in the corpus) — state it, do not correct it. On the UK side the mirror sums
British produce **plus re-exports** to BNA; re-exports are ~10% of the flow and the
mirror fails without them.

**First run of the mirror (2026-09-01, aggregate, British produce only, no blend):**
implied $/£ is 4.6–6.3 in most years against par 4.87 — i.e. within band once
re-exports are added — but **1873–74 read 7.4 and 6.9**. The Canadian side for those
years is at print (Dominion recapitulation), so the UK export side for 1873–74 is the
first thing workstream B must look at.

## 2. Disciplines carried forward (unchanged, from both campaigns)

1. Snapshot before any change; per-cell diff (`diff_payload_cells.py`,
   `diff_explorer_cells.py`, `ca_diff_abstract_cells.py`) before believing a headline.
2. An exact printed closure beats any oracle, model, or plausibility argument.
3. Never synthesise rows to close a gap; coverage losses are second-witness territory.
4. A DB-level candidate list is never a target list — confirm against the payload.
5. Structural finds pay 15–115 cells; cell-by-cell pays 0–3. Stop a cell campaign on
   the two-rounds-under-+5 rule.
6. No value→acreage coefficients. The geography stays in £/$ and in named suppliers.

## 3. Workstreams

### A — Canadian imports to completion (`CANADA_IMPORTS_PLAN.md` phases 5.2–8; 5–7 sessions)

The slog. Order within A:
- **A1** Regime D witness merge (StatCan 1891–96 is on disk) + the GS-tail Abstract as
  per-cell oracle + promotion of FY1891–97 into `imports_general_rows.csv`. The single
  largest quality lever left anywhere in the Canadian corpus (six years at .69–.86).
- **A2** Promote FY1898–1908 spread rows into the schema (plan phase 6), keeping the
  tariff-group columns; `fy_months`=9 on 1907. Cheap; do it before curation so the
  fold vocabulary sees the full run.
- **A3** Curation key (plan phase 7) → `commodity_key` on the Canadian exports.
- **A4** Final rebuild + origins report 1868–1908 (plan phase 8).
- Explicitly deferred: 1868–73 beyond .62–.83 needs a third engine or re-imaging; file
  it, do not slog it.
- Acceptance: plan §4 as written, plus `fy_months` present and the 1874–75 Dominion
  source documented in the data dictionary (§G).

### B — UK exports and re-exports materialised (3–5 sessions)

The July plan's phase 0 and phase 1, scoped to what the goal needs.
- **B1** One shared overlay loader (`scripts/export_overlays.py`) replacing the four
  copies of `load_repairs`; every consumer imports it. Regression: the Canada explorer
  JSON is byte-identical before/after.
- **B2** Materialise flow='export_uk' and flow='reexport' rows into
  `country_year_final` (or a sibling `destination_year_final` with the same trust
  columns), destination × article × year, from the overlay recipe. The recipe stops
  being the database. `reconcile_exports.py` is the baseline metric per flow.
- **B3** Canada-destination first: every commodity, 1870–1900, both flows. Then the
  top ~30 export families for all destinations (the July finish line). Do not chase the
  small-commodity tail.
- **B4** Work the mirror flags from §1: 1873–74 first; then 1897–1900 (already known as
  the weakest export years).
- Acceptance: export and re-export rows in the DB with tiers; Canada-destination
  coverage ≥95% of the printed national export-to-BNA total per year; the aggregate
  mirror passes T3 in ≥25 of the 29 years.

### C — The mirror instrument (1 session to build; rerun at every phase boundary)

`scripts/mirror_canada_uk.py` → `reports/mirror_canada_uk.md`. Implements T1–T4 and
the money/geography rules of §1. Two levels:
- **C1 aggregate**: UK (produce + re-exports) to BNA/Canada vs Canadian `val_imp` from
  Great Britain, per year, blended, with the three-year sums. Build immediately after
  B1; it prioritises B4.
- **C2 by commodity**: same test per key row of the cross-national key (workstream D).
  Value first; quantity only where units are definitionally comparable.
- **C3 the other direction** (available NOW, no new parsing): UK imports *from* British
  North America by commodity (in `country_year_final`) vs Canadian exports to GB — the
  printed by-country export series in `reference/canada_country_series_voted.csv` is
  the aggregate side today; Statement No. 4 (workstream F) supplies the article side later.
- Acceptance: report exists, is regenerated by the rebuild recipe, and every flag names
  the side that is not at print.

### D — The cross-national commodity key (2–3 sessions, after A3 and B2)

`reference/canada_uk_commodity_key.csv`: Canadian `commodity_key` ↔ UK export
article/family ↔ UK import group, with a `basis` column (same good / manufactured-from /
none) and a `note`. Rules:
- Move the `CROSSWALK` dict out of `analyze_canada_reach.py` into this file first; then
  extend value-ranked from both sides until coverage ≥80% of Canada's imports from GB
  AND ≥80% of UK exports to BNA by value.
- **The C2 mirror is the acceptance test per key row**: a key row whose commodity mirror
  sits far outside band is a wrong key or a wrong series, and is not accepted until
  which one is known.
- Tariff-line churn on the Canadian side (1898, 1904) and era-split labels on the UK
  side are handled by the era-fold vocabularies of A3 and `export_group_families.csv`,
  not by loosening the key.

### E — The analysis layer (2–3 sessions, after D; standing thereafter)

Rebuild the three existing products (Entrepôt, Ghost Acres geography, Supply Network)
on linked data, then add what only the join makes possible:
- **E1** Per commodity: Canada's imports from Britain split into British produce vs
  forwarded foreign goods (from the UK side), and the forwarded share attributed to
  origin by the UK import-origin mix of that commodity-year (existing method).
- **E2** Direct trade from the Canadian side: imports from the US, France, Germany,
  West Indies, China/Japan etc. beside the through-Britain flow — the blind spot of the
  entrepôt lens, closed by the Canadian returns.
- **E3** Embodied inputs for British produce: the RULES dict becomes a reference CSV
  (`reference/embodied_inputs.csv`) with citations; stays a probable-supplier network,
  no quantities to acres.
- **E4** Whole-period geography first (the user's stated framing), then commodity-by-
  commodity narratives on top. Republish the docs site from the rebuilt reports.
- Acceptance: each product regenerates from the DB by script; caveats (blend, valuation,
  Newfoundland, allocation ≠ observation) printed on the page.

### F — Canadian exports, Statement No. 4 (4–6 sessions, after A)

The article × country sibling of the General Statement. Anchors already in hand:
`canada_country_series_voted.csv` (measure=exports, 379 rows, 1872+) and
`canada_printed_totals.csv` total_exports. Same chain pattern as imports (parse →
witness merge → infer → export → check), same disciplines. The C3 mirror against UK
imports from BNA is the external check from day one. Out of scope until A4 is done.

### G — Make it usable by others (½ session now, 1 session at the end)

- **Now:** push the 27 unpushed commits; write `PIPELINE.md` encoding the three chains
  and their rebuild order (today they live in the plan, the log, and Claude's memory —
  a new person cannot rebuild from the repo); a data dictionary for the 25-column
  Canadian rows CSV and the country_year exports (README covers UK only).
- **At the end:** LICENSE and CITATION.cff; a `Makefile` or driver that runs each chain
  and the three per-cell ship tests as regression; drop the `_snap*` leftover tables
  from the DuckDB file; one shared number-parser module for the seven copies; a
  versioned data release (Zenodo DOI) of `exports/` + `reference/` + the DuckDB.

## 4. Order of work

```
G-now (½)  →  B1 + C1 (1½)  →  A1 (2–3)  →  A2 (1)  →  B2–B4 (3–4)  →  A3 (2)
→  A4 (½)  →  D (2–3)  →  C2 (½)  →  E (2–3)  →  F (4–6)  →  C3 by article (½)  →  G-end (1)
```

Why this order: C1 is cheap and immediately tells B where to look; A1 is the biggest
quality gain per session in the corpus; B2 must precede D because a key against a
recipe cannot be regression-tested; D needs A3's Canadian key; E needs D; F is the
largest new parsing job and gains most from everything before it (the mirror, the key,
the witness machinery). A and B are independent enough to interleave when one stalls.

Roughly 25–35 sessions to F complete; 15–20 to the first linked analysis (through E).

## 5. Acceptance for the plan as a whole

1. One DuckDB with imports-by-origin, exports and re-exports by destination (UK side),
   and Canadian imports by origin (and exports, after F), every row carrying trust
   columns and `fy_months` where fiscal.
2. `reports/mirror_canada_uk.md` passing T3 in ≥25 of 29 years at the aggregate and
   published per key commodity.
3. `reference/canada_uk_commodity_key.csv` at ≥80% value coverage both sides, every row
   mirror-tested.
4. The linked analysis products regenerated from the DB by script and live on the
   docs site with their caveats.
5. `PIPELINE.md`, data dictionaries, LICENSE, CITATION.cff, a driver with the ship tests,
   and a DOI release.

## 6. Do not

- Do not shift Canadian fiscal years to calendar years anywhere but inside the mirror
  script, and never treat a mirror ratio as a closure proof (§1).
- Do not build the cross-national key against the export *recipe*; materialise first (B2).
- Do not chase the UK export small-commodity tail or the 1868–73 Canadian floor with
  cell-by-cell work; both are filed as third-engine / re-imaging items.
- Do not convert value to acreage, and do not present allocated origins as observed ones.
- Do not start F before A4; export-table findings met during A get filed, not worked.
