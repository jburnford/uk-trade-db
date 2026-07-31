# Mahogany under two names, and why the unscoped fold had to be scoped

Worked 2026-07-31 (`/loop /next-defect`).
**exact01 3,486 → 3,488, denominator 9,524 → 9,518, zero regressions.**

## The gap

`Wood And Timber — Furniture Hardwoods And Veneers : Mahogany` sat at
bracketed-gap **rank 4 — 1882-1885, £2.32M, four years at 0.00** — inside a
series that otherwise closed 1876-81 and 1886-87.

## What it actually was

Two payload nodes carrying **the same printed line**:

| | anchors | countries |
|---|---|---|
| `…Furniture Hardwoods And Veneers : Mahogany` | 1868-1887 | 1876-81, 1886-87 |
| `Wood And Timber — Mahogany` | 1866-70, 1885-1900 | 1872-74, **1882-85**, 1886-99 |

Each holds what the other lacks in exactly the gap years. The proof is the
host's own country sums against the sub-label's anchors:

| 1872 | 1873 | 1874 | 1882 | 1883 | 1884 | 1886 | 1887 |
|---|---|---|---|---|---|---|---|
| **33,920 =** | **53,330 =** | 64,644/64,674 | **36,478 =** | 50,138/50,158 | **62,836 =** | **48,732 =** | **37,650 =** |

**Eight years agreeing, six to the digit.** Folded into the clean name, per the
standing rule that the sub-label is the damaged one — the same direction the
iteration-23 note insisted on when it declined this pairing's mirror image.

## The part worth recording: unscoped was wrong here

Every fold this session has defaulted to **unscoped**, because an unscoped
fold can only add to the target and any harm is visible to the diff. That rule
held — the harm *was* visible — but this is the first case where it fired:

```
Wood And Timber — Mahogany  1887  ('exact01', 37650) -> ('within5', 38287)
Wood And Timber — Mahogany  1888  ('exact01', 42859) -> ('within5', 44541)
```

**Both nodes carry country cells for 1886-1889, and they are the same cells.**
The payload's near-duplicate dedup caught most of the overlap — 1877 came out
at 56,700 rather than a naive 108,163, 1886 stayed exact — but it is a
*near*-duplicate test, and the residue it let through was enough to push two
digit-perfect years off exact.

Scoping the fold to **1868-1885** fixes it, and **discards nothing real**: the
source's 1886-1889 country cells are duplicates of the host's own, which
already close to the digit in all four years. The rule that follows is
narrower than "always unscoped":

> Default to unscoped. But when **both** nodes hold countries in overlapping
> years, scope the fold to the years the target lacks — dedup is a
> near-duplicate test, not a set union, and it will not save you.

## Result

The merged commodity closes in **14 of its 35 anchored years**, with
1872-74 and 1882-84 newly exact and 1886-1892 preserved. Corpus effect is +2
because the fold also removes six duplicated anchor-years from the
denominator — the usual honest arithmetic of de-duplication.

## Left open in this family, which is badly scattered

- **`Furniture And Hardwoods : Mahogany Tons Unenumerated`** is another
  **fused two-column header**, and it decodes cleanly:
  `5015862786` → 50,158 ‖ 62,786, `5605355983` → 56,053 ‖ 55,983,
  `4873250717` → 48,732 ‖ 50,717, `3765057994` → 37,650 ‖ 57,994 — four of
  five years reproducing **both** the Mahogany and the Unenumerated anchors
  exactly (1884's head is one digit out). Unlike the feathers case this buys
  nothing: **both halves are already known**, so the node is pure junk
  contributing 5 `nodata` years. A drop, not a Rosetta stone. **Recording the
  distinction matters — the same artifact is decisive in one family and
  worthless in the next, and only the decode tells you which.**
- `Wood And Timber — Furniture, Hardwoods, And Veneers : Unenumerated` still
  has holes at 1881, 1884-87. Its candidate partner
  `Wood And Timber — Mahogany : Unenumerated` does **not** match — 0.82, 0.24,
  0.99, 0.16 against the anchors — so that is a different split, not this one.
- Two shadow nodes with no countries at all: `Furniture Woods And Hardwoods —
  Unenumerated` (T1 1885-1896) and `Furniture Wood: Mahogany` (T1 1893-97).
  The latter's anchors are identical to the merged mahogany node's for
  1893-97, so it is a third duplicate label of the same series.
- The merged node's residual: 1881 reads **1.88** and 1897 **1.36**, both
  over-counts that predate this fold and are the next thing to look at here.

## A tool gap worth checking

`match_orphan_countries`' era-split path should in principle have found this
pair — the source has countries, does not anchor 1882/1883/1884, and the host
anchors them with no countries of its own. It did not. Worth a run to see
whether the candidate-uniqueness guard is rejecting it (this family has at
least four near-identical labels, so "exactly one candidate clears the bar"
is a plausible culprit).
