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
