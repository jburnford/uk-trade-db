# The other direction: orphan country tables

Worked 2026-07-29 (`/loop /next-defect` iteration 17).
`scripts/match_orphan_countries.py` → `reports/orphan_country_matches.csv`.

**exact01 3,261 → 3,309 (+48), nodata 4,815 → 4,756, within 5% 44.7% → 45.3%,
GBP within 0.1% 50.8% → 51.1%. Zero true regressions.**

## How it was found

The iteration began by refreshing the standing bracketed-gap ranking, which was
badly stale (+132 exact and −153 nodata since it was last generated). The
refreshed list was **led by items my own folds had just made visible** — the
campaign working as designed. `Silver, Ore Of…` appeared four times for £8.5M,
because iteration 15's fold had given it an anchor to be measured against.

Working it turned up something more useful than the commodity. Silver ore
closes **1.0000 in fifteen of its twenty-one anchored years**, and every broken
year — 1876, 1879, 1883, 1888 — was the same thing: the origin table sitting in
a *separate payload node that holds countries and no total*, while the total
sits in the main commodity.

| broken year | where the table actually was |
|---|---|
| 1876, 1879 | `Silk Manufactures — Silver **ONE**, Or **ONE** Of Which…` — ORE misread as ONE, under a stale SILK MANUFACTURES head |
| 1883 | `Cotton — Silver Ore, Or Ore The Greater Part Of Which…` |
| 1888 | `Silver Ore, Or Ore Of Which The Greater Part Is Silver` — the same name, shorter wording |

Three folds: **1876 (499,775 = T1 exactly), 1883 (1,031,548 vs 1,030,542) and
1888 (1,495,972 = T1 exactly)** all nodata → EXACT.

## The instrument gap

`match_shadow_anchors.py` scans **one direction only**: a label holding a
national total and no countries, looking for the commodity holding the
countries. Silver ore is the **mirror** — countries and no total, with the
total in the main commodity. Both are produced by the same defect (a stale or
misread group heading splitting one printed line in two), but **which half
keeps the anchor depends on where the heading was lost**, so a one-way scanner
misses about half the population.

Scanning the other way: **1,189 country-only orphans against 755
anchor-holding hosts**, ~900,000 pairs, same evidence bar as the forward scan
(≥2 years agreeing to the digit, each ≥1,000, the host holding no country data
in those years, exactly one host clearing the bar). **21 resolved, 2
ambiguous.**

Six taken:

| orphan | → host | evidence |
|---|---|---|
| `Coffee — Manufactured` | `Cork — Manufactured` | **15 years exact**, gains 20 |
| `Lace, And Articles Thereof` | `Lace` | 7 exact, gains 10 |
| `Beer And Ale — Raw Or Kiln Dried` | `Chicory, Raw Or Kiln-Dried` | 7 exact, gains 7 |
| `Flowers, Artificial — Raw, Not Otherwise Described` | `Fruit — Unenumerated : Raw` | 6 exact, gains 10 |
| `Fruit — Plums (French) And Prunelles` | `Plums, French, And Pruneloes` | 3 exact |
| `Bark — Sumach` | `Sumach` | 3 exact |

The first is the clearest picture of the defect: fifteen years of manufactured
cork origins had been sitting under a stale **COFFEE** group head, agreeing to
the digit with cork's national total every one of those years.

## The caution, learned by causing it

**The arithmetic vouches only for the years it matched, but a fold brings the
whole source unless it is year-scoped.** Folding `Bark — Sumach` into `Sumach`
unscoped carried a 1893 cell (12,036) into a target that already held a
*better* 1893 reading (11,515, closing exactly on its own anchor), and pushed
that year from exact01 to within5 — the single true regression in the
iteration. Scoped to `1889;1895;1896;1898`, the years the host actually lacks,
it gains four years and costs nothing.

The script now emits a **`safe_scope`** column for exactly this: the years the
host has no data in. Use it as the fold's year scope by default.

(Two mechanical notes from the same repair. Editing a CRLF reference CSV by
byte offset dropped a field separator and silently produced `years=None`, which
`csv.DictReader` reports as a short row rather than an error — check the parsed
value, not the file. And the regression only became visible because the diff
was re-run against the iteration's *starting* payload rather than the previous
step's.)

## What is left in this direction

**15 resolved orphans still unfolded** after this pass, all at 2 exact years,
worth ~45 commodity-years — including several whose host is itself a
sticky-group artefact (`Cards, Playing — Transparent…` → `Soap, Transparent…`,
`Quicksilver, (Metallic) — Woollen…` → `Rags, Woollen…`), where the pairing is
arithmetically sound but both names are damaged and the group repair should
come first. Two ambiguous.

And silver ore's own remaining defects: **1879 at 0.987** (the fold's 1879
cells sum 715,215 against 724,515), **1884 at 1.101** (over — a duplicate
admission), and **1894 at 0.306**, whose missing three-quarters is not in any
of the nodes examined here.

---

## Update, iteration 19 — the agreement bar was a hair too strict

