# Misfiled blocks: 140 nodata commodity-years whose data is parsed and filed elsewhere

**No metric gain this round.** exact01 held at 3,741. The round produced a
validated screen, a large confirmed target list, and one more instance of a trap
that has now caught three screens.

## The trap, caught before it did damage

The obvious way to build this screen is to ask the database which anchors have no
origin data. Done that way it reports **312 misfiled blocks** — `Tea` 1894-97
filed under `SPIRITS`, `Petroleum` under `PARAFFINE` and `PERFUMERY`, `Potatoes`
under `PORK`, `Rice` under `RAGS`. The stale group is alphabetically adjacent to
the true one every time, which is exactly the sticky-group signature, and the
blocks close their anchors to 1.0000.

**All of them are already fixed.** In the payload, Tea 1894-97 reads 1.0000,
Petroleum 1883-94 reads 1.0000, Potatoes and Rice likewise.
`build_viz_payload`'s country-cell sticky repair re-homes them; the database
keeps the stale group because the repair happens downstream of it.

This is the third screen to hit this — `detect_column_crossing.py` and
`detect_lost_vote.py` both measure `(article, year)` in the database, which can
span several payload nodes or be re-homed before the baseline sees it. **Any
DB-level screen must have its candidate list confirmed against the payload before
a single row is written.**

## The real list

Re-pointed at the payload's own nodata cells: of **960 reachable nodata
commodity-years**, **140 have a parsed block that closes their anchor to within
2%**. These are genuine — the commodity is empty in the payload, and an
independently printed anchor is closed by a block that is not attached to it.

| GBP/yr | commodity | year | ratio | filed under |
|---:|---|---|---:|---|
| 20,788,482 | `Corn And Grain — Wheat` | 1897-99 | 0.9999 / 0.9848 / 1.0029 | `CHEESE` |
| 3,948,661 | `Cork — Manufactured` | 1897, 1899 | 1.0000 | `CHEESE` |
| 3,471,234 | `Wheatmeal And Flour` | 1870, 1900 | 1.0000 / 0.9969 | `CORN AND GRAIN` |
| 3,221,763 | `Oil — Palm` | 1870 | 1.0000 | `METAL` |
| 3,135,713 | `Nuts And Kernels — Coco-Nut` | 1883, 1886, 1887 | 1.0000 | `OIL` |
| 2,002,384 | `Indigo` | 1870 | 1.0000 | `ICP` |
| 1,845,040 | `Slates` | 1899 | 1.0000 | `COTTON` |

The target group needs **no vote over labels** — it is the payload node's own
name. `Corn And Grain — Wheat` gives `CORN AND GRAIN`. That is what makes this
different from the two attempts in `reports/late_era_group_staleness.md`, both of
which derived the group from labels and both of which regressed.

## What did not work, and what is needed

46 `group_repairs.csv` rows were generated for the tightest cases (within 0.2%)
and applied. **They were inert** — `Corn And Grain — Wheat` 1897-99 and
`Nuts And Kernels — Coco-Nut` 1883-87 still read `nodata`, and the baseline moved
by −1. The rows were reverted rather than left in place asserting a fix that did
not happen.

`new_group` did not bind. The keying is the open question: the `article_group`
written must presumably match the source row exactly (a null group is not `''`),
`obs_source` distinguishes the two engines, and it is not yet established whether
`new_group` alone re-homes a row or whether the article must move with it.
**Settling that is the whole of the next round**, and the 140-row target list is
already computed and waiting.
