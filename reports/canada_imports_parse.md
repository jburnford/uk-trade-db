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

Diagnostics: scrambled_row 3547, fused_article_country_nodash 2983, short_article_heading 1690, short_row 1307, blank_row_skipped 1082, unfused_rows 668, article_fragment 658, country_label_lost 550, short_country_label 513, label_in_province_slot 504, no_regime_yet 455, fused_cells 380, grand_total_rejoined 350, label_slip_repaired 282, article_heading_lost 180, adjacent_blocks_merged 167, lost_label_resolved_detail 167, page_top_total_fusion 136, short_total_label 116, fused_rows_expanded 90, heading_deferred_past_data_row 87, article_heading_lost_after_total 75, lost_label_after_total 75, province_unrecognised 75, lost_label_block 51, total_tail_rejoined 37, fused_article_country 35, country_label_in_province_slot 33, article_closed_with_prev 32, nil_province_row 28, lost_label_joined_next_country 28, grand_total_after_single_row 26, heading_fused_into_total 24, lost_label_joined_prev_country 23, country_inferred_Great 23, heading_fragment_starts_article 19, split_country_province 17, article_closed_with_next 16, lost_label_resolved_total 16, value_column_lost_block 14, page_top_heading_new_article 13, lost_label_total_structural 12, stray_unit_cells_dropped 11, heading_fragment_on_data_row 11, summary_line 11, trailing_label_lost 9, heading_from_label_row 8, value_column_lost 8, fused_efc_duty_split 7, province_values_on_next_row 7, slip_hypothesis_flipped 5, page_top_heading_continuation 5, duty_cell_dropped 4, label_slip2_repaired 4, article_resumed 3, country_inferred_United 1, label_slip_down 1
Cell flags: fused 1877, unparsed 135

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
| 1880 | C | 15339 | detail 8738, article_province_total 4020, country_total 1816, article_total 686, country_noprov 65, article_total_fused 14 | country closure 3957 ok / 708 bad; article blocks (sum detail vs grand total, val_imp): exact 420, no_grand_total 268, within_1pct 124, under 54, over 26
    - Ginger Ale/Great Britain val_efc: rows 2486.00 vs printed 2446.00
    - Ginger Ale/Great Britain duty: rows 489.39 vs printed 489.19
    - Horses/United States val_efc: rows 41407.00 vs printed 41409.00
    - Swine/United States duty: rows 23525.33 vs printed 23725.13
    - Baking Powders/United tates val_efc: rows 23217.00 vs printed 23017.00
    - Black Lead/United States val_imp: rows 3811.00 vs printed 3711.00
| 1882 | C | 17123 | detail 9966, article_province_total 4418, country_total 1989, article_total 681, article_total_fused 35, country_noprov 33, heading_row 1 | country closure 4989 ok / 314 bad; article blocks (sum detail vs grand total, val_imp): exact 526, no_grand_total 323, under 71, within_1pct 54, over 11
    - Black Lead/United States val_imp: rows 8434.00 vs printed 8034.00
    - Books, Printed, &c/Germany duty: rows 62.92 vs printed 62.85
    - Account Books, Copy Books, or Books to b/United States val_imp: rows 44065.00 vs printed 44095.00
    - Account Books, Copy Books, or Books to b/United States val_efc: rows 43830.00 vs printed 43860.00
    - Bookbinders' Tools and Implements, inclu/United States duty: rows 2492.62 vs printed 2488.62
    - Braces or Suspenders, Belts and trusses /Great Britain val_efc: rows 85308.00 vs printed 85360.00
| 1883 | C | 17708 | detail 10414, article_province_total 4395, country_total 2066, article_total 738, country_noprov 60, article_total_fused 35 | country closure 5194 ok / 372 bad; article blocks (sum detail vs grand total, val_imp): exact 553, no_grand_total 331, under 81, within_1pct 72, over 9
    - Ale, beer and porter, in casks/Great Britain val_efc: rows 28475.00 vs printed 29335.00
    - Bags, containing fine salt/Great Britain val_imp: rows 10937.00 vs printed 10417.00
    - Baking powders/United States val_imp: rows 77265.00 vs printed 77215.00
    - Blacklead/Great Britain duty: rows 2943.15 vs printed 2942.15
    - Books, printed, periodicals and pamphlet/France duty: rows 7024.90 vs printed 7023.90
    - Account books, copy books, or books to b/France val_imp: rows 576.00 vs printed 568.00
