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

---

# The careful fats-and-oils review (2026-07-25, session 8)

The user's framing came with a warning worth keeping: **the tallow price
collapsed in the 1890s when Australian tallow flooded the market.** A price
series that falls by half is not evidence of a defect here, and unit price is
only usable as a check WITHIN a block, against its own neighbours — which is
how it is used below, and how it settled New Zealand's tallow and the
United States' lard.

Where the family stands after the review (map view, 1872-99):

| commodity | before | after |
|---|---|---|
| `Lard` | 27 of 28 years close | **28 of 28** |
| `Tallow And Stearine` | 24 (0.82/0.73/0.74 in 1897-99) | **27**, 1889 alone |
| `Oil — Palm` | 25 | **26** |
| `Seeds — Flax Or Linseed` | 22 | **25** |
| `Seeds — Rape` | 19 | **20** |
| `Nuts And Kernels — Commonly…` | no anchor at all | **18 measurable, 6 exact** |
| `Oil — Animal` / `Oil — Chemical…` | stop 1896 | **run to 1899** |

## What the family actually taught, in order of how far it reached

### 1. The integrator was throwing away every region-qualified row of an Infinity-only block

`Tallow And Stearine` sits at 1.000 of its printed national total in every
year 1872-96 and then falls to 0.821 / 0.726 / 0.740. Nothing was missing
from the parse. The 1897-99 origins come from an Infinity-only block whose
whole American section is printed region-qualified —

```
United States of America : On the Atlantic   260,602   571,959   519,847
                         " On the Pacific     10,931         -     7,341
```

— and `integrate_sources` step 2 dropped every member whose country contained
`' : '`. Half a million cwt a year.

The blanket skip exists for a real reason: a `Region : Sub` row must not
double-count against a `Region` aggregate printed beside it. The guard now
looks at the **printed segment** (the run between Total rows) rather than the
whole block, because an Infinity glue block runs several commodities under one
stale article — the plain `United States of America` that vetoed tallow's
Atlantic/Pacific split in as_1899 belongs to the TAR table below it.

This is not an oils defect. It is a corpus-wide one:

```
Wheatmeal And Flour 1895-99   0.15-0.28 -> 0.96-1.00
Barley 1897-99                0.82-0.88 -> 0.96-1.00
Seeds - Rape 1883             0.281 -> 1.000
Spices - Unenumerated 1891    0.161 -> 1.000
Tar 1897                      0.082 -> 0.991
Shell Fish : Oysters 1897     0.294 -> 1.000
```

It also exposed an older double-count: a group repair names ONE engine's copy
of a glue block, and the other engine's copy re-enters as Infinity-only under
its own stale group. as_1899 oats is printed once and reached
country_year_final twice. The guard for that has to work **cell by cell** —
scoped to the whole commodity-year it killed barley 1893, and scoped to the
volume it killed as_1873 lard's Germany, a row whose own repair note says
"Germany stays lost (honest)". The honest loss was only Chandra's; Infinity
had the row.

### 2. 'Russia' was the northern ports, and the southern ports were being dropped

Every consumer treats a `(coast)` cell as drill-down detail inside its parent
and sums the parent alone. That is right when the parent is the printed
aggregate and wrong when the parser gave ONE coast its bare country name and
qualified the other — which is what `Russia : Northern Ports / Southern
Ports` does through the 1870s and 1880s. In the 1882 flax table `Russia`
597,454 IS the northern row, and `Russia (Southern Ports)` 442,058 was being
discarded as redundant to it. `country_year_final` summed to the printed
total to the digit the whole time; only the payload's view of it was short.

Told apart the one way that cannot guess: fold the coasts into the parent
only when doing so brings **the year's origin sum** closer to its printed
national total. Measuring against the parent cell alone instead — the obvious
mistake, and one I made first — fires 421 times and costs five points of
closure.

```
Corn And Grain - Wheat 1872           0.625 -> 0.999
Corn And Grain - Wheat 1875,77-79,84  0.84-0.94 -> 0.99-1.00
Wool - Sheep Or Lambs' 1873,75,78-80  0.968-0.987 -> 1.000
Seeds - Flax Or Linseed 1881-83       0.82-0.88 -> 1.000
```

### 3. Four digits, each pinned by two columns

The method that keeps working: **one engine is right about the quantity and
the other about the value, and each block's own printed subtotal says which.**

* **Lard 1885, United States 500,406 -> 800,406.** Chandra's Foreign subtotal
  526,035 agrees with its own 500,406, but its grand total 871,210 does not
  (526,035 + 45,175 = 571,210). Infinity reads 800,406, subtotal 826,035, and
  826,035 + 45,175 = 871,210 = T1. The value runs the other way: Chandra's
  1,449,766 closes the printed 1,523,167 exactly.
