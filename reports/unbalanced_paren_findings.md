# One stray bracket was deleting 438 origin cells

Session 11, iteration 55 (2026-07-27). The item was `Oil — Palm` (**GBP 19.2M**,
six off-cells). Four of the six turned out to be one character.

```
1875 2.000   1882 1.074   1885 0.605   1887 0.688   1889 0.567   1890 0.523
```

## The bug

`fold_country` opened with

```python
c = c.strip('()').strip()               # '(Straits Settlements)'
```

The comment says what it is for: a label *wholly wrapped* in brackets. But
`str.strip` removes those characters from **either** end independently, so a
label with a **trailing bracketed qualifier** lost only its closing bracket:

```
'The Gold Coast (including Lagos)'  ->  'The Gold Coast (including Lagos'
'West Coast of Africa (Foreign)'    ->  'West Coast Of Africa (Foreign'
```

An unbalanced `(` is not cosmetic. **Every consumer in this pipeline treats a
parenthesis in a country label as "drill-down detail inside a parent" and
excludes it from the origin sum** — `reconcile_baseline`, the coast/port
roll-ups, the map. So each of those cells was silently deleted.

Palm oil lost its largest origin four years running:

```
1885  The Gold Coast (including Lagos)  357,810      0.605
1887                                    343,073      0.688
1889                                    446,238      0.567
1890                                    414,187      0.523
```

`V.cnorm`, on the consensus path, strips brackets properly — which is why the
same printed label behaved differently depending on whether a cell arrived via
the vote or via a `groupfix`/`subentry` recovery. That divergence is what made
the class invisible: the label looked fine in most commodities.

The fix distinguishes the two cases:

```python
if c.startswith('(') and c.endswith(')'):
    c = c[1:-1].strip()                 # '(Straits Settlements)'
else:
    c = c.replace('(', ' ').replace(')', ' ').strip()
```

**Blast radius, measured before and after:** 81 distinct labels over 438 rows end
in `)` without starting with `(`. Unbalanced-paren labels in the payload go
**51 → 0**; distinct country labels 1,130 → 1,107 as the broken forms merge back
into their correct counterparts; commodity count unchanged at 1,977.

## Palm 1875 — the region total counted as an origin

The remaining palm defect was already diagnosed in `reports/oils_findings.md` in
session 5b/6 and had been queued ever since. Row 1082,
`West Coast of Africa (Foreign)` **904,562**, is the printed **region total**:
its six sub-entries at 1076-1081 sum to 904,562 to the digit, and that is also
T1. Admitting 1076-1081 and dropping 1082 puts the year exactly on its anchor.

> The detector that report asked for is still worth building: **an origin whose
> quantity equals the year's whole national total is the Total row.** The
> existing impossible-origin filter only fires above 1.15×, so it steps straight
> over the exact-match case.

## Result

```
exact01 2,795 -> 2,808  (+13) ; within 0.1% GBP 52.6% -> 53.0%
within 5% GBP 70.3% -> 70.4% ; under 238 -> 232 ; nodata 5,750 -> 5,749
denominator UNCHANGED at 9,940
```

Seventeen cells change class. Thirteen become exact — and only four of them are
palm oil:

```
Oil — Palm 1875 2.000 -> 1.0000     1885 0.605 -> 1.0000
           1889 0.567 -> 1.0000     1890 0.523 -> 1.0000
Coffee — Raw 1874, 1882, 1883, 1886, 1887, 1888   all within5 -> exact01
Cocoa 1894, 1895                                  within5 -> exact01
Nuts And Kernels — Commonly Used For Expressing Oil Therefrom 1886  0.931 -> 1.0
Ore, Unenumerated 1894                            nodata -> exact01
```

**Two regressions, both in `Caoutchouc`** — 1874 exact01 → 1.0059, and 1882
0.897 → 1.0758. That commodity is the known-broken one held for a dedicated
session (iteration 49): four-table glue, subtotals and region heads absorbed as
countries. Restoring its deleted cells naturally pushes it further over, because
the double counts were being partly cancelled by the deletions. Recorded, not
hidden.

`Oil — Palm 1887` moves 0.688 → 1.0661 — much closer and correct, but it crosses
from under to over.

## Still open

- **`Oil — Palm` 1882 (1.0737) and 1887 (1.0661)** are now the only two left, and
  they share a suspicious signature: the origin sum exceeds T1 by **+60,002** and
  **+60,000** respectively. Anchor not yet checked. Worth doing together.
- The **`(` = drill-down convention is undocumented and load-bearing**. It is
  relied on by `reconcile_baseline`, the roll-ups and the map, and nothing
  validates that a label's brackets balance. A one-line assertion after
  `fold_country` would have caught this on the day it was introduced.
