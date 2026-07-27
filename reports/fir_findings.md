# Fir timber — three tables under one label, and a whitespace spelling split

`Wood And Timber — Sawn Or Split, Planed Or Dressed, Fir` read **0.932 (1898)**
and **0.939 (1899)** — about 6.5% short on a **GBP 193M** commodity, the top of
the GBP-ranked list of remaining off-cells.

## Not a missing country — a wrong one

The as_1899 label covers **three consecutive fir tables**: the main one and two
smaller `Unenumerated` variants, five years interleaved by `row_seq`. The
payload was mixing them. It took the variants' United States rows —

```
13,374 + 58,207 + 10,347 = 81,928
```

— **instead of** the main table's `United States of America : On the Atlantic`
at **469,401**. That single substitution is the entire shortfall.

The main table is **seq 22853-22954** (22853 is 1895's `Russia`, 22954 the 1899
grand `TOTAL`, 22955 starts the first variant), and it closes on its own printed
totals:

```
1899   foreign 4,678,314 + British 1,781,658 = 6,459,972 = T1 to the digit
       (the country rows sum 6,459,272 — 700 short)
1898   grand TOTAL 6,204,787 = T1 to the digit
```

Only **1898 and 1899** are superseded. 1895, 1896 and 1897 under this label feed
other payload commodities, so their consensus rows are left in place and the
re-admission skips them via `consensus_triples_ga`.

## Two rows were needed: whitespace makes a separate supersede key

`country_obs` spells this article three ways:

```
as_1897   'Sawn or Split, planed or dressed, Fir'
as_1898   'Sawn or Split, planed or dressed, Fir'
as_1899   'Sawn or Split, planed or dressed,     Fir'      <- five spaces
```

`supersede` matches the **literal** article string. Superseding the as_1899
spelling left the as_1897/as_1898 consensus copies alive, and **1898 came back
at 1.009 — over by 55,934**: the variant tables' `on the atlantic` 41,310 and
`united states of america` 12,003 sitting beside the main table's sub-entries
that the repair had just admitted.

A second **supersede-only row (`seq 0-0`)** on the single-space spelling, year
1898 only, fixes it.

**Rule: before superseding, run `SELECT DISTINCT volume, article_group, article`
for the label. Whitespace variants are separate supersede keys.** This is the
sibling of the casing rule (`country_obs` spelling, never
`country_year_final`'s) — same failure surface, different axis.

## Result

```
1898  0.9317 -> 1.0000        1899  0.9389 -> 0.9999
```

`exact01` **2,770 → 2,772**, `under` GBP-weighted 4.9% → **3.3%**, and **within
0.1% GBP-weighted 48.6% → 50.2%** — a 1.6 point jump that takes the corpus past
half. Two cells move and nothing else.

## Still open

- **`SUGAR | Sawn or Split, Planed or Dressed, Unenumerated`** (`source=infonly`,
  1898) is the fir `Unenumerated` variant filed under a stale `SUGAR` group —
  USA 120,011, Canada 38,285, Russia 32,180, France 12,903, Norway 10,768,
  Sweden 10,696, Holland 7,073, Germany 2,802, Other British 274. Wrong home,
  but a different signature, so it does not touch this commodity. Unworked.
- **1900 is `nodata`** for this commodity (T1 6,401,636).
- The 700-load residual inside the 1899 block (components 6,459,272 against the
  printed 6,459,972).
