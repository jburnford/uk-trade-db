# Canada imports completion — working log

One section per phase of `CANADA_IMPORTS_PLAN.md`: what ran, the numbers, what was decided.

## Phase 0 — bookkeeping (2026-08-31, commit 2b01a6e)

FY1891–1897 registered in `raw_canada/INDEX.tsv` with the new **NOPARSE note-prefix**
(all four INDEX-driven parsers skip such rows); FY1897 = `32_5`, `32_4` demoted to
secondary. `reference/canada_printed_totals.csv` extended 1890–1908 by per-cell majority
vote across five StatCan prefatory No. 1 tables (FY1907 is a genuine 9-month year;
FY1908 single-witness). `sweep_junk_country_labels`: 9 country labels recovered from the
article slot, 177 numeric-junk labels → `?`. Ship test 0/0.

## Phase 1 — page-break Total-block defect (2026-08-31, commit 315c62b)

Pass (a'') + hijacker-label restore. 34 carry-backs, 125 restored rows.
Country-`?` $2,995,809 → $945,345; 1886 abstract 0.975 → 0.991, 1885 → 0.990.
Ship 20 better / 9 worse (worse = sub-$30K on polluted cells).
Full mechanics in `reports/canada_page_break_total_findings.md`.

## Phase 2 — shortlist with in-table proofs (2026-08-31, commits d4381c8..cd0df63)

- **2a** Abstract oracle row-sanity (`repair_row_arithmetic`): 23 cells repaired by the
  two-identity pin (row `dut+free==total` × column `TOTAL−Σcountries`), 19 flagged.
  1881 France Ontario phantom dead; 1881 abstract column now equals the printed national
  EfC exactly.
- **2b** Province-order pairs arbitrated by the abstract: 3 swapped, 1 confirmed,
  10 undecided (left flagged). Ship 10/0.
- **2c** 1880 tea t418-419 solved by exhaustive assignment (both value columns exact,
  duty pins to the cent); **manual-repair channel built**
  (`reference/canada_manual_repairs.csv`, strict match-or-abort). Ship 12/0.
- **2d** Duplicate-name pairs: corkwood = already distinguished by parent 'Barks' (no
  defect); champagne = nominal only; spades renamed (Summary EXACT); ginger span renamed
  (raw heading + Summary EXACT); calf-kid 1887 = ONE article, its 'TOTAL' rows were the
  US run (all exact), remaining GB/US runs lost at the page break → phase 3 list.
  Ship 9/1 (the 1 over-ruled by exact closure).

**State after phase 2**: country-`?` $939,991, article-`?` $1,982,848; abstract ratios
1880-90: 1.000/.978/.990/.988/.991/.990/.991/.996/.991/.999/.988. Parked coverage:
`reports/canada_phase3_coverage_list.md`.

## Phase 3 — StatCan second engine (2026-08-31, commit 32c36ca; IN PROGRESS)

**3a done**: `raw_canada/INDEX_W2.tsv` + `ca_parse_witness.py` →
`db/canada/imports_general_rows_w2.csv` (185,675 rows, 11 regime-C years). The regime
parser needed NO changes for the StatCan scans. Witness quality:
`reports/canada_witness_parse.md` (1882 is the witness's bad year, 1.121 — treat its
cells with suspicion in every gate).

**3b first merge done**: `ca_merge_witnesses.py` — **the chain now runs
parse → merge → infer_articles → infer_countries → export → check.**
Pass L label-transfer (11 runs $471K), pass I gated insertion (90 blocks $162K).
Ship 187/9. Country-`?` now $677,582.

**Still open in phase 3**:
- the value-fill class (Canadiana rows with BLANK values, witness has them — 1883 GB
  machinery is the type case);
- the misfiled-row class (1884 peaches GB run sits under 'Oranges and lemons' as bare
  country_total rows — witness shows the truth; needs a row-level correction pass);
- the big under cells still open: 1886 GB Ontario −1.02M (witness reads +2.6% over
  there — needs per-block arbitration, not cell fill), 1881 Newfoundland, 1882
  sugar-molasses, 1883/85 GB province unders;
- regime B years through the witness (cheap once trusted);
- 1890's unmatched abstract value 685,649.

### Phase 3 continued (same day, commits through HEAD)

- **Pass F** (value fill): 192 blank-value rows, $1.13M — 1882 sugar-molasses closed
  (US NS within $142 of print).
