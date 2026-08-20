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

Diagnostics: scrambled_row 3588, fused_article_country_nodash 2933, short_article_heading 1572, short_row 1420, article_fragment 595, label_in_province_slot 595, short_country_label 564, country_label_lost 558, unfused_rows 528, article_heading_lost 475, no_regime_yet 455, fused_cells 344, label_slip_repaired 190, lost_label_resolved_detail 159, lost_label_after_total 139, short_total_label 116, fused_rows_expanded 80, province_unrecognised 78, lost_label_block 64, page_top_total_fusion 53, label_row_no_values 25, lost_label_resolved_total 18, lost_label_joined_prev_country 18, split_country_province 17, lost_label_total_structural 11, heading_fused_into_total 10, value_column_lost 8, fused_article_country 8, trailing_label_lost 6, country_inferred_United 5, country_inferred_Great 3
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
| 1880 | C | 15644 | detail 8676, article_province_total 3880, country_total 2291, article_total 689, country_noprov 103, article_total_fused 5 | country closure 3831 ok / 887 bad; article blocks (sum detail vs grand total, val_imp): no_grand_total 368, exact 319, within_1pct 105, under 96, over 40
    - Ginger Ale/Great Britain val_efc: rows 2486.00 vs printed 2446.00
    - Ginger Ale/Great Britain duty: rows 489.39 vs printed 489.19
    - Horses/United States val_efc: rows 41407.00 vs printed 41409.00
    - Swine/United States duty: rows 23525.33 vs printed 23725.13
    - Baking Powders/United tates val_efc: rows 23217.00 vs printed 23017.00
    - Black Lead/United States val_imp: rows 3811.00 vs printed 3711.00
| 1882 | C | 17207 | detail 10003, article_province_total 4319, country_total 2184, article_total 622, country_noprov 68, article_total_fused 11 | country closure 4951 ok / 390 bad; article blocks (sum detail vs grand total, val_imp): no_grand_total 479, exact 404, under 105, within_1pct 45, over 19
    - Swine/United States val_imp: rows 21006.00 vs printed 21964.00
    - Swine/United States val_efc: rows 21006.00 vs printed 21964.00
    - Swine/United States duty: rows 4201.06 vs printed 4392.66
    - Black Lead/United States val_imp: rows 8434.00 vs printed 8034.00
    - Books, Printed, &c/Germany duty: rows 62.92 vs printed 62.85
    - Account Books, Copy Books, or Books to b/United States val_imp: rows 44065.00 vs printed 44095.00
| 1883 | C | 17742 | detail 10434, article_province_total 4293, country_total 2251, article_total 651, country_noprov 102, article_total_fused 11 | country closure 5153 ok / 470 bad; article blocks (sum detail vs grand total, val_imp): no_grand_total 520, exact 415, under 130, within_1pct 61, over 13
    - Ale, beer and porter, in casks/Great Britain val_efc: rows 28475.00 vs printed 29335.00
    - Swine/United States val_imp: rows 4659.00 vs printed 21614.00
    - Swine/United States val_efc: rows 4659.00 vs printed 21614.00
    - Swine/United States duty: rows 931.85 vs printed 4322.85
    - Swine to be slaughtered in bond for Expo/United States val_imp: rows 1053.00 vs printed 173585.00
    - Swine to be slaughtered in bond for Expo/United States val_efc: rows 1053.00 vs printed 1090.00
| 1884 | C | 17872 | detail 10657, article_province_total 4010, country_total 2390, article_total 717, country_noprov 84, article_total_fused 14 | country closure 5338 ok / 493 bad; article blocks (sum detail vs grand total, val_imp): no_grand_total 502, exact 469, under 109, within_1pct 46, over 26
    - Horses/Great Britain val_imp: rows 12069.00 vs printed 12049.00
    - Horses/United States val_efc: rows 207988.00 vs printed 107988.00
    - Sheep/United States duty: rows 9378.90 vs printed 9678.90
    - Swine/United States } (for immediate slaughter)..... } duty: rows 18754.20 vs printed 18751.20
    - Baking powders/Great Britain val_imp: rows 657.00 vs printed 647.00
    - Without pockets, 4½ by 9 ft. or under/United States val_imp: rows 2931.00 vs printed 3331.00
