# Canadian T&N split-spread alignment

Working log for `SPREAD_ALIGNMENT_PLAN.md`. One section per numbered step in §5 of the plan:
what ran, what the numbers were, what was decided.

## Step 1 — survey reproduced, layout checked (2026-08-30)

`python3 scripts/ca_spread_survey.py` reproduces the plan's appendix exactly (number-only
tables: 30.5% of 1,151 tables in StatCan FY1900, 25.6% of 746 in Canadiana `32_4`, 0–5%
everywhere before 1897, 0–0.7% in the UK volumes). No change to those figures.

Three findings change the plan. All three are recorded as amendments in the plan itself.

### 1. The split is not one statement, it is four families

The plan's §0 described the affected statement as *the General Statement of Imports*. That
was generalised from a single sampled pair. Classifying every pair by the `No. N.—` running
head before the left table:

| statement | FY1900 | FY1898 |
|---|---|---|
| **No. 37 — General Statement** (article × country × province) | **217** | **219** |
| No. 17 — Summary Statement of Foreign Merchandise | 30 | 29 |
| No. 48 / No. 50 — Number and Tonnage of Sailing and Steam Vessels (by nationality) | 34 | 32 |
| No. 40 / 42 / 52 / 53 — vessels, description and number | 10 | 10 |
| No. 28 — Abstract of Total Value of Goods Exported | 5 | 4 |
| No. 87 — General Statement (second series) | 0 | 8 |
| No. 1 / 6 / 9 — value and comparative statements | 3 | 2 |
| continuation pages whose running head did not OCR | 17 | 4 |
| **total pairs** | **325** | **320** |

No. 37 is two thirds of the problem and the plan's invariants (I1–I4, I6) were derived from
it. The rest need their own column maps:

- **No. 17** is article-level with no country dimension: left `Number | ARTICLES | General
  Tariff Rates of Duty | TOTAL IMPORTS (qty, value)`, right `ENTERED FOR HOME CONSUMPTION`.
  I1 should still hold; the `Number` column is an extra ordinal anchor the aligner can use,
  and a strong one.
