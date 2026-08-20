# Canadian imports General Statement — parse diagnostics

`scripts/ca_parse_imports.py` → `db/canada/imports_general_rows.csv` (142535 rows)

| FY | volume | tables | rows |
|---|---|---|---|
| 1866-67 | oocihm.9_08052_1_1 | 0 | 0 |
| 1868 | oocihm.9_08052_2_1 | 87 | 1701 |
| 1869 | oocihm.9_08052_3_1 | 177 | 2562 |
| 1870 | oocihm.9_08052_4_2 | 198 | 2789 |
| 1871 | oocihm.9_08052_5_3 | 211 | 2469 |
| 1873 | oocihm.9_08052_7_4 | 251 | 3304 |
| 1877 | oocihm.9_08052_11_4 | 406 | 10831 |
| 1879 | oocihm.9_08052_13_10 | 0 | 0 |
| 1880 | oocihm.9_08052_14_2 | 459 | 15644 |
| 1882 | oocihm.9_08052_16_2 | 505 | 17207 |
| 1883 | oocihm.9_08052_17_1_2 | 521 | 17742 |
| 1884 | oocihm.9_08052_18_2 | 525 | 17872 |
| 1885 | oocihm.9_08052_19_1_2 | 530 | 17825 |
| 1887 | oocihm.9_08052_21_3 | 547 | 15785 |
| 1889 | oocihm.9_08052_23_2 | 558 | 16804 |

Diagnostics: short_row 3967, scrambled_row 3588, fused_article_country_nodash 2933, lost_label_after_total 1348, lost_label_resolved_detail 1266, article_heading_lost 971, label_in_province_slot 595, country_label_lost 558, unfused_rows 528, no_regime_yet 455, fused_cells 344, article_fragment 296, lost_label_block 244, lost_label_resolved_total 183, fused_rows_expanded 80, province_unrecognised 78, country_inferred_United 65, page_top_total_fusion 46, lost_label_total_structural 28, label_row_no_values 22, split_country_province 17, fused_article_country 8, lost_label_total_by_sum 3
Cell flags: fused 1997, unparsed 875

| FY | regime | rows | row kinds |
|---|---|---|---|
| 1868 | A | 1701 | detail 1198, article_total 503 | article closure (details vs total, blocks with 2+ rows) 335 ok / 388 bad
    - Sulphuric val_imp: rows 62436.00 vs printed 24.00
    - Sulphuric val_efc: rows 4408.00 vs printed 543.00
    - Other F. Countries val_imp: rows 90796.00 vs printed 78842.00
    - Other F. Countries val_efc: rows 95966.00 vs printed 52307.00
| 1869 | A | 2562 | detail 1715, article_total 847 | article closure (details vs total, blocks with 2+ rows) 375 ok / 670 bad
    - Horned Cattle duty: rows 280.00 vs printed 300.00
    - Sulphuric val_imp: rows 1763.00 vs printed 1733.00
    - Sulphuric val_efc: rows 1763.00 vs printed 1733.00
    - Sulphuric duty: rows 547.39 vs printed 524.39
| 1870 | A | 2789 | detail 1943, article_total 846 | article closure (details vs total, blocks with 2+ rows) 487 ok / 650 bad
    - Cordials val_imp: rows 526141.00 vs printed 632.00
    - Cordials val_efc: rows 75873.00 vs printed 706.00
    - Cordials duty: rows 7625.25 vs printed 407.46
    - Whiskey val_efc: rows 14828.00 vs printed 60.00
| 1871 | A | 2469 | detail 1586, article_total 883 | article closure (details vs total, blocks with 2+ rows) 383 ok / 500 bad
    - PAYING SPECIFIC DUTY val_imp: rows 13746.00 vs printed 317.00
    - PAYING SPECIFIC DUTY val_efc: rows 14120.00 vs printed 271.00
    - PAYING SPECIFIC DUTY duty: rows 2761.86 vs printed 52.80
    - Benzole, Naphtha, and Refined Petroleum val_imp: rows 767.00 vs printed 924.00
