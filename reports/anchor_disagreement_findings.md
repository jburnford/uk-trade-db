# The anchors the vote got wrong (2026-07-26)

Every closure test in this project measures a country table against its printed
national total, so a wrong anchor is invisible to all of them: the table can be
perfect and still read 0.11, or be missing half its rows and still read 1.000.
`scripts/anchor_disagreement.py` keeps what the cross-volume vote throws away —
every distinct reading of every series-year, with the volumes and engines behind
it — and scores the payload's origin sum against each. When the origins close on
a **losing** candidate, the vote is probably wrong.

Phase 0.4 of the corpus-wide plan was to work that queue. Twenty rows carried the
verdict `ORIGINS-FAVOUR-LOSER`; eight had already been adjudicated into
`reference/manual_t1.csv` in an earlier session, leaving twelve.

Six are now overridden. Six turned out to be one defect wearing six years, and
it is not an anchor problem at all.

## The six overrides

| commodity | year | voted | corrected | origins | why the vote lost |
|---|---|---|---|---|---|
| `Jute` | 1886 | 267,455 | **5,349,109** | 5,349,109 *(exact)* | a unit change, not a digit |
| `Tobacco — Unmanufactured` | 1894 | 57,781,317 | **87,781,317** | 87,967,085 (+0.21%) | 8 read as 5, one volume, tier C |
| `Preserved, Otherwise Than By Salting` | 1889 | 611,705 | **641,705** | 641,675 (−30) | 4 read as 1, 4 printings v 3 |
| `Cured, Sardines` | 1894 | 925,244 | **105,116** | 105,155 (+39) | a foreign body, 5 printings v 1 |
| `Gum — Arabic` | 1872 | 12,837 | **42,837** | 42,917 (+80) | 4 read as 1, one printing each |
| `Paper — Hangings` | 1890 | 9,174 | **9,474** | 9,504 (+30) | 4 read as 1, 4 printings v 1 |

**Jute 1886 is the interesting one, because it is not the digit class at all.**
Seven printings say 267,455 and one says 5,349,109, and
5,349,109 ÷ 267,455 = **20.0000 exactly**. Jute's national line moves from
hundredweights to tons in the as_1887 volume, and the vote merged the two units
into one series: the later volumes are printing the same year in tons under the
column header the parser kept from 1886. The Cwts. series runs 3.4–5.9 million
every year 1872–85 and the 1886 country table sums to 5,349,109 to the digit.

**Sardines 1894 is the largest failure of print-majority in the set.** Five
printings carry 925,244 against a series that runs 125,292 / 175,723 / 197,747 /
239,273 / 217,230 in 1893 and 1896–99 and closes to 1.0000 in four of those five
years. The single dissenting printing, 105,116, lands 39 below the origin sum.

**Gum arabic 1872 is overridden but the year is still a genuine dip** — 42,837
against 76,136 in 1871 and 64,378 in 1873. The override only says the corpus's
one alternative reading beats a sixfold collapse; it does not claim the year is
now understood.

## The six that are not anchor errors: `Yarn` is jute yarn wearing cotton's table

Six of the twelve were `cotton | yarn` — 1874, 1885, 1886, 1887, 1891, 1893 —
and in five of them the origins favoured a consistently *higher* candidate while
in 1874 they favoured a *lower* one. Two coherent series alternating inside one
key is not a vote that keeps slipping; it is two printed lines being voted
against each other.

The country tables name them:

```
                 1874        1885        1886        1887        1891        1893
  COTTON|Yarn  1,521,187   8,362,281   8,125,556   7,841,924   9,435,187   7,381,546
  JUTE  |Yarn  4,528,509   8,085,237   3,948,886   2,556,642   3,021,391   1,550,555
```

Line those up against the two candidate series and every year lands: the
"losing" candidate is the cotton figure in 1885, 1886, 1887, 1891 and 1893, and
in **1874 the roles swap** — the winner 4,528,512 is jute's table to within three
pounds and the loser 1,521,187 is cotton's to the digit. That swap is what a
year-by-year coin toss between two real lines looks like, and it is why 1874 sat
in the report pointing the opposite way from the other five.

The Abstract prints jute yarn as a
**groupless** `Yarn` line — the JUTE heading is lost — and `reconcile.py` keys
its series on the article alone, so `Cotton | Yarn` and the groupless `Yarn`
became one series and the vote has been choosing between cotton and jute year by
year since 1868. The payload commodity called `Yarn` is the result: **cotton
yarn origin tables measured against a jute yarn anchor.** Its ratio history says
so plainly — 1.0000 in 1875–79, 1883, 1888 and 1892 (the years the vote happened
to pick cotton), and 2.06, 3.07, 2.73, 3.14, 4.76 in the years it picked jute.

No override was written. Six `manual_t1` rows would make a mislabelled commodity
arithmetically tidy and hide the thing that is actually wrong. This needs the
series key to distinguish a grouped label from a groupless one, which is a
`reconcile.py` change, not a reference-CSV one.

It is also the **third** instance this session of one class: two printed lines
collapsing onto one commodity key and destroying each other's cells. Bacon and
hams collapsed by token absorption in `sig_of`; oxen collapsed across a stale
group head; cotton and jute yarn collapse in the Tier-1 series key. Where the
two tables list the same origins in the same year — and they do — the
`(country, unit, year)` dedup silently drops one of them.

## Found while checking, not repaired

**`Jute` reads exactly twice its anchor for thirteen consecutive years — in the
payload.** The Tons series 1887–99 runs 1.9922 … 1.9993. *(Resolved the same
day: it is `British East Indies` 337,303 counted beside its own drill-down
`Bengal` 336,728, and the map's parent/child de-duplication already removes it —
`map_slim` closes at 0.9982–1.0000 for those years. The 2.00 is a payload-level
artefact `reconcile_baseline.py` sees and the shipped map does not. Jute's real
defect was the unit change; see `reports/unit_change_findings.md`.)*

**`Cured, Sardines` 1895 carries the same foreign body as 1894** — an anchor of
1,082,588 against origins of 140,187 — and this report cannot see it, because
its readings do not disagree. Every printing carries the wrong figure.

**`Paper — Hangings` 1894–98 is a chimera.** A series that closes to the digit in
fifteen of the nineteen years 1872–93 reports origins of 826,506 in 1894 against
an anchor of 9,060, then 2.3M, 2.7M, 2.8M and 3.2M with no anchor at all, plus a
single Gallon cell of 33–46 million a year.

**`Gum — Arabic` loses half its origin table in 1874, 1876, 1885, 1887 and
1897–99** (ratios 0.48, 0.53, 0.62, 0.57, 0.31, 0.60, 0.59) while closing to
1.0000 in eleven other years.
