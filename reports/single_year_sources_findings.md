# The single-year blind spot: 17 commodity-years, from a bar that could never be met

Worked 2026-07-31 (`/loop /next-defect`).
**exact01 3,500 → 3,517 (+17), denominator unchanged at 9,518, zero
regressions. Every one of the 17 went `nodata` → `exact01`.**

## How it surfaced

The refreshed bracketed-gap screen put **`Wood And Timber — Mahogany` 1875,
£1.95M** at rank 5 — a hole created by my own merge two iterations ago. Its
countries turned out to be sitting in a node called **`Wood And Timber —
Staves : Mahogany`**: a sticky STAVES sub-label over the mahogany table,
holding **only 1875**, its nine countries summing to **80,705 = the mahogany
Tier-1 for 1875 exactly**. The country list settles it without the arithmetic —
Mexico 47,298, British Honduras 11,082, Central America 8,946, Hayti, the
Spanish West Indies: the Caribbean mahogany trade, which is not where staves
came from.

Then the question worth asking: **why did `match_orphan_countries` never find
this?**

## The blind spot

Its bar is **≥ 2 years agreeing to the digit**, and that bar exists for a good
reason — across ~900,000 candidate pairs a single agreeing year is expected to
occur by chance about 180 times. But it has a consequence nobody had written
down:

> **A source that carries only ONE year can never clear it, no matter how
> perfect the match.**

There are **483 single-year country-bearing nodes** in the payload. All of them
were structurally invisible to both arithmetic matchers.

## The discriminator that makes one year enough

Of those 483, **22 have exactly one host whose Tier-1 they match to the digit**
— which on its own is precisely the coincidence-grade evidence the bar was
built to reject. What separates the real ones is a **second, independent**
signal:

> **the article name IS the host commodity** (or a documented OCR garble of
> it).

`Cotton — Cinnamon` against `Spices — Cinnamon`. `Cards, Playing — Brandy`
against `Brandy`. `Manganese, One Of` against `Manganese, Ore Of` — the same
ONE/ORE garble already on record for iron and silver ore. Name evidence plus
exact arithmetic is decisive where either alone is not.

**16 accepted, 6 declined**, and all six declines are now in
`reference/match_declines.csv` so no future run re-adjudicates them.

## The sixteen

| £ | year | source | → host |
|---|---|---|---|
| 3,723,260 | 1872 | `Linen Yarn (Including Linen Yarn Waste)` | `Linen Yarn` |
| 2,770,341 | 1899 | `Cotton — Cinnamon` | `Spices — Cinnamon` |
| 2,734,094 | 1872 | `Pyrites Of Iron… — Quicksilver` | `Qui Silver` |
| 2,614,056 | 1882 | `Flax, Dressed Or Undressed — Unenumerated, Raw` | `Fruit — Unenumerated : Raw` |
| 2,465,122 | 1899 | `Cards, Playing — Brandy` | `Brandy` |
| 2,386,805 | 1882 | `Flax, Dressed Or Undressed — Apples, Raw` | `Fruit — Apples, Raw` |
| 1,502,294 | 1892 | `Ducts` | `Chemical Manufactures And Products, Unenumerated` |
| 415,706 | 1882 | `Bark — Dyes Obtained From Coal Tar (Aniline)` | `Dyes Obtained From Coal Tar` |
| 96,031 | 1889 | `Manganese, One Of` | `Manganese, Ore Of` |
| 75,826 | 1899 | `Cotton — Ginger` | `Spices — Ginger` |
| 36,860 | 1875 | `Wood And Timber — Staves : Unenumerated` | `…Furniture, Hardwoods, And Veneers : Unenumerated` |
| 15,964 | 1872 | `Feathers — For Bends` | `Feathers — For Beds` |
| 11,133 | 1893 | `Tobacco — Red, In Bottles : Sparkling : Burgundy` | `Sparkling, Red: Burgundy` |
| 7,808 | 1890 | `Dye Stuffs… — Cocchineal` | `Cochineal (Including Granilla And Dust)` |
| 2,390 | 1894 | `Animals, Living — Swords, Cutlasses, Bayonets` | `Arms : Swords, Cutlasses, Matchets, Bayonets` |
| 2,103 | 1881 | `Skins, Furs, And Pelts — Whalepins` | `Whalebone (Whalefins)` |

Three of these were already on the bracketed-gap ranked list under their host's
name — `Chemical Manufactures And Products, Unenumerated` 1892 (rank 8),
`Fruit — Unenumerated : Raw` 1882, and `Wood And Timber — Mahogany` 1875 — so
the queue was pointing at them all along without anything being able to say
where the data was.

`Ducts` deserves a note: it is not a commodity, it is the tail of **"Pro-|
ducts"** split across a line break, and it holds the whole 1892 origin table
for chemical manufactures.

## The six declines, and why they matter as much

| source | → host | why not |
|---|---|---|
| `Fish (Including Turtle) — Fresh (Not Of British Taking)…` | `Other Sorts Of Shell Fish` | no name relation |
| `Feathers And Down — Sardines` | `Other Sorts Of Shell Fish` | **same host as the row above** — two unrelated sources pointing at one host is a coincidence signature, not a defect signature |
| `Buttons And Strips, Not Of Metal — L Of All Sorts` | `Candles Of All Sorts` | "L Of All Sorts" *might* be a truncation; one year cannot decide |
| `Bones (Except Whalebone)…` | `Brass And Bronze Manufactures` | no relation whatever |
| `Bark — Cocaine` | `Cochineal (Including Granilla And Dust)` | **a plausible-looking garble is not a garble** — cocaine and cochineal are different commodities |
| `Cordage, Twine, And Cable Yarn — Unmanufactured` | `Cork — Unmanufactured` | `Unmanufactured` is a generic article shared by dozens of commodities |

Six of 22 is a 27% false-positive rate on single-year arithmetic alone —
close enough to the coincidence estimate to confirm that the ≥2-year bar was
right, and that the fix is a **second kind of evidence**, not a looser bar.

## What to do with the rest

The other 461 single-year sources match no host at all, so nothing here says
they are defective. The instrument to build, if this is worth revisiting, is
the same test with the name relation as a **precondition** rather than a
post-hoc filter — that would let the arithmetic bar drop to one year safely
instead of by hand.
