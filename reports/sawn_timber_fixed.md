# Sawn timber closed, and the label defect underneath it

Sequel to `reports/sawn_timber_findings.md`, which identified the missing
component but concluded that no instrument could apply it. Both halves are now
fixed.

**Measured: exact01 3,774 → 3,790 of 9,509 (+16). GBP-weighted within 0.1%
54.1% → 55.1%, within 5% 72.6% → 73.7%. Twenty commodity-years better, ZERO
worse.** Fifteen years of `Wood And Timber — Sawn Or Split` now close to the
digit where they had never closed at all.

Unlike the attempt recorded in the previous report, the GBP-weighted rise here
is backed by a per-cell gain — it is not the weighting artefact that report
warned about.

## The label defect: a vote that loses to a systematic OCR failure

The root cause was not in the timber data. It was one row of
`reference/article_group_authority.csv`:

```
"Sawn or Split, Planed or Dressed : Unenumerated",SUGAR,0.61,228,2,,
```

That file is `repair_groups.py`'s cross-volume plurality vote: the parser's
sticky group state loses column-top headings, so the true group is recovered as
the commonest reading of each article. The method assumes the defect is
*sporadic*. Here it is *systematic* — the as_1898 and as_1899 Infinity parses
lost the `WOOD AND TIMBER` heading for the **whole timber section**, putting
Hewn Fir/Oak/Teak/Unenumerated and Sawn Fir/Unenumerated all under a stale
`SUGAR` head, 140 rows of it. Those outvoted the seven volumes that read the
heading correctly (as_1875-81, ~66 rows), and SUGAR won at 0.61.

**A plurality is not evidence when every reading shares one cause.** The
clearest case in the same family is `Staves, of all Dimensions`, which the vote
gives to SUGAR at **plurality 1.00** of 138 rows — unanimity, and wrong in every
row.

The evidence the vote cannot see is the **abstract's own group line**: the
Annual Statement prints `Wood and Timber | Sawn or Split` and
`Wood and Timber | Staves, of all dimensions` in the summary table, where no
column-top heading can be lost. Checking all 576 applied vote rows against it,
**61 are contradicted by the abstract** — see "Still open" below.

### The fix

`reference/group_authority_overrides.csv`, a new hand-adjudicated file that
wins over the vote, with the abstract cited as evidence per row. Four entries so
far, all timber. Applied in two places:

* `vote_country_years.load_group_authority()` — overrides beat the vote, and
  apply regardless of its REVIEW flag, so they can also promote an article the
  vote left unapplied.
* `integrate_sources.main()`, just before the dedup — because the vote is only
  consulted on the **consensus** path. Gap-fill, sub-entry, two-up and manual
  rows carry whatever stale group their parse had, which is how the sawn section
  ended up split between `Wood And Timber — Sawn, Unenumerated` and
  `Sugar — Sawn Or Split, Planed Or Dressed, Unenumerated` at the same time.

**Applying the whole vote on the gap-fill path was measured and rejected**: it
would re-group 1,228 of 8,025 rows, and the vote is wrong often enough
(`Furs, Rabbit Skins` → Cotton, `Manganese, Ore of` → LEATHER MANUFACTURES) to
corrupt groups the Infinity parse had right. Only adjudications travel.

Effect: 129 rows re-grouped. `Sugar — Sawn Or Split, Planed Or Dressed :
Unenumerated` (GBP 8.1M) and `Sugar — Sawn Or Split, Planed Or Dressed, Fir`
(GBP 14.5M) are gone as commodities; the Unenumerated sub-sort is now one
continuous series 1875-1900. Zero cells changed bucket from the relabel alone,
which is the expected result — a sub-sort with no anchor of its own is never
measured until it joins one.

## The arithmetic: a deferred, anchor-guarded combine

The abstract prints **one** quantity line for the section (`Sawn or Split`,
1868-96) while the country tables print it broken into **two** sub-sorts, Fir
and Unenumerated. The payload node held the section anchor and only the Fir
origins, so it ran 3-10% short in every year 1875-96. The shortfall is the
sub-sort, to the digit: 1875 is `3,305,390 − 3,015,032 = 290,358`, which is the
Unenumerated table's 1875 sum exactly, and the same holds in 1876, 1877, 1878,
1881, 1882, 1885, 1886, 1889, 1890 and 1891.

Two things had to change before a `combine` could work.

**1. It has to run AFTER the era-wording fold.** This is what defeated the
previous attempt. At the normal curation point the target is still *two* nodes —
the anchor-only `Wood And Timber — Sawn Or Split` (GBP 272K, 25 T1 years, no
origins) and `Wood And Timber — Sawn Or Split, Planed Or Dressed, Fir`
(GBP 314M, the origins) — and `fold_era_wordings` is what later makes them one.
Combining early puts the constituent on the anchor-only half; measured, that
splits the node, leaves 1891/1893/1895 reading **0.03** and drops 1892 to
nodata. That is the "combine renamed the node and gutted it" result the previous
report recorded, and the cause was never the label counter — it was **pass
order**.

New action `combine-late` in `commodity_curation.csv`, applied in a second
curation phase after the era fold. Deferring is safe for exactly the reason the
existing post-era re-runs of the anchor passes are safe: a combine only moves a
cell where the year's own printed total says the cell brings it closer.

