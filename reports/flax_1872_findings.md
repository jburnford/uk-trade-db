# Flax 1872: the import table found, the repair not landed

Session 11, iteration 64 (2026-07-27). `Flax, Dressed Or Undressed` reads
**0.013** in both 1872 and 1874 — **GBP 12.8M**. The origins are 1.3% of the
anchor in both years.

**Nothing was applied. Baseline unchanged: exact01 2,823, 53.8% GBP.** The
location of the missing table is now known, and one attempt was made, measured at
zero effect, and reverted.

## What the payload was showing

Three cells, 26,445 against an anchor of 2,020,970:

```
United States : Atlantic  23,029      Other Countries  3,416      Belgium  5,406
```

They come from `as_1872 | FLAX | Dressed and Undressed`, seq 905-908 — whose
**`flow` is `export_uk`**. The year's only origin data was the export table.

## Where the import table actually is

Under a stale **`FISH`** group, `flow='import'`, in three consecutive segments:

```
FISH | FLAX, Dressed        624-629      176,789
FISH | Rough or Undressed   630-637    1,515,855   (Russia 1,115,804)
FISH | Tow or Codilla of    638-642      325,296
                                       ---------
                                       2,017,940   v  T1 2,020,970  =  0.99850
```

All three belong to the anchor: the Tier-1 line is printed **`Flax, Dressed and
Undressed, and Tow`** in as_1875 and as_1876. The anchor itself was checked first
and is tier A on three volumes.

## The attempt, and why it was reverted

Four `group_repairs` rows — the three segments plus a supersede for the two-up
copy of the export table — produced **zero cells changed**. The groupfix rows did
not reach the payload at all.

This is the **second iteration running** with the same failure mode: iteration 63
predicted 0.991 and 0.998 for caoutchouc 1885/1887 from clean raw blocks and got
0.384 and 1.014. Here the prediction was 0.9985 and the result was no movement.

> **A `group_repairs` block that is arithmetically right can still deliver
> nothing.** The raw block sums correctly, the supersede fires, and the payload
> does not move. Whatever gate is dropping these rows is now the limiting factor
> on this whole class of repair — it has cost three years across two iterations.
> It is worth one iteration spent instrumenting `integrate_sources.py` to report
> *why* a groupfix row was rejected (sig mismatch, `consensus_triples_ga`,
> `seen_added`, `is_subtotal`), rather than continuing to guess.

Candidate causes, none confirmed: the segments' own consensus rows sig to
`('dressed','flax')` and `('flax',)` while the repair target sigs to
`('dressed','flax','undressed')`, so they are *not* blocked by
`consensus_triples_ga` — which means the rows should have landed and did not.

## 1874 is a different, blocked case

For 1874 the same three segments sit under their **correct** `FLAX` group
(`FLAX | Dressed`, `FLAX | Rough or Undressed` with Russia 1,376,291,
`FLAX | Tow or Codilla of`). Re-homing those into `Flax, Dressed Or Undressed`
would be a **taxonomy fold**, not a glue repair.

It is a defensible one — `Flax — Dressed`, `Flax — Rough Or Undressed` and
`Flax — Tow Or Codilla Of` all carry **no Tier-1 anchor of their own**
(`T1units={}`), so the fold would be data completeness rather than a merge of two
anchored series, the same reasoning as the Mahogany fold in iteration 12 — but it
is still a taxonomy decision and the loop does not take those alone.

## Still open

- **Flax 1872**: the table is located; the repair mechanism is what fails.
- **Flax 1874**: needs the fold decision above.
- **The groupfix-rejection instrumentation**, which is now blocking more than
  this commodity.
