# Name as the precondition, arithmetic as the confirmation

Worked 2026-07-31 (`/loop /next-defect`).
**exact01 3,517 → 3,526 (+9), denominator 9,518 → 9,515, zero true
regressions.**

## The instrument

`scripts/match_by_name.py` inverts the evidence the arithmetic matchers use.
Those require **two** years agreeing to the digit, which is correct on its own
terms — across ~900,000 pairs one agreeing year is expected by chance about 180
times — but it rejects two whole populations: single-year sources (483 of
them), and multi-year sources that happen to agree in only one year.

Here **the name relation is the precondition and the arithmetic confirms it**,
so one agreeing year suffices. The relation is tested three ways: signature
equality of the trailing article segments, normalised string equality of them
(which catches `Unenumerated, Raw` against `Unenumerated : Raw`), and
source-article against the host's whole name.

**16 resolved. 8 accepted, 8 declined.** All eight declines are in
`reference/match_declines.csv` with reasons.

## The eight that landed

| source | → host | effect |
|---|---|---|
| `Fruit — Rum` | `Spirits — Rum` | **1896, 1898, 1899 all exact01** — £5.3-5.6M each |
| `Paper — Wood Pulp Boards` | `Wood Pulp Board` | 1895, 1896, 1898 exact01 |
| `Beads Of All Sorts — Brass, Bronze…` | `Brass, Bronze… }Manufactures Of` | 1893, 1894 exact01 |
| `Bark — Logwood` | `Dye Woods — Logwood` | 1899 exact01 |
| `Lates — Ginger` | `Spices — Ginger` | 1898 exact01 |
| `Feathers And Down — For Beds, In Beds Or Otherwise` | `Feathers — For Beds` | 1897 exact01, five more years measured |
| `Copper — Cordage, Cables (Not Of Iron)` | `Cordage, Twine, And Cable Yarn` | 1895 within5 |
| `Dye Stuffs… — Dyes Obtained From Coal Tar` | `Dyes Obtained From Coal Tar` | 1887 measured |

`Beads Of All Sorts` was the pair the arithmetic matcher had been reporting as
**ambiguous** for two iterations; with the name relation as the precondition it
resolves cleanly.

Two folds had to be **year-scoped** — `Lates — Ginger` to `1897;1898` and
`Feathers And Down — For Beds…` to `1894-1898` — because both nodes hold cells
in the overlap years and the unscoped versions pushed `Spices — Ginger` 1894
and 1895 and `Feathers — For Beds` 1893 off `exact01`. Scoping recovered all
three, exactly as the proviso from two iterations ago predicts.

## The sharp finding: a shared modifier is not a name relation

The most instructive candidate was one I rejected:

> **`Pork — Salted` → `Beef — Salted`**, matched by *signature* relation.

Pork is not beef. The tools agreed on the article `Salted` — a **modifier**,
not a commodity — and the guard I had written into the docstring, *"a
signature-only match is required to be non-empty"*, does **not** catch it,
because `Salted` has a perfectly good non-empty signature. `Unenumerated` and
`Raw` are excluded for free by being all-filler; `Salted`, `Dry`, `Rough`,
`Undressed` are not.

**The name test needs the shared article to be a commodity noun, not a shared
adjective**, and nothing in the current implementation enforces that. Recorded
in the decline file and in the script's own docstring; until it is fixed, every
`sig`-relation candidate must be read for this.

## The second decline class: folding into a de-headed host

Five candidates propose folding a **properly headed** source into a host that
is itself a **de-headed fragment** — `Wood And Timber — Fir` → `Sawn — Fir`,
`Wood And Timber — Staves` → `Staves`, `Seeds — Rape` → `Rape`, `Oil —
Coco-Nut` → `Coco Nut`, `Metal — Leaf, Not Gold` → `Leaf, Not Gold`.

That is the **wrong direction** — the same shape as the `Gum — Unenumerated` →
`Of Other Sorts` decline standing since iteration 23. Folding cements the
damaged label on good data. The first of them carries **£63.8M** on a single
agreeing year, which is exactly the combination that should not be waved
through.

**The matcher has no notion of which name is the damaged one.** It ranks by
size and reports a relation; direction is still a human judgement, and this run
proposed five wrong-direction folds out of sixteen.
