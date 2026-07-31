# A screen for phantom region articles — 66 blocks, and three wrong place-tests

Worked 2026-07-31 (`/loop /next-defect`).
**No data change; baseline unchanged at exact01 3,496 / 9,518.** A new
instrument, built because the last iteration concluded that the arithmetic
matchers are exhausted and **structural** evidence is what remains.

## The gap in the existing repairs

`repair_country_as_article.py` already handles one form of this defect: a
printed region heading ('From West Africa:') is absorbed as the article, and
because the GROUP is the commodity (TEA, COFFEE) the repair is
`article -> NULL`.

**That repair is wrong, silently, whenever the group has real sub-sorts.**
`FEATHERS AND DOWN` prints *For Beds* and *Ornamental*; when as_1895 absorbed
'British Possessions in South Africa' the rows belonged to **Ornamental**, the
article immediately above — not to the group. Nulling the article would have
invented a commodity. Both feathers cases were found by hand; this screen
looks for the rest of that sub-class.

## Result: 102 candidate rows, 66 distinct blocks, 24 groups, 16 volumes

Two printed headings account for almost all of it:

| phantom article | rows |
|---|---|
| `East Coast of Africa` | 46 |
| `West Africa` | 46 |
| everything else (`British East-Indies`, `South Africa`, `Australia`, …) | 10 |

Named leads at the top include `SUGAR | East Coast of Africa` → *Cane, and
Other Sorts* (43 rows), `HIDES, Raw, and Pieces | East Coast of Africa` → *Dry*
(32, both engines), `NUTS AND KERNELS | West Africa` → *Commonly used for
expressing oil* (28, both engines), `COCOA | West Africa`, `SPICES | East Coast
of Africa` → *Pepper*, `SKINS and FURS | East Coast of Africa` → *Sheep,
Undressed*, and `IVORY | East Coast of Africa`.

**`NUTS AND KERNELS | West Africa` is worth noting**: `Nuts And Kernels — Of
Other Sorts` 1875 is sitting at bracketed-gap rank 7 (£1.58M), and this may be
the same defect in the same family.

## Three wrong place-tests, and why the reference cases earned their keep

The screen was tested against the two feathers blocks already solved by hand
**before** its output was believed, and that test failed three times:

1. **"used as a country by ≥5 commodities"** → 682 candidates, almost all the
   word `Unenumerated`, which leaks into the country column constantly.
2. **Adding "…and used as an ARTICLE in ≤2 groups"** → down to 7 candidates,
   but `BUTTER`, `BRISTLES` and `MILK, CONDENSED` survived (they leak into the
   country column via row-slips), and **both reference cases were still
   missing**.
3. **Adding gazetteer containment**, then discovering the real cause of the
   misses: `as_article['south africa'] = 39`.

That last number is the finding. The guard was **exactly inverted for the
class being hunted** — 'South Africa' is an article in 39 different groups
*precisely because it is a phantom in 39 different groups*. A frequency test
cannot distinguish "this word is a commodity descriptor" from "this defect is
widespread", and here it did the opposite of what was intended.

**Placehood is a semantic question.** The gazetteer answers it directly, needs
no frequency guard, and excludes `Unenumerated` for free because it has no
gazetteer overlap. Also fixed on the way: the "group has ≥2 real articles"
test had to become **corpus-wide** rather than per-volume, because as_1895
parses only `Ornamental` beside the phantom and a per-volume count of 1
skipped the very case the screen exists to find.

**The general rule: test a new screen against cases you already solved by
hand, and do it before you look at its output.** Two of these three versions
produced confident, plausible-looking lists that did not contain the answer.

## Honest limitation — the arithmetic column is not wired

`parent_t1` is empty on **every** row, so `closes` is empty everywhere and the
list is ranked by block size rather than by evidence. The cause is a name
mismatch: `country_obs.article_group` reads `FEATHERS AND DOWN` while
`consensus.article_group` reads `Feathers`, so the Tier-1 lookup finds
nothing. Until that is bridged the screen **locates** candidates and a human
must do the closure test, exactly as I did for as_1895 and as_1896.

That is still the useful half — it turns "search 16 volumes by hand" into
"adjudicate 66 named blocks" — but the column that would rank them by proof is
the obvious next piece of work, and nothing here should be folded on the
strength of the ranking alone.

---

## The closure column, bridged — and the first repair off the screen

Same day, next iteration. **exact01 3,496 → 3,498, denominator unchanged at
9,518, zero regressions.**

### Fixing the lookup

The Tier-1 lookup now keys on **signature**, not on the literal
`article_group` string, using the same `validate_gold.sig` the pipeline uses.
The literal match had found a Tier-1 for **zero of 102** candidates, because
`country_obs` says `FEATHERS AND DOWN` where `consensus` says `Feathers`.

With that bridged: **22 of the 102 candidate rows close on the parent's
Tier-1.**

### A second limitation, found immediately — and it matters more than the first

`OIL | West Africa → Palm` dominates the closing list: **13 blocks across
seven volumes, both engines, every one at ratio 1.0000.** It is also
**already fixed** — `Oil — Palm` reads 1.00 in the payload for every one of
those years, because the existing machinery already admits those rows.

**The screen's arithmetic cannot tell "this block is misfiled" from "this
block was misfiled and is already repaired."** Both produce
`parent + phantom = Tier-1`. Ranking by that column alone sends you straight
to work that is already done. The column that would fix it is the parent's
**current payload ratio**, and until it exists every candidate must be checked
against the payload before being worked.

That is a general hazard for any screen built on the raw tables: `country_obs`
is the input to the repair pipeline, not its output, so a screen over it is
blind to every repair already applied.

### The real find: tin ore

`Tin — Ore Of` read **1895: 0.10, 1896: 0.11** — and those are exactly the two
volumes the screen flags. The heading `East Coast of Africa` had swallowed
everything but the first two or three origins.

Both close **at three levels, to the digit**:

| | as_1895 | as_1896 |
|---|---|---|
| foreign members (incl. the ones stranded under `Ore of`) | **4,553** = printed foreign TOTAL | **4,751** = printed foreign TOTAL |
| British members | **152** = printed British TOTAL | **121** = printed British TOTAL |
| grand | **4,705** = printed grand TOTAL | **4,872** = printed grand TOTAL |

Four `group_repairs` rows (both engines, both volumes). Result:

```
Tin — Ore Of  1895  ('under', 478, 4705) -> ('exact01', 4705, 4705)
Tin — Ore Of  1896  ('under', 535, 4872) -> ('exact01', 4872, 4872)
```

### Queued next, with its numbers

**`HIDES, Raw, and Pieces | East Coast of Africa` → `Dry`.** The payload reads
**1894: 0.62, 1895: 0.20, 1896: 0.16**, and the screen closes as_1894 (16 rows,
both engines) and as_1895 (32 rows). as_1896 (29 rows) does *not* close, so it
needs its own look — probably the same partial-swallow as the as_1896 feathers
block. Six repair rows if all three hold.

Also on the list and unchecked: `HEMP | … → Dressed or Undressed` (as_1893,
1 block) — note `Hemp` itself reads 0.00 for 1893-95, so there may be more
there than the one flagged block.
