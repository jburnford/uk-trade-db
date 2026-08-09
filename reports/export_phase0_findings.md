# Exports, phase 0: the anchor is in the block, and two plan premises were stale

Written 2026-08-09, at the start of the export campaign. Measurement and
instrument-building only — **no data was repaired in this session.**

## The finding that reshapes the campaign

`EXPORT_CAMPAIGN_PLAN.md` phase 0 says: *"Without clean T1 anchors nothing
downstream is provable."* That is not true. The export country tables carry
their own anchor, printed on the same page, in a three-level hierarchy:

```
Russia … Other Foreign Countries        <- member rows
TOTAL                                   <- section subtotal (Foreign)
Gibraltar … Other British Possessions   <- member rows
TOTAL                                   <- section subtotal (British Possessions)
TOTAL                                   <- grand total = Foreign + British
```

Verified on `as_1885 / COTTON MANUFACTURES / Piece Goods, Plain`: the two grand
totals in that block close **exactly** (14,456,950 + 16,108,527 = 30,565,477;
10,755,356 + 6,950,781 = 17,706,137).

This matters for three reasons:

1. **No label join is needed.** The abstract-line route requires matching dirty
   article strings between `abstract_obs` and `country_obs`; a naive attempt
   matched only 24% of blocks, and the failures were join failures, not data
   failures. The in-block anchor needs no join at all.
2. **Coverage is denser than imports.** 84% of export blocks carry at least one
   printed anchor. On the import side a third of commodity-years have no
   reachable anchor whatsoever (2,374 anchor-only + 801 unpublished).
3. **It replaces gold.** There is no gold transcription for exports and none is
   needed as the primary instrument: a destination cell inside a section that
   sums exactly to its printed subtotal has been corroborated by the
   compositor. Gold would calibrate; the page proves.

The parser fuses adjacent printed tables into one block — a block with 6 or 9
`TOTAL` rows is two or three tables run together. `reconcile_exports.py` splits
on the rollup pattern rather than assuming one table per block.

## The measured baseline

`scripts/reconcile_exports.py`, member sections (destination rows against their
own printed subtotal), value measure:

| flow | engine | sections | exact (≤0.1%) | within 5% |
|---|---|---:|---:|---:|
| export_uk | obs | 15,288 | 45.9% | 69.7% |
| export_uk | obs, **own-year witnesses only** | 9,699 | **59.2%** | **77.1%** |
| export_uk | inf | 14,691 | 38.9% | 65.6% |
| reexport | obs | 19,365 | 53.3% | 71.3% |

For comparison the curated import payload stands at 39.9% exact / 52.7% within
5%. **Both unprocessed flows already close better than the finished import
dataset**, because the anchor is denser and sits in the same block.

## There is no 1893 break — in either flow

The first pass of this metric pooled every witness and showed exports falling
from ~65% exact before 1893 to ~38% after. That collapse is an artifact of
pooling. Split by witness role — a volume is the own-year witness for its
maximum year, every other year it carries is a comparative reprint:

| year | own-year exact | comparative exact |
|---|---:|---:|
| 1893 | 73.1% | 11.3% |
| 1894 | 67.7% | 20.6% |
| 1895 | 75.1% | 25.7% |
| 1896 | 72.4% | 24.8% |
| **1897** | **8.2%** | 21.0% |
| **1898** | **16.4%** | 28.0% |
| 1899 | 18.2% | — |
| 1900 | 19.0% | — |

The own-year volumes `as_1893`–`as_1896` close at 67–75%, indistinguishable
from the 1880s. The same test on **imports** gives 77.5 / 66.9 / 77.9 / 81.0%
own-year against 33.6 / 44.5 / 45.9 / 48.5% comparative.

So the 1893 break that the import balanced panel shows is the **vote being
poisoned by comparative reprints that are half as accurate as the contemporary
volume**. `integrate_sources.py` line 564 tallies a plain unweighted majority
(`Counter(round(r['q']) for r in readings)`) with no volume provenance, so two
reprints from `as_1898`/`as_1899` outvote the contemporary `as_1895`. This is
the mechanism already recorded anecdotally as the lone-reprint tie-break
(bacon 1893/94/97, copper 1888, hams 1898) — now measured at corpus scale.

