## Canonical checkpoint reconciliation — 25 October 2026 (after exact-head CI)

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **PR #6:** open, draft, unmerged.
- **Latest verified code/test commit:** `50802e96e06756b57a9f930e0c54c680777922d4`. Exact-head Backend CI [run #40209741299](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40209741299) completed successfully on that SHA.
- **Verified:** backend pytest; broker-write boundary enforcement; SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade; synthetic PostgreSQL/document-volume restore drill. The synthetic restore does not prove actual Oracle Cloud recovery.
- **Concurrency acceptance gap closed:** the PostgreSQL test now races two promotion calls for the same reviewed component alongside verification; both promotion calls must return the full allocation set, and the final ledger must contain complete reconciled rows with one consistent durable reference.
- **Next single implementation step:** close the canonical-ledger integration gap (Phase 3 Gates 1C/5). Canonical snapshot materialization/review/allocation/reconciliation services exist, but `live_fill_accounting_service` still verifies raw source-component rows and the legacy six-row source ledger. Audit the intended canonical snapshot path and implement/test a fail-closed end-to-end route from reviewed source rows (including combined/split transaction/IPFT) through canonical snapshot allocation/reconciliation into live-fill accounting. Do not silently drop or double-count extra source components; do not add generic quantity/notional allocation.
- **Remaining gates:** evidence-backed effective-dated tariff selection (Gate 2), approved per-fill rule wiring (Gate 3), invoice/source-backed GST/component acceptance (Gate 4), final adversarial/migration/restore review (Gate 6), and final exact-head docs/sign-off (Gate 7) remain open.
- **Upstox decisions:** no unused SDK runtime dependency; Agent Skill remains static-review-only and must not be executed or given live credentials. Brokerage calculator output is estimate-only; aggregate charge endpoints are not per-fill actual evidence. GST/IPFT/tariff candidates remain DRAFT until authentic applicable evidence and independent review support approval.
- **Safeguards:** original `tarunsharma2610-del/Tradepro` is out of scope and must remain untouched; PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. Do not merge PR #6 without explicit user approval.

---


# Phase 3 — Latest CI Checkpoint

**Checkpoint date:** 25 October 2026  
**Repository:** `tarunsharma2610-del/tradepro-improved`  
**Branch:** `phase3/durable-per-fill-charge-allocation`  
**PR:** #6 — open, draft, unmerged

## Latest verified implementation

- **Commit:** `50802e96e06756b57a9f930e0c54c680777922d4`
- **Backend CI:** [Run #40209741299 — completed successfully on this exact commit](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40209741299).
- **Result:** backend pytest, broker-write boundary guard, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore drill passed.
- **Concurrency acceptance:** two concurrent promotion attempts now race against a verification attempt; both promotions must return the full set and the final ledger must have a consistent durable reference.

## Phase 3 status
Implemented and previously verified: normalized canonical source links; immutable reviewed snapshots; split transaction + IPFT provenance; durable per-fill allocation persistence; canonical ledger verification; deterministic paise allocation; promotion/replay checks; tampered-allocation rejection; rollback assertions; incomplete-fill-set rejection; PostgreSQL concurrent-promotion coverage.

**Next step:** integrate canonical snapshot allocation/reconciliation with live-fill accounting and add focused end-to-end tests for split transaction/IPFT mapping, exact replay, and rejection of unsupported components. This documentation update requires its own exact-head CI.

## Required checkpoint protocol
After every CI run, refresh PR head and inspect that exact run. On failure, diagnose full logs, fix root cause and rerun. On success, update all 18 maintained checkpoint documents with exact SHA/run/result/next step, commit the checkpoint, then verify CI on that checkpoint commit. Never inherit a parent's green result as proof a child commit is green.

## Safeguards
Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched. PR #6 stays draft/unmerged absent explicit authorization. PAPER mode is mandatory and live broker order writes remain disabled. Production GST/IPFT tariff acceptance is a separate evidence gate; unapproved tariff candidates remain DRAFT.
