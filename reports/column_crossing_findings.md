# The column-crossing screen, and Rosin 1872

Built from the class found in `reports/boots_1883_findings.md`, where a two-up
page had the parser pair the right column's country labels and **values** with
the left column's **quantities**. Nothing looked for that, because every
quantity-side instrument sees only a short year and every value-side instrument
sees a clean one.

## The test

> A commodity-year whose **origin quantity** sum falls far short of its Tier-1
> quantity while its **origin value** sum matches the printed Tier-1 value.

A genuinely incomplete block loses both columns in proportion. Only a crossed or
misread quantity column loses one. `scripts/detect_column_crossing.py` reports
both directions, since either column can be the survivor, and writes
`reports/column_crossing.csv` worst-first by GBP.

**Two joins had to be normalised or the screen sees almost nothing.** The country
side often carries a stale group — Boots 1883 sits under `JUTE`, Rosin 1872 under
`RAGS AND OTHER MATERIALS FOR MAKING PAPER` — so the join is on **article**, not
group. And the unit is OCR-variable on the anchor side (`Cwts.`, `Cwts`, `Cuts.`,
`Ccts.`, `Cicts.` are all hundredweights) and frequently **null** on the country
side; joining on the literal string gave 362 commodity-years, folding it to a
coarse key gives **800**.

## Coverage, stated plainly

Only **800** commodity-years carry both a quantity and a value anchor that can be
paired — most abstract lines publish one or the other. So this screen is a
targeted probe, not a sweep, and a clean result from it says nothing about the
other ~8,600 commodity-years. 35 are flagged.

The generic-article hits (`raw`, `yarn`, `unenumerated`, `manufactures`) need
their group read before they mean anything — the join is on article alone, so one
commodity's anchor can meet another's origins.

## Rosin 1872 — closed exactly

The cleanest hit, and unambiguous (one commodity, one article). The year read
**0.6734**: three countries — France 82,615, United States 527,536, Other
Countries 9,043 — summing to 619,194 against a Tier-1 of **919,494 Cwt**. Yet
their **values** summed to 492,246 against a printed value total of 492,216:
**0.006% out**. Three countries cannot account for the whole value and only
two-thirds of the quantity.

**The United States figure is wrong: the page prints 827,836, not 527,536.**

- **Five readings against one.** Chandra's as_1872, as_1873 and as_1874 all carry
  827,836, as do Infinity's as_1873 and as_1874. Only Infinity's as_1872 reads
  527,536 — and it won because **Chandra's as_1872 rosin block is not parsed at
  all**, so the year arrived through the `infonly` gap-fill with no contemporary
  rival.
- **The arithmetic is exact.** 82,615 + 827,836 + 9,043 = **919,494**, the printed
  Total and the tier-A anchor across five volumes. 527,536 leaves it 300,300 short.
- **Price confirms it independently.** The printed 1872 world figures give
  £492,216/919,494 = **£0.535 a cwt**, and the United States is about 90% of the
  volume, so its own price must sit close to that. At 827,836 the US price is
  **£0.528** — within 1.3% — and consistent with the external E&H gold series
  (£0.440 in 1871, £0.317 in 1876). At 527,536 it is **£0.829**, 55% *above* the
  world price, which is arithmetically impossible for a country carrying nine
  tenths of the trade.
- **The OCR distance is coherent**: 527,536 → 827,836 is 5-for-8 twice, in the
  hundred-thousands and the hundreds.

This is a stronger proof than the Boots 1883 France cell, which had to be derived
from the total; here the correct figure is **attested five times** and the
arithmetic, the price and the OCR shape all agree.

**919,494 / 919,494 — exact01. Baseline 3,588 → 3,589 of 9,473**, one cell, no
regressions. Rosin now closes in every year 1872-1878.

Worth noting: Rosin is one of the two commodities in the external E&H gold
validation. The gold series holds 1871 and 1876 but **not** 1872, so this
correction neither draws on nor disturbs the hold-out.

## Queued from the screen

- **`Cotton | Raw` 1893 (qty 0.180, £1.2M) and 1894 (qty 0.090, £854K)** — the two
  largest flags by a wide margin, both value-intact. Next.
- **`phosphate of lime and rock` 1887-88** — a *different* defect the screen picked
  up: the group-less `Phosphate Of Lime And Rock` node carries 412,676 / 419,293,
  which are the as_1891 slipped-row values, while `Manures — Phosphate Of Lime And
  Rock` carries the correct 283,415 / 257,886 and closes. Same slipped page as the
  Manganese 1891 override; the manganese fix did not reach this node.
- `yarn` 1874 (qty 0.336) and `Wood And Timber — Furniture and Hardwoods |
  Unenumerated` 1877 (qty 0.445).
