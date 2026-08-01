# Saltpetre 1878-79: one year closes, one year is queued rather than guessed

Worked 2026-08-01 (`/loop /next-defect`), bracketed-gap rank 3, GBP 624k.

**exact01 3,555 → 3,556, within 5% 1,109 → 1,110, under 283 → 282, nodata 4,332
→ 4,331. Zero regressions.**

| year | before | after |
|---|---|---|
| 1878 | *nodata* | **1.000000** |
| 1879 | 0.0810 | **0.99014** |

## 1878 — both columns close

The origin table is absent from both parses and present in both engines' raw
text, printed as `SALTPETRE (NITRATE OF POTASH)`. Both engines transcribe every
figure identically, and **both printed columns close to the digit**: the six
members sum to **279,601 = the block's own printed Total = the Tier-1**, and
their values to **294,880 = the printed value total**.

## 1879 — an export table, and a digit that is not guessable

**Defect one: what was there was a re-export table.** `as_1879`'s parsed
`SALTPETRE` block (seq 963-967; Infinity files the same rows under a stale
`QUICKSILVER` head) is the **re-export** table — Germany 7,329, France 6,693,
Spain and Canary Islands 6,026, Other Countries 11,919, its own printed Total
31,967 — and three of its rows had become the entire import-origin profile for
the year. Britain re-exported Indian saltpetre to France and Spain; it did not
import it from them.

**Fourth instance of the export-leakage class** (after Toys 1880 and leather
manufactures 1883-84). Removed by supersede — two-up rows cannot be displaced
any other way.

**Defect two: the import table is in neither parse**, and its quantity column
does not close.

**The value column does close, to the digit** — 33,778 + 16,065 + 236,230 +
4,319 = **290,392 = the printed value total** — which proves the member *list* is
complete. But the quantities sum to 301,331 against a printed **304,331**, and
**the missing 3,000 is deliberately not guessed**:

- **Both engines transcribe all four quantities identically**, so there is no
  cross-engine arbitration to make.
- **Four different single-digit repairs each close the column**: Germany
  30,246→33,246, Holland 14,790→17,790, Bengal and Burmah 251,923→254,923, or
  Other Countries 4,372→7,372.
- The within-year **price ordering** — Europeans dearer than the Indian source,
  as in 1877, 1880 and 1881 — mildly favours Bengal and Burmah, the only
  candidate that leaves Germany and Holland above India. But **1879 is a
  low-price year overall** (the block prices at 0.954 against 1.07-1.08 in 1877
  and 1880), so the cross-year band cannot separate the candidates and the
  ordering argument alone is not proof.

Recorded as an **honest partial**: four named origins at 301,331/304,331 =
0.99014, where the year previously carried three wrong ones. Same treatment as
silver ore 1879 in `reports/silver_ore_findings.md`.

**This is the case the alpaca rule anticipated.** That iteration established
that when a closure has more than one single-digit solution the arithmetic is
exhausted and an out-of-block test is required — and that *if the tests
disagree or are inconclusive, queue it rather than choose*. Here they are
inconclusive, so it is queued.

## Open

- **The 3,000 in 1879**, with the four candidates named above. A page image
  would settle it in seconds.
- 1866-1871 and 1900 are `nodata` — seven further years with a Tier-1 and no
  origin table located.
