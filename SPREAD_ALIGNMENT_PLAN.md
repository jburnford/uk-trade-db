# Split-Spread Alignment Plan — Canadian Trade & Navigation tables

*Drafted 2026-08-30 from a survey of every Canadian T&N Chandra output on this machine
(`scripts/ca_spread_survey.py`). Written to be executed by a fresh session: read §0 first,
then work §5 in order.*

*Amended 2026-08-30 after §5 step 1 ran. Three corrections, marked **[A1]**, **[A2]**,
**[A3]** below and evidenced in `reports/canada_spread_alignment.md`: the split affects four
statement families, not one; Canadiana FY1897 is a different volume design; there are three
OCR runs per year with a manifest that picks one. Steps 2 onward have not been started.*

## 0. Read this first

**The problem.** From FY1897 the *General Statement of Imports* is printed across two
facing pages. Canadiana and StatCan both scanned each page as its own image, so Chandra
emits two tables per spread: a **left** table with the row labels (article, country,
province) and the first value columns, and a **right** table that is numbers only. The
right table carries no row labels, and the two tables do not have the same number of rows
(in FY1900 only 51 of 325 pairs do; most differ by 1–10 rows). Joining by row position
would mis-pair ~85% of spreads.

**The key.** The right page's *Total Value* column **is** the left page's *Value* column
(the same number printed on both pages), and where the total is blank it equals
*General Tariff Value + Preferential Value*. A crude sequence alignment on that key, with
no OCR tolerance and no other constraints, already aligns **77% of left rows in FY1900
and 73% in FY1898**. The plan is to turn that into a proper aligner with the printed
arithmetic as the validator, exactly as the rest of this repo does.

**What this is not.** It is not a positional join, not an LLM guessing which rows go
together, and not (yet) a re-OCR of merged page images. Image merging is the fallback in
§7, to be decided only after §5 step 5 reports the residue.

### Scope, from the survey

| tier | statement | volumes | number-only tables / volume | share of tables |
|---|---|---|---|---|
| **1 (main)** | four statement families, see **[A1]** | StatCan `CS4-4-1898 … 1908` | 190–360 | 25–32% |
| **1b** | a different set of statements again, see **[A2]** | Canadiana `oocihm.9_08052_32_4` (FY1897); StatCan FY1897 | 191 / 72 | 25.6% / 8.9% |
| **2 (small)** | Value of Imports/Exports *at each Port*; *Exports from the Province of X to each Country*; multi-year comparative statements | Canadiana + StatCan 1868–1889 | ~35 (ports 12–16, exports-by-country 4–6, comparatives ~15) | 3–5% |
| — | UK Annual Statements and T&N Accounts (`raw/as_*`, `raw/tn_*`) | — | 0–4 | ≤0.7% — **no problem, out of scope** |

**[A1] Tier 1 is four families, not one.** Classifying every FY1900 / FY1898 pair by the
`No. N.—` running head: **No. 37 General Statement** (article × country × province) 217 / 219
pairs; **No. 17 Summary Statement of Foreign Merchandise** (article-level, no country) 30 / 29;
**No. 48 and No. 50 Number and Tonnage of Vessels** (split by *nationality column group*) 34 / 32;
No. 40/42/52/53 vessels 10 / 10; No. 28 exports abstract 5 / 4; No. 87 second-series general
statement 0 / 8; No. 1/6/9 value and comparative 3 / 2; running head not OCR'd 17 / 4.
Total 325 / 320. The layout in §0 and the invariants below were derived from **No. 37** — two
thirds of the problem. No. 17 carries an ordinal `Number` column that is an extra anchor.
No. 48/50 share **no** value column between the pages, so I1 does not apply there: the left
page keeps its labels and the right page holds the remaining nationalities plus `Total`, which
makes it a column-completion problem solved by the tier-2 horizontal sum. **Build the
horizontal-sum key alongside I1, not after it.**

**[A2] Canadiana FY1897 (`32_4`) is a different volume design, not an early tier-1 instance.**
161 pairs, **none of them No. 37**: No. 6 *Itemized Statement of Values of Imports* 53,
No. 14 *by Provinces* 34, No. 12 / No. 13 *Principal and Other Articles* 35, No. 8 / No. 9
*Quantities and Values* 17. Crude baseline 41.4% vs 77.0% for FY1900 — a different table
design, not a worse scan. StatCan FY1897 is different again: 60 pairs, baseline 71.1%. So the
Canadiana ↔ StatCan 1897 pair is a second witness to the *year*, not to the same layout; §3
step 7 should not assume a direct per-cell join there.

The FY1868–1875 ("regime A") *import* coverage loss of 0.55–0.72 in
`reports/canada_imports_parse.md` §coverage is **not** this problem; every regime-A page
carries its own labels. That is OCR quality (bitonal microfilm) and the second witness
addresses it. Do not conflate the two.

