# Sugar imports — what the tables actually say (2026-07-24)

The sugar family had been deferred three times, and for a good reason: forty-
odd labels, four eras of printed classification, and a Total-versus-sub-sort
distinction that a careless merge would double-count. It is now unified. What
made it tractable was not more labels but two arithmetic identities the printed
volumes supply for free:

```
    beetroot + cane and other sorts   =  unrefined, total
    in lumps and loaves + other sorts, including candy  =  refined, total
```

Both close **to the digit** for 1893–96 against national totals printed on
different pages from the origin tables. That is the whole proof. Every fold
below either satisfies one of those identities or matches an independently
printed national total year by year; nothing here was fitted.

## First, a unit that was hiding half the family

The 1893–1900 national totals for beetroot, cane, glucose and lumps-and-loaves
were printed under a column header the OCR read as **`Cnts`**, not `Cwts`. The
map's anchor has to be one unit, so those series were invisible: four of the
largest sugar lines had origin tables with nothing to check them against, while
their national totals sat one key away.

`Sugar — Other Sorts, Including Candy` prints both spellings, and where it does
they are the same figure to the digit (1896: 12,131,275 either way). That
settles it. Eight more misread headers were found the same way — `Gt Hunds`
beside `Great Hundred` on Eggs, `Doz Prs` beside `Dozen Pairs` on Gloves — and
folded. Eggs became one continuous series 1866–1900 instead of two.

Nothing else in this document was possible before that fix.

## The unrefined line: one commodity under seven labels

| label | held | years |
|---|---|---|
| `Sugar — Unrefined Of All Kinds` | origins | 1875–81 |
| `Sugar — Of All Kinds` | origins | 1882 |
| `Sugar — Unrefined; Beetroot : Total Of` | origins | 1883–84 |
| `Spices — Sugar Unrefined : Total Of` | origins | 1886 |
| `Sugar — Unrefined, Total` | origins | 1887–99 |
| `Sugar — Raw` | national total | 1868–81 |
| `Sugar — Unrefined` | national total | 1878–91 |
| `Unrefined` | national total | 1892–96 |

Five era labels for the origins, three for the total, and — this is the point —
the origin spans do not overlap at all. Folded together the merged commodity
tracks the independently printed total at **1.00 in seventeen of the eighteen
years 1875–92**, which is what a correct merge of two independent witnesses
looks like.

The heads are worth noticing: `Spices — …` is glue from a neighbouring table,
and `Unrefined; Beetroot : Total Of` is the fused-line pattern the teak work
named — the `Beetroot` is the *previous* printed sub-sort bleeding in, and the
line is the Total. The figures decide it, not the words: 20,517 against a
printed total of 20,367 is the total, not beetroot's 10,154.

### A digit dispute settled by closure

`Sugar — Raw` and `Sugar — Unrefined` both print 1878–81 and agree exactly on
three of the four years. In 1881 they read **15,651,383** and **18,651,383**
thousandths — a single leading digit. The origin tables, printed elsewhere, sum
to 18,651,383. So `Sugar — Raw` carries the OCR error, and the fold order puts
`Sugar — Unrefined` first so the correct figure wins. This is the closure rule
doing exactly what it is for; no page image was needed.

## The refined line, and why the sub-sorts stay separate

`Sugar — Refined : Total Of` now runs 1872–99 with a national total 1866–96 and
sits at 1.00 for twenty of twenty-two checkable years. The two sub-sorts —
lumps and loaves, and other sorts including candy — are kept as their own
commodities, because that is how the source prints them and because their sum
*is* the total. Merging a sub-sort into its own family total is the one move
that would have quietly doubled the family, and it is the reason this job was
deferred rather than guessed at.

`Sugar — In Lumps And Loaves` gained its national total (1893–1900) and now
reads 1.00 in all six checkable years.

## Molasses and glucose: four one-year labels with a head glued on

Molasses lost single years to labels whose head came from whatever was printed
above them. Each is confirmed by the printed molasses total for that year, to
the digit:

```
  Cards, Playing — Molasses                      1872   696,615  =  696,615
  Sugarrefined, … Including Candy — Molasses     1883   372,683  =  372,683
  Sugar, Unrefined : Total Of — Molasses         1888   345,894  =  345,894
```

With those and the de-headed `Molasses` national total (1866–68, 1892–1900),
molasses now runs 1872–99 at **1.00 in twenty-two of twenty-five years**.

Glucose gained a national total back to 1866 from two earlier era labels, the
older of which supplies its 1872–73 origins — again equal to the printed
totals for those years.

