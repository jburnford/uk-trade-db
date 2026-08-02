# Opium 1882: absent from both parses, closing on both columns

Worked 2026-08-02 (`/loop /next-defect`), bracketed-gap rank 3, GBP 483k.
**`Opium` 1882 went from `nodata` to exactly 1.000000** — 478,624 of 478,624 Lb.

**exact01 3,568 → 3,569, nodata 4,292 → 4,291, denominator held at 9,464. One
commodity-year changed; zero regressions.**

## The table

Absent from `country_obs` and `country_obs_inf` alike, and present in **both
engines' raw text**, printed simply as `Opium`:

| Holland | Turkey | Persia | China | Other Countries | **Total** |
|---|---|---|---|---|---|
| 10,998 | 359,560 | 54,442 | 34,347 | 19,277 | **478,624** |
| 8,977 | 261,590 | 41,219 | 24,122 | 14,242 | **350,150** |

**Both printed columns close to the digit** — 478,624 = the block's own Total =
the Tier-1, and 350,150 = the printed value total.

## The arbitration

The engines disagree on exactly one figure: **Persia, Chandra 54,442 against
Infinity 54,412**. Chandra's is the reading that closes the quantity column;
Infinity's leaves it 30 short. That is the whole of the arbitration — the
closure picks one candidate and there is no second single-digit solution, so no
out-of-block test was needed.

Written as five `manual_rows` under `DRUGS | Opium`, the label the node's own
1883-1899 rows carry. `commodity_curation` row 666 folds that label into `Opium`
with a year scope that **already included 1882** — checked before writing, per
the year-scoped-fold trap.

## Still open in this commodity

1866-1871, 1890, 1893, 1899 and 1900 are `nodata` — ten years with a Tier-1 and
no origin table located.
