# The third match type: anchored node ↔ anchored node

Worked 2026-07-29 (`/loop /next-defect` iteration 23).

**exact01 3,374 → 3,458 (+84), nodata 4,655 → 4,507 (−148), within 5% 46.2% →
47.5%, GBP within 0.1% 51.4% → 51.6%, within 5% 68.2% → 68.4%. Zero true
regressions.** The second-largest move of the session.

## The gap

A stale or re-worded group head splits one printed line into two payload
commodities. Three instruments already existed for that, and each carried a
structural precondition:

| instrument | requires |
|---|---|
| `match_shadow_anchors` | the source has **no countries** |
| `match_orphan_countries` | the source has **no anchor** |
| `deheaded_anchor_match` | one name is a **suffix** of the other |

Staves broke all three at once last iteration: `Wood And Timber — Staves` held
countries *and* an anchor for 1890-91, `Staves, Of All Dimensions` held an
anchor for 1892-94, and neither name contains the other. **A node can hold an
anchor for one era and countries for another**, with the other era's anchor
under a different name.

## The fix, and why it stays safe

`match_orphan_countries` now takes **any node with countries** as a source, not
only anchorless ones. What keeps it honest is a **per-year** condition rather
than a per-node one:

> the source must not anchor the matched year itself.

If it does, the two nodes *disagree* about that year rather than completing
each other, and folding would be a duplicate merge. Everything else is
unchanged — ≥2 years agreeing within 0.02%, each ≥1,000, the host holding no
country data in them, and exactly one host clearing the bar.

Sources are tagged `orphan` (no anchor at all) or `era-split` (anchored
elsewhere) so the new population is separable from what has already been
worked. Population: **1,615 country-bearing sources × 751 hosts**, of which
**19 matched as era-split**.

## Twelve folds

| source | → host | evidence |
|---|---|---|
| `Hats Or Bonnets — Of Straw` | `Straw` | **13 years exact**, gains 18 |
| `Thrown, Dyed Or Not Dyed` | `Silk — Thrown` | **12 exact**, gains 13 |
| `Dye Stuffs… — Shumach` | `Shumach` | **11 exact**, gains 14 |
| `Skins, Furs, And Pelts — Goat, Undressed` | `Skins And Furs — Goat, Undressed` | **11 exact**, gains 13 |
| `Bar, Angle, Bolt And Rod` | `Iron — In Bars` | 6 exact, gains 9 |
| `Skins, Furs, And Pelts — Sheep, Undressed` | `Skins — Sheep And Lamb, Undressed` | 5 exact, gains 13 |
| `Straw Platting, For Making Hats Or Bonnets` | `Straw Platting For Hats Or Bonnets` | 5 exact |
| `Meat — Salted Or Fresh, Not Otherwise Described` | `Meat, Salted Or Fresh` | 5 exact |
| `Oil — Seed` | `Seed, Of All Kinds` | 5 exact |
| `Ammunition — Shot, Large And Small` | `Shot, Large And Small` | 4 exact |
| `Hats Or Bonnets — Of Felt` | `Of Felt` | 3 exact |
| `Apples — Raw` | `Fruit — Apples, Raw` | 3 exact |

Two are the same words with different punctuation (`Straw Platting, For Making
Hats Or Bonnets` / `Straw Platting For Hats Or Bonnets`). The rest are stale
group heads — the straw tables under a HATS OR BONNETS head, the seed tables
under OIL, the shot tables under AMMUNITION.

Per commodity the effect is much larger than the corpus count suggests:

- **`Straw`: 1 closing year → 17** (32 → 34 anchored years, 12 → 23 countries)
- **`Silk — Thrown`: 7 closing years → 27**

## The scope rule, extended

Iteration 18 established that a fold must be year-scoped to the host's missing
years. **That is not sufficient for an era-split source**, because the fold
*pops* the source node and any year outside the scope leaves the corpus with
it — and an era-split source, by definition, holds anchor years of its own.

So the scope here is **the host's missing years UNION the source's own anchor
years**. Computed per fold rather than taken from the `safe_scope` column.

## Honest note on the denominator

**9,596 → 9,553 (−43).** These merges remove duplicate anchor-years — the same
printed line's totals reaching the payload under two names. On the *new*
denominator the pre-iteration count of 3,374 reads 35.3% against **36.2%** now,
so the gain is real either way, but the percentage is flattered by roughly
0.2 points.

## What is left

Two era-split matches were declined:

- `Gum — Unenumerated` → `Of Other Sorts` (4 exact) — the host is a de-headed
  generic name; folding into it would cement a bad label.
- `Wood And Timber — Mahogany` → `Wood And Timber — Furniture Hardwoods And
  Veneers : Mahogany` (4 exact) — **the direction is wrong**. The sub-label is
  the damaged name and mahogany is the repaired commodity; this pairing wants
  the reverse fold, which the earlier iterations already did year by year.
  **A match is not a licence to fold in the direction the tool prints it.**
