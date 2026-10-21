# Phase 3 — Contract-note charge allocation contract

Status: design gate; implementation not yet approved.

## Problem

`LiveFillAccountingService` accepts a per-fill charge breakdown and validates that its total equals the six supplied charge components. That validation proves internal arithmetic consistency only. It does not prove that a breakdown represents the broker's actual charges for that fill, nor does it define how a contract-note total covering multiple fills is apportioned.

## Required invariants

1. **No implicit duplication.** A contract-note-level fee total must never be copied in full onto every fill covered by that note.
2. **Evidence provenance.** Each allocated amount must be traceable to a broker contract note, broker/account identity, trade date, and the relevant broker trade/fill identifiers where available.
3. **Explicit basis.** Allocation must use a documented broker-supported basis or a source-provided per-trade breakdown. Do not assume equal-per-fill, quantity, turnover, or proportional allocation without evidence that the selected basis is valid for the charge type.
4. **Currency precision.** Persist INR amounts to paise precision using decimal arithmetic, never binary floating-point arithmetic for fee allocation.
5. **Deterministic residual.** If a valid proportional allocation is explicitly approved, use a deterministic ordering and residual rule so allocated paise sum exactly to the source total. Record the basis and method/version.
6. **Reconciliation.** For every source note and charge component, the sum of allocations must equal the source amount exactly. A mismatch blocks promotion and requires review.
7. **Idempotency.** A unique source-note/component identity must prevent the same source charge from being allocated twice on replay or recovery.
8. **Atomicity.** Allocation records, execution accounting, and live-position updates must commit or roll back together.
9. **Fail closed.** Missing, contradictory, or ambiguous source evidence must block automatic accounting promotion; preserve the evidence and flag manual review rather than inventing a fee split.

## Proposed data boundary

Keep source-level evidence separate from per-fill allocations:

- **Charge source:** immutable source identity, broker/account, note/reference, trade date, currency, source total per charge component, and raw-evidence fingerprint/location.
- **Allocation:** source identity, broker trade/fill identity, allocated component amounts, allocation basis, method version, and reconciliation state.
- **Execution charge snapshot:** the per-fill amounts actually used for accounting, linked to the allocation record and protected by the existing idempotency constraints.

Names and schemas are illustrative; do not implement a migration until repository models, retention policy, and uniqueness constraints are reviewed.

## Allocation policy

- Prefer a broker-provided trade-level fee breakdown when present and validated against the source note.
- Otherwise, require an explicitly approved allocation basis for each charge component. Different components may require different bases.
- If no valid basis is documented for a component, leave it unallocated and block automatic promotion for the affected accounting operation.
- Never infer that the six components are interchangeable or that all charges scale linearly with turnover.

## Required regression tests before implementation is considered complete

1. One note with multiple fills and broker-provided per-trade charges reconciles exactly.
2. A source-level charge is not duplicated across fills.
3. A documented proportional method handles uneven amounts and deterministic paise residuals.
4. Source-note total mismatch blocks promotion.
5. Repeated source-note ingestion and fill replay do not duplicate allocations.
6. Two concurrent workers cannot allocate the same source component twice.
7. A fill arriving before the source note remains pending and is reconciled safely later.
8. Ambiguous or missing basis fails closed without creating an execution or mutating a live position.
9. Rollback after allocation failure leaves no partial allocation, execution, or position change.
10. Audit evidence identifies the source, allocation basis, method version, and reconciliation result.

## Acceptance gate

Do not bridge `BrokerFillIdentity` to `BrokerTradeRecord`, add automatic contract-note allocation, or enable automatic accounting promotion until the evidence contract, schema, migration, idempotency strategy, and tests have been reviewed and CI passes on the exact commit.

## Current safety state

Live broker submission, automatic accounting promotion, and automatic scheduling remain disabled. Phase 2 remains closed. This document defines requirements; it is not evidence that allocation is implemented.


## Phase 3 model and CI audit — 2026-10-21

