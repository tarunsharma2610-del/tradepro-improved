## Canonical checkpoint reconciliation — 25 October 2026 (end-of-day verified checkpoint)

- **Work only in:** `tarunsharma2610-del/tradepro-improved`, branch `phase3/durable-per-fill-charge-allocation`. Never modify original `tarunsharma2610-del/Tradepro`.
- **End-of-day verified commit:** `075b16af03cf6be4897c381378f68db76a6cbba6`. Branch head matched this SHA.
- **Exact-head Backend CI:** [Run #40211145592 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40211145592), completed 25 October 2026 at 16:21:33 UTC (21:51:33 India time) on this exact SHA.
- **PR #6:** open, draft, unmerged. Do not merge without explicit user approval.
- **Completed:** PostgreSQL concurrency acceptance for two concurrent promotions of one reviewed component racing verification; 25 maintained documents synchronized; root charge-source register marked legacy duplicate, with `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md` canonical.
- **Verified CI gates:** Backend pytest, broker-write safety boundary, SQLite/PostgreSQL 16 migration upgrade-downgrade-re-upgrade, synthetic PostgreSQL/document-volume restore drill. Synthetic restore does not prove actual Oracle Cloud recovery.
- **NEXT STEP — resume here only:** integrate canonical snapshot allocation/reconciliation into `live_fill_accounting_service`. Current accounting still verifies raw source-component rows through the legacy six-row ledger. Audit existing canonical APIs first, then implement a fail-closed end-to-end path for reviewed source evidence, including combined/split transaction/IPFT, exact replay, complete totals, and rejection of extra/unmapped components. Add focused tests only for integration gaps; do not repeat completed concurrency work or duplicate existing tests. Never silently drop/double-count charges or add generic quantity/notional allocation.
- **Remaining Phase 3 gates:** (2) authentic effective-dated tariff applicability; (3) approved component-specific per-fill allocation rules; (4) invoice/source-backed GST/IPFT/component acceptance; (6) final adversarial, migration, and recovery review; (7) exact-head docs/sign-off. Keep candidates DRAFT absent authentic applicable evidence and independent review.
- **Upstox safeguards:** no unused SDK runtime dependency; Agent Skill static-review-only; brokerage calculator estimate-only; aggregate charge API is not per-fill actual evidence.
- **Trading safeguards:** PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling disabled.
- **Resume protocol:** check branch head and latest CI first, then read this checkpoint plus Phase 3 roadmap/instructions. Continue from the next step above; do not restart completed work. Every new commit requires its own exact-head CI before being called verified.
- **Documentation-sync note:** this records the verified state of `075b16a`; any subsequent documentation commit must receive its own exact-head CI before implementation resumes.

---


# Phase 3 — Latest CI Checkpoint

**Checkpoint date:** 25 October 2026  
**Repository:** `tarunsharma2610-del/tradepro-improved`  
**Branch:** `phase3/durable-per-fill-charge-allocation`  
**PR:** #6 — open, draft, unmerged

## Latest verified implementation

- End-of-day exact commit: `075b16af03cf6be4897c381378f68db76a6cbba6`.
- Exact-head Backend CI [#40211145592 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40211145592).
- Resume next: integrate canonical snapshot allocation/reconciliation into live-fill accounting, testing split transaction/IPFT, exact replay, complete totals, and fail-closed unsupported-component rejection.
- Do not repeat the completed concurrency acceptance work.


## Phase 3 status
Implemented and previously verified: normalized canonical source links; immutable reviewed snapshots; split transaction + IPFT provenance; durable per-fill allocation persistence; canonical ledger verification; deterministic paise allocation; promotion/replay checks; tampered-allocation rejection; rollback assertions; incomplete-fill-set rejection; PostgreSQL concurrent-promotion coverage.

**Next step:** integrate canonical snapshot allocation/reconciliation with live-fill accounting and add focused end-to-end tests for split transaction/IPFT mapping, exact replay, and rejection of unsupported components. This documentation update requires its own exact-head CI.

## Required checkpoint protocol
After every CI run, refresh PR head and inspect that exact run. On failure, diagnose full logs, fix root cause and rerun. On success, update all 18 maintained checkpoint documents with exact SHA/run/result/next step, commit the checkpoint, then verify CI on that checkpoint commit. Never inherit a parent's green result as proof a child commit is green.

## Safeguards
Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched. PR #6 stays draft/unmerged absent explicit authorization. PAPER mode is mandatory and live broker order writes remain disabled. Production GST/IPFT tariff acceptance is a separate evidence gate; unapproved tariff candidates remain DRAFT.
