# Drugs — Unenumerated

## 1874 — closed to 0.99922 (exact01); a 333 residual queued

`Drugs — Unenumerated` 1874 read **0.0000** against a Tier-1 of **427,938**
(modal unit `Value`), a one-year hole bracketed by populated neighbours —
bracketed-gap rank 3, GBP 443,880.

### Why no parse had it: both engines garble the ARTICLE, and differently

Neither `country_obs` nor `country_obs_inf` contains an as_1874 DRUGS block.
The raw text explains it. Chandra reads the head as

    ENVOYS, Unenumerated:

and Infinity reads the same head as

    DYES, Unenumerated:

Both are garbles of **`DRUGS, Unenumerated`**. The identity is settled by
position and by arithmetic, not by the string: the block sits between `CUTCH`
and the Dyeing-and-Tanning-Stuffs section — exactly where DRUGS falls
alphabetically — and its printed `Total` of **427,938** is the Tier-1 anchor to
the digit.

This is the second article-garble case this run after Kowrie's `Kowzie`, and a
worse one. A garbled *article* is invisible to every label-based screen, and
here the two engines garble it **differently**, so even a cross-engine label
match fails. Only the raw page, read positionally, recovers it.

The block is also **value-only** — the quantity column is a literal `-`
throughout — consistent with the Tier-1 unit `Value`.

### The 333 is not guessed

The two engines disagree on four of the ten members:

| Country | Chandra | Infinity | diff |
|---|---:|---:|---:|
| France | 37,216 | 37,416 | +200 |
| Chili | 23,131 | 23,134 | +3 |
| British East Indies | 163,304 | 163,801 | +497 |
| Other Countries | 60,492 | 60,192 | −300 |

Chandra's ten sum to **427,605** (333 short of the printed Total); Infinity's to
**428,005** (67 over). **No combination of the two readings gives 427,938** —
the four differences are +200, +3, +497 and −300, and no subset of them sums to
+333. So either a third cell is misread, or a cell both engines agree on is
wrong, and the arithmetic cannot say which.

Chandra's readings are taken (the primary engine) and the 333 is queued rather
than assigned. The year lands at 427,605/427,938 = **0.99922**, inside exact01
either way — Infinity's list would give 1.00016 — so the metric does not depend
on the unresolved cell, and nothing here rests on a guessed digit.

Ten `manual_rows` written under `DRUGS | Unenumerated` / `Value` / 1874.

### Still open

- The **333**. Resolving it needs an out-of-block test: a third impression of
  the 1874 table, or the same countries' 1875 figures to bound which of France /
  Chili / British East Indies / Other Countries moved.
- Worth a screen: **blocks whose printed Total matches a Tier-1 exactly while
  the article string matches nothing**. That test would have found this block
  without reading the page, and would find the rest of the garbled-article class.
