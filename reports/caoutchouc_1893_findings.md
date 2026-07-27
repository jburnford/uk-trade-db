# Caoutchouc 1893-99: the detector found a clean block the hand trace never saw

Session 11, iteration 59 (2026-07-27). `Caoutchouc` came back into the loop
because iteration 58 built the boundary detector. All seven 1893-99 cells move
out of `over`/`under`:

```
1893 1.0881 -> 0.9677    1894 1.2106 -> 0.9969    1895 1.4064 -> 0.9955
1896 1.1693 -> 0.9902    1897 1.0654 -> 0.9871    1898 1.1174 -> 0.9789
1899 0.9430 -> 0.9818
```

**Not closed** — all seven land in `within5`, 0.5-3.3% short. `exact01` is
unchanged at 2,814, but `over` falls 207 → **201**, `under` 232 → 231, within-5%
GBP 70.5% → **70.7%**, and GBP-weighted `over` 3.0% → 2.9%.

## What the detector added

Iteration 49 traced the `as_1898` copy by hand, found its label covering four
tables, and stopped — because that block's grand-total rows carry the **wrong
year labels** (values in printed column order, years running 1894, 1896, 1897,
1898, 1895), so it has no clean boundary. The detector was pointed at the same
commodity and returned something the hand trace never looked at:

```
as_1897 | CAOUTCHouc | Eastern Coast of Africa   seq 1828-2002
         boundary 2002 == seq_max, ZERO rows after, years 1893-97
as_1899 | CAOUTCHOUC | Eastern Coast of Africa   seq 1791-1968  (Infinity)
         boundary 1968 == seq_max, ZERO rows after, years 1895-99
as_1898 | CAOUTCHOUCC | Eastern Coast of Africa  seq 1808-2131
         boundary 1976, 155 rows after            <- the one traced by hand
```

Two clean blocks, ranked against the dirty one, in a single query. Their printed
halves reproduce T1 exactly: 237,957 + 103,596 = 341,553 (1895),
309,291 + 121,857 = 431,148 (1896), 272,872 + 124,057 = 396,929 (1897).

## The printed table is split across two parser labels

Admitting the `Eastern Coast of Africa` half alone leaves every year at **0.81**.
The foreign *head* — Russia : Northern Ports, Germany, Holland, Belgium, France,
Portugal, Turkey European and the five Western Coast of Africa sub-entries — sits
under the **NULL article** of the same group, seq 1768-1827 in `as_1897` and
1721-1790 in `as_1899`'s Infinity copy. For 1895 the head is worth **61,531**,
which is exactly the 19% the tail was missing.

> The detector names the label's *end*. It does not tell you the block also has a
> **head** under a different article of the same group. Check the rows
> immediately before `seq_min` before trusting a range.

`as_1899`'s Infinity head needed a hand-set lower bound too: that same label also
covers seq 5-181, a re-export table with its own totals.

## The trap that cost a rebuild: FIVE OCR spellings of one group

The first attempt superseded `CAOUTCHouc` and moved **one** cell. `supersede`
keys the literal group string, and the vote had spread the year across five:

```
CAOUTCHOUCC  170 consensus rows      CAOUTCHOUIC  135
CAOUTCHOUC   131                     CAOUTCHOUQ    17
CAOUTCHOUUC   12
```

With four of them alive, `consensus_triples_ga` blocked the groupfix rows and
only 5 of ~70 landed.

> **This is the OCR-SPELLING axis of the supersede key** — sibling to the casing
> rule (iteration 35), the whitespace rule (44) and the both-engines rule (46).
> Before superseding, run `SELECT DISTINCT upper(article_group), article` over
> `country_year_consensus` for the years in scope. `Manufactures of` is a
> different commodity and was deliberately left alone.

## Still open

- **All seven years, 0.5-3.3% short.** 1893 is worst at 0.9677 (short 9,470);
  1895 sits at 0.9955 where the hand arithmetic on the two admitted halves
  predicts 0.99956, so roughly 1,400 cwt is still going missing somewhere
  between the block and the payload. That gap is now small-scale — dropped or
  misread individual rows — and is a different problem from the four-table glue
  this iteration removed.
- **1872, 1878, 1882, 1885, 1886, 1887** are untouched (0.067 to 1.107). The
  detector reports every caoutchouc label in those volumes as clean
  (`rows_after` = 0), so their defects are *not* stale-label glue and want a
  separate look.
