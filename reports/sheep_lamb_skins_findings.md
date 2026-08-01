# Sheep and lamb skins 1881: a column-split page, and half the answer in each engine

Worked 2026-08-01 (`/loop /next-defect`), bracketed-gap rank 3, GBP 1.28M.
**`Skins — Sheep And Lamb, Undressed` 1881 went from `nodata` to exactly
1.000000** — 6,475,264 of a Tier-1 of 6,475,264.

**exact01 3,545 → 3,546, nodata 4,342 → 4,341, denominator unchanged at 9,497.
One commodity-year changed in the whole corpus; zero regressions.**

## The table, and it closes on both columns

It is in the **right-hand column** of the as_1881 import country page, beside
SILK Manufactures and immediately above SILVER ORE, headed `„ Sheep,
Undressed :`:

| Germany | Belgium | France | Turkey | Argentine Rep. | BP South Africa | Australasia | Other | **Total** |
|---|---|---|---|---|---|---|---|---|
| 230,229 | 378,547 | 814,514 | 293,000 | 580,697 | 2,146,354 | 1,163,771 | 868,152 | **6,475,264** |
| 24,036 | 34,613 | 106,585 | 26,259 | 85,197 | 274,501 | 156,600 | 94,997 | **802,788** |

The eight members sum to **6,475,264 = the block's own printed Total = Tier-1
to the digit**, and their values sum to **802,788 = the printed value total, to
the digit**. Both printed columns close independently.

## A new failure class: the column split, with half the answer in each engine

Neither engine's *parse* contains this table, and neither engine's *raw text*
contains all of it either — but between them it is complete:

- **Chandra** puts the country label and its figure in **alternating rows of
  the same fourth cell** — `„ France - - -` in one row, `814,514` in the next
  — so no label can be paired with a number. It has the **country order**.
- **Infinity** keeps the two numeric columns together and correctly paired, but
  **loses the country labels to the left-hand SILK block**. It has the
  **quantity/value pairs**.

Chandra supplies the names, Infinity supplies the pairs, and the two agree on
every quantity. This is distinct from the two classes worked immediately before
it — a *stale or phantom label* (silver ore 1894) and a *dropped fractional
unit* (feathers 1890) — and distinct again from the as_1875 nuts page, where
the whole page collapsed in both extractors. **Here the geometry failed
differently in each engine, and the repair is only possible because it failed
differently.**

Recovered as eight `manual_rows`, tier B, under `SKINS, FURS, and PELTS |
Sheep, Undressed` — the label the sibling years 1880 and 1882 already arrive
under. `commodity_curation` row 673 folds that node into this one **unscoped**,
checked before writing, per the year-scoped-fold trap found the previous
iteration.

## Still open in this commodity — and it is much larger than what was fixed

| year | ratio |
|---|---|
| 1880 | 0.9907 |
| 1882 | 0.9700 |
| 1886 | 0.8642 |
| 1890 | 0.9237 |
| **1894** | **0.1662** |
| **1895** | **0.1622** |
| **1896-1899** | **0.00 (nodata)** |

**The 1894-99 collapse has a strong lead already on file.** `as_1898` carries a
block `SILVER, Ore of… | Skins, Sheep, undressed` at seq 19832-20013 — the
sheep-skin 1894-98 comparative wearing the stale SILVER head that
`reports/silver_ore_findings.md` describes. **Its 1894 grand TOTAL is
13,831,508, which is this commodity's 1894 Tier-1 exactly.** Its British half
sits under the phantom region article `Eastern Coast of Africa`.

Note a debt created there: the silver-ore repair of 2026-08-01 replaced twelve
`article=NULL` cells that had absorbed the *Eastern Coast of Africa* half of
this table, so those sheep-skin figures are currently in no commodity at all.
Re-heading the block to `SKINS, FURS, AND PELTS | Sheep, Undressed` would both
repay that and put six years of this commodity back — but it is a taxonomy
change touching several chimera nodes and was deliberately not attempted inside
one iteration.

## Also built this iteration

`scripts`-free, in the session scratchpad: a grep of every volume's raw
markdown for printed **cross-reference** rows (`„ Other Sorts. See FRUIT.`),
the class that closed nuts and kernels 1875. **538 rows across all 28
volumes**, 12-33 per volume. as_1881 has 14 and none of them is a sheep-skin
reference, which is what ruled that explanation out here in one query. The list
is worth turning into a permanent screen.
