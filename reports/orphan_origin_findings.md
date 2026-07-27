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

---

# Round 37 — `Safflower`, and a lesson about what "no origin data" means

`Safflower` (a dye plant) published a Tier-1 line for **33 years 1866-1899** and
read as having **no origin data at all**. Five stale-head labels hold its tables:

| years taken | label | |
|---|---|---|
| 1872, 1873, 1875-1879, 1881 | `Rosin — Safflower` | **eight, all exact** |
| 1880 | `Rags And Other Materials For Making Paper — Safflower` | **exact** |
| 1882 | `Drugs — Safflower` | 1,278 v 1,298 |
| 1883, 1884, 1887-1892 | `Dye Stuffs, And Substances Used In Tanning — Safflower` | **eight, all exact** |
| 1885 | (same label) | 639 v 715 — only source, reads short |
| 1895, 1897, 1899 | `Dye Stuffs (Other Than Dye Woods)… — Safflower` | **three, all exact** |
| 1896 | `Copper, Ore Of — Safflower` | 535 v 536 |

**Twenty years exact to the digit.** Six folds, four of them `years`-scoped.

## Three years scoped out because they read exactly double

`Dye Stuffs… — Safflower` gives 1893 as **64 against a printed 32** and 1894 as
**802 against 401**; `Dye Stuffs (Other Than Dye Woods)… — Safflower` gives 1896
as **1,072 against 536**. Exactly 2.000 in all three. Those labels have each
country twice for those years, and half of a doubled cell is not something a fold
can take — so 1893 and 1894 stay gaps, and 1896 was taken from `Copper, Ore Of —
Safflower` instead, which reads it 535 against 536.

`Rosin — Safflower` 1874 was scoped out for the opposite reason: its Cwt cells
give **166** against a printed 13,791 and it also holds one unattached cell of
18,625. Neither is the year.

## The lesson: "no origin data" can mean "no data in the anchor's unit"

`Safflower` did not have zero origin cells. It had **eleven cells that had lost
their printed unit** — 1872, 1873, 1874 and 1876 — and every consumer that keys
on the anchor's unit was blind to them, including `reconcile_baseline`, this
report's own matcher, and the map.

Folding changed that for 1874. With 1874 scoped out of the `Rosin` fold, the
target had no Cwt cell for the year, so the payload's unit-healing pass was free
to relabel the four unitless cells — and 1874 went from `nodata` to **0.4066**:

```
Belgium 941 + France 2,505 + Holland 1,393 + Other Countries 769 = 5,608
printed total                                                    13,791
                                                                 -------
missing                                                           8,183
```

1873's table, which closes exactly, is **British India 9,495 + Egypt 335 + Other
Countries 246**. 1874's surfaced cells contain no British India at all. **The
missing 8,183 cwt is a lost British India row** — a specific, checkable claim
rather than a shrug. (1872, 1873 and 1876 kept their unitless cells because the
folds supplied Cwt cells for the same countries, so healing had nowhere to put
them; those years close exactly on the folded data and the '?' copies are
excluded, as they should be.)

So this round's diff has **two years going from "no data" to "visibly
incomplete"** — 1874 at 0.41 and 1885 at 0.93. That is the reconciliation working:
an unmeasured year is worse than a measured bad one.

## Result

```
exact01  2,308 -> 2,328      nodata  5,957 -> 5,933
under      244 ->   246      within5    803 ->   805
within 0.1%  23.2% -> 23.4% of commodity-years   (GBP-weighted flat at 39.5%)
within 5%    31.3% -> 31.5%
```

Full corpus ratio diff: **24 cells changed, every one inside `Safflower`, every
one from "no origin data"**. `Safflower` goes from 0 origin-years to 24 and from
5 countries to 15.

Gaps left: **1866-1871** (no candidate on any label), **1886** (none), **1893 and
1894** (only the doubled label). And the queued repair above: **1874's missing
British India row, 8,183 cwt.**

---

# Round 38 — `Indigo` did not close, and finding out why was worth more

## The item that failed

`Indigo` has a Tier-1 line for 35 years and origin data for eleven (1872-82).
Its orphan, `Dye Stuffs, And Substances Used In Tanning — Indigo` (GBP34.4M),
matches the printed total in 1883 (−30) and **1884 exactly** — and then reads
**1.87 to 1.94 times** the printed total in every year 1885-1894. Its late twin,
`Dye Stuffs (Other Than Dye Woods)… — Indigo`, does the same for 1895-99.

