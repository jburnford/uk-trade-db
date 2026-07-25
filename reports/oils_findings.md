# The oils — what was actually wrong (2026-07-25)

The previous version of this note credited a "geographic method" with fixing
palm oil, and left three years queued as still wrong. That reading was
half right. Geography did find three misfiled tables. But the reason palm
oil's origins **looked** wrong — Portuguese West Africa as Britain's dominant
source of palm oil through the 1870s — was not a misfiled table at all. It was
a parser heuristic mislabelling every row of an origin block, in a way no
arithmetic check could see.

## First, the question that started this: palm oil vs palm kernel oil

The user's instinct was that Germany should be a source of palm *kernel* oil
while palm oil comes from West Africa, and that the source distinguished them.
Checked against the print, in every volume 1872-1899:

* **Germany is a printed origin of "Oil: Palm", and a large one.** The 1899
  volume's own table reads `From Germany — 102,772 / 233,852 / 123,022 /
  120,970 / 131,243 Cwts` for 1895-99, ahead of every West African entry
  except Lagos. Our figures are that table, digit for digit. Germany is not
  an extraction error.
* **The source does not separate the two oils.** There is one line, `Oil,
  Palm`, and the alphabetical index carries one cross-reference, `PALM OIL
  (see Oil)`. Grepping every volume for `palm nut`, `palm kernel` or `kernel
  oil` returns nothing.
* **Palm kernels are in the statistics, but as raw material, not as oil.**
  They sit inside `Nuts and Kernels, commonly used for expressing Oil
  therefrom` (Tons) — one aggregate line that also carries copra from the
  Philippines and the Pacific, ground nuts, and Ceylon produce. Its origin
  table names Lagos, Sierra Leone, the Gambia and the Niger Protectorate
  beside Java, Manila and New South Wales.

So the economic intuition is right and the statistic does not honour it. What
Hamburg shipped to Britain was overwhelmingly oil crushed from West African
kernels, and the Board of Trade filed it under `Oil, Palm` alongside oil
pressed at the source. **Germany's share of "palm oil" imports should be read
as kernel oil re-exported after crushing, and this source cannot separate it.**
That is a caveat for anyone mapping palm oil origins, not a defect to fix: any
map of `Oil — Palm` shows Germany as a consignor, because the source does.

## The real defect: a heading row read as a row-slip

The standard geometry of an origin table puts the unit caption on the row that
opens a region:

```
        From West Coast of Africa (Foreign) :     Cwts.        £
            Fernando Po                           8,747      15,514
            Portuguese Possessions                5,013       8,773
            Not particularly designated         630,994   1,125,708
        " British West Africa                    28,864      49,621
        " The Gold Coast                        208,400     370,929
        " Other Countries                        15,246      27,621
            Total                                897,264   1,598,166
```

`parse_country.py` treated a country-ish row whose cells hold only a unit as
the **row-slip signature** — the case (real, in as_1882 wool) where the OCR
pushed every value down a line. So it queued the heading and paired it with
Fernando Po's numbers, then gave Fernando Po the Portuguese figures, and so on
down the block, dropping `Other Countries` off the end.

Every quantity was right. Every label was one row out. The block still summed
to its printed total, because relabelling preserves a sum — which is why
sixteen rounds of anchor reconciliation never saw it, and why the queued
"1876 reads 0.25" style notes kept pointing at the wrong thing.

Corpus-wide the heuristic fired on **83 blocks and was wrong on 82 of them.**
The one real case is as_1882 `Wool, Sheep or Lambs'`, where `From Russia:`
carries a spurious colon and is a plain sibling of `" Denmark` below it.

### How the two readings are now told apart

Only a genuine slip leaves an **orphan numbers row with no label** at the end
of the block, holding the last country's figures. So the shift is applied
provisionally and the end of the block settles it:

* drained by an orphan row → the slip was real, keep it;
* drained by the printed Total → un-shift the block in place, reopen the
  heading as the region context, and give the trailing label its own numbers.

Two supporting fixes were needed to make that test work:

