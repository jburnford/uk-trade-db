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

## Not done — escalated

Adding volumes to the country corpus **changes the vote** for every year they
touch, so this is not a change to make unilaterally. Recorded here and put to the
user.

Two risks worth stating before anyone runs it:
1. The five-year comparative layout in `tn_1899`/`tn_1901` is the `feed_multiyear`
   shape the parser handles for `as_1897-99`, but it has never been exercised on
   these files.
2. `tn_1901`'s 1896-99 columns overlap years already parsed from `as_*`. Where
   they agree the rank improves; where they disagree the vote moves, and some
   currently-exact cells could shift.
