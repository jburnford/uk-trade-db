# Wood imports by country, standardized wide (1872–1899)

Widened from `exports/wood_country_year_voted.csv` (cross-volume, 
cross-engine voted) by `scripts/widen_country_year.py`. Fixed country 
columns + a complete 1872–1899 year grid per commodity, so series are 
comparable across years. Values are in each commodity’s native unit 
(loads or tons); a **blank means the origin was not separately returned 
that year** (source zeros are treated as missing, not zero trade).

## Files

- `exports/wood_wide/<commodity>.csv` — per-commodity matrix (year rows × country cols + Total).
- `exports/wood_country_wide.csv` — all commodities stacked (one row per commodity×year).
- `exports/wood_country_wide_tier.csv` — same shape, cell = worst contributing tier (A/B/C).
- `reference/country_standardize.csv` — the source-label → standard-country crosswalk (reviewable).

## The world was not standard — what we reconciled

- **United States** is summed from the coast split the source introduced in 
  1893 (*On the Atlantic* + *On the Pacific* + an unspecified *United States* 
  residual); pre-1893 it is the single *United States of America* line. A stray 
  duplicate (sawn-fir 1896, 386,003) is dropped by keeping only the best-attested 
  row per identical label before summing.
- **Empires kept distinct.** *French West Africa* (the explicitly French 
  possessions/Senegambia) is a separate column from British African possessions 
  (*Gold Coast*, *Niger Protectorate*, *Cape of Good Hope*); the residual 
  *West Africa (unspecified)* holds only the non-attributable "foreign / not 
  distinguished" labels that cannot be assigned to any empire. **Australasia** 
  sums the British colonies (Victoria, NSW, New Zealand, West Australia).
- **British India & Burma** absorbs the 1877 *Bombay and Scinde* variant.
- **Russia** follows the UK returns and **includes Finland** — unlike the TTJ 
  count series, which lists Finland separately. Do not compare the two Russias naively.
- **Sweden & Norway** is kept as its own column for the rare years the source 
  printed them combined; in every other year Sweden and Norway are already split.
- Cell **confidence** = the worst voting tier (A<B<C) of the rows summed into it; 
  see the `_tier` companion. Tier ≠ attribution: a digit-perfect number filed under 
  the wrong year/commodity is still its tier.

Dropped 97 rows carrying a unit different from their commodity’s 
majority measure (genuine measure confusion, not summable).

**Unmapped source labels needing review:** `british west indies and guiana`, `scinde`

## Per-commodity coverage

| commodity | unit | years | countries | cells | %A | %B | %C |
|---|---|--:|--:|--:|--:|--:|--:|
| wood-furniture-hardwoods | tons | 1877–1889 | 38 | 100 | 0% | 42% | 58% |
| wood-hewn-fir | loads | 1873–1899 | 20 | 247 | 21% | 57% | 22% |
| wood-hewn-oak | loads | 1873–1899 | 16 | 186 | 8% | 78% | 14% |
| wood-hewn-teak | loads | 1873–1899 | 17 | 97 | 24% | 59% | 18% |
| wood-hewn-unenumerated | loads | 1875–1899 | 15 | 155 | 29% | 46% | 25% |
| wood-mahogany | tons | 1873–1899 | 31 | 216 | 22% | 57% | 20% |
| wood-sawn-fir | loads | 1877–1899 | 21 | 204 | 32% | 56% | 12% |
| wood-sawn-unenumerated | loads | 1877–1896 | 14 | 150 | 0% | 88% | 12% |
| wood-staves | loads | 1873–1895 | 13 | 162 | 0% | 88% | 12% |
| wood-unenumerated | tons | 1873–1899 | 40 | 247 | 34% | 40% | 26% |
