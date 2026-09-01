# PIPELINE — how every table in this repository is rebuilt

*Workstream G of `COMPLETION_PLAN.md`. Until 2026-09-01 the rebuild orders lived in
plans, logs and session notes; this file is the one place. Every chain below is
"run in this order, from the repo root". Where a script takes no arguments it reads
and writes the fixed paths named in its docstring.*

All chains read the gitignored corpora: `raw/` (Chandra OCR of the UK volumes),
`raw_infinity/` (Infinity-Parser key of the same PDFs), `raw_canada/` (symlink to the
Canadiana + StatCan OCR; `INDEX.tsv` = primary witness, `INDEX_W2.tsv` = StatCan witness,
`NOPARSE`-prefixed notes are skipped by every driver), `pdfs/` (600 dpi page images for
adjudication). The UK database is `db/uk_trade.duckdb`; the Canadian tables are CSVs
under `db/canada/`.

---

## 1. UK imports by origin (DuckDB, `country_year_final` flow='import')

```
python3 scripts/parse_abstract.py             # Tier-1 abstracts (Chandra)   -> abstract_obs
python3 scripts/parse_infinity.py             # Tier-1 abstracts (Infinity)  -> infinity_obs
python3 scripts/parse_country.py              # origin tables (Chandra)      -> country_obs
python3 scripts/parse_country_infinity.py     # origin tables (Infinity)     -> country_obs_inf
python3 scripts/parse_tn_overlap.py           # tn_ volumes (annual T&N)     -> country_obs_tn, country_obs_tn_inf
python3 scripts/parse_twoup.py                # recovery parsers for layouts the main parser skips
python3 scripts/parse_runin.py
python3 scripts/build_dimensions.py           # commodity / country ids + aliases
python3 scripts/reconcile.py                  # Tier-1 cross-engine consensus  -> consensus
python3 scripts/reconcile_country.py          # Tier-2 block arbitration       -> country_consensus
python3 scripts/repair_country_as_article.py  # phantom-region repair
python3 scripts/repair_groups.py              # group authority (article_group_authority.csv + overrides)
python3 scripts/anchor_tier1.py               # block sums vs voted T1 totals
python3 scripts/grade_country.py              # magnitude grades            -> country_graded
python3 scripts/rescore_value.py              # unit-price corroboration    -> country_rescored
python3 scripts/vote_country_years.py         # cross-volume vote           -> country_year_consensus
python3 scripts/integrate_sources.py          # + twoup + runin + subentry + groupfix + infonly + manual -> country_year_final
```

**Before re-running any parser**: `group_repairs.csv` is `row_seq`-keyed. Snapshot
`country_obs` / `country_obs_inf` as `snap_*`, re-parse, then run
`scripts/rebase_group_repairs.py` once, or the hand repairs relabel innocent tables.

**Standing QC battery, after every `integrate_sources.py`:**

```
python3 scripts/build_viz_payload.py exports/viz_payload.json
python3 scripts/reconcile_baseline.py exports/viz_payload.json          # THE metric (exact01 / within5 / nodata)
python3 scripts/reconcile_country_vs_t1.py exports/viz_payload.json     # detectors A (country-sum vs T1) + B (spikes)
python3 scripts/reconcile_country_vs_t1.py exports/viz_payload.json --series   # C (holes) + D (dips/spikes)
python3 scripts/find_bracketed_gaps.py                                  # data-hole-data, ranked by GBP
python3 scripts/diff_payload_cells.py OLD.json exports/viz_payload.json # THE SHIP TEST — snapshot OLD before the change
```

Gold checks (external, do not tune to them): `validate_gold_numeric.py`,
`validate_gold_tier1.py`, `validate_gold_eandh.py`, `build_usability_table.py`.

Repair vocabulary consumed by the chain (all in `reference/`, all hand- or
script-curated and committed): `group_repairs.csv` (label_shift / supersede /
new_country / years), `group_aliases.csv`, `group_authority_overrides.csv`,
`manual_rows.csv`, `manual_t1.csv`, `flow_repairs.csv`, `anomaly_adjudications.csv`,
`commodity_curation.csv`, `human_review.csv`. See `reports/CAMPAIGN_SUMMARY.md` for the
refuted hypotheses — do not re-try them.

### 1a. The public map

```
python3 scripts/curate_commodities.py exports/viz_payload.json     # KEEP bucket (must precede the map)
python3 scripts/build_gazetteer.py
python3 scripts/reconcile_country_vs_t1.py exports/viz_payload.json # known-issues list for the page
python3 scripts/build_map_slim.py                                   # per-year arrays are [value, qty, rank]
python3 scripts/build_map_artifact.py                               # -> exports/trade_origins_map.html
NODE_PATH=~/.local/js/node_modules node scripts/smoke_map.js        # 17 smoke checks
```
Publish with the Artifact tool passing the existing `url=` so the link is kept.

---

## 2. UK exports and re-exports by destination (a recipe until workstream B2 lands)

There is no materialised table yet: the consumers apply value overlays to `country_obs`
rows of flow `export_uk` / `reexport` at load time. Regenerate the overlays in this
order (each writes one CSV in `reference/`):

