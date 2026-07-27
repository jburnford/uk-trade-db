# The block-boundary detector

Session 11, iteration 58 (2026-07-27). **The deliverable is an instrument, not a
commodity. Baseline unchanged: exact01 2,814, 53.1% GBP within 0.1%.**

## Why this and not the next commodity

Three items are currently excluded from the defect loop because each is one
stale label covering several printed tables, and each was too large to trace by
hand in a single slot:

```
Caoutchouc                    GBP 38.5M   13 cells   (iteration 49)
Tea                           GBP 18.6M    2 cells   (iteration 56)
Cured Or Salted, Unenumerated GBP 18.1M    3 cells   (iteration 53)
```

That is **~GBP 75M over 18 cells** against a next-best single item of GBP 15.4M
over one cell. The blocker is common to all three, so the tool outranks the
commodity.

## The rule

Derived in iteration 56 from tea, proved in iteration 57 on glucose:

> Inside one label's `row_seq` range, a `TOTAL` row whose quantity equals the
> commodity-year's Tier-1 figure is the **end** of that block. Everything after
> it belongs to a different printed table.

It works because each printed table closes on a grand total that *is* the
national total the abstract publishes. When a group heading is lost, one label
swallows the tables that follow — and the printed grand total of the right table
is the only number in the whole range guaranteed to equal the anchor.

## `scripts/block_boundary.py`

Outputs `reports/block_boundaries.csv`, one row per label, ranked by how much
lies beyond the boundary. Key columns: `boundary_seq` (feeds straight into a
`group_repairs` range), `rows_after`, `qty_after`, `matched`.

```
Tier-1 keys: own 12,291, by (year,qty) 8,894
labels with a T1-matching TOTAL:            7,782
  ...carrying rows BEYOND their boundary:     780
  ...with more than one grand-total run:       42
```

**780 labels** carry rows past their own boundary. That is the size of the
stale-label population, measured for the first time.

Two implementation notes that matter:

- **The label often cannot sig to its own anchor.** `Glucose, Solid or Liquid`
  sigs to `('glucose','liquid','solid')` while its Tier-1 line is printed
  `.. Glucose (Solid or Liquid)` — and `V.sig` *drops parenthesised content*, so
  the anchor sits under `('glucose',)`. The direct test misses it. So a second
  lookup matches a TOTAL against **any** commodity's anchor for that year and
  reports which one in `matched`. `matched='own'` is the strong case; anything
  else names the commodity the boundary total actually belongs to, and is a
  finding in itself — `as_1874 | TEA | Unmanufactured` matches **`Tobacco|Raw`**,
  i.e. that label is a tobacco table mis-headed as tea.
- **Foreign subtotals can match too.** Glucose 1895 has no British half, so its
  *foreign* total equals T1. The boundary is therefore the **longest run** of
  hits with non-repeating years, not the first hit: grand totals cover every
  year column, a stray subtotal covers one.

`--selftest` replays both cases the rule came from and asserts the seq:

```
ok  country_obs as_1899 SUGAR|Glucose, Solid or Liquid -> 21728  (165 rows after)
ok  country_obs as_1896 TEA|None                      ->   289  ( 66 rows after)
```

## It reaches all three blocked items

```
CAOUTCHOUC   as_1898 CAOUTCHOUCC | Eastern Coast of Africa
             seq 1808-2131, boundary 1976, 155 rows after
TEA          as_1896 TEA | (null)
             seq 280-355,   boundary  289,  66 rows after   <- matches the hand trace exactly
CURED FISH   as_1893..as_1896 FISH | Cured or Salted, unenumerated
             boundary == seq_max, 0 rows after
```

The cured-fish result is a **negative control that lands correctly**: iteration
53 concluded those years suffer a *missing British half*, not extra tables, and
the detector declines to flag them.

## An honest limitation, which is also a second signal

Caoutchouc's boundary comes back **1976** where the block actually ends at
**1980**. The reason is exactly what iteration 49 diagnosed: that block's
grand-total rows carry the **wrong year labels** (values in printed column order,
years running 1894, 1896, 1897, 1898, 1895). Row 1977 holds 341,553 — Tier 1 for
**1895** — but is labelled 1896, so it fails the test and the run stops one row
early.

> **When a comparative's grand-total run breaks off before covering every year
> column, suspect a year-label shift in the total rows.** The detector cannot
> resolve that case, but it points straight at it.

## Next

- Work the 780-label list, top-down by `rows_after`. The first fifteen alone
  include `as_1897 NUTS AND KERNELS | Eastern Coast of Africa` (913 rows after),
  `as_1898 PAPER | Hangings` (612), `as_1898 METAL | Leaf, not Gold` (545) and
  `as_1898 PORK | POTATOES` (473).
- Caoutchouc now has a usable boundary despite the caveat; it and tea are ready
  to come back into the loop.
- The `matched` column is worth a pass of its own: every label whose boundary
  total belongs to a *different* commodity is a mis-headed block, named.
