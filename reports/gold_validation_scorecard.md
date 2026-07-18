# Gold validation scorecard (Ghost Acres vs pipeline)

Overlap years: [1871, 1876, 1881, 1886, 1891, 1896]

## A. Commodity coverage
- Gold commodities (overlap yrs): **603**; name-matched to a pipeline commodity: **576** (96%)
- Gold commodity-year cells: 2,130 — matched with data **1,314** (62%), missing **816** (38%)

## Coverage by year (matched / gold cells)
- 1871: matched 0/336 (0%)
- 1876: matched 275/355 (77%)
- 1881: matched 222/325 (68%)
- 1886: matched 244/344 (71%)
- 1891: matched 249/367 (68%)
- 1896: matched 324/403 (80%)

## B. National total accuracy (matched cells, same-unit)
- exact (≤1%): 664   close (≤5%): 48   off (>5%): 311   unit-differs(skipped): 160

## C. Country attribution (matched cells)
- match: 535
- attribution-shift: 22
- value-error: 588
- missing: 169

## Files
- reports/gold_missing_commodities.csv
- reports/gold_national_mismatch.csv
- reports/gold_attribution_defects.csv
- reference/commodity_gold_crosswalk.csv
