# Value-only origin tables never reach `country_year_final`

**Status: diagnosed and sized, NOT applied. The fix is a vote/integrate change
and needs a go/no-go.**

## What the queue said, and what it actually was

`reports/volume_row_outliers.csv` left a group described as "0 exact but nothing
blown" — `Toys` 0/30, `Pork, Salted And Fresh` 0/28, `Hemp, Dressed…` 0/19.
Two different defects were hiding under that label:

- **`Toys` is `nodata`, not "off".** It has 16 origin countries, but every cell
  carries unit `'?'` while its Tier-1 line is a **Value** series, so no cell
  ever matches the modal unit and the reconciliation sees nothing.
- **`Pork, Salted And Fresh` and `Hemp, Dressed And Undressed, And Tow` have no
  origin cells at all** (`countries=1`, i.e. only `§TOTAL`). That is a separate,
  unexamined defect — do not fold the two together.

## Root cause

```
country_year_final rows with quantity IS NULL AND value IS NOT NULL:  0
```

Every value-only origin table in the corpus is discarded. The volumes print a
good many origin tables with **no quantity column at all** — Toys, Watches,
Musical Instruments, Lace, Embroidery, Artificial Flowers, Silk Manufactures,
Leather Manufactures, Painters' Colours — where the only figure per country is
£ value.

- `country_obs` holds **20,064** such import country rows across **2,079**
  `(group, article, year)` blocks.
- `country_year_consensus` **keeps 64,237 of them**: `vote_country_years` votes
  quantity and value independently and tiers them separately, so the value cells
  arrive with real tiers (Toys 1872 germany/holland/belgium/france/other are all
  `v_tier` B).
- They die one step later, at `scripts/integrate_sources.py:221-222`:

```python
if not q or float(q) <= 0:
    continue
```

with the same test at `load_csv` (line 95) for the two-up and run-in CSVs. One
quantity guard drops the entire value-only universe.

Two-up rows reach the CSV with the value written into the **quantity** column
and no unit (`exports/twoup_country.csv`: `as_1873,import,,TOYS,,Belgium,,1873,61289,`),
which is why the surviving `Toys` cells show up as unit `'?'` in the payload
rather than as values. That is a second, smaller inconsistency in the same area.

## The prize — measured, not estimated

`reports/valueonly_block_closure.csv` sums each value-only block's country cells
(printed totals and `Region : Sub` rows excluded) and compares against the Tier-1
**value** line for the same signature and year:

| | blocks |
|---|---|
| have a T1 value anchor | 586 |
| **close EXACTLY (≤0.1%)** | **246** |
| within 5% | 86 |
| off | 254 |

**240 distinct commodity-years close exactly.** Worked examples where the
country values sum to the printed national value to the pound:

```
Toys                            1872   325,242 = T1 (tier A)
Watches                         1872   351,199 = T1 (tier A)
Silk Manufactures, Out of Europe 1872  287,258 = T1 (tier A)
Flowers, Artificial             1872   411,540 = T1 (tier A)
Embroidery and Needlework       1872    87,097 = T1 (tier A)
Musical Instruments             1873   602,106 = T1 (tier A)
Linen Manufactures              1873   234,903 = T1 (tier A)
Drugs, Unenumerated             1873   334,377 = T1 (tier A)
```

Payload side: **899 T1 commodity-years across the commodities whose T1 modal
unit is `Value`, GBP 71.3M, are `nodata` today.** Seventeen of them already have
origin cells sitting unusable in unit `'?'` — `Silk — Manufactures` (GBP 12.8M),
`Shells Of All Kinds` (GBP 11.3M), `Leather Manufactures — Unenumerated`,
`Painters' Colours And Pigments`, `Lace`, `Musical Instruments`, `Watches`,
`Toys` and the rest.

## Why this was not applied

Admitting value-only cells changes `integrate_sources.py` — the vote/integrate
pipeline — and grows `country_year_final` by up to ~64k rows that every
downstream consumer (validators, detectors, map, gold harness) currently never
sees. `reconcile_baseline.py` and `build_viz_payload.py` would also need to
reconcile a value series against a value anchor rather than a quantity against a
quantity. That is squarely the "changes the vote — stop and ask" case.

**A payload-only fix is impossible**: `build_viz_payload.py` reads
`country_year_final`, which holds none of these rows.

## If it goes ahead — the shape of the change

1. `integrate_sources.py`: relax the guard to admit `q IS NULL AND v > 0`, and
   carry `unit='Value'` (or a dedicated `measure` column) so the cells are never
   mistaken for quantities.
2. `parse_twoup.py` / `exports/twoup_country.csv`: write value-only figures to
   the **value** column, not the quantity column.
3. `build_viz_payload.py` / `reconcile_baseline.py`: reconcile a `Value` T1
   series against the country **value** sum.
4. Re-run the detector battery — the 254 blocks that do **not** close are the
   new work this exposes, and some will be glue of the kind rounds 26-36 have
   been clearing.