- **No. 48 / 50** are split by *column group*, not by measure: the left page carries the
  first five nationalities (British, United States, Norwegian and Swedish, Belgian, Danish)
  and the right page the remaining five plus `Total`. There is no shared value column, so I1
  does not apply — the key is the plan's tier-2 horizontal sum, `Total − sum(right) ==
  sum(left)`, per row. The left page keeps its port and country labels, so this family is
  *only* a column-completion problem, not a row-identity problem.

So the tier-2 horizontal-sum key is needed inside the 1898+ volumes, not only in the
1868–1889 side statements. Build it alongside I1, not after.

### 2. Canadiana FY1897 (`oocihm.9_08052_32_4`) is a different volume, not an early instance

161 pairs, and **not one of them is No. 37**. Its statements are numbered and structured
differently: No. 6 *Itemized Statement of Values of Imports* (53 pairs), No. 14 *by
Provinces* (34), No. 12 / No. 13 *Principal and Other Articles* (35), No. 8 / No. 9
*Quantities and Values* (17). The crude value-key baseline there is 41.4%, against 77.0% for
FY1900 — consistent with it being a different table design rather than a worse scan.

StatCan FY1897 is different again: only **60** pairs (baseline 71.1%), because its shipping
and itemized statements are set differently from the Canadiana printing of the same year.

Consequence: FY1897 is its own tier with its own column maps, and the Canadiana ↔ StatCan
"second witness" for 1897 is a witness to the *year*, not to the same table layout. Do not
expect a per-cell join between them to be as direct as the plan's §3 step 7 assumes.

### 3. There are three OCR runs per year, and a manifest that picks one

The plan's §1 said two. `../sessional_papers/statcan_trade/ocr/MANIFEST.tsv` has columns
`statcan_plato_may_bytes`, `statcan_nibi_w2_bytes`, `statcan_plato_w2_bytes` and a
`preferred_source` + `md_path` naming the chosen one per fiscal year. Use `md_path` from the
manifest; do not glob for a volume. Preferred source for the tier-1 years:

```
1897 statcan_plato_may   1898 statcan_plato_may   1899 statcan_plato_w2
1900-1908 statcan_nibi_w2
```

The runs differ by cluster (Plato / Nibi) and date, so they are not merely duplicates — but
they are the same page images, so the plan's §6 rule stands: they are not independent
witnesses of the *scan*.

### Decided

- Step 2 (`ca_pair_spreads.py`) must classify each pair by statement number from the running
  head and carry it as a `statement` column; the pair count sanity check becomes ~217 for
  No. 37 in a 1898+ volume, not ~325 overall.
- Step 3 (`ca_align_spreads.py`) needs a column-map registry keyed by statement, and both
  keys from the start: the shared-value key (I1) for No. 37 / No. 17 and the horizontal-sum
  key for No. 48 / No. 50.
- FY1897 (both witnesses) moves out of the tier-1 batch into its own step, after FY1900 works.
- Nothing has been built yet. Step 2 is the next action.

## Steps 2–3 — pairing and alignment built and run on FY1900 (2026-08-30)

`scripts/ca_pair_spreads.py` and `scripts/ca_align_spreads.py`. Run:

```bash
python3 scripts/ca_pair_spreads.py --fy 1900 --fy 1898
python3 scripts/ca_align_spreads.py --tag statcan_nibi_w2_1900 --fy 1900
```

### Pairing

Classification is by **header signature**, not by how numeric the body looks — the survey
heuristic was too loose and matched ordinary page continuations (e.g. the No. 21 French
Treaty tables, where both halves carry full headers and labels). A genuine right-hand page
has column headers but **no label column**. Header-less tables inherit the previous side.

FY1900: **256** `imports_37` pairs. FY1898: **254**. Every pair is adjacent in document
order. Raw row counts match in only 4% of pairs — but after dropping left rows that carry no
numbers (article headings, section banners, which have no counterpart on the right), **57% of
pairs match exactly and 84% are within ±1** (10,400 left data rows vs 10,381 right). The
structure is regular; positional joining still fails, because the residual ±1s shift blocks.

**FY1898 prints "Reciprocal Tariff" where FY1900 prints "Preferential Tariff"** — the same
column, renamed with the tariff itself. The right-page signature must accept both, or a whole
volume silently yields zero pairs.

### Column map — corrected

The plan's §0 was wrong about where the break falls. It does **not** fall between column
groups; it falls **through the middle of one**:

```
LEFT   article | country/province | TOTAL IMPORTS qty | TOTAL IMPORTS value | GT qty
RIGHT  GT value | GT duty | PT qty | PT value | PT duty | TOTAL qty | TOTAL value | TOTAL duty
```

The General Tariff group's **Quantity** is the last column of the left page while its Value
and Duty are the first two of the right page. Two consequences:

1. The plan's I1 (`left Value == right Total Value`) is **not an identity**. Left "TOTAL
   IMPORTS" is goods *imported*; right "Total" is goods *entered for home consumption*. They
   coincide only when nothing was warehoused — which is exactly why the crude survey matched
   77% rather than ~100%.
2. There is a better key, and it genuinely spans the break:
   **`left.gt_qty + right.pt_qty == right.tot_qty`**. Nothing but a correct join satisfies it.

`ca_profile.parse_table` drops `rowspan`, which shifts every column position on rows under a
spanned article cell; `ca_align_spreads.expand_rowspans()` restores them.

### Result, FY1900

10,850 rows over 256 pairs. Pair grades: **225 PASS, 18 PARTIAL, 13 FAIL**.

| status | rows | share |
|---|---:|---:|
| joined, confirmed by arithmetic (`xpage_qty` 3,136 · `value` 2,472 · `qty` 18) | 5,626 | 51.9% |
| joined by position, bracketed by confirmed rows in the same pair | 1,263 | 11.6% |
| joined by position only, not bracketed | 3,044 | 28.1% |
| left row with no counterpart (flagged, kept) | 469 | 4.3% |
| right row with no counterpart (flagged, kept) | 448 | 4.1% |

95.5% of left rows joined; **51.9% carry independent arithmetic confirmation**, 63.5% are
confirmed or sit between two confirmed rows. Nothing is silently dropped: unjoined rows are
written to `reports/spread_residue_<tag>.csv` and also kept in the row output with their
status, so downstream can threshold in SQL exactly as `country_year_final` does.

Ceiling check: **14% of right rows fail their own internal closure** (GT+PT == Total), i.e.
carry an OCR error independent of any alignment. No cross-page check can exceed ~86% while
that holds — the second witness is the way past it, not a better matcher.

### Decided / next

- The 28% position-only rows are the target for improvement, and the second witness is the
  main lever (see below).
- Second witness for 1898–1908 **is obtainable and has not been fetched**: `raw_canada`
  stops at FY1889 + FY1897, but `sessional_papers/ids.txt` lists the Canadiana series out to
  `oocihm.9_08052_34_1_1`. Those volumes are a genuinely independent scan of the same years.
- Not yet done: run over 1898–1908; No. 17 summary family; T1 abstract closure check.

## Step 4 — run across the decade (2026-08-30)

The header signatures drift twice across the run, both times following the tariff law rather
than the printer. Pairing now accepts all three eras:

| years | left label columns | right tariff columns |
|---|---|---|
| 1898 | ARTICLES IMPORTED · COUNTRIES **AND PROVINCES** | General + **Reciprocal** |
| 1899–1900 | ARTICLES IMPORTED · COUNTRIES AND PROVINCES | General + **Preferential** |
| 1901–1903 | ARTICLES IMPORTED · **COUNTRIES** (province dimension dropped) | General + Preferential |
| 1904–1908 | ARTICLES IMPORTED · COUNTRIES | **Preferential + Surtax** (General moves left) |

Miss any one of these and a whole volume silently yields zero pairs — 1904–1908 did, until
the signature was widened to "two tariff columns of any of these names".

### Pairs found, all years

```
1897   0 (different volume, see below)   1903  129
1898 256                                 1904  131
1899 256                                 1905  140
1900 256                                 1906  139
1901 127                                 1907  149
1902 126                                 1908  153
```

### Rows joined, 1898–1903 (the years whose column map is verified)

| FY | rows | verified by arithmetic | +bracketed | flagged | pair grades |
|---|---:|---:|---:|---:|---|
| 1898 | 10,605 | 3,113 | 4,328 | 912 | 220 PASS / 30 PARTIAL / 6 FAIL |
| 1899 | 10,678 | 5,847 | 6,990 | 851 | 232 / 17 / 7 |
| 1900 | 10,850 | 5,626 | 6,889 | 917 | 225 / 18 / 13 |
| 1901 | 4,737 | 927 | 1,263 | 397 | 106 / 14 / 7 |
| 1902 | 4,559 | 1,536 | 2,096 | 360 | 111 / 8 / 7 |
| 1903 | 4,865 | 1,737 | 2,305 | 352 | 104 / 20 / 5 |
| **total** | **46,294** | **18,786 (40.6%)** | **51.6%** | **8.2%** | |

95–97% of left rows join in every year. The verified share is much lower in 1901–1903 because
those volumes dropped the province dimension: fewer rows carry a quantity, so the strong
cross-page key fires less often. 1898 is low for a different reason still to be diagnosed
(1,675 `xpage_qty` hits vs 3,549 in 1899 on a similar row count).

**Not yet done:** 1904–1908 need a second column map (Preferential + Surtax, 9 right-hand
columns instead of 8); the pairs are already found. The No. 17 summary family is still unrun.

## The second witness is already on disk (2026-08-30)

`sessional_papers/markdown/` holds **371 Chandra-OCR'd Canadiana sessional-paper volumes**,
including the sessions after 1889 that `raw_canada` stops at. Scoring them by customs-table
vocabulary density and General-Statement count identifies the Trade & Navigation volume for
every year 1890–1899:

| FY | volume | FY | volume |
|---|---|---|---|
| 1890 | `oocihm.9_08052_24_3` | 1895 | `oocihm.9_08052_29_4` |
| 1891 | `oocihm.9_08052_25_4` | 1896 | `oocihm.9_08052_31_4` |
| 1892 | `oocihm.9_08052_26_4` | 1897 | `oocihm.9_08052_32_5` |
| 1893 | `oocihm.9_08052_27_5` | 1898 | `oocihm.9_08052_33_5` |
| 1894 | `oocihm.9_08052_28_4` | 1899 | `oocihm.9_08052_34_5` |

Two consequences:

1. **FY1897 is `32_5`, not `32_4`.** `raw_canada/INDEX.tsv` indexes `32_4` and notes that it
   yields 0 rows and that "the T&N tables proper for FY1897 are a separate sessional paper".
   That paper is `32_5`: 835 tables and **344** General-Statement-of-Imports headings, against
   `32_4`'s 776 tables and **0**. INDEX.tsv should be corrected.
2. **1890–1896 is a coverage gap that can be closed with no new OCR** — `raw_canada` has
   nothing between FY1889 and FY1897, and these seven volumes are already extracted.

For 1897–1899 these give a genuine second witness (independent scan, independent imaging
chain) against the StatCan copy, which is the only way past the 14% of right-hand rows that
fail their own internal closure. 1900–1908 still has one witness: `ids.txt` stops at session
34, so those Canadiana volumes have not been downloaded.

## Step 5 — ground-truth validation on FY1897, the last unsplit year (2026-08-30)

`scripts/ca_validate_split.py`.

**Why FY1897 exists as a control.** Its General Statement of Imports fits on one page: five
value columns (Imported qty/value, Entered-for-consumption qty/value, Duty). In FY1898 the
preferential tariff added three more, the table outgrew the page, and from then on it was
printed across a spread. Both witnesses confirm it — **324 unsplit tables in StatCan
CS4-4-1897, 323 in Canadiana `32_5`, and essentially no split ones in either**. So the split
was caused by the tariff change, not by the scanner.

That gives a control no real split year can: cut the 1897 tables at the column boundary
ourselves and check whether the aligner puts back exactly the rows that were together.
Every answer is known in advance.

### Result

| condition | correct | joined to the WRONG row | not joined |
|---|---:|---:|---:|
| clean cut, StatCan (4,746 rows) | **99.81%** | 7 | 2 |
| clean cut, Canadiana (4,662 rows) | **99.96%** | 1 | 1 |
| 5% of right rows deleted, StatCan | 93.8–94.1% | 183–200 | 87–91 |
| 5% of right rows deleted, Canadiana | 93.7–95.2% | 137–191 | 77–94 |

On clean input the joiner is effectively exact. The interesting condition is the second: when
right-hand rows go missing — which is what the real scans do, 2–4 rows per page — about **4%
of rows are joined to the wrong partner**, and a wrong join is silent. That is the real risk
in this whole approach, now measured rather than assumed.

### The confidence label is doing its job

Breaking the damaged condition down by which key carried each join:

| join carried by | correct | wrong | error rate |
|---|---:|---:|---:|
| arithmetic key | 5,358 | 6 | **0.1%** |
| duty-rate plausibility only | 2,691 | 308 | 10.2% |
| shape only (no key) | 69 | 39 | 36.1% |
| nothing | 409 | 46 | 10.1% |
| all rows | 8,527 | 399 | 4.5% |

**Filtering to arithmetic-confirmed rows takes the error rate from ~4.5% to ~0.1%.** Every
error lives in the unconfirmed rows. The per-row `align_status` is therefore a real
reliability filter, empirically calibrated, not a decoration — and the honest way to use this
data is `WHERE key IN ('xpage_qty','value','qty')` unless a question can tolerate the rest.

**Caveat:** this control necessarily uses weaker keys than the real 1898+ data has — an
unsplit 1897 row has no split tariff, so the strong cross-page quantity identity does not
exist to be tested. The real years should therefore do better than 4.5%, not worse. What
carries over is the shape of the result: confirmed rows are trustworthy, unconfirmed rows
are where the errors are.

## Also fixed in this step: cents folding

The two witnesses disagree about how a duty is cellised — StatCan usually emits `26,857 14`
as one cell, Canadiana usually splits it into `26,857` and `14` — and *both* do it
inconsistently (853 of 1,531 sampled StatCan right rows were split too). Anchoring columns
from the right without folding those back shifts every column and silently reads the row as a
different set of measures. `ca_align_spreads.fold_cents()` folds a bare two-digit cell onto a
preceding integer, rightmost first, only while the row is wider than the printed table; a bad
fold cannot hide, because the row then fails its own closure. FY1900 joined rows rose from
9,933 to 10,018 on this fix alone.

## Step 6 — two column-anchoring bugs found and fixed (2026-08-30)

Re-running the witness comparison after the cents fix still showed the two scans disagreeing
on ~60% of cells and the damage falling almost entirely on one witness (1,460 rows vs 103).
Two independent scans of the same setting of type cannot really disagree that much, so the
comparison was measuring a bug, not the sources. It was measuring two.

### Bug 1 — a spurious trailing column, and a check that could not see it

The **StatCan** right-hand tables carry an extra empty `<th></th>` on the top header row and
a junk cell at the end of every body row; the Canadiana tables do not. Anchoring columns
from the right therefore dropped StatCan's leading General-Tariff **Value** and shifted every
measure one place left — so its "values" were actually duties.

What makes this worth recording: **the shifted parse still passed the closure check.** The
duty triple satisfies `GT + PT == Total` exactly as the value triple does, so the check was
happily confirming a wrong reading. The reported "86% of right rows close" was true and
meaningless. A validating invariant that is invariant under the error it is meant to catch
is no check at all.

Fix: `header_width()` takes the leaf column count from the **last** header row (which names
the real leaf columns) rather than the first, and `right_rows()` anchors from the **left** —
correct for both witnesses, because a right-hand page has no label column, so its first cell
is genuinely the first value column and any junk is at the end.

### Bug 2 — cents cellised inconsistently

StatCan usually emits a duty as one cell (`26,857 14`), Canadiana usually splits it in two
(`26,857`, `14`), and both do it inconsistently. `fold_cents()` folds a bare two-digit cell
onto a preceding integer, rightmost first, only while the row is wider than the printed
table.

### Verification

Both witnesses now return **identical numbers** for the same rows, which is the result that
proves the fix — two independent scans, independent imaging chains, same digits:

```
GT value 3,845   PT value   851   Total value 4,696     (both witnesses, value closes)
GT duty  770.00  PT duty 148.95   Total duty    918.95  (both witnesses, duty closes)
```

### Effect on the headline numbers

Everything reported before this step was computed on shifted StatCan columns. Corrected:

| witness | rows | verified | +bracketed | flagged |
|---|---:|---:|---:|---:|
| StatCan 1898 | 10,531 | 68.2% | 83.3% | 7.3% |
| StatCan 1899 | 10,649 | 68.7% | 79.9% | 7.4% |
| StatCan 1900 | 10,759 | 70.4% | 84.3% | 6.8% |
| StatCan 1901 | 4,706 | 66.4% | 83.6% | 7.1% |
| StatCan 1902 | 4,542 | 68.2% | 86.9% | 7.2% |
| StatCan 1903 | 4,826 | 67.7% | 84.5% | 5.7% |
| Canadiana 1898 | 10,716 | 26.1% | 32.6% | 12.7% |
| Canadiana 1899 | 10,867 | 27.6% | 30.0% | 10.5% |
| **all, 67,596 rows** | | **55.3%** | **66.7%** | **8.5%** |

The StatCan verified share rose from ~40% to **~68%**, and join rates rose too (1898
96.6% -> 97.3%; Canadiana 1898 87.0% -> 93.3%, 1899 88.1% -> 94.6%).

The Canadiana volumes still verify at only ~27%, far below StatCan's ~68% on the same rows.
That gap is not yet explained and is the next thing to look at — it is most likely a
remaining left-page parsing difference, not a scan-quality difference, given that the two
witnesses agree cell-for-cell where both parse.

### Still not trustworthy: the witness comparison itself

`ca_compare_witnesses.py` keys rows on (normalised label, occurrence). That is too fragile:
one dropped row shifts every later occurrence of that label, and the "56.7% of cells differ"
it reports is mostly mispaired rows, not disagreeing scans — as the spot check above proves,
the scans agree exactly where they are compared correctly. **Do not quote the rescue rates
from `reports/witness_compare_*.md`.** Comparing two witnesses needs the same monotone
alignment used for left/right halves, run witness-against-witness. That is the next build.

## Step 7 — the Canadiana gap was my bug, not the scan (2026-08-30)

The previous step reported Canadiana verifying at ~27% against StatCan's ~68% on the same
rows and guessed at a "remaining left-page parsing difference". It was neither parsing nor
scan quality.

**`ca_align_spreads.main()` resolved the volume from the StatCan manifest by fiscal year.**
Running `--tag cdn_33_5_1898 --fy 1898` therefore read the *StatCan* markdown while applying
the *Canadiana* pair offsets — table offsets from one document indexed into another. Every
Canadiana figure in steps 4-6 was produced from mismatched documents and is void.

`--md` is now required for any tag that is not a `statcan_*` preferred source, and the
program refuses rather than silently resolving. Corrected:

| | joined | verified | +bracketed | efc_value filled |
|---|---:|---:|---:|---:|
| Canadiana 1898, before | 93.3% | 25.0% | 31.0% | 36.6% |
| **Canadiana 1898, after** | **96.9%** | **62.0%** | **78.5%** | **98.5%** |
| Canadiana 1899, after | 96.8% | 68.2% | 83.7% | 98.4% |

The two collections are of equal quality on this evidence. The earlier claim that the
bitonal microfilm scan was materially worse is not supported by anything measured here.

### Corrected totals, all eight witness-volumes

| witness | rows | verified | +bracketed | flagged | closure |
|---|---:|---:|---:|---:|---:|
| StatCan 1898 | 10,532 | 64.5% | 83.0% | 7.3% | 79.2% |
| StatCan 1899 | 10,649 | 67.7% | 79.9% | 7.4% | 91.5% |
| StatCan 1900 | 10,761 | 69.4% | 84.1% | 6.9% | 87.5% |
| StatCan 1901 | 4,706 | 66.4% | 83.6% | 7.1% | 95.1% |
| StatCan 1902 | 4,542 | 68.2% | 86.9% | 7.2% | 93.0% |
| StatCan 1903 | 4,826 | 67.7% | 84.5% | 5.7% | 89.1% |
| Canadiana 1898 | 10,447 | 62.0% | 78.5% | 12.0% | 88.6% |
| Canadiana 1899 | 10,539 | 68.2% | 83.7% | 10.0% | 91.3% |
| **total** | **67,002** | **66.6%** | **82.5%** | **8.3%** | |

## Step 8 — the two-witness question, answered (2026-08-30)

`ca_compare_witnesses.py` now matches rows by **aligning the two witnesses' label
sequences** (`difflib.SequenceMatcher` over normalised labels), comparing only rows inside
maximal identical runs and leaving the rest unmatched rather than guessed.

The previous (label, occurrence) key was the last artefact: the label is not unique -- the
1898+ layout puts countries and provinces in one column, so 'Iron > Ontario' recurs under
every country that shipped iron -- and one dropped row shifts every later occurrence of that
label. Mispaired rows are indistinguishable from disagreeing scans, which is where the
implausible "75% of cells differ" came from.

| | FY1898 | FY1899 |
|---|---:|---:|
| rows matched by sequence alignment | 5,038 | 5,717 |
| every comparable cell identical | **69.6%** | **78.3%** |
| some cells agree, some differ | 21.0% | 11.8% |
| all comparable cells differ | 9.1% | 8.8% |
| both witnesses' arithmetic closes | 3,499 | 4,621 |
| only StatCan closes | 279 | 436 |
| only Canadiana closes | 789 | 428 |
| neither closes | 424 | 184 |
| **damaged in one, sound in the other** | **21.4%** | **15.2%** |
| **good rate: one witness -> two** | **75.7% -> 91.5%** | **89.2% -> 96.8%** |

The damage is roughly symmetric between the collections, which is what independent OCR noise
should look like and is further evidence the two scans are of comparable quality.

**This is the answer to "when they agree we're happy, when they don't we dig".** A second
witness lifts the sound-row rate from 76-89% to **92-97%**, and it isolates the residue: 184
rows in 1899 and 424 in 1898 are damaged in both and are the genuine hand-check queue --
hundreds of rows, not thousands.

### Method note for whoever reads these numbers next

Three separate bugs in this build produced plausible-looking but wrong results, and all three
were caught by a number being *too good* or *too lopsided* rather than by a test failing:
a shifted column parse that still satisfied the closure check; a witness comparison whose
disagreement rate was impossibly high; a one-sided damage split. Symmetry and plausibility
checks earned their keep here. Prefer them to any single headline percentage.

## Step 9 — FY1904-1908 column map, and the decade completed (2026-08-30)

The 1904 tariff change moved the break. `ca_align_spreads.py` is now era-aware, detecting the
era from the right page's header (`SURTAX` present or not) and switching column map, closure
rule and scoring together:

```
GP  FY1898-1903   General + Preferential (Reciprocal in 1898)
    the break falls THROUGH the General Tariff group
    LEFT  5 : article | country/province | TOT imports qty | TOT imports value | GT qty
    RIGHT 8 : GT value | GT duty | PT qty | PT value | PT duty | TOT qty | TOT value | TOT duty

