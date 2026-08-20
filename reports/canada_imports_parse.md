# Canadian imports General Statement — parse diagnostics

`scripts/ca_parse_imports.py` → `db/canada/imports_general_rows.csv` (141636 rows)

| FY | volume | tables | rows |
|---|---|---|---|
| 1866-67 | oocihm.9_08052_1_1 | 0 | 0 |
| 1868 | oocihm.9_08052_2_1 | 87 | 1701 |
| 1869 | oocihm.9_08052_3_1 | 177 | 2535 |
| 1870 | oocihm.9_08052_4_2 | 198 | 2763 |
| 1871 | oocihm.9_08052_5_3 | 211 | 2421 |
| 1873 | oocihm.9_08052_7_4 | 251 | 3277 |
| 1877 | oocihm.9_08052_11_4 | 406 | 10828 |
| 1879 | oocihm.9_08052_13_10 | 0 | 0 |
| 1880 | oocihm.9_08052_14_2 | 459 | 15338 |
| 1882 | oocihm.9_08052_16_2 | 505 | 17127 |
| 1883 | oocihm.9_08052_17_1_2 | 521 | 17719 |
| 1884 | oocihm.9_08052_18_2 | 525 | 17708 |
| 1885 | oocihm.9_08052_19_1_2 | 530 | 17747 |
| 1887 | oocihm.9_08052_21_3 | 547 | 15765 |
| 1889 | oocihm.9_08052_23_2 | 558 | 16707 |

Diagnostics: scrambled_row 3547, fused_article_country_nodash 2964, short_article_heading 1692, short_row 1307, blank_row_skipped 1081, article_fragment 669, unfused_rows 659, label_in_province_slot 541, country_label_lost 537, short_country_label 511, no_regime_yet 455, fused_cells 378, article_heading_lost 216, label_slip_repaired 201, short_total_label 116, lost_label_resolved_detail 99, fused_rows_expanded 90, province_unrecognised 87, lost_label_after_total 81, page_top_total_fusion 55, lost_label_block 49, province_values_on_next_row 34, country_label_in_province_slot 33, lost_label_joined_prev_country 22, page_top_heading_continuation 22, split_country_province 17, lost_label_resolved_total 15, heading_fused_into_total 14, lost_label_total_structural 11, value_column_lost 8, fused_article_country 7, trailing_label_lost 5, country_inferred_Great 4, label_row_no_values 1
Cell flags: fused 1874, unparsed 137

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
| 1870 | A | 2763 | detail 1865, article_total 898 | article closure (details vs total, blocks with 2+ rows) 447 ok / 664 bad
    - Cordials val_imp: rows 526141.00 vs printed 632.00
    - Cordials val_efc: rows 75873.00 vs printed 706.00
    - Cordials duty: rows 7625.25 vs printed 407.46
    - Whiskey val_efc: rows 14828.00 vs printed 60.00
| 1871 | A | 2421 | detail 1492, article_total 929 | article closure (details vs total, blocks with 2+ rows) 342 ok / 539 bad
    - PAYING SPECIFIC DUTY val_imp: rows 13746.00 vs printed 317.00
    - PAYING SPECIFIC DUTY val_efc: rows 14120.00 vs printed 271.00
    - PAYING SPECIFIC DUTY duty: rows 2761.86 vs printed 52.80
    - Benzole, Naphtha, and Refined Petroleum val_imp: rows 767.00 vs printed 924.00
| 1873 | A | 3277 | detail 2035, article_total 1242 | article closure (details vs total, blocks with 2+ rows) 582 ok / 670 bad
    - Perfumed Spirits not in Flasks val_imp: rows 5174.00 vs printed 3168.00
    - Perfumed Spirits not in Flasks val_efc: rows 4796.00 vs printed 2958.00
    - Perfumed Spirits not in Flasks duty: rows 1493.67 vs printed 645.38
    - Perfumed Spirits in Flasks val_imp: rows 8728.00 vs printed 8394.00
