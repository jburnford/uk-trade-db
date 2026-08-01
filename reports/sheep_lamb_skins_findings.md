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

---

## The late era, 2026-08-01: four years out of `nodata`, and the subtotal that wears a country's name

Same iteration's follow-on, taking the item the section above queued.

**nodata 4,341 → 4,337, within 5% 1,105 → 1,108, under 287 → 288, exact01
unchanged at 3,546, GBP-weighted exact01 51.8% → 51.9%. Zero regressions.**
The node goes from **GBP 26.96M to 33.62M** and from 51 to 58 countries.

| year | before | after |
|---|---|---|
| 1882 | 0.9700 | **0.9976** |
| 1895 | 0.1622 | **0.9482** |
| 1896 | *nodata* | **0.9967** |
| 1897 | *nodata* | **0.9954** |
| 1898 | *nodata* | 0.8937 |
| 1899 | *nodata* | **0.9745** |

### Where it was

`as_1899` carries the 1895-99 comparative **under the right group** (`SKINS, AND
FURS`) — but split across two parser labels, neither of which reaches the
commodity:

- the twelve European members under the article `Skins, Sheep, undressed`
  (seq 19590-19649), which forms its own orphan node;
- **everything else** — the rest of the foreign section, the whole British
  section and both printed subtotals — under the phantom region article
  **`Eastern Coast of Africa`** (seq 19650-19774), which
  `repair_country_as_article` unfiles into the bare `Skins, And Furs` node.

**Proof the block is this commodity:** its grand TOTAL row reproduces the
abstract's own five-year line to the digit in four of five years — 1896
13,364,634, 1897 14,539,056, 1898 15,077,072, 1899 15,478,816 — and 1895 reads
15,082,442 for a printed 15,682,442, a single 6-for-0 misread in the leading
group.

### The trap in this block: a subtotal wearing a country's name

The row labelled **`Australasia`** at seq 19765-19769 is the *Total from British
Possessions*. It equals **grand minus foreign to the digit** in 1896
(11,168,107), 1897 (11,119,089) and 1898 (11,625,412). `integrate_sources`'
`is_subtotal` guard only recognises labels beginning `total`, so admitting the
range wholesale would have **doubled the British half**. Both repair ranges stop
short of it (19649 and 19764).

This is the second instance on file of the same class — the first was the
as_1875 `West Coast of Africa (Foreign)` row carrying its block's own grand
total in `reports/nuts_kernels_findings.md`. **A region-named subtotal is a
recurring shape, not a one-off, and no guard catches it.**

### Honest limits

The recovery is **partial, not exact**: foreign sections run 3,600-114,200
light and 1899's British section is one member short by 391,290. 1898 lands at
0.8937 only because of an **anchor disagreement** — `as_1899` prints the 1898
total as 15,077,072 while the payload's Tier-1 is 16,742,764; against as_1899's
own print the members give 0.9924.

### A pre-existing bad figure that the repair made visible — and then fixed

Landing 157 rows in this commodity changed what `build_viz_payload`'s
unit-healer did with an unrelated cell: **as_1882's `british east indies`
925,991, previously parked in the `?` bucket and invisible to the metric, was
healed into `Number` and flipped 1882 from 0.9700 to `over` at 1.0834.**

The repair did not create it, and the price test condemns it: at a value of
13,807 that quantity prices the skins at **GBP 0.0149 each against a band of
0.063-0.209 across every other member of the same year** — a 6-14× outlier.
**Infinity reads 225,291** where Chandra reads 925,991, both engines agreeing on
the value; 225,291 prices at 0.0613, squarely in band, and brings the year to
**8,145,718 / 8,165,718 = 0.9976**. Replaced.

**Still open there:** the country *label* is wrong too. The as_1882 raw reads
`„ British East Indies - 318,585 | 19,992` then `„ Australasia - 225,291 |
13,807`, while Chandra interposes a stray `Total - 3,407,991` row and slips the
labels by one — so the payload's `aden` cell is really British East Indies and
its `british east indies` cell is really Australasia. **A row-slip cascade
needing its own pass; only the quantity was corrected here.**

### Still open in this commodity

