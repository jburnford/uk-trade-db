---
description: Work the top queued defect to exact closure or re-queue it with evidence
---

# /next-defect — one queued defect, worked to proof

Re-entrant by design: every iteration rebuilds its own state from disk, so
`/clear` between iterations is free and loses nothing.

## 0. Usage gate (first thing, every iteration)

Run the estimator in the session scratchpad:

```
python3 <scratchpad>/usage_check.py
```

- Exit 0 → under 80%, continue.
- Exit 1 → **at or past 80%. Stop the loop** (`ScheduleWakeup stop:true`) and
  report the estimate. Do not start another item.
- Exit 2 → no anchor. Ask the user for their `/usage` percentage, then
  `usage_check.py anchor <pct>`.

The limit is **not** readable locally — transcripts record consumption only,
with no rate-limit or reset fields. The estimator extrapolates from a
percentage the user read off `/usage`. Treat it as an estimate: re-anchor every
few iterations by asking for a fresh `/usage` figure, and say plainly that it is
an extrapolation whenever reporting it.

## 1. Rebuild state (always, even if you think you remember it)

- Read the `opus-work-plan-to-monday` memory — the ranked open list lives in
  the "FOR FABLE" section; the session logs say what has already been tried.
- Run `git log --oneline -5` and `git status --short`.
- Read the `reports/*_findings.md` for the family you're about to touch. Each
  ends with a "still open" list carrying the proofs.

## 2. Pick exactly ONE item

Take the top item from the ranked open list, with these exclusions:

- **SKIP the cotton/jute yarn series-key change.** It alters `reconcile.py`'s
  `_sig` and re-votes the corpus. Live adjudication only.
- **SKIP anything that changes taxonomy or the vote.** If the item turns out to
  need one, STOP and ask rather than deciding alone.

## 2b. Keep a running note (this is what makes compaction survivable)

Maintain `<scratchpad>/LOOP_STATE.md` — overwrite it, don't append:

```
ITEM: <the one item>
ESTABLISHED: <each proof as it lands, with the numbers>
REJECTED: <hypotheses killed, so they aren't re-tried>
NEXT: <the immediate next step>
```

**Update it the moment a proof lands, not at the end of the iteration.** The
between-iteration handoff is already safe (step 1 rebuilds from disk); the real
exposure is compaction landing mid-iteration, after the analysis and before the
report. A proof that exists only in context is one compaction away from being
re-derived from scratch.

Keep bulk out of context: dump wide query results to the scratchpad and read
back only the rows that matter. In step 1, read the plan memory's ranked list
and the most recent session log — not the whole file, which is long and grows.

## 3. Work it

Guardrails, all learned the hard way — see the "Hard guardrails" section of the
plan memory:

- **Exact closure or queue it.** Never guess a digit. Never accept a subset-sum
  closure reached by trying many combinations — coincidence risk is real.
- **Closure outranks print-majority** (compositors copy prior volumes).
- **Raw text first.** Check what the page actually says before theorising.
- A screen tripping is not evidence (the tallow export-table suspicion was
  wrong — 2 export-ish names out of 22).
- Append-only on reference CSVs; quote note fields containing commas.
- `map_slim.json`'s per-year array is `[value, quantity, rank]` — **value first**.

If the item does not close, that is a result. Re-queue it with the evidence
that defeated it — a negative result recorded is worth more than a silent skip.

## 4. Close the iteration (all four, every time)

1. Append findings to the relevant `reports/*_findings.md`.
2. Run `scripts/reconcile_baseline.py` and record the number.
3. Commit with a round-style message. **Do not push.**
4. Append a one-paragraph entry to the plan memory's session log.

## 5. Report

Three lines: **item / outcome / baseline.** Then stop and wait.
