# Bracketed-gap campaign — state and open items

Started 2026-07-28 (Fable, at the user's request: "commodities with data,
then a gap, then data again — a data problem, not a change in trade").
Instrument: `scripts/find_bracketed_gaps.py` -> `reports/bracketed_gaps.csv`
(ranked by GBP at stake; re-run after any payload rebuild).

**The method that worked**: for a hole year, the missing table's own printed
TOTAL must equal the anchor — search BOTH engines' obs tables for that exact
number under ANY label. It found the table (or proved the anchor wrong) in
six of eight hunts.

## Fixed (commits 3666047, 2f696d1, 48d485d — see messages for full proofs)

boots 1887-90 (as_1891 gloves-column slip; manual_t1), chemical products
(hyphen split), almonds (interleaved labels), cocoa 1883-85 (phantom-region
folds), glucose (era split), woollen rags (five heads), tanning bark
(era folds, partial), spices pepper+unenumerated 1889/90 (glue block +
supersede), sheep 1887 (garbled continuation head), iron ore 1894 (era head).

## Diagnosed, NOT fixed — evidence gathered, ready to work

- **Sardines 1895 ANCHOR SLIP** (read 0.13): the payload T1 1,082,588 is the
  `FISH | Cured or Salted, unenumerated` 1895 total to the digit (printed
  as_1895/as_1897/as_1898). Sardines' true 1895 reading (~140k cwt by series
  shape) needs the abstract vote dump for the sardines label across volumes,
  then a manual_t1 row. Same class as boots 1887-90.
- **Spirits `Unenumerated, Not Sweetened` 1876 + 1887 ANCHOR SLIPS** (holes):
  T1 1876 = 2,324,405 = as_1876 FRUIT|Raisins block total; T1 1887 =
  2,340,078 = as_1887 SPIRITS|Rum block total. Both anchors are other lines'
  figures; no origin table can match them. Find the true readings in the
  abstract vote, manual_t1.
- **China/Porcelain 1883-85** (read 0.05/0.05/0.00): the tables are GLUED
  under CHEMICAL MANUFACTURES labels. as_1883: group `CHEMICAL MANUFACTURES
  and PRODUCTS. Unenumerated`, article `Other Vegetable matter applicable to
  the uses of Chicory or Coffee` — members (Germany 37,110 + Holland 60,103 +
  Belgium 12,179 + France 24,807 + China 3,902 + Japan 4,821 ...) sum to the
  china T1 146,471 EXACTLY. as_1884: same group, article None (T1 143,556
  exact); as_1885: `Vegetable matter applicable...` (T1 146,830 exact).
  Needs seq-scoped group_repairs (find the seq ranges; the chicory line's own
  small table is adjacent — split carefully).
- **Feathers Ornamental 1883** (read 0.10) and **Drugs Unenumerated 1879**
  (hole): NO total matching the anchor in either engine — lost block or
  wrong anchor. Page-image candidates. (Drugs 1880/81 near-misses at
  663,459/854,322 are OTHER tables — not matches.)

## Residues from the fixed families (small, with evidence)

- Gutta percha 1874 short EXACTLY 3,000 (lost row, Egypt fits the series —
  not guessed); 1891 fused sub-entry label. reports/gutta_percha_findings.md.
- Cocoa 1882: NO import block in either engine (both carry only the
  re-export table, Total 8,429,893 closing on itself). 1885 residual 0.92.
- Chemical products 1873/1875 read 1.30-1.32 (country-name variants double-
  counting inside the union) and 1881 0.90.
- Bark 1880 (0.889), 1881 (1.360); 1892-99 era copies over-count 1.2-1.5x
  on country-name variants — needs per-country reconciliation, NOT a fold.
- Sheep 1887 seq 45: 5,524 with the country label absorbed into the article
  text ('Sheep and Lambs') — the block's missing 0.57%; page-image for name.
- Boots 1886: anchor sits under the `Leather Manufactures` label-key split
  (the payload label pair 'Boots And Shoes' / 'Leather Manufactures — Boots
  And Shoes' is a headless-vs-headed era pair the fold pass cannot see).

## Known-and-queued items the screen keeps re-finding (do not re-diagnose)

Sugar Unrefined 1874 (no block in either engine), Caoutchouc — Manufactures
Of 1892-98 (printed anchor scope change, session-11 iteration 11), Mahogany
1886-88/1892 (no table on either half, iteration 12).

## Instrument gaps worth building (from the gutta percha post-mortem)

1. Detector A's token-subset clustering silently UNIONS split labels; when
   the cluster closes but a member with its own anchor reads <0.6 or >1.9
   alone, emit that as a 'split-label' finding. Would have caught gutta
   percha and enumerates the class.
2. Headless-vs-headed era pairs with digit-identical T1 overlap (gutta
   percha Raw, boots/leather) — a screen for that signature.