A ratio pinned near 1.9 for fifteen straight years is not noise. Comparing the
two years either side of the break says what it is:

```
1884 (closes exactly)   Bengal And Burmah 66,654 + Bombay 1,181 + Madras 25,096
                        + eight others  = 104,423 = printed total.  No parent row.

1885 (reads 1.87)       Bengal 64,629 + Madras 17,648 + Bombay 134 + Ceylon 1,561
                        AND ALSO  'British East Indies'  83,979  <- their total
                        sum 176,591 against a printed 94,314
```

`British East Indies` is the **printed aggregate of the presidencies**, and where
the parser loses the sub-entry colon its members arrive as plain countries, so
India is counted twice. Drop the parent and 1885 is
`92,612 + 1,702 (unitless) = 94,314` — **the printed total to the digit**.

## The class, measured

That shape is not Indigo's alone. Counting commodity-years where an aggregate
shares a year with one of its own members **and a printed total exists**:

| aggregate | checkable years | dropping it moves closer | further | within 0.1% before → after |
|---|---|---|---|---|
| `British East Indies` | 302 | **290** | 12 | 5 → 115 |
| `Australasia` | 378 | **335** | 43 | 13 → 122 |
| `British Possessions In South Africa` | 159 | **137** | 22 | 5 → 22 |

## The fix

A new pass in `build_viz_payload`, modelled on the coast-sibling fold directly
above it and carrying the same guard: **drop the aggregate's cell only where
doing so brings that year closer to its own printed national total.** A parent
that is really an unenumerated residual beside named members overshoots when
removed, so the guard leaves it; a year with no printed total is never touched.
The "further" columns above therefore never fire — they describe the population,
not the rule.

**Ordering matters and cost a measurement to find.** Placed before
`heal_units`, the pass deleted parent cells and thereby *freed* the (country,
year) slot, letting a unitless cell for the same country heal into it — the
Safflower-1874 mechanism from round 37, running backwards. Moved to **after**
`heal_units`, that interaction is gone and the result is strictly better.

```
                       before      after
exact01                 2,328      2,547        (+219)
over                      623        327        (-296)
within 0.1%   23.4% / 39.5% GBP   25.6% / 45.4% GBP
within 5%     31.5% / 55.9% GBP   34.5% / 63.7% GBP
```

710 aggregate cells dropped. Full corpus ratio diff: **530 commodity-years
changed, 521 closer to their anchor, 9 further.**

### The nine, named

`Honey` 1894 (1.0048 → 0.9590), `Oats` 1893/1897/1898, `Tallow And Stearine`
1897, `Teeth, Elephants'…` 1895 (0.9361 → 0.8501), `Tow` 1896/1897, and
`Wool — Sheep Or Lambs'` 1896 (1.7818 → 1.9931). Eight of them were already
*under* their anchor and lost a little more; the guard saw a different sum at
its own point in the pipeline than the passes that run later (`fold_tun_ton`,
`drop_shifted_duplicates` and the curation folds all follow it). Wool 1896 is
the odd one — its sum went *up*, which this pass cannot do directly, so it is a
knock-on in the dedup pass. All nine are recorded rather than tuned away.

## Why `Indigo` still did not close

The pass is anchor-guarded, so it can only fire on a commodity that has its own
printed total — and an orphan, by definition, has none. `Dye Stuffs… — Indigo`
still reads 1.9× and still cannot be folded.

**The repair is knowable and is queued with its ordering requirement**: fold the
orphan into `Indigo` *first*, so its cells sit under a label that has an anchor,
then let the aggregate pass clean them. Today the curation folds run **after**
this pass, so the folded cells arrive too late to be cleaned. Either the pass
moves after curation, or the fold and the clean-up happen in one place. That is
a restructuring, not a one-line move, and it is not made here.

Same blockage, same fix, for every dye-stuffs orphan whose ratio sits near 1.9.

---

# Round 39 — the pass runs twice, and `Indigo` closes

Round 38 ended with a blockage stated precisely: the aggregate-beside-members
pass is **anchor-guarded**, an orphan has no anchor, so the pass could never
reach the doubled India sitting inside the dye-stuffs orphans. The repair had to
be **fold first, clean after** — and the curation folds run *after* the pass.