SX  FY1904-1908   Preferential + Surtax, General moved to the left page
    the break falls cleanly BETWEEN groups
    LEFT  7 : article | country | TOT qty | TOT value | GT qty | GT value | GT duty
    RIGHT 9 : PT qty | PT value | PT duty | SX qty | SX value | SX duty | TOT qty | TOT value | TOT duty
```

**The later layout is the easier one.** Because the break falls between groups, `GT + PT + SX
== Total` holds separately on **quantity, value and duty** — three independent identities
spanning the break, where era GP has one. Conversely era SX has no intra-right closure at all
(the General Tariff is on the other page), so a right row cannot be pre-screened on its own;
all that is testable alone is that the parts do not exceed the total.

That trade turns out strongly in SX's favour:

| era | years | joined | verified | +bracketed | flagged |
|---|---|---:|---:|---:|---:|
| GP | 1898-1903 | 95.9-97.3% | 60-69% | 78-87% | 5.7-12% |
| **SX** | **1904-1908** | **98.5-99.0%** | **80-86%** | **93-95%** | **1.4-2.6%** |

### All thirteen volumes

| volume | era | rows | verified | +bracketed | flagged |
|---|---|---:|---:|---:|---:|
| StatCan 1898 | GP | 10,532 | 62.4% | 82.9% | 7.3% |
| StatCan 1899 | GP | 10,651 | 66.8% | 79.8% | 7.5% |
| StatCan 1900 | GP | 10,763 | 69.1% | 84.0% | 6.9% |
| StatCan 1901 | GP | 4,709 | 63.1% | 83.2% | 7.2% |
| StatCan 1902 | GP | 4,542 | 65.9% | 86.7% | 7.2% |
| StatCan 1903 | GP | 4,826 | 66.4% | 84.4% | 5.7% |
| StatCan 1904 | SX | 4,969 | 82.9% | 93.9% | 1.8% |
| StatCan 1905 | SX | 5,290 | 85.6% | 95.1% | 1.4% |
| StatCan 1906 | SX | 5,316 | 79.6% | 93.3% | 1.6% |
| StatCan 1907 | SX | 5,515 | 83.6% | 93.5% | 2.2% |
| StatCan 1908 | SX | 5,772 | 82.4% | 93.9% | 2.6% |
| Canadiana 1898 | GP | 10,447 | 60.5% | 78.5% | 12.0% |
| Canadiana 1899 | GP | 10,540 | 67.3% | 83.6% | 10.0% |
| **total** | | **93,872** | **70.2%** | **85.7%** | **6.5%** |

**FY1898-1908 is now complete** on the StatCan witness, with Canadiana as a second witness for
1898-1899. Output: `db/canada/spread_rows_<tag>.csv`, one row per printed line, with `era`,
`align_status` and `key` on every row.

## FY1890-1896 is not this project's problem

The seven Canadiana volumes identified in step 4 (`24_3` … `31_4`) contain **no split spreads
at all** — `ca_pair_spreads.py` finds zero pairs in each. The split began with the FY1898
tariff, exactly as FY1897 showed. Those years are ordinary single-page tables and belong to
`ca_parse_imports.py` (regime C), which currently stops at FY1889 only because `raw_canada`
does. Closing FY1890-1896 means registering those volumes as a source for the existing
parser, not extending this one.

## Step 10 — the path now travels with the data (2026-08-30)

Audit of the bug class from step 7. Every other `ca_parse_*` script derives its document as
`RAW / tag / f'{tag}.md'` — the path comes *from* the tag, so the two cannot disagree. The
defect was specific to the new scripts, which took `--tag` for output naming and `--fy` for
input resolution and let them drift.

Structural fix rather than a guard on the caller: **`ca_pair_spreads.py` now records
`md_path` in the pairs TSV**, and `ca_align_spreads.py` reads the document from there.
Offsets and the document they were measured against travel together. An explicit `--md` may
only confirm the recorded path; a mismatch is refused:

```
$ ca_align_spreads.py --tag cdn_33_5_1898 --md .../CS4-4-1898-eng.md
--md .../CS4-4-1898-eng.md does not match the document these offsets were measured
against (.../oocihm.9_08052_33_5.md); refusing to index one book into another
```

All thirteen volumes regenerated; figures unchanged.

## Step 11 — FY1891-1897 recovered: 79,078 rows, no join required

FY1890-1896 turned out not to be one problem but two, and neither is the spread joiner.

| years | header | status |
|---|---|---|
| FY1868-**1890** | `ARTICLES AND COUNTRIES WHENCE IMPORTED \| PROVINCES INTO WHICH IMPORTED` | regime C. **FY1890 has the identical header to FY1889** — needs registering in `raw_canada/INDEX.tsv`, not new code |
| **FY1891-1897** | `ARTICLES IMPORTED \| COUNTRIES AND PROVINCES \| IMPORTED \| ENTERED FOR HOME CONSUMPTION` | a distinct single-page layout, 7 columns. New: `scripts/ca_parse_unsplit.py` |
| FY1898-1908 | the same statement, split across a spread | `ca_pair_spreads` + `ca_align_spreads` |

### A third instance of the same failure mode, caught before it ran

`ca_parse_imports.regime_of()` classifies the FY1891-1897 header as **regime B**, because it
contains ARTICLES, COUNTRIES and DUTY. Regime B is the 1877 'by Provinces' layout, with
different columns and a deliberate one-row label slip. Pointing the existing parser at these
seven volumes would have produced ~79,000 confident, wrong rows. `ca_parse_unsplit.py`
matches on the **full header signature** instead of keyword presence, and explicitly excludes
the split years' left page (which shares the first half of that signature but says
`TOTAL IMPORTS`).

That is now three times in this build that a keyword-level or year-level shortcut silently
addressed the wrong thing. The pattern is worth stating as a rule: **identify a table by its
whole header, and a document by the path that travelled with its offsets — never by a
substring or a year.**

### Result

`article | country/province | IMPORTED qty, value | ENTERED FOR HOME CONSUMPTION qty, value |
DUTY`, all on one page. Rows are emitted in the `ca_align_spreads` schema with
`align_status='whole'`, `key='unsplit'`: these rows were never split, so no join can be wrong.
That is a statement about join risk only — the digits still need a witness or a totals check.

| FY | volume | rows | efc_value populated |
|---|---|---:|---:|
| 1891 | `25_4` | 10,349 | 98.2% |
| 1892 | `26_4` | 11,076 | 98.2% |
| 1893 | `27_5` | 11,257 | 98.7% |
| 1894 | `28_4` | 11,066 | 98.3% |
| 1895 | `29_4` | 11,228 | 97.9% |
| 1896 | `31_4` | 12,126 | 98.2% |
| 1897 | `32_5` | 11,976 | 98.4% |
| **total** | | **79,078** | |

### Cross-validated on FY1897, which exists in both witnesses unsplit

| | |
|---|---:|
| rows, StatCan `CS4-4-1897` vs Canadiana `32_5` | 12,316 vs 11,976 |
| matched by label-sequence alignment | 8,341 |
| **every comparable cell identical** | **89.6%** |
| some agree, some differ | 4.8% |
| all comparable cells differ | 5.5% |

**89.6% is the highest two-witness agreement measured in this project**, against 69.6%
(FY1898) and 78.3% (FY1899) for the split years — which is exactly the expected ordering,
since the unsplit years carry no alignment risk at all. It is independent evidence that
`ca_parse_unsplit.py` reads the columns correctly.

## Corpus as it now stands

| span | method | rows |
|---|---|---:|
| FY1891-1897 | single page, no join | 79,078 (Canadiana) + 12,316 (StatCan 1897) |
| FY1898-1908 | spread, joined and graded | 93,872 (11 StatCan + 2 Canadiana volumes) |

Still open: FY1890 registration for `ca_parse_imports` (regime C, no new code); the No. 17
summary family; a printed-totals closure check for the unsplit years; second witness for
FY1900-1908 when those Canadiana volumes are fetched.

## Step 12 — printed-arithmetic check for the unsplit years: mostly a negative result

`scripts/ca_check_unsplit.py`. The idea: the larger articles in FY1891-1897 are printed
twice, once broken by country and once by province, some with a printed grand total, so the
two breakdowns and the total must agree. Where the labels parse cleanly it works exactly as
hoped:

```
Ale, beer and porter, in bottles   countries 154,190  provinces 154,190  printed 154,190
Ale, beer and porter, in casks     countries  28,332  provinces  28,332  printed  28,332
Ale, ginger                        countries   5,805  provinces   5,805  printed       -
```

**But it does not generalise, and should not be used as a quality gate.** Across the seven
volumes only ~20% of rows sit in a block with two breakdowns at all — the printer gave the
province split to major articles only — and of the blocks that can be checked, roughly 5%
pass every available comparison and 24% pass some.

The cause is the label structure, not the arithmetic. These volumes use ditto marks and
sub-articles, so the two label columns are not reliably (article, country):

```
'United States.... > " Sheep.....'      country in the article slot
'Total..... > " Sheep.....'             sub-article in the province slot
```

A block-level check needs to know which article a row belongs to, and that is exactly what
these labels do not reliably say. Fixing it means a proper article/sub-article state machine
of the kind `ca_parse_imports.py` already carries for regime C — a real piece of work, not a
tweak, and worth doing only if the second witness proves insufficient.

**For the unsplit years the second witness is the usable verification**, and it is already
in hand: FY1897 in both scans agrees cell-for-cell on 89.6% of matched rows (step 11).

### One real bug came out of it

Chandra infers `rowspan` from the image and sometimes makes one too long. The stale carry
then occupies column 0 while the row's real first cell is pushed right, so a 6-column row
comes back with 8 cells and an article label sits in the country slot:

```
raw   <td rowspan="5">" Sheep.....</td><td>Great Britain.....</td><td>640</td>...
got   ['Total.....', '" Sheep.....', 'Great Britain.....', '640', ...]     8 cells, 6 columns
```

Strict HTML semantics reproduce that faithfully, which is not what is wanted from a table
whose spans are guesses. `expand_rowspans()` now takes the printed width and, when a row
would exceed it, drops the carried cells for that row and uses the row as printed.

Applied to every caller. **No change to any split-year figure** (FY1900 69.1% verified,
FY1905 85.6%, Canadiana FY1898 61.1% — all unmoved), so it corrects label corruption without
disturbing the value columns.