**2. A year-scoped combine must not delete the years it did not take.** The
scope filter dropped the out-of-scope cells outright. A scoped `combine` means
"in these years the source is a constituent of the target", not "the other years
are junk" — so the remainder now stays in the payload under its own name, with
`v` split between the two halves in proportion to cell value. Without this the
sub-sort's 1898-1900 origins (GBP 3.35M of real trade) were deleted.
`fold`/`rename` keep dropping the remainder: there the *label* is wrong, in
every year.

### Why the scope is 1875-1896

That is exactly the span where the anchor is the section total. **From 1898 the
abstract prints `Sawn: Fir` — a fir-only anchor — and the fir table already
closes against it to the digit** (1898 and 1899, the two years
`reports/fir_findings.md` repaired by hand). Adding the sub-sort there would
push both off a closure that is already right. 1900's 7% gap is *not* this
component either: the sub-sort covers only 305,476 of the 448,627 missing.

The arithmetic guard would have refused most of that on its own; the scope makes
the reasoning explicit rather than relying on it.

## Result

```
        before   after            before   after
1875    0.9122   1.0000    1886    0.9390   1.0000
1876    0.9130   1.0000    1887    0.9311   0.9921
1877    0.9184   1.0000    1888    0.9478   0.9988
1878    0.9007   1.0000    1889    0.9460   1.0000
1879    0.8951   0.9999    1890    0.9460   1.0000
1880    0.9220   1.0000    1891    0.9629   1.0000
1881    0.9081   1.0000    1893    0.9704   0.9999
1882    0.9127   1.0000    1895    0.9739   1.0000
1883    0.9156   1.0000    1896    0.9140   0.9573
1884    0.9219   0.9988    1898    1.0000   1.0000  (untouched)
1885    0.9261   1.0000    1899    0.9999   0.9999  (untouched)
```

1898 additionally moved from 6,204,727 to **6,204,787 — its printed total to the
digit** — because putting the duplicate Infinity copy of the fir table on the
right signature let the payload dedupe keep the better-ranked reading per cell.

Still short and honestly so: 1868-74 (no origin table printed on either
engine), 1892 (no Unenumerated table in any volume), 1894 0.9440, 1896 0.9573,
1900 0.9299.

## Also fixed: a GBP 50.1M phantom on the published map

`Wine, British Made — Rough, Hewn, Sawn, Or Split` was the fifth-largest timber
"commodity" in the payload and is on the published map at that size. It is one
as_1872 two-up block, and **the entire GBP 50.1M is a single corrupt row**: a
country label made of two fused printed lines, `British Possessions in South
AfricaMauritius`, carrying 1,779,661 units / GBP 61,301,773 against the block's
own printed Total of **18,884 / GBP 82,985** — 94x the total it belongs to. The
ten clean members sum to 15,804.

The article label is the stale one; the *group* is right, and the countries
(Australia, British Possessions in South Africa, Ceylon, Channel Islands, Chili,
Peru, Uruguay, Western Africa) are British-made-wine **export** destinations, so
the block is an export table filed as an import one. Nothing in it belongs to an
import commodity: not the article, not the flow, not the number. Dropped.

## Two traps worth keeping

**A curation row's position in the file is load-bearing.** Once the override
gives `Staves, of all Dimensions` its real group the node emits under a new
name, and the curation row keyed on the old name goes dead. Re-keying it *in
place* at index 666 measures **−4 exact01**; the identical row **appended at the
end** of the file reproduces the original numbers exactly and costs nothing.
Rows are applied in file order and this fold's target is assembled by rows that
precede it. (Letting the era pass handle the pair instead costs −2, on the
opposite tie-break: later-era-wins rather than target-wins.)

**The previous report's diagnosis was half right.** The combine really was
harmful, and the node really was renamed — but not because `combine` merges
label counters. Curation runs on the emitted payload, which has no label
counters left. The rename was the era-wording fold declining to merge a node
that curation had already altered. Pass order, not label merging.

## Still open

* **61 of the 576 applied group-authority rows are contradicted by the
  abstract.** Some contradictions are obviously right and unworked
  (`Flax and Linseed` → Seeds not Cotton; `COPPER, Ore of` → Metals and Ores not
  CONFECTIONERY; `Boots and Shoes : Unenumerated` → Leather Manufactures not
  JUTE; Champagne/Hock/Moselle/Burgundy → the wine section, not TOBACCO). Some
  are noise (`Total of all Kinds`, n=1). **A blanket "abstract wins" rule is NOT
  safe** and this needs the same per-row adjudication the four timber rows got.
  Reproduce the list by comparing `article_group_authority.csv` against the
  `consensus` table's own `article_group` per article signature.
* `Mahogany : Unenumerated` → WOOD AND TIMBER was adjudicated and **measured at
  −2** (it overshoots `Wood And Timber — Mahogany` 1887/1888, both currently
  exact). Left out of the overrides file deliberately; the mahogany family needs
  its own pass.
* The stones family is split the same way — `STONES, MARBLE, and SLATE. Rough,
  Hewn or Manufactured` votes to `STATIONERY other than PAPER` at 0.83 — leaving
  `Stones, Marble, And Slate : ...` (GBP 16.2M, 17 T1 years) beside
  `Stationery Other Than Paper — Stones, ...` (GBP 2.4M). Not timber, not
  touched.
* `Wood And Timber — Hewn` still holds 29 anchor years with no origins, and
  `Wood And Timber` (GBP 234.9M) and `Wood And Timber — Fir` (GBP 63.8M) still
  hold origins with no anchor. The hewn side of the section has the same
  two-sub-sorts-one-anchor shape the sawn side just had, and was not worked.
