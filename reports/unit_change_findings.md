# When the volumes re-denominate a line (2026-07-26)

The Abstract does not keep one unit for a commodity's whole life. Jute is
printed in hundredweights to 1886 and in tons from the 1887 volume; flax and
hemp go the other way in 1893; boots, shoes and gloves move from pairs to dozen
pairs in 1878; coffee from pounds to hundredweights in 1874. The country tables
change with the national line.

Nothing in the pipeline knew that. `build_map_slim.py` picks one dominant unit
per commodity for the quantity axis and takes the anchor from the same unit —
which is right, and which silently discarded everything printed in the other
era. **Jute showed fifteen years with £2.5–4.5M of value a year and no tonnage
at all**, and its 1868–86 national totals went with them. A £161M commodity was
half unmeasured and carried no quality flag, because a year with no quantity and
no anchor trips nothing.

This came out of the wrong end of a mistake. The 2026-07-26 anchor pass flagged
jute as reading "exactly twice its anchor for thirteen consecutive years" and
called it the largest unexplained pattern it had found. That ratio is real but
it is a **payload-level** artefact — `British East Indies` 337,303 counted
beside its own drill-down `Bengal` 336,728 — and the map's parent/child
de-duplication already removes it: `map_slim` closes at 0.9982–1.0000 for those
same years. Chasing it is what surfaced the fifteen blank ones.

## The fix

Converting is arithmetic, not estimation: twenty hundredweight **are** a ton.
`build_map_slim` now carries a table of definitional factors (20 cwt/ton,
112 lb/cwt, 2240 lb/ton, 12 per dozen) and applies them on both sides — origin
cells and the national total — with three guards that each earned their place by
breaking something first.

**Only years the dominant unit does not reach.** A year printing both units is a
garbled header, not a regime change. Jute 1883 holds 922 junk tons beside 7.4M
hundredweights; converting it would have double-counted, so it is left exactly
as it was.

**The same guard on both sides.** Filling the anchor for a mixed year while
declining to convert its origins turns a year that merely had no anchor into one
reading 0.0025 of one. Jute 1883 again.

**The label is not evidence — decide by the numbers, per year.** Two commodities
print `Cwt` headers over figures that were always tons: `Metal — Unenumerated,
Unwrought` reads 2,699 for 1892 under "Cwt" beside 2,469 for 1896 under "Ton",
with origins of 2,878 tons. Dividing by twenty invented a 21× over-count out of
a commodity that had no flag at all. And the verdict has to be **per year**, not
per unit, because an era header outlives the change it marks: coffee's "Lbs"
national line runs 127–192 million for 1866–72 and then prints 1,637,523 for
1873, which is already hundredweights under a stale header. One verdict for the
whole unit gets that year wrong by a factor of 112 whichever way it falls.

Each fill year is judged against its own origin table; years with no origin
table follow the majority verdict of the years that have one; and where nothing
supports either reading, the year is left unanchored and logged rather than
mis-scaled.

## What it recovered

| | commodities | years |
|---|---|---|
| origin-cell eras converted into the shown unit | 12 | 44 |
| anchor years recovered | 13 | 68 |
| …of which the unit *label* was wrong and the figures were kept as printed | 6 | 13 |
| rejected — no origin table in any of those years to judge it by | 16 | — |

`reports/unit_era_changes.csv` names every one.

**Jute goes from twelve anchored years to twenty-seven**, closing at 0.98–1.00
in every year 1872–1898. Only 1899 (0.8952) and the mixed 1883 remain.

| commodity | GBP | before | after |
|---|---|---|---|
| `Jute` | 161.1M | 12 anchored years, 15 with no quantity | 27 anchored, all but two closing |
| `Coffee — Raw` | 278.1M | 1872 unmeasured | 1872 at 0.9816, 1873 at 0.9839 |
| `Flax, Dressed Or Undressed` | 57.4M | `underanchor` | `underanchor` cleared — the "shortfall" was its own tonnage |
| `Hemp — Dressed Or Undressed` | 40.2M | `nooverlap` (never measured) | measurable, and it closes |
| `Hemp — Unenumerated Vegetable Substances…` | 1.4M | `nooverlap` | measurable, and it **over**-counts |
| `Boots And Shoes` / `Leather Manufactures — Gloves` | 61M | pairs-era anchors dropped | 9 and 5 years recovered |

