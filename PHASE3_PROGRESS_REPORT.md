# Phase 3 Progress Report — Durable Per-Fill Charge Accounting

**Last updated:** 2026-10-25  
**Repository:** `tarunsharma2610-del/tradepro-improved`  
**Branch:** `phase3/durable-per-fill-charge-allocation`  
**Pull request:** [#6](https://github.com/tarunsharma2610-del/tradepro-improved/pull/6) — open, draft, unmerged at last verified status  
**Phase 3 plan:** [`PHASE3_ROADMAP.md`](PHASE3_ROADMAP.md)  
**Phase 3 rules:** [`PHASE3_INSTRUCTIONS.md`](PHASE3_INSTRUCTIONS.md)

## Current checkpoint — be precise about the CI boundary

- Latest previously verified implementation HEAD: `97843aec1d9b0acc4d55d0fc4529b4ea5b81fd50`.
- Exact-HEAD workflow [#40187635881](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40187635881) completed successfully on that SHA. Reported suite: **907 passed, 1 warning, 0 failures**.
- The run covered the backend test workflow, including broker-write boundary checks, SQLite/PostgreSQL migration round-trips and synthetic database/document-storage restore checks, according to the recorded checkpoint. Synthetic restore is not proof of real Oracle Cloud backup recovery.
- This report and the new Phase 3 roadmap/instructions are documentation changes after that implementation HEAD. **Do not treat run #40187635881 as CI for later documentation commits.** Exact-head CI for the latest documentation HEAD must be checked before calling the current HEAD green.
- The latest previously checked PR state was open/draft/unmerged. Recheck before relying on that status after further work.
- PAPER mode remains mandatory; live broker order writes, automatic live-fill promotion and automatic scheduling remain disabled. Original `tarunsharma2610-del/Tradepro` is out of scope and must not be modified.

## Status vocabulary

- **CI verified:** exact commit SHA is covered by a successful required workflow.
- **Implemented, verification pending:** code exists but exact-head CI has not yet passed.
- **Evidence/review pending:** implementation or arithmetic exists, but authentic source evidence or independent approval is missing.
- **Complete:** all roadmap acceptance criteria for the gate have passed; docs record evidence and no unacknowledged blockers remain.

Do not infer completion percentages from test count or number of documentation updates. Use the acceptance gates below.

## Gate-by-gate status

| Gate | Status | Evidence / remaining work |
|---|---|---|
| Durable allocation ledger, deterministic paise allocation, source-total reconciliation, replay/conflict controls and review/promotion safeguards | **Implemented; prior CI verified** | Current known exact-head run #40187635881 passed on SHA `97843aec1d9b0acc4d55d0fc4529b4ea5b81fd50`. Reconfirm relevant tests remain enabled in final CI. |
| Source evidence intake and representation validation | **Implemented; source approval pending** | Versioned combined/split IPFT representation, raw-label retention and missing/ambiguous/conflicting input rejection exist. Source-label count validation alone is not proof of one-to-one label → normalized component → amount binding; inspect and close that gap if still present. |
| IPFT combined/split arithmetic | **Policy settled; end-to-end accounting acceptance pending** | NSE circular NSE/FA/73061: cash ₹307.00/crore, futures ₹183.00/crore, options ₹3,553.00/crore combined; split equivalent is ₹306.99+₹0.01, ₹182.99+₹0.01, ₹3,552.99+₹0.01. Do not add IPFT twice. |
| GST taxable composition and invoice reconciliation | **Evidence/review pending** | Working 18% canonical taxable-base policy is documented; authentic invoice/tax-base validation by product, segment and effective date remains open. |
| Effective-dated component tariff rules and actual API/contract-note mapping | **Open** | Tariff candidates remain DRAFT. Verify authentic Upstox field semantics and source provenance. Calculator is estimate-only; Get Trade Charges is aggregate reconciliation evidence, not per-fill actual evidence. |
| Approved component rules wired to durable per-fill allocation | **Open** | Need end-to-end allocation with exact fill manifest, approved component-specific basis, exact source-total reconciliation, no dropped component and no IPFT/GST double count. Generic QUANTITY/NOTIONAL allocation remains disabled unless component-specific rules approve it. |
| Real live-fill service vs allocation verification/promotion concurrency | **Open acceptance gate** | Must test the real `LiveFillAccountingService.promote_trade` and `_load_reconciled_allocation_fees` path against concurrent ledger verification/promotion; a stubbed loader is not enough. Include replay, conflicting fill sets, rollback and no partial execution/position writes. |
| Migrations, adversarial review and restore | **Prior synthetic CI checks passed; final review open** | Recheck SQLite and PostgreSQL 16 upgrade/downgrade/re-upgrade, broker-write boundary, evidence retention and synthetic restore on final HEAD. Actual retained Oracle backup restore is a separate operational check. |
| Dedicated Phase 3 roadmap/instructions/progress reporting | **Created; latest-doc CI pending** | `PHASE3_ROADMAP.md`, `PHASE3_INSTRUCTIONS.md` and this report define gates, safety constraints and update rules. Verify exact current HEAD before marking documentation checkpoint green. |
| Phase 3 sign-off / PR merge | **Not complete** | All acceptance gates and evidence gaps must be reconciled; PR #6 remains draft/unmerged until explicit user approval. No live-trading enablement is included in Phase 3 closure. |

## Next actions — in order

1. **Verify exact latest documentation HEAD and CI.** If any required job fails, diagnose and fix the cause without weakening safeguards; rerun on the resulting HEAD.
2. **Audit source-label binding in code and tests.** Confirm each raw label is bound to the correct normalized component, amount and provenance; add focused adversarial tests only if the gap exists.
3. **Approve evidence-backed, effective-dated component rules and API mappings.** Keep unsupported rules DRAFT and fail closed.
4. **Wire the reviewed rules into per-fill allocation and test combined/split IPFT equivalence and GST no-double-count behavior end-to-end.**
5. **Close GST/invoice reconciliation and component-specific edge cases** (multi-fill brokerage caps, STT/CTT side/product, stamp duty, demat/other charges and effective-date boundaries).
6. **Close the real-service PostgreSQL concurrency/rollback gate** using the actual live-fill accounting path, not test-only stubs.
7. **Run final adversarial review and exact-head CI;** synchronize the progress report, shared checkpoint docs and acceptance matrix after the verified result.
8. **Request explicit user acceptance before any merge.** Do not enable live order writes or automatic promotion.

## Verified step log

| Date | Commit / workflow | Result |
|---|---|---|
| 2026-10-25 | `97843aec1d9b0acc4d55d0fc4529b4ea5b81fd50`; [CI #40187635881](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40187635881) | **Passed:** 907 passed, 1 warning, 0 failures. This result applies to that SHA only. |
| 2026-10-25 | New Phase 3 roadmap and instruction documents | Committed after the verified implementation SHA; exact-head CI is pending and must be recorded here only after it succeeds. |

## Required update rule for every future successful step

After a code/test step is merged into the working branch (not the PR base) and exact-head CI succeeds, append a dated row to this report containing:
- what changed and the acceptance criterion it closes;
- implementation/test commit SHA;
- exact workflow URL and conclusion;
- test pass/fail/skip/warning counts and confirmation that PostgreSQL-specific tests ran;
- any evidence limitation that remains;
- the next single concrete action.

If CI fails or is still running, update status to **verification pending/failed** with the exact SHA and run link; never mark the gate complete. Do not backfill success from a different commit or repeat a completed step as if new work.

## 2026-10-25 implementation checkpoint — explicit source-label association

**Status: implemented; exact-head CI verification pending.**

- Changed `backend/app/services/broker_charge_representation_contract.py` to require an explicit `labels_by_component` association, with exact component-key coverage, non-empty/unique labels and consistency with retained raw-label order.
- Changed `backend/app/api/v1/broker_charge_evidence.py` to pass the explicit component-to-label mapping derived from each persisted source-component row during review validation.
- Added regression coverage in `backend/tests/test_broker_charge_representation_contract.py` for missing associations, wrong component sets and inconsistent label mapping/order.
- Implementation commits: `79dd66d8c429498501e9edfb35e73a1ca0b756b4`, `0146ecd75f0e6a625b21761d3195c896bba293f7`, `fb147a3c5580091574bc71c35e7a641cf7386935`.
- Current implementation HEAD at time of entry: `fb147a3c5580091574bc71c35e7a641cf7386935`. No CI result for this exact HEAD has been verified yet; do not mark the gate complete until the exact-head workflow passes.
- Limitation: structural mapping proves which persisted label is associated with a normalized component row; it does not independently authenticate that the transcribed label/amount matches the original contract note. Independent source review remains required.
- Next action: verify exact-head CI, confirm focused tests and API review tests pass, fix any failures without weakening safeguards, then update this report with the successful run and counts.

### CI failure and corrective test-fixture update

- Workflow [#40188703796](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40188703796) on implementation SHA `fb147a3c5580091574bc71c35e7a641cf7386935` **failed** during pytest. The failure was in the new test helper: `zip(..., strict=True)` raised while constructing an intentionally malformed fixture, so the validator was never exercised. This was a test-fixture error, not evidence that the production validator failed.
- Corrective test commit: `e2758ae3db5309641196f0cd0ce035591f6c03ac`; the helper now allows the malformed fixture to reach validation, and the assertion checks the validator's fail-closed component-key error.
- Verification for the corrected commit remains pending until its own CI result is checked. The earlier failed run is retained as history; it is not counted as a successful step.