### Layout of a tier-1 spread (verified on StatCan FY1900; re-verify per volume, §5 step 1)

```
LEFT PAGE                                                RIGHT PAGE
running head: "No. 37.—GENERAL STATEMENT"                "OF IMPORTS—Continued.  ENTERED FOR HOME CONSUMPTION."
ARTICLES IMPORTED | COUNTRIES AND PROVINCES |            General Tariff | Preferential Tariff        | Total
  TOTAL IMPORTS (Quantity, Value) |                       Value, Duty   | Quantity, Value, Duty      | Quantity, Value, Duty Collected
  ENTERED FOR HOME CONSUMPTION → General Tariff Quantity

1. Iron and steel … | Great Britain … |      | 41    |    9,567 | 2,391 40 |     | 41 | 7 69 |     | 9,608 | 2,399 69
                    | United States … |      | 9,567 |
Total …             | Ontario …       |      | 3,336 |    3,335 | 833 75   |     | 1  | 0 19 |     | 3,336 | 833 94
                    | Quebec …        |      | 3,277 |    3,237 | 808 90   |     | 40 | 7 50 |     | 3,277 | 816 40
                    | Nova Scotia …   |      | 1,150 |    1,150 | 287 50   |     |    |      |     | 1,150 | 287 50
```

Duty cells print dollars and cents separated by a space (`833 75` = $833.75). Unit rows
(`Cwt.`, `Lbs.`) are printed on **both** pages and are free anchors.

## 1. Inputs

| what | where | notes |
|---|---|---|
| Canadiana Chandra output | `raw_canada/<tag>/<tag>.md` | HTML `<table>` inside markdown, **no page markers**; `<tag>_metadata.json` has per-page token counts only |
| StatCan Chandra output | path from `ocr/MANIFEST.tsv`, column `md_path` | **[A3]** *three* runs exist per year — `statcan_plato_may`, `statcan_nibi_w2`, `statcan_plato_w2` — and the manifest's `preferred_source` + `md_path` already choose one. Read the manifest; do not glob. Preferred for tier 1: 1897–1898 `statcan_plato_may`, 1899 `statcan_plato_w2`, 1900–1908 `statcan_nibi_w2`. Different clusters and dates, but the same page images, so §6's rule still holds |
| Table inventory (Canadiana only) | `reports/canada_tables.tsv` | one row per table: byte `offset`, `header`, `first_row`, `cells_hist`, `span_hist` |
| Shared HTML-table helpers | `scripts/ca_profile.py` | `TABLE_RE`, `ROW_RE`, `CELL_RE`, `parse_table()`, `clean()` — reuse, don't re-implement |
| Existing import parser | `scripts/ca_parse_imports.py` | regimes A/B/C; `parse_table_A` shows the "anchor columns from the right" trick; regime C shows the row-kind vocabulary and the output row schema (`db/canada/imports_general_rows.csv`) |
| Closure checks | `ca_check_abstract.py`, `ca_check_summary.py` | how block sums are compared with printed totals |
| Gold | the T1 abstract in each volume (`ca_parse_abstract.py`) | national totals per article — the external check for tier-1 output |

Known gotchas already recorded elsewhere and relevant here: `oocihm.9_08052_13_10` is not a
T&N volume; FY1879 is `13_1`; the Canadiana FY1897 volume (`32_4`) currently parses to
**0 rows** because no regime matches its header — this plan is what fixes that.

## 2. Invariants (the validator)

Every one of these is printed on the page; none needs a model.

- **I1 value key** — `L.Value == R.TotalValue`, or `L.Value == R.GTValue + R.PTValue` when
  the total is blank or garbled. Exception: goods warehoused rather than entered for
  consumption, where the two legitimately differ — such rows align by neighbours (I5).
- **I2 right-page closure** — `GTValue + PTValue == TotalValue`; `GTDuty + PTDuty ==
  TotalDuty`. A right row that fails I2 is itself suspect; don't let it win an alignment.
- **I3 duty rate** — within one ad-valorem article, `Duty / Value` is a constant (25% in
  the example: 3,335 → 833 75; 1,150 → 287 50). Use it to confirm a match and to detect a
  digit slip in either number.
- **I4 vertical sums** — province rows sum to their country/article `Total` row on both
  pages. Total rows are alignment anchors, and a block whose provinces don't sum is
  reported, not silently accepted.
- **I5 order** — the alignment is monotone: rows never cross. Dropped or merged rows
  become gaps, never shifts. This is what prevents false rows.
- **I6 quantity key** — `L.GTQuantity` relates to `R.TotalQuantity` (`= GTQty + PTQty`);
  a second key for rows whose value is blank.
