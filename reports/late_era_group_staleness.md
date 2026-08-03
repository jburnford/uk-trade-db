# The 1897-1900 gap class: diagnosed, and two fixes refuted

**No metric gain this round.** exact01 held at 3,741. What it produced is a
diagnosis of the largest reachable gap pool and the elimination of the two
obvious ways to fix it — both of which were tried, measured, and reverted.

## The class

328 `nodata` cells across 146 commodities fall in 1897-1900, and the pattern is
sharp:

| gap years | commodities |
|---|---|
| 1897, 1898, 1899 | **45** |
| 1900 only | 43 |
| 1897-1900 | 22 |

Almost all have their **last origin year at 1896** — exactly where the volumes
switch to the five-year comparative layout.

**The data is not missing.** `country_obs` carries these years: `Dry` has 15 rows
from as_1897, 15 from as_1898, 17 from as_1899 and 17 from tn_1901. What has gone
wrong is the **group**. Traced through `country_year_consensus`, the article `Dry`
is filed under `HIDES, Raw, and Pieces thereof` in 1895-96 and under `GLASS`,
`HATS OR BONNETS` and `HEMP` from 1897 — three volumes, three different stale
headings. The parser's sticky group loses its footing in the late-era layout.

**62 articles have a dominant group that flips between 1893-96 and 1897-1900.**
And both eras are unreliable: `skins, unenumerated, undressed` is wrong early
(SILVER, ORE OF) and right late (SKINS AND FURS); `dry` is right early and wrong
late. There is no era one can simply trust.

## Refuted fix 1 — regenerate the group authority

`reference/article_group_authority.csv` is the designed instrument for exactly
this (a cross-volume plurality vote on the article's group, consumed by
`vote_country_years.py`, which applies the 576 non-REVIEW rows). `Dry` is simply
absent from it, so `repair_groups.py` was re-run.

It produced a *larger* authority — 687 rows to 1,050, applied rows 576 to 931 —
and fixed some things (`Train or Blubber` → `OIL`). It also produced
`Bere or Bigg` → `CORK` and `BOXES (except Whalefins)` → `BEEF`.

```
exact01        3,741 -> 3,611   (-130)
GBP within 0.1% 53.6% -> 51.0%
```

**Reverted.** The plurality vote is taken over the same corrupted group
assignments it is meant to fix, so where the corruption is the majority it
enshrines it. The file on disk is better than what the generator now produces,
and **`repair_groups.py` must not be run blindly** — anyone re-running it should
diff and measure first.

## Refuted fix 2 — containment matching in the sticky repair

`build_viz_payload` already has a country-cell sticky repair that re-homes a row
when its printed group+article is not an attested commodity but the article alone
unambiguously names one. It cannot reach this class, and the reason is worth
recording:

> the anchor for these commodities is a **de-headed label carrying the whole
> phrase**. `Hides, Raw, and pieces thereof, Dry` is printed groupless, so its
> signature is the full phrase, while the country rows carry group `HIDES, RAW,
> AND PIECES THEREOF` and article `Dry`. The two agree only while the group
> holds. There is **no Tier-1 anywhere whose article is `Dry`**, so the repair
> has nothing to re-home to.

The fix attempted was containment: re-home when exactly one attested signature
*contains* all the article's tokens. Measured first — it resolves uniquely for
`dry`, `wet` and `geldings`, but `yarn` has **20** candidate commodities and
`in blocks, ingots, bars, or slabs` has **9**, so it was gated on uniqueness.

```
exact01  3,741 -> 3,721   (-20)     39 better, 32 worse
```

**Reverted.** The gains were small commodities (Skins And Furs — Unenumerated,
Bones For Manure); the losses were larger and worse — `Rice — Not Rough Nor In
The Husk` 1874 fell from exact01 to 0.0955, and `Rags, Woollen` lost eight years
to `nodata`. Uniqueness of containment is not sufficient: a single-token article
can be contained by exactly one attested signature and still belong where it was.

## What would actually work

The group is recoverable, but not from the article label and not from a vote over
the corpus. The two signals that have not been used:

1. **Position on the page.** These are stale-sticky-group errors, so the correct
   group is the last one printed *above* the row in the same volume — a
   `row_seq`-local question, not a corpus-wide one. `group_repairs.csv` already
   expresses exactly this (`new_group` over a seq range); what is missing is a
   screen that proposes the ranges.
2. **The anchor's own arithmetic.** A misfiled block makes its true commodity
   read `nodata` and its false host read `over`. Pairing an `over` host with a
   `nodata` commodity of the same unit and testing whether moving the block
   closes *both* is a two-sided test, and much stronger than either side alone.
