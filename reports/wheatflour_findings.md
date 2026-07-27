# Wheat Meal or Flour: one multi-line US label, two failure modes, five years

Session 11, iteration 46 (2026-07-27). `Corn And Grain — Wheat Meal Or Flour`
was the top non-sugar item on the GBP-ranked board — **GBP 72.6M**, five
off-cells running **both ways**:

```
1883 1.309   1885 1.233   1886 0.899   1887 0.937   1889 1.234
```

Mixed over/under normally means two defects. Here it is **one** — the printed
table splits the United States by shipping coast, and the parser fails on that
multi-line label in two different ways depending on the volume.

## Variant 1 — the terminal bare-US row is a printed TOTAL (1883, 1885, 1889)

The block ends with a row labelled `United States of America` carrying a number
far too large to be a country. It is the printed subtotal, and the rows above it
prove it **to the digit**:

```
as_1885  Meal and Flour | Wheat Meal or Flour
  671-679  Russia..United States of America : Other Foreign Countries
           sum 15,417,241  ==  row 680 'United States of America'   EXACT
  681-684  British half                415,602  ==  printed TOTAL 685  EXACT
  686      grand 15,832,843  ==  T1

as_1889  675-685 sum 13,469,698  ==  row 686 'United States of America'  EXACT
         687-689 British  1,202,384  ==  printed TOTAL 690  EXACT
         691     grand 14,672,082  ==  T1

as_1883  row 642 'United States of America' 16,329,312  ==  T1 itself
         (no British subtotal printed; members 626-641 sum 16,326,012)
```

So the label the parser wrote is the **head of the US group that ran on into the
subtotal line**. Counting it as a country is the entire overage — and it also
suppresses the coast roll-up, which only synthesizes a parent for years the
parent lacks.

## Variant 2 — the US head row ate the Atlantic number (1886, 1887)

Here the sub-entry heads are gone and the labels have all slipped up one:

```
as_1886  670 'United States of America'  9,948,250
         671 'On the Atlantic'           1,477,001
         672 'On the Pacific'               11,300
         673 'Argentine Republic'           13,552
         674 TOTAL                      13,842,553   <- members close EXACTLY
```

`fold_country` maps bare `on the atlantic` / `on the pacific` to
`United States Of America (Atlantic)` / `(Pacific)` — **paren drill-down cells,
which the reconcile excludes** — while the bare parent beside them is itself
only the Atlantic figure. That is the whole shortfall, to the digit:

```
1886  14,689,560 - (1,477,001 + 11,300)  = 13,201,259   = the observed 0.8987
1887  18,063,234 - (1,124,551 +  9,707)  = 16,928,976   = the observed 0.9372
```

**The slip reading is fixed by two independent series across four years**, not by
one guess:

| | 1885 | 1886 | 1887 | 1889 |
|---|---|---|---|---|
| Pacific | 1,559,054 | 1,477,001 | 1,124,551 | 1,321,320 |
| Other Foreign | 23,098 | 11,300 | 9,707 | 15,316 |

Reading 1886 *without* the slip would put its Atlantic at 1,477,001 against
10,172,849 in 1885 and 8,722,400 in 1889.

**The sum is invariant to the relabel** — all three rows are members either way,
and 1886's members close on the printed foreign TOTAL 13,842,553 exactly. Only
the country attribution changes, which is why the relabel is safe to make on
series evidence.

## The repair

18 `group_repairs` rows. Ranges skip the phantom subtotal rows; three per-row
`new_country` overrides each for 1886 (seq 670/671/672) and 1887 (667/668/669);
`new_unit=Cwts.` throughout, which also heals 1883's Turkey 6,423, Belgium 3,017
and Other Countries 5,576 out of unit `?`.

`V.sig('MEAL AND FLOUR Wheat Meal or Flour') == V.sig('Wheat Meal or Flour') ==
('flour','meal','wheat')`, so the re-admitted rows land on the same commodity as
the consensus rows they replace.

### The trap: a supersede must cover ALL THREE engines, and step order matters

The first attempt used 15 rows and moved only 1883, 1886 and 1887.

- **1885 and 1889 did not move at all.** Infinity carries the *identical* block
  under its own stale label — `CORN, GRAIN, MEAL, and FLOUR` (as_1885 rows
  558-573) and `Corn and Grain` (as_1889 rows 536-552) — phantom subtotal
  included, and re-admitted it as `source=infonly`.
- **1883 landed at 0.9992 instead of 0.999798.** Two-up is **step 3** and group
  repairs are **step 6**, so once the consensus copy was superseded the two-up
  copy — under a *third* label, `CORN, GRAIN, MEAL, AND FLOUR` — claimed every
  country first, **without units**. The payload unit-heal rescued most of them
  but left Turkey 6,423 and Belgium 3,017 at `?`: exactly the 9,440 shortfall.

Three more supersede-only rows closed all three.

> **Rule.** Before superseding, list the label in **`country_year_consensus`**,
> **`country_obs_inf`** *and* **`exports/twoup_country.csv`**. Superseding a
> consensus label does not remove the block — it hands it to whichever earlier
> step still has a copy, and the earlier steps carry weaker units. This is the
> third axis of the same failure surface, after casing (iteration 35) and
> whitespace (iteration 44).

## Result

```
1883  1.3087 -> 0.999798        1885  1.2328 -> 1.000000
1886  0.8987 -> 1.000000        1887  0.9372 -> 0.999983
1889  1.2335 -> 1.000000

exact01 2,773 -> 2,778 ; within 0.1% GBP 50.4% -> 50.9% ; within 5% 68.2% -> 68.7%
over 220 -> 217 ; under 256 -> 254 ; denominator UNCHANGED at 9,940
```

`diffcells.py` confirms **exactly five cells change class**, and they are these
five.

## Still open

- **1883 is 3,300 short on quantity and 33 short on value** against its own
  printed total (16,326,012 / 12,344,745 against 16,329,312 / 12,344,778). Both
  columns short by different proportions, so it is one small misread rather than
  a dropped row. Not guessed.
- **1887's foreign half is 300 short** (17,091,045 against printed 17,091,345).
  Same character.
- The **variant-2 signature is worth sweeping for**: a bare
  `United States of America` cell immediately followed by de-headed
  `On the Atlantic` / `On the Pacific` rows, in any commodity. It reads as an
  *under* because the reconcile excludes paren drill-downs, so no over-count
  detector sees it.
