# Near-miss years: two hypotheses tested, both largely refuted

The `within5` pool is the largest tractable one left — 1,206 commodity-years, of
which **531 sit inside 0.5%** of closing. The obvious guesses about what is wrong
with them are that the pipeline picked the wrong reading, or that one figure has a
misread digit. Both were tested. Neither explains the pool.

## Instrument: `scripts/detect_lost_vote.py`

It proposes nothing. For a near-miss year it computes `delta = anchor − sum` and
asks only whether **some parse in the corpus already holds** a figure that closes
it:

> does any reading of `(article, country, year)` in `country_obs` or
> `country_obs_inf` equal `cell + delta`?

When one does, it is not a repair and not a guess — it is a **vote the pipeline
lost**. Rosin 1872 was exactly this shape: five readings said 827,836, the one
that won said 527,536, and the year read 0.67.

## Negative result 1 — near-misses are not mostly lost votes

**18 of 316** near-miss commodity-years close on a reading the corpus already
holds, and only **4** of those have *more* support than the figure in use. The
voter is, overwhelmingly, already picking the best-supported reading. That
retires the hypothesis.

## Negative result 2 — nor are they mostly misread digits

A single misread digit produces a delta that is a **round multiple** — 5-for-8 in
the hundred-thousands is exactly ±300,000. Across the 316 near-misses:

| delta | count |
|---|---|
| not a round multiple | **268** |
| multiple of 100 | 25 |
| multiple of 1,000 | 14 |
| multiple of 10,000 | 8 |
| multiple of 100,000 | 1 |

So **85% of near-miss deltas cannot be a single-digit misread.** Whatever the
pool is, it is mostly small non-round discrepancies — a minor origin absent from
the list, or a printed total that covers something the origin table does not.
That is a different instrument, and worth knowing before building one.

## What was fixed

The four better-supported cases, each written as a `replace=1` row that records
the vote count rather than a digit:

| commodity | year | country | was | now | support |
|---|---|---|---|---|---|
| `Metal — Unenumerated, Unwrought` | 1895 | Germany | 197 | 107 | 3 v 1 |
| `Manures — Guano` | 1895 | Other British Possessions | 1,078 | 795 | 3 v 2 |
| `Cutch And Gambier` | 1895 | Other Foreign Countries | 127 | 96 | 3 v 2 |
| `Plate — Of Silver, Gilt Or Ungilt` | 1897 | British East Indies | 1,239 | 1,320 | 2 v 1 |

**3 better, 0 worse. exact01 3,738 → 3,741 of 9,509.**

## A limitation of the screen, found by the one that did not move

The Metal cell corrected — 197 to 107, and it is better supported — but its
commodity-year did not change bucket. The screen works on the database's
`(article, year)`, and that article is spread across **five** payload nodes
(`Metal — Unenumerated, Unwrought`, `Manufactures Of Iron And Steel — Metal,
Unenumerated, Unwrought`, three more). A closure proved at DB level need not
correspond to any single node the metric measures. The cell is still right; the
screen's arithmetic just was not measuring the thing the baseline measures.

## Still open

- The 14 candidates with **equal** support (`1v1`) are genuinely unadjudicated —
  two readings, one each, and the page decides. Listed in
  `reports/lost_vote.csv`.
- The seven page-adjudication candidates from
  `reports/redundant_country_findings.md` are untouched.
