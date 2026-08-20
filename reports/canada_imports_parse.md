# Canadian imports General Statement — parse diagnostics

`scripts/ca_parse_imports.py` → `db/canada/imports_general_rows.csv` (144134 rows)

| FY | volume | tables | rows |
|---|---|---|---|
| 1866-67 | oocihm.9_08052_1_1 | 0 | 0 |
| 1868 | oocihm.9_08052_2_1 | 87 | 1809 |
| 1869 | oocihm.9_08052_3_1 | 177 | 2798 |
| 1870 | oocihm.9_08052_4_2 | 198 | 3104 |
| 1871 | oocihm.9_08052_5_3 | 211 | 2935 |
| 1873 | oocihm.9_08052_7_4 | 251 | 3941 |
| 1877 | oocihm.9_08052_11_4 | 406 | 10822 |
| 1879 | oocihm.9_08052_13_10 | 0 | 0 |
| 1880 | oocihm.9_08052_14_2 | 459 | 15642 |
| 1882 | oocihm.9_08052_16_2 | 505 | 17196 |
| 1883 | oocihm.9_08052_17_1_2 | 521 | 17725 |
| 1884 | oocihm.9_08052_18_2 | 525 | 17863 |
| 1885 | oocihm.9_08052_19_1_2 | 530 | 17811 |
| 1887 | oocihm.9_08052_21_3 | 547 | 15741 |
| 1889 | oocihm.9_08052_23_2 | 558 | 16747 |

Diagnostics: short_row 4115, fused_article_country_nodash 2930, lost_label_after_total 1348, fused_cells 1292, lost_label_resolved_detail 1267, article_heading_lost 951, label_in_province_slot 593, country_label_lost 557, no_regime_yet 455, article_fragment 324, lost_label_block 245, lost_label_resolved_total 183, province_unrecognised 78, page_top_total_fusion 46, lost_label_total_structural 28, label_row_no_values 22, split_country_province 17, fused_article_country 8, lost_label_total_by_sum 3
Cell flags: fused 3407, unparsed 1810

| FY | regime | rows | row kinds |
|---|---|---|---|
| 1868 | A | 1809 | detail 1306, article_total 503 | article closure (details vs total, blocks with 2+ rows) 366 ok / 290 bad
    - 8,002 val_imp: rows 460543.00 vs printed 1832.00
    - 8,002 val_efc: rows 557412.00 vs printed 3190.00
    - 8,002 duty: rows 310526.20 vs printed 543.00
    - 9,512 val_imp: rows 28179.00 vs printed 4169.00
| 1869 | A | 2798 | detail 1797, article_total 1001 | article closure (details vs total, blocks with 2+ rows) 277 ok / 451 bad
    - Horned Cattle duty: rows 280.00 vs printed 300.00
    - Sulphuric val_imp: rows 1763.00 vs printed 1733.00
    - Sulphuric val_efc: rows 1763.00 vs printed 1733.00
    - Sulphuric duty: rows 547.39 vs printed 524.39
| 1870 | A | 3104 | detail 2127, article_total 977 | article closure (details vs total, blocks with 2+ rows) 377 ok / 465 bad
    - Cordials val_imp: rows 526141.00 vs printed 632.00
    - Cordials val_efc: rows 75873.00 vs printed 706.00
    - Cordials duty: rows 7625.25 vs printed 407.46
    - Spirits and Strong Waters val_efc: rows 176.00 vs printed 14.00
| 1871 | A | 2935 | detail 1892, article_total 1043 | article closure (details vs total, blocks with 2+ rows) 316 ok / 421 bad
    - PAYING SPECIFIC DUTY val_imp: rows 187254.00 vs printed 317.00
    - PAYING SPECIFIC DUTY val_efc: rows 124359.00 vs printed 271.00
    - PAYING SPECIFIC DUTY duty: rows 179914.22 vs printed 52.80
    - Benzole, Naphtha, and Refined Petroleum val_imp: rows 767.00 vs printed 924.00
| 1873 | A | 3941 | detail 2535, article_total 1406 | article closure (details vs total, blocks with 2+ rows) 488 ok / 521 bad
    - Perfumed Spirits not in Flasks val_imp: rows 5174.00 vs printed 3168.00
    - Perfumed Spirits not in Flasks val_efc: rows 4796.00 vs printed 2958.00
    - Perfumed Spirits not in Flasks duty: rows 1493.67 vs printed 645.38
    - Holland val_imp: rows 163838.00 vs printed 13774.00
