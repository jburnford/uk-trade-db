# Whale oil (train oil) and whalebone / whalefins (baleen) — survey

Written 2026-07-28 at the user's request ("look at whale oil (train oil) and
whalefin or whatever they called baleen"). **This is a survey, not a repair —
nothing in this file has been fixed.** Numbers are from the payload at commit
d9a18ce.

## What the volumes actually print

Two commodity families, each printed under a name that drifts across the
period, and each split in the corpus into overlapping shadows of one series.

**Whale/fish oil.** The abstract line is a COMBINED one and its wording moves:
`Train, Spermaceti, and Blubber (including Cod Liver Oil)` (1866-70) ->
`Train or Blubber, and Spermaceti` (1868-81) -> `Train or Blubber, and Sperm`
(1878-96) -> `Fish: Train or Blubber` (1893-1900). Eight payload commodities
carry fragments of it, all overlapping:

| payload commodity | unit | T1 years |
|---|---|---|
| Train, Spermaceti, And Blubber (Including Cod Liver Oil) | Ton | 1866-1870 |
| Oil :Train Or Blubber, And Spermaceti | Tun | 1868-1880 |
| Train Or Blubber, And Spermaceti | Ton | 1868-1881 |
| Train Or Blubber, And Sperm | Ton | 1881-1895 |
| Oil — Train Or Blubber, And Sperm | Ton | 1878-1896 |
| Oil — Train Or Rubber, And Sperm | Ton | 1886-1890 (OCR garble of Blubber) |
| Oils — Fish, Train Or Blubber | Tun | 1893-1897 |
| Oil — Fish : Train Or Blubber | Tun | 1894-1900 |

**Baleen.** `Whalefins` (1866-81) -> `Whalebone (Whalefins)` (1878-94) ->
`Whalebone` (1891-1900), plus a Ton-denominated shadow of the earliest years
and several garbles (`Tin — Whalerone (Whalefins)`, `Skins, Furs, And Pelts —
Whalepins`).

The Ton/Cwt shadow settles itself: 1868 reads **190 Ton** and **3,800 Cwt**,
1869 **84 / 1,680**, 1870 **213 / 4,260** — exactly 20 cwt to the ton in all
three. Same printed data, transcribed twice.

## Finding 1 — the whale-oil origin data exists and closes, but the metric cannot see it

Every oil label reads **nodata** for almost all its T1 years. That is not
missing data. The abstract prints ONE combined line; the origin tables print
**two sibling lines**, `OIL | Train or Blubber` and `OIL | Spermaceti or Head
Matter`. Nothing ever sums the siblings against the combined anchor, so good
country data sits unmatched.

Summing the two printed block totals against the combined T1:

| year | Train/Blubber | Spermaceti | sum | combined T1 | ratio |
|---|---|---|---|---|---|
| 1872 | 15,004 | 3,715 | 18,719 | 18,719 | **1.0000** |
| 1873 | 15,069 | 2,817 | 17,886 | 17,686 | 1.0113 |
| 1874 | 1,292 | 26 | 1,318 | 17,051 | 0.0773 (parse loss) |
| 1875 | 14,890 | 4,469 | 19,359 | 19,359 | **1.0000** |
| 1876 | 13,466 | 3,218 | 16,684 | 16,684 | **1.0000** |
| 1877 | 17,111 | 2,254 | 19,365 | 19,365 | **1.0000** |
| 1878 | 15,500 | 5,156 | 20,656 | 20,656 | **1.0000** |
| 1879 | 17,949 | 2,247 | 20,196 | 20,196 | **1.0000** |
| 1880 | 13,447 | 1,784 | 15,231 | 15,231 | **1.0000** |
| 1881 | 15,903 | 2,127 | 18,030 | 18,030 | **1.0000** |

**Eight of ten years close to the digit.** This is the
[[sibling-identity-check]] class exactly: `noanchor` means UNCHECKED, not
uncheckable, and `reconcile_baseline.py` is blind to sibling sums.

**1873 is arbitrated by it.** The two T1 labels disagree — `Oil :Train Or
Blubber, And Spermaceti` prints 17,686, `Train Or Blubber, And Spermaceti`
prints 17,886. The sibling sum is 17,886, so the higher reading is right and
17,686 is the misread.

