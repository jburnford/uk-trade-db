# Zinc — Manufactures, Unenumerated: four holes, four different causes

Worked 2026-07-29 (`/loop /next-defect` iteration 10). Picked because the
series closes **1.0000 in every year 1878–1893 except four**, and a hole in a
series like that is a parse defect by construction.

| year | before | after | |
|---|---|---|---|
| 1879 | 0.0000 | **1.0000** | `ZINO` — OCR garble of the group |
| 1884 | 0.0000 | **1.0000** | glue block under `WOOLLEN MANUFACTURES` |
| 1891 | 0.0000 | **1.0000** | label shortened to `Manufactures` |
| 1892 | 0.0000 | **0.99969** | mangled group **and** wrong flow |

Every one of the four blocks was **complete and already in the database**, and
every one closes on its own printed total. Nothing was reconstructed.

## The four causes

### 1879 — `ZINO`

`as_1879` `country_obs` carries the whole zinc import section under the group
`ZINO`. Germany 74,256 + Holland 116,063 + Belgium 115,034 + Other 4,072 =
**309,425 = Tier-1 to the digit**.

`ZINO` is an unambiguous OCR garble (C read as O): it appears as the import
group in `as_1877` and `as_1879` and the re-export group in `as_1885` (and
`as_1884` in the Infinity copy), and its article list is zinc's own throughout
— *Crude in Cakes, Ore, Manufactures Unenumerated, Goods Unenumerated,
Manufactured*. The Infinity copy of the same page reads the group as `ZINC`.
Fixed with a `group_aliases` row, which is what that file is for.

### 1884 — glue under `WOOLLEN MANUFACTURES`

Germany 138,826 + Holland 152,450 + Belgium 108,657 + France 1,230 + Other 440
= **401,603 = Tier-1 to the digit**. Three independent confirmations that it is
zinc and not wool:

1. **Country profile.** Germany/Holland/Belgium are the whole of zinc's supply
   in every neighbouring year, and none of woollens'.
2. **Implied price.** £390,157 ÷ 401,603 = **£0.97/cwt**, against £1.12 (1879)
   and £1.28 (1891) for zinc manufactures — and an order of magnitude below any
   woollen manufacture.
3. 1884 was the only hole in an otherwise unbroken 1.0000 run.

### 1891 — the label lost ", Unenumerated"

`as_1891` prints the line as plain `Manufactures`, which sends it to a separate
payload node. **Both** printed totals close: the five foreign members sum to
403,019 = the printed foreign TOTAL, and + Channel Islands 144 = **403,163 =
Tier-1 to the digit**. `supersede_years` scoped to 1891 so the node's
1893/1894/1896 cells are untouched.

### 1892 — two defects at once

The group label is OCR-mangled to **`ZINC'd)`** — the *same mangle pattern*
`flow_repairs.csv` already records for **`Wool'd)`** in this very volume — and
the block is filed as **`export_uk`**. It is an import table: Germany 76,833 +
Holland 216,238 + Belgium 82,679 + France 3,252 + Other Foreign 40 = 379,042 =
the printed foreign TOTAL, + 119 British = **379,161 = the IMPORT Tier-1 to the
digit**, with the same Germany/Holland/Belgium profile as 1891.

**Repaired with `group_repairs` rather than `flow_repairs`, deliberately.**
`flow_repairs.csv` keys on (volume, article_group, year), so a row for
`as_1892 / ZINC'd)` would also flip the **62 genuine export rows** sitting
under the same mangled group (`Unmanufactured` 32, `Manufactured` 30). A
`group_repairs` row matching `flow='export_uk'` is scoped to the eight rows
actually verified, and step 6 emits repaired rows as imports regardless of the
flow they matched on. **Worth remembering: a mangled group label can carry both
flows, and the coarse-keyed repair file cannot separate them.**

The 119 shortfall is the British half's printed total, whose member label the
parser lost — 0.031%, still inside 0.1%.

## Result

Baseline 9,634 c-y: exact01 3,139 → **3,143** (32.6%), GBP within 0.1% 51.0%,
within 5% 68.0% → **68.1%**. Four commodity-years nodata → EXACT, **zero
regressions** — the payload diff shows exactly those four rows and nothing
else, so the `ZINO` alias disturbed no other commodity.

## Left open

- 1889 reads 1.0130 and 1893 reads 0.9991 — small residuals, untouched.
- The `ZINO` alias also relabels that group's *other* articles (`Ore`,
  `Manufactured`, `Goods, Unenumerated`, `Crude, in Cakes`) in as_1877/1879/
  1885. The payload diff shows no change from them, meaning those cells were
  already landing elsewhere or are duplicates — worth a look if the zinc family
  is revisited.
- `Zinc — Manufactures` still holds 1893/1894/1896 cells that may be the same
  printed line under the same shortened wording. They were left alone because
  those years already close in the target and folding them risked a
  double-count; the 1891 repair is year-scoped for the same reason.
