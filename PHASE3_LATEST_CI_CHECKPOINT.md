# Phase 3 — Latest CI Checkpoint

**Checkpoint date:** 25 October 2026  
**Repository:** `tarunsharma2610-del/tradepro-improved`  
**Branch:** `phase3/durable-per-fill-charge-allocation`  
**PR:** #6 — open, draft, unmerged

## Latest verified implementation
- **Commit:** `07df26a88d5eb9cbebc76a5654e10e00e38de171`
- **Backend CI:** [Run #40204137793 — completed successfully on this exact commit](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40204137793).
- **Failure fixed:** PostgreSQL rejected the complete durable reconciliation reference because `broker_charge_allocations.reconciliation_reference` was limited to 200 characters.
- **Fix:** model column widened to 320 characters; migration `202610250026_widen_charge_reconciliation_reference.py` added. Downgrade refuses to truncate any reference longer than 200 characters.
- **Result:** the exact-head Backend CI passed, including the PostgreSQL concurrent-promotion test and configured backend gates. This verifies the implementation commit, not a future documentation-only commit.

## Phase 3 status
Implemented and previously verified: normalized canonical source links; immutable reviewed snapshots; split transaction + IPFT provenance; durable per-fill allocation persistence; canonical ledger verification; deterministic paise allocation; promotion/replay checks; tampered-allocation rejection; rollback assertions; incomplete-fill-set rejection; PostgreSQL concurrent-promotion coverage.

**Next step:** verify the documentation checkpoint commit's CI. Once green, inspect existing coverage for any actual conflicting-set/rollback gap and add tests only if a gap is demonstrated; then run the full backend CI gate.

## Required checkpoint protocol
After every CI run, refresh PR head and inspect the exact run. On failure, diagnose the full log, fix root cause and rerun. On success, update all 13 designated docs with exact SHA/run/result/next step, commit the checkpoint, then verify CI on that checkpoint commit. Never inherit a parent's green result as proof that a child commit is green.

## Safeguards
Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched. PR #6 stays draft/unmerged absent explicit authorization. PAPER mode is mandatory and live broker order writes remain disabled. Production GST/IPFT tariff acceptance is a separate evidence gate; unapproved tariff candidates remain DRAFT.