- **Tier-2 horizontal sum** — in ports and exports-by-country tables the right page ends
  with `Total` / `Grand Total`; `Total − sum(right cells) == sum(left cells)` is the key.

## 3. Algorithm

1. **Pair tables.** Walk the volume's tables in document order (reuse
   `ca_profile.parse_table`). Classify each as `L` (label columns present; header contains
   `TOTAL IMPORTS` / `ARTICLES`), `R` (number-only body; header contains `General Tariff`
   / `Preferential` / `Duty Collected`, or the intertext before it carries the right-hand
   running-head fragment `OF IMPORTS—Continued`), or `other`. Pair each `L` with the next
   `R` unless a different statement title intervenes. Emit
   `reports/spread_pairs_<fy>.tsv` (pair_id, L seq/offset, R seq/offset, row counts,
   running heads). **Sanity: ~320–330 pairs per StatCan volume 1898+.**
2. **Normalise columns per side.** Flatten `colspan`/`rowspan` header cells into canonical
   names (`L`: article, country_province, tot_qty, tot_value, gt_qty; `R`: gt_value,
   gt_duty, pt_qty, pt_value, pt_duty, tot_qty, tot_value, tot_duty). When the header
   failed to OCR, anchor positionally **from the right** (`tot_duty` is last and
   cents-style), as `parse_table_A` does. Parse numbers with `parse_num(..., cents_ok=True)`
   semantics from `ca_parse_imports.py`.
3. **Type rows.** `L`: section banner (`DUTIABLE GOODS` / `FREE GOODS`), article heading,
   country row, province row, `Total` row, unit row, blank. Forward-fill article and
   country down the block (they print once, like a rowspan). `R`: unit row, value row,
   total row (confirmed by I4 after alignment).
4. **Align.** Needleman–Wunsch over the two row sequences, monotone (I5). Match score:
   exact I1 or I6 = high; I1 with one same-length digit substitution = low positive
   (report it as `near`, never as `exact`); unit-row ↔ unit-row = anchor; total-row ↔
   total-row confirmed by I4 = anchor. Gap penalty on either side. Reject a match that
   violates I2 on the right row or I3 within the article.
5. **Validate each pair.** Fraction of `L` value rows aligned, I2/I4 pass counts, unaligned
   rows per side. Grade: `PASS` (≥95% aligned and all Total blocks close), `PARTIAL`,
   `FAIL` (pairing itself is doubtful — e.g. row counts differ by >15 or no anchors).
6. **Emit.** Rows in the `imports_general_rows.csv` schema with `regime='D'`, plus
   `pair_id`, `align_status ∈ {exact, sum, qty, near, neighbour, unaligned}` and the source
   table seqs on every row. Unaligned rows are still emitted (left-only / right-only) so
   nothing is lost; they carry `unaligned`. Write `reports/canada_spread_alignment.md`
   (per-volume: pairs, grades, aligned %, top failure causes) and
   `reports/spread_residue.csv` (the unaligned rows — this is the retry queue for §7).
7. **Second witness.** FY1897 exists in both Canadiana (`32_4`) and StatCan; 1898+ exists
   as two StatCan runs. After single-witness alignment, arbitrate per cell the way
   `reconcile_country.py` does, using I1–I4 as the tie-breaker. A cell that aligns
   identically in both witnesses is rank-1 evidence; the residue shrinks to what both
   witnesses missed.

Tier 2 (1868–1889 ports / exports-by-country / comparatives) uses the same engine with a
different column map and the horizontal-sum key. Do it after tier 1 is graded.

## 4. Acceptance

- Baseline to beat (crude matcher, no constraints): **77.0%** of left value rows aligned
  in StatCan FY1900, **73.1%** in FY1898, measured by `ca_spread_survey.py --align`.
- Target for tier 1: ≥90% of left value rows aligned with `exact`/`sum`/`qty` status;
  ≥80% of pairs `PASS`; every `Total` block that closes on the left also closes on the
  right; T1 abstract totals for the top-30 import articles reproduced within 1% for at
  least one 1898+ volume.
- Never report a `near` or `neighbour` alignment as verified. Ranks follow the repo
  convention (README "Every country_year_final cell carries per-cell trust columns").

## 5. Work order

0. Read: this file; `README.md` (Sources, Pipeline, Quality stages); `scripts/ca_profile.py`;
   `scripts/ca_parse_imports.py` docstring, `regime_of()`, `parse_table_A` (lines ~1375–1440),
   and the regime-C row kinds; `reports/canada_imports_parse.md` (the diagnostics
   vocabulary); `../sessional_papers/statcan_trade/README.md` and `ocr/MANIFEST.tsv`.
