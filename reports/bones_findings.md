# Bones for manufacturing 1892-94: three stale heads, and a two-up page that rules out a range repair

Worked 2026-08-02 (`/loop /next-defect`), bracketed-gap rank 3, GBP 480k.
**All three years went from `nodata` to `exact01`.**

**exact01 3,569 → 3,572 (+3), nodata 4,291 → 4,288, denominator held at 9,464.
Zero regressions.**

| year | result |
|---|---|
| 1892 | **10,476 / 10,476 = 1.000000** |
| 1893 | 5,046 / 5,049 = **0.99941** |
| 1894 | **7,926 / 7,926 = 1.000000** |

## All three were parsed — the article right, the group stale

| volume | filed under |
|---|---|
| as_1892 | `BONES (except Whalebone) \| Applicable to Manufacturing Purposes` |
| as_1893 | `BEADS OF ALL SORTS \| Applicable to Manufacturing Purposes` |
| as_1894 | `BEADS OF ALL SORTS \| Applicable to Manufacturing Purposes` |
| Infinity 1892-93 | `BEEF \| Applicable to Manufacturing Purposes` |

## Why a seq-range repair was the wrong instrument

**The page is two-up, and the parser gives both columns' rows the same
`row_seq`.** `as_1892` seq 235 carries *France 792* (bones) **and** *France
38,818* (beads of all sorts); seq 236 carries USA 1,819 and Java 2,091,411. A
`group_repairs` range over 235-242 would have dragged the beads table into the
bones commodity.

**That is a general constraint worth carrying: on a two-up page, seq ranges do
not separate the columns, so `manual_rows` is the instrument, not
`group_repairs`.**

## The arithmetic

**1892 closes on both columns.** Foreign 792 + 1,819 + 6,072 + 835 = **9,518** =
the printed foreign Total; British 633 + 325 = **958** = the printed British
Total; **9,518 + 958 = 10,476 = the Tier-1**; values **76,355** = the printed
grand value Total.

The British half needed the raw: **that column prints its labels above their
numbers**, so `From Australasia` takes 633/6,701 and `Other British Possessions`
325/1,034 — the same one-row offset found on the as_1882 hardwoods page.

**1894 closes on the quantity column**: 6,951 foreign + 975 British = **7,926 =
the Tier-1**. Its **value** column does not — the five foreign values sum to
47,728 against a printed 47,668, **60 over**. Recorded, not adjusted; the
commodity's modal unit is Tons, so the metric reads quantities. *(That mismatch
was caught by an assertion before anything was written, which is why the first
attempt aborted cleanly.)*

**1893 is three tons short and the three are deliberately not guessed.** The
value column closes exactly (foreign 28,130, grand 33,899), proving the member
list complete — but **seven different single-digit repairs each close the
quantity column**, and the unit-price band separates none of them: adding 3
moves every member's price by under 2%. Per the rule set on alpaca wool and
exercised on saltpetre, the arithmetic is exhausted and the residual is queued.
The year reads 0.99941 — `exact01` regardless.

## Still open

1889, 1890, 1897, 1898, 1899 and 1900 are `nodata`; and the family is scattered
across a dozen further nodes (`Bones (Except Whalebone) Whether Burnt Or Not…`,
`Beads Of All Sorts — Bones (Except Whalefins)…`, `Beer And Ale — Bones…`) that
look like the same line under stale heads and OCR variants.
