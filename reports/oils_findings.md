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

## Third pass, same day: the region headers and the unit that was two units

### The phantom-region class, and why 1894 read 0.079

`Nuts And Kernels — Commonly Used For Expressing Oil Therefrom` read **0.079**
for 1894 — 5,907 tons against a printed 75,102. Neither a digit nor a lost
page: the whole table was in the parse, split across three phantom "articles"
that are region headers absorbed as article names (`West Africa`, `India`,
`East Coast of Africa`), leaving a four-row European fragment carrying the
commodity's own label.

It closes at three levels once reassembled, which is what makes the
identification certain rather than plausible:

    foreign members   16,745  = printed Foreign TOTAL
    British members   58,357  = printed British TOTAL
    16,745 + 58,357 = 75,102  = printed grand total AND the national line

Same class found and repaired in **1886** (a header absorbed as `India`, and
three-level closure at 24,262 / 28,632 / 52,894) and **1891** (a header
absorbed as `West Africa`, 12,465 tons, closing at 13,452 + 49,478 = 62,930).

  1894  0.079 -> 0.986   (5 origins -> 23: Lagos 26,324, Sierra Leone 5,511,
                          the Niger Protectorate 4,527, the Philippines 6,765)
  1891  0.789 -> 0.981
  1886  0.291 -> 0.696 on the map, and the payload sums to 52,894 EXACTLY

1886 needed one extra one-row repair: the table prints West Africa TWICE,
16,067 tons foreign and 13,834 British, and the OCR lost the qualifier from
both, so the two rows collided on one country key and the British one was
dropped as a duplicate.

**A scan for place-name articles under `NUTS AND KERNELS` is the cheap way to
find the rest of this class** — it also turns up as_1883, as_1893, as_1895,
as_1897 and as_1898, not all of which are defects (1893 and 1895 already
close, so their segments are reaching the commodity another way).

### Tun and Ton are one unit

`Oil — Olive` is printed in TUNS and the two engines alternate almost year by
year — Ton in 1872, Tun in 1873, Ton in 1874 — so half the origins never
shared a unit key with the commodity's own Tier-1 line and the quantity axis
dropped them silently. `heal_units` cannot see it: it folds a country's
minority unit into its dominant one, and this split is by YEAR across every
country at once, so no country has a minority.