## Queued, with the evidence

**Cane and other sorts is still over its anchor.** The merged cane line reads
1.2–1.9× the national total for 1893–99. Some is the parent/child double-count
the map already removes; the rest is not yet explained, and the commodity ships
flagged `overanchor` rather than clean. Its 1880, 1881, 1883 and 1888 origin
years are fragments (1883 reads 383,000 cwt where closure wants ~10,200,000).

**`Sugar — Unrefined : Cane, And Other Sorts` 1895: British East Indies and
Australasia both read 2,894,873 cwt for £1,525,112** — the same two numbers to
the digit. One of the two is a mis-aligned second parse. Australasia's series
is continuous either side (1894 and 1896 both present); British East Indies
appears in no other year. Not dropped, because with two labelled cells there is
no rule that says which to keep — logged in
`reports/reparsed_origin_cells.csv`, which now carries 66 such pairs across the
dataset (Rice 1895 Bengal/Burmah, Rye 1893 Russia/Germany — adjacent rows in
the printed country column, every time).

**`Glucose (Solid Or Liquid)` is not folded.** Its 1874–87 origins equal the
printed glucose totals exactly and would fill a fourteen-year gap. But its
1895–99 origins carry an Australasian block — Australasia 1,804,229 cwt, New
South Wales, Queensland, Victoria, New Zealand — against a national total of
1,315,866, in a commodity whose 1894 table has no Australasian entry at all.
That is a glued block from a neighbouring table. Folding would trade a clean
commodity for a flagged one. It becomes safe once the block is removed at
source.

**`Spices — Molasses` 1885 reads 431,323 cwt** against a printed 1885 total of
392,875 — but against 1886's 430,490 it is within 0.2%. Either the label or the
year is wrong and the figures cannot say which, so it is not folded.

**`Sugar — Total Unrefined Of All Kinds` is not folded.** Its 1873 is plausible
but its 1874 reads 3,616,142 cwt against a printed total of 14,130,000 — a
quarter of the year. Folding would replace a gap with a wrong number.

**`Sugar`** (£29.7M) is a transposed table: its origin column is a list of
commodities — Refined, Unrefined, Glucose, Tea, Molasses — with real countries
mixed in. **`Sugar — In Blocks, Ingots, Bars, Or Slabs`** is a copper sub-sort
name under a sugar head, shipping from Java and Chile at once. Both are left
for the chimera work.

## Where the family stands

| commodity | GBP | flags |
|---|---|---|
| `Sugar — Unrefined, Total` | 365.2M | *(none)* |
| `Sugar — Refined : Total Of` | 229.5M | *(none)* |
| `Sugar — Other Sorts, Including Candy` | 183.7M | *(none)* |
| `Sugar — Unrefined : Cane, And Other Sorts` | 111.8M | `overanchor` |
| `Sugar — Unrefined : Beetroot` | 95.9M | *(none)* |
| `Sugar — In Lumps And Loaves` | 37.4M | *(none)* |
| `Sugar — Molasses` | 5.2M | *(none)* |
| `Sugar — Glucose` | 4.2M | *(none)* |

Seven of the eight carry no quality flag at all, including the two largest
commodities on the entire map. Before this work the unrefined and refined
totals had no national total to be checked against and were split five ways
each.

---

# The careful review (2026-07-25)

The user asked for a careful look at sugar after the July 24 unification:
*"the data looks OK, so I'm not seeing massive failures, but there is still
gaps."* That reading was right about the big lines and right about the gaps.
It was the gaps that hid the failures.

`reports/sugar_review_scope.md` framed three hypotheses. One was wrong in an
instructive way, one was wrong outright, and the third was right.

## The anchor gap was not a missing label. It was a missing question.

The scope guessed that beetroot, cane, lumps and other-sorts carried an
anchor for only six or seven of their twenty years because the 1880s
national totals were hiding under some other spelling. They are not hiding.
**The Abstract did not publish a beet/cane split, or a lumps/other-sorts
split, before 1893.** Until then it printed two lines — unrefined, and
refined and candy — and the country tables went finer than the summary did.

So the four sub-sorts have no anchor of their own for the 1880s and never
will. What they have is better: the printed parent, and each other.

```
    beetroot + cane and other sorts               =  unrefined, total
    in lumps and loaves + other sorts, incl candy =  refined, total
```

Measured that way, against a total printed on a different page, **eleven of
the eighteen years 1882-1899 were wrong** and nobody could see it, because
every one of them was scored `noanchor` and skipped. The identity is not a
weaker check than an anchor. It is a stronger one: it constrains two series
at once, and it decides which of them is short.