- **Cross-year insertion**: G1 relaxed to corpus-wide article existence + fragment
  guard; 112 blocks, $977K — 1881 Newfoundland recovered from the witness.
- Ratios now: 1880 1.000 / 1881 0.986 / 1882 0.994 / 1883 0.988 / 1884 0.994 /
  1885 0.994 / 1886 0.991 / 1887 0.997 / 1888 0.991 / 1889 0.999 / 1890 0.993.
  Country-`?` $677,582.
- Still open (phase 3): misfiled-row class (1884 peaches GB under Oranges); the GB
  Ontario/Quebec dut unders 1881/1883/1886 (witness over-reads the same cells — needs
  block-level arbitration, the next build); regime B years through the witness; 1890
  unmatched abstract 685,649; witness 1882 quarantine check.

### Phase 3, second day (2026-09-01, commits 4a269bc..e469296)

The merge grew to six operations — **L** label transfer (11 runs, $471K), **R** row
completion against the block's own printed total (8), **B** block replacement for
structurally broken blocks (252 blocks, $15.1M turned over; fingerprint matching because
article names differ between witnesses; exact cross-closure — witness details equal the
CANADIANA printed total — over-rules the per-cell gate), **F** value fill (128, $861K),
**I** gated insertion (104, $594K; G3 fallback under the 60%-residual-shrink fit test),
plus the parse-side `sweep_total_country` (the $705K 1886 double-count).

Direct closures this day: 1887 Switzerland Quebec EXACT (the re-OCR item), 1886 GB
Ontario's missing wool million, 1881 Greece exact, 1882 Newfoundland Quebec exact,
ckey folds worth $1.4M of matching (Sp. W. Indies, Spanish Possessions all other,
Brit W Indies, E. Guiana, Central Am. States, Norway and Sweden).

**Abstract ratios 1880–90: 1.001/.985/.996/.988/.995/.996/1.004/1.000/.992/.998/1.001.**
National efc ratios all within ±1.2% (nine of eleven within ±0.7%). Country-`?` $952K —
$275K of that is the 1881 Newfoundland-provision sub-articles (Fish Oil / Seal Oil)
deliberately parked at `?`: the witnesses disagree and Newfoundland would overshoot the
printed Quebec cell.

**Remaining for phase 3 close-out**: 1881 GB Ontario (−790K) and 1883 GB Quebec/Ontario
(−505K/−390K) — the witness is ALSO under there (−341K/−265K/−188K), so full closure is
re-OCR/Gemini territory; the merged-vs-witness gap is variant-name mirror residue
('flannele'/'flannels', 'cropes'/'crapes') that nets zero per cell. 1886/1880 run ~0.4%
OVER nationally (residual junk mass, unlocated). Regime B witness runs not yet done.
1885 US NB / 1888 US BC duty cells drift over. The misfiled-row class (1884 peaches GB
under Oranges) still unbuilt.

## Phase 4 — first survey (2026-09-01; merge attempt REVERTED)

The witness parse for regime A/B ran clean (`ca_parse_witness.py regimeAB`):
**the greyscale witness transforms regime A** — province-statement efc ratios
0.797/0.911/1.080/0.949/0.913/0.933/0.938/0.919 (1868–75) against Canadiana's
0.72/0.69/0.60/0.48/0.55/0.53/0.62/0.96. Regime B stays Canadiana-primary (the
witness reads 0.894/1.030/0.981/1.160 there — worse).

**Discovery: 1874–75 print a DOMINION RECAPITULATION** — a national article×country
statement. Canadiana's 1874 Dominion sums to 127,607,261 vs printed 127,404,169
(**1.0016**) while its province statements manage 0.624. The national series for
1874–75 should be sourced from the Dominion statement; the exports currently exclude
it from nothing/everything inconsistently — decide in the phase-4 session.

A first block-vote merge (`ca_merge_regimeA.py`) was written, run, measured, and
**reverted**: it loses mass (1868 → 0.613) because a detail-complete block with an
unparsed total counts as non-closing and gets superseded, and sequence-position
pairing mis-pairs. The script is annotated with the failure analysis and the three
requirements for the real vote (no-total ≠ total-mismatch; fingerprint pairing;
per-statement printed grands as arbiter). Nothing from this attempt is in the corpus.

## Phase 4 — the real vote (2026-09-01, commits 4733283+)

