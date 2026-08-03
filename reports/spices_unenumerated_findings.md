# Spices unenumerated 1887: a truncated second engine silently halves a year

Worked 2026-08-02 (`/loop /next-defect`), bracketed-gap rank 3, GBP 451k.
**`Spices — Unenumerated` 1887 went from 0.1847 to exactly 1.000000** —
14,293,955 of 14,293,955 Lb.

**exact01 3,576 → 3,577, under 275 → 274, denominator held at 9,464. One
commodity-year changed; zero regressions.**

## The whole table was already parsed, and already closed

`as_1887` seq 3083-3098 in Chandra carries the complete block:

| | members | printed |
|---|---|---|
| Foreign (8) | **2,639,853** | **2,639,853** |
| British (5) — Aden 555,263, British East Indies 3,576,920, Hong Kong 2,992,000, British West India Islands 4,503,341, Other British Possessions 26,578 | **11,654,102** | **11,654,102** |
| Grand | 2,639,853 + 11,654,102 = **14,293,955** | **14,293,955 = the Tier-1** |

Every level to the digit. **Only the foreign half reached the payload.**

## Why — a class not previously named

**Infinity's copy of the block stops at the foreign TOTAL** (nine rows, seq
2676-2684). The block arbitration kept only the portion **both** engines carry,
and **silently discarded the British section — 11,654,102 Lb, 82% of the
commodity-year.**

**That is worth carrying: a truncated second parse does not merely fail to help;
it can subtract from what the primary already had.** The year then reads as a
plausible-looking partial (0.18) rather than as missing data, which is exactly
the shape that survives every screen — the members present are real countries
with real figures.

Repaired with a single `group_repairs` row over the British seq range; the label
was already correct.

## The foreign half, deliberately left alone

The two engines pair **the same eight numbers to different labels**: Chandra
reads `East Coast of Africa: Native States` as one country and adds an `Other
Foreign Countries` at the end; Infinity splits East Coast of Africa from Native
States and shifts everything after it by one. **The sum is identical either way**
(2,639,853), so the metric is unaffected and the pairing is not adjudicated
here — but the country attribution for those eight cells is uncertain and should
not be quoted at country level without checking the page.

## Queued: 1885 and 1892 look the same and are not

Both show the same shortfall — 0.165 and 0.1415 — but **Chandra's own blocks for
those years are truncated too** (seven and three rows), so they are a different
defect and need the raw.