## What was actually wrong

**Britain was importing refined sugar from Malta, Gibraltar and Algeria.**
Eight UK export tables and two re-export tables sat in the import payload
under `SUGAR|Refined and Candy`, 1875-1886. Each block carries its own
printed Total and each Total equals the export (or re-export) national total
for refined sugar to the digit — 972,263 in 1875, 909,177 in 1881,
1,294,311 in 1884, 994,353 in 1885 — while the refined *import* total those
years is three to four times larger. In 1884 and 1885 they were the only
origin table `Sugar — Refined : Total Of` had, which is why it read 0.28 and
0.14 of its anchor.

Two more re-export tables did the same to the unrefined side. The 1880 and
1881 volumes each print a cane block and a beetroot block whose Totals sum,
**in both columns**, to the re-export national total for unrefined sugar
(298,661 + 14,974 = 313,635 cwt and GBP353,685 + GBP20,758 = GBP374,443).
Those two tables were the whole of the map's beetroot series before 1881 —
a beet-sugar trade of 2,812 cwt supplied by Denmark, Portugal, Italy and the
Azores.

**A repair from round 8 had come to point the wrong way.** It relabelled the
1884 and 1885 `Refined; Total of` per-country tables *into* `Other Sorts,
including Candy` and superseded the real other-sorts tables as "fragments",
on the then-reasonable belief that candy was the total-semantics series. The
July 24 unification disproved that — lumps + other sorts equals the printed
refined total exactly in 1883 and in 1886-98 — but nobody went back. They
were never fragments: 1884 prints TOTAL 2,344,098 and 2,344,098 + lumps
1,919,775 = 4,263,873, the printed refined total, with all ten origins
closing individually. This is the cost of a repair that is right about the
arithmetic and wrong about the label, and the only thing that catches it is
re-deriving the identity after the taxonomy changes.

**Beetroot was shipped from Brazil and Peru.** In 1883 the beetroot block
ends at Portugal with a printed TOTAL of 8,245,307, which its six members
give exactly; the parser ran through that TOTAL and swallowed the last nine
rows of the cane table. Meanwhile the cane table's middle twenty-seven
origins — Java 3,396,782, the British West Indies 1,656,217, British Guiana,
Madras, the Philippines — sat in a phantom commodity named `East Coast of
Africa`, the first country of the block absorbed as the article. Cane showed
the eight European rows alone, 382,622 of a 12,121,320 year.

**Hong Kong was the third largest source of cane sugar in 1887.** The
British-Possessions half lost its first label, so every value sat one label
up and the last fell off: 'Hong Kong' carried the British East Indies'
828,547 and British Guiana's own 1,382,217 vanished. Both engines had a
copy; the vote took the broken one, and marked all seven rows tier C, which
is the system saying *I do not trust this* in a place nobody was looking.

The rest, in one line each: 1888's cane table was split across two OCR group
heads and only the British half reached the series; 1890's whole sugar
section parsed with no unit column and the quantity axis dropped what the
unit heal could not rescue, including the British East Indies' 710,736;
1891 counted the British-Possessions subtotal as an origin named
'Australasia' and then added the drill-downs on top of it.

## Where the family stands now

| year | beet + cane / printed | | year | lumps + other / printed |
|---|---|---|---|---|
| 1882 | 1.0000 | | 1883 | 1.0000 |
| 1883 | 0.9994 *(was 0.517)* | | 1884 | 1.0000 *(was 1.450)* |
| 1884 | 0.9998 | | 1885 | 1.0000 *(was 1.253)* |
| 1885 | 0.9990 | | 1886-88 | 1.0000 |
| 1886 | 0.9955 | | 1889-91 | 0.990-1.000 |
| 1887 | 1.0000 *(was 0.923)* | | 1893-98 | 0.9996-1.0002 |
| 1888 | 1.0000 *(was 0.545)* | | 1899 | 0.9965 *(was 0.852)* |
| 1889 | 0.9997 | | | |
| 1890 | 0.9995 *(was 0.953)* | | | |
| 1891 | 0.9991 *(was 1.138)* | | | |
| 1893-99 | 0.996-1.015 | | | |

`Sugar — Unrefined, Total` now has origins in every year 1873 and 1875-1899.
1873 came back because the volume prints that table in four duty classes and
a Total, and the classes close on the Total country by country; 1885 came
back from under a Spices head. 1872 and 1874 stay blank — no origin block
for either exists in either engine.

