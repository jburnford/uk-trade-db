# House frames 1892: the fourth flow-misfile in as_1892

Worked 2026-08-01 (`/loop /next-defect`).
**exact01 3,538 → 3,539, denominator unchanged at 9,511, zero regressions.**

```
Wood And Timber — House Frames, Fittings, And Joiners' Work
  1892  ('nodata', 0, 675138) -> ('exact01', 675138, 675138)
```

## The block

Bracketed-gap rank 6, £1.45M, the only hole in a series that closes 1885-1895.
The table is in `as_1892`, parsed under the **export** flow, beneath a mid-page
continuation head `WOOD and TIMBER'd)`.

It closes at **three levels, to the digit**:

| | |
|---|---|
| eleven foreign members | **655,992** = the printed foreign TOTAL |
| four British members | **19,146** = the printed British TOTAL |
| sum | **675,138** = the printed grand TOTAL **and the import Tier-1** |

And the country list settles it without the arithmetic: Russia, Sweden,
Norway, Germany, Holland, Belgium, France, the United States — the Baltic and
North American timber trades, which is where Britain **bought** joinery.

**This is the fourth flow-misfile found in `as_1892`**, after `ZINC'd)`,
`WOOL | Alpaca, Vicuña, and Llama` and `WOOD and TIMBER | Staves`/`Mahogany`.
The volume's standing as a systematic problem is now well past coincidence.

## The trap I nearly walked into

The obvious instrument is `reference/flow_repairs.csv`, which flips a whole
group's flow for a volume-year. It would have been **wrong**.

The mangled `WOOD and TIMBER'd)` head is not a misfiled import section — it is
the genuine **export** section, whose heading happens to be OCR-damaged. Under
that same head, at seq 2825-2833, sits a **real re-export table**: France, the
United States, then British South Africa and Australasia as destinations,
totalling 46,149. A group-level flow flip would have dragged that into the
import side.

Only seq **57-74** is an import table. So the repair is a `group_repairs` row
matched on `flow='export_uk'` with an explicit seq range — the same instrument
used for the three earlier misfiles in this volume, and for the same reason.

**A mangled group head is not evidence of a misfile.** Here the mangling and
the misfile are independent: the head is damaged *and* the section under it is
mostly correct, with one block inside it that is not.

## Note on the sibling

`House Frames, Fittings, and Joiners' Work` at seq 2825-2833 (`reexport`,
46,149) is left exactly where it is. It is the same commodity, correctly filed
on the export side, and nothing here suggests otherwise.
