# `Tons. Cwts` — decoding the fused two-column quantity

Worked 2026-07-29 (`/loop /next-defect` iteration 13), following the class
named in iteration 12 (`reports/feathers_ornamental_findings.md`).

## The defect

The `METAL … Wrought or Manufactured` origin tables print **two quantity
columns, `Tons.` and `Cwts.`**. Both engines read the header as one compound
unit (`Tons. Cwts`) and the two figures as one number. So Germany 1893 entered
the corpus as **34,515 tons** where the print says **345 tons 15 cwt** — a
hundredfold error, carried into `country_year_final` and onto the map.

139 rows across 11 volumes. Confined to `METAL` in as_1883–as_1894, plus two
stray single rows (`TIN | Ore` 1874, `GOLD | Ore of` 1880).

## The decode, and how it is proved

Split each fused figure into `(tons, cwts)` with **cwts ≤ 19**, then require
the members to sum — **with the cwt carry at 20 to the ton** — to the block's
own printed sub-total. The carry is what makes it exact and is the reason a
naive "strip the last digit" reading fails.

`as_1894`, worked through:

    Germany     51,218 →   512 t 18 cwt
    Holland      9,456 →   945 t  6 cwt
    Belgium      1,327 →   132 t  7 cwt
    France      55,816 →   558 t 16 cwt
    USA         20,512 →   205 t 12 cwt
    Other        1,019 →    10 t 19 cwt
                          ─────────────
                        2,362 t 78 cwt  =  2,365 t 18 cwt
    printed foreign TOTAL 236,518    →  2,365 t 18 cwt   ✓
    printed British TOTAL     116    →      1 t 16 cwt
    printed grand   TOTAL 236,714    →  2,367 t 14 cwt   ✓  (2,365t18 + 1t16)

**Every decode emitted is UNIQUE.** The solver enumerates *every* combination
of *every* member's candidate readings and counts how many close. Exactly one
does, in each of the four blocks admitted — so this is not a subset-sum
coincidence, which is the standing risk with any closure reached by search.
Blocks with more than one closing combination would have been reported
ambiguous and dropped; none were.

**1893 and 1894 carry a second, independent confirmation.** Their grand totals
decode to 2,370 t 15 cwt and 2,367 t 14 cwt against Tier-1 quantities of
**2,371** and **2,368** Tons (the abstract rounds), and each block's value
column totals **£301,953** and **£286,696** — the Tier-1 values **to the
pound**.

| volume | closes on | proof |
|---|---|---|
| as_1884 | printed grand 1,436 t 19 cwt | unique decode |
| as_1888 | printed grand 1,806 t 1 cwt | unique decode |
| **as_1893** | printed foreign 2,367 t 3 cwt | unique decode **+ T1 tons + T1 value** |
| **as_1894** | printed foreign 2,365 t 18 cwt | unique decode **+ T1 tons + T1 value** |

27 `manual_rows` (`replace=1`), tier A for 1893/94, tier B for 1884/88.

## Five blocks did NOT decode — left alone

`as_1885` (grand 19,193), `as_1889` (17,617), `as_1890` (18,187), `as_1891`
(217,813), `as_1892` (223,011). No combination of member readings closes on any
reading of their printed totals, which means something else is wrong in them as
well — a lost row, a slipped label, or a misread total. **Guessing a decode
that does not close would be exactly the coincidence this method is built to
avoid.** Queued.

## Why the baseline does not move

Zero commodity-years changed. The reason is structural and is the *same shape*
as the feathers case:

1. **The anchor is de-headed.** The Tier-1 series (2,371 / 2,368 / 2,618 Tons
   for 1893-95) sits in a bare **`Wrought Or Manufactured`** payload node with
   no countries at all. The country data sits in `Metal — Wrought Or
   Manufactured`.
2. **And that host node is a two-commodity chimera.** It also carries a **Cwt**
   Tier-1 for 1866-1879 whose values (2,109,885 in 1878, 2,246,387 in 1879) are
   *the iron-manufactures-unenumerated series* — a duplicate shadow of the
   commodity repaired in iteration 9. `reconcile_baseline` takes the **modal**
   T1 unit, and Cwt has fourteen years against Ton's three, so folding the Ton
   anchor in would still leave the Ton years unmeasured.

So this correction is real but invisible to the metric until the node is split
by unit. **That is the third commodity this session whose defect is masked by a
de-headed anchor** (drugs, feathers, metal) — worth treating as a class in its
own right rather than one commodity at a time.

## Noted in passing

The as_1888 block also exists in `country_obs_twoup` under a **different
article string**, still carrying the fused figures. It is a pre-existing
duplicate (not introduced here — `replace=1` drops the *consensus* copy only,
and the payload diff confirms nothing moved), but it means the uncorrected
numbers survive in one gap-fill source. Clearing it needs a `supersede` keyed
on that article.

Baseline unchanged: 9,634 c-y, exact01 **3,144** (32.6%), GBP 51.0% / 68.1%.
