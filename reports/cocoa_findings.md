# Cocoa 1879 and 1882: two whole tables in neither parse, and a digit from each engine

Worked 2026-08-01 (`/loop /next-defect`), bracketed-gap ranks 3 and 8, GBP 875k
and 639k. **Both years went from `nodata` to exactly 1.000000** — 26,155,788 of
26,155,788 Lb and 19,101,646 of 19,101,646 Lb.

**exact01 3,549 → 3,551 (+2), nodata 4,337 → 4,335, denominator unchanged at
9,497. Two commodity-years changed in the whole corpus; zero regressions.**

`Cocoa` is exact or near-exact in almost every other year 1872-1899; these two
were complete holes.

## Both tables are absent from both parses and present in both raws

Neither `country_obs` nor `country_obs_inf` has any COCOA block for `as_1879` or
`as_1882`. Both engines' **raw text** carries them in full, printed as
`COCOA : From Germany …` and `COCOA : From France …`.

## 1879 — a cross-engine reconstruction, one digit from each

Fifteen members, and **each engine is wrong on a different quantity**:

| | Chandra | Infinity | taken |
|---|---|---|---|
| Holland | **14,344** | 14,314 | Chandra |
| Dutch Guiana | 488,596 | **488,896** | Infinity |
| Hayti | 579,991 | **879,991** | Infinity |

Every other quantity is identical in both. With that combination the fifteen
members sum to **26,155,788 = the block's own printed Total = the Tier-1, to the
digit**.

**No other combination closes.** Chandra's list alone is 300,300 short;
Infinity's alone is 30 short — **and the 30 is exactly the Holland difference**,
which is what identifies Chandra as right on that cell and Infinity as right on
the other two.

The **value** column is identical in both engines and sums to **1,089,417 = the
printed value total, to the digit** — the independent check that no member row is
missing from either transcription, which is what makes the quantity
reconstruction safe rather than a search over combinations.

## 1882 — the engines agree, and the value column arbitrates

Thirteen members; **both engines agree on every quantity**, and they sum to
**19,101,646 = the printed Total = the Tier-1, to the digit**.

The single disagreement is a **value**: British West India Islands, Chandra
382,228 against Infinity 382,928. The printed value total settles it — the other
twelve values sum to 215,191, so BWI must be 597,419 − 215,191 = **382,228**,
Chandra's reading. Both printed columns then close to the digit.

## The method worth carrying

This is the fourth consecutive item whose table was **not in either parse**, and
the second where **neither engine's raw was correct on its own**. The as_1881
sheep-skins case had each engine holding half the *structure* (Chandra the
country order, Infinity the numeric pairs); here each engine holds a different
*digit*.

**The discipline that makes it safe is the second printed column.** Reconstructing
a quantity column by picking between engines is a search, and searches find
coincidences — but the value column is transcribed independently, and when it
closes to the digit it proves the member *list* is complete. Only then is the
quantity arbitration a two-alternative choice per cell rather than a fishing
expedition. See [[two-column-digit-proof]].