### Repository evidence reviewed

- `BrokerTradeRecord` currently stores broker connection ID, broker order reference ID, broker trade ID, quantity, price, side, instrument token, and exchange timestamp. It has a uniqueness constraint on `(broker_connection_id, broker_trade_id)`, plus positive quantity/price and valid-side checks.
- The reviewed `BrokerTradeRecord` model does not itself store contract-note reference, source charge totals, per-component charge evidence, allocation basis/version, or reconciliation state.
- `LiveFillChargeBreakdown` in `backend/app/services/live_fill_accounting_service.py` accepts per-promotion amounts for brokerage, STT, exchange, SEBI, stamp duty, GST, total, source, and reference. The service validates the supplied total against the six supplied components and persists charges as part of the fill promotion. This does not establish how a multi-fill contract-note total was apportioned or independently reconcile a source-note total.
- The path `backend/app/models/broker_fill_identity.py` was not found at the repository path checked. Do not assume the identity model name/path; locate it from the repository tree before designing any bridge. The same applies to `backend/app/schemas/live_fill_accounting.py`, which was also not found at that exact path.

### CI gap — distinguish missing coverage from missing execution

- Last verified code CI baseline remains [run 39609474410](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39609474410): 485 passed, 1 warning; broker-write boundary guard and SQLite/PostgreSQL 16 migration cycle passed.
- Actions history shows a successful run for progress commit `4b600863e6280de201d4637610a78ae4cd7a8828` ([run 39615363395](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39615363395)). This is not the current HEAD.
- Current HEAD before this audit update was `f52873b2ebe71b1dea96186acaee9a3117f9fe42`, which adds the charge-allocation design document. No run matching that exact SHA was visible. Thus the observed gap is exact-HEAD CI verification for docs commits, not evidence that the backend workflow itself is absent.
- Required regression coverage not yet evidenced in current code: source-note-to-multiple-fill allocations, source-total reconciliation, deterministic paise residual, duplicate source-charge prevention, concurrent allocation races, retry/recovery, and fail-closed behavior for missing/ambiguous allocation basis.

### Next safe implementation sequence

1. Inspect the repository tree and existing charge/contract-note ingestion before naming or adding models.
2. Identify the broker-specific source fields and evidence format; do not guess allocation basis.
3. Add source-note and allocation persistence with unique source-component and source-fill constraints only after the schema and migration are reviewed.
4. Add the listed regression tests and extend the existing backend CI workflow to execute them and migration checks.
5. Verify CI against the exact resulting code SHA, then update the nine core docs and this contract.

No allocation algorithm, schema migration, or identity bridge is implemented by this audit. Live broker submission, automatic accounting promotion, and automatic scheduling remain disabled. Phase 2 remains closed.


### Broker ingestion path traced — 2026-10-21

- `backend/app/services/broker_trade_ingestion_service.py` fetches and validates Upstox trade rows, then persists normalized `BrokerTradeRecord` rows. The staged row has trade identity/economics/timestamp but no contract-note charge payload. Duplicate ingestion is checked against the connection-scoped broker trade ID and conflicting trade fields are rejected.
- `backend/app/services/broker_child_order_reconciliation_service.py` compares broker-reported filled quantity and average price with staged trade records and updates child-order metadata only. Its module contract explicitly avoids creating `Execution` rows or changing cash/positions/P&L.
- Therefore, the currently reviewed ingestion/reconciliation path supplies no contract-note total or component-level fee evidence to the charge allocator. Do not implement allocation by pretending this evidence is present. The next prerequisite is to identify the actual Upstox contract-note/charges endpoint or supported export and the existing adapter/data-retention policy; until then, keep source-note allocation blocked by design.
- The existing `.github/workflows/backend-tests.yml` already runs pytest with PostgreSQL 16, the broker-write boundary guard, and SQLite/PostgreSQL Alembic upgrade/downgrade/re-upgrade. No separate workflow is needed just for this feature at present; missing tests must be added to the existing suite. Exact-HEAD CI remains a separate verification requirement.


