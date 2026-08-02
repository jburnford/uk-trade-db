# Cordage 1888: closed by routing around a guard that still blocks 1,593 blocks

Worked 2026-08-02 (`/loop /next-defect`), bracketed-gap rank 3, GBP 515k.
**`Cordage, Twine, And Cable Yarn` 1888 went from `nodata` to exactly
1.000000** — 459,138 of 459,138.

**exact01 3,565 → 3,566, nodata 4,298 → 4,297, denominator held at 9,468. One
commodity-year changed; zero regressions.**

## The block was parsed, correctly labelled, and closes at every level

Infinity parses it under the **correct** group `CORDAGE, TWINE, and CABLE YARN`
at seq 352-363. Chandra has no as_1888 cordage block at all.

| | members | printed |
|---|---|---|
| Foreign (7) | 50,718 + 39,750 + 32,514 + 35,775 + 101,712 + 11,093 + 6,763 = **278,325** | **278,325** |
| British (2) | 179,710 + 1,103 = **180,813** | **180,813** |
| Grand | 278,325 + 180,813 = **459,138** | **459,138 = the Tier-1** |

All three to the digit.

## Why the Infinity-only path could not take it — and this is not a cordage problem

This is a **value-only** table: the commodity's Tier-1 unit is `Value` and the
printed table has no quantity column. `integrate_sources`' **step-2 (infonly)
member filter still carries `or not q or q <= 0`**, which discards every row
without a quantity.

**That is the same predicate the silver-ore session fixed in step 6**, with the
user's approval, after finding it cost 234 cells across 23 group repairs (see
`reports/silver_ore_findings.md`). **Step 2 was never changed.**

**Measured scope: 23,938 value-only Infinity import rows, in 1,593 distinct
blocks, are currently unreachable by the `infonly` path.** Not all of them are
recoverable — many will be years consensus already covers — but the guard makes
every one of them invisible to that route regardless.

**No code change was made for this item.** The block was routed through **step
6** instead, with a `group_repairs` row carrying `obs_source=inf`, because the
value-only branch already works there. **The step-2 guard is queued as a
separate, corpus-wide question needing its own measurement and decision —
exactly as the step-6 change did.**

## Still open in this commodity

1868-1871 `nodata`; and a run of `under` years — 1885 at 0.422, 1880 at 0.708,
1882 at 0.732, 1876 at 0.833, 1883 at 0.916, 1873 at 0.920.