| 1884 | C | 17702 | detail 10620, article_province_total 4070, country_total 2148, article_total 777, country_noprov 57, article_total_fused 28, heading_row 2 | country closure 5367 ok / 415 bad; article blocks (sum detail vs grand total, val_imp): exact 592, no_grand_total 347, under 67, within_1pct 59, over 20
    - Horses/Great Britain val_imp: rows 12069.00 vs printed 12049.00
    - Horses/United States val_efc: rows 207988.00 vs printed 107988.00
    - Sheep/United States duty: rows 9378.90 vs printed 9678.90
    - Swine/United States } (for immediate slaughter)..... } duty: rows 18754.20 vs printed 18751.20
    - Baking powders/Great Britain val_imp: rows 657.00 vs printed 647.00
    - Without pockets, 4½ by 9 ft. or under/United States val_imp: rows 2931.00 vs printed 3331.00
| 1885 | C | 17747 | detail 10812, article_province_total 3839, country_total 2224, article_total 791, country_noprov 61, article_total_fused 19, heading_row 1 | country closure 5541 ok / 395 bad; article blocks (sum detail vs grand total, val_imp): exact 615, no_grand_total 374, under 64, within_1pct 62, over 15
    - Ale, beer and porter, in casks/United States duty: rows 9374.00 vs printed 9374.06
    - Baking powders/Great Britain duty: rows 115.20 vs printed 117.20
    - Bells of any description, except for chu/United States val_efc: rows 12134.00 vs printed 12334.00
    - Books, printed, periodicals and pamphlet/France val_imp: rows 32222.00 vs printed 32272.00
    - British copyright works, reprints of/United States duty: rows 574.95 vs printed 568.95
    - Bibles, prayer books, psalm and hymn boo/Great Britain val_imp: rows 75066.00 vs printed 75068.00
| 1887 | C | 15787 | detail 11785, country_total 2434, article_total 903, article_province_total 497, country_noprov 105, recap 51, summary 7, article_total_fused 5 | country closure 5958 ok / 612 bad; article blocks (sum detail vs grand total, val_imp): exact 691, no_grand_total 408, within_1pct 102, under 98, over 8
    - Ale, ginger/Great Britain duty: rows 771.40 vs printed 791.40
    - Horned cattle/United States val_efc: rows 60398.00 vs printed 60497.00
    - Sheep/United States duty: rows 14689.22 vs printed 14659.22
    - Swine/United States val_efc: rows 36986.00 vs printed 36936.00
    - Belts and trusses of all kinds/United States val_imp: rows 15060.00 vs printed 15120.00
    - Belts and trusses of all kinds/United States val_efc: rows 15060.00 vs printed 15120.00
| 1889 | C | 16720 | detail 12792, country_total 2610, article_total 994, article_province_total 211, country_noprov 55, recap 54, summary 4 | country closure 7043 ok / 118 bad; article blocks (sum detail vs grand total, val_imp): exact 892, no_grand_total 337, under 73, within_1pct 11, over 10
    - Ale, beer and porter, in casks/United States val_efc: rows 14148.00 vs printed 13148.00
    - Belts and trusses of all kinds/Great Britain duty: rows 1931.70 vs printed 1932.20
    - British copyright works, reprints of/United States val_efc: rows 15970.00 vs printed 15941.00
    - Wire cloth/United States val_efc: rows 8532.00 vs printed 8332.00
    - Brass, manufactures of, N. E. S/Great Britain duty: rows 22103.60 vs printed 21603.60
    - Beans/Great Britain duty: rows 2.85 vs printed 5.85

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
| 1880 | C | 87,359,659 | 86,489,747 | 1.010 | 72,044,443 | 71,787,349 | 1.004 | 14,189,121 | 14,138,849 | 1.004 |
| 1882 | C | 116,291,578 | 119,419,500 | 0.974 | 111,821,756 | 112,648,927 | 0.993 | 21,388,564 | 21,708,837 | 0.985 |
| 1883 | C | 130,767,924 | 132,254,022 | 0.989 | 120,741,043 | 123,137,019 | 0.981 | 22,791,649 | 23,172,309 | 0.984 |
| 1884 | C | 114,249,578 | 116,397,043 | 0.982 | 106,505,626 | 108,180,644 | 0.985 | 19,788,818 | 20,164,963 | 0.981 |
| 1885 | C | 108,271,865 | 108,941,486 | 0.994 | 102,213,306 | 102,710,019 | 0.995 | 19,006,091 | 19,133,559 | 0.993 |
| 1887 | C | 113,208,386 | 112,892,236 | 1.003 | 106,122,052 | 105,639,428 | 1.005 | 22,217,142 | 22,469,706 | 0.989 |
| 1889 | C | 115,352,778 | 115,224,931 | 1.001 | 109,827,744 | 109,673,447 | 1.001 | 23,612,225 | 23,784,523 | 0.993 |
