# Leather manufactures, unenumerated 1882-84: the right years in the wrong commodity

Worked 2026-08-01 (`/loop /next-defect`), bracketed-gap rank 3, GBP 832k.

**Baseline exact01 is FLAT at 3,553** (within 5% 1,108 → 1,109, under 285 → 283,
nodata 4,333 → 4,334). **This iteration is a correctness gain, not a metric
gain**, and the reason is worth recording.

| | before | after |
|---|---|---|
| `Leather Manufactures — Unenumerated` 1882 | *nodata* | **0.99981** |
| `Leather Manufactures — Unenumerated` 1883 | 0.0684 | **0.98841** |
| `Leather Manufactures — Unenumerated` 1884 | 0.0856 | **1.00000** |
| `Leather, Undressed — Unenumerated` 1882 | 1.00000 | *nodata* |
| `Leather, Undressed — Unenumerated` 1884 | 1.00000 | *nodata* |

## Where the tables were

All three are parsed, under the stale group head `LEATHER, Undressed` with the
printed sub-head **MANUFACTURES absorbed**. The volumes print

```
LEATHER: Undressed / Dressed / Varnished, Japanned, or Enamelled
MANUFACTURES: Boots and Shoes / Gloves / Unenumerated
```

and the parser carries the first head across the whole run. **Infinity's as_1883
copy names the absorbed sub-head explicitly in its article — `MANUFACTURES :
Unenumerated` — which is the documentary proof of which line these blocks are.**

Arithmetic: as_1884's six members sum to **209,510 = the printed TOTAL = the
Tier-1, to the digit**; as_1882's to 328,459 against a printed 328,522 (63 short,
0.99981 — and **no combination of the two engines' readings closes it**: they
differ only on Germany 47,061/47,064, Holland 178,938/178,038 and Belgium
28,513/28,613, and none of the eight combinations gives 328,522); as_1883
(Infinity only) to 244,907 against 247,778.

## Why the two "lost" closures were never real

The earlier illusory-gap pass was right that 1882 and 1884 already closed —
inside `Leather, Undressed — Unenumerated`. **But that node's anchor is
borrowed.**

The consensus rows for 1882, 1883 and 1884 are printed under **`Leather
Manufactures | Unenumerated`**, tier A, in four to six volumes each. The
undressed-leather node acquires them through the **generic groupless article
`Unenumerated`** — and the same mechanism hands it an **1889 anchor of 814,593
that actually belongs to `Drugs | Unenumerated`**.

So `Leather, Undressed — Unenumerated` is a **generic-article magnet**, and its
1882/1884 "closures" were arithmetic accidents of an anchor it had no claim to.
Two exact01s were given up; neither was real.

The `match_declines.csv` entry of 2026-07-31 — *"leather manufactures and
undressed leather are different printed lines"* — **remains correct** as a
refusal to fold the whole node. This repair moves three years of origin cells,
not the node.

## An export table that cost twice

After the re-home, 1883 and 1884 still would not close. Two **two-up gap-fill**
rows already occupied the label: `Australasia` 8,514 / 8,738 and `Other
Countries` 8,428 / 9,198. Australasia is a **destination** for British leather
manufactures, not an origin — the same export-leakage class as Toys 1880 — and
the bogus `Other Countries` row additionally **blocked the real one** (19,388 in
1883, 1,986 in 1884) through `seen_added`.

**So an export-leakage row costs twice: wrong data in, and right data out.**
That is a sharper statement of the Toys finding, where the leak merely blocked
the `infonly` path. Removed by supersede — two-up rows cannot be displaced any
other way.

## Open, and deliberately not decided here

**`Leather, Undressed — Unenumerated` should probably not carry a Tier-1 series
at all.** Its anchor is assembled from at least two other commodities' printed
lines via the generic article. Deciding that is a taxonomy change and was not
taken inside this loop.

Also still open in `Leather Manufactures — Unenumerated`: **1895 reads 0.00**
against a Tier-1 of 408,408.
