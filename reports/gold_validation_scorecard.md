# Gold validation scorecard (Ghost Acres vs pipeline)

Overlap years: [1871, 1876, 1881, 1886, 1891, 1896]

## A. Commodity coverage
- Gold commodities (overlap yrs): **603**; name-matched to a pipeline commodity: **576** (96%)
- Gold commodity-year cells: 2,130 — matched with data **1,299** (61%), missing **831** (39%)

## Coverage by year (matched / gold cells)
- 1871: matched 0/336 (0%)
- 1876: matched 265/355 (75%)
- 1881: matched 216/325 (66%)
- 1886: matched 244/344 (71%)
- 1891: matched 250/367 (68%)
- 1896: matched 324/403 (80%)

## B. National total accuracy (matched cells, same-unit)
- exact (≤1%): 639   close (≤5%): 49   off (>5%): 300   unit-differs(skipped): 182

## C. Country attribution (matched cells)
- match: 517
- attribution-shift: 20
- value-error: 577
- missing: 185

## Files
- reports/gold_missing_commodities.csv
- reports/gold_national_mismatch.csv
- reports/gold_attribution_defects.csv
- reference/commodity_gold_crosswalk.csv
