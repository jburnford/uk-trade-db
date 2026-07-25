# The oils — using geography to find misfiled origin tables (2026-07-25)

Palm oil closed against its own printed national total in **6 of 28 years**
when this started. It now closes in **25**, carries no quality flag, and
nothing was recovered from the source: every figure was already in the payload
under some other label.

The method that found the last of them is the user's, and it generalises to
the whole oils family.

## The geographic rule

The oils are unusually easy to attribute by origin, because each one comes
from somewhere distinct:

| oil | ships from | the tell |
|---|---|---|
| **Palm oil, palm kernels** | West Africa | Lagos, Niger Protectorate, Gold Coast, Fernando Po, Sierra Leone, Whydah, Bonny, Old Calabar, Congo, Portuguese Possessions in Western Africa |
| **Olive oil** | the Mediterranean | Italy, Spain, Portugal, France, Turkey, Greece, Tunis, Algeria, the Levant |
| **Coconut oil** | Ceylon, through most of the period | Ceylon; later also the Straits and the South Seas |

West Africa shipped palm oil and palm kernels and **essentially nothing else in
the oils**. So an oil-family origin row from a West African port is palm (or
kernels) — and if palm oil is short that year, it is palm oil's row. That is a
strong enough constraint to attribute a misfiled table on its own, and where
it can then be checked against the printed national total, it closes.

**Search recipe** (this is how the three 1872/1873/1880 labels were found):
scan every commodity in `exports/map_data.json` for origins matching the West
African vocabulary, restricted to the years the target commodity is short, and
sort by quantity. The misfiled tables stand out immediately.

## What that found for palm oil

Three labels, each closing on its own arithmetic:

```
'Nitre, Cubic (Nitrate Of Soda) — Palm'   1880   1,032,793  vs anchor 1,032,823
'Oil — West Coast Of Africa (Foreign)'    1873   1,013,186  vs anchor 1,017,947
'Oil — West Coast Of Africa'              1872     999,483  vs anchor 1,006,497
```

All three are the same defect in different clothes. The first is a nitrate
head glued to a palm article. The other two have a **place absorbed as the
article**, so an origin table for the West African coast became a commodity of
its own. Palm oil had *no* origins for 1880 and 6,994 and 4,761 cwt for 1872
and 1873.

Earlier in the same investigation, three other things were fixed:

1. **Unit-less origins.** 1874's Portuguese Possessions (878,548) and Sierra
   Leone (150,646) carry no printed unit, and the quantity axis counts only the
   dominant unit — so the map showed 0.02 of the anchor while the value sat
   there in full. The per-country heal is defeated here by a *real* collapse in
   one origin's trade (Portuguese West Africa ships 878,548 in 1874 and
   600–42,100 in the 1890s). The year's arithmetic settles it instead:
   `heal_by_anchor` moves a year's unit-less cells only when that brings the
   year closer to its printed total.
2. **The anchor under another label** — `Palm`, supplying 1877 and 1894–1900.
3. **The 1886–92 origins under `Oil`**, a de-headed label holding Lagos, the
   Niger Protectorate and the Gold Coast for exactly the seven years palm oil
   showed only European re-exports. 1888: 877,070 + the target's own 76,729 =
   953,799, the printed total to the digit.

## Where palm oil stands

```
1872-1899
1.00 0.98 0.99 1.86 0.25 0.98 0.54 0.99 0.99 0.99 1.06 0.99 0.99 1.00
0.99 1.07 1.00 1.00 1.00 1.00 1.00 1.01 1.03 1.06 1.01 1.00 1.00 1.00
```

## QUEUED — the three years still wrong

- **1875 reads 1.86.** An origin row carries the national total *exactly*
  (`West Coast Of Africa Foreign`, 904,562 against an anchor of 904,562) — a
  printed "Total" line parsed as a country. The impossible-origin filter cannot
  catch it because that filter only fires above 1.15×, and this sits at 1.00.
  **This is a general class worth a detector**: an origin whose quantity equals
  the year's whole national total is the total row, not an origin.
- **1876 reads 0.25 and 1878 reads 0.54.** Part of each year's table is
  somewhere else. Apply the search recipe above for those two years.
- **`Oil — West Africa` is deliberately NOT folded.** Its 1885 cells sum to
  873,363 against an anchor of 905,439, but 1885 already closes at 1.00, so it
  is a duplicate — and its `The Gold Coast (Including Lagos` row would collide
  with nothing and inflate the year.

## NEXT — the same method on the rest of the family

The geographic rule has not yet been applied to the other oils. Olive oil and
coconut oil both have era-split labels and unit-less cells of the same kind,
and the Mediterranean/Ceylon vocabularies should disambiguate them as cleanly
as West Africa did for palm. `Oil — Olive` currently reads `gapyears` with
1880, 1884 and 1885 blank; `Nuts And Kernels — Coco-Nut` and the coconut-oil
labels are worth the same treatment.
