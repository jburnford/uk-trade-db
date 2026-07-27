# Bacon and hams — one heading, two tables, one of them deleted (2026-07-26)

Phase 0.3 of the corpus-wide plan asked what to do about two apparent duplicate
series: `Bacon And Hams — Bacon` (£212M) and `Bacon` (£124M), which the dupe
detector scored as 15–16% copies of each other. Neither was a duplicate. The
larger of the two was a chimera, and finding out why exposed a defect class the
payload builder had carried since it was written.

## What the volumes print

The country tables print **two** tables under one section heading — `BACON AND
HAMS | Bacon` and `BACON AND HAMS | Hams` — in every year from 1872 to 1895.
The Abstract prints their **sum** as a single national line, `Bacon and Hams`,
until 1895, and only from the 1896 volume does it split into `Bacon` and `Hams`.

The identity that proves this is the section's own arithmetic:

```
    bacon origins + hams origins  =  printed 'Bacon and Hams' total
```

It closes **to the digit in thirteen of the twenty-four years** — 1872, 1873,
1875, 1876, 1878, 1879, 1881, 1884, 1887, 1888, 1890, 1894, 1895 — and within
0.2% in six more. It is confirmed from the other end too. `tn_1871` is the one
volume that prints bacon alone before the split, as `Bacon and Hams: Bacon`, and
the differences against the combined line are exactly the printed ham totals:

```
    1868   638,127 − 592,668 = 45,459 = Hams 1868
    1869   740,193 − 696,177 = 44,016 = Hams 1869
    1870   567,164 − 536,844 = 30,320 = Hams 1870
```

and at the far end, from the 1896 volume onward, `Bacon` + `Hams` reproduces the
last four combined figures exactly (1892: 3,881,378 + 1,253,132 = 5,134,510;
same for 1893, 1894, 1895).

## What was wrong

`sig_of` builds a commodity signature by unioning the group and article tokens.
An article that only repeats a word already in its group heading therefore
contributes **nothing**: `BACON AND HAMS | Bacon` and `BACON AND HAMS | Hams`
both key on `('BACON','HAMS')`. The two tables merged — and because cells are
deduplicated on `(country, unit, year)`, and the bacon and ham tables list the
same origins in the same years, **the ham cell was discarded every time**.

Twenty-three years of ham origin tables were being destroyed. 1874 is the plain
case: five bacon rows and five ham rows for the same five countries, and only
the bacon five survived. 1890 shows the messier version, where the ham table had
lost its unit header, so its two countries that bacon happens not to list —
Spain 171 and Russia 46 — slipped through and the shipped "bacon" table was a
mixture of eight bacon cells and two ham cells.

The survivor was then measured against the **combined** national total, so
`Bacon And Hams — Bacon` read 0.75–0.93 of its anchor for its entire life. It
carried no quality flag. A commodity that has been a fifth short for
twenty-four consecutive years looked well measured, because the missing fifth
was hams and nothing in the pipeline knew hams existed.

## The fix, and why it is narrow

Token absorption is deliberate and correct almost everywhere — it is what makes
`Sawn, Fir` and `Sawn : Fir` one commodity. **104 signatures currently carry
more than one printed article for exactly that reason**, and separating them
would shatter the corpus.

The discriminator is that two articles under one signature are the same printed
line spelled two ways iff their vocabularies **overlap** (`Sheep or Lambs'` vs
`Sheep or Lambs' Wool`, `Ore` vs `Ore of`, `Pig and Sheet` vs `Pig or Sheet`).
They are different lines iff their meaningful vocabularies are **disjoint** and
the volumes print both **in the same year**. Run over the whole corpus that
rule fires on `BACON AND HAMS` and on nothing else — the next-closest case has
disjoint vocabularies but zero shared years.

`build_viz_payload` now computes that set up front and keeps the article
load-bearing for those signatures only. It is a general rule that currently has
one member; it will catch the same shape after any re-parse.

## Where the family stands

