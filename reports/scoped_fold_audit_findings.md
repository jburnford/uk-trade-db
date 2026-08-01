# Auditing my own fold scopes: 18 silent discards, 15 recovered

Worked 2026-08-01 (`/loop /next-defect`).
**exact01 3,532 → 3,538 (+6), denominator unchanged at 9,511, zero true
regressions. Fifteen commodity-years improved.**

## Why audit

Twice now a year-scoped fold has quietly thrown data away — iteration 23
(scope built from the wrong host, cost 14 commodity-years) and the glucose
fold last iteration (scope correct for the years it was written against, but
1895's OCR label drifted into the source's form and fell through). Both were
found by accident, months apart, off a ranked list. **A scope failure is
invisible by construction: the year reads `nodata` before and after.**

There are 45 year-scoped folds. That is a bounded population, so it can be
checked rather than waited on.

## The method: one rebuild, not forty-five

Blank **every** fold scope at once, rebuild, and diff against the current
payload. The diff separates cleanly into two populations:

- years going **`nodata`/`under` → measured** — cells the scope was
  **discarding**;
- years going **measured → worse** — the **double-counts the scopes exist to
  prevent**.

| | |
|---|---|
| recovered by removing scopes | **18** |
| broken by removing scopes | 19 |

Net −9, which is why the scopes are there. But the 18 are individually
recoverable **without** giving up the 19.

## The 18, and the three that stay excluded

Fifteen were restored by adding just those years back to the relevant scope:

| commodity | years | result |
|---|---|---|
| `Bark` | 1892, 1893 | **exact01** — 380,337 and 318,617 |
| `Seeds — Unenumerated, For Expressing Oil Therefrom` | 1875 | **exact01** 141,184 |
| `Safflower` | 1893, 1894 | **exact01** |
| `Safflower` | 1896 | within5 → **exact01** |
| `Fruit — Unenumerated : Raw` | 1892 | nodata → within5 (832,375/841,022) |
| `Seeds — Unenumerated…` | 1872, 1873, 1874 | under → within5 |
| `Books` | 1882, 1884, 1886, 1887 | under → within5 |
| `Feathers — For Beds` | 1877 | under → within5 |

**Three were left out, deliberately: `Opium` 1890, 1893 and 1899.** Removing
the scope makes them *measured* but *wrong* — 1890 over at 501,193/451,193,
1893 over at 615,577/368,566, 1899 under. Iteration 20 established that the
source's cells for exactly those years are inflated and scoped them out on
purpose. **The audit surfaces them and the record refutes them; a screen that
only counted "years recovered" would have reinstated three known-bad years.**

## One second-order effect, and the same old mechanism

Extending the Seeds scope to 1872-75 pushed **1876 and 1879** from `under` to
`nodata` — two years neither the source nor the target list mentions. Whatever
path had been supplying their (small) sums stopped firing once the source
node's membership changed. This is the iteration-18 copper interaction again.
Adding 1876 and 1879 to the scope restored them, and the final state has zero
regressions.

**So the audit itself needs the same discipline as the folds: extend, rebuild,
diff, and fix what moves — the second-order effects are not predictable from
the fold's own years.**

## Standing recommendation

Re-run this audit after any batch of folds. It is one rebuild and one diff, and
it caught six exact closures plus nine partial recoveries that no ranked list
would have surfaced — `Safflower` 1893 is a **32 cwt** commodity-year that will
never appear near the top of anything.
