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

## Why the first attempt was inert, and the fix

46 `group_repairs.csv` rows were written for the tightest cases and changed
nothing. Reading the application code in `integrate_sources.py` settled it — two
separate keying mistakes:

```sql
WHERE volume = ? AND flow = ? AND article_group = ?
  AND article IS NOT DISTINCT FROM ? AND row_seq BETWEEN ? AND ?
```

1. `article_group` is matched by **equality**, so the literal source string is
   required — a `coalesce(article_group,'')` never matches. (No block in this
   corpus has a NULL group, so nothing is lost to that.)
2. The real one: the destination signature is
   `V.sig(f"{new_grp} {new_art}")`. **Leaving `new_article` blank produces a
   signature with no article tokens at all** — `CORN AND GRAIN` instead of
   `CORN AND GRAIN WHEAT` — so it matches no commodity. `new_group` alone does
   not re-home a row; the article has to travel with it.

With both corrected, 38 distinct blocks were written (one row per block, not per
year — the five-year layout interleaves the years across one seq span).

## The double-count that the seq range cannot avoid

Because the years interleave, a seq range selects **every** year in the block. For
a commodity that already has data in some of those years, the repair adds a second
copy: `Corn And Grain — Wheat` gained 1899 but drove 1895 to 1.33 and 1896 to 1.68.
There is no year field in `group_repairs.csv` and no seq range that isolates a
year, so the only honest control is to measure per commodity and drop the repairs
that do not pay. Five were dropped on that basis — Wheat, `Manures —
Unenumerated`, `Teeth, Elephants'…`, `Caoutchouc — Manufactures Of`,
`Oil — Coco-Nut`.

## Result

**35 cells better, 2 worse.**

```
exact01          3,741 -> 3,770   (+29)
                 39.3% -> 39.6%
GBP within 0.1%  53.6% -> 53.9%
```

Whole years recovered from `nodata`: `Cork — Manufactured` 1897/1899,
`Oil — Palm` 1870, `Nuts And Kernels — Coco-Nut` 1883/1886/1887,
`Nuts And Kernels — Seed` 1885/1886, and 25 more.

The two remaining regressions are mild and left in place with their cause known:
`Cork — Manufactured` 1895 (0.9906) and `Teeth, Elephants'…` 1879 (0.9708), both
`exact01` to `within5`.

## The `years` column (next round)

`group_repairs.csv` gained a **`years`** column and `integrate_sources.py` filters
the selected rows by it. Empty means every year in the range, so all 1,090
pre-existing rows behave exactly as before — verified as a no-op rebuild before
anything was written.

That removes the structural limit above. `Corn And Grain — Wheat` is the proof:
unscoped it gained 1899 and destroyed 1895 (1.33) and 1896 (1.68), and the repair
had to be abandoned. Scoped to `1897;1899` it recovers **1897 (0.9977), 1898
(0.9881) and 1899 (0.9995) with no effect on 1895-96 at all.**

21 further blocks were written year-scoped. Two whose commodity still netted
negative were dropped on measurement (`Caoutchouc — Manufactures Of`,
`Fruit — Raisins`) — the per-commodity check stays necessary, because re-homing a
block also removes rows from the *host* it was wrongly attached to, and that host
may have been relying on them.

**18 better, 2 worse. exact01 3,770 → 3,774; GBP within 0.1% 53.9% → 54.1%.**

Recovered: `Corn And Grain — Wheat` 1897-99, `Nuts And Kernels — Seed` 1884/1887,
`Tin — In Blocks, Ingots, Bars, Or Slabs` 1899 and 1886, `Skins, And Furs — Skins,
Unenumerated, Undressed` 1893, `Manures — Unenumerated` 1897/1898,
`Gum — Unenumerated` 1872, `Oil — Coco-Nut` 1898.

Two regressions left with their cause known: `Oil — Coco-Nut` 1881 (1.0451) and
1878 (1.1301).

## Still open

- The reachable payload-nodata pool has fallen from 960 to **451**, and only 28
  of those now have a closing block — the two-sided test has largely been worked
  out for the tight band. What remains in that pool needs a different instrument.
- The per-commodity net check cannot be skipped: a repair moves rows *out* of a
  host as well as *into* a target, and the host's own arithmetic can depend on
  them.
