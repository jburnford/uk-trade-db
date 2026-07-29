# Export tables riding in as imports — the twoup flow-tag leak

Written 2026-07-28, prompted by the user spotting `Woollen And Worsted
Manufactures — Broad Cloths, Coatings, Duffs, &C., Plain, All Wool` in the
import payload. **Survey, not a repair — nothing here is fixed.** This is the
population measurement `EXPORT_CAMPAIGN_PLAN.md` phase 0 asks for.

## The case that started it: broad cloths

The user was right. Evidence, in order of strength:

1. **The primary engines say so.** Every `Broad Cloths, Coatings, Duffs...`
   block in `country_obs` and `country_obs_inf`, as_1872 through as_1881, is
   tagged `flow='export_uk'`. Not one is tagged import.
2. **`country_obs_twoup` disagrees with itself.** It tags as_1876/77/79/80
   `export` and as_1874/78/81 `import`. Same commodity, same layout, same
   parser — the flow tag is simply unreliable in that engine.
3. **The destinations are destinations.** Bengal and Burmah, Madras, Bombay,
   Straits Settlements, Hong Kong, British West India Islands and British
   Guiana, Chili, Peru, United States of Colombia, Egypt, Turkey Proper — plus
   a **United States (Atlantic) / (Pacific)** split, which is an export-table
   convention. Nobody imports West-of-England broad cloth from Madras.
4. **No T1.** The commodity has no import national line at all, because there
   isn't one.

What leaked into `country_year_final` (which is import-only):

| year | rows | source | declared value |
|---|---|---|---|
| 1874 | 10 + 11 + 19 | twoup | £4.01e12, £2.39e12, £1.54e13 |
| 1878 | 20 | **human** | £2,348,667 |
| 1881 | 21 | twoup | £12,421,000 |

Two separate defects stacked: it is export data, *and* the 1874 values are
fused-digit garbage in the £trillions. The 1878 rows came in through
`manual_rows` — export data was hand-keyed into the import reference file.

## The general shape

A cheap engine-disagreement screen, complementary to the arithmetic test in
`scripts/detect_flow_leakage.py` (which matches a block's printed total to the
export_uk/reexport national line):

> find blocks that `country_obs_twoup` tags `import`, where **both** primary
> engines carry that (volume, group, article) **only** as `export_uk` and
> never as import.

Restricting to export-only articles matters. My first pass omitted it and
returned 531 blocks — wrong, because most commodities legitimately appear in
*both* the import and export sections of a volume, so a twoup import block
matching a primary *export* block proves nothing. Corrected:

**451 blocks, 4,692 rows.**

Largest by declared value:

| volume | group | article | rows | value |
|---|---|---|---|---|
| as_1872 | ZINC OR SPELTER | Crude, in Cakes | 4 | £774,007,803 |
| as_1876 | BRASS | Manufactures of, not being Ordnance | 16 | £148,333,177 |
| as_1873 | COTTON MANUFACTURES | Piece Goods, Plain | 48 | £65,546,732 |
| as_1878 | COTTON MANUFACTURES | Piece Goods, Plain | 52 | £58,306,488 |
| as_1873 | COTTON MANUFACTURES | Piece Goods, Printed | 49 | £43,098,142 |
| as_1874 | COTTON MANUFACTURES | Piece Goods, Printed | 49 | £39,056,796 |
| as_1892 | WOOLLEN MANUFACTURES | Stuffs | 8 | £18,138,154 |
| as_1882 | LINEN MANUFACTURES | Plain, Unbleached or Bleached | 32 | £9,519,512 |

The top two values are themselves absurd (£774M of zinc in four rows) — the
same fused-digit corruption as broad cloths 1874, which is a hint that
whatever loses the column heading also mangles the number parsing.

Dominated by **COTTON MANUFACTURES piece goods**, then woollen, then linen and
jute — exactly the families the plan memory already names.

## How much reached the import table

Matching leaked (article, year) pairs against `country_year_final`:

| source | rows | value |
|---|---|---|
| twoup | 2,510 | £283,499,519 |
| consensus | 2,353 | £166,666,101 |
| groupfix | 1,042 | £333,623,731 |
| infonly | 94 | £2,240,589 |
| human | 64 | £24,166,419 |
| subentry | 11 | £55,723 |

**Read this carefully.** The match is on (article, year), not row-by-row, so
only the `twoup` line is a confident leak count — the `consensus` and
`groupfix` rows could be genuine imports of a same-named article from another
volume. Treat **~2,510 rows / £283M as the firm floor** and the rest as
needing row-level confirmation. Do not quote the £838M total.

## What it would take

- `reference/flow_repairs.csv` already supports this, keyed on
  (volume, article_group, year, flow_from, flow_to). It currently holds **one**
  row, running the other direction (as_1892 wool, export_uk -> import). The
  451 blocks would be `flow_from=import, flow_to=export_uk`.
- Before writing 451 repair rows, confirm the screen row-by-row on a sample:
  the flow-tag disagreement is strong evidence but it is still an engine
  disagreement, not arithmetic. The arithmetic test — block total equals the
  export_uk national line to the digit — should be run over these 451 to
  promote them from "probable" to "proved". `detect_flow_leakage.py` already
  does exactly that and should simply be pointed at this candidate list.
- The fused-digit values (zinc 1872, brass 1876, broad cloths 1874) are a
  *separate* defect and want their own pass; do not let the flow fix bless
  £trillion cells.

This is phase-0 measurement for the export campaign, which remains **deferred
awaiting the user's go/no-go**. Nothing above has been acted on.
