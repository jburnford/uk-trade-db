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

---

# Round 45 — a combined line whose halves were parsed apart

`Cutch And Gambier` is not a de-headed anchor and not an orphan. It is a
**combined printed line** — "cutch and gambier" — and its origin table is
**two tables**: gambier ships from the Straits Settlements, cutch from British
India. The parser gave each its own commodity, so the anchored label had no
origins at all before 1882 while both halves sat unanchored.

Summed, they are the printed total:

```
1873  22,514 + 6,998 = 29,512      1877  25,354 + 6,664 = 32,018
1875  23,074 + 5,771 = 28,845      1879  21,357 + 4,277 = 25,634
1876  21,759 + 4,805 = 26,564      1880  26,413 + 5,694 = 32,107
```

**Six years to the digit.** Neither half alone comes close — gambier is 70-85%
of the line and cutch the rest — so this is a third distinct shape, after the
stale head (rounds 34-40) and the de-headed anchor (rounds 41-43).

## The mechanism gap, measured rather than glossed

A `fold` merges cells by (country, unit, year) **with the target winning**, which
is right for a duplicate and wrong for a constituent. Both halves carry an
`Other Countries` row (and `Straits Settlements` in 1873), so the second fold's
copy is dropped rather than added, and the reunited years land **7 to 539 tons
short** instead of exact. Gambier is folded first because its `Other Countries`
is the larger reading in five of the six years.

**The curation vocabulary has no way to say "these constituents ADD."** That is
a real limitation and this is the first case that needed it. Recorded as a tool
gap, not worked around.

## Result

Ten commodity-years changed, all inside `Cutch And Gambier`, **10 closer, 0
further** — every one from "no origin data" to a ratio:

```
1872 0.9846   1873 0.9913   1874 1.0106   1875 0.9998   1876 0.9958
1877 0.9993   1878 0.9973   1879 0.9980   1880 0.9832   1881 0.8421
```

Two land inside 0.1% and seven inside 5%, against six that would have been exact
had the constituent cells been added rather than merged. That is the cost of the
gap, stated in full.

```
exact01  2,694 -> 2,696      nodata  5,820 -> 5,810
within 0.1%   27.1% of commodity-years / 47.8% GBP
within 5%     36.3% of commodity-years / 65.6% GBP
```

`Bark — Catch And Gambier` was left alone: its one year, 1892 at **25,200**, is
exactly the printed total, but 1892 is a year the target already carries, so
folding it could only collide.

---

# Round 46 — `combine`: a curation action for constituents

Round 45 proved `Cutch And Gambier` is one printed line whose origin table is
two, and then could not apply the proof: a `fold` merges cells by (country,
unit, year) **with the target winning**, so the second half's `Other Countries`
row was dropped rather than added and six digit-exact years landed 7 to 539 tons
short.

## The action

A third curation verb beside `drop` / `fold` / `rename`:

```
combine,<target>   the source is a CONSTITUENT of the target, not a copy.
                   Where both sides hold the same (country, unit, year), ADD.
```

It is **anchor-guarded like every other pass in this file**: a colliding cell is
added only where the target prints a total for that (unit, year) **and adding
brings the year closer to it**. With no printed total to check against,
`combine` behaves exactly as `fold`. So it can only turn a duplicate into a
double count if a human writes the action *and* the arithmetic agrees — the same
two-key discipline the group repairs use.

## Result

Eleven constituent cells added. The six years round 45 proved now land where the
proof said they would:

| year | as `fold` | as `combine` |
|---|---|---|
| 1872 | 0.9846 | **0.9989** |
| 1873 | 0.9913 | **1.0000** |
| 1875 | 0.9998 | **1.0000** |
| 1876 | 0.9958 | **1.0000** |
| 1877 | 0.9993 | **1.0000** |
| 1879 | 0.9980 | **1.0000** |
| 1880 | 0.9832 | **1.0000** |
| 1881 | 0.8421 | 0.8534 |

```
exact01  2,696 -> 2,700
within 0.1%   27.2% of commodity-years / 47.8% GBP
within 5%     36.3% of commodity-years / 65.6% GBP
```

