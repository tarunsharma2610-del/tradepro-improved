## Canonical checkpoint reconciliation — 25 October 2026

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **PR #6:** open, draft, unmerged.
- **Latest verified implementation/documentation base before this synchronization:** `fee15a546ebbdfba9fdbb6040cfe5550d5cdac43`. Backend workflow [#40206354866](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40206354866) completed successfully on that exact commit.
- This synchronization corrects stale checkpoint references and aligns maintained documents to that verified base. The new documentation-sync commit must receive its own exact-HEAD CI run; the run above does not validate a later commit.
- **Phase 3 next step after this docs checkpoint passes CI:** inspect existing conflicting-fill-set and rollback coverage for a demonstrated acceptance gap; add only missing coverage, then run the full backend CI gate. Do not duplicate existing PostgreSQL concurrency, incomplete-fill-set, promotion atomicity, or rollback tests without a concrete uncovered case.
- **Upstox decisions:** API/SDK and Agent Skill audits are included in the canonical inventory. No unused SDK runtime dependency is approved; Agent Skill remains static-review-only and must not be executed or given live credentials. Brokerage calculator output is estimate-only; aggregate charge endpoints are not per-fill actual evidence.
- **Safeguards:** original `tarunsharma2610-del/Tradepro` is out of scope and must remain untouched; PAPER mode mandatory; live broker order writes disabled; GST/IPFT/tariff candidates remain DRAFT until authentic, applicable evidence and independent review support approval.

---


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
After every CI run, refresh PR head and inspect that exact run. On failure, diagnose full logs, fix root cause and rerun. On success, update all 18 maintained checkpoint documents with exact SHA/run/result/next step, commit the checkpoint, then verify CI on that checkpoint commit. Never inherit a parent's green result as proof a child commit is green.

## Safeguards
Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched. PR #6 stays draft/unmerged absent explicit authorization. PAPER mode is mandatory and live broker order writes remain disabled. Production GST/IPFT tariff acceptance is a separate evidence gate; unapproved tariff candidates remain DRAFT.
