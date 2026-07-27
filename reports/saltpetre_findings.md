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

---

# The seeds glue under the saltpetre head — iteration 39, 2026-07-27

The `as_1897` `SALTPETRE (Nitrate of Potash)` head carries two articles that are
not saltpetre at all: `Rape` (seq 18476-18981) and `Clover and Grass`
(seq 18185-18475). Neither is one commodity. **The `Rape` article alone is SIX
origin tables concatenated**, ~99 rows per year, with the five years
**interleaved by `row_seq`** — the same layout trap as the as_1899 comparative
table above.

Segmenting on the printed `TOTAL` rows and matching each year's grand total
against the consensus quantity lines identifies five of the six:

| block | seq range | unit | true commodity | years closing |
|---|---|---|---|---|
| **A** | 18476-18549 | Quarters | **Rape** | 4 of 5 — **APPLIED** |
| B | 18550-18627 | Quarters | `Seeds \| Garden, unenumerated` (Lbs) | 4 of 5 |
| C | 18628-18681 | Quarters | **unidentified** | 0 |
| D | 18682-18705 | Bushels | `Tares and Lentils` | **5 of 5** |
| E | 18706-18828 | Bushels | `Seeds, Unenumerated, for expressing Oil therefrom` | **5 of 5** |
| F | 18829-18981 | Cwts | `Seeds \| Other sorts` | **5 of 5** |

## A — applied

```
1893  252,560 = T1        1896  179,730 = T1
1894  299,046 vs T1 299,016   (one digit, not chased)
1895  325,393 = T1        1897  185,232 = T1
```

The payload commodity **`Rape`** carries Tier-1 Quarters for 1866-68 and
1892-1900 and had **no origin data at all**, so the relabel displaces nothing.
One `group_repairs` row, `new_group=RAPE`, `new_article` empty, **no
`supersede_years`** — superseding would drop sub-blocks B-F before they are
worked. Ratios after: 1893 **1.0000**, 1894 0.9941, 1895 0.9784, 1896 **0.9998**,
1897 **1.0000**. Whole-payload ratio-class diff: five new cells, nothing else
moved. `exact01` **2,757 → 2,760**.

**The trap A avoided**: relabelling to `SEEDS | Rape` would have gained nothing —
that commodity's Tier-1 stops at **1891**. `Rape` alone is the label carrying the
1892-1900 national line. Check the target commodity's T1 coverage *and* its
existing origins before relabelling any of B-F.

## Still open here

- **B, D, E and F are fully specified above** and each has multi-year exact
  closure. They are the next work, one at a time, each with its target checked.
- **Sub-block C is unidentified** — grand totals 447,476 / 450,082 / 473,430 /
  236,394 / 240,547 Quarters match no consensus quantity line in any year.
- **Rape 1894 (0.9941) and 1895 (0.9784)**: the country sum falls short of the
  printed grand total, which itself equals T1. Unexamined.
- **The entire `Clover and Grass` article run (seq 18185-18475, GBP 23.4M) is
  untouched** and is presumably segmented the same way.

## Iteration 40 — the other four sub-blocks, measured. **None can be applied.**

Iteration 39 left B, D, E and F as "the next work, one at a time". Working F
forced a pre-check of the other three, and the queue entry was wrong. Recorded
here so none of it is re-tried.

### F — `Seeds | Other sorts`: applied, measured, **reverted**

`exact01`, `over` and `nodata` were **all unchanged**. Two independent reasons:

1. The target commodity's Tier-1 series is **entirely under unit `Value`** — 30
   entries, of which 1868-1892 are £ values and **1893-1897 are cwt quantities
   mis-healed into the Value bucket** (816,471 / 585,804 / 827,001 / 478,135 /
   548,415). The relabelled cells arrive as `Cwt` and never meet it. This is the
   same value/quantity confusion as `reports/value_only_origins_findings.md`,
   reached from the other direction.
2. Even ignoring units, **the cells do not close.** Country sums 727,559 /
   559,772 / 923,308 / 490,058 / 565,018 against T1 816,471 / 585,804 / 827,001
   / 478,135 / 548,415 — ratios 0.891 / 0.955 / 1.116 / 1.025 / 1.030. The
   block's *grand total* matches T1, but its foreign components **overshoot
   their own printed subtotal by 9,091 in 1897** (549,985 vs 540,894). A grand
   total that matches is not the same as a block that closes.

The label choice was right, at least: the relabel merged `Seeds — Of Other
Sorts` into a new `Seeds — Other Sorts` on the same signature.

### B — `Seeds | Garden, unenumerated`: the origins are already there

`Garden, Unenumerated` reads **0.960 / 1.004 / 0.999 / 0.999 / 0.996 / 0.995 /
1.000** for 1893-1899. Relabelling B would double them.

### D — `Tares and Lentils`: already over-counted

50 countries already, and the target years are **already over**: 1894 1.029,
1895 1.121, 1896 1.123, **1897 1.700, 1898 1.895, 1899 1.623** — against ~1.000
through 1893. Adding D makes it worse. **The over-count itself is a new,
untraced defect.**

### E — the only candidate, blocked on a unit-label question

