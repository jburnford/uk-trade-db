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

**The `AMMUNITION` glue block — worked 2026-07-26, and it was smaller than this
section first claimed.** In `as_1897` (obs `row_seq` 145–700) and `as_1898`
(`row_seq` 152–698) the whole `ANIMALS, LIVING` section is parsed under the
preceding `ARMS AND AMMUNITION` head: Oxen and Bulls, Cows, Calves, Sheep and
Lambs, Swine, Stallions, Mares, Geldings and Unenumerated, five years apiece in
the comparative layout, with the real arms articles resuming at seq 701 and 699.
Every line is therefore in `country_year_final` twice.

Measured line by line, the `ANIMALS, LIVING` copy is the better reading
everywhere except oxen: sheep closes 1.0000–1.0040 in every year 1893–99 while
the stale head runs 1.3054–1.4253; the three horse lines close 0.99–1.01 while
the stale head is **truncated** to 0.0004–0.65. But **the payload was already
absorbing that correctly** — `Cows`, `Calves`, `Mares`, `Geldings` and
`Animals, Living — Sheep And Lambs` all close at 0.99–1.01, because the
duplicate cells collide on `(country, unit, year)` and one copy is discarded.
The exposure was two labels that escaped as commodities of their own,
`Ammunition — Stallions` and `Ammunition — Swine`, whose article alone names no
attested commodity so the sticky-group repair could not re-home them. Both
dropped.

**A `group_repairs` relabel is the WRONG instrument here and this is worth
recording.** Relabelling the block to `ANIMALS, LIVING` with `supersede_years`
was tried and reverted: superseding removes the bad consensus copies, but the
repair's step-6 gap-fill then adds them straight back, because the stale-head
parse spells its countries differently (`United States of America : On the
Atlantic` against a plain name) so they miss the "already in consensus" guard.
Sheep went from 1.0040 to 1.4027 in 1894, swine from 1.0000 to 4.0000. Every one
of the seven lines got worse. Superseding *without* re-adding would need a
supersede-only row, which the schema has no way to express.

**1893 US value understates by £3M.** The stale-head copy carries
£1,667,152 where the `ANIMALS, LIVING` copy carries £4,667,152 — a 4 read as a
1. The `ANIMALS, LIVING` set closes the printed 1893 value total exactly
(4,667,152 + 1,436,479 + 106,674 + 2,802 + 340 = **6,213,447**); the stale-head
set gives 3,213,147. The fold keeps the stale-head cell, so the shipped 1893
value is low. Not patched because its country key is itself junk — the parser
kept `On the Atlantic` with the parent lost — and a manual row on that key would
not survive a re-parse. Fix it with the group repair above.

**Stallions had an anchor and origins under two labels and could not be checked
at all.** Fixed 2026-07-26: the printed national line is `Horses (including
ponies), viz.: Stallions` (anchor 1893–1900, no origin table) while the country
tables sit under `Animals, Living — Stallions` (origins 1888–99, no anchor).
Folded; the series now reads 0.9822 / 0.9948 / 1.0420 / 1.0241 / 1.0264 / 1.0726
/ 0.9968 for 1893–99 — loose, but the line is 462–933 head a year and was
previously unmeasurable in every year. Mares and Geldings need no such fold;
their groupless labels already carry both halves.

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

---

# The four cow tables were already recovered; the 1881 gap is one cell (2026-07-26)

## The queued item is stale — strike it

"1876, 1878, 1881, 1882 — `Cows` has no origin table at all" was true when
written and is not true now. All four tables are in the payload and the family
closes with all three children present in every one of those years:

```
1876  271,576 v 271,576   1.0000     1878  253,432 v 253,462   0.9999
1881  316,374 v 319,374   0.9906     1882  343,690 v 343,699   1.0000
```

They were recovered as a side effect of session 9's oxen fold. What the parser
had done is worth recording, because it is a class: **it lost the
`ANIMALS, LIVING` group head in as_1876/78/81/82 and promoted the section's
first article to group**, so `country_obs` carries `article_group='Cows'` with a
null article (the cow table itself) and `Calves`, `Horses`, `Sheep and Lambs`,
`Swine`, `Unenumerated` hanging beneath it as though they were sub-sorts of
cows. Two of those escaped into the payload as commodities of their own and are
still there: **`Cows — Horses` (GBP2.4M, 1876/78/81/82) and `Cows — Swine`
(GBP0.5M)**. They are the horse and swine tables of those four years wearing the
wrong head — a curation lead, not adjudicated here.

The predicted residuals were 58,520 / 29,384 / 34,056 / 45,052. The tables
actually read 58,520 / 29,354 / 31,056 / 45,043 — 1876 matching the prediction
to the digit.

## 1881 is short by exactly 3,000, and it is one cell in the oxen block

Not cows. `ANIMALS LIVING|Oxen and Bulls` in as_1881, seq 5–16:

```
  countries sum   248,635
  printed TOTAL   251,635        <- 3,000 more than its own rows
  251,635 + 36,683 calves + 31,056 cows = 319,374 = the parent's T1, EXACTLY
```

The parent total is printed identically by as_1881 through as_1885, so 251,635
is confirmed twice over and the payload's 248,635 is 3,000 short.

**It is a misread quantity, not a dropped row**, and the value column proves it:
the same eleven countries sum to **5,475,177**, the block's printed value total,
to the digit. A missing country would take value with it.

Both engines were consulted and neither settles which cell. They agree on every
quantity and on both totals, differing only at France (2,499 Chandra / 2,199
Infinity) — a 300 difference that cannot make 3,000.

Unit price narrows it to three. With the value column trustworthy, the block's
prices run GBP18.65–24.83, and adding 3,000 head to each candidate gives:

