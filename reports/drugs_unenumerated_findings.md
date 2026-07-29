# Drugs — Unenumerated: an era-wording split six ways

Worked 2026-07-29 (`/loop /next-defect` iteration 8).

## Why the screen never ranked this first

`Drugs — Unenumerated` carries a Tier-1 value series for **1868–1895** and
origin data for 1872–1888 only. The holes are 1868–71, 1874, **1879–81** and
**1889–95** — the last a seven-year run worth roughly £5.8M.

`find_bracketed_gaps.py` reported only the 1879–81 run (£2.3M, rank 8). It
cannot see 1889–95 **because that run reaches the end of the series and the
screen only reports runs bracketed by a good year on BOTH sides.** Worth
knowing: the instrument is blind to a trailing collapse, which is exactly where
an era re-wording puts one.

## The defect

The printed line is re-worded repeatedly across the 1880s and 1890s —
`Unenumerated` → `Unenumerated and Medicinal preparations` → `Unenumerated,
including Medicinal preparations` → `... not liable to Duty` — and each wording
became its own payload commodity, none of them carrying the anchor:

| payload node | years | £ |
|---|---|---|
| `Drugs — Unenumerated` *(holds the T1)* | 1872–88, 1890 | 8,931,775 |
| `Cotton Manufactures — (Including Medicinal Preparations)` | 1879 | 691,110 |
| `Cotton Manufactures — Drugs, Unenumerated: (Including Medicinal Preparations)` | 1880–81 | 2,207,886 |
| `Drugs — Unenumerated And Medicinal   Preparations` | 1889–90 | 1,678,127 |
| `Drugs — Unenumerated, Including Medi-     Cinal Preparations` | 1891, 1892, 1896 | 1,635,501 |
| `Drugs — Unenumerated, Including Medicinal Preparations` | 1893 | 697,414 |
| `Drugs — Unenumerated, Including Medi-   "   Cinal Preparations Not Liable   "   To Duty` | 1893–99 | 3,913,451 |
| `Drugs — Unenumerated, Including Medicinal Preparations Not Liable To Duty` | 1894–98 | 1,692,634 |
| `Drugs — Medicinal Preparations` | 1894 | 694,486 |
| `Drugs — Not Liable To Duty` | 1896 | 748,425 |

**`fold_era_wordings` is structurally blind to this family.** Its pairing test
requires one side's article vocabulary to be a strict subset of the other's and
bails on `if not va or not vb`. `Unenumerated` is *entirely* filler tokens, so
the canonical short wording has an **empty** vocabulary and can never pair with
anything. Any commodity whose base wording is a bare `Unenumerated`,
`Unmanufactured`, `Raw`, `Other Sorts` … has the same immunity. That is an
instrument gap worth fixing: when one side's vocab is empty, fall back to the
literal-prefix test the groupless branch already uses.

## Fixed: three folds, five commodity-years, all closing

Three `commodity_curation.csv` `fold` rows into `Drugs — Unenumerated`:

| year | folded sum | T1 | ratio |
|---|---|---|---|
| 1879 | 691,110 | 691,140 | 0.99996 |
| 1880 | 664,787 | 665,387 | 0.99910 |
| 1881 | 851,989 | 851,999 | 0.99999 |
| 1889 | **814,593** | **814,593** | **1.00000** |
| 1890 | **863,534** | **863,534** | **1.00000** |

All five **nodata → EXACT**. Baseline 9,634 c-y: exact01 3,133 → **3,138**
(32.6%), GBP 50.9% / 68.0%. **Zero regressions.**

Note the 1879–81 tables are also a sticky-group instance — they sit under the
`COTTON MANUFACTURES` / `COTTON` heading in `as_1879` seq 502-519, `as_1880`
493-510 and `as_1881` 389-404, in **both** engines. They were repaired here
with a curation fold rather than a `group_repairs` row because **the table is
value-only and `integrate_sources` step 6 filters every row with no quantity**,
so a group repair would have admitted nothing. Second time that limitation has
bitten in three iterations (clocks 1893-97 was the first).

## NOT fixed, fully diagnosed: 1891–1895 (and 1896–99, which has no anchor)

The remaining five wordings were **not** folded, because they do not close.
Simulating the merge exactly as `fold` performs it — by (country, unit, year),
first writer winning — gives:

| year | union of all five | T1 | ratio |
|---|---|---|---|
| 1891 | 699,865 | 812,351 | 0.8615 |
| 1892 | 748,116 | 832,815 | 0.8983 |
| 1893 | 724,580 | 806,282 | 0.8987 |
| 1894 | 716,004 | 797,312 | 0.8980 |
| 1895 | 637,535 | 1,012,466 | 0.6297 |

The union never exceeds T1, so folding would not double-count — but it would
land the years at ~0.90, not at closure.

**And 1891 says why, to the pound.** `as_1891` `country_obs` seq 877-914 is a
complete, well-formed block whose printed totals close on themselves and on
Tier-1: foreign TOTAL **673,373** + British TOTAL **138,978** = **812,351** =
T1 exactly. The payload node holds 699,865 of it. The 112,486 difference splits
into two quite different causes:

1. **77,052 is sub-entry exclusion, not loss.** `British Possessions in South
   Africa : Cape of Good Hope-Natal` (11,530) and `: Mauritius` (355), plus the
   five `British East Indies : …` rows — Bombay and Scinde 16,282, Madras
   10,124, Ceylon 15,555, Other 7,644, Hong Kong 15,562. The rows are in the
   database; `reconcile_baseline` excludes drill-down labels from the numerator
   and no parent row exists to roll them up into. The coast-rollup /
   aggregate-beside-members passes did not synthesize the `British East Indies`
   and `British Possessions in South Africa` parents here — **the case to test
   is a value-only commodity, which may be why.**
2. **35,434 is genuinely lost.** The thirteen parsed British rows sum to
   103,544 against the printed British TOTAL of 138,978. Rows are missing from
   the page in this engine's copy.

So 1891 is really at 776,917/812,351 = **0.9564** of the block *present in the
database*, and would read 0.9564 if the sub-entries rolled up. Closing it needs
(a) the parent rollup and (b) the missing British rows from the other engine or
the page image.

**Recommended next step for this family**: check whether the Infinity copy
(`country_obs_inf` `as_1891` seq 810-848, 39 rows) carries the 35,434, then fix
the rollup. If both land, 1891 closes and the same treatment probably carries
1892-94, which sit at the same 0.898.

## Left alone deliberately

- `Drugs` (£315,783, 1895-99) — a **de-headed** label. Folding de-headed labels
  is the palm-oil `Oil` trap: they pick up other commodities' cells. Needs the
  year-scoped treatment, not a blanket fold.
- `Drugs — Not Liable To Duty` (1896, 748,425) — almost certainly the same
  line (`as_1896` prints both `Unenumerated (including Medi- cinal
  preparations)` and `… : Not liable to Duty`), but 1896 has no Tier-1 in the
  payload series, so there is no closure test to adjudicate it with.
- The `Medicines — …` nodes are export-side and unrelated.