**The real break is at 1897**, and it is confined to the four years for which
no single-year volume exists (1897–1900).

### What the 1897–1900 error actually is: near, not wrong

The exact-closure bar makes 1897–1900 look destroyed. It is not. Measured on
member-section deviation across all witnesses:

| flow | era | ≤0.1% | ≤1% | ≤2% | ≤5% | **median dev** |
|---|---|---:|---:|---:|---:|---:|
| export | 1870–1896 | 53.4% | 64.3% | 68.1% | 73.4% | **0.04%** |
| export | 1897–1900 | 18.8% | 38.4% | 46.4% | 56.5% | **2.69%** |
| import | 1870–1896 | 67.2% | 75.9% | 78.7% | 82.0% | **0.00%** |
| import | 1897–1900 | 42.4% | 57.9% | 63.9% | 71.2% | **0.33%** |

The regime change is from *exact* to *approximate*, not from right to wrong.
A median section in 1897–1900 is off by 2.7% (exports) or 0.33% (imports).
**That supports trend and direction-of-change analysis; it does not support
precise level claims or small year-on-year differences.** Earlier drafts of
this report called those years unusable — too harsh.

Diagnosis of the mechanism is **incomplete**. Two candidates were tested:

- *Own-year value column collapses.* True in `as_1897 ALKALI`, where the
  Foreign section closes at **−71.6%** while British Possessions in the same
  column closes at −1.39%, and where `as_1898` and `as_1899` agree exactly on
  values `as_1897` reads ~10x too small (Germany 40,904 against 3,994).
  **But not general** — a within-block test of implied unit price (own-year
  column against the other columns of the same block, no cross-volume join)
  gives a median ratio of 0.96–1.01, with only 3–10% of blocks below 0.5.
  So value-collapse is a real class covering roughly 5–10% of blocks, not the
  dominant mode.
- *The metric is miscounting comparative layouts.* Ruled out — the walker was
  hand-traced on the alkali block and its section boundaries are right.

What drives the remaining bulk of the 1897–1900 deviation is **not yet known**.

### The trap in the obvious fix

Do not implement "prefer the own-year witness". For 1897 and 1898 the ordering
**inverts** — the comparative reprints close better than the contemporary
volume (1897: 21.0% comp against 8.2% own). What degrades is a column position
in the five-year comparative layout, not reprinting as such, and a volume's own
year sits in the worst position. The witness must be chosen per year on
measured closure.

Sizing the import-side prize was attempted and **abandoned as unreliable**: the
exact-string join between `country_obs` and `country_year_final` matched only
1,853 rows, so its 9% disagreement rate measures the join, not the data. Any
change to the vote needs the payload snapshot and per-cell diff, not a DB-level
count.

## Two plan premises corrected

**Phase 1 ("recover a second engine for exports", 1–2 sessions) is largely
unnecessary.** The round-19 diagnosis was that Infinity reads export country
columns as one run-on string so consensus never fires. Measured now:

| flow | obs cells | inf cells | paired | agree |
|---|---:|---:|---:|---:|
| import | 142,280 | 132,164 | 33,448 | 85.7% |
| export_uk | 218,577 | 189,480 | 45,249 | **76.3%** |
| reexport | 104,830 | 93,122 | 21,572 | 82.7% |

189,480 clean inf export cells at 76.3% agreement is a working second engine.
(The low pairing count is a join artifact — the key includes raw article
strings, which drift between engines — not missing data.)

**Re-exports are the cleanest flow, not the hardest.** The plan schedules them
last, in phase 4, as the small hard remainder. They close best of all three.
Consider promoting them: the same instruments apply and the yield is higher.

**obs (Chandra) is the primary export engine**, as it is for imports — 45.9%
against inf's 38.9%.

## Canada

The destination vocabulary resolves cleanly once witnesses are deduplicated by
volume. A volume is the primary witness for its **maximum** year: `as_1897`
covers 1893–97 but is primary only for 1897; `tn_1871` is primary for 1870 and
`tn_1901` for 1900. Summing across volumes double-counts — the raw sum for 1895
comes to £21M against a true ~£5M because three volumes reprint it.