```
python3 scripts/parse_tn_overlap.py                 # only if raw/ or the parser changed
python3 scripts/repair_edge_columns.py              # -> edge_column_repairs.csv
python3 scripts/detect_scaled_blocks.py --out reference/scaled_block_repairs.csv
python3 scripts/repair_row_slip.py                  # -> row_slip_repairs.csv      (cross-engine label slips)
python3 scripts/repair_label_merge.py               # -> label_merge_repairs.csv   (same-engine slips, neighbour volumes as witness)
#   reference/export_manual_repairs.csv is HAND-EDITED — never regenerated
python3 scripts/repair_section_closure.py           # -> section_closure_repairs.csv (reads the overlays above)
python3 scripts/build_capture_reassign.py           # -> capture_reassign.csv
python3 scripts/build_fused_splits.py               # -> fused_section_splits.csv (merges fused_section_splits_manual.csv)
python3 scripts/build_inf_fallback.py               # -> inf_fallback_rows.csv (inf-only closing sections)
```

Load order inside every consumer (`scripts/export_overlays.py` once B1 lands): value
overlays by raw key — export_cell, malformed, edge_column, row_slip, scaled_block,
label_merge, export_manual, section_closure (last) → `fused_section_splits` (row_seq
range, sets group/article/unit) → phantom relabel → promote_headings → reassign
(`group_reassign.csv` then `capture_reassign.csv`) → `group_name_folds` →
`export_group_families`.

Consumers and measurement:

```
python3 scripts/export_country_series.py --country "British North America" --country Canada --country Newfoundland --out reports/canada_export_series.csv
python3 scripts/export_destination_panel.py
python3 scripts/build_canada_explorer_data.py       # -> reports/canada_explorer.json (re-embed as `const D=` in canada_trade_explorer.html)
python3 scripts/reconcile_exports.py --min-year 1893 --repairs      # the export-side baseline
python3 scripts/diff_explorer_cells.py OLD.json reports/canada_explorer.json --min 2000   # THE SHIP TEST
```

Canada = "British North America" (includes Newfoundland) through 1896; separate
"Canada" and "Newfoundland" labels from 1897.

---

## 3. Canadian imports by origin (`db/canada/imports_general_rows.csv`)

The canonical chain — ORDER MATTERS, every step rewrites the rows CSV in place:

```
python3 scripts/ca_parse_imports.py               # Canadiana primary witness, regimes A/B/C (FY1868-1890)
python3 scripts/ca_merge_witnesses.py             # StatCan witness vote, regime C  (six passes L/R/B/F/I + sweeps)
python3 scripts/ca_merge_regimeA.py               # StatCan witness vote, regime A; Dominion recapitulation for 1874-75
python3 scripts/ca_infer_lost_articles.py         # article '?' blocks named from other volumes' article order
python3 scripts/ca_infer_lost_countries.py        # country '?' segments named from the volume's Abstract
python3 scripts/ca_export_country_year.py         # -> exports/canada_imports_country_year.csv, _article_country_year.csv, reports/canada_imports_origins.md
python3 scripts/ca_check_abstract.py              # -> reports/canada_abstract_check.md (the per-year ratio table)
```

Run whenever the corresponding input changes, NOT part of the chain:

```
python3 scripts/ca_parse_abstract.py              # a volume lands  -> db/canada/imports_abstract_rows.csv (the per-cell oracle)
python3 scripts/ca_parse_summary.py && python3 scripts/ca_check_summary.py   # No. 2 Summary = article-level Tier-1
python3 scripts/ca_parse_country_series.py        # prefatory by-country series -> reference/canada_country_series*.csv
python3 scripts/ca_parse_witness.py [regimeC] [regimeAB]   # witness OCR changed -> db/canada/imports_general_rows_w2.csv
```

Staged, not yet promoted (workstream A1/A2). Regime D, FY1891–97 — run in this order:

```
python3 scripts/ca_parse_regimeD.py               # Canadiana primary  -> db/canada/imports_general_rows_d.csv, reports/canada_regimeD_parse.md
python3 scripts/ca_parse_regimeD.py --witness     # StatCan witness    -> imports_general_rows_d_w2.csv, reports/canada_regimeD_witness_parse.md
python3 scripts/ca_merge_regimeD.py [--dry-run]   # block vote + Abstract room -> rows_d.csv rewritten, witness_patches_d.csv, reports/canada_regimeD_merge.md
```
(`ca_parse_abstract.py` covers 1891–97 since 2026-09-01 and must have run first.)
FY1898–1908: `ca_pair_spreads.py` + `ca_align_spreads.py` (→ `spread_rows_<tag>.csv`, graded
verified / bracketed / flagged), `ca_compare_witnesses.py` (two-witness agreement).

Hand-repair channel: `reference/canada_manual_repairs.csv` (strict match-or-abort).
Anchors: `reference/canada_printed_totals.csv` (national, FY1868–1908),
`reference/canada_country_series_voted.csv` (printed by-country EfC 1873–89 and
exports 1872+), the per-volume Abstract (1880+), per-article printed grand totals.

**The ship test**: copy `db/canada/imports_general_rows.csv` to the scratchpad BEFORE any
change, then

```
python3 scripts/ca_diff_abstract_cells.py OLD_rows.csv db/canada/imports_general_rows.csv
```

and read BETTER / WORSE per (fy, country, province) cell. Never snapshot after a
`CA_DEBUG_TABLE=` run (it writes a no-inference parse).

---

## 4. Cross-national instruments (workstreams C and D — being built)

```
python3 scripts/mirror_canada_uk.py     # -> reports/mirror_canada_uk.md  (UK CY vs blended Canadian FY; see COMPLETION_PLAN.md §1)
```

---

## 5. Analysis products and the docs site

`analyze_canada_reach.py` → `reports/canada_reach.*`; `analyze_ghost_acres.py` →
`reports/canada_ghost_acres.*`; `build_supply_network.py` →
`reports/canada_supply_network.*`. The public site is GitHub Pages from `main:/docs`;
republish by copying the rebuilt `reports/*.html` into `docs/` (keeping the footer nav)
and pushing.
