# Matching de-headed anchors by arithmetic instead of by name

Worked 2026-07-29 (`/loop /next-defect` iteration 15).
`scripts/match_shadow_anchors.py` → `reports/shadow_anchor_matches.csv`.

**exact01 3,158 → 3,255 (+97), nodata 4,968 → 4,830 (−138).** The largest move
of the session by a wide margin.

## The problem the previous instrument could not touch

`deheaded_anchor_match.py` pairs an anchor-only label with its countries
**structurally** — the shadow's name must be the suffix of the counterpart's.
That works when the article is distinctive and fails completely when it is not:

- **334 anchor-only labels hold 2,682 commodity-years**
- only **24** have any structural counterpart at all
- and the generic names are ambiguous even then: `Unenumerated` is the suffix
  of **fifty-one** payload commodities, `Raw` of eleven, `Of Other Sorts` of six

So the name is the wrong evidence. **Two series that agree to the digit in
several independent years are the same line, and no name evidence is needed.**

## The method, and the guard that makes it admissible

For every (shadow, candidate) pair, count the years where the candidate's
country cells sum **exactly** to the shadow's printed national total.
330 shadows × 1,643 candidates ≈ **542,000 pairs scored**, so chance agreements
are a certainty, not a risk. The bar:

- **≥ 2 years agreeing to the digit** — not "close", exact
- each agreeing year carrying **≥ 1,000 units**, so zero and single-digit years
  cannot qualify
- the candidate must hold **no anchor of its own** in those years — if it does,
  the shadow duplicates it rather than completing it
- and a shadow is reported RESOLVED only when **exactly one** candidate clears
  the bar. Ties are printed as ambiguous and left alone.

That last rule is the one the `Tons. Cwts` decoder uses: **a closure reached by
search is evidence only when it is the only closure.** Result: **24 resolved,
2 ambiguous** out of 330 — the bar rejects the overwhelming majority, which is
what a bar is for.

## Nineteen folds

**First tranche — arithmetic alone, ≥4 exact years:**

| shadow | → candidate | evidence |
|---|---|---|
| `Cordage And Twine` | `Cordage, Twine, And Cable Yarn` | **13 years exact**, gains 21 |
| `Silver Ore` | `Silver, Ore Of, …` | **11 years exact**, gains 17 |
| `Manufactures, Unenumerated` | `Copper — Manufactures Of, Unenumerated, Including Copper Coin` | **10 years exact**, gains 11 |
| `Skins And Furs — Manufactures Of` | `Skins, Furs, And Pelts — Manufactures Of, Including Rugs` | 8 exact (1885-92, every year) |
| `House Frames, &c.` | `Wood And Timber — House Frames, Fittings, And Joiners' Work` | 6 exact, gains 10 |
| `Other Farinaceous Substances` | `Farinaceous Substances And Manufactures Thereof` | 4 exact |
| `Dried Or Preserved` | `Fruit — Plums, Dried Or Preserved` | 4 exact |
| `Soup, Transparent, …Spirit Has Been Used` | `Fruit — Transparent In The Manufacture Of Which Spirit Has Been Used` | 4 exact |
| `Shumash` | `Dye Stuffs… — Shumach` | 4 exact |
| `Manufactures, Piece Goods, Muslins` | `Cotton Manufactures — Muslins` | 4 exact |

Thirteen and eleven independent years agreeing to the digit is not a
coincidence anyone needs to argue about. **Copper manufactures 1875-1881,
1884, 1886 and 1887 all went straight to EXACT.**

**Second tranche — 2-3 exact years, taken only where the NAME corroborates:**
`Imitation Cheese`; `Old Broken, And Old Broken Steel` → `Iron — Old Broken,
And Old Cast Iron And Steel`; `Tobacco — Raw` → `Tobacco — Unmanufactured`;
`Figs And Fig Cuke` → `Fruit — Figs` (*Fig Cuke* is an OCR reading of *Fig
Cake*); `Mica And Tale` → `Mica And Talc` (*Tale* for *Talc*);
`Metals — Manufactures, Unenumerated` → the copper node; both `Bones …
Manufacturing Purposes` shadows → `Bones (Except Whalefins) — Applicable To
Manufacturing Purposes`.

