# Sumach 1890-92: the spelling-split floor, and why the fold direction mattered

Worked 2026-08-02 (`/loop /next-defect`), bracketed-gap rank 3, GBP 514k.
**User-approved taxonomy fold.**

**exact01 3,566 → 3,567 (+1), within 5% 1,113 → 1,112, nodata 4,297 → 4,293,
denominator 9,468 → 9,464 (−4, exactly as predicted). Zero regressions.**

| year | before | after |
|---|---|---|
| 1890 | *nodata* | **11,432 / 11,432 = 1.000000** |
| 1891 | *nodata* | **11,648 / 11,648 = 1.000000** |
| 1892 | *nodata* | **12,286 / 12,286 = 1.000000** |
| 1894 | *nodata* | **12,616 / 12,616 = 1.000000** |

## One line, two spellings

`Shumach` and `Sumach` carry the **identical Tier-1 in every year both hold one**
(1889 12,514; 1890 11,432; 1892 12,286), and between them cover 1866-1900 with
their origin tables in complementary years — `Shumach` holds 1872-1894,
`Sumach` holds 1889, 1893, 1895, 1896 and 1898.

**The only year both hold origins is 1889, and the two are byte-identical** —
Austrian Territories 319, France 210, Italy 11,920, Other Foreign 65 — the same
printed table parsed under both spellings, so the payload's
per-(country, unit, year) dedupe collapses it with no double count. Checked
before folding.

**No name-relation test can pair these**: `{SHUMACH}` and `{SUMACH}` share no
token. **This is the self-declared floor of the illusory-gap filter**, and it is
exactly why the ranked 1890-92 "holes" were never flagged as illusory even
though they close to the digit under the other spelling.

## The direction was the interesting decision

Folded **`Shumach` → `Sumach`**, not the reverse, for two reasons:

1. **`Sumach` is the correct spelling** and the one every other label in the
   corpus uses (`Dye Stuffs … — Sumach`, `Copper, Ore Of — Sumach`), so it should
   be the surviving display name.
2. **The two prints disagree on the 1891 anchor** — Shumach 11,618 against
   Sumach 11,648 — and **Shumach's own origins sum to 11,648**, proving 11,618
   the misread. A curation fold keeps the **target's** anchor for years both
   hold, so folding this way **settles 1891 by construction**.

That second point is worth generalising: **when two spellings of one line
disagree on an anchor, fold toward the spelling whose anchor the origins
support, and the disagreement resolves itself** — no `manual_t1` override, and
no `reconcile.py` re-run (which takes over two minutes and truncates
`consensus` if it is killed).

## The bookkeeping behind a +1

27 cells left `Shumach` (18 `exact01`, 6 `nodata`, 2 `within5`, 1 `under`) and 23
appeared in `Sumach` (15 `exact01`, 6 `nodata`, 1 `within5`, 1 `under`), plus the
four shared cells above moving `nodata` → `exact01`: **−18 + 15 + 4 = +1**.

## The commodity now

One continuous node, **35 Tier-1 years, 15 countries, GBP 5.13M**, exact through
1872-1896 bar a couple. Still open: **1866-1871, 1897, 1899 and 1900 `nodata`**,
and 1898 at 0.9983.
