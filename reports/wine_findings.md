# Wine — and a new glue class: the "Principal Articles Imported" summary

## How this one was picked

Rather than take the next entry off the standing queue, every remaining
off-cell in the payload was re-ranked by GBP exposure. `Wine — Total Of All
Kinds` came out near the top — **GBP 77M, four years running at 13.3× / 14.3× /
20.1× / 22.7×** — and nobody had looked at it. The old queue's next items were
an order of magnitude smaller. **Re-rank before picking.**

## The defect — a summary table read as a country list

Each volume prints a **summary of principal articles imported** after the
detailed tables. Its row labels are commodity names with their unit captions
attached. In as_1876, as_1877, as_1881 and as_1882 the `WINE | Total of all
Kinds` label runs on past its own printed `TOTAL` and swallows that summary, so
the parser read the article names as **countries**:

```
Cocoa - Lbs                                20,443,591
Corn:—Wheat - "                            44,454,657
Petroleum - Gallons                        25,201,177
Tanned, Tawed, Curried, or Dressed - Lbs   44,768,891
```

**The signature is a country list containing `Corn Wheat` and `Petroleum
Gallons`.** No arithmetic detector catches it as a *labelling* error — it shows
up only as a wildly inflated country sum.

## The repair

In all four volumes the true wine block is the **first ~17 rows** and ends at a
printed `TOTAL` that is the Tier-1 figure to the digit:

| volume | seq | printed TOTAL = T1 | rows sum | residual |
|---|---|---|---|---|
| as_1876 | 253-269 | 19,950,723 | 19,946,820 | −3,903 |
| as_1877 | 226-242 | 19,568,807 | 19,569,407 | +600 |
| as_1881 | 178-194 | 16,297,033 | 15,958,043 | **−338,990** |
| as_1882 | 144-160 | 15,715,813 | 15,715,963 | +150 |

Four `group_repairs` rows, each superseding its own year and re-admitting only
its block:

```
1876  13.3252 -> 0.9998        1881  20.0838 -> 0.9792
1877  14.2981 -> 1.0000        1882  22.7038 -> 1.0000
```

`exact01` **2,767 → 2,770**, `over` 225 → **221**, and **within 0.1%
GBP-weighted 48.2% → 48.6%** — the largest GBP move of the session, because the
commodity is large. The whole-payload ratio-class diff moves exactly those four
cells.

## Corpus-wide check after the fix

Scanning `country_year_final` for the summary table's pseudo-country names
(`corn wheat`, `cocoa lbs`, `petroleum gallons`, `indian corn or maize`,
`tanned tawed curried or dressed lbs`, `sheep and lambs`, …) shows the repairs
cleared nearly all of them. **Five blocks remain**, 1-3 cells each:

- `ANIMALS, LIVING` 1881, 1882, 1899
- `ANIMALS, LIVING | Metals` 1881
- `OIL` 1898

## Still open

- **as_1881 is short 338,990 (2.1%)** — one country row the parser dropped. The
  block genuinely begins at `Germany` (seq 178) and seq 177 is `WINE | White`'s
  own `TOTAL`, so nothing was mislabelled: the row is absent. Page-image
  candidate; not guessable.
- The **five residual summary-table blocks** listed above.
- Other `WINE | Total of all Kinds` years carry the same glue but **never reach
  the payload** — 1873 (34 rows), 1875 (35), 1885 (51), 1888 (57) against a
  normal ~25. Consistent with the standing lesson that a volume can absorb rows
  under a heading without the payload's anchored years ever seeing them; listed
  so nobody re-derives it.