| period | printed label | note |
|---|---|---|
| 1870–1896 | British North America | **includes Newfoundland** |
| 1897–1900 | Canada + Newfoundland separately | splice as Canada+Nfld to match BNA |
| 1880 | both, inside one volume | BNA 35 articles + Canada 76 — a mid-volume label change |

`British North America` sits at **68.7% corroboration** — the share of its cells
inside an exactly-closing section — the second-highest of any major destination
after Sweden and Norway (72.4%). The `Canada` label sits at 20.4% only because
it lives almost entirely in the degraded 1897–1900 volumes.

Own-year series (`reports/canada_export_series.csv`, 8,101 cells, 4,620
own-year), corroborated share = tier A+B+C by value:

```
1870  £9.30M  45%     1881 £12.21M  23%     1892  £7.24M  60%
1872  £9.46M  70%     1882 £10.52M  31%     1893  £6.64M  65%
1873  £9.75M  24%     1883  £8.55M  60%     1894  £5.97M  79%
1874  GARBAGE  0%     1884  £8.73M  43%     1895  £5.28M  71%
1875  £9.51M  62%     1885  £6.75M  77%     1896  £5.56M  74%
1876  £8.10M  45%     1886  £7.17M  76%     1897  £5.06M   4%
1877 £10.02M  37%     1887  £7.76M  73%     1898  £5.31M   7%
1878  £8.67M  33%     1888  £7.35M  78%     1899  £6.69M  20%
1879  £6.91M  33%     1889  £8.04M  86%     1900  £7.65M  27%
1880  £8.73M  28%     1890  £7.12M  83%
                      1891  £6.89M  86%
```

The shape is historically right — high early 1870s, an 1881–82 peak during CPR
construction, long decline to a mid-1890s trough, recovery from 1899. **1885–96
is the trustworthy window** (71–86% corroborated). 1897–1900 fails the exact
bar, but the median section there is off by only ~2.7% — usable for trend and
direction, not for precise levels or small year-on-year differences. See the
1897–1900 section above.

## The catastrophic tail

`scripts/detect_impossible_cells.py` flags destination cells exceeding the
subtotal they are printed under — threshold-free, pure arithmetic against the
page. **2,028 export cells** contradict their own subtotal.

The worst share one signature: the *label* is two printed lines fused
(`United States : Atlantic Pacific`, `British India: Bombay and …`), and the
digits fuse with them. `as_1880 / Jute Manufactures` row 1791 reads
£94,998,020,000 with a null quantity; the section arithmetic says the two
fused rows should carry £974,815 between them.

1874 is the worst year for Canada and is a single family: all 42 absurd cells
in `as_1874` are WOOLLEN and WORSTED MANUFACTURES, three articles. One cell —
Narrow Cloths, British North America — reads £45,265,090,000 and alone accounts
for the £45.27bn year total; the remaining 1874 cells sum to £8.40M, in line
with 1873 (£9.75M) and 1875 (£9.51M). The inf engine reads that block with a
different destination list and sane values (BNA £166,188 on 1,447,020 yards =
£0.115/yd), closing to within 3.8% of its printed total.

**Not repaired.** obs and inf disagree on which destinations belong to the
article, so the block needs the page image to settle — Phase 3 work.

## Instruments added

- `scripts/reconcile_exports.py` — the campaign metric. Section-aware in-block
  closure, all flows, both engines, `--country-report` for per-destination
  corroboration.
- `scripts/export_country_series.py` — per-destination series with volume
  dedup, cross-engine pairing on a normalised article key, and A–X tiering by
  printed-section corroboration.
- `scripts/detect_impossible_cells.py` — cells contradicting their own printed
  subtotal.

## Next

1. **The 1897–1900 block**, in both flows. Four years, no clean single-year
   volume, and the contemporary column is the worst-parsed one. This is the
   real structural target and it is where the Canada series dies (4–27%
   corroborated against 71–86% for 1885–96).
2. **Witness selection in the vote**, import side. The provenance blindness is
   proven; the remedy is not "prefer own-year" but a per-year measured choice.
   Requires payload snapshot + `diff_payload_cells.py`, never a DB-level count.
3. **Row-fusion repair.** The class is identified and the section arithmetic
   supplies the target sum; needs a splitter plus page adjudication.
4. **Promote re-exports** ahead of the export tail on the measured numbers.
5. Only then the per-block queue campaign the plan describes.
