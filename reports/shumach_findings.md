# Shumach: the most scattered family yet, and a repair route that does not work

Worked 2026-07-29 (`/loop /next-defect` iteration 25). **Nothing landed** —
this is a diagnosis, a proof set that is ready to use, and one blocked
mechanism recorded so the next attempt does not repeat it. Baseline unchanged
at exact01 **3,472**; every change made was backed out and the reference files
match HEAD.

## The family

Shumach (a tanning material, almost all of it Italian) has an eight-year hole
1878-1885 — bracketed-gaps **rank 4, £4.5M**. The cause is the most extreme
sticky-group case found so far: **the origin table is glued under a different
stale group head in nearly every volume**, while the article stays constant.

| volume | group the table was filed under |
|---|---|
| 1872, 1873, 1875, 1878 | `SHIPS, with their Tackle, Apparel, and Furniture` |
| 1876, 1879 | `SEEDS` |
| 1874, 1877, 1880, 1881 | `Cotton` |
| 1882, 1890 | `DRUGS` |
| 1882-1885, 1888, 1889, 1891, 1893, 1895, 1897-99 | `Bark` |
| 1884 | `Corn and Grain` |
| 1883-1892 | `DYE STUFFS, and Substances used in Tanning` (the correct one) |
| 1898 | `COPPER, ORE OF` |

Because the article carries the signature and the payload keys on
*group — article*, each volume became its own commodity. The family is spread
over **six payload nodes across three spellings** — `Shumach`, `Sumach`,
`Shunach`.

## The proofs, which are solid and ready

Six of the eight missing years close on their own members:

| year | members | Tier-1 | |
|---|---|---|---|
| 1879 | 11,369 + 762 = **12,131** | 12,131 | **exact** |
| 1880 | 10,573 + 1,047 = **11,620** | 11,620 | **exact** |
| 1881 | 12,338 + 758 = **13,096** | 13,096 | **exact** |
| 1883 | 14,873 | 14,876 | −3 |
| 1884 | 11,714 | 11,704 | +10 |
| 1885 | **11,157** | 11,157 | **exact** |

**1878 is a member mislabelled `TOTAL`** — the same mechanism as the as_1881
china block. France 612 + Italy 12,731 = 13,343, and seq 1491 carries exactly
**580** under the label `TOTAL`; 13,343 + 580 = **13,923 = Tier-1 to the
digit**. Every neighbouring year names that residual row *Other Countries*
(762, 1,047, 758), so the label is recoverable, not guessed.

**1882 cannot be closed and is left alone.** Chandra reads Italy 12,297,
Infinity 12,097, and the printed grand total (13,935, which is the Tier-1 to
the digit) demands **12,997** with Other Countries at 938. Both engines are one
digit away, in the same position, and **neither has it** — so closing the year
would mean synthesising a figure no parse contains. That is exactly what the
standing rule forbids.

## The blocked mechanism — record this before trying again

Relabelling the stray blocks with `group_repairs` **admits nothing**:

1. Without `supersede_years`, every repaired row is dropped at
   **`drop_consensus_holds_triple`** — the same cells are already in consensus
   under the stale group label, so the guard that normally prevents
   double-counting prevents the relabel instead. The audit shows
   `selected: 3, drop_subtotal: 1, drop_consensus_holds_triple: 2` for each
   block.
2. **Adding `supersede_years` is not sufficient either.** It drops 15 more
   consensus rows, but the repairs still admit nothing and the baseline does
   not move. Why the second guard still fires was not established, and that is
   the open question for the next attempt.

The curation-fold route is also unavailable: a scan of every payload node for
Ton sums matching the shumach anchor in 1878-1885 found **only one genuine
node** (`Cotton — Shumach`, 1880). The other near-matches are unrelated
commodities of similar magnitude (`Manganese, Ore Of`, `Steel — Unwrought`,
`Seed, Of All Kinds`) — coincidence, not misfiling. So the rows for 1879 and
1881-1885 are in `country_year_final` but are not reaching any recognisable
payload node, and **finding where they go is the prerequisite for any fix.**

## Operational note

`reference/group_repairs.csv` has **22 ragged rows** carrying more fields than
the header. Any `csv.DictWriter` rewrite of the whole file therefore raises
`ValueError: dict contains fields not in fieldnames: None` — twice now. **Never
rewrite that file wholesale.** Append, or drop-and-re-append matched lines at
the byte level, remembering that fields containing commas are quoted (the
match string needs `"DYE STUFFS, and Substances used in Tanning",` with the
quotes).
