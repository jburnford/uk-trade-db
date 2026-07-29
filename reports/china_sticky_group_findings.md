# The CHINA, OR PORCELAIN, AND EARTHENWARE sticky group, 1893–1899

Worked 2026-07-29 (`/loop /next-defect` iteration 6). Carried into the loop as
the top open item — described in the iteration-5 log as *"a sticky group across
1893-1899 carrying Barley, Wheat, Peas, Buckwheat, Oatmeal and Groats, Maize,
Rye, Wheatmeal, Herrings, Manufactured tobacco and Cotton Waste — tens of
millions of cwt under a china heading. Much larger than anything left in the
whale or china families."*

**That framing was wrong, and correcting it is the first finding.**

## 1. Most of the sticky rows were never misfiled

`integrate_sources.load_csv` keys a row on

```python
asig = V.sig(art) or V.sig(f"{grp} {art}")   # generic article -> group fallback
```

— the GROUP IS ONLY CONSULTED WHEN THE ARTICLE IS EMPTY OR ALL-STOPWORD. Of the
**5,507** rows carrying the china group in `country_obs_inf` (as_1897 2,557 +
as_1898 2,950; as_1899 has none), **4,348 carry a sig-able article** — Wheat,
Barley, Oats, Peas, Rye, Buckwheat, Maize, Opium, Bark Peruvian, Piece Goods,
Hosiery — and were already keyed on that article, i.e. already in the right
commodity. Only **1,159 fall back to the china sig.**

Downstream the same holds: `country_year_final` keeps the literal
(group, article) pair and `build_viz_payload` re-sigs ARTICLE-FIRST, so
`CHINA…|Wheat` and `CORN…|Wheat` land on the same node. The payload's own
sticky-repair pass (891 repairs) folds most of the rest. Before this session's
change only **five** phantom china-group commodities survived in the payload
(Wheat, Manufactured, Meal not otherwise enumerated, Maize or Indian Cornmeal,
Fresh (Not Of British Taking) : Herrings) — none of them "tens of millions of
cwt of grain filed under china".

**Rule worth keeping: a stale `article_group` is only a data loss where the
article is empty or generic. Count the fallback rows before sizing the item.**

## 2. What the real defect was

One printed page-run in the as_1897 volume (the alphabetical C's of the general
imports origin section). The parser saw the `CHINA, OR PORCELAIN, AND
EARTHENWARE:` head and then missed the next four heads, so four complete origin
tables sat under it:

| main-engine seq | true commodity | printed grand TOTAL (1893 / 1894) |
|---|---|---|
| 2297–2366 | CHINA, OR PORCELAIN, AND EARTHENWARE | 201,963 Cwts / £625,532 |
| 2367–2396 | CIDER AND PERRY | 558,108 Gals / £23,814 · 431,155 / 17,309 |
| 2397–2437 | CLOCKS, AND PARTS THEREOF | £418,996 · £442,161 |
| 2438–2488 | COAL, CULM, AND CINDERS | 25,645 Tons / £52,321 · 10,313 / 31,092 |
| 2489–2553 | CONFECTIONERY | 45,836 Cwts / £88,393 · 53,106 / 104,775 |

Every one of cider, clocks, coal and confectionery closes **EXACT on both
printed columns** against its own T1 line — that is the identification, not a
guess from the country list.

**The unit runs are not the segment boundaries.** The parser's `Gals` run
covers cider *and clocks' first three rows* (Germany 26,301, Holland 61,135,
Belgium 105,063 are clocks values). Cutting on the unit change would have moved
three clocks rows into cider. Segment bounds have to come from the country
sequence matched against the raw page, exactly as the as_1888 whalebone/timber
case demanded.

The chimera was visible in `country_year_final`: china 1893–97 carried
**Turkey European + Turkey Asiatic in Cwts** (confectionery), **Australasia +
Australasia : New South Wales + New Zealand in Tons** (coal) and **United
States of America : On the Atlantic in Gals** (cider).

Two further blocks in the Infinity engine, same class, far downstream:
`as_1897` seq 2704–2777 and `as_1898` seq 4586–4664 are COTTON MANUFACTURES —
Unenumerated (grand TOTAL £1,566,245 / £1,705,442 == T1 EXACT), and `as_1898`
seq 4665–4669 is DIAMONDS (Cape of Good Hope carats; 1895 3,607,750/£4,754,055
against as_1897's 3,607,750/£4,754,025 and as_1899's 3,607,750/£4,751,035).
Both were parsed with article `Unenumerated`, whose sig is empty — so they too
fell back onto china.

## 3. Result

`reference/group_repairs.csv` +9 rows, `reference/group_aliases.csv` +2 rows.

* **China 1895, 1896, 1897: within5 → EXACT.** 239,239→237,805 (T1 237,811);
  316,097→323,888 (323,708); 352,758→351,241 (351,310).
* **The china node stops being a chimera**: 22 countries → 17, and the `Gallon`
  and `Ton` unit series disappear from it entirely.
