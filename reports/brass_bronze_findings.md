# Brass and bronze: a duplicate commodity, and a −1 that is a gain

Worked 2026-08-01 (`/loop /next-defect`).
**exact01 3,532 → 3,531 (−1), denominator 9,515 → 9,511 (−4), zero true
regressions.**

## The gap and what it actually was

Bracketed-gap rank 8: `Brass And Bronze Manufactures` 1893-1895, £1.47M, three
years at 0.00 between 1892 and 1896 at 1.00.

There was no missing table. **Two payload nodes carried the same commodity with
identical Tier-1 anchors** for those years — 18,639 / 22,311 / 32,221:

| | anchors | 1893-95 |
|---|---|---|
| `Brass And Bronze Manufactures` | 1892-1896 | **no countries** |
| `Brass, Bronze, And Metal Bronzed Or Lacquered, }Manufactures Of` | 1893-1900 | **closes to the digit** |

The second is the printed heading, carrying an OCR `}` before *Manufactures*;
the first is a shortened form. So the "hole" was an artifact of the split: the
data existed and closed, under the other name.

## Folded into the printed name, scoped to 1892

Direction: into the printed heading, not the shortened one. Scope: **1892
only** — because both nodes hold country cells for **1896** (40,850 each), and
an unscoped fold doubles that year to 81,700. 1892 is the only year the target
lacks.

The surviving node, renamed to drop the `}`:

| 1892 | 1893 | 1894 | 1895 | 1896 | 1897 | 1898 |
|---|---|---|---|---|---|---|
| exact01 | exact01 | exact01 | exact01 | exact01 | exact01 | exact01 |

**Seven consecutive years, every one closing**, where before there were two
nodes, thirteen anchor-years, eight closures and a three-year hole.

## Why the corpus count falls, and why that is right

`exact01` drops by one and the denominator by four. Both nodes carried 1896
and both closed it — that year was **counted twice**, and now it is counted
once. The 1893-95 anchors in the shortened node were duplicates of the printed
node's and leave with it.

This is the same arithmetic recorded for opium: **a de-duplication makes the
headline worse while making the data better.** Nothing that closed has stopped
closing; a commodity that appeared twice now appears once. Reporting the −1
without the reason would be actively misleading, and reporting the seven-year
run without the −1 would be no better.

## Queued: two more glue nodes in the family

`Brass, Bronze, And Metal, Bronze And Lacquered` (country years 1872-84) and
`Brass, Bronze, And Metal Bronzed Orlacquered` (1875, 1880-82) both hold
countries and no anchor. They are the same commodity again, mis-spelled twice
more. They cannot be folded usefully yet: **the surviving node has no Tier-1
before 1892**, so their cells would land where nothing can check them. Finding
the pre-1892 anchors for this commodity is the prerequisite, and is a separate
piece of work.
