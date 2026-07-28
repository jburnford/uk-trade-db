# Caoutchouc 1885/1887: the retry the instrumentation unblocked

Session 11, iteration 66 (2026-07-27). Iteration 63 attempted these two years,
predicted 0.991 and 0.998, got **0.384** and **1.014**, and reverted. Iteration 65
built the groupfix audit. This is the retry.

```
1885  0.889276 -> 0.996997
1887  0.901411 -> 0.999579   EXACT

exact01 2,823 -> 2,824 ; under 229 -> 227 ; within 5% GBP 71.1% -> 71.2%
denominator UNCHANGED at 9,940
```

`diffcells.py`: **exactly two cells change class**, both gains.

## What the audit showed, in order

The new standing rule is to read `reports/groupfix_rejects.csv` *before* the
baseline. Doing that caught a second, different problem on the first attempt:

```
as_1887 East Africa  311-333   selected 23   admitted 0   drop_already_added 22
```

Every row rejected — because a **pre-existing repair from an earlier session
already covers that block** at `as_1887 East Africa 314-339` (selected 26,
admitted 23). My row was wholly redundant. Dropping it left the audit clean:

```
as_1885 (null)                246-249  sel  4  adm  3
as_1885 West Africa           250-250  sel  1  adm  1
as_1885 West Africa           251-251  sel  1  adm  1
as_1885 East Coast of Africa  252-252  sel  1  adm  1
as_1885 East Coast of Africa  253-271  sel 19  adm 18
as_1887 (null)                302-306  sel  5  adm  5
as_1887 West Africa           307-309  sel  3  adm  3
as_1887 East Africa           310-310  sel  1  adm  1
```

That pre-existing repair is also **why iteration 63 read 1.0142 for 1887** rather
than the predicted 0.998: the tail was already being contributed, and the attempt
added the head on top of a year that was not fully superseded.

## The two fixes the instrumentation named

**One repair row per `article` value.** Iteration 63 used one row per year over
seq 246-271 and selected 4 rows from a range holding 26, because the parser wrote
three different articles inside it — `NULL` 246-249, `West Africa` 250-251,
`East Coast of Africa` 252-272. Five rows now cover as_1885 and four cover
as_1887.

**Disambiguate the colliding country.** `Portuguese` appears under *both*
`West Africa` and `East Coast of Africa` in each year, and `seen_added` is keyed
on `(sig, country, year)` — so one of the two would have been dropped as a
duplicate. Each is relabelled to its printed region
(`West Africa : Portuguese Possessions`, `East Coast of Africa : Portuguese
Possessions`), which is also the correct label. Exactly one collision per year;
the audit's `drop_already_added` column is how it was found.

Also carried: 1887's consensus spells the group **`CAOUTCHOUK`** — a sixth OCR
spelling after the five in iteration 59 — needing its own supersede key.

Both ranges stop short of the printed **British TOTAL wearing the last
sub-entry's head** (`British East Indies` 37,476 at as_1885 row 272; row 334 in
as_1887), the shape first named in iteration 54.

## Still open

- **1885 at 0.99700** — 541 cwt short, against a block whose foreign half is
  1,527 short of its own printed total. Small-scale.
- **1878 (1.107), 1882 (1.061), 1886 (0.891)** remain. None of their labels
  carries a T1-matching TOTAL, so the boundary rule gives no purchase; they need
  the block extent found another way.
- The redundant-repair case is worth a sweep of its own: `groupfix_rejects.csv`
  now makes **`admitted 0` with a high `drop_already_added`** a one-line query,
  and each hit is either a duplicate repair or a genuine multi-segment collision.
