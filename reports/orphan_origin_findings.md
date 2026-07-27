# Orphan origin tables — findings

A commodity's **national total** and its **origin table** are printed
independently. That makes a test available that needs no page image, no second
OCR engine and no vote: if an unanchored label's countries sum to some *other*
commodity's printed national total, year after year, it is that commodity's
origin table wearing a name the parser invented. One value coincidence is
possible. Two is not. Fourteen is a proof.

Round 34 (`reports/livestock_findings.md`) found this shape by hand for living
horses and swine. `scripts/orphan_origin_match.py` generalises it.

## The instrument

```
python3 scripts/orphan_origin_match.py [payload.json] [out.csv]
  -> reports/orphan_origin_matches.csv
```

For every payload commodity it takes the T1 series (modal unit) and the origin
sum by year **as consumers see it** — paren drill-downs and `§TOTAL` excluded,
the same rule `reconcile_baseline.py` uses. A commodity-year is a **gap** when a
national total is printed and no origin cell exists. Every other label's origin
sums are then joined onto those gaps *on the value itself*; a hit is `exact`
when equal to the digit and `near` within 0.1%.

Two columns decide whether a candidate is safe to act on:

- `source_has_own_t1` — a source with its own anchor is a **rival series**, not
  an orphan. Those are the duplicate-label question, not this one.
- `overlap_years` — years both labels already carry. A fold merges cells by
  (country, unit, year) with the target winning, so a *country* the source has
  and the target lacks is **added**, not suppressed. Non-empty overlap means a
  fold can double-count, and the pair must be scoped or skipped.

First run, against a 2,009-commodity payload: **5,991 gap commodity-years across
770 commodities**, 222 candidate pairs, **95 of them clean** (no overlap, source
unanchored). This is a queue, not a result — each pair still has to be read.

## Round 35 — `Steel — Unwrought`

`Steel — Unwrought` printed a national line for **all 35 years 1866-1900** and
carried **no origin data whatsoever**. Steel is printed immediately after iron,
and the tables had gone to a stale `IRON` head.

| | 1872 | 1873 | 1875 | 1876 | 1878 | 1880 | 1881 | 1882 | 1884 | 1886 | 1887 | 1889 | 1890 | 1892 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| orphan sum | 7,545 | 9,525 | 7,509 | 9,230 | 4,583 | 5,895 | 6,665 | 5,935 | 6,723 | 12,082 | 14,727 | 10,868 | 8,144 | 6,483 |
| printed T1 | 7,545 | 9,525 | 7,509 | 9,230 | 4,583 | 5,895 | 6,665 | 5,935 | 6,723 | 12,082 | 14,727 | 10,868 | 8,144 | 6,483 |

**Fourteen years exact to the digit**, with 1877 −3, 1883 −3, 1891 −6, 1888 +20,
1885 −30, 1897 −37 as single-cell noise. The source has no T1 of its own, so no
anchor contest; the target had no origin year at all, so no overlap; units are
`Ton` on both sides.

A second orphan supplies the **one year the first one misses**:
`Iron (Con.) — Steel, Unwrought` holds 1879 alone, **5,183**, which is the
printed T1 for 1879 exactly. (`Iron (Con.)` is the continuation head at the top
of a carried-over page.) The complementarity is the same signature round 34 had.

Two `fold` rows in `reference/commodity_curation.csv`. The full before/after
diff of every commodity-year ratio in the payload changed **28 cells, every one
of them inside `Steel — Unwrought` and every one from "no origin data" to a
ratio**. Nineteen land within 0.1%, eight within 5%.

```
exact01  2,265 -> 2,284      nodata  6,010 -> 5,982
within 0.1%  22.8% -> 23.0% of commodity-years   (GBP-weighted flat at 39.5%)
within 5%    30.8% -> 31.1%
```

### What the fold exposes, recorded rather than hidden

- **1874 reads 1.5175** — the orphan sums to 11,129 against a printed 7,334. One
  year of that block is glued or double-counted. It was invisible while the
  table had no anchor; now it is an `over` the detectors can see.
