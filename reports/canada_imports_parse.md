# Canadian imports General Statement — parse diagnostics

`scripts/ca_parse_imports.py` → `db/canada/imports_general_rows.csv` (208084 rows)

| FY | volume | tables | rows |
|---|---|---|---|
| 1866-67 | oocihm.9_08052_1_1 | 0 | 0 |
| 1868 | oocihm.9_08052_2_1 | 87 | 1701 |
| 1869 | oocihm.9_08052_3_1 | 177 | 2535 |
| 1870 | oocihm.9_08052_4_2 | 198 | 2758 |
| 1871 | oocihm.9_08052_5_3 | 211 | 2421 |
| 1872 | oocihm.9_08052_6_2 | 240 | 3195 |
| 1873 | oocihm.9_08052_7_4 | 251 | 3277 |
| 1874 | oocihm.9_08052_8_3 | 369 | 5619 |
| 1875 | oocihm.9_08052_9_2 | 398 | 6487 |
| 1876 | oocihm.9_08052_10_1 | 288 | 7931 |
| 1877 | oocihm.9_08052_11_4 | 406 | 10830 |
| 1878 | oocihm.9_08052_12_2 | 406 | 10701 |
| 1879 | oocihm.9_08052_13_10 | 0 | 0 |
| 1880 | oocihm.9_08052_14_2 | 459 | 15340 |
| 1881 | oocihm.9_08052_15_1_2 | 485 | 15879 |
| 1882 | oocihm.9_08052_16_2 | 505 | 17162 |
| 1883 | oocihm.9_08052_17_1_2 | 521 | 17713 |
| 1884 | oocihm.9_08052_18_2 | 525 | 17727 |
| 1885 | oocihm.9_08052_19_1_2 | 530 | 17735 |
| 1887 | oocihm.9_08052_21_3 | 547 | 15788 |
| 1888 | oocihm.9_08052_22_1 | 571 | 16546 |
| 1889 | oocihm.9_08052_23_2 | 558 | 16739 |
| 1897 | oocihm.9_08052_32_4 | 0 | 0 |

Diagnostics: scrambled_row 6461, fused_article_country_nodash 3869, short_row 2200, short_article_heading 2147, blank_row_skipped 1339, unfused_rows 1148, fused_cells 929, article_fragment 779, country_label_lost 680, label_in_province_slot 656, short_country_label 594, value_in_qty_slot 466, no_regime_yet 455, grand_total_rejoined 422, label_slip_repaired 334, article_heading_lost 250, fused_rows_expanded 235, adjacent_blocks_merged 225, lost_label_resolved_detail 194, page_top_total_fusion 162, short_total_label 133, regime_flip_ignored 123, qty_cells_dropped 115, lost_heading_closed_with_next 112, heading_deferred_past_data_row 103, fused_qty_value_split 99, lost_label_after_total 81, value_column_lost_block 78, article_heading_lost_after_total 77, duty_cell_dropped 75, fused_efc_duty_split 69, lost_label_block 66, duty_cents_only 58, duty_cell_split_rejoined 56, province_unrecognised 52, fused_article_country 45, total_tail_rejoined 42, lost_label_joined_next_country 42, article_closed_with_prev 41, country_label_in_province_slot 39, value_in_duty_slot 37, nil_province_row 36, phantom_blank_cell_dropped 35, duty_cell_dropped_dutiable 34, heading_fused_into_total 31, value_column_lost 29, grand_total_after_single_row 28, country_inferred_Great 27, short_heading_with_country 24, country_noprov_is_first_province 23, heading_fragment_starts_article 23, province_order_swapped 20, phantom_pair_cells_dropped 20, summary_line 19, split_country_province 18, lost_label_joined_prev_country 17, lost_label_resolved_total 16, article_closed_with_next 15, page_top_heading_new_article 15, heading_fragment_on_data_row 14, noprov_slip_down 13, stray_unit_cells_dropped 12, lost_label_total_structural 12, trailing_label_lost 11, page_top_heading_continuation 11, qty_value_scrambled_block 10, heading_from_fragment_before_country 9, province_order_unarbitrated 8, heading_from_label_row 8, province_dup_relabelled 7, total_block_labels_shifted 7, province_values_on_next_row 7, value_in_duty_slot_duty_row 7, slip_hypothesis_flipped 6, article_resumed 4, label_slip2_repaired 4, province_rows_swapped 3, heading_on_total_row 2, country_inferred_United 2, province_dup_unarbitrated 1, grand_total_on_country_row 1, label_slip_down 1, single_detail_chain 1
Cell flags: fused 3630, unparsed 184

