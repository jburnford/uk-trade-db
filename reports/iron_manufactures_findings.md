# Iron — Manufactures Of Iron Or Steel, Unenumerated

Worked 2026-07-29 (`/loop /next-defect` iteration 9). A £52.6M commodity whose
origin series closes to **1.0000 in sixteen of twenty-three years** — so every
year that does not is a parse defect, not a trade story.

| year | ratio | |
|---|---|---|
| 1878 | 0.2058 | **export table in the numerator** — see §3 |
| 1879 | 0.2209 | same |
| 1880–91, 1893–94, 1897 | 1.0000 | |
| **1892** | **0.0000** | **fixed here** |
| 1895 | 0.9632 | residual |
| 1896 | 1.0243 | residual |
| 1898–99 | 0.9998 / 0.9999 | |
| 1900 | 0.0000 | no volume carries 1900 origins |

## 1. 1892 — the table was never lost, only mislabelled

`as_1892` `country_obs` seq 2011-2029 is a complete, well-formed block whose
grand TOTAL **2,875,567 Cwts / £2,532,118 matches Tier-1 on BOTH columns to
the digit**. It reached the payload under `IRON and STEEL. | Manufactures of
Iron and Steel` — note **AND**, where every other year prints **OR** — and so
landed in the anchorless node `Iron And Steel — Manufactures Of Iron And
Steel`, leaving the anchored commodity at 0.0000.

Relabelled to the wording `as_1893` and `as_1894` use (`IRON and STEEL |
Unenumerated`), both of which close exactly. Four `group_repairs` rows, one
`supersede_years=1892` to stop the block being counted twice.

**1892 nodata → EXACT** (2,875,605 against T1 2,875,567, +38 = 0.0013%).

## 2. Two cells the engines disagreed on, both settled by a printed total

### Norway: 60,887, not 69,887 — the foreign TOTAL decides

Chandra reads 69,887, Infinity 60,887. With Chandra's, the eleven foreign
members sum to **2,877,833** against a printed foreign TOTAL of **2,868,801**
— an excess of 9,032. With Infinity's they sum to **2,868,833**, +32.

The four cells the engines read differently are Sweden (539,587 / 339,587),
Norway, Holland (1,228,259 / 1,228,250) and Other Foreign (1,995 / 1,295).
Brute-forcing all sixteen combinations against the printed total: **no
combination other than the two that take Chandra's Sweden and Infinity's
Norway comes within 600.** Each engine wins a different cell, which is the
documented pattern — see [[two-column-digit-proof]].

**The value column proves the method independently**: it closes *exactly* on
the printed £2,517,631 once Denmark takes Infinity's 19,038 instead of
Chandra's 19,938. One column closing exactly on one engine's cell while the
other column closes on the other engine's cell is about as strong as
cross-engine arbitration gets.

Encoded as a `manual_rows` row rather than by switching `obs_source` to `inf`,
because Infinity's Sweden is wrong by 200,000. The group repair deliberately
**skips seq 2013** so the manual row is the only Norway cell — step 6 runs
before step 5, and a `replace=1` row would have been *added* beside the
repair's, not substituted for it.

### Canada: the drill-down label costs the closure

Seq 2025 was parsed `British North America : Canada` (a fused run-in head).
`as_1893` and `as_1894` print a bare `Canada` in the same position, and left as
a drill-down the 4,703 is **excluded from every commodity-vs-T1 sum** — the
metric drops `Parent (Sub)` labels. Fixed with a row-level `new_country`.

The British half closes with Chandra's 4,703 and not with Infinity's 1,702:
359 + 828 + 4,703 + 20 + 862 = 6,772 against the printed British TOTAL 6,763,
where Infinity would leave it 2,992 short.

**This is the third time in two iterations that sub-entry exclusion has been
the whole difference between a year closing and not** (drugs 1891 was 77,052 of
its 112,486 shortfall). Worth a screen of its own: *commodity-years where the
country sum plus its excluded drill-downs would close but the sum alone does
not.*

## 3. 1878 and 1879 — NOT worked: this is export leakage

Diagnosed, deliberately left. The 0.21 is not a lost table — it is the **wrong
table in the numerator**. The target's 1878/79 country cells are

    Australia · British India · China · Hong Kong · Straits Settlements ·
    Japan · Turkey Proper · Wallachia and Moldavia · Other Countries

— a **destination** list, admitted by the `twoup` gap-fill under `IRON |
Manufactures of Iron or Steel, Unenumerated`. That is the export-leakage
signature the campaign's phase 0 measured (451 blocks / 4,692 rows).

**And the real 1879 import block is present and closes to the digit.** It sits
in the de-headed payload node `Iron` (unit `?`), from `IRON AND STEEL | ⟨null
article⟩`:

    Belgium 954,955 + Holland 738,687 + Sweden 376,179 + USA 66,408 +
    Russia 35,969 + France 35,742 + Germany 28,986 + Other 6,777 +
    Canada 2,684  =  2,246,387  =  T1 EXACTLY

Closing 1879 therefore needs **two** things: the export rows removed
(`drop-country` is the guarded tool, but it would take a dozen rows) *and* the
`Iron` node's 1879 cells folded in — and `Iron` is **de-headed**, the palm-oil
trap, so it must be year-scoped. Both halves belong with the export campaign
rather than in a single-defect iteration. 1878 will need the same treatment;
its import block was not located in this pass.

## 4. Left behind

- After the 1892 rows moved out, the residual node renamed itself
  `Iron And Steel — Manufactures Of Iron And Steel` → `Iron And Steel,
  Manufactures` and now holds **only a §TOTAL** — an anchor-only duplicate
  shadow carrying 1876-81 and 1896-1900. Its 1878-81 values are the target's;
  its 1896-1900 values (420,068 / 421,178 / 425,462 / 423,736 / 435,024) are a
  *different* series from the target's (3.74M / 3.45M / 4.34M / 4.50M) and are
  not yet identified. Confirmed a rename and not a split: same node, country
  count 17 → 1, no third node, all eleven affected years nodata before and
  after.
- 1895 (0.9632) and 1896 (1.0243) are untouched residuals.
- 1900 has no origin volume at all; expected, not a defect.

## Result

Baseline 9,634 c-y: exact01 3,138 → **3,139** (32.6%), GBP within 0.1%
50.9% → **51.0%**, within 5% 68.0%. One commodity-year changed to EXACT,
**zero regressions** (the other 22 diffs are the rename above, nodata → nodata).
