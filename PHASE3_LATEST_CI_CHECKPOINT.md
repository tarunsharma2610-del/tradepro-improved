# Phase 3 Latest CI Checkpoint — 27 October 2026

## Latest verified code checkpoint

- **Repository:** `tarunsharma2610-del/tradepro-improved`
- **Branch / PR:** `phase3/cross-broker-gst-ipft-resolution` / PR #7 (Draft, unmerged)
- **Code/test commit:** `fb8ca7bf6653c46e21207fdcfa3b39e6777a0081`
- **Backend CI:** [#40457215343 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40457215343)
- **Test result:** 1,087 passed, 1 warning.
- **Verified gates:** broker-write boundary; SQLite migration upgrade/downgrade/re-upgrade; PostgreSQL 16 migration upgrade/downgrade/re-upgrade; synthetic PostgreSQL + document-volume restore; restore evidence retention.
- **Documentation sync:** This checkpoint is being synchronized with the maintained project docs after the green code run. The final documentation-head CI must pass before the docs checkpoint is called green.

## Latest increment: DP status/completeness hardening

The prior increment integrated optional `demat_transaction_charges` into live-fill validation, execution persistence, totals, API status and replay identity. The latest increment closes an additional fail-open edge case: completeness must not be true merely because the DP status is anything other than `UNKNOWN`.

Updated:
- `Execution.total_charges_complete` now returns true only for a consistent `KNOWN` state with an explicit amount, or `NOT_APPLICABLE` with no amount. Unknown, invalid or inconsistent states fail closed.
- `execution_charge_total_is_complete` applies the same rule.
- Added regressions for invalid status, `UNKNOWN` with amount, `KNOWN` without amount, `NOT_APPLICABLE` with amount, and valid known/not-applicable states.

## DP/demat accounting already implemented

1. DP is an optional canonical component separate from the six core charge components.
2. Canonical snapshot materialization supports component-specific eligible-fill manifests so DP can cover only eligible delivery sells.
3. Delivery SELL requires a reviewed/reconciled DP snapshot and durable allocation for that exact fill; missing DP evidence fails closed before accounting mutation.
4. DP is persisted in `Execution.demat_transaction_charges`, included exactly once in `total_charges`, and included in replay comparison.
5. `KNOWN` and `NOT_APPLICABLE` are distinct from `UNKNOWN`; unresolved totals must not be presented as complete.
6. Canonical DP allocation promotion is supported after independent review and deterministic per-fill allocation verification.

## Remaining Phase 3 gates

- Continue component-by-component accounting acceptance: exact fill identities, paise totals, source-to-canonical mappings, idempotent and conflicting replay, atomic rollback, and segment/product applicability.
- Audit DP manifest eligibility against the actual trade/order segment and side, not only source reviewer-provided fill lists.
- Continue effective-dated tariff and statutory GST valuation review, including taxable-base inclusion, Rule 33 evidence gates, place-of-supply handling, and paise rounding. Public estimate output is not actual invoice-level acceptance.
- Ensure API/UI totals remain visibly incomplete whenever applicability or any required component is unresolved.
- Real contract-note acceptance and production Oracle backup/restore acceptance remain deferred until genuine evidence/deployment backups exist. Synthetic restore passing is not production acceptance.
- Re-run the full safety, migration and restore gates after each code increment and synchronize all maintained docs to the latest green code head.

## Safety / scope invariants

- PR #6 and PR #7 remain Draft/unmerged; do not merge.
- PAPER mode is mandatory. Live broker order writes remain disabled.
- Work only in `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` repository is out of scope.
- No personal contract note is available or required to continue synthetic testing.
- Do not restart GST/IPFT from zero; continue from the accounting acceptance audit.
