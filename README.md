## Phase 3 source-reconciliation safety correction — 22 October 2026

- Code review identified a safety gap in `backend/app/services/broker_charge_allocation_persistence_service.py`: the service previously marked rows `RECONCILED` merely because calculated allocations summed to the caller-provided component total. That is arithmetic reconciliation, not independent verification of a broker contract-note source total.
- Fixed in commit `fce01b98ce33760e3361991e8d2ffba01b0ad281`: newly persisted allocations remain `PENDING_RECONCILIATION`; this service clears the reconciliation reference and does not promote them to `RECONCILED`. A separate source-verification workflow must establish provenance and validate the source component total before promotion.
- Updated regression expectation in commit `8c38ab8ecc8114f392e11ea988ac25c3d7c8e2df` to assert pending status and no reconciliation reference even when arithmetic totals match.
- **CI pending:** the code/test commits and documentation commits need a fresh exact-head run. Do not describe this correction as verified until CI passes.
- This deliberately fails closed: matching a number supplied by the caller is not treated as proof that it came from an authentic contract note. Contract-note authenticity/parser, component-specific allocation methodology, source-total verification, and controlled accounting integration remain open Phase 3 gates.
- Keep PR #6 draft/unmerged pending exact-head CI and broader review. Live broker submission and automatic accounting promotion remain disabled.
- Scope remains exclusively `tarunsharma2610-del/tradepro-improved`; do not modify original `Tradepro`.

---

## Phase 3 allocation edge-case hardening — 22 October 2026

- Code review found a rounding edge case in `backend/app/services/broker_charge_allocation_service.py`: when a source total was one paise and a zero-weight fill ID sorted before positive-weight IDs, the deterministic largest-remainder tie-break could assign that paise to a fill whose weight was zero.
- Fixed in commit `1f04b5d0c0fc07af15eadd4fe7c70f14ff054f91`: only strictly positive-weight fills participate in residual ranking. Zero-weight fills remain in the result at INR 0.00.
- Added regression coverage in commit `347f9588485bd7452d949dd816ba6966196354f6` for the one-paise/tied-remainder case and the two-paise case.
- **Verification pending:** CI for these code/test commits and the following documentation commits must pass on the exact latest branch head before this fix is called verified. The prior PostgreSQL concurrency success does not include this new change.
- Existing successful PostgreSQL concurrency run: `39737580271` on `d59e7d8`, `527 passed, 1 warning`, with `TEST_POSTGRES_URL` set. New allocation edge-case fix is a separate code change and needs fresh CI.
- Source authenticity, component-appropriate allocation policy, exact source-total reconciliation against real contract-note data, and accounting integration remain release gates. Keep PR #6 draft/unmerged; live broker submission and automatic accounting promotion remain disabled.
- Scope remains exclusively `tarunsharma2610-del/tradepro-improved`; do not modify original `Tradepro`.

---

## Phase 3 PostgreSQL concurrency verification — 22 October 2026

- **Verified green:** GitHub Actions run `39737580271`, commit `d59e7d8a613471c3134b8d0c6dcdb326713ce7eb`, completed successfully. Job `Backend pytest` passed; log summary: `527 passed, 1 warning in 32.20s`.
- The test job environment explicitly set `TEST_POSTGRES_URL` to the dedicated PostgreSQL 16 service. The suite reported no skipped tests, so the opt-in PostgreSQL integration test was not skipped in this run.
- The preceding fixture corrections addressed (1) missing `Base` import and (2) parent user row not flushed before dependent records. The subsequent exact-head run is green.
- This is evidence that the new PostgreSQL concurrency integration test completed successfully in the suite. Keep its specific invariant documented: competing independent sessions target one evidence/component with different fill sets; only one allocation should persist, without partial/mixed rows.
- Remaining gates are not closed by this test: authenticated contract-note provenance/schema, reviewed charge-component allocation methodology and residual handling, reconciliation against source totals, and controlled integration with live-fill accounting still need review/acceptance. Live broker order submission and automatic accounting promotion remain disabled.
- PR #6 remains draft/unmerged pending review of the full change and its broader release gates.
- Scope remains exclusively `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is not the target.

---

## PostgreSQL concurrency-test fixture correction — 22 October 2026

- Inspected failed workflow `39737225306` on commit `d6a9cab`. PostgreSQL test failed during fixture setup, before the race assertion: the `broker_connections.user_id` foreign key referenced a user not yet flushed to PostgreSQL. The suite result was `1 failed, 526 passed, 1 warning`.
- Fixed in code commit `0c4d5133a1224fbac5b0eb2cafb3b7c195612d40`: explicitly flush the user parent row before adding dependent portfolio/instrument/connection rows. No production behavior was changed.
- **Pending:** exact-head CI for `0c4d513` and subsequent documentation commits. Do not infer that the concurrency test passes from this fixture correction alone.
- Acceptance remains: on PostgreSQL, two independent sessions race different fill sets against the same evidence/component; exactly one complete allocation set succeeds, the other fails closed, and no partial/mixed ledger remains.
- PR #6 remains draft/unmerged until this test and exact-head CI pass. Contract-note authenticity, allocation methodology review, and accounting integration remain separate gates. Live broker submission and automatic accounting promotion remain disabled.
- Scope remains exclusively `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is not the target.

---

## PostgreSQL concurrency-test CI correction — 22 October 2026

