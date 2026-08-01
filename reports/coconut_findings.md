# Coco-nut 1876: the gap is illusory, and the real finding is a four-way split

Worked 2026-08-01 (`/loop /next-defect`), bracketed-gap rank 3, GBP 532k.
**No data change this iteration** — the item resolves to a taxonomy decision and
is escalated rather than decided alone.

## The 1876 table is parsed, correct, and complete

`as_1876` seq 1215-1220, under `OIL | Coco-nut`:

| Mauritius | British India: Madras | Ceylon | Australia | Other Countries | **Total** |
|---|---|---|---|---|---|
| 15,901 | 47,472 | 126,313 | 4,118 | 5,627 | **199,431** |

The five members sum to **199,431 = the printed Total = the `Cocoa Nut` 1876
Tier-1, to the digit**, and they feed `Oil — Coco-Nut`, **which reads 1.0000 in
1876**.

**So the ranked gap is genuinely illusory** — the year closes, under a
differently-named node.

## The real finding: four nodes for one printed line

| node | T1 years | countries | origins |
|---|---|---|---|
| `Oil — Coco-Nut` | 21 | 26 | the real series |
| `Coco Nut` | 33 | 6 | **1885 only** |
| `Cocoa Nut` | 10 | 13 | **1875 and 1877 only** |
| `Nuts And Kernels — Coco-Nut` | 5 | 43 | 1883-99 (a genuinely different line) |

`Coco Nut` and `Cocoa Nut` are **de-headed anchor shadows** — the same printed
line with the `OIL:` section head lost — and they carry the **identical anchor in
every year they share** with `Oil — Coco-Nut` (1872 433,883; 1873 266,798; 1874
134,196; 1875 219,158; 1876 199,431; 1879 199,991; 1880 318,454; 1881 248,412;
1882 133,782; 1883 210,874; 1885 185,496; 1886 156,775 …).

**`Cocoa Nut` vs `Coco Nut` is an OCR-spelling split** — `{COCOA, NUT}` and
`{COCO, NUT}` share no token, so no name-relation test can pair them. **This is
exactly the floor the illusory-gap filter names for itself** (`Sumach`/`Shumach`,
`Slate By Tale`/`Sale`/`Talc`).

## The prize, and why it was not taken

**The shadows hold origins the oil node lacks**, with no overlap:

- `Cocoa Nut` 1875 = **219,158**, and `Oil — Coco-Nut` 1875 is `nodata` with a
  Tier-1 of **219,158** — an exact close.
- `Coco Nut` 1885 = **185,496**, and `Oil — Coco-Nut` 1885 is `nodata` with a
  Tier-1 of **185,496** — an exact close.

Folding both shadows into `Oil — Coco-Nut` would gain **+2 exact01** and remove
two duplicate nodes. **Checked: no year in which a shadow holds origins is a year
the oil node also holds origins, so the fold cannot double-count.**

**Three reasons it was escalated instead of applied:**

1. It merges three payload nodes — a **taxonomy change**, which this loop's
   guardrails reserve for a human decision.
2. `reference/match_declines.csv` line 18 already declines `Oil — Coco-Nut` ←
   `Coco Nut` as *"host `Coco Nut` is a de-headed name; wrong direction."*
   **That decline is correct as written** — the matcher proposed folding the
   *oil* node into the *shadow*. The fold worth making is the reverse, and
   reversing a standing decline should be explicit.
3. The **denominator** would fall by roughly 29 — about 64 commodity-years spread
   across three nodes collapsing to ~35 in one. That is legitimate
   de-duplication (the Stones and Pyrites iterations did the same at −7 each),
   but it is a large headline move and should be expected, not discovered.

## Recommendation

Fold `Coco Nut` and `Cocoa Nut` into `Oil — Coco-Nut`, unscoped, and replace the
line-18 decline with a note recording the correct direction.
