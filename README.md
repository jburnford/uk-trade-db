# UK Trade Database (Annual Statements + Trade & Navigation Accounts)

Relational database of UK imports/exports by article, country, and year,
built from Chandra-OCR'd parliamentary trade statistics, 1868–1900.
Companion to the Timber Trades Journal shipment microdata
(`~/timber_data`).

## Sources

- `raw/as_1872 … as_1898`: Annual Statements of Trade (27 volumes,
  Chandra OCR, ~290–1,000 pp each). Abstract tables carry 5-year
  comparatives → effective coverage 1868–1898.
- `raw/tn_1871, tn_1872, tn_1895, tn_1899, tn_1900`: monthly Accounts of
  Trade & Navigation (comparative columns → 1869–1900, monthly resolution).
- Double-key: Infinity-Parser2-Pro FP8 runs on the same PDFs
  (`nibi:~/projects/def-jic823/infinity/output/trade_db/`, jobs in
  `infinity/trade_jobs.tsv`) for cell-level reconciliation.

## Pipeline

```
scripts/parse_abstract.py       markdown -> abstract_obs (DuckDB)
scripts/parse_infinity.py       Infinity result.json -> infinity_obs
                                (same parser, pseudo-markdown stream)
scripts/parse_country.py        Tier 2 country sections -> country_obs
scripts/build_dimensions.py     stable IDs: commodity + country + aliases
scripts/reconcile.py            cross-engine cell matching + consensus
                                table with A/B/C confidence tiers
scripts/validate_gold_tiers.py  consensus vs hand-keyed gold DB, by tier
scripts/validate_internal.py    printed group subtotals vs member sums
scripts/validate_country.py     country-block sums vs printed totals;
                                wood x country vs gold decennial
scripts/validate_series.py      cross-volume disagreement + neighbour-jump
                                outliers -> reports/validation_flags.csv
```

Database: `db/uk_trade.duckdb`
- `abstract_obs(volume, flow, measure, article_group, article, unit, year,
  value, raw_unparsed, row_seq)` — one row per printed cell; the same
  statistical year appears in up to 5 volumes (kept for reconciliation).
- `commodity(commodity_id, label, first_year, last_year, n_obs)` — slug IDs
  derived from normalized text (stable across re-parses).
- `commodity_alias(article_group, article, commodity_id)` + human merges in
  `reference/commodity_merges.csv` (alias_id,canonical_id).
- `country` / `country_alias` — schema ready, populated by Tier 2.

Flows: `import`, `export_uk` (UK produce), `reexport` (foreign & colonial).
Measures: `quantity` (unit column), `value` (GBP).

## Validation status (2026-07-03)

- Wood & timber totals match the hand-built decennial Full British Imports
  DB **digit-perfect** at 1871, 1881, 1891.
- 24,451 year-cells with multi-volume observations; 22.5% disagree —
  inflated by known issue #2 below; reconcile after Infinity pass.
- Neighbour-jump detector flags 57 wild outliers (mostly the port-table
  leak, plus genuine digit slips).

## Reconciliation status (2026-07-04, evening pass)

Infinity fleet complete (34/34 volumes; 5 malformed result.json salvaged at
the element level). Both keys parsed by the SAME parser (parse_infinity.py
rebuilds a pseudo-markdown stream).

Cell-level: 118,983 cells matched across engines (multi-pass matcher:
exact, unit-token-stripped, article-only within table family, group-glued
variants — each fallback pass requires an unambiguous 1:1 candidate),
87.7% verified identical. Consensus (51,268 series-years): **tier A 50.9%,
B 31.4%, C 17.6%** (was 26.3/39.6/34.1 before the matcher + parser fixes).
Gold check by tier: A 95.1% exact — the residue is dominated by known
gold-side transcription slips (Lard 1871, Galls 1874, Madder Root 1873/77:
all 5 printings x both engines unanimous against the gold value) and
category-scope diffs (turpentine subcats, cutch) — B 85.1%, C 61.5%; the
tiers stratify confidence correctly.

Parser fixes that drove the jump (2026-07-04): markdown-emphasis in late
captions ("TOTAL **Quantities** of...") broke caption regexes and the
sticky flow/measure mislabeled whole pages — asymmetrically across engines;
ports/customs-duties/parcel-post table families now excluded (reset
markers); content-based measure sanity check (quantity pages carry unit
words/dittos, value pages none) with dash-cell collapse so both engines
score alike.

## Tier 2: country detail (2026-07-04)

