# Phase 3 Latest CI Checkpoint — 27 October 2026

## Current verified code checkpoint

- **Repository:** `tarunsharma2610-del/tradepro-improved`
- **Branch:** `phase3/cross-broker-gst-ipft-resolution`
- **Latest code/test commit:** `855fcf68cb3202f09e3a2f98cecb99ce57240728`
- **Backend CI:** [#40456029280 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40456029280)
- **Test result:** 1,077 passed, 1 warning.
- **Latest documentation synchronization:** 20 maintained documents updated. Exact-head CI for the final documentation commit is pending; do not mark the documentation checkpoint green until that run completes.

## Work completed in this increment

1. **DP/demat accounting integrated into live-fill charge validation.** `LiveFillChargeBreakdown` supports an optional DP amount, validates finite/non-negative paise precision, and includes DP in the total only when an amount is explicitly supplied.
2. **Delivery-sell promotion requires DP evidence.** Equity-delivery SELL requires a reviewed, verified and reconciled canonical DP snapshot and a durable allocation for that exact fill. Missing DP snapshot/allocation fails closed before any execution or position mutation.
3. **Component-specific eligible-fill manifests.** Canonical snapshot materialization now validates fill manifest/weights per canonical component, so DP can apply only to eligible delivery sells without forcing brokerage, STT, GST and other components to share the same fill population. Contributing rows combined into one component (such as split transaction charges/IPFT) must still agree.
4. **DP allocations can be reconciled.** Removed the former hard block on promoting a reviewed DP canonical allocation set after the execution persistence and total calculation paths were added.
5. **Execution total and status.** DP is persisted in `Execution.demat_transaction_charges`; status is `KNOWN` for a sourced amount and `NOT_APPLICABLE` when not applicable. DP is included in `total_charges` exactly once. Replay comparison includes DP amount and status; incomplete or conflicting amounts cannot be treated as exact replay.
6. **Tests.** Added a synthetic delivery-sell promotion with reconciled DP, a missing-DP rejection test, paise precision tests, and a DP-only subset-manifest test. One initial run had a stale error-message assertion (1,076 passed); that assertion was corrected before the successful run #40456029280.

## Verified CI gates on code head 855fcf6

- Backend test suite: PASS (1,077 passed, 1 warning).
- Broker-write boundary guard: PASS.
- SQLite migration upgrade/downgrade/re-upgrade: PASS.
- PostgreSQL 16 migration upgrade/downgrade/re-upgrade: PASS.
- Synthetic PostgreSQL + document-volume restore drill: PASS.
- Restore evidence retention step: PASS.

## Remaining Phase 3 gates

- Verify exact-head CI for the final synchronized documentation commit.
- Continue component-by-component accounting acceptance: exact fill identities, paise totals, source-to-canonical mapping, idempotent replay, conflicting replay and atomic rollback.
- Independently review effective-dated tariff/tax rules and the GST taxable-base implementation. Public rule research and estimates do not substitute for actual invoice-level acceptance.
- Keep real contract-note acceptance and real Oracle backup/restore acceptance deferred until genuine evidence and deployment backups exist; synthetic restore passing is not a real production restore.
- Review DP treatment for every relevant segment/product and confirm the API/UI consistently marks incomplete totals.
- Continue SQLite/PostgreSQL regression and broker-write safety checks after each code increment.

## Explicit safeguards

- PR #6 and PR #7 remain Draft/unmerged.
- PAPER mode is mandatory; live broker order writes remain disabled.
- Do not enable automatic live-fill promotion/scheduling as part of this work.
- Work only in `tarunsharma2610-del/tradepro-improved`. The original `tarunsharma2610-del/Tradepro` repository is out of scope and must not be modified.
- GST/IPFT work is not being restarted. Continue from the DP/demat accounting step above.
