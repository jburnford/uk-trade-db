# The tn_ overlap: refuted with the clean vocabulary in place

Scope class #3 — admitting `tn_1895` and `tn_1899` as a genuine second witness
for 1894-98 — was the largest queued lever. **It is net-negative and is now
closed.**

## Why it was worth retesting

Iteration 35 tried the overlap twice and both attempts failed, but **both ran
while the corpus-wide parser vocabulary was still contaminated** by seeding pass 1
from the new volumes. The third attempt fixed the vocabulary *and* restricted the
`tn_` rows to 1870 and 1900, and gained +115. The combination that was never
tested is the one that matters: **overlap admitted, vocabulary clean.**

## The measurement

`keep_row` was opened to every year, both engines re-parsed, and the full Tier-2
chain re-run.

```
                      before        after
commodity-years        9,509        9,530
exact01                3,774        3,694    (-80)
GBP within 0.1%        54.1%        50.3%
nodata                 4,044        3,915    (-129)
```

Per cell: **202 better, 203 worse.** The overlap does put data into 129 previously
empty cells — that part is real — but it costs 80 exact cells and nearly four
points of GBP-weighted agreement to do it.

## The mechanism is a plain double count, and it is localised

160 of the 203 regressions fall in **1894-1899**, exactly the years the two
`tn_` annuals overlap, and **50 of them land in `over`** at ratios that say what
is happening:

| commodity | year | was | now |
|---|---|---:|---:|
| `Corn And Grain — Wheat` | 1897 | within5 | **1.8003** |
| `Corn And Grain — Wheat` | 1896 | exact01 | **1.6855** |
| `Corn And Grain — Wheat` | 1898 | within5 | **1.6717** |
| `Oats` | 1898 | exact01 | **1.5101** |
| `Oats` | 1897 | exact01 | **1.3279** |
| `Copper, Ore Of` | 1899 | exact01 | 1.1229 |

Ratios of 1.3 to 1.8 are a second copy of part of the block, not a disagreement
between witnesses. **The pipeline does not dedupe the same
(commodity, country, year) across `as_` and `tn_` volumes.** `vote_country_years`
is supposed to arbitrate readings, and for rows that reach it, it does; the
duplicates are arriving through paths that bypass it — `integrate_sources`'
gap-fill steps and the volume-and-seq-keyed `group_repairs` entries, which cannot
tell that another volume already supplied the same cell.

## Verdict

**Closed as refuted.** The `tn_` volumes stay restricted to 1870 and 1900, where
they are purely additive and worth +115. Their 1894-98 columns cannot be admitted
as a second witness until the gap-fill and group-repair paths carry a
cross-volume duplicate guard — which is a much larger change than the second
witness is worth, since those years already have `as_` coverage.

The baseline was restored to 3,774 exactly after reverting.
