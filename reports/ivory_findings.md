# Ivory: six years, six mechanisms, and a 2178x that was two fused rows

Session 11, iteration 48 (2026-07-27). `Teeth, Elephants', Sea Cow, And Sea
Horse` — **GBP 45.5M**, six off-cells, top of the re-ranked board after the two
taxonomy-blocked sugar items:

```
1873 0.673   1874 0.645   1875 0.892   1878 0.942   1880 0.668   1881 2178.261
```

**All six now close EXACTLY.** `exact01` 2,780 → **2,786**, within 0.1% GBP
**51.3% → 51.6%**, within 5% 69.2% → 69.5%, `under` 252 → 247, `over` 216 → 215,
denominator unchanged at 9,940. `diffcells.py`: **exactly six cells change
class**, and all six land on 1.0000.

## Two things run through the whole series

### 1. A re-export table wearing the commodity's own name

The re-exports are printed under `TEETH | Elephants', Sea Cow, and Sea Horse` —
the commodity's name with **no export wording anywhere in the label** — and the
two-up parse delivers them straight into the import payload. In 1873 that is
France 1,673, United States 622 and Other Countries 327 sitting beside three
real import origins. The blocks' own printed totals give them away: **7,930
(1874), 7,546 (1875), 7,640 (1881)** against national imports of 13,365, 16,258
and 12,377.

The gap-fill export guard (which rejected 4,385 cells in 437 blocks this run)
never sees them, because it keys on export wording the label does not carry.

> **Signature worth sweeping for:** a two-up block whose group is the bare
> commodity noun and whose article is the rest of the printed line, sitting
> beside a consensus block under a *stale* group. The re-export table keeps the
> real name; the import table is the one that got glued to `TAR`.

### 2. Infinity holds the closing copy in four of the six years

| year | Chandra | Infinity |
|---|---|---|
| 1873 | 3 rows only (Germany, Malta, Egypt) | 11 members = **13,385 = T1 EXACT** |
| 1874 | members 13,333 v printed 13,365 | differs on two rows, **13,365 EXACT** |
| 1875 | 15,577 — **lost the final `Other Countries` 681** | **16,258 EXACT** |
| 1880 | closes, but stamped unit **`Cyts`** | same numbers, unit `Cwts` |
| 1878 | **correct** (11 members + the eaten label) | label-slipped in the tail |
| 1881 | the only copy; two rows fused digit-wise | import table absent (export only) |

1874's two differences are `Not particularly designated` 1,958 for 1,956 and
`British Possessions in South Africa` 1,548 for 1,518 — 32 in total, which is
exactly what Chandra is short.

## 1880 — a unit alias, fixed without touching the code

Both engines read the same twelve members and they close on the printed 13,435
to the digit. Chandra stamped the unit **`Cyts`**, an OCR variant `norm_unit`
does not fold (it folds `Cuts` and `Ccts` but not this), so every cell fell out
of the Cwt sum. `Cyts` occurs **18 times in the whole corpus, 12 of them in this
one block**, so admitting Infinity's `Cwts` copy fixes the year without a
corpus-wide alias change.

## 1878 — the "TOTAL" that was the last member

Row 1723 parses as `TOTAL` 856. The printed grand total is 14,635, and Chandra's
eleven members sum **13,779**:

```
13,779 + 856 = 14,635 = T1   EXACTLY
```

So 856 is the last *member*, whose label the parser ate — the same shape as the
wine summary tables and the cotton piece-goods exports. `Other Countries` is the
row in that slot in 1879 (1,091) and 1880 (1,267), and 856 sits in that range.
Here **Chandra is right and Infinity is wrong**: Infinity fuses `Bombay and
Scinde` with `Bengal and Burmah` and then calls Bengal's 134 `Other Countries`.

## 1881 — the 2178x was two rows fused digit-wise

`other countries` read **25,711,341** against a national total of **12,377**.
Row 1584's label is itself two labels run together — `West Africa: Portuguese
Possessions` + `Not particularly design-nated`, printed as separate rows in
1875, 1878 and 1879 — and the numbers ran together the same way:

```
row 1584   quantity "1243698"      ->  1,243 | 698
           value    "4664028629"   ->  46,640 | 28,629     (same boundary)
row 1591   quantity "25711341"     ->  2,571 | 1,341
           value    "12024356575"  ->  120,243 | 56,575    (46.8 and 42.2 GBP/cwt,
                                        inside the block's 40.9-52.5 range)
```

This is not a subset-sum search. Row 1584 has six possible splits and row 1591
has seven; **exactly one pair of them — (1,941), (3,912) — hits the residual the
printed total demands**, and the quantity column then closes to the digit:

```
333 + 1,243 + 698 + 2,155 + 1,118 + 547 + 595 + 550 + 1,226 + 2,571 + 1,341
  = 12,377 = printed TOTAL = T1
```

The value column corroborates the first row's boundary independently and lands
within 3 on the second.

**One label is not recoverable.** The 1,341 half of row 1591 is `Other
Countries` (1,091 in 1879, 1,267 in 1880); the **2,571 half sits between British
East Indies and Other Countries and cannot be named without the page**. It is
booked into the `Other Countries` cell as a single 3,912 rather than given an
invented label. The arithmetic closes either way; only that attribution is open,
and it is flagged in the manual_rows note.

## Still open

- **`Teeth, Elephants', Sea Cow, And Sea Horse` 1881** — the identity of the
  2,571 row. Page-image call; the quantity is not lost, only mis-attributed
  inside `Other Countries`.
- **The other half of the family is untouched.** `Teeth, Elephants', Sea-Cow,
  Sea-Horse, Or Sea-Morse` (the post-1893 wording, **GBP 32.3M**) still reads
  0.594 / 0.452 / 0.850 / 0.592 / 0.527 / 0.515 / 0.618 across 1893-99 — a
  consistent ~half, which usually means one printed half of the table is
  missing. Not worked here.
- **Folding the two wordings into one commodity is a taxonomy change** and was
  deliberately not attempted. They are the same printed line under an era
  re-wording — the same question as the copper and woollen-yarn folds already
  waiting on a decision.
- The export-leakage signature above should be swept for corpus-wide;
  `detect_export_leakage.py` exists but did not catch this shape.
