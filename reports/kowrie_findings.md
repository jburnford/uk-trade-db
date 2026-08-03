# Kowrie 1875-76: a one-letter article garble, and a shadow that is not worth folding

Worked 2026-08-02 (`/loop /next-defect`), bracketed-gap rank 3, GBP 453k.
**Both years went from `nodata` to exactly 1.000000** — 34,730 and 38,200 Cwt.

**exact01 3,574 → 3,576 (+2), nodata 4,286 → 4,284, denominator held at 9,464.
Zero regressions.**

## Both years close on both printed columns

| year | members | Tier-1 | values | printed |
|---|---|---|---|---|
| 1875 | 8,168 + 26,261 + 301 = **34,730** | **34,730** | 22,212 + 67,867 + 785 = **90,864** | **90,864** |
| 1876 | 1,678 + 36,514 + 8 = **38,200** | **38,200** | 5,685 + 90,673 + 30 = **96,388** | **96,388** |

1875 is United States, Australia, Other Countries; 1876 is United States, New
Zealand, Other Countries — a kauri-gum import profile, which is what it should
be.

## Why 1875 was invisible: a one-letter article garble

**Chandra OCR'd the article as `Kowzie`** — z for r — so no kowrie block could
be produced from its parse by any label-based route. Its page also carries the
**label-above-numbers offset**. Infinity ran the whole block into a single cell.

**The two agree member for member once Chandra's offset is applied**, which is
the confirmation: Infinity's run-in text reads `From United States of America
8,168 22,212 ,, Australia 26,261 67,867 ,, Other Countries 301 785 Total 34,730
90,864`.

**A single mangled letter in the ARTICLE removes a block from every label-based
screen** — the signature has no near-match, so neither `match_by_name` nor the
era/spelling folds can reach it. Only the arithmetic and the raw text can.

## A shadow that is *not* a folding opportunity

`Gum : Kowrie` looks like a spelling/era sibling, and after coco-nut and sumach
it is tempting. **It is not: it is a pure anchor shadow — nine Tier-1 years and
zero country data in any of them.** Folding it would add anchors, not origins,
and would enlarge the denominator for nothing.

**Worth carrying: before treating a sibling as a fold candidate, check it
actually holds origins.** The coco-nut and sumach folds paid because each shadow
carried years the target lacked; this one carries none.

## Still open

1868-1871, 1882-1884 and 1900 are `nodata`; 1887 reads 0.9456 and 1893 1.0158.
