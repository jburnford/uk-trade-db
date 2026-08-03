# Four annual volumes are excluded from the country parser by a wrong assumption

Prompted by the question of why recent rounds move the metric by one cell.

## Where the remaining defects actually are

Of the payload's 9,473 commodity-years, 4,286 are `nodata`. That splits three ways:

| pool | cells | GBP |
|---|---|---|
| `nodata` in nodes that have origins in **other** years (real gaps) | 1,789 | £2.79bn |
| `nodata` in **anchor-only** nodes (no origin table in any year) | 2,253 | £258M |
| `within5` sitting inside 0.5% of exact01 (near-misses, not nodata) | 696 | — |

And the first pool splits again, decisively, by **year**:

| gap cells | where |
|---|---|
| **1,121 (63%)** | outside 1872-1899 — **884 in 1866-71, 237 in 1900** |
| 668 | inside 1872-1899 |

`country_obs` and `country_obs_inf` both cover **1872-1899 only**. Every Tier-1
outside that window comes from an abstract's five-year comparative column, so the
gap years had no origin table in the corpus to match against.

## Why: a blanket exclusion whose stated reason is wrong

`scripts/parse_country.py` globs only `as_*`:

```
779:  str(p) for p in (BASE / 'raw').iterdir() if p.name.startswith('as_')
 39:  Usage: python3 parse_country.py [as_dir ...]   (tn_* monthly volumes skipped)
```

Six `tn_` volumes sit in `raw/`. Their own title pages say what they are:

| volume | title page says | covers | already a Tier-1 source | country-parsed |
|---|---|---|---|---|
| `tn_1871` | "ANNUAL STATEMENT … IN THE YEAR 1870" | **1870** | yes | **no** |
| `tn_1872` | "For each Month during the Year 1872" | monthly | no | no — correct |
| `tn_1895` | "ANNUAL STATEMENT … FOR THE YEAR 1894" | **1894** | yes | **no** |
| `tn_1899` | "ANNUAL STATEMENT … 1898, COMPARED WITH THE FOUR PRECEDING YEARS" | **1894-98** | yes | **no** |
| `tn_1900` | "For each Month during the Year 1900" | monthly | no | no — correct |
| `tn_1901` | "ANNUAL STATEMENT … 1900 COMPARED WITH THE FOUR PRECEDING YEARS. VOLUME I. (Abstract and **Detailed Tables** of Imports and Exports)" | **1896-1900** | yes | **no** |

**Four of the six are annual statements with detailed origin tables**, and all
four are *already trusted as Tier-1 sources* — `abstract_obs` and `infinity_obs`
carry `tn_1871`, `tn_1895`, `tn_1899` and `tn_1901`. Only the country parser
excludes them, on a description that is accurate for `tn_1872` and `tn_1900`
alone.

Their origin-table density matches the volumes that are parsed. `tn_1901` is
9.8 MB with 183 `From Germany` and 707 `COUNTRIES` occurrences, against
`as_1899`'s 8.8 MB / 158 / 639. Its tables print five years per row —
`Gunpowder: From Germany — 200 127 — 1,333` — so one volume carries 1896-1900.

## What it would reach

- **`tn_1901`** covers **1900**, where 237 gap cells sit — the single largest
  year in the pool — plus a second witness for 1896-99.
- **`tn_1871`** covers **1870** (167 gap cells) and its comparative columns reach
  back toward 1866-69 (another ~560).
- **`tn_1895` and `tn_1899`** fall inside the already-parsed window, so they add a
  **second independent witness** for 1894 and 1894-98 — which matters directly,
  since rank 1 requires the same figure printed in two volumes and agreeing.

## Done, and what it took

User authorised all four annual volumes. Parsing them naively **regressed the
corpus**, and the two failures are worth recording because neither was obvious.

**1. Overlapping years are destructive, not merely noisy.** `tn_1899` and
`tn_1901` print five years per row, so admitting their full span delivered the
same (commodity, country, year) twice with different provenance and the pipeline
neither deduped nor arbitrated it. `Cotton — Raw` 1895 double-counted to **1.79x**
its printed total and 1887 **lost all 23 of its cells**. Corpus-wide that run was
438 cells better, 233 worse, **180 previously-exact cells broken**, and
GBP-weighted agreement fell 51.9% -> 46.5%. The tn_ volumes are therefore admitted
only for years outside the `as_*` span, i.e. **1870 and 1900** (`keep_row`).

**2. Pass 1's vocabulary is corpus-wide, so a new volume re-parses the old ones.**
With the year restriction in place `Cotton — Raw` was *still* broken across
1880-1895 — years no tn row could reach. The cause is that pass 1 seeds a shared
group/sub vocabulary that drives pass 2's header classification for **every**
volume. Adding the tn volumes to that seed moved 93 payload cells the wrong way
and broke 69 exact ones. Seeding the vocabulary from `as_*` only fixes it: the tn
volumes are still parsed in pass 2, against the vocabulary the corpus already had.

With both fixes, **zero pre-existing volumes change a single row** in either
engine — the addition is arithmetically additive.

## Result

```
                      before        after
commodity-years        9,473        9,509
exact01                3,589        3,704     (+115)
                       37.9%        39.0%
GBP within 0.1%        51.9%        51.9%
GBP within 5%          68.9%        71.6%     (+2.7)
nodata                 4,286        4,044     (-242)
```

Per-cell: **281 better, 19 worse**, 214 new cells (65 exact01), 178 gone.
Chandra gains 32,015 rows, Infinity 30,808 — all in 1870 and 1900.

Biggest single gains are the whole of **1900**, which had no origin data at all:
Maize, Cotton Raw, Fir, Wool, Oxen, Wheat and Sugar all move off `nodata`.

## Still open

- **19 regressions, of which 16 were exact.** The material ones are `Wool — Sheep
  Or Lambs'` **1893-96**, which move to `within5` at ~1.02 — a 2% over-count once
  the second witness is admitted — and `Linen Yarn` 1873/1891/1893, which fall to
  `nodata`. Both need a look; neither is large enough to outweigh +115.
- **1866-1869 remain unreachable.** `tn_1871` is a single-year annual for 1870;
  its country tables do not carry the four preceding years, so ~450 gap cells in
  1866-69 still have no origin table in the corpus.
- `tn_1895` and `tn_1899` contribute nothing under the year restriction (their
  years are inside the `as_*` span). Admitting them as a genuine second witness
  needs the overlap arbitration that failure 1 showed is missing.
