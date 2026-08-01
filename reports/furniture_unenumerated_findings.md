# Furniture hardwoods "Unenumerated" 1881: a sub-sort that lost its parent

Worked 2026-08-01 (`/loop /next-defect`).
**exact01 unchanged at 3,539, within5 1,103 → 1,104, denominator unchanged at
9,511, zero regressions.**

```
Wood And Timber — Furniture, Hardwoods, And Veneers : Unenumerated
  1881  ('nodata', 0, 51566) -> ('within5', 51266, 51566)
```

## What it was

Bracketed-gap rank 7 (1881-82, £1.17M). The 1881 table is in `as_1881` and was
never lost — it simply lost its **parent prefix**. Chandra files it as a bare
`Unenumerated` at seq 1702-1713, sitting **immediately after** the
`Furniture, Hardwoods, and Veneers : Mahogany` block, which is what identifies
it: it is that heading's second sub-sort. Infinity instead runs it on under the
`Mahogany` label, so its "Mahogany" block (seq 1178-1198) covers **two tables**.

Corroboration beyond position: the block's printed TOTAL is **51,566 = the
Tier-1 for 1881 to the digit**, and the country list — Turkey, Italy, Hayti,
Central America, Brazil, the British West Indies — is furniture-hardwood
country, not fir or deal.

## Repaired from Infinity, because Chandra is row-slipped

Chandra's copy **lost its leading row** (Russia, 942 tons / £10,759) and every
label sits one row up — its "Russia" carries Infinity's Germany figures, and so
on down. That is exactly why its members sum 50,624 against a printed 51,566.

**Neither engine's members actually close**: Chandra is 942 short, Infinity 300
short. Infinity is simply the better copy, so the year lands at **0.9942**, not
exact. Recorded as such rather than described as a close.

## The label form matters, and got it wrong first

The first attempt used `Furniture, Hardwoods and Veneers : Unenumerated` — the
spelling that feeds the node in **1880**, taken from `country_year_final`. It
**split the node**, costing 1878, 1879 and 1880 their exact closes and 1877 its
partial:

```
1878  ('exact01', 25117) -> ('nodata', 0, 25117)
1879  ('exact01', 32425) -> ('nodata', 0, 32425)
1880  ('exact01', 37846) -> ('nodata', 0, 37846)
```

Backed out, baseline restored, and retried with the **comma** form
`Furniture, Hardwoods, and Veneers : Unenumerated` — matching the payload node
name and the as_1881 Mahogany sibling — which lands cleanly.

**This is the farinaceous lesson recurring: `build_viz_payload` keys the node on
the group/article STRING, so a repair must use the spelling the node already
carries, not merely a spelling that reaches it from some other year.** A single
comma is enough to fork a commodity.

## Still open

**1882 reads 0.09** and a printed-total hunt for its anchor (52,770) across
`as_1882`/`as_1883` returns nothing — a different cause, not examined. The
commodity also has holes at 1868-74 and 1884-87.