* **Tallow 1897, New Zealand 209,874 -> 299,874**, and BOTH engines were
  wrong (200,874 / 209,874). Grand total less Foreign total requires 1,406,365
  from the British section; with New South Wales 695,473 and Canada 1,358 the
  members reach 1,316,365, exactly 90,000 short. The value column agrees
  independently — 285,083 / 299,874 = GBP0.951/cwt, the rate every other
  Australasian row carries, where 209,874 would price New Zealand tallow at
  GBP1.36 against New South Wales's 0.95.
* **Palm 1878, 161,074 -> 461,074** — the repair queued above, now applied.
* **Flax and linseed 1899, Bengal 593,023 -> 897,423.** The printed British
  total less Gibraltar, Bombay and Canada leaves 897,423; the printed British
  VALUE total less the same three leaves 1,688,072, which is Chandra's value
  exactly while Infinity's is wrong.

### 4. The palm-kernel line's anchor was never missing, only differently worded

`Nuts And Kernels — Commonly Used For Expressing Oil Therefrom` — palm
kernels, copra and ground nuts, GBP18.3M — had origins in all 28 years and an
anchor of zero, so nothing about it was checkable. The abstract prints the
same line as `Nuts and Kernels: For expressing Oil therefrom` (34 years) and
as `Nuts, For expressing Oil therefrom` (1893-97). The arithmetic settles it:
the T1 series equals the origin sum **to the digit** in 1873, 1877-79,
1882-85 and 1887, and within ten tons in 1888-90.

Folding it in paid for itself immediately, because the parent/child de-dup
decides against the anchor: 1876 went 1.94 -> 0.88 as duplicated parent rows
were dropped.

### 5. The 1883-87 abstract printed the whole OILS section under a NUTS AND KERNELS head

…and the 1893+ five-year country tables did it again, so every `Nuts And
Kernels — <oil article>` label is a second copy of an `Oil — <same article>`
line. Checked pair by pair, they do not all say the same thing — which is why
the scoping note's "verify before folding" was right:

* **Animal** and **Chemical, Essential Or Perfumed**: 1883-87 T1 is the oil
  line's T1 to the digit and 1893-96 repeats origins the oil already has, but
  1897-99 the oil label has nothing and the stale one does. Folded, scoped to
  1897-99.
* **Turpentine**: pure duplication, no recovery. Dropped.
* **Coco-Nut**: NOT folded. Its 1894-99 origins run 1.3-2.3M cwt against
  coconut oil's ~200k, so whatever they are they are not that oil.

## Still open, with the evidence

1. **The T1 for flax and linseed 1899 is wrong and there is no way to fix it.**
   as_1899 prints 1,708,887; tn_1901 prints 1,798,887; the country block's own
   grand total is 1,798,857 and both its section totals close. So the year now
   reads 1.05, and the 1.05 is the anchor's error. **There is no override path
   for a T1 cell** — `reconcile.py` has no manual-adjudication input, the way
   `country_obs` has `manual_rows.csv`. That gap is worth closing; it will not
   be the only anchor with a broken digit.
2. **Flax and linseed 1880 reads 1.060** now that the southern-ports row is
   counted. The row belongs there, so the year carries a separate ~100,000-
   quarter error elsewhere: candidates are `bengal and burmah` 664,741,
   `russia` 534,956 and `bombay and scinde` 239,472, all round-100,000 away
   from a plausible neighbour.
3. **`Nuts And Kernels — Commonly Used…` 1894 reads 0.079** — 5,907 tons
   against 75,102. That is a lost table, not a digit. 1886 reads 0.291, 1874
   0.493, 1891 0.789; 1872 is still double-counted at 1.751; and 1881 has a
   printed origin table with no T1 line in either engine.
4. **`Oil — Oil Seed Cakes` stops in 1891 while its T1 runs to 1896**, and
   `Oil Seed Cake — Linseed Cake` / `Oil-Seed Cake — Cotton Cake` start in
   1892. That is an era split — one aggregate line becoming named sub-sorts —
   and it needs the sugar treatment (printed parent + siblings), NOT a merge.
   1890 reads 1.23 as well.
5. **`Oil — Olive` 1884 and 1885 have no origins at all** and 1894-96, 1899
   have origins with no anchor. `Nuts And Kernels — Olive` 1893-97 is a
   candidate carrier but its 1894 (35,553) does not match olive's own 26,332,
   so it needs the print, not arithmetic.
6. **`Seeds — Unenumerated, For Expressing Oil Therefrom` runs 0.48-0.73
   through the 1870s** with four blank years — the most systematically short
   series left in the family.
