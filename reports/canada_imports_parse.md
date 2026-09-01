# Canadian imports General Statement — parse diagnostics

`scripts/ca_parse_imports.py` → `db/canada/imports_general_rows.csv` (253792 rows)

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
| 1879 | oocihm.9_08052_13_1 | 446 | 11454 |
| 1880 | oocihm.9_08052_14_2 | 459 | 15340 |
| 1881 | oocihm.9_08052_15_1_2 | 485 | 15879 |
| 1882 | oocihm.9_08052_16_2 | 505 | 17162 |
| 1883 | oocihm.9_08052_17_1_2 | 521 | 17713 |
| 1884 | oocihm.9_08052_18_2 | 525 | 17727 |
| 1885 | oocihm.9_08052_19_1_2 | 530 | 17735 |
| 1886 | oocihm.9_08052_20_1_2 | 552 | 17349 |
| 1887 | oocihm.9_08052_21_3 | 547 | 15788 |
| 1888 | oocihm.9_08052_22_1 | 571 | 16546 |
| 1889 | oocihm.9_08052_23_2 | 558 | 16739 |
| 1890 | oocihm.9_08052_24_3 | 578 | 16904 |
| 1897 | oocihm.9_08052_32_4 | 0 | 0 |

Diagnostics: scrambled_row 6461, fused_article_country_nodash 5085, short_row 2875, short_article_heading 2822, blank_row_skipped 1601, unfused_rows 1438, article_fragment 968, fused_cells 929, label_in_province_slot 795, country_label_lost 770, short_country_label 752, value_in_qty_slot 532, grand_total_rejoined 466, no_regime_yet 455, label_slip_repaired 353, article_heading_lost 297, adjacent_blocks_merged 267, fused_rows_expanded 235, lost_label_resolved_detail 215, qty_cells_dropped 212, junk_country_label 193, page_top_total_fusion 186, short_total_label 169, fused_efc_duty_split 143, lost_heading_closed_with_next 138, fused_qty_value_split 135, pagebreak_hijacker_restored 125, regime_flip_ignored 123, value_column_lost_block 122, heading_deferred_past_data_row 111, lost_label_after_total 93, article_heading_lost_after_total 86, lost_label_block 84, province_unrecognised 84, duty_cell_dropped 76, duty_cents_only 70, manual_repair 68, duty_cell_split_rejoined 56, fused_article_country 52, article_closed_with_prev 48, country_label_in_province_slot 47, lost_label_joined_next_country 46, value_in_duty_slot 45, total_tail_rejoined 45, nil_province_row 41, grand_total_after_single_row 37, value_column_lost 36, short_heading_with_country 35, phantom_blank_cell_dropped 35, total_pagebreak_rejoined 34, duty_cell_dropped_dutiable 34, country_inferred_Great 30, country_noprov_is_first_province 27, province_order_swapped 24, heading_fragment_starts_article 23, summary_line 23, lost_label_joined_prev_country 22, lost_label_resolved_total 21, phantom_pair_cells_dropped 20, split_country_province 20, page_top_heading_new_article 18, article_closed_with_next 16, lost_label_total_structural 16, heading_fragment_on_data_row 15, province_order_unarbitrated 14, noprov_slip_down 14, page_top_heading_continuation 14, stray_unit_cells_dropped 13, trailing_label_lost 13, qty_value_scrambled_block 10, heading_from_fragment_before_country 10, heading_fused_into_total 9, junk_country_swapped 9, heading_from_label_row 8, value_in_duty_slot_duty_row 8, province_dup_relabelled 7, total_block_labels_shifted 7, province_values_on_next_row 7, slip_hypothesis_flipped 6, heading_on_total_row 5, article_resumed 4, label_slip2_repaired 4, province_rows_swapped 3, country_inferred_United 2, province_dup_unarbitrated 1, grand_total_on_country_row 1, label_slip_down 1, single_detail_chain 1
Cell flags: fused 3857, unparsed 205

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
| 1879 | B | 11454 | detail 8683, article_total 2771 | article closure (details vs total, blocks with 2+ rows) 4535 ok / 2198 bad
    - All other, not elsewhere specified val_imp: rows 92988.00 vs printed 2504.00
    - All other, not elsewhere specified val_efc: rows 92988.00 vs printed 2504.00
    - All other, not elsewhere specified duty: rows 14886.83 vs printed 313.93
    - Billiard Tables, Bagatelle Boards, &c val_imp: rows 8825.00 vs printed 4660.00
| 1880 | C | 15341 | detail 8774, article_province_total 4029, country_total 1788, article_total 680, country_noprov 56, article_total_fused 14 | country closure 3981 ok / 718 bad; article blocks (sum detail vs grand total, val_imp): exact 440, no_grand_total 239, within_1pct 129, under 32, over 27
    - Ginger Ale/Great Britain val_efc: rows 2486.00 vs printed 2446.00
    - Ginger Ale/Great Britain duty: rows 489.39 vs printed 489.19
    - Horses/United States val_efc: rows 41407.00 vs printed 41409.00
    - Swine/United States duty: rows 23525.33 vs printed 23725.13
    - Baking Powders/United tates val_efc: rows 23217.00 vs printed 23017.00
    - Black Lead/United States val_imp: rows 3811.00 vs printed 3711.00
