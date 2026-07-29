# A self-inflicted hole, and how it hid

Worked 2026-07-29 (`/loop /next-defect` iteration 24).
**exact01 3,458 → 3,472 (+14), nodata 4,507 → 4,490, zero regressions.**

## What happened

Refreshing the bracketed-gap screen put **`Iron — In Bars` 1882-1886, £8.3M**
at rank 3 and **`Shumach` 1878-1885, £4.5M** at rank 4 — two large multi-year
holes that had not been there before.

Both were **created by my own folds in iteration 23.**

## The bug

Iteration 23 folded twelve era-split sources, each year-scoped. The scope was
built like this:

```python
scopes = {r['orphan']: r['safe_scope'] for r in csv.DictReader(open(...))}
```

`reports/orphan_country_matches.csv` carries **up to three rows per source** —
the top three candidate hosts. A dict comprehension keeps the **last**
occurrence, and the file is sorted best-first, so this took the
**worst-ranked host's** `safe_scope`, not the matched one's.

For `Bar, Angle, Bolt And Rod` → `Iron — In Bars` the matched host lacked
**1882-1890**; the scope written was **1887-1900**. The fold pops the source
node, so the source's **1882-1886 country cells were discarded**. Those rows
are still in `country_year_final` — they simply stopped reaching the payload.

## Why the diff did not catch it

The payload diff compares bucket transitions per (commodity, year). Those five
years read **`nodata` in `Iron — In Bars` both before and after**: before,
because the data was in the other node and the target had no cells; after,
because the data was gone. **A cell that moves from an unmeasured node into
oblivion produces no bucket transition at all.**

That is the general lesson: **the payload diff is a regression check on
*measured* years, not a conservation check on data.** Under-scoping a fold
destroys cells silently; over-scoping produces conflicts the diff *does* see.

## The fix, and the rule that follows

All twelve scopes removed. **Default to an unscoped fold.** An unscoped fold
can only *add* to the target — the target wins every conflict — and any harm it
does is visible to the diff. Scope only in response to an observed regression,
which is exactly how the one legitimate scope (`Bark — Sumach` → `Sumach`,
iteration 18) was arrived at.

Recovered immediately: **+14 commodity-years**, `Iron — In Bars` 1883 and 1884
back to closing on the digit (122,895 and 115,486), the commodity now closing
in 24 of its 35 anchored years.

## Two smaller notes

- The rank-3 and rank-4 entries were **evidence of my own damage presented as
  new work**. Worth remembering when a refreshed ranking surfaces something
  large in a commodity touched last iteration: **suspect the last change before
  theorising about the corpus.**
- `Shumach` recovered the same way and now closes in 18 of 27 years. Its
  residual 1878-1885 gap is real and separate — the 1878 block sits in
  `country_obs_inf` under a stale `Cotton` head (`Cotton | SHUMACH`, TOTAL
  13,923 = Tier-1 to the digit) and never reached `country_year_final` at all.
  The shumach family is scattered over six payload nodes (`Shumach`, `Sumach`,
  `Cotton — Shumach`, `Copper, Ore Of — Sumach`, `Dyeing Or Tanning Stuffs —
  Shunach`, `Dye Stuffs (Other Than Dye Woods)… — Sumach`) across three
  spellings. Queued.
