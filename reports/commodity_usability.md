# What can I use? — per-commodity reliability

`exports/commodity_usability.csv` grades every gold-benchmarked commodity by
**numeric fingerprint** against the Ghost Acres gold data at the five overlap
years (1876, 1881, 1886, 1891, 1896). Built by `scripts/build_usability_table.py`.
Interactive version: the Commodity Usability Guide artifact.

Matching is by **number, not name** (the OCR labels drift across the era), and is
built to resist coincidence — because an earlier single-number version produced
false matches (Cotton Raw ↔ Raisins) that destroyed trust.

| signal | question | test |
|---|---|---|
| **TOTAL** | "commodity X, total imports by year" | pipeline total within ±5% of gold **and** the pipeline article shares a real name-word with the gold commodity (the name gate kills coincidences — a bare total is *not* collision-safe) |
| **BY-COUNTRY** | "commodity X **from country Y**" | total **and** largest origin both match (two independent numbers → collision-safe on their own) |

Tiers: **SOLID** (every gold year) · **MOSTLY** (all but one) · **MIXED** (some) ·
**WEAK** (≤ half) · **SPARSE** (<2 years to judge) · **UNVERIFIED** (never
independently identified).

## Tally (475 commodities)

| tier | TOTAL | BY-COUNTRY |
|---|--:|--:|
| SOLID | 27 | 26 |
| MOSTLY | 58 | 57 |
| MIXED | 53 | 51 |
| WEAK | 212 | 216 |
| SPARSE | 111 | 111 |
| UNVERIFIED | 14 | 14 |

**~85 commodities have a trustworthy national series (SOLID+MOSTLY); ~83 by
country too.** This is the *honest* count — an earlier cut reported 255 national-
SOLID, but those were inflated by single-number coincidences. Validating OCR'd
Victorian trade stats against an independent benchmark is unforgiving.

## How to use it

1. **National series**: use when `total_tier` is SOLID/MOSTLY.
2. **By-country breakdown**: use only when `bycountry_tier` is SOLID/MOSTLY too.
3. **Pick years from the `*_ok_years` columns** — the tier is a summary; a WEAK
   commodity can still be solid in the exact year you need.
4. **WEAK ≠ wrong.** It means "couldn't confirm against gold." Often the national
   total is fine but the origins are grouped coarser than gold (see **Cocoa,
   Rice, Wool** — TOTAL beats BY-COUNTRY). **UNVERIFIED** = the series couldn't be
   located in the pipeline at all.
5. `pipeline_match` names the pipeline article to query (`article_group|article`),
   chosen to prefer a genuine name overlap so it's checkable.

## Caveats

- Signals are judged only at the 5 gold years; other years inherit the tier by
  inference, not proof. Known-broken stretches (e.g. tea 1882–90) are flagged in
  [[uk-trade-colonial-subentries]].
- **Wood/timber** is validated separately (26/26 country cells exact vs the
  decennial gold; A-grade 83% of rows) and is the most dependable part of the
  corpus — it isn't re-graded here.
- Peak volume is each commodity's native unit — comparable within a unit, not
  across.
