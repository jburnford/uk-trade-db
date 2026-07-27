# Cotton — Raw: the coast roll-up doubles a duplicated printed row

Session 11, iteration 45 (2026-07-27). Picked by re-ranking every remaining
off-cell by GBP exposure: `Cotton — Raw` carries **GBP 36.3M per commodity-year**,
the highest per-cell weight left on the board, with two cells off —
**1897 at 1.801** and **1874 at 1.065**.

`Sugar — Unrefined, Total` (GBP 81.9M over 6 cells) ranks higher in total but
its Total-vs-sub-sort overlap *is* the deferred sugar-taxonomy item, which the
loop is not allowed to decide alone.

## 1897 — CLOSED, 1.8006 -> 0.999998

### The same printed row, counted twice, then doubled again by the roll-up

`country_year_final` carries one printed cell under two country spellings:

```
COTTON,Raw,on the atlantic,                              Cwts ,1897,12323090,consensus
COTTON,Raw,United States of America : On the Atlantic,   Cwts.,1897,12323090,groupfix
```

The first is as_1897's own reading after the vote stripped the head off the
sub-entry label; the second is the headed form that group_repairs line 12 (the
as_1899 `CORDAGE|Raw` 1895-99 comparative) supplies. `fold_country` maps **both**
to `United States Of America (Atlantic)`.

`build_viz_payload.py` has a per-year dedupe (line 1209) that would collapse
them — but **the coast roll-up at line ~580 runs first**, and it synthesizes the
bare parent `United States Of America` as the *sum* of its coast cells:

```
12,323,090 x 2 = 24,646,180
```

That one synthesized parent is the entire overage. The dedupe then tidies
`(Atlantic)` back to a single cell, so the finished payload shows a parent
exactly twice its own only child — and nothing downstream flags it, because a
parent larger than its drill-downs is the normal case.

```
payload sum 27,718,288 - 12,323,090 = 15,395,198   v T1 15,394,289
```

### The shape occurs exactly ONCE in the corpus

Scanning all **115,066** `country_year_final` rows for a bare coast label
(`on the atlantic`, `on the pacific`, `atlantic`, `pacific`) sitting beside a
headed `... : On the Atlantic/Pacific` sub-entry with an **identical quantity**
in the same group / article / unit / year / flow returns **one pair** — this
one. So the right response is a data repair, not a re-ordering of the payload
build. (Re-ordering would be defensible on its own merits; it is not worth a
corpus-wide vote-adjacent change to fix a single cell.)

### The fix, and why the year goes to the as_1899 block

A supersede-only `group_repairs` row (`seq 0-0`, `COTTON|Raw`,
`supersede_years=1897`). The consensus copy drops; the as_1899 groupfix block —
already relabelled to `COTTON|Raw` — refills all 29 rows, because the supersede
`continue` at `integrate_sources.py:213` runs *before* `consensus_triples.add`,
so the groupfix gate at :634 no longer blocks them.

Checks run before superseding, per the standing rules:

- `SELECT DISTINCT article_group, article` for 1897 returns a **single**
  `('COTTON','Raw')` spelling — no whitespace or casing twin (the iteration-44
  and iteration-35 traps).
- No `twoup`, `runin`, `manual` or `subentry` row exists for `COTTON|Raw` 1897;
  the year is consensus (25 rows) + groupfix (8) and nothing else.

**Closure decides which reading wins, not print majority.** The as_1899 block is
strictly better than as_1897's own on *both* printed subtotals:

| half | as_1899 members | as_1897 members | printed |
|---|---|---|---|
| British | 383,650 + 40 = **383,690 EXACT** | 383,651 (39 short) | 383,690 |
| Foreign | 15,010,569 (30 short) | 15,009,929 (670 short) | 15,010,599 |
| grand | **15,394,259** | 15,393,580 | T1 15,394,289 |

as_1897 is 39 short on the British half because it **fuses two printed rows**:
Canada 1,618 and Other British Possessions 40 arrive as a single
`Other British Possessions 1,658`. as_1899 prints them apart and closes to the
digit.

### Result

```
1897   1.8006 -> 0.999998
exact01 2,772 -> 2,773 ; within 0.1% GBP 50.2% -> 50.4% ; over GBP 4.2% -> 3.9%
denominator UNCHANGED at 9,940 commodity-years
```

