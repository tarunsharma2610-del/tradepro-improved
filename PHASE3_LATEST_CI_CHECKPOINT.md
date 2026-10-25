## Canonical checkpoint reconciliation — 25 October 2026 (latest exact-head CI verified)

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **PR #6:** open, draft, unmerged.
- **Latest verified branch head before this documentation sync:** `e9440e2f31f9d4d108b9160608e653efffd2d9fc`. Exact-head Backend CI [run #40210391188](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40210391188) completed successfully on this exact SHA (25 October 2026).
- **Latest verified code/test checkpoint:** `50802e96e06756b57a9f930e0c54c680777922d4`; Backend CI [run #40209741299](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40209741299) passed on that exact SHA.
- **Verified gates:** backend pytest; broker-write safety boundary; SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade; synthetic PostgreSQL/document-volume restore drill. The synthetic restore does not prove actual Oracle Cloud recovery.
- **Concurrency acceptance gap closed:** PostgreSQL coverage races two promotion calls for the same reviewed component alongside verification; both promotions must return the complete allocation set and final reconciled rows must share one durable reference.
- **Next single implementation step:** integrate canonical snapshot allocation/reconciliation end-to-end with live-fill accounting (Phase 3 Gates 1C/5). Current live-fill accounting still validates raw source-component rows through the legacy six-row ledger. Add focused integration coverage for combined/split transaction/IPFT, exact replay, complete totals, and fail-closed rejection of extra/unmapped components. Do not silently drop or double-count charges; do not introduce generic quantity/notional allocation.
- **Remaining gates:** evidence-backed effective-dated tariff selection (Gate 2); approved per-fill rule wiring (Gate 3); invoice/source-backed GST/component acceptance (Gate 4); final adversarial/migration/restore review (Gate 6); final exact-head documentation/sign-off (Gate 7).
- **Upstox controls:** no unused SDK runtime dependency; Agent Skill is static-review-only and must not be executed or supplied live credentials. Brokerage calculator output is estimate-only; aggregate charge endpoints are not per-fill actual evidence. GST/IPFT/tariff candidates remain DRAFT until authentic applicable evidence and independent review support approval.
- **Safety invariants:** original `tarunsharma2610-del/Tradepro` remains out of scope and must stay untouched; PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. Do not merge PR #6 without explicit user approval.
- **Checkpoint protocol:** this 25-file documentation sync must pass CI on its own resulting commit before the next implementation change. Parent-commit CI does not verify a newer SHA.

---


# Phase 3 — Latest CI Checkpoint

**Checkpoint date:** 25 October 2026  
**Repository:** `tarunsharma2610-del/tradepro-improved`  
**Branch:** `phase3/durable-per-fill-charge-allocation`  
**PR:** #6 — open, draft, unmerged

## Latest verified implementation

- **Previously verified exact head:** `e9440e2f31f9d4d108b9160608e653efffd2d9fc`
- **Exact-head Backend CI:** [Run #40210391188 — completed successfully on this exact commit](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40210391188).
- **Verified result:** backend pytest, broker-write boundary guard, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore drill passed.
- **Next step:** canonical snapshot allocation/reconciliation must be integrated with live-fill accounting and tested for split transaction/IPFT, exact replay, complete totals, and unsupported-component rejection.
- **Current documentation sync:** the 25-file update has its own new commit and must pass exact-head CI before implementation work resumes.


## Phase 3 status
Implemented and previously verified: normalized canonical source links; immutable reviewed snapshots; split transaction + IPFT provenance; durable per-fill allocation persistence; canonical ledger verification; deterministic paise allocation; promotion/replay checks; tampered-allocation rejection; rollback assertions; incomplete-fill-set rejection; PostgreSQL concurrent-promotion coverage.

**Next step:** integrate canonical snapshot allocation/reconciliation with live-fill accounting and add focused end-to-end tests for split transaction/IPFT mapping, exact replay, and rejection of unsupported components. This documentation update requires its own exact-head CI.

## Required checkpoint protocol
After every CI run, refresh PR head and inspect that exact run. On failure, diagnose full logs, fix root cause and rerun. On success, update all 18 maintained checkpoint documents with exact SHA/run/result/next step, commit the checkpoint, then verify CI on that checkpoint commit. Never inherit a parent's green result as proof a child commit is green.

## Safeguards
Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched. PR #6 stays draft/unmerged absent explicit authorization. PAPER mode is mandatory and live broker order writes remain disabled. Production GST/IPFT tariff acceptance is a separate evidence gate; unapproved tariff candidates remain DRAFT.
