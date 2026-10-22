## Replay-basis test correction — 22 October 2026

- Latest CI failed on head `bac124af41342293e5bceba8d5641e85184bee16`: `525 passed, 1 failed, 1 warning`. The new test supplied `ALTERNATE_REVIEWED`, which is intentionally not a supported allocation basis; validation rejected it before replay-conflict detection.
- Test-only correction committed as `6b91827d6a4a01ea93009d664d467ca32d5ec342`: the test now uses `QUANTITY`, a supported basis distinct from the original `EXPLICIT_REVIEWED`, so it exercises the intended changed-basis replay guard without weakening production validation.
- **Pending:** exact-head CI for `6b91827` and documentation updates must pass before replay-basis coverage is marked green.
- Concurrency review remains open: unique evidence/trade/component rows protect duplicate per-fill rows, but do not alone prove correct handling of concurrent conflicting fill sets. PostgreSQL integration coverage is required.
- PR #6 stays draft/unmerged. Live broker submission and automatic accounting promotion remain gated. All work stays in `tarunsharma2610-del/tradepro-improved`, not original `Tradepro`.

---

## Phase 3 rollback CI verified; replay-basis test added — 22 October 2026

- CI run `39734057700` passed for commit `85e022e630682da50b1b9e906a8b5986e541d97b`. This confirms the explicit SQLite transaction-boundary correction fixed the rollback test on that head.
- Added a new regression test to reject a replay that changes the reviewed allocation basis, while preserving the existing exact-replay behavior. Test commits: `3f912a1b02cea3880cd7020dea88fa9cbf1185f9` and helper correction `25695e5fc6a1d65f9344bd44f3229c9fa90a69a0`.
- **Pending verification:** the new replay-basis test and following documentation commits have not yet passed exact-head CI. Do not count them as green until CI completes.
- Concurrency note: the model has a unique constraint on evidence + trade + component, which prevents duplicate rows for a fill, but it does not by itself serialize concurrent requests that race with different fill sets. Before merge, add/review a database-backed concurrency strategy and test on PostgreSQL; SQLite alone cannot prove row-lock semantics.
- Still not proven: contract-note authenticity, legally/economically appropriate allocation basis, and integration with live accounting. No automatic accounting promotion is enabled.
- PR #6 remains draft/unmerged. Work remains confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is not the target.

---

## SQLite rollback test infrastructure correction — 22 October 2026

