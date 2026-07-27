# Tea: DIAGNOSED, NOT CLOSED — and the rule that finds the block boundary

Session 11, iteration 56 (2026-07-27). `Tea` — **GBP 18.6M**, two off-cells:

```
1894  0.931        1896  1.242
```

**Neither closes. Nothing was applied; baseline unchanged.** Both anchors are
sound (1894 tier A on seven volumes, 1896 tier A on six), so this is entirely
origin-side — and it is the third item this session where **one label spans
several printed tables**.

## What the `TEA` label actually covers

In `as_1896`, `TEA` with a NULL article runs seq 280-532 and contains, in order:

| seq | table |
|---|---|
| 280-289 | **the tea import origin table** |
| 290-294 | a by-sort consumption table (BEI / Ceylon / China / Other, TOTAL 227,785,500) |
| 295-314 | **TOBACCO, Unmanufactured** — imports |
| 315-330+ | another commodity again |
| 356-532 | **WINE** — `Red, in Casks`, `White, in Bottles: Sparkling : Champagne`, `Moselle`, `Burgundy`, `Total of all Kinds` |

The payload's `united states of america` **74,163,042** for tea comes from seq
305 — and it is **tobacco**, proven outright: four other volumes carry that exact
figure under `TOBACCO | Unmanufactured` for 1896 (`as_1897` 27463, `as_1898`
27105, `as_1899` 27078, plus Infinity's copies).

The `Total` sub-article is no better: in `as_1894` it is the **re-export** table
(printed grand 31,894,171 against imports of 244,310,500), and in `as_1896` the
same re-export table is parsed **six times over** — rows 2329-2436 are six
identical copies of the same seventeen rows.

## The rule that finds the boundary

The tea import table's own arithmetic marks exactly where it stops:

```
280-287  members            226,364,732
288      'British East Indies'  226,364,682   <- printed section total (50 out)
289      'TOTAL'               265,394,122   <- EQUALS T1 EXACTLY
290      the next table starts
```

> **A `TOTAL` row whose quantity equals the commodity-year's Tier-1 figure is the
> END of the block.** Everything after it belongs to another printed table.

This is worth building as a detector. It is cheap — one pass over `country_obs`
joined to `consensus` — and it would have found the boundary in **caoutchouc**
(iteration 49, four tables under one label), in **coffee 1880** (iteration 54, a
whole multi-commodity duty page), and here, without any of the manual tracing
those took. The same scan also names the *stale-label* blocks worth repairing,
because a label whose seq range contains **more than one** T1-matching TOTAL is
by definition covering more than one commodity.

## Why nothing was applied

Admitting only rows 280-287 for 1896 gives 226,364,732 against T1 265,394,122 —
**0.853, under**. The foreign half (≈39,029,440 = 265,394,122 − 226,364,682) is
not in that range and has not been located; the payload's China 31,115,707 is
import-scale and comes from somewhere else again. So the correct partial repair
would move 1896 from 1.242 over to 0.853 under without closing it, and would make
the eventual full repair harder to reason about — the same call as caoutchouc
(iteration 49) and cured fish 1897-99 (iteration 53).

1894 is the mirror problem: its country list looks entirely plausible (Bengal
116.1M, Ceylon 71.6M, China 23.0M) and is simply **16,896,070 short**. No junk to
remove — a block is missing.

## Still open

- **`Tea` 1894 and 1896**, both of them. The route in is the boundary rule above:
  find every `TOTAL` row equal to T1 inside the `TEA` label's seq range, in
  `as_1894`, `as_1896`, and the `as_1898`/`as_1899` comparatives (seq 26923-27049
  and 26900-27023), then admit the tea segments and supersede the rest.
- **Tea is now the third caoutchouc-class item** (with caoutchouc itself and the
  cured-fish 1897-99 block). All three are one stale label over many tables, and
  all three are too large for a single defect-loop slot. They want a dedicated
  pass built around the boundary detector rather than one commodity at a time.
- Two smaller things visible in 1896 and worth folding into that pass: a
  duplicate pair `Bombay And Schinde` / `Bombay` both at 528,980, and two
  separate `china` cells (31,115,707 and 19,831,678) from different tables.