**1894 at 0.1662 is now the largest**, and its table is located: `as_1898 |
SILVER, Ore of… | Skins, Sheep, undressed` seq 19832-20013, whose 1894 grand
TOTAL 13,831,508 is this commodity's 1894 Tier-1 exactly. `as_1897` carries a
third copy under `SHELLS of all kinds`. Also open: 1886 at 0.8642, 1890 at
0.9237, and the 1898 anchor disagreement above.

---

## 1894 closes — and the volume's own-year printing was the worse source

Same day, the item the section above queued. **0.1662 → 0.99977. exact01 3,546
→ 3,547, under 288 → 287, denominator unchanged at 9,497. One commodity-year
changed in the whole corpus; zero regressions.** Every year 1880-1899 in this
commodity is now measured.

### Where 1894 was, and where the 0.1662 came from

The origin table is the 1894-98 comparative in `as_1898`, wearing the
`SILVER, Ore of…` head — twelve European members under the article `Skins,
Sheep, undressed` (seq 19832-19891) and the rest of the foreign section, the
whole British section and all three printed subtotals under the phantom region
article `Eastern Coast of Africa` (seq 19892-20017). Its 1894 grand TOTAL is
**13,831,508 = the Tier-1 to the digit**; its printed foreign (2,266,302) and
British (11,565,205) subtotals sum to 13,831,507; its members reproduce those to
−960 and −49.

Unlike the `as_1899` copy, this block prints its British subtotal as a literal
`TOTAL`, so no range gymnastics were needed.

**The 2,298,931 the payload had been carrying was `as_1894`'s own-year printing
of the same table — and that copy is truncated.** It prints only the foreign
half: fourteen members, then a mismatched `TOTAL` of 24,368, and the next
article begins. There is no British section at all. Its fourteen members sum to
**exactly 2,298,931**.

**Worth stating plainly: an own-year printing is not automatically the better
source.** Here the five-year comparative in a volume four years later is
complete and closes on three printed subtotals, while the year's own volume
carries a truncated fragment.

### Two cells the two printings disagree on, both arbitrable

Admitting the block took 1894 to **1.0182** — over, from two duplicates:

- **Brazil.** `as_1894` reads 72,890, `as_1898` reads 12,820, and **both prints
  carry the same value, 1,165**. The price test decides: 72,890 prices the skins
  at **GBP 0.016 each against a 1894 band of 0.058-0.140** in the same block
  (USA 0.058, Uruguay 0.107, Argentine 0.127, Chile 0.140) — a 6× outlier —
  while 12,820 prices at 0.091, squarely in band. Replaced.
- **Turkey.** `as_1894` prints one combined `Turkey` row of 195,291/11,670;
  `as_1898` splits the same line into `Turkey, European` 25,360/2,065 and
  `Asiatic` 168,301/9,479, summing to 193,661/11,544. Both were in the payload,
  so the same trade was counted twice at two granularities. Dropped the
  aggregate (`commodity_curation drop-country`, scoped to 1894 — the pass is
  arithmetic-guarded, so it removes the cell only if that brings the year
  closer).

13,828,385 / 13,831,508 = **0.99977**.

### The debt from the silver-ore iteration is repaid

`reports/silver_ore_findings.md` records that the 2026-08-01 silver repair
replaced twelve `article=NULL` cells which had absorbed the *Eastern Coast of
Africa* half of this table, leaving those sheep-skin figures in no commodity at
all. They now land where they belong.

### The commodity now

Every year 1880-1899 is measured. Exact: 1881, 1884, 1885, 1887, 1888, 1889,
1891, 1892, 1893, **1894**. Within 5%: 1880 (0.9907), 1882 (0.9976), 1883
(0.9993), 1885, 1896 (0.9967), 1897 (0.9954), 1899 (0.9745). Still short:
**1886 (0.8642)**, **1890 (0.9237)**, **1895 (0.9482)**, and **1898 (0.8937),
which is an anchor disagreement rather than missing data** — `as_1899` prints
the 1898 total as 15,077,072 against the payload's Tier-1 of 16,742,764, and the
members give 0.9924 against as_1899's own print. The as_1882 row-slip cascade
(labels, not quantities) also stands.