7. **The margarine/butterine cluster is split across four labels**
   (`Butterine` 1886 only, `Butterine (Margarine)` 1887 only, `Butter —
   Margarine…` 1893-99 reading 0.08 in 1893, `Lard — Imitation Lard…`). One
   printed line renamed twice; the sugar era-label method applies.
8. **`Nuts And Kernels` (plain, GBP12.2M)** carries 1893-97 "origins" of
   840,131 to 28,295,329 TONS — junk from some other table under a stale head
   — beside a T1 for 1887-91 that duplicates the palm-kernel line's. Its real
   content needs separating before either half is usable.
9. **Tallow 1897-99 still carries ~13,000 cwt of intruders** (Channel Islands,
   a second United States row, Peru, Spain) belonging to the TAR and following
   tables in the same Infinity glue block — the round-9 group-repair class.

## A caution about the metrics themselves

`scripts/validate_gold.py` is **not deterministic**. Three consecutive runs on
identical data gave match 510 / 529 / 517 and national-exact 630 / 653 / 639,
because `build_crosswalk` re-resolves ambiguous name matches each run. Judge
changes on `reconcile_baseline.py` and `validate_gold_numeric.py`, which are
stable. Over this session the stable pair went from **34.5% to 36.6% of GBP
within 0.1% of T1 and 51.5% to 53.6% within 5%**, with under-counted
commodity-years 325 -> 289.

## Continued the same day: the anchors, the era labels, and 1884-85

The first half of the review fixed what the origins were doing. The second
half turned out to be about everything else — anchors that were wrong,
labels that were the same line twice, and two whole years that had gone
missing behind a garbled group head.

### Tier 1 can be wrong, and now it can be told so

`country_obs` has had `reference/manual_rows.csv` from the start. Tier 1 had
nothing, so a provably wrong national total dragged its year's ratio forever
and made every commodity measured against it read as broken. Two turned up in
one afternoon, so it is a mechanism now: **`reference/manual_t1.csv`**,
applied in `reconcile.py` after the cross-volume vote, matched on the TOKEN
SIGNATURE of group+article (the same line comes through as `" Flax or
Linseed`, `„ Flax or Linseed`, `Oil Seed Cake - - - - -`; a literal key would
go stale on the next re-parse). Overridden rows carry `manual` in `volumes`,
and a rule matching nothing is reported by name.

* **Oil seed cake 1890, 229,616 -> 282,616 Tons.** The vote picked 229,616
  because two late printings carry it; the three volumes nearest the year all
  print 282,616 and the origin table sums to 282,582 — thirty-four tons from
  one figure, fifty-three thousand from the other. 1.231 -> 1.000.
* **Flax and linseed 1899, 1,708,887 -> 1,798,887 Quarters**, and this one is
  exact three ways: the Foreign members sum to their printed 780,265; with
  Bengal at 898,023 the British members come to 1,018,622; and their sum is
  tn_1901's printed national total to the digit. as_1899 misread the
  ten-thousands digit of the national line AND the hundreds digit of the
  British subtotal, and **the two errors hid each other** — taking its
  subtotal at face value (which is what I did first) gives a Bengal 600 short
  and a year that never closes.

### 'GIL' is OIL, and 1884-85 lost the whole section

Every oil read 0.00 origins in 1884 AND 1885 while 1883 and 1886 both closed
at 1.00. The tables were never missing; they were under a group nobody looked
for. as_1884's group is **`GIL`** — OIL with the O read as G — carrying 100
rows and all eleven articles. as_1885's is **`Fish`**, which is not a garble:
the printed line is `Oil: Fish, Train or Blubber`, so the parser kept `Fish`
as the sticky group for everything below it.

The identification is arithmetic, not typographic. Olive 1884's block total
is 17,213 Tuns — olive oil's national total to the digit. Animal 1885 is
121,498 cwt against a printed 121,498. `GIL` is a global alias (it appears in
one volume, on oil articles only); `Fish` is folded label by label, because
`Fish` is a real group in as_1874/84/88.

  Oil — Animal   1884 0.00 -> 1.00, 1885 0.00 -> 1.00
  Oil — Olive    1884 0.00 -> 1.00, 1885 0.00 -> 1.14
  Oil — Coco-Nut 1884 0.00 -> 1.00
  Oil — Seed     1884 0.00 -> 0.92, 1885 0.00 -> 1.00

### One line, six labels: the butter substitutes

`Butterine` (1886) becomes `Butterine (Margarine)` after the Margarine Act
1887 and `Margarine (including all kinds of Artificial or Imitation Butter)`
in the 1890s. The payload carried it as six commodities, four of them
anchor-only. The sixth was a signature accident: `…of Imitation Butter` and
`…of Artificial or Imitation Butter` differ by one word.

