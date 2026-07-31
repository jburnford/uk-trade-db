# Re-running the orphan matcher: four folds, and copper bites twice

Worked 2026-07-31 (`/loop /next-defect`).
**exact01 3,488 → 3,496 (+8), denominator unchanged at 9,518, zero
regressions.** Every one of the ten changed commodity-years went `nodata` →
measured.

## Why re-run it

The previous iteration folded a mahogany pair that `match_orphan_countries`'
era-split path should in principle have found and did not, so the tool was
queued for a re-run. It returned **8 resolved + 1 ambiguous**. The mahogany
pair itself is gone (already folded), so *why* it was missed stays open — but
the re-run paid for itself anyway.

## Adjudication — four accepted, five declined

**Accepted:**

| source | → host | evidence |
|---|---|---|
| `Brass… Manufactures Of, Not Otherwise Enumerated` | `Brass… }Manufactures Of` | 3 years to the digit; era wording, host name carries an OCR `}` |
| `Cards, Playing — Transparent In The Manufacture Of Which Spirit Has Been Used` | `Soap, Transparent, In The Manufacture…` | 2 to the digit; sticky CARDS head, **article text identical to the host name** |
| `China, Or Porcelain… — Fresh (Not Of British Taking) : Herrings` | `Fish : Fresh, Herrings` | 2 to the digit; sticky CHINA head over a FISH line |
| `Copper — Manufactures Of, Unenumerated` | `…Unenumerated, Including Copper Coin` | 2 to the digit — **later withdrawn, see below** |

**Declined, with reasons on record:**

- `Gum — Unenumerated` → `Of Other Sorts` — declined in iteration 23 and still
  declined: the host is a de-headed generic name and folding cements a bad
  label. **The matcher keeps re-proposing it; the decline needs to live
  somewhere the tool can see, not just in a report.**
- `Skins, Furs, And Pelts — Unenumerated : Undressed` → `Skins And Furs —
  Goat, Undressed` — same shape. *Unenumerated* is not *Goat*.
- `Seeds — Rape` → `Hemp`, **£23.2M** — two years to the digit is the bar, but
  rape seed is not hemp. A sum agreeing twice is not a licence to merge two
  named commodities; this needs the printed page first.
- `Wood And Timber — Hewn, Unenumerated` → `Wood And Timber — Unenumerated`,
  **£5.9M** — *Hewn* is a real printed sub-sort, so this may be a sub-sort
  being folded into its own parent, which would double-count. Needs checking,
  not assuming.
- `Beads Of All Sorts — Brass…` → the same brass host — the tool itself marks
  it **ambiguous** (more than one candidate cleared the bar). The name
  identity is overwhelming and it is probably right, but held.

## Copper, and the same mechanism as iteration 18

The copper fold was correct on its evidence and still had to be **withdrawn**.
Unscoped it produced:

```
Copper — Manufactures Of, Unenumerated,   Including Copper Coin
   1887  ('exact01', 51874) -> ('nodata', 0, 51874)
```

A year **neither node touches** lost its data. This is precisely the
iteration-18 copper finding: the explicit fold changes `fold_era_wordings`
bucket membership in `build_viz_payload`, and an **automatic** era-fold that
had been supplying the host's 1887 stops firing. Two tests, both negative:

- scoping to the matcher's `safe_scope` (which excludes 1887) — no help;
- **widening** the scope to include 1887 — no help either; the source has no
  1887 country cells to give.

Iteration 18 concluded that only dropping the fold works, and that holds. So
copper is now a **twice-observed specimen of this class**, in the same
commodity both times.

**The cost of that decision, stated plainly:** withdrawing the fold gives up
**six `within5` years and one `under`** (1874, 1888, 1889, 1892, 1893, 1894,
1895) that were honest new measurement, in order to avoid one `exact01` →
`nodata` regression. exact01 lands at 3,496 either way. That is the
zero-regression discipline being expensive rather than free, and it is worth
recording as such — the underlying fix is `fold_era_wordings`, the second
queued code question, which has never been asked or answered.

## The soap fold did respond to scoping

Unscoped it took `Soap, Transparent…` 1895 from `exact01` 13,842 to `within5`
14,102 — both nodes hold cells there. Scoping to `1896;1898;1899` fixed it and
cost nothing, exactly as the proviso added last iteration predicts. 1896 lands
at `over` (15,795 vs 14,595), which is new measurement rather than a
regression, and is the next thing to look at in that commodity.

## Result

`Fish : Fresh, Herrings` 1895 and 1896 both close **to the digit** (767,598
and 773,591) where they had no origins at all — the largest single win here,
and it came from a sticky CHINA OR PORCELAIN head, the same volume-scale
stickiness already recorded for `as_1897`.