Nine commodity-years changed, eight closer and **one further**: 1874 goes
1.0106 to 1.0137. The guard fired correctly on the state it saw — adding the
cell did move the year toward its total at that moment — and a later pass then
shifted the sum. Three thousandths against six exact years is the trade, and it
is recorded rather than tuned.

## Where else this applies

`combine` is now available for any printed "A and B" line whose halves were
parsed apart. The dye-stuffs section has more of them — `Madder, Madder Root,
Garancine, And Munjeet` sits beside `Madder`, `Madder — Root`, `Madder —
Garancine` and `Madder — Munjeet`, all anchored, which makes it the deferred
"which label carries Tier 1" question as well as this one. It should not be
attempted until that decision is made.

---

# Round 47 — `Imitation Lard` and `Quicksilver`

Two more off the queue, one of each shape.

## `Imitation Lard` — a de-headed anchor

Printed Cwt totals for 1893-1900 and **not one country cell**, beside
`Lard — Imitation Lard (Including All Kinds Of Artificial Or Imitation Lard)`
with five countries, GBP1.0M and no anchor. **Six years to the digit**: 1893
83,754, 1894 47,974, 1895 48,444, 1896 39,663, 1898 84,454, 1899 78,281.

Folded so the surviving name keeps the group.

**Recorded**: 1897 reads **30,988 against a printed 39,988** — the
ten-thousands digit 0 for 9, the same misread class that put 299,282 on bacon's
Canada in round 32. The year now shows 0.7749 instead of nothing, which is what
makes it visible. 1891 and 1892 have origins but no anchor on either label; 1900
has the anchor and no origins.

## `Quicksilver` — orphans that tile 1872-79

`Quicksilver` has 35 printed years and 28 countries, but its own origins start in
**1880**. Two labels fill the gap and, once again, the pair is complementary:

- `Quicksilver (Metallic)` holds 1872 and **1874-79** — four exact (1875
  3,195,786; 1876 2,843,918; 1877 3,593,961; 1878 3,232,618), with 1872 +710,
  1874 −3,000, 1879 −300.
- `Plumbago — Quicksilver, Metallic` holds **1873 alone, 2,391,704** — the
  printed total for 1873 exactly, and the one year the other misses.

**Not folded**, and worth knowing why: five further labels carry a `Quicksilver`
head — `Quicksilver, Metallic — Linens And Cotton Rags`, `Quicksilver,
(Metallic) — Woollen…`, `— In The Husk`, `— Rags, Woollen…`,
`Quicksilver — Woollen, Applicable To Other Uses Than Manure…`. Their values are
16,259 Ton, 24,827 Ton, 16,601 Quarter, 26,420 unitless against a line running in
the millions of pounds. **These are the reverse of the usual glue: quicksilver's
own head stuck to the articles that follow it**, so they are other commodities
wearing this one's name. Folding any of them would be the mistake this whole
report exists to avoid.

`Pyrites Of Iron Or Copper Or Sulphur Ore — Quicksilver, Metallic` reads 1872 as
**2,734,104** against the printed 2,734,094, ten better than the folded label's
2,734,804 — but it overlaps 1872, so taking it needs a cell replace rather than
a fold. Queued.

## Result

Fifteen commodity-years changed, **15 closer, 0 further**, every one from "no
origin data" to a ratio; **thirteen land inside 0.1%**.

```
exact01  2,700 -> 2,713      nodata  5,810 -> 5,795
within 0.1%   27.3% of commodity-years / 47.8% GBP
within 5%     36.5% of commodity-years / 65.6% GBP
```

---

# Round 48 — `Books`, `Bark`, and the magnitude tell earning its keep

## `Books`

31 printed Cwt years, origins for 1872-84, 1886 and 1887 only. Two labels supply
the gap and neither is the obvious one:

- **`Beef — Books, Bound Or Unbound, Including Maps And Charts`** — the book
  table under a stale BEEF head — holds 1888, 1889, 1891, 1893, 1894, 1895, all
  gaps, **four exact** (1888 30,350; 1889 33,310; 1891 33,052; 1895 47,095) with
  1893 −3 and 1894 +5.
