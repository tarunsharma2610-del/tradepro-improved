# Phase 3 — Latest CI Checkpoint

**Checkpoint date:** 25 October 2026  
**Repository:** `tarunsharma2610-del/tradepro-improved`  
**Branch:** `phase3/durable-per-fill-charge-allocation`  
**PR:** [#6 — open, draft, unmerged](https://github.com/tarunsharma2610-del/tradepro-improved/pull/6)

## Latest verified implementation/test head
- Commit: `3d8c4e1425825e6b996500ce9f24630d6352ff5e`
- Backend CI: [Workflow #40200645237](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40200645237) — completed successfully on that exact commit.
- Passing gates: pytest; broker-write boundary enforcement; SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade; synthetic PostgreSQL/document-volume restore drill.
- Latest regression test: `test_canonical_reconciliation_rejects_incomplete_allocation_fill_set` in `backend/tests/test_broker_charge_canonical_component_snapshot_service.py`. Removing one allocation from a two-fill canonical set blocks promotion; the remaining row stays pending with no reconciliation reference.

## Current state and next step
Implemented already: normalized source links, immutable reviewed canonical snapshots, split transaction + IPFT provenance, durable per-fill allocation persistence, canonical ledger verification, deterministic paise allocation, promotion/replay checks, tampered-allocation rejection, rollback assertions, and incomplete-fill-set rejection.

**Next single implementation step:** add PostgreSQL concurrent-promotion coverage. Assert concurrent promotion attempts leave the complete set in one consistent state with one durable reconciliation reference and never produce partial/mixed promotion. Inspect existing coverage first; add conflicting-set/rollback tests only if there is a verified gap. Then run the full backend CI gate.

## Mandatory checkpoint rules
After every CI run: failure → diagnose, fix, rerun; success → update all 13 documents with exact SHA/run/result and next step, commit the checkpoint, and verify CI on that checkpoint commit. Never call a checkpoint commit green based only on its parent’s run. Before resuming, refresh the live PR head and use documents from that exact SHA.

## Safety
Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` stays untouched. PR #6 remains draft/unmerged unless explicitly authorized. PAPER mode mandatory; live broker order writes disabled. Production GST/IPFT tariff acceptance remains separate; synthetic engineering tests may continue. Unapproved tariffs remain DRAFT.

**CI scope warning:** workflow #40200645237 verifies implementation commit `3d8c4e1425825e6b996500ce9f24630d6352ff5e`, not any later documentation checkpoint commit. The documentation commit needs its own exact-head CI verification.