Folded INTO `Margarine` rather than out of it, because its cells are the
better ones where they overlap. Two digit repairs finished it, both the same
**8-read-as-5** as lard 1885 and flax 1899 — 1886 Holland 335,328 -> 835,328
and 1899 Holland 597,806 -> 897,806. **GBP46.0M, closing in every year
1886-99.** `Oleo-Margarine` stays separate (it is the beef-fat raw material,
not the butter substitute) and now closes in all eight of its years.

### Where the family stands

| commodity | closing years 1872-99 |
|---|---|
| `Butter` GBP325.7M | **28 of 28** |
| `Lard` GBP69.6M | **28 of 28** |
| `Margarine` GBP46.0M | **14 of 14** |
| `Seeds — Rape` GBP23.1M | **20 of 20** |
| `Tallow And Stearine` GBP61.2M | 27, 1889 alone |
| `Seeds — Clover And Grass` GBP19.8M | 27, 1874 alone |
| `Seeds — Flax Or Linseed` GBP148.2M | 26, 1874 and 1880 |
| `Oil — Palm` GBP111.9M | 26, 1882 and 1887 |
| `Oil — Turpentine` GBP13.2M | 25 of 28 |
| `Oil — Coco-Nut` GBP8.2M | 17 of 21 |
| `Oil — Olive` GBP24.3M | 15 of 21 |

Payload within 0.1% of T1 **34.5% -> 36.8%** of GBP over the session, within
5% **51.5% -> 53.7%**; under-counted commodity-years 325 -> 289.

### Still open, revised

1. **`Oil — Oil Seed Cakes` 1892-96 is an ERA SPLIT, not a hole.** The
   printed identity is proven: `Linseed Cake` + `Cotton Cake` + `Of other
   sorts` = `Oil Seed Cake` exactly in 1894, 1895 and 1896 and within 30 in
   1893. The aggregate keeps a national line to 1896 while the country tables
   move to the sub-sorts in 1892, so the parent has no origin table of its
   own for five years. Do NOT merge parent into children (the sugar trap);
   the honest options are to synthesise the parent from its children the way
   the country-side roll-up does, or to mark it an era label.
2. **`Nuts And Kernels — Commonly Used…` 1894 reads 0.079** — 5,907 tons
   against 75,102, a lost table rather than a digit. 1874 0.49, 1886 0.29,
   1872 1.75.
3. **`Oil — Seed` runs 0.81-0.94 through the 1880s** and `Seeds —
   Unenumerated, For Expressing Oil Therefrom` has six 1870s years at
   0.48-0.73 whose two candidate tables are geographically disjoint — one
   Indian and Black Sea (and closing exactly in 1875), one European. Two
   different tables under one national total; merging them produces a number
   that is neither.
4. **Olive 1885 folds at 24,209 against a printed 21,227** because Chandra
   totals that block 24,204 where Infinity totals 21,201 — a live digit
   dispute the fold does not settle. Olive 1888/90/91 run 0.88-0.93.
5. **`Coco Nut` holds an 1885 table of 368,757** that is almost exactly TWICE
   coconut oil's printed 185,496 — a parent-plus-children double count.
6. **`Nuts And Kernels` (plain, GBP12.2M)** carries 1893-97 "origins" of
   840,131 to 28,295,329 TONS, junk from another table under a stale head,
   beside a T1 for 1887-91 that duplicates the palm-kernel line's.
7. **`Oil — Fish : Train Or Blubber` has no anchor in any year** and stops in
   1896; 1894 reads 0.44 against what anchor it has.
8. **Margarine 1899's VALUE column** exceeds its printed total by 19,492, and
   Germany at GBP4.29/cwt against Holland's 2.65 is the row to look at.
9. **Tallow 1897-99 still carries ~13,000 cwt of intruders** (Channel
   Islands, a second United States row, Peru, Spain) belonging to the TAR and
   following tables in the same Infinity glue block.

### The digit class this family kept producing

Four separate repairs this session were the same confusion — **a printed 8
read as 5** — and all four were caught the same way, by a printed subtotal on
the same page rather than by anything about the number itself:

| | reads | should be |
|---|---|---|
| Lard 1885, United States | 500,406 | 800,406 |
| Flax and linseed 1899, Bengal | 593,023 | 898,023 |
| Butterine 1886, Holland | 335,328 | 835,328 |
| Margarine 1899, Holland | 597,806 | 897,806 |

Worth a detector: **a member row whose value/quantity ratio is 1.5x or more
off its own block's rate, where adding 300,000 or 500,000 to the quantity
closes the block's printed total.**
