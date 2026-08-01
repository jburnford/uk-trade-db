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

---

## The guard that works: does the source carry an anchor of its own?

**exact01 3,526 → 3,528, denominator unchanged at 9,515, zero true
regressions.**

The previous section left the name test with a hole it could not plug: a shared
**modifier** (`Pork — Salted` → `Beef — Salted`) passes every signature test,
because `Salted` has a perfectly good signature. Trying to classify articles as
commodity nouns versus adjectives is the obvious fix and a bad one — it needs a
lexicon the corpus does not have.

The right question turned out not to be about the article at all:

> **Does the source carry a Tier-1 of its own?**

A source that anchors years of its own is a **real printed line, not glue**.
Glue has no anchor because it never appeared as a printed heading. *Pork
salted* is a genuine commodity — which is precisely why it has one.

Tested against the hand adjudication of the previous run, it separates the set
almost exactly:

| | source anchors its own years | no anchor |
|---|---|---|
| **8 folds I accepted** | 0 | **8** |
| **8 pairs I declined** | **6** | 2 |

It catches `Seeds — Rape`, `Wood And Timber — Staves`, `Oil — Coco-Nut`,
`Leather Manufactures — Unenumerated`, `Metal — Leaf, Not Gold` and — the one
that mattered — **`Pork — Salted`**, with **no false rejections** among the
accepted set.

Anchored sources are still reported, under `kind='anchored-source'`, because
the era-split population found in iteration 23 lives there and is genuine. They
are simply never `resolved`.

### What it still cannot do

The two declines it misses are both **direction** problems: `Wood And Timber —
Fir` → `Sawn — Fir` and `Wood And Timber — Mahogany : Unenumerated`. Neither
source has an anchor, so the guard passes them; both would fold a properly
headed source into a de-headed fragment. **The tool has no notion of which of
two names is the damaged one, and that remains a human judgement.**

### Result

With the guard in place the list drops from 16 to **2 resolved**, both further
glue nodes under stale heads already folded last iteration, and both landing
exact:

```
Cordage, Twine, And Cable Yarn  1874  nodata -> exact01  552,665
Dyes Obtained From Coal Tar     1883  nodata -> exact01  386,623
```

The script's docstring has been corrected — it previously claimed the
non-empty-signature rule made the sig path safe, which this run disproved.
