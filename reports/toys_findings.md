# Toys 1880: an export table standing in for the imports, and the real one in the other engine

Worked 2026-08-01 (`/loop /next-defect`), bracketed-gap rank 3, GBP 1.04M.
**`Toys` 1880 went from 0.118 to exactly 1.000000** — 577,397 of a Tier-1 of
577,397.

**exact01 3,547 → 3,548, under 287 → 286, denominator unchanged at 9,497. One
commodity-year changed in the whole corpus; zero regressions.**

`Toys` is exact in 1872-79 and 1882-92; 1880 was its only broken year.

## Two defects, stacked

### 1. What was there was an EXPORT table

The 68,160 the payload carried was six two-up gap-fill rows:

| Australia | British India | United States | Other Countries | BP South Africa | Straits Settlements |
|---|---|---|---|---|---|
| 23,067 | 16,135 | 15,071 | 7,723 | 4,480 | 1,684 |

That is a **destination** list. Britain did not import toys from the Straits
Settlements or British India — it exported them there. The commodity was
showing readers a fabricated origin profile whose largest source was Australia.

**`scripts/detect_export_leakage.py` did not flag it.**

### 2. The real import table is Infinity-only, and `infonly` could not reach it

**Chandra's parse has no `as_1880 TOYS` block at all** — so the block never
entered `reconcile_country`, which arbitrates only blocks the primary engine
found. The Infinity-only admission path (integrate_sources step 2) could not
rescue it either, because **that path admits only commodity-years ABSENT from
consensus, and this year was occupied by the leaked export rows.**

**That is the general shape worth carrying: an export table leaking into a year
does not merely add wrong data — it BLOCKS the gap-fill path that would
otherwise have supplied the right data.** The two defects protect each other,
and neither screen sees the pair.

Infinity parses the true table at seq 1571-1577:

| Germany | Holland | Belgium | France | United States | Other Countries |
|---|---|---|---|---|---|
| 106,419 | 329,563 | 51,612 | 79,505 | 9,668 | 630 |

A German-and-Dutch toy-import list, which is what the trade actually was.
**The six members sum to 577,397 = the Tier-1 to the digit.**

## Cross-print arbitration on the total

Infinity's own block-TOTAL row reads **577,897**. **Chandra's raw text prints
577,397**, and the members close on that exactly — so 577,897 is a single-digit
misread. Both engines' raw text carry all six member figures identically. The
repair range ends at seq 1576 and excludes the bad total.

## The repair

One `group_repairs` row: `obs_source=inf`, seq 1571-1576, `supersede_years=1880`
— the supersede is what removes the leaked export rows, which arrive via `twoup`
and cannot be displaced any other way (`new_country` cannot suppress a
non-groupfix cell; see `reports/nuts_kernels_findings.md`).

## Still open in this commodity

- **1866-1871 are `nodata`** — six years with a Tier-1 and no origin table found.
- **1893, 1894, 1895 read 1.5652, 1.5047, 1.5600** — a consistent ~1.55 overcount
  across three consecutive comparative-era years, which is a different defect
  and untouched here.
