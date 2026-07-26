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
