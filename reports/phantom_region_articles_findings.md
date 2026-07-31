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
