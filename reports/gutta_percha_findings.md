# Gutta percha: five labels, one line, and a re-export table riding as imports

Audited 2026-07-28 at the user's request, teak-style. Before: the plain
`Gutta Percha` label read **0.04–0.11 of its anchor for 1876–1880** while a
sibling `Gutta Percha — Raw` closed exactly and then went orphan; three more
fragment labels carried £158k of phantom or misplaced value. After: **one
commodity, anchors 1866–1900, closing 1.0000 (or within 0.13%) in 26 of 28
origin years 1872–1899.** Fixes are seven `commodity_curation.csv` rows
(2026-07-28 batch), payload-level only.

## What the volumes actually print

Each volume prints up to THREE gutta percha country tables:

1. **`GUTTA PERCHA, RAW`** — the import origin table (Straits Settlements
   dominant, 20–65k cwt/yr). Printed with the `Raw` article to ~1881, then as
   plain `Gutta Percha` — an era split. The two payload labels' T1 anchors are
   **digit-identical in all four overlap years** (1876–79: 21,577 / 26,068 /
   32,912 / 51,416), and `Raw`'s orphan origin sums for 1880/1881 equal the
   plain label's printed anchors **to the digit** (65,856 / 68,445).
2. **A second bare `GUTTA PERCHA` table** — destinations France, Holland,
   United States, 2–12k cwt/yr. This is the **RE-EXPORT table** (foreign gutta
   percha re-exported, principally to the continental cable industry): it
   closes on its own printed Total (1874: Germany 662 + France 1,297 + Other
   492 = **2,451 exact**) and never on the import anchor, and the abstract
   attests a `reexport` Gutta Percha line. With its article lost, the two-up
   gap-fill filed it as imports under the bare group — the same class that
   put export tables inside refined sugar. Its non-colliding cells were the
   whole of the plain label's 1876–80 "origins" (hence 0.04–0.11).
3. **`Manufactures of`** — genuinely tiny (144–488 cwt/yr, `All Countries`
   then Germany-led).

## The fixes (curation batch, in file order)

- **Fold plain `Gutta Percha` INTO `Gutta Percha — Raw`**, not the other way:
  the fold target wins cell collisions, and Raw holds the genuine 1872–74
  France/Holland/Other readings that the re-export strays would otherwise
  overwrite. Then **rename back to `Gutta Percha`**.
- **`drop-country` France 1875–76, Holland 1879–80, US 1880** — the re-export
  cells that did not collide. Anchor-guarded: each fired only because removal
  took its year to 1.0000.
- **Drop `Gutta Percha — From British East Indies`** (£150,933): a
  phantom-region duplicate — its three `?`-unit cells (Straits 22,313,
  British Guiana 1,109, Other British 4) are the main label's own 1887 cells,
  which already close at 0.999.
- **Fold `Gutta Percha — Raw · Manufactures Of` into `— Manufactures Of`**:
  its single cell (All Countries 488, 1872) completes the manufactures series
  1872–1882.

## Still open, with the evidence

- **1874 reads 0.8999 — short exactly 3,000.** Both engines agree on every
  printed member (Holland 2,921 + France 1,046 + Straits 21,085 + Other 1,918
  = 26,970) against the printed TOTAL 29,970, which is also the anchor. A
  member row is missing from both parses. Egypt runs 9,814 (1872) → 4,906
  (1873) → absent, so a lost `Egypt 3,000` row fits the series — **not
  guessed; PAGE-IMAGE CANDIDATE** (as_1874, gutta percha raw table).
- **1891 reads 0.9601.** The consensus holds a `british east indies` parent
  53,625 beside sub-entries summing 50,667 — and the biggest sub-entry label
  is FUSED: `Straits Settlements-Other British East Indian Possessions`
  49,119, two printed rows glued into one cell. Keeping the parent instead
  overshoots (1.0087), so a sub-row's quantity is wrong or a sibling is lost.
  Needs the printed block; queued.
- The re-export table itself (2,023 → 12,323 cwt/yr, 1872–85+) is parsed and
  clean — it belongs to the **export campaign** payload when that opens, per
  [[scope-redirects]].