## The fix

The pass is now a function, `drop_aggregate_beside_members(store)`, called twice:
once where it was, and **again after the curation folds**, on `payload` instead
of `comms`. It sits beside `fold_tun_ton(payload)`, which is re-run there for the
same reason, and under the same licence the comment there already states: only a
pass whose test is *the year's own arithmetic against its printed total* is safe
to re-run after a fold. This one qualifies — it moves a cell only when doing so
brings the year closer to that total, so a fold that duplicates (and therefore
overshoots) is left alone.

The refactor on its own was verified behaviour-preserving: 710 drops before, 710
after. The second call then fires **166 more times**, on cells that earlier folds
had already brought in:

```
                  after round 38    second call
exact01                  2,547         2,598
over                       327           260
within 0.1%      25.6% / 45.4%   26.1% / 47.4% GBP
within 5%        34.5% / 63.7%   35.2% / 65.4% GBP
```

Full corpus ratio diff for the second call alone: **125 commodity-years changed,
125 closer, 0 further.**

## `Indigo`

With the ordering fixed, the two orphans fold. Their years (1883-94 and 1895-99)
are disjoint from the target's own (1872-82), and the doubling is cleaned by the
pass on the way through:

| | before | after |
|---|---|---|
| 1885 | 176,591 against a printed 94,314 (**1.87×**) | **94,314 — exact** |
| origin years | 11 | **28** |
| of which exact to the digit | 11 | **22** |

The six that are not exact are 1883 (−30), 1886 (−295), 1887 (+500), 1890 (+97),
1893 (−33), 1895 (+132), 1896 (+126) and 1899 (−30) — every one inside 0.65%.

Fold diff: 17 commodity-years changed, **17 closer, 0 further**.

```
exact01  2,598 -> 2,610      nodata  5,933 -> 5,916
within 0.1%   26.3% of commodity-years / 47.5% GBP
within 5%     35.3% of commodity-years / 65.5% GBP
```

## What this unblocks

Every orphan whose ratio sits near 1.9× is now foldable — the arithmetic that
proves it belongs is the same arithmetic that cleans it. `Cutch And Gambier`
(35 T1 years, 18 with origins) and the rest of the dye-stuffs section are the
immediate candidates, and the 88 clean pairs still in
`reports/orphan_origin_matches.csv` should be re-read with this in mind: a pair
that looked unusable because the source read ~2× may now be a clean fold.

The nine regressions named in round 38 are unchanged by this round.

---

# Round 40 — the matcher learns to see through the doubled aggregate, and `Sago`

Round 39 ended with a note: an orphan reading ~1.9× is now foldable, so the
queue should be re-read. But the matcher itself could not see those pairs — its
join is on the value, and a doubled value matches nothing.

## Instrument change

`orphan_origin_match.py` now offers every source **twice**: as parsed, and with
the regional aggregate's cell removed wherever its members are present in the
same year — the same `AGGREGATES` table the payload pass uses. Matches found
that way are tagged `exact*` / `near*` and counted in a new
`n_via_aggregate_drop` column, so a reader can always tell which proof is which.

Clean candidate pairs went **88 → 107**.

## `Sago`

`Sago` printed a Tier-1 line for 31 years 1866-1896 and carried **no origin data
at all**. Three stale-head labels hold the tables, and their years are disjoint:

| years | label | |
|---|---|---|
| 1872 | `Rags And Other Materials For Making Paper — Sago And Sago Flour` | 298,418 **exact** |
| 1873, 1877-79, 1881-84, and 1874/76/90 | `Sago And Sago Flour` | seven exact as parsed |
| 1875, 1880, 1885-89, 1891-92, 1894 | `Rosin — Sago And Sago Flour` | three exact as parsed, seven via the aggregate drop |

Two details are worth keeping. **1883**: the label's Cwt cells give 332,021 and
it also holds an unattached cell of **1,314** — together 333,335, the printed
total exactly, the same unitless-cell rescue as Valonia 1876 and Safflower 1874.
**1885**: `Rosin — Sago And Sago Flour` reads **728,614 against a printed
364,307**, and closes to the digit once `British East Indies` is dropped from
beside its own presidencies.

