# Fruit, Unenumerated Raw 1875: one stale article over three different tables

Worked 2026-08-01 (`/loop /next-defect`), bracketed-gap rank 3, GBP 1.01M.
**`Fruit — Unenumerated : Raw` 1875 went from 0.0551 to exactly 1.000000** —
2,220,412 of a Tier-1 of 2,220,412 Bushels.

**exact01 3,548 → 3,549, under 286 → 285, denominator unchanged at 9,497. One
commodity-year changed in the whole corpus; zero regressions.**

The commodity is exact or near-exact in every other year 1872-1899; 1875 was
the outlier.

## The 122,294 was a different fruit

The same `as_1875` FRUIT import page that hid the nuts-and-kernels table — the
four-cell-per-side layout with an empty indent cell before every country, which
collapsed in both extractors (see `reports/nuts_kernels_findings.md`).

Chandra emitted **two** blocks under a stale `FLOWERS, ARTIFICIAL` head and gave
**both the same article, `Raw, not otherwise described`** — and neither is the
Raw table:

| seq | what it actually is | members | printed Total |
|---|---|---|---|
| 556-563 | **Dried, not otherwise described** — France 6,381, Turkey 71,157, Egypt 3,020, Persia 4,303, Bombay 15,860, Gibraltar 3,526, Other 18,047 | sum **122,294** | **122,294** |
| 564-569 | **GALLS** — Turkey 6,789, Persia 2,480, China 13,714, Bombay and Scinde 3,746, Other 1,433 | sum **28,162** | **28,162** |

`commodity_curation` row 636 folds that stale label into `Fruit — Unenumerated :
Raw` **unscoped**, so a *dried-fruit* printed total became the entire origin
profile of raw fruit for the year. Each block closes on its own printed total —
which is exactly why nothing flagged them: **internally consistent tables under
the wrong name.**

## The real table, closing on both columns

Printed in the FRUIT section as `„ Raw, not otherwise described :`, and absent
from both parses:

| Germany | Holland | Belgium | France | Portugal, Azores & Madeira | Spain & Canaries | United States | British N. America | BWI Islands | Other |
|---|---|---|---|---|---|---|---|---|---|
| 146,493 | 199,865 | 703,777 | 581,170 | 151,391 | 199,650 | 164,160 | 44,450 | 20,546 | 8,910 |

**Quantities sum to 2,220,412 = the block's own printed Total = the Tier-1, to
the digit. Values sum to 986,248 = the printed value total, to the digit.**

## The repair

- One `group_repairs` row: `supersede_years=1875` (removes both misfiled
  segments from this commodity) and re-homes the **Dried** half to the existing
  `Fruit — Dried, Not Otherwise Described` node.
- Ten `manual_rows` for the real Raw table, under `FRUIT | Unenumerated : Raw`
  — the label the node's own sibling years carry.

A companion row was written to re-home the **GALLS** half as well; it admitted
nothing, because **an existing repair on seq 564-569 already covers it and fires
first**. It was removed rather than left in the reference file as dead weight.

## The lesson worth carrying

**One stale article can sit over several different printed tables, and each of
them can be internally perfect.** Every arithmetic check the battery applies —
members sum to the block's own Total — passes on both intruders here. What gives
them away is that *the block's total is not the commodity's Tier-1*: 122,294
against 2,220,412. A screen comparing each block's printed Total to the Tier-1 of
the commodity its label folds into would find this class directly.
