# Sawn timber: the missing component found, and why `combine` cannot apply it

> **SUPERSEDED 2026-08-05 — see `reports/sawn_timber_fixed.md`.** The component
> identified here is now applied: +16 exact01, 20 commodity-years better, 0
> worse, fifteen years closing to the digit. Two conclusions below are wrong and
> worth knowing why:
>
> * "`combine` merges the source's label counter and renames the node" — it does
>   not. Curation runs on the emitted payload, which no longer carries label
>   counters. The rename was **pass order**: at the curation point the anchor
>   (`Wood And Timber — Sawn Or Split`, GBP272K, no origins) and the origins
>   (`... Planed Or Dressed, Fir`, GBP314M) are still two nodes, and
>   `fold_era_wordings` is what later makes them one. Combining into the
>   anchor-only half is what split the node and left cells at 0.03. Deferring the
>   combine to after that fold (new `combine-late` action) applies it cleanly.
> * "the fix needs an addition no current instrument does" — the instrument was
>   `combine` all along, plus a year scope that stops deleting the years it did
>   not take.
>
> The root cause was a label defect one layer up: a row of
> `reference/article_group_authority.csv` giving a timber article the group
> SUGAR, because a systematic OCR failure outvoted the correct readings.

Reopened after the user asked why `Sawn — Fir` has no good data despite earlier
timber work. **The cause is identified and proved. The fix is not yet made** — the
one instrument that looked right is harmful, and was reverted.

## `Sawn — Fir` is not where the trade is

That node is a de-headed fragment: GBP 237K, 5 Tier-1 years, **zero** origin years.
The real commodity is `Wood And Timber — Sawn Or Split` — **GBP 282.9M**, 32 anchor
years, 27 origin years.

## It is short in almost every year, and always has been

```
1875 0.9122  1880 0.9220  1885 0.9261  1890 0.9460  1895 0.9739
1876 0.9130  1881 0.9081  1886 0.9390  1891 0.9629  1896 0.9140
1877 0.9184  1882 0.9127  1887 0.9311  1892 0.9681  1898 1.0000
1878 0.9007  1883 0.9156  1888 0.9478  1893 0.9704  1899 0.9999
1879 0.8951  1884 0.9219  1889 0.9460  1894 0.9016  1900 0.9299
```

Only 1898 and 1899 close, and those are exactly the two years
`reports/fir_findings.md` repaired by hand. That work was correct but *cell-level*
— it fixed the years it was aimed at and the other twenty-three were never
touched. A smooth 3-10% shortfall across twenty-five consecutive years is a
**missing component**, not scattered OCR error.

Verified not a regression from the 2026-08-03 campaign: the pre-campaign payload
snapshot carries `Sugar — Sawn Or Split, Planed Or Dressed, Fir` at exactly
GBP 14,474,668, the same figure, and no timber node was lost.

## The component is the `Unenumerated` sub-sort

It is split off into **anchorless sibling nodes** — `Wood And Timber — Sawn,
Unenumerated` (GBP 7.1M) and, under a stale sticky group, `Sugar — Sawn Or Split,
Planed Or Dressed : Unenumerated` (GBP 8.1M). Adding them to the parent:

| year | parent alone | + sub-sort |
|---|---:|---:|
| 1879 | 0.8951 | **0.9999** |
| 1884 | 0.9219 | **0.9990** |
| 1890 | 0.9460 | **1.0000** |
| 1894 | 0.9016 | 0.9449 |
| 1896 | 0.9140 | 0.9591 |
| 1900 | 0.9299 | 0.9776 |

Three years close essentially to the digit. The later years are only partly
explained, so at least one further component is missing after 1893.

## Why `fold` is wrong and `combine` is also wrong

`fold` merges by `(country, unit, year)` with the **target winning**, and the
parent and sub-sort list the *same* countries — 12 of 13-14 shared — so a fold
would discard almost every cell it was meant to add.

`combine` adds, and is arithmetic-guarded. It was tried and is **harmful**:

```
0 cells better, 4 worse.  exact01 3,774 -> 3,774 (unchanged)
Wood And Timber — Sawn Or Split 1891/1893/1895 within5 -> under (0.037, 0.032, 0.027)
                                1892             within5 -> nodata
```

`combine` merges the source's **label counter** into the target, which flipped the
node's plurality display name to `Wood And Timber — Sawn Or Split, Planed Or
Dressed, Fir`. That renamed node kept only **3** of the 32 anchor years; the rest
stayed on the old name with their origins removed, and were gutted to 0.03.

**A trap worth recording: the GBP-weighted figure went UP, 54.1% to 55.3%, while
four cells got worse and none got better.** That metric weights by commodity
value, and the rename reassigned a GBP 283M node's weight. A GBP-weighted gain with
no per-cell gain is a weighting artifact, not an improvement. Reverted; baseline
restored to 3,774 / 54.1% exactly.

## What is needed

The sub-sort must be added to the parent **without merging label counters**, so
the node keeps its identity and its 32-year anchor series. That is a
`manual_rows`-style cell-level addition, or a `combine` variant that leaves
`labels` alone. Neither exists yet.

## Also open, and larger

The timber family is scattered across **99 nodes worth GBP 999M**, of which GBP 72.7M
sits under groups that are plainly wrong — `Wine, British Made — Rough, Hewn,
Sawn, Or Split` (GBP 50.1M), `Sugar — Sawn Or Split, Planed Or Dressed, Fir`
(GBP 14.5M), `Sugar — … : Unenumerated` (GBP 8.1M) — plus `Wood And Timber` (GBP 234.9M)
and `Wood And Timber — Fir` (GBP 63.8M) carrying origins with **no anchor at all**,
and `Wood And Timber — Hewn` carrying 29 anchor years with **no origins**.