- **`Books, Bound Or Unbound, Including Maps And Charts`** — the same table under
  its own head — **scoped** to 1885, 1890, 1892, 1896, the four remaining gaps.
  1885 22,309, 1890 32,268 and 1892 29,522 are exact; 1896 is 44,182 against
  43,851. Its other years would collide with the target's own cells, and 1895 is
  left to the fold above, which reads it identically.

**Not folded, and this is round 47's caution paying for itself**:
`Books, Bound And Unbound, In- Cluding Maps And Charts` looks like a third copy
of the same title — the hyphen break in "In- Cluding" is the sort of OCR damage
that usually means a variant — but its values are **2,789,501 against a printed
32,529, eighty-six times over**. It is a different commodity wearing this one's
name. The tell was magnitude, not the label.

## `Bark — For Tanners' Or Dyers' Use`

`Bark — For Tanners' Or Dyers' Use, Unenumerated` holds 1872-75 — **all four
exact** (476,323; 467,515; 324,703; 471,900) and disjoint from the target's
1876-81. Folded.

**It changes no ratio, which was predicted before applying it**: the target's
Tier-1 cells carry **no unit at all** while its country cells are `Cwt`, so
`reconcile_baseline` compares the unitless anchor against a unitless origin sum
of zero. The fold is right; the scoring cannot see it.

### That class, measured

**15 commodities have a unitless Tier-1 series and origins in a real unit — 105
commodity-years, of which 16 already match the printed total to the digit.**

| commodity | T1 | origins | exact | GBP |
|---|---|---|---|---|
| `Bark — For Tanners' Or Dyers' Use` | 14y `?` | 10y Cwt | 6 | 2.1M |
| `Manures — Unenumerated` | 12y `?` | 25y Ton | 5 | 7.6M |
| `Manures — Nitrate Of Soda (Cubic Nitre)` | 3y `?` | 6y Ton | 2 | 5.8M |
| `Ivory — Vegetable` | 6y `?` | 16y Cwt | 1 | 21.2M |
| `Ore Of (Including Chrome)` | 5y `?` | 6y Ton | 0 | 24.6M |

Sixteen exact matches are sitting behind a missing unit label on the **anchor**
side. Queued — the repair is to give the T1 series the unit its own origins use,
guarded (as ever) by the years that already agree.

## Result

Ten commodity-years changed, **10 closer, 0 further**, every one from "no origin
data"; **nine land inside 0.1%**.

```
exact01  2,713 -> 2,722      nodata  5,795 -> 5,785
within 0.1%   27.4% of commodity-years / 47.8% GBP
within 5%     36.6% of commodity-years / 65.6% GBP
```

---

# Round 49 — the anchor that lost its unit

Round 48 folded four exact years into `Bark — For Tanners' Or Dyers' Use` and
watched them change nothing, because that commodity's **Tier-1 series carries no
unit** while its country cells are `Cwt`. `reconcile_baseline` compares the
unitless total against an unitless origin sum of zero, so the commodity scores
nothing in any year — even where the countries already sum to the printed figure
exactly.

## The pass

`unit_the_anchor`, run in both the places the other anchor-guarded passes run.
**The origins' unit is real information — it was printed on the column — and the
anchor's is what went missing, so the anchor takes the origins' unit, never the
reverse.**

Guarded by agreement: **at least two years must already match to the digit**
before the label is moved, the same refusal of single coincidences the orphan
matcher uses. A commodity whose countries do not agree with its own printed total
in two separate years has something else wrong with it and is left alone.

## Result

29 anchor cells relabelled, across **three** commodities. Full corpus ratio diff:
**22 commodity-years changed, 22 closer, 0 further, and 15 now inside 0.1%.**

| commodity | years recovered |
|---|---|
| `Bark — For Tanners' Or Dyers' Use` | 10 |
| `Manures — Unenumerated` | 9 |
| `Manures — Nitrate Of Soda (Cubic Nitre)` | 3 |