| FY | regime | rows | row kinds |
|---|---|---|---|
| 1868 | A | 1701 | detail 1145, article_total 556 | article closure (details vs total, blocks with 2+ rows) 268 ok / 462 bad
    - Sulphuric val_imp: rows 62436.00 vs printed 24.00
    - Sulphuric val_efc: rows 4408.00 vs printed 543.00
    - Other F. Countries val_imp: rows 90796.00 vs printed 78842.00
    - Other F. Countries val_efc: rows 95966.00 vs printed 52307.00
| 1869 | A | 2535 | detail 1674, article_total 861 | article closure (details vs total, blocks with 2+ rows) 341 ok / 695 bad
    - Horned Cattle duty: rows 280.00 vs printed 300.00
    - Sulphuric val_imp: rows 1763.00 vs printed 1733.00
    - Sulphuric val_efc: rows 1763.00 vs printed 1733.00
    - Sulphuric duty: rows 547.39 vs printed 524.39
| 1870 | A | 2758 | detail 1870, article_total 888 | article closure (details vs total, blocks with 2+ rows) 450 ok / 666 bad
    - Cordials val_imp: rows 526141.00 vs printed 632.00
    - Cordials val_efc: rows 75873.00 vs printed 706.00
    - Cordials duty: rows 7625.25 vs printed 407.46
    - Whiskey val_efc: rows 14828.00 vs printed 60.00
| 1871 | A | 2421 | detail 1499, article_total 922 | article closure (details vs total, blocks with 2+ rows) 334 ok / 541 bad
    - PAYING SPECIFIC DUTY val_imp: rows 13746.00 vs printed 317.00
    - PAYING SPECIFIC DUTY val_efc: rows 14120.00 vs printed 271.00
    - PAYING SPECIFIC DUTY duty: rows 2761.86 vs printed 52.80
    - Benzole, Naphtha, and Refined Petroleum val_imp: rows 767.00 vs printed 924.00
| 1872 | A | 3195 | detail 1975, article_total 1220 | article closure (details vs total, blocks with 2+ rows) 423 ok / 727 bad
    - China val_imp: rows 934655.00 vs printed 872796.00
    - China val_efc: rows 825240.00 vs printed 816219.00
    - China duty: rows 292526.66 vs printed 286780.44
    - China val_efc: rows 145565.00 vs printed 145559.00
| 1873 | A | 3277 | detail 2037, article_total 1240 | article closure (details vs total, blocks with 2+ rows) 585 ok / 678 bad
    - Perfumed Spirits not in Flasks val_imp: rows 5174.00 vs printed 3168.00
    - Perfumed Spirits not in Flasks val_efc: rows 4796.00 vs printed 2958.00
    - Perfumed Spirits not in Flasks duty: rows 1493.67 vs printed 645.38
    - Perfumed Spirits in Flasks val_imp: rows 8728.00 vs printed 8394.00
| 1874 | A | 5619 | detail 3923, article_total 1696 | article closure (details vs total, blocks with 2+ rows) 1137 ok / 1055 bad
    - roasted or ground val_imp: rows 36580.00 vs printed 2520.00
    - roasted or ground val_efc: rows 36487.00 vs printed 84.00
    - Spain val_imp: rows 59700.00 vs printed 257.00
    - Spain val_efc: rows 136.00 vs printed 37.00
| 1875 | A | 6487 | detail 4834, article_total 1653 | article closure (details vs total, blocks with 2+ rows) 1488 ok / 1227 bad
    - fresh, salted or smoked val_imp: rows 869400.00 vs printed 768415.00
    - fresh, salted or smoked val_efc: rows 827915.00 vs printed 746445.00
    - fresh, salted or smoked duty: rows 88450.77 vs printed 81936.11
    - Coal and Kerosene, Naphtha, Benzole and  val_imp: rows 22458.00 vs printed 22442.00
| 1876 | B | 7931 | detail 6001, article_total 1930 | article closure (details vs total, blocks with 2+ rows) 3585 ok / 1175 bad
    - Cigars duty: rows 17584.29 vs printed 17586.29
    - Hops val_imp: rows 7113.00 vs printed 7110.00
    - Hops val_efc: rows 7113.00 vs printed 7110.00
    - Hops duty: rows 1902.20 vs printed 1901.30
