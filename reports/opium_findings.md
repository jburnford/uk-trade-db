# Opium: one closing year becomes eleven — and why the headline says +2

Worked 2026-07-29 (`/loop /next-defect` iteration 20).

## How it surfaced

Refreshing the bracketed-gap screen put **Opium 1879-1893, £6.3M, a fifteen-year
hole** at rank 3. It had not been there before, and the reason is that last
iteration's `Copper, Ore Of — Opium` → `Opium` fold gave the commodity clean
1894-98 data — which turned a trailing collapse into a *bracketed* gap the
screen can see. **Second time this session that folding one thing has promoted
another into the ranked list.**

## Two sibling nodes, two different defects

**`Onions — Opium`** — a stale ONIONS group head over the opium origin tables,
holding 1877, 1879, 1880, 1881. Closes on opium's own Tier-1: **1881 793,146 =
793,146** and **1879 572,381 against 572,411**, with 1877 at 0.9906 and 1880 at
0.9083.

**`Drugs — Opium`** — not a stale head but **the same series with its own
anchor**. The proof is the anchors themselves: they are **identical in every
one of the sixteen years both nodes carry (1878-1895)**, while each holds years
the other lacks — `Opium` has 1866-77 and 1896-1900, `Drugs — Opium` has 1882
and 1891. Two halves of one printed line that each kept a total. Its country
cells close on opium's anchor **to the digit in eight years**: 1883, 1884,
1885, 1886, 1889 and 1892 exactly, 1887 654,072 vs 654,122, 1888 587,374 vs
587,365 — plus 1891 at 511,271 against its own 511,274.

**Both folds year-scoped.** `Drugs — Opium` reads 1.11 in 1890 and 1.67-1.96 in
1893-1896 against opium's anchor — those years' cells are inflated, and the
host already holds clean 1894-98 data from last iteration — so they are
excluded. 1882 is included **for its anchor alone**: the fold pops the source
node, and without it that year would leave the corpus entirely.

## The result, and why the headline understates it

Opium's origin series before and after:

| | before | after |
|---|---|---|
| years closing | **1878 only** | **1877, 1879, 1883, 1884, 1885, 1886, 1887, 1888, 1889, 1891, 1892** |

Eleven years where there was one. But the baseline moved only **3,366 →
3,368 (+2)**, because **the denominator fell 9,610 → 9,594 (−16)**. That is
the honest arithmetic of de-duplication: before the fold, the same printed
line's years were counted **twice** — as `exact01` under `Drugs — Opium` and
as `nodata` under `Opium`. Afterwards each is counted once. Opium gained
roughly eleven and the duplicate key took roughly nine away with it.

**Zero true regressions** — no commodity-year moved to a worse bucket.

The lesson is one to apply to every fold that merges two *anchored* nodes:
**a +2 headline can conceal a series going from 6% closed to 65% closed.**
Quote the commodity's own before/after, not just the corpus count.

## Re-testing the last two known-dead verdicts — they hold

Mahogany's retraction last iteration made every "known-dead" verdict suspect,
since all were reached by hunting the printed total through `country_obs` and
that hunt cannot see a table filed under a sub-label. The two remaining ones
were re-tested against **every node in the payload**, not just the matchers:

- **Sugar — Unrefined, Total 1874** (T1 14,130,041 Cwt): **zero** candidate
  nodes sum within 2% in that year. Dead confirmed.
- **Caoutchouc — Manufactures Of 1892-98**: the only near-matches are
  `Cork — Manufactured`, `Yarn`, `Straw Platting` and `China, Or Porcelain…
  — Manufactured` — **all commodities with anchors of their own**, so the
  agreement is coincidence between unrelated Lb-denominated series, not
  misfiling. Dead confirmed.

Worth noting *why* the ad-hoc scan threw those up while the matchers do not:
**the matchers require the candidate to hold no anchor in the matched years.**
That single condition is what separates "this node is the missing half of that
commodity" from "these two unrelated series happen to be the same size". The
false hits here are a live demonstration that the guard earns its keep.

So mahogany was the exception, not the rule — but it was still worth the
re-test, and the re-test cost one query.
