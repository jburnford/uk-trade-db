# Boots and Shoes 1883: a two-up page with its columns crossed

`Leather Manufactures — Boots And Shoes` 1883 read **0.1282** against a Tier-1 of
**123,058 Dozen Pairs** — the only break in a run that closes **exactly** in every
other year 1878-1890.

## The parser crossed the two columns

The page is two-up. The **left** column is a Cwt-denominated leather table
totalling **15,780**; the **right** column is Boots and Shoes, totalling
**123,058**. The pipeline paired the right column's **country labels and VALUES**
with the left column's **QUANTITIES**.

That single fact explains every symptom at once: the year held 15,780 dozen pairs
against a 123,058 anchor; its value column nevertheless looked sane; and
countries that are boot *destinations* — Canada, Turkey, the United States,
Australasia — appeared as origins. Each cell was a chimera, e.g.
`belgium | 78 | 85,585`: the quantity from the left table, the value from the
right.

## The rows are also offset by one, and the left column proves it

The unit-header row (`Cwt. | £`) consumed the first country's cells, so every
number sits one row **below** its label. Read that way the left column has **8
labels and 8 numbers, one-to-one**, and they sum to **15,780 exactly** — the
printed total. The right column has 10 labels and 10 numbers on the same
alignment.

A second, independent proof of the offset: it puts **£233,038 on France**, whose
series runs 43,689 (1882) and 44,632 (1884). The same-row reading would give
France **161** dozen pairs in 1883 — absurd beside those two — and would make
**Turkey** the largest supplier of boots to Britain.

## France is derived, not read — and that is flagged

Nine of the ten quantities are read identically by both engines, and every one of
their unit prices sits inside its own 1881-85 band: Holland £3.67 against
3.58/3.68/3.23/3.63; Belgium £2.13 against 2.65/2.02/2.15; Germany £2.69; the
United States, Other Countries and British North America all £2-4.

France alone is impossible as read. 23,437 dozen for £233,038 is **£9.94 a
dozen** against a French band of **£4.40-5.27** — more than double.

The decisive structural point: the **value column is complete to within £360**
while the **quantity column is short 30,403**. A missing row would cost both
columns in proportion, so this is an under-read *quantity* with its value intact.
France is then the only cell that can absorb 30,403 and stay price-plausible, and
**53,840** gives £4.33 a dozen — 1.6% under 1884's £4.40 — and closes the printed
Total **to the digit**.

Written with `q_tier` **C**, because it is derived from the printed total rather
than read.

> **Objection recorded, not buried.** 23,437 → 53,840 is a **four-digit
> distance**, not an ordinary OCR slip, and **no third source confirms it** —
> as_1886 does contain 53,840, but it is Pork, Fresh from Holland, a coincidence.
> Both engines read ~23,4xx (Chandra 23,437, Infinity 23,137). The figure is
> forced by arithmetic and corroborated by unit price, but it is **not
> independently attested**. The nearest precedent, the as_1883 BPSA sheep-wool
> override in `manual_t1.csv`, had an OCR distance of one digit rather than four.

**Result: 123,058 / 123,058 — exact01. Baseline 3,587 → 3,588 of 9,473**, one
cell changed, no regressions.

## The class, and a screen worth building

Column-crossing on a two-up page is a distinct defect from the two-up classes
already on file (shared `row_seq`, duty-class glue). Its signature is sharp and
cheap to test for:

> a commodity-year whose **quantity** sum falls far short of its Tier-1 while its
> **value** sum matches the printed value total.

Nothing currently looks for that. It would have found this block without reading
a page, and it is the natural companion to the fuzzy-merge screen built last
iteration.

## Still open

- The **£360** the value column is short.
- `Leather — Wrought, Boots And Shoes` holds unit-less 1883/1884 figures for
  Argentina, Brazil, British Possessions in South Africa, Chile, Egypt and
  Colombia — an **export** table riding in the import payload. Not touched here.
- The left column's own 15,780 Cwt table has lost its home and should be filed
  back to whichever leather line printed it.