| 1877 | B | 10830 | detail 8103, article_total 2727 | article closure (details vs total, blocks with 2+ rows) 4830 ok / 1794 bad
    - Cigars, old T to 21st Feb val_imp: rows 16949.00 vs printed 16491.00
    - Hops val_imp: rows 7641.00 vs printed 7636.00
    - Hops val_efc: rows 7641.00 vs printed 7636.00
    - Hops duty: rows 1581.75 vs printed 1577.70
| 1878 | B | 10701 | detail 7928, article_total 2773 | article closure (details vs total, blocks with 2+ rows) 4430 ok / 1926 bad
    - Roasted or ground val_imp: rows 2117.00 vs printed 2083.00
    - Roasted or ground val_efc: rows 2441.00 vs printed 2417.00
    - Roasted or ground duty: rows 1903.54 vs printed 1883.32
    - Mutton val_imp: rows 318288.00 vs printed 318029.00
| 1880 | C | 15340 | detail 8773, article_province_total 4029, country_total 1788, article_total 680, country_noprov 56, article_total_fused 14 | country closure 3980 ok / 719 bad; article blocks (sum detail vs grand total, val_imp): exact 440, no_grand_total 239, within_1pct 129, under 32, over 27
    - Ginger Ale/Great Britain val_efc: rows 2486.00 vs printed 2446.00
    - Ginger Ale/Great Britain duty: rows 489.39 vs printed 489.19
    - Horses/United States val_efc: rows 41407.00 vs printed 41409.00
    - Swine/United States duty: rows 23525.33 vs printed 23725.13
    - Baking Powders/United tates val_efc: rows 23217.00 vs printed 23017.00
    - Black Lead/United States val_imp: rows 3811.00 vs printed 3711.00
| 1881 | C | 15879 | detail 9193, article_province_total 4189, country_total 1824, article_total 626, country_noprov 26, article_total_fused 21 | country closure 4628 ok / 387 bad; article blocks (sum detail vs grand total, val_imp): exact 518, no_grand_total 246, within_1pct 60, under 36, over 12
    - Ale, Beer and Porter, in bottles/United States val_imp: rows 1126.00 vs printed 1128.00
    - Ale, Beer and Porter, in bottles/United States val_efc: rows 986.00 vs printed 1336.00
    - Ale, Beer and Porter, in casks/Great Britain val_imp: rows 22084.00 vs printed 22031.00
    - Ale, Beer and Porter, in casks/Great Britain val_efc: rows 23828.00 vs printed 23818.00
    - Ginger Ale/Great Britain val_imp: rows 2912.00 vs printed 3234.00
    - Ginger Ale/Great Britain val_efc: rows 2401.00 vs printed 2770.00
| 1882 | C | 17162 | detail 10006, article_province_total 4424, country_total 1983, article_total 684, article_total_fused 35, country_noprov 29, heading_row 1 | country closure 5051 ok / 310 bad; article blocks (sum detail vs grand total, val_imp): exact 568, no_grand_total 271, within_1pct 61, under 33, over 10
    - Black Lead/United States val_imp: rows 8434.00 vs printed 8034.00
    - Books, Printed, &c/Germany duty: rows 62.92 vs printed 62.85
    - Account Books, Copy Books, or Books to b/United States val_imp: rows 44065.00 vs printed 44095.00
    - Account Books, Copy Books, or Books to b/United States val_efc: rows 43830.00 vs printed 43860.00
    - Bookbinders' Tools and Implements, inclu/United States duty: rows 2492.62 vs printed 2488.62
    - Braces or Suspenders, Belts and trusses /Great Britain val_efc: rows 85308.00 vs printed 85360.00
| 1883 | C | 17713 | detail 10419, article_province_total 4406, country_total 2072, article_total 728, country_noprov 53, article_total_fused 35 | country closure 5245 ok / 362 bad; article blocks (sum detail vs grand total, val_imp): exact 585, no_grand_total 285, within_1pct 76, under 42, over 7
    - Ale, beer and porter, in casks/Great Britain val_efc: rows 28475.00 vs printed 29335.00
    - Swine to be slaughtered in bond for Expo/United States val_imp: rows 173625.00 vs printed 173585.00
    - Bags, containing fine salt/Great Britain val_imp: rows 10937.00 vs printed 10417.00
    - Baking powders/United States val_imp: rows 77265.00 vs printed 77215.00
    - Blacklead/Great Britain duty: rows 2943.15 vs printed 2942.15
    - Books, printed, periodicals and pamphlet/France duty: rows 7024.90 vs printed 7023.90
