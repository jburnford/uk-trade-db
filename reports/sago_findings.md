# Sago 1893: a British subtotal wearing a country's name, and a fold that is not yet worth making

Worked 2026-08-02 (`/loop /next-defect`), bracketed-gap rank 3, GBP 513k.
**`Sago` 1893 went from `nodata` to exactly 1.000000** — 611,506 of 611,506.

**exact01 3,567 → 3,568 (+1), within 5% 1,112 → 1,111, under 274 → 275,
denominator held at 9,464. Two cells changed — one better, one worse, and the
worse one is reported rather than hidden.**

## The table, and the row that had to come out

`as_1893` seq 2950-2957, parsed under the era wording `SAGO and Flour and Meal
thereof`:

| | members | printed |
|---|---|---|
| Foreign | Austrian Territories 3,900 + China 2,638 + Other Foreign 125 = **6,663** | **6,663** |
| British | Bombay 2,520 + Straits Settlements 602,323 = **604,843** | — |
| Grand | 6,663 + 604,843 = **611,506** | **611,506 = the Tier-1** |

**Seq 2956 is labelled `British East Indies` and carries 604,843 — the Total
from British Possessions, not a country.** `is_subtotal` recognises only labels
beginning `total`, so the repair ranges are split around it.

**Sixth instance of that class**: as_1875 `West Coast of Africa (Foreign)`,
as_1899 `Australasia`, as_1891 pepper's two, as_1882 hardwoods in the mirror
direction, and now this. It is also **why the era sibling read 1.0099 for 1893
instead of closing** — its copy counted the subtotal.

## The trade-off, stated plainly

The repair needed a `supersede` on the source label, because without it the
printed table sat in the corpus twice and the sibling node went from 1.0099 to
1.1158. With the supersede, `Sago, And Flour Or Meal Thereof` 1893 falls from
`within5` to `under` (0.2317).

**Neither reading was a real measurement.** The old 1.0099 double-counted part of
the British subtotal; what remains (141,686) is a **different, incomplete
printing** under the comma spelling `SAGO, AND FLOUR OR MEAL THEREOF`, which was
left alone. The net is +1 exact01 and one duplicate node's phantom figure
replaced by a visibly incomplete one.

## The fold, measured and deliberately not made

`Sago` and `Sago, And Flour Or Meal Thereof` are **one commodity in successive
era wordings** — identical anchors in all four overlapping years (1893 611,506;
1894 682,381; 1895 694,040; 1896 626,588) — and folding would give one
continuous 1866-1899 series and hand `Sago` its 1895 and 1896 origins.

**But an unscoped fold was measured at −1 exact01.** Both nodes hold 1894
origins from the same printed table with different OCR readings, and **only
`Sago`'s closes**: 682,381 = the Tier-1 exactly, against the sibling's 675,354
plus two extra countries (Holland 7, United States 2,054). Merged, 1894 becomes
684,442 / 682,381 = 1.0030 — `within5` instead of `exact01`.

**Resolve 1894 first — decide which of the two readings of the Straits
Settlements figure is right (679,798 or 670,726) and whether Holland and the
United States belong — then fold.** A year-scoped fold is not a way round it:
the curation fold pops the source node entirely and carries only the scoped
years, so it would discard the sibling's 1897-99, which are its own exact and
near-exact years.

## Still open

`Sago` 1866-1871 `nodata`, 1895 and 1896 `nodata` (both available in the sibling,
pending the fold).
