# Stones 1889 and 1893: the unit split hid a three-year match

Worked 2026-08-01 (`/loop /next-defect`).
**exact01 3,539 → 3,541 (+2), denominator unchanged at 9,511, zero
regressions.**

```
Stones, Marble, And Slate : Rough, Hewn Or Manufactured : (Other Than Works Of Art)
  1889  ('nodata', 0, 399122) -> ('exact01', 399122, 399122)
  1893  ('nodata', 0, 546219) -> ('exact01', 546219, 546219)
```

## The pair

Bracketed-gap rank 8, £1.16M. `Stones, Marble, And Slate — (Other Than Works
Of Art)` holds origin tables for 1889, 1890, 1891 and 1893 with **no anchor at
all**, while the target holds the anchors and read **0.00 in 1889 and 1893**.

It closes on the target's Tier-1 in **three** years:

| year | source | anchor | |
|---|---|---|---|
| 1889 | 392,423 `Ton` **+ 6,699 `?`** = 399,122 | 399,122 | **exact** |
| 1891 | 428,072 `Ton` | 428,072 | **exact** |
| 1893 | 541,338 `Ton` **+ 4,881 `?`** = 546,219 | 546,219 | **exact** |

Scoped to 1889 and 1893 — the only years the target lacks; it already closes
1890 and 1891 from its own cells.

## Why no matcher found it: the unit split

**The arithmetic matchers sum per unit.** This commodity's cells are divided
between `Ton` and a `?` bucket — cells whose printed unit was never captured —
so on `Ton` alone only **1891** clears, and the bar is **two** agreeing years.
Three exact matches were sitting there and every instrument scored it as one.

That is a distinct blind spot from the ones already recorded:

| instrument | blind to |
|---|---|
| `match_orphan_countries` / `match_shadow_anchors` | single-year sources; **and now: unit-split sources** |
| `match_by_name` | sources whose article shares no name relation |
| `detect_flow_misfile` | value-only blocks (fixed); entity-corrupted signatures |

**A source split across a real unit and an unlabelled one is arithmetically
invisible, however many years actually agree.** The fix, if this is worth
pursuing, is to test the union across all units against the anchor rather than
per-unit — the payload's own unit-healing already does exactly that
downstream, which is why both years landed **exact** here rather than the
`within5` I predicted from the `Ton` cells alone.

## The family is still fragmented

Nine `Stones`/`Stones And Slates` nodes remain, seven of them with no Tier-1 at
all — `Slate By Tale`, `Slate By Sale`, `Slate By Talc` (three OCR spellings of
one line), `Grindstones, Millstones, And Other Sorts`, and others. The target
also reads 0.00 for **1896-1900**, where the sibling `Stones, Rough, Hewn, Or
Manufactured (Other Thanworks Of Art)` closes 1895-1899 — the two are era-split
copies of one series and a merge is the obvious next step, but both carry
anchors for 1893-1895 and the overlap needs scoping care.