| 1884 | C | 17727 | detail 10656, article_province_total 4088, country_total 2141, article_total 766, country_noprov 45, article_total_fused 29, heading_row 2 | country closure 5387 ok / 417 bad; article blocks (sum detail vs grand total, val_imp): exact 622, no_grand_total 308, within_1pct 67, under 32, over 18
    - Horses/Great Britain val_imp: rows 12069.00 vs printed 12049.00
    - Horses/United States val_efc: rows 207988.00 vs printed 107988.00
    - Sheep/United States duty: rows 9378.90 vs printed 9678.90
    - Swine/United States } (for immediate slaughter)..... } duty: rows 18754.20 vs printed 18751.20
    - Baking powders/Great Britain val_imp: rows 657.00 vs printed 647.00
    - Without pockets, 4½ by 9 ft. or under/United States val_imp: rows 2931.00 vs printed 3331.00
| 1885 | C | 17735 | detail 10817, article_province_total 3840, country_total 2216, article_total 782, country_noprov 59, article_total_fused 20, heading_row 1 | country closure 5597 ok / 377 bad; article blocks (sum detail vs grand total, val_imp): exact 651, no_grand_total 322, within_1pct 71, under 27, over 13
    - Ale, beer and porter, in casks/United States duty: rows 9374.00 vs printed 9374.06
    - Baking powders/Great Britain duty: rows 115.20 vs printed 117.20
    - Bells of any description, except for chu/United States val_efc: rows 12134.00 vs printed 12334.00
    - Books, printed, periodicals and pamphlet/France val_imp: rows 32222.00 vs printed 32272.00
    - British copyright works, reprints of/United States duty: rows 574.95 vs printed 568.95
    - Bibles, prayer books, psalm and hymn boo/Great Britain val_imp: rows 75066.00 vs printed 75068.00
| 1887 | C | 15788 | detail 11808, country_total 2427, article_total 902, article_province_total 497, country_noprov 91, recap 51, summary 7, article_total_fused 5 | country closure 5981 ok / 615 bad; article blocks (sum detail vs grand total, val_imp): exact 721, no_grand_total 371, within_1pct 103, under 65, over 9
    - Ale, ginger/Great Britain duty: rows 771.40 vs printed 791.40
    - Horned cattle/United States val_efc: rows 60398.00 vs printed 60497.00
    - Sheep/United States duty: rows 14689.22 vs printed 14659.22
    - Swine/United States val_efc: rows 36986.00 vs printed 36936.00
    - Belts and trusses of all kinds/United States val_imp: rows 15060.00 vs printed 15120.00
    - Belts and trusses of all kinds/United States val_efc: rows 15060.00 vs printed 15120.00
| 1888 | C | 16546 | detail 12460, country_total 2586, article_total 978, article_province_total 325, country_noprov 126, recap 60, summary 8, article_total_fused 3 | country closure 6780 ok / 202 bad; article blocks (sum detail vs grand total, val_imp): exact 868, no_grand_total 309, under 56, within_1pct 34, over 11
    - Horned cattle/United States duty: rows 4199.20 vs printed 4190.20
    - Sheep/United States duty: rows 13678.30 vs printed 13078.30
    - Swine/United States val_imp: rows 53504.00 vs printed 53501.00
    - Swine/United States val_efc: rows 53504.00 vs printed 53501.00
    - Bells of any description, except for chu/United States duty: rows 2096.55 vs printed 4272.45
    - Posters, advertising, bills, tickets and/United States val_imp: rows 29435.00 vs printed 29135.00
| 1889 | C | 16739 | detail 12816, country_total 2606, article_total 995, article_province_total 215, recap 54, country_noprov 49, summary 4 | country closure 7058 ok / 120 bad; article blocks (sum detail vs grand total, val_imp): exact 923, no_grand_total 304, under 39, within_1pct 15, over 8
    - Ale, beer and porter, in casks/United States val_efc: rows 14148.00 vs printed 13148.00
    - Belts and trusses of all kinds/Great Britain duty: rows 1931.70 vs printed 1932.20
    - British copyright works, reprints of/United States val_efc: rows 15970.00 vs printed 15941.00
    - Drawing tubing and plain and fancy tubin/Great Britain duty: rows 0.00 vs printed 906.30
    - Drawing tubing and plain and fancy tubin/United States duty: rows 0.00 vs printed 1750.90
    - Wire cloth/United States val_efc: rows 8532.00 vs printed 8332.00