```
exact01  2,722 -> 2,737      nodata  5,785 -> 5,763
within 0.1%   27.5% of commodity-years / 47.9% GBP
within 5%     36.8% of commodity-years / 65.7% GBP
```

## What the guard refused, and why that is the right answer

Twelve of the fifteen candidates were **left alone**, including the two largest
in the class — `Ivory — Vegetable` (GBP21.2M, 6 unitless T1 years against 16
years of Cwt origins, **one** agreement) and `Ore Of (Including Chrome)`
(GBP24.6M, **none**).

One agreement is exactly the coincidence this project refuses. A missing unit
label is not the only thing wrong with those two: if the countries and the
printed total agreed, they would agree more than once. Relabelling their anchors
would have made them *look* scored while measuring nothing. They stay in the
queue, needing a reason for the disagreement rather than a unit.

---

# Round 50 — a wrong unit is out by a factor, not by two per cent

Round 49's guard required **two years agreeing to the digit** before it would
give an unitless anchor its origins' unit. That refused `Ore Of (Including
Chrome)` (GBP24.6M), which agrees with its own printed totals like this:

```
1893  1.0005    1894  1.0244    1895  0.9877    1896  1.0042    1897  1.0031
```

Never to the digit, and never far away either. Nothing but the same measure
produces that: **a wrong unit is out by a FACTOR — twenty, for Ton against Cwt —
not by two per cent.**

## The second path

`unit_the_anchor` now accepts a series on either of two kinds of evidence:

- **two years exact to the digit** (identity), or
- **every overlapping year within 5%, and at least three of them**
  (proportionality).

The second is not a weakening. It demands *all* the years hold, where the first
demands only two, and it is refused the moment a single year strays.

## It still refuses `Ivory — Vegetable`, and that is the test

`Ivory — Vegetable` (GBP21.2M) has **1899 matching to the digit** — 17,188
against 17,188 — while 1894-98 run:

```
1894  11.3x    1895  31.1x    1896   9.4x    1897  21.4x    1898  29.5x
```

One exact year and five wild ones, with no consistent ratio. That is not a
missing unit label: **its printed totals for 1894-98 are not the total of these
countries at all**, which is a different defect and one a unit cannot repair.
Both paths refuse it, and it stays queued as an unexplained series rather than
being made to look scored.

## Result

49 anchor cells relabelled (was 29). Full corpus ratio diff: **13 commodity-years
changed, 13 closer, 0 further.**

| commodity | years | |
|---|---|---|
| `Ore Of (Including Chrome)` | 5 | 1893 inside 0.1%, the rest inside 5% |
| `Manures — Bones For Manure (Whether Burnt Or Not)` | 5 | 1896, 1897, 1899 **exact**; 1898 0.9995 |
| `Saumur` | 3 | 1896 **exact**; 1893 0.9999, 1894 0.9992 |

```
exact01  2,737 -> 2,745      nodata  5,763 -> 5,755
within 0.1%   27.6% of commodity-years / 47.9% GBP
within 5%     36.9% of commodity-years / 65.9% GBP
```

---

# Round 51 — `Ivory — Vegetable`: one glued cell, five years, GBP20.8M

Round 50 refused to give this commodity's anchor a unit and said why: its 1899
matched to the digit while 1894-98 ran 9× to 31× with no consistent ratio, so
something other than a unit label was wrong. This round found it.

Vegetable ivory is corozo (tagua) nut, and it comes from **Colombia and
Ecuador**. The commodity carries a `British East Indies` row in every year
1894-98:

| year | printed total | that one row | everything else | else / total |
|---|---|---|---|---|
| 1894 | 33,076 | **337,303** | 34,985 | 1.058 |
| 1895 | 12,988 | **390,694** | 13,661 | 1.052 |
| 1896 | 39,129 | **338,684** | 30,385 | 0.777 |
| 1897 | 16,412 | **334,833** | 16,784 | 1.023 |
| 1898 | 12,716 | **360,947** | 13,709 | 1.078 |
| 1899 | 17,188 | *(none)* | 17,188 | **1.0000** |

**1899 is what identifies it**: the one year with no such row is already exact.
The rest is a stable ~350,000 cwt East Indies series — steady enough to be some
other printed line's real data — sitting in a commodity whose entire world trade
is twelve to thirty-nine thousand.

## A third curation verb: `drop-country`

```
drop-country,<country>   this country's cells are not this commodity's.
```

Anchor-guarded like everything else here: a cell is removed only where the
commodity prints a total for that year **and removing it brings the year
closer**. A mis-aimed rule therefore removes nothing, and a country that really
belongs is kept by the arithmetic rather than by trust. It takes the optional
`years` scope, and `v` — the size the map ranks by — follows the cells out, so a
commodity cannot go on advertising trade it no longer holds.

One wrinkle worth recording: the guard falls back to matching the anchor **by
year alone** when the commodity's own anchor has lost its unit label. That is
exactly the state a glued cell leaves it in — `unit_the_anchor` refuses to label
a series whose years disagree, and they disagree *because* of the glued cell.
The closer-to-the-total test still has to hold.

## Result

Five cells dropped. **1,762,461 cwt** and **GBP20,775,334** of phantom trade
leave the commodity: `Ivory — Vegetable` goes from **GBP21,172,464 to
GBP397,130**, which is the size a corozo-nut line should be.

**No commodity-year ratio changed, and that was predicted.** The commodity still
cannot be scored: its anchor is still unitless, because 1896 (0.777) breaks the
proportionality path and only 1899 is exact, so the identity path is one year
short. The fix here is real and the reconciliation still cannot see it.

```
within 0.1%   47.9% -> 48.0% GBP        within 5%   65.9% -> 66.0% GBP
nodata GBP-weight  24.6% -> 24.5%       exact01 unchanged at 2,745
```

**Those two tenths are weight leaving, not years improving** — GBP20.8M of
phantom value was sitting in the `nodata` bucket and is now gone. Stated
plainly because it is the same trap as the duplicate-shadow denominator: a
percentage can rise without one number getting better.

## Still open

**`Ivory — Vegetable` 1896 reads 0.777** on the cleaned data — 30,385 against a
printed 39,129, about 8,700 cwt short — while its four neighbours sit at
1.02-1.08. One more year explained and this commodity's anchor earns its unit
and six years become scorable.

---

# Round 52 — the item did not close, and the generalisation did

## `Ivory — Vegetable` 1896: not closed

Round 51 left one year at 0.777 and asked what was wrong with it. The answer is
that **nothing identifiable is**. The anchor is sound: `import / quantity /
Vegetable Ivory` is carried by **three volumes agreeing** (`as_1898`, `as_1899`,
`tn_1899`) at 39,129, tier B. So the origin side really is ~8,744 cwt short, and
the country list for 1896 is the *longest* of the three years (twelve entries
against 1897's eight), so it is not an obviously dropped row.

The four neighbouring years run **1.058, 1.052, 1.023, 1.078** — consistently a
few per cent *over* — so 1896 is the odd one in a series that is otherwise
slightly heavy. Nothing in the parses pins it and guessing a digit is refused.
**Re-queued with that evidence.** Note also that even with 1896 explained the
commodity would still not be scorable: `unit_the_anchor`'s 5% band fails on 1898
(1.078) and 1894 (1.058) as well.

## The generalisation: oversized country cells

Round 51's repair — one country cell far larger than the whole commodity — is
worth looking for everywhere. `reports/oversized_country_cells.csv` lists every
country cell **at least five times its own commodity's printed total**:

**197 cells across 30 commodities.** Most of the labels are not places at all but
article strings absorbed into the country column — `Prunes From France Other`,
`Plums French And Prunelo`, `Whale Fisheries Northern Other Cou`,
`Bombay And Scinde Bengal And Burma`.

Only **five** are cells whose removal lands the year within half a factor of its
printed total, and four were applied (the fifth, `Tobacco — Burgundy` / France,
lands at 0.74 on a label that is itself junk — "Burgundy" is a wine):

| commodity | the cell | year | after |
|---|---|---|---|
| `Silk — Raw` | **84,778,433,506** against a printed 6,445,213 | 1873 | 13,150× → **0.9196** |
| `Skins, Furs, And Pelts — Seal` | 502,306,368 against 713,632 | 1884 | 704× → **0.9207** |
| `Horns And Hoofs` | 342,009 against 5,745 | 1889 | 60.5× → **0.9998** |
| `Isinglass` | 4,253,700 against 4,098 | 1874 | — |

Three commodity-years changed, **3 closer, 0 further**. `exact01` 2,745 -> 2,746.

## A bug in round 51's own bookkeeping, caught by the diff

Making `v` follow the dropped cells looked right and was wrong. `v` is
accumulated as a sum of **min(cell_value, 50,000,000)** — the same cap the
commodity roll-up applies — and the garbage cells being removed carry garbage
*values* as well as garbage quantities. Subtracting the raw figure drove
`Silk — Raw` from **GBP127.6M to zero** and `Skins, Furs, And Pelts — Seal` from
**GBP63.4M to zero**: two large, real commodities erased from the map by a
repair aimed at one bad row.

The subtraction is now capped the same way `v` was built. Silk keeps GBP77.6M,
the seal skins GBP13.4M, and the fifty million each loses is exactly what the
bad cell had contributed.

**It was the full before/after diff that caught this, not the baseline** — the
headline numbers barely moved while two of the corpus's larger commodities were
being zeroed.

---

# Round 53 — a label split hid a vote majority

## The twin

Round 51 removed a glued East Indies series from `Ivory — Vegetable`. **The same
printed table is also under a second label**, `Vegetable`, wearing its sub-entry
name: `Bengal` **336,723 / 389,939 / 338,233 / 334,636 / 360,702** cwt for
1894-98, where the other label carried the aggregate `British East Indies`. One
table, two labels, two levels.

**A fix applied to one label may need applying to its twin.** Dropped; that
label falls from **GBP20,765,554 to GBP16,657**, which is all it ever legitimately
held.

## The finding: the vote never saw its own majority

Round 52 could not explain `Ivory — Vegetable` 1896 because "three volumes agree
on 39,129". They do not. The readings are split across **two spellings of the
article**:

```
under 'Vegetable Ivory'   as_1898  39,129    tn_1899  39,129    as_1899  30,129
under 'Vegetable'         as_1897  30,129    tn_1901  30,129
```

Within the first row the vote is 2-1 for 39,129 and it wins. **Across both
spellings it is three volumes to two for 30,129** — and the consensus keys on the
article string, so neither row ever saw the other's ballots. A cousin of
[[vote-tiebreak-lone-reprint]], and a mechanism worth its own name: **a label
split hides a vote majority.**

The origin arithmetic settles it without needing the ballots at all. With the
glued series gone, 1896's countries sum to **30,385**:

```
30,385 / 30,129 = 1.0085          30,385 / 39,129 = 0.7765
neighbours:  1894 1.058   1895 1.052   1897 1.023   1898 1.078
```

1.0085 belongs to that series; 0.7765 does not. **39,129 is a 3-for-9 misread of
the ten-thousands digit**, and round 52's open item closes.

Applied through `reference/manual_t1.csv` — the sanctioned override, whose 18
existing rows are precisely this class.

## The re-vote was clean, which is the safety result

`reconcile.py` rebuilds the Tier-1 vote for the **whole corpus** (51,268
series-years, 2m38s). The full before/after diff:

- **exactly one commodity-year changed** — `Ivory — Vegetable` 1896, T1 39,129 ->
  30,129;
- **exactly one `v` changed** — `Vegetable`, from the twin's dropped cells.

Nothing else moved, so the `consensus` table was in sync and the re-run
introduced no drift. That is worth stating because it is the thing that could
have gone wrong.

```
exact01 unchanged at 2,746        within 5%  65.9% -> 66.0% GBP
nodata GBP-weight 24.5% -> 24.4%
```

Those tenths are **weight leaving the nodata bucket again**, not years improving —
GBP20.7M of phantom left `Vegetable`. Said plainly for the third time because it
is the easiest number in this project to misread.

## Still not scorable, and now for a stated reason

`Ivory — Vegetable`'s anchor is now correct and the commodity **still cannot be
scored**: `unit_the_anchor`'s identity path needs two exact years and has one
(1899), and its proportionality path needs every year within 5% and gets 1894 at
1.058 and 1898 at 1.078. The anchor being right is worth having anyway — anyone
reading the series now gets the true figure.

## The oversized-cell survey, classified

Of the 30 commodities in `reports/oversized_country_cells.csv`, the median
`rest/T1` after removing the oversized cell separates two kinds:

- **single-cell cases** — `Vegetable` 0.01, `Silk — Raw` 0.92,
  `Skins, Furs, And Pelts — Seal` 0.92, `Isinglass` 1.00, `Horns And Hoofs` 1.00,
  `Yarn` 1.95. All now handled or one step away.
- **chimeras** — `Collodium` (28 cells, median 871), `Slates` (19, 368),
  `Oil-Seed Cake — Of Other Sorts` (16, 331), `Dye Woods — Logwood` (16, 79),
  `Leather, Undressed` (15, 77), `Madder…` (15, 61). **Removal does not rescue
  the year, because the whole label is glue.** Those want `drop`, not cell
  surgery — and `Madder` is also inside the deferred era-spelling decision.

---

# Round 54 — the classification was wrong, and nothing was applied

Round 53 sorted the oversized-cell commodities by the **median `rest/T1` after
removing the cell** and called the high ones chimeras. Reading them shows that
statistic conflates three different things, so the label was wrong for most.

## What they actually are

| | commodity | T1 yrs | within 5% | >2× | no origin in anchor unit |
|---|---|---|---|---|---|
| good, few bad years | `Cotton` | 35 | **26** | 0 | 7 |
| | `Coffee — Raw` | 27 | **24** | 2 | 1 |
| | `Fruit — Raisins` | 27 | **23** | 0 | 4 |
| | `Paper — Hangings` | 29 | **21** | 1 | 6 |
| | `Dye Woods — Logwood` | 33 | **20** | 5 | 6 |
| | `Caoutchouc` | 35 | **15** | 0 | 7 |
| genuinely broken | `Collodium` | 8 | 1 | 6 | 1 |
| | `Oil-Seed Cake — Of Other Sorts` | 5 | 1 | 4 | 0 |
| no origins in the anchor unit at all | `Leather, Undressed` | 8 | 0 | 0 | **8** |
| | `Shells Of All Kinds` | 11 | 0 | 0 | **11** |
| | `Slates` | 7 | 0 | 0 | **7** |

Most of these are **sound commodities with a handful of glued years**, not
chimeras. `Cotton` (GBP65.8M) closes in 26 of 35 years; `Coffee — Raw` (GBP278M)
in 24 of 27. Dropping any of them would have been a serious mistake, and the
median statistic that suggested it should not be used for this again.

## A hypothesis raised and refuted in the same round

`Leather — Dressed` showed a median origin/anchor ratio of **exactly 112.0** —
the pounds-to-hundredweight factor — which looked like a whole class: anchors in
Cwt, origins in Lb, never converted. A corpus scan for **every** anchor/origin
pair separated by a clean unit factor (112, 20, 2240, and their inverses),
requiring two or more years agreeing within 5%, found **nothing**.

`Leather — Dressed` has **one** T1 year. The 112.0 was a single data point
wearing the shape of a law. Recorded so it is not raised again.

## `Dye Woods — Logwood`, characterised but not repaired

1893 closes **exactly**: British West India Islands 27,064 + British Honduras
12,667 + Mexico 7,507 + Hayti 3,402 + Argentine 752 + United States 302 + Other
Foreign 226 + France 222 + Germany 158 = **52,300**, the printed total. That is
the real geography of a Central American dyewood.

1894-98 carry **32 to 39 countries** on a European and Mediterranean profile —
Belgium 2,954,843, Russia 2,496,038, Denmark 2,019,503, Canada, Egypt, Spain,
Portugal, Morocco, Sweden, Italy, Austrian Territories, Gibraltar — against
printed totals of 39,297 to 68,457.

**29 countries appear only in those five years** and account for **4,318,823 of
1894's 4,693,306, or 92%**. But removing them still leaves the year at 5.5× its
total, because the countries that *do* belong are inflated too (British West
India Islands 33,713 in 1894 against 27,064 in the year that closes). **The block
is thoroughly glued, not garnished**, so `drop-country` cannot clean it and
**nothing was applied**. It needs a source-level `group_repairs` range, which is
outside what the payload can express.

A half-cleaned block that still reads 5.5× is worse than one plainly flagged, so
it is queued whole.

## Nothing changed

No curation rows, no code, no baseline movement. The deliverables are the
corrected taxonomy above, the refuted unit-factor hypothesis, and a logwood block
described precisely enough for a source-level repair to start from.

---

# Round 55 — `Dye Woods — Logwood`: the glue was one volume

Round 54 characterised the 1894-98 block and declined to repair it at payload
level. The source level makes it simple.

## What the volumes hold

`as_1898` carries **621 rows** under a stale `DYE WOODS | Logwood` head across
`row_seq` 4504-6282 — about **105 "countries" a year summing to 11.8-14.1
million tons** against printed totals of 39,297 to 76,075. **172× to 358×.** A
whole section of the volume absorbed under one commodity's heading. Every other
volume has 4 to 27 rows.

`as_1897`'s own logwood block (`row_seq` 5849-5912) is correct and closes:

```
1894  Germany 562 + France 62 + Spain 450 + US:Atlantic 219
      + US:Danish West Indies 378 + US:Hayti 8,893 + Mexico 9,915
      + Other Foreign 145                     = 20,624   printed foreign TOTAL
      British West India Islands 33,713 + British Honduras 14,120
                                              = 47,833   printed British TOTAL
                                              = 68,457   printed GRAND  — EXACT