Three folds. Full corpus ratio diff: **22 commodity-years changed, all inside
`Sago`, all from "no origin data", 22 closer and 0 further — and twenty of them
land at exactly 1.0000** (1876 is 1.0003, 1892 is 0.9999).

```
exact01  2,610 -> 2,632      nodata  5,916 -> 5,894
within 0.1%   26.5% of commodity-years / 47.5% GBP
within 5%     35.6% of commodity-years / 65.5% GBP
```

`Sago` goes from 0 origin-years to **22** and from 1 country to **21**.

## Left alone

- **`Sago, And Flour Or Meal Thereof`** carries its own T1 for 1893-99, exactly
  where `Sago`'s ends (1896). That is a **wording change mid-series** — the
  deferred "which label carries Tier 1" decision — not a fold to make alone.
- `Sago And Sago Flour — From British East Indies` holds only unitless cells and
  its 1888 (423,311 against 426,346) would overlap the `Rosin` fold.
- Gaps left: 1866-71, 1893, 1895, 1896.

---

# Round 41 — the de-headed anchor: three labels reunited with their own countries

A shape the queue kept surfacing and the earlier rounds had not named. An
abstract row loses its group head, so the payload mints a commodity from the
article alone — `Manufactures Of`, `Metals — Manufactures`,
`Manufactures Of India And China`. Each has **a full run of printed national
years and not one country cell**. The country data is under a label that kept
its head and has no anchor. They are two halves of one line.

The fold therefore runs **in the opposite direction to rounds 34-40**: the
anchor-only label is the *source*, so the surviving name is the one that says
what the commodity is.

| anchor-only label | T1 years | reunited with | exact |
|---|---|---|---|
| `Manufactures Of` (Lb) | 35, 1866-1900 | `Caoutchouc — Manufactures Of` (43 countries) | **8 in a row, 1874-81**, plus 6 more |
| `Metals — Manufactures` (Cwt) | 16, 1878-93 | `Zinc — Manufactures, Unenumerated` | **9 of 12** |
| `Manufactures Of India And China` (Pieces) | 16, 1866-81 | `Cotton Manufactures — Piece Goods Of India And China` | **9 of 10** |

The zinc naming was settled on the printed heads rather than on preference:
`country_year_final` carries `article_group` **ZINC** with `Manufactures,
Unenumerated` and three spelling variants across 1872-1899, 144 rows. The
`Metals` form appears only on the de-headed abstract label.

Full corpus ratio diff: **49 commodity-years changed, all three inside the
targets, and nothing else in the corpus moved.**

```
exact01  2,632 -> 2,670      nodata  5,894 -> 5,845
within 0.1%   26.9% of commodity-years / 47.5% GBP
within 5%     36.0% of commodity-years / 65.6% GBP
```

## The break the caoutchouc fold exposes

1872-91 closes — eight consecutive years to the digit and six more inside 0.06%.
Then the **anchor** jumps and the origin side does not:

```
1891   T1 3,180,198   origins 3,180,195
1892   T1 9,055,694   origins 3,420,706     0.38
...
1898   T1 12,497,946  origins 5,569,993     0.45
1899   T1  5,065,320  origins 5,005,520     0.99
1900   T1 13,550,183  origins       —
```

1892-98 now read 0.34-0.45 and 1899 closes again. That is not the origin table
failing: it is the **printed national line changing scope for seven years**, and
it was invisible while the two halves were apart. Seven commodity-years moved
from `nodata` to `under`, which is the reconciliation doing its job — a
measured bad year beats an unmeasured one.

## Queued, not folded

`Zinc — Manufactures` (GBP1.7M, 6 countries) and `Metals — Manufactures,
Unenumerated` (anchor-only, GBP35k) are further fragments of the zinc line and
need their own year checks before either is moved.

---

# Round 42 — the de-headed anchors, measured — and a bound on what is left

Round 41 named the shape. This round asks how much of the corpus it accounts
for, with `scripts/deheaded_anchor_match.py`.

## The class

**381 labels carry printed national totals and not one country cell, between
them 3,263 commodity-years — 56% of every remaining "no origin data" year.**
They are not a long tail. They are the largest single block left.

The relationship is structural, so the tool looks for it structurally: a
candidate is any commodity whose name ends with `— <the shadow's name>`, which
is de-heading run backwards. It does not require the numbers to agree, because a
reunion is worth making even where the origin table is incomplete.

