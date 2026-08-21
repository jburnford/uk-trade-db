# Canadian imports General Statement — parse diagnostics

`scripts/ca_parse_imports.py` → `db/canada/imports_general_rows.csv` (141651 rows)

| FY | volume | tables | rows |
|---|---|---|---|
| 1866-67 | oocihm.9_08052_1_1 | 0 | 0 |
| 1868 | oocihm.9_08052_2_1 | 87 | 1701 |
| 1869 | oocihm.9_08052_3_1 | 177 | 2535 |
| 1870 | oocihm.9_08052_4_2 | 198 | 2761 |
| 1871 | oocihm.9_08052_5_3 | 211 | 2421 |
| 1873 | oocihm.9_08052_7_4 | 251 | 3277 |
| 1877 | oocihm.9_08052_11_4 | 406 | 10830 |
| 1879 | oocihm.9_08052_13_10 | 0 | 0 |
| 1880 | oocihm.9_08052_14_2 | 459 | 15339 |
| 1882 | oocihm.9_08052_16_2 | 505 | 17123 |
| 1883 | oocihm.9_08052_17_1_2 | 521 | 17708 |
| 1884 | oocihm.9_08052_18_2 | 525 | 17702 |
| 1885 | oocihm.9_08052_19_1_2 | 530 | 17747 |
| 1887 | oocihm.9_08052_21_3 | 547 | 15787 |
| 1889 | oocihm.9_08052_23_2 | 558 | 16720 |

Diagnostics: scrambled_row 3547, fused_article_country_nodash 2982, short_article_heading 1690, short_row 1307, blank_row_skipped 1082, unfused_rows 668, article_fragment 658, country_label_lost 553, label_in_province_slot 541, short_country_label 513, no_regime_yet 455, fused_cells 380, grand_total_rejoined 349, label_slip_repaired 202, article_heading_lost 188, lost_label_resolved_detail 168, page_top_total_fusion 136, short_total_label 116, fused_rows_expanded 90, article_heading_lost_after_total 87, heading_deferred_past_data_row 86, province_unrecognised 76, lost_label_after_total 75, lost_label_block 51, total_tail_rejoined 37, fused_article_country 35, country_label_in_province_slot 33, article_closed_with_prev 33, nil_province_row 28, lost_label_joined_next_country 28, country_inferred_Great 23, lost_label_joined_prev_country 22, heading_fragment_starts_article 19, heading_fused_into_total 18, lost_label_resolved_total 17, split_country_province 17, article_closed_with_next 16, page_top_heading_new_article 14, lost_label_total_structural 13, stray_unit_cells_dropped 11, heading_fragment_on_data_row 11, summary_line 11, heading_from_label_row 8, value_column_lost 8, province_values_on_next_row 7, trailing_label_lost 5, page_top_heading_continuation 5, article_resumed 3, country_inferred_United 1, label_slip_down 1
Cell flags: fused 1884, unparsed 135

| FY | regime | rows | row kinds |
|---|---|---|---|
| 1868 | A | 1701 | detail 1198, article_total 503 | article closure (details vs total, blocks with 2+ rows) 335 ok / 388 bad
    - Sulphuric val_imp: rows 62436.00 vs printed 24.00
    - Sulphuric val_efc: rows 4408.00 vs printed 543.00
    - Other F. Countries val_imp: rows 90796.00 vs printed 78842.00
    - Other F. Countries val_efc: rows 95966.00 vs printed 52307.00
| 1869 | A | 2535 | detail 1674, article_total 861 | article closure (details vs total, blocks with 2+ rows) 341 ok / 695 bad
    - Horned Cattle duty: rows 280.00 vs printed 300.00
    - Sulphuric val_imp: rows 1763.00 vs printed 1733.00
    - Sulphuric val_efc: rows 1763.00 vs printed 1733.00
    - Sulphuric duty: rows 547.39 vs printed 524.39
| 1870 | A | 2761 | detail 1862, article_total 899 | article closure (details vs total, blocks with 2+ rows) 440 ok / 667 bad
    - Cordials val_imp: rows 526141.00 vs printed 632.00
    - Cordials val_efc: rows 75873.00 vs printed 706.00
    - Cordials duty: rows 7625.25 vs printed 407.46
    - Whiskey val_efc: rows 14828.00 vs printed 60.00
| 1871 | A | 2421 | detail 1499, article_total 922 | article closure (details vs total, blocks with 2+ rows) 334 ok / 541 bad
    - PAYING SPECIFIC DUTY val_imp: rows 13746.00 vs printed 317.00
    - PAYING SPECIFIC DUTY val_efc: rows 14120.00 vs printed 271.00
    - PAYING SPECIFIC DUTY duty: rows 2761.86 vs printed 52.80
    - Benzole, Naphtha, and Refined Petroleum val_imp: rows 767.00 vs printed 924.00
