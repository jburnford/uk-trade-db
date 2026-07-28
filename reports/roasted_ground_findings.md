# Roasted or Ground 1894: the right table was already there

Session 11, iteration 67 (2026-07-27). `Roasted Or Ground` 1894 read **218.961×**
— 31,317,763 against an anchor of 143,029, **GBP 10.1M** on one cell. It is now
**1.0000, exact**.

```
exact01 2,824 -> 2,825 ; within 0.1% GBP 53.8% -> 53.9% ; over 196 -> 195
denominator UNCHANGED at 9,940
```

`diffcells.py`: **exactly one cell changes class.**

## Nothing needed recovering

The correct table was already in the corpus — six **hand-keyed `human` rows**
under `CHICORY | Roasted or Ground`:

```
Belgium 59,546   Channel Islands 32,834   Holland 25,941
Germany 20,949   Other Foreign 2,242      France 1,517
                                          -------
                                          143,029  =  T1, to the digit
```

Beside them sat **18 consensus rows under a stale `BEER AND ALE` group** carrying
a different commodity entirely — British East Indies 17,035,547, Ecuador
5,777,279, Portugal 4,787,326, Brazil 2,448,661. Those are cocoa or raw-coffee
origins; roasted coffee is a 143,029-pound line.

The two sets **overlap on six countries and differ on twelve**, so the payload
dedupe kept one cell per country and summed both tables. One supersede-only row
drops the glue and leaves the hand-keyed table standing alone.

> **A commodity can be wrong while already containing its own exact answer.** The
> hand-keyed rows summed to the anchor to the digit and had done so all along;
> what was missing was the removal of what sat next to them. Worth a detector:
> any commodity-year holding `human`-sourced rows *and* rows from another source
> under a different `article_group`.

## Scope

The `BEER AND ALE | Roasted or Ground` glue exists across **1872-1896**, but only
1894 is off-ratio, so only 1894 is superseded. The other years are either already
exact or carry too little of it to move a bucket — worth revisiting only if one of
them surfaces on the board.

## Also checked this iteration

The iteration-65 audit sweep was run first and is thin: only **6** repairs admit
nothing, all with benign causes (subtotal-only ranges, already-added). The
partial-landing view — 53 repairs losing rows, led by
`as_1898 COPPER, ORE OF | Raw` losing 123 of 146 — is dominated by multi-year
comparative blocks overlapping the vote, which is the gate working as designed
rather than a defect vein.