1. The wide two-up geometry **skipped label-less rows entirely** ("data may
   still ride label-less rows; nothing to classify"), so genuine slips could
   never find their orphan and lost their final member — as_1872 CHEESE lost
   `Other Countries` 4,039 / 13,333 that way. They are now fed when a cascade
   is open. 170 blocks began draining correctly, each recovering a row.
2. A Total *smaller than the block's largest member* is not a block total. In
   as_1874 palm oil the OCR prints `Total 10,193` (really Other Countries)
   above the true `Total 1,067,767`, so that block keeps its shift and the
   queued label takes the figures.

Units improved as a side effect: the caption on the heading row is now read as
the block's unit instead of being discarded, so **~11,500 rows gained a printed
unit and ~2,000 stale ones were corrected** (`Tons`→`Cwts` for hams; the
non-unit `Oil`→`Tons`). Unit-less origin cells never reach the map's quantity
axis, so several of the "unit-less origins" complaints in earlier rounds were
this.

### Proof, on palm oil's own arithmetic

For 1874 and 1876-79 the corrected reading closes **both columns exactly**
against the printed totals — quantity *and* value, which the mislabelled
reading also did, but only the corrected one agrees with the print row by row:

| year | qty sum | T1 anchor | value sum | printed value |
|---|---|---|---|---|
| 1874 | 1,067,767 | 1,067,767 | 1,792,041 | 1,792,041 |
| 1876 | 879,824 | 879,824 | 1,529,360 | 1,529,360 |
| 1877 | 897,264 | 897,264 | 1,598,166 | 1,598,166 |
| 1878 | 670,797\* | 670,797 | 1,167,161 | 1,167,161 |
| 1879 | 881,299 | 881,329 | 1,344,788 | 1,344,788 |

\*with the 1878 digit repair below.

Palm oil's origin sum now sits at 1.00 of its printed national total in **21 of
26 years 1872-1897**, and the dominant origin through the 1870s is `West Coast
of Africa (Foreign), not particularly designated` — the Bights, as it should
be — rather than Angola.

### Five hand-repairs had been patching this case by case

`reference/group_repairs.csv` already carried five `label_shift` entries whose
notes describe exactly this mechanism:

* as_1895 wheat — "'From Russia:' heading took Northern Ports' value"
* as_1886 / as_1891 / as_1893 rice — "'From British East Indies:' heading
  absorbed Bombay and Scinde's value and every member slipped one row"
* as_1883 lac — "Infinity's 'British India' heading absorbed Bombay's value"

The parser now does what they were doing by hand, so they were retired (the
group/unit relabel each also carries is kept). Applying them again would shift
those blocks a second time. **Retiring them is verified**: the rice pairings
the notes derived by hand — 1891 `B&S 2,682 / Madras 41,004 / Bengal 1,175,929
/ Burmah 3,916,754 / Straits 48,048 / HK 9,000`, 1893 `Bengal 848,241 / Burmah
3,342,941 / Straits 121,697 / Other BEI 141` — are now what the parser emits,
unaided.

## The cross-engine matcher was re-applying the shift

Even with the parser fixed, 1874 and 1877 still came out mislabelled in
`country_year_final`. `reconcile_country.align_members` pairs the two OCR
engines' rows **by country name, then leftovers by position**. Once one engine
carries the region prefix (`West Coast Of Africa (Foreign) : Fernando Po`) and
the other prints it bare, no member matches by name, every row falls to the
positional fallback, and because the engines differ by one line the fallback
pairs each label with the other engine's *next* row — reconstructing the
defect the parser had just removed. Matching now falls back to the member's own
name under a region header before it falls back to position.

## Migrating 777 seq-keyed repairs

Every entry in `group_repairs.csv` addresses rows by `row_seq` range, and
`row_seq` is a running counter, so adding or dropping one row renumbers
everything after it in that section. This change moved 22 sections. Left
alone, 35 hand-adjudicated repairs would have started relabelling innocent
tables — as_1873 LARD onto JUTE, as_1882 HORN onto HIDES.

`scripts/rebase_group_repairs.py` re-finds each repair's rows by content
(the quantity/value sequence, not the labels, which a label repair exists to
change) and rewrites the range; it reports anything it cannot place uniquely
rather than guessing. Verdicts: 735 unchanged, 35 re-based, 5 premise-gone
(above), 2 ranges extended by one row because the parser now recovers a final
member that used to be misread as the block's Total. **Run it once per
re-parse, before the ranges are rewritten.**

## Effect on the standing metrics

| metric | before | after |
|---|---|---|
| gold numeric reproduction ±5% | 1,322/1,456 (91%) | 1,327/1,456 (91%) |
| gold numeric reproduction ±2% | 1,207 (83%) | 1,215 (83%) |
| gold attribution: value-error | 592 | 582 |
| gold attribution: shift | 24 | 22 |
| gold national exact (≤1%) | 648 | 639 |
| payload within 0.1% of T1 (GBP-wt) | 34.1% | 34.0% |

National closure is **flat by construction** — this defect never moved a sum,
which is the whole point. The gold `exact` count fell 9 because 12 fewer gold
cells name-matched a pipeline commodity (crosswalk churn as labels moved); the
reproduction and attribution measures, which is where a relabel shows up, both
improved. Gold covers six years and only two of them (1876, 1886) sit in the
worst-affected volumes, so it is a weak instrument for this class.

## Still wrong, with the evidence to fix it

Ordered by how provable each one is.

1. **Palm 1878: `Not particularly designated` reads 161,074, should be
   461,074.** The print itself shows 161,074, but the value column closes
   exactly at the printed 1,167,161 with 797,648 on that row, and the quantity
   column is exactly 300,000 short of the printed 670,797. 797,648/461,074 =
   £1.73/cwt, the block rate; against 161,074 it is £4.95, impossible. A
   broken-4 read as 1, the as_1883 wool class. → `manual_rows` with
   `replace=1`. Year goes 0.55 → 1.00.
2. **Palm 1875 double-counts: 2.00.** `west coast of africa foreign` carries
   904,562 — the printed **Total**, not an origin — beside six sub-rows that
   already sum to 904,562. `_apply_cctx` renames a Total row to its open region
   context, and its guard (`total > 2 × context sum`) cannot fire when the
   region spans the whole block. Same phantom in 1876 (value 879,824). The
   detector this needs is the one the earlier note proposed and is still worth
   building: **an origin whose quantity equals the year's whole national total
   is the Total row.** The existing impossible-origin filter only fires above
   1.15×, so it steps over the exact-match case.
3. **Palm 1877 is still mislabelled, and the fix is not the parser's.**
   Chandra reads the block correctly and closes; the Infinity OCR **itself**
   put Fernando Po's figures on the heading row (`From West Coast of Africa
   (Foreign) : | Cwts. 8,747 | £ 15,514`) and left `Other Countries` empty, so
   its copy is genuinely slipped and wins the arbitration at 1.00. Both blocks
   sum identically, so no arithmetic tie-break exists. Signature worth a
   detector: **a `From X :` heading row carrying figures while a later member
   row in the same block carries none.** Meanwhile a `group_repairs` entry
   against `obs_source=inf` is the established remedy.
4. **Palm 1898-99 are dominated by junk origins.** The de-headed `Oil` label
   folded into `Oil — Palm` (correct for the 1886-92 West African origins)
   also brings its corrupt 1897-99 cells, whose "countries" are commodity
   names — `Petroleum Gallons` 219,249,539, `Potatoes`, `Onions Raw Bushels`,
   `Paper Including Strawboard`. They were dismissed as harmless because they
   carry no unit and miss the quantity axis, but they are in the payload, they
   make `?` the dominant unit for those years, and they read as origins. Wanted:
   a filter dropping payload cells whose country matches a known commodity
   name — this will not be the only commodity affected.
5. **Olive oil has no usable anchor because `Tun` and `Ton` split it.** The
   printed unit is Tuns; the OCR alternates almost year by year (1872 Ton,
   1873 Tun, 1874 Ton, 1875 Tun…), so half the years' origins never share a
   unit key with the T1 line and the closure ratio reads 0.00 across the
   series. `heal_units` folds a labelled minority unit, but the split is by
   YEAR across all countries, so no country has a minority. Tun/Ton is an
   OCR-confusable pair (u↔o) and no article was ever printed in both, so the
   defensible rule is: within one commodity, fold Tun/Ton to whichever the T1
   anchor uses. Likely fixes the whole olive series at once.
6. **Coconut oil double-counts 1892-93 (1.98, 1.83)** — `British East Indies`
   is present alongside its own `Ceylon` and `Madras` children; the
   parent/children dedupe misses it because the children arrive as bare names
   the gazetteer does not list under that parent. 1894-96 have origins but no
   matched anchor; 1875, 1884 and 1885 are empty.
7. **`Nuts and Kernels, commonly used for expressing Oil therefrom` — the
   palm-kernel line — has coherent origins for all 28 years and no anchor at
   all** (anchor 0 in every year), so nothing about it can be quality-checked.
   Its T1 line is printed in Tons under a differently-worded label. Worth
   fixing before anyone uses kernels as a series, and it is the line that
   matters for the Germany question above.

## The geographic method still stands

Nothing above retracts it. West Africa shipped palm oil and palm kernels and
essentially nothing else in the oils, so an oil-family origin row from Lagos,
the Niger Protectorate, Fernando Po or Portuguese West Africa belongs to one of
those two lines — which is how the three misfiled labels (`Nitre, Cubic
(Nitrate Of Soda) — Palm` for 1880, `Oil — West Coast Of Africa (Foreign)` for
1873, `Oil — West Coast Of Africa` for 1872) were found and folded, and those
folds remain correct. The caution is the one this round taught: **a year that
closes against its printed total is not a year that is right.** Geography and
arithmetic both passed the 1870s palm tables while every country on them was
wrong.
