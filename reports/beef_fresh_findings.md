# Beef, Fresh 1898-99: the whole foreign half was under a FISH label

Session 11, iteration 68 (2026-07-27). `Beef — Fresh` read **0.399** and
**0.365** — **GBP 9.9M** over two cells.

```
1898  0.399254 -> 0.997919      1899  0.364798 -> 0.997618

under 227 -> 225 ; within 5% GBP 71.2% -> 71.3% ; exact01 unchanged at 2,825
denominator UNCHANGED at 9,940
```

`diffcells.py`: **exactly two cells change class**, both gains. Neither reaches
`exact01` — they sit 0.21% and 0.24% short — but both leave `under`.

## What was there, and what wasn't

The payload had **only Australasian cells**, and one of them was a phantom: a
bare `Australasia` 619,007 in 1898, equal to Queensland 483,932 + New Zealand
92,756 + New South Wales 42,159 + Victoria 160 to the digit — the region total
counted beside its own members.

Missing was the entire foreign half of a trade that was overwhelmingly American:

```
United States of America  2,750,458      Argentine Republic  150,308
Denmark  41,775                          Holland  15,589
Canada  90,238  (British side)
```

Infinity's `as_1899 | BEEF | Fresh`, seq **1072-1148**, is clean by the boundary
detector (boundary at `seq_max`, nothing after) and its grand totals equal Tier 1
for **five straight years**. Its members give 1896 0.99887, 1897 0.98901, 1898
0.99792, 1899 0.99762 — so only 1898 and 1899 are superseded; 1896 and 1897 are
not off-ratio and must not be moved.

The audit predicted and confirmed the landing: `selected 77, admitted 62`, with
all 15 drops being subtotal rows. The range holds a single `article` value,
checked per the iteration-65 rule.

## One label, two commodities — and a cost worth stating

`FISH | Fresh` for 1899 is **two printed tables in one consensus label**:

```
beef:  United States 2,756,458 · Queensland 513,225 · Argentine 150,368 ·
       New Zealand 134,427 · Canada 90,238 · Denmark · NSW · Holland · Victoria ·
       South Australia · France · Sweden
fish:  Channel Islands 1,338,115 · Germany 757,700 · Portugal 133,613 ·
       Canary Islands 92,847 · Belgium · Malta · Spain · Norway · Egypt
```

Superseding it removes both halves. **The cost, stated rather than buried:** the
`Fish — Fresh` payload commodity loses its 1898-99 origins. It carries **no
Tier-1 line at all**, so the reconcile denominator is untouched and no bucket
moves — and the beef half of that table was wrong there in any case. The fish
half should be re-admitted under its own label in a later pass; that is a real
outstanding item, not a tidy-up.

## Still open

- **1898 short 6,454; 1899 short 9,060** against their own anchors — the block's
  printed foreign total is 2,908,098 where its members give 2,908,065 in 1899, so
  the residual is inside the block, not missing from it.
- **`Fish — Fresh` 1898-99 origins**, removed by the supersede above and needing
  re-admission under a fish label.
- **1897 at 0.98901** in the same block. It is not currently off-ratio under the
  present sources, so it was left alone — but if it ever surfaces, this block is
  where it goes, and it will land at 0.989 rather than exact.
