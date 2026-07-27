# Ivory 1893-99: the British half of the table was invisible

Session 11, iteration 50 (2026-07-27). `Teeth, Elephants', Sea-Cow, Sea-Horse,
Or Sea-Morse` — the post-1893 wording of the line whose 1873-81 half closed in
iteration 48 — **GBP 32.3M**, seven off-cells, every one of them roughly a half:

```
1893 0.594   1894 0.452   1895 0.850   1896 0.592
1897 0.527   1898 0.515   1899 0.618
```

A consistent fraction across seven consecutive years is not seven misreads. The
payload's country list said what it was: **no Aden, no British East Indies, no
Zanzibar, no South Africa, no Malta in any year** — and those are the largest
rows in the 1870s prints of the same commodity. The entire
British-possessions half was missing.

## Cause — a phantom region article

Both comparative blocks are split in two by the parser:

```
as_1899  IVORY | Teeth, Elephants', Sea-cow, Sea-horse, or Sea-morse   11505-11566
         IVORY | Eastern Coast of Africa                               11567-11670
as_1897  IVORY | Teeth, Elephants', Sea-cow, Sea-horse, or Sea-morse   11413-11470
         IVORY | Eastern Coast of Africa                               11471-11570
```

The printed region head **`Eastern Coast of Africa`** is absorbed as the
**article**, so the second half of each block sigs to a different commodity
entirely and never reaches ivory. This is the class already recorded in
[[phantom-region-article]] — a region header eating the article name hides whole
table segments — here costing half of every year for seven years.

## The blocks' printed halves reproduce T1 exactly

Both blocks are trustworthy where it counts. Their foreign and British subtotals
sum to the Tier-1 figure to the digit, even where the printed *grand* row is a
misread:

```
as_1897   1893   6,376 + 3,642 = 10,018 = T1      (printed grand 10,918 — misread)
          1894   5,254 + 5,140 = 10,394 = T1      (printed grand 10,291 — misread)
as_1899   1897   6,251 + 4,037 = 10,288 = T1
          1898   5,794 + 4,203 = 10,002 = T1
          1899   6,015 + 3,024 =  9,039 …
```

1899's foreign subtotal reads **6,015 where the grand and the British half
require 6,915** — a 9→0 misread, and the third case in this family where the
*halves* are right and a printed total is not.

## The repair

Four block-admission rows (foreign half and British half of each volume) plus
two supersede-only rows for the other consensus spellings — `Teeth, Elephants',
Sea Cow, Sea Horse, or Sea Morse` and `Teeth, Elephants'. Sea Cow, Sea   Horse,
or Sea Morse` (full stop after the possessive, three-space run) — which are
separate supersede keys under the casing and whitespace rules.

The as_1899 rows are placed **before** the as_1897 rows so as_1899 wins the
overlapping years 1895-97, where it reads closer; as_1897 then fills 1893 and
1894, for which it is the only source, and contributes the countries as_1899
lacks in the shared years.

**A label trap worth keeping.** The first attempt set `new_group='TEETH'` with
the full label as `new_article`. The *sig* was right — `sig()` dedups tokens —
but `display()` does not, so the commodity was renamed
`Teeth — Teeth, Elephants', Sea-Cow, Sea-Horse, Or Sea-Morse` in the picker.
Putting the whole label in `new_group` with an **empty `new_article`** keeps both
the sig and the display string exactly as they were.

> **Rule.** When a repair supersedes every pre-existing copy of a label, the
> repair rows become the *most common printed rendering* and therefore set the
> display name. Check `display(fold_group(new_group), new_article)` before
> applying, not just `sig()`.

## Result

```
1893  0.5943 -> 0.999102   EXACT
1894  0.4518 -> 0.992881
1895  0.8501 -> 0.999175   EXACT
1896  0.5924 -> 0.997709
1897  0.5272 -> 1.000000   EXACT
1898  0.5150 -> 1.000000   EXACT
1899  0.6180 -> 0.993661

exact01 2,786 -> 2,790 ; within 0.1% GBP 51.6% -> 51.8% ; within 5% 69.5% -> 69.8%
under 247 -> 240 ; denominator UNCHANGED at 9,940
```

`diffcells.py`: **exactly seven cells change class**, and all seven leave `under`.

## Still open

- **Three small residuals**: 1894 short **74**, 1896 short **25**, 1899 short
  **63** against their Tier-1 figures. Each is well under 1% and each is a
  dropped or misread row inside a block whose own printed halves close — the
  same character as the 1883 wheat-flour and 1897 oats residuals. Not guessed.
- The two wordings of this printed line remain **two commodities**. Folding them
  is a taxonomy change and is still queued with the copper and woollen-yarn folds.
- The phantom-region-article signature is worth a sweep: `Eastern Coast of
  Africa`, `West Coast of Africa`, `West Africa` and `East Africa` all appear as
  ARTICLE values in `country_obs` for the 1893-99 volumes, across several
  commodities — caoutchouc among them (iteration 49).
