# Coffee — Raw: a duty page read as countries, twice over

Session 11, iteration 54 (2026-07-27). `Coffee — Raw` — **GBP 20.6M**, two
off-cells and both of them spectacular:

```
1880  243.837x        1897  2.618
```

Neither anchor was at fault (checked first, per the standing rule): 1880 is
1,546,451 tier A on four volumes, 1897 is 756,482 and confirmed by four more.
Both years were **article names and table headers read as countries**.

## 1880 — a whole multi-commodity duty page under one label

`as_1880 | COFFEE` with a NULL article runs from seq 29 to 231. Coffee's own
origin block is **rows 29-53**. Rows 55-109 are a run of entirely different
commodities — Collodion, Ether, FRUIT (Currants, Figs, Plums, Prunes, Raisins),
Malt, Naphtha, Pickles, Plate, Soap, SPIRITS (Rum, Brandy, Geneva) — and their
run-on article lines became countries:

```
'Prunes: From France - - - - " Other Countries'                  362,501,129
'Plums (French) and Pruneloes: From France - - - - " Other …'     13,029,327
```

Both are fused multi-column digit strings, and between them they are the entire
243x. Restricting the block to the coffee rows leaves members at **1,546,419**
against T1 **1,546,451** — 32 short.

Note which figure the members corroborate: as_1880's own printed total reads
**1,546,151**, a 4-for-1 misread. The members agree with the **anchor**, not with
the printed row beneath them.

### An unbalanced parenthesis, worth 22,945

The first attempt landed at 0.985 instead. `West Coast of Africa (Foreign)`
passes through `fold_country` as **`West Coast Of Africa (Foreign`** — the
closing bracket is eaten, and the surviving open paren makes every consumer treat
the cell as a drill-down and drop it. That is 22,945, the exact residual. A
per-row relabel to `West Coast of Africa, Foreign` closes the year.

> **Rule.** A parenthesis in a country label is a de-duplication instruction, so
> an *unbalanced* one silently deletes the cell. Worth a corpus sweep: any
> `country` in `country_year_final` containing `(` with no `)`.

## 1897 — the home-consumption table's column headers

The overage is a duty / home-consumption table glued into the origin block, with
its **column headers read as countries**:

```
Entered - 1897  248,411      Entered - 1896  247,956
Entered - 1895  240,545      Entered - 1894  241,522
Retained for H. C  237,987
Deduct—Exported on Drawback, Over Entered, &c  4,250
Kiln Dried, Roasted, or Ground  1,893          Entered  1,893
```

All eight arrive under `COFFEE` with an **empty article**, from the two-up and
run-in parses — one supersede key covers the lot.

Three volumes carry the real block and all three close on the printed grand
**756,482 = T1**; as_1899's copy is used because it is the only one with units.
The range stops at 25918 to exclude row 25923, `British East Indies` 161,493 —
the printed **British TOTAL** wearing the last sub-entry's head (its members sum
to 161,493 exactly), which would have doubled the British half.

## Result — and one regression

```
1880  243.837188 -> 0.999979   EXACT
1897    2.618407 -> 0.999967   EXACT
1898    0.996663 -> 0.999129   EXACT      (bonus)
1895    0.999758 -> 1.002271   REGRESSED  (exact01 -> within5)

exact01 2,793 -> 2,795 ; within 0.1% GBP 52.3% -> 52.6% ; over 214 -> 212
denominator UNCHANGED at 9,940
```

**The 1895 regression is real and is stated rather than hidden.** The as_1899
block is a 1895-99 comparative whose year columns **interleave by `row_seq`**, so
a contiguous seq range unavoidably carries a few cells of the neighbouring years.
Only 1897 is superseded, so those extra cells are added only where the other
years' consensus lacks that country — which for 1895 is 1,758 cwt, 0.23%.

Superseding the other years instead is **not** the answer: on this range the
block closes only for 1897.

```
1895 0.968   1896 0.966   1897 0.99997   1898 0.987   1899 0.987
```

Net for the iteration: three cells gained, one lost.

## Still open

- **`Coffee — Raw` 1895**, now 1.0023. Fixing it means either a seq range that
  can select a single year column — which `group_repairs` cannot express — or a
  separate block admission tuned to 1895's own row extent.
- The **year-interleaved comparative** is a structural limitation worth naming:
  `group_repairs` selects by `row_seq` alone, so for any 1893+ comparative the
  repair leaks into adjacent years. Every such repair so far has been lucky in
  that the leaked cells were already present in consensus. A `years` column on
  `group_repairs` would remove the whole class.
