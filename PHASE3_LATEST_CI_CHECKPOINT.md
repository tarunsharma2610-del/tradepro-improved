# Phase 3 Latest CI Checkpoint — 27 October 2026

## Latest verified code checkpoint

- **Repository:** `tarunsharma2610-del/tradepro-improved`
- **Branch / PR:** `phase3/cross-broker-gst-ipft-resolution` / PR #7 (Draft, unmerged)
- **Code/test head:** `b0d6262f77da1b803bc3e95a178d46a5ff8f2d44`
- **Backend CI:** [#40458015093 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40458015093)
- **Test result:** 1,091 passed, 1 warning.
- **Verified gates:** broker-write boundary; SQLite migration upgrade/downgrade/re-upgrade; PostgreSQL 16 migration upgrade/downgrade/re-upgrade; synthetic PostgreSQL + document-volume restore; restore evidence retention.

## Documentation synchronization

Existing maintained project documents were synchronized after the green code result, including handover, progress, master roadmap, project instructions, audit, architecture, requirements, changelog, roadmap, security, GST/IPFT acceptance/research/source registers, README, safeguards, Upstox evidence, Bhav audit, and the Algory AI-integration plan.

- Last multi-document synchronization commit: `5bec10c28a51cbe56def43fd606c086335532732`
- This checkpoint refresh is the final documentation commit for the current increment. Exact-head CI must pass on this final checkpoint commit before the documentation head is marked green.
- PR #7 description has been updated to reflect DP integration and the latest code CI; PR remains Draft/unmerged.
- Three candidate root paths (`TARIFF_RULE_SOURCE_REGISTER.md`, `SECURITY_AUDIT.md`, `PHASE3_ACCOUNTING_ACCEPTANCE.md`) were not present and were not created.

## Latest increment: DP status and manifest eligibility

- `Execution.total_charges_complete` and `execution_charge_total_is_complete` now return complete only for a consistent `KNOWN` state with an explicit amount, or `NOT_APPLICABLE` with no amount. Unknown, invalid or inconsistent states fail closed.
- DP canonical manifests are validated against the persisted broker trade → child order → local order mapping. Every manifest fill must belong to the reviewed broker connection, and both trade and local order must be SELL with the order segment `EQUITY_DELIVERY`.
- Added regressions for invalid/inconsistent DP status/amount pairs, plus DP manifest rejection for BUY trades, intraday orders and mismatched order/trade sides, and acceptance of a correctly mapped delivery SELL.

## DP/demat accounting already implemented

1. DP is an optional canonical component separate from the six core charge components.
2. Canonical snapshot materialization supports component-specific eligible-fill manifests so DP can cover only eligible delivery sells.
3. Delivery SELL requires a reviewed/reconciled DP snapshot and durable allocation for that exact fill; missing DP evidence fails closed before accounting mutation.
4. DP is persisted in `Execution.demat_transaction_charges`, included exactly once in `total_charges`, and included in replay comparison.
5. `KNOWN` and `NOT_APPLICABLE` are distinct from `UNKNOWN`; unresolved totals must not be presented as complete.
6. Canonical DP allocation promotion is supported after independent review and deterministic per-fill allocation verification.

## Remaining Phase 3 gates — next work

1. Continue component-by-component accounting acceptance: exact fill identities, paise totals, source-to-canonical mappings, idempotent and conflicting replay, atomic rollback, and segment/product applicability.
2. Continue effective-dated tariff and statutory GST valuation review, including taxable-base inclusion, Rule 33 evidence gates, place-of-supply handling, and paise rounding. Public estimate output is not actual invoice-level acceptance.
3. Ensure API/UI totals remain visibly incomplete whenever applicability or any required component is unresolved.
4. Real contract-note acceptance and production Oracle backup/restore acceptance remain deferred until genuine evidence/deployment backups exist. Synthetic restore passing is not production acceptance.
5. Re-run safety, migration and restore gates after every code increment and synchronize maintained docs to the latest green code head.

## Safety / scope invariants

- PR #6 and PR #7 remain Draft/unmerged; do not merge.
- PAPER mode is mandatory. Live broker order writes remain disabled.
- Work only in `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` repository is out of scope.
- No personal contract note is available or required to continue synthetic testing.
- Do not restart GST/IPFT from zero; continue from the accounting acceptance audit.
