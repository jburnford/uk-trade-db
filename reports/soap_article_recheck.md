# Re-testing the 2021 soap article against the OCR pipeline

Jim Clifford, 'London's Soap Industry and the Development of Global Ghost Acres
in the Nineteenth Century', *Environment and History* 27:3 (August 2021),
471–497. DOI 10.3197/096734019X15463432086982.

**Question.** The article's quantitative claims rest on the hand-keyed
'British Imports Database' (article n. 29). If the same analysis were run on the
OCR pipeline in this repository instead, would any of it change?

**Answer.** The argument is unchanged. Two published numbers are wrong, and in
both cases the error is in the hand-keyed database, not in the OCR.

---

## 1. The two series being compared

| | article's series | this repository |
|---|---|---|
| name | 'British Imports Database' (n. 29) | `exports/map_slim.json`, `exports/_origin_dedup.csv` |
| method | hand keyed by the author and students from 2014 | dual-engine OCR (Chandra + Infinity), cross-volume vote |
| the extract used here | `reference/gold_eandh.csv`, from `BritishImportsDatabase_EandH.xls`, SHA-256 `6fa90e2309970f4b…` | `raw/as_1872`–`as_1899` |
| sources | CUST 5/1B (Kew); HCPP *Annual Statement of Trade* | the same HCPP volumes |
| overlap tested | 1872–1899 (28 years), tallow; national series to 1900 | |

They are two independent transcriptions of the same printed pages. Where they
disagree, exactly one is wrong, and the question of which can be settled by
evidence neither of them contains — the printed subtotal on another page.

Full validation harness and tolerances: `reports/gold_eandh_validation.md`.
Units below: quantity in hundredweights unless 'tons' is stated; 1 long ton =
20 cwt; prices in shillings per cwt, computed as 20 × value ÷ quantity.

---

## 2. Claim-by-claim audit

### Claims that survive unchanged

| # | claim | page | article's figure | pipeline | verdict |
|---|---|---|---|---|---|
| 1 | US becomes the largest supplier in 1873 | 490 | 32.3% share | 32.3% | identical |
| 2 | US largest through the rest of the 1870s | 490 | 1873–1880 | 1873–1880 | identical |
| 3 | Australasia dominant in the 1880s | 490 | 1881–1890 | 1881–1890 | identical |
| 4 | total imports trend down in the 1880s | 490 | 1880–84 avg 57,782 t → 1885–89 avg 53,060 t (−8.2%) | identical to the tonne | identical |
| 5 | Australia floods the market in the 1890s | 490 | Australasian share to 82.9% in 1895 | 82.9% | identical |
| 6 | Russia's decline after the mid-1860s | 489 | 9.7% (1872) → 0.2% (1895) | identical | identical |
| 7 | 1901 tallow imports 89,266 tons | 495 | = gold World row 1,785,319 cwt | 1901 outside corpus | not testable |
| 8 | 1901 rosin imports 90,624 tons | 496 | = gold World row 1,812,478 cwt | 1901 outside corpus | not testable |

**Leading supplying region: 0 of 28 years differ.** Rebuilt from pipeline data,
Figure 4 would be identical to the tonne in **22 of 28 years**; the median year
has **0.00%** of its tonnage reallocated between countries.

### Claims that change

| # | claim | page | article | corrected | cause |
|---|---|---|---|---|---|
| 9 | 'the lowest average yearly import price dropping under 16s per hundredweight in 1898' | 489 | 15.76s in 1898 | **20.44s in 1898; the series low is 1897 at 19.17s** | gold's 1898 quantity is wrong |
| 10 | 1898 as the year the price 'finally collapsed' after stockpiling | 494 | 1898 is the series peak at 131,097 tons | **101,097 tons; the peak is 1900 (108,900 t) then 1895 (108,791 t)** | same error |

---

## 3. The 1898 error, proved

The gold's 1898 `World` row reads **2,621,941 cwt**. Three independent sums say
it should be 2,021,941.

**(a) The gold's own country rows.** They sum to 1,921,991 cwt — 27% below the
gold's own World row, the largest self-inconsistency anywhere in the tallow
series (`reports/gold_eandh_selfcheck.csv`).

**(b) The gold's own Argentina cell.** The gold reads Argentine Republic at
**64,087** cwt; we read **164,037**. The *value* column agrees to GBP50
(178,452 vs 178,402), so both transcriptions are certainly reading the same
printed row. Substituting our quantity:

```
1,921,991 − 64,087 + 164,037 = 2,021,941 cwt
```

**(c) Our Tier-1 anchor.** The national line for 1898, printed on a different
page from the country table and read independently by two OCR engines, is
**2,021,941 cwt** — the same figure, to the hundredweight.

