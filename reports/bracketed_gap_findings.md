# Bracketed-gap campaign — state and open items

Started 2026-07-28 (Fable, at the user's request: "commodities with data,
then a gap, then data again — a data problem, not a change in trade").
Instrument: `scripts/find_bracketed_gaps.py` -> `reports/bracketed_gaps.csv`
(ranked by GBP at stake; re-run after any payload rebuild).

**The method that worked**: for a hole year, the missing table's own printed
TOTAL must equal the anchor — search BOTH engines' obs tables for that exact
number under ANY label. It found the table (or proved the anchor wrong) in
six of eight hunts.

## Fixed (commits 3666047, 2f696d1, 48d485d — see messages for full proofs)

boots 1887-90 (as_1891 gloves-column slip; manual_t1), chemical products
(hyphen split), almonds (interleaved labels), cocoa 1883-85 (phantom-region
folds), glucose (era split), woollen rags (five heads), tanning bark
(era folds, partial), spices pepper+unenumerated 1889/90 (glue block +
supersede), sheep 1887 (garbled continuation head), iron ore 1894 (era head).

## Diagnosed, NOT fixed — evidence gathered, ready to work

- ~~**Sardines 1895 ANCHOR SLIP**~~ **FIXED in sweep 8 — and the re-test was
  worth demanding.** It is neither an anchor slip in the "the anchor is a
  different series" sense nor a glue block: it is the same *foreign body*
  already adjudicated for 1894 — the abstract's sardines line borrows the
  figures of the line printed immediately below it. `Cured, Sardines`
  1895: 1,082,588 -> **140,178**, origins 140,187, EXACT. See "Sweep 8" at
  the foot of this file.
- ~~**Spirits `Unenumerated, Not Sweetened` 1876 + 1887 ANCHOR SLIPS**~~
  **FIXED in sweep 4 — and the diagnosis was backwards.** The anchors are
  solid Tier-A totals; the collisions meant the spirits *tables* are misfiled
  under the `FRUIT|Raisins` and `SPIRITS|Rum` labels. Both years now close
  exactly, and Geneva 1876/1887 with them. See "Sweep 4" at the foot of this
  file, including the retracted reasoning and the corrected method note.
- **China/Porcelain 1883-85** (read 0.05/0.05/0.00): the tables are GLUED
  under CHEMICAL MANUFACTURES labels. as_1883: group `CHEMICAL MANUFACTURES
  and PRODUCTS. Unenumerated`, article `Other Vegetable matter applicable to
  the uses of Chicory or Coffee` — members (Germany 37,110 + Holland 60,103 +
  Belgium 12,179 + France 24,807 + China 3,902 + Japan 4,821 ...) sum to the
  china T1 146,471 EXACTLY. as_1884: same group, article None (T1 143,556
  exact); as_1885: `Vegetable matter applicable...` (T1 146,830 exact).
  Needs seq-scoped group_repairs (find the seq ranges; the chicory line's own
  small table is adjacent — split carefully).
- **Feathers Ornamental 1883** (read 0.10) and **Drugs Unenumerated 1879**
  (hole): NO total matching the anchor in either engine — lost block or
  wrong anchor. Page-image candidates. (Drugs 1880/81 near-misses at
  663,459/854,322 are OTHER tables — not matches.)

## Residues from the fixed families (small, with evidence)

- Gutta percha 1874 short EXACTLY 3,000 (lost row, Egypt fits the series —
  not guessed); 1891 fused sub-entry label. reports/gutta_percha_findings.md.
- Cocoa 1882: NO import block in either engine (both carry only the
  re-export table, Total 8,429,893 closing on itself). 1885 residual 0.92.
- Chemical products 1873/1875 read 1.30-1.32 (country-name variants double-
  counting inside the union) and 1881 0.90.
- Bark 1880 (0.889), 1881 (1.360); 1892-99 era copies over-count 1.2-1.5x
  on country-name variants — needs per-country reconciliation, NOT a fold.
- Sheep 1887 seq 45: 5,524 with the country label absorbed into the article
  text ('Sheep and Lambs') — the block's missing 0.57%; page-image for name.
- Boots 1886: anchor sits under the `Leather Manufactures` label-key split
  (the payload label pair 'Boots And Shoes' / 'Leather Manufactures — Boots
  And Shoes' is a headless-vs-headed era pair the fold pass cannot see).

## Known-and-queued items the screen keeps re-finding (do not re-diagnose)

Sugar Unrefined 1874 (no block in either engine), Caoutchouc — Manufactures
Of 1892-98 (printed anchor scope change, session-11 iteration 11), ~~Mahogany
1886-88/1892 (no table on either half, iteration 12)~~.

**MAHOGANY IS RETRACTED (2026-07-29, iteration 18).** The tables for **1887 and
1888 were there all along**, sitting in a payload node called `Wood And Timber
— Furniture And Hardwoods : Mahogany` — a sub-label, holding countries and no
anchor. Folded, they close **to the digit**: 1887 37,650 = 37,650 and 1888
42,859 = 42,859. Found by `scripts/match_orphan_countries.py`, which matches a
country-only node to the commodity holding its anchor by arithmetic alone.

1886 and 1892 are still open, so the entry is not withdrawn entirely — but
"no table on either half" was checked by hunting the *printed total* through
`country_obs`, and that hunt cannot see a table whose rows are present but
filed under a sub-label the payload keeps separate. **Any "known-dead" verdict
reached by a printed-total hunt alone should be re-tested against the two
arithmetic matchers before it is trusted again.**

## Instrument gaps worth building (from the gutta percha post-mortem)

1. Detector A's token-subset clustering silently UNIONS split labels; when
   the cluster closes but a member with its own anchor reads <0.6 or >1.9
   alone, emit that as a 'split-label' finding. Would have caught gutta
   percha and enumerates the class.
2. Headless-vs-headed era pairs with digit-identical T1 overlap (gutta
   percha Raw, boots/leather) — a screen for that signature.

---

## Sweep 4 (2026-07-28) — the spirits "anchor slips" were not anchor slips

**Item worked**: `Unenumerated, Not Sweetened` (Proof Gallon) 1876 + 1887,
GBP 5,709,213 + 5,747,709 = 11.46M — the top *workable* rows of
`reports/bracketed_gaps.csv` (the three ranked above them are the known-dead
sugar 1874 / caoutchouc 1892-98 / mahogany 1886-88).

### The diagnosis above was backwards — correcting it

The "ANCHOR SLIP" entry in the *Diagnosed, NOT fixed* section is **wrong** and
is retracted here. Both anchors are solid Tier-A national totals:

- 1876: `as_1876`, `as_1877`, `as_1878`, `as_1879` each print **2,324,405**
  (`as_1880` alone prints 2,524,405 — a lone digit slip). The as_1876 five-year
  comparative abstract prints the whole series 1,307,428 / 1,260,050 /
  1,865,939 / 2,795,378 / 2,324,405.
- 1887: `as_1887`, `as_1889`, `as_1891` each print **2,340,078**
  (`as_1890` alone 2,342,078).

The collisions that prompted the slip theory were read the wrong way round.
`FRUIT | Raisins` does not lend its total to spirits — **the spirits origin
table is misfiled under the raisins label**, and the number is the spirits
block's own. Same for `SPIRITS | Rum` in 1887. Both are ordinary glue blocks,
and both tables were sitting in `country_obs` the whole time.

**Method note worth keeping**: when the printed-total hunt finds the anchor
under another label, the *default* reading is a misfiled table, not a borrowed
number. Check the found rows' unit first — a `Proof Gallons` TOTAL under a
`Raisins` label is the giveaway.

### 1876 — straight relabel, both columns exact

`as_1876` `country_obs` seq 137-146, glued under `FRUIT | Raisins`
(contiguous with the Brandy segment at 132-135 and the Rum segments at
124-129 that earlier sweeps already repaired).

| | qty | value |
|---|---|---|
| Geneva (seq 137-139) | Holland 318,967 + Other 7,401 = **326,368** = T1 | 55,875 + 2,001 = **57,876** = printed |
| Unenumerated (seq 140-146) | Russia 119,065 + Germany 1,768,594 + Holland 45,587 + Belgium 237,080 + France 145,519 + Other 8,560 = **2,324,405** = T1 | 6,005 + 139,672 + 4,271 + 18,811 + 13,767 + 1,705 = **184,231** = printed |

The raw page (line 35650ff) puts every figure in the same cell as its own
label (`" Germany - - - -` / `Proof Gallons. 1,768,594`), so there is **no**
row slip in this printing. Two `group_repairs` rows, nothing else needed.

### 1887 — the same one-row slip the Brandy repair already knew about

`as_1887` `country_obs` seq 97-113, glued under `SPIRITS | Rum`.

The mechanism, visible three times on this one page: the repeated unit-header
row (`Proof Gallons. / £ / Proof Gallons. / £`) is emitted *between* a
sub-block's run-in head and that head's figures, so the parser paired
label(i+1) with numbers(i), dropped the first label, and orphaned the last
number as a bare unlabelled pair. Earlier work encoded exactly this for the
Brandy segment (seq 87-89 `new_country` repairs) without naming the class.

Re-paired in printed order, eight labels against eight numbers:

    Russia 95,054 / Sweden 42,562 / Denmark 156,669 / Germany 1,814,191 /
    Holland 113,678 / France 4,300 / USA 104,238 / Other Foreign 6,527
      -> 2,337,219 = printed foreign TOTAL, values -> 137,425 = printed
    British: S.Africa 861 + Australasia 1,317 + Other British 681 = 2,859
      (printed; no slip — no header row intrudes)
    grand 2,340,078 = T1 EXACTLY

**The arithmetic cannot settle the direction** — the sum is shift-invariant.
The series does, three ways:

1. Germany is the dominant source every neighbouring year (1,768,594 in 1876;
   2,489,395 in 1889; 1,575,747 in 1890; 1,153,103 in 1892) while Holland
   never exceeds ~66k (45,587 / 16,100 / 21,219 / 66,486). The unshifted parse
   makes Holland 1,814,191 for one year — impossible.
2. France 4,300 sits against 1889's 4,827 and 1890's 4,319; unshifted it is
   113,678.
3. Russia is present in 1876 and in 1889-91 and would be absent from 1887 alone.

The Brandy segment on the same page confirms the mechanism independently:
shifted it gives Germany 79,120 against 1876's 82,286 and Holland 19,326
against 1876's 18,130.

Encoded as seven per-row `new_country` repairs (seq 101-107), one range repair
for the British half (109-111), one for Geneva (seq 97 -> Holland), and two
`manual_rows` for the orphans that no parse carries — Unenumerated
`Other Foreign Countries` 6,527/£1,385 (raw 45605-45606) and Geneva
`Other Foreign Countries` 792/£180 (raw 45495-45496). Neither is guessed: the
parsed members and the printed subtotals demand those two numbers and nothing
else closes, on **both** columns.

### Result

| commodity-year | before | after |
|---|---|---|
| Unenumerated, Not Sweetened 1876 | 0.0000 | **1.0000** |
| Unenumerated, Not Sweetened 1887 | 0.0000 | **1.0000** |
| Spirits — Geneva 1876 | 0.0000 | **1.0000** |
| Spirits — Geneva 1887 | 0.0000 | 0.9999 |

Geneva 1887 stops at 259,740 of 259,776 because its British half is printed
only as a subtotal (36 / £17) with no country line — honest, not lossy.

Corpus: 9,634 commodity-years with a T1 line, exact01 3,115 -> **3,119**
(32.3% -> 32.4%), GBP within 0.1% 50.8% -> **50.9%**, within 5% 68.0%.
Full per-cell diff: **4 commodity-years changed, 0 regressions.**

### Fell out of this work — queued with proofs, not worked

- **Rum 1887 over-count, fully diagnosed.** Reads 6,589,972 against T1
  6,362,070. The block's own members close exactly (foreign 287,143 + British
  6,074,927 = 6,362,070). The excess is seven glue-leaked cells still filed as
  Rum: sweden 95,054 + holland 79,120 + denmark 42,562 + other foreign
  countries 4,989 + russia 2,879 + austrian territories 2,168 + channel
  islands 1,130 = **227,902 exactly**. Sweden/Denmark belong to the
  Unenumerated segment, Holland and the 4,989 to Brandy, Russia and Austrian
  Territories to the methylated block, Channel Islands to Perfumed. They came
  in as `manual_rows` (`source='human'`), so clearing them means *removing*
  reference rows — against the append-only convention. **Needs a live
  decision**: delete the seven, or add a supersede-style mechanism for
  hand-keyed cells.
- **Brandy 1887 seq 90.** The earlier repair "left seq 90 as printed"; under
  the now-confirmed shift its 4,989 is **Spain**, and the lost 3,204 is
  **Other Foreign Countries**. One `new_country` row plus one `manual_rows`
  row would close Brandy 1887 from 0.9963 to exact.
- **`as_1888` carries the same disease**: `SPIRITS | Rum` runs unbroken from
  seq 91 to 186 (rum + tobacco + cigars). Not currently flagged by
  find_bracketed_gaps, so it is invisible to the campaign screen.
- **Instrument gap 3** (add to the two already listed): a screen for the
  *unit-header-displaces-first-country* signature — a sub-block whose parsed
  members fall short of its printed subtotal by exactly the value of a bare
  unlabelled number pair later in the same block. It fires three times on this
  single page and is certainly not confined to it.

---

## Sweep 5 (2026-07-28) — clearing the as_1887 Rum glue leak

**Item**: Rum 1887's over-count (reading 1.0358), queued by sweep 4 as needing
a live decision. The user asked for a recommendation and it was taken.

### What the seven stray cells actually were

Rum 1887 read 6,589,972 against T1 6,362,070 while the block's own members
close perfectly (foreign 287,143 + British 6,074,927). The excess was seven
`manual_rows` cells still filed as Rum:

    sweden 95,054 + holland 79,120 + denmark 42,562 + other foreign
    countries 4,989 + russia 2,879 + austrian territories 2,168 +
    channel islands 1,130  =  227,902 exactly

They came from a **bulk page-transcription batch** — `as_1887 SPIRITS|Rum` is
a contiguous run of 24 `manual_rows` with empty note fields, one of the largest
such clusters in the file (empty notes are not themselves a smell: 50% of
`manual_rows` have none, and they cluster into transcription batches). Whoever
keyed it walked down the printed column and inherited the sticky `Rum` article
label straight through the segment breaks. The **numbers are good; the label is
wrong**.

That is what made deletion the right call rather than a new supersede
mechanism. Six of the seven were checked one at a time and are **exact
duplicates already present under a correct label**:

| figure | now filed as | source |
|---|---|---|
| 95,054 | Unenumerated, not Sweetened or Mixed — Russia | groupfix |
| 42,562 | Unenumerated, not Sweetened or Mixed — Sweden | groupfix |
| 79,120 | Brandy — Germany | groupfix |
| 2,879 | Unenumerated, Sweetened or Mixed (Tested) — Russia | twoup |
| 2,168 | Unenumerated, Sweetened or Mixed (Tested) — Austrian Territories | twoup |
| 1,130 | Perfumed — Channel Islands | twoup |

Deleting them discards no transcription work — the same printed cells enter
under correct labels. Keeping them was double-counting, not caution.

### The seventh forced the queued Brandy item

`other foreign countries` 4,989 existed **only** under Rum. By the slip sweep 4
named, it is Brandy's **Spain** row, so removing it without relabelling would
have made Brandy worse. Both were done together:

- seq 90 -> `Brandy`, `new_country=Spain` (completes the seq 87-89 repairs,
  which had left seq 90 "as printed" because the slip direction was not yet
  known).
- The orphan 3,204/£1,122 at raw lines 45409-45410 -> `manual_rows` as Brandy's
  true Other Foreign Countries. Not guessed: the four labelled members total
  2,820,773 / 1,314,877 against printed foreign TOTALs of 2,823,977 /
  1,315,999, so both columns demand exactly 3,204 and 1,122.
- seq 92-94 -> `Brandy`: the British half (1,005 + 520 + 606 = printed 2,131,
  values 455+366+404 = 1,225) had never been relabelled out of the glue and was
  **absent from `country_year_final` entirely**.

### Result

| commodity-year | before | after |
|---|---|---|
| Spirits — Rum 1887 | 1.0358 | **1.0000** |
| Spirits — Brandy 1887 | 0.9963 | **1.0000** |

Corpus: 9,634 commodity-years, exact01 3,119 -> **3,121**, GBP within 0.1%
**50.9%**, within 5% 68.0%. Two commodity-years changed, **0 regressions**.

**The deletion was self-verifying**, which is why it was safe: 6,589,972 −
227,902 = 6,362,070, so Rum had to land on the anchor to the digit or the
diagnosis was wrong. It did.

### Convention amended

`reference/*.csv` are append-only **except** rows proven to be duplicate
transcriptions under a superseded label, which may be removed in a commit that
cites the closure proving it. Recorded here and in the plan memory's guardrails
so the next session finds a rule covering the deletion rather than an
unexplained one.

### Still open on this page

- **Five Gallons-unit strays remain** under `as_1887 SPIRITS|Rum` (`madeira`
  1,606, `gibraltar` 918, `canary islands` 721, `foreign countries` 434,
  `british possessions` 14). They do not affect the Rum ratio — different unit,
  excluded from the T1 comparison — and unlike the seven they have **not** been
  traced to a correct label, so they may be the sole carrier of their figures.
  Trace before touching; do not blind-delete.
- `as_1888` still carries the same glue unbroken from seq 91 to 186, invisible
  to `find_bracketed_gaps`.

---

## Sweep 6 (2026-07-28) — china/porcelain 1883-85

**Item**: `China, Or Porcelain, And Earthenware` 1883-85, GBP 1,447,644 —
the last fully-diagnosed entry in the *Diagnosed, NOT fixed* list above.

### The tables

All three are glued under CHEMICAL labels, exactly as diagnosed. The printed
head **`CHINA or PORCELAIN, AND EARTHENWARE.`** is visible in the as_1883 raw
at line 23502: it sits in the left column of a **two-up page** whose right
column is an unrelated table (Mexico / Peru / Bolivia / Chile), which is why
the sticky label never advanced.

- **1885** (`as_1885` seq 374-387) — the cleanest. Both columns close on
  **all three** printed totals: foreign 144,529 / £503,854, British 2,301 /
  £14,642, grand **146,830 = the Tier-A T1**. Range starts at 374 so the
  chicory line's own tail TOTAL at seq 373 (28/£74) stays out.
- **1884** — taken from **Infinity**, because the two engines split the two
  columns between them. Chandra (= the raw md, lines 23342-23432) reads
  British East Indies **176** and Japan value **25,294** and closes *neither*
  column (143,554 vs 143,556; 547,600 vs 550,600). Infinity reads **178** and
  **28,294** and its quantity column closes **exactly** on 143,556 = printed
  TOTAL = the Tier-A T1 across five volumes. 6->8 and 5->8 are this corpus's
  standard broken-glyph confusions. Infinity's value column is over by £1
  (France 141,329 where the column demands Chandra's 141,328) — the one cell
  where Chandra is right, left alone rather than replaced.
- **1883** (`as_1883` seq 364-376) — **value column closes EXACTLY** at
  £603,410, so all twelve members are present and their values are right.
  Quantity sums 146,441 against a printed 146,471: **short 30, unresolved.**
  Both engines read the same digits, no member row is missing, and no price
  test picks the culprit (Australasia's £17.74/cwt is the only outlier and
  +30 does not fix it). Left as printed rather than guessed. Ratio 0.99980 —
  inside the 0.1% band, but it is a residue, not a closure. **Page-image
  candidate.**

### A stale two-up cell was sitting on 1884

After the repairs, 1884 read **1.041** — 149,451 against 143,556. The excess
was `Other Countries` **6,896** (value £17,940, unit NULL, q_tier C), a two-up
gap-fill cell under the *target* label that beat the repair's own Other
Countries row at `drop_already_added`. 6,896 − 1,001 = **5,895 exactly**. The
printed table says 1,001 and the column closes on 143,556 with it and nothing
else, so closure outranked the two-up reading; cleared with a supersede-only
row scoped to 1884.

### Method note — the repair that "worked" and moved nothing

Worth recording because it cost a full rebuild cycle. The first pass targeted
group `CHEESE` / article `CHINA or PORCELAIN and EARTHEN- WARE`, chosen by
matching the incumbent 1886/1889 rows and confirmed by
`article_group_authority` (0.82 plurality). It was **wrong**: that pair is a
*duplicate* label feeding a separate payload commodity,
`Cheese — China Or Porcelain And Earthen- Ware`, which carries **no T1**. The
groupfix audit reported `admitted 12 / 11 / 11`, `country_year_final` showed
the blocks landing with 1884 and 1885 summing to their anchors exactly — and
the corpus baseline **did not move by a single cell**. The payload keys this
commodity on the **group** (`CHINA OR PORCELAIN AND EARTHENWARE`, article
NULL — the 1886/1887/1888 pattern), not the article.

**Instrument gap 4**: flag any group repair whose admitted rows land in a
payload commodity with no `§TOTAL`. That is a silent failure — every
intermediate signal says success — and only a per-commodity-year payload diff
catches it. `country_year_final` being right is not evidence the repair worked.

### Result

| commodity-year | before | after |
|---|---|---|
| China, Or Porcelain, And Earthenware 1883 | 0.0534 | 0.9998 (residue: 30 cwt) |
| China, Or Porcelain, And Earthenware 1884 | 0.0480 | **1.0000** |
| China, Or Porcelain, And Earthenware 1885 | 0.0000 | **1.0000** |

Corpus: 9,634 commodity-years, exact01 3,121 -> **3,124**, GBP within 0.1%
**50.9%**, within 5% 68.0%. Three commodity-years changed, **0 regressions**.

### Still open on this commodity

**1880 and 1881 are also holes** (both 0.0000) and were *not* in the campaign
list. 1881's T1 is contested — `as_1882`/`as_1883` print 134,487 (tier A) but
`as_1884`/`as_1885` print 131,487 (tier B), a 3,000 split of exactly the kind
the 1884 Japan cell showed. Worth taking next; the same CHEMICAL glue is the
obvious first place to look.

---

## Sweep 7 (2026-07-28) — china/porcelain 1880-81: the "holes" were a sibling parent

**Item**: `China, Or Porcelain, And Earthenware` 1880 and 1881, flagged at the
end of sweep 6 as unlisted holes (both 0.0000).

### They are not holes

The abstract for 1878-1881 prints **two** lines where later years print one:

- `China or Porcelain Ware` — its own Tier-A series, 1876-1881
- `China or Porcelain and Earthenware` — the COMBINED line, 1878 onward

and the origin section prints two matching tables, `CHINA or PORCELAIN WARE`
and `EARTHENWARE, not being China or Porcelain Ware`. **There is no separate
earthenware anchor anywhere in the corpus.** So the combined line is a parent
whose children are separately filed, and it reads nodata because nothing sums
its two children — the [[sibling-identity-check]] class again, one year after
the same structure was found in whale oil.

The identity closes to the digit in both years:

| year | china ware | earthenware | sum | combined T1 |
|---|---|---|---|---|
| 1880 | 54,562 | 53,695 | **108,257** | 108,257 |
| 1881 | 61,971 | 72,516 | **134,487** | 134,487 |

**Merging them into the parent commodity is not possible mechanically.** Both
children list the same countries (Germany, Holland, Belgium, France, Other
Countries), so relabelling both into one commodity collides on
`(sig, country, year)` and the second table would be silently dropped at
`drop_already_added` — losing data, not gaining it. Closing these years needs
the country rows *summed* before admission, which is a modelling change and
the user's call, not loop work.

Also note `China or Porcelain Ware` 1880 was **already exact** (54,569 against
its own 54,562 anchor) — the sweep-6 note calling 1880 a hole was reading the
parent's ratio, not the child's.

### What was fixable: one row

`China And Porcelain Ware` **1881: 0.9352 -> 1.0000**. `as_1881` seq 173 carries
4,013/£21,404 under the label `TOTAL`, so `is_subtotal` dropped it. It is not
the total — it is the block's last member, `Other Countries`. Proved three
independent ways:

1. The line's own Tier-A anchor is 61,971 and the six labelled members sum to
   57,958. 61,971 − 57,958 = **4,013** exactly.
2. The raw (as_1881 md lines 22556-22621) shows the printed head
   `CHINA or PORCELAIN WARE:` followed by seven country labels ending in
   `Other Countries`, on a **two-up page whose right column is a Tons table**.
   The intruding column header displaced the first row's figures and orphaned
   the last pair — the same mechanism as the as_1887 spirits page (sweep 4).
3. The sibling identity above.

Series shape confirms the direction: the alternative pairing would put China
at 19,763 cwt (4,594 in 1880, 3,902 in 1883) and Germany at 4,013 (10,565 in
1880) — both implausible.

Corpus: exact01 3,128 -> **3,129**, GBP within 0.1% **50.9%**. One
commodity-year changed, **0 regressions**.

### Found in passing, not worked

`CHINA, OR PORCELAIN, AND EARTHENWARE` is a **sticky group** in 1893-1899,
carrying Barley, Wheat, Peas, Buckwheat, Oatmeal and Groats, Maize, Rye,
Wheatmeal, Herrings, Manufactured tobacco and Cotton Waste — tens of millions
of cwt filed under a china heading. That is a large separate defect and a
better target than anything left in this family.

Earthenware itself carries duplicate shadows with no anchor to arbitrate them
(1880: 53,635 under `EARTHWARE, NOT BEING...` vs 51,846 under `DYE WOODS`;
1881: 72,516 under `COTTON MANUFACTURES` vs 5,948 under `DYE WOODS`). Without
a T1 there is nothing to verify a consolidation against, so they are left.

---

## Sweep 8 (2026-07-29) — sardines 1895 is a foreign body, not an anchor slip

**Item worked**: `Cured, Sardines` 1895, read 0.13 (origins 140,187 against an
anchor of 1,082,588), GBP 4,738,884 — the top *workable* row of the refreshed
`reports/bracketed_gaps.csv` (the three ranked above it are the known-dead
sugar 1874 / caoutchouc 1892-98 / mahogany 1886-88).

### The re-test was worth demanding, and both hypotheses in the queue were wrong

The queued diagnosis offered two readings — "anchor slip" (the sardines anchor
is really some other series' total) or "glue block" (a sardines-unit table
filed under the `FISH | Cured or Salted` label). **Neither.** The anchor is the
sardines line's own cell in the abstract, and it has simply been read off the
row below.

`Fish — Cured or Salted, unenumerated` runs

    1893      1894      1895      1896      1897      1898      1899
  916,366   925,244  1,082,588 1,060,813 1,165,664 1,200,723 1,003,397

— a smooth, independently anchored series. **1,082,588 is its 1895 figure**,
and 925,244 (the value already overridden out of sardines 1894) is its 1894
figure. Same neighbour, two consecutive years.

### The Infinity abstract parse of this table is shifted a row

Visible directly in `infinity_obs`:

| volume | what Infinity puts on the SARDINES label |
|---|---|
| `as_1897` | 916,366 (1893) · 925,244 (1894) · 1,082,588 (1895) — all three are the unenumerated line |
| `tn_1899` | 1,060,813 (1896) · 1,165,664 (1897) · 1,200,723 (1898) — same |
| `as_1899` | **140,178** (1895) — correct |

The Chandra parse is right in the contemporary volume and in `as_1899`, and
wrong only in `as_1898` for 1894 and 1895.

### Why the vote lost, and the tie-break that would have saved it

1895 readings: **140,178** from `as_1897`/ch, `as_1899`/ch and `as_1899`/inf —
against **1,082,588** from `as_1897`/inf, `as_1898`/ch, `as_1898`/inf,
`tn_1899`/ch and `tn_1899`/inf. **`tn_1899` is `as_1898` reprinted**, so the
5-3 majority is really one volume plus one Infinity row-shift counted five
times, beating the contemporary volume. Textbook
[[vote-tiebreak-lone-reprint]] — except here the reprint is not lone, it is
*duplicated*, which is worse.

### Five independent supports for 140,178

1. `as_1897` — the **contemporary** volume — reads it in Chandra.
2. `as_1899` reads it in **both** engines.
3. The origin table sums to **140,187**, nine cwt (0.006%) above it.
4. **Unit price.** £427,113 (the value column, unanimous across every volume)
   ÷ 140,178 = **£3.05/cwt**, against £3.64 / £3.25 / £2.95 / £2.88 in 1893,
   1894, 1896 and 1897. With 1,082,588 the price would be £0.39/cwt.
5. Series shape: 125,292 / 105,116 / **140,178** / 175,723 / 197,747 /
   239,273 / 217,220.

### Result

One `manual_t1` row. `reconcile.py` re-run against a `consensus_bak` snapshot
changed **exactly one row in each direction** (29 of 29 override rules applied),
proving the corpus-wide re-vote was otherwise faithful.

`Cured, Sardines` 1895 **under -> EXACT** (140,187 against 140,178). Baseline
9,634 c-y: exact01 3,132 -> **3,133** (32.5%), GBP 50.9% / 68.2% within 5%.
One commodity-year changed, **0 regressions**.

### Found in passing, not worked

- The sardines origin rows are triplicated across three label variants —
  `FEATHERS AND DOWN | Cured, Sardines`, `FISH (INCLUDING TURTLE) | Cured,
  Sardines` and `FISH (INCLUDING TURTLE) | Sardines`. The payload folds the
  first two but leaves **`Fish (Including Turtle) — Sardines` (£426,739) as a
  separate duplicate-shadow node** carrying a subset of the same countries.
  Belongs with the 44 weak duplicate shadows already queued.
- `FEATHERS AND DOWN` as the group on a sardines table is another sticky-group
  instance; harmless here only because the article carries the sig.
- `Cured or Salted, unenumerated` 1893 is tier C on `as_1897` alone, because
  the Infinity copy of that volume spent its 1893 cell on the sardines label.
