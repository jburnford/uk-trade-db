# Sugar — scope for the careful review (state at 2026-07-25, HEAD 372bdcd)

Read `reports/sugar_findings.md` first: the 2026-07-24 unification, and the two
printed identities that make this family checkable at all —

```
    beetroot + cane and other sorts             =  unrefined, total
    in lumps and loaves + other sorts, incl candy =  refined, total
```

Both close to the digit for 1893–96. Everything below should be tested against
them or against an independently printed national total, never fitted.

The user's read (2026-07-25): *"the data looks OK, so I'm not seeing massive
failures, but there is still gaps."* That matches the snapshot — the big lines
track their anchors where they have one; the problem is **how few years have an
anchor at all**, plus a tail of era-labels and glue.

## The family as the map ships it — 24 commodities

| GBP | commodity | span | anchored yrs | within 5% | flags |
|---|---|---|---|---|---|
| 365,158,756 | Sugar — Unrefined, Total | 1872-1899 | 24 | 21 | gapyears |
| 223,806,800 | Sugar — Refined : Total Of | 1872-1899 | 25 | 23 | — |
| 183,657,273 | Sugar — Other Sorts, Including Candy | 1882-1899 | 7 | 7 | — |
| 109,910,501 | Sugar — Unrefined : Cane, And Other Sorts | 1880-1899 | 7 | 6 | — |
| 95,882,826 | Sugar — Unrefined : Beetroot | 1880-1899 | 7 | 7 | — |
| 37,361,636 | Sugar — In Lumps And Loaves | 1883-1898 | 6 | 6 | gapyears |
| 20,754,861 | Sugar — Total Unrefined Of All Kinds | 1873-1874 | 0 | 0 | nounit noanchor |
| 17,818,166 | Sugar — Refined, Or Rendered By Any Process Equal Thereto : In Lumps And Loaves | 1882-1899 | 0 | 0 | noanchor |
| 5,182,584 | Sugar — Molasses | 1872-1899 | 26 | 25 | gapyears |
| 4,223,573 | Sugar — Glucose | 1872-1896 | 14 | 10 | gapyears |
| 1,162,401 | Succades (Including All Fruits And Vegetables Preserved In Sugar) | 1881-1895 | 0 | 0 | noanchor |
| 692,288 | Succades (Including Fruits And Vegetables Pre- Served In Sugar) | 1875-1880 | 0 | 0 | noanchor |
| 555,388 | Spirits — Succades And Confectionery (Including Fruits Andvegetables Preserved In Sugar) | 1873-1874 | 0 | 0 | nounit noanchor |
| 421,917 | Sugar — Molasses, Treacle, And Syrup | 1875-1881 | 0 | 0 | nounit noanchor |
| 324,742 | Fruit — Unenumerated : Preserved Without Sugar | 1883-1895 | 0 | 0 | nounit noanchor |
| 236,303 | Sugar — Elephants, Sea Cow, And Sea Horse | 1881 | 0 | 0 | nounit oneyear noanchor |
| 224,506 | Sugar — Molasses, Treacle, Syrup, And Glucose | 1883-1884 | 0 | 0 | nounit noanchor |
| 208,483 | Spirits — Suggades And Confectionery (…Preserved In Sugar) | 1872 | 0 | 0 | nounit oneyear noanchor |
| 167,097 | Spices — Molasses | 1885 | 0 | 0 | oneyear noanchor |
| 157,053 | Preserved Without Sugar | 1882 | 0 | 0 | oneyear nooverlap |
| 143,967 | Sugar (Including All Fruits And Vegetables Preserved In Sugar) | 1885 | 0 | 0 | nounit oneyear noanchor |
| 34,660 | Sugar — Complete | 1899 | 0 | 0 | nounit oneyear noanchor |
| 0 | Sugar— — 4Th Class | 1873 | 0 | 0 | noval nounit oneyear noanchor |
| 0 | Sugar— — 3Rd Class | 1873 | 0 | 0 | noval nounit oneyear noanchor |

## What the shape suggests — hypotheses to TEST, not conclusions

**1. The anchor gap is the main story.** Other Sorts, Cane, Beetroot and Lumps
each publish origins across ~18–20 years but carry an anchor for only 6–7 of
them. `sugar_findings.md` records that the 1893–1900 totals for beetroot, cane,
glucose and lumps sat under an OCR'd `Cnts` header and were folded. So the
anchored years are probably the *late* ones and the 1880s totals are still
missing — sitting under another label, another era spelling, or a group the
sticky-group repair scattered. Find them before judging any of these series.
The identities above are the lever: where three of the four terms are known the
fourth is named.

**2. Two labels that look like one printed line, split.** Test with the fold
test that worked for cochineal and the seeds family — does one label's printed
national total equal the other's origin sum, year by year, to the digit?
  - `Sugar — In Lumps And Loaves` (anchor, 6 yrs) vs `Sugar — Refined, Or
    Rendered By Any Process Equal Thereto : In Lumps And Loaves` (£17.8M,
    **noanchor**, 1882-99). Long vs short printed heading, complementary
    coverage — the cochineal signature exactly.
  - `Sugar — Total Unrefined Of All Kinds` (1873-74, noanchor) is almost
    certainly the era label of `Sugar — Unrefined, Total`.
  - `Sugar — Molasses, Treacle, And Syrup` (1875-81) and `Sugar — Molasses,
    Treacle, Syrup, And Glucose` (1883-84) against `Sugar — Molasses`
    (1872-99): three spellings, contiguous non-overlapping spans. CAUTION —
    the 1883-84 label bundles GLUCOSE, which has its own commodity; check
    whether the printed line really merged them in those years before folding.
  - The three Succades labels (1872-74 / 1875-80 / 1881-95) tile the period
    with no overlap: one line, three spellings, two of them glued under
    `Spirits`. `Sugar (Including All Fruits And Vegetables Preserved In Sugar)`
    1885 and `Preserved Without Sugar` 1882 belong to this cluster too.

**3. Glue and junk to adjudicate, not fold.**
  - `Sugar — Elephants, Sea Cow, And Sea Horse` (£236k, 1881) — whale-fishery
    teeth/ivory under a stale SUGAR head. Refile or drop.
  - `Spices — Molasses` (1885), `Sugar — Complete` (1899), `Sugar— — 3Rd/4Th
    Class` (1873, zero value) — heads and fragments.
  - `Fruit — Unenumerated : Preserved Without Sugar` vs `Preserved Without
    Sugar` — the second is the same line de-headed.

## Method reminders that apply here specifically

- **A year that closes against its printed total is not a year that is right.**
  Sugar's sub-sorts and Totals sum to each other, so a mislabelled row can
  preserve every sum. Check per-row against the print, not just the totals.
- **Total vs sub-sort is the trap this family is famous for.** `Refined : Total
  Of` and `In Lumps And Loaves` + `Other Sorts, Including Candy` are the SAME
  trade counted two ways; the map's parent/child de-duplication does not know
  that, because these are sibling commodities, not parent/child origins. Any
  fold that merges a Total with a sub-sort double-counts. Round 8 of the
  anomaly log has the 1884/85 case where the fragment, the lumps line and the
  Total-of table all existed as separate labels.
- Watch the flow: several sugar twoup blocks were re-export tables misfiled as
  imports (anomaly log round 22).
- After ANY curation rename/fold here, regenerate
  `reports/country_t1_reconciliation.csv` (the artifact embeds it) and re-run
  `scripts/smoke_map.js`.
