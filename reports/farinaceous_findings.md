# Farinaceous 1882: the table found and relabelled, and why the metric still cannot see it

Worked 2026-07-31 (`/loop /next-defect`).
**exact01 unchanged at 3,531 / 9,515, zero regressions.** A correct repair that
lands in the database and not in the payload, plus the mechanism that explains
it — established by trying the obvious fix and measuring the damage.

## The table

Bracketed-gap rank 7, £1.51M. `Farinaceous Substances And Manufactures
Thereof` closes at 1.00 in every year 1878-1888 except **1879 and 1882**.

The 1882 origin table is glued under an **`EXTRACTS, of other Sorts than
Dye-Stuffs, Unenumerated`** head, immediately after the real (and much smaller)
extracts table — two tables run together under one label, seq 614-617 then
618-626.

The proof is the block's own printed TOTAL: **752,945 = the Tier-1 for 1882 to
the digit**. Its eight named members are a plausible farinaceous origin list —
Holland 320,088, British West India Islands 207,020, France 72,372, Austria
42,101, Other Countries 29,887, Italy 24,066, Straits Settlements 19,605,
United States 11,725 — summing **726,864**, exactly **26,081** short.

### The two engines split the last row between them

**Infinity's copy reads 26,081 in the row where Chandra reads 752,945.**

`726,864 + 26,081 = 752,945`. One engine kept the block's last **member**, the
other kept its **total**, and each lost what the other has. The member's country
label is lost in both, so the year is admitted at **0.965** rather than closed —
but the arithmetic identifying the table is complete.

## The repair is admitted and still invisible

```
as_1882 EXTRACTS…  seq 618-626   selected 9   admitted 8   drop_subtotal 1
target_sig: farinaceou+manufacture+substance+thereof
```

All eight rows are now in `country_year_final` under
`FARINACEOUS SUBSTANCES AND MANUFACTURES THEREOF, UNENUMERATED`, unit `Value`,
`source = groupfix`. **And the payload does not change at all.**

### Why: the two stages key the commodity differently

The printed group in `as_1883` — the year that *does* close — is
`FARINACEOUS SUBSTANCES and Manufact- tures thereof, Unenumerated`, with a
hyphen-space in the middle of *Manufactures*.

- **`integrate_sources`** matches by `V.sig`, and that mangled string signs as
  `farinaceou+manufact+substance+thereof+**ture**` — two tokens where there
  should be one. A repair aimed at the mangled spelling therefore fails the
  signature test.
- **`build_viz_payload`** keys the node on the group **string**, and folds the
  hyphen, so the mangled spelling is what produces
  `Farinaceous Substances And Manufactures Thereof`.

So the clean spelling satisfies the first stage and creates a *new, anchorless*
node in the second; the mangled spelling satisfies the second and is rejected
by the first. **A repair can be admitted, correct, and invisible.**

### `group_aliases` does not bridge it — tested, and it costs six years

The obvious fix is a group alias mapping the mangled spelling to the clean one.
Applied, it produced **six true regressions**:

```
Farinaceous… 1881  ('exact01', 732225) -> ('nodata', 0, 732225)
Farinaceous… 1883  ('exact01', 785998) -> ('nodata', 0, 785998)
Farinaceous… 1888  ('exact01', 1017344) -> ('nodata', 0, 1017344)
…and 1880, 1889, 1890
```

**The alias relabels country rows but not the `§TOTAL`.** Renaming the group
moved every country cell to the clean name while the anchor stayed on the
mangled one, splitting a working commodity into an anchorless node and a
countryless one. Backed out; exact01 restored to 3,531.

## What was kept, and what is queued

The `group_repairs` row **stays**, with the clean spelling. The eight origins
are now correctly filed against farinaceous instead of extracts — a real
correction to the database that the metric happens not to score, in the same
class as the invisible corrections of iterations 12-13.

Queued: unifying the two spellings needs the alias to move the anchor too, or
`build_viz_payload` to key on the signature rather than the string. Both are
code changes and neither was attempted. `Farinaceous` **1879** is a second hole
in the same commodity and was not examined.
