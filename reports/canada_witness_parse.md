# Second witness (StatCan CS4-4) — parse diagnostics

`scripts/ca_parse_witness.py` → `db/canada/imports_general_rows_w2.csv` (263178 rows)

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
| 1880 | statcan_plato_may_1880 | 459 | 15335 | 0.997 | 0.980 | 74/188 |
| 1881 | statcan_plato_may_1881 | 485 | 15995 | 0.998 | 0.987 | 98/187 |
| 1882 | statcan_plato_may_1882 | 521 | 17659 | 1.121 | 1.113 | 114/226 |
| 1883 | statcan_plato_may_1883 | 523 | 17829 | 0.996 | 0.988 | 111/218 |
| 1884 | statcan_plato_may_1884 | 525 | 17673 | 0.988 | 0.984 | 146/228 |
| 1885 | statcan_plato_may_1885 | 530 | 17720 | 0.991 | 0.990 | 167/239 |
| 1886 | statcan_plato_may_1886 | 552 | 17411 | 1.017 | 1.014 | 136/231 |
| 1887 | statcan_plato_may_1887 | 547 | 15816 | 1.001 | 0.995 | 141/236 |
| 1888 | statcan_plato_may_1888 | 571 | 16526 | 0.998 | 0.995 | 122/237 |
| 1889 | statcan_plato_may_1889 | 558 | 16783 | 1.021 | 1.016 | 143/253 |
| 1890 | statcan_plato_may_1890 | 578 | 16928 | 1.031 | 1.030 | 178/261 |

Diagnostics: fused_article_country_nodash 4342, short_article_heading 3660, short_row 2985, blank_row_skipped 1834, article_fragment 1164, label_in_province_slot 936, country_label_lost 885, value_in_qty_slot 848, unfused_rows 804, short_country_label 737, junk_country_label 657, fused_cells 531, grand_total_rejoined 497, article_heading_lost 363, label_slip_repaired 299, scrambled_row 250, lost_label_resolved_detail 246, page_top_total_fusion 196, qty_cells_dropped 189, adjacent_blocks_merged 188, duty_cell_dropped 179, lost_heading_closed_with_next 162, short_total_label 154, regime_flip_ignored 136, country_label_in_province_slot 134, article_heading_lost_after_total 132, duty_cell_dropped_dutiable 122, heading_deferred_past_data_row 119, pagebreak_hijacker_restored 111, province_unrecognised 109, value_column_lost_block 98, lost_label_after_total 95, duty_cell_split_rejoined 95, lost_label_block 92, duty_cents_only 83, country_noprov_is_first_province 75, total_tail_rejoined 58, fused_article_country 53, article_closed_with_prev 52, fused_qty_value_split 50
