# Export / Re-export Campaign Plan

*Drafted 2026-07-23, at the close of the import QC campaign (round 26, HEAD 8d29610).
Approved scope decision pending; nothing in this plan has been started.*

## Goal

Bring UK **exports (British produce)** and **re-exports** to the same evidentiary
standard as the imports dataset: country-level series 1872–99 that reconcile to
the T1 national abstracts through arithmetic proof (member sums == printed
subtotals == T1), with slips, glue blocks, and phantom columns repaired, and
coverage measured by the canonical baseline script.

**Finish line (recommended):** the top ~30 export commodity families (≈85% of
export T1 GBP) reconcile at-or-better than the import baseline
(`scripts/reconcile_baseline.py`, 2026-07-23 canonical: 31.4% of GBP within
0.1%, 46.6% within 5%). Do **not** chase the small-commodity tail to import
parity — it is the back 40% of effort for ~15% of value.

## What we start with

| layer | imports | exports | re-exports |
|---|---|---|---|
| raw country rows (Chandra) | 172k | **256k** | 128k |
| T1 abstract lines | 73k | 43k | 45k |
| two-engine consensus | yes | **no** (see defect below) | unknown |
| in country_year_final | fully audited | partial, untagged | absent |
| gold transcriptions | 1,456 cells | none | none |

Already done on the export side (rounds 19–26): cotton piece goods **Plain
1872–87** complete with exact closures; **Printed 1878–87**; ~70 slip-repaired
blocks (coals, woollens, linens, glass, arms, paper, iron pig, soap, leather);
the round-22 mechanized slip audit exists as a rebuildable script; 253
export_uk rows already in `reference/group_repairs.csv`; integrate step 6b
already admits export_uk manual rows.

### The two structural defects

