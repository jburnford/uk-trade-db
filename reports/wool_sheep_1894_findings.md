# Wool — Sheep or Lambs' 1894: the origins were right and the anchor was wrong

Session 11, iteration 51 (2026-07-27). `Wool — Sheep Or Lambs'` 1894 read
**0.909** — one cell, but **GBP 29.3M**, the highest per-cell exposure left on
the board. Thirty-two of its thirty-three Tier-1 years were already fine.

It was never a missing-origin problem.

## The origin table closes on its own printed halves

`as_1894 | Wool | Sheep or Lambs'`, seq 3949-3987:

```
foreign  members 81,374,098   printed TOTAL  81,374,188    (90 short)
British  members 619,173,044  printed TOTAL 619,176,074    (3,030 short)
                 81,374,188 + 619,176,074 = 700,550,262 = the printed grand row
```

The anchor said **799,559,262**. The two figures differ in exactly three digit
positions, **all 0 for 9**.

## Seven printings say 700,550,262; two say otherwise, and they are one volume

```
as_1894  700,550,262      as_1895  700,550,262      as_1896  700,550,262
as_1897  700,550,262      tn_1895  700,550,262
as_1898  799,559,262      tn_1899  799,559,262
```

`tn_1899` mirrors `as_1898` row for row — same corrupted unit (a ditto mark `„`
where the others print `Lbs.`), and the same value cell reading **24,791,169**
where every other volume reads **24,791,160**. The same 0→9 failure, in the same
row, in both columns.

## Why the vote lost it

The readings are split across **four different label spellings**, and the vote is
per label key:

```
key  "Sheep or Lambs' Wool"   as_1897 700,550,262 | as_1898, tn_1899 799,559,262
                              -> 2 votes beat 1, tier B, 799,559,262
key  "Sheep and Lambs'"       the other four volumes' wool readings sat here,
                              and the key's vote was won by 484,597 —
                              the LIVESTOCK figure
```

So inside the winning key it really was 2 against 1, and the four contemporary
readings that would have settled it were parked under a key whose vote went to a
number from a different commodity. This is [[vote-tiebreak-lone-reprint]] with an
extra twist: **the label split is what made the reprint a majority.**

## The fix

One row in `reference/manual_t1.csv` — the established page-adjudication
vocabulary, applied *after* the vote rather than changing it, and the fourth
entry of exactly this kind (silk 1884, yeast 1880, bottles 1899 all carry the
same "closure outranks print-majority" reasoning). Here closure and the print
majority **agree**; only the vote's label bookkeeping disagreed.

`reconcile.py` was re-run to rebuild `consensus`. Verified idempotent: the new
table has the same 51,268 series-years and **zero rows differ from the
pre-change snapshot** apart from the overridden one, which is now
`700,550,262`, tier A, `volumes = as_1897,as_1898,tn_1899,manual`.

## Result

```
1894  0.908513 -> 1.000136    EXACT

exact01 2,790 -> 2,791 ; within 0.1% GBP 51.8% -> 52.0% ; within 5% 69.8% -> 70.0%
under 240 -> 239 ; denominator UNCHANGED at 9,940
```

`diffcells.py`: **exactly one cell changes class.**

### A second-order effect worth knowing

The origin sum for the year *also* moved, 726.4M → 700.6M, without any origin
data changing. `build_viz_payload`'s aggregate-beside-members and coast/port
sibling folds only collapse a duplicate aggregate **when doing so brings the year
closer to its printed national total**. With the inflated anchor, keeping the
`British Possessions In South Africa` 9,661,265 aggregate *beside* its Cape
55,126,493 and Natal 15,459,100 members looked like an improvement, so ~26M of
double-counted aggregates were retained. Correcting the anchor let the payload's
own de-duplication do its job.

> **A wrong anchor does not merely misscore a year — it misleads every
> anchor-guided fold in the payload build.** Fix the anchor before judging the
> origin side.

## Still open

- The remaining **+95,364 (0.014%)** is the extras this commodity picks up from
  other volumes' copies of the same table. Well inside 0.1%; not chased.
- The label-split mechanism above is worth a detector: a Tier-1 series whose
  readings scatter across several article spellings, where one spelling's vote is
  won by a figure belonging to a *different* commodity (here 484,597 sheep).
  `anchor_disagreement.py` compares readings within a key; nothing compares
  across the keys a fuzzy-merge later unites.
