# Nuts and kernels 1875: the target did not close, a different defect did

Worked 2026-07-31 (`/loop /next-defect`).
**exact01 unchanged at 3,531 / 9,515. Zero regressions.** One real data
correction, one honest negative, and one mechanism finding.

## The item: `Nuts And Kernels — Of Other Sorts` 1875 — NOT RECOVERABLE

Bracketed-gap rank 6, £1.58M. The commodity reads 1.00 in 1872, 1873, 1876 and
0.99 in 1874; **1875 alone reads 0.00**, against a Tier-1 of 584,525.

`as_1875` contains **no `Of other Sorts` origin block at all**, in either
engine. What it contains instead is a badly interleaved page:

- Chandra filed a run of `Raw, not otherwise described` blocks under a
  `FLOWERS, ARTIFICIAL` head — those are *fruit*, not flowers;
- Infinity has, at seq 548, a **run-in list of country labels with no numbers
  whatever** — `Almonds : From France ,, Portugal ,, Spain and Canary Islands
  ,, Italy ,, Morocco ,, Gibraltar ,, Other Countries` — followed at seq
  549-553 by a **column of bare TOTALs** (182,345 / **584,525** / 1,341,704 /
  66,113 / 986,248) with no countries attached.

**The labels and the numbers are in the parse, in the right order, and neither
engine paired them.** The 584,525 sitting there is the Tier-1 itself, not an
origin table. There is nothing to relabel and nothing to fold.

**Verdict: page-image job**, alongside feathers 1890. Recorded so the next
pass does not re-derive it.

## What was found instead: a parent counted beside its own members

The sibling `Nuts And Kernels — Commonly Used For Expressing Oil Therefrom`
read **1.9012** in the same year — an overcount nobody had looked at.

The cause: the row at `as_1875` seq 1036 is labelled **`West Coast of Africa
(Foreign)`** and carries **36,745 Tons — the block's own printed grand total**,
against a Tier-1 of 36,715 (0.08%). It escaped the subtotal guard because
**that guard recognises only labels whose first word is `total`**, and this one
is a region name. So it sat beside its own members:

| The Gold Coast | Not Particularly Designated | Islands In The Pacific | Australia | British West Africa | Portuguese Possessions |
|---|---|---|---|---|---|
| 13,732 | 10,084 | 3,429 | 2,788 | 2,744 | 281 |

`13,732 + 10,084 + 3,429 + 2,788 + 2,744 + 281 = 33,058`, and
`33,058 + 36,745 = 69,803` — exactly what the payload was summing.

Dropped. **1875 goes from `over` 1.90 to `under` 0.90.** It does not close,
because two members — `India: French Possessions` 2,827 and `Other Countries`
857 — are not reaching the payload; with them the block gives 36,742 against
36,715. That residue is a separate question.

**The metric does not move at all for this**, and it is still worth doing: a
fabricated 36,745-ton country called *West Coast Of Africa Foreign* was being
shown to readers as an origin, and the commodity was overstated by 90%.

## Mechanism finding: `new_country` cannot suppress a consensus cell

The first repair attempted was a `group_repairs` row with
`new_country = 'TOTAL'` on that seq, to let the existing subtotal machinery
drop it. **It was completely inert.**

`new_country` is a row-level relabel applied inside the **groupfix** path, and
this cell does not arrive that way — it comes through **consensus**, which the
groupfix path cannot suppress. The row was backed out rather than left in the
reference file as dead weight, and `commodity_curation` **`drop-country`**
(year-scoped to 1875) is the instrument that works.

**Rule: match the tool to the cell's SOURCE, not to its shape.** A row-level
label fix only helps if the row reaches the payload through the path that fix
lives in.

---

## RETRACTED 2026-08-01 — 1875 was recoverable, and it closes exactly

Re-tested in `/loop /next-defect`. **The "NOT RECOVERABLE / page-image job"
verdict above is wrong.** `Nuts And Kernels — Of Other Sorts` 1875 went from
`nodata` to **exactly 1.000000** — 584,525 of a Tier-1 of 584,525.

**exact01 3,544 → 3,545, nodata 4,343 → 4,342, denominator unchanged at 9,497.
One commodity-year changed in the whole corpus; zero regressions.**

### Why the first pass missed it

**It looked at the parse, not at the raw text.** Everything it reported about
`country_obs` and `country_obs_inf` was accurate — neither engine's *parse* has
an `Of other Sorts` block — but both engines' **OCR** transcribe the table in
full.

The import country section prints, under `NUTS and KERNELS`, the line:

```
„ Other Sorts. See FRUIT.
```

**A printed cross-reference.** The origin table is filed in the FRUIT section
as `„ Nuts, principally used as Fruit :`, value-only (the quantity column is a
literal `-`):

| Belgium | France | Spain | Italy | New Granada | Ecuador | Brazil | BWI Islands | British Guiana | Other |
|---|---|---|---|---|---|---|---|---|---|
| 18,330 | 128,284 | 214,253 | 12,322 | 26,843 | 18,446 | 67,402 | 41,312 | 8,227 | 49,106 |

**They sum to 584,525 — the block's own printed Total and the Tier-1 anchor, to
the digit.** Chandra and Infinity transcribe all ten figures and the Total
identically.

The `584,525` the first pass found "sitting there ... the Tier-1 itself, not an
origin table" was **this block's printed Total**, and the bare-TOTAL column
beside it (182,345 / 584,525 / 1,341,704 …) is the Almonds / Nuts /
Oranges-and-Lemons totals of the same page.

**Why no parser saw it:** the as_1875 FRUIT page uses a four-cell-per-side
layout with an **empty indent cell before every country**, so both table
extractors collapsed it — Chandra emits only `Raw, not otherwise described`
blocks under the stale `FLOWERS, ARTIFICIAL` head, Infinity a run-in list of
country labels with no numbers followed by that column of bare Totals.

### The second half of the fix, and a trap worth naming

Ten `manual_rows` under `FLOWERS, ARTIFICIAL | Nuts, principally used as Fruit`
— the stale head the **sibling years already arrive under** (1872/73/74/76 all
do), per the [[payload-node-string-keying]] rule.

They landed in `country_year_final` and **the payload did not move at all.**

`commodity_curation.csv` folds that node into this commodity, and the fold row
was **year-scoped `1872;1873;1874;1876`** — the scope the orphan matcher wrote
when it adjudicated the pair, listing only the years that *had country data at
the time*. **1875 was excluded, so the fold silently discarded exactly the
cells the repair had just recovered.**

**RULE: a year-scoped curation fold is a filter on future data, not just a
record of past evidence. After recovering a year, check every fold on the path
from the label you wrote to the node you are aiming at, and widen the scope.**
The failure is silent in both directions — the rows are present and correct in
`country_year_final`, and the metric does not move.

### Result

| year | ratio |
|---|---|
| 1872 | 0.999931 |
| 1873 | 1.000000 |
| 1874 | 0.993460 |
| **1875** | **1.000000** |
| 1876 | 0.999943 |

The commodity's early era is now complete. **1874 at 0.9935** (546,863 of
550,463, 3,600 short) is the only remaining gap in it, and the two findings
recorded in the original pass — the `West Coast of Africa (Foreign)` subtotal
masquerading as a country, and `new_country` being unable to suppress a
consensus cell — both still stand.
