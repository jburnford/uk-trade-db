# Wool imports — what the tables actually say (2026-07-25)

Wool is the largest commodity in the dataset. It arrived at this audit reading
as *well measured* and was not: its last three years were 90% empty, and five
more sat 15–20% above their own printed national total. Both are now closed,
and the machinery that let them hide has been fixed rather than the symptoms.

## Sheep and lambs' wool: the last three years were missing

`Wool — Sheep Or Lambs'` showed 65–77 million lb for 1897, 1898 and 1899
against a national total of 663–736 million. The colonial clip — Australasia,
New South Wales, New Zealand, the Cape — which is almost the whole trade, was
absent; only the European wool survived.

It was never lost. It sits under the de-headed label **`Wool`**, one of whose
own 1899 origin rows is the article `Sheep Or Lambs` — the head fell off the
printed line and the parser kept the fragment as a commodity of its own.

Folding it in failed the first time, and the reason is worth recording because
it applies to every fold in the project. Cells merge by **(country, unit,
year)**, and a source cell that lost its printed unit sits under `?`. It
therefore never collides with the target's labelled cell for the same country
and year:

* every year both labels covered was added **twice** (New South Wales 1896 is
  163,717,080 lb under either label — the same figure to the digit);
* the years only the source had stayed **invisible to the quantity axis**,
  which counts the dominant unit alone.

Healing the unit **before** the year check fixes both ends at once, and needs
`heal_units`' second idea as well as its first: a span median is the wrong
yardstick for a growing series, so a cell that fails the bucket test is
rescued against its *nearest labelled year*. Australasia's 1897 cell is 1.3×
its own 1896 neighbour and far above the 1872-onward median.

## And five more years were 15–20% over

Where a printed origin table carries both a regional total and the colonies
listed under it, one of the two has to go. The old rule was a share test: keep
the children if they account for 85% of the parent. Two things were wrong.

It measured the share on **value** while the map displays **quantity**, and the
parent's value cells are the unreliable ones — Australasia's wool is £2.0M in
1897 against £21.8M in 1893 for a similar tonnage. And it is second-best
evidence anyway: where the year has a Tier-1 anchor, that anchor was printed on
another page and says what the origins must add up to.

Wool shows why it matters. Its `Australasia` row equals the colonies beneath it
in some years and runs 1.22–1.28× them in others, so the share test flipped its
verdict from year to year — 1888, 1889 and 1896 dropped the parent and closed
at 1.00 while 1890–93, 1895 and 1898 kept it and sat at 1.15–1.20.

One further trap: the groups have to be chosen **together**. Judged one at a
time against a running total that still holds the other groups' duplicates,
wool 1894's Australasia parent looked 4.8M lb from the anchor when the honest
comparison was 75M, and the year closed at 0.88.

**Result — every year the source published:**

```
1872-1899
0.99 0.99 0.98 0.99 0.99 1.00 0.99 0.98 0.98 0.99 1.00 1.00 0.99 1.00
1.00 1.00 1.00 1.00 1.00 0.99 1.00 1.00 1.02 1.00 1.00 0.96 0.97 0.98
```

## Alpaca: one line, the animals in a different order

`Wool — Alpaca, Llama, And Vicuna` (national total 1868–77, origins 1872–80)
and `Wool — Alpaca, Vicuña, And Llama` (1878–1900) are the same printed line
with the three animals reordered and the accent lost between volumes. Folded;
24 of the 26 checkable years sit at 1.00.

## QUEUED: the goats'-hair cluster has anchors from the wrong line

This one is a source-level defect and is **not** patched here, because the
national totals are attached upstream of commodity curation. The evidence is
exact.

The family splits in 1893 into mohair and other goats' hair, and the 1896
figures prove the structure closes:

```
mohair 14,986,979 + other 2,156,233 = 17,143,212 = goats' wool or hair, total
```

But for 1893–95 both sub-sorts carry a national total belonging to something
else:

| label | year | its "national total" | what that figure actually is |
|---|---|---|---|
| `Wool — Other Goats' Wool Or Hair` | 1893 | 672,763,274 | the **sheep and lambs'** total, to the digit |
| | 1895 | 770,955,203 | the sheep total, to the digit |
| | 1894 | 700,550,262 | the sheep total with a leading 7 for 8 (799,559,262) |
| `Wool — Goats' Wool, Mohair` | 1893–95 | 19,647,742 etc. | the goats' **parent** total, to the digit |

So "other goats' wool" is credited with roughly two hundred times its real
trade, and mohair with its parent's. Until those are re-attached the two
sub-sorts cannot be measured, which is why both still ship flagged
`nooverlap`.

`Wool — Goats' Wool Or Hair` itself is sound to 1892 (0.93–1.00) and reads
1.34, 1.36 and 1.46 for 1893–95 — the same three years, and very likely the
same cause: the sub-sort tables leaking into the parent's origin list once the
line was split.

## Also noted

- `Wool — Sheep Or Lambs'` origin tables end in 1899 while the anchor runs to
  1900. That is the source, not a defect: the origin tables stop there.
- `Wool — Other Kinds, And Flocks` sits at 0.92–0.96 throughout, consistently a
  few per cent under its anchor. Small and stable; not chased.
