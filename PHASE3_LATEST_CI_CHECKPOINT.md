# Phase 3 — Latest CI Checkpoint

**Checkpoint date:** 25 October 2026  
**Repository:** `tarunsharma2610-del/tradepro-improved`  
**Branch:** `phase3/durable-per-fill-charge-allocation`  
**PR:** #6 — open, draft, unmerged

## Latest verified implementation
- **Commit:** `07df26a88d5eb9cbebc76a5654e10e00e38de171`
- **Backend CI:** [Run #40204137793 — completed successfully on that exact commit](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40204137793).
- **Failure fixed:** PostgreSQL rejected the complete durable reconciliation reference because `broker_charge_allocations.reconciliation_reference` was limited to 200 characters.
- **Fix:** model column widened to 320 characters; migration `202610250026_widen_charge_reconciliation_reference.py` added. Downgrade refuses to truncate any reference longer than 200 characters.
- **Result:** exact-head Backend CI passed, including PostgreSQL concurrent-promotion coverage and configured backend gates. This verifies the implementation commit, not this documentation checkpoint commit.

## Phase 3 status
Implemented and previously verified: normalized canonical source links; immutable reviewed snapshots; split transaction + IPFT provenance; durable per-fill allocation persistence; canonical ledger verification; deterministic paise allocation; promotion/replay checks; tampered-allocation rejection; rollback assertions; incomplete-fill-set rejection; PostgreSQL concurrent-promotion coverage.

**Next step:** after this documentation checkpoint's CI is green, audit existing coverage for any real conflicting-set/rollback gap. Add tests only for demonstrated gaps, then run the full backend CI gate.

## Required checkpoint protocol
After every CI run, refresh PR head and inspect that exact run. On failure, diagnose full logs, fix root cause and rerun. On success, update all 14 designated checkpoint documents with exact SHA/run/result/next step, commit the checkpoint, then verify CI on that checkpoint commit. Never inherit a parent's green result as proof a child commit is green.

## Safeguards
Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched. PR #6 stays draft/unmerged absent explicit authorization. PAPER mode is mandatory and live broker order writes remain disabled. Production GST/IPFT tariff acceptance is a separate evidence gate; unapproved tariff candidates remain DRAFT.