| 1877 | B | 10828 | detail 8102, article_total 2726 | article closure (details vs total, blocks with 2+ rows) 4830 ok / 1792 bad
    - Cigars, old T to 21st Feb val_imp: rows 16949.00 vs printed 16491.00
    - Hops val_imp: rows 7641.00 vs printed 7636.00
    - Hops val_efc: rows 7641.00 vs printed 7636.00
    - Hops duty: rows 1581.75 vs printed 1577.70
| 1880 | C | 15338 | detail 8770, article_province_total 3898, country_total 1909, article_total 669, country_noprov 87, article_total_fused 5 | country closure 3881 ok / 835 bad; article blocks (sum detail vs grand total, val_imp): no_grand_total 353, exact 347, within_1pct 102, under 78, over 38
    - Ginger Ale/Great Britain val_efc: rows 2486.00 vs printed 2446.00
    - Ginger Ale/Great Britain duty: rows 489.39 vs printed 489.19
    - Horses/United States val_efc: rows 41407.00 vs printed 41409.00
    - Swine/United States duty: rows 23525.33 vs printed 23725.13
    - Baking Powders/United tates val_efc: rows 23217.00 vs printed 23017.00
    - Black Lead/United States val_imp: rows 3811.00 vs printed 3711.00
| 1882 | C | 17127 | detail 10004, article_province_total 4376, country_total 2075, article_total 600, country_noprov 59, article_total_fused 13 | country closure 4982 ok / 364 bad; article blocks (sum detail vs grand total, val_imp): no_grand_total 492, exact 411, under 107, within_1pct 43, over 14
    - Swine/United States val_imp: rows 21006.00 vs printed 21964.00
    - Swine/United States val_efc: rows 21006.00 vs printed 21964.00
    - Swine/United States duty: rows 4201.06 vs printed 4392.66
    - Black Lead/United States val_imp: rows 8434.00 vs printed 8034.00
    - Books, Printed, &c/Germany duty: rows 62.92 vs printed 62.85
    - Account Books, Copy Books, or Books to b/United States val_imp: rows 44065.00 vs printed 44095.00
| 1883 | C | 17719 | detail 10458, article_province_total 4355, country_total 2161, article_total 646, country_noprov 88, article_total_fused 11 | country closure 5175 ok / 452 bad; article blocks (sum detail vs grand total, val_imp): no_grand_total 511, exact 427, under 127, within_1pct 59, over 10
    - Ale, beer and porter, in casks/Great Britain val_efc: rows 28475.00 vs printed 29335.00
    - Swine/United States val_imp: rows 4659.00 vs printed 21614.00
    - Swine/United States val_efc: rows 4659.00 vs printed 21614.00
    - Swine/United States duty: rows 931.85 vs printed 4322.85
    - Swine to be slaughtered in bond for Expo/United States val_imp: rows 1053.00 vs printed 173585.00
    - Swine to be slaughtered in bond for Expo/United States val_efc: rows 1053.00 vs printed 1090.00
| 1884 | C | 17708 | detail 10656, article_province_total 4027, country_total 2240, article_total 695, country_noprov 76, article_total_fused 14 | country closure 5343 ok / 486 bad; article blocks (sum detail vs grand total, val_imp): no_grand_total 509, exact 469, under 114, within_1pct 46, over 23
    - Horses/Great Britain val_imp: rows 12069.00 vs printed 12049.00
    - Horses/United States val_efc: rows 207988.00 vs printed 107988.00
    - Sheep/United States duty: rows 9378.90 vs printed 9678.90
    - Swine/United States } (for immediate slaughter)..... } duty: rows 18754.20 vs printed 18751.20
    - Baking powders/Great Britain val_imp: rows 657.00 vs printed 647.00
    - Without pockets, 4½ by 9 ft. or under/United States val_imp: rows 2931.00 vs printed 3331.00
