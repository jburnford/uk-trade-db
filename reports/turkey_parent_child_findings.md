# Turkey counted twice: a parent line and its sub-entries as siblings

Found while chasing the 19 regressions left by the `tn_` volume work. The cause
turned out to have nothing to do with those volumes.

## The defect

The abstract prints Turkey as a parent line with two parts:

```
Turkey              21,873,318
  „ European         4,513,880
  „ Asiatic         17,031,222
```

The pipeline carries all three as **flat sibling countries** — `Turkey`,
`Turkey European`, `Asiatic` — so a year that sums its origins counts Turkey
twice.

This was harmless for years, because the two sub-entries carried **no unit** and
the bucket arithmetic sums only the modal unit, which skipped them. The `tn_`
rebuild ran the unit-healing pass over a larger corpus, the sub-entries were
promoted into the modal unit, and every affected year began running ~2% over.

## The proof that `Turkey` is the parent

`Wool — Sheep Or Lambs'` 1893 sums to **684,613,774** with the children and
**672,763,274** without — and 672,763,274 is the printed Tier-1 **to the digit**.

Corpus-wide the same test holds: **74 commodity-years** carry both a `Turkey`
cell and a child in the modal unit, and removing the children takes 17 of them to
`exact01` at ratios between 0.9994 and 1.0006 — Cotton 1896, Galls 1893-94,
Gum Arabic 1894-96, Maize 1893/95, Rye 1894-95, Flax Or Linseed 1895-96, Silk Raw
1896, Wool Sheep 1893-96.

## The fix

133 `drop-country` rows across 72 commodities. Written **unscoped**, because
`drop-country` is **arithmetic-guarded** — it removes a cell only where doing so
brings the year closer to its anchor — so years where the child is genuinely the
only Turkey data exclude themselves.

The guard is not quite sufficient on its own. Four commodity-years fell from
`exact01` under the unscoped rules (`Wool — Sheep Or Lambs'` 1899, `Silver, Ore
Of` 1894, `Skins — Sheep And Lamb, Undressed` 1894, `Old, Fit Only To Be
Re-Manufactured` 1895). Those four commodities are now **year-scoped** to the
years where the drop provably helps; two of them keep no years at all.

**Result: 34 cells better, 0 worse.**

```
                    before        after
exact01              3,704         3,723    (+19)
                     39.0%         39.2%
GBP within 0.1%      51.9%         53.6%    (+1.7)
GBP within 5%        71.6%         71.7%
```

## Worth noting about the guard

An arithmetic guard that only asks "does this bring the year closer?" will still
fire in a year where the cell it removes was load-bearing but the year was
slightly over for an unrelated reason. It is a good default and a poor
adjudicator. Where a guarded rule regresses a previously-exact cell, scope it
rather than trust it.

## Still open

- The same parent/child shape almost certainly exists for other composite
  origins. `Turkey` was found because it regressed; nothing has swept for the
  general case — a screen for *a country whose name is a prefix of, or is
  parent to, another country in the same commodity-year* would find them.
- `Linen Yarn` 1873/1891/1893 fell to `nodata` in the `tn_` rebuild and is **not**
  explained by this; still open.
