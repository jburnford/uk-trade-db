# Flow-misfile screen round 2, and two negatives worth keeping

Worked 2026-08-01 (`/loop /next-defect`).
**No data change; baseline unchanged at exact01 3,539 / 9,511.** A tooling
iteration with three results, two of them negative.

## Why re-run the screen

`detect_flow_misfile.py` found two candidates when it was built (iteration 22).
Last iteration I found a **third and fourth** by hand — `as_1892` house frames,
£675,138, an import table under the export flow. **The screen should have found
it and did not**, so the screen was wrong, not the corpus.

## Two real blind spots, both now fixed

1. **`WHERE ... AND quantity > 0`.** The house-frames block has no quantity
   column at all — it is a value-only table — so it was invisible before any
   name matching happened. Now `coalesce(quantity, value)`.
2. **Exact signature equality.** The export label carries extra tokens:
   `House Frames, Fittings, Joiners' and Cabinet Work` against an import
   commodity of `House Frames, Fittings, and Joiners' Work`. Added a
   strict-subset fallback requiring ≥3 tokens and a unique candidate.

**Re-run: 0 candidates.** Both earlier finds and both hand finds are repaired,
so the screen correctly reports nothing outstanding. That is a clean result,
but it is not evidence the fixes work — so I checked directly, and they do not
fully.

## The real reason house frames was missed: an un-decoded HTML entity

The import anchor's article is **`House Frames, &amp;c.`**. `V.sig` sees
`&amp;c.` and produces the tokens **`amp`** and **`c`**, so the anchor signs as
`amp+c+frame+house` while the export block signs as
`cabinet+fitting+frame+house+joiner+work`. They share only two tokens. **Neither
exact nor subset matching can ever pair them**, and my subset fallback does not
find it either — I verified that against the known case rather than assuming.

Scope of the contamination in `consensus`: **76 distinct article values and 7
distinct group values, 1,022 rows**. `&amp;` is the only entity present — no
`&quot;`, `&lt;`, `&#`.

### Measured before proposing: it is cosmetic

Fixing this means decoding the entity inside `V.sig`, which **re-signs the whole
corpus** and would change `country_year_final` grouping — the class the working
rules say to stop and ask about rather than decide alone. So I measured the
prize first:

- payload nodes carrying the entity in their displayed name: **5**
  (`Of Europe, &Amp;C.`, `Sawn Or Split Deals, Battens, &Amp;C`, …)
- node pairs that would **merge** if it were decoded: **0**

So the contamination costs **no closure at all**. It is a display defect on five
map labels and a latent trap for future signature matching, not a data defect.
**Not worth a corpus-wide re-sign; queued as a cosmetic rename instead.**

## The ranked item: `Skins — Sheep And Lamb, Undressed` 1881 — NOT RECOVERABLE

£1.28M, the only hole in a series with countries for every year 1872-1895.

`as_1881` contains **no import block** for this commodity in either engine —
the import SKINS blocks are Goat, Unenumerated and Manufactures only. The one
sheep-and-lamb block present is `reexport`, and it is **genuinely a re-export
table**: it totals **1,123,028** against an import anchor of **6,475,264**, so
it is not a misfiled import. A printed-total hunt for 6,475,264 across `as_1881`
and `as_1882` returns nothing but a coincidental maize row.

**Verdict: page-image job**, alongside feathers 1890 and nuts 1875.