- **1893-99 run −118 to +100, and 1898 −517 / 1899 −409.** Within 5%, not to the
  digit. The late years are where the fourth orphan below also lives.

### Deliberately NOT folded

Two more labels carry the same printed line and both would double-count:

- **`Iron — Steel, Unw Ought`** (OCR garble of "Unwrought"), 1883 only, **4,517
  — the printed T1 exactly**, where the folded orphan reads 4,514. It is the
  *better* reading of a year the target already has, so taking it needs a
  cell-level replace, not a fold. 1883 already closes to within 0.1%, so this
  buys 3 tons.
- **`Horns, Tips And Pieces Of Horns And Hoofs — Steel, Unwrought`** (GBP1.08M,
  9 countries) — a stale-head duplicate covering 1893-98, years the folded
  orphan already has. Its readings are better in 1894/1895 (−14, −34 against
  +86, +100), much worse in 1896 (−881 against +62) and identical in 1898. It is
  a **duplicate reading of a table now counted**, so the right action is
  probably `drop`; that is a curation call, queued not taken.

## The queue — top clean candidates after round 35

94 clean pairs remain. Ranked by exact matches:

| exact | near | source | target | source GBP | target gap years |
|---|---|---|---|---|---|
| 12 | 0 | `Dye Stuffs, And Substances Used In Tanning — Valonia` | `Valonia` | 5,344,751 | 33 |
| 10 | 3 | `Caoutchouc — Manufactures Of` | `Manufactures Of` | 10,361,298 | 35 |
| 10 | 1 | `Zinc — Manufactures, Unenumerated` | `Metals — Manufactures` | 9,076,353 | 16 |
| 10 | 0 | `Cotton Manufactures — Piece Goods Of India And China` | `Manufactures Of India And China` | 429,700 | 16 |
| 8 | 2 | `Sago And Sago Flour` | `Sago` | 3,032,962 | 31 |
| 8 | 0 | `Rosin — Safflower` | `Safflower` | 283,075 | 29 |
| 6 | 0 | `Metal — Wrought Or Manufactured` | `Iron And Steel, Wrought Or Manufactured` | 12,834,643 | 14 |
| 6 | 0 | `Lard — Imitation Lard (…)` | `Imitation Lard` | 1,042,450 | 8 |
| 5 | 0 | `Dye Stuffs, And Substances Used In Tanning — Sumach` | `Sumach` | 3,712,197 | 11 |
| 4 | 2 | `Quicksilver (Metallic)` | `Quicksilver` | 3,268,235 | 15 |
| 4 | 2 | `Beef — Books, Bound Or Unbound (…)` | `Books` | 1,572,844 | 16 |

Read the CSV before acting on any of them. Three cautions the steel case
already demonstrated:

1. **A high exact count does not license a blind fold.** Check every year of the
   source, not just the matching ones — 1874 was a 52% overshoot sitting inside
   an otherwise digit-perfect series.
2. **Look for the complement.** The clean pair is often not the whole story; a
   second and third orphan may hold the missing years, and only some of them can
   be folded without double counting.
3. **The `Dye Stuffs, And Substances Used In Tanning —` prefix appears against
   four different targets** (Valonia, Safflower, Sumach, Shumach). That is one
   group head that swallowed a whole section, so the sensible unit of work is
   the section, not one pair.

---

# Round 36 — `Valonia`, scattered across six labels that tile the years

`Valonia` — acorn cups, a tanning material — published a national line for **all
35 years 1866-1900** and carried origin data for **two** of them. The tables were
never lost. They were sitting under **eight** labels the parser minted from stale
section heads, and **six of them tile the years without a single overlap**:

