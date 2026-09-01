# Canada imports completion — working log

One section per phase of `CANADA_IMPORTS_PLAN.md`: what ran, the numbers, what was decided.

## Phase 0 — bookkeeping (2026-08-31, commit 2b01a6e)

FY1891–1897 registered in `raw_canada/INDEX.tsv` with the new **NOPARSE note-prefix**
(all four INDEX-driven parsers skip such rows); FY1897 = `32_5`, `32_4` demoted to
secondary. `reference/canada_printed_totals.csv` extended 1890–1908 by per-cell majority
vote across five StatCan prefatory No. 1 tables (FY1907 is a genuine 9-month year;
FY1908 single-witness). `sweep_junk_country_labels`: 9 country labels recovered from the
article slot, 177 numeric-junk labels → `?`. Ship test 0/0.

## Phase 1 — page-break Total-block defect (2026-08-31, commit 315c62b)

Pass (a'') + hijacker-label restore. 34 carry-backs, 125 restored rows.
Country-`?` $2,995,809 → $945,345; 1886 abstract 0.975 → 0.991, 1885 → 0.990.
Ship 20 better / 9 worse (worse = sub-$30K on polluted cells).
Full mechanics in `reports/canada_page_break_total_findings.md`.

## Phase 2 — shortlist with in-table proofs (2026-08-31, commits d4381c8..cd0df63)

- **2a** Abstract oracle row-sanity (`repair_row_arithmetic`): 23 cells repaired by the
  two-identity pin (row `dut+free==total` × column `TOTAL−Σcountries`), 19 flagged.
  1881 France Ontario phantom dead; 1881 abstract column now equals the printed national
  EfC exactly.
- **2b** Province-order pairs arbitrated by the abstract: 3 swapped, 1 confirmed,
  10 undecided (left flagged). Ship 10/0.
- **2c** 1880 tea t418-419 solved by exhaustive assignment (both value columns exact,
  duty pins to the cent); **manual-repair channel built**
  (`reference/canada_manual_repairs.csv`, strict match-or-abort). Ship 12/0.
- **2d** Duplicate-name pairs: corkwood = already distinguished by parent 'Barks' (no
  defect); champagne = nominal only; spades renamed (Summary EXACT); ginger span renamed
  (raw heading + Summary EXACT); calf-kid 1887 = ONE article, its 'TOTAL' rows were the
  US run (all exact), remaining GB/US runs lost at the page break → phase 3 list.
  Ship 9/1 (the 1 over-ruled by exact closure).

**State after phase 2**: country-`?` $939,991, article-`?` $1,982,848; abstract ratios
1880-90: 1.000/.978/.990/.988/.991/.990/.991/.996/.991/.999/.988. Parked coverage:
`reports/canada_phase3_coverage_list.md`.

## Phase 3 — StatCan second engine (2026-08-31, commit 32c36ca; IN PROGRESS)

**3a done**: `raw_canada/INDEX_W2.tsv` + `ca_parse_witness.py` →
`db/canada/imports_general_rows_w2.csv` (185,675 rows, 11 regime-C years). The regime
parser needed NO changes for the StatCan scans. Witness quality:
`reports/canada_witness_parse.md` (1882 is the witness's bad year, 1.121 — treat its
cells with suspicion in every gate).

**3b first merge done**: `ca_merge_witnesses.py` — **the chain now runs
parse → merge → infer_articles → infer_countries → export → check.**
Pass L label-transfer (11 runs $471K), pass I gated insertion (90 blocks $162K).
Ship 187/9. Country-`?` now $677,582.

**Still open in phase 3**:
- the value-fill class (Canadiana rows with BLANK values, witness has them — 1883 GB
  machinery is the type case);
- the misfiled-row class (1884 peaches GB run sits under 'Oranges and lemons' as bare
  country_total rows — witness shows the truth; needs a row-level correction pass);
- the big under cells still open: 1886 GB Ontario −1.02M (witness reads +2.6% over
  there — needs per-block arbitration, not cell fill), 1881 Newfoundland, 1882
  sugar-molasses, 1883/85 GB province unders;
- regime B years through the witness (cheap once trusted);
- 1890's unmatched abstract value 685,649.
