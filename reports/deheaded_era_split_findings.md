# The de-headed anchor has a third kind, and it was the blind spot

Worked 2026-07-29 (`/loop /next-defect` iteration 14).

## Why this iteration exists

Three consecutive iterations produced real corrections the baseline could not
see — drugs unenumerated (8), ornamental feathers (12), metal wrought (13) —
and every time the blocker was the same: **the commodity's Tier-1 anchor sits
in one payload node and its countries in another**, so the corrected data has
nothing to be measured against. Rather than correct a fourth invisible thing,
this iteration went after the visibility.

## The instrument had two kinds; the interesting case is a third

`scripts/deheaded_anchor_match.py` finds abstract rows that lost their group
head and became their own anchor-only commodity. It classified every match two
ways:

- **REUNION** — the counterpart has no anchor. Two halves of one line.
- **DUPLICATE** — the counterpart has its own anchor, so the shadow is a
  phantom publishing a total it cannot substantiate.

The test for "duplicate" was merely *does the counterpart have an anchor*. That
put all three of this session's cases in the wrong bucket, because there is a
third shape:

> **ERA-SPLIT** — the counterpart has an anchor, but the two anchors are
> **disjoint in years**. The shadow is not a duplicate of the counterpart's
> series; it is its later (or earlier) era, de-headed partway through. Folding
> **completes** a series rather than removing a phantom — and it is the only
> one of the three kinds that adds measured years *and* leaves
> `reconcile_baseline`'s denominator alone.

One line of classification (`anchor_overlap = set(shadow_t1) & set(cand_t1)`)
splits the old DUPLICATE bucket 41 → **7 era-split + 34 duplicate**.

## Four folds, fourteen commodity-years

| shadow | → counterpart | result |
|---|---|---|
| `Wheat` | `Corn And Grain — Wheat` | **1892-1896 all five EXACT** |
| `Pepper` | `Spices — Pepper` | 1892, 1893, 1895, 1896 EXACT; 1894 under |
| `Rum` | `Spirits — Rum` | 1892, 1893, 1894 EXACT; 1895/97 within5; 1896 under |
| `Swine` | `Animals, Living — Swine` | 1896 (4 = 4) and 1898 (450 = 450) EXACT |

**exact01 3,144 → 3,158 (+14).** Zero regressions: every changed row in the
payload diff is a shadow key disappearing or a counterpart key appearing — not
one previously-good commodity-year got worse.

`Wheat` is worth singling out. It is the corpus's largest commodity (£663M) and
its 1892-1900 anchors were sitting in a bare `Wheat` node, all nine years in
`nodata`, while `Corn And Grain — Wheat` held every country row. Five of them
now close **to the digit** — 1892 at 64,901,799 = 64,901,799.

**A note on the dry run.** Computing the fold by hand beforehand predicted
1.03-1.05 for four of the wheat years; the actual fold produced exact. The
merge is not a simple sum — cells merge by (country, unit, year) with the
target winning, and the payload's later passes then re-run on the merged node
(`aggregate-beside-members` went 875 → 885). **Predict the direction, but
measure the result.**

## Two honest caveats

1. **GBP-weighted `within 0.1%` moved 51.0% → 50.8% while the count went up.**
   The GBP weighting spreads each commodity's total value uniformly across its
   Tier-1 years, so merging two nodes redistributes weight across a different
   year count. The unweighted count is the unambiguous measure here; the
   GBP figure is doing something the fold did not.
2. **The pepper fold exposes a duplicate-admission defect rather than causing
   one.** Before the fold my dry run showed 1892 at 1.947 and 1895 at 1.979 —
   almost exactly double. After the fold both read EXACT, because the merge
   deduplicated them. That is the right outcome, but it means a duplicate
   *was* there, and the same shape may sit under other commodities. 1894 is
   left at 0.054 — a genuine shortfall now visible for the first time.

## What is left in this class

- **334 anchor-only labels holding 2,682 commodity-years**, of which only 24
  have a structural counterpart. The rest are blocked by **generic shadow
  names**: `Unenumerated` alone matches 51 candidates, `Raw` 11, `Of Other
  Sorts` 6. A name that generic cannot be resolved structurally — those
  shadows are probably several commodities' anchors merged into one node, and
  splitting them needs the arithmetic, not the name.
- **Three era-split rows not taken**, each blocked by a defect underneath:
  - `Ornamental` + `Feathers And Down — Ornamental` — blocked by the fused
    `Lbs. ozs` quantity (iteration 12); folding now would publish 1892 at 48.8.
  - `Wrought Or Manufactured` + `Metal — Wrought Or Manufactured` — blocked by
    the host node being a two-commodity chimera. `reconcile_baseline` takes the
    **modal** T1 unit, and the host's Cwt series (14 years, the iron shadow)
    outnumbers the Ton series (6), so folding changes nothing until the node is
    split by unit.
  - `Horses` + `Animals, Living — Horses` — gains no years.
- **34 true duplicates** holding ~232 commodity-years. Folding them all would
  *shrink the denominator* and raise every percentage without a single number
  improving — the tool prints that separately for exactly this reason, and it
  should be reported as a denominator change if ever done.

Baseline 9,634 c-y: exact01 3,144 → **3,158** (32.6% → **32.8%**), within 5%
43.3% → **43.4%**, nodata 4,986 → 4,968.
