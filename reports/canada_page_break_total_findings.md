# The previous article's Total block continuing past a page break

*Opened 2026-08-30, diagnosed to an exact two-column proof. **FIXED 2026-08-31** — pass (a'')
in `ca_parse_imports.resolve_lost_labels`, see the resolution at the end of this file.*

## The defect

FY1886 t525 is the largest single country-`'?'` concentration in the corpus:
**$1,644,588**, 55% of all country `'?'` (which totals $2,995,783).

Row order as parsed:

```
article_province_total  Yarn, knitting…   TOTAL           Ontario         95,959
article_province_total  Yarn, knitting…   TOTAL           Quebec          67,064
article_province_total  Yarn, knitting…   TOTAL           Nova Scotia      8,024
article_province_total  Yarn, knitting…   TOTAL           New Brunswick   12,082
detail                  All other fabrics Great Britain   Manitoba         3,107   <-- wrong
detail                  All other fabrics Great Britain   Br. Columbia     2,592   <-- wrong
detail                  All other fabrics Great Britain   P. E. Island     1,263   <-- wrong
country_total           All other fabrics Great Britain                  190,091   <-- wrong
detail                  All other fabrics ?               Quebec       1,186,452
detail                  All other fabrics ?               Nova Scotia    178,050
detail                  All other fabrics ?               New Brunswick  177,967
detail                  All other fabrics ?               Manitoba        43,584
detail                  All other fabrics ?               Br. Columbia    29,946
detail                  All other fabrics ?               P. E. Island    28,589
country_total           All other fabrics ?                              (blank)
detail                  All other fabrics United States   Ontario         44,670
detail                  All other fabrics France          Ontario         94,879
…
```

Two tells. The Yarn TOTAL block is missing exactly Manitoba, British Columbia
and P. E. Island — and the three rows that follow it carry exactly those three
provinces. And the `'?'` run is missing exactly Ontario, the one province the
runs after it do carry.

## The proof — exact in both columns

The three rows labelled `Great Britain` are the **Yarn** article's province
totals for Manitoba / BC / P. E. Island, and the row parsed as Great Britain's
`country_total` is the **Yarn article's grand total**:

| | val_imp | val_efc |
|---|---:|---:|
| Yarn province totals present (Ont, Que, NS, NB) | 183,129 | 183,274 |
| rows mislabelled `Great Britain` (Man, BC, PEI) | 6,962 | 6,853 |
| **sum** | **190,091** | **190,127** |
| row parsed as `Great Britain` country_total | 190,091 | 190,127 |
| difference | **0** | **0** |

Exact in val_imp *and* val_efc. There is no combination-search here: the
province split is fixed by the print order, and both columns close on the
first reading tried.

## What it means

The Yarn article's Total block ran over a page break. Its last three province
rows and its grand total landed on the new page, where the next article's first
country label (`Great Britain`) slid up onto them. The genuine first country of
"All other fabrics composed wholly or in part of wool" then had no label left,
opening the `'?'` run.

That `'?'` run is almost certainly **Great Britain**: it is the dominant source
for wool fabrics, it is missing only Ontario (whose row will be at the tail of
t524, the previous page), and every other country in the block is a
single-province run. That last step is inference, not arithmetic — the article
has **no** `article_total` and no `article_province_total` of its own in the
parsed rows, so there is no in-table anchor to close it against. Confirm
against the printed Abstract cell or the t524 tail before assigning the label.

## Why the existing passes miss it

- `_fix_grand_total_on_country_row` (line 1010) handles a different shape: the
  grand total riding the **last** country-labelled detail of the article's own
  block. Here it rides an **early** row, and the block it belongs to is the
  *previous* article's.
- Pass (a) — "a LEADING country_total equal to the province totals = old
  article's grand total", 349 hits — is the right family, but it reassigns the
  `country_total` row alone. This case needs the **k preceding detail rows** to
  go back to the old article's Total block as well. The signature that makes
  that safe is the province complementarity: the old Total block is missing
  exactly the provinces the mislabelled rows carry, and the sum closes on both
  columns.

## Still open

1. Extend pass (a) to carry back the k preceding rows when (i) the previous
   article's Total block is missing exactly those provinces, (ii) the sum
   closes exactly on the trailing `country_total` in **two** columns. Guard:
   never fire when the old block is already complete.
2. Then name the freed `'?'` run — by the t524 tail or the Abstract, not by
   assuming Great Britain.
3. Re-check the other country-`'?'` concentrations for the same signature:
   FY1885 t270 ($286,776), FY1890 t556 ($183,336), FY1881 t566 ($108,163).
   The FY1881 table also carries the largest article-`'?'` mass in that year,
   so it may be one defect, not two.


## Resolution (2026-08-31)

Pass (a'') in `resolve_lost_labels`, inserted between (a') and (b). Trigger: an
`article_province_total` run with no grand total of its own, then in the following
block(s) 1–4 detail rows whose provinces strictly continue the Total run's province
order, then a `country_total` equal to sum(Total run) + sum(those rows) **to the
dollar in both value columns**. The rows go back as the old article's Total tail
(they may bear the hijacking country's label or heading junk — FY1881 t566's tail
spans two blocks, so the closing total is required in the LAST carried row's block,
not the first).

**The freed `'?'` run is the hijacker's own block, and that is provable, not
assumed**: the label that slid up is the label the print gave the block that
follows. FY1882 t442 proves it in-table — Melado's printed Quebec province total
160,514 closes exactly (58,178 + 8,458 + 93,878) only with the `'?'` row counted,
and the hijacking label there was United States, which the printed Abstract
confirms (US Quebec returns to −16K of print with the restore, −89K without).
So the pass restores the hijacker's label to the immediately following `'?'` run
(`pagebreak_hijacker_restored`, with `row_kind` normalised from `detail_lostlabel`
so the later lost-label segment pass does not re-clear it — that re-clearing
silently undid the first version of this fix).

**34 carry-backs, 125 restored rows across 1880–1886.** Ship test vs the
pre-fix snapshot: 20 BETTER / 9 WORSE cells; country-`'?'` $2,995,809 →
$945,345 (−$2.05M; FY1886 −$1,644,588 = the full t525 mass), article-`'?'`
−$150K. FY1886 abstract ratio 0.975 → 0.991, FY1885 0.987 → 0.990. The worse
cells are sub-$30K drifts on cells polluted by other defects (1886 GB NS/BC
carry pre-existing overs now unmasked).

Of the re-check list: FY1885 t270 and FY1881 t566 were this class and are fixed.
**FY1890 t556 is NOT this class** — its `'?'` runs (Jute cloth $175K) are a
page-top block with the article labelled but the first country lost, no preceding
Total block to close against; it stays open for the abstract-fit/witness phases.
