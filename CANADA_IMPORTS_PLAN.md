# Canadian Imports Completion Plan — parse and clean FY1868–1908

*Drafted 2026-08-31 from a full review of the corpus at HEAD e0b7ad9. Written to be
executed by fresh sessions: read §0 first, then work §5 in order. Exports (Statement
No. 4 family) are explicitly AFTER this plan completes — nothing here builds them, but
§5 phase 0 protects the inputs they will need.*

## 0. Read this first

**The goal.** One analysable imports table — article × country (× province where
printed) × fiscal year, 1868–1908, in the `imports_general_rows.csv` schema — with
every year anchored to its printed national totals and the per-country cells anchored
to the printed Abstract. When this is done, Canadian exports begin.

**Where it stands (2026-08-31):**

| span | rows | form | state |
|---|---:|---|---|
| FY1868–1875 (regime A) | 27,993 | article × country | **broken** — national ratios 0.48–1.11, garbled right-hand facing pages in the bitonal Canadiana scan |
| FY1876–1879 (regime B) | 40,916 | article × country | good — EfC ratios 0.993–1.036 |
| FY1880–1890 (regime C) | 184,882 | article × country × province | good — abstract ratios 0.966–1.000, country `?` $3.0M / article `?` $3.4M on $2.6bn |
| FY1891–1897 | 91,394 | flat `"article > country"` label pairs (`ca_parse_unsplit.py`) | recovered, **not resolved into columns** |
| FY1898–1908 | 93,872 | spread-joined, graded (`ca_align_spreads.py`) | 70.2% verified / 85.7% incl. bracketed / 6.5% flagged; **not in the schema** |

Only FY1868–1890 (253,791 rows) reach `exports/canada_imports_*_year.csv`.

**The three disciplines that hold everywhere** (from the campaign to date — do not relax):

1. **Snapshot before any change**: copy `db/canada/imports_general_rows.csv` to the
   scratchpad, then read `ca_diff_abstract_cells.py OLD NEW` per (fy, country, province)
   cell before believing any headline ratio.
2. **An exact in-table closure beats the per-cell oracle.** Where several defects overlap
   in one abstract cell the oracle calls a correct fix WORSE; a detail sum that hits the
   printed article/country total exactly is the stronger proof.
3. **Never synthesise rows** to close a gap (refuted 2026-08-21: province-`?` detail
   rows from country_total − Σdetails launder garbled blocks). Coverage losses are
   re-OCR / second-witness territory, not arithmetic patches.

## 1. Inputs

**Witness 1 — Canadiana** (bitonal CIHM microfilm, Sessional Papers reprint):
`raw_canada/INDEX.tsv` → symlink to `/home/jic823/sessional_papers/output_trade_navigation/`.
FY1891–1897 mains exist on disk but are NOT yet in the index (see phase 0):
`oocihm.9_08052_{25_4,26_4,27_5,28_4,29_4,31_4,32_5}` under
`/home/jic823/sessional_papers/markdown/`. Note **FY1897 = `32_5`**; the currently
indexed `32_4` is the Trade & Commerce report with no General Statement.

**Witness 2 — StatCan CS4-4** (greyscale departmental edition, Chandra OCR):
`/home/jic823/sessional_papers/statcan_trade/ocr/` with `MANIFEST.tsv` naming a
`preferred_source` per year across three runs (`statcan_plato_may` 1850–1898,
`statcan_nibi_w2` 1850–76 + 1880/81/84 + 1890–1908 (no 1898), `statcan_plato_w2` 1899).
**Every fiscal year 1868–1908 has at least one StatCan `.md` on disk.** Same setting of
type as Canadiana, opposite imaging failure (verified FY1885 cell-for-cell; FY1897
two-witness agreement 89.6%). Chandra `.md` table HTML is byte-identical to `.html` —
settled, do not re-verify.

**Scripts** (all `scripts/ca_*.py`): the chain
`ca_parse_imports.py → ca_infer_lost_articles.py → ca_infer_lost_countries.py →
ca_export_country_year.py → ca_check_abstract.py` (ORDER MATTERS; `ca_parse_abstract.py`
is NOT in the chain — run it whenever a volume lands). Plus `ca_parse_unsplit.py`,
`ca_pair_spreads.py` / `ca_align_spreads.py`, `ca_compare_witnesses.py`,
`ca_check_unsplit.py`, `ca_parse_summary.py` / `ca_check_summary.py`.

