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

---

## Hides: three years off the same screen

**exact01 3,498 → 3,499, within5 1,082 → 1,084, denominator unchanged at
9,518, zero regressions.**

`HIDES, Raw, and Pieces thereof | East Coast of Africa` (hyphenated
`East-Coast` in as_1896) sits between the `Dry` block and the `Wet` block in
all three volumes — it is the tail of the Dry table, and the payload read
**1894: 0.62, 1895: 0.20, 1896: 0.16**.

| year | proof | before → after |
|---|---|---|
| 1894 | foreign members left under `Dry` sum **112,912 = the printed foreign TOTAL to the digit**; all members **419,210** against a printed grand **419,205** | under 258,363 → **exact01 419,210** |
| 1895 | the heading swallowed the **tail of the foreign section as well** — foreign across both labels **139,877 = the printed foreign TOTAL exactly**; all members 491,544 vs printed 491,547 | under 100,232 → **within5 (0.19%)** |
| 1896 | relabel structurally certain, **but the year does not close** | under 59,028 → **within5 (0.81%)** |

### as_1896 is admitted as an honest partial, and here is why

Its printed subtotals **do not agree with each other**: foreign 115,102 +
British 250,961 = 366,063, but the printed grand says **369,063**. The members
give foreign 118,102, British 247,961, grand 366,063. So a single 3,000
discrepancy sits somewhere in the printed column, with no third source to
arbitrate it.

The relabel is still right — those rows are plainly the continuation of the
Dry table and moving them invents nothing — so the year is admitted at 0.81%
rather than held back. **Moving rows to their correct label is a different act
from guessing a digit**, and only the second is forbidden. Recorded so the
0.81% is not later mistaken for a repair that failed.

### Note on the 1895 arithmetic

My hand computation said 491,544 and the payload sums 490,632. The difference
is the payload's own de-duplication of two `British Possessions in South
Africa` rows in that block — the repair is unaffected, but it is worth
recording that **hand sums over `country_obs` and payload sums will not always
agree**, because the payload has passed through de-dup and the raw table has
not. Same lesson as the screen's blindness to repairs already applied, from
the other side.

---

## The payload-ratio column, and the closing seam is exhausted

**No data change; baseline unchanged at exact01 3,499 / 9,518.**

Two columns added, `payload_now` and `live`, and the list re-sorted by them.
`live` means *closes on the parent Tier-1 **and** the payload demonstrably
still falls short*.

| | |
|---|---|
| candidates | 102 |
| closing on the parent Tier-1 | 22 |
| **live** | **0** |

All 22 are already repaired: 13 are `OIL | West Africa → Palm`, which was fixed
long before this screen existed, 4 are the tin blocks and 6 the hides blocks
taken off this screen in the last two iterations. **The closing seam is
exhausted.**

### One false positive, and it was mine

The first cut of the `live` rule treated a *missing* payload ratio as live,
which surfaced exactly one candidate: `HEMP | Australia → Dressed or
Undressed` (as_1893). Its arithmetic is impeccable — foreign members 69,224 =
the printed foreign TOTAL, British members including the phantom's New Zealand
1,537 and Other British Possessions 5 = 9,109 = the printed British TOTAL, and
69,224 + 9,109 = 78,333 = the printed grand TOTAL, all to the digit — and it is
**Chandra-only**, Infinity having parsed the block whole.

I wrote the repair. It admitted nothing:

```
as_1893 HEMP|Australia  selected 4  admitted 0
                        drop_subtotal 2  drop_consensus_holds_triple 2
```

`country_year_final` already holds `HEMP | Dressed or Undressed | new zealand
1,537` with `source = consensus`. **The upstream vote was already filing those
rows correctly**; the repair was redundant and has been backed out rather than
left as inert clutter.

The reason the payload ratio was missing is the reason the metric would never
have shown it either: the hemp family is fragmented across **thirty-plus**
payload nodes and `Hemp — Dressed Or Undressed` carries no Tier-1 at all. So
the rule is now: **absence of a payload ratio is not evidence that work is
undone.** Usually it means the parent has no Tier-1 in the payload, and a
repair there would be invisible whether or not it was needed.

### Where the remaining value is

**Not in the closing column.** 80 of the 102 candidates do *not* close, and
that is exactly what a **partial swallow** looks like — the as_1896 hides block
and the as_1896 feathers block both took part of a table rather than a clean
section, and neither would satisfy `parent + phantom == Tier-1`. Those need a
different test: the phantom's own printed subtotal against the *section* it
completes, rather than the parent's grand Tier-1.

That is the next instrument, and it is where the rest of this defect class
lives.

---

## The section-subtotal test, and the class is now essentially clean

**exact01 3,499 → 3,500, denominator unchanged at 9,518, zero regressions.**

### The test that should have been first

Concatenate the parent block and the phantom block in row order and walk them:
**every printed TOTAL should equal either the members since the previous TOTAL
(a section subtotal) or the members from the start (the grand total).**

This is the evidence every hand adjudication in this class already used —
feathers, tin, hides — and it has one decisive property the Tier-1 column
lacks: **it needs no anchor**, so it still works on a **partial swallow**,
where the phantom took only part of a table and `parent + phantom` therefore
does *not* equal Tier-1.

| test | blocks proven |
|---|---|
| parent + phantom == Tier-1 | 22 |
| **every printed subtotal reconciles** | **34** |

The extra 12 are exactly the partial swallows — including `as_1896 FEATHERS AND
DOWN | East Coast of Africa`, which the Tier-1 column never flagged and which
I had to find by hand two iterations ago.

### What it found: one repair, and then the bottom of the seam

Of 102 candidates, **only two** had a parent the payload still reads short.

**`SPICES | East Coast of Africa` → `Pepper`, as_1894** — the payload read
**0.05**. Three-level closure to the digit: foreign members **966,640** = the
printed foreign TOTAL; Sierra Leone 331,856 and Niger Protectorate 288,040 left
under `Pepper` plus the phantom's Zanzibar, Bombay, Madras, Straits, Other BEI
and Other BP = **28,246,364** = the printed British East Indies subtotal;
966,640 + 28,246,364 = **29,213,004** = the printed grand TOTAL.

```
Spices — Pepper  1894  ('under', 1586536, 29213004) -> ('exact01', 29213004, 29213004)
```

**`IVORY | West Africa` + `East Africa` → `Teeth, Elephants'…`, as_1888** —
payload 0.00, and **it does not close**. Two phantoms in a row here, not one:
`West Africa` (2 rows) then `East Africa` (5 rows). All members together give
**5,708** against a printed TOTAL of **5,648** — off by 60, about 1%. The
relabel is probably right and one member is misread, but there is a single
printed total and nothing to arbitrate against. **Queued, not applied.**

### The class is worked out

- **34 blocks** have every printed subtotal reconciling; **all but the pepper
  one were already repaired** in the payload.
- **50 of the 102 candidates have no payload ratio at all** — their parent
  carries no Tier-1, so nothing about them is measurable in either direction.
- **2 had a real shortfall**; one is now exact, one is queued with its numbers.

So the phantom-region-article seam has given up what it has: tin (2 years),
hides (3 years), pepper (1 year), on top of the two feathers blocks found by
hand that started it. The instrument stays, and it is now the right shape —
**section proof first, Tier-1 closure second, payload ratio as the liveness
filter** — for re-running after any future parse change.