So the hand keying slipped twice on one page: a dropped leading digit in
Argentina, and `2,621,941` for `2,021,941` in the World row. The value column of
that World row (GBP2,066,433) is correct — we read it identically — which is why
the error shows up as a price, not as a missing sum.

Recorded as `verdict = gold_error` in `reports/gold_eandh_adjudication.csv`.

### Consequence for the price series

| | 1897 | 1898 |
|---|---|---|
| value (GBP, both series agree) | 1,869,929 | 2,066,433 |
| gold quantity (cwt) | 1,950,925 | 2,621,941 |
| corrected quantity (cwt) | 1,950,925 | **2,021,941** |
| gold price | 19.17s | 15.76s |
| corrected price | 19.17s | **20.44s** |

The collapse itself is untouched: 42.88s in 1872 to 19.17s in 1897, more than a
halving. But the trough moves back a year, 1898 ticks *up*, and 'under 16s'
becomes 'under 20s'.

**The correction improves the article's own corroboration.** Crosfield's
notebook records tallow at 21s in the mid-1890s (p. 488, n. 67), and the article
says 'British trade statistics confirm the record in the notebook'. The
corrected import price is **21.26s in 1896 and 19.17s in 1897** — on the
notebook. The gold's 15.76s sat a quarter below it.

### Consequence for Figure 4

1898 is the tallest bar in the article's chart. Corrected, it falls to 101,097
tons — **fifth**, behind 1900 (108,900), 1895 (108,791), 1899 (103,057) and 1896
(102,487). The narrative of an Australian glut still holds, but its statistical
climax is 1895, not 1898, and 1898 becomes an ordinary year in a high plateau
rather than a spike.

Note that Figure 4 is stacked *by country*, so if it was drawn from the country
rows rather than the World row it already shows 96,100 tons for 1898 and is not
itself affected. The error is in the prose price claim on p. 489.

---

## 4. National series, full comparison 1872–1899

'gold s/cwt' is what the article's database yields; 'pipeline s/cwt' is this
repository. Blank in the last column means the two agree exactly.

| year | gold cwt | pipeline cwt | gold tons | pipeline tons | value GBP | gold s/cwt | pipeline s/cwt | |
|---|---|---|---|---|---|---|---|---|
| 1872 | 1,328,444 | 1,328,444 | 66,422 | 66,422 | 2,848,164 | 42.88 | 42.88 |  |
| 1873 | 1,527,321 | 1,527,321 | 76,366 | 76,366 | 3,152,413 | 41.28 | 41.28 |  |
| 1874 | 1,155,243 | 1,155,243 | 57,762 | 57,762 | 2,331,479 | 40.36 | 40.36 |  |
| 1875 | 987,396 | 967,396 | 49,370 | 48,370 | 2,045,863 | 41.44 | 42.30 | **differ** |
| 1876 | 1,344,445 | 1,344,445 | 67,222 | 67,222 | 2,875,170 | 42.77 | 42.77 |  |
| 1877 | 1,224,239 | 1,224,239 | 61,212 | 61,212 | 2,568,479 | 41.96 | 41.96 |  |
| 1878 | 921,203 | 921,203 | 46,060 | 46,060 | 1,814,179 | 39.39 | 39.39 |  |
| 1879 | 1,174,907 | 1,174,907 | 58,745 | 58,745 | 2,106,927 | 35.87 | 35.87 |  |
| 1880 | 1,316,379 | 1,316,379 | 65,819 | 65,819 | 2,311,689 | 35.12 | 35.12 |  |
| 1881 | 1,192,075 | 1,192,075 | 59,604 | 59,604 | 2,100,619 | 35.24 | 35.24 |  |
| 1882 | 1,116,581 | 1,116,581 | 55,829 | 55,829 | 2,252,517 | 40.35 | 40.35 |  |
| 1883 | 1,038,277 | 1,038,277 | 51,914 | 51,914 | 2,101,617 | 40.48 | 40.48 |  |
| 1884 | 1,114,888 | 1,114,888 | 55,744 | 55,744 | 2,106,020 | 37.78 | 37.78 |  |
| 1885 | 1,008,960 | 1,008,960 | 50,448 | 50,448 | 1,580,015 | 31.32 | 31.32 |  |
| 1886 | 1,011,911 | 1,011,911 | 50,596 | 50,596 | 1,299,214 | 25.68 | 25.68 |  |
| 1887 | 895,121 | 895,121 | 44,756 | 44,756 | 1,073,611 | 23.99 | 23.99 |  |
| 1888 | 1,145,928 | 1,145,928 | 57,296 | 57,296 | 1,432,596 | 25.00 | 25.00 |  |
| 1889 | 1,244,031 | 1,244,031 | 62,202 | 62,202 | 1,645,801 | 26.46 | 26.46 |  |
| 1890 | 1,383,593 | 1,383,593 | 69,180 | 69,180 | 1,725,255 | 24.94 | 24.94 |  |
| 1891 | 1,371,201 | 1,371,201 | 68,560 | 68,560 | 1,772,268 | 25.85 | 25.85 |  |
| 1892 | 1,375,679 | 1,375,679 | 68,784 | 68,784 | 1,747,968 | 25.41 | 25.41 |  |
| 1893 | 1,559,397 | 1,559,397 | 77,970 | 77,970 | 2,161,407 | 27.72 | 27.72 |  |
| 1894 | 1,837,587 | 1,837,587 | 91,879 | 91,879 | 2,344,773 | 25.52 | 25.52 |  |
| 1895 | 2,175,822 | 2,175,822 | 108,791 | 108,791 | 2,575,071 | 23.67 | 23.67 |  |
| 1896 | 2,049,749 | 2,049,749 | 102,487 | 102,487 | 2,178,652 | 21.26 | 21.26 |  |
| 1897 | 1,950,925 | 1,950,925 | 97,546 | 97,546 | 1,869,929 | 19.17 | 19.17 |  |
| 1898 | 2,621,941 | 2,021,941 | 131,097 | 101,097 | 2,066,433 | 15.76 | 20.44 | **differ** |
| 1899 | 2,061,137 | 2,061,137 | 103,057 | 103,057 | 2,380,033 | 23.09 | 23.09 |  |