## The negative result, which is the useful part

**Only 39 of the 381 shadows have a structural counterpart at all**, and most of
those are useless: the commonest de-headed articles are `Unenumerated`,
`Of Other Sorts` and `Raw`, and each matches five to a dozen commodities:

```
Of Other Sorts (35y)  ->  Beer And Ale — / Bark — / Zinc — / Metal — / Oil — Of Other Sorts
Unenumerated   (35y)  ->  Woollen Yarn — / Beads — / Bark — / Paper — / Slates — ...
```

That is not an accident of the tool. **Those articles lost their identity
precisely because the article alone never carried one** — which means the bulk
of these 3,263 commodity-years cannot be recovered by name, and the numeric
matcher (`orphan_origin_match.py`) is the only instrument that can reach them.
Round 41's three all came from there, not from here.

So this bounds the remaining `nodata`: over half of it is de-headed anchors, and
most of those need a value-based proof, one commodity at a time.

## The other half of the class, and a warning about the headline number

57 of the rows are **duplicates** rather than reunions — the counterpart has its
own anchor, so the same printed line reached the payload twice and the shadow is
a phantom publishing a national total it cannot substantiate. `Oil — Animal` and
its shadow `Animal` (33 years) are the clearest.

**Folding those away would remove ~520 commodity-years from
`reconcile_baseline`'s denominator.** Every percentage would rise without one
number improving. That is a real cleanup and it should happen — but it changes
the measurement universe, so it is **queued for a decision, not taken here**, and
whoever takes it must report the before/after denominator alongside the rates.
The tool prints that figure so it cannot pass silently.

## What was folded: `Mahogany`

The one candidate the structural test resolves with more than a single year's
evidence. `Mahogany` holds printed totals for 17 years (1866-70, 1885-96) and no
countries; `Wood And Timber — Mahogany` holds **44 countries and GBP21.2M** and
no anchor. Three years match to the digit — 1889 **39,859**, 1890 **39,842**,
1891 **48,021** — and 1895 is 34,732 against 34,818.

Folded, and **not clean, which is the honest result**: 1893 and 1894 read 1.09
and 1.11, 1896 reads 0.87, and 1866-70, 1886-88 and 1892 have no origin table on
either half. Eight commodity-years changed, all inside
`Wood And Timber — Mahogany`, and nothing else moved.

```
exact01  2,670 -> 2,673      nodata  5,845 -> 5,837
denominator unchanged at 9,935 commodity-years
```

The gain that does not show in the counts: **a GBP21.2M commodity has a printed
anchor for the first time**, so its years can be checked at all.

`Logwood` was left alone — its counterpart `Bark — Logwood` agrees in exactly
one year (1899, 33,429), and one agreement is the coincidence the matcher's
two-year minimum exists to refuse.

---

# Round 43 — `Metal — Wrought Or Manufactured`, and a year split three ways

The largest unworked pair in the queue, and another de-headed anchor.
`Iron And Steel, Wrought Or Manufactured` carries printed Cwt totals for
1866-79 and **not one country cell**; `Metal — Wrought Or Manufactured` carries
15 countries and **GBP12.8M** with no anchor.

**Five years match to the digit**: 1872 **781,966**, 1873 **614,358**,
1875 **1,159,762**, 1876 **1,390,225**, 1878 **2,109,885**.

The name goes to the METAL side on the printed heads, not on preference —
`country_year_final` carries `article_group` **METAL** with `Wrought or
Manufactured` in Cwts 1872-78, Tons 1882-95 and `Tons. Cwts` 1884-94, while
`Iron And Steel` appears only on the abstract label.

Seven commodity-years changed, all inside that commodity, nothing else moved.

```
exact01  2,673 -> 2,678      nodata  5,837 -> 5,830
within 0.1%   27.0% of commodity-years / 47.5% GBP
within 5%     36.1% of commodity-years / 65.5% GBP
```

## 1874 is split across three unit keys, and the three sum exactly

```
Cwt       119,515
unitless  872,745
Ton        61,759
          --------
        1,054,019   = the printed total for 1874, to the digit
```