1874 is a genuine parse loss (both sibling blocks truncated, and a duplicate
unit-NULL copy of each sits beside them).

## Finding 2 — "Whale Fisheries" is an ORIGIN promoted to an article

`Whale Fisheries: Northern` / `Southern` are printed ORIGIN rows — whale
products were credited to the fishery, not to a country. There are 107+ rows
carrying it as `country_raw` (1872-1899). But in ten volume-blocks the printed
sub-head `Whale Fisheries:` was absorbed as the **article**, leaving
`Northern` as the country and hiding the table:

| volume | stale group | rows | years |
|---|---|---|---|
| as_1886 | OIL | 17 | 1886 |
| as_1886-90 | WHALEBONE (Whalefins) | 8/8/29/7/8 | 1886-1890 |
| as_1886 | SKINS, FURS, and PELTS | 9 | 1886 (sealskins — legitimate origin) |
| as_1897/98/99 | **NUTS AND KERNELS** | 47/47/45 | 1893-1899 |

The `NUTS AND KERNELS` ones are the largest single loss here: a multi-year
block of whale-oil origins (Newfoundland, Falkland Islands, Canada) filed
under a nut group. This is the [[phantom-region-article]] class.

## Finding 3 — a wrong baleen number that the label split protects

`Whalefins` 1881 reads **30,956 Cwt** against neighbours of ~2,000-4,000.
`as_1881` alone prints 30,956; **as_1882, as_1883, as_1884 and as_1885 all
print 2,103**, and the payload carries that 2,103 too — under the *other*
label, `Whalebone (Whalefins)`.

So the era-spelling split does more than fragment the series: it **shields a
bad reading from the cross-volume vote**. Four volumes to one would have
settled 1881 instantly had both spellings been one commodity. Worth
generalising — wherever a duplicate shadow exists, the vote is running on a
subset of the evidence. Related: [[vote-tiebreak-lone-reprint]].

## Smaller cautions

- `Whalefins` 1879 and 1880 both read exactly **2,145 Cwt**. Attested in five
  and four volumes respectively, so it is what the source prints, but an
  identical two-year run in a series that otherwise moves 20-40% a year looks
  like a compositor copying the prior column. Flagged, not changed.
- The Ton/Tun split across oil labels is transcription, not a real unit
  change — magnitudes match across it (1893: 19,939 Ton vs 19,337 Tun). The
  payload already has a Tun/Ton fold; these labels are not landing in it.
- `Bones (except Whalefins)` is a *different* commodity (bone for manure and
  manufacturing) — the phrase is a printed exclusion, not a whale product. It
  is itself fragmented across ~8 labels but is out of scope here.

## What it would take

1. Fold the eight oil labels into one commodity and the four baleen labels
   into one (era-wording folds, the `fold_era_wordings` path). **Taxonomy
   change — needs adjudication, not a loop iteration.**
2. Teach the reconciliation the sibling pair `Train or Blubber` +
   `Spermaceti or Head Matter` -> the combined line. Eight years close exactly
   the moment it exists.
3. `group_repairs` for the ten `Whale Fisheries`-as-article blocks, recovering
   the country as `Whale Fisheries, Northern`. Ordinary loop work.
4. Adjudicate `Whalefins` 1881 to 2,103 (four volumes to one).

Item 3 is the only one that is unambiguously in scope for `/next-defect`;
items 1 and 2 change taxonomy or the vote and are the user's call.

---

## Repair 1 (2026-07-28) — the baleen half of finding 2

Worked at the user's request ("queue whalefisheries for next iteration").
**Baleen only.** The oil half is deliberately deferred — see below.

### What was wrong

In each of as_1886 through as_1890 the whalebone origin table is printed as
one run, but the parser promoted the sub-head `Whale Fisheries:` to the
ARTICLE partway down. Everything from the fishery row onward split off under
a phantom article, so the year reconciled on only its head rows and read
0.86-0.92. The fishery row itself lost its identity too: country `Northern`
rather than `Whale Fisheries, Northern`.

Fix: strip the phantom article (restoring NULL, matching the head rows) and
restore the fishery row's country. Ten `group_repairs` rows — one per volume
for the fishery row with `new_country`, one for the remainder.

### The arithmetic

