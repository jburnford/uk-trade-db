# Teak imports — what the tables actually say (2026-07-24)

Written after a careful read of every teak label. Two defects were repairable
by curation and are fixed; three are source-level and are queued here with the
evidence rather than patched.

## The commodity was split across five labels

| label | held |
|---|---|
| `Wood And Timber — Hewn, Teak` | the origins, 1873–1899, GBP19.8M, no anchor |
| `Wood And Timber — Teak` | the Tier-1 anchor, 1893–1900, plus origins 1872–1893 |
| `Wood And Timber — Hewn, Teak : Unenumerated` | **not teak at all** (see below) |
| `Wood And Timber:Not Sawn Or Split, Including Teak` | a 1866–70 category total |
| `Not Sawn Or Split, Including Teak` | the same total, one digit different |

The first two are one commodity under two era labels — teak is printed under
"Hewn" in the earlier volumes and as its own line later. Folded together, and
the merge validates itself: the origins now track the independently printed
national total at **1.02, 1.14, 1.00, 1.00, 1.00, 1.00, 1.00** for 1893–99.
Before the fold the map showed teak with an anchor covering 1893–1900 and
origins stopping in 1893 — an apparently well-measured commodity whose two
halves never met.

## `Hewn, Teak : Unenumerated` is not teak

Its origins are Canada 234,355, Russia 43,752, Sweden 36,734, Norway 32,225,
British Guiana 24,471 — the hewn softwood trade. Teak ships from Burma, Siam
and the Indian presidencies; none of it comes from Canada or Scandinavia.

This turned out to be a systematic class, not a one-off. In `<mode>, A : B`
the A is the previous printed sub-sort bleeding in and B is this line, and the
origin profile settles it every time:

| label | ships from | so it belongs to |
|---|---|---|
| `Hewn, Fir : Oak` | Germany, Canada, US, Russia | `— Oak` |
| `Hewn, Fir : Unenumerated` | Canada, British Guiana, Norway | `— Hewn, Unenumerated` |
| `Hewn, Teak : Unenumerated` | Canada, Russia, Sweden, Norway | `— Hewn, Unenumerated` |
| `Sawn, Fir : Unenumerated` | Sweden, Russia, Norway, US | `— Sawn, Unenumerated` |

All four folded. (The `Furniture, Hardwoods And Veneers : …` labels match the
pattern textually but not structurally — that family has its own twelve-label
tangle and is left alone.)

## Queued: 1873 is 4.6x its neighbours

1873 read 138,645 loads against ~30,000 either side. The excess is Canada
61,599, Sweden 10,487, Russia 8,349, Norway 7,103, United States 6,670,
British Guiana 1,267 — six origins that appear in **no other year** of teak's
whole span, and again the softwood profile. A block from a neighbouring table
was glued into teak's 1873 column.

The map now suppresses these (`scripts/detect_profile_outliers.py`, which
generalises the case: 137 commodity-years across the dataset), leaving 1873 at
43,170 loads. **The source tables still carry them.**

## Queued: country-shifted duplicate cells, 1875/1876/1884

The same quantity appears twice in one year — once under a plausible origin in
`Load`, once under a *different* origin with the unit lost:

```
1875   Bengal And Burmah  Load 30,515      Other Countries      ?  30,515
1876   Bengal And Burmah  Load 34,416      Straits Settlements  ?  34,416
1884   Bengal And Burmah  Load 35,498      Bombay               ?  35,498
1884   Siam               Load  4,784      Burmah               ?   4,784
1884   Bombay             Load    137      Bombay And           ?     137
```

A second parse of the same rows with the country column slipped by one. The
quantity side is unaffected (the map takes the dominant unit, `Load`) but the
**value side double-counts** those years. The `Load` copy is the reliable one.

## Queued: a one-digit disagreement in the 1866 total

Two labels carry the same 1866–70 category total and agree exactly on four of
the five years:

```
                                                   1866        1867 …
Wood And Timber:Not Sawn Or Split, Including Teak   1,485,093   1,223,686 …
Not Sawn Or Split, Including Teak                   1,185,093   1,223,686 …
```

1,4**8**5,093 against 1,1**8**5,093 — a single leading digit, 4 against 1, in
otherwise identical series. One of the two is an OCR error and the page image
decides which. Exactly the class the anomaly rounds handle; not guessed at
here.

## Also noted

- **1889 is missing entirely** — no origins and no anchor, in a series that is
  otherwise continuous 1872–1899.
- **1900** has an anchor (63,080 loads) but no origins; the origin tables end
  at 1899, so this is expected rather than a defect.
- **East Coast Of Africa, 6,319 loads in 1894** survives the profile test
  because the label recurs, but teak was not grown in East Africa. Probably a
  mislabel; too small to be worth a page check on its own.
