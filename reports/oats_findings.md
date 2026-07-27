# Oats: a repaired block with no supersede, beside its own voted copy

Session 11, iteration 47 (2026-07-27). `Oats` was the top non-sugar item on the
GBP-ranked board — **GBP 61.2M**, three off-cells:

```
1895 1.064    1897 0.892    1898 0.877
```

## Root cause

The oats origin table is not printed once per volume. It is carried by
**multi-year comparative blocks** sitting under stale glue groups — `CORDAGE`
in as_1897 and as_1899, `CHINA, OR PORCELAIN, AND EARTHENWARE` in Infinity's
as_1897/as_1898, `CHEESE` in Infinity's as_1899. `group_repairs` line 18 relabels
the as_1897 block into `CORN AND GRAIN | Oats` but carries **no
`supersede_years`**, so for 1893-1897 the *voted* copy of the same block sits
beside the *groupfix* copy.

Every duplicated port or coast cell is then **summed by the port roll-up before
the payload dedupe can collapse it** — the mechanism found on raw cotton in
iteration 45. In 1897 the payload's bare `Russia` came out at 10,926,960, which
is exactly twice its own ports (5,379,480 + 84,000).

## 1898 — CLOSED, 0.8771 -> 1.000000

The as_1899 Chandra block closes **perfectly**:

```
foreign members  13,082,550  == printed TOTAL   EXACT
British members   2,495,350  == printed TOTAL   EXACT
grand            15,577,900  == T1              EXACT
```

Infinity's as_1898 copy misreads the United States as **3,421,220 for
8,421,320**, and with that figure its own foreign members sum **7,927,040**
against its printed total of 13,052,530 — it does not close at all. It was
reaching the payload as `source=infonly` and winning the US cell on rank.
Superseding it leaves the block that closes.

## 1897 — CLOSED, 0.8918 -> 1.000023

The as_1897 block closes too:

```
foreign members  14,334,620  v printed 14,334,560   (+60)
British members   1,781,968  v printed  1,781,259
grand                                    v T1 16,116,810  ->  0.99999
```

and it closes **exactly** on 14,334,560 if Chile is the voted copy's **1,800**
rather than the block's 1,860 — two independent lines agreeing, though the 60
never mattered to the ratio.

What broke the year was the voted copy: it contributes a bare
`united states of america` of **814,249 at tier B**, which outranks the
groupfix `United States of America` 8,082,800 at tier C — while the real US
figure sits in the paren cell `United States Of America (Atlantic)` 8,082,300
and is *excluded* from the reconcile sum as drill-down detail. So the year read
as an 11% shortfall that was really a tier-B phantom displacing an 8.08M cell.

## The repair

Five supersede-only rows (`seq 0-0`), covering **every engine's stale label** for
the years touched — the iteration-46 lesson applied up front rather than after
two rebuilds:

| key | years |
|---|---|
| `CORDAGE \| Oats` (voted) | 1895; 1897 |
| `CORN, GRAIN, MEAL, AND FLOUR \| Oats` (as_1895 own-year, both engines) | 1895 |
| `CORN, GRAIN, MEAL AND FLOUR \| Oats` (two-up, comma-less spelling) | 1895 |
| `CHINA, OR PORCELAIN, AND EARTHENWARE \| Oats` (Infinity) | 1895; 1897; 1898 |
| `CHEESE \| Oats` (Infinity, as_1899) | 1895; 1897; 1898 |

The last two are pre-emptive: each is next in line to re-admit itself as
`infonly` the moment the copy above it is superseded.

## Result

```
1895  1.0638 -> 0.993646   (over -> within5; NOT closed, see below)
1897  0.8918 -> 1.000023   EXACT
1898  0.8771 -> 1.000000   EXACT

exact01 2,778 -> 2,780 ; within 0.1% GBP 50.9% -> 51.3% ; within 5% 68.7% -> 69.2%
under 254 -> 252 ; over 217 -> 216 ; denominator UNCHANGED at 9,940
```

`diffcells.py`: **exactly three cells change class**, all of them oats.

## 1895 — NOT CLOSED. Queued with the evidence.

Three label families collided here, and the as_1895 own-year copy is
**label-slipped**: `sweden` carries Germany's 748,64x, `germany` carries
Holland's 278,350, `holland` carries Roumania's 43,200, `turkey` carries the
US's 297,800, `united states of america` carries Argentine's 96,760. Its phantom
`russia` 12,122,560 was becoming the payload's bare Russia parent and blocking
the port roll-up entirely. Superseding it removes real phantoms and takes the
year from 1.064 to 0.9936 — an honest improvement, but not closure.

**The British half is settled.** Two independent copies close on the printed
327,070, and they agree on the finer decomposition:

```
as_1899   S.Australia 9,320 + Victoria 53,700 + N.Zealand 259,600
          + Canada 3,350 + Other British 1,100   = 327,070   EXACT
as_1895   the same, with Canada and Other British MERGED into one 4,450 row
                                                  = 327,070   EXACT
as_1897 (the block now in the payload) reads N.Zealand 252,600, Canada 3,250,
          S.Australia 9,329  ->  319,979, 7,091 short
```

**The foreign half turns on Russia's port split, and it does not resolve.**

```
as_1897   Northern 11,756,669   Southern 265,900   ->  12,022,569
as_1899   Northern 11,756,660   Southern 365,000   ->  12,121,660
as_1895   Russia printed as ONE line               ->  12,122,560
```

`12,122,560 - 11,756,660 = 365,900` — a figure that shares its leading digit
with as_1899 and its trailing digits with as_1897, which is exactly what a
two-position misread in each engine would produce. But **the value column
refuses to corroborate it**: as_1897's port values are 2,763,851 + 70,583 =
2,834,434 against the as_1895 Russia value of 2,813,434, a 21,000 gap, so one of
those three value readings is wrong too. And no combination of the two engines'
foreign readings closes on the printed foreign total 15,201,240 — the nearest
lands 306 away, in either direction depending on whether `Other Foreign
Countries` is read as 6,000 (as_1897) or 7,800 (as_1899).

The accounting of the remaining 98,673:

| | delta |
|---|---|
| Russia Southern Ports 265,900 -> 365,900 | +100,000 |
| New Zealand 252,600 -> 259,600 | +7,000 |
| Canada 3,250 -> 3,350 | +100 |
| Sweden 1,139,870 -> 1,130,870 | −9,000 |
| S. Australia 9,329 -> 9,320 | −9 |
| Northern Ports 11,756,669 -> 11,756,660 | −9 |
| | **+98,082**, leaving 591 |

Applying all six would give 0.999962. Four of them are proven by the exact
British-half closure; the Southern Ports 365,900 is not, and it is 100,000 of
the 98,082. **Not guessed.** This needs the as_1895 or as_1897 page image.

## Still open

- **`Oats` 1895** as above — a page-image call on one number.
- `group_repairs` line 18 (as_1897 `CORDAGE|Oats` 3611-3724) still has no
  `supersede_years` for **1893, 1894 and 1896**. Those years are not in the
  off-list, so the duplicate is not currently costing them a bucket — but the
  same voted-copy-beside-groupfix shape is present and should be checked before
  anything else changes in that family. The sibling `CORDAGE|Rye`,
  `CORDAGE|Peas` and `CORDAGE|Oatmeal and Groats` segments come off the same
  block and were repaired the same way.