| year | foreign members = printed | British = printed | grand | vs T1 |
|---|---|---|---|---|
| 1886 | 5,382 ✓ | 136 ✓ | 5,518 | see below |
| 1887 | 3,951 ✓ (values 126,679 ✓) | 191 ✓ | 4,142 | **exact** |
| 1888 | 4,181 vs **4,176** | 130 ✓ | 4,311 | 1.0012 |
| 1889 | 4,393 ✓ (values 176,114 ✓) | 76 ✓ | 4,469 | **exact** |
| 1890 | 4,714 ✓ | 280 ✓ | 4,994 | **exact** |

**1888** is five over on quantity while its **value column closes exactly**
(144,807). Both engines read the same digits and no price test picks the
culprit — Denmark 258 and Germany 258 are suspiciously equal but nothing
confirms it. Left as printed rather than guessed. Page-image candidate.

**Range discipline**: the as_1888 repair stops at seq 3615. Seq 3616-3636 is a
**WOOD AND TIMBER `Hewn: Fir`** table glued under the same phantom article —
310,522 Loads of it. Relabelling that range as whalebone would have been a
catastrophe. as_1889 has the same wood table at seq 3570+, but there it wears
its own article and was never at risk.

### 1886: closure outranks print-majority

The 1886 anchor is split **four ways** — 5,618 (as_1886, as_1890), 5,518
(as_1889), 5,513 (as_1887) — and the cross-volume vote took 5,618 on a 2-1-1
count, tier C. The origin block closes **three** printed totals at 5,518, and
as_1889 prints that figure independently. A 5->6 misread copied into two
printings outvotes the truth; arithmetic does not.

Adjudicated in `reference/manual_t1.csv` (1886 -> 5,518, tier A), the same
shape as the Oil Seed Cake 1890 precedent already in that file. **Note this is
an anchor override, not a group repair — flagged for the user to veto.**

`manual_t1` is consumed by `reconcile.py`, not `integrate_sources.py`, so the
vote had to be rebuilt. Before doing that the database was copied aside and
`consensus` snapshotted; the re-run changed **exactly one row in each
direction** — 5,618/tier C out, 5,518/tier A in — confirming the re-vote was
otherwise a faithful reproduction.

### Result

| commodity-year | before | after |
|---|---|---|
| Whalebone (Whalefins) 1886 | 0.8841 | **1.0000** |
| Whalebone (Whalefins) 1887 | 0.8776 | **1.0000** |
| Whalebone (Whalefins) 1888 | 0.9201 | 1.0012 |
| Whalebone (Whalefins) 1889 | 0.9060 | **1.0000** |
| Whalebone (Whalefins) 1890 | 0.8562 | **1.0000** |

Corpus: 9,634 commodity-years, exact01 3,124 -> **3,128**, GBP within 0.1%
**50.9%**, within 5% 68.0%. Five commodity-years changed, **0 regressions**.

### Why the oil half was deferred

Two reasons, both real:

1. **The target label is a taxonomy decision.** The correctly-labelled oil
   rows carry article NULL under group `OIL`, whose signature collides with
   every other oil line in the corpus. Relabelling the phantom rows to match
   them would merge whale oil into that collision; giving them a proper
   article name is a taxonomy call, which this loop does not make alone.
2. **Relabelling alone would not close them.** The oil T1 is the COMBINED
   line and the origin tables are the two siblings (finding 1), so the years
   would still read nodata afterwards.

The as_1886 oil arithmetic is nevertheless already proved and waiting:
`Fish: Train or Blubber` foreign 6,358 + 185 + 214 + 1,068 + 464 + 375 =
printed 8,664 exactly (values 175,244 exactly), British 245 + 5,545 + 112 =
5,902 exactly, grand 14,566; `Spermaceti, or Head Matter` grand 1,268; and
**14,566 + 1,268 = 15,834 = the combined T1 exactly**. One caution for whoever
takes it: seq 2121's country is `Fish : Train or Blubber` — the run-in head
swallowed the first origin's name, and the 6,358 belongs to a country the
parse has lost. Needs the page.

The `as_1897/98/99 NUTS AND KERNELS | Whale Fisheries` blocks (47/47/45 rows,
1893-1899) remain the largest single loss in this family and are untouched.