| 1877 | B | 10822 | detail 8100, article_total 2722 | article closure (details vs total, blocks with 2+ rows) 4816 ok / 1793 bad
    - Cigars, old T to 21st Feb val_imp: rows 16949.00 vs printed 16491.00
    - Hops val_imp: rows 7641.00 vs printed 7636.00
    - Hops val_efc: rows 7641.00 vs printed 7636.00
    - Hops duty: rows 1581.75 vs printed 1577.70
| 1880 | C | 15642 | detail 8702, article_province_total 3755, country_total 2470, article_total 607, country_noprov 103, article_total_fused 5 | country closure 3572 ok / 1229 bad; article blocks (sum detail vs grand total, val_imp): no_grand_total 368, exact 292, within_1pct 98, under 68, over 57
    - Ginger Ale/Great Britain val_efc: rows 2486.00 vs printed 2446.00
    - Ginger Ale/Great Britain duty: rows 489.39 vs printed 489.19
    - Horses/? val_efc: rows 41407.00 vs printed 41409.00
    - Swine/United States duty: rows 23525.33 vs printed 23725.13
    - Baking Powders/United tates val_efc: rows 23217.00 vs printed 23017.00
    - Black Lead/United States val_imp: rows 3811.00 vs printed 3711.00
| 1882 | C | 17196 | detail 9992, article_province_total 4301, country_total 2215, article_total 612, country_noprov 66, article_total_fused 10 | country closure 4878 ok / 479 bad; article blocks (sum detail vs grand total, val_imp): no_grand_total 456, exact 366, under 97, within_1pct 48, over 35
    - Swine/United States val_imp: rows 21006.00 vs printed 21964.00
    - Swine/United States val_efc: rows 21006.00 vs printed 21964.00
    - Swine/United States duty: rows 4201.06 vs printed 4392.66
    - Blacking, Shoe, and Shoemaker's Ink, Har/? val_imp: rows 8434.00 vs printed 8034.00
    - Books, Printed, &c/Germany duty: rows 62.92 vs printed 62.85
    - Account Books, Copy Books, or Books to b/United States val_imp: rows 44065.00 vs printed 44095.00
| 1883 | C | 17725 | detail 10434, article_province_total 4256, country_total 2281, article_total 643, country_noprov 101, article_total_fused 10 | country closure 5073 ok / 559 bad; article blocks (sum detail vs grand total, val_imp): no_grand_total 493, exact 402, under 116, within_1pct 56, over 28
    - Ale, beer and porter, in casks/Great Britain val_efc: rows 28475.00 vs printed 29335.00
    - Swine/United States val_imp: rows 4659.00 vs printed 21614.00
    - Swine/United States val_efc: rows 4659.00 vs printed 21614.00
    - Swine/United States duty: rows 931.85 vs printed 4322.85
    - Swine to be slaughtered in bond for Expo/United States val_imp: rows 1053.00 vs printed 173585.00
    - Swine to be slaughtered in bond for Expo/United States val_efc: rows 1053.00 vs printed 1090.00
| 1884 | C | 17863 | detail 10667, article_province_total 3983, country_total 2394, article_total 726, country_noprov 83, article_total_fused 10 | country closure 5298 ok / 543 bad; article blocks (sum detail vs grand total, val_imp): no_grand_total 459, exact 435, under 95, over 46, within_1pct 45
    - Horses/Great Britain val_imp: rows 12069.00 vs printed 12049.00
    - Horses/United States val_efc: rows 207988.00 vs printed 107988.00
    - ?/United States duty: rows 9378.90 vs printed 9678.90
    - ?/United States } (for immediate slaughter)..... } duty: rows 18754.20 vs printed 18751.20
    - Baking powders/Great Britain val_imp: rows 657.00 vs printed 647.00
    - Without pockets, 4½ by 9 ft. or under/United States val_imp: rows 2931.00 vs printed 3331.00