The map's unflagged count is unchanged at 165 of 1,031. That is the honest
outcome: two commodities lost a flag they should never have carried, one gained
a real one, and one moved from "never measured" to "measured and wrong", which
is progress of the kind that does not show up in a headline number.

## Still open

**Jute 1899 reads 0.8952** (256,784 tons against 286,839) in a series that
closes everywhere else.

**Jute 1883 is unresolved.** Its origins are 7,383,990 with no printed unit at
all, plus 922 tons of junk and 116 hundredweights. The junk tons are what makes
it a "mixed" year and keep the guards from touching it. Fixing it means settling
the unit on the unlabelled block, not converting anything.

**Sixteen era anchors were rejected outright** because no year in the foreign
unit has an origin table to judge the reading by. They are listed in
`unit_era_changes.csv` and are recoverable the moment those origin tables are.

**The payload still holds both units.** This fix lives in the map layer, where
unit normalisation already lived; `exports/viz_payload.json` deliberately keeps
the printed units apart, so `reconcile_baseline.py` still cannot score these
years. Moving the conversion upstream would change the baseline's universe and
is a larger decision.

---

# Jute 1899: the anchor was wrong, not the origins (2026-07-26)

After the unit-era conversion, jute closed 0.98–1.00 in every year 1872–1898 and
**0.8952 in 1899** — 256,784 tons of origins against an anchor of 286,839. A
series that closes for twenty-seven consecutive years and misses by 10% in the
twenty-eighth has a locatable defect, and it turned out to be in the anchor.

## The country block is right and says 256,839

`as_1899`'s jute block closes at both of its levels:

```
  foreign   4,527 + 354 + 185 + 121 + 295 + 90 + 55  =   5,627   = its printed foreign TOTAL
            (the value column too: 51,010, exactly)
  BEI       75 + 575 + 250,429 + 115 + 18            = 251,212   = the printed BEI row
                                    5,627 + 251,212  = 256,839
```

The 1898 block in the same volume has the identical shape and closes at all
three levels against its own anchor — `1,190 + 360,947 = 362,137` = T1 — so
there is no third segment in 1899 either, and nothing is missing.

## Both wrong figures are one digit away from 256,839

```
  256,839   the block's components
  258,839   the block's printed grand TOTAL      6 -> 8
  286,839   the abstract, and the anchor         5 -> 8
```

Two independent single-digit misreadings of the same number. For 286,839 to be
correct instead, the British East Indies row **and all five of its children**
would have to be wrong by a consistent 30,000 — six printed figures failing
together in one direction.

`tn_1901` printing 286,839 as well is not independent confirmation; the later
volumes copy the earlier ones, which is exactly why the standing rule is that
closure outranks print-majority. The 5/8 confusion is this corpus's commonest
digit error — lard 1885, flax 1899, butterine 1886, margarine 1899 and oxen 1899
were all the same pair.

Fixed in `reference/manual_t1.csv`. **Jute 1899 0.8952 → 0.9997, and no jute
year is now off by more than 2% anywhere in 1872–1899.**

## Two corrections to earlier notes

**The queued item was right and my re-validation was wrong.** In iteration 6 of
this session I re-checked jute against the **payload**, which keeps British East
Indies beside its own drill-down Bengal by design, and read 1.7712 for 1899 and
1.0000 for 1883. Both are artifacts of that double count. Jute — like the other
eleven unit-converted commodities — must be judged on `map_slim`'s own `t1`,
never the payload anchor. That is the fourth trap in the E&H notes and it caught
me even having written it down.

**`reconcile_baseline` cannot score this fix**, for the same structural reason it
could not score copper 1888: jute's payload view double-counts, so it sits in the
`over` bucket either way. The corpus baseline is unchanged at 38.3% / 55.9%.