```
  United States          GBP22.86    plausible
  British North America  GBP20.41    plausible
  Denmark                GBP19.87    plausible
  Portugal / Germany     GBP17.40 / 17.85   marginal
  Sweden / Spain         GBP15.26 / 15.80   below the cluster
  France / Holland / Norway / Other   GBP11.28 and below — ruled out
```

**A page-image candidate**: as_1881, the Oxen and Bulls import table, one of the
United States / British North America / Denmark rows. Three candidates is not a
repair, and guessing between them is exactly the coincidence this project
refuses.

## Settled in passing

**Infinity's United States value for 1881 oxen is wrong.** It reads 2,100,386
against Chandra's 2,400,386, and only Chandra's closes the block's printed value
total. Chandra's France quantity (2,499) is also the more plausible of the two on
price — GBP24.83 against GBP28.22 for a block topping out at GBP24.83 — but the
value column cannot settle that one, so it stays open.

---

# Round 34 — the living-horses and living-swine origin tables, found under three group heads

`Animals, Living — Horses` carried a printed T1 line for **every year 1866-1891**
and origin data for exactly **one** of them (1880). `Animals, Living — Swine` was
the same story before 1880. The missing tables were not missing at all — they
were sitting under two other group heads.

## The head-drift

The printed section heading is `ANIMALS, LIVING :`. The parser captured it as:

| head captured | years | payload label |
|---|---|---|
| `ANIMALS` | 1872-75, 1877, 1879 | `Animals — Horses`, `Animals — Swine` |
| `COWS` | 1876, 1878, 1881, 1882 | `Cows — Horses`, `Cows — Swine` |
| `ANIMALS LIVING` | 1880 | the target, already correct |

`COWS` is not a stray string: it is the tail of the **preceding article**,
`Oxen, Bulls, Cows, and Calves`. The head drifted onto the rows below it.

The three sets of years are **perfectly complementary** — no year appears under
two heads, and 1880, the one year the target already had, appears under none of
the others. That pattern is itself the signature: each printed year-table went to
whichever head the parser was holding at the time.

## The proof is the anchor, year by year

Neither orphan carries a T1 line of its own; the target holds T1 for all of these
years, so there is **no anchor contest** — the only question is whether the
origin tables belong to it, and the printed national totals answer it:

| year | source | origin sum | target T1 | |
|---|---|---|---|---|
| 1872 | `Animals — Horses` | 12,618 | 12,618 | **exact** |
| 1873 | `Animals — Horses` | 17,822 | 17,822 | **exact** |
| 1874 | `Animals — Horses` | 12,033 | 12,033 | **exact** |
| 1875 | `Animals — Horses` | 25,727 | 25,757 | −30 |
| 1876 | `Cows — Horses` | 41,148 | 41,148 | **exact** |
| 1877 | `Animals — Horses` | 30,524 | 30,524 | **exact** |
| 1878 | `Cows — Horses` | 26,521 | 26,521 | **exact** |
| 1879 | `Animals — Horses` | 15,246 | 15,246 | **exact** |
| 1881 | `Cows — Horses` | 9,950 | 9,950 | **exact** |
| 1882 | `Cows — Horses` | 8,824 | 8,827 | −3 |

Swine, same volumes and the same drift:

| year | source | origin sum | target T1 | |
|---|---|---|---|---|
| 1876 | `Cows — Swine` | 43,558 | 43,558 | **exact** |
| 1877 | `Animals — Swine` | 20,034 | 20,031 | +3 |
| 1878 | `Cows — Swine` | 55,911 | 55,911 | **exact** |
| 1879 | `Animals — Swine` | 52,366 | 52,366 | **exact** |
| 1881 | `Cows — Swine` | 24,283 | 24,283 | **exact** |

**Eleven exact digit matches out of fifteen checkable years**, and the four that
miss are off by 30, 3, 3 and 0 — single-cell OCR noise, not a mis-assignment.

## The fix

Four `fold` actions in `reference/commodity_curation.csv` — payload level, no
vote, no database, no parser change. Units are `Number` on both sides of all four
folds and the year sets are disjoint, so nothing merges and nothing doubles
(verified before applying: zero overlapping years in every fold).

Full before/after diff of every commodity-year ratio in the payload: **15 cells
changed, all of them from "no origin data" to a ratio**, and nothing else moved.

```
exact01  2,251 -> 2,265      nodata  6,025 -> 6,010
within 0.1%  22.7% -> 22.8% of commodity-years   (GBP-weighted flat at 39.5%)
within 5%    30.6% -> 30.8%
```

The GBP weight does not move because these are small commodities — GBP6.5M of
horses and GBP2.5M of swine against a GBP-billions corpus. What moves is
coverage: a commodity that published a national line for 26 years and showed
origins for one now shows them for eleven.

## Still open in this family

- **`Animals, Living — Horses` 1866-71 and 1883-91** still have no origin data.
  The 1883-87 tables exist under `Animals Living — Horses, Mares, Geldings,
  Colts, And Foals` (four spelling variants of one label, GBP1.05M, no T1) —
  that is a **wording change mid-series**, so it is the deferred
  "which label carries Tier 1" decision, not a fold to make alone.
- **`Horses` (1892-96, T1 20,994-40,677) continues `Animals, Living — Horses`
  (T1 ends 1891 at 21,672)** without a break in the level. Same deferred
  decision; note its unit reads `Cwt`, which cannot be right for live horses.
- `Animals — Swine` 1872-75 (16,100 / 80,978 / 115,389 / 72,170) was folded on
  the strength of the years that close, but **no T1 exists for swine before
  1876 on any label** — those four years are unverifiable and stay that way.