| 1873 | A | 3277 | detail 2035, article_total 1242 | article closure (details vs total, blocks with 2+ rows) 582 ok / 670 bad
    - Perfumed Spirits not in Flasks val_imp: rows 5174.00 vs printed 3168.00
    - Perfumed Spirits not in Flasks val_efc: rows 4796.00 vs printed 2958.00
    - Perfumed Spirits not in Flasks duty: rows 1493.67 vs printed 645.38
    - Perfumed Spirits in Flasks val_imp: rows 8728.00 vs printed 8394.00
| 1877 | B | 10830 | detail 8103, article_total 2727 | article closure (details vs total, blocks with 2+ rows) 4830 ok / 1794 bad
    - Cigars, old T to 21st Feb val_imp: rows 16949.00 vs printed 16491.00
    - Hops val_imp: rows 7641.00 vs printed 7636.00
    - Hops val_efc: rows 7641.00 vs printed 7636.00
    - Hops duty: rows 1581.75 vs printed 1577.70
| 1880 | C | 15339 | detail 8711, article_province_total 3966, country_total 1846, article_total 724, country_noprov 78, article_total_fused 14 | country closure 3902 ok / 763 bad; article blocks (sum detail vs grand total, val_imp): exact 410, no_grand_total 291, within_1pct 118, under 69, over 22
    - Ginger Ale/Great Britain val_efc: rows 2486.00 vs printed 2446.00
    - Ginger Ale/Great Britain duty: rows 489.39 vs printed 489.19
    - Horses/United States val_efc: rows 41407.00 vs printed 41409.00
    - Swine/United States duty: rows 23525.33 vs printed 23725.13
    - Baking Powders/United tates val_efc: rows 23217.00 vs printed 23017.00
    - Black Lead/United States val_imp: rows 3811.00 vs printed 3711.00
| 1882 | C | 17123 | detail 9963, article_province_total 4413, country_total 1992, article_total 684, article_total_fused 35, country_noprov 35, heading_row 1 | country closure 4984 ok / 315 bad; article blocks (sum detail vs grand total, val_imp): exact 510, no_grand_total 349, under 88, within_1pct 52, over 11
    - Black Lead/United States val_imp: rows 8434.00 vs printed 8034.00
    - Books, Printed, &c/Germany duty: rows 62.92 vs printed 62.85
    - Account Books, Copy Books, or Books to b/United States val_imp: rows 44065.00 vs printed 44095.00
    - Account Books, Copy Books, or Books to b/United States val_efc: rows 43830.00 vs printed 43860.00
    - Bookbinders' Tools and Implements, inclu/United States duty: rows 2492.62 vs printed 2488.62
    - Braces or Suspenders, Belts and trusses /Great Britain val_efc: rows 85308.00 vs printed 85360.00
| 1883 | C | 17708 | detail 10416, article_province_total 4384, country_total 2077, article_total 732, country_noprov 64, article_total_fused 35 | country closure 5188 ok / 397 bad; article blocks (sum detail vs grand total, val_imp): exact 518, no_grand_total 380, under 111, within_1pct 71, over 8
    - Ale, beer and porter, in casks/Great Britain val_efc: rows 28475.00 vs printed 29335.00
    - Swine/United States val_imp: rows 4659.00 vs printed 21614.00
    - Swine/United States val_efc: rows 4659.00 vs printed 21614.00
    - Swine/United States duty: rows 931.85 vs printed 4322.85
    - Swine to be slaughtered in bond for Expo/United States val_imp: rows 1053.00 vs printed 173585.00
    - Swine to be slaughtered in bond for Expo/United States val_efc: rows 1053.00 vs printed 1090.00
| 1884 | C | 17702 | detail 10613, article_province_total 4064, country_total 2160, article_total 775, country_noprov 60, article_total_fused 28, heading_row 2 | country closure 5349 ok / 440 bad; article blocks (sum detail vs grand total, val_imp): exact 569, no_grand_total 384, under 93, within_1pct 55, over 19
    - Horses/Great Britain val_imp: rows 12069.00 vs printed 12049.00
    - Horses/United States val_efc: rows 207988.00 vs printed 107988.00
    - Sheep/United States duty: rows 9378.90 vs printed 9678.90
    - Swine/United States } (for immediate slaughter)..... } duty: rows 18754.20 vs printed 18751.20
    - Baking powders/Great Britain val_imp: rows 657.00 vs printed 647.00
    - Without pockets, 4½ by 9 ft. or under/United States val_imp: rows 2931.00 vs printed 3331.00
| 1885 | C | 17747 | detail 10810, article_province_total 3837, country_total 2231, article_total 784, country_noprov 65, article_total_fused 19, heading_row 1 | country closure 5534 ok / 416 bad; article blocks (sum detail vs grand total, val_imp): exact 586, no_grand_total 418, under 93, within_1pct 61, over 14
    - Ale, beer and porter, in casks/United States duty: rows 9374.00 vs printed 9374.06
    - Baking powders/Great Britain duty: rows 115.20 vs printed 117.20
    - Bells of any description, except for chu/United States val_efc: rows 12134.00 vs printed 12334.00
    - Books, printed, periodicals and pamphlet/France val_imp: rows 32222.00 vs printed 32272.00
    - British copyright works, reprints of/United States duty: rows 574.95 vs printed 568.95
    - Bibles, prayer books, psalm and hymn boo/Great Britain val_imp: rows 75066.00 vs printed 75068.00
