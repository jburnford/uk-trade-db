# Second witness (StatCan CS4-4) — parse diagnostics

`scripts/ca_parse_witness.py` → `db/canada/imports_general_rows_w2.csv` (185675 rows)

| FY | witness volume | tables | rows | national efc ratio | abstract efc ratio | abstract cells exact |
|---|---|---|---|---|---|---|
| 1880 | statcan_plato_may_1880 | 459 | 15335 | 0.997 | 0.980 | 74/188 |
| 1881 | statcan_plato_may_1881 | 485 | 15995 | 0.998 | 0.987 | 98/187 |
| 1882 | statcan_plato_may_1882 | 521 | 17659 | 1.121 | 1.113 | 114/226 |
| 1883 | statcan_plato_may_1883 | 523 | 17829 | 0.996 | 0.988 | 111/218 |
| 1884 | statcan_plato_may_1884 | 525 | 17673 | 0.988 | 0.984 | 146/228 |
| 1885 | statcan_plato_may_1885 | 530 | 17720 | 0.991 | 0.990 | 167/239 |
| 1886 | statcan_plato_may_1886 | 552 | 17411 | 1.017 | 1.014 | 136/231 |
| 1887 | statcan_plato_may_1887 | 547 | 15816 | 1.001 | 0.995 | 141/236 |
| 1888 | statcan_plato_may_1888 | 571 | 16526 | 0.998 | 0.995 | 122/237 |
| 1889 | statcan_plato_may_1889 | 558 | 16783 | 1.021 | 1.014 | 138/253 |
| 1890 | statcan_plato_may_1890 | 578 | 16928 | 1.031 | 1.022 | 169/261 |

Diagnostics: fused_article_country_nodash 4342, short_article_heading 3660, blank_row_skipped 1834, article_fragment 1164, label_in_province_slot 936, country_label_lost 885, value_in_qty_slot 848, short_country_label 737, unfused_rows 644, grand_total_rejoined 497, short_row 456, article_heading_lost 339, label_slip_repaired 299, lost_label_resolved_detail 246, page_top_total_fusion 196, qty_cells_dropped 189, duty_cell_dropped 179, lost_heading_closed_with_next 162, short_total_label 154, country_label_in_province_slot 134, article_heading_lost_after_total 132, adjacent_blocks_merged 131, duty_cell_dropped_dutiable 122, heading_deferred_past_data_row 119, pagebreak_hijacker_restored 111, province_unrecognised 109, value_column_lost_block 98, lost_label_after_total 95, duty_cell_split_rejoined 95, lost_label_block 92, duty_cents_only 83, country_noprov_is_first_province 75, total_tail_rejoined 58, fused_article_country 53, article_closed_with_prev 52, fused_qty_value_split 50, nil_province_row 41, grand_total_after_single_row 40, short_heading_with_country 35, country_inferred_Great 34
