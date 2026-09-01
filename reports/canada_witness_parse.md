# Second witness (StatCan CS4-4) — parse diagnostics

`scripts/ca_parse_witness.py` → `db/canada/imports_general_rows_w2.csv` (77503 rows)

| FY | witness volume | tables | rows | national efc ratio | abstract efc ratio | abstract cells exact |
|---|---|---|---|---|---|---|
| 1868 | statcan_plato_may_1868 | 87 | 1806 | 0.797 |  | 0/0 |
| 1869 | statcan_plato_may_1869 | 181 | 3312 | 0.911 |  | 0/0 |
| 1870 | statcan_plato_may_1870 | 196 | 3598 | 1.080 |  | 0/0 |
| 1871 | statcan_plato_may_1871 | 223 | 3871 | 0.949 |  | 0/0 |
| 1872 | statcan_plato_may_1872 | 240 | 4299 | 0.913 |  | 0/0 |
| 1873 | statcan_plato_may_1873 | 255 | 4503 | 0.933 |  | 0/0 |
| 1874 | statcan_plato_may_1874 | 366 | 7070 | 0.938 |  | 0/0 |
| 1875 | statcan_plato_may_1875 | 394 | 7489 | 0.919 |  | 0/0 |
| 1876 | statcan_plato_may_1876 | 289 | 7867 | 0.894 |  | 0/0 |
| 1877 | statcan_plato_may_1877 | 402 | 10698 | 1.030 |  | 0/0 |
| 1878 | statcan_plato_may_1878 | 411 | 10951 | 0.981 |  | 0/0 |
| 1879 | statcan_plato_may_1879 | 458 | 12039 | 1.160 |  | 0/0 |

Diagnostics: short_row 2529, junk_country_label 651, fused_cells 531, scrambled_row 250, unfused_rows 160, regime_flip_ignored 132, adjacent_blocks_merged 57, fused_rows_expanded 41, article_heading_lost 24, junk_country_swapped 21