`scripts/parse_country.py` parses the GENERAL IMPORTS (free + subject-to-
duty) and GENERAL EXPORTS (UK produce + foreign & colonial) country
sections: article x country x (quantity, value) for the statement year,
into `country_obs`. Two-up column layout, two-pass parse (pass 1 harvests
country names so port-breakdown headers — "United States of America :" ->
Atlantic/Pacific — aren't mistaken for sub-articles). Printed 'Total' rows
kept (country_raw='TOTAL'); `validate_country.py` checks sum(countries) ==
printed total per block and wood x country vs the decennial gold DB.
`build_dimensions.py` populates `country`/`country_alias` (stable slugs;
human merges in reference/country_merges.csv).

Tier 2 is double-keyed (2026-07-04 late pass): parse_country_infinity.py
runs the same parser over the Infinity output -> country_obs_inf, and
reconcile_country.py arbitrates block-by-block into **country_consensus**
(the analysis table; country_obs is the raw Chandra key). Blocks pair by
key then by content fingerprint (shared member values); a corpus-wide
group/sub-name gazetteer (382 groups, 884 subs, harvested in pass 1)
standardizes header classification across both engines. Per block+field
the reconciler records how it resolved (q_block/v_block columns):
exact | inf_struct (Infinity's self-consistent block adopted — Chandra
broke the structure) | inf_block/swap (single-cell repair from the other
engine) | anchor (members sum to the tier-A/B national total; the printed
Total row was the misread) | digit_fix (total independently confirmed and
exactly one member admits a one-digit change equal to the residual) |
inf_only | nototal | flagged.

Result (block arithmetic on country_consensus, 28,490 blocks): **57.2%
exact, +15.8% within 2%, 27.0% flagged** (raw single key was 48.1 / 20.2 /
31.7). Mid-era 1885-90: 68-73% exact; as_1897-99 still 45-64% flagged
(changed layout, dedicated pass pending). Wood x country vs the decennial
gold DB: 26/26 matched cells exact. 2,840 country IDs pre-merge.

## Usability grades (grade_country.py -> country_graded)

Every member row carries q_grade/v_grade under a MAGNITUDE-error lens
(first-digit errors are fatal, small slips are not):
  A — block passes printed-total arithmetic OR both engines independently
      agree on the cell; first-digit error effectively impossible
  B — block within 2% of its printed total and this cell isn't the
      engine-disagreement suspect: small-error risk only
  C — unverifiable (structural block + single-engine cell), engine-
      disagreement suspects, series jumps >3x vs both neighbouring years,
      or value above the 50M GBP plausibility ceiling (glued digits /
      quantity landed in the value column — a shared-parser failure that
      cross-engine agreement cannot catch)

Corpus: A 73.2% of rows (53% of plausible GBP), B 3.0%, C 23.7% (44% of
GBP — big articles have big multi-page blocks that break more often).
Best era 1885-96: A 79% of rows / 75% of GBP. Wood imports: A 83% of
rows / 73% of GBP. **Analyses should filter v_grade='A'** (add B for
robustness checks). reports/country_review_queue.csv ranks grade-C rows
by capped GBP value: the top 2,000 rows cover 76% of flagged exposure
(~a day of human review); reports/review_queue_ranked.csv does the same
for the 9.0k tier-C abstract series (top 1,500 = all >=1M exposure).

## Wood commodity crosswalk (map_wood_commodities.py)

Timber article labels drift across the era (1870s ditto-depth subs
'" " Fir' under 'Sawn or Split'; 1880s 'Sawn, Fir'; 1897+ 'Rough, Hewn,
Sawn, or Split' CONSOLIDATION — kept as wood-rough-combined, a real
category break, never merged into hewn or sawn). Parser now decodes
ditto DEPTH (one token repeats the group, two repeat group+sub), 'From
X:'/region headers open country contexts (not sub-articles), a country
context refuses a Total >2x its members' sum (else the block total gets
credited to one country), page-overlap duplicate blocks are fuzzily
deduped, memberless grand-total blocks never adopt the other engine's
members (foreign/British/grand printed splits), and orphan region
sub-rows fold into their parent when OCR lost the parent row.

reference/wood_commodity_map.csv: 71 label variants -> 13 canonical IDs
(wood-hewn-fir/-oak/-teak/-unenumerated, wood-sawn-fir/-unenumerated,
wood-staves, wood-lathwood, wood-mahogany, wood-furniture-hardwoods,
wood-house-frames, wood-unenumerated, wood-rough-combined); rows marked
'confirmed' survive regeneration; 17 variants (mostly bare 'Fir' and
tiny 1880 leaks) in review. Stitched exports:
- exports/wood_country_year.csv — canonical x origin x year x unit x
  qty/value x grade (worst contributing row). Hewn-fir runs 1873-1898
  for Canada/Russia/Sweden/Norway/France/USA, mostly grade A; sawn-fir
  1877-1898 (~1M loads/yr Canada, grade A). Canada's decline is in
  verified data: hewn 247k loads (1873) -> 69k (1898).
- exports/wood_national_year.csv — Tier 1 totals x flow x measure with
  confidence tiers.
Continuity check: 32 >3x adjacent-year jumps among A/B cells corpus-wide,
all plausibly genuine trade swings (Siam teak, US oak growth).

## Validation status (2026-07-04 evening)

- validate_gold_tiers.py: consensus vs gold by tier — A 95.1% exact
  (~98% net of known gold-side slips), B 85.1%, C 61.5%.
- validate_internal.py (now unit-aware + skips groups with unparsed
  members): 857 subtotal checks, 58.8% exact; top residual mismatches are
  two systematic layout quirks (as_1890 Corn group double-counts meal
  lines; late-era "Goods manufactured/unmanufactured" catch-alls), all
  flagged.
- validate_series.py: multi-volume disagreement 20.7% (was 25.8%);
  neighbour-jump outliers 171 (was 196); ports-leak gone.
- validate_country.py: see Tier 2 section.

## Known issues / next steps

1. Late-era country sections (as_1897-99) use a changed layout — block
   arithmetic much weaker there (50-69% flagged); needs a dedicated pass.
2. "AT PRINCIPAL PORTS" tables excluded; build their dedicated two-up
   parser later (port-level dataset).
3. Country/commodity crosswalk for the wood gold test (match breadth) and
   commodity label drift (Madder Root vs Madder Root and Munjeet) —
   candidates for reference/*_merges.csv, human review.
4. Tier-C review queue now 9.0k (was 23.8k); targeted human review of the
   residue.
5. as_1890 Corn value-group and late-era "Goods" catch-all subtotal
   layouts (validate_internal top offenders) unhandled.
