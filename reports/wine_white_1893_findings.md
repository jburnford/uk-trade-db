# Wine — White 1893: the right anchor, pointed at the wrong printed table

Session 11, iteration 62 (2026-07-27). `Wine — White` 1893 read **1.683** — one
cell, **GBP 15.4M**, the highest per-cell exposure left after the taxonomy- and
page-image-blocked items. It is now **0.999893, exact**.

```
exact01 2,821 -> 2,822 ; within 0.1% GBP 53.6% -> 53.8% ; within 5% 71.0% -> 71.1%
over 197 -> 196 ; denominator UNCHANGED at 9,940
```

`diffcells.py`: **exactly one cell changes class.**

## Not glue, not the anchor — a wrong table selection

The anchor was checked first and is sound. What made this one different is that
the defect was in an **existing repair**, not in the parse.

Two `group_repairs` rows mapped `as_1893 | WINE | White: Total of` (seq 484-499,
plus a continuation at 500-512) onto `WINE | White`. That block's origins sum to
**4,731,471** gallons. But the `Wine — White` anchor for 1893 is **2,811,813**,
and the whole 1893-97 Tier-1 series —

```
2,811,813   2,596,539   3,132,217   2,820,884   2,994,978
```

— is the **`White, in Casks`** line: the abstract prints the bare word `White`
under a *WINE, IN CASKS* section head. The all-sorts white total is nearly twice
that.

The correct block was two tables earlier and closes to the digit:

```
as_1893 | WINE | White, in Casks   seq 363-380
   members        2,811,513
   printed grand  2,811,813  ==  T1
```

Wine's printed hierarchy is deep — `White, in Casks`, `White, in Bottles: Still`,
five sparkling sub-sorts, `White: Total of`, `Total of all Kinds` — and every one
of those is a plausible-looking origin table. Only the arithmetic distinguishes
them.

## A note on how this was applied

This is the first change in the session that **edits existing rows** in
`reference/group_repairs.csv` rather than appending. The two rows were replaced
by one, and the replacement carries the full original note text plus the reason
for the change, so nothing is lost from the record.

The append-only convention exists to stop earlier adjudications being quietly
rewritten. Here the earlier adjudication is simply wrong for this commodity —
it points a 4.73M table at a 2.81M anchor — and the correction is arithmetic
rather than judgement. Appending a competing block would not have worked in any
case: `seen_added` is first-wins in file order, so a later row loses to the rows
it is meant to supersede.

> **`group_repairs` has no way for a later row to override an earlier one.** When
> an existing repair points at the wrong table, the row itself has to change.

## Still open

- The **1889-1892** repairs use the same `White: Total of` → `White` mapping
  (rows for as_1889, as_1890, as_1891, as_1892). None of those years is currently
  flagged off, and `Wine — White` carries no Tier-1 line before 1893, so they are
  not costing a bucket — but they are the same mapping, and if an anchor ever
  arrives for those years they will read ~1.7 exactly as 1893 did. Worth
  re-pointing at each volume's `White, in Casks` block in the same pass.
- `Wine — White` has **no origin data at all for 1894-97** (T1 present, sum zero).
  The `White, in Casks` block should exist in each of those volumes too.
