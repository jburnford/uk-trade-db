# UK Trade Database (Annual Statements + Trade & Navigation Accounts)

Relational database of UK imports/exports by article, country, and year,
built from double-keyed OCR of parliamentary trade statistics, 1868–1900.
Companion to the Timber Trades Journal shipment microdata
([timber-data](https://github.com/jburnford/timber-data), which consumes
`exports/wood_country_year.csv` for its Canada triangulation).

## Sources

- `raw/as_1872 … as_1899`: Annual Statements of Trade (28 volumes, Chandra
  OCR, ~290–1,000 pp each). Abstract tables carry 5-year comparatives →
  effective national-total coverage 1866–1900.
- `raw/tn_1871, tn_1872, tn_1895, tn_1899, tn_1900, tn_1901`: Accounts of
  Trade & Navigation. **Publication-year naming**: tn_1901 holds trade of
  1893–1900; tn_1871's comparative columns are the *only* source for
  1866–1867 (single-keyed — treat those years as advisory).
- Double key: Infinity-Parser2-Pro FP8 runs on the same PDFs, parsed by the
  same parser (`parse_infinity.py` rebuilds a pseudo-markdown stream) for
  cell-level reconciliation.
- Gold benchmark: London's Ghost Acres British Imports 1856–1906
  (quinquennial, hand-keyed, by country) — external truth at
  1866/1871/1876/1881/1886/1891/1896.

## Repository layout

Committed: `scripts/`, `reference/` (authorities + human merges),
`reports/` (validation scorecards), `exports/` (analysis-ready CSVs).
Gitignored (2 GB+, regenerable or distributed separately): `raw/`,
`raw_infinity/`, `pdfs/`, `db/uk_trade.duckdb`, `page_cache/`, and the two
giant generated review artifacts (`reports/country_review_queue.csv`,
`reports/review_pages.json`).

## Pipeline

```
parse_abstract.py            markdown -> abstract_obs        (Tier 1)
parse_infinity.py            Infinity key -> infinity_obs
parse_country.py             country sections -> country_obs (Tier 2)
parse_country_infinity.py    Infinity key -> country_obs_inf
parse_twoup.py / parse_runin.py   recovery parsers for layouts the main
                             parser skips (feed integrate_sources gap-fill)
build_dimensions.py          stable IDs: commodity + country + aliases
reconcile.py                 Tier-1 cross-engine consensus (A/B/C tiers)
reconcile_country.py         Tier-2 block arbitration -> country_consensus
repair_country_as_article.py phantom-region repair (see Quality stages)
anchor_tier1.py              cross-tier corroboration vs voted T1 totals
grade_country.py             magnitude-lens grades -> country_graded
rescore_value.py             value-as-signal price check -> country_rescored
vote_country_years.py        cross-volume voting -> country_year_consensus
integrate_sources.py         consensus + twoup + runin -> country_year_final
map_wood_commodities.py      wood label crosswalk -> exports/wood_*
wood_voted_series.py         price-aware wood series (reads country_rescored)
build_usability_table.py     per-commodity trust grades vs gold
validate_gold*.py, validate_internal/country/series.py   validation suite
```

Database: `db/uk_trade.duckdb`. Analysis tables: `consensus` (Tier-1
national totals, cross-volume voted), `country_rescored` (Tier-2 member
rows + grades + price verdicts), `country_year_final` (integrated
commodity × country × year). Flows: `import`, `export_uk`, `reexport`.

## Quality stages (2026-07-05/06)

Applied in order after reconciliation; every stage was gold-checked before
being kept (numeric reproduction held at 85% throughout — these move
*confidence*, not values):

1. **Colonial sub-entry recovery** (vote_country_years): nested
   `Region : Sub` rows (`British East Indies : Ceylon`) were dropped
   wholesale, losing e.g. ~70% of tea. Re-admitted under three gates:
   parent-row detection **global across volumes and duty tags**, garbage
   filter, and a grand-total shortfall gate (printed grand TOTAL sourced
   from the raw parse — the reconciler keeps only one TOTAL per block).
   Tea 1891: 0.27× gold → 1.00×; wool unchanged at 1.00×.
2. **Printed-subtotal unfiling** (integrate_sources): "Total from Foreign
   Countries / British Possessions" rows leaked from the two-up gap-fill
   parser and were summed as countries (407 rows, ~200 commodity-years).
   Detail-aware: dropped when matching detail exists, retained as one
   aggregate bucket when the subtotal is the only carrier of that volume.
3. **Value-as-signal rescore** (rescore_value): quantity and value are two
   independently printed numbers; a cell whose unit price sits in its
   series' band (market-shock robust, asymmetric verdicts) is corroborated
   without OCR agreement. Wired into voting and the wood series: 75.5k
   cells carry price corroboration as their verification; 8.7k flagged
   likely digit-slips head the review queue.
4. **Cross-tier anchoring** (anchor_tier1): a Tier-2 block whose member-sum
   equals the multi-volume-voted Tier-1 total is corroborated by other
   volumes' printings — the independent check once-printed country triples
   otherwise never get. Exact integer match → `t1_anchor` (A-logic, 548
   blocks); within 1% → `t1_near` (B, ~2.5k blocks).
5. **Country-as-article repair** (repair_country_as_article): region
   headers promoted to phantom articles (`group='Fish', article='West
   Africa', country='Gold Coast'` = Fish from West Africa : Gold Coast).
   Frequency-detected (plain-country or `Region : Sub`-parent usage, ≥3
   groups — protects Turkey/Guinea), 9 phantoms, **53,989 rows (13% of the
   corpus) refiled**.
6. **Group authority applied** (repair_groups → vote_country_years): the
   parser's sticky group state scatters commodities across bogus groups
   (wine articles under TEA, Raisins under CARDS PLAYING); bucket keys and
   output labels now use the cross-volume plurality group.

**Measured guardrails** (A/B against gold — do not redo): sig-token article
keys and duty-agnostic vote keys both *over-merge* distinct series (gold
reproduction 1231→1223 of 1456). Safe canonicalizations: group authority +
unit aliasing (cwts/cuts→cwt). The late-era (as_1897–99) flagged mass is
**key misalignment, not parsing** — the 5-year columns parse evenly
(~15k rows/year/volume); a parser rewrite is not justified by the evidence.

## Validation status (2026-07-06)

- **Numeric fingerprint vs gold** (`validate_gold_numeric.py`,
  name-independent: national total + largest origin must both match):
  **85% of 1,456 substantive commodity-years reproduced at ±5%**
  (92% at ±8%). Per year: 1876 84% · 1881 75% · 1886 82% · 1891 89% ·
  1896 91%.
- **Tier-1 vs gold incl. early anchors** (`validate_gold_tier1.py`):
  1871 = 73% ok of comparable cells — same rate as the established
  1876–1891 anchors (72–74%); 1866 = 61% but single-keyed (tn_1871 only);
  1896 = 94% (late-era source prints gold's fine categories). Tiers
  stratify out-of-sample: A 75% exact, B 70%, C 66%. `scope` (>2×) rows
  are gold-vs-source *category granularity* (gold "Hams" vs source "Bacon
  and Hams"), not misreads.
- **Wood × country** vs the decennial gold DB: 26/26 matched cells exact;
  wood quantities byte-identical through every quality stage above.
- Cross-engine reality check: Chandra × Infinity exact agreement is ~27%
  of blocks in 1872–84 but ~6% in 1885–96 and ~1.5% in 1897–99 — the
  engines fail *correlatedly* on dense late layouts, which is why printed
  block totals, T1 anchoring, and price corroboration carry the mid/late
  era rather than a third OCR key.

## Per-commodity usability (`exports/commodity_usability.csv`)

Every gold-benchmarked commodity graded on two collision-resistant signals
(`build_usability_table.py`; the name gate exists because a bare-total
match is *not* collision-safe — Cotton Raw's total coincides with Barley,
Sheep-skins, and Raisins):

- **TOTAL** — national total within ±5% of gold AND shares a name token.
- **BY-COUNTRY** — total *and* largest origin both match (two independent
  numbers).

Tiers SOLID / MOSTLY / MIXED / WEAK / SPARSE / UNVERIFIED per signal, with
the reproduced-year lists (the tier is a summary; the year lists are the
truth). Current tally (475 commodities): TOTAL 29 SOLID + 60 MOSTLY;
BY-COUNTRY 28 + 59. WEAK means *unconfirmed against gold*, not proven
wrong — often the origins are aggregated coarser than gold (Wool →
"Australasia" vs gold's per-state split). `reports/commodity_usability.md`
documents the method.

**Rules for analysis**: filter `v_grade='A'` (add B for robustness); use a
national series when TOTAL is SOLID/MOSTLY; use its by-country split only
when BY-COUNTRY is too; never sum across units.

## Wood commodity crosswalk (map_wood_commodities.py)

`reference/wood_commodity_map.csv`: 71 label variants → 13 canonical IDs
(hewn/sawn × species, staves, mahogany, the 1897+ "Rough, Hewn, Sawn, or
Split" consolidation kept as its own category — a real break, never merged).
Stitched exports: `exports/wood_country_year.csv` (canonical × origin ×
year × unit × grade), `exports/wood_country_year_voted.csv` (cross-volume,
price-aware), `exports/wood_wide/` (fixed country columns, 1872–1899 grid),
`exports/wood_national_year.csv`. Canada's decline is in verified data:
hewn 247k loads (1873) → 69k (1898); sawn holds ~1M loads/yr.

## Known issues / next steps

1. **Late-era key alignment** (as_1897–99): the remaining lever is
   value-aware bucket matching (align singleton buckets across volumes by
   value fingerprint before voting) — string loosening is ruled out by the
   guardrail measurements above.
2. **Targeted adjudication of the flagged residue**: ~33k flagged cells are
   engine-*disagreement* (adjudicable from text + arithmetic context —
   cheap); ~28k are correlated-agreement (only the page images in `pdfs/`
   can arbitrate).
3. **Human review**: `reports/country_review_queue.csv` (regenerate via
   grade_country.py) ranks grade-C rows by capped GBP exposure — the top
   2,000 rows cover ~76% of flagged value; price-flagged cells sort first.
4. "AT PRINCIPAL PORTS" tables excluded; a dedicated two-up parser would
   yield a port-level dataset.
5. Known parser-level residue: tea 1883/1890 broken country blocks, the
   1896 US-tea misread, as_1890 Corn value-group double-count, late-era
   "Goods" catch-all subtotals.
6. Gold 1901/1906 anchors need an as_1900/as_1901 or tn_1902 volume added
   to the corpus (tn_1901 ends at trade-year 1900).