| commodity | origins | anchor | closure |
|---|---|---|---|
| `Bacon` | 1872–1899 | 1892–1900 | 1892 to 30 cwt; 1895/96/98/99 within 0.5% |
| `Hams` | **1872–1899** *(was 1882, 1893–99)* | 1866–70, 1892–1900 | 1892 exact; 1894/95 to 0.02% |
| `Bacon And Hams` | *(none — the parent line)* | 1866–1895 | the identity above |

`Bacon And Hams — Bacon` was folded into `Bacon`, scoped to 1872–1892. The
overlap years are deliberately not taken; see the first open item.

Both `Bacon` and `Hams` now ship with no quality flag; both were `gapyears`
before.

## Still open, with the evidence

**`Bacon` 1893, 1894 and 1897 count a country beside its own sub-entry.** They
read 1.55, 1.24 and 1.23 of their anchors. In each, a bare `united states of
america` cell sits next to `United States of America : On the Atlantic`, and it
is the **sub-entry** that is right: 1893's Atlantic figure 2,177,293 is the
`BACON AND HAMS | Bacon` table's own US reading to the digit. Substituting it
brings 1893 to 3,195,663 against a 3,198,887 anchor and 1897 to 5,041,672
against 5,004,915. 1897 additionally carries `russia` 27,713 and `northern
parts` 27,713 — the same printed row read twice. This is why the fold is scoped
to 1892: merging into these years would have decided the dispute by fold order.

**The ham identity misses in six years, and each miss is locatable.** 1882 has
no ham table under the group at all — its table is the un-grouped one, which is
why `Hams` carried a 1882 entry all along — leaving the identity at 0.8101.
1885's ham table reads 1,588,854 against a residual of 787,963, roughly double,
so a glued or duplicated block. 1891 is short by 83,683, 1883 by 30,000 exactly
(the digit class), 1874 by 2,990 and 1880 by 3,000.

**`Bacon And Hams` carries the wrong figure for 1866 and 1867.** Those two years
have no combined printing anywhere, so the only reading available is
`tn_1871`'s bacon-only line (578,272 and 493,627), which now sits on the parent
commodity as though it were the combined total. 1868–70 are unaffected: the
combined and bacon-only readings collide on the same key and the combined one
wins. Fixing this needs a way to re-home a T1 cell, which the curation
vocabulary does not have.

**`Hams` 1898 reads 0.8479** (1,672,294 against 1,972,299) — a 300,005 shortfall
in a series that closes in every neighbouring year.

---

# The 1893/94/97 over-count was a lost TOTAL label (2026-07-26)

The first "still open" item above read the 1.55/1.24/1.23 over-counts as a
country counted beside its own sub-entry, and proposed substituting the
`: On the Atlantic` figure. The substitution arithmetic was right and the
diagnosis was wrong, which matters because the two call for different repairs.

## What the row actually is

`as_1897` prints bacon as a five-year comparative table — one printed row per
country, five year-columns — and the parser emits one observation per
(row, year), so a single printed row occupies five consecutive `row_seq`
values. Seq **982–986** is one such row, and it is the **foreign-countries
TOTAL**, carrying the `United States of America` label of the rows above it:

```
972-976  United States of America : On the Atlantic     2,177,293 … 3,592,635
977-981  United States of America : Other Foreign Coun.     2,495 …       404
982-986  United States of America                       3,935,097 … 4,713,979  <- TOTAL
987-991  Canada                                           193,772 …   299,282
997-1001 TOTAL  (British)                                 193,790 …   299,926
1002-06  TOTAL  (grand)                                 3,198,887 … 5,063,915
```

`United States of America : Other Foreign Countries` is the same mis-nesting
one row earlier: a top-level row swallowed as a US sub-entry.

Four independent proofs, no page image needed:

1. **The row plus the British total is the printed grand total.**
   1895: `3,792,945 + 270,473 = 4,063,418`.
   1896: `4,092,512 + 457,014 = 4,549,526`. Both exact.
2. **The other engine labels the identical numbers `TOTAL`.** `country_obs_inf`
   carries 3,792,945 (as_1895, as_1899), 4,092,512 (as_1896, as_1898, as_1899)
   and 4,713,979 (as_1898, as_1899) — every one of them as `TOTAL`.
