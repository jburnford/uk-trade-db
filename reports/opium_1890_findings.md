# Opium 1890: one bad digit, and a year-scoped fold I had already been warned about

Worked 2026-08-02 (`/loop /next-defect`), bracketed-gap rank 3, GBP 450k.
**`Opium` 1890 went from `nodata` to exactly 1.000000** — 451,193 of 451,193 Lb.

**exact01 3,577 → 3,578, nodata 4,284 → 4,283, denominator held at 9,464. One
commodity-year changed; zero regressions.**

## The table was already parsed, complete, with one bad digit

`as_1890` seq 833-844 in Chandra carries all nine members and all three printed
totals. **Chandra reads Persia 80,035 where Infinity reads 30,035, and only
30,035 closes:**

| | members | printed |
|---|---|---|
| Foreign (7) | 2,060 + 33,704 + 360,963 + 3,543 + **30,035** + 5,106 + 5,834 = **441,245** | **441,245** |
| British (2) | 9,223 + 725 = **9,948** | **9,948** |
| Grand | **451,193** | **451,193 = the Tier-1** |

Chandra's 80,035 puts the foreign half 50,000 over, which is what kept the year
out of the payload. **Second opium year recovered this run after 1882, and the
same cross-engine arbitration settled both — there the disagreement was Persia
54,442/54,412, here Persia 80,035/30,035.** Written as `manual_rows` because a
seq-range repair cannot correct a digit.

## The part that cost a rebuild

The nine rows landed in `country_year_final` correctly — and **the payload did
not move at all.**

`commodity_curation`'s fold of `Drugs — Opium` into `Opium` is **year-scoped**,
and its list ran `1882;1883;…;1889;1891;1892` — **1890 was missing.** Every year
that had data when the fold was adjudicated is there; the one year that did not
is the one I was recovering.

**This is the same trap as nuts-and-kernels 1875, and I had already checked this
very fold — for 1882, two iterations ago — and did not re-check it for 1890.**
The check is not "does this fold carry a year scope"; it is **"is the specific
year I am adding inside it"**, every time.

## Not adjusted

The value column does not close and was left alone: the seven foreign values sum
to 277,299 against a printed 277,209, and the printed grand value (282,779) does
not equal its own halves (277,209 + 5,430 = 282,639). The commodity's modal unit
is Lb, so the metric reads the quantity column, which closes exactly.

## Still open in this commodity

1866-1871, 1893, 1899 and 1900 are `nodata`.
