# Pyrites 1873, and why three recent gaps produced nothing

Worked 2026-08-01 (`/loop /next-defect`).
**exact01 unchanged at 3,542, denominator 9,504 → 9,497 (−7), zero
regressions.**

## The item

Bracketed-gap rank 7, `Pyrites Of Iron Or Copper` 1873, £1.08M. The 1873
origin table was never missing — it sits in the earlier era wording
**`Pyrites Of Iron, Copper, Or Sulphur`**, where four countries (Norway,
Portugal, Spain, Other) sum **520,347 = the anchor to the digit**, and that
node **already read `exact01`**.

The two carry identical anchors for every year both hold (1868 229,720, 1869
319,947, 1870 411,512, 1872 517,626, 1873 520,347, 1874 498,637; 1871 differs
in the last digit only). Folded, scoped to 1873 — the source's other six
anchor-years are duplicates with no cells behind them.

**Net effect on the corpus count: zero.** The target gained 1873; the source's
identical 1873 left with it. Seven duplicate anchor-years dropped out of the
denominator. The commodity is now one node instead of two.

## The pattern worth naming

**This is the third consecutive item of exactly this shape** — brass and bronze,
stones, and now pyrites. In each, the ranked "gap" was **illusory**: the year
already closed, under a sibling label carrying the same anchor. All three
produced a −1 or 0 corpus movement while genuinely improving the data.

**The bracketed-gap screen looks at one node at a time**, so it cannot tell a
real hole from a duplicate-label split.

## Measured: 9 of 101 ranked gap-years are illusory

| commodity | year | already closed by |
|---|---|---|
| `Leather Manufactures — Unenumerated` | 1882, 1884 | `Leather, Undressed — Unenumerated` |
| `Cocoa Nut` | 1876 | `Oil — Coco-Nut` |
| `Oil — Coco-Nut` | 1875, 1885 | `Cocoa Nut` / `Coco Nut` |
| `Sumach` | 1890, 1892 | `Shumach` |
| `Sago` | 1893 | `Sago, And Flour Or Meal Thereof` |
| `Manganese, Ore Of` | 1891 | `Manures — Phosphate Of Lime And Rock` |

**The last row is the caution.** Manganese ore and phosphate manures are
unrelated commodities that happen to share an anchor value in one year — a
coincidence, not a duplicate. So this check **cannot be used on its own**: it
needs the name relation from `match_by_name` as a filter, exactly as the
single-year test did.

Two of the others (`Oil — Coco-Nut`, `Leather Manufactures — Unenumerated`) are
pairs already **declined** in `match_declines.csv` — one for wrong direction,
one for matching on a generic `Unenumerated`. Those declines stand until
re-argued; the anchor agreement is new evidence but not by itself sufficient.

## What this means for the ranking

**About 9% of the remaining ranked gap-years are not work at all.** The screen
overstates what is left, and three iterations were spent discovering that one
family at a time. Filtering the ranking by "does another node with this anchor
already close this year" — with a name-relation guard — would strip them out
before they are picked. That is the next tooling step here.
