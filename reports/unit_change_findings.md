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