`diffcells.py` confirms **exactly one cell changes class**, and it is this one.
The commodity's GBP weight falls 1,270.9M -> 1,200.3M — correct, and part of the
same defect: the duplicated row was doubling the **value** column too.

## 1874 — DOES NOT CLOSE. Queued with the evidence.

A different defect. There is no consensus copy at all: all 23 rows are
`groupfix` from group_repairs line 11 (as_1874 `Meal and Flour|Raw` 409-432,
the raw-cotton origin table under a stale group head).

**The block fails against its own printed totals, in opposite directions:**

```
quantity  members 14,907,735  v printed TOTAL 13,989,861   OVER  by 917,874
value     members 50,524,787  v printed TOTAL 50,696,496   SHORT by 171,709
```

So it is not a dropped row (that would leave both columns short).

### A second witness exists, and it does not settle it

Infinity carries the same table under a *different* stale group,
`as_1874 | Corn and Grain | Raw`, seq **431-455** — and it starts one row
earlier: **Germany 3,541 / 21,409, which Chandra's block is missing entirely.**

Engine disagreements (Chandra / Infinity):

| country | qty C | qty I | value C | value I |
|---|---|---|---|---|
| Egypt | 1,548,549 | 1,328,319 | 7,269,342 | 7,269,342 |
| Bombay and Scinde | 3,943,248 | 3,043,248 | 8,600,911 | 8,604,911 |
| Madras | 582,411 | 382,411 | 1,620,463 | 1,620,463 |
| New Granada | 73,151 | 7,151 | 225,498 | 227,495 |
| Brazil | 709,834 | 709,534 | 2,611,837 | 2,761,837 |
| Hayti | 4,783 | 1,783 | 17,224 | 17,224 |
| Australia | 25,284 | 23,254 | 126,742 | 126,742 |
| Holland | 6,715 | 6,715 | 18,466 | 15,466 |
| Belgium | 6,110 | 6,110 | 21,867 | 21,567 |
| Spain | 2,018 | 2,013 | 10,467 | 10,167 |
| China | 3,561 | 3,501 | 9,791 | 9,791 |
| TOTAL | 13,989,861 | 13,989,561 | 50,696,496 | 50,696,496 |

Infinity's own members sum **13,519,651** — 470,210 short of the printed total.

**Neither column can be closed by choosing between the two engines.** Taking
Infinity as the base, the available Infinity→Chandra quantity swaps are
+220,230 (Egypt), +900,000 (Bombay), +200,000 (Madras), +66,000 (New Granada),
+3,000 (Hayti), +2,030 (Australia), +300 (Brazil), +60 (China), +5 (Spain).
**No subset sums to the required +470,210** (the nearest, Egypt+Madras+New
Granada, overshoots by 16,020). The value column behaves the same way: Infinity
is +2,094 over printed and no subset of the value swaps reaches −2,094.

At least one country's true figure is therefore in **neither** engine, or the
printed total itself is misread. That is a page-image call, and this loop does
not guess digits.

Unit price is suggestive but is a within-block check only and settles nothing
on its own: the Indian grades cluster at 2.53-2.78 GBP/cwt (Bengal 2.53,
Ceylon 2.76), which fits Chandra's Madras (2.78, against Infinity's 4.24) and
Infinity's Bombay (2.83, against Chandra's 2.18) — i.e. it points at a
*different* engine for each of the two Indian rows.

### Still open

- **`Cotton — Raw` 1874** (ratio 1.065, GBP 36.3M) — as above. Needs the
  as_1874 page image. Both engine copies are named here, and Chandra's block is
  additionally **missing the Germany row** (3,541 / 21,409) whichever way the
  digits go.
- The 1897 block still has a **30-cwt foreign-half residual**, and it is
  pinned to one row. Holding as_1899's Italy 900 (as_1897 reads 200), the half
  comes to 15,010,569 with Peru at as_1899's 70,109 — **30 short** — and to
  15,010,629 with Peru at as_1897's 70,169 — **30 over**. The printed
  15,010,599 sits exactly between the two engines' Peru readings, so the true
  figure is 70,139 or the printed total's last digits are misread. One small
  misread, not a missing row; not guessed.