## National check: sum of province-level rows vs the printed Total Imports series

Printed series: `reference/canada_printed_totals.csv`. Parsed = sum of `detail` rows (regime C: province rows; A/B: country rows, province statements only, Dominion recapitulation excluded).

| FY | regime | parsed val_imp | printed imports | ratio | parsed val_efc | printed e.f.c. | ratio | parsed duty | printed duty | ratio |
|---|---|---|---|---|---|---|---|---|---|---|
| 1868 | A | 52,550,219 | 73,459,644 | 0.715 | 51,571,024 | 71,985,306 | 0.716 | 5,156,126 | 8,819,432 | 0.585 |
| 1869 | A | 47,436,878 | 70,415,165 | 0.674 | 46,572,733 | 67,402,170 | 0.691 | 4,602,293 | 8,398,970 | 0.548 |
| 1870 | A | 73,784,376 | 74,814,339 | 0.986 | 42,892,389 | 71,237,603 | 0.602 | 5,032,164 | 9,462,940 | 0.532 |
| 1871 | A | 46,418,582 | 96,092,971 | 0.483 | 41,744,409 | 86,947,482 | 0.480 | 5,137,089 | 11,843,656 | 0.434 |
| 1872 | A | 62,714,082 | 111,430,527 | 0.563 | 59,243,975 | 107,709,116 | 0.550 | 5,749,173 | 13,045,494 | 0.441 |
| 1873 | A | 66,669,157 | 128,011,281 | 0.521 | 67,452,302 | 127,514,594 | 0.529 | 6,698,258 | 13,017,730 | 0.515 |
| 1874 | A | 90,729,581 | 128,213,582 | 0.708 | 79,460,234 | 127,404,169 | 0.624 | 7,599,990 | 14,421,883 | 0.527 |
| 1875 | A | 136,076,992 | 123,070,283 | 1.106 | 114,622,467 | 119,618,657 | 0.958 | 11,014,607 | 15,361,382 | 0.717 |
| 1876 | B | 92,461,532 | 93,210,346 | 0.992 | 94,167,491 | 94,733,218 | 0.994 | 13,028,871 | 12,933,114 | 1.007 |
| 1877 | B | 99,643,779 | 99,327,962 | 1.003 | 99,756,093 | 96,300,483 | 1.036 | 14,690,553 | 12,548,451 | 1.171 |
| 1878 | B | 92,578,907 | 93,081,787 | 0.995 | 90,519,037 | 91,199,577 | 0.993 | 12,676,023 | 12,795,693 | 0.991 |
| 1880 | C | 87,454,688 | 86,489,747 | 1.011 | 72,127,707 | 71,787,349 | 1.005 | 14,208,046 | 14,138,849 | 1.005 |
| 1881 | C | 103,920,646 | 105,330,840 | 0.987 | 90,375,720 | 91,611,604 | 0.987 | 17,992,988 | 18,500,786 | 0.973 |
| 1882 | C | 116,570,076 | 119,419,500 | 0.976 | 112,119,987 | 112,648,927 | 0.995 | 21,457,381 | 21,708,837 | 0.988 |
| 1883 | C | 131,214,782 | 132,254,022 | 0.992 | 121,698,728 | 123,137,019 | 0.988 | 22,875,867 | 23,172,309 | 0.987 |
| 1884 | C | 115,475,345 | 116,397,043 | 0.992 | 107,607,226 | 108,180,644 | 0.995 | 20,075,809 | 20,164,963 | 0.996 |
| 1885 | C | 108,426,525 | 108,941,486 | 0.995 | 102,145,567 | 102,710,019 | 0.995 | 19,043,122 | 19,133,559 | 0.995 |
| 1887 | C | 112,441,511 | 112,892,236 | 0.996 | 105,346,584 | 105,639,428 | 0.997 | 22,242,428 | 22,469,706 | 0.990 |
| 1888 | C | 110,539,334 | 110,894,630 | 0.997 | 102,148,390 | 102,847,100 | 0.993 | 22,333,332 | 22,209,642 | 1.006 |
| 1889 | C | 114,970,472 | 115,224,931 | 0.998 | 109,771,395 | 109,673,447 | 1.001 | 23,688,593 | 23,784,523 | 0.996 |