| 1885 | C | 17811 | detail 10811, article_province_total 3756, country_total 2431, article_total 719, country_noprov 86, article_total_fused 8 | country closure 5439 ok / 523 bad; article blocks (sum detail vs grand total, val_imp): no_grand_total 499, exact 483, under 102, within_1pct 42, over 30, double 1
    - Ale, beer and porter, in bottles/? duty: rows 9374.00 vs printed 9374.06
    - Baking powders/Great Britain duty: rows 115.20 vs printed 117.20
    - Bells of any description, except for chu/? val_efc: rows 12134.00 vs printed 12334.00
    - Books, printed, periodicals and pamphlet/France val_imp: rows 32222.00 vs printed 32272.00
    - British copyright works, reprints of/United States duty: rows 574.95 vs printed 568.95
    - Bibles, prayer books, psalm and hymn boo/Great Britain val_imp: rows 75066.00 vs printed 75068.00
| 1887 | C | 15741 | detail 11583, country_total 2564, article_total 917, article_province_total 492, country_noprov 130, recap 52, article_total_fused 3 | country closure 5722 ok / 750 bad; article blocks (sum detail vs grand total, val_imp): exact 582, no_grand_total 495, under 184, within_1pct 87, over 15
    - Ale, ginger/Great Britain duty: rows 771.40 vs printed 791.40
    - ?/United States val_efc: rows 60398.00 vs printed 60497.00
    - Sheep/United States duty: rows 14689.22 vs printed 14659.22
    - Swine/United States val_efc: rows 36986.00 vs printed 36936.00
    - Belts and trusses of all kinds/United States val_imp: rows 15060.00 vs printed 15120.00
    - Belts and trusses of all kinds/United States val_efc: rows 15060.00 vs printed 15120.00
| 1889 | C | 16747 | detail 12631, country_total 2785, article_total 1000, article_province_total 211, country_noprov 74, recap 46 | country closure 6874 ok / 217 bad; article blocks (sum detail vs grand total, val_imp): exact 790, no_grand_total 413, under 132, within_1pct 19, over 18
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
| 1868 | B | 46,965,203 | 73,459,644 | 0.639 | 41,753,675 | 71,985,306 | 0.580 | 22,243,059 | 8,819,432 | 2.522 |
| 1869 | A | 46,071,003 | 70,415,165 | 0.654 | 46,731,962 | 67,402,170 | 0.693 | 13,714,439 | 8,398,970 | 1.633 |
| 1870 | A | 81,603,551 | 74,814,339 | 1.091 | 42,818,146 | 71,237,603 | 0.601 | 10,388,256 | 9,462,940 | 1.098 |
| 1871 | A | 81,609,377 | 96,092,971 | 0.849 | 56,650,930 | 86,947,482 | 0.652 | 20,100,589 | 11,843,656 | 1.697 |
| 1873 | A | 122,238,657 | 128,011,281 | 0.955 | 73,129,110 | 127,514,594 | 0.573 | 21,875,605 | 13,017,730 | 1.680 |
| 1877 | B | 99,643,116 | 99,327,962 | 1.003 | 99,755,430 | 96,300,483 | 1.036 | 14,690,553 | 12,548,451 | 1.171 |
| 1880 | C | 90,223,603 | 86,489,747 | 1.043 | 74,154,705 | 71,787,349 | 1.033 | 14,897,182 | 14,138,849 | 1.054 |
| 1882 | C | 118,788,666 | 119,419,500 | 0.995 | 114,197,374 | 112,648,927 | 1.014 | 21,853,171 | 21,708,837 | 1.007 |
| 1883 | C | 133,157,261 | 132,254,022 | 1.007 | 122,964,635 | 123,137,019 | 0.999 | 23,045,219 | 23,172,309 | 0.995 |
| 1884 | C | 121,618,596 | 116,397,043 | 1.045 | 113,839,699 | 108,180,644 | 1.052 | 21,348,057 | 20,164,963 | 1.059 |
| 1885 | C | 108,424,754 | 108,941,486 | 0.995 | 102,395,877 | 102,710,019 | 0.997 | 19,026,263 | 19,133,559 | 0.994 |
| 1887 | C | 109,898,802 | 112,892,236 | 0.973 | 105,979,620 | 105,639,428 | 1.003 | 22,447,278 | 22,469,706 | 0.999 |
| 1889 | C | 115,901,299 | 115,224,931 | 1.006 | 110,366,117 | 109,673,447 | 1.006 | 23,392,744 | 23,784,523 | 0.984 |
