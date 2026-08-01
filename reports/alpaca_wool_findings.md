# Alpaca wool 1873-74: when closure alone cannot choose the digit

Worked 2026-08-01 (`/loop /next-defect`), bracketed-gap rank 3, GBP 644k.
**Both years went from `nodata` to exactly 1.000000** — 4,540,037 of 4,540,037 Lb
and 4,182,867 of 4,182,867 Lb.

**exact01 3,553 → 3,555 (+2), nodata 4,333 → 4,332, denominator unchanged at
9,497. Two commodity-years changed in the whole corpus; zero regressions.**

Both tables are absent from both parses and present in both engines' raw text,
printed as `WOOL: / Alpaca, Llama, and Vicuna`.

## 1874 — a clean two-column split between the engines

| | Chandra | Infinity | closes |
|---|---|---|---|
| Chili **quantity** | **724,685** | 721,685 | Chandra |
| Other Countries **value** | 2,819 | **2,849** | Infinity |

With Chandra's Chili the quantities give 3,435,786 + 724,685 + 22,396 =
**4,182,867 = the printed Total = the Tier-1**; with Infinity's Other Countries
the values give 444,323 + 110,428 + 2,849 = **557,600 = the printed value
total**. **Each engine supplies the digit the other missed, in a different
column.** Every resulting unit price is in band (Peru 0.1293, Chili 0.1524,
Other 0.1272).

## 1873 — closure alone is not enough, and that is the point

Both engines transcribe the three members **identically**: Peru 3,896,366,
Chili 1,633,418, Other Countries 10,253. Those sum to 5,540,037 against a
printed Total of 4,540,037 — **exactly 1,000,000 over**.

**Two different single-digit repairs each give exactly 4,540,037:**

- Peru 3,896,366 → 2,896,366, or
- Chili 1,633,418 → **633,418** (a dropped leading `1`, the commonest OCR shape)

**So the closure test cannot choose between them** — and picking one because it
"looks like" an OCR error would be exactly the guess the loop's guardrails
forbid. Two independent series tests decide it, and they agree:

1. **Price band.** This commodity runs **GBP 0.111-0.187 a lb** in the years that
   close (Peru 0.1307 / 0.1310 / 0.1113 in 1872 / 1875 / 1876; Chili 0.1644 /
   0.1417 / 0.1275). With Chili = 633,418 the 1873 prices are Peru 0.1193, Chili
   0.1450, Other 0.0973 — all in band. With Peru = 2,896,366 instead, **Chili's
   price would be 0.0562, three times below the band**.
2. **Quantity series.** Chili ships **124,219 lb in 1872, 397,406 in 1875,
   339,809 in 1876** — hundreds of thousands, never 1.6 million — while Peru
   ships 3.52M, 3.61M and 3.12M, so 3,896,366 is exactly where Peru belongs.

Both tests point the same way: **Chili = 633,418**.

The **value column confirms the member list independently**: 464,933 + 91,871 +
998 = **557,802 = Infinity's printed value total exactly** (Chandra reads
557,302, a single-digit misread of its own). That completeness check is what
licenses arbitrating a quantity at all — see [[two-column-digit-proof]].

## The method note

The cocoa iteration established that a cross-engine quantity reconstruction is
safe only once the other printed column closes. **This case adds the next
constraint: when the closure has more than one single-digit solution, the
arithmetic is exhausted and an out-of-block test is required.** The unit-price
band and the country's own quantity series are both available for every
commodity-year in the corpus, and here they were unanimous.