The rebuilt vote works (details in the commit): fingerprint pairing, no-total vs
mismatch closure semantics, cross-closure against Canadiana's own printed totals,
room-gated insertions in both value columns, and a regime-A value-fill for the
column-loss class (1870's efc column). Regime C ship test 0/0 — the two merge layers
do not interfere.

**Province-statement efc ratios 1868–75**:
.771 / .831 / .700 / .619 / .710 / .666 / .778 / .986 (from .716/.691/.602/.480/.550/.529/.624/.958).

**The Dominion switch**: 1874–75 national + country series now come from the Dominion
recapitulation. Against the printed EfC-by-country series: 1874 GB 1.015 / US 0.995 /
Germany 0.989 (France 1.367 — a residual defect, filed); 1875 GB 0.931 / US 0.973 /
France 1.003 / Germany 0.919.

**The honest ceiling, stated in the origins report**: 1868–73 sit at 0.62–0.83 of
print after the vote — both scans fail on those years (bitonal garble vs greyscale
junk), and only per-block closure proofs transfer. Getting further means a third
engine (targeted Gemini per the standing decision) or re-imaging. The plan's §5
phase-4 acceptance (N ≥ 0.97) is MET for 1874–75 via the Dominion source and NOT MET
for 1868–73 — recorded here as the §4.2 written explanation.

**Bonus for the exports campaign**: `reference/canada_country_series_voted.csv`
already carries a printed by-country EXPORTS series (379 rows, 1872+) — a ready
Tier-1 anchor for Statement No. 4 parsing.

**Chain order (canonical, updated)**: `ca_parse_imports` → `ca_merge_witnesses` →
`ca_merge_regimeA` → `ca_infer_lost_articles` → `ca_infer_lost_countries` →
`ca_export_country_year` → `ca_check_abstract`; `ca_parse_witness` (both roles, one
file) must run whenever witness OCR changes; `ca_parse_abstract` on volume ingest.

## Phase 5 — regime D parser, step 1 (2026-09-01, commit 0636a53)

**Design correction**: the cross-tab does NOT end at FY1890. All seven 1891–97 volumes
print one combined 'COUNTRIES AND PROVINCES' column; dash-suffixed countries open
province runs (277 'United States—' headers in 1893). The unsplit CSVs lose exactly
those headers → `ca_parse_regimeD.py` parses from raw.

National efc: 1891 **0.987** / 1892 .819 / 1893 .787 / 1894 .861 / 1895 .714 /
1896 .691 / 1897 .756. The unders are Canadiana OCR coverage; the StatCan witness for
1891–96 is on disk. Staging output `imports_general_rows_d.csv` — NOT yet promoted.

**Queued for phase-5 step 2**: (a) the witness merge for regime D (the phase-3
pattern); (b) the GS-tail 'ABSTRACT BY COUNTRIES AND PROVINCES' as the per-cell
oracle (compact per-country layout, t331+ in 1891); (c) orphan_total placement;
(d) section-boundary hardening (1894 FREE > DUT smells); (e) promotion into the main
corpus + the export/check plumbing for regime D.

## Phase 5 — step 2 (2026-09-01): parser v3, witness, vote, oracle

See `reports/completion_log.md` (A1 step 1–2) for the full account. Headline: the regime D
shortfall was the parser mis-slotting value-only rows, not OCR coverage; after the header-driven
column map, the slip cascade, the recap/section-total tags, the StatCan witness vote and the
1891–97 Abstract oracle, the seven years read **0.944 / 0.901 / 0.917 / 0.980 / 0.953 / 0.929 /
1.015** of print (from 0.987* / .819 / .787 / .861 / .714 / .691 / .756). Staging only; promotion
and the GB/US under-read are the next step. Chain for the staging corpus:
`ca_parse_regimeD.py` → `ca_parse_regimeD.py --witness` → `ca_merge_regimeD.py`;
`ca_parse_abstract.py` now covers 1891–97.

## Phase 5 — step 3 (2026-09-01): promoted

Regime D rows enter the exports through `imports_general_rows_d.csv` (read by
`ca_export_country_year.py`); origins report 1868–1897. Absorption guard and cross-closure added
to the vote; 1891–97 at .925/.896/.917/.982/.952/.923/1.015 of print. The UK↔Canada mirror passes
every year 1890–1896 on the promoted data. Remaining under-read is diffuse (GB/US), filed for a
third engine. Next: phase 6 (FY1898–1908 spread rows into the schema).
