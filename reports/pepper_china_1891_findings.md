# Pepper and china 1891: two stale heads in one volume, and four subtotals wearing country names

Worked 2026-08-01 (`/loop /next-defect`), bracketed-gap ranks 3 and 5, GBP 863k
and 663k. **Both years went from `nodata` to exactly 1.000000** — 34,794,260 of
34,794,260 Lb and 208,633 of 208,633 Cwt.

**exact01 3,551 → 3,553 (+2), nodata 4,335 → 4,333, denominator unchanged at
9,497. Two commodity-years changed in the whole corpus; zero regressions.**

## Both tables were parsed — under stale heads, with the commodity as the article

Unlike the last six items, nothing was missing from the parse. `as_1891`'s
Chandra copy files each table under the **previous section's head**, with the
commodity's own name absorbed as the **article**:

| printed commodity | filed as | seq |
|---|---|---|
| Pepper | `SKINS, FURS, and PELTS \| Pepper` | 3235-3249 |
| China, or Porcelain, and Earthenware | `CHEESE \| CHINA or PORCELAIN, and EARTHEN- WARE` | 397-409 |

Each became a chimera node (`Skins, Furs, And Pelts — Pepper`, a **one-year**
node of GBP 1.36M; `Cheese — China Or Porcelain, And Earthen- Ware`) instead of
reaching its commodity.

## China closes at every level

Foreign 81,699 + 66,799 + 12,950 + 28,276 + 1,551 + 13,083 + 2,131 = **206,489 =
the printed foreign TOTAL**; British 335 + 1,735 + 74 = **2,144 = the printed
British TOTAL**; and 206,489 + 2,144 = **208,633 = the printed grand TOTAL = the
Tier-1**, all to the digit. Every subtotal row here is labelled `TOTAL`, so one
range sufficed.

**Scoped to `as_1891` only.** The chimera node also carries 1886-1896, but this
commodity is already exact in every one of those years except 1891, so a
wholesale fold would double-count.

## Pepper: the block sums to exactly twice its Tier-1

The fifteen rows sum to **69,588,520 — exactly 2 × 34,794,260** — because **two
of them are printed subtotals wearing country names**:

- `East Coast of Africa` **3,314,499** = *Total from Foreign Countries*
  (Holland 1,170,686 + France 250,864 + the four East-Coast sub-entries
  177,253 + 1,339,144 + 199,200 + 177,352 sum to it to the digit)
- `British East Indies` **31,479,761** = *Total from British Possessions*
  (Sierra Leone + Niger Protectorate + Aden + the three British East Indies
  sub-entries sum to it to the digit)

and **3,314,499 + 31,479,761 = 34,794,260 = the Tier-1 exactly.** With both
excluded, the twelve real members sum to 34,794,260 to the digit. The repair
ranges are split around seq 3241 and stop at 3247.

**These are the third and fourth instances of this class**, after `as_1875`'s
`West Coast of Africa (Foreign)` (`reports/nuts_kernels_findings.md`) and
`as_1899`'s `Australasia` (`reports/sheep_lamb_skins_findings.md`). It is now
clearly systematic, and `is_subtotal` — which recognises only labels beginning
`total` — cannot see any of them.

## Supersede-then-hijack, caught in the measurement

Superseding Chandra's stale-head copy **freed the commodity-year**, and
`integrate_sources`' Infinity-only path promptly admitted Infinity's own
`SPICES | Pepper` block — which carries **the same `East Coast of Africa`
subtotal by a different route**. The year came back at 1.0952, over by exactly
3,314,499.

Removed with a `commodity_curation` `drop-country` scoped to 1891; that pass is
arithmetic-guarded, so it acts only if removing the cell brings the year closer
to the printed total.

**The lesson: excluding a bad row from a repair's seq range does not exclude it
from the corpus.** Freeing a year invites every other parse of the same page,
and they carry the same defects. Check the year again after the supersede lands.
