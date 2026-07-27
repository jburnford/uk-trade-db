# Tea 1894-98: closed, and a wine table in gallons was blocking it

Session 11, iteration 60 (2026-07-27). `Tea` — **GBP 18.6M** — came back into the
loop with the boundary detector. Four cells now close exactly:

```
1894  0.9308 -> 1.000000   1895  1.0039 -> 0.999802
1896  1.2418 -> 1.000000   1898  1.0042 -> 1.000000

exact01 2,814 -> 2,818 ; within 0.1% GBP 53.2% -> 53.5% ; within 5% 70.7% -> 70.8%
under 231 -> 230 ; over 201 -> 200 ; denominator UNCHANGED at 9,940
```

`diffcells.py`: **exactly four cells change class**, all tea, all gains.

## The detector answered what the hand trace could not

Iteration 56 mapped the `as_1896 | TEA | (null)` label across five printed
tables — tea imports, a by-sort consumption table, **tobacco**, another
commodity, then **wine** — and stopped, because admitting the tea rows alone left
1896 at 0.853 with a foreign half of ~39,029,440 unlocated.

The detector was pointed at the label and returned a different block:

```
as_1898 | TEA | (null)   seq 26923-27051   boundary == seq_max, 0 rows after
  1894 244,310,500 EXACT   1895 0.99980   1896 265,394,122 EXACT
  1897 0.99810             1898 271,593,683 EXACT
```

Five consecutive years closing on their anchors. The 1896 foreign half iteration
56 could not find is simply *in it*: **39,029,440**, the printed foreign TOTAL.
And per the iteration-59 lesson the rows before `seq_min` were checked — the
label starts at 26923, so unlike caoutchouc there is no separate head to add.

## The blocker: a wine table, in gallons, wearing tea's signature

The block repair alone left **1896 at 0.97683** — 6,139,523 short. The missing
cells were Holland **4,616,116**, France **1,520,917** and Belgium **2,490**,
which sum to exactly that.

They were blocked by `TEA | Other Sorts` — a **wine** table under the stale `TEA`
group, whose three cells are *in gallons*:

```
TEA | Other Sorts | holland  2,992 Gallons
TEA | Other Sorts | belgium    954 Gallons
TEA | Other Sorts | france     847 Gallons
```

`V.sig('Other Sorts')` is **empty** — "sorts" is stopword vocabulary — so it
falls back to `sig(group + article)` = `('tea',)`, **the same signature as tea
itself**. Those three cells therefore held the `(tea, holland/france/belgium,
year)` triples.

> ⚠ **`seen_added` and `consensus_triples_ga` are UNIT-BLIND.** A cell in gallons
> can block a cell in pounds. The gate exists to stop a comparative re-admitting
> a country the vote already carries — but it cannot tell a wine gallon from a
> tea pound, so a mis-headed table in the wrong unit silently starves the right
> one.

This is worth a sweep in its own right: any label whose article sigs to nothing
inherits its group's signature wholesale, and a stale group then makes it a
sibling of the real commodity.

## Still open

- **`Tea` 1897 at 0.99810** and **1899 at 0.96573** — 1897 is 506,013 lb short
  against its own block, 1899 comes from the `as_1899` copy which is 3.4% short
  in that year. Both are small-scale now.
- **1893 at 0.98102.** The `as_1898` block starts at 1894; the `as_1893 | TEA`
  label has boundary 271 with 5 rows after, so it has its own smaller version of
  the same defect.
- The unit-blind-gate finding above deserves a detector: labels whose article
  contributes no tokens, sitting under a group that belongs to a different
  commodity.