And the demonstration case: **`Unenumerated` → `Leather, Undressed —
Unenumerated`.** That shadow is the suffix of fifty-one commodities, so no
structural rule could ever resolve it — the arithmetic picks exactly one.

## The denominator moved, and it should be reported

`reconcile_baseline`'s universe went **9,634 → 9,627 commodity-years (−7)**.
Tracing it: 84 Tier-1 cells left their shadow nodes and 77 arrived at targets.
The seven-cell difference is **genuine duplicate removal** — `Tobacco — Raw`
carried 16 anchor years into `Tobacco — Unmanufactured`, which already held
four of them; the two `Bones` shadows carried 15 between them into a target
that already held three. The same printed line had reached the payload twice.

That is a real (small) shrink, so the honest comparison is: on the **new**
denominator, the pre-iteration count of 3,158 would read 32.8% and the
post-iteration 3,255 reads **33.8%**. The +97 stands either way.

**No true regressions.** Every line in both payload diffs is a node key
appearing or disappearing; not one previously-good commodity-year got worse.

## What is left

- **Fourteen resolved shadows not taken** (2-3 exact years, no corroborating
  name), worth ~50 more measurable commodity-years. They want a look each
  rather than a batch — several point at targets that are themselves
  sticky-group artefacts (`Fish : Fresh, Herrings` → `China, Or Porcelain, And
  Earthenware — Fresh…`), where uniting anchor and countries inside an artefact
  node is arguably the wrong move.
- **Two ambiguous shadows**, both brass/bronze, where two or three candidates
  tie at 2 exact years.
- **~300 shadows still unmatched.** They cleared no candidate at the bar, which
  means either their countries genuinely are not in the payload, or they are
  several commodities' anchors merged into one node — the case the bar is
  designed to refuse. Lowering `MIN_EXACT` to 1 would sweep them in and would
  be indefensible.

Baseline 9,627 c-y: exact01 **3,255** (33.8%), within 5% **44.6%**,
GBP-weighted 50.8% / 67.7%.

---

## Update, iteration 16 — the seam is worked out

Re-running the matcher on the post-fold payload (the 19 folds changed the
candidate set, so the residual list had to be recomputed) leaves **5 resolved
shadows, not the 14 estimated** — most of the estimate was absorbed by folds
already applied.

**Two taken**, both clean:

- `Chicory And Coffee, Roasted Or Ground Mixed` → `Coffee And Chicory, Mixed`
  (3 exact years) — the same printed line with the ingredients named in the
  other order.
- `Dried` → `Fruit — Unenumerated, Dried` (2 exact, gains 8) — a bare `Dried`
  shadow that the arithmetic resolves out of the whole payload. It also rippled:
  the payload's era-fold pass then closed **`Yeast, Dried` 1887** (nodata →
  EXACT, 284,962 = 284,962), which nothing in this iteration targeted.

**Three deliberately not taken.** Their targets are themselves sticky-group
artefacts — `China, Or Porcelain, And Earthenware — Fresh (Not Of British
Taking) : Herrings`, `Horns, Tips And Pieces Of Horns And Hoofs — Manufactures
Of Iron Or Steel: Girders…`, `Flowers, Artificial — Nuts, Principally Used As
Fruit`. Uniting an anchor with its countries *inside* an artefact node makes
the artefact look substantiated, which is worse than leaving both halves
visibly broken. They want the group repair first.

Denominator 9,627 → **9,624** (−3), again genuine duplicate anchors.
exact01 3,255 → **3,260** from the folds, → **3,261** with the feathers decode.
