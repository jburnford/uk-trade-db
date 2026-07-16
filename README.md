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
integrate_sources.py         consensus + twoup + runin + colonial sub-entry
                             recovery -> country_year_final ('Region : Sub'
                             rows carry per-state origin detail the voter
                             drops as redundant to national totals)
map_wood_commodities.py      wood label crosswalk -> exports/wood_*
wood_voted_series.py         price-aware wood series (reads country_rescored)
build_usability_table.py     per-commodity trust grades vs gold
validate_gold*.py, validate_internal/country/series.py   validation suite
```

Database: `db/uk_trade.duckdb`. Analysis tables: `consensus` (Tier-1
national totals, cross-volume voted), `country_rescored` (Tier-2 member
rows + grades + price verdicts), `country_year_final` (integrated
commodity × country × year). Flows: `import`, `export_uk`, `reexport`
(`country_year_final` is imports only).

Every `country_year_final` cell carries per-cell trust columns
(`q_tier`/`v_tier` A/B/C and numeric `q_rank`/`v_rank` 1/2/3) so analysis
can threshold in SQL (`WHERE q_rank <= 2`). Rank 1 = same number printed
in ≥2 volumes and agreeing (mostly 1893+; earlier country triples print
once). Rank 2 = printed once but verified: block sums to the printed
annual total, both OCR engines agree, human-confirmed, or unit price in
the series band. Rank 3 = unverified (single unproven reading, engine
disagreement, or two-up/run-in gap-fill rows, which carry no
verification). Current split: 6% / 63% / 31%.

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
7. **Infinity-only block admission** (integrate_sources, 2026-07-15): the
   two OCR engines fail on DIFFERENT pages — 4,493 import blocks appear
   only in Chandra, 3,279 only in Infinity, 4,663 in both. Chandra is the
   stronger engine (75.1% vs 66.1% of blocks sum exactly to their printed
   Total; better in every volume) and stays primary, but
   reconcile_country only arbitrates blocks the primary found, so
   Infinity-only pages never entered the pipeline (cheese 1885, late-era
   grain, palm oil tails). Now admitted as source='infonly' for
   commodity-years absent from consensus, gated on the printed-total
   check (sum within 0.5% → tier B, else C) plus junk filters
   (dash-leader/ditto/unit-word "countries", glued numbers): 6,333 cells.
   Closed the full-run gaps in barley, oats, cheese, hewn fir, palm oil,
   rice 1885, wheat 1895/97–99; gold reproduction 90% → 91%.
8. **Two-up geometry + row-slip repair** (parse_country, 2026-07-15): the
   parser had assumed every side-by-side table is `(label,qty,val)×2` in
   cells 0–5; the 1872–82 OCR actually emits 8-slot rows with dash-leader
   cells, 10/12-slot export layouts, colspan-shifted headers, and pages
   whose left half is blank filler — losing the whole right column (the
   British Possessions continuations of big origin tables) and shifting
   left-column quantities into the value field, 11–29 tables per volume
   in exactly the weak years. Fixed with per-table geometry (colspan slot
   expansion, alpha-dominant label columns, digit-dominant qty/val
   picking). Separately, some 1881/82 pages carry an OCR row-slip (units
   alone on the first country row, every value one row down, an orphan
   label-less row re-absorbing it) which sums correctly to the printed
   total while misattributing every country — repaired by a pending-label
   cascade keyed on the unit-only-row signature. Recovered a.o. wool ×
   Australia 1872–84 continuous (173→430M lbs) and raw cotton × US
   1877–82; gold reproduction rose 85% → 90%.

**Measured guardrails** (A/B against gold — do not redo): sig-token article
keys and duty-agnostic vote keys both *over-merge* distinct series (gold
reproduction 1231→1223 of 1456). Safe canonicalizations: group authority +
unit aliasing (cwts/cuts→cwt). The late-era (as_1897–99) flagged mass is
**key misalignment, not parsing** — the 5-year columns parse evenly
(~15k rows/year/volume); a parser rewrite is not justified by the evidence.

## Validation status (2026-07-15)

- **Numeric fingerprint vs gold** (`validate_gold_numeric.py`,
  name-independent: national total + largest origin must both match):
  **91% of 1,456 substantive commodity-years reproduced at ±5%**
  (95% at ±8%). Per year: 1876 95% · 1881 91% · 1886 84% · 1891 90% ·
  1896 92%. (Before the 2026-07-15 two-up geometry fix + Infinity-only
  admission: 85%, with 1876 84% and 1881 75%.)
- **Tier-1 vs gold incl. early anchors** (`validate_gold_tier1.py`):
  1871 = 73% ok of comparable cells — same rate as the established
  1876–1891 anchors (72–74%); 1866 = 61% but single-keyed (tn_1871 only);
  1896 = 94% (late-era source prints gold's fine categories). Tiers
  stratify out-of-sample: A 75% exact, B 70%, C 66%. `scope` (>2×) rows
  are gold-vs-source *category granularity* (gold "Hams" vs source "Bacon
  and Hams"), not misreads.
- **Wood × country** vs the decennial gold DB: 37 matched cells (was 26
  before the geometry fix), 36 exact. The one mismatch (staves 1891
  Austrian Territories, gold 1,037 vs ours 1,937) is a probable gold
  keying slip: the printed value column (£10,618 at ~£5.5/load)
  corroborates 1,937.
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
truth). Current tally (475 commodities): TOTAL 50 SOLID + 68 MOSTLY;
BY-COUNTRY 50 + 65. WEAK means *unconfirmed against gold*, not proven
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
7. Post-geometry-fix residue (2026-07-15): (a) blocks whose column-top
   "GROUP (Cont'd)" header the OCR dropped inherit the other column's
   group (e.g. 1877 wool sits at `WOOD AND TIMBER|Sheep and Lambs'`,
   correct numbers, wrong group — viz shows it as a related-series chip;
   a group-repair reference CSV like flow_repairs.csv would fix the
   label); (b) as_1882 wool 'Other Countries' number unrecoverable (OCR
   dropped the orphan row — honestly absent, block-sum flags it);
   (c) ~935 consensus cells carry bare 'on the atlantic/pacific' labels
   (parent prefix lost in voting; fold_country normalizes at viz time);
   (d) wool 1886/91: the 'Australasia' aggregate cell is actually the
   printed "Total from British Possessions" subtotal misfiled (1891:
   614.6M ≈ Australasia 471M + S.Africa 97M + India 40M) — inflates the
   aggregate and double-counts the sum; extend printed-subtotal unfiling.