| commodity | GBP | flags |
|---|---|---|
| `Sugar — Unrefined, Total` | 395.7M | `gapyears` (1872, 1874) |
| `Sugar — Refined : Total Of` | 225.4M | *(none)* |
| `Sugar — Other Sorts, Including Candy` | 180.0M | *(none)* |
| `Sugar — Unrefined : Cane, And Other Sorts` | 125.9M | *(none)* |
| `Sugar — Unrefined : Beetroot` | 94.1M | *(none)* |
| `Sugar — In Lumps And Loaves` | 43.6M | *(none)* |
| `Sugar — Molasses` | 5.2M | `gapyears` |
| `Sugar — Glucose` | 4.2M | `gapyears` |

`Sugar — Refined, Or Rendered By Any Process Equal Thereto : In Lumps And
Loaves` is gone: not the complement its coverage suggested but the same
printed line under the long heading, agreeing country for country to the
digit in every overlapping year. It was the sole carrier of 1882, 1884 and
1899, so it was folded rather than dropped, and 1899 — where the short label
has nothing — is what took the refined family from 0.852 to 0.997.

## Still open, with the evidence

**1898 unrefined, 0.9599.** The only year of the identity that does not
close. Beetroot 9,265,761 against a t1 of 9,565,811; cane 4,838,421 against
5,127,095. Both short, which smells like one lost block rather than a slip.

**`Sugar — Unrefined, Total` runs 1.04-1.11 of its anchor in 1895, 1897-99**
while its own sub-sorts close. The parent series is over, not the children;
suspect a drill-down counted beside its parent.

**The succades line is eight labels for one printed heading**, and folding
them is not yet safe. `Succades` (GBP1.58M, 1888-94), `Succades (Including
All Fruits And Vegetables Preserved In Sugar)`, `Succades (Including Fruits
And Vegetables Pre- Served In Sugar)`, `Spirits — Succades And
Confectionery…`, `Spirits — Suggades…`, `Straw — Succades…`, `Sugar
(Including All Fruits And Vegetables Preserved In Sugar)` and `Succades —
From British East Indies` tile 1872-1895 with almost no overlap, and the
1893 block closes on the printed `Fruits and Vegetables preserved in Sugar`
total to the digit (141,496). But a naive merge reads 1.50 of that total in
1892, 1.58 in 1894 and **exactly 2.00 in 1895** — the 1892 and 1894 blocks
count a British-East-Indies parent beside its own sub-entries, and 1895 is
simply two copies. Fix the double counts first, then fold. The heads
(STATIONERY, STRAW, COALS, SPIRITS) are all glue.

**`Sugar — Molasses, Treacle, And Syrup` (1875-81) and `— Treacle, Syrup,
And Glucose` (1883-84)** are era spellings of the molasses line and tile the
gaps in `Sugar — Molasses`. Not folded: neither has a unit, neither has an
anchor, and the 1883-84 spelling bundles glucose, which is its own
commodity. The molasses anchor exists for both spans — this is checkable and
was simply not reached.

**`Spices — Molasses` 1885** reads 431,323 cwt against a printed 1885
molasses total of 392,875 but is within 0.2% of 1886's 430,490. Either the
label or the year is wrong and the figures cannot say which. Unchanged from
the July 24 note.

**`Fruit — Unenumerated : Preserved Without Sugar`** carries 1883 (747,798)
and 1895 (45,856,283) with no unit, against a `Preserved without Sugar`
national total printed in Lbs 1892-96. `Preserved Without Sugar` (1882,
14,948,516 Lb) is the same line de-headed. Both need the unit settled first.

**`Sugar — Complete` 1899** was dropped, but its block is worth recovering:
Holland 190,713/GBP34,000, Belgium 575,461/GBP576,931, France
1,104,303/GBP852,057, printed TOTAL 1,002,878/GBP1,498,201. The value column
nearly closes (1,496,558) and the quantity column does not, so the block is
row-slipped and its true article is unidentified.

## The method note worth keeping

A commodity with no anchor is not a commodity that cannot be checked. It is
a commodity nobody has checked. Every defect above lived in a year the
quality flags called `noanchor`, and every one of them was decidable from
arithmetic already in the volume — a sibling sub-sort, a printed subtotal,
a parent total on another page, or the same table read by the other engine.
The reconciliation baseline barely moved across this whole review (34.1% to
34.5% of GBP within 0.1%) because it can only score commodity-years that
carry their own Tier-1 line. That is exactly why these survived.