1900 (outside the article's Figure 4 country data, inside our national series):
both read 2,177,991 cwt = 108,900 tons.

**26 of 28 quantities and 28 of 28 values agree, most of them to the pound and
the hundredweight.**

**1875** is the other disagreement and is also a gold error: the sheet carries
the same World row twice, at 967,396 and 987,396; its own country rows sum to
967,396, and so do ours. 1,000 tons, no bearing on any claim.

---

## 5. Where the pipeline is worse than the hand keying

At country-cell level the hand keying is the better record. Of 370 comparable
tallow country-year cells, quantity agrees within 0.1% in 347 and value in 339
(`reports/gold_eandh_country.csv`). The disagreements concentrate in two years.

| year | tonnage reallocated | share of year |
|---|---|---|
| 1897 | 6,832 t | **7.00%** |
| 1898 | 5,325 t | **5.54%** |
| 1883 | 530 t | 1.02% |
| 1899 | 889 t | 0.86% |
| 1880 | 150 t | 0.23% |
| 1891 | 150 t | 0.22% |
| all other 22 years | ≤4 t | ≤0.01% |

### 1897

Our block sums to 1,953,168 cwt against a Tier-1 anchor of 1,950,925 — 0.11%
out, which passes a 5% closure test and only just fails a 0.1% one. The gold's
country rows hit the anchor exactly. The defect is a digit that moved between
two adjacent rows:

| country | gold cwt | pipeline cwt | diff cwt | gold GBP | pipeline GBP |
|---|---|---|---|---|---|
| **Argentina** | 167,625 | 107,025 | **−60,600** | 106,527 | 106,557 |
| **United States Of America (Atlantic)** | 200,602 | 260,602 | **+60,000** | 231,024 | 231,021 |
| **British East Indies** | 8,243 | 0 | **−8,243** | 9,293 | 0 |
| **United States Of America** (bare) | 0 | 6,608 | **+6,608** | 0 | 3,128 |
| **Channel Islands** | 0 | 6,062 | **+6,062** | 0 | 1,788 |
| **China** | 10,672 | 10,072 | −600 | 11,825 | **1,195** |
| **Chile** | 1,316 | 1,810 | +494 | 1,120 | **112** |
| **Belgium** | 31,931 | 31,031 | −900 | 35,997 | 33,967 |
| **United States Of America (Pacific)** | 10,931 | 10,031 | −900 | 9,593 | **958** |
| **§RESIDUAL** | 5,624 | 5,325 | −299 | 5,616 | **2,183** |
| New South Wales | 695,473 | 695,473 | 0 | 661,202 | 661,202 |
| New Zealand | 299,874 | 299,874 | 0 | 285,683 | 285,083 |
| Queensland | 146,721 | 146,721 | 0 | 136,917 | 136,917 |
| Victoria | 234,216 | 234,216 | 0 | 223,987 | 223,987 |
| France | 50,734 | 50,734 | 0 | 62,599 | 62,529 |
| Uruguay | 36,113 | 36,113 | 0 | 35,234 | 35,291 |
| **sum** | **1,950,925** | 1,953,168 | | 1,869,929 | 1,847,525 |

Note the value column separately: China GBP11,825 → 1,195, Chile 1,120 → 112,
US Pacific 9,593 → 958, residual 5,616 → 2,183. Four cells in one block lost a
leading digit — a distinct truncation defect from the quantity slip.

Effect on Figure 4 if rebuilt as-is: the Argentina+Uruguay band shrinks ~36% and
the United States band grows ~30% in 1897. Australasia is 71.4% of the year
either way, so no band ordering changes.

### 1898

Here we are right on the quantity axis (see §3) and wrong on two value cells:

| country | gold cwt | pipeline cwt | diff cwt | gold GBP | pipeline GBP |
|---|---|---|---|---|---|
| **Argentina** | 64,087 | **164,037** | **+99,950** | 178,452 | 178,402 |
| **Belgium** | 38,882 | 33,832 | **−5,050** | 49,297 | 49,297 |
| **Canada** | 19,519 | 19,519 | 0 | 19,023 | **10,023** |
| **New South Wales** | 503,966 | 503,066 | −900 | 566,676 | **506,676** |
| **Channel Islands** | 0 | 6,354 | **+6,354** | 0 | 2,022 |
| **British East Indies** | 1,692 | 1,002 | −690 | 0 | 1,608 |
| United States Of America (Atlantic) | 571,959 | 571,959 | 0 | 538,243 | 538,243 |
| New Zealand | 305,245 | 305,245 | 0 | 321,480 | 321,450 |
| Victoria | 132,268 | 132,268 | 0 | 135,298 | 135,298 |
| Queensland | 118,642 | 118,642 | 0 | 123,387 | 123,387 |
| France | 78,878 | 78,878 | 0 | 98,032 | 98,032 |
| **sum** | 1,921,991 | **2,021,983** | | 2,124,686 | 2,068,745 |

Our Canada (19,023 → 10,023) and New South Wales (566,676 → 506,676) each lost a
digit in the value column, GBP69,000 together. Our *national* value line for 1898
is nonetheless correct — it reads GBP2,066,433, identical to the gold — so the
value errors are confined to country cells.

All of these are logged in `reports/gold_eandh_adjudication.csv` and are **not**
fixed from the gold: under the hold-out rule the gold is a test set, so any
repair has to be justified from the page image or our own printed subtotals.

---

## 6. Erratum-ready statements

If a correction were issued, the minimal accurate wording:

> p. 489. For 'the lowest average yearly import price dropping under 16s per
> hundredweight in 1898' read 'the lowest average yearly import price dropping
> to just over 19s per hundredweight in 1897'. The 1898 figure in the British
> Imports Database (2,621,941 cwt) is a transcription error for 2,021,941 cwt;
> the corrected 1898 average is 20.4s.

> p. 494. The claim that the price 'finally collapsed in 1898' should be read
> against the corrected series, in which the price trough is 1897 and 1898 rises
> slightly. The *Oil and Colourman's Journal* evidence for London stockpiling is
> independent of the trade statistics and is unaffected.

> Figure 4. The 1898 total should read 101,097 long tons, not 131,097. The peak
> year is 1900 (108,900 tons), followed by 1895 (108,791), 1899 (103,057) and
> 1896 (102,487); 1898 is the fifth highest year, not the highest.

---

## 7. Scope and limits

**Testable here:** tallow, 1872–1899 country detail and 1868–1900 national
totals; rosin at 1866, 1871, 1876, 1881, 1886, 1891, 1896, 1900.

**Not testable here:** everything before 1868 (Figure 3, the Russian steppe
material, the 1800 and 1851 figures, the 55s price in 1855); the 1901 and
1906–09 figures on pp. 494–496; the re-export claims on p. 489; the soap
production series; and every non-tallow commodity in the conclusion's 1901 list.

**Independence caveat.** The E&H extract and the Ghost Acres workbook used by
`scripts/validate_gold.py` come from the same underlying database, so 1876,
1881, 1886, 1891 and 1896 have been benchmarked against this pipeline before.
The 1897 and 1898 findings, and the 1875 finding, are all in never-benchmarked
years.

**What this does not show.** That the OCR pipeline is generally more accurate
than hand keying. It is not: at country-cell level the hand keying wins 347–370
on quantity. What it shows is that the two are *independent*, so each catches
what the other misses, and that at the aggregate level on which this article's
argument rests they are interchangeable.

---

## Sources

- `reports/gold_eandh_validation.md` — the full validation, ladder and tolerances
- `reports/gold_eandh_adjudication.csv` — every disagreement with its verdict
- `reports/gold_eandh_selfcheck.csv` — the gold's internal consistency by year
- `reports/gold_eandh_country.csv` — all 370 country-cell comparisons
- `reference/gold_eandh.csv`, `reference/gold_eandh.provenance.json`
- `scripts/validate_gold_eandh.py`, `scripts/countrykey.py`