- First run of the new integration test failed before reaching the race assertion: `NameError: Base is not defined` in test schema setup. Suite result was `1 failed, 526 passed, 1 warning` on commit `1859179`.
- Fixed by importing `Base` from `app.core.database` in commit `eb4b6c4`. This is a test setup correction only; it does not weaken production checks.
- **Pending verification:** CI for `eb4b6c4` and the documentation commits is not yet confirmed green. The PostgreSQL test's runtime race behavior remains unverified until it executes successfully against the CI PostgreSQL 16 service.
- The test provisions isolated records and races two independent sessions against one evidence/component. Acceptance criterion: exactly one allocation request succeeds, the other fails closed, and exactly one allocation row remains.
- Keep PR #6 draft/unmerged until exact-head CI passes and the concurrency result is inspected. Evidence authenticity, valid charge basis, and integration with live accounting remain separate gates. Live broker submission and automatic accounting promotion remain disabled.
- All work stays in `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is not the target.

---

## Phase 3 PostgreSQL concurrency test added — 22 October 2026

- Added `backend/tests/test_broker_charge_allocation_postgres_concurrency.py`, an opt-in integration test that uses `TEST_POSTGRES_URL`, two independent SQLAlchemy sessions and concurrent threads to race incompatible single-fill allocations against one reviewed evidence record/component. The expected result is exactly one winner and one persisted allocation, with no mixed/partial fill set.
- The existing `.github/workflows/backend-tests.yml` provisions PostgreSQL 16 and exports `TEST_POSTGRES_URL`; the integration test creates ORM metadata in that dedicated CI test database because pytest runs before the later Alembic migration verification step.
- Test setup was corrected to build the required portfolio → instrument → order → broker-order → broker-trade foreign-key chain. Test commits: `a69e083`, `4b5e8cc`, `1859179`.
- **Pending:** this new PostgreSQL concurrency test has not yet been confirmed green by exact-head CI. A green prior run does not cover these commits. If CI fails, inspect the test output and correct the fixture or concurrency assumptions before claiming safety.
- The evidence-row `SELECT ... FOR UPDATE` is the serialization point. This integration test is the empirical verification needed; SQLite-only unit tests are insufficient.
- PR #6 remains draft/unmerged pending successful exact-head CI and review. Contract-note authenticity, component-appropriate allocation basis and live accounting integration remain separate release gates. Live broker submission and automatic accounting promotion remain disabled.
- Scope remains exclusively `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is not the target.

---

## Phase 3 continuation — PostgreSQL concurrency test still required — 22 October 2026

- Latest confirmed successful workflow remains `39735969492` on commit `a94760f66d5405a563cca25960c95f00ba2a4e5f`; it is a PR-triggered backend-tests run. No later code change is represented by that result.
- Rechecked the allocation persistence service and test setup. The default test fixture explicitly forces SQLite in-memory; it does not exercise PostgreSQL row locks. The workflow file is named `.github/workflows/backend-tests.yml` (not `ci.yml`).
- Source evidence is locked with SQLAlchemy `with_for_update()` before fill rows and existing allocations are queried. This is a plausible PostgreSQL serialization point but is not yet race-tested with two independent transactions.
- Next step remains an opt-in integration test using a dedicated PostgreSQL test database/URL and two independent sessions racing different fill sets against the same evidence/component. The test must assert one complete winner and one fail-closed conflict, with no partial rows. CI must provision PostgreSQL or clearly report the integration test as skipped; a skipped test is not proof of safety.
- Keep PR #6 draft/unmerged pending that test and exact-head green CI. Source document authenticity, allocation-basis review and accounting-service integration remain separate release gates. Live broker order submission and automatic accounting promotion remain disabled.
- All changes in this project remain confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is not the target.

---

## Phase 3 checkpoint — concurrency safeguard and verification boundary — 22 October 2026

- Confirmed latest recorded successful GitHub Actions run for this branch: `39735332590`, commit `9ed382f5872faaf2c20f71e4292ac5cc3baf322f` (backend tests, success).
- The source-evidence `SELECT ... FOR UPDATE` lock is implemented in `backend/app/services/broker_charge_allocation_persistence_service.py` before fill-set lookup/allocation persistence. This is intended to serialize concurrent allocations for the same evidence on PostgreSQL.
- **Important verification limit:** the green run is for commit `9ed382f`; it does not include any later changes. The current test file still lacks a PostgreSQL-backed concurrent allocation test. Do not claim race-safety has been empirically proven until that test runs against PostgreSQL with two independent sessions/transactions.
- Next implementation step: add an opt-in integration test using a dedicated PostgreSQL test URL (e.g. `TEST_POSTGRES_URL`) that starts two transactions attempting incompatible fill sets against one evidence/component; verify the second waits/re-reads the ledger and fails closed without partial rows. If CI does not provide a PostgreSQL service for pytest, add a dedicated PostgreSQL test job rather than treating SQLite `FOR UPDATE` behavior as equivalent.
- After the test, run full exact-head CI, inspect logs, and update this checkpoint with the observed result. Keep PR #6 draft/unmerged until verified.
- Charge-note authenticity, appropriate per-component allocation methodology, and accounting-service integration remain review gates. No automatic accounting promotion or live broker submission is enabled.
- Scope remains exclusively `tarunsharma2610-del/tradepro-improved`; do not modify original `Tradepro`.

---

## Phase 3 concurrent allocation serialization — 22 October 2026

- Latest previously verified CI head `9e07a5c95401ab3ccfd6c32a8223721dd573b928` passed, including backend pytest, broker write-boundary enforcement, and Alembic upgrade/downgrade/re-upgrade on SQLite and PostgreSQL 16.
- Code commit `34dd6cebb424f50963a3ca788de37490d39bdb60` adds a row-level lock on the reviewed `BrokerChargeEvidence` record before locking fill rows and inspecting/inserting component allocations. Rationale: locking only the target fills does not serialize two concurrent requests using disjoint fill sets against the same evidence/component; both could otherwise observe an empty ledger and insert different subsets. PostgreSQL's evidence-row lock provides a per-source serialization point.
- **Pending validation:** run exact-head CI for `34dd6ce` and the documentation commits. SQLite does not enforce `FOR UPDATE`; green SQLite tests alone are not proof of concurrency behavior. Add or run a PostgreSQL-backed concurrent test before treating race safety as fully verified.
- No live accounting promotion was enabled. Evidence authenticity and the economic correctness of a selected allocation basis remain review-gated.
- PR #6 stays draft/unmerged. All changes remain confined to `tarunsharma2610-del/tradepro-improved`, not original `Tradepro`.

---

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

