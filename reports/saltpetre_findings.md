# Saltpetre (Nitrate of Potash) — the seeds-glue arc, 1893-1900

## The defect

The `SALTPETRE (Nitrate of Potash)` head in the five-year volumes absorbed a
whole seeds section — its articles include `Rape` at 14,812,573 quarters and
`Clover and Grass` at 5,052,279 — and the payload summed that glue with the good
readings. Six of the eight Tier-1 years ran between **6.1× and 17.9×** their
printed national line.

## 1893-1896 — closed 2026-07-27 (iteration 35)

Each year's correct table is in its own **single-year** volume and closes exactly
on its own printed grand total, which is the Tier-1 figure:

```
as_1893 seq 2958-2966   109,738 + 132,830 = 242,568 = T1
as_1894 seq 2993-3001   156,304 + 133,059 = 289,363 = T1
as_1895 seq 2897-2905   143,655 +  84,822 = 228,477 = T1
as_1896 seq 2961-2970   130,206 + 210,544 = 340,750 = T1
```

`supersede_years` is volume-agnostic, so each year needed its own repair row:
supersede the year, re-admit that year's own block. Ratios went
6.14 → 1.0000, 12.20 → 1.0000, 14.96 → 1.0011, 7.20 → 1.0000.

**The mistake that iteration cost more than the repair**: the first attempt
**deleted saltpetre 1893-96 outright**, because the repair rows were written from
what `country_year_final` displays. `country_obs` spells the group
`SALTPETRE (Nitrate of Potash)`; `integrate` upper-cases it to
`SALTPETRE (NITRATE OF POTASH)`. `supersede` upper-cases before comparing, so it
matched and dropped the rows, while the re-admission queries `country_obs` with
the literal string and matched nothing. **The failure mode is not "nothing
happens" — it is deletion without replacement.** A `group_repairs`
`article_group`/`article` must be copied from `country_obs`, exactly as that
table spells it.

## 1897-1898 — closed 2026-07-27 (iteration 38)

Iteration 34 recorded "no single-year volume covers 1897-1900". That was wrong.
**`as_1899` carries a clean five-year comparative table for the same commodity at
seq 17829-17874**, covering 1895-1899 with nine rows per year.

```
1897  Germany 58,506 + Holland 22,235 + Belgium 12,227 + Other Foreign 205
      vs printed foreign TOTAL 93,283            (residual 110)
      British East Indies 236,730 = Bombay 11,319 + Bengal 225,411   EXACT
      93,283 + 236,730 = 330,013 = T1 to the digit

1898  66,233 + 30,723 + 17,108 + 137 = 114,201
      vs printed foreign TOTAL 114,206           (residual 5)
      BEI 148,064 vs Bombay 3,780 + Bengal 144,281 = 148,061  (residual 3)
      114,206 + 148,064 = 262,270 = T1 to the digit
```

**1898's block contradicts itself and T1 breaks the tie.** Its own printed grand
total reads **292,270**; its components sum to **262,270**, which is the Tier-1
figure exactly. A 6→9 digit error in the total, not in the components — closure
against T1 outranks the printed total.

Result: 1897 **12.740 → 0.9997**, 1898 **17.914 → 1.0000**. A whole-payload
ratio-class diff moves exactly those two cells.

## The trap: interleaved comparative tables

A five-year comparative table **interleaves its years by `row_seq`**, so no
contiguous seq range can isolate one year. Normally harmless — `seen_added` and
`consensus_triples_ga` skip cells an earlier repair or the consensus already
holds — **except where two volumes spell the same country differently.**

Seq 17864 is `British East Indies : Other British Possessions` 898 for **1896**.
`as_1896` carries the same 898 under the label `Cape of Good Hope`. Different
`cnorm` key, so both were admitted, 898 was double-counted inside the BEI
aggregate, and **1896 fell from 1.0000 to 1.003** (measured on the first
attempt). The fix is two repair rows straddling that row: **17831-17863** and
**17865-17873**.

Generalisation: when re-admitting from an interleaved multi-year block, diff the
admitted country labels against those the neighbouring years already hold, and
straddle any row whose label is a spelling variant rather than a duplicate.

## Baseline

`exact01` **2,755 → 2,757**, `over` 232 → **230**, within 0.1% GBP-weighted
48.1% → **48.2%**.

## Still open

- **1900 is `nodata`** — `as_1899`'s comparative table stops at 1899, so 1900
  needs a later volume. **1899 sits at 0.998** (consensus, untouched by these
  repairs).
- **`Saltpetre (Nitrate Of Potash) — Rape` (GBP 2.3M) and `— Clover And Grass`
  (GBP 23.4M) are still the seeds section**, misfiled under the saltpetre head.
  Superseding `article=''` does not touch them; they need their own relabel to
  the real seeds commodities. Unworked.
