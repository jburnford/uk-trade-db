# DATA DICTIONARY — the analysis tables

*Workstream G of `COMPLETION_PLAN.md`. Columns of every table an outside user is
expected to read. Rebuild recipes are in `PIPELINE.md`; quality stages and validation
numbers in `README.md`, `reports/CAMPAIGN_SUMMARY.md` and
`reports/canada_completion_log.md`.*

## Conventions that hold everywhere

- **Values are the printed declared values**: pounds sterling for the UK tables, dollars
  for the Canadian tables (Canadian customs converted at £1 = $4.8666). Nothing is
  deflated or converted.
- **Years.** UK tables are calendar years. Canadian tables are FISCAL years: FY *y* runs
  1 July *y−1* – 30 June *y* for FY1868–FY1906; FY1907 is nine months (1 July 1906 –
  31 March 1907); FY1908 on runs 1 April – 31 March. Never re-key a fiscal year to a
  calendar year in these tables; the blend rule for comparisons is in
  `COMPLETION_PLAN.md` §1.
- **Origins are consignment, not production.** A UK "country" label is where the goods
  were shipped from; a Canadian one is the country "whence imported".
- `?` as a label means the OCR lost it and no inference could name it. It is kept, and
  its value is counted in the `?` column of the origins reports, never dropped.
- Never sum quantities across units. Value is always summable within a flow.

---

## UK — `country_year_final` (DuckDB `db/uk_trade.duckdb`; CSV copy `exports/_country_year_final.csv`)

Commodity × origin country × year, imports only (flow = `import` for every row today;
export and re-export rows arrive with workstream B2).

| column | meaning |
|---|---|
| `article_group` | printed group heading (e.g. `WOOL`), after group-authority repair |
| `article` | printed article line within the group |
| `country` | origin as printed; `Region : Sub` keeps a nested sub-entry (`British East Indies : Ceylon`) |
| `unit` | printed quantity unit, aliased (`cwt`, `Lbs`, `Loads`…); see `reference/` folds |
| `flow` | `import` (`export_uk`, `reexport` pending) |
| `year` | calendar year of trade |
| `quantity`, `value` | printed quantity and £ value |
| `source` | which extraction admitted the row: `consensus` (cross-engine, cross-volume vote), `twoup` / `runin` (recovery parsers, unverified), `subentry` (nested sub-row recovery), `groupfix` (relabelled glue block, `reference/group_repairs.csv`), `infonly` (Infinity-only page, gated on printed total), `human` (`manual_rows.csv`), `flowfix` |
| `q_tier`, `v_tier` | trust grade for quantity / value: `A` printed in ≥2 volumes and agreeing; `B` printed once but verified (block sums to printed total, engines agree, human-confirmed, or unit price in band); `C` unverified |
| `q_rank`, `v_rank` | the same as 1 / 2 / 3 for SQL thresholds (`WHERE v_rank <= 2`) |

Companion tables: `consensus` (Tier-1 national totals by commodity-year, cross-volume
voted), `country_rescored` (member rows with grades and unit-price verdicts),
`abstract_obs` / `country_obs` (raw parses, one row per printed line, both engines).
`exports/viz_payload.json` is the curated per-commodity view the baseline metric and
the public map are built from; `exports/commodity_usability.csv` grades each
gold-benchmarked commodity (TOTAL / BY-COUNTRY tiers).

## UK — `reports/canada_export_series.csv` (British produce to Canada; interim until B2)

One row per commodity × year × destination label, flow `export_uk` unless
`--flow reexport` was passed.

| column | meaning |
|---|---|
| `year`, `country` | calendar year; `British North America` (incl. Newfoundland) to 1896, `Canada` / `Newfoundland` from 1897 |
| `article_group`, `article`, `unit` | as printed, after the overlay recipe |
| `value`, `quantity` | Chandra reading (£) |
| `value_inf`, `engines_agree` | Infinity reading and whether the two agree |
| `section` | how the row's printed section closes against its printed total: `exact01` (≤0.1%), `within5`, `mod`, `gross`, `none` (no total) |
| `tier` | `A` section closes exact and engines agree · `B` closes exact, single engine · `C` closes within 5%, engines agree · `D` neither · `X` no printed total |
| `volume`, `own_year`, `row_seq` | source volume; `own_year`=1 when the volume's own trade year (vs a five-year comparative column); row position for repairs |

## Canada — `db/canada/imports_general_rows.csv` (one row per printed line, FY1868–1890)

Same schema for `imports_general_rows_w2.csv` (StatCan witness parse) and
`imports_general_rows_d.csv` (regime D, FY1891–97, staged).

