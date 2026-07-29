# The sub-entry-loss screen — and the negative result it returned

Built and run 2026-07-29 (`/loop /next-defect` iteration 11).
`scripts/detect_subentry_loss.py` → `reports/subentry_loss.csv`.

## Why it was built

`integrate_sources` step 1 skips every consensus row whose country contains
`' : '` — they are drill-downs, and counting them beside their parent would
double-count. Step 4 recovers most (6,880 cells). When a block prints *only*
drill-downs under a parent heading and step 4 does not fire, the trade is gone
and the commodity-year reads short by exactly their total.

That mechanism had been the deciding factor in three consecutive iterations:

- **iron manufactures 1892** — `British North America : Canada` 4,703, one row,
  the whole difference between within5 and EXACT
- **drugs unenumerated 1891** — 77,052 of a 112,486 shortfall (five
  `British East Indies : …`, two `British Possessions in South Africa : …`)
- the same shape is the residual in drugs 1892-94

Three hits in three iterations reads like a seam. **It is not.**

## The screen

Anchored on the **commodity-year**, not the block. For each (article
signature, year):

    T1             the voted national total (consensus, quantity, best tier)
    got            what country_year_final actually holds
    lost_subentry  ' : ' rows in either engine whose (sig, country, year)
                   reached neither table

reported where `got` is short but `got + lost_subentry` lands within 0.5% of
T1 — the signature of an orphan drill-down set, where nothing double-counts.

**An earlier block-anchored version was wrong and is worth recording as a
method note.** It compared each block's plain rows against that block's own
printed total and returned 91 blocks — but its top hits (brandy 1886, corn
wheat 1895, cotton raw 1893, tea 1895/1897) were *all already closing at
1.00*, because another volume's copy of the same table supplied the trade.
**A block being short proves nothing. Only the commodity-year is the unit of
loss.**

## What it found: four, of which two were real

| lost | year | commodity | before → after |
|---|---|---|---|
| 472,665 Lb | 1895 | Feathers — Ornamental | see below |
| 22,717 Cwt | 1893 | **Paraffine** | **0.9704 → 1.0000** ✅ |
| 18,027 Cwt | 1896 | Paraffine | false positive |
| 1,394 Cwt | 1886 | Safflower | ambiguous, trivial |

### Fixed: paraffine 1893 — one row, exact

`as_1893` (Infinity) seq 2720-2727. Russia 560 + Germany 1,209 + USA 744,109 =
745,878 = the printed foreign TOTAL, and the only other row is
**`British East Indies : Burmah` 22,717 Cwts** — Burmese paraffin, the expected
source. 745,878 + 22,717 + 10 = **768,605 = Tier-1 exactly**. One
`group_repairs` row; step 6 keeps drill-downs with their literal label and
`build_viz_payload` folds them to a top-level country.

### Admitted but not yet measurable: ornamental feathers 1895

`as_1895` (Infinity) seq 1081-1091. The **whole British half** of the block is
drill-downs — `British Possessions in South Africa : Cape of Good Hope`
**326,418**, `: Natal` 8,534, `British East Indies : Bombay` 76,385,
`: Bengal` 59,741, `: Other` 1,587 — plus three plain British rows no
consensus copy carries. The nine sum to the block's printed British TOTAL
**484,606** exactly. The Cape ostrich-feather trade, the single largest origin
of the year, was absent from the commodity entirely.

Admitted (8 rows), **and the payload bucket did not move** — which is the
second false-positive mode, and a real finding about the corpus:

> **The commodity's anchor is in a different payload node.** `Feathers And
> Down — Ornamental` holds T1 **1868-1891**; a bare, de-headed `Ornamental`
> node holds T1 **1892-1900**. The screen compares against `consensus` (keyed
> by signature) while `reconcile_baseline` compares against the payload (keyed
> by display label), so the two disagree about what 1895 even reads.

That commodity needs the de-headed-anchor treatment, not a sub-entry repair,
and it is worse than a split: the country side is a **chimera** (1889 reads
16,000,502 Lb and 1892 reads 41,652,370 against a T1 of ~800,000). Queued
separately — it is a £27M node.

### False positive: paraffine 1896

`as_1898 ORE, unenumerated | PARAFFINE` is a 496-row sticky glue run holding
several commodities. Paraffine's own block is seq 16073-16109 and **closes on
itself** (2,240 + 681,381 + 700 = 684,321 foreign; + 41,005 + 72 = 41,077
British; grand 725,308 against a T1 of 725,398). The `British East Indies : …`
rows the screen credited to paraffine sit at seq 16166-16187, inside the *next*
block (foreign TOTAL 1,090,336). **Sig-level attribution cannot see block
boundaries inside a glue run** — recorded in the script's docstring.

### Ambiguous: safflower 1886

Chandra reads `Foreign Countries` 715 + `British Possessions (South Australia)`
3 = 718, its own printed total. Infinity reads a single
`British East Indies : (Bengal)` 1,394, which is the Tier-B T1 to the digit.
Two irreconcilable readings of one small table; 1,394 Cwts is not worth a page
image. Left.

## Conclusion

**The class is nearly exhausted.** Four candidates corpus-wide, two real, one
worth 22,717 Cwt. The three iterations that made it look like a seam were
finding it *inside blocks they were already repairing for other reasons* —
which is where it will keep turning up. The screen is worth keeping as a
post-repair check rather than a source of new work.

Baseline 9,634 c-y: exact01 3,143 → **3,144** (32.6%), GBP 51.0% / 68.1%.
One commodity-year to EXACT, zero regressions.