3. **1893's value column gives it away.** as_1897's row reads
   `3,935,097 / 7,984,601`; `as_1893`'s own foreign TOTAL row reads
   `3,005,097 / 7,984,601`. The value matches to all seven digits, so the
   quantity is a misread of 3,005,097 — and `3,005,097 + 193,790 = 3,198,887`,
   the anchor.
4. **`as_1898`'s 1897 block closes at all three levels.**
   `27,713 + 48,879 + 1,026,552 + 17,751 + 3,592,635 + 449 = 4,713,979` foreign;
   `290,283 + 565 + 88 = 290,936` British; sum `5,004,915` = the anchor.

**Why it survived.** `BACON` with no article is a 1896+-era label, and for 1893,
1894 and 1897 `as_1897` was its *only* witness. The vote had nothing to compare
against, so a printed total entered `country_year_final` as an origin.

## The repair, and a mechanism worth knowing

Two rows were needed, because they fix different things:

- `group_repairs.csv`: `as_1897 / BACON / seq 982-986 / new_country=TOTAL`.
- `manual_rows.csv` `replace=1` for the three US cells: 1893 = 2,177,293,
  1894 = 2,561,203, 1897 = 3,592,635.

The mechanism, which cost a cycle to learn: **a `new_country` group repair does
not remove a consensus cell.** `repaired_rows` is consulted only by step 4 to
stop the sub-entry path re-adding a relabelled row; the `consensus` source comes
from `vote_country_years`, which ran before `integrate_sources` ever read the
manifest. `supersede_years` would reach it but is keyed
`(group, article, year)` — superseding `BACON|''` for these years drops Denmark,
Sweden, Canada and the rest of the table with it. The only country-scoped
instrument is `manual_rows`.

1893 is quotable as a two-column proof: with Germany at 9,744 the block closes
on **both** columns —
`16,823+62,339+711,854+9,744+24,639+2,177,293+2,405 = 3,005,097` and
`43,947+163,693+2,148,138+29,890+69,599+5,523,447+5,887 = 7,984,601` — so the
same arithmetic that identifies the TOTAL row also pins Germany 1893 at 9,744
(as_1893 read 5,744, as_1897 read 9,742).

1894 and 1897 ship with **no value**: the three volumes read 5,082,951 /
5,032,951 / 5,632,951 and 5,253,624 / 5,353,624 / 5,553,624, and no combination
closes the printed foreign-total value without choosing among the other rows
first. A blank is honest; the figure it replaced was the total's value.

## Result

| year | before | after |
|---|---|---|
| 1893 | 1.5485 | **0.9990** |
| 1894 | 1.2392 | **1.0025** |
| 1897 | 1.2314 | **1.0073** |

Every Bacon year 1892–99 now closes within 0.75%. Corpus baseline 38.2% → 38.3%
of GBP within 0.1%, 55.2% → 55.8% within 5% (same 9,935-commodity-year universe);
under-counted commodity-years unchanged at 245.

## Still open, with the evidence

**The residual in each year is fully accounted for and is a different class —
the vote preferring `as_1897`'s drifted readings over a block that closes.**

- **1897 (+36,757).** `Russia` 27,713 and `Northern Parts` 27,713 are the same
  printed row counted twice (+27,713), and Canada reads 299,282 where the
  printed British total 290,936 requires **290,283** (+8,999). 27,713 + 8,999 +
  45 (Germany, which as_1898 folds into Other Foreign) = 36,757 exactly.
- **1894 (+9,279).** The same duplicated Russia row, as `Russia` 9,992 beside
  `Northern Parts` 9,902.
- **1893 (−3,224).** Every country where the vote took as_1897 over as_1893:
  Sweden −19, Denmark −303, Germany −2, Holland −2,989, Other Foreign +90,
  Canada −1. as_1893's block closes on both columns; as_1897's does not.