`Unenumerated, For Expressing Oil Therefrom` has T1 in **Bushel** for 1883-84
and 1891-1900, **zero countries**, and the block's grand totals equal T1 in all
five years: 143,488 / 131,743 / 97,544 / 101,177 / 209,736. It is the clean case
Rape was.

**But the units disagree.** The block's own unit column reads `Quarters`, and so
does the article name — it is literally `Unenumerated, for expressing Oil
therefrom - Quarters`, the unit caption absorbed into the label — while the T1
series for those years is filed under `Bushel`. `new_unit=Bushels` would
reconcile but aligns the origins to a label that looks wrong; `Quarters` is
truthful but leaves the cells invisible. The T1 series itself steps **1890
Quarter 125,475 → 1891 Bushel 94,426 with no factor-of-8 jump**, so this is a
label flip, not a real mid-series unit change.

Deciding it means correcting a Tier-1 unit, so it is queued rather than guessed.

## Revised "still open" for this run

- **E**, once the Quarters/Bushel label question is settled.
- **Sub-block C** remains unidentified.
- **`Tares And Lentils` 1897-1899 over-count** (1.700 / 1.895 / 1.623) — new,
  unrelated to this run, source not traced.
- The `Clover and Grass` article run (seq 18185-18475, GBP 23.4M) is still
  untouched — and after the above, **check each target's existing origins and
  T1 unit BEFORE assuming a sub-block is workable.**

---

# The same seeds run, a second time — `Cotton | Tares and Lentils` in as_1899

Iteration 40 flagged `Tares And Lentils` as over-counted without tracing it.
Iteration 41 traced it, and it is the seeds run again, under a different volume
and a different stale label.

**The as_1899 `Cotton | Tares and Lentils` label spans FOUR consecutive origin
tables** — 74-78 rows per year, five years interleaved by `row_seq` — and the
consensus voted the whole run in. The affected cells sat in
`country_year_final` as `article_group='COTTON'`, `source='consensus'`.

Segmenting on the printed `TOTAL` rows gives four grand totals per year:

| block | grand TOTAL seq | 1895 | 1896 | 1897 | 1898 | 1899 |
|---|---|---|---|---|---|---|
| T0 | 14439-14443 | 17,082 | 22,293 | 38,985 | 33,253 | 37,878 |
| **T1blk** | 18474-18478 | **623,690** | **394,028** | **259,637** | **345,769** | **414,399** |
| T2 | 18599-18603 | 97,514 | 101,177 | 209,736 | 171,715 | 194,195 |
| T3 | 18750-18754 | 827,001 | 478,135 | 548,415 | 701,031 | 643,939 |

**T1blk's five grand totals are the `Tares and Lentils` Tier-1 figures for
1895-1899, every one exact.**

## Applied

Supersede 1895-1899 for `(Cotton, Tares and Lentils)` and re-admit **seq
18404-18478** only — 18404 is 1895's first `Russia` row, 18478 the last grand
`TOTAL`, and 18479 starts T2. Superseding all five years also drops the
as_1895 / as_1896 / as_1898 readings, which is intended: this one block covers
every year and closes on each.

```
1895  1.1208 -> 0.9985      1898  1.8954 -> 1.0000
1896  1.1228 -> 0.9999      1899  1.6231 -> 0.9999
1897  1.6996 -> 0.9965
```

`exact01` **2,760 → 2,763**, `over` 230 → **225**. The whole-payload
ratio-class diff moves exactly those five cells.

Two label details, both previously-earned rules:

- `new_group='TARES AND LENTILS'` with an **empty article** keeps the signature
  `{TARES,LENTILS}`. `SEEDS | Tares and Lentils` would have created a different
  commodity — the same trap Rape avoided.
- `article_group` is written **`Cotton`**, the way `country_obs` spells it;
  `supersede` upper-cases it to match `COTTON` in the final table.

## This settles the Quarters/Bushel question left open by iteration 40

**T2 is `Unenumerated, For Expressing Oil Therefrom`** — its Tier-1 Bushel
series carries **209,736 for 1897** and **194,195 for 1899**, both of which are
T2's grand totals — and **as_1899 prints the whole block in Bushels.** So the
Tier-1 `Bushel` label is right and the `Quarters` caption absorbed into the
as_1897 article name was the outlier. No Tier-1 unit needs correcting.

That commodity still has **zero countries**, and T2 (**seq 18479-18603**) is a
clean five-year block for it. It is the next item.

## Still open here

- **T2 → `Unenumerated, For Expressing Oil Therefrom`, seq 18479-18603** —
  fully specified, zero-country target, unit question settled.
- **T3, seq 18604-18754** — grand totals match the `Seeds | Other sorts` series,
  which iteration 40 proved does not reconcile because its Tier-1 is filed under
  unit `Value`. Do not work it until that is fixed.
- **T0, seq 14419-14443** — a small table (17,082-38,985) matching a second
  `tares%` series in the consensus. Unidentified.
- **Residual shortfalls inside T1blk**: 1895 short **930** (622,760 vs 623,690)
  and 1897 short **905** (258,732 vs 259,637) — individual country rows the
  parser dropped from an otherwise exact block.
- **Tares 1894 at 1.029** is untouched; its source is as_1898 / as_1894.