u and o are the OCR pair and no article in these tables is printed in both,
so within ONE commodity the two spellings are the same unit. Folded to
whichever is better attested, anchor included, once over the raw signatures
and again after curation (a curation fold is exactly how a Tun commodity
acquires Ton cells). **80 folds, 31 commodity-years better and ZERO worse.**

  Oil — Olive   1882-93 from nodata or 0.06-0.12 to 1.00; the series now
                closes in 20 of its 21 measurable years, 1885 alone
  Oil — Seed    7 closing years -> 13, after folding `Oil — Seed Oil, Of All
                Kinds` (the same line pre-1880: its 1878 origins are 12,863
                tuns, the target's printed 1878 total to the digit)

### Where the family stands at the end of the session

| commodity | closing years |
|---|---|
| `Butter` GBP325.7M | **28 of 28** |
| `Lard` GBP69.6M | **28 of 28** |
| `Margarine` GBP46.0M | **14 of 14** |
| `Seeds — Rape` GBP23.1M | **20 of 20** |
| `Oil-Seed Cake — Cotton Cake` GBP4.3M | **5 of 5** |
| `Tallow And Stearine` GBP61.2M | 27, 1889 alone |
| `Seeds — Clover And Grass` GBP19.8M | 27, 1874 alone |
| `Seeds — Flax Or Linseed` GBP148.2M | 26, 1874 and 1880 |
| `Oil — Palm` GBP111.9M | 26, 1882 and 1887 |
| `Oil — Turpentine` GBP13.2M | 25 of 28 |
| `Oil — Animal` GBP4.5M | 21 of 21 in span |
| `Oil — Olive` GBP24.3M | **20 of 21**, 1885 alone |
| `Oil — Coco-Nut` GBP8.2M | 17 of 21 |
| `Oil — Seed` GBP13.9M | 13 of 16 |

Payload closure over the whole session: **34.5% -> 37.0% of GBP within 0.1%
of T1, 51.5% -> 54.0% within 5%**; unflagged map commodities 160 -> 166.

### Still open at the close

1. **`Nuts And Kernels — Commonly Used…` 1872-1884 runs 0.88-0.94** with 3-7
   origins a year — the same missing-segment shape as 1886/91/94 but with no
   place-name article to find it by. 1872 reads 1.751 and 1875 1.527 (the
   European block at as_1872 seq 745-751 and the West African at 1214-1222 do
   not sum to the 27,848 anchor, so at least one belongs elsewhere); 1874
   reads 0.493.
2. **`Oil — Fish : Train Or Blubber` reads exactly 0.50 in 1894, 1895 and
   1896** — newly visible, because the Tun/Ton fold gave it anchors it did not
   have. Half of something, three years running, is a missing section.
3. **`Oil — Oil Seed Cakes` 1892-96 is an ERA SPLIT, not a hole** — identity
   proven (`Linseed` + `Cotton` + `Of other sorts` = the aggregate exactly in
   1894-96). Needs a decision, not a repair.
4. **`Seeds — Unenumerated, For Expressing Oil Therefrom`**: six 1870s years
   at 0.48-0.73 whose two candidate tables are geographically disjoint.
5. **Olive 1885 at 1.14** — Chandra totals the block 24,204 where Infinity
   totals 21,201.
6. **The map's parent/child de-dup can only choose parent-or-children**, never
   keep-both, so 1886 kernels shows 0.696 where the payload closes at 1.000.
7. Flax 1880 (1.06, a ~100,000-quarter digit), palm 1882/1887, tallow 1889,
   `Coco Nut` 1885's doubled table, margarine 1899's value column, and the
   ~13,000 cwt of TAR-block intruders in tallow 1897-99.

## Fourth pass: building the instruments that see what closure cannot

The previous three passes repaired what the closure test could find. Asked
how confident I was that any given fats-and-oils commodity is 95% right, the
answer was no — because closure had four proven blind spots and every one of
them had produced a defect in this family in a single day. This pass builds
an instrument for each blind spot, and then measures the family with them.

### 1. The anchor itself — `scripts/anchor_disagreement.py`

Closure measures a country table against its printed national total, so a
wrong anchor is invisible to it: the table can be perfect and read 0.81, or
be missing a section and read 1.000. The 1893+ Abstract prints each year up
to five times and both engines read every printing, so a national total can
have ten independent readings; `reconcile.py` votes and keeps one.

This keeps the rest. **2,889 of 11,285 quantity series-years (25.6%) have
disagreeing readings, and 4,068 of 11,331 value series-years (35.9%).** Most
are one garbled printing outvoted eight to one. The queue is the 21 where the
payload's origin sum closes on a **losing** candidate:

| year | line | vote | origins say | GBP |
|---|---|---|---|---|
| 1884 | `silk \| raw` | 4,322,702 | **4,522,702** | 3.3M |
| 1894 | `tobacco unmanufactured` | 57,781,317 | **87,781,317** | 2.5M |
| 1881 | `oil \| coco nut` | 218,412 | **248,412** | 370k |
| 1899 | `bottles` | 1,206,959 | **1,266,959** | 528k |

Every one is a single digit, and the country block's own arithmetic lands on
the loser to the digit. This is the report that would have found oil seed
cake 1890 and flax 1899 without anyone noticing them by hand.

### 2. The value column — `scripts/value_closure.py`

Every block prints two columns and two printed totals and only one had ever
been tested. The national value line was sitting in `consensus`, used as a
sort key and nothing else. It now rides on the `§TOTAL` cell's fourth
element through `build_viz_payload` and `build_map_slim`, which puts value
closure in exactly the curated, de-duplicated space quantity closure lives
in.

    quantity   22.2% of commodity-years within 0.1%, 30.4% within 5%
    value      25.1% within 0.1%, 33.9% within 5%   (8,163 with an anchor)

The two columns are independent tests of the same block, so the signal is
where they **disagree**: 113 commodity-years close to the digit on quantity
and fail on value, 48 the other way round. Those are single-column digit
errors and `reports/value_closure.csv` names them.

### 3. The relabelled block — `scripts/cross_engine_labels.py`

**This is the one that matters most, because arithmetic cannot reach it.**
Relabelling preserves sums: the 1870s palm oil tables had every quantity
right, every label one row out, and closed against their printed total.

So the detector uses the second reading rather than the sum. For each block
in both keys it aligns the two readings twice — once on the sequence of
numbers, once on the sequence of countries — and flags the blocks where the
numbers line up at one offset and the labels at another. **83 blocks
corpus-wide, GBP338M; 15 in this family.**

Two things had to be got right for the verdict to mean anything:

- **The third voice must be cross-engine, not just cross-volume.** A parser
  that takes the country column one row out on a table shape does it in
  every volume printing that shape, so "as_1898's Chandra reading agrees
  with as_1897's Chandra reading" is not a second opinion. Scored properly,
  21 blocks have an independent verdict, **11 are engine-systematic
  disagreements no vote can settle, and 51 are printed once** — everything
  before 1893. For those the vote is structurally unable to help.
- **Segment arithmetic settles the single-printing case.** The engines have
  different ROW SETS, not merely different labels, so the one whose members
  add up to the printed segment total read the right rows. That decides 62
  of the 83.

### 4. The misread digit — `scripts/digit_repair_candidates.py`

The proposed instrument was a unit-price outlier detector. It turned out a
stronger one was available, because the same page prints the answer:

    delta = printed TOTAL - sum(members)
    if a member's figure + delta differs from what was read in exactly ONE
    digit position, that member is the misread row and delta is the digit

Corroboration in order of worth: **the other engine already prints the
repaired number** for that line (then it is not a hypothesis about a digit,
it is a reading the vote lost); the repaired row's unit price moves towards
its own block's rate; the digit pair is one these tables confuse. Peer
agreement outranks uniqueness — butter 1889 has four members sitting one
digit from closing, and only Russia's 8,393 is printed anywhere.

Two traps, both now handled and both found by getting them wrong first:

- The peer lookup must be scoped to the same **article**, not the same
  volume. Unscoped, a five-cwt coincidence in the tar table counted as
  corroboration for a seed-oil row: nine false positives out of 34.
- When the member sum is **itself** one digit from the printed total, the
  TOTAL may be the error instead. Margarine 1898 is either France 9,000
  short or the total 9,000 long; only the within-block price test separates
  them (France at GBP3.48/cwt against a block rate of 2.68 is the outlier,
  so the member is wrong). Those rows are flagged, never applied on closure
  alone.

Corpus-wide: 24,435 blocks, 50,809 arithmetic possibilities, 3,811 either
unique or printed by the other engine, **547 corroborated and still shipping
the misreading.**

### What was repaired

Twenty-five one-digit cells in this family, each closing its block exactly,
each printed by the other engine, each still shipping the wrong number.
The two that close open items:

    tallow 1889   Australasia   481,169 -> 431,169
        British segment then sums to its printed 456,242 to the digit, and
        787,789 + 456,242 = the printed grand total 1,244,031. Tallow 1889
        was the one year of twenty-eight that did not close.
    linseed cake 1894  France        943 ->     343
        closes the foreign segment at 179,714 exactly; GBP1.92/ton against a
        block running 6.0-7.1 was impossible anyway.

And the whole of **`OIL | Olive` 1874**, ten rows, reconstructed. Chandra
lost the leading France label, so every country carried the line above's
figures — Italy was given Spain's 7,683 tuns, Austrian Territories Italy's
9,728 — and the last data row, 253, landed on the TOTAL label. That is
precisely why the block still summed and why no closure test ever flinched.

The reconstruction is fixed by arithmetic, not by preferring an engine. With
Infinity's labels, Chandra's Spain value (328,464) and Chandra's last
quantity (253), **both** printed columns close to the digit:

    France 159 / 9,029        Portugal 503 / 20,963
    Spain 7,683 / 328,464     Italy 9,728 / 467,089
    Austrian Terr. 311 / 13,412   Greece 554 / 23,397
    Tripoli and Tunis 937 / 38,679  Morocco 1,781 / 72,142
    Malta 811 / 34,193        Other Countries 253 / 10,093
    ------------------------------------------------------
    22,720 tuns   GBP1,017,461   = both printed totals, exactly

Each engine had exactly one wrong number and neither had the labels wrong
twice.

### The honest confidence number — `reports/oils_confidence.md`

Generated by `scripts/family_confidence.py`, measured on `map_slim.json`
(the shipped, de-duplicated file — judging tallow on the raw payload reads
1.4-1.8 through the 1890s purely because `Australasia` and `Victoria` are
both still present there), with years that have no origin table at all
counted separately rather than as failures.

**Of 452 fats-and-oils commodity-years with an origin table, both printed
columns close to the digit in 216 — 48%.** Quantity alone closes in 65%,
value alone in 65%. At the looser 5% tolerance earlier sessions quoted:
quantity 90%, both columns 74%.

That is the number to quote, and it is lower than the family's headline
looked. Two columns closing on the same block are two independent tests, and
it is the strongest statement available without the page image. Per
commodity the spread is wide and worth reading: `Seeds — Rape` 17/20,
`Tallow And Stearine` 20/28, `Butter` 15/28, `Oil — Palm` 7/28,
`Nuts And Kernels — Commonly Used…` 2/27.

### Still open after the fourth pass

1. **The 51 label-slipped blocks printed once**, where each engine is
   self-consistent and segment arithmetic does not separate them. These are
   the page-image queue, and they are the reason a confidence figure above
   the mid-80s cannot be claimed for the 1870s and 1880s from internal
   evidence alone.
2. **`Nuts And Kernels — Commonly Used For Expressing Oil Therefrom` closes
   in 2 of 27 years** — the worst in the family by far, and the five
   `NUTS AND KERNELS | Seed` blocks in as_1898 are all label-slipped by two
   rows with Infinity's row set closing.
3. **Olive 1891 Italy's value** — 174,266 where 474,266 closes the block
   exactly and the price test is decisive (GBP15.16/tun against a block
   running 34-41). Not applied because the other engine reads it the same
   way, so it is a genuine misprint-or-misread rather than a lost vote.
   Same shape: lard 1890 US value, margarine 1898 France quantity.
4. **Butter 1899 Victoria's value**, GBP1,651,338 on 211,744 cwt = 7.80
   against a block at 4.9, with the British segment GBP599,987 over its
   printed total. No single-digit repair closes it.
5. **Margarine 1899's value column** is still 19,492 over, and no unique
   one-digit repair exists — consistent with the note already in
   `manual_rows.csv`.
6. Everything on the third pass's open list that these instruments do not
   touch: the oil-seed-cake era split, `Oil — Fish : Train Or Blubber`
   reading exactly 0.50 in 1894-96, the two disjoint tables under
   `Seeds — Unenumerated`, olive 1885, the map's parent-or-children de-dup.

## Fifth pass: what the confidence card exposed downstream of the data

The card from the fourth pass is measured on `map_slim.json` — the file the
public map ships — and comparing it against the payload turned out to be an
instrument in its own right. Three of the family's worst-looking commodities
were not defective at all; the pipeline between the payload and the map was
losing them.

### The map could only choose parent OR children

The parent/child de-duplication weighs a parent line against its breakdown
and drops one side. That is right when the two are the same trade counted
twice, and wrong when the printed table carries a parent that is a genuine
REMAINDER beside children that do not cover it. Forced into a binary choice,
the pass was throwing away whichever side was smaller — **on years that were
already exactly right**:

    tea 1885-92        1.000 -> 0.96
    silk raw 1886-92   1.000 -> 0.79-0.91
    Oil — Palm         eleven years 1.000 -> 0.976-0.993

86 exact commodity-years broken against 289 fixed. The exhaustive search now
has three options per group — drop the parent, drop the children, or keep
both — which is safe for exactly the reason the anchor became the arbiter
here in the first place: a genuine duplicate kept twice overshoots the
Tier-1 total and loses. **Broken 86 -> 5, fixed 289 -> 301.** Palm oil goes
from 7 of 28 years closing on both columns to 19.

### `Oil — Fish : Train Or Blubber` was not missing half of anything

It read **exactly 0.500 in 1894, 1895 and 1896**, and the fourth pass wrote
that up as "half of something three years running, a missing section". It
was not. `fold_tun_ton` appended the folded unit's cells without checking
for a year the keep-unit already had, so the national line — printed under
both spellings in one year — left TWO `§TOTAL` cells, and `build_map_slim`
**added them**. A doubled anchor halves a commodity and trips no flag.

The fold now skips colliding years and the slim anchor takes one reading per
year rather than their sum. **0 of 3 years closing -> 3 of 3.**

### A value anchor that is really the quantity line

Making the value column a first-class metric exposed the class hiding behind
it never having been tested. Some printings put the quantity figure in the
abstract's VALUE column and the cross-volume vote copies it faithfully:
`Seeds — Flax Or Linseed` 1885 has a value line of 2,046,352 which IS its
quantity line, in six volumes, while the origins come to GBP4.4M at 2.1 a
quarter. Left in, that is worse than an untested column — it reports a sound
block as 2.14x its printed total.

Detected on the commodity's own median price, so goods that genuinely cost
about a pound a unit are never touched, and **dropped rather than failed**:
the year has no value test, which is not the same as failing one. 68 anchors
across 33 commodities -> `reports/quantity_as_value.csv`. Two years already
written up as data defects were not: sugar unrefined 1888 at 0.678 and flax
1874 at 2.79 were both bad anchors.

### Export tables riding in as imports — `scripts/detect_flow_leakage.py`

Butter 1882's import block closes to the digit at its printed 2,169,717 cwt,
and a second block of six origins — Portugal, Gibraltar, Malta, South
Africa, Brazil — rides in beside it and adds 1.3% to a commodity that was
already complete. Those six are the UK export table. The proof is not a
judgement about which countries look like destinations (that screen was
tried on tallow and tripped on Chile and the Channel Islands, which is where
British tallow came from); it is arithmetic:

    the intruding block's own printed Total   31,640 cwt / GBP219,726
    the export_uk Tier-1 line, butter 1882    31,640 cwt / GBP219,726

**318 blocks corpus-wide whose printed Total is an export or re-export
national line, 222 matching on both columns, 217 with cells reaching
country_year_final — 2,039 cells of export data shown as imports.** In this
family: butter in eleven years, tallow in four, lard in one.

`integrate_sources` now rejects such a block from the gap-fill sources, with
the guard that makes it safe: only when NONE of the block's Totals is the
import line. Some volumes print all three tables under one lost heading —
butter 1880 has three Total rows, 2,326,305 import, 31,408 export, 43,125
re-export — and dropping that block would take the import table with it.
Those stay, logged for per-cell work. 3,306 cells rejected across 369
blocks; **butter 1882, 1883 and 1885 now close on both columns**.

### A manual replace could not reach a sub-entry

`V.cnorm('Australasia : Victoria')` is `'australasia'`, so a manual row
naming Victoria never matched the cell it was written to replace, and the
hand-adjudicated figure was ADDED BESIDE the broken one. Step 4 now tests
the sub half on its own name.

The row in question: butter 1899 Victoria, GBP1,651,338 on 211,744 cwt =
7.80, in a British section whose value members exceed their printed
2,972,430 by 599,987 and whose other rows run 4.4-5.0. Victoria's own price
series reads 5.16, 4.93, 4.62, 4.97, 4.80 for 1893-97; 1,051,338 gives 4.97.
A printed 0 read as 6. Stated plainly, **it does not close to the digit** —
the segment is still 13 over and the quantity column separately 30 short, so
one more small error remains on that page. Value 1.035 -> 0.9999.

### Where the family stands after the fifth pass

    quantity closes   73% of measurable commodity-years  (was 65%)
    value closes      75%                                (was 65%)
    BOTH columns      54% of 446 commodity-years         (was 48%)

Corpus-wide on the shipped map, both columns close in 49.7% of the 3,790
commodity-years that have origins at all, up from 47.3%.

### Still open

Everything from the fourth pass except train oil and the palm shortfall,
plus:

1. **The mixed export blocks** — butter 1872-81 and 1886, tallow 1872/74/77/
   80, lard 1883: one lost heading over all three tables, so the export rows
   have to come out cell by cell. `reports/flow_leakage.csv` lists them with
   the member rows.
2. **Two years the de-dup still breaks, both outside this family**: Indigo
   1882 loses Bengal (60,888 of 95,272) and `Bark — Peruvian` 1881 loses
   United States Of Colombia (70,944 of 125,358) to some other filter in the
   slim build — not the parent/child pass.
3. **Butter 1899's residual 13** on value and 30 on quantity, and
   **Victoria 1897 is in the final table twice**, 169,975 and 169,075 cwt
   against one value of 816,399.
4. `Oil — Chemical, Essential, Or Perfumed` 1874 at 0.780 and
   `Oil Seed Cake — Linseed Cake` 1899 at 0.961.

## Sixth pass: the vote itself, and the instruments' own queue

### `ver[0]` was deciding which printing to believe

Coco-nut oil 1881 is printed 248,412 cwt in as_1881, as_1883, as_1884 and
as_1885 and 218,412 in as_1882, and the origin table sums to 248,412
exactly. It shipped at 218,412 — the commodity read 1.137 for the year and
`anchor_disagreement.py` flagged it on the first run.

The cause was in the vote. Tier B took `ver[0]`, the first cell in list
order, whenever there were verified readings without a verified majority.
"Verified" means the two OCR engines agreed on that printing, which says
nothing about whether the printing is right, so two internally consistent
volumes can disagree and the tiebreak was **nothing at all**. Among verified
readings it now takes the one the corpus supports most.

**224 of 51,268 consensus rows change**, and the largest are a class this
session had been patching downstream — a value line that is really the
quantity line. Wool 1888's "value" was 634,943,685, the pounds of wool, and
is now GBP25,849,918; tobacco unmanufactured 1888 46,679,898 -> GBP1,464,557;
woollen yarn 1884 -> GBP1,881,295; pepper 1888 -> GBP917,800. All four were in
`reports/quantity_as_value.csv`, which drops from 68 anchors to 56. Fixing it
in the vote beats suppressing it in the map. Coco-nut oil 1881 goes to 1.000
with no override needed.

### Eight anchors the country tables settle

`reports/anchor_disagreements.csv` listed 20 years where the origin sum lands
on a LOSING reading. Applied the eight where it lands **exactly** and the two
readings are **one digit apart** — the class this corpus produces:

| year | line | vote | printed elsewhere | origins |
|---|---|---|---|---|
| 1884 | silk, raw | 4,322,702 | **4,522,702** | 4,522,702 |
| 1880 | yeast, dried | 268,123 | **208,123** | 208,123 |
| 1874 | yeast, dried | 163,811 | **153,811** | 153,811 |
| 1899 | bottles | 1,206,959 | **1,266,959** | 1,266,959 |
| 1872 | gutta percha, raw | 41,597 | **44,597** | 44,597 |
| 1897 | brimstone | 449,028 | **419,028** | 419,028 |
| 1898 | moss litter | 89,449 | **80,449** | 80,449 |
| 1898 | snuff | 6,502 | **6,902** | 6,902 |

All eight close after the override. Left alone: four cotton-yarn years and
jute 1886, where the two candidates differ by 2-20x rather than a digit — a
different line, not a misread one — and three where the origins land near but
not on the loser (tobacco 1894, cured sardines 1894, paper hangings 1890).

Note what this queue is: the vote fix above CAUSED two of these (yeast dried
1874 and 1880 changed hands), and the instrument caught them on the next run.
That is the loop working.

### Bengal is not foreign to indigo

The profile-outlier suppression asks whether an origin looks like it belongs
to a commodity, and it exists for years with no anchor. Where there was one
it still fired, and the origin most likely to look unfamiliar is the one that
dominates a single year: **Bengal was being suppressed from Indigo 1882**
(60,888 tons of a printed 95,272) and **United States Of Colombia from
Peruvian bark 1881** (70,944 of 125,358). The archetypal source of each. The
cell is now kept whenever dropping it moves the year away from its printed
total. Indigo closes in all eleven of its years, Peruvian bark in eight of
ten, and 167 suppressions still stand.

### The mixed export blocks, closed by their own arithmetic

The fifth pass left these deliberately: one lost heading over the import,
export and re-export tables, so rejecting the block would take the import
table with it. It only would if the import table were not parsed elsewhere,
and it usually is — butter 1880's primary parse closes on its printed
2,326,305 cwt. **A gap-filler with no gap to fill can only be contributing
the export rows.** Gated on the primary block summing EXACTLY to the import
national line, which makes it self-validating. Rejected cells 3,306 ->
4,385; zero years went from exact to not-exact.

### One thing tried and reverted

A row that equals the SUM OF ITS SIBLINGS is a Total row whatever it is
called, and that would catch the ones the exact anchor test just misses — the
1872 nuts-and-kernels block ends with 'West Coast of Africa' 27,818 tons
against a printed 27,848, 0.1% away and therefore not caught, while its eight
sub-entries come to 27,577 and the commodity reads 1.75x its own total.
Implemented, measured, **reverted**: it cost two exact years (Jute 1894 and
1895) for one gained, because dropping a cell changes what the parent/child
pass sees afterwards and its exhaustive choice flips. The defect is real and
still open; the rule as written is not the way to fix it.

### Where the family and the corpus stand

    fats and oils   quantity 74%, value 75%, BOTH 55% of 446 years
    shipped map     quantity 64.3%, BOTH 50.4% of 3,791 years
                    (from 60.8% / 47.3% at the start of the fifth pass)

## Seventh pass: coverage, and ranking the rest by money

### 77 family-years had no value test for a filing accident

Essential oils are quantified under `Oil | Chemical, Essential, and
Perfumed` and valued under a **groupless** `Chemical, Essential, and
Perfumed` in almost every year of the corpus. The value anchor was keyed on
a signature built from the group, so the two halves of one printed line
could only meet when both copies happened to carry it.

Every value line is now keyed on its ARTICLE tokens as well, restricted to
article-years carrying one distinct value so a generic article printed under
several commodities is never paired.

    value-measurable commodity-years   3,497 -> 3,649
    value exact                        2,222 -> 2,312
    BOTH columns exact                 1,909 -> 1,989

Three checks that this pairs lines rather than pairing anything: no year went
from value-exact to not-exact, no already-anchored year had its anchor
changed, and **90 of the 152 newly-paired years close to the digit** — which
a wrong pairing does not do. In this family: essential oils 4/23 -> 11/23,
olive 13/21 -> 17/21, turpentine 15/28 -> 19/28, coco-nut 8/19 -> 12/19.

### The remaining error, ranked by money

204 failing commodity-years hold **GBP3.35M of error between them, out of
GBP999M — 0.34% of the family**. That is the number worth quoting alongside
the closure counts, and it reorders the work: the commodity with the worst
ratio is not where the money is.

| GBP at stake | commodity | year | quantity off by |
|---|---|---|---|
| 463,870 | `Oil — Turpentine` | 1897 | 3.0% |
| 300,103 | `Oil — Olive` | 1891 | — (value only) |
| 294,287 | `Seeds — Flax Or Linseed` | 1892 | 0.9% |
| 248,946 | `Nuts And Kernels — Commonly Used…` | 1872 | 75% |
| 216,732 | `Tallow And Stearine` | 1899 | 0.4% |
| 164,223 | `Butter` | 1884 | — (value only) |
| 159,097 | `Oil — Palm` | 1886 | — (value only) |

`Oil Seed Cake — Linseed Cake` scores 1 of 7 and is **not** in this list: six
of its seven years are within 0.8% and only 1899 has a real gap. The strict
0.1% bar overstates it, which is worth knowing before spending a session on
it.

### Eleven cells repaired, and one guardrail learned by breaking it

Applied where the block's arithmetic and the within-block price agree —
olive 1891 Italy GBP174,266 -> 474,266 (the block 300,000 short, GBP15.16 a
tun against a block running 34-41), lard 1890 United States, and nine
smaller. Skipped by the same test: five whose repaired price moves AWAY from
the block rate, including a 500,000 cwt jump on margarine 1892's dominant
row.

**A block closing is not the same as the commodity-year closing.** Three of
the fourteen first applied made their year WORSE despite closing their own
printed segment exactly: margarine 1898's block is 9,000 cwt short and the
year was already summing to its national total, because another source
supplies those 9,000. Both cannot be right and the block arithmetic cannot
say which. Removed and queued. The rule is now in the detector's docstring —
after applying a batch, re-measure per commodity-year and keep only what did
not regress.

### Where the family stands

    quantity closes   74% of 446 commodity-years with origins
    value closes      76% of 419 with a value anchor
    BOTH columns      62%   (was 48% three passes ago)
    at 5% tolerance   quantity 94%, both columns 87%
    money still wrong GBP3.35M of GBP999M
