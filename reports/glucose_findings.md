# Glucose 1895: a year-scoped fold quietly threw it away

Worked 2026-08-01 (`/loop /next-defect`).
**exact01 3,531 → 3,532, denominator unchanged at 9,511, zero regressions.**

```
Sugar — Glucose  1895  ('nodata', 0, 1315866) -> ('exact01', 1315866, 1315866)
```

## Not a missing table — a discarded one

Bracketed-gap rank 9, £1.46M. The block was never lost: `as_1895` carries
`SUGAR | Glucose (Solid or Liquid)` at seq 3539-3544 in **both** engines, and
its five origins —

`Germany 68,823 + Holland 4,456 + France 13,910 + United States 1,228,507 +
Other Foreign 170 = 1,315,866`

— are the printed TOTAL **and** the Tier-1, to the digit. They reach
`country_year_final` from consensus. They simply never reach the payload.

## The cause: a scope written against the labels that were visible

`reference/commodity_curation.csv` carries an earlier fold:

```
Glucose (Solid Or Liquid) -> Sugar — Glucose      years: 1872-1892
```

scoped deliberately, because the target's own 1893+ years already closed and an
unscoped fold double-counted them (1894 read 1.883).

The scope is correct for every year it was written against — **and 1895 is the
one year in which the CONSENSUS label is the parenthetical form** rather than
plain `Glucose`:

| year | consensus article |
|---|---|
| 1893 | `Glucose` |
| 1894 | `Glucose` |
| **1895** | **`Glucose (Solid or Liquid)`** |
| 1896 | `Glucose` |

So 1895's origins fell into the scoped source node, landed outside `1872-1892`,
and were **discarded**. Extending the scope to `1872-1892;1895` recovers them.

## The general shape, and why it is worth a screen

This is the iteration-23 scope bug in a new dress. There the scope was built
from the wrong host; here it is right, and still lossy, because **a fold's year
scope is a statement about label spellings as much as about years**. A single
year whose OCR label drifts into the source's form falls through a scope that
was never meant to exclude it, and the loss is invisible: the year reads
`nodata` before and after.

**Checkable class**: for every year-scoped fold, list the source's years
*outside* the scope where the **target reads `nodata`**. Each is a candidate
silent discard. There are 49 scoped folds in `commodity_curation.csv`, so this
is a bounded screen and the next thing to build here.

## Also open in this commodity

`Sugar — Glucose` **1885 still reads 0.00**, and 1885 *is* inside the scope, so
it is a different cause and was not investigated.