**`Northern Parts` is an OCR misread of `Northern Ports`.** `fold_country`'s
port-split regex matches `ports?` only, so the Russian northern-ports row
survives as a phantom country named `Northern Parts` and double-counts against
the volumes that spell it `Russia`. Widening the pattern would fix 1894 and
1897 here; **blast radius not measured — do not apply blind.**

**`Hams` 1898 still reads 0.8479** (1,672,294 against 1,972,299), untouched by
this work.

---

# `Hams` 1898 closes: the vote preferred a lone reprint over two agreeing engines (2026-07-26)

The last open item on this family read 0.8479 — 1,672,294 against an anchor of
1,972,299, short by **300,005**. It is now 1.0000.

## Where the 1898 table lives

Under stale heads in both engines, which is why it was never obvious:

```
country_obs_inf  as_1898 seq 9082-9133   GUM | HAMS
country_obs      as_1898 seq 9364        GLASS | Australia
```

and reprinted by `as_1899` in both. The payload's own copy sits under a headless
`HAMS` group — the same promoted-article shape as the cow tables.

## The proof

Four independent readings of the United States cell exist, and the two from the
contemporary volume agree:

```
as_1898  country_obs      1,851,520
as_1898  country_obs_inf  1,851,520
as_1899  country_obs_inf  1,591,520
as_1899  country_obs      1,551,520   <- what the vote took
```

All four agree the value is 3,651,414. The vote took the lone outlier, and the
same happened at Denmark (908 in both as_1898 engines, 903 in as_1899).

Each volume closes one half of the block and corrupts the other, so together
they pin it exactly:

```
as_1898 foreign   908 + 1,125 + 420 + 204 + 1,851,520 + 690 = 1,854,867   = its printed foreign TOTAL
as_1899 British   117,428 + 4                               =   117,432   = its printed British TOTAL
                  1,854,867 + 117,432                       = 1,972,299   = the anchor
```

Restoring the two cells closes the year to the digit:
`1,851,520 + 117,428 + 1,125 + 908 + 690 + 420 + 204 + 4 = 1,972,299`. The
300,000 and the 5 are exactly the two disputed cells.

## Where the family stands now

| year | 1892 | 1893 | 1894 | 1895 | 1896 | 1897 | 1898 | 1899 |
|---|---|---|---|---|---|---|---|---|
| `Hams` | 1.0000 | 1.0097 | 1.0002 | 1.0002 | 1.0000 | 1.0018 | **1.0000** | 0.9999 |

Only 1893 remains over 0.1%. Both `Bacon` and `Hams` close within 0.75% in every
year they are printed.

**The class worth naming**: a cross-volume vote that treats every printing as an
equal witness will prefer a single late reprint over two contemporary engines
that agree. Bacon 1893/94/97 was the same shape (a lone as_1897 reading winning
a tie) and so was copper 1888 (a lone as_1891 reading winning a tie). Three
defects in one session with one cause. **A vote that weighted the contemporary
volume, or simply broke ties toward engine agreement, would have caught all
three.** That is a reconcile-level change and is not made here.

---

# Round 31 — `Northern Parts` was Russia all along

## The defect

`country_year_final` carried a country called **`northern parts`** on `BACON`
for 1893-97, beside a `russia` cell in 1894-97 whose figures were the same
line. The map summed both, so Russian bacon was counted twice in four years,
and 1893's Russia origin was invisible because it was wearing the wrong name.

## What the page says

`as_1897`'s printed import table (the 1893-97 comparative block) reads:

```
BACON :
From Russia :        Cwts. Cwts. Cwts. Cwts. Cwts.   £  £  £  £  £
  Northern Parts     16,823  9,902  12,054  19,001  27,713 | 43,947 21,536 23,924 35,421 59,953
  " Sweden           62,320 72,541  96,385  76,317  48,579 | ...
```

The parent row `From Russia :` carries the **unit labels**, not blanks, so the
parser's colon-parent rule did not fire and the sub-entry lost its parent.
`Northern Parts` is an OCR misread of `Northern Ports`, and because Russia's
only sub-entry in this table is that one line, **the Northern Ports figure IS
Russia's whole bacon line** — which is exactly why `as_1898` and `as_1899`
print the same numbers under a plain `From Russia`.

