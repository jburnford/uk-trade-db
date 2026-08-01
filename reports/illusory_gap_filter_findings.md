# Filtering illusory gaps — and a correction to my own 9% figure

Worked 2026-08-01 (`/loop /next-defect`).
**No data change; baseline unchanged at exact01 3,542 / 9,497.**

## What was built

`find_bracketed_gaps.py` now checks, for every gap-year, whether **another node
carrying the same anchor already closes that year** — the duplicate-label split
that made brass, stones and pyrites three consecutive net-zero iterations. New
columns `dup_years`, `dup_by`, `all_dup`; fully-illusory gaps sort last and are
dropped from the printed ranking.

The check is guarded by the **name relation** from `match_by_name`, and that
guard is not optional: `Manganese, Ore Of` 1891 and `Manures — Phosphate Of
Lime And Rock` share an anchor value in that one year and are entirely
unrelated commodities. Anchor agreement alone is coincidence-grade — the same
lesson the single-year matcher taught.

## Correction: it is 3%, not 9%

Last iteration I reported "**9 of 101** ranked gap-years are illusory … about 9%
of the remaining ranked gap-years are not work at all." **That figure was
wrong.** It counted raw anchor agreement with no name guard, so it included the
Manganese/Manures coincidence and pairs whose names have no relation at all.

With the guard applied the honest number is:

> **3 of 100 gap-years (3.0%), in 2 gaps of 77.**

- `Oil — Coco-Nut` 1885 — fully illusory, closed by `Coco Nut`
- `Leather Manufactures — Unenumerated` 1882 and 1884 — closed by
  `Leather, Undressed — Unenumerated`

**The ranking is not substantially polluted.** The three net-zero iterations
were real duplicate-label splits, but they were the bulk of the population, and
folding them cleared it. What remains is largely genuine work.

## Both survivors are pairs I have already declined

Neither flagged case is new work:

- `Oil — Coco-Nut` → `Coco Nut` is in `match_declines.csv` as **wrong
  direction** — folding a properly headed source into a de-headed fragment.
- `Leather Manufactures — Unenumerated` → `Leather, Undressed — Unenumerated`
  is declined for matching on the **generic article `Unenumerated`**; leather
  manufactures and undressed leather are different printed lines.

So the filter's entire current yield is: *the two illusory gaps left are the
two you decided not to merge, and you were right to leave them in the ranking
as unresolved rather than fold them.* The declines stand.

## Known limitation: OCR spellings are invisible to it

`Sumach` and `Shumach` are the same commodity and close each other's years, but
their signatures are `('sumach')` and `('shumach')` — **different tokens, no
relation, not flagged**. The same applies to `Slate By Tale` / `Sale` / `Talc`.

**No signature test can pair an OCR misspelling with its correct form**, so this
filter will always under-report duplicates in exactly the families where the
spelling is damaged. That is a floor on the check, not a bug to fix here.
