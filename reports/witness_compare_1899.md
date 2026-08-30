# Two-witness comparison: statcan_plato_w2_1899  vs  cdn_34_5_1899

| | statcan_plato_w2_1899 | cdn_34_5_1899 |
|---|---:|---:|
| joined rows | 9,856 | 9,483 |

**Rows matched by label-sequence alignment: 5,717** (60% of the smaller witness)

## Do the two scans print the same numbers?

- every comparable cell identical: **4,479** (78.3%)
- some cells agree, some differ: **677** (11.8%)
- all comparable cells differ: **502** (8.8%)
- nothing comparable: **59** (1.0%)

## Does a second witness rescue a damaged row?

A row "closes" when its own printed columns add up (GT + PT == Total).

- both witnesses close: **4,621**
- only statcan_plato_w2_1899 closes (B damaged): **436**
- only cdn_34_5_1899 closes (A damaged): **428**
- neither closes: **184**
- not checkable: 48

**Of 5,669 checkable rows, 864 (15.2%) are damaged in one witness and sound in the other — recoverable only because there are two scans.** Single-witness good rate 89.2% -> two-witness 96.8%.

184 rows are damaged in both and need a third source or a human.

## Sample rescues

| good witness | label | A: GT+PT / Total | B: GT+PT / Total |
|---|---|---|---|
| A | 4 Animals, living, viz.:— Hogs..... > Ontario ..... | 6 / 6 | 6 / 40 |
| A | Horned cattle..... > Newfoundland..... | 10 / 10 | 10 / 2 |
| A | Quebec..... | 74 / 74 | 74 / 15 |
| A | Manitoba..... | 10 / 10 | 10 / 2 |
| A | P. E. Island..... | 10 / 10 | 10 / 2 |