**Anchors**: `reference/canada_printed_totals.csv` (1868–1889 only — phase 0 extends it),
`reference/canada_country_series_voted.csv` (printed EfC by country 1873–1889), the
per-volume Abstract by Countries and Provinces (printed through at least 1897), and
per-article printed grand totals in every General Statement.

## 2. Instruments (the validators, per phase acceptance)

- **N** — national ratio: Σ detail rows vs `canada_printed_totals.csv`, three columns
  (val_imp, val_efc, duty).
- **A** — abstract ratio + per-cell diff: `ca_check_abstract.py`,
  `ca_diff_abstract_cells.py`.
- **C** — in-table closure: article blocks exact / within 1% / under / over
  (`canada_imports_parse.md` per-year tables).
- **W** — two-witness cell agreement: `ca_compare_witnesses.py` (89.6% on FY1897 is the
  bar to beat or explain).
- **Q** — `?` masses: country-`?` and article-`?` dollars by year.

## 3. Invariants

- I1. A row's values belong to the label the PRINT gave them; every relabelling needs an
  exact closure proof or a printed-abstract witness (never plausibility alone).
- I2. Witness merge is a per-cell VOTE arbitrated by printed totals (user decision
  2026-08-28) — never pick-the-better-scan wholesale.
- I3. The freed side of any structural fix must be re-anchored: after moving rows out of
  a `?` block, the block's new owner needs its own proof (the FY1886 t525 note: the
  article has no printed total — the owner comes from the previous table's tail or the
  Abstract, NOT assumed GB).
- I4. New volumes/witnesses enter through the full chain plus `ca_parse_abstract.py`,
  then a per-cell diff on OLD years expecting 0/0 (cross-volume votes may move small
  cells; each move must be read).

## 4. Acceptance (for the plan as a whole)

1. Every FY 1868–1908 present in `imports_general_rows.csv` (or a successor with the
   same columns), one row per printed line, with `witness` provenance.
2. National ratios in [0.99, 1.01] on val_efc for every year, or the residual explained
   in writing (named blocks, named cause).
3. Country-`?` + article-`?` under 0.25% of detail value per year.
4. A curated commodity key giving continuous series for the top articles by value —
   measured as ≥60% of regime-C value in articles present in all years of their era
   (today: 8.9% verbatim, 15.2% normalised).
5. `reports/canada_imports_origins.md` rebuilt 1868–1908; per-cell ship test archived
   for the final state.

## 5. Work order

### Phase 0 — bookkeeping (½ session; do first, everything downstream reads these)

- **0a.** Register FY1891–1897 mains in `raw_canada/INDEX.tsv` (tags above), correcting
  the FY1897 entry to `32_5` and demoting `32_4` to a note (it stays valuable: its No. 6
  five-year national article series 1893–97 is a future Tier-1 witness).
- **0b.** Extend `reference/canada_printed_totals.csv` to FY1890–1908 from the prefatory
  No. 1 multi-year series in the latest volumes on disk (FY1890's own volume and the
  StatCan 1900s volumes carry the full run). Every later phase needs the **N** anchor.
- **0c.** Sweep the numeric junk country labels out of the regime-A export
  (`"2,829—407,370"` class, 1868/1877, ~$340K) — route to `?`, not deletion.
- Acceptance: chain re-run is a corpus no-op outside the touched cells; **N** column
  populated for all 41 years.

### Phase 1 — the queued page-break Total-block defect (1 session; proof already written)

`reports/canada_page_break_total_findings.md`. The previous article's Total block runs
past a page break; its tail provinces + grand total land on the next page and steal the
next article's first country label. FY1886 t525 alone is $1,644,588 — 55% of ALL
remaining country-`?`. Fix in the pass-(a) family but carrying the k preceding rows back
with the total; re-anchor the freed `?` run per I3. Re-check the same signature at
FY1885 t270, FY1890 t556, FY1881 t566.
- Acceptance: country-`?` $3.0M → ≤ $1.4M; per-cell diff read; FY1886 abstract ratio
  0.975 → ≥ 0.985.