| 1885 | C | 17747 | detail 10842, article_province_total 3809, country_total 2295, article_total 712, country_noprov 80, article_total_fused 9 | country closure 5517 ok / 441 bad; article blocks (sum detail vs grand total, val_imp): no_grand_total 529, exact 501, under 108, within_1pct 51, over 20
    - Ale, beer and porter, in casks/United States duty: rows 9374.00 vs printed 9374.06
    - Baking powders/Great Britain duty: rows 115.20 vs printed 117.20
    - Bells of any description, except for chu/United States val_efc: rows 12134.00 vs printed 12334.00
    - Books, printed, periodicals and pamphlet/France val_imp: rows 32222.00 vs printed 32272.00
    - British copyright works, reprints of/United States duty: rows 574.95 vs printed 568.95
    - Bibles, prayer books, psalm and hymn boo/Great Britain val_imp: rows 75066.00 vs printed 75068.00
| 1887 | C | 15765 | detail 11754, country_total 2454, article_total 887, article_province_total 504, country_noprov 112, recap 51, article_total_fused 3 | country closure 5906 ok / 658 bad; article blocks (sum detail vs grand total, val_imp): exact 593, no_grand_total 525, under 198, within_1pct 82, over 11
    - Ale, ginger/Great Britain duty: rows 771.40 vs printed 791.40
    - Horned cattle/United States val_efc: rows 60398.00 vs printed 60497.00
    - Sheep/United States duty: rows 14689.22 vs printed 14659.22
    - Swine/United States val_efc: rows 36986.00 vs printed 36936.00
    - Belts and trusses of all kinds/United States val_imp: rows 15060.00 vs printed 15120.00
    - Belts and trusses of all kinds/United States val_efc: rows 15060.00 vs printed 15120.00
| 1889 | C | 16707 | detail 12763, country_total 2624, article_total 980, article_province_total 216, country_noprov 62, recap 62 | country closure 7007 ok / 161 bad; article blocks (sum detail vs grand total, val_imp): exact 784, no_grand_total 454, under 163, within_1pct 14, over 12
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
| 1870 | A | 72,975,680 | 74,814,339 | 0.975 | 42,063,554 | 71,237,603 | 0.590 | 4,989,429 | 9,462,940 | 0.527 |
| 1871 | A | 44,312,679 | 96,092,971 | 0.461 | 40,595,356 | 86,947,482 | 0.467 | 5,114,785 | 11,843,656 | 0.432 |
| 1873 | A | 65,498,455 | 128,011,281 | 0.512 | 69,856,771 | 127,514,594 | 0.548 | 6,885,348 | 13,017,730 | 0.529 |
| 1877 | B | 99,643,116 | 99,327,962 | 1.003 | 99,755,430 | 96,300,483 | 1.036 | 14,690,553 | 12,548,451 | 1.171 |
| 1880 | C | 88,258,591 | 86,489,747 | 1.020 | 72,892,370 | 71,787,349 | 1.015 | 14,347,310 | 14,138,849 | 1.015 |
| 1882 | C | 116,393,970 | 119,419,500 | 0.975 | 111,910,630 | 112,648,927 | 0.993 | 21,392,942 | 21,708,837 | 0.985 |
| 1883 | C | 131,397,482 | 132,254,022 | 0.994 | 121,370,413 | 123,137,019 | 0.986 | 23,024,585 | 23,172,309 | 0.994 |
| 1884 | C | 114,401,263 | 116,397,043 | 0.983 | 106,655,469 | 108,180,644 | 0.986 | 19,830,105 | 20,164,963 | 0.983 |
| 1885 | C | 108,195,083 | 108,941,486 | 0.993 | 102,211,374 | 102,710,019 | 0.995 | 19,031,586 | 19,133,559 | 0.995 |
| 1887 | C | 113,606,103 | 112,892,236 | 1.006 | 106,528,494 | 105,639,428 | 1.008 | 22,519,692 | 22,469,706 | 1.002 |
| 1889 | C | 115,991,380 | 115,224,931 | 1.007 | 110,411,189 | 109,673,447 | 1.007 | 23,436,404 | 23,784,523 | 0.985 |
