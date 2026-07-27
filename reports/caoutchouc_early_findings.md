# Caoutchouc 1872: the payload had the first four rows of the table

Session 11, iteration 63 (2026-07-27). The early half of `Caoutchouc` —
1872, 1878, 1882, 1885, 1886, 1887, **GBP 15.4M** — is the part iteration 59 did
not touch, and the boundary detector reports every label in those volumes clean,
so it is not stale-label glue.

**One year closes. Two attempts were made, measured, and reverted.**

```
1872  0.067206 -> 1.000038   EXACT
exact01 2,822 -> 2,823 ; under 230 -> 229 ; denominator UNCHANGED at 9,940
```

`diffcells.py`: **exactly one cell changes class.**

## 1872 — the table stopped after four rows

The payload carried Germany 1,786, Holland 4,397, France 2,113 and Portugal
2,263, and nothing else: **the first four rows of the printed table**, 10,559
against an anchor of 157,114.

Infinity has the whole block — `as_1872 | CAOUTCHOUC | (null)` seq 198-212,
members **157,120** against the printed TOTAL at 213 of **157,114 = T1**. What
was missing is everything from `West Coast of Africa` 876 onward: Portuguese
Possessions 13,259, Ecuador **68,143**, Brazil 10,439, Mauritius 13,855, Bengal
and Burmah 15,296.

The anchor was checked first, per the standing rule: tier A on five volumes, and
the Tier-1 series is smooth across the decade (152,118 / 161,085 / **157,114** /
157,436 / 129,163).

## 1885 and 1887 — attempted, measured, reverted

Both have a clean-looking Infinity block whose printed totals equal T1:

```
as_1885  seq 246-272, grand at 273 = 180,141 = T1
         row 272 'British East Indies' 37,476 is the printed BRITISH TOTAL
         wearing the last sub-entry's head (members 261-271 sum 37,386)
         hand arithmetic: 141,138 + 37,386 = 178,524  ->  0.99103

as_1887  seq 302-333, grand at 335 = 237,511 = T1
         British members 322-333 sum 65,668 — the printed British total TO THE
         DIGIT; foreign members 400 short of 171,843
         hand arithmetic: 171,443 + 65,668 = 237,111  ->  0.99832
```

Applied, they did **not** produce those numbers. 1885 came back at **0.384** —
worse than the 0.889 it started at — and 1887 at **1.0142** rather than 0.998.
The groupfix rows are landing only partly, so the hand arithmetic on the raw
block is not what reaches the payload.

Both rows were **removed** rather than shipped. A year going from 0.889 to 0.384
is a regression, and shipping it because the accompanying year improved would be
trading one number for another without understanding either.

> The gap between "the raw block sums to X" and "the payload sums to X" is where
> this class of repair fails, and it is not visible until the rebuild. Predict
> the number *before* applying, and treat a mismatch as a stop signal rather than
> something to tune away.

## Still open

- **1885 (0.889) and 1887 (0.903)** — the blocks are identified and their printed
  totals verified; what is unknown is why only part of each lands. The likely
  candidates are the same two gates that have bitten before: a surviving
  consensus/subentry row holding the `(sig, country, year)` triple, or another
  OCR spelling of the group left unsuperseded. 1887's consensus spells the group
  **`CAOUTCHOUK`**, which is a sixth spelling on top of the five found in
  iteration 59.
- **1878 (1.107), 1882 (1.061), 1886 (0.898)** — untouched. None of their labels
  carries a T1-matching TOTAL, so the boundary rule gives no purchase and the
  block extent has to be found another way.
