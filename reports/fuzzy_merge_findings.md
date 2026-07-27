# Fuzzy-merge findings — `build_viz_payload.py`'s edit-distance net

`build_viz_payload.py` merges two commodity signatures when they have the same
token count and every token pairs up either exactly or within edit distance 2
(both tokens length ≥ 5, same first letter). It exists to absorb OCR garbles
(`CAOUCHEUC` → `CAOUTCHOUC`, `MYRBOLAMS` → `MYRABOLAMS`). Its failure mode is
**two distinct real English words that happen to sit 2 edits apart**, which the
net silently fuses into one commodity. `FALSE_PAIRS` is the exemption list.

The full merge set is exported to **`reports/fuzzy_merges.csv`** (134 merges
after the fixes below). Re-export it after any change to `toks()`, `sig_of()`
or the merge rule, and re-read the real-word pairs — this is the only place the
conflations are visible.

## 2026-07-27 — `HORNS` ↔ `HORSE` (the `Horse` 1874 outlier)

`Horse` (horse hair, Cwt) ran at **6.79× its printed T1 in 1874** and was the
last entry in `reports/volume_row_outliers.csv` with a blown year. It was not a
glue block in `country_obs`.

- The genuine block is `as_1874` seq **734-741**: Russia 3,109 / Germany 6,819 /
  Brazil 366 / Uruguay 3,022 / Argentine Republic 4,313 / Australia 647 /
  Other Countries 796, printed **TOTAL 19,102** — the T1 figure to the digit.
- The four intruders were rank-3 cells Belgium **69,180**, USA **22,553**,
  Holland **13,231**, France **5,725**. They are
  `HIDES, NOT TANNED, TAWED, CURRIED, OR IN ANY WAY DRESSED | Horns`, 1874,
  `source='infonly'` — i.e. the infinity engine's reading of the **hops** origin
  block, misfiled under a hides/horns heading. (Consensus `HOPS` 1874 carries
  Belgium 69,480, USA 22,553, Holland 13,231, France 5,725; the infinity copy
  differs by one digit in Belgium's quantity and Germany's value.)
- `HORNS` and `HORSE` are both length 5, share a first letter and sit 2 edits
  apart, so the net fused `{HORNS}` into `{HORSE}` and every `Horns`-labelled
  cell became horse hair.

**Fix**: `('HORNS', 'HORSE')` added to `FALSE_PAIRS`.
**Effect**: `Horse` 1872 1.337 → **1.0000**, 1874 6.793 → 0.998,
1876 1.476 → **1.0000**, 1877 1.048 → **1.0000**. A whole-payload ratio-class
diff moved **only those four cells** — nothing else regressed.

## 2026-07-27 — `STAVES` ↔ `SLATES` (found by the same audit)

Auditing all 135 merges surfaced a second real-word pair. `STAVES` (timber
staves) was being merged into `SLATES` (roofing slates), which is why `Slates`
showed **0 exact of 7** T1 years: its origin cells were inside the Staves
commodity under Staves' modal unit and never reached the reconciliation.

**Fix**: `('STAVES', 'SLATES')` added to `FALSE_PAIRS`.
**Effect**: four `Slates` commodity-years that were `nodata` now carry country
sums, and **1895 and 1898 close EXACTLY** on their own printed T1, 1896 at
0.997. That closure is the proof the split is right, not the count.

## Baseline

`scripts/reconcile_baseline.py`, both fixes applied:
`exact01` **2,750 → 2,755**, `over` **235 → 232**, within 5% GBP-weighted
66.1% → **66.2%**; within 0.1% GBP-weighted unchanged at 48.1%. The
commodity-year universe grows 9,935 → 9,940 because splitting a fused signature
splits its T1 series too.

## Measured and rejected — do not re-test

Each candidate real-word pair was added to `FALSE_PAIRS` on its own and the
baseline re-measured. **Zero effect** on `exact01` or `over`:

| pair | verdict |
|---|---|
| `CLOVES` / `CLOCKS` | still looks semantically wrong; carries no anchored country data |
| `CHINESE` / `CHEESE` | same |
| `SLABS` / `SLATE` | no effect |
| `BONES` / `BOXES` | no effect |
| `GRASS` / `GLASS` | plausible genuine garble (`Glass, Unenumerated`) |
| `BUTTON` / `BUTTER` | no effect |
| `PEATS` / `PELTS` | genuine garble — `Goat Skins, Pelts, Undressed` |

`HOOPS` → `HOOFS` was left merged deliberately: it always co-occurs with the
token `HORNS`, and "Horns and Hoofs" is the printed commodity, so `Hoops` there
is a garble rather than timber hoops.

## Still open

- **`Horse` 1874 residual 30 cwt.** The seven printed country lines sum 19,072
  against the printed TOTAL 19,102 (0.16%). Only one engine read the block — the
  infinity engine's `HAIR | Horse` 1874 (seq 428-432, TOTAL 2,464) is a
  different, partial table and cannot arbitrate. **Page-image candidate**: either
  a country line was dropped or one cell/the total has a digit error. Not
  guessable.
- **`Horse` 1893-1898 residuals** — 1.014 / 1.016 / 1.004 / 0.980 / 1.036 /
  1.003. Small, unexamined.
- **`Slates` 1897 at 0.722** — only visible after the de-merge.
- **`HIDES, NOT TANNED … | Horns` 1874 `infonly` rows are a mislabelled HOPS
  block.** Harmless to `Horse` now, but still wrong where they sit, and they are
  a duplicate of a consensus block that already exists.