<!-- Phase 3 docs sync: df8b73a2971cbcee949efa14e98bc16a070bf093 -->

> **Documentation synchronization:** commit [df8b73a2971cbcee949efa14e98bc16a070bf093](https://github.com/tarunsharma2610-del/tradepro-improved/commit/df8b73a2971cbcee949efa14e98bc16a070bf093) synchronized the Phase 3 checkpoint across all 16 top-level project Markdown documents. Verify the exact HEAD's CI before treating the documentation checkpoint as fully green.

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

------

## Historical checkpoint — formerly marked Current verified checkpoint — 21 October 2026

- **Latest CI-verified `main` HEAD:** `7798f03200ba823d51bdd359539594b38e9830e1`; exact-head backend CI [run 39567592850](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567592850) passed.
- **Latest code/test checkpoint:** `00ee9bad0e962d92244da6f63da1e46ba058ad6f`; exact-head backend CI [run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) passed **472 tests, 1 warning**, the broker-write boundary guard and SQLite/PostgreSQL 16 reversible migration checks.
- The slow-persistence/lease-race audit is complete: the PostgreSQL row-lock test proves reclaim waits while a fenced write transaction is open; `test_postgres_high_volume_expiry_races_never_resurrect_stale_lease` passed 20 concurrent expiry-boundary renewal/reclaim races. Expired owners cannot renew, and ownership generation/token advance is verified.
- Official Upstox V2 order-book and get-trades-for-day endpoints are current-day endpoints without documented pagination parameters. Historical trades are a separate paginated API; that API is not wired into the Phase 2 worker.
- **Current task:** synchronize the remaining historical architecture/roadmap/reference-audit notes. This documentation commit needs its own exact-head CI and a final stale-status scan before Phase 2 is formally closed. Phase 3 remains blocked until then.
- Live broker submission, automatic accounting promotion and automatic scheduling remain disabled. The original `Tradepro` repository remains untouched.

------

# Tradepro Improved

A separate improvement track for Tradepro. The original `Tradepro` repository and its `main` branch remain untouched.

## Safety-first development rules

- Preserve existing functionality while fixing verified defects.
- Keep paper trading as the default mode.
- Keep live trading disabled until broker execution, order reconciliation, duplicate-order prevention, risk limits, and an emergency kill switch are implemented and tested.
- Never commit API tokens, OAuth secrets, passwords, or other credentials.
- Validate changes with automated tests and build checks before deploying.

## Historical checkpoint — formerly marked Current Phase 2 checkpoint — 21 October 2026

- Reconciliation crash recovery and transaction-level lease fencing have passed backend CI on the recorded checkpoint (470 tests, 1 warning, broker-write guard, SQLite/PostgreSQL 16 migration cycles).
- Latest test commit [e56bf4c66f74b875a3ba8fe388138a9d688dd1e2](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e56bf4c66f74b875a3ba8fe388138a9d688dd1e2) adds failed-commit rollback coverage. Exact-head backend CI [run 39564568154](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39564568154) passed 471 tests (1 warning), broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles. Documentation HEAD `adb69aeb05b70ba4fa9095fc73d9dea033d31eec` also passed backend CI [run 39565251793](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39565251793).
- Phase 2 is in final documentation verification: code/test HEAD `00ee9bad0e962d92244da6f63da1e46ba058ad6f` passed [CI run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) with 472 tests, source guard and SQLite/PostgreSQL 16 migration checks. The documentation sync must pass its own exact-head CI before closure. Intent-based BrokerFillIdentity and manual BrokerTradeRecord remain separate; live submission, automatic accounting promotion and automatic scheduling remain disabled. See MASTER_ROADMAP.md and SAFETY_BRANCH_PORT_MATRIX.md for authoritative scope.

## Historical checkpoint — formerly marked Current status

The original source tree has been imported into this repository. Recent improvements include:
- A dashboard at `/` with portfolio summaries and navigation.
- Backend input validation for orders and rejection of invalid broker prices.
- One-time, expiring broker OAuth state backed by a database nonce digest.
- Paper LIMIT-order matching in the worker, using the shared transaction-cost, cash and position accounting.
- Automated backend and frontend checks in GitHub Actions.
- An environment-controlled emergency kill switch blocks new strategy entries when `AUTOMATED_ENTRIES_ENABLED=false`; strategy exits remain enabled.

See [AUDIT_REPORT.md](./AUDIT_REPORT.md) for findings, verification links and remaining work. See [REFERENCE_REPOSITORY_AUDIT.md](./REFERENCE_REPOSITORY_AUDIT.md) for the external repository comparison and safe integration plan.

## Important trading behavior

- **Paper market orders:** use a current Upstox quote for the simulated fill; the application does not invent a price when the quote is unavailable or invalid. The quote parser requires the exact requested instrument key and will not substitute another instrument's price if that key is missing.
- **Paper limit orders:** remain pending until the worker checks them during market hours (about every 5 minutes). A BUY can fill when LTP is at or below its limit; a SELL can fill when LTP is at or above its limit. The matcher uses the shared accounting engine, checks available cash / delivery holdings, and users can cancel pending orders from the portfolio order history.
- **Emergency kill switch:** set `AUTOMATED_ENTRIES_ENABLED=false` in the backend environment and restart the API/worker to stop automated strategy entries. Existing strategy exits are intentionally not blocked. This switch does not stop manual paper orders.
- **Live trading:** is **not implemented** by the shared execution service. Phase 1 has durable intent/idempotency/outbox storage; Phase 2 has pure order/trade normalization, strict local-intent matching, versioned status persistence and idempotent individual fill identity persistence. These do not fetch broker data, aggregate partial fills into account accounting, or submit/cancel orders. Setting `TRADING_MODE=LIVE` is not sufficient to make real broker orders happen; do not treat this repository as ready for live trading.
- **Portfolio settings:** each portfolio has a manual settings form for renaming and optional risk controls: maximum daily realized loss, estimated open exposure, per-order value, simultaneous open/pending positions and orders per day. Controls are disabled until enabled. Limits are checked for paper manual and strategy orders; closing/reducing orders are allowed. Exposure is a conservative cost-basis estimate, not broker margin.
- **Upstox WebSocket:** authenticated endpoints are POST /api/v1/market-data/stream, GET /api/v1/market-data/stream, and DELETE /api/v1/market-data/stream. The portfolio order form has Start/Stop controls for the selected instrument and displays fresh LTP updates. Subscribe only to active catalog keys. Streams are process-local and disappear on API restart; use one API worker until a shared stream/cache layer is added. ExecutionService uses fresh stream ticks when available and otherwise falls back to REST.
- **Instrument sync:** admin POST /api/v1/instruments/sync now reconciles absent/expired instruments only after a completeness gate passes. A separate GitHub Actions workflow successfully downloaded the real official Upstox master and synced it into temporary in-memory SQLite (123,930 active instruments); it never touched production.
- **Migration/deployment:** the portfolio-risk migration is CI-tested on clean SQLite. Back up the deployed database and verify alembic upgrade head in staging before deploying to an existing database.
- **Remaining work:** broker reads/worker and full reconciliation (including fill-vs-intent economic validation, partial-fill aggregation/accounting and out-of-order updates), live order placement, a global account-level live-trading kill switch, exchange holiday calendar, real authenticated WebSocket verification with a user OAuth session, multi-worker stream sharing, and staging migration verification. Live trading is not implemented and must remain disabled.


## Verified status — 17 October 2026
- Latest backend CI after documentation updates: [run 39039714203](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39039714203) — **203 tests passed, 1 warning**; clean SQLite Alembic migration verification passed.
- Safety regression coverage includes exact-instrument quote matching, portfolio order-count cap, incomplete instrument snapshot rejection, WebSocket silence reconnect, and V3 authorization URL validation.
- Official Upstox instrument master was downloaded and synchronized into a disposable in-memory SQLite database: **123,930 active instruments** ([verification workflow](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037390129)). This did not modify production data.
- Frontend TypeScript/build verification for the stream controls passed ([run 39037642093](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037642093)).
- **Not production-ready for live trading:** real OAuth WebSocket verification, multi-worker stream sharing, backup-safe staging migration, idempotent live submission and broker reconciliation remain open. Keep live trading disabled; no live orders have been submitted.


## Live-order idempotency and reconciliation — design review (17 October 2026)

The approved live-trading design is now in **Phase 1 implementation** (durable records/repository safeguards only). See [`LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`](LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md) for the detailed architecture, implementation sequence and acceptance tests.

The design requires durable idempotency keys, payload-hash conflict detection, a committed intent/outbox before broker I/O, explicit UNKNOWN state after ambiguous submissions, broker order/trade reconciliation, fill deduplication, risk rechecks and an account-level emergency stop. Upstox order tags are for correlation/history lookup; the project does not assume they guarantee broker-side idempotency.

**Live broker submission and reconciliation are still not implemented.** Phase 1 adds only durable records/repository safeguards; the shared execution service still creates PAPER orders, live submission remains disabled, no production migration ran and no real orders were submitted. Do not set `TRADING_MODE=LIVE` or connect the paper path to the live broker method. Latest Phase 1 code CI: [run 39048147046](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048147046), 215 tests passed, 1 warning; simultaneous idempotency requests passed against PostgreSQL 16, and Alembic upgrade → downgrade → re-upgrade passed on both SQLite and PostgreSQL 16.


## Project roadmap
See [ROADMAP.md](ROADMAP.md) for the phased implementation plan, verified status, release gates and the evidence required before live trading can be considered.


## Live-order safety development status — 17 October 2026
- Phase 1 durable intent/idempotency storage and Phase 2 pure broker-order normalization + strict intent-matching helpers are CI-tested.
- Latest Phase 2 matching test checkpoint: [GitHub Actions run 39050424898](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39050424898), 255 passed, 1 warning, including SQLite/PostgreSQL 16 reversible migration checks.
- The helpers do not make broker API calls and do not persist reconciled states or import fills. Live order submission/cancellation remains unavailable and disabled.


### Phase 2 reconciliation repository update — 17 October 2026
- A repository-only versioned transition now persists a validated normalized status and an audit event atomically. It rejects stale versions and invalid regressions, and duplicate same-state observations do not add duplicate audit rows.
- Cancel/fill races can be represented if subsequent broker trade evidence confirms execution after a cancel. This code does not fetch that evidence itself.
- Latest verified test checkpoint: [run 39050941218](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39050941218), 261 passed, 1 warning. Broker reads, fill ingestion and live order placement/cancellation remain unimplemented.


### Phase 2 individual fill identity checkpoint — 17 October 2026
- Pure Upstox trade normalization and repository-only idempotent fill identity persistence are implemented and CI-tested. Identical duplicate trades are ignored; conflicting payloads are quarantined as conflicts. The repository does not fetch broker trades or update positions/P&L.
- Latest code/test run: [39052203329](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052203329) — 274 passed, 1 warning, with SQLite/PostgreSQL 16 migration checks.
- Live trading remains unavailable and disabled.


### Phase 2 fill-to-intent validation checkpoint — 17 October 2026
Linked fill persistence now requires the same broker order ID and exact instrument, side, product and order type as the intent snapshot; it enforces order quantity ceilings and limit-price protection. [Run 39052939770](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052939770) passed 279 tests, 1 warning, with SQLite/PostgreSQL 16 migration checks. It still does not fetch broker data or update live positions/P&L.


### Phase 2 unmatched-fill recovery foundation — 17 October 2026
A previously unmatched fill can now be linked to a local intent later, but only after broker order ID, account, instrument, side, product, order type, quantity and limit-price checks pass. The link and audit event are atomic; repeat linking is a no-op. [Run 39053352921](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053352921) passed 281 tests, 1 warning. No broker polling or live accounting is implemented.


### Phase 2 out-of-order status/fill checkpoint — 17 October 2026
Order-state persistence now resolves broker status against already-persisted individual fill evidence before applying a transition. A stale OPEN/PENDING status cannot erase known partial fills; a partial fill followed by cancellation is represented separately; contradictory quantities/statuses are quarantined for review. Exact code checkpoint [run 39056392873](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056392873) passed **294 tests, 1 warning**, including SQLite/PostgreSQL 16 migration checks. The read-only broker worker remains design-only; no live broker reads, order actions or accounting updates are implemented. See [READ_ONLY_RECONCILIATION_WORKER_DESIGN.md](READ_ONLY_RECONCILIATION_WORKER_DESIGN.md).


### Read-only Upstox reconciliation client — 17 October 2026
Added a separate fixed-path GET-only client for order book, details, history and per-order trades. It exposes no order-write methods and sanitizes upstream failures. Mocked contract tests passed in [run 39056868434](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056868434): 309 passed, 1 warning, with SQLite/PostgreSQL 16 migration checks. The worker has not been implemented or invoked; no real broker requests or order actions occurred.


### Reconciliation lease foundation — 17 October 2026
Added a durable one-per-broker-connection lease with atomic claim, expiry/reclaim, renewal and stale-owner protection. Exact CI run [39057273255](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39057273255) passed 318 tests, 1 warning, including reversible SQLite/PostgreSQL 16 migrations. The lease is not yet connected to a worker; no broker polling has started.


### Latest Phase 2 checkpoint — leased read-only reconciliation worker
`backend/app/services/live_order_reconciliation_worker.py` now provides an explicit on-demand, read-only reconciliation pass. It validates the user-owned Upstox connection and usable token, claims a per-connection lease, reads the order book and daily trades through the fixed GET-only client, uses bounded transient retries, matches local intents, and persists/deduplicates individual trade identities. It never places/modifies/cancels orders and never updates local portfolio accounting. The worker is not scheduled or wired to an API route; tests use mocks only. Latest CI [run 39058734080](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39058734080) passed **338 tests, 1 warning**, including SQLite/PostgreSQL 16 migration checks. Remaining: validate historical-day/session/pagination semantics, persist operator-facing summaries/manual-review cases, add crash-boundary tests, and only then consider a separately approved read-only sandbox check. Live submission remains disabled.


### Durable reconciliation run summaries
Every explicitly invoked read-only worker pass now creates a `live_reconciliation_runs` record after acquiring its lease. It stores timestamps, terminal status, a safe error category and count-only summary; raw broker responses, credentials and exception text are excluded. Migration `202610170004` and tests passed in [run 39059271937](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059271937): 340 passed, 1 warning, with SQLite/PostgreSQL 16 reversible migration checks. Stale `RUNNING` recovery and operator-facing manual-review records are not implemented yet.


### Durable manual-review queue foundation
The worker now persists deduplicated `live_reconciliation_issues` records for malformed broker rows, unmatched/ambiguous orders, trade conflicts, fill-link conflicts and status-transition conflicts. Issue details are allowlisted, credential-key-checked and limited to safe reason codes/normalized identifiers; repeat occurrences increment a counter and reopen the issue. Migration `202610170005` and tests passed in [run 39059749652](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059749652): 342 passed, 1 warning. The queue currently exists only in the database—no UI/API resolution workflow yet. This newer checkpoint supersedes older dated README statements saying the worker did not exist.


### Read-only reconciliation review endpoints
Authenticated users can list their own safe run summaries at `GET /api/v1/reconciliation/runs` and manual-review issues at `GET /api/v1/reconciliation/issues`. Both routes are owner-scoped, support bounded filters and return sanitized schema fields only. Cross-user/auth tests passed in [run 39060230705](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39060230705): 345 passed, 1 warning, plus SQLite/PostgreSQL 16 migration checks. These endpoints do not trigger a worker or mutate issues/orders; frontend display and a separately reviewed resolution workflow are not implemented.


### Reconciliation review screen
The dashboard now links to `/reconciliation`, a read-only screen showing recent reconciliation run summaries and manual-review issues. It supports filtering by issue status and refreshing the list. It does not trigger broker reads or resolve issues. Frontend TypeScript/Next.js checks and backend CI passed for [commit e4343dcb](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e4343dcb225c1f332b6c89399694d0a29a5df739): 345 backend tests passed, 1 warning; SQLite/PostgreSQL 16 migrations passed. Issue resolution, stale-run recovery and historical trade windows remain unimplemented.


## Live-fill accounting recovery and verification — 2026-10-20

The deleted service, original tests and migration 0008 are restored to their original paths. Supporting models `BrokerOrder`, `BrokerTradeRecord`, `LivePosition` and migrations `202610180006` / `202610180007` were added to complete the chain. GitHub Actions [run 39475387511](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39475387511) passed **355 tests, 1 warning**, plus SQLite and PostgreSQL 16 migration upgrade → downgrade → re-upgrade checks at code/test checkpoint `a906274b98f3f7e0c913f376128f4996b996c52b`.

This is not a complete live-fill pipeline: the service remains unregistered, ingestion and reconciliation integration remain outstanding, and no real-account or production migration was performed. Keep live order submission disabled. Continue Phase 2 reconciliation release gates and crash/recovery/fill-linkage checks. Do not delete the recovered files without explicit user approval.


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

## Phase 3 source-document access and integrity audit — 22 October 2026

- Audited the existing `BrokerChargeEvidence` model and `require_reviewed_charge_evidence` service on `phase3/durable-per-fill-charge-allocation`. The model persists filename, SHA-256, byte size, parser-version metadata, report reference, and review provenance, but explicitly stores the original document outside the table.
- No broker-contract-note-specific upload/retrieval endpoint or storage adapter was found in the audited application entrypoint, API route locations, service paths, and configuration. This is a scoped audit finding, not proof that no generic file handling exists elsewhere.
- The current evidence validator checks evidence identity/connection, source kind, reviewed status, reviewer identity/timestamp, and report reference. It does not retrieve the original bytes, recompute SHA-256/byte size, or parse an authoritative charge-component total.
- **Step 1 remains in progress; no source-storage implementation is claimed.** Before implementation, define a private, persistent, non-web-served storage boundary and a stable evidence-ID-to-object mapping. Retrieval must enforce authorization, prevent path traversal, verify the exact byte count and SHA-256 before parsing, and fail closed on missing/changed content. Do not treat a matching hash alone as proof of broker authenticity.
- Next implementation should add a configurable storage adapter and durable object key tied to the evidence record, then authenticated upload/retrieval and integrity tests. Choose the deployment-backed persistent volume only after confirming the Docker/VM volume layout; do not silently store source documents in an ephemeral container filesystem or Git.
- The prior successful PR-head CI run applies to its exact tested commit only; documentation updates require a fresh CI run on the resulting exact head. PR #6 remains draft/unmerged. Live broker submission and automatic accounting promotion remain disabled. All work stays in `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is not the target.

## Phase 3 private contract-note storage implementation — 22 October 2026

- Added configurable `BROKER_CHARGE_DOCUMENT_ROOT` (default `/var/lib/tradepro/contract-notes`) and a named Docker volume mounted only into backend and worker containers, not Nginx/frontend.
- Added authenticated upload/download endpoints under `/api/v1/broker-charge-evidence`. Upload requires ownership of the broker connection, limits files to 10 MiB, uses an application-generated UUID key, records SHA-256, byte size, and uploader identity (`received_by_user_id`), and leaves evidence in `RECEIVED`; it never auto-reviews or promotes accounting.
- Added atomic private file storage and integrity-checked retrieval. Opaque keys reject path traversal; missing/modified content fails closed. Added storage-service tests for round-trip, tampering, missing documents, invalid keys, empty input, and deletion, plus API tests for owner-scoped upload/download and tamper rejection.
- Alembic revision `202610220011` adds nullable `storage_key` for legacy evidence compatibility. **Exact-head CI and SQLite/PostgreSQL migration upgrade/downgrade/re-upgrade checks remain required.**
- SHA-256 proves byte continuity with the recorded upload, not broker-origin authenticity. Independent source-component parsing/review, persisted component provenance, exact fill-set/amount/currency/rounding reconciliation, and atomic promotion remain later Phase 3 gates.
- PR #6 remains draft/unmerged; live broker submission and automatic accounting promotion remain disabled. Work remains exclusively in `tarunsharma2610-del/tradepro-improved`; do not modify original `Tradepro`.

## Phase 3 durable source-component provenance — 22 October 2026

- Added `BrokerChargeSourceComponent` and Alembic revision `202610220012` to persist a charge component's evidence ID, exact source SHA-256, component name, INR amount, source page/row locator, extraction method, parser-version field, extracting user, status, reviewer, review timestamp, and review note.
- This first workflow is explicitly **manual transcription**, versioned as `manual-transcription-v1`; it does not claim that a broker-specific parser exists or that the amount was machine-extracted. No PDF/CSV parser or broker document format was assumed.
- Added authenticated endpoints to record a component as `PENDING_REVIEW`, verify the original file's stored fingerprint/size before recording or reviewing, and require a distinct platform administrator (the existing `is_admin` role) to confirm the amount against the original source before it becomes `VERIFIED`. Rejected components remain rejected; duplicate component entries and non-INR currencies fail closed.
- Added API regression tests for pending-before-review behavior, same-user review rejection, distinct-reviewer verification, tampered-source rejection, invalid currency, and duplicate component prevention.
- CI run [39742979087](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39742979087) passed on code head `c1004fb5718592fb76ccf50c4007a0d8aec11fb7`: 542 tests passed, 1 warning; broker-write boundary guard and SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks passed. **This documentation synchronization creates a newer head, so recheck exact-head CI before merge.** This is source-component provenance, not the final reconciliation gate: allocation totals must still match verified source components, exact eligible fill sets, currency, and rounding policy under a transaction before any future promotion is considered.
- PR #6 stays draft/unmerged. Live broker order submission and automatic accounting promotion remain disabled. All changes target `tarunsharma2610-del/tradepro-improved`, never original `Tradepro`.

## Phase 3 allocation-ledger verification — 22 October 2026

- Added `verify_component_allocation_ledger` as a fail-closed verifier for a reviewed source component and its allocation rows. It rechecks the stored document fingerprint/size and validates component/evidence review provenance.
- Source-component review persists the canonical sorted eligible trade-record UUID set, its SHA-256 manifest fingerprint, the approved `largest-remainder-v1` method, and the reviewer-approved allocation basis. The reviewer must identify persisted fills from the same broker connection; duplicate/missing/cross-connection IDs are rejected.
- Verification requires the allocation ledger's exact fill set to equal the reviewed manifest, every source total to equal the independently reviewed component amount, currency/method/basis to match, and the paise-exact allocated sum to equal the source amount. Evidence, component, allocation rows, and fills are locked during verification.
- Transactional promotion is implemented in `promote_verified_component_allocations` in `broker_charge_allocation_reconciliation_service.py`. It calls the verifier while holding the transaction locks, requires the authorized source-component reviewer, promotes the entire eligible set to `RECONCILED` with a deterministic durable reference, and supports exact idempotent replay. It uses a savepoint and does not commit the caller's outer transaction; callers must commit only with the enclosing accounting operation. It is service-only, not exposed as a public API endpoint.
- Mismatched source bytes, provenance, fill set, amount, currency, method, basis, mixed/rejected statuses, or stale references fail closed; the full set remains pending or the transaction rolls back. No partial promotion is allowed.
- Tests cover exact verification, fill-set/source-total/tampered-source failures, successful atomic promotion, idempotent replay, wrong-reviewer rejection, and outer-transaction rollback. CI run [39745393196](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39745393196) passed on code head `007c41796da7413823a98f92360d93af074ab88e`: **549 tests passed, 1 warning**; broker-write guard and SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks passed.
- CI run [39745820117](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39745820117) passed on exact head `5139146d48cb3f5906db77014a93b5d20ead3146`: 549 tests passed, 1 warning; broker-write guard and SQLite/PostgreSQL 16 migration round-trips passed. This is a historical exact-head checkpoint; every later code or documentation commit must receive its own exact-head CI verification before merge. PR #6 remains draft/unmerged. Live broker order submission remains disabled.

## Phase 3 transactional allocation promotion — 22 October 2026

- Added `promote_verified_component_allocations` as an internal service (not an API endpoint). It re-runs the source-document, review-provenance, exact fill-set, amount, INR currency, rounding-method, approved-basis, and total checks while locking the relevant evidence, component, allocation, and trade rows.
- Promotion sets the complete eligible allocation set to `RECONCILED` and writes a deterministic durable reference tying the component UUID, source SHA-256, and eligible-fill-set SHA-256. It rejects mixed, rejected, stale-reference, incomplete, or mismatched sets.
- The operation runs inside a savepoint and **never commits the caller's transaction**. The caller must commit only after the whole enclosing transaction succeeds. A repeated exact promotion is idempotent; tests cover successful promotion, replay, unauthorized actor rejection, and outer-transaction rollback.
- This internal service is not wired to an automatic accounting path or exposed as an API endpoint. Live broker submission remains disabled; the service does not itself create accounting entries or send orders.
- CI run [39745393196](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39745393196) passed on promotion-code head `007c41796da7413823a98f92360d93af074ab88e`: 549 tests passed, 1 warning; broker-write guard and SQLite/PostgreSQL 16 migration round-trips passed. Step 4 code is verified at that head; any subsequent code or documentation commits require another exact-head CI check before merge. PR #6 remains draft/unmerged and all changes remain exclusively in `tarunsharma2610-del/tradepro-improved`.

## Phase 3 final audit follow-up — 22 October 2026

- Preserved rejected source-component history: each evidence/component pair now uses a positive revision number; a new transcription is allowed only after prior revisions for that component are rejected. Pending or verified duplicates remain blocked, and the unique evidence/component/revision constraint protects concurrent attempts.
- Promotion now rechecks that the recorded reviewer is still an active platform administrator at promotion time, in addition to matching the reviewed component identity. Loss of authorization fails closed and leaves allocations pending.
- Exact-head CI run [39746382703](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39746382703) passed on `6870fdc8a0bee91f486a250351eac1beb7edbf3d`: 551 tests passed, 1 warning; broker-write guard and SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks passed. Any later commit requires a fresh exact-head CI check before merge.
- PR #6 remains draft/unmerged. Live broker order submission remains disabled, and allocation promotion is still an internal transaction-owned service rather than a public API endpoint.


## Phase 3 exact-head verification checkpoint — 22 October 2026

- Current reviewed PR head at checkpoint start: `2d524632a98167e360be249a5bf255a55cae6daf` on `phase3/durable-per-fill-charge-allocation` in `tarunsharma2610-del/tradepro-improved`.
- Exact-head GitHub Actions run [39746755812](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39746755812) completed successfully: 551 tests passed, 1 warning; broker-write boundary guard passed; SQLite and PostgreSQL 16 migration round-trip checks passed. This supersedes earlier notes in this document that described this commit's CI as pending.
- The PostgreSQL concurrency test exists at `backend/tests/test_broker_charge_allocation_postgres_concurrency.py`; it requires CI's dedicated `TEST_POSTGRES_URL`. The previous documented successful PostgreSQL race run is still a separate earlier commit; confirm the current run's test job environment/logs before claiming this exact run exercised the race test.
- Document storage writes atomically to a private file and verifies SHA-256 and byte count on retrieval. Deployment backup/restore and cleanup of orphaned files remain operational follow-ups; code-level storage tests do not prove production recovery procedures.
- Outstanding review gates: confirm the current CI run executed the PostgreSQL race test; review transaction/authorization behavior and accounting integration; verify deployment volume backup/restore; assess broker-source authenticity limitations. SHA-256 proves byte continuity against recorded evidence, not broker-origin authenticity.
- PR #6 remains draft and unmerged pending review and explicit approval. No live broker order submission or automatic accounting posting is enabled. Scope remains `tarunsharma2610-del/tradepro-improved`; do not modify original `Tradepro`.


## Follow-up: upload rollback cleanup and residual orphan risk — 22 October 2026

- Re-reviewed `backend/app/api/v1/broker_charge_evidence.py` at PR #6 branch `phase3/durable-per-fill-charge-allocation`. After writing the private document, the upload endpoint commits the evidence row; on `IntegrityError` or other caught exceptions it rolls back the database session and attempts `delete_document` for the generated storage key. This is an existing compensating cleanup path and should not be described as entirely absent.
- Residual risk remains: process termination between successful file write and database commit, or failure during the compensating delete, can leave an unreferenced object. Current tests prove basic storage/read integrity but do not demonstrate crash injection or production orphan reconciliation.
- Safe next improvement: add a read-only audit command/service that enumerates only validated 32-hex storage keys and compares them with database `storage_key` values; report missing referenced files, mismatched hashes/sizes, and unreferenced files without deleting anything. Cleanup should be a separate explicit, audited operation with age/grace-period checks and approval; never delete automatically during audit.
- Operational validation still required: coordinated backup and isolated restore of both PostgreSQL `postgres_data` and `broker_charge_documents`, then verify each restored evidence object's storage key, SHA-256, and byte size. Compose mounts confirm shared runtime volume wiring, not a backup guarantee.
- Last verified CI before this documentation follow-up: run [39747922164](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39747922164) passed for commit `f87dd096b2e2f4044b1eb67fa63e277bceb136c9`; rerun and verify CI after the final documentation commit before treating this checkpoint as closed.
- PR #6 remains draft/unmerged pending final review and explicit approval. SHA-256 verifies byte continuity against recorded metadata, not broker-origin authenticity. No automatic accounting posting or live broker order submission is enabled. Scope remains `tarunsharma2610-del/tradepro-improved`; do not modify original `Tradepro`.


## Read-only contract-note storage audit checkpoint — 22 October 2026

- Implemented `audit_contract_note_storage` in `backend/app/services/broker_charge_document_storage_service.py`. It compares evidence rows to files in the configured storage root and reports missing files, size/SHA-256 mismatches, invalid storage keys, duplicate database keys, and unreferenced opaque-key files. The audit is read-only and never deletes files.
- Added regression tests for a clean store and for missing, tampered, and unreferenced files. Exact-head CI run [39749195128](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39749195128) passed on commit `e7214e970b8e2fa3e966dc339141288a30154038`: **553 passed, 1 warning**; broker-write boundary guard passed; SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks passed.
- The endpoint-level database-rollback plus cleanup-failure path is covered by a regression test. Still required: interrupted-process/crash recovery validation, an isolated coordinated PostgreSQL-plus-document-volume restore drill, and final accounting/idempotency review.
- Do not automatically delete orphaned files. Cleanup remains a separate approved, audited operation with grace-period safeguards. SHA-256 demonstrates byte continuity against recorded evidence, not broker-origin authenticity.
- PR #6 remains draft/unmerged pending final review and explicit approval. Live broker order submission remains disabled. Scope is `tarunsharma2610-del/tradepro-improved`; do not modify original `Tradepro`.


## Upload cleanup regression checkpoint — 22 October 2026

- Added a regression test for the contract-note cleanup helper when storage deletion raises `OSError`; the failure is logged and does not escape the helper, allowing the upload handler to preserve its original database exception.
- Exact-head GitHub Actions run [39750696319](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39750696319) passed on commit `279ea3e6f170dc991c243b57372b86e86db065ee`: **554 passed, 1 warning**. Broker-write boundary guard and SQLite/PostgreSQL 16 migration checks passed.
- Upload-recovery coverage is now stronger: an endpoint-level regression test forces database commit failure plus compensating file-deletion failure, then verifies the orphan is reported by the read-only storage audit. This is a simulated integration test, not a production restore drill.
- Remaining gates: coordinated PostgreSQL + contract-note-volume restore drill; independently reviewed source-origin evidence; final allocation replay/idempotency and promotion transaction review; CI verification after the next documentation or code change.
- PR #6 remains draft/unmerged. Live broker order submission remains disabled. Scope is `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is not the target.


### Phase 3 checkpoint — 2026-10-22 (contract-note upload recovery integration)

- Added a real upload-endpoint regression test that forces the evidence database commit to fail after the source bytes are written, then forces compensating file deletion to fail. The test verifies the original database exception remains visible, no evidence row persists, and the read-only storage audit identifies the unreferenced opaque-key file without deleting it.
- CI run 39752136518 passed on test commit 5cfa76e14add51a34e6bc157ad328c74d9f2a33b: 555 passed, 1 warning; broker-write boundary guard passed; SQLite and PostgreSQL 16 migration checks completed successfully.
- This validates the simulated endpoint/database/storage failure path; it is not a production-volume backup/restore drill and does not establish contract-note authenticity beyond recorded SHA-256/size continuity.
- Remaining gates: coordinated database plus document-volume backup/restore drill; final source-evidence, exact fill-set, currency/rounding, idempotency, and atomic-promotion review; synchronize this checkpoint across all nine documents and rerun CI on the final documentation commit.
- Scope/safety unchanged: only `tarunsharma2610-del/tradepro-improved`; PR #6 remains draft/unmerged; live broker order submission remains disabled.


### Phase 3 restore-drill gate

- Do not mark backup/restore complete based on Compose volume declarations or unit tests. In an isolated environment, take a consistent PostgreSQL backup and a matching snapshot/archive of the `broker_charge_documents` volume, restore both into an isolated stack, run the storage audit, verify representative evidence hashes/sizes and database-to-file references, then record the backup identifiers, timestamps, commands, results, and any missing/mismatched/unreferenced files. No production restore has been performed by this checkpoint.


### CI verification checkpoint — 2026-10-22

- Documentation commit `13a406891b286dd8077ee1430c1d62f3b6086309` passed GitHub Actions run `39753249388` for the backend pytest workflow. That run alone establishes the backend test result; do not attribute broker-write guard or SQLite/PostgreSQL migration checks to it without separate exact-commit job evidence.
- This CI result applies to that exact commit only. These documentation updates will create a new head and require a fresh CI result before being called verified.
- Production backup/restore remains unperformed. The required isolated drill must restore PostgreSQL and `broker_charge_documents` together, then validate source hashes/sizes and database/file references; do not infer restore success from CI or volume declarations.


### Exact-head CI scope correction — 2026-10-22

- Latest verified head before this note, `bb46a17dd8578ccce1858ed820584a4348c05e8f`, passed GitHub Actions run `39753596786`: **555 passed, 1 warning in 39.40s** in the Backend pytest job.
- The run queried for that SHA exposes only the Backend pytest job. Therefore this exact-head result does not independently establish the broker-write guard or SQLite/PostgreSQL migration round-trip checks; cite earlier runs for those only at their own SHAs.
- This note creates a new documentation head; verify CI on the resulting exact head before considering it fully checkpointed. The coordinated database + document-volume restore drill remains unperformed.


### Phase 3 backup/restore runbook checkpoint — 2026-10-22

- Added `docs/PHASE3_BACKUP_RESTORE_DRILL.md`, a step-by-step isolated procedure for paired PostgreSQL + `broker_charge_documents` backup, restore into a separate target, SHA-256 artifact verification, storage-audit acceptance, and recorded reviewer sign-off.
- The runbook is a procedure only. No actual coordinated backup/restore has been performed or claimed by this commit. Keep the worker stopped in the target until integrity checks pass; never restore over production or enable live broker orders for this drill.
- Latest prior documentation commit `8b3c87da67aea8d21cca8a6748b7d27b88a1878a` passed backend pytest in run `39754157399`. This new runbook and documentation checkpoint creates a new head and requires fresh CI verification.
