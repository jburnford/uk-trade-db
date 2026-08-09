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
| export_uk | obs | 15,288 | **45.9%** | 69.7% |
| export_uk | inf | 14,691 | 38.9% | 65.6% |
| reexport | obs | 19,365 | **53.3%** | 71.3% |

For comparison the curated import payload stands at 39.9% exact / 52.7% within
5%. **Both unprocessed flows already close better than the finished import
dataset**, because the anchor is denser and sits in the same block.

Export closure by era (obs, member sections):

| era | exact |
|---|---:|
| 1870–1892 | 49–83% |
| 1893–1896 | 36–41% |
| 1897–1900 | 17–22% |

The same regime break the imports show at 1893, and sharper. It is one defect
class affecting both flows — the highest-value structural target in the corpus.

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
is the trustworthy window** (71–86% corroborated). 1897–1900 carries plausible
values on almost no proof and should not be used unrepaired.

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

1. **The 1893 break**, in both flows. One class, the largest payoff available.
2. **Row-fusion repair.** The class is identified and the section arithmetic
   supplies the target sum; needs a splitter plus page adjudication.
3. **Promote re-exports** ahead of the export tail on the measured numbers.
4. Only then the per-block queue campaign the plan describes.