### Phase 2 — regime C shortlist with in-table proofs (1–2 sessions; STOP at coverage)

Work ONLY the queued items that can close on printed arithmetic; anything that turns out
to be rows-never-read goes on the re-OCR/witness list for phase 3, not hand-worked:
- 1880 tea t418-419 China block (evidence in memory; label_slip interaction).
- Duplicate-name adjacent article pairs (Ginger ground/unground, Corkwood in every
  volume 1882–89, Champagne 1889, Spades 1885, Calf-kid 1887) — arbitrated by
  Summary-Statement value matching, article dimension only.
- The 7 `province_order_unarbitrated` candidates — arbitrate by the Abstract.
- 1881 Abstract row-sanity check (dut+free==total): catches the France Ontario
  1,359,178 misprint class inside the ORACLE itself before it misleads again.
- Known coverage items to PARK for phase 3: 1881 Newfoundland NS/Quebec free (~$630K),
  1886 GB Quebec/Ontario (~$2.0M), 1882 BWI/US sugar-molasses pages, 1887 Switzerland
  t505, 1888 US Quebec free, 1883/84/85 GB/US province unders.
- Acceptance: every shortlist item either closed exactly or filed on the phase-3 list
  with its cell and dollar value.

### Phase 3 — StatCan as second engine for regime C, 1880–1890 (2–3 sessions)

The structural answer to the coverage class no parser fix can reach.
- **3a.** Teach the driver a `witness` column (INDEX or a parallel witness index) so
  `ca_parse_imports.py` can run the StatCan `.md` for a year it already parses from
  Canadiana; rows carry (fy, witness, volume). Start with ONE year with big known
  coverage loss (1886 or 1883) to shake out StatCan-specific layout noise.
- **3b.** Build `ca_merge_witnesses.py`: per-cell vote at (fy, table-position, row)
  granularity, arbitrated by in-table closure then the printed Abstract (I2).
  Agreement → keep; disagreement → the witness whose block closes exactly wins;
  neither closes → flag for a targeted third opinion (Gemini, cell-level question —
  user decision 2026-08-28: not a blanket run).
- **3c.** Roll across 1880–1890, then re-run regime B years the same way (cheap once
  the machinery exists; B already parses well, expect small gains).
- Acceptance: the phase-2 parked list resolved or explained; every regime-C year
  abstract ratio ≥ 0.99; **W** reported per year.

### Phase 4 — regime A rebuilt from the greyscale witness, 1868–1875 (1–2 sessions)

The Canadiana right-hand facing pages are unrecoverable (bitonal microfilm); the StatCan
greyscale `.md`s for exactly these years are already on disk in BOTH runs. Parse them
under regime A, merge with the Canadiana left-page material via the phase-3 machinery.
This is the largest quality jump available anywhere in the corpus: eight years from
0.48–1.11 to regime-B territory.
- Acceptance: **N** ≥ 0.97 on val_efc for each of 1868–1875 (these years have no
  Abstract; the national anchor and article closures carry it), **C** exact-block counts
  reported, and the country_year export regenerated with the origins report's
  regime-A caveat removed or narrowed.

### Phase 5 — FY1891–1897 into the schema (2–3 sessions; new code, "regime D")

All seven volumes are "GENERAL STATEMENT (by Countries and Provinces)" but the design
changed: per article, country rows (national), then a `Total` block by PROVINCE, then a
grand total — a marginal table, not the crossed one. The unsplit rows already hold the
values; what is missing is the article/sub-article state machine (ditto marks,
`'" Sheep'` sub-articles, `'Total.... > Ontario'` province blocks).
- **5a.** Write the state machine over `ca_parse_unsplit.py`'s output (or fold into
  `ca_parse_imports.py` as regime D), emitting the standard schema: country rows as
  `detail` (province empty), province rows as `article_province_total`, grand totals as
  `article_total`.
