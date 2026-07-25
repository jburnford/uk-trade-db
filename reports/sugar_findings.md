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
