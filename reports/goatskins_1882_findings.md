# Goat skins 1882: both engines parsed it under the right label, and neither copy was usable

Worked 2026-08-02 (`/loop /next-defect`), bracketed-gap rank 3, GBP 477k.
**`Skins And Furs — Goat, Undressed` 1882 went from `nodata` to exactly
1.000000** — 3,620,868 of 3,620,868 Number.

**exact01 3,572 → 3,573, nodata 4,288 → 4,287, denominator held at 9,464. One
commodity-year changed; zero regressions.**

## Neither parse was usable, and the label was never the problem

Both engines file the block under the **correct** `SKINS, FURS, and PELTS |
Goat, Undressed`. But:

- **Chandra lost the entire quantity column** — all nine rows have a value and a
  null quantity;
- **Infinity mislabelled the last member as `TOTAL`**, so its members summed
  3,260,186 against a Tier-1 of 3,620,868 and the year read `nodata`.

## `as_1882` offsets its labels — the third block on that volume

The printed rows read:

```
" Goat, Undressed :
From Holland | - - - - - | Number. | £        <- Holland's label shares the header row
" France     | - - - - - | 74,165  | 11,876
" Turkey     | - - - - - | 63,481  | 11,302
…
" Other Countries | - - - - - | 1,187,853 | 80,325
Total        | - - - - - | 3,620,868 | 358,775
```

**Each number pair belongs to the label above it.** This is the third block found
on `as_1882` with that layout, after the furniture-hardwoods block and the bones
block — **`as_1882` should be treated as a known-bad-layout volume.**

**What settles the reading is that both engines agree once the offset is
applied**: the first eight pairs go to Holland…Bengal — which is exactly what
Infinity's parse assigns — and the ninth figure, **360,682, is `Other
Countries`**, the row Infinity called `TOTAL`.

**Second instance of a country wearing the subtotal's name**, and both are in
this same volume.

## Both columns close

The nine members sum to **3,620,868 = the printed Total = the Tier-1**, and their
values to **358,775 = the printed value total**. `Other Countries`' value is
**pinned by that closure at 37,419**; Infinity reads 37,319, which leaves the
value column 100 short.

## Still open

1878, 1879 and 1900 are `nodata`; 1892 reads 0.9776 and 1888 0.9892.
