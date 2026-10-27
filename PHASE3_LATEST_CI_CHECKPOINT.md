# Phase 3 Latest CI Checkpoint — 27 October 2026

## Verified code checkpoint

- **Repository:** `tarunsharma2610-del/tradepro-improved`
- **Branch / PR:** `phase3/cross-broker-gst-ipft-resolution` / PR #7 (Draft, unmerged)
- **Latest verified code/test head:** `fb8ca7bf6653c46e21207fdcfa3b39e6777a0081`
- **Backend CI:** [#40457215343 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40457215343)
- **Test result:** 1,087 passed, 1 warning.
- **Verified gates:** broker-write boundary; SQLite migration upgrade/downgrade/re-upgrade; PostgreSQL 16 migration upgrade/downgrade/re-upgrade; synthetic PostgreSQL + document-volume restore; restore evidence retention.

## Documentation synchronization

The latest verified code result above was synchronized across the existing maintained Phase 3 documents, including handover, progress, roadmap, project instructions, audit, architecture, requirements, changelog, security, GST/IPFT research and acceptance matrices, Upstox evidence, Bhav audit and the Algory AI integration plan. Three candidate root paths (`TARIFF_RULE_SOURCE_REGISTER.md`, `SECURITY_AUDIT.md`, `PHASE3_ACCOUNTING_ACCEPTANCE.md`) were not present and were not created.

- Last multi-document sync commit before this checkpoint refresh: `a02a374414cd7d07ffb66ec28a8a5c6c0d3d9023`
- Final checkpoint refresh is the current commit containing this file. Its exact-head CI must pass before this final documentation checkpoint is treated as green.
- PR #7 description has been updated to reflect DP integration and the current acceptance gates; PR remains Draft/unmerged.

## Latest increment: DP status/completeness hardening

The prior increment integrated optional `demat_transaction_charges` into live-fill validation, execution persistence, totals, API status and replay identity. This increment closed a fail-open edge case: completeness must not be true merely because the DP status is anything other than `UNKNOWN`.

- `Execution.total_charges_complete` now returns true only for a consistent `KNOWN` state with an explicit amount, or `NOT_APPLICABLE` with no amount.
- `execution_charge_total_is_complete` applies the same rule.
- Unknown, invalid or inconsistent states fail closed.
- Added regressions for invalid status, `UNKNOWN` with amount, `KNOWN` without amount, `NOT_APPLICABLE` with amount, and valid known/not-applicable states.

## DP/demat accounting already implemented

1. DP is an optional canonical component separate from the six core charge components.
2. Canonical snapshot materialization supports component-specific eligible-fill manifests so DP can cover only eligible delivery sells.
3. Delivery SELL requires a reviewed/reconciled DP snapshot and durable allocation for that exact fill; missing DP evidence fails closed before accounting mutation.
4. DP is persisted in `Execution.demat_transaction_charges`, included exactly once in `total_charges`, and included in replay comparison.
5. `KNOWN` and `NOT_APPLICABLE` are distinct from `UNKNOWN`; unresolved totals must not be presented as complete.
6. Canonical DP allocation promotion is supported after independent review and deterministic per-fill allocation verification.

## Remaining Phase 3 gates — next work

1. Continue component-by-component accounting acceptance: exact fill identities, paise totals, source-to-canonical mappings, idempotent and conflicting replay, atomic rollback, and segment/product applicability.
2. Audit DP manifest eligibility against the actual trade/order segment and side, not only source reviewer-provided fill lists.
3. Continue effective-dated tariff and statutory GST valuation review, including taxable-base inclusion, Rule 33 evidence gates, place-of-supply handling, and paise rounding. Public estimate output is not actual invoice-level acceptance.
4. Ensure API/UI totals remain visibly incomplete whenever applicability or any required component is unresolved.
5. Real contract-note acceptance and production Oracle backup/restore acceptance remain deferred until genuine evidence/deployment backups exist. Synthetic restore passing is not production acceptance.
6. Re-run safety, migration and restore gates after every code increment and synchronize the maintained docs to the latest green code head.

## Safety / scope invariants

- PR #6 and PR #7 remain Draft/unmerged; do not merge.
- PAPER mode is mandatory. Live broker order writes remain disabled.
- Work only in `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` repository is out of scope.
- No personal contract note is available or required to continue synthetic testing.
- Do not restart GST/IPFT from zero; continue from the accounting acceptance audit.