| 1885 | C | 17825 | detail 10807, article_province_total 3789, country_total 2399, article_total 732, country_noprov 89, article_total_fused 9 | country closure 5495 ok / 453 bad; article blocks (sum detail vs grand total, val_imp): no_grand_total 535, exact 494, under 116, within_1pct 49, over 19
    - Ale, beer and porter, in casks/United States duty: rows 9374.00 vs printed 9374.06
    - Baking powders/Great Britain duty: rows 115.20 vs printed 117.20
    - Bells of any description, except for chu/United States val_efc: rows 12134.00 vs printed 12334.00
    - Books, printed, periodicals and pamphlet/France val_imp: rows 32222.00 vs printed 32272.00
    - British copyright works, reprints of/United States duty: rows 574.95 vs printed 568.95
    - Bibles, prayer books, psalm and hymn boo/Great Britain val_imp: rows 75066.00 vs printed 75068.00
| 1887 | C | 15785 | detail 11632, country_total 2557, article_total 914, article_province_total 500, country_noprov 127, recap 52, article_total_fused 3 | country closure 5812 ok / 677 bad; article blocks (sum detail vs grand total, val_imp): exact 575, no_grand_total 537, under 214, within_1pct 81, over 12
    - Ale, ginger/Great Britain duty: rows 771.40 vs printed 791.40
    - Horned cattle/United States val_efc: rows 60398.00 vs printed 60497.00
    - Sheep/United States duty: rows 14689.22 vs printed 14659.22
    - Swine/United States val_efc: rows 36986.00 vs printed 36936.00
    - Belts and trusses of all kinds/United States val_imp: rows 15060.00 vs printed 15120.00
    - Belts and trusses of all kinds/United States val_efc: rows 15060.00 vs printed 15120.00
| 1889 | C | 16804 | detail 12676, country_total 2764, article_total 1010, article_province_total 211, country_noprov 79, recap 64 | country closure 6944 ok / 163 bad; article blocks (sum detail vs grand total, val_imp): exact 778, no_grand_total 461, under 169, within_1pct 14, over 13
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
| 1869 | A | 47,836,228 | 70,415,165 | 0.679 | 47,247,673 | 67,402,170 | 0.701 | 4,604,996 | 8,398,970 | 0.548 |
| 1870 | A | 73,534,332 | 74,814,339 | 0.983 | 42,486,719 | 71,237,603 | 0.596 | 5,039,071 | 9,462,940 | 0.533 |
| 1871 | A | 51,502,140 | 96,092,971 | 0.536 | 46,775,761 | 86,947,482 | 0.538 | 5,125,374 | 11,843,656 | 0.433 |
| 1873 | A | 70,742,791 | 128,011,281 | 0.553 | 68,814,918 | 127,514,594 | 0.540 | 6,673,915 | 13,017,730 | 0.513 |
| 1877 | B | 99,643,810 | 99,327,962 | 1.003 | 99,756,138 | 96,300,483 | 1.036 | 14,690,503 | 12,548,451 | 1.171 |
| 1880 | C | 88,141,423 | 86,489,747 | 1.019 | 72,813,467 | 71,787,349 | 1.014 | 14,352,589 | 14,138,849 | 1.015 |
| 1882 | C | 117,629,002 | 119,419,500 | 0.985 | 113,064,982 | 112,648,927 | 1.004 | 21,554,700 | 21,708,837 | 0.993 |
| 1883 | C | 130,515,640 | 132,254,022 | 0.987 | 120,502,393 | 123,137,019 | 0.979 | 22,839,491 | 23,172,309 | 0.986 |
| 1884 | C | 114,241,353 | 116,397,043 | 0.981 | 106,492,875 | 108,180,644 | 0.984 | 19,793,786 | 20,164,963 | 0.982 |
| 1885 | C | 108,139,694 | 108,941,486 | 0.993 | 102,094,684 | 102,710,019 | 0.994 | 19,005,257 | 19,133,559 | 0.993 |
| 1887 | C | 109,931,299 | 112,892,236 | 0.974 | 106,018,032 | 105,639,428 | 1.004 | 22,454,749 | 22,469,706 | 0.999 |
| 1889 | C | 115,948,997 | 115,224,931 | 1.006 | 110,412,224 | 109,673,447 | 1.007 | 23,452,274 | 23,784,523 | 0.986 |
