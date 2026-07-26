# The sibling identity, run as a pass (2026-07-26)

Three sessions in a row found defects the same way: the volumes print a parent
line *and* its sub-sorts, and the sub-sorts constrain each other whether or not
any of them carries an anchor of its own. Eleven wrong years in sugar 1882–99,
twenty-three destroyed ham origin tables, four missing cow tables — every one of
them inside years the quality flags called `noanchor` and every other test in
this project skipped.

`scripts/sibling_identity.py` makes that a pass instead of a habit.

## Finding identities without fitting them

The standing guardrail is that a subset-sum reached by trying combinations is a
coincidence, not a proof. So candidate families are read off the **printed
labels** and arithmetic is only ever allowed to confirm or refute them:

| rule | how a family is proposed | proposed | confirmed |
|---|---|---|---|
| `TOTAL` | the parent's label says so — `… Total`, `… of all kinds` | 7 | 1 |
| `UNION` | the parent's name **is** its children's, concatenated | 119 | 5 |
| `HEAD` | the group head is itself a commodity (`Glass` beside `Glass — …`) | 52 | 0 as named |
| `SEARCH` | bounded subsets of a `TOTAL`/`HEAD` parent's siblings | 1,999 | 3 |

A family is confirmed only if the identity closes **within 0.1% in at least two
years** — three for `SEARCH`, which is the only rule that looks at combinations
and is additionally capped at eight candidate siblings and one surviving family
per parent. Everything else is discarded unreported: a family that never closes
was never an identity.

`UNION` is the rule that pays. It is a very tight constraint on names — the
children's vocabularies must be pairwise disjoint and cover the parent's exactly
— and it is what catches `Bacon and Hams` = `Bacon` + `Hams` and
`Oxen, Bulls, Cows, and Calves` = `Oxen and Bulls` + `Cows` + `Calves` without
being told. `HEAD` confirmed nothing as a named set, because a head with nine
sub-sorts almost never has all nine printing an origin table in the same year;
it earns its place by supplying parents to `SEARCH`, which is how `Glass` and
`Woollen Yarn` were found.

## What it confirmed

Nine identities, 167 family-year tests. **114 of those 167 are the cross test —
the children's origin tables against the parent's printed national total — which
is available to families where no sub-sort has an anchor at all.** That is
exactly the population `reconcile_baseline.py` cannot score.

| GBP | identity | closes |
|---|---|---|
| 615.7M | `Sugar — Unrefined, Total` = cane + beetroot | anchor 4/4 |
| 448.9M | `Sugar — Refined : Total Of` = lumps and loaves + other sorts incl. candy | anchor 4/4, origin 14/18 |
| 351.2M | `Bacon And Hams` = `Bacon` + `Hams` | anchor 4/4, cross 16/24 |
| 212.9M | `Animals, Living — Bulls, Oxen, Cows, And Calves` = oxen and bulls + cows + calves | anchor 3/3, cross 18/24 |
| 51.0M | `Fruit — Oranges And Lemons` = oranges + lemons | anchor 2/2 |
| 49.4M | `Glass` = flint + plate + window + manufactures unenumerated | cross 3 |
| 41.4M | `Woollen Yarn` = for fancy purposes + for weaving + unenumerated | cross 9 |
| 37.3M | `Copper, Ore And Regulus` = `Copper, Ore Of` + `Copper — Regulus` | cross 3 |
| 22.5M | `Cutch And Gambier` = `Cotton Manufactures — Cutch` + `Gambier` | cross 3 |

The four largest reproduce, from the labels alone, what three sessions found by
hand. The bottom five are new, and four of them are checked **only** by the
cross test.

`Woollen Yarn` is the clearest new case. Its three sub-sorts have no anchor
between them, and their origin tables — three genuinely separate country lists,
Belgium and France for weaving, Germany for fancy purposes — sum to the printed
`Woollen Yarn` national total **to the digit in 1883–89** and within 1.3% in
1873–82. Twenty years of origin data validated where nothing had ever been
checked.

`Cutch And Gambier` does something else useful: the identity only closes if
`Cotton Manufactures — Cutch` is counted, which confirms that label is the cutch
line under a stale group head. That is a curation lead arrived at by arithmetic.

## Telling the two failure modes apart

A family whose children overshoot the parent's printed total looks identical to
a family that is double-counting a drill-down, so each row carries both sides'
own closure (`parent_ratio`, `children_ratio`) beside the identity. Sugar
unrefined 1895 is the second kind — the children read 1.4430 of the parent's
anchor, but the **parent's own origin table reads 1.3596 of the same anchor**, so
the whole family is over-counting and the identity has found nothing new (that
class is `detect_origin_overcount.py`'s, and the map de-duplicates it). Woollen
yarn 1874 is the first kind and is a real shortfall.

The source of truth is `exports/viz_payload.json`, the same pre-de-duplication
view `reconcile_baseline.py` scores — deliberately not the map's de-duplicated
`map_slim.json`, so the two metrics stay comparable.

## Queued, with the evidence

**`Copper, Ore And Regulus` 1888 has an anchor twenty times its series.**
3,562,071 tons against 250,567 in 1889 and 169,511 in 1887. The identity cannot
test the year — only one child has an origin table after 1881 — but the anchor is
plainly wrong and nothing else reports it.

**`Copper — Regulus` loses its origin table after 1881.** From 1882 to 1899 only
`Copper, Ore Of` has one, so a family that closed at 1.0000 in 1874, 1877 and
1879 cannot be tested at all for eighteen years.

**`Woollen Yarn` 1894–99: the sub-sort origin tables collapse.** They sum to
21,024–1,328,595 lb against national totals of 16–20 million. Before 1894 they
close to the digit. Something takes the origin tables out of the payload at
exactly the point the abstract splits the line into its 1890s wordings
(`Woollen Yarn, For Fancy purposes, including Berlin Wool and Zephyr Yarn`).

**`Glass` and `Copper` both run 0.94–0.99 in their early years** — small, steady
shortfalls of the kind a single missing origin row produces, in years with no
other check.

## The honest limit

Nine families is not many. The reason is structural rather than a defect in the
rules: the payload carries only **50 commodities with a total-ish label** and
**52 bare group heads that are themselves commodities**, and `UNION` needs the
children's names to partition the parent's exactly. Most of the corpus's printed
sub-sort structure was flattened long before the payload — by era-label folds, by
stale group heads, and by the signature collisions this session spent its day on.
Recovering more identities means recovering more taxonomy first; the instrument
will pick them up as that happens, which is the argument for re-running it after
every curation batch.