8. Remaining full-run holes after Infinity admission (all pages absent or
   unusable in BOTH OCR runs): wheat grain 1892; deals/sawn 1872, 1892;
   hemp 1874, 1898–99; rice 1872–75 (patchy); tobacco 1879; petroleum
   1875–76. The 1890s grain country detail otherwise sits under
   sticky-junk groups from the Infinity multiyear pages ('CHEESE|Wheat')
   — numbers correct, labels repaired at viz level. Duplicate spelling
   pairs from infonly ('Romania'/'Roumania' same qty) survive the
   near-dup dedup — country canonicalization would merge them.
9. **Glue blocks + group repairs (2026-07-16)**: the OCR sometimes
   concatenates multi-page runs of the country tables into ONE block under
   a stale `(group, article)` when column-top headings are lost (as_1887
   has a 213-row block labelled `SPIRITS|Rum` spanning rum + methylated +
   tea + tobacco + cigars + wine). `reference/group_repairs.csv`
   (volume + wrong label + obs `row_seq` range → true group/article/unit)
   is consumed by integrate_sources step 6 and admits the relabelled
   segment as `source='groupfix'`, tier C. First application recovered raw
   (unmanufactured) tobacco origin blocks for 1874, 1878, 1880, 1883,
   1884, 1887, 1888, 1890 — every segment sums to its printed total —
   making tobacco unmanufactured continuous 1872–99 except 1879 (whole
   page absent in both OCR runs; 1876/77/81/82 carry it under a blank
   article). Known remaining glue-block content worth the same treatment:
   wine detail 1889–97 (blocks under stale `TOBACCO` group), wood under
   `TOBACCO|Wood` 1898–99. The coverage-explorer payload
   (build_viz_payload.py) additionally re-homes country cells whose
   article alone unambiguously names exactly one abstract-attested
   commodity (~7.6k cells: wine reds under SPIRITS/TOBACCO, grains under
   CORDAGE/CHEESE, ivory under TAR) — display-level only, table
   untouched.