- Latest exact-head CI `39733775193` failed again: `524 passed, 1 failed`. The explicit session transaction still did not roll back the rows because SQLite's legacy driver transaction mode did not issue a physical `BEGIN` before the service's nested SAVEPOINT.
- Test-only infrastructure correction committed as `d49e3cdfae519dc7d7f80bdcda882fcaa6842c51`: configure the in-memory SQLite test engine with explicit transaction boundaries (disable driver-managed implicit transaction control and emit `BEGIN` on SQLAlchemy's begin event). This is the documented SQLAlchemy pattern for reliable SAVEPOINT behavior; it changes test setup, not production database code.
- **Pending:** rerun CI for this commit and documentation updates; only mark rollback coverage resolved if the test passes.
- If the rollback test still fails, stop and replace it with a database-specific integration test rather than weakening the assertion. Concurrent conflicting replay tests remain next after green CI.
- PR #6 stays draft/unmerged; live broker submission and automatic accounting promotion remain gated. Work is limited to `tarunsharma2610-del/tradepro-improved`, not original `Tradepro`.

---

## Rollback-test CI failure and correction — 22 October 2026

- CI run `39733515473` failed at commit `c9adf3b9da90e1a2d350c216ccdb923ac3ba41a8`: **524 passed, 1 failed, 1 warning**. The only failure was the new rollback test, which assumed the shared SQLite test session had a real outer transaction. The fixture commits setup records, and SQLite can release a SAVEPOINT without an explicit outer `BEGIN`.
- Corrective test commit: `f941b4bf32c8be77ad4c8c17811632ed77b540f0`. The test now starts an explicit outer transaction around the allocation service and rolls that transaction back before asserting no allocation rows remain. This tests caller-owned transaction rollback instead of relying on SQLite's implicit transaction behavior.
- **Pending verification:** exact-head CI for `f941b4b` and the documentation commits must pass before this rollback regression is considered resolved.
- No application transaction semantics were changed by this test-only correction. The service still leaves commit/rollback to its caller. Remaining follow-up: concurrent conflicting replay tests and database-level serialization review.
- Keep PR #6 draft/unmerged; live broker submission and automatic accounting promotion remain gated. Work is limited to `tarunsharma2610-del/tradepro-improved`, not original `Tradepro`.

---

## Phase 3 rollback test checkpoint — 22 October 2026

- Exact-head CI verified green for the corrected connection-safety assertion and latest documentation head `a19313ccba7c2fe79c6ac588d3acb81cd4168dce`; run `39733212480` and latest docs run `39733267668` both completed successfully.
- Added `test_outer_transaction_rollback_removes_all_new_allocations` in commit `c9adf3b9da90e1a2d350c216ccdb923ac3ba41a8`. It confirms the persistence service does not commit on the caller's behalf and a caller rollback removes all allocation rows created in that transaction.
- **Pending:** run exact-head CI for the rollback test and subsequent documentation commits. Do not count this new test as passed until the run succeeds.
- Remaining review: database-level uniqueness already guards duplicate evidence/trade/component rows; simultaneous imports can still require stronger serialization/unique source-component identity and explicit conflicting concurrent replay coverage. Source-document authenticity and allocation-basis suitability remain manual/review-gated; no accounting promotion is wired.
- Keep PR #6 draft/unmerged and live broker submission/automatic accounting promotion gated. Changes remain confined to `tarunsharma2610-del/tradepro-improved`, not original `Tradepro`.

---

## Follow-up CI diagnosis — 22 October 2026

- The corrected-fixture CI run `39732808218` failed after executing the tests: **523 passed, 1 failed, 1 warning**. The remaining failure was an overly specific expected error-message regex in the cross-connection rejection test; the service correctly rejected the trade with `Every broker trade record must belong to the evidence connection.`
- Fix committed as `6ff7d5bfc442f7fa06f6df9299b23199faf04d3d`: align the assertion with the service's actual safety error. This is a test assertion correction, not a relaxation of the connection guard.
- The exact-head CI for `6ff7d5b` must be checked before declaring the regression resolved.
- Next after CI passes: add explicit rollback coverage, then review concurrent/replayed allocation behavior and database constraints. Keep PR #6 draft/unmerged until the full required checks pass.
- Live broker submission and automatic accounting promotion remain gated. Work is limited to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains out of scope.

---

## CI failure analysis and correction — 22 October 2026

- Latest persistence-test CI failed on commit `f7d84cd695192e59bee12f1de625e570746a2e88`: backend pytest reported `519 passed, 1 warning, 5 errors`.
- Root cause from the job log: all five new persistence tests requested a `reviewed_evidence` fixture that did not exist. This was test setup failure, not evidence that the allocation assertions passed.
- Corrective commit `a1149cbff48357fd9aab006de7fe3435a89cbed0` adds a local fixture creating a user, broker connection, and reviewed contract-note evidence row using the actual model fields. The new commit must still pass exact-head CI before this issue can be considered resolved.
- Next: verify CI for the corrected head. If green, add rollback and concurrency/replay tests. If it fails, inspect job logs and fix before proceeding.
- No merge; no live-accounting promotion. Work is confined to `tarunsharma2610-del/tradepro-improved`, not original `Tradepro`.

---

## Phase 3 persistence-test checkpoint — 22 October 2026

- Added database-backed tests for successful component allocation and exact source-total reconciliation, idempotent identical replay, conflicting replay with changed total, cross-connection trade rejection, and changed fill-set rejection without partial rows.
- Tests use the existing isolated SQLAlchemy test-session fixture. They are committed to the Phase 3 branch; exact-head CI for this test commit and the documentation commits still needs verification.
- Review note: the current persistence service marks a component `RECONCILED` as soon as stored allocations sum to the source total. This is arithmetic reconciliation only, not proof that the chosen allocation basis is correct or the source document is authentic. No live-fill accounting promotion is wired to it.
- **Next:** verify exact-head CI; fix test/migration issues. Then add explicit transaction rollback coverage and consider DB-level concurrency/idempotency enforcement for simultaneous identical/conflicting imports before any merge.
- Live broker submission and automatic accounting promotion remain gated. All changes are confined to `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` is not the target.

---

## Phase 3 transactional allocation persistence checkpoint — 22 October 2026

- Added `backend/app/services/broker_charge_allocation_persistence_service.py` to validate reviewed contract-note evidence, enforce that every referenced persisted broker trade belongs to the same broker connection, and persist per-fill component allocations in a database savepoint.
- Replay handling: identical replay requests return the existing allocation rows; changed fill sets, totals, allocation values, basis, method version, currency, or rejected rows fail closed. Allocations are marked `RECONCILED` only when the full fill set exists and the sum equals the source component total exactly.
- This service uses the existing deterministic largest-remainder utility and writes a reconciliation reference. It does not authenticate the original contract-note document, choose an economically/legal basis, parse broker files, or enable accounting promotion.
- **Validation still required:** exact-head CI and DB-backed integration tests for successful allocation, identical replay, conflicting replay, cross-connection fill rejection, partial failure rollback, and migration upgrade/downgrade/re-upgrade. Treat the implementation as unverified until those pass.
- **Next:** run CI, add database-backed persistence tests and repair issues found; then review concurrency/idempotency behavior and synchronize the PR description/docs. Do not merge until exact-head CI is green.
- Keep live broker submission and automatic accounting promotion gated. Changes remain limited to `tarunsharma2610-del/tradepro-improved`; do not modify the original `tarunsharma2610-del/Tradepro`.

---

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

## Historical checkpoint — formerly marked Current Phase 3 checkpoint — 21 October 2026

- **Latest verified code/test HEAD:** `3963c2bf4e6ffe2bb33d327b10e2995cd243d003`. Exact-head [Backend CI run 39607630055](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39607630055) passed **484 tests, 1 warning in 29.34s**; the broker-write boundary guard passed, and SQLite/PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed.
- New Phase 3 guard: broker-reported live-fill charge references are trimmed for storage and rejected when longer than the `Execution.charge_reference` 200-character column limit. This prevents a predictable storage error from being misreported as a concurrent promotion conflict. Regression coverage is included in the 484-test result.
- The existing Phase 3 safety gates remain active: replay must match the accounted fill and exact charge evidence; only broker-reported, internally consistent charges with a non-empty audit reference are accepted; durable staged trade quantities must match broker-confirmed child fills before promotion; exchange-time ambiguity/out-of-order fills fail closed; paper positions and cash remain isolated.
- **Phase 3 remains in progress, not complete.** Remaining review includes coordinator/identity boundaries, charge provenance/allocation semantics, full partial-fill and crash/restart acceptance criteria, and any explicitly selected bridge design. Keep `BrokerFillIdentity` separate from manual `BrokerTradeRecord` unless a reviewed Phase 3 design explicitly authorizes a narrow bridge.
- Live broker submission, automatic accounting promotion, and automatic scheduling remain disabled. The original `tarunsharma2610-del/Tradepro` repository remains untouched. Phase 2 remains closed.
- This checkpoint describes the verified code commit above. The documentation synchronization commit will trigger its own CI; do not treat that documentation commit as green until its exact-head run passes. Older checkpoint entries below are historical audit trail, not current status.

---

## Historical checkpoint — formerly marked Current verified checkpoint — 21 October 2026

- **Last verified code/test checkpoint:** `00ee9bad0e962d92244da6f63da1e46ba058ad6f`; exact-head backend CI [run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) passed **472 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 reversible migration checks.
- **Last verified documentation checkpoint before this status refresh:** `391dfefc9580abf9537ee659877578033baae4fd`; exact-head backend CI [run 39568264419](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39568264419) passed.
- The Phase 2 audit covers the dependency/port matrix, broker-fill workflow boundary, idempotency and rollback, reconciliation crash recovery, transaction-level lease fencing, slow persistence, 20 concurrent expiry-boundary renewal/reclaim races, and official Upstox current-day API semantics.
- Official Upstox V2 [order-book](https://upstox.com/developer/api-documentation/get-order-book/) and [get-trades-for-day](https://upstox.com/developer/api-documentation/get-trade-history/) endpoints are current-day endpoints without documented pagination parameters. Historical trades use a separate [paginated API](https://upstox.com/developer/api-documentation/get-historical-trades/); it is not wired into the Phase 2 worker.
- **Phase 2 technical checklist is complete.** Before any Phase 3 work, require a passing exact-head CI run for the then-current `main` and explicit user approval; never infer a later commit is green from an earlier run.
- Live broker submission, automatic accounting promotion and automatic scheduling remain disabled. The original `Tradepro` repository remains untouched.

---

## Historical checkpoint — formerly marked Current verified checkpoint — 21 October 2026

- **Verified code/test checkpoint:** `00ee9bad0e962d92244da6f63da1e46ba058ad6f`; exact-head backend CI [run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) passed **472 tests, 1 warning**, the broker-write boundary guard, and SQLite/PostgreSQL 16 reversible migration checks.
- **Previously verified documentation checkpoint:** `a2e639f61e2c50070deb26d1a9a0741545c9737d`; exact-head backend CI [run 39568011689](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39568011689) passed. This is historical evidence for that SHA; every new commit still requires its own exact-head CI.
- The slow-persistence/lease-race audit is complete: the PostgreSQL row-lock test proves reclaim waits while a fenced write transaction is open; `test_postgres_high_volume_expiry_races_never_resurrect_stale_lease` passed 20 concurrent expiry-boundary renewal/reclaim races. Expired owners cannot renew, and ownership generation/token advance is verified.
- Official Upstox V2 [order-book](https://upstox.com/developer/api-documentation/get-order-book/) and [get-trades-for-day](https://upstox.com/developer/api-documentation/get-trade-history/) endpoints are current-day endpoints without documented pagination parameters. Historical trades use a separate [paginated API](https://upstox.com/developer/api-documentation/get-historical-trades/); it is not wired into the Phase 2 worker.
- Phase 2 technical audit and scope reconciliation are complete. Keep Phase 3 blocked until this final documentation commit's exact-head CI passes. Do not enable live broker submission, automatic accounting promotion or automatic scheduling. The original `Tradepro` repository remains untouched.

------

<!-- Historical checkpoint retained for audit trail; superseded by the current verified checkpoint above. -->
> **Latest verified checkpoint — 21 October 2026**
>
> - Repository: `tarunsharma2610-del/tradepro-improved`; branch: `main`. Original `Tradepro` repository remains protected and untouched.
> - Latest code/test commit: `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`. Backend [CI run 39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed **466 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration checks. Frontend [CI run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript and Next.js build.
> - Documentation audit commit `6407c5a05865c1be0ef673d3bb5e71c0231ef8da` passed [CI run 39556816828](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556816828).
> - Phase 2 checkpoint complete through atomic run/lease finalization, stale-run and cancellation recovery, lease-loss fencing, five-record renewal, and incomplete-summary warnings.
> - **Historical next-task note — completed:** slow persistence and 20-round concurrent expiry-boundary renewal/reclaim tests passed CI run [39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386).
> - Deferred safety-branch work remains tracked in `SAFETY_BRANCH_PORT_MATRIX.md`; no wholesale branch merge. Keep live broker submission and automatic accounting promotion disabled. Keep `BrokerFillIdentity` separate from `BrokerTradeRecord`.
>
> The CI status above refers to the stated code and documentation commits. This documentation refresh will create a new commit and trigger its own CI run; do not call that new run passed until GitHub reports success.

# Tradepro Improved — Roadmap and Release Gates

Last reviewed: 2026-10-21
Scope: this repository only. The original `Tradepro` repository must remain untouched.

## Historical checkpoint — formerly marked Current verified checkpoint

- User-approved live-order idempotency/reconciliation design is implemented partially for Phase 1: [LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md](LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md).
- Architecture, safeguards, README, audit, project instructions and progress tracker link to the design.
- Phase 1 records/repository/tests are on `main`; latest verified Phase 1 code checkpoint `dd36b48a92057ad50618f6f9941f908832c9cea3` passed [workflow 39048147046](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048147046), **215 tests passed, 1 warning**. The Phase 2 normalization foundation is now on `main` at test commit `b37452210bf07ad03acee1495e0627fae1378582`; [workflow 39049395091](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39049395091) passed **247 tests, 1 warning**, including SQLite and PostgreSQL 16 reversible migration checks.
- The code checkpoint adds Phase 1 durable storage/repository safeguards and tests only. It does not implement live submission or reconciliation, does not run a production migration and does not prove live trading readiness.

## Status summary

| Workstream | Status | Evidence / next gate |
|---|---|---|
| Paper execution and existing safeguards | Existing functionality; preserve | Keep regression tests proving paper path cannot call live broker placement |
| Instrument-master snapshot validation | Implemented and regression-tested; operational sync was disposable/in-memory | Repeat verified staging sync before deployment; never mutate production from an incomplete snapshot |
| Upstox V3 WebSocket authorization/reconnect protections | Partial implementation and unit/regression coverage | Real authorized session test remains open; shared stream state across workers remains open |
| Portfolio-wide risk controls | Existing configurable controls, still require deployment-aware review | Confirm atomic reservations, exposure semantics and user-adjustable thresholds; don't represent cost-basis/realized-loss checks as mark-to-market broker margin |
| Durable live-order idempotency | Phase 1 partially implemented; CI green for latest code checkpoint | Add concurrency/race tests and cross-database migration review; no broker submission |
| Broker order/trade reconciliation | Phase 2 read-only worker + durable run summaries + deduplicated manual-review issue records implemented and CI-tested; operator UI/API and real-account verification remain gated | Worker uses only the fixed-path GET-only Upstox client, user-scoped connection/token validation, lease, bounded retry, idempotent fill/status repositories and count-only durable run summaries. No write endpoint, scheduler, live submission or accounting updates. |
| Live submission orchestration | Not implemented / disabled | Sandbox-only workflow after prior phases pass |
| Production deployment verification | Incomplete | Backup-restored staging migration against actual DB engine, rollback/restore drill and operational runbook |

## Ordered roadmap

### Gate 0 — Design review (complete — user approved 2026-10-17)
- Read [PROJECT_INSTRUCTIONS.md](PROJECT_INSTRUCTIONS.md), [ARCHITECTURE.md](ARCHITECTURE.md), [LIVE_TRADING_SAFEGUARDS.md](LIVE_TRADING_SAFEGUARDS.md), [AUDIT_REPORT.md](AUDIT_REPORT.md), and [LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md](LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md).
- Confirm order-field canonicalization, supported Upstox products/order varieties, broker tag limits, order-history/trade API semantics and status mapping against current official docs.
- User explicitly approved `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`; approval is recorded in `PROGRESS.md`. This authorizes Phase 1 durable storage/repository safeguards only, not live-order submission.

### Gate 1 — Durable records only (no broker POST) — in progress
- [x] Additive SQLAlchemy records and Alembic migration for live intents, audit events, dispatch/outbox and broker-fill identities.
- [x] Unique idempotency key scoped to user/broker connection, canonical JSON payload hash, same-key/same-payload reuse and same-key/different-payload conflict.
- [x] Transactionally persist intent + initial event + outbox; enforce portfolio and broker-connection ownership in the repository.
- [x] Focused repository tests and clean SQLite Alembic migration run passed in GitHub Actions: [run 39043177545](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39043177545), 210 tests passed, 1 warning.
- [x] Add rollback atomicity test and a deterministic independent-session simulation of a competing unique-key winner; repository recovery returns the committed winner.
- [x] Validate order snapshots and audit event details as finite JSON and reject credential-like keys (nested access/refresh tokens, secrets, passwords, API keys, authorization headers and cookies); regression tests pass.
- [x] Add simultaneous same-key creation coverage using two independent PostgreSQL sessions and a barrier that forces both requests past an initial empty lookup; [workflow 39048147046](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048147046) passed.
- [x] CI verifies clean SQLite and PostgreSQL 16 upgrade → downgrade of revision `202610170002` → re-upgrade: [run 39048147046](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048147046).
- [ ] Verify upgrade/downgrade and constraints against a backup-restored staging copy of the actual deployment DB engine. No production migration has run.
- Scope boundary: no worker, API route or code path submits/cancels/reconciles broker orders in this phase.

### Gate 2 — Reconciliation-only workflow — repository foundation implemented; broker integration remains open
- [x] Add pure normalization for documented Upstox order book/details/history statuses and required fields; preserve raw status and route unknown/inconsistent records to review. Tested in [run 39049395091](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39049395091).
- [x] Add pure strict intent matcher: scope candidates to the authenticated broker connection, prefer an existing broker order ID, otherwise require one exact broker tag and exact instrument/side/type/quantity/product plus applicable price fields. Multiple candidates, cross-connection candidates, economic mismatches and unknown/contradictory broker states are not auto-linked. Tests passed in [run 39050424898](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39050424898).
- [x] Add repository-only status transition persistence with an allowlist of state transitions, optimistic version/state compare-and-set, broker-order-ID uniqueness handling, atomic audit event, credential-field validation and idempotent same-state no-op. [Run 39050941218](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39050941218) passed 261 tests, 1 warning, plus SQLite/PostgreSQL 16 reversible migrations.
- [x] Add pure Upstox per-order trade normalizer using documented `trade_id`, `order_id`, `instrument_token`, `transaction_type`, `quantity`, `average_price` and `exchange_timestamp`; unknown/malformed fields are rejected. [Run 39052075052](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052075052).
- [x] Add repository-only `record_broker_fill()` keyed by broker connection + stable trade ID; atomically persist fill and linked intent audit event; identical replays are no-ops, conflicting replays fail closed, and cross-connection intent linking is rejected. [Run 39052203329](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052203329) passed 274 tests.
- [x] Validate each linked fill against the already broker-ID-linked intent: instrument, side, order type, product, positive integer requested quantity, per-fill/aggregate quantity ceilings, and limit/stop-limit price protection. Reject fills before persistence when any check fails. [Run 39052939770](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052939770) passed 279 tests, 1 warning, plus SQLite/PostgreSQL 16 migration checks.
- [x] Validate linked fills against the intent snapshot (instrument/side/product/type, linked broker order ID, integer order quantity, aggregate quantity ceiling and limit-price protection); safely link previously unmatched fills later after revalidation. [Run 39053352921](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053352921) passed 281 tests, 1 warning.
- [x] Reconcile out-of-order status/fill observations against persisted fill evidence. Stale active states cannot erase partial/full trade evidence; partial fills plus cancellation are represented as `PARTIALLY_FILLED_CANCELLED`; conflicting full/partial or reject/fill evidence is quarantined as `RECONCILIATION_REQUIRED`. [Run 39056392873](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056392873) passed 294 tests, 1 warning, with SQLite/PostgreSQL 16 migration checks.
- [x] Implement the read-only worker in `backend/app/services/live_order_reconciliation_worker.py`: validates user-owned Upstox connection and usable token, claims/renews/completes the per-connection lease, uses only the GET-only client, applies bounded retry, normalizes daily trades and order-book records, strictly matches intents, persists unmatched fill identities, links verified fills, resolves state against trade evidence, and returns safe summary counts. No worker schedule/API trigger is wired, and CI uses mocks only.
- Remaining: add durable operator-facing run summaries/manual-review queue, confirm order/trade pagination and session/day boundaries against current official API responses, cover sliced orders, and plan a read-only sandbox verification. Current worker rejects invalid envelopes, stops on token/permission errors, retries bounded transient failures, and records unmatched fills without linking. It does not calculate positions or update local Order/Execution rows.
- No order-placement call in this phase.

### Gate 3 — Disabled sandbox submission workflow
- Transactionally persist intent, risk decision, audit and outbox before network I/O.
- Unknown submission after timeout/crash is reconciled; never blindly retry an ambiguous POST.
- Test crashes before/after broker acceptance, concurrent workers, rate limits, token expiry, rejection and cancellation races with mocks/sandbox only.
- Global live-submit switch stays hard-disabled in deployed configuration.

### Gate 4 — Operational readiness
- Verify account kill switch, portfolio risk recheck/reservation, alerts, safe audit redaction, monitoring, backup/restore, migration rollback and incident runbook.
- Verify real authenticated market-data stream separately; stream verification is not order-path certification.
- Resolve process-local WebSocket state before using multiple API workers.

### Gate 5 — Explicit controlled release
- Requires successful prior gates, official API contract verification, broker/account configuration, applicable compliance review and explicit user authorization.
- Start with a limited manually confirmed pilot and low risk limits. No autonomous live rollout by default.

## Completion/reporting rules

- After every meaningful change, update `PROGRESS.md`; update `AUDIT_REPORT.md`, `README.md`, `ARCHITECTURE.md` and safeguards when the verified behavior or safety boundary changes.
- Commit changes to `tradepro-improved` and verify the exact commit SHA and GitHub Actions result. A successful older workflow does not validate a newer commit.
- Distinguish implemented, unit-tested, sandbox-tested, staging-verified and production-verified states. Never claim a real Upstox session or order test without evidence.
- Keep live trading disabled until all release gates and explicit authorization are complete.


### Read-only reconciliation client — implementation started
- [x] Added `backend/app/brokers/upstox/reconciliation_client.py`, a narrow fixed-path GET-only client for order book, order details, order history by order ID/tag, and per-order trades. It exposes no place/modify/cancel methods and classifies 401/403/429/5xx/network/timeout/non-JSON errors without returning response bodies.
- [x] Added contract tests for documented endpoints, query parameters, missing token, sanitized failures and absence of write methods. [Run 39056868434](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056868434) passed **309 tests, 1 warning**; SQLite/PostgreSQL 16 migration checks passed.
- [x] Implement worker orchestration, token/connection validation, bounded retries, job lease, order matching, fill import and safe in-memory summary counts. Verified with mocked worker tests; the code can make read-only GET calls only when explicitly invoked with a valid user-owned connection. It is not scheduled or wired into an API route.


### Worker lease foundation — implementation checkpoint
- [x] Added `LiveReconciliationLease` schema and reversible Alembic revision `202610170003` for one lease per broker connection.
- [x] Added `LiveReconciliationLeaseRepository` with bounded lease durations, atomic claims, expiry/reclaim, lease renewal, ownership checks and token-guarded completion. A stale worker cannot complete a newer worker's lease.
- [x] Added lease tests for contention, expiry/reclaim, stale-owner completion, renewal, cross-user ownership and invalid lease duration. [Run 39057273255](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39057273255) passed 318 tests, 1 warning; SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade passed.
- [x] Connect the lease to the read-only worker orchestration and add a PostgreSQL concurrency test proving only one simultaneous claim succeeds. [Lease concurrency test commit](https://github.com/tarunsharma2610-del/tradepro-improved/commit/bf0c2b707aaa023a961f899502ed9f2ae4d265a4).
- [x] Verify official API day-window semantics and document pagination boundaries; persistent run summaries and manual-review visibility are implemented. Official order-book and get-trades-for-day endpoints are current-day, with no documented pagination parameters. Historical trades use a separate paginated API that is not wired into this worker. No live/sandbox request was made.


### Latest Phase 2 worker verification — 2026-10-17
- Worker implementation: [`live_order_reconciliation_worker.py`](backend/app/services/live_order_reconciliation_worker.py), commit [`4ee8427`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/4ee8427f890f7c31021e30f7b36177e2f3f227c3). It is GET-only by dependency construction and is not automatically scheduled or wired to an API route.
- Regression coverage now includes successful matching/fill linking, repeat-run deduplication, cross-user rejection, busy lease, missing token, no mutation when either read fails, bounded transient retry and Retry-After, 403 no-retry, malformed envelope/data rejection, and UNKNOWN execution status recovery when later trade evidence arrives.
- Latest code test run [39058734080](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39058734080) passed **338 tests, 1 warning**; SQLite/PostgreSQL 16 reversible migration checks passed. No live Upstox request, order action, production migration or accounting update occurred.
- Historical Phase 2 status superseded: current-day API/session boundary has been checked against official Upstox documentation; see the current checkpoint at the top of this file. Historical-trade retrieval remains separate future work, not part of this worker's current-day contract.


### Durable reconciliation run summary checkpoint — 2026-10-17
- Added `LiveReconciliationRun`, migration `202610170004`, and `LiveReconciliationRunRepository`; worker now persists a count-only summary and sanitized status/error category for each leased run.
- Test commit [`0e69fb2`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/0e69fb2efea692f2f675604ef3312cb1954ecc39) passed [run 39059271937](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059271937): **340 passed, 1 warning**, with SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks.
- The run summary contains only known non-negative counters; no broker payload, token, header or exception text is stored. A run left in `RUNNING` after process crash is visible as incomplete, but automatic stale-run recovery and operator review UI remain future work.


### Durable manual-review issue checkpoint — 2026-10-17
- Added `LiveReconciliationIssue`, migration `202610170005`, and `LiveReconciliationIssueRepository`; the worker records safe, deduplicated issues for unmatched orders, malformed order/trade rows, trade persistence conflicts, fill-link conflicts and status-transition conflicts.
- Exact latest code commit [`71b5668`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/71b5668533f0461c12374319e496665cbda7e61c) passed [run 39059749652](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059749652): **342 passed, 1 warning**, plus SQLite/PostgreSQL 16 reversible migrations. An earlier run failed because normalization errors were caught by the persistence-conflict branch; that was fixed by separating normalization from persistence, and the latest exact commit is green.
- Historical checkpoint superseded: run summaries and safe review issues are exposed through owner-scoped read API/UI; stale-run recovery and crash-boundary tests are covered. A privileged issue-resolution workflow and historical-trade API integration remain separate future work. No real broker request/order action or accounting update occurred.


### Owner-scoped reconciliation read API checkpoint — 2026-10-17
- Added run and issue list endpoints, typed response schemas and a query repository; queries always scope by authenticated `user_id`, with optional connection/status/type filters and a hard maximum limit of 100.
- Added HTTP tests for unauthenticated rejection, cross-user isolation, connection filtering, status filtering, invalid status/limit and safe response fields. Exact code commit [`f65b4ba`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/f65b4ba20ce9a1dacfe40580d8042cd98f36c19f) passed [run 39060230705](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39060230705): **345 passed, 1 warning**, plus SQLite/PostgreSQL 16 reversible migrations.
- The API is read-only: no issue resolution, run trigger, broker call or order action is exposed. Frontend UI and historical trade window support remain open.


### Reconciliation review UI checkpoint — 2026-10-17
- Added `frontend/app/reconciliation/page.tsx` and dashboard navigation link. The page lists recent safe run summaries and issues from the authenticated read API, supports issue-status filtering and manual refresh, and exposes no action to trigger reconciliation or resolve an issue.
- Exact commit [`e4343dc`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e4343dcb225c1f332b6c89399694d0a29a5df739) passed [frontend checks](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39060564743) and [backend CI](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39060564787): TypeScript/Next.js build succeeded; **345 backend tests passed, 1 warning**, and SQLite/PostgreSQL 16 migration checks passed.
- Remaining: issue-resolution workflow, stale-run recovery, crash-boundary tests and historical trade window/pagination support. No live broker request or order action occurred.


## Reference-repository audit — 2026-10-20

See [REFERENCE_REPOSITORY_AUDIT.md](REFERENCE_REPOSITORY_AUDIT.md) for the source-level comparison and integration priorities.

### Current priority gate — updated 2026-10-20

1. The recovered live-fill accounting files and supporting model/schema dependencies are present again. Revisions `202610180006` → `202610180007` → `202610180008` now form a valid chain after `202610170005`.
2. Code/test checkpoint [run 39475387511](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39475387511) passed **355 tests, 1 warning**, including SQLite and PostgreSQL 16 upgrade → downgrade → re-upgrade checks.
3. This does not make live-fill accounting end-to-end complete: service is deliberately unregistered; ingestion, worker integration, shared live order/status accounting and real-account reconciliation remain outstanding.
4. Next: continue Phase 2 reconciliation release gates and crash/recovery/fill-linkage checks. Integrate the service only through a separately reviewed and tested path.
5. Live order submission remains disabled; no real orders for testing. All work stays in `tradepro-improved`; original `Tradepro` remains untouched. Do not delete the recovered files without explicit user approval.


## Safety-branch port checkpoint — 2026-10-21

- Main code/test checkpoint `3f210e592c8aa2e643e536a04f186da8187bc06b`; [CI run 39480002328](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39480002328) passed **431 tests, 1 warning**, with SQLite/PostgreSQL 16 reversible migration checks passing.
- Ported pure Upstox response parsing and isolated broker trade staging with tests. Staging rejects missing exchange timestamps and does not update executions, positions, portfolio cash, or local order status.
- See [`SAFETY_BRANCH_PORT_MATRIX.md`](SAFETY_BRANCH_PORT_MATRIX.md) for 21 safety-only test modules and dependency/port decisions. Branch test counts are not directly comparable because source and test trees differ.
- Next: audit and test child-order reconciliation/partial-fill aggregation; keep fill promotion and broker writes disabled until transaction, idempotency, recovery, and account-isolation gates pass.


## Cumulative fill-accounting guard — 2026-10-21

- Added aggregate per-child cap in `LiveFillAccountingService`: previously accounted executions plus the new trade cannot exceed the broker-confirmed child filled quantity.
- Added regression test for two distinct trade IDs attempting to overrun the same child fill total. Exact-head [run 39480669799](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39480669799) passed **432 tests, 1 warning**, with SQLite/PostgreSQL 16 migration checks passing.
- Next architecture gate: reconcile the worker's `BrokerFillIdentity` intake with the staging/accounting path's `BrokerTradeRecord`; do not dual-write or connect them until idempotency and transaction boundaries are explicit.


## Child-order reconciliation port — 2026-10-21

- Ported child-order status/fill reconciliation with current-main schema compatibility. It validates the broker snapshot against durable staged trade quantities and weighted average price, locks the child row, rejects fill regressions/terminal-state conflicts, and updates only child status/fill quantity.
- Exact-head [run 39481385581](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39481385581) passed **438 tests, 1 warning**, including SQLite/PostgreSQL 16 reversible migration checks.
- Remaining architecture gate: distinguish the intent-based `BrokerFillIdentity` workflow from the manual Order `BrokerTradeRecord`/`BrokerOrder` workflow, or design an explicit transaction-safe bridge. No live order submission or automatic accounting promotion is enabled.


## Phase 2 resume point — 2026-10-21

Latest main-branch checkpoint is `0ce59a7965e3e96a425fa8ae30c841eb0cb755bc`; exact-head [CI run 39552821228](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552821228) passed 461 backend tests, the broker-write guard, and SQLite/PostgreSQL 16 migration cycles. Phase 2 now covers stale-run recovery, incomplete-summary UI warning, inconsistent lease-state rejection, and eventual recovery after lease-release/summary-persistence crash. Next: review transaction atomicity between lease completion and run-summary finish and add lost-lease/ordering tests. Keep live submission and automatic accounting promotion disabled.


## Phase 2 resume point — 2026-10-21

Latest verified code/test HEAD `8f967adaa2328f16a0a08a104c3ec394e62f9310`; exact-head [CI run 39553655005](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39553655005) passed 463 backend tests, the broker-write guard, and SQLite/PostgreSQL 16 migration cycles. Terminal run-summary persistence and lease release are now atomic; stale owners are marked `LEASE_LOST` without releasing a newer owner's lease. Next: audit cancellation, unexpected exceptions, and lease renewal/expiry concurrency. Keep live submission and automatic accounting promotion disabled.


## Phase 2 resume point — 2026-10-21

Historical checkpoint superseded by the lease-race audit: code/test HEAD `00ee9bad0e962d92244da6f63da1e46ba058ad6f` passed 472 tests, source guard and SQLite/PostgreSQL 16 migration checks in [run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386). Large-batch expiry and renewal races are now covered. Keep live submission and automatic accounting promotion disabled.


## Phase 2 resume point — 2026-10-21

Historical checkpoint superseded: renewal remains every five records; UI marks `LEASE_LOST` and `WORKER_INTERRUPTED` summaries incomplete. Slow-record/high-volume expiry races and transaction-level fencing were subsequently audited and passed in CI run [39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386). Keep live submission/accounting promotion disabled.


## Phase 3 live-fill accounting checkpoint — 2026-10-21

- Latest reviewed code HEAD at this checkpoint: `ef60ec93d39543c644dfd557f6f73b48ab793b60`.
- Exact-head [Backend CI run 39609474410](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39609474410) completed successfully: **485 passed, 1 warning in 30.25s**; broker-write boundary guard passed; SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed.
- The one warning is non-failing; CI logs also report GitHub Actions Node.js 20 deprecation notices.
- Existing safeguards cover replay identity/charge validation, broker-confirmed fill quantities, cumulative child/order quantity limits, rejected-order protection, and atomic live-position/execution updates. This CI result verifies the current HEAD, not completion of all Phase 3 requirements.
- **Open Phase 3 requirement:** define and test the fee-allocation contract when a broker contract-note charge total covers multiple fills. The current API accepts a per-promotion breakdown and validates that its total equals its six components; it does not itself establish how a multi-fill contract-note total is allocated. Do not claim this issue resolved or wire in a coordinator/identity bridge until the rule is designed and regression-tested.
- Safety constraints unchanged: do not enable live broker submission, automatic accounting promotion, or automatic scheduling; keep `BrokerFillIdentity` and `BrokerTradeRecord` separate pending a reviewed bridge design. Phase 2 remains closed.


## Phase 3 checkpoint refresh — 2026-10-21

- **Repository boundary:** all current Phase 3 work is confined to `tarunsharma2610-del/tradepro-improved`, branch `main`. The original `tarunsharma2610-del/Tradepro` is a protected baseline and must not be modified.
- **Current HEAD at audit start:** `3b5c8831d4f3475eee320176b3c06bdbd5364bd2` (source-ledger design-gate documentation). The documentation synchronization commit created after this note requires its own exact-HEAD CI result.
- **Latest confirmed backend CI during this audit:** [run 39618611385](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39618611385) completed successfully on **commit `49f95bdd5f20ee99b21a573087c6e97a9bc03526`**, with **485 passed, 1 warning in 30.65s**. The broker-write boundary guard and SQLite/PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade steps passed. This run is an older SHA, not current HEAD; do not label later commits green based on it.
- **Phase 3 status:** in progress. Current blocker is verified actual-charge evidence and an approved allocation basis. Reviewed Upstox documented APIs provide trade data, aggregate charges, or estimates, but no verified per-fill actual-charge source/contract-note ingestion capability was found in the reviewed adapter/API catalogue. Do not treat estimates as actual charges or allocate aggregate totals by guess.
- **Next engineering sequence:** establish authoritative source format and retention/security boundary; then implement immutable source evidence and per-fill allocation records, migration, transactional reconciliation/idempotency, and required regression tests; finally verify exact-HEAD CI.
- **Safety:** live broker submission, automatic accounting promotion, and automatic scheduling remain disabled. Phase 2 remains closed. This checkpoint is status tracking, not a claim that Phase 3 charge allocation is implemented.

## Latest Phase 3 continuation checkpoint — 2026-10-21

- Current reviewed repository HEAD at checkpoint start: 03b8e73cb918ab22e8c2a3857b77108c4a157942. This file's update will create a newer documentation-only commit.
- Re-inspected backend/tests/test_live_fill_accounting_service.py and backend/app/services/live_fill_accounting_service.py. The parametrized regression test includes ESTIMATED, AGGREGATE_CHARGES, TRADE_CHARGES_API and BROKER_ESTIMATE and asserts rejection before Execution/LivePosition writes. The service only accepts the literal source BROKER_REPORTED and validates reference presence/length, paise precision, non-negative components and total equality.
- Important limitation: the source string and reference are caller-supplied; this validation is not cryptographic/source provenance. No real per-fill actual-charge evidence path has been verified, so an arbitrary caller can still mislabel a source. This is not fixed by the negative-source tests.
- Exact-HEAD CI: not verified. The GitHub connector's workflow-run wrapper filters to pull-request-triggered runs; direct workflow-run endpoint access was rejected by the connector, so prior empty results cannot establish that no push run exists. Do not claim CI success or failure from these empty results. Inspect the actual Actions page/run for the newest SHA before marking green.
- Do not add a production importer, allocation formula, or schema migration until authoritative evidence defines the file structure and component-specific allocation basis. Continue with provenance design only where it can be made correct without assuming unknown broker fields.
- Safety and scope unchanged: all changes belong only in tarunsharma2610-del/tradepro-improved; original Tradepro is protected. Phase 2 remains closed. Live broker submission, automatic accounting promotion, and automatic scheduling remain disabled.
