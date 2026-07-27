# Why a correct block delivers nothing: the groupfix gate, instrumented

Session 11, iteration 65 (2026-07-27). **The deliverable is instrumentation, not
a commodity. Baseline unchanged: exact01 2,823, 53.8% GBP; `diffcells` reports
zero cells moved, so the patch is behaviour-neutral.**

## Why this instead of the next commodity

Two iterations running produced arithmetically-correct blocks that delivered
nothing:

```
iteration 63  caoutchouc 1885/1887   predicted 0.991 / 0.998   got 0.384 / 1.014
iteration 64  flax 1872              predicted 0.9985          got ZERO cells moved
```

Both were reverted. Three commodity-years lost to guessing at an invisible gate —
the same argument that made the boundary detector the right pick in iteration 58.

## What was added

`integrate_sources.py` now counts every selected row's disposition per repair and
writes `reports/groupfix_rejects.csv`:

```
volume, article_group, article, seq_start, seq_end, obs_source, target_sig,
selected, admitted,
drop_null_qty, drop_subtotal, drop_bad_subentry, drop_no_sig,
drop_consensus_holds_triple, drop_already_added
```

and prints, at the end of the run, every non-supersede repair that admitted
**nothing**, with its dominant reason. On the current corpus that is 6 of ~380
repairs, each with an obvious cause (`drop_subtotal`, `drop_already_added`).

## It answered both failures on first use

### Flax 1872 — `seen_added` dedupes the segments against each other

```
FISH | FLAX, Dressed       624-629   selected 6   admitted 6
FISH | Rough or Undressed  630-637   selected 8   admitted 2   drop_already_added 6
FISH | Tow or Codilla of   638-642   selected 5   admitted 0   drop_already_added 5
```

All three segments target the same commodity, so they share a `target_sig` — and
they share countries by construction, because each is the same country list for a
different sub-sort. `seen_added` is keyed on `(sig, country, year)`, so the second
and third segments' Russia, Germany, Holland and Belgium are dropped as
duplicates of the first's.

> **A commodity assembled from several printed sub-sort tables cannot be built by
> admitting several blocks.** The gate that stops a comparative re-admitting a
> country the vote already carries also collapses the *legitimate* repetition of
> a country across sub-sorts, which must be **summed**, not deduped.

### Caoutchouc 1885 — the seq range spans several `article` values

```
as_1885 CAOUTCHOUC (null article)  seq 246-271   selected 4   admitted 3
```

Four rows selected from a range holding twenty-six. The repair's SELECT matches
`article IS NOT DISTINCT FROM ?`, and inside that one seq range the parser has
written **three different articles** — `NULL` for 246-249, `West Africa` for
250-251, `East Coast of Africa` for 252-272. A repair row fetches one of them.

That is the whole of iteration 63's 0.384: the year got the four-row NULL-article
fragment and nothing else.

> **A `row_seq` range is not a block.** Check `SELECT DISTINCT article` over the
> range before writing the row, and compare `selected` against the number of rows
> actually in the range — the audit file now makes that a one-line check.

## What this changes about the two blocked commodities

- **Flax 1872** is not repairable as three blocks. Either the three sub-sorts are
  folded into one commodity upstream (a taxonomy decision), or `seen_added` needs
  to distinguish "same country, different printed sub-sort" from "same country,
  re-admitted twice" — which it cannot do on `(sig, country, year)` alone.
- **Caoutchouc 1885/1887** *is* repairable: it needs one repair row per `article`
  value in the range, not one per year. That is a straightforward retry, and the
  audit file will confirm `selected` matches the block before anything is
  measured.

## Rule

> Before applying a block repair, predict `selected` and `admitted`. After
> applying, read `reports/groupfix_rejects.csv` **before** reading the baseline.
> A repair whose `selected` is smaller than the block, or whose
> `drop_already_added` is non-zero, has not done what the note says it does —
> whatever the ratio happens to show.
