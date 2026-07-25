# Gold validation scorecard (Ghost Acres vs pipeline)

Overlap years: [1871, 1876, 1881, 1886, 1891, 1896]

## A. Commodity coverage
- Gold commodities (overlap yrs): **603**; name-matched to a pipeline commodity: **576** (96%)
- Gold commodity-year cells: 2,130 — matched with data **1,298** (61%), missing **832** (39%)

## Coverage by year (matched / gold cells)
- 1871: matched 0/336 (0%)
- 1876: matched 269/355 (76%)
- 1881: matched 217/325 (67%)
- 1886: matched 240/344 (70%)
- 1891: matched 247/367 (67%)
- 1896: matched 325/403 (81%)

## B. National total accuracy (matched cells, same-unit)
- exact (≤1%): 646   close (≤5%): 48   off (>5%): 314   unit-differs(skipped): 161

## C. Country attribution (matched cells)
- match: 523
- attribution-shift: 20
- value-error: 579
- missing: 176

## Files
- reports/gold_missing_commodities.csv
- reports/gold_national_mismatch.csv
- reports/gold_attribution_defects.csv
- reference/commodity_gold_crosswalk.csv