* Coal gains 17 sub-entry cells and cider 10 (both previously inside china).
* **Zero regressions**; every other commodity-year unchanged.
* Baseline 9,634 c-y: exact01 **3,129 → 3,132** (32.5%), GBP 50.9% / 68.0%.

## 4. Three things that cost real time — write them down

### (a) `supersede_years` is global, and it moves the payload's commodity name

`supersede` is keyed `(GROUP.upper(), article, year)` with no volume scope, so
superseding china for a year drops that year in **every** volume using that
exact group string — as_1898 and as_1899 had to be re-added by their own repair
rows even though their tables are clean.

Worse, and not obvious: with the consensus rows gone, the surviving china rows
carried *different* literal spellings of the heading, and
`build_viz_payload`'s commodity merge **SPLIT the node in two** —
`China Or Porcelain, And Earthenware` (1878–99) and
`China, Or Porcelain, And Earthenware` (1883–93) — dropping **1887, 1888 and
1890 to nodata**. Fixed with two `group_aliases` rows folding
`CHINA OR PORCELAIN, AND EARTHENWARE` and `CHINA OR PORCELAIN AND EARTHENWARE`
onto the comma'd spelling. (`CHINA OR PORCELAIN WARE` must NOT be aliased — it
is the separate 1876–81 line.)

**Check after any supersede: did the payload commodity keep its name and its
country count?** The baseline number alone will not tell you — the split cost
3 commodity-years while the repair gained 3, and netted to −4 with the other
regressions masking it.

### (b) Supersede only the years that are actually polluted

The first attempt superseded 1893–1898. The as_1897 volume only covers 1893–97,
so 1898 was superseded for nothing — and china 1898 fell from EXACT to within5
because the surviving Holland reading changed from 86,603 to 96,503. (Neither
is right: the block closes at 86,503. Two engines, two different single-digit
misreads, and the closure names the true value — logged below, not applied.)
Narrowing to 1893–97 restored it.

### (c) A relabelled segment can double-count against an *aggregate*

Re-filing the CONFECTIONERY segment pushed confectionery 1893/94/95 **off
exact01** (45,836 → 47,059 in 1893, exactly +1,223). Confectionery's own
volumes print Turkey as ONE aggregate row — 1,223 = 369 European + 854 Asiatic
— and the `consensus_triples_ga` guard compares `cnorm` country keys, so
`turkey` never matched `turkey asiatic`. The segment is therefore **deliberately
not re-filed**: the supersede alone takes it out of china, which was the point,
and confectionery already closes EXACT from its own volumes.

**Generalisation: before re-filing a relabelled segment, check whether the
target commodity already carries the same trade as a coarser aggregate.** The
existing guard cannot see it.

## 5. Still open

* **CLOCKS 1893–97 cannot be recovered by a group repair.** The table is
  value-only (every quantity NULL) and step 6 filters `q is None or q <= 0`.
  Step 1 already has a value-only branch (admit under the literal unit
  `'Value'`); the groupfix path needs the same. 41 cells in as_1897, plus 74 +
  79 for the two COTTON MANUFACTURES — Unenumerated blocks. **Pipeline change,
  small and well-precedented — worth doing, not loop work.**
* **China 1898 Holland = 86,503**, by closure: T1 322,928 minus the other ten
  countries (236,425) leaves 86,503, and the two engine readings are 86,603
  and 96,503 — one digit away in each direction. Not applied; it would be a
  `manual_rows` replace and no page image was consulted.
* **The 1,159-row Infinity fallback set is only half-worked.** Repaired here:
  the two cotton blocks and diamonds (all documented, all admitting nothing —
  they exist so the supersede cannot strand them). NOT repaired: `as_1897` seq
  226–481 and `as_1898` seq 2117–2387 (the Infinity copy of the same
  china/cider/clocks/coal/confectionery run) and seq 482–721 / 2388–2621
  (COPPER, ORE OF and COPPER — Regulus and Precipitate). None of them reach
  `country_year_final` today, because step 2 only admits Infinity-only blocks
  for commodity-years absent from consensus and these are all present. Two
  cautions for whoever picks them up:
  1. **The Infinity copy of the china table is label-shifted the wrong way for
     `label_shift=1`.** `From Germany` absorbed the unit-header row, so
     numbers(i) belong to label(i−1); the flag re-pairs label(i+1) with
     numbers(i), which is the opposite. The main engine has these labels right.
  2. **`Regulus and Precipitate` has divergent sigs.** Step 6 computes
     `V.sig(f"{new_grp} {new_art}")` GROUP-FIRST → `copper+ore+precipitate+
     regulu`, while every other path is article-first → `precipitate+regulu`.
     The dedup guards therefore miss, and only the final
     `round(qty/1000)` dedup stands between the repair and a double count.
* **COAL, CULM, AND CINDERS has no `§TOTAL` in the payload**, so none of its
  origin work is measurable by the baseline. Worth a look on its own.