| 1873 | A | 3304 | detail 2082, article_total 1222 | article closure (details vs total, blocks with 2+ rows) 575 ok / 651 bad
    - Perfumed Spirits not in Flasks val_imp: rows 5174.00 vs printed 3168.00
    - Perfumed Spirits not in Flasks val_efc: rows 4796.00 vs printed 2958.00
    - Perfumed Spirits not in Flasks duty: rows 1493.67 vs printed 645.38
    - Perfumed Spirits not in Flasks val_imp: rows 8728.00 vs printed 8394.00
| 1877 | B | 10831 | detail 8103, article_total 2728 | article closure (details vs total, blocks with 2+ rows) 4830 ok / 1794 bad
    - Cigars, old T to 21st Feb val_imp: rows 16949.00 vs printed 16491.00
    - Hops val_imp: rows 7641.00 vs printed 7636.00
    - Hops val_efc: rows 7641.00 vs printed 7636.00
    - Hops duty: rows 1581.75 vs printed 1577.70
| 1880 | C | 15644 | detail 8702, article_province_total 3755, country_total 2470, article_total 607, country_noprov 105, article_total_fused 5 | country closure 3572 ok / 1229 bad; article blocks (sum detail vs grand total, val_imp): no_grand_total 368, exact 292, within_1pct 98, under 68, over 57
    - Ginger Ale/Great Britain val_efc: rows 2486.00 vs printed 2446.00
    - Ginger Ale/Great Britain duty: rows 489.39 vs printed 489.19
    - Horses/United States val_efc: rows 41407.00 vs printed 41409.00
    - Swine/United States duty: rows 23525.33 vs printed 23725.13
    - Baking Powders/United tates val_efc: rows 23217.00 vs printed 23017.00
    - Black Lead/United States val_imp: rows 3811.00 vs printed 3711.00
| 1882 | C | 17207 | detail 9999, article_province_total 4301, country_total 2215, article_total 614, country_noprov 68, article_total_fused 10 | country closure 4881 ok / 478 bad; article blocks (sum detail vs grand total, val_imp): no_grand_total 454, exact 366, under 96, within_1pct 48, over 37
    - Swine/United States val_imp: rows 21006.00 vs printed 21964.00
    - Swine/United States val_efc: rows 21006.00 vs printed 21964.00
    - Swine/United States duty: rows 4201.06 vs printed 4392.66
    - Blacking, Shoe, and Shoemaker's Ink, Har/? val_imp: rows 8434.00 vs printed 8034.00
    - Books, Printed, &c/Germany duty: rows 62.92 vs printed 62.85
    - Account Books, Copy Books, or Books to b/United States val_imp: rows 44065.00 vs printed 44095.00
| 1883 | C | 17742 | detail 10447, article_province_total 4259, country_total 2281, article_total 643, country_noprov 102, article_total_fused 10 | country closure 5086 ok / 563 bad; article blocks (sum detail vs grand total, val_imp): no_grand_total 494, exact 402, under 116, within_1pct 56, over 28
    - Ale, beer and porter, in casks/Great Britain val_efc: rows 28475.00 vs printed 29335.00
    - Swine/United States val_imp: rows 4659.00 vs printed 21614.00
    - Swine/United States val_efc: rows 4659.00 vs printed 21614.00
    - Swine/United States duty: rows 931.85 vs printed 4322.85
    - Swine to be slaughtered in bond for Expo/United States val_imp: rows 1053.00 vs printed 173585.00
    - Swine to be slaughtered in bond for Expo/United States val_efc: rows 1053.00 vs printed 1090.00
| 1884 | C | 17872 | detail 10672, article_province_total 3985, country_total 2395, article_total 726, country_noprov 84, article_total_fused 10 | country closure 5299 ok / 547 bad; article blocks (sum detail vs grand total, val_imp): no_grand_total 460, exact 435, under 95, over 46, within_1pct 45
    - Horses/Great Britain val_imp: rows 12069.00 vs printed 12049.00
    - Horses/United States val_efc: rows 207988.00 vs printed 107988.00
    - ?/United States duty: rows 9378.90 vs printed 9678.90
    - ?/United States } (for immediate slaughter)..... } duty: rows 18754.20 vs printed 18751.20
    - Baking powders/Great Britain val_imp: rows 657.00 vs printed 647.00
    - Without pockets, 4½ by 9 ft. or under/United States val_imp: rows 2931.00 vs printed 3331.00
