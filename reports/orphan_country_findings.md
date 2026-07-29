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
