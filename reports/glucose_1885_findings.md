# Glucose 1885: the engines differ on layout, not on digits

Worked 2026-08-02 (`/loop /next-defect`), bracketed-gap rank 3, GBP 459k.
**`Sugar — Glucose` 1885 went from `nodata` to exactly 1.000000** — 460,524 of
460,524 Cwt.

**exact01 3,573 → 3,574, nodata 4,287 → 4,286, denominator held at 9,464. One
commodity-year changed; zero regressions.**

## The table

Absent from both parses, present in both engines' raw text, printed as
`Glucose, Solid and Liquid`:

| Germany | Holland | Belgium | France | United States | **Total** |
|---|---|---|---|---|---|
| 404,435 | 8,323 | 1,110 | 30,125 | 16,531 | **460,524** |
| 284,184 | 5,702 | 970 | 22,385 | 12,824 | **326,065** |

**Both printed columns close to the digit** — 460,524 = the block's own Total =
the Tier-1, and 326,065 = the printed value total.

## What made it safe

**The two engines disagree only on layout, not on digits.** Chandra prints each
label on the same row as its numbers; Infinity has the **label-above-numbers
offset** (`From Germany` sharing the header row) that `as_1882` showed three
times. **Once the offset is applied the two assign identical figures to
identical countries** — so the reading needed no arbitration at all.

That is worth noting as a distinct, benign case: the offset is not always a
defect to be corrected against a closing total. **Where one engine has it and the
other does not, and the two agree after correction, the layout difference is
itself the confirmation.**

Written as five `manual_rows` under `SUGAR | Glucose`, the spelling the payload
node's own name carries.

## Still open

1866-1871 `nodata`; 1874 reads 0.6298 and 1880 0.9615.
