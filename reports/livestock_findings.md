# Live animals — the oxen series, and the glue block under it (2026-07-26)

Phase 0.3 of the corpus-wide plan asked what to do about the second apparent
duplicate pair: `Animals, Living — Oxen And Bulls` (£146M) and `Oxen And Bulls`
(£98M), scored 18% duplicates of each other. They are one printed line under
three group headings, one of which is wrong.

## The three headings

| country-table heading | years | what it is |
|---|---|---|
| `ANIMALS` | 1872–79 | the section head before it settled |
| `ANIMALS LIVING` / `ANIMALS, LIVING` | 1880–99 | the section head |
| `AMMUNITION` | 1893–98 | **a stale head** — see below |

The Abstract prints the national total under `Animals, Living : Oxen, Bulls,
Cows, and Calves` to 1895 and under a groupless `Oxen and Bulls` from 1894, so
the payload had the origin cells split across two commodities and the anchors
split across both.

## The sibling identity settles 1872–1892

Neither payload label had an anchor before 1893, and the flags said `noanchor`.
But the printed line those years is the **broad** one, and its members are all
in the corpus:

```
    oxen and bulls + cows + calves  =  oxen, bulls, cows, and calves
```

That closes **to the digit in fourteen of the twenty-one years 1872–1892**, and
every miss is locatable rather than mysterious:

- **1876, 1878, 1881, 1882 — `Cows` has no origin table at all.** The residuals
  are 58,520 / 29,384 / 34,056 / 45,052 head, which is what those four missing
  cow tables are worth. Nothing else in the pipeline reports them.
- 1874 short 3,300, 1879 short 1,600, **1891 short exactly 3,000** (the digit
  class), 1884 over by 20, 1886 over by 55.

So the merged 1872–92 origin series is independently confirmed in fourteen years
that no anchor could reach.

The identity also settles a Tier-1 dispute the vote got wrong. For 1893 the
broad line reads **340,015** in as_1893/94/95 and **340,045** in as_1896. The
members give 337,063 + 2,908 + 74 = **340,045**. as_1896 is right.

## The fold

`Animals, Living — Oxen And Bulls` was folded into `Oxen And Bulls`. The origin
spans are disjoint — 1872–79 in the target, 1880–99 in the source — so the fold
takes 1880–92 and 1899 whole, and the two labels' overlapping 1893–98 readings
of the same table agree (1893: both give 337,063, the printed total to the
digit).

The target keeps the fuller anchor (1894–1900, four volumes) and the better
reading of every disputed year:

- **1894 United States 381,657, not 581,657.** The wrong reading is a 5 for a 3.
  381,657 closes the printed 471,794 exactly with its own country set, and
  £6,758,843 over 381,657 head is £17.71 against a 1893–97 band of £17.1–18.8;
  over 581,657 head it is £11.62.
- 1896 558,425 and 1898 564,300, against printed totals of 558,361 and 564,290.

Merged closure for 1893–99: **1.0000, 1.0001, 1.0075, 1.0001, 0.9989, 1.0000,
1.0000.** One commodity, origins in every year 1872–1899, no quality flag; it
was `gapyears` before.

## 1899 Argentina: an 8 read as a 5

`ANIMALS, LIVING | Oxen and Bulls | Argentine Republic | 1899` was stored as
55,359 head. It is 85,359, proven three ways:

1. **The printed total closes exactly.** 320,054 + 91,376 + 85,359 + 518 + 125 =
   **497,432**, the 1899 `Oxen and Bulls` national total to the digit. As stored
   the year was 30,000 short.
2. **Unit price.** £1,392,543 over 55,359 head is **£25.15**, against Argentina's
   own £15.56 / 14.06 / 15.62 / 15.12 in 1895–98 and the United States and
   Canada at £17.26 and £16.89 in the same year. Over 85,359 head it is
   **£16.31** — back in band.
3. **The series.** 39,436 → 65,698 → 73,832 → 89,369 → 55,359 is a 38% collapse;
   85,359 is not.

Applied as `manual_rows` `replace=1`.

## Still open, with the evidence

**The `AMMUNITION` glue block is the root cause and is not repaired.** In
`as_1897` (obs `row_seq` 145–700) and `as_1898` (`row_seq` 152–698) the whole
`ANIMALS, LIVING` section is parsed under the preceding `ARMS AND AMMUNITION`
head: Oxen and Bulls, Cows, Calves, Sheep and Lambs, Swine, Stallions, Mares,
Geldings and Unenumerated, five years apiece in the comparative layout, with the
real arms articles resuming at seq 701 and 699. Only the oxen line has been
adjudicated. The others are duplicated in `country_year_final` exactly the same
way — `Cows` and `Calves` each appear twice for 1893–98, once under each head —
which is why the broad-line identity above reads 2.0 to 3.2 for those years
before the payload de-dup. The instrument is a `group_repairs` row per volume
with `new_group = ANIMALS, LIVING` and `supersede_years`, but it must be checked
line by line first: for oxen the stale-head copy is the **better** reading in
1894, 1896 and 1898 and superseding it wholesale would lose those.

**1893 US value understates by £3M.** The stale-head copy carries
£1,667,152 where the `ANIMALS, LIVING` copy carries £4,667,152 — a 4 read as a
1. The `ANIMALS, LIVING` set closes the printed 1893 value total exactly
(4,667,152 + 1,436,479 + 106,674 + 2,802 + 340 = **6,213,447**); the stale-head
set gives 3,213,147. The fold keeps the stale-head cell, so the shipped 1893
value is low. Not patched because its country key is itself junk — the parser
kept `On the Atlantic` with the parent lost — and a manual row on that key would
not survive a re-parse. Fix it with the group repair above.

**The four missing cow tables** (1876, 1878, 1881, 1882), worth 58,520 / 29,384
/ 34,056 / 45,052 head, each pinned to the digit by the identity residual.

**1891 is short by exactly 3,000** and 1874 by 3,300 on the same identity.

**`Oxen, Bulls, Cows, and Calves` 1893 should be 340,045, not 340,015.** Three
volumes print the wrong figure and one prints the right one; the members decide
it. A `manual_t1` candidate, low value — the broad line ships no origins.

**1895 is the one merged year over 0.1%** (416,445 against 413,337, +0.75%).
The `ANIMALS, LIVING` parse fuses the Channel Islands into Other British
Possessions — 1894's 153 is 117 + 36, 1895's 1,685 is 1,554 + 131 — so where
both parses survive the fold the Channel Islands is counted twice. Worth 131–140
head a year, plus an Australasian sub-entry pair in 1895.
