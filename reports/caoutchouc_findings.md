# Caoutchouc: one glue label over four tables — DIAGNOSED, NOT CLOSED

Session 11, iteration 49 (2026-07-27). `Caoutchouc` was the top non-sugar item
on the re-ranked board — **GBP 38.5M across 13 off-cells**:

```
1872 0.067  1878 1.107  1882 0.897  1885 0.889  1886 0.840  1887 0.864
1893 1.088  1894 1.211  1895 1.406  1896 1.169  1897 1.065  1898 1.117  1899 0.943
```

**It does not close, and no data change was made.** What follows is the
evidence, because two parts of it are decisive and will save the next attempt
the discovery work.

## Proof 1 — T1 1894-1898 is exactly the block's own printed subtotals, but the British-half total rows carry the WRONG YEAR

The whole 1893-99 era is carried by one multi-year comparative block in as_1898,
sitting under the glue label `CAOUTCHOUCC | Eastern Coast of Africa`. Its printed
foreign and British subtotal rows reproduce the Tier-1 series **exactly** —
once the British rows are shifted back one year:

| year | printed foreign | printed British | sum | T1 |
|---|---|---|---|---|
| 1894 | 228,048 | 74,403 | **302,451** | 302,451 ✓ |
| 1895 | 237,957 | 103,596 | **341,553** | 341,553 ✓ |
| 1896 | 309,291 | 121,857 | **431,148** | 431,148 ✓ |
| 1897 | 272,872 | 124,057 | **396,929** | 396,929 ✓ |
| 1898 | 355,169 | 134,412 | **489,581** | 489,581 ✓ |

Five years, five exact hits. But the parser labelled the British and grand total
rows `1894, 1896, 1897, 1898, 1895` — the *values* are in printed column order,
the *year labels* are not:

```
row_seq 1971-1975 (British)  74,403 / 102,596 / 121,857 / 124,057 / 124,412
                     years    1894  /  1896   /  1897   /  1898   /  1895
```

Two of those five values are also single-digit misreads against the table above
(102,596 for 103,596; 124,412 for 134,412) — each corroborated by the T1 sum, not
guessed at.

The foreign half is *correctly* year-assigned: its members for parser-1895 sum
**237,932** against the printed 237,957, 25 short. So the year-label defect is
confined to the British/grand total rows.

**Consequence already visible in the payload:** the 1895 British-possessions
total **103,596 is being counted as a COUNTRY named `west coast of africa`** —
the subtotal-as-country class, and by itself a quarter of that year's 1.406.

## Proof 2 — the label covers FOUR consecutive tables, and table 3 leaks into every year

`CAOUTCHOUCC | Eastern Coast of Africa` runs across four printed tables. For
1895 the boundaries are:

| table | seq | foreign TOTAL | British TOTAL | grand |
|---|---|---|---|---|
| 1 — caoutchouc, the real one | 1748-1980 | 237,957 | (103,596) | 341,553 |
| 2 — a Lbs-denominated table | 1985-2045 | 4,611,269 | 58,629 | 4,669,898 |
| 3 — a Cwts table, Canada 1,432,181 | 2050-2131 | 862,390 | 1,477,062 | 2,339,452 |
| 4 — Imitation Cheese | 2135-2146 | 68 | — | 68 |

Table 2 supplies the payload's `Germany [unit Lb] 2,010,560`, `France [Lb]
602,102` and friends. Table 3 supplies **`Australasia : New Zealand`, which
appears in the caoutchouc payload in every year 1894-98**:

```
1894 45,898   1895 44,439   1896 74,894   1897 55,095   1898 69,253
```

It is not caoutchouc. The real caoutchouc `Australasia` row is in table 1 at seq
1960 and reads **961** for 1895. New Zealand's figures come from seq 2095-2126,
inside table 3's British half, whose own total is 1,477,062.

Removing that leakage alone moves the years to roughly 1.059 / 0.973 / 0.995 /
0.926 / 0.976 — closer in four of five, further in 1897, and **exact in none**.
That is why nothing was applied: the residual is a genuine second gap and a
partial patch would make the eventual full repair harder to reason about.

## What the repair actually needs

1. A full re-admission of **table 1 only** (seq 1748-1980 for the 1893-99 era),
   with the other three tables excluded by seq range — the same shape as the fir
   and oats repairs.
2. The same treatment for the as_1899 copy, and a supersede covering **every**
   engine's stale label (`CAOUTCHOUCC` in Chandra, and whatever Infinity and the
   two-up parse call it) — the iteration-46/47 lesson.
3. The British-half **year labels are wrong in the total rows**; check whether
   the British *member* rows share the shift before trusting them. For
   parser-1895 the British members sum **117,081** against a true 1895 British
   total of 103,596 and a 1896 total of 121,857 — they match neither, so this is
   unresolved and is the thing that defeated the iteration.
4. The 1872-1887 half (six cells, 0.067 to 1.107) was not examined at all.

## Still open

- **All 13 cells.** Nothing applied; baseline unchanged.
- `Caoutchouc` is a multi-mechanism commodity — four-table glue, mixed Cwt/Lb/`?`
  units, region headers absorbed as countries, subtotals absorbed as countries,
  and a year-label shift. It wants a dedicated session rather than a slot in the
  defect loop.
