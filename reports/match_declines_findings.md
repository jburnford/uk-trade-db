# A declines list the tools can read — and the arithmetic seam is now dry

Worked 2026-07-31 (`/loop /next-defect`).
**No data change; baseline unchanged at exact01 3,496 / 9,518.** This is a
tooling iteration and a closing statement on a seam that has been the single
biggest source of gains this session.

## The problem it fixes

The previous run of `match_orphan_countries` re-proposed `Gum — Unenumerated`
→ `Of Other Sorts`, which iteration 23 had already declined for a stated
reason. The decline lived only in a findings report, so the tool could not see
it and would surface it on every run forever, costing a fresh adjudication
each time.

There is a second, sharper reason to record declines **in a place the tool
reads**: a declined candidate still occupies a slot in the *"exactly one
candidate clears the bar"* uniqueness test. Leaving it in can make an
otherwise-resolvable pair read `ambiguous`. So declines are filtered **before
scoring**, not after.

## What was built

- `reference/match_declines.csv` — `source, host, reason, declined_on`. A
  blank `host` declines a source against every host.
- `scripts/match_declines.py` — shared loader, wired into both
  `match_orphan_countries.py` and `match_shadow_anchors.py`, with the
  path-insert needed so the matchers still run from the repo root.
- Both matchers now report `(adjudicated declines filtered: N)`.

Six declines recorded, each with its reasoning. **One of them is not a
judgement on the evidence at all**, and that distinction is the point of
writing reasons rather than just keys:

> `Copper — Manufactures Of, Unenumerated` → `…Including Copper Coin` —
> **CORRECT BUT UNAPPLICABLE.** A true era-wording pair, two years to the
> digit. Applying it takes the host's 1887 from `exact01` to `nodata` — a year
> *neither node touches* — because the explicit fold shifts
> `fold_era_wordings` bucket membership and an automatic era-fold that had
> been supplying 1887 stops firing. Scoping and widening both tested, both
> fail. **Re-open when `fold_era_wordings` is fixed.**

A future run must not re-litigate that as if the arithmetic were doubtful.

## The seam is exhausted, and the control run proves it

| | with declines | without declines |
|---|---|---|
| `match_shadow_anchors` | 0 resolved, 0 ambiguous | **0 resolved, 0 ambiguous** |
| `match_orphan_countries` | 0 resolved, 1 ambiguous | 5 resolved, 1 ambiguous |

The shadow direction returns nothing **with the declines file removed**, so
its zero is real exhaustion and not my filter suppressing work. And every one
of the five matches the orphan direction still finds is one adjudicated
earlier today — four declined on the merits, one declined as unapplicable.

**So the arithmetic matchers have nothing left to give.** Across this session
that seam returned +97, +84, +48, +25, +11 and +8 commodity-years; it is now
worked out. One `ambiguous` pair remains (`Beads Of All Sorts — Brass…`
against the brass host), held because the tool itself cannot choose.

## What that implies for where to look next

The remaining defects are, by construction, the ones **arithmetic cannot
find** — where the two halves do not sum to each other because one of them is
truncated, fused, mis-flowed, or absent from both parses. Every recent win has
had that shape: the feathers phantom region article, the silver-ore
`SILK MANUFACTURES` glue, the `China, Or Porcelain` sticky head over the
herring line. **Structural evidence — a fused header, a place-name article, a
stale group — is now the productive instrument, not agreement of sums.**