1. ~~Run the survey, eyeball three FY1900 pairs, check FY1897.~~ **DONE 2026-08-30** —
   survey reproduces exactly; findings [A1]–[A3] recorded in
   `reports/canada_spread_alignment.md` and folded into §0/§1 above.
2. Write `scripts/ca_pair_spreads.py` (§3 step 1), classifying each pair by statement number
   from the `No. N.—` running head and carrying it as a `statement` column **[A1]**. Run on
   FY1900. Sanity is now **~217 No. 37 pairs** (325 pairs overall), not ~325 of one kind.
   Stop and inspect if No. 37 is not ~217, or if the unclassified-running-head bucket exceeds
   the ~17 seen in the survey.
3. Write `scripts/ca_align_spreads.py` (§3 steps 2–6) with a column-map registry keyed by
   statement, and both keys from the start: the shared-value key (I1) for No. 37 / No. 17 and
   the horizontal-sum key for No. 48 / No. 50 **[A1]**. Iterate on **No. 37 in FY1900 only**
   until the §4 targets hold there. Keep a diagnostics `Counter` in the style of
   `ca_parse_imports.py` so failure causes are countable, not anecdotal.
4. Run over the tier-1 volumes: StatCan 1898–1908 (manifest `md_path` per year). Then, as a
   separate step with its own column maps, tier 1b: Canadiana `32_4` and StatCan 1897 **[A2]**.
   Commit `reports/canada_spread_alignment.md` and `reports/spread_pairs_*.tsv`.
5. Wire the second witness (§3 step 7). Produce `reports/spread_residue.csv` with a
   per-row reason. **This is the decision point for §7** — bring the residue size and its
   causes back before building any fallback.
6. Closure against the T1 abstract for one 1898+ volume (`ca_parse_abstract.py` already
   reads those tables). Then integrate regime-D rows into the existing pipeline
   (`build_dimensions.py` → `vote_country_years.py`) — a separate, later change.
7. Tier 2 (1868–1889 side-spreads), same engine, horizontal-sum key.

Each numbered step ends with a short note in `reports/canada_spread_alignment.md`
(what ran, what the numbers were, what was decided) — the same habit as the rounds in
`reports/CAMPAIGN_SUMMARY.md`.

## 6. Do not

- Do not join rows by position, even for pairs with equal row counts — they still slip.
- Do not use an LLM to guess row correspondence. LLMs may be used later, on the residue
  only, to *read* a page image, never to *pair* rows.
- Do not modify `parse_table_A/B/C` or their outputs while doing this.
- Do not merge page images before step 5 has produced the residue.
- Do not treat the two StatCan runs as independent witnesses of the *scan* (they are the
  same images through the same model); the Canadiana ↔ StatCan pair is the independent one.

## 7. Fallback for the residue — merged page images

Only if the residue after two witnesses is large enough to matter. The concern is real:
each facing page is its own scan with its own skew, vertical offset and scale. Row pitch is
~30 px at Chandra's render size, so a 1° skew across a page shifts baselines by a full row
at the far edge, and a half-row registration error manufactures exactly the false rows we
are trying to avoid. A composite is also double-width, which halves Chandra's pixels per
digit on pages that already read worst.

If it is attempted: deskew each page, register on the horizontal rules and the unit rows,
composite at full resolution, OCR, and accept the result **only** through the same I1–I4
checks — a merged read has no other way of proving it is right. Alternatives that avoid
registration entirely: re-OCR the right page alone at higher resolution (the digits are the
problem, not the pairing) and re-run the aligner; or have a VLM read the residue pairs
as *two images in one prompt* and emit joined rows, again validated by I1–I4.

The StatCan PDFs are on Nibi (`../sessional_papers/statcan_trade/01_download.sh`); the
Canadiana FY1897 PDF is not on this machine.

## Appendix — survey numbers (2026-08-30)

Number-only tables (`first two cells numeric/blank in ≥85% of body rows`, ≥8 rows):

```
Canadiana  1868 10.2% (55)   1869–1889  1–5%   1897 (32_4) 25.6% (191)
StatCan    1850–1897 0–9%    1898 31.7% (358)  1899 31.2%  1900 30.5% (351)
           1901 30.5%  1902 28.5%  1903 28.0%  1904 29.2%  1905 29.6%
           1906 28.4%  1907 29.1%  1908 29.0%
UK         as_1872–1879 0–0.7%   tn_1871/1872 0.5–0.6%
```

FY1900 pairs: 325; right-minus-left row-count difference: 0 (51 pairs), −1 (50), −2 (45),
−3 (39), −4 (30), +1 (26), −5 (19), −6 (17), ≤−7 (32+). Crude value-key alignment: 77.0%
of 13,017 left value rows (per pair: ≥90% 82, 70–90% 134, 50–70% 100, <50% 9).