| 1881 | C | 15879 | detail 9186, article_province_total 4196, country_total 1821, article_total 629, country_noprov 26, article_total_fused 21 | country closure 4628 ok / 379 bad; article blocks (sum detail vs grand total, val_imp): exact 521, no_grand_total 241, within_1pct 60, under 36, over 12
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
| 1883 | C | 17713 | detail 10417, article_province_total 4408, country_total 2071, article_total 729, country_noprov 53, article_total_fused 35 | country closure 5245 ok / 359 bad; article blocks (sum detail vs grand total, val_imp): exact 586, no_grand_total 284, within_1pct 76, under 42, over 7
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
| 1885 | C | 17735 | detail 10813, article_province_total 3844, country_total 2214, article_total 784, country_noprov 59, article_total_fused 20, heading_row 1 | country closure 5597 ok / 371 bad; article blocks (sum detail vs grand total, val_imp): exact 654, no_grand_total 319, within_1pct 70, under 27, over 13
    - Ale, beer and porter, in casks/United States duty: rows 9374.00 vs printed 9374.06
    - Baking powders/Great Britain duty: rows 115.20 vs printed 117.20
    - Bells of any description, except for chu/United States val_efc: rows 12134.00 vs printed 12334.00
    - Books, printed, periodicals and pamphlet/France val_imp: rows 32222.00 vs printed 32272.00
    - British copyright works, reprints of/United States duty: rows 574.95 vs printed 568.95
    - Bibles, prayer books, psalm and hymn boo/Great Britain val_imp: rows 75066.00 vs printed 75068.00
| 1886 | C | 17349 | detail 11399, article_province_total 2679, country_total 2338, article_total 853, country_noprov 56, article_total_fused 24 | country closure 5935 ok / 453 bad; article blocks (sum detail vs grand total, val_imp): exact 713, no_grand_total 354, within_1pct 77, under 38, over 10
    - Ale, ginger/Great Britain val_efc: rows 2836.00 vs printed 2942.00
    - Ale, ginger/Great Britain duty: rows 567.20 vs printed 588.40
    - Swine/United States duty: rows 24311.60 vs printed 24811.60
    - Animals, all other N.E.S/United States duty: rows 2601.10 vs printed 2600.90
    - Bells of any description, except for chu/United States duty: rows 2014.30 vs printed 2064.30
    - Bird cages of all kinds/United States duty: rows 1067.00 vs printed 1068.00
| 1887 | C | 15788 | detail 11812, country_total 2428, article_total 901, article_province_total 493, country_noprov 91, recap 51, summary 7, article_total_fused 5 | country closure 5984 ok / 615 bad; article blocks (sum detail vs grand total, val_imp): exact 721, no_grand_total 372, within_1pct 103, under 64, over 9
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
| 1890 | C | 16904 | detail 13038, country_total 2668, article_total 1044, country_noprov 57, recap 57, article_province_total 36, summary 4 | country closure 7230 ok / 139 bad; article blocks (sum detail vs grand total, val_imp): exact 960, no_grand_total 309, under 56, within_1pct 14, over 6, double 1
    - Books, printed: periodicals and pamphlet/Germany duty: rows 183.30 vs printed 133.30
    - Bookbinders' tools and implements, inclu/Great Britain duty: rows 2226.36 vs printed 2226.30
    - Arrowroot and tapioca/Great Britain duty: rows 0.00 vs printed 7034.80
    - All other breadstuffs, N.E.S/China val_imp: rows 976.00 vs printed 988.00
    - ?/United States duty: rows 133.65 vs printed 31.00
    - do do costing $100 each and over/United States val_efc: rows 1175.00 vs printed 1085.00

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
| 1879 | B | 82,244,439 | 81,964,427 | 1.003 | 80,381,682 | 80,341,608 | 1.000 | 13,327,406 | 12,939,541 | 1.030 |
| 1880 | C | 87,454,688 | 86,489,747 | 1.011 | 72,131,305 | 71,787,349 | 1.005 | 14,208,767 | 14,138,849 | 1.005 |
| 1881 | C | 103,883,445 | 105,330,840 | 0.986 | 90,338,519 | 91,611,604 | 0.986 | 17,990,107 | 18,500,786 | 0.972 |
| 1882 | C | 116,570,076 | 119,419,500 | 0.976 | 112,119,987 | 112,648,927 | 0.995 | 21,457,381 | 21,708,837 | 0.988 |
| 1883 | C | 131,214,560 | 132,254,022 | 0.992 | 121,698,422 | 123,137,019 | 0.988 | 22,875,806 | 23,172,309 | 0.987 |
| 1884 | C | 115,475,345 | 116,397,043 | 0.992 | 107,607,226 | 108,180,644 | 0.995 | 20,075,809 | 20,164,963 | 0.996 |
| 1885 | C | 108,412,570 | 108,941,486 | 0.995 | 102,131,612 | 102,710,019 | 0.994 | 19,040,965 | 19,133,559 | 0.995 |
| 1886 | C | 104,333,834 | 104,424,561 | 0.999 | 99,485,193 | 99,602,694 | 0.999 | 19,129,860 | 19,448,124 | 0.984 |
| 1887 | C | 112,486,650 | 112,892,236 | 0.996 | 105,396,725 | 105,639,428 | 0.998 | 22,252,457 | 22,469,706 | 0.990 |
| 1888 | C | 110,539,334 | 110,894,630 | 0.997 | 102,148,390 | 102,847,100 | 0.993 | 22,333,332 | 22,209,642 | 1.006 |
| 1889 | C | 114,970,472 | 115,224,931 | 0.998 | 109,771,395 | 109,673,447 | 1.001 | 23,688,593 | 23,784,523 | 0.996 |
| 1890 | C | 121,580,591 | 121,858,241 | 0.998 | 112,608,536 | 112,765,584 | 0.999 | 23,859,728 | 24,014,908 | 0.994 |
