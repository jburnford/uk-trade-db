# Furniture hardwoods 1882: a page that offsets its labels, and a row called TOTAL that is a country

Worked 2026-08-01 (`/loop /next-defect`), bracketed-gap rank 3, GBP 543k.
**`Wood And Timber — Furniture, Hardwoods, And Veneers : Unenumerated` 1882 went
from 0.0934 to 1.03138** — `under` to `within5`.

**within 5% 1,111 → 1,112, under 275 → 274, exact01 unchanged at 3,563,
denominator held at 9,497. One commodity-year changed; zero regressions.**

## Where it was

Parsed all along, under `Wood and Timber | Mahogany : Unenumerated` (seq
1977-1991) — the run-in form in which the printed sub-head `Furniture,
Hardwoods, and Veneers` was absorbed after the preceding Mahogany article.

## The page offsets its label column one row above its numbers

```
Mahogany:
From Spanish West India Islands |  Tons. |   £
" Mexico                        |  1,910 |  18,524
" Central America               | 19,444 | 194,818
" British Honduras              |  2,799 |  27,630
" Other Countries               | 10,173 |  92,331
                                |  2,152 |  22,270
Total                           | 36,478 | 355,573
```

**The Mahogany block proves the offset independently.** Read with the offset its
members are Spanish West India Islands 1,910, Mexico 19,444, Central America
2,799, British Honduras 10,173 and Other Countries 2,152 — which sum to
**36,478 = its own printed Total, to the digit**.

**The parser already applies that offset correctly** to both blocks, so the
fourteen member labels Russia…British Guiana at seq 1977-1990 are right.

## The one error: a row called TOTAL that is a country

Seq 1991 is parsed as country **`TOTAL`** with 4,446/37,541. Under the same
one-row offset that figure belongs to **`Other Countries`** — the printed
`Total` line's own numbers sit on the row below, off the bottom of the block.

**Proof:** the fourteen parsed members sum to 48,324, and **48,324 + 4,446 =
52,770 = the Tier-1 to the digit.**

Supplied by `manual_rows`, because `is_subtotal` drops anything labelled TOTAL.

**This is the mirror of a class already on file.** Four blocks have been found
carrying a *subtotal wearing a country's name* (as_1875 `West Coast of Africa
(Foreign)`, as_1899 `Australasia`, as_1891 pepper's two). **This is the opposite:
a country wearing the subtotal's name**, and it is invisible for the same reason
— `is_subtotal` keys on the literal word.

## Residual, diagnosed and deliberately not fixed

The year lands at 54,426/52,770 = 1.03138, **exactly 1,656 over**, and the 1,656
is **Belgium 718 + Holland 938**. Neither appears in the printed 1882 hardwoods
block; both arrive from `commodity_curation` row 694, which folds
`Wood And Timber — Staves : Unenumerated` into this node **unscoped**.

Overturning an adjudicated unscoped fold needs its own evidence and is a
taxonomy question, so it was left alone. **If that fold is right for other years
and wrong here, the fix is a year scope; if it is wrong wholesale, the fifteen
printed members close this year exactly on their own.**

## Still open in this commodity

1868-1871, 1873, 1874 and 1884-1887 are `nodata` (nine years with a Tier-1 and no
origin table located); 1872 reads 0.1085 — **the export-leakage signature band** —
and 1876/1877 sit at 0.934/1.093.
