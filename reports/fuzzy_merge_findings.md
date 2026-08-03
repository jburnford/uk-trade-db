# The fuzzy-merge screen: 138 merges, 4 conflicts, 0 new false pairs

`build_viz_payload.py` unifies signatures whose tokens pair within edit distance
2 — the pass that makes `{ALPACA,LLAMA,VICUNA,WOOL}` and
`{ALPACA,LLAMA,VLONNA,WOOL}` one commodity. It is guarded by a hand-maintained
`FALSE_PAIRS` set, and every entry in it (WASTE/WHITE, HORNS/HORSE,
STAVES/SLATES, and now MANUFACTURED/MANUFACTURES) was found **one commodity at a
time**, each after a wrong number had been traced back through the pipeline by
hand. The last one had put Cork's national line inside Caoutchouc for seven years.

## The discriminator

A genuine OCR variant is **the same printed line read two ways**. So wherever two
merged spellings both carry a Tier-1 figure for the same year and unit, the two
figures must **agree**. Two different commodities disagree — Cork printed
9,055,694 for 1892 where Caoutchouc printed 3,448,727.

That test needs nothing but the data already in hand, and it is now computed on
every build: `reports/fuzzy_merges.csv` lists all 138 merges with the count of
conflicting years, the differing tokens, and the worst disagreement. The screen
is **report-only** — it changes no merge, because a conflict is a candidate for
adjudication against the page, not an automatic split.

## Result: the class is exhausted

**Only 4 of 138 merges conflict at all, and none of the four is a false pair.**

| conflict | differing tokens | worst year | the two readings |
|---|---|---|---|
| 2y | CAVENDISH / CUXENDISH | 1896 Lb | 998,264 vs 508,264 |
| 2y | GENEVA / GENEVER | 1895 Proof Gal | 332,432 vs 312,432 |
| 1y | CURRANTS / CURRENTS | 1894 Cwt | 1,307,403 vs 1,507,403 |
| 1y | PRUNELLOCS / PRUNELOES | 1898 Cwt | 54,913 vs 54,013 |

All four are the same commodity under two spellings — `Cuxendish` for
*Cavendish*, `Currents` for *Currants*, `Genever` and `Geneva` for gin. The
merges are right. What disagrees is a **single digit in the abstract line**, so
the screen turns out to be two instruments at once: a false-pair detector that
found nothing left to find, and a **Tier-1 digit-disagreement detector** that
found four candidates for free.

Three of the four were already voted correctly — Cavendish 1896, Geneva 1895 and
Currants 1894 each close on their own origin table at the reading the vote took.

## Fixed: Plums, French, and Pruneloes 1898

The fourth did not. The anchor read **54,913** where the page prints **54,013** —
a 9-for-0 in the hundreds place — and the year sat at 0.98361 in an otherwise
clean run (1896, 1897 and 1899 all close exactly). Three independent supports:

- the `Prunellocs` spelling carries 54,013 across **three** volumes (as_1898,
  as_1899, tn_1899) against **two** for `Pruneloes`' 54,913;
- the raw text carries 54,013 **fourteen times across both engines in both
  volumes** (Chandra as_1898 ×3, as_1899 ×4; Infinity as_1898 ×4, as_1899 ×3)
  against three occurrences of 54,913;
- the origin table sums to **54,013 exactly**.

`manual_t1.csv` override, tier A. The year goes **0.98361 → 1.000000**, and the
consensus table's grand total falls by exactly 900 — one row, the right one.

**Baseline: exact01 3,586 → 3,587 of 9,473.** Exactly one cell changed class.

## What this settles, and what it does not

The Caoutchouc/Cork class — a fuzzy merge silently swapping one commodity's
national line for another's — **is now exhausted**: any such pair would have to
show conflicting Tier-1 years, and only four merges do. That is a real negative
result and it retires a worry, not just a task.

It does **not** cover merges where only one side carries a Tier-1 (no overlap to
test), which is the majority. For those the test is silent by construction, and
the guard remains the token-level judgement in `FALSE_PAIRS`.
