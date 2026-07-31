# Silver ore: the 1879 table found and proved, and the one line of code that refuses it

Worked 2026-07-31 (`/loop /next-defect`). **Nothing landed. Baseline unchanged
at exact01 3,486.** This is a proof plus a blocked mechanism, pinned to a
single line — and the block is not specific to silver ore.

## The commodity

`Silver, Ore Of, Or Ore Of Which The Greater Part In Value Is Silver` closes
in **20 of its 22 anchored years**, most of them to the digit. Only two break
it, and both were on the bracketed-gap ranking: **1894 at 0.31 (£3.09M, rank
3)** and **1879 at 0.00 (£1.32M, rank 13)**.

## 1879 — found, and proved

The entire 1879 origin table is glued under a stale **`SILK MANUFACTURES`**
head, with the commodity name absorbed as the ARTICLE and OCR-garbled in
Chandra: `SILVER ORE, or ONE of which the greater part in value is Silver` —
**ONE for ORE**, the same garble already on record for iron. Infinity carries
the same block un-garbled at seq 1209-1218 with identical figures.

The block's own printed TOTAL is **724,515 = the Tier-1 anchor to the digit**.
Its nine named members are exactly what an 1879 silver-ore table should name:

| Spain | Greece | USA | Mexico | New Granada | Peru | Bolivia | Chili | Other |
|---|---|---|---|---|---|---|---|---|
| 417,247 | 23,089 | 33,210 | 38,261 | 48,667 | 41,448 | 1,038 | 91,220 | 21,035 |

They sum to **715,215 — 9,300 short of the printed total, in BOTH engines**.
So one member row is lost from both parses and the year would land at
**0.9872**, not exact. An honest partial recovery of £724K of origin data
under nine named countries, replacing a year with no origins at all.

## The blocker, and it is one line

The repair matches the block perfectly and admits **nothing**:

```
SILK MANUFACTURES  1498-1507  ch   selected: 10  admitted: 0  drop_null_qty: 10
SILK MANUFACTURES  1209-1218  inf  selected: 10  admitted: 0  drop_null_qty: 10
```

`scripts/integrate_sources.py`, step 6:

```python
fixed_rows = [r for r in fixed_rows
              if r[3] is not None and r[3] > 0]      # r[3] is the QUANTITY
```

**Every row with no quantity is discarded, however good its value.** The
printed silver-ore table for 1879 has no quantity column at all — it is a
value-only commodity — so all ten rows go.

This is the same branch flagged back in iteration 8 and carried unanswered in
every `LOOP_STATE.md` since. Corpus-wide it now costs:

- **23 group repairs lose cells to it, 234 cells in total**
- **5 repairs admit nothing whatsoever because of it** — `as_1879 SILK
  MANUFACTURES` ×2 (this one, both engines) and `as_1897`/`as_1898 CHINA, OR
  PORCELAIN, AND EARTHENWARE` ×3

So three separate families are held up by one predicate, plus the clocks
1893-97 and COTTON MANUFACTURES — Unenumerated blocks recorded earlier.

**The two repair rows have been committed and left in place.** They are inert
(`admitted: 0`) and cost nothing, and they will activate the moment the guard
learns to keep a value-only row. The proof should not have to be re-derived.

## 1894 — diagnosed, deliberately not attempted

`as_1894`'s own silver-ore block (seq 1880-1886) is only the European
section — Germany 67,988, Holland 7,460, Belgium 239,427, France 19,142,
Italy 30,022, Other Foreign 1,338, **TOTAL 365,377, which its members close to
the digit**. Against a Tier-1 of 2,439,955 the American section — Mexico,
Bolivia, Chile, Peru, the countries silver ore actually comes from — is
elsewhere and was not found by a printed-total hunt.

Worse, the year is **polluted from several sources**. The payload node's 1894
cells run in three units (`Value`, `Number`, `?`) and the `Value` cells that
make up the measured 746,264 — Mexico 204,174, Peru 120,179, Spain 215,138,
Greece 76,040, Colombia 99,918 — **are not the figures in `as_1894`'s own
block**. Some other volume's silver-ore table is being read into 1894, while
`as_1894`'s is partly absent. Alongside it sit four sibling nodes that are
stale-head chimeras (`— Skins, Sheep, Undressed`, `— Skins, Unenumerated,
Undressed`, `— Specimens Illustrative Of Natural Science`) and one
phantom-region-article node (`— Dutch Possessions In The Indian Seas`).

Untangling which volume each 1894 cell came from is a real piece of work and
**not something to guess at inside one iteration**. Queued with the above as
the starting evidence. Note that 1884 also reads **1.1009**, an overcount in
the same commodity, and is probably the same pollution seen from the other
side.

---

## Resolved the same session — the guard was changed, with permission

The user approved changing the predicate. Two edits to
`scripts/integrate_sources.py` step 6:

```python
fixed_rows = [r for r in fixed_rows
              if (r[3] is not None and r[3] > 0)
              or (r[4] is not None and r[4] > 0)]
```

and, at row construction, a value-only branch that mirrors **exactly** what
step 1 has done all along — the GBP figure in the quantity slot under the
literal unit `'Value'`, so it reconciles against the Value anchor and can
never be mistaken for a quantity. `strip_values` cannot apply on that path:
the value is the only figure there is. The previous code would have crashed on
`float(q)` with a null quantity, which is presumably why the guard was written
that way in the first place.

### Effect, measured

| | before | after |
|---|---|---|
| cells lost to `drop_null_qty` | 234 | **14** |
| repairs admitting nothing because of it | 5 | **0** |
| `as_1879 SILK MANUFACTURES` (ch) | sel 10, adm 0 | **sel 10, adm 9** |
| `as_1879 SILK MANUFACTURES` (inf) | sel 10, adm 0 | sel 10, adm 0 — correctly deduped as `already_added` |
| `as_1897/98 CHINA, OR PORCELAIN` | 0 admitted | 24, 10, 10, 22, 10, 14 |

**exact01 3,486 unchanged, within5 1,081 → 1,082, nodata 4,441 → 4,440.**

**Exactly one commodity-year changed in the whole corpus:**

```
Silver, Ore Of…  1879   ('nodata', 0, 724515) -> ('within5', 715215, 724515)
```

Zero regressions. That the china/porcelain blocks now admit 90 rows and move
no bucket is worth stating plainly: those rows land in years that were already
measured or that remain `nodata` for other reasons. **The guard was not the
only thing wrong with them** — unblocking it was necessary, not sufficient.

The 9,300 residual in 1879 stands: one member row is missing from both
parses, so the year sits at **0.9872** and not at exact. It is honest
measurement where there was none.
