# Two residues, and the fused prefix that hid them

Worked 2026-07-31 (`/loop /next-defect`).
**exact01 3,528 → 3,531 (+3), denominator unchanged at 9,515, zero true
regressions. Seven commodity-years moved from `nodata` to measured.**

## Opium 1880-82, bracketed-gap rank 5

Iteration 20 folded `Onions — Opium` into `Opium` and reported eleven closing
years where there had been one. It left a sibling behind: **`Onions — Raw ·
Opium`**, holding the 1880 and 1881 origin tables with no anchor at all.

The proof is immediate — **1881 sums 793,146 = the Opium Tier-1 to the digit** —
and the country list settles it without any arithmetic: **Turkey, Persia,
China, the United States**. That is an opium origin list, not an onion one.

- **1881 → exact01.**
- **1880 → within5**: 363,675 in `Lb` plus a 31,699 cell whose unit was never
  captured, together 395,374 against an anchor of 400,374. Admitted as honest
  partial measurement, not a close; the 5,000 shortfall has no second source to
  arbitrate it.
- **1882 remains open.** No source found; it is the one year of the three with
  nothing to attach.

## Why no tool found it: a fused prefix defeats signature equality

`match_by_name` should have caught this and could not. The source's article
tail is `Raw · Opium`, which signs as `('opium', 'raw')`; the host signs as
`('opium')`. **Equality fails on a token the fusion added.**

So the relation set gains **`sig-subset`**: the host's signature being a strict
subset of the source's. That is precisely the shape fusion produces. It is a
much looser test, so it is guarded twice — the host signature must carry **at
least two tokens** (a single-token host like `Rum` or `Fir` would otherwise
match every article containing that word), and the source-anchor guard from the
previous iteration still has to pass.

## What the subset relation immediately found

**`Stones, Marble, Rough Hewn, Or Manufactured (Other Than Works Of Art)`** →
**`Stones, Rough, Hewn, Or Manufactured (Other Thanworks Of Art)`** — £4.6M.

A textbook shadow/orphan pair: the host holds Tier-1 for 1893-99 and **no
countries**, the source holds countries for 1895-99 and **no anchor**. The
names differ only by the fused group token `Marble` and an OCR space loss in
the parenthetical.

The tool reports **one** exact year. The truth is stronger — **all five
overlapping years agree within 1%**:

| year | source | anchor | |
|---|---|---|---|
| 1895 | 574,578 | 574,884 | 0.05% |
| 1896 | 678,918 | 673,206 | 0.85% |
| **1897** | **740,442** | **740,497** | **0.007%** |
| 1898 | 860,777 | 869,782 | 1.04% |
| 1899 | 889,533 | 891,173 | 0.18% |

**Worth noting against the tool's own output**: it counts only years agreeing
*to the digit*, so a pair whose five years all sit within 1% is reported as
one-year evidence. The ranking understates corroboration of exactly this kind,
and the numbers have to be read, not the count.

Result: 1895 and 1897 to `exact01`, 1896/1898/1899 to `within5`, five years
that read `nodata` before.

## Still open here

`Opium` 1882 — anchor 478,624, no origin table found in either engine under any
label yet tried.
