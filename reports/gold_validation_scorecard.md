# Gold validation scorecard (Ghost Acres vs pipeline)

Overlap years: [1871, 1876, 1881, 1886, 1891, 1896]

## A. Commodity coverage
- Gold commodities (overlap yrs): **603**; name-matched to a pipeline commodity: **575** (95%)
- Gold commodity-year cells: 2,130 — matched with data **1,250** (59%), missing **880** (41%)

## Coverage by year (matched / gold cells)
- 1871: matched 0/336 (0%)
- 1876: matched 242/355 (68%)
- 1881: matched 200/325 (62%)
- 1886: matched 236/344 (69%)
- 1891: matched 248/367 (68%)
- 1896: matched 324/403 (80%)

## B. National total accuracy (matched cells, same-unit)
- exact (≤1%): 529   close (≤5%): 58   off (>5%): 362   unit-differs(skipped): 206

## C. Country attribution (matched cells)
- match: 418
- attribution-shift: 43
- value-error: 577
- missing: 212

## Files
- reports/gold_missing_commodities.csv
- reports/gold_national_mismatch.csv
- reports/gold_attribution_defects.csv
- reference/commodity_gold_crosswalk.csv
