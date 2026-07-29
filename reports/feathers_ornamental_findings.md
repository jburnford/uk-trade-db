# Feathers And Down — Ornamental: a £27M node with three stacked defects

Worked 2026-07-29 (`/loop /next-defect` iteration 12). **Nothing here closed** —
this is a diagnosis, a correction of my own previous repair, and one new named
defect class. Recorded so the next pass starts from the evidence rather than
the symptom.

The commodity closes **1.0000 in 1872–1882, 1884 and 1891** and is broken
everywhere else:

| | ratio | |
|---|---|---|
| 1868–71 | 0.0000 | no origin volume |
| 1874 | 0.8792 | |
| 1883 | 0.1050 | ← bracketed-gaps rank 6, £3.3M |
| 1885 | 0.2243 | |
| 1886 | 0.6212 | |
| 1887 | 0.2664 | |
| 1888 | 1.1582 | |
| **1889** | **20.09** | fused unit |
| 1890 | 0.1554 | |
| **1892** | **48.82** | fused unit |
| 1893–98 | 0.50–1.34 | anchor not attached (see §2) |
| 1899–1900 | 0.0000 | |

## 1. NEW DEFECT CLASS: a fused two-column quantity

`as_1889`–`as_1892` print ornamental feathers with **two quantity columns,
`Lbs.` and `ozs.`**, and both engines read the header as one compound unit
(`Lbs. oz` / `Lbs. ozs`) and the two figures as one number. That is the whole
of the 20× and 49× over-counts.

**The decode is provable from the block's own printed totals.** `as_1892`:

| printed | reads as | |
|---|---|---|
| foreign TOTAL 5,696,900 | 569,690 lb 0 oz | |
| British TOTAL 2,835,662 | 283,566 lb 2 oz | |
| grand TOTAL 8,532,562 | **853,256 lb 2 oz** | **= Tier-1 exactly** |

and 569,690 + 283,566 = 853,256 ✓. Three printed totals, all consistent, and
the grand total lands on the national anchor to the digit.

**The members do not decode as cleanly, and that is why this was not fixed
here.** The ounces field has no fixed width — a 0-oz row fuses one digit, a
13-oz row fuses two — so each member needs its own adjudication. Taking one
digit off everything and two off France gives foreign members of 569,659
against a printed 569,690 (31 short); the British half comes to 284,618
against 283,566. The unit price is a useful cross-check and confirms the
magnitude: South Africa decodes to 222,071 lb for £488,342 = **£2.20/lb**,
exactly right for Cape ostrich feathers, while the raw 2,220,718 would imply
22 pence a pound.

**The class is bounded and larger than this commodity.** Scanning every unit
label that looks like two columns fused:

| unit | rows (ch/inf) | volumes | labels |
|---|---|---|---|
| `Tons. Cwts` | 103 / 36 | 11 | 6 |
| `Lbs. oz` + `Lbs. ozs` | 71 / 43 | 4 | 1 (this one) |
| `Tons. £` | – / 10 | 1 | 1 |
| `Loads. £` | – / 8 | 1 | 1 |

(`Oz. Troy`, `Doz. Pairs`, `Gt. Hunds`, `Prf. Galls` are genuine single units,
not fusions.) **`Tons. Cwts` is the bigger prize and has not been looked at.**

## 2. The anchor is de-headed, and it splits the series in two

`Feathers And Down — Ornamental` carries Tier-1 for **1868–1891**. A bare
`Ornamental` node, with no countries at all, carries Tier-1 for
**1892–1900**. So 1892–98 have origin data that is measured against nothing,
and the seven anchors are measured against no origins.

Folding them is one `commodity_curation` row — **but do not do it before §1 is
fixed.** The fold would move seven commodity-years out of `nodata` and land
1892 at 48.8 and 1895 at 1.34. Order matters: decode the fused unit first,
then unite the anchor.

## 3. Correction to iteration 11's repair

Iteration 11's sub-entry screen flagged this commodity's 1895 British half and
I admitted eleven rows (seq 1081–1091). **That was wrong for five of them, and
the mechanism is worth recording.**

The five drill-downs — `British Possessions in South Africa : Cape of Good
Hope` 326,418 and `: Natal` 8,534, `British East Indies : Bombay` 76,385,
`: Bengal` 59,741, `: Other` 1,587 — are **not missing from the corpus**.
Consensus already holds every one under `FEATHERS AND DOWN` with a **NULL
article**, which folds to a different payload node. Admitting them here put
them in the `Ornamental` node a second time, and `build_viz_payload` then
**synthesized a `British Possessions In South Africa` parent** (326,418 +
8,534 = 334,952) from the newly-present constituents and counted it beside
them — a triple count of the Cape trade.

It was invisible to the baseline only because this node has no Tier-1 for 1895
(see §2), so it would have surfaced as 1.34 the moment the anchor was folded.
The repair is narrowed to seq 1087–1091, keeping the three **plain** British
rows that no consensus copy carries (Australasia 2,872, British West India
Islands 1,491, Other British Possessions 2,532). 1895 goes 1,330,537 →
522,920.

**Generalisation: the CONSTITUENTS pass synthesizes a parent from members that
are present, and the baseline counts both.** Adding drill-downs to a node that
already has their siblings is therefore not safe by inspection — check whether
a synthesized aggregate appears beside them. This is the *third* distinct way
this corpus double-counts an aggregate against its members (the others: the
confectionery `turkey` aggregate in iteration 6, and `British East Indies`
beside `Bengal` recorded in the anchor-disagreement report).

## What to do next, in order

1. **Decode `Lbs. ozs` for as_1889–as_1892** — 71 rows, four blocks, each with
   three printed totals to adjudicate against. This is the only thing blocking
   the rest.
2. Then fold `Ornamental` into the headed node (one curation row).
3. Then the shortfall years (1883, 1885, 1887, 1890 all read 0.10–0.27) — most
   likely the same label split as §2 rather than lost tables, given how much of
   this commodity's data sits under `FEATHERS AND DOWN | ⟨null article⟩`.
4. Separately: **`Tons. Cwts`**, 139 rows across 11 volumes and 6 labels, the
   same fused-column class and not yet examined.

Baseline unchanged this iteration: 9,634 c-y, exact01 **3,144** (32.6%),
GBP 51.0% / 68.1%. Zero commodity-years changed by the narrowing.