| years | label the parser gave it | Ton sum vs printed T1 |
|---|---|---|
| 1872, 1873, 1881 | `Toys — Valonia` | 32,481 / 28,977 / 26,795 — all **exact** |
| 1874, 1876, 1877, 1879 | `Turpentine (Rough) — Valonia` | 26,336 / 29,989 / 34,217 **exact**; 1876 below |
| 1880 | `Tin — Valonia` | 33,773 — **exact** |
| 1882 | `Drugs — Valonia` | 35,604 — **exact** |
| 1883-1894 | `Dye Stuffs, And Substances Used In Tanning — Valonia` | **twelve consecutive years, every one exact** |
| 1895-1898 | `Bark — Valonia` | 1895 and 1897 **exact**; 1896 −22, 1898 −30 |

1875 and 1878 — the two years the target already had — appear under none of
them. Six labels, twenty-five years, no collision: the parser was simply
holding whatever head it last saw when each year's table came round.

**1876 is the detail worth keeping.** `Turpentine (Rough) — Valonia`'s Ton cells
sum to 34,886 against a printed 34,923, thirty-seven short — and the same label
holds one cell that lost its unit, of exactly **37**. The fold's magnitude guard
rescued it and the year closes to the digit.

## Result

Six `fold` rows in `reference/commodity_curation.csv`. The full before/after diff
of every commodity-year ratio in the payload changed **25 cells, every one inside
`Valonia` and every one from "no origin data" to a ratio** — and **twenty-three
of them land at exactly 1.0000**:

```
exact01  2,284 -> 2,308      nodata  5,982 -> 5,957
within 0.1%  23.0% -> 23.2% of commodity-years   (GBP-weighted flat at 39.5%)
within 5%    31.1% -> 31.3%
```

`Valonia` goes from 2 origin-years to **27**, and from 5 countries to 12.

## Deliberately not folded

Two labels also carry Valonia Ton cells and both would double-count:

- **`Copper, Ore Of — Valonia`** — Ton 1894-98, overlapping the Dye Stuffs and
  Bark folds. It reads **1898 exactly** where the folded `Bark` is 30 short, and
  1897 exactly too; but 1896 is 5,018 out. A per-year improvement worth 30 tons,
  needing a cell replace rather than a fold.
- **`Dye Stuffs (Other Than Dye Woods), And Substances Used In Tanning Or Dyeing
  — Valonia`** — its Ton cells give 1899 as **24,306 against a printed 24,336**,
  and 1899 is a year *no clean source covers*. But the same label holds **34
  countries of Cwt cells** that are a different article entirely (275,597 against
  a 35,605-ton line), and the `years` scope cannot filter by unit — folding even
  one year of it would import that block into Valonia's map. Left alone.

## Still open on this line

`Valonia` gaps remaining: **1866-1871, 1899, 1900** — eight of thirty-five. 1899
is reachable if the Cwt block above is split off first; the six early years and
1900 have no candidate on any label.

## The section, not the pair

The dye-stuffs section is one head that swallowed many articles, and Valonia was
only its most tractable line. The same shape is waiting on:

| target | T1 years | origin years | gaps | orphans seen |
|---|---|---|---|---|
| `Safflower` | 33 | 4 | 29 | `Dye Stuffs…— Safflower`, `Rosin — Safflower`, `Copper, Ore Of — Safflower`, `Rags…— Safflower`, `Drugs — Safflower` |
| `Shumach` | 27 | 2 | 25 | `Dye Stuffs…— Shumach` (21y, Ton), `Bark — Sumach`, `Copper, Ore Of — Sumach`, `Cotton — Shumach` |
| `Indigo` | 35 | 11 | 24 | `Dye Stuffs…— Indigo` (12y, GBP34.4M) |
| `Cutch And Gambier` | 35 | 18 | 17 | `Cutch`, `Gambier`, `Bark — Catch And Gambier`, `Cotton Manufactures — Cutch` |

**A caution before touching sumach.** Its anchor is itself split across four era
spellings — `Shumach` (27 T1 years), `Sumach` (12), `Shumash` (5) and
`Dyeing Or Tanning Stuffs — Shunach` (5). Folding orphans into one of them is
safe; folding the *anchor carriers* into each other is the deferred
"which label carries Tier 1" decision and must not be done alone. The same
warning applies to the madder cluster, which has six anchor-bearing spellings.
