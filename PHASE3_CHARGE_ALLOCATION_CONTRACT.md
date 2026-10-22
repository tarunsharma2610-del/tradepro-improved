## Phase 3 allocation-math checkpoint — 22 October 2026

- Added `backend/app/services/broker_charge_allocation_service.py` with deterministic largest-remainder allocation math using Decimal values and integer paise, stable fill-ID tie-breaking, explicit method version, and source-total equality check.
- Added regression tests for source-total reconciliation, input-order independence, tie-breaking, zero weights, invalid/negative/non-finite values, unsupported basis, and paise precision.
- **Important limitation:** this is a pure allocation-math utility, not yet the durable persistence/orchestration service. It does not read reviewed evidence, bind trade rows to a connection, write immutable ledger rows, reconcile stored component totals across all fills, or gate execution promotion. A caller must select an explicitly reviewed basis appropriate to the charge component; no basis is inferred here.
- Existing schema migration/model slice had CI success at PR head `1505b71198f7f9f42ad749588597b7c8bb63eb0d`, run [39730707245](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39730707245). The newer service/tests/docs commits still require exact-head CI verification.
- **Next:** verify latest CI and correct failures; then implement a transactional persistence service that validates reviewed evidence + same-connection trades, inserts replay-safe rows, and marks a component reconciled only when the allocations sum exactly to its source total. Add DB-backed tests for idempotency, conflicting replays, foreign-connection evidence/trades, and rollback.
- Keep live broker submission and automatic accounting promotion gated. All work remains in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` must remain untouched.

---

## Phase 3 allocation-ledger implementation checkpoint — 22 October 2026

- **Branch:** `phase3/durable-per-fill-charge-allocation` (based on verified main `54342a69249c9a790544c415842ec74c9ddf57fb`).
- **Initial implementation slice:** added `BrokerChargeAllocation` model and migration `202610220010`, registered the model, and added schema-contract tests. Ledger fields capture source evidence, broker connection, broker trade record, charge component, source component total, allocated amount in INR paise precision, allocation basis, method version, reconciliation state, and an optional reconciliation reference.
- **Idempotency constraint:** unique `(evidence_id, broker_trade_record_id, charge_component)`; supported components and nonnegative amounts are database-constrained. New rows default to `PENDING_RECONCILIATION`.
- **Not yet complete:** this is the durable schema foundation only. There is not yet a persistence/allocation service, cross-record validation that evidence and trade belong to the same connection, immutable-update enforcement, deterministic rounding/residual algorithm, source-total reconciliation, or linkage to execution promotion. Do not claim live accounting is using this ledger.
- **Verification:** exact-head CI has not yet been observed for this branch. Do not merge until backend tests and SQLite/PostgreSQL migration upgrade/downgrade/re-upgrade checks pass.
- **Next:** validate migration/tests, add a service that uses Decimal/paise arithmetic only when an explicitly reviewed basis is authorized, enforces evidence/connection/trade binding and replay-safe inserts, and reconciles each source component total exactly. Ambiguous allocations must remain pending and block promotion.
- **Safety/scope:** keep live broker submission and automatic accounting promotion gated. All changes are limited to `tarunsharma2610-del/tradepro-improved`; do not modify original `tarunsharma2610-del/Tradepro`.

---

## End-of-day checkpoint — 21 October 2026 (post-merge verification)

- PR #5 (`Phase 3: add fail-closed reviewed charge evidence validator`) was squash-merged into `main` as commit `3f9c3f2c99d8f1afcbdd7a00933c9451c7ae35c7`.
- Feature-branch exact-head CI passed at commit `6cd76bbe430d49032234a1e0d804158562c17553` in run [39639800746](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39639800746).
- Post-merge `main` CI for merge commit `3f9c3f2c99d8f1afcbdd7a00933c9451c7ae35c7` is run [39640095959](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39640095959); last checked status was `in_progress` for Backend pytest. Do not mark post-merge CI green until a completed successful result is verified.
- **Next action on resume:** re-check run `39640095959` first. If failed, inspect logs, fix, commit, and verify exact-head CI. If successful, proceed to the durable per-fill charge-allocation ledger: immutable allocations, deterministic paise rounding/residual policy, source-total reconciliation, idempotency/replay, partial fills and crash recovery.
- Phase 3 remains incomplete. Contract-note import/parsing and authenticated-source validation are not yet complete; evidence hash/review status are not proof of broker authenticity. Keep live broker submission and automatic accounting promotion gated.
- Scope remains strictly `tarunsharma2610-del/tradepro-improved`; do not modify original `tarunsharma2610-del/Tradepro`.

---

<!-- Phase 3 checkpoint sync: 2026-10-21; branch phase3/reviewed-charge-evidence-gate; commit 42a7418c674d92af9d099b1095d90af660678e2b; exact-head CI run 39638875688 passed. -->

## Latest verified Phase 3 checkpoint — 21 October 2026

- **Code/test commit:** `42a7418c674d92af9d099b1095d90af660678e2b` on `phase3/reviewed-charge-evidence-gate` in `tarunsharma2610-del/tradepro-improved`.
- **Exact-head CI:** GitHub Actions run [39638875688](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39638875688) completed successfully. Backend pytest, broker-write boundary enforcement, SQLite migration upgrade/downgrade/re-upgrade, and PostgreSQL 16 migration checks passed.
- **New regression coverage:** rejects charge evidence from non-contract-note sources and mismatched reviewer identities. Existing evidence validation covers connection binding, reference matching, reviewed status, reviewer identity and review timestamp.
- **Scope and safety:** PR #5 remains open and unmerged as of this checkpoint. Evidence metadata/hash and a review status are provenance/workflow controls, not cryptographic proof of broker authenticity. Contract-note parsing/import, immutable per-fill charge allocation, deterministic paise rounding/residual handling, source-total reconciliation, and complete replay/partial-fill/crash-recovery acceptance remain unfinished.
- **Next:** continue with a reviewed contract-note import boundary and a durable, idempotent per-fill allocation ledger; do not invent charge splits. Keep live broker submission, automatic accounting promotion and automatic scheduling disabled until release gates pass.
- **Repository constraint:** changes must remain in `tarunsharma2610-del/tradepro-improved`; do not modify the original `tarunsharma2610-del/Tradepro` repository.

---

<!-- Authoritative checkpoint refresh: 21 October 2026. Scope: tradepro-improved only. -->

## Authoritative Phase 3 checkpoint — 21 October 2026

- **Current code-and-documentation HEAD before this documentation sync:** `4fe58dd11b018d1f85000540ad2ec1b7f6f52ae5`. Its exact-HEAD push CI [run 39633514414](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39633514414) completed successfully. Backend pytest, broker-write boundary guard, and SQLite/PostgreSQL 16 migration upgrade-downgrade-reupgrade checks all passed.
- **Evidence-ledger implementation:** `6c0a382eb9fea7f386433cfdb65a65cbc53f218e`; migration correction: `c17f522bf68121a6d162a4d858cd9de8b95d45d1`. Their CI runs [39633266180](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39633266180) and [39633330531](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39633330531) both passed.
- **Implemented:** `BrokerChargeEvidence` model and migration `202610210009`; captures broker connection, report metadata, filename, SHA-256 fingerprint, byte size, parser version, and review status. Tests cover persistence, duplicate-fingerprint rejection per connection, and database constraints.
- **Limits:** a hash detects byte-level changes but does not prove broker origin. The ledger does not yet retain document bytes, import/parse the broker document, establish authenticity, or allocate charge components to fills. `REVIEWED` is a workflow status, not automatic approval to promote live accounting.
- **Next Phase 3 gate:** build a fail-closed, idempotent contract-note import/review boundary and inspect a real redacted broker contract note before selecting charge-specific allocation rules. Then implement immutable per-fill allocation records, paise rounding/residual rules, source-total reconciliation, and replay/crash/partial-fill tests.
- **Phase 3 remains in progress.** Keep live broker submission, automatic accounting promotion, and automatic scheduling disabled. Phase 2 remains closed. All changes must stay in `tarunsharma2610-del/tradepro-improved`; do not modify `tarunsharma2610-del/Tradepro`.
- Older checkpoints below are historical; this section is authoritative until replaced by a later verified checkpoint.

---

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


### Verified manual contract-note export path — 2026-10-21

Correction/refinement: the reviewed Upstox public API catalogue did not show a contract-note download API, but Upstox Help Center documents a supported manual export. In the app: My account → Reports → Miscellaneous reports → Filters; select segment, report type `CONTRACT`, financial year and date; choose Get Report and download the contract note. Upstox also says contract notes are sent to the registered email within 24 hours. Official source: https://upstox.com/help-center/how-can-i-access-and-download-the-contract-note-248457/. This supersedes any broad wording suggesting contract notes cannot be obtained; the accurate limitation is no documented contract-note download API was identified, while manual export is available.

Implementation consequence: design a user-initiated, read-only import of the downloaded contract-note file, not automatic API retrieval. Before coding, inspect a redacted sample to establish file format, signed-document verification, trade-level IDs, actual charge fields, account/segment/date scope and allocation basis. Treat files as untrusted; enforce account ownership and duplicate-import idempotency; store minimal provenance/fingerprint; reject ambiguous mappings; protect source files under access/retention rules; never store PAN/password in the source record. Do not approve a fee allocation formula until the actual document fields and valid allocation basis are verified.

CI: backend run https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39619332422 passed on SHA `49f95bdd5f20ee99b21a573087c6e97a9bc03526`, not current HEAD `273a340dc12ae3f20dbe87aa2b16463de5e75e7c`; exact-HEAD Actions query returned zero runs. Do not infer latest-head green. Phase 3 open; Phase 2 closed; live submission, automatic accounting promotion and scheduling disabled. All work must remain in `tradepro-improved`, never original `Tradepro`.

### Public sample contract-note review — 2026-10-21

A public, third-party-hosted Upstox contract-note transcription was located for field discovery:
- https://www.scribd.com/document/735902961/CW-T-842243-20240521-NSE-35749411
- A second example is available at https://www.scribd.com/document/971660843/CW-T-3JCTYG-20250312-NSE-66319975-1
These are user-uploaded copies, not broker-authenticated test fixtures. They contain personal/client information and must not be copied into the repository, test data, logs, or documentation. Only their field structure was reviewed.

The reviewed sample text shows contract-note metadata (contract-note number, trade date, segment, settlement, trading code), trade rows with order number/time, trade number/time, contract description/ISIN, side, quantity, rate, brokerage per unit, net rate and net trade total, plus segment-level obligation and charge lines. The charge summary may include IGST/GST, STT and rounding, stamp duty, turnover/exchange charges, IPFT, SEBI fees and depository transaction charges depending on the activity. A sample explicitly says trade-wise levies can be provided on request.

This is enough to establish a candidate *field inventory*, but not a safe allocation contract:
- Publicly visible text is not the original PDF byte stream and cannot verify PDF structure, embedded digital signature, tamper status, parser behavior, or exact fields in the currently downloadable report.
- A sample contract note's segment-level totals do not establish how every charge component maps to each individual trade/fill. The note's displayed per-unit brokerage is not proof that every other levy can be apportioned with the same basis.
- Public samples are privacy-sensitive third-party uploads and cannot be trusted as authoritative account evidence.

Official references:
- Upstox explains how an account holder can download their own contract note from the app/site: https://upstox.com/help-center/my-account/portfolio-reports/
- NSE's official sample format documents order/trade numbers, time, security, side, quantity, price, brokerage, net total and levies: https://nsearchives.nseindia.com/web/sites/default/files/inline-files/How_to_buy_and_sell_shares_in_Stock_Exchange.pdf
- NSE says the revised contract-note format is mandatory for equity and derivatives segments and transaction charges may be combined across exchanges: https://www.nseindia.com/static/trade/contract-note-faqs

Decision: the public sample search reduces uncertainty about the likely visible fields, but does NOT clear the implementation gate. Do not build a production parser, treat the public sample as authenticated, or allocate aggregate levies to fills without a verified actual downloadable file format and a documented, component-specific allocation basis. Keep the import boundary read-only and all live-account safety gates unchanged.

### Repository code-path audit — 2026-10-21

Inspected current files on `main` directly:
- `backend/app/services/broker_trade_ingestion_service.py` — stages normalized broker trades separately; module contract says it does not update accounting balances, positions or P&L.
- `backend/app/services/broker_child_order_reconciliation_service.py` — reconciles broker child-order status against staged trades; module contract limits writes to broker-order metadata.
- `backend/app/models/broker_trade_record.py` — unique broker connection + trade ID, quantity, price, side, instrument token and exchange timestamp; no contract-note source, source fingerprint, or per-component allocation evidence.
- `backend/app/services/live_fill_accounting_service.py` — requires explicit `BROKER_REPORTED` charge source, a non-empty reference <= 200 chars, non-negative finite paise-precision components and exact sum equality across brokerage, STT, exchange, SEBI, stamp duty and GST. It atomically promotes one staged trade and compares the charge values/reference on idempotent replay.
- `backend/app/models/execution.py` — persists the six charge components, total, source and 200-character reference; unique connection + broker trade ID prevents duplicate accounted fills.

Conclusion: the existing promotion boundary validates a caller-supplied charge breakdown but does not establish the authenticity of the source document or prove how aggregate contract-note levies should be apportioned. Do not change the promotion contract or add schema until a documented source-specific allocation rule is available. This audit found no basis to treat a text transcription or a broker estimate as verified per-fill actual fees.

CI workflow inspection: `.github/workflows/backend-tests.yml` runs pytest, broker-write boundary guard, and SQLite/PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks on pushes to main and pull requests. The current docs-only commit will trigger the push workflow, but exact-HEAD success must be checked after GitHub finishes.

### Official Upstox API schema cross-check — 2026-10-21

Checked the current public Upstox API documentation directly:
- Trade-wise realised P&L endpoint: https://upstox.com/developer/api-documentation/get-profit-and-loss-report/
  The documented response exposes quantity, ISIN, scrip name, trade type, buy/sell dates, average prices and buy/sell amounts. The documented response does not expose the six actual per-fill charge components or broker trade IDs needed to attach verified charge evidence to `Execution`.
- Charges endpoint: https://upstox.com/developer/api-documentation/get-trade-charges/
  The documented response exposes a `charges_breakdown` total and aggregate brokerage, taxes (GST, STT, stamp duty) and charges (transaction, clearing, IPFT, others, SEBI turnover and demat transaction). The request is scoped by date range, segment and financial year; the documented response is a segment/date-period aggregate, not a per-fill charge allocation record.
- Historical trade endpoint: https://upstox.com/developer/api-documentation/get-historical-trades/
  This provides historical trade/transaction data with pagination for up to the last three financial years, but does not, by itself, document a per-trade actual-charge breakdown.

NSE's revised contract-note FAQ says trade details including order number/time, trade number/time, quantity and price are to be attached as an annexure, and says transaction charges across exchanges are combined in the revised format: https://www.nseindia.com/static/trade/contract-note-faqs. This reinforces that a contract note can aggregate some charge categories and does not itself prove a unique per-fill mapping for every charge.

Decision: the reviewed official API schemas do not eliminate the actual-charge evidence/allocation blocker. Do not reinterpret aggregate charge totals as per-fill fees, and do not match the trade-wise P&L rows to staged fills based only on symbol/date/average price. An importer may only persist source evidence and perform mappings for which exact identifiers and allocation rules are supported; ambiguous rows/components must remain unreconciled and must not be promoted automatically.


## Implementation checkpoint — broker charge source evidence metadata (2026-10-21)

A first persistence slice adds `broker_charge_evidence` and migration `202610210009`. It stores the broker connection, report metadata, filename, SHA-256 fingerprint, byte size, parser version, and review workflow status. The same fingerprint cannot be registered twice for the same broker connection. Tests cover persistence and database constraints.

**Limitations are intentional:** the metadata ledger does not store the source document bytes, prove that a file originated from Upstox, validate the file format, parse charge rows, or allocate charges to fills. A SHA-256 fingerprint only identifies the bytes that were hashed. Do not treat `REVIEWED` as cryptographic authenticity or automatic accounting approval. Importer, evidence retention/access controls, review authorization, immutable allocation ledger, and component-specific allocation rules remain separate gates. Do not enable live accounting promotion based on this metadata alone.
