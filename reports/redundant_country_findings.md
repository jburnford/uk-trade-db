# The one-redundant-cell screen: two classes of double-counted origin

Generalised from `reports/turkey_parent_child_findings.md`, where `Turkey` was
carried as a flat sibling of its own printed parts. That was found only because a
rebuild happened to expose it; nothing swept for the shape.

## The screen

`scripts/detect_redundant_country.py`. Name-matching cannot find this class —
`Asiatic` does not contain `Turkey`. The arithmetic can:

> a commodity-year that is over its anchor and lands **inside 0.1% when exactly
> one country is removed**.

257 commodity-years qualify. **Most are coincidence**, and the report says so:
where a year is 0.2% over and carries thirty origins, some small country will
usually match the excess. Two columns separate signal from noise — the **excess**
and how exactly the candidate matches it. Filtering to an excess of 2% or more
*and* a candidate matching it to within 0.1% leaves **19**.

A second, sharper screen with no coincidence risk at all: **a country cell equal
to the printed Tier-1 while other countries also appear.** Ten commodity-years.

Adjudication is then mostly automatic, from two pieces of evidence the payload
already holds — does the candidate have a **twin** (another country with the
identical figure), and is its name a **subtotal name**?

## Class 1 — one place under two names

Thirteen name pairs, 33 commodity-year instances, each carrying the **identical
figure**: `Mauritius`/`Mauritius And Dependencies` (8), `Turkey`/`Turkey Asiatic`
(7), `Tunis`/`Tunisia` (3), `Hayti And St Domingo`/`Hayti And St. Domingo` (3),
`West Africa Foreign`/`West Africa, Foreign` (3), `Aden`/`Aden And Dependencies`
(2), `The Gold Coast`/`The Gold Coast Colony`, `French`/`French Possessions`,
`East Coast Of Africa Portu Guese`/`East Coast Of Africa, Portuguese`, and more.

`reference/country_standardize.csv` already maps most of these — but it is
consumed by `countrykey.py` and `widen_country_year.py`, **not** by
`build_viz_payload`. Applying the whole crosswalk here would rename every country
in the payload and, worse, its `summed_subregion` rows would fold sub-regions into
parents and change real totals. So the fix is deliberately the narrowest rule that
removes the double count and nothing else:

> drop a cell only when another cell in the same commodity, unit and year holds an
> **identical non-zero figure** and its name is a prefix of, or prefixed by, this
> one once punctuation and spacing are ignored. Keep the shorter name.

Identical figures are what makes it safe: two genuinely distinct origins do not
report the same quantity to the digit under kindred names.

## Class 2 — a subtotal wearing a country's name

Proven by exact equality with the anchor, not inferred:

| commodity | year | the cell | reads |
|---|---|---|---|
| `Lac, Seed, Shell, Stick, And Dye` | 1884 | `British India` = 112,479 = the Tier-1, with its own six parts listed beside it summing to the same | 2.000 |
| `Part Wrought` | 1893 | `United States Of America` = 4,241 = the Tier-1, six other countries listed | 2.000 |
| `Nuts And Kernels — For Expressing Oil Therefrom` | 1876 | `West Coast Of Africa Foreign` = 31,471 = the Tier-1 | 1.939 |
| `Steel — Unwrought` | 1874 | `Other Countries` = 7,334 = the Tier-1 | 1.517 |
| `Yarn And Waste Of` | 1881 | `All Countries` — the total line itself | 1.062 |
| `Books` | 1887 | `British Possessions` — a possessions subtotal | 1.039 |

Plus two twins the kindred-name rule cannot see because the names share no
prefix: `Rice` 1895, where `Bengal` and `Burmah` **each** carry 2,864,646 (the
printed line is *Bengal and Burmah* and both halves were given the combined
figure), and `Spices — Unenumerated` 1877, where `East Coast Of Africa Native
States` equals `Native States`.

Ten year-scoped `drop-country` rows, each naming its own evidence.

## Result

**16 cells better, 0 worse. exact01 3,723 → 3,738 of 9,509 (39.3%).**

## Recorded honestly

- **`Cheese — Imitation Cheese` 1893-95** reads exactly 2.000 on two cells that
  *both* equal the Tier-1 — `United States Of America` and `Other Foreign
  Countries`. One is a restatement; the residual is dropped as the likelier
  artifact. **The metric is identical either way; the attribution is not.** This
  is a choice, not a proof, and is marked as such in the curation note.
- **Three of the ten rows were inert on the first attempt** — written
  `United States of America` where the node carries `United States Of America`.
  `drop-country` matches commodity and country strings exactly. Same trap as
  `supersede` and `manual_replace`.
- **Seven of the 19 strong candidates have no automatic evidence** and are NOT
  acted on: `Cotton` 1873 (Turkey), `Vinegar` 1895 (Germany), `Linen — Yarn` 1884
  (France), `Part Wrought` 1894 (Holland), `Caoutchouc — Manufactures Of` 1872
  (Canada), `Manufactures Of Iron And Steel — Tyres` 1895 (Germany),
  `Animals, Living — Stallions` 1896 (Australasia). Each closes its year exactly,
  but the candidates are ordinary origins with no twin and no subtotal name, so
  they need the page. **A screen that closes the arithmetic is not a proof of
  which cell is wrong.**
