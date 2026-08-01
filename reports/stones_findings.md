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

---

## The union fix, generalised — and it yields exactly one more pair

Next iteration. **exact01 3,541 → 3,543 (+2), within5 1,104 → 1,105,
denominator unchanged at 9,511, zero regressions.**

`match_orphan_countries` now **unions the unlabelled unit buckets** when
comparing an orphan's cells to a host's anchor: `per[unit] + per['?'] +
per['']`. Only `?` and `''` are ever added — unioning two *real* units would be
summing tons with numbers.

**367 payload nodes carry both a real unit and an unlabelled bucket**, so the
population at risk is large. The yield is not:

> **One new resolved pair.**

`Onions` → `Onions — Raw`. The de-headed era form holds origin tables for 1872,
1877 and 1879 with no anchor; the full name holds anchors 1866-1900 and has no
cells at all in those years. On `Bushel` alone neither year clears; on the
union both close **to the digit**:

| year | Bushel | unlabelled | total | anchor | |
|---|---|---|---|---|---|
| 1872 | 707,788 | 151,243 | **859,031** | 859,031 | **exact** |
| 1877 | 1,908,253 | 55,981 | **1,964,234** | 1,964,234 | **exact** |
| 1879 | 1,862,370 | — | 1,862,370 | 1,895,370 | 0.983 |

Country lists overlap throughout. Scoped to those three years; the source's
stray 1882 cell (3,259) is left out because the host already closes 1882.

### Honest accounting of the fix

The stones pair that motivated this was found **by hand**, not by the fixed
tool — it was already folded before the change. So the change's actual return
is the onions pair alone: **+2 exact01 and +1 within5**.

That is a real return on a small, correct change, but **it is not a seam**. 367
nodes have the split and 366 of them produce nothing, which says the unlabelled
bucket is usually either empty in the matched years or attached to a commodity
with no partner to find. Worth having in the tool permanently; not worth
expecting more from.

---

## The era-split merge: a −1 that buys a continuous series

Next iteration. **exact01 3,543 → 3,542 (−1), denominator 9,511 → 9,504 (−7),
zero true regressions.**

The two nodes are copies of one printed line, with **identical anchors wherever
both carry a year** — 1893 546,219, 1894 585,476, 1895 574,884, 1896 673,206,
1897 740,497, 1898 869,782, 1899 891,173.

| | anchors | closes |
|---|---|---|
| `Stones, Marble, And Slate : Rough, Hewn Or Manufactured : (Other Than Works Of Art)` | 1885-1900 | 1886-1894 |
| `Stones, Rough, Hewn, Or Manufactured (Other Thanworks Of Art)` | 1893-1899 | 1895-1899 |

Folded into the first — it has the fuller anchor range and eight closing years
the other lacks — **scoped to 1896-1899**, because both hold 1895 country cells
(571,884 and 574,578) and an unscoped fold would double that year to 1,146,462.

### The result, and the honest cost

The surviving node now runs **1885-1900 continuously**, with every year
measured except 1900:

**10 exact01, 5 within5, 1 nodata**, where before there were two nodes, 23
anchor-years, and 1893/1894 counted twice.

But the corpus count **falls by one**, and the reason is worth stating: **the
source's 1895 was the better copy**. It closed on the anchor (574,578) where
the target reads 0.995 (571,884). Scoping the fold to 1896-1899 discards it, so
a genuine `exact01` is given up to gain 1897 and to stop double-counting
1893/1894.

Including 1895 in the scope would not have saved it — both nodes hold cells
there, so the merge would double the year instead. **Keeping the better of two
overlapping copies is not something a year-scoped fold can express**; it would
need cell-level surgery, and 0.995 is not worth that.

So: **−1 exact01, −7 denominator, one commodity where there were two, and a
sixteen-year series with a single hole.** Recorded as de-duplication, not as a
gain.

Seven `Stones` nodes still remain, six of them anchorless.
