# Import tables parsed under the wrong flow

Worked 2026-07-29 (`/loop /next-defect` iteration 22).
`scripts/detect_flow_misfile.py` → `reports/flow_misfile_candidates.csv`.

## Why

`parse_country` takes each block's flow from the page heading. When that
heading is lost or OCR-mangled the block keeps the previous section's flow, so
an **import origin table lands under `export_uk` or `reexport` and never
reaches the import side at all**. Two had been found by hand, both in
`as_1892` — the `ZINC'd)` block (iteration 10) and `WOOD and TIMBER | Mahogany`
(iteration 21). Two in one volume is a pattern, not a coincidence.

## The screen

For every non-import block, compare its own printed grand TOTAL against the
**import** Tier-1 for the same commodity-year. Export and import tables of one
commodity are often the same order of magnitude, so two guards:

- the import commodity-year must currently be **empty or short** — a match
  against a year that already closes is a coincidence by construction;
- agreement within 0.05% of the anchor.

Everything surviving still needs hand adjudication, and **the decisive evidence
is the country list**: an export table names destinations, an import table
names sources.

## Result: two candidates corpus-wide, both real, both in `as_1892`

**`WOOL | Alpaca, Vicuña, and Llama` 1892.** Germany 191,616 + France 6,160 +
**Peru 4,059,246** + **Chile 537,879** = **4,794,901 = the import Tier-1 to the
digit**, against a commodity-year reading 0.0000. The country list settles it
without the arithmetic: alpaca, vicuña and llama wool comes from Peru and
Chile, which supply 96% of the block. Britain was not exporting Andean wool to
the Andes. **nodata → EXACT.**

**`WOOD and TIMBER | Staves` 1892.** Foreign members 41,725 + 17,067 + 25,238 +
23,551 + 1,049 + 1,158 + 575 + 22,761 + 67 = **133,191 = the printed foreign
TOTAL**, + Canada 2,872 = **136,063 = the import Tier-1 to the digit**. Country
list: Russia, Sweden, Norway, Germany, the United States, Canada — the Baltic
and North American timber trades, which is where Britain *bought* staves.

That the screen returns **only two candidates in the whole corpus, and both in
the volume already under suspicion**, is itself the useful result: this is a
narrow defect confined to `as_1892`, not a systematic one. **`as_1892` is now a
named problem volume — four separate blocks in it have needed repair, every one
with a mangled or stale group head.**

## A third instrument gap, found by following the staves

The staves rows landed correctly and the year *still* would not close, because
**`Wood And Timber — Staves` held the countries and Tier-1 for 1890-91 while a
node called `Staves, Of All Dimensions` held Tier-1 for 1892-94.** Disjoint
anchors, one series re-worded mid-run — and the countries prove it, the
target's own sums being 136,063 for 1892 and 131,708 for 1893, *exactly* the
other node's anchors.

**Neither arithmetic matcher can see this pair**, and nor can the structural
one:

| instrument | requires | why it misses this |
|---|---|---|
| `match_shadow_anchors` | shadow has **no countries** | both nodes have countries |
| `match_orphan_countries` | orphan has **no anchor** | both nodes have anchors |
| `deheaded_anchor_match` | one name is a **suffix** of the other | `Staves, Of All Dimensions` is not |

So there is a third population: **anchored node ↔ anchored node, disjoint
anchor years, no name relation.** `deheaded_anchor_match`'s era-split logic is
the right test but its structural pre-filter excludes them. Folding this one
took staves 1893, 1894, 1895 and 1896 to EXACT.

**That is the next instrument to build**, and it should be cheap: reuse the
era-split test (anchors disjoint) but select candidates by *arithmetic*
(one node's country sums matching the other's anchor) instead of by name.

## Result

exact01 3,371 → **3,374**, nodata 4,654 → 4,655, denominator 9,594 → 9,596.
Zero true regressions.

A residue: the `Staves, Of All Dimensions` fold left a bare `Staves` node still
holding 1866-68 and 1892-95 anchors with no countries — 1892's anchor did not
travel with the rest. Queued.