| 1887 | C | 15787 | detail 11780, country_total 2445, article_total 894, article_province_total 496, country_noprov 109, recap 51, summary 7, article_total_fused 5 | country closure 5946 ok / 636 bad; article blocks (sum detail vs grand total, val_imp): exact 658, no_grand_total 457, under 134, within_1pct 91, over 8
    - Ale, ginger/Great Britain duty: rows 771.40 vs printed 791.40
    - Horned cattle/United States val_efc: rows 60398.00 vs printed 60497.00
    - Sheep/United States duty: rows 14689.22 vs printed 14659.22
    - Swine/United States val_efc: rows 36986.00 vs printed 36936.00
    - Belts and trusses of all kinds/United States val_imp: rows 15060.00 vs printed 15120.00
    - Belts and trusses of all kinds/United States val_efc: rows 15060.00 vs printed 15120.00
| 1889 | C | 16720 | detail 12785, country_total 2620, article_total 984, article_province_total 211, country_noprov 62, recap 54, summary 4 | country closure 7028 ok / 149 bad; article blocks (sum detail vs grand total, val_imp): exact 862, no_grand_total 373, under 94, within_1pct 12, over 9
    - Ale, beer and porter, in casks/United States val_efc: rows 14148.00 vs printed 13148.00
    - Belts and trusses of all kinds/Great Britain duty: rows 1931.70 vs printed 1932.20
    - British copyright works, reprints of/United States val_efc: rows 15970.00 vs printed 15941.00
    - Wire cloth/United States val_efc: rows 8532.00 vs printed 8332.00
    - Brass, manufactures of, N. E. S/Great Britain duty: rows 22103.60 vs printed 21603.60
    - Grain and products of: Beans/Great Britain duty: rows 2.85 vs printed 5.85

## National check: sum of province-level rows vs the printed Total Imports series

Printed series: `reference/canada_printed_totals.csv`. Parsed = sum of `detail` rows (regime C: province rows; A/B: country rows, province statements only, Dominion recapitulation excluded).

| FY | regime | parsed val_imp | printed imports | ratio | parsed val_efc | printed e.f.c. | ratio | parsed duty | printed duty | ratio |
|---|---|---|---|---|---|---|---|---|---|---|
| 1868 | B | 53,899,270 | 73,459,644 | 0.734 | 52,701,665 | 71,985,306 | 0.732 | 5,215,091 | 8,819,432 | 0.591 |
| 1869 | A | 47,436,878 | 70,415,165 | 0.674 | 46,572,733 | 67,402,170 | 0.691 | 4,602,293 | 8,398,970 | 0.548 |
| 1870 | A | 72,977,241 | 74,814,339 | 0.975 | 42,065,115 | 71,237,603 | 0.590 | 4,990,282 | 9,462,940 | 0.527 |
| 1871 | A | 46,418,582 | 96,092,971 | 0.483 | 41,744,409 | 86,947,482 | 0.480 | 5,137,089 | 11,843,656 | 0.434 |
| 1873 | A | 65,498,455 | 128,011,281 | 0.512 | 69,856,771 | 127,514,594 | 0.548 | 6,885,348 | 13,017,730 | 0.529 |
| 1877 | B | 99,643,779 | 99,327,962 | 1.003 | 99,756,093 | 96,300,483 | 1.036 | 14,690,553 | 12,548,451 | 1.171 |
| 1880 | C | 87,319,027 | 86,489,747 | 1.010 | 72,005,656 | 71,787,349 | 1.003 | 14,153,948 | 14,138,849 | 1.001 |
| 1882 | C | 116,291,653 | 119,419,500 | 0.974 | 111,808,313 | 112,648,927 | 0.993 | 21,385,149 | 21,708,837 | 0.985 |
| 1883 | C | 130,490,074 | 132,254,022 | 0.987 | 120,463,558 | 123,137,019 | 0.978 | 22,786,979 | 23,172,309 | 0.983 |
| 1884 | C | 114,231,777 | 116,397,043 | 0.981 | 106,486,936 | 108,180,644 | 0.984 | 19,784,089 | 20,164,963 | 0.981 |
| 1885 | C | 108,191,357 | 108,941,486 | 0.993 | 102,132,762 | 102,710,019 | 0.994 | 19,005,909 | 19,133,559 | 0.993 |
| 1887 | C | 113,205,866 | 112,892,236 | 1.003 | 106,119,562 | 105,639,428 | 1.005 | 22,216,261 | 22,469,706 | 0.989 |
| 1889 | C | 116,366,013 | 115,224,931 | 1.010 | 110,833,911 | 109,673,447 | 1.011 | 23,609,555 | 23,784,523 | 0.993 |