## Three independent proofs that it is Russia

1. **Position.** In `as_1897` the row is the FIRST foreign country of the block
   (seq 947-951), the slot `as_1898` (seq 939-942) and `as_1899` (seq 920-922)
   give to `Russia`; `as_1897` has no Russia row anywhere in that block.
2. **Digits.** 1896 `19,001 / 35,421` and 1897 `27,713 / 59,953` are identical
   to `as_1898`'s and `as_1899`'s Russia cells to the digit.
3. **Closure.** `as_1897`'s own printed *Total from Foreign Countries* closes
   EXACTLY with the row counted as one of the seven foreign origins:
   - 1896: `19,001 + 76,317 + 1,222,114 + 512 + 22,651 + 2,751,518 + 399
     = 4,092,512` = printed total. (`as_1896` closes the same year on its own
     six-country list to the same total, with Russia 19,001.)
   - 1897: the same sum is 300 short only because `as_1897` misreads Sweden as
     `48,579`; `as_1898` prints `48,879`, and `4,713,979` is then exact.
   - 1895: `as_1898`'s country values with **Russia = 13,954** sum to
     `3,792,945`, which is `as_1897`'s printed foreign total to the digit —
     so `as_1897`'s `12,054` is the misread, not `as_1898`'s figure.

## The fix

`fold_country` in `scripts/build_viz_payload.py` — the port-split regex now
accepts `parts?` as well as `ports?`. `Northern Parts` folds to
`Russia (Northern Ports)`, and every downstream consumer already treats a
parenthesised cell as drill-down detail inside its parent (`reconcile_baseline`
and the map both exclude `(` cells from the origin sum), so:

- 1894-97: the duplicate stops being summed — Russia's parent cell stands alone;
- 1893: no parent Russia cell exists, so the coastal roll-up **synthesises** one
  at 16,823 and the Russia series runs unbroken 1891-99.

No vote, taxonomy or database change. The string occurs in **exactly 5 cells
corpus-wide** (`country_obs`, `country_rescored`, `country_consensus` and
`country_year_final` all agree: BACON, `as_1897`, 1893-97; there is no
`Southern Parts` anywhere), and a full before/after diff of every
commodity-year ratio in the payload changed **4 cells, all Bacon**:

| year | before | after |
|---|---|---|
| 1894 | 1.0025 | **0.9998** |
| 1895 | 1.0030 | **1.0001** |
| 1896 | 1.0043 | **1.0002** |
| 1897 | 1.0073 | 1.0018 |

Baseline: GBP within 0.1% **38.3% -> 39.0%**; `exact01` 2,244 -> 2,247.

## What it left behind, with evidence

- **`Bacon` 1897 residual is Canada.** After the fold the year is over by
  **9,044** cwt. `as_1897` prints Canada 1897 as `299,282`; `as_1898` prints
  `290,283` — a difference of **8,999**. `as_1898`'s British half closes
  exactly (`290,283 + 565 + 88 = 290,936` = its printed British total) while
  `as_1897`'s does not (`299,282 + 653 = 299,935` against a printed `299,926`).
  Note also that `as_1897`'s British-possessions total for 1897 is `299,926`
  where `as_1898` prints `290,936`: the same `0 -> 9` corruption runs down that
  whole column in `as_1897`. This confirms the already-queued repair
  **Canada 1897 = 290,283**, and predicts it closes 1897 to `1.0000` (residual
  45 cwt).
- **`Bacon` 1893 stays 0.9990**, short 3,224 cwt, untouched by this fix.
- **`Bacon` 1898 stays 0.9947.**
- The first `BACON` block in `as_1897`/`as_1898`/`as_1899` (`To Russia :
  Northern Ports`, small figures) is the **export** table; it is out of scope
  here but it is riding in the import payload's group.
- Country-column garbage seen in passing: `Animals, Living` carries an origin
  called `Clocks And Parts Thereof` (1899, 572,576). Known class, not this item.