Refreshing all three instruments on the post-fold payload left the matchers
looking exhausted: 2 resolved shadows, 6 resolved orphans. Then the refreshed
bracketed-gap screen put a **£9.7M six-year hole** at rank 3 —
`Farinaceous Substances And Manufactures Thereof`, 1882-1887 — that neither
matcher had reported.

**It was the rounding.** Both matchers counted a year as agreeing only on digit
equality, `round(a) == round(b)`. Farinaceous 1885 reads **802,967 against a
printed 802,970** — three pounds in eight hundred thousand, **0.0004%** — so
that year did not count, the pairing dropped to one agreeing year, and a
six-year hole stayed invisible.

Agreement is now `|diff| <= max(1, TOL × anchor)` with **TOL = 0.0002**. The
coincidence guard still holds comfortably: a random pair agrees in one year
about once in 5,000 and in **two independent years about once in 25 million**;
across ~900,000 pairs that is well under one expected false positive.

Effect of the retune alone: **orphan matches 6 → 15 resolved, shadow matches
2 → 8.**

## Sixteen folds

The farinaceous family is the clearest instance of the underlying defect yet
seen: **the same printed wording split by where the OCR broke the hyphen** —
`Manufac- Tures`, `Manu- Factures`, `Manufacturesthereof` — each variant
becoming its own payload commodity holding a few years' countries and no
anchor, while the anchor sat in the properly-spelled node with those years
empty. Three folds recover it:

| year | after | |
|---|---|---|
| 1883 | 785,998 = 785,998 | EXACT |
| 1884 | 778,899 vs 783,407 | 0.9942 |
| 1885 | 802,967 vs 802,970 | EXACT |
| 1886 | 809,855 = 809,855 | EXACT |
| 1887 | 867,296 vs 867,291 | EXACT |

Others worth naming: `Copper, Ore Of — Opium` → `Opium` (a stale COPPER head
over the opium tables); three separate stale heads over the same gin line
(`Cards, Playing — Geneva`, `Fruit — Geneva`, and **`Spirits — Genève`**, an
accent variant) all folding into `Spirits — Geneva`; `China, Or Porcelain, And
Earthenware — Meal…` → `Meal, Unenumerated`; `Woollen Yarn — Stuffs` →
`Woollen Manufactures — Stuffs`.

**Two skipped on a signal worth recording.** `Brass, Bronze, And Metal Bronzed
Or Lacquered…` and `Of Wool… : Cloths` each appeared in **both** matchers'
output, in opposite roles — each claiming to be the anchor-holder for the
other. That can only mean both nodes hold anchors *and* countries in different
years, which is a different defect from the one these folds address. Left
alone. **A pair appearing in both directions is a warning, not a
confirmation.**

Baseline 9,610 c-y (−14, duplicate anchors again): exact01 3,334 → **3,366**
(35.0%), within 5% 45.6% → **46.1%**, GBP within 0.1% **51.4%**, within 5%
**68.2%**. Zero true regressions.

---

## Update, iteration 26 — six folds, and folds cascade

Six taken, all unscoped per the iteration-24 rule:

| source | → host | evidence |
|---|---|---|
| `Nuts And Kernels — Other Sorts, Unenumerated (Not Fruit)` | `… (Not Used As Fruit)` | 3 exact |
| `Boots And Shoes` | `Leather Manufactures — Boots And Shoes` | 2 exact |
| `Feathers And Down — For Beds` | `Feathers — For Beds` | 2 exact |
| `Linen And Cotton Rags` | `Rags And Other Materials For Making Paper — Linen And Cotton` | 2 exact |
| `Nuts And Kernels — Other Sorts, Unenumerated (Not Used As Fruit)` | `Nuts And Kernels — Of Other Sorts` | 3 exact |
| `Silk Manufactures — Of Countries Out Of Europe` | `Manufactures — Of Countries Out Of Europe` | 2 exact |

The boots pair is worth noting: `reports/bracketed_gap_findings.md` has carried
*"Boots 1886: anchor sits under the `Leather Manufactures` label-key split …
a headless-vs-headed era pair the fold pass cannot see"* since the campaign
began. **The arithmetic matcher sees it.**

**FOLDS CASCADE — and this is the reusable finding.** The first Nuts And
Kernels fold merged `(Not Fruit)` into `(Not Used As Fruit)`; the enlarged node
then matched a **third** wording of the same line, `Nuts And Kernels — Of Other
Sorts`, which had not been reported before the fold. So **re-run the matcher
within an iteration, not only between iterations** — each merge can expose the
next link in a chain.

exact01 3,472 → **3,483**, nodata 4,490 → **4,448**, within 5% 47.6% →
**47.9%**, GBP 51.6% → **51.7%** / 68.4% → **68.5%**. Denominator 9,553 →
9,524 (−29, duplicate anchors). Zero true regressions.

Nine resolved matches remain, all previously reasoned about and declined:
generic hosts (`Gum — Unenumerated` → `Of Other Sorts`), wrong direction
(`Wood And Timber — Mahogany`), the bidirectional brass warning, the copper
pair that breaks `fold_era_wordings`, and four whose host is a sticky-group
artefact or whose pairing is semantically implausible (`Seeds — Rape` →
`Hemp`).
