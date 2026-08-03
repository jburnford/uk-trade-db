# Where the data stands, and what is left

Consolidation written at the end of the `/next-defect` campaign, 2026-08-03.
The stopping rule the user set — two consecutive rounds under +5 cells — was met.

## The measure

`scripts/reconcile_baseline.py exports/viz_payload.json` compares, for every
commodity-year, the sum of its published origin cells against the Statement's own
printed national total (Tier-1), on that commodity's modal unit.

```
commodity-years with a Tier-1 line   9,509
  exact01  (within 0.1%)             3,774   39.7%   GBP-weighted 54.1%
  within5  (within 5%)               1,218   12.8%
  under / over                         522    5.5%
  nodata                             3,995   42.0%
                          within 5%:  51.9% of cells, 71.7% GBP-weighted
```

**A third of the corpus cannot close, and never will.** That is the single most
important thing to know before reading the headline figure:

| | cells | share | GBP |
|---|---:|---:|---:|
| exact01 | 3,774 | 39.7% | 7.42bn |
| within5 | 1,218 | 12.8% | 2.53bn |
| under / over | 522 | 5.5% | 1.14bn |
| real gaps — the year IS published | 820 | 8.6% | 1.07bn |
| gap — **no volume publishes that year** | 801 | 8.4% | 1.17bn |
| **anchor-only — no origin table in ANY year** | **2,374** | **25.0%** | 0.39bn |

The last two rows are structural. 2,374 commodities print a national total and
never print an origin table at all; 801 more are gaps in 1866-69, years for which
no volume exists in the corpus. Together they are **3,175 cells, 33.4%**, and no
amount of work reaches them.

**Excluding the anchor-only cells — arguably denominator pollution — the figure
is 3,774 / 7,135 = 52.9%.** That is the truer statement of how much judgeable
data agrees with its anchor.

The ceiling, if every remaining reachable cell closed, is 66.6%.

## What the campaign established

Roughly forty rounds. The pattern that mattered: **structural finds pay 15-115
cells; cell-by-cell work pays 0-3.** Three structural finds account for most of
the movement.

- **Four annual `tn_` volumes were excluded from the country parser** on the
  stated grounds that they were monthly. Four of the six are annual statements
  with detailed origin tables, already trusted as Tier-1 sources. Admitting them
  for 1870 and 1900 — the years no `as_` volume covers — was worth **+115** and
  gave 1900 origin data for the first time. (`tn_volumes_findings.md`)
- **A single edit-distance-1 pair** put Cork's national line inside Caoutchouc for
  seven years. `MANUFACTURED` and `MANUFACTURES` merged in the fuzzy OCR-variant
  pass; the merged entry's plurality label carried the wrong commodity's fold.
  **+19**, and Cork got its post-1891 anchor back. (`caoutchouc_manufactures_findings.md`)
- **Misfiled blocks**: the parser's sticky group goes stale, so a commodity reads
  `nodata` while its rows sit under another group entirely. Found by a two-sided
  test — the true commodity is empty *and* an independently printed anchor is
  closed by a block not attached to it. **+33** across two rounds, after
  `group_repairs.csv` gained a `years` column. (`misfiled_block_findings.md`)

Also closed: parent/child country double-counts (Turkey carried beside its own
printed parts, **+19**), one-place-under-two-names duplicates and subtotals
wearing a country's name (**+16**), and a scatter of single-cell adjudications
each proved against a printed total.

## What was tried and refuted

Recorded because they are expensive to re-try and each was measured:

| hypothesis | result |
|---|---|
| Near-misses are lost votes | **18 of 316.** The voter already picks the best-supported reading. |
| Near-misses are single-digit misreads | **268 of 316 deltas are not round multiples.** 85% cannot be one digit. |
| Regenerating `article_group_authority.csv` fixes stale groups | **−130 cells.** The plurality vote runs over the corruption it is meant to fix. |
| Containment matching in the sticky repair | **−20 cells.** Unique containment is not sufficient. |
| Admitting the `tn_` overlap years as a second witness | **−80 cells.** A plain double count; the pipeline does not dedupe across `as_` and `tn_`. |
| More false pairs in the fuzzy merge | **0 left.** 4 of 138 conflict, all genuine variants. |

## The methodological trap worth carrying forward

Three separate screens were built against the database and all three were
measuring something the baseline does not. `country_year_final` keeps stale
groups that `build_viz_payload` repairs downstream; a database `(article, year)`
can span several payload nodes. The misfiled-block screen reported **312**
candidates, of which **every one was already fixed** in the payload.

**A DB-level candidate list is never a target list. Confirm against
`exports/viz_payload.json` before writing a single row.**

## What is left

- **820 real gaps** in published years (GBP 1.07bn). Only ~28 still have a block
  that closes them; the rest need a different instrument.
- **1,218 near-misses**, 531 of them inside 0.5%. Neither lost votes nor single
  digits, so the mechanism is unknown — most likely a minor origin absent from
  the list, or a printed total covering something the origin table does not.
- **522 under/over.** Seven redundant-country candidates and fourteen
  equal-support vote candidates are adjudicated only as far as arithmetic can go
  and need the page.
- **Export leakage** is the one structural class never scoped.
- The 2,374 anchor-only cells should probably leave the denominator. That is a
  presentation decision, not a data one.

## Standing instruments

`reconcile_baseline.py` (the metric) · `find_bracketed_gaps.py` ·
`detect_column_crossing.py` · `detect_lost_vote.py` ·
`detect_redundant_country.py` · `detect_misfiled_block.py` ·
`fuzzy_merges.csv` (written every build) · `curate_commodities.py`

## The public map

`https://claude.ai/code/artifact/ac9a240f-b0d7-4568-b170-c41c6bf71e80` — rebuilt
on this data and republished. 1,242 commodities (was 996), 117 gazetteer labels,
89 known reconciliation issues surfaced on the page itself. All 17 smoke checks
pass. Rebuild: `curate_commodities` → `build_gazetteer` →
`reconcile_country_vs_t1 exports/viz_payload.json` → `build_map_slim` →
`build_map_artifact` → `smoke_map.js` → publish with `url=`.