10. **US raw cotton recovered end-to-end (2026-07-16)**: the US is printed
    coast-split ('On the Atlantic'/'On the Pacific') with no parent row
    1876–99, and four separate years were mislabelled: 1872/1874 raw
    cotton under a stale `Meal and Flour` group; 1895–99 in a multiyear
    glue block under `CORDAGE|Raw` (as_1899 — its grand totals match T1 to
    the digit, sole carrier of 1898–99); and as_1883's `COTTON|Raw` block
    is ROW-SLIPPED (every quantity belongs to the label one row down: US
    11,066,166 sat at 'British North America'; Infinity corroborates the
    US label). group_repairs.csv gained `label_shift` (re-pair label(i+1)
    with numbers(i)) and `supersede_years` (drop the misaligned consensus
    rows a repaired block replaces); step 6 now keeps ' : ' sub-entry
    labels literally like source='subentry', and step 4 skips blocks the
    manifest relabels. The viz adds a coastal roll-up: parent-country
    cells synthesized as the sum of '(Atlantic)'+'(Pacific)' entries per
    unit-year where no parent row exists (918 cells; coast entries stay
    as drill-down). US raw cotton is now continuous 1872–1899. Caveat:
    the 1880 US figure rides the bare-'on the atlantic' consensus rows,
    and 1872/74/83/98/99 enter at tier C (single printing; 1872/74/83
    totals corroborated against T1 to the digit).
11. **Systematic sweep (2026-07-16)** — `scripts/reconcile_country_vs_t1.py`
    runs two detectors over the viz payload: (A) per commodity-cluster,
    country-sum vs T1 national total per year (year-presence lies — the
    tobacco trap); (B) single-year country spikes >=20x own median
    (row-slip fingerprint). The localization trick: a stray block's
    printed TOTAL row equals the T1 quantity nearly to the digit, so
    searching both engines for `quantity ≈ T1` finds where a lost block
    landed. Recovered via group repairs + a new
    `reference/group_aliases.csv` (unambiguous OCR garbles relabelled in
    place across all sources/years — HORS=HOPS, BRIINSTONE/BREMTONE=
    BRIMSTONE, GALIS=GALLS): hops 1873/76/80/82/92 (+ HORN 1882), galls
    1875/84/87 (twice misread as GLASS), isinglass 1892 (as GLASS),
    brimstone 1877/82, oats+rye 1893–97 (multiyear glue under
    CORDAGE|Oats, with Russia Northern/Southern Ports detail), hay
    1895–99 (multiyear glue under HATS OR BONNETS|Of Other Materials;
    all five grand totals == T1 hay exactly; sole carrier of 1898–99).
    Supersession now runs BEFORE the consensus guards so repaired blocks
    can replace their mislabelled consensus rows cleanly. One segment of
    the as_1899 hats glue block (Spain/China/Japan, ~1M 'Number'/yr,
    matches no T1 series) is preserved under an explicit 'unidentified
    first segment' label for page-image adjudication. Remaining detector-A
    flags at >=£500k are all label-orphan T1 aggregates ('Of Europe, &c.',
    'Stones, &c') or unprinted detail (Parcel Post) — no known missing
    origin blocks. Detector-B residue: wool 1896–98 'Australasia' cells
    are the printed BP subtotal misfiled (same class as the known
    1886/91 case — subtotal-unfiling lever); beans 1895 US 15.79M is a
    probable misread pending page-image adjudication.
