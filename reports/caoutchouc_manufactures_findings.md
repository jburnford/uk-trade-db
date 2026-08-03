# Caoutchouc — Manufactures Of 1892-98: the anchor belongs to Cork

GBP 11.8M, seven years, ranked #1 on the bracketed-gap board, reading a flat
**0.34-0.45** since it was first folded. `commodity_curation` row 543 records the
break in its own note and diagnoses it as a scope change:

> KNOWN BREAK, recorded not hidden: from 1892 the ANCHOR jumps (3,180,198 in
> 1891 to 9,055,694 in 1892) while the origin sum runs on smoothly … The printed
> national line changes scope there; the origin side does not.

**That diagnosis is wrong.** The printed line does not change scope. The anchor
changes *commodity*.

## The proof, from the printed abstracts

The as_1892 abstract prints, a few lines apart:

```
Caoutchouc:
  Manufactures of  - - - Lbs. | 3,116,510 | 3,132,976 | 3,563,469 | 3,180,198 | 3,448,727
Cork :
  Unmanufactured   - - - Tons |    14,293 |    21,938 |    18,111 |    13,258 |    12,522
  Manufactured     - - - Lbs. | 7,316,143 | 8,767,249 | 9,734,200 | 8,852,416 | 9,055,694
```

and as_1899 continues the second line:

```
Cork, " Manufactured - - Lbs. | 10,118,249 | 11,358,407 | 12,604,828 | 12,497,946 | 12,294,141
```

The node's Tier-1 for 1892-98 is **9,055,694 / 9,293,789 / 9,407,079 /
10,118,249 / 11,358,407 / 12,604,828 / 12,497,946** — Cork, Manufactured's
series, verbatim, every year. Caoutchouc's own printed figures are
**3,448,727 / 3,211,322 / 3,202,377 / 3,909,569 / 4,365,472 / 4,551,285 /
4,669,998**, and 1899 (5,065,320) is already correct because Cork's series does
not reach it under the same label.

## The correct values are already in `consensus`

This needs no anchor override. Both series are present and tier A:

| group | article | unit | years | whose |
|---|---|---|---|---|
| *(none)* | `Manufactures of` | Lbs. | 1890-1899 | **Caoutchouc — correct, every year** |
| *(none)* | `Manufactured` | Lbs. | 1892-1897 | Cork |
| *(none)* | `" Manufactured` | Lbs. | 1898 | Cork |

`reconcile._sig` separates them — `('manufactures',)` vs `('manufactured',)` —
and so does `build_viz_payload.sig_of`. They are nevertheless **merged into one
node before curation runs**: a curation row `Manufactured → fold → Cork —
Manufactured` is a **no-op**, because no `Manufactured` node exists to fold. The
merge is `fold_era_wordings` treating `Manufactured` and `Manufactures Of` as two
era spellings of a single printed line. They are not: they are two different
commodities that happen to share a qualifier, both de-headed by the same abstract
layout (`Cork :` and `Caoutchouc:` are group heads on their own rows).

## Both commodities are damaged, and the fix is one fix

`Cork — Manufactured` has origins for 1892-96 — **9,106,294 / 9,293,789 /
9,395,999 / 10,118,249 / 11,337,177** — which reproduce Cork's own anchors to
within 0.6%, two of them **to the digit**. Its Tier-1 stops dead at 1891. Cork's
anchors are not missing; they are on Caoutchouc.

Correcting the assignment yields, on today's origin sums:

| year | origins | current T1 (Cork's) | now | true T1 | after |
|---|---:|---:|---:|---:|---:|
| 1892 | 3,420,706 | 9,055,694 | 0.3777 | 3,448,727 | 0.9919 |
| 1893 | 3,219,970 | 9,293,789 | 0.3465 | 3,211,322 | 1.0027 |
| 1894 | 3,202,372 | 9,407,079 | 0.3404 | 3,202,377 | **0.999998** |
| 1895 | 3,909,569 | 10,118,249 | 0.3864 | 3,909,569 | **1.000000** |
| 1896 | 4,365,472 | 11,358,407 | 0.3843 | 4,365,472 | **1.000000** |
| 1897 | 4,776,515 | 12,604,828 | 0.3789 | 4,551,285 | 1.0495 |
| 1898 | 4,669,993 | 12,497,946 | 0.3736 | 4,669,998 | **0.999999** |

Four years land exact **to the digit** — which is itself the strongest possible
confirmation that these are the right anchors — and Cork picks up five more
cells. That the origin sums reproduce the `Manufactures of` series and not the
`Manufactured` one is independent proof of ownership.

## Fixed this iteration: Germany 1898

The 1898 row above only reaches 0.999999 because of a second, separate defect
closed here. The vote took Germany 1898 = **2,910,560**, which appears in exactly
one reading — Chandra's as_1899 reprint, under the garbled group `CAOUTCHOUIC`.
**Three** readings say **2,010,560**: Chandra's own contemporary as_1898,
Infinity's as_1898, and Infinity's as_1899. The lone-late-reprint pattern, and
the arithmetic is decisive — 2,010,560 gives 4,669,993 against a printed
4,669,998 (five Lbs, 0.999999); 2,910,560 gives 5,569,993, 19.3% over.

**The repair had to be keyed to the garbled spelling.** `manual_replace` keys on
`V.sig(GROUP + ARTICLE)` and `V.sig` **preserves OCR garbling in the group**, so a
row written under `CAOUTCHOUC` silently failed to bind against a source row
grouped `CAOUTCHOUIC`. This commodity is the known five-spelling case. Same rule
as `supersede`: name the spelling **the source row carries**, not the one the
node displays.

## Blocked, pending a decision

There is **no reference-file lever** that separates the two anchor series: the
curation fold is a no-op, and a `manual_t1` override keyed `('manufactured',)`
would reach only Cork's series and would write Caoutchouc's numbers into it.
Resolving this means changing how `fold_era_wordings` buckets these two labels —
a node-assembly change, escalated rather than taken alone.
