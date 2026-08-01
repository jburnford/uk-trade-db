# Figs 1880-82: the duty tables, and a fold broken by adding data to a node

Worked 2026-08-01 (`/loop /next-defect`), bracketed-gap rank 3, GBP 608k.
**All three years went from broken to exactly 1.000000** — 85,913, 138,225 and
73,578 Cwt.

**exact01 3,556 → 3,559 (+3), nodata 4,331 → 4,330, denominator unchanged at
9,497. Three commodity-years changed; zero regressions.**

## Defect one: the fifth export table, and the signature is now confirmed

The only figs data for those years was four two-up gap-fill rows naming
**`Australia` 2,593 (1880), `Australasia` 3,700 (1881) and 5,180 (1882)** plus
`Other Countries`. Australia is not a source of figs — it is a destination.

**Fifth instance of the export-leakage class**, and the signature holds across
all five:

| commodity | year | ratio before |
|---|---|---|
| Fruit — Unenumerated : Raw | 1875 | 0.06 |
| Leather Manufactures — Unenumerated | 1883-84 | 0.07 / 0.09 |
| Saltpetre | 1879 | 0.08 |
| **Fruit — Figs** | **1880-81** | **0.11 / 0.07** |
| Toys | 1880 | 0.12 |

**A small NON-ZERO ratio of 0.06-0.12 is the tell.** (Figs 1882 read 0.00 only
because that year's copies additionally sat under a stale `FLAX` head and never
reached the commodity at all.) Removed by supersede — two-up rows cannot be
displaced any other way.

## Defect two: the import tables are in the duty tables

Absent from both parses, and **not in the country section at all** — they are in
the **duty tables**, where the fig line is printed with its country breakdown
**run into a single cell**:

```
" Figs: From Spain - - - - " Turkey, Asiatic - - - - " Other Countries - - - -
Cwts. 16,285 53,332 16,296
£ 18,421 138,954 21,910
```

**All three quantity columns close on the Tier-1 to the digit:**

| year | members | Tier-1 |
|---|---|---|
| 1880 | 16,285 + 53,332 + 16,296 | **85,913** |
| 1881 | 9,332 + 115,916 + 12,977 | **138,225** |
| 1882 | 6,912 + 6,018 + 59,067 + 1,581 | **73,578** |

1882's value column closes exactly too (165,680). 1880's is 3 short of a printed
179,288 and 1881's 300 over a printed 291,127, and Infinity resolves neither (it
reads Spain 1880 as 18,121, which is *worse*). Those residuals are cosmetic: the
commodity's modal unit is Cwt, so the metric reads the quantity column.

**Worth carrying: the duty tables are a second place origin breakdowns live.**
Every prior item in this run looked only at the country section.

## The trap this iteration measured — a new mode

The rows were first written under `FRUIT | Figs and Fig Cake`, which is what 115
of the corpus's own fig rows use. **That created a new node `Fruit — Figs And Fig
Cake` holding 22 countries and stripped `Fruit — Figs` down to 7** — costing
**4 exact01** and moving the **denominator 9,497 → 9,501**.

The two spellings have **different signatures** and were being held together by
`build_viz_payload`'s **era-wording fold**, whose precondition is that one node's
year span strictly precedes the other's (`min(a) < min(b) and max(a) < max(b)`).
**Adding 1880-82 to the Cake node broke that precondition and the fold stopped
firing.**

**So: adding data to a node can break an era fold that depended on its year
span.** This is a sixth mode of [[payload-node-string-keying]], and the first
where the damage shows up in the *denominator* — which is the tell to watch for,
since a changed denominator means a node appeared or vanished.

Relabelled to `FRUIT | Figs` — the spelling the node's own name carries — and all
three years closed.

## Still open in this commodity

1866-1871 `nodata`; 1872 (0.155), 1873 (0.103), 1874 (0.323) and 1878 (0.357)
all show the export-leakage signature; 1885 and 1891 `nodata`; **1893 reads
1.9018**, nearly double.
