# Copper — the ore-and-regulus family (2026-07-26)

Worked from the ranked open item: "`Copper, Ore And Regulus` 1888 anchor is
3,562,071 tons against 250,567 the next year; `Copper — Regulus` loses its
origin table entirely after 1881." Both halves were real. The first is fixed;
the second is a structural finding that needs a decision, not a patch.

## 1. The 1888 anchor — FIXED

`Copper, Ore And Regulus` read **3,562,071 tons** in 1888, between 169,511 in
1887 and 250,567 in 1889.

The series is printed under two labels — `Copper, Ore and Regulus` and
`Metals :Copper, Ore and Regulus` — and they are **digit-identical in all 21
other overlapping years**. 1888 is the only disagreement, and the sibling says
230,319.

Only `as_1891` prints 3,562,071, and its abstract **quantity column is
misaligned through the entire metals section**:

```
as_1891 seq=38  Meat, Unenumerated ; Salted or Fresh   230,319  Cwts.   <- the copper figure
as_1891 seq=41  Copper, Ore and Regulus              3,562,071  Tons
as_1891 seq=46  Bars                                 1,495,972  Tons    <- Silver Ore's VALUE
```

The true 230,319 is sitting three rows above its own label. It is printed as the
quantity by `as_1889` and `as_1890`, and appears again in `as_1888` and
`as_1892`. The price check settles it: the printed value 4,975,790 over 230,319
tons is **GBP21.6/ton** against 14.8 in 1887 and 16.9 in 1889 — high, but 1888 is
the Secrétan copper corner, so a spike is expected — whereas 3,562,071 tons
would imply GBP1.40/ton.

It won the vote only because 1888 happened to be a **1–1 tie** (as_1890 against
as_1891) where every other year was 2–1 against as_1891.

Fixed by `reference/manual_t1.csv`. The series now runs
169,511 → **230,319** → 250,567 → 215,935.

**The corpus baseline does not move**, and that is the point: `Copper, Ore And
Regulus` has no origin table in any year, so it sits in the `nodata` bucket and
`reconcile_baseline.py` structurally cannot score it. The anchor was wrong by a
factor of 15 and no closure metric could have seen it.

## 2. The regulus origins are not lost — they are under two other labels

`Copper — Regulus` stops in 1881 because the printed article changes. The
country tables carry the same line as **`Regulus and Precipitate`** from 1882,
under `COPPER` to 1892 and `COPPER, ORE OF` from 1887. In the payload it is a
**headless label** — the group was lost and the article became the commodity
name — carrying **GBP41.8M** of trade across 1882–1899.

So the family is:

| payload label | GBP | origins | anchor |
|---|---|---|---|
| `Copper, Ore And Regulus` | 1.8M | **none, ever** | 1866–96 |
| `Metals :Copper, Ore And Regulus` | 2.0M | none, ever | 1868–94 |
| `Copper, Ore Of` | 22.7M | 1872–1899 | only 1893–1900 |
| `Copper — Regulus` | 12.8M | 1872–1881 | none |
| `Regulus And Precipitate` | 41.8M | 1882–1899 | none |

## 3. The sibling identity, and why it is queued and not applied

`Copper, Ore Of` + regulus = the printed `Copper, Ore and Regulus` total, across
**both** regulus label eras:

```
1874    47,876 +  28,424 =  76,300  v  76,290    +10
1877   115,632 +  33,694 = 149,326  v 149,326      0   EXACT
1879    87,824 +  46,152 = 133,976  v 133,976      0   EXACT
1882   103,490 +  48,619 = 152,109  v 152,068    +41
1884   124,255 +  62,394 = 186,649  v 186,679    -30
1886    84,887 +  67,566 = 152,453  v 152,415    +38
1887    89,636 +  79,875 = 169,511  v 169,511      0   EXACT
1889   136,517 + 114,050 = 250,567  v 250,567      0   EXACT
```

Eight years within 50 tons, four exact to the digit, plus 1872 (−60) and 1878
(−303). Four of the eight use `Copper — Regulus` and four use `Regulus And
Precipitate`, so the identity holds across the label change — which is itself
the proof that the two are one line.

**Not applied, and it needs a decision rather than a patch.** Three reasons:

1. It is a taxonomy fold with a **GBP64.5M** blast radius (`Regulus And
   Precipitate` plus `Copper, Ore Of`) into a parent labelled GBP1.8M.
2. **It breaks systematically from 1891**: +13.2%, +14.1%, +12.0%, +15.2%,
   +14.7%, +17.6% for 1891–96, plus 1883 (+12.2%) and 1885 (+8.5%). Something
   changes in the early 1890s and the identity should not be assumed through it.
3. From **1893 `Copper, Ore Of` acquires its own Tier-1 anchor** (89,898 in 1893
   against the combined 199,608), so the abstract is printing ore separately in
   exactly the era where the identity fails. The era semantics need settling
   before anything is merged — this is the shape that made the sugar family
   expensive.

The safe reading is that the parent is the printed combined line and the two
children are its country-table detail; the parent has **no origins of its own**,
so supplying them is not the sugar double-count trap. But the 1891+ era has to
be understood first.

## 4. Lead, unverified — a stale `COPPER, ORE OF` group head

`country_year_final` carries these under `COPPER, ORE OF`, all 1894–98:
`Bark`, `Cutch and Gambier`, `Madder, Madder Root, Garancine and Munjeet`,
`Myrobalans`, `Safflower`, `Sumach`, `Valonia`, plus `Opium` and `Yarn`.

The first seven are **dyeing or tanning stuffs** — one printed section sitting
under a stale copper head. `Opium` and `Yarn` are neither. This has the shape of
a glue block (see the round-9 class), but the seq ranges have **not** been
checked and no printed total has been tested. Do not repair on this note alone.
