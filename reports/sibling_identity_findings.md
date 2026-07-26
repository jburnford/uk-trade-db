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

---

# Two of the queued items re-checked (2026-07-26)

## `Woollen Yarn` 1894–99 does not collapse — the instrument was reading the wrong labels

The queued item said the sub-sort origin tables "collapse" after 1894, summing
to 21,024–1,328,595 lb against national totals of 16–20 million. **That is an
artifact of the labels the identity was computed on, not a defect in the data.**

The abstract re-words all three sub-sorts in the 1890s, and the country tables
follow. `For Weaving` becomes `For Weaving, Mixed or not with Silk` in 1894;
`For Fancy purposes` becomes `For Fancy Purposes, including Berlin Wool and
Zephyr Yarn` in 1893. Each new wording is a **separate payload commodity**, so
the identity — built on the pre-1894 names — was summing labels that had gone
quiet while the trade carried on next door.

Recomputed on era-correct labels:

```
yr     weaving      fancy    unenum        sum      parent-anchor   ratio
1882  12,731,339    938,819    93,898   13,764,056   13,764,056    1.0000  EXACT
1886  18,620,957  1,420,393    40,619   20,081,969   20,081,969    1.0000  EXACT
1887  16,088,197  1,188,556    37,066   17,313,819   17,313,819    1.0000  EXACT
1895  18,298,736  1,220,214    54,612   19,573,562        —
1899  20,619,078  1,036,268    36,890   21,692,236        —
```

The identity in fact holds **1882–1892** — wider than the 1883–89 previously
claimed — with 1882, 1886 and 1887 exact to the digit and the rest within 30 to
11,090 lb on totals of 13–20 million. And 1895–99 sum to 17.4–21.7M lb, exactly
the range the national totals occupy. Nothing collapsed.

**`sibling_identity.py` has a real gap: it does not know that a printed line can
change its wording mid-series.** It builds families from label text, so an era
re-wording silently truncates a child's span and the cross test then reports a
shortfall that is not there. Any family whose sub-sort names change between
1872 and 1899 is exposed to this. That is the fix worth making before the tool's
output is trusted further.

## The real defect underneath: the fancy line is counted twice where the wordings overlap

The two fancy wordings **both** carry origins in 1893, 1894 and 1896:

```
1893   For Fancy Purposes  1,320,619   |  …including Berlin Wool  1,320,619   identical
1894                       1,217,385   |                          1,219,151
1896                       1,267,323   |                          1,265,393
```

1893 is digit-identical — one printed table read twice under two names. Counting
it once brings the identity to **1.0006 in 1893** (15,530,897 against 15,521,638)
and **1.0003 in 1894** (16,286,990 against 16,281,974), from 1.0857 and 1.0751.

**Not folded.** The fold itself is routine, but the anchors have scattered across
the same era labels — the parent's anchor stops at 1894, `For Weaving` carries
one for 1896–1900, and a fourth label `Woollen Yarn, For Fancy Purposes,
Including Berlin } Lbs` carries 1895–99 with no origins at all — so a fold has to
decide which label holds the Tier-1 series as well as the origins. That is the
same era-semantics question that made sugar expensive, and it wants a decision
rather than a guess.

## Lead found in passing: a stale `WOOLLEN YARN` group head, 1893–99

`Woollen Yarn — Stuffs` (**GBP52.1M**) and `Woollen Yarn — Cloths` (GBP5.2M) are
Woollen *Manufactures* articles, not yarn. `WOOLLEN MANUFACTURES|Stuffs` and
`|Cloths` both run to 1896 and stop; the WOOLLEN YARN-headed copies run 1893–99.
`Woollen Yarn — Goods, Being Either In Part Or Wholly Manufactured` (1893–94) and
`— From British North America` (1894) are under the same head. Seq ranges not
checked and no printed total tested — this is a lead, not an adjudication.

## Correction to this report's copper entry

The queued note above says `Copper — Regulus` "loses its origin table after 1881"
and that the family "cannot be tested at all for eighteen years". **Both are
wrong**, and for the same reason as woollen yarn: the article is re-worded to
`Regulus and Precipitate` in 1882 and lands under a headless payload label. The
identity is testable throughout and closes exactly in 1887 and 1889. See
`reports/copper_findings.md`. The 1888 anchor is fixed.
