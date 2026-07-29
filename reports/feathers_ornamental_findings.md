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

---

## Update, iteration 16 — 1889 decoded and closed

The `Lbs. ozs` decode was run with the uniqueness-counting solver built for
`Tons. Cwts` (`scripts/decode_tons_cwts.py`), adapted to a **carry of 16**
ounces to the pound.

**`as_1889` decodes uniquely and closes twice over.** The thirteen members sum
— with the carry — to **796,537 lb 4 oz**, which is both the block's own
printed grand total and the **Tier-1 for 1889 (796,537 lb)** to the digit. So
the decode has the same double confirmation the 1893/94 `Tons. Cwts` blocks
had: its own printed total *and* the national anchor.

    British East Indies   8,793,614  ->  87,936 lb 14 oz
    France                2,283,838  -> 228,383 lb  8 oz
    United States         2,237,278  -> 223,727 lb  8 oz
    South Africa          1,481,670  -> 148,167 lb  0 oz
    …thirteen rows, one closing combination

**`Feathers And Down — Ornamental` 1889: `over` at 20.09× → EXACT** (796,538
against 796,537). Thirteen `manual_rows`, tier A.

**`as_1890`, `as_1891` and `as_1892` do not decode and were left alone.**
1891's grand reads 71,457,511 and 1892's 8,532,562; no combination of member
readings closes on any reading of their printed totals. 1892 is the frustrating
one — its *totals* decode perfectly (569,690 + 283,566 = 853,256 lb 2 oz = T1
exactly, shown in the original write-up above) but its **members** fall 31
short of the printed foreign total, so something else is wrong in the block as
well. Guessing past that is exactly what the uniqueness guard exists to
prevent.

The era-split fold of the de-headed `Ornamental` anchor is still queued behind
the remaining three years.

---

# A one-engine NULL quantity column — 1883 and 1885 recovered, 1890 is a page job

Worked 2026-07-29 (`/loop /next-defect` iteration 27).
**exact01 3,483 → 3,485 (+2), denominator unchanged at 9,524, zero
regressions.** The corpus headline is small; the commodity's is not.

## How it surfaced

The refreshed bracketed-gap screen put ornamental feathers at rank 3 (1890,
£3.33M) and rank 5 (1883, £2.83M) — ranks 1 and 2 being the two confirmed-dead
verdicts. A printed-total hunt for 646,144 and 804,666 returned nothing in
either engine, and iteration 16's `Lbs. ozs` decoder had reported `as_1890:
SKIP`. Both of those pointed the wrong way. **The unit was never the problem.**

## The defect: one engine loses the quantity column, cell by cell

The `Lbs. ozs` years are not fused here — the quantity is simply **absent** for
some rows, and `integrate_sources` then admits the surviving value under unit
`'Value'`, which the modal-unit metric cannot count. Scanning NULL quantities
across the whole series separates two populations cleanly:

| volume | Chandra NULL | Infinity NULL | |
|---|---|---|---|
| as_1875 | 1 of 11 | 0 of 11 | recoverable (already self-healed) |
| as_1883 | 6 of 20 | 0 of 19 | **recoverable** |
| as_1885 | 9 of 18 | 0 of 18 | **recoverable** |
| as_1886 | 4 of 19 | 4 of 19 | page image |
| as_1887 | 8 of 18 | 8 of 18 | page image |
| as_1890 | 9 of 18 | 9 of 18 | page image |

**When both engines NULL the same rows the column is gone from the scan, not
from the extraction** — no decode, no arbitration, nothing to do but the page.
That is the whole answer for 1890, and it is why the decoder skipped: its
`if not tot or not mem` branch fired because the block's grand TOTAL carries no
quantity at all. The old brute-force script's separate "search space too large"
SKIP had sent the last attempt looking for a fused column that was never there.

## 1883

Chandra dropped exactly the five largest origins — Holland, France, British
Possessions in South Africa, British East Indies, Australasia — so the year read
**0.1050**, the fourteen small survivors summing to 67,828. Infinity carries all
five: 87,455 / 129,002 / 268,802 / 91,934 / 861. Total **645,882 against Tier-1
646,144**, −262, **0.041%**.

Values are left as Chandra had them and are **not** adjudicated: the block's
member values sum 30,030 short of the printed 2,011,926, and it prints no
foreign/British subtotal to arbitrate with. `v_tier` B, honestly.

## 1885 — where the value column does the work

Chandra dropped six quantities. Here the **value** column closes to the digit
and settles both engine disagreements without any guessing:

- foreign member values sum **488,665 = Infinity's printed foreign subtotal**,
  so **Chandra's 458,665 is the misread**;
- British member values need BPSA = 1,005,414 − 101,795 = **903,619**, so
  **Chandra's 903,619 is right and Infinity's 908,619 is wrong**;
- 488,665 + 1,005,414 = **1,494,079 = the Tier-1 value exactly**.

With that established, the quantities give foreign 437,375 against a printed
437,437 and British 313,823 against a printed 313,824 — grand **751,198 against
Tier-1 751,261, 0.0084%**. And the foreign subtotal rejects Infinity's Belgium
11,557 outright (it would overshoot by 9,938), so **Chandra's 1,557 stands**.
The residual 62 is one small foreign cell both engines misread; the printed
subtotal admits no candidate either engine holds, so it is left alone.

**This is the two-column proof running in the other direction** — everywhere
before, the quantity column arbitrated the value. Here the value column, which
is not what the metric measures, is the only reason the quantities can be
trusted at all.

## Why `obs_source=inf` was the wrong instrument

The obvious move — flip both blocks to Infinity wholesale — is worse than it
looks. Infinity's as_1883 copy **mislabels `Other Countries` as `TOTAL`** and
loses the real grand total, so the block would be dropped as a subtotal and the
year would land at 0.9913 rather than exact. Infinity's as_1885 copy has Belgium
11,557 and BPSA value 908,619, both refuted above. **Neither engine's copy of
either block is right; only the union is.** Eleven `manual_rows` cells with
`replace=1`.

## as_1875 — a real correction the metric already had

Chandra's 1875 quantity column is **row-slipped one down from Belgium**
(Belgium NULL, France holding Belgium's 3,475, Egypt holding France's 131,534,
and so on). Infinity is aligned and its ten members sum to **296,000 = the
printed TOTAL = Tier-1 to the digit**. Five manual rows were written for it and
then **removed**: the payload already read 296,000 with the correct country
attribution, because Chandra's NULL Belgium had dropped that row and let
Infinity's copy fill the block. **The pipeline self-healed the slip.** Worth
recording, because the same one-NULL-cell trigger is what makes a slipped block
recoverable without intervention — and a block slipped *without* a NULL would
not be.

## Result

| year | before | after |
|---|---|---|
| 1883 | 0.1050 | **0.9996 — exact01** |
| 1885 | 0.2243 | **0.9999 — exact01** |

The commodity now closes in **19 of its 24 anchored years**. The residue is
1886 (0.6212), 1887 (0.2664), 1888 (1.1582) and 1890 (0.1554) — 1886/87/90 all
page-image jobs by the table above, 1888 an over-count that is a different
defect.

## Queued: a junk sibling node

`Feathers: For Beds Cwts. Ornamental` holds 18 T1 years of **fused two-column
anchors** — `22437296000` is 22,437 ‖ 296,000, the For-Beds and Ornamental
columns run together — and no country data at all. It contributes 18 `nodata`
commodity-years to the denominator for free. A fused *T1* under a phantom
article is a class the fused-quantity decoders do not look at, and this is a
clean specimen of it.
