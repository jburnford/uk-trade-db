# Glucose: the boundary rule's first clean win

Session 11, iteration 57 (2026-07-27). `Glucose (Solid Or Liquid)` — **GBP
18.3M**, seven off-cells, every one of them over and most near 2×:

```
1893 1.066  1894 2.564  1895 2.523  1896 2.002  1897 1.974  1898 1.683  1899 1.722
```

**Six of the seven now close exactly, with no regressions.**

## The rule found the block edge in one query

Iteration 56 ended with a proposed rule and no chance to use it:

> Inside a label's seq range, a `TOTAL` row whose quantity equals the
> commodity-year's Tier-1 figure marks the **end** of the block.

Here it worked first time. `as_1899 | SUGAR | Glucose, Solid or Liquid` runs
seq 21683-21893, and its grand-TOTAL rows at **21724-21728** read

```
1,315,866 / 1,539,127 / 1,610,115 / 1,887,046 / 1,825,609
```

— every one the T1 figure for 1895-99 **exactly**. That is the boundary, found
without tracing a single country. Rows 21729 onward are a different table
altogether (Russia, Uruguay, Argentine, then Australasia, Canada, Falkland
Islands; grand 2,175,822 in 1895), and its Australasian colonies were being read
as glucose origins — New South Wales **853,559** and New Zealand **198,348** in
1894 alone, against a national total of 1,062,074.

Infinity's copy in `as_1898` has the same shape, boundary at 21510 by the same
test, and is the **sole carrier of 1894**.

Anchors were checked first and are all tier A and consistent. The origin blocks
were never wrong; only their extent was.

## Result

```
1894 2.5638 -> 1.000000    1895 2.5229 -> 1.000000    1896 2.0024 -> 1.000000
1897 1.9739 -> 1.000316    1898 1.6829 -> 1.000000    1899 1.7218 -> 0.999981

exact01 2,808 -> 2,814 ; within 0.1% GBP 53.0% -> 53.1% ; within 5% 70.4% -> 70.5%
over 213 -> 207 ; nodata UNCHANGED ; denominator UNCHANGED at 9,940
```

`diffcells.py`: **exactly six cells change class**, all of them glucose.

## A near-miss worth recording: a supersede key can back two commodities

The first attempt also superseded `SUGAR | Glucose` for 1894-99. It closed the
same six cells — and **emptied `Sugar — Glucose` 1894 and 1896**, two cells that
had been exact, turning them into `nodata`.

`Sugar — Glucose` is a *separate payload commodity*: the same printed line under
the pre-1893 wording, carrying T1 for 1866-1896. The label I superseded was the
only thing feeding it.

> **Rule.** Before superseding a label, check which payload commodities it backs
> — not just the one being repaired. An era-worded sibling can be living on the
> same key, and superseding it is a silent deletion, not a correction.

Dropping that one supersede row left the six gains intact with `nodata`
unchanged. Net: **six cells gained, none lost.**

## Still open

- **`Glucose (Solid Or Liquid)` 1893, at 1.0662.** Same defect, and the fix is
  identified but blocked. The `as_1893 | SUGAR'd) | Glucose` block at seq
  3643-3648 closes: Germany 65,194 + Holland 3,102 + France 13,369 + **United
  States 1,152,985** + Other Foreign 1,200 = 1,235,850 against T1 **1,235,800**,
  and its row 3648 is the T1-matching TOTAL that marks the boundary. The
  payload's US cell instead carries **1,235,800 — the printed grand total** —
  from another source.
  Admitting the block requires superseding `SUGAR | Glucose` for 1893, which is
  exactly the key `Sugar — Glucose` lives on, and that commodity's 1893 cell is
  currently exact. **The two are the same printed line under two wordings, so
  this is the era-fold taxonomy question again** — the same decision already
  waiting on copper and woollen yarn. Not taken alone.
- The boundary rule is still unbuilt as a script. It has now paid for itself
  twice (tea's diagnosis, glucose's fix) and would have saved the manual tracing
  in caoutchouc and coffee 1880.