12. **Ceylon coffee + the generic-article sig collision (2026-07-16)**:
    detector A misses a lost single COUNTRY row inside an otherwise-intact
    block. Ceylon coffee (peak supplier pre leaf-rust) was missing 13
    years via three defects: (a) coffee's whole origin block hid in
    chemical-neighbourhood glue blocks — as_1872 under `CHICORY|Roasted
    or Ground` (Ceylon 76.7M **Lbs** — the abstract's 166,269,052 for
    1872 is the Lbs era, not junk), as_1873 under `CARDS, PLAYING`
    (Ceylon 849,911 cwt; TOTAL == T1 exactly), as_1890 under `CHICORY`,
    as_1891/92 under `COCOA` (TOTALs == T1); (b) `V.sig('Raw')` is a
    valid sig, so the sub-entry guard let `COTTON|Raw|ceylon` block
    `COFFEE|Raw|ceylon` — integrate now keeps a GROUP-AWARE triples set
    for steps 4/6, which unblocked **1,299 sub-entries pipeline-wide**;
    (c) as_1898's `COPPER, ORE OF|Raw` is another copy of the multiyear
    raw-cotton table — it and `CORDAGE|Raw` were phantom consensus
    commodities showing cotton numbers as copper ore / cordage 1894–99,
    now superseded (306 rows). Step 6 also strips run-in section headers
    absorbed into the first country label ('COFFEE: From France').
    Ceylon coffee residuals: 1879 (whole-page loss volume), 1882,
    1886–88 (Ceylon line absent from OCR; block otherwise intact), 1874
    reading 30,195 is a broken digit (true ~750k, PDF-adjudicable).
    Follow-up spotted: as_1894–98 dye-stuffs/meal neighbourhood glued
    under `COPPER, ORE OF` (Opium/Bark/Madder/Valonia chimera series) —
    display pollution only, proper series carry the data.
13. **South African wool (2026-07-16)**: (a) 1877's whole sheep-wool
    origin table sat under `WOOD and TIMBER|Sheep and Lambs'` (TOTAL ==
    T1 exactly; SA 41.6M, Australia 281.2M) — repaired + superseded;
    (b) 1891 sub-entry label slip put SA's 96,662,069 on 'BPSA : Aden'
    — fixed via the new `new_country` column in group_repairs.csv
    (row-level country override; suppresses only the exact replaced rows
    from the sub-entry recovery); (c) the origin regime changes in
    1891/92 from the 'British Possessions in South Africa' aggregate to
    per-colony Cape of Good Hope + Natal — build_viz_payload now has a
    CONSTITUENTS map that synthesizes such aggregates from their
    complete constituent set in years they lack. Residual: 1883 SA
    18,870,981 is a correlated both-engine misread (true ~55M by
    neighbours) — page-image adjudication only.
14. **Standing anomaly battery (2026-07-16)** — run after every integrate:
    `python3 scripts/build_viz_payload.py /tmp/payload.json` then
    `python3 scripts/reconcile_country_vs_t1.py /tmp/payload.json` (A/B)
    and `... /tmp/payload.json --series` (C/D). Four detectors: (A)
    commodity country-sum vs T1 per year; (B) misattribution spikes; (C)
    interior year-HOLES in a consistent major supplier's series; (D)
    single-year DIPS/SPIKES vs series median with normal neighbours —
    share-weighted (>=4% median share) and ranked by commodity GBP x
    share into `reports/country_series_anomalies.csv`. C/D encode the
    checks that found Ceylon coffee, SA wool, and US cotton. Top open
    flags at first run: wine 1874 (red/white/total segments sit
    unrepaired in the as_1874 TEA glue block seq 264-310, incl. a
    Canary-Islands row carrying Spain's 7,496,590), wine 1883+1892
    country blocks, Australasia wool aggregate 1883/84/88/89 (per-state
    era — CONSTITUENTS roll-up candidate), teak (Wood/BEI+Burmah)
    1890-92, Russia oats 1873-78, US flour 1881-82.
6. Gold 1901/1906 anchors need an as_1900/as_1901 or tn_1902 volume added
   to the corpus (tn_1901 ends at trade-year 1900).
