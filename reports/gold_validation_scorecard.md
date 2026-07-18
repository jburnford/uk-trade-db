# Gold validation scorecard (Ghost Acres vs pipeline)

Overlap years: [1871, 1876, 1881, 1886, 1891, 1896]

## A. Commodity coverage
- Gold commodities (overlap yrs): **603**; name-matched to a pipeline commodity: **576** (96%)
- Gold commodity-year cells: 2,130 — matched with data **1,315** (62%), missing **815** (38%)

## Coverage by year (matched / gold cells)
- 1871: matched 0/336 (0%)
- 1876: matched 271/355 (76%)
- 1881: matched 219/325 (67%)
- 1886: matched 243/344 (71%)
- 1891: matched 257/367 (70%)
- 1896: matched 325/403 (81%)

## B. National total accuracy (matched cells, same-unit)
- exact (≤1%): 648   close (≤5%): 46   off (>5%): 318   unit-differs(skipped): 173

## C. Country attribution (matched cells)
- match: 520
- attribution-shift: 24
- value-error: 592
- missing: 179

## Files
- reports/gold_missing_commodities.csv
- reports/gold_national_mismatch.csv
- reports/gold_attribution_defects.csv
- reference/commodity_gold_crosswalk.csv
