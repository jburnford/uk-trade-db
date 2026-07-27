# Wheat 1890: a missing space before a colon cost 16.97 million cwt

Session 11, iteration 52 (2026-07-27). `Corn And Grain — Wheat` 1890 read
**0.767** — one cell, **GBP 27.1M**, the highest per-cell exposure left on the
board. It is now **1.0000, exact**.

## Neither the anchor nor the block was wrong

Following the iteration-51 lesson, the anchor was checked first: **60,474,180**,
tier A, and unanimous across `as_1890, as_1891, as_1892, as_1893, as_1894,
tn_1895`. Sound.

And the origin block is sound too — `as_1890 | Corn and Grain | Wheat`,
seq 551-576:

```
foreign  members 47,176,349  ==  printed TOTAL 47,176,349    EXACT
British  members 13,297,831  ==  Infinity's printed British TOTAL  EXACT
                             (Chandra prints 13,297,531 — a 300 misread)
grand            60,474,180  ==  T1                          EXACT
```

Everything needed was already in the table. The payload was throwing away a
quarter of it.

## One label, no space

```
551  'Russia: Northern Ports'   2,416,585      <- no space before the colon
552  'Southern Ports'          16,972,440
```

`V.cnorm` folds `Russia: Northern Ports` to plain **`russia`**, because the
colon-no-space form does not match the `' : '` sub-entry pattern. That makes a
**phantom parent**, and row 552's 16,972,440 becomes
`Russia (Southern Ports)` — a paren drill-down that every consumer excludes as
detail *inside* a parent that, in truth, is only the northern half.

This is exactly the class already recorded in `manual_rows.csv` for as_1877 and
as_1878 flax. What is new is the second-order damage.

## A wrong parent bred a second wrong parent

With 16.97M missing, the year read 43.3M against an anchor of 60.5M — and
`build_viz_payload`'s aggregate-beside-members step then **synthesized an
`Australasia` cell of 3,034,462** (exactly South Australia 1,072,392 + Victoria
223,078 + New Zealand 1,738,992) and counted it *beside* those same three
members. That step only fires when the addition brings the year closer to its
printed total — and with the port row gone, a 3M double count genuinely did look
like an improvement.

> **Second time this session an anchor-guided fold has been misled by an upstream
> error** (iteration 51 was the mirror image: a wrong anchor made a duplicate
> aggregate look right). These folds are only as good as the numbers they are
> judging against. When a year is far off, expect the payload to have *added*
> compensating garbage, and expect it to disappear on its own once the real
> defect is fixed.

## The repair

One block re-admission plus four per-row relabels:

- **551 → `Russia : Northern Ports`** (spaced), so the roll-up synthesizes
  Russia = 2,416,585 + 16,972,440 = **19,389,025**.
- **570/571/572 → `Australasia : …`** — the parser had carried the `British East
  Indies` head down past its last member, filing South Australia, Victoria and
  New Zealand as East Indian. Their sum is precisely the 3,034,462 the payload
  had been synthesizing.
- **`new_unit='Cwts.'`** — the block prints no unit at all, and the payload's
  unit-heal left three cells at `?`: Uruguay 87,816, United States of Columbia
  66,520, Other British Possessions 23,438. That is **177,774**, which was the
  exact residual after the port fix.
- One supersede-only row for Infinity's fragment under a stale `COPPER` group,
  pre-empted so it cannot re-admit itself once the consensus copy goes.

## Result

```
1890  0.766582 -> 1.000000    EXACT

exact01 2,791 -> 2,792 ; within 0.1% GBP 52.0% -> 52.3% ; within 5% 70.0% -> 70.3%
under 239 -> 238 ; denominator UNCHANGED at 9,940
```

`diffcells.py`: **exactly one cell changes class.**

## Still open

- **The colon-no-space form is worth a corpus sweep.** `Russia: Northern Ports`,
  `East Coast of Africa: Native States` and similar appear throughout
  `country_obs`; wherever the spaced sibling also exists, the unspaced one
  becomes a phantom parent and its sibling's quantity is silently excluded. The
  detector is cheap: a country whose cnorm equals a bare country name that also
  has `(…)` drill-down cells in the same commodity-year, where the bare cell is
  much smaller than the drill-down.
- Chandra's printed British TOTAL for this block reads **13,297,531** where its
  own members and Infinity both say **13,297,831** — a 300 misread, recorded but
  not material.
