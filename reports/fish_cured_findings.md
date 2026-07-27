# Fish — Cured or Salted, unenumerated: the same reprint trick as sheep wool

Session 11, iteration 53 (2026-07-27). `Cured Or Salted, Unenumerated` — a
de-headed `FISH` article — **GBP 24.2M**, four off-cells:

```
1894 14.948   1897 1.410   1898 1.076   1899 1.251
```

**1894 is now exact. 1897-99 are a different, two-part defect and are queued.**

## 1894 — a wrong anchor, and the iteration-51 mechanism exactly

The Tier-1 series makes the diagnosis before any arithmetic:

```
1893   916,366
1894    61,927      <- an order of magnitude below both neighbours
1895 1,082,588
```

The abstract readings:

```
as_1897   925,244
as_1898    61,927
tn_1899    61,927      <- tn_1899 mirrors as_1898
```

Two votes to one, tier B. **One late reprint, counted twice, beating the
contemporary reading** — the same shape as `Wool — Sheep Or Lambs'` 1894 two
iterations ago.

The origin table settles it to the digit. `as_1894 | FISH | Cured or Salted,
unenumerated`, seq 1153-1171:

```
foreign  members 577,720  v printed TOTAL 577,711     (9 over)
British  members 347,533  == printed TOTAL 347,533    EXACT
grand                     == 925,244  ==  as_1897's reading
```

One row in `reference/manual_t1.csv`. `reconcile.py` re-run and verified
idempotent again: 51,268 series-years, **zero rows differ from the pre-change
snapshot** apart from the overridden one, now tier A.

```
1894  14.948052 -> 1.000480    EXACT
exact01 2,792 -> 2,793 ; over 215 -> 214 ; denominator UNCHANGED at 9,940
```

`diffcells.py`: **exactly one cell changes class.**

> **Two anchor errors in three iterations, both 1894, both the same shape:
> `as_1898` and `tn_1899` are one printing counted twice.** That pair is worth a
> systematic pass — every Tier-1 series where `as_1898,tn_1899` outvote an
> earlier volume and the origin block agrees with the earlier volume.

## 1897, 1898, 1899 — diagnosed, NOT fixed

These three are origin-side and have **two** faults each.

**(a) The printed foreign TOTAL wears the `United States of America` label** and
is counted as a country — the run-on-head shape from the wheat-flour work:

```
1899  row 6831 'United States of America'  660,112
      foreign members above it              660,049      (63 short — decisive)
1898  row 6834 'United States of America'  703,676
      foreign members above it              684,446
```

In both years the real US figures are the sub-entry rows beside it
(`: On the Atlantic`, `: On the Pacific`, `: Other Foreign Countries`).

**(b) The British half is largely missing.**

```
1898   printed British 497,047   members present 156,203   ->  340,844 absent
1899   printed British 343,285   members present 186,085   ->  157,200 absent
```

(1899's British total is derived: printed grand 1,003,397 − foreign 660,112. The
row parsed as the British TOTAL reads 543,235, which is consistent with neither.)

**Why nothing was applied.** Fixing (a) alone takes 1899 from **1.251 over** to
**≈0.843 under** — correct, but not closure, and it would leave the year looking
worse by the metric while the real gap (b) stays hidden. The two have to be done
together, and (b) needs the dropped rows recovered from another engine or the
page. Same reasoning as caoutchouc in iteration 49: a half-repair makes the
eventual full repair harder to reason about.

## Still open

- **1897, 1898, 1899** as above. The recovery route to try first is the other
  engine: Infinity files these blocks under a stale `Bark` group
  (`as_1897 | Bark | Cured or Salted, unenumerated`, 3069-3452 and 4784-4891;
  `as_1898 | Bark | …`, 3631-4014 and 6491-6567), which the 1893-99 volumes'
  comparative layout usually keeps more completely.
- 1897's own-year block was not located in `country_obs` at all under a
  `FISH%` group — worth confirming it is not simply absent from that parse.