| column | meaning |
|---|---|
| `fiscal_year` | Canadian fiscal year (see conventions) |
| `volume` | Canadiana / StatCan volume tag (`raw_canada/INDEX*.tsv`) |
| `table_seq`, `row_seq` | table number within the volume, row position — the repair key |
| `regime` | table layout: `A` 1868–75 by provinces, 8 value columns; `B` 1876–79 by provinces, 5 value columns; `C` 1880–90 by countries and provinces; `D` 1891–97 combined country/province column |
| `block_id` | article block counter within the table |
| `section` | `DUTIABLE` / `FREE` (blank where the volume does not split) |
| `section_label` | the printed section heading the row sits under |
| `article_parent`, `article` | parent heading(s) and leaf article as printed; `?` = heading lost |
| `country` | as printed; `?` = lost |
| `country_inferred` | `0` printed; `1` restored by the parser (page-break hijack, slip cascade); `2` inferred from the volume's Abstract by Countries and Provinces; `3` inferred cross-year |
| `province` | province into which imported (regime C; blank for national rows) |
| `row_kind` | `detail` (article × country × province) · `country_total` (article × country over provinces) · `article_province_total` · `article_total` · `article_total_fused` · `country_noprov` (regime A/B national row) · `recap` (Dominion recapitulation 1874–75) · `superseded_w2` (row replaced by the witness vote — kept for audit, excluded from sums) · `summary` · `heading_row` |
| `unit` | printed quantity unit (Canadian spellings, not aliased) |
| `qty_brit`, `qty_foreign`, `qty_land` | regime A only: quantity by British vessels / foreign vessels / land carriage |
| `qty_imp`, `val_imp` | quantity and $ value **imported** |
| `qty_efc`, `val_efc` | quantity and $ value **entered for (home) consumption** — the Abstract's measure |
| `duty` | $ duty collected |
| `flags` | semicolon list of repair provenance: `label_slip`, `fused`, `repaired`, `lost_heading_closed_with_next`, `article_inferred`, `witness_block_replaced` / `_inserted`, `witnessA_*` (regime-A vote), `superseded_by_witness*`, `pagebreak_hijacker_restored`, `grand_total_rejoined`, `junk_country_label`, `value_lost`, `unparsed`, … |
| `raw` | the OCR line the row was read from |

Sums: national totals = `detail` rows only (regime C) or `country_noprov` (A/B);
`recap` rows carry the 1874–75 Dominion statement used for the national series.

## Canada — `exports/canada_imports_country_year.csv` and `exports/canada_imports_article_country_year.csv`

| column | meaning |
|---|---|
| `fiscal_year`, `regime` | as above |
| `article_parent`, `article` | (article file only) leaf and parent, as printed, not yet curated (workstream A3 adds `commodity_key`) |
| `country` | normalised spelling (`ckey` folds: e.g. `Sp. W. Indies` = `Spanish West Indies`) |
| `section` | `DUTIABLE` / `FREE` / blank |
| `unit` | (article file only) |
| `rows` | number of source rows summed |
| `qty_imp`, `val_imp`, `qty_efc`, `val_efc`, `duty` | sums of the above |

Caveats printed in `reports/canada_imports_origins.md`: 1874–75 come from the Dominion
recapitulation; 1868–73 are incomplete (0.62–0.83 of print after the witness vote).

## Canada — anchors in `reference/`

- `canada_printed_totals.csv`: `fiscal_year, total_exports, total_imports,
  entered_for_consumption, duty, source` — printed national totals FY1868–1908 (FY1907
  nine months), majority-voted across prefatory No. 1 tables.
- `canada_country_series_voted.csv`: `measure` (`efc`, `duty`, `aggregate`, `exports`),
  `fiscal_year, country, value, n_attest, n_agree, sources` — the printed by-country
  series from the prefatory tables, voted across volumes. The authoritative origin
  (and destination) table at country level; the General Statement is the article layer
  beneath it.
- `canada_manual_repairs.csv`: hand repairs, strict match-or-abort.

## Canada — `db/canada/spread_rows_<tag>.csv` (FY1898–1908, staged)

Spread-joined rows with tariff-group columns: `tot_*` (total imports), `gt_*` (General
Tariff), `pt_*` (Preferential Tariff), `sx_*` (surtax), `efc_*` (entered for
consumption); `align_status` = `verified` / `bracketed` / `flagged`; `closes` = whether
the row's own arithmetic closes. Workstream A2 maps these into the rows schema.

## Wood (UK)

`exports/wood_country_year.csv`, `wood_country_year_voted.csv`, `wood_national_year.csv`,
`wood_wide/`: canonical wood id (`reference/wood_commodity_map.csv`, 13 ids) × origin ×
year × unit × grade. Consumed by the timber-data repository.