| 1885 | C | 17825 | detail 10822, article_province_total 3756, country_total 2431, article_total 719, country_noprov 89, article_total_fused 8 | country closure 5445 ok / 523 bad; article blocks (sum detail vs grand total, val_imp): no_grand_total 502, exact 484, under 101, within_1pct 42, over 30, double 1
    - Ale, beer and porter, in bottles/? duty: rows 9374.00 vs printed 9374.06
    - Baking powders/Great Britain duty: rows 115.20 vs printed 117.20
    - Bells of any description, except for chu/? val_efc: rows 12134.00 vs printed 12334.00
    - Books, printed, periodicals and pamphlet/France val_imp: rows 32222.00 vs printed 32272.00
    - British copyright works, reprints of/United States duty: rows 574.95 vs printed 568.95
    - Bibles, prayer books, psalm and hymn boo/Great Britain val_imp: rows 75066.00 vs printed 75068.00
| 1887 | C | 15785 | detail 11614, country_total 2564, article_total 917, article_province_total 495, country_noprov 140, recap 52, article_total_fused 3 | country closure 5749 ok / 740 bad; article blocks (sum detail vs grand total, val_imp): exact 584, no_grand_total 488, under 181, within_1pct 87, over 16
    - Ale, ginger/Great Britain duty: rows 771.40 vs printed 791.40
    - ?/United States val_efc: rows 60398.00 vs printed 60497.00
    - Sheep/United States duty: rows 14689.22 vs printed 14659.22
    - Swine/United States val_efc: rows 36986.00 vs printed 36936.00
    - Belts and trusses of all kinds/United States val_imp: rows 15060.00 vs printed 15120.00
    - Belts and trusses of all kinds/United States val_efc: rows 15060.00 vs printed 15120.00
| 1889 | C | 16804 | detail 12672, country_total 2785, article_total 1000, article_province_total 211, country_noprov 90, recap 46 | country closure 6911 ok / 210 bad; article blocks (sum detail vs grand total, val_imp): exact 790, no_grand_total 413, under 131, within_1pct 20, over 18
    - DUTTABLE GOODS/United States val_efc: rows 14148.00 vs printed 13148.00
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
| 1869 | A | 47,836,228 | 70,415,165 | 0.679 | 47,247,673 | 67,402,170 | 0.701 | 4,604,996 | 8,398,970 | 0.548 |
| 1870 | A | 73,534,332 | 74,814,339 | 0.983 | 42,486,719 | 71,237,603 | 0.596 | 5,039,071 | 9,462,940 | 0.533 |
| 1871 | A | 51,502,140 | 96,092,971 | 0.536 | 46,775,761 | 86,947,482 | 0.538 | 5,125,374 | 11,843,656 | 0.433 |
| 1873 | A | 70,742,791 | 128,011,281 | 0.553 | 68,814,918 | 127,514,594 | 0.540 | 6,673,915 | 13,017,730 | 0.513 |
| 1877 | B | 99,643,810 | 99,327,962 | 1.003 | 99,756,138 | 96,300,483 | 1.036 | 14,690,503 | 12,548,451 | 1.171 |
| 1880 | C | 90,223,603 | 86,489,747 | 1.043 | 74,154,705 | 71,787,349 | 1.033 | 14,897,182 | 14,138,849 | 1.054 |
| 1882 | C | 118,790,662 | 119,419,500 | 0.995 | 114,199,370 | 112,648,927 | 1.014 | 21,853,262 | 21,708,837 | 1.007 |
| 1883 | C | 133,170,018 | 132,254,022 | 1.007 | 122,977,477 | 123,137,019 | 0.999 | 23,046,059 | 23,172,309 | 0.995 |
| 1884 | C | 121,678,431 | 116,397,043 | 1.045 | 113,899,428 | 108,180,644 | 1.053 | 21,360,084 | 20,164,963 | 1.059 |
| 1885 | C | 108,431,885 | 108,941,486 | 0.995 | 102,402,958 | 102,710,019 | 0.997 | 19,027,585 | 19,133,559 | 0.994 |
| 1887 | C | 109,974,182 | 112,892,236 | 0.974 | 106,062,199 | 105,639,428 | 1.004 | 22,463,401 | 22,469,706 | 1.000 |
| 1889 | C | 116,110,492 | 115,224,931 | 1.008 | 110,572,727 | 109,673,447 | 1.008 | 23,468,986 | 23,784,523 | 0.987 |