### Upstox API evidence-source review — 2026-10-21

Official Upstox documentation review identified these relevant endpoints:

- `GET /v2/order/trades` and `GET /v2/order/trades/get-trades-for-day` expose order/trade execution data; inspect their exact response schemas before wiring them into ingestion.
- `GET /v2/charges/historical-trades` returns historical trade rows including trade ID, date, quantity, price, and transaction type, paginated for up to the last three financial years. Its documented sample/schema does not include per-trade fee components.
- `GET /v2/trade/profit-loss/charges` returns a charges breakdown aggregated for a requested segment/date range/financial year; its documented response is a total breakdown, not a per-trade allocation ledger.
- `GET /v2/charges/brokerage` calculates a charge estimate for given instrument/quantity/product/side/price. This is not evidence of actual fees assessed on a completed fill and must not be passed as `BROKER_REPORTED` actual charges.

References: Upstox [Get Trade History](https://upstox.com/developer/api-documentation/get-historical-trades/), [Get Trade Charges](https://upstox.com/developer/api-documentation/get-trade-charges/), and [Brokerage Details](https://upstox.com/developer/api-documentation/get-brokerage/).

Conclusion: available documented APIs provide trade-level execution identity and a date/segment-level aggregate fee total, but the reviewed public response schemas do not establish a source-provided per-trade actual-charge breakdown. Do not distribute the aggregate by guessed proportions. The safe next path is to inspect `GET /v2/trade/profit-loss/data` and metadata for any trade-wise fee fields, and/or ingest the actual broker contract-note/bill report as source evidence. Until an exact per-trade charge mapping is verified, automatic live accounting promotion must remain blocked for those trades.


### Trade-wise P&L endpoint checked — 2026-10-21

The official `GET /v2/trade/profit-loss/data` documentation describes trade-wise realized P&L rows with quantity, buy/sell dates, averages and amounts, but its documented response schema does not include per-trade charge components. Its companion metadata endpoint provides report counts/page limits only. This does not close the actual-charge evidence gap. Continue to treat the aggregate charges endpoint as reconciliation context only, not as per-fill allocation evidence. Reference: https://upstox.com/developer/api-documentation/get-profit-loss-report/ and https://upstox.com/developer/api-documentation/get-report-meta-data/.


### Contract-note source availability check — 2026-10-21

- Reviewed the current official Upstox API endpoint catalogue via its Swagger UI and developer API overview. The documented post-trade/charges endpoints include historical trades, trade-wise P&L data/metadata, aggregate P&L charges, and brokerage estimation; no documented contract-note download endpoint was identified in that catalogue review.
- This is a bounded documentation review, not proof that no contract-note export exists in the Upstox web/app or support channels. The source remains unresolved. Until verified, use an explicit manual evidence-import boundary only if the product already supports secure uploads and retention; otherwise keep actual-charge promotion blocked rather than allocating aggregate totals.
- Official endpoint catalogue: https://api.upstox.com/v2/swagger-ui/index.html and https://upstox.com/developer/api-documentation/.
- Do not call `/charges/brokerage` estimates actual charges, and do not treat `/trade/profit-loss/charges` aggregates as per-trade fees. Keep any future source ingestion read-only and separate from order placement.


### Existing adapter capability audit — 2026-10-21

- Reviewed `backend/app/brokers/base.py`, `backend/app/brokers/upstox/adapter.py`, `backend/app/brokers/upstox/response_parsing.py`, `backend/app/services/broker_trade_ingestion_service.py`, and `backend/app/models/execution.py`.
- `BrokerAdapter` exposes order/trade retrieval methods but no contract-note ingestion or actual-charge retrieval method. `UpstoxAdapter` defines a `BrokerageChargeEstimate` parser in response parsing for the estimate endpoint; its own docstring says this is an estimate, not proof of final fees. The ingestion parser's `BrokerTrade` schema likewise contains no charge fields.
- `Execution` persists per-fill charge components and a 200-character `charge_reference`, but there is no source-note/allocation ledger or FK to immutable source evidence. The current test fixture uses a reference named like a contract note; this is only test input and must not be mistaken for proof the production adapter fetched or validated that note.
- Decision: do not add an adapter method or migration until the accepted evidence format/path and security/retention requirements are approved. If using a contract-note file, parse it as untrusted input, validate account/period/IDs/totals, retain a fingerprint and provenance, and make import idempotent. Keep it read-only and never couple it to broker order-write APIs.


### Implementation gate decision — 2026-10-21

The reviewed current `BrokerAdapter`/`UpstoxAdapter` contract exposes trade retrieval and a brokerage-estimate capability, but no actual-charge/contract-note retrieval operation. `Execution` persists per-fill components but is not linked to immutable source evidence. Therefore Phase 3 cannot safely finish actual charge allocation solely by editing `LiveFillAccountingService`.

**Approved next implementation boundary:** add a separate, read-only source-evidence ingestion layer only after an actual supported source is selected. It must not be added to order-placement paths. A source record should be immutable after import and include broker connection/account scope, source document fingerprint, source period, currency, original totals/components, parser/schema version, import status, and provenance. Per-fill allocation records must reference the source record and broker trade identity, store basis/method version and allocated components, and enforce uniqueness preventing repeated allocations. Use database transactions to ensure source reconciliation and allocation rows commit atomically. Reject unknown or unmatched rows; never auto-promote on aggregate-only evidence.

**Tests to add to the existing backend workflow:** (1) duplicate source fingerprint/import idempotency, (2) account/period mismatch rejection, (3) invalid/tampered document rejection, (4) unmatched/duplicate broker trade IDs, (5) component and total reconciliation, (6) deterministic paise residual under an explicitly approved basis, (7) concurrent import/allocation uniqueness race, (8) transaction rollback on partial failure, (9) retry idempotency, (10) ensure estimate endpoint payload cannot be accepted as actual charges, (11) ensure no broker order-write call is made by import, and (12) SQLite/PostgreSQL migration reversibility.

No schema or allocation formula should be implemented until the supported contract-note/export format and a valid per-charge allocation basis are verified. This is a deliberate safety gate, not permission to silently substitute estimates or heuristics.


## Phase 3 checkpoint refresh — 2026-10-21

- **Repository boundary:** all current Phase 3 work is confined to `tarunsharma2610-del/tradepro-improved`, branch `main`. The original `tarunsharma2610-del/Tradepro` is a protected baseline and must not be modified.
- **Current HEAD at audit start:** `3b5c8831d4f3475eee320176b3c06bdbd5364bd2` (source-ledger design-gate documentation). The documentation synchronization commit created after this note requires its own exact-HEAD CI result.
- **Latest confirmed backend CI during this audit:** [run 39618611385](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39618611385) completed successfully on **commit `49f95bdd5f20ee99b21a573087c6e97a9bc03526`**, with **485 passed, 1 warning in 30.65s**. The broker-write boundary guard and SQLite/PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade steps passed. This run is an older SHA, not current HEAD; do not label later commits green based on it.
- **Phase 3 status:** in progress. Current blocker is verified actual-charge evidence and an approved allocation basis. Reviewed Upstox documented APIs provide trade data, aggregate charges, or estimates, but no verified per-fill actual-charge source/contract-note ingestion capability was found in the reviewed adapter/API catalogue. Do not treat estimates as actual charges or allocate aggregate totals by guess.
- **Next engineering sequence:** establish authoritative source format and retention/security boundary; then implement immutable source evidence and per-fill allocation records, migration, transactional reconciliation/idempotency, and required regression tests; finally verify exact-HEAD CI.
- **Safety:** live broker submission, automatic accounting promotion, and automatic scheduling remain disabled. Phase 2 remains closed. This checkpoint is status tracking, not a claim that Phase 3 charge allocation is implemented.