1. **Export pairing defect** (round 19): Infinity reads export country columns
   as one run-on string, so consensus never fires; final rides on twoup parses
   that the round-22 sweep showed were *pervasively slipped one row* (every
   country wearing its predecessor's value). Chandra obs blocks are often
   correctly paired but single-engine.
2. **Flow blindness** (round 24): `country_year_final.flow` says 'import' for
   every row; export rows are mixed in untagged, and export articles sharing a
   token sig with an import commodity get guard-blocked (the linen-yarn-1894
   case).

### On the absence of gold data

Gold mattered early (engine accuracy measurement); the campaign's operative
standard became **arithmetic proof**, which is flow-agnostic and fully
available here: printed member/subtotal/grand closures, multi-volume T1
majority, cross-print comparative arbitration (1893–99 volumes are 3
independent typesettings per cell), cross-engine digit arbitration, 600dpi
page adjudication, bracket tests, rate sanity. Optional cheap substitute for
calibration: a **stratified mini-gold** — hand-key ~20 export tables (~500–800
cells) from page images across eras/commodities as an acceptance test
(1–2 sessions, can be done by Claude from the PDFs in `pdfs/`).

## Phases

### Phase 0 — flow-aware architecture (1–2 sessions)
- Real `flow` column through `country_year_final`; flow-aware sigs and guards
  in `integrate_sources.py` (kills the cross-flow guard-block class).
- Per-flow viz payloads; detectors A–D run per flow.
- **Export T1 cleanup pass**: the export abstracts are messier than imports —
  era-split labels, aggregate 'TOTAL OF …' lines, garbles (there is a £2.2B
  5-year 'PERFUSION CAPS' label that is certainly a piece-goods misparse).
  Canonicalize labels, clamp junk, build the export commodity-family map.
  Without clean T1 anchors nothing downstream is provable.
- Extend `flow_repairs.csv` / repair vocabulary to reexport flow.

### Phase 1 — recover a second engine for exports (1–2 sessions)
- Parse the Infinity run-on country strings into paired rows (round 19 already
  used them as authoritative label lists; the digits are present in the raw
  text). Even partial success restores consensus voting for the biggest tables.
- Where only Chandra pairs: closure + neighbour-bracket machinery substitutes
  (rounds 20–24 pattern).
- Same diagnosis pass for re-export parses (state unknown).

### Phase 2 — mechanized sweep (1–2 sessions)
- Generalize the round-22 twoup-slip audit (agree%/valhit% vs obs, closure vs
  printed TOTAL and T1) plus the round-23 **value-column integrity check**
  (self-consistent phantom value columns pass closure; anchor on inf TOTALs,
  T1 value majority, cross-year rate) across *all* export blocks, all years.
- Auto-admit what passes both gates; queue the rest ranked by GBP.
- On imports this auto-verified roughly half the flagged blocks; expect similar.

### Phase 3 — the queue campaign (8–15 sessions)
- Work the ranked queue exactly like import rounds 19–26: per-block
  arbitration, label_shift repairs, supersede-then-hijack discipline,
  cherry-picked comparative seqs, page adjudication for correlated misreads.
- The 1893–99 comparative era will contain CARDS-chimera-class glue (the
  LEAD|'Piece Goods, Plain, Unbleached or Bleached' 460-row blocks in
  as_1898/99 are already scoped: ~60 destinations × 5 years × 3 prints).
  The round-26 cocoa playbook applies directly: locate own-year tables first,
  then cross-print majority + closure, then 600dpi pages.
- Value concentration to exploit: cotton piece-goods family, iron & steel,
  woollens/worsteds, yarns, coal ≈ top of the GBP ranking; top-25 labels ≈
  55% of export T1 GBP even before family-folding.

### Phase 4 — re-exports (3–5 sessions)
- Smaller universe (£9.5B T1 GBP vs £35.6B exports; 128k rows).
- Head start: the import campaign already identified many misfiled re-export
  tables (currants, sugar refined, molasses, skins, perfumed-in-bond…) —
  every one is *found data* for this flow, with its printed totals already
  matched to T1 reexport.
- Same sweep + queue mechanics.

### Ongoing
- Re-run `scripts/reconcile_baseline.py` per flow at each phase boundary;
  the per-flow numbers are the campaign's progress metric.
- Keep the import-side stopping rule: no open unadjudicated flag above ~£10M.

## Effort summary

| phase | sessions (est.) | deliverable |
|---|---|---|
| 0 architecture + T1 cleanup | 1–2 | flow-aware pipeline, clean export anchors |
| 1 export pairing recovery | 1–2 | second engine / consensus for exports |
| 2 mechanized sweep | 1–2 | ~half of export volume auto-verified |
| 3 export queue campaign | 8–15 | top-30 families at import-baseline quality |
| 4 re-exports | 3–5 | same standard, smaller universe |
| (optional) mini-gold | 1–2 | 500–800-cell acceptance benchmark |

**Total: roughly 15–25 sessions.** Phases 0–2 (~4 sessions) are the cheap
information-buying step: after them we will know the true size of phase 3
before committing to it.

## Known hazards (all previously encountered, all have documented fixes)

- Supersede-then-hijack across stale labels and dot-prefixed article variants.
- Self-consistent phantom value columns (closure alone is not proof).
- Three-column tables (Yards + Lbs + GBP) where an engine stores Lbs as value.
- Re-export/import misfiling in both directions (check flow before believing
  a weird origin/destination pattern).
- Generic-token sig collisions (the 'Other Sorts' class) blocking re-adds.
- S-form 8, broken-4, damaged-9 glyph plagues in the mid-1890s volumes;
  compositors copy prior-volume comparatives, so print-majorities can share
  one inherited error — closure outranks majority.
- `manual_rows.csv` must be append-only (legacy rows break DictWriter rewrites).

## Decision needed before starting

1. Go/no-go on the campaign at all, and whether re-exports are in scope.
2. Accept the recommended finish line (top-30 families) or set another.
3. Whether to commission the mini-gold benchmark first.
