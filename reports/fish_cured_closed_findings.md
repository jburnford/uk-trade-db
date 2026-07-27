# Cured fish 1895-99: one row Chandra never printed

Session 11, iteration 61 (2026-07-27). `Cured Or Salted, Unenumerated` — a
de-headed FISH article, **GBP 18.1M** — was the last of the three
caoutchouc-class items held out of the loop. All five years in the block improve,
three of them to exact:

```
1895 1.0018 -> 1.000290   EXACT      1896 1.0139 -> 1.000823   EXACT
1897 1.4097 -> 0.994522              1898 1.0764 -> 0.972027
1899 1.2513 -> 0.999907   EXACT

exact01 2,818 -> 2,821 ; within 0.1% GBP 53.5% -> 53.6% ; within 5% 70.8% -> 71.0%
over 200 -> 197 ; denominator UNCHANGED at 9,940
```

`diffcells.py`: **exactly five cells change class**, all gains, no regressions.

## The missing row

Iteration 53 closed 1894 (a wrong anchor) and left 1897-99 with two faults: the
printed foreign TOTAL wearing the `United States of America` label, and a British
half that was largely absent — 157,200 missing in 1899, 340,844 in 1898. It named
Infinity's stale-`Bark` copy as the route to try and stopped there.

Infinity does have it, under a stale `EGGS` group, and the missing row has a name:

```
Canada : On the Pacific      1899  157,200      1898  310,843
```

**157,200 is exactly the 1899 shortfall.** Chandra's copy drops the row entirely.
With it the British members come to

```
47 + 71,588 + 157,200 + 114,086 + 81 + 283  =  343,285
660,112 + 343,285                            =  1,003,397  =  T1, to the digit
```

The boundary detector confirmed the Infinity block is clean (seq 6869-6981,
boundary at `seq_max`, nothing after) before any of this was traced.

## Splitting a range around the phantom rows

The block still contains the foreign-total-as-country rows, and they turned out
to be **consecutive**: seq 6936-6940 hold one per year —

```
1895 729,279   1896 731,687   1897 779,330   1898 703,676   1899 660,112
```

so a single split — `6869-6935` plus `6941-6981` — excludes all five. That is
worth remembering: in a comparative block the same printed row occupies
consecutive `row_seq` values across its year columns, so a phantom row is a
**contiguous run**, not five scattered exclusions.

Four supersede-only rows cover the other copies, including
`FISH (INCLUDING TURTLE) | Cured or **S**alted, unenumerated` — the same label
with a capital S, a separate supersede key under the iteration-35 casing rule.

## Still open

- **1897 at 0.9945** (6,432 short) and **1898 at 0.9720** (33,606 short). Both
  are now genuine small residuals rather than structural faults: 1898's British
  members reach 467,044 against a printed 497,047, and its foreign members
  700,073 against a printed 703,676. Two more dropped or misread rows, in a block
  whose other three years close.
- With this, **all three caoutchouc-class items are resolved or reduced** —
  caoutchouc 1893-99 to within 0.5-3.3% (iteration 59), tea 1894-98 exact
  (iteration 60), cured fish here. The boundary detector built in iteration 58
  is what made each of them tractable.