1895 −3      1896 −900      1897 +60      1893 52,300 — EXACT
```

## The repair

One `group_repairs` row: supersede the consensus readings for **1893-1898** and
re-admit `as_1897`'s block in their place.

| year | before | after |
|---|---|---|
| 1894 | 68.6× | **1.0000** |
| 1895 | 109.9× | **0.9999** |
| 1896 | 93.1× | 0.9882 |
| 1897 | 131.5× | **1.0015** |
| 1898 | 134.5× | **nodata** |

**1898 exists only in the glued block**, so it becomes an honest gap rather than
a measured 134× — a deliberate trade, and the reason `over` falls by five while
`exact01` rises by only one.

```
exact01  2,746 -> 2,747      over  261 -> 256      within 5%  36.9% -> 37.0%
GBP: `Dye Woods — Logwood` 21,269,545 -> 9,145,775
```

## 1893 had to be superseded too, and finding out why is the lesson

The first attempt superseded only 1894-98 and **1893 went from exactly 1.0000 to
1.0650** — a year that was already right, broken by a repair aimed elsewhere.

`as_1897`'s block is a five-year comparative table, so each printed row is five
consecutive `row_seq` and 1893's cells are **interleaved** with the rest; the
seq range cannot exclude them. Step 6 skips a repaired cell only when consensus
already holds that (sig, country, year) — and the repair carries sub-entries
under their literal `Parent : Sub` labels, which consensus stores folded, so
1893's sub-entry rows were admitted a second time.

Superseding 1893 as well fixes it, and is safe because `as_1897`'s 1893 sums to
**52,300, the printed total exactly**.

**The rule: when a repair block spans years you are not superseding, its
sub-entry rows can double-count into them. Supersede the whole span the block
covers, or check every year it touches.**

## Left standing

`Dye Woods — Logwood` **1883 reads 1.0074**, up from exactly 1.0000. It is
outside the repair's years entirely; the knock-on runs through the payload's
own passes, which see different inputs (`coast-rollup` 2,424 -> 2,427). Three
quarters of one per cent on one year, against five years rescued from 68× to
131×, and recorded rather than chased.