- **5b.** Validators: per-article, Σ(country details) == Σ(province totals) == printed
  grand where printed (the FY1893 probe showed ~20% of rows sit in fully checkable
  blocks — use it as a sample gauge, NOT a gate); the volume's own Abstract by Countries
  and Provinces for the country dimension; **W** via StatCan (both witnesses exist for
  all seven years; 1897 already measured at 89.6%).
- **5c.** Wire into the chain + exports; the country_year export must tolerate
  province-less years.
- Acceptance: seven years in the rows CSV; **N** ≥ 0.99; **A** against each volume's
  Abstract reported; two-witness merge done for at least the years where the single
  witness misses **N** by > 1%.

### Phase 6 — FY1898–1908 promoted into the schema (1–2 sessions)

The spread rows are aligned and graded but live in their own CSVs with tariff-group
columns (GT/PT/SX). Map them into the schema (val_imp = TOT imports value, val_efc =
EfC/TOT consumption value, duty = TOT duty; keep the tariff-group columns as extra
fields — they are analytically valuable, don't flatten them away).
- Only `verified` + `bracketed` rows enter the export by default; `flagged` rows carry a
  flag through, excluded from country_year sums, counted in a residual line so the
  ratios stay honest.
- Raise the GP-era verified rate (60–69%) with the second witness: Canadiana 1898–1899
  are already aligned; FY1900+ Canadiana volumes are a fetch-and-OCR item — queue on
  Nibi, do not block the phase on it.
- Acceptance: **N** against the phase-0 anchors for all eleven years; a stated verified
  share per year in the origins report.

### Phase 7 — commodity curation layer (2 sessions, then standing)

Today: 5,102 raw article strings over eleven regime-C years, 74 verbatim in all eleven
(8.9% of value); ~⅓ of one-year-only names have a ≥0.90 sibling elsewhere = recoverable
variance, the rest is real tariff churn. Port the UK tooling pattern:
`ca_curate_commodities.py` queue → `canada_commodity_curation.csv` actions →
a `commodity_key` column on the exports. Respect the UK lessons: combine-late, scoped
combines keep untaken years, folds live in one place. The FY1891+ sub-article structure
(phase 5) and the tariff-line churn at 1898/1904 make an era-fold vocabulary necessary —
model on `fold_era_wordings`.
- Acceptance: §4.4's ≥60% value-in-continuous-series bar, measured per era.

### Phase 8 — final rebuild and report (½ session)

Full chain over all witnesses and years; regenerate
`exports/canada_imports_country_year.csv`, `…article_country_year.csv`,
`reports/canada_imports_origins.md` (1868–1908, with the per-year verified/coverage
caveats inline); archive the final per-cell diff. Declare imports DONE and open the
exports plan (Statement No. 4 = article × country sibling of the GS; `exports_abstract`
= its per-country arbiter; `total_exports` anchor already in phase-0's file).

## 6. Do not

- Do not hand-patch coverage losses (rows the OCR never produced) — phases 3/4 exist
  for exactly that; the synthesis approach is REFUTED.
- Do not re-add a ckey() fold for arbitrary trailing parentheticals (refuted 2026-08-30;
  only the `'Gt.'` spelling ever broke matching).
- Do not use the FY1891–1897 two-breakdown arithmetic check as a quality gate (~5% of
  blocks pass for label-structure reasons; it is a sample gauge only).
- Do not trust the per-cell abstract oracle over an exact in-table closure, and do not
  snapshot the rows CSV after a `CA_DEBUG_TABLE` run (it writes a no-inference parse).
- Do not assume a freed `?` run's owner (I3), and do not let `ca_parse_abstract.py`
  fall out of the ingest ritual.
- Do not start exports work inside these phases beyond phase 0's input protection —
  findings about export tables get FILED, not worked.

## 7. Sequencing notes

Phases 1–2 come before 3 because they are cheap, carry exact proofs, and shrink the
noise the witness vote must arbitrate. Phase 3 before 4 because the merge machinery is
built against the best-understood regime, then pointed at the broken one. Phase 5
before 6 keeps the schema extension (province-less years) ahead of the tariff-column
extension. Phase 7 needs the full year range to fold across, so it waits for 5 and 6.
Phases 3/4, 5, and 6 are independent enough to interleave if a session stalls on one.
