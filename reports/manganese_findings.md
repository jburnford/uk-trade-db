# Manganese ore 1891: an abstract page with its numbers slipped one row

Worked 2026-08-01 (`/loop /next-defect`), bracketed-gap rank 3, GBP 603k.
**`Manganese, Ore Of` 1891 went from 0.3826 to 0.96833** — `under` to `within5`.

**within 5% 1,110 → 1,111, under 276 → 275, exact01 unchanged at 3,563,
denominator held at 9,497. One commodity-year changed; zero regressions.**

## The origins were never the problem

1891's origin table is perfectly ordinary — Russia 48,807, Chile 31,331, Sweden
3,377, Portugal 3,195, Greece 2,500, Spain 2,138, Australasia 2,062, Germany
1,532, Japan 1,125, France 1,131, Turkey 670, Other Foreign 368 — twelve
plausible manganese sources summing to **98,236**. It read 0.38 because the
**anchor** was wrong.

## The anchor belonged to a different commodity

The voted Tier-1 was **256,772**, which is **Phosphate of Lime and Rock's 1891
figure** — tier A across five volumes. The series it sat in was also absurd on
its face: 1890 140,174 → **1891 256,772** → 1892 109,823.

The `as_1891` abstract page has its **number columns slipped one row against its
labels**:

```
Manufactures - - - Cwt  | 26,378 | 34,831 | 29,501 | 27,417 | 29,324
Liquorice - - - - Tons  | 90,383 | 72,088 | 96,031 | 140,174 | 101,449
Manganese, Ore of - -   | 283,415 | 257,886 | 301,953 | 343,501 | 256,772
Manures : - - - - "     | 73,957 | 102,957 | 88,739 | 83,290 | 79,981
Phosphate of Lime and Rock | 412,676 | ...
```

**Each run belongs to the label above it**, and three independent consensus
series prove it:

- `26,378 / 34,831 / 29,501 / 27,447 / 29,324` is **Liquorice's** own tier-A
  series 1887-91.
- `90,383 / 72,088 / 96,031 / 140,174` is **Manganese's** tier-A series 1887-90,
  agreeing with five to six other volumes in every year — so the fifth figure on
  that run, **101,449, is manganese 1891**.
- `283,415 / 257,886 / … / 343,501 / 256,772` is **Phosphate of Lime and Rock's**
  series, whose 1890 and 1891 are tier A across five volumes.

## Why the vote could not fix it, and why only one year broke

`as_1891` is the **first volume to print 1891**, and four later volumes copied
its slipped row forward — so the wrong figure had **six volumes behind it**.

**But 1887-1890 were unharmed**, because earlier volumes had already established
those years and outvoted the slip; and **Liquorice 1891 and Phosphate 1891 are
tier A from other volumes**. **Only the year `as_1891` introduced was
corrupted.** That is the general shape: *a row-slip in an abstract page damages
exactly the years that page is the first to publish.*

This is the same failure mode as `Oil Seed Cake` 1890 and `Flax or Linseed` 1899
already in `reference/manual_t1.csv` — a broken figure copied forward outvoting
the truth — but arriving by a different route: not a misread digit, a misaligned
row.

Corrected via `manual_t1.csv`. **The consensus rebuild was diffed against a
snapshot and changed exactly one row.**

## Two operational notes

- **`reconcile.py` takes over two minutes.** Run it with an explicit long
  timeout: killed mid-write it leaves `consensus` **truncated** (34,258 of
  51,268 rows) with no error, and everything downstream then rebuilds from a
  partial anchor table. Snapshot `consensus` first and diff after.
- The illusory-gap filter was **right** to refuse this pair. It flags a gap as
  illusory only when a *name-related* sibling shares the anchor, and manganese
  and phosphate manures are unrelated — which is exactly why the shared value
  was a defect rather than a duplicate.

## Residual

The origins are **3,213 short** of 101,449 (0.96833) — a missing member, not a
digit. Honest partial. Also open: 1866-1871 and 1900 `nodata`; 1895/1896 read
1.127/1.166.