The year reads **0.1134** because only the Cwt eighth is counted. This is not a
data defect at all — every figure is present and correct — it is one printed
table whose rows landed under three different unit labels. `heal_units` cannot
fix it: its per-country magnitude test compares a country's minority unit
against the same country's majority, and here the *whole year* is split, so no
country has a majority to fold toward. Same blind spot the Tun/Ton fold was
written for, in a different shape.

**A queued repair with the arithmetic already done**, not a guess.

## Also recorded

- **1877 reads 1,783,921 against a printed 1,683,921** — a leading-digit misread
  of exactly 100,000 in one country cell. Only one volume prints the year, so
  which cell is not decidable here; it is a `digit_repair_candidates` entry.
- The source's **Ton cells for 1882-95 have no anchor at all**: the printed line
  re-denominates from Cwt to Ton around 1882 while the abstract's total series
  stops at 1879. That is the [[mid-series-unit-change]] class, and it means this
  commodity's later two-thirds still cannot be checked against anything.
- `Metal — Unenumerated, Wrought Or Manufactured` is a **different line** and was
  left alone: its Ton values for the same years run 364-687 against totals in the
  hundreds of thousands.

---

# Round 44 — one table, several unit labels

Round 43 found `Metal — Wrought Or Manufactured` 1874 reading 0.11 with nothing
missing: its cells were 119,515 under `Cwt`, 872,745 with no unit and 61,759
under `Ton`, and the three summed to the printed 1,054,019 exactly. This round
asks how often that happens.

## The measurement

Of **4,337 commodity-years that have both origin cells and a printed total**,
the anchor-unit sum misses while the **raw sum across every unit key hits**:

- **14 exactly to the digit**
- 5 more within 0.1% — **deliberately left alone**

Small, but the test is a proof rather than a heuristic. Genuinely mixed measures
cannot land on the printed total by chance: a Ton figure is a twentieth of its
Cwt equivalent, so adding them and hitting the total to the digit does not
happen. Equality *is* the evidence that all the numbers were in one measure and
only the labels differed.

`heal_units` is blind to it by construction — its magnitude test compares a
country's minority unit against **that country's own** majority, and here the
whole year is split, so no country has a majority to fold toward.

## The pass

`heal_split_year_units` in `build_viz_payload`, run in both places the
aggregate pass runs. It relabels a year's non-anchor-unit cells to the anchor
unit **only when the cross-unit sum equals the printed total exactly**, only
when more than one unit is present, and only when the anchor-unit sum is short.
A country that already holds an anchor-unit cell for that year would be two
printed rows rather than one mislabelled one, so the whole year is abandoned
rather than merged.

**Exact only, never "close".** This pass rewrites units, which is the most
expensive thing to get wrong; the five near misses are noise plus a coincidence
and are not worth the risk.

## Result

137 cells relabelled. Full corpus ratio diff: **19 commodity-years changed, 19
closer, 0 further.**

| | before | after |
|---|---|---|
| `Jute` 1883 | **0.0000** (116 against a printed 7,385,028) | **1.0000** |
| `Metal — Wrought Or Manufactured` 1874 | 0.1134 | **1.0000** |
| `Watches` 1876, 1878, 1882 | 0.0000 | **1.0000** |
| `Drugs, Unenumerated` 1872, 1873, 1875, 1877 | 0.0000 | **1.0000** |
| `Straw` 1888 | 0.7509 | **1.0000** |
| `Dye Woods — Unenumerated` 1872-74 | 0.92-0.95 | **1.0000** |

```
exact01  2,678 -> 2,694      nodata  5,830 -> 5,820
within 0.1%   27.1% of commodity-years / 47.8% GBP
within 5%     36.2% of commodity-years / 65.5% GBP
```

`Jute` 1883 is the one to notice: a **7,385,028 cwt** year that read as
essentially empty, restored to the digit, on a commodity this project has
already spent two sessions on.

## Recorded: the pass exposes duplicates for the dedup to take

Four `Drugs, Unenumerated` years land near but not on 1.0 — 1876 at 0.86, 1878
at 0.98, 1884 at 1.01 — although they qualified on exact equality. Relabelling
the units makes two copies of one row visibly the same row, and
`drop_shifted_duplicates`, which runs later, then removes one. The year no
longer sums to its total because it was summing a duplicate before. Every one of
them still moved closer, so the interaction is left as it is and noted rather
than tuned.
