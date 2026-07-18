# Gold validation scorecard (Ghost Acres vs pipeline)

Overlap years: [1871, 1876, 1881, 1886, 1891, 1896]

## A. Commodity coverage
- Gold commodities (overlap yrs): **603**; name-matched to a pipeline commodity: **576** (96%)
- Gold commodity-year cells: 2,130 — matched with data **1,286** (60%), missing **844** (40%)

## Coverage by year (matched / gold cells)
- 1871: matched 0/336 (0%)
- 1876: matched 263/355 (74%)
- 1881: matched 221/325 (68%)
- 1886: matched 238/344 (69%)
- 1891: matched 244/367 (66%)
- 1896: matched 320/403 (79%)

## B. National total accuracy (matched cells, same-unit)
- exact (≤1%): 645   close (≤5%): 44   off (>5%): 311   unit-differs(skipped): 153

## C. Country attribution (matched cells)
- match: 514
- attribution-shift: 25
- value-error: 564
- missing: 183

## Files
- reports/gold_missing_commodities.csv
- reports/gold_national_mismatch.csv
- reports/gold_attribution_defects.csv
- reference/commodity_gold_crosswalk.csv
