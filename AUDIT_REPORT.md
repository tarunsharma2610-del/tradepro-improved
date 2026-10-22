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

## Historical checkpoint — formerly marked Current verified checkpoint — 21 October 2026

- **Latest verified code/test HEAD:** `00ee9bad0e962d92244da6f63da1e46ba058ad6f`; exact-head backend CI [run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) passed **472 tests, 1 warning**, the broker-write boundary guard, and SQLite/PostgreSQL 16 reversible migration checks.
- The lease-race audit now has both pieces of evidence: PostgreSQL test `test_postgres_write_fence_blocks_reclaim_until_persistence_transaction_finishes` proves reclaim waits while a fenced transaction holds the lease-row lock; new `test_postgres_high_volume_expiry_races_never_resurrect_stale_lease` runs 20 concurrent expiry-boundary renewal-versus-reclaim races and asserts expired owners cannot renew and generation/token ownership advances safely.
- CI logs confirm the full backend suite and source guard passed; the successful workflow includes SQLite and PostgreSQL 16 upgrade/downgrade/re-upgrade checks. The one Python warning is the existing Starlette/AnyIO deprecation.
- **Current task:** synchronize all authoritative documents with this result. The resulting documentation HEAD still needs exact-head CI and a final stale-status scan before Phase 2 is formally closed. Do not start Phase 3 before then.
- Live broker submission, automatic accounting promotion and automatic scheduling remain disabled. The original `Tradepro` repository remains untouched.

------

<!-- Authoritative checkpoint audit: 2026-10-21; updated after Phase 2 lease-fencing verification. -->
## Superseding audit note — latest test commit, 21 October 2026

- Latest code/test commit reviewed: [e56bf4c66f74b875a3ba8fe388138a9d688dd1e2](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e56bf4c66f74b875a3ba8fe388138a9d688dd1e2). It adds test_failed_commit_rolls_back_execution_and_live_position to simulate a failed database commit during live-fill promotion and assert there is no partial Execution/LivePosition and the paper position is unchanged.
- Exact-head CI is verified: [run 39564568154](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39564568154) for this code/test commit passed 471 tests, 1 warning, the broker-write boundary guard and SQLite/PostgreSQL 16 reversible migration cycles. The later documentation HEAD `adb69aeb05b70ba4fa9095fc73d9dea033d31eec` passed [run 39565251793](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39565251793).
- The workflow-boundary decision is resolved for Phase 2: keep intent-based BrokerFillIdentity and manual Order BrokerTradeRecord separate; do not add a bridge or dual-write. The safety-branch matrix records compatible ports versus items deferred to Phase 3/Phase 4.
- Reconciliation crash recovery/lease fencing remains closed unless new evidence identifies a regression. Phase 2's defined engineering checks and exact-head CI are verified; synchronize all authoritative docs and require CI on the resulting documentation HEAD before formally advancing to Phase 3. No live broker submission, automatic accounting promotion, or automatic scheduling is enabled.

## Authoritative checkpoint audit — 21 October 2026

- **Repository/branch:** `tarunsharma2610-del/tradepro-improved`, `main`. The original `tarunsharma2610-del/Tradepro` repository is a protected baseline and must remain untouched.
- **Latest code/test commit:** `fe07b77b193da1232787384efb38cb589e0d71b6` — lease-fence failures now propagate out of persistence exception handlers rather than being misclassified as ordinary record conflicts.
- **Exact-commit backend CI:** [run 39561621808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39561621808) passed **470 tests, 1 warning**, the broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles. It includes lease-fence ownership/expiry tests, a high-volume batch-stop regression, and a PostgreSQL contention test proving an expired lease cannot be reclaimed while a fenced persistence transaction still holds the row lock.
- **Documentation checkpoint CI:** [run 39561881539](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39561881539) passed on documentation commit `292cad087bf0febad7793dcec164ebb5435726e8`; this follow-up synchronizes the closure wording and design note.
- **Frontend:** no frontend files changed in this Phase 2 patch. The latest verified frontend CI remains [run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474), which passed TypeScript and Next.js build on code/test commit `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`.
- **Previously completed Phase 2 protections:** atomic run/lease finalization; stale-owner protection; cancellation and interrupted-run recovery; inconsistent token/expiry rejection; five-record renewal checks; and incomplete-summary warnings for `WORKER_INTERRUPTED` and `LEASE_LOST`.
- **Newly completed lease-expiry audit:** every worker-owned reconciliation persistence operation (fill identity, review issue, order transition and fill-to-intent link) now obtains a current, unexpired lease fence immediately before the write. The lease row is locked through the repository's persistence transaction, so a competing claimant must wait until that transaction commits or rolls back. Lease loss fails closed before the next mutation.
- **Historical checkpoint:** the defined Phase 2 dependency/port matrix, workflow-boundary decision, rollback coverage and CI checks were verified on their cited commits. The current documentation reconciliation and its exact-head CI status are tracked in the top checkpoint.
- **Scope remains unchanged:** external-repository borrowing/adaptation is paused; no outside application code was imported. Live broker submission, automatic accounting promotion and automatic scheduling remain disabled. Keep `BrokerFillIdentity` separate from `BrokerTradeRecord`; do not wholesale-merge the divergent safety branch.
- Intermediate CI runs on partially applied commits were red while the new regression test preceded its matching fix; the final code/test commit above is the authoritative green result. Do not count those intermediate failures as the current code status.

## Historical checkpoint — formerly marked Current scope and backlog clarification — 21 October 2026

- The **reconciliation crash-recovery/lease-fencing slice** is complete. Code/test commit `fe07b77b193da1232787384efb38cb589e0d71b6` passed backend CI run [39561621808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39561621808): 470 tests, 1 warning, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles.
- The documentation synchronization commit is CI-checked separately; use the live [GitHub Actions page](https://github.com/tarunsharma2610-del/tradepro-improved/actions) to verify the exact current `main` HEAD. Do not infer exact-HEAD CI from an earlier commit.
- **This does not mean the entire Phase 2/Phase 2 roadmap is backlog-free.** Phase 2 still has open work: complete the safety-branch dependency matrix, resolve the `BrokerFillIdentity` versus manual `BrokerTradeRecord` workflow boundary before any bridge, and complete the remaining focused accounting/idempotency/rollback tests for any selected port slice.
- Phase 3 live-fill accounting integration and Phase 4 live-trading release gates remain future work and are intentionally blocked. No live submission, automatic accounting promotion, or automatic scheduling is enabled.
- External-repository borrowing remains paused; the original `Tradepro` repository remains untouched. Keep `BrokerFillIdentity` separate from `BrokerTradeRecord`; do not wholesale-merge the divergent safety branch.

<!-- Latest verified status, updated 2026-10-21 -->
> **Latest verified checkpoint — 21 October 2026**
>
> - Repository: `tarunsharma2610-del/tradepro-improved`; branch: `main`. Original `Tradepro` repository remains protected and untouched.
> - Latest code/test commit: `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`. Backend [CI run 39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed **466 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration checks. Frontend [CI run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript and Next.js build.
> - Documentation audit commit `6407c5a05865c1be0ef673d3bb5e71c0231ef8da` passed [CI run 39556816828](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556816828).
> - Phase 2 checkpoint complete through atomic run/lease finalization, stale-run and cancellation recovery, lease-loss fencing, five-record renewal, and incomplete-summary warnings.
> - **Completed engineering task:** audited single slow-write and high-volume lease-expiry races; transaction-level fencing and regression coverage passed backend CI run 39561621808 (470 passed, 1 warning).
> - Deferred safety-branch work remains tracked in `SAFETY_BRANCH_PORT_MATRIX.md`; no wholesale branch merge. Keep live broker submission and automatic accounting promotion disabled. Keep `BrokerFillIdentity` separate from `BrokerTradeRecord`.
>
> The CI status above refers to the stated code and documentation commits. This documentation refresh will create a new commit and trigger its own CI run; do not call that new run passed until GitHub reports success.

# Tradepro Improved — Audit and Change Log

Audit target: `main` in this repository. The original `Tradepro` repository is read-only and has not been modified.

## Current findings

| Area / requirement | Status | Evidence / next action |
|---|---|---|
| FastAPI APIs, SQLAlchemy models/repositories | Existing; tests pass | Backend test suite passed on the current backend changes. Continue adding coverage as features change. |
| Paper market orders | Implemented, still needs operational validation | Uses Upstox LTP for simulated fills and records transaction costs and position/cash updates. Never fall back to a made-up price. |
| Order input validation | Improved | Service boundary rejects non-positive quantities, unsupported order types, missing/non-positive LIMIT prices, and a limit price attached to MARKET orders. API schema also rejects non-positive limit prices. |
| Quote price parsing | Improved | Rejects malformed, non-finite, zero, and negative LTP values before paper accounting. |
| Paper limit orders | Implemented; tests passed | Worker checks pending PAPER LIMIT orders during market passes, fills only when LTP crosses the limit, uses limit-or-better pricing, shares cost/cash/position accounting, and rejects delivery sells without holdings. Owners can cancel pending orders from the portfolio page. |
| Live order placement | Incomplete / not enabled | Shared execution service still records PAPER orders; durable intent/outbox/audit/fill-identity storage and a read-only reconciliation worker exist, but no broker placement/cancel, no scheduling/API trigger and no accounting integration. Do not enable live orders. |
| Broker order status normalization and intent matching | Phase 2 helper layer implemented and tested | `backend/app/services/live_order_reconciliation.py` normalizes documented Upstox statuses and strictly matches a normalized observation to a candidate intent by connection scope, exact existing broker order ID or unique exact tag, and economic fields. Unknown/contradictory states, duplicate tags, cross-connection candidates and economic mismatches are never auto-linked. No network/database side effects. [Run 39050424898](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39050424898): 255 passed, 1 warning. Not yet a reconciliation worker; no state persistence, fill ingestion or broker API calls. |
| Durable live-order records | Phase 1 partial; latest code CI passed | Additive Alembic revision `202610170002`, unique key + canonical request hash, ownership checks, transactionally persisted intent/outbox/initial event, and stable broker fill identity constraint. The latest code checkpoint [run 39049395091](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39049395091) passed 247 tests, including the simultaneous same-key PostgreSQL test and new reconciliation-normalization tests. CI passed clean SQLite and PostgreSQL 16 migration upgrade → downgrade → re-upgrade. Backup-restored staging verification against an actual deployment database remains deferred because the project is not deployed. |
| Strategy activation | Fixed | Strategy evaluation returns HOLD for inactive strategies before contacting the broker; regression test added. |
| Daily risk controls | Portfolio-level manual controls implemented; strategy guard preserved | The portfolio settings UI/API supports manually configured daily realized-loss, estimated exposure, per-order value, open/pending position and daily-order limits. They are disabled by default, enforced on paper/strategy order paths, and calculated using the Asia/Kolkata day. Exposure remains a cost-basis estimate, not broker margin/mark-to-market risk. |
| Broker OAuth | Improved | State is signed, expires after 10 minutes, and is bound to user/broker/connection. A nonce digest and expiry are persisted and consumed by a conditional database update, so repeated/concurrent callback attempts cannot consume the same state twice. |
| OAuth schema migration | Added; deployment not yet verified | `202608220001_oauth_state_replay.py` adds the two nullable state columns. Apply and verify migrations in a backup-safe staging environment before deploying to an existing database. |
| Upstox instrument sync / streaming | Multi-segment sync and stream client implemented; live BOD verification passed | Snapshot-gated reconciliation and expiry deactivation are atomic. Live workflow run 39037390129 downloaded the real official BOD master and synced 123,930 active instruments into disposable in-memory SQLite. The V3 WebSocket client/API includes auth URL validation, reconnect, ping/pong, protobuf decode and stale-quote rejection; a live OAuth session is still unverified. |
| Frontend dashboard | Improved | Root page is now a dashboard with portfolio/cash summaries and links to portfolios, backtests, news, broker settings, and notifications. It no longer duplicates the broker settings page. |
| Frontend typecheck/build | Verified in CI | TypeScript check and Next.js production build passed. The `lint` script runs TypeScript checking because the project uses Next.js 16, where the old `next lint` command is not available. |
| Database migrations | CI migration check passed on SQLite; staging still required | The full Alembic chain, including the OAuth nonce migration, successfully upgraded a clean SQLite database in CI. Verify against a backup and staging copy of the actual deployment database before production rollout. |

## Changes committed

1. Added a service-level inactive-strategy guard and a regression test.
2. Added signed, expiring OAuth state validation bound to the requesting user and broker connection.
3. Added persisted, one-time OAuth nonce consumption with an atomic conditional update and Alembic migration.
4. Added order validation at both the API schema and execution-service boundary.
5. Hardened last-traded-price parsing so invalid prices cannot enter paper-accounting calculations.
6. Added a worker-driven paper LIMIT matcher with crossing rules, limit-or-better pricing, cash/holding checks, and shared accounting.
7. Added an authenticated cancel endpoint and portfolio UI action for pending paper orders, with ownership and status checks.
8. Replaced the duplicate root broker-settings page with an account dashboard.
9. Updated the frontend check command for Next.js 16.
11. Added an environment-controlled emergency kill switch for automated strategy entries, with a regression test proving it blocks entry without creating a position; exits remain available.
10. Added GitHub Actions workflows for backend tests and frontend typecheck/build.

## Verification

- **Backend:** Latest code CI passed — **203 tests passed, 1 warning**, including portfolio position-cap, daily-order-cap, daily-loss/India-midnight boundary, exact-instrument quote-key, WebSocket reconnect and authorization-URL checks, incomplete-snapshot reconciliation, and official-format V3 authorization coverage; clean SQLite Alembic migration verification passed. [View latest backend run](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39039645511).
- **Frontend:** TypeScript check and Next.js production build passed after portfolio risk and stream-control UI changes. [View frontend run](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037642093).
- The tests use SQLite and mocked broker calls; they do not prove a live Upstox session or live market-order execution works.
- The OAuth migration passed a clean SQLite upgrade in CI but has not been applied to your production database.
- No live orders have been submitted.

## Remaining high-priority work

1. Add durable order idempotency/reconciliation before any live-trading implementation. The automated-entry kill switch is now present but must be included in deployment configuration and operational runbooks.
2. Validate the new portfolio-risk migration and manually configured limits against a backup/staging copy of the deployed database; decide whether mark-to-market/margin-aware risk is required.
3. Verify WebSocket streaming using a real authorized Upstox session and decide whether deployment needs shared stream state for multiple API workers.
4. Verify the Alembic migration path in staging and check current deployment configuration. The exchange holiday calendar remains outstanding.
5. Review remaining analytics and backtest behavior against the requested product requirements.


## Requirements-to-code/test gap map (reviewed 2026-10-17)

This is a repository-source review, not a live-broker certification. The current backend CI run for commit `a8faa2581a05778df0f7d30a7a0fb3f0d4e6164a` completed successfully (workflow run [39036087413](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39036087413)). That run was triggered by documentation changes; it confirms the existing test workflow is green, not that untested live-trading features work.

| Requirement | Source evidence reviewed | Status | Next safe action |
|---|---|---|---|
| Paper orders must not submit real orders | `backend/app/services/execution_service.py` constructs orders with `trading_mode="PAPER"`; `backend/app/brokers/base.py` defines broker placement separately; `test_paper_market_order_never_calls_broker_live_order_endpoint` | Regression test present and passing in backend CI | Preserve this boundary; never wire paper execution to adapter `place_order` |
| Live order lifecycle and reconciliation | `ExecutionService.place_order` simulates accounting; adapter has `place_order`, `get_order_status`, `get_order_book`, `get_positions`, but no live orchestration service was found in reviewed files | Not implemented / not enabled | Design a separate live execution service only after idempotency, risk and broker rules are specified; no real orders in tests |
| Duplicate submission protection | `Order` model has no visible broker idempotency key in reviewed fields; safeguards document calls this out | Gap | Define unique client intent key + persisted submission state and retry semantics before live execution |
| Strategy-specific daily loss | `backend/app/services/risk_engine.py` checks strategy realized loss; portfolio risk service checks portfolio realized loss | Strategy guard preserved; portfolio daily limit uses Asia/Kolkata calendar day with midnight-boundary regression test | Consider unrealized P&L/margin-aware limits separately; do not imply realized-only controls are full account risk |
| Portfolio-wide loss / exposure / order-frequency caps | `backend/app/services/portfolio_risk_service.py`, Portfolio risk fields, owner-scoped settings API and portfolio UI | Implemented for paper/strategy order paths; configurable and disabled by default | Keep threshold, India-session boundary and concurrency coverage current. These controls use realized daily P&L and cost-basis exposure; they are not a broker-margin or mark-to-market risk model. |
| Emergency stop for automated entries | `backend/app/core/config.py` exposes `AUTOMATED_ENTRIES_ENABLED`; `strategy_execution_service.py` blocks entries while preserving exits | Implemented for automated strategy entries, not manual paper orders or live orders | Add runbook/monitoring; do not describe as a global account-wide live kill switch |
| Upstox instrument master | InstrumentService, InstrumentRepository batch upsert/reconciliation and live verification script | Real official master download and disposable SQLite sync passed | Live verification run [39037390129](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037390129) imported 123,930 active instruments across supported segments. Missing-key and expired derivative deactivation is snapshot-gated and atomic; a regression test confirms a syntactically valid snapshot missing required segments cannot alter the existing catalog. This did not write to production. See [official Upstox Instruments docs](https://upstox.com/developer/api-documentation/instruments/).
| Upstox WebSocket market data | V3 streamer/manager, authenticated /market-data/stream routes, official V3 protobuf schema/decoder; ExecutionService prefers fresh stream quotes | Implemented with mocked transport/data tests; live account session unverified | One-time authorize URL, TLS verification, binary subscription, protobuf decoding, ping/pong, exponential reconnect and stale-data rejection are implemented. Fresh stream ticks are preferred before REST fallback. The stream manager is process-local; multi-worker deployment needs shared state. See [V3 stream docs](https://upstox.com/developer/api-documentation/v3/get-market-data-feed/) and [authorize docs](https://upstox.com/developer/api-documentation/get-market-data-feed-authorize-v3/).
| OAuth replay prevention | Audit documents persisted nonce digest, expiry and conditional consumption; migration file exists | CI clean-SQLite tested; production/staging not verified | Backup and validate upgrade against a staging copy of the actual DB before deployment |
| Production migration safety | Existing clean SQLite migration CI is not equivalent to the deployed DB engine/data | Unverified | Record DB engine/version, backup, staging upgrade and rollback plan before deployment |
| Frontend checks | Portfolio risk settings and live stream controls in portfolio UI | TypeScript and Next.js production build passed in run 39037642093 | Keep CI required for future frontend changes |

### Review sequence / acceptance gates

1. Paper/live adapter-isolation regression coverage is implemented and passing. Keep the service boundary intact.
2. Portfolio-wide configurable controls are implemented for daily realized loss, estimated exposure, per-order value, open/pending positions and daily order count. Keep strengthening threshold, boundary and concurrency coverage; these controls do not yet account for unrealized P&L or broker margin.
3. Instrument sync and streaming are implemented with mocked tests; the real BOD master sync was validated only in disposable SQLite, while an authenticated live WebSocket session and production topology remain unverified.
4. Treat idempotent live order submission, broker reconciliation, account-level emergency stop, static-IP/2FA/session requirements, authorization and applicable compliance review as mandatory blockers before any real-order feature.
5. Run full backend/frontend CI after code changes; do not call CI triggered by docs a code regression test.

### Scope boundary

This workstream added portfolio risk settings/enforcement, snapshot-gated expiry/delisting reconciliation, a V3 WebSocket client/API and real upstream master verification against disposable SQLite. Latest verified backend CI passed 203 tests and clean SQLite migration verification; frontend typecheck/build passed for the stream-control UI. No live orders were submitted. No production database sync or production/staging migration was run. Live authenticated WebSocket behavior still requires account-level verification. Live trading remains unimplemented and must remain disabled.


### Latest verification checkpoint — 2026-10-17

- Latest backend workflow after documentation changes: [39039714203](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39039714203) — **203 passed, 1 warning**. Clean SQLite Alembic upgrade completed through `202610170001`; this is not proof of safe migration on the deployed database engine/data.
- Regression tests on `main` cover the portfolio daily-order cap, rejection of incomplete instrument snapshots without catalog mutation, WebSocket silence reconnect, unsafe authorization URL rejection, and valid official-format V3 authorization URL/headers.
- Real upstream instrument master was downloaded and synced to disposable in-memory SQLite with **123,930 active instruments**: [workflow 39037390129](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037390129). Production database was not touched.
- Frontend TypeScript and production build passed for stream-control UI: [workflow 39037642093](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037642093).
- Remaining release blockers: authenticated real-session WebSocket test; multi-worker/shared stream state; backup-safe staging migration against the actual deployment DB; and idempotent live order submission plus broker reconciliation and emergency stop. No live orders were submitted. Keep live trading disabled.
- Next safe step: document idempotency and reconciliation design against the existing adapter/order model/audit trail before implementing live order submission.


## Live-order idempotency/reconciliation design review — 2026-10-17

### Source review findings
- `backend/app/models/order.py` stores local order intent/status but has no durable client idempotency key, broker connection/order identity, submission-attempt ledger or reconciliation state.
- `backend/app/models/execution.py` can represent multiple executions conceptually but has no broker trade ID uniqueness guard to deduplicate imported fills.
- `backend/app/repositories/order_repository.py` performs ordinary create/save commits; it does not implement a transactional outbox or an atomic idempotency claim.
- `backend/app/services/execution_service.py` constructs `trading_mode="PAPER"` orders. Keep that behavior isolated; do not connect this method directly to live broker submission.
- `backend/app/brokers/base.py` and `backend/app/brokers/upstox/adapter.py` expose order placement, status, order-book, positions and holdings calls, but adapter methods alone do not provide durable idempotency, uncertain-submit recovery, fill deduplication or reconciliation orchestration.

### Design deliverable
Added [`LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`](LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md) (commit `f74386a99722d761bcd23848f442cb754dd0e231`). It defines additive intent/event/outbox/fill identity records; key + canonical request hash semantics; unknown-submit handling and no blind retries; broker history/order-book/trade reconciliation; partial-fill and cancellation-race handling; risk/kill-switch rechecks; migration and deployment gates; implementation phases; and a regression-test matrix. Related architecture/safety/README documentation links this design.

### Official API contract notes
Reviewed official Upstox Place Order V2/V3, Order History, Order Book, Order Details and Order Trades pages. Upstox tags support correlation and history lookup; this design does **not** assume a tag is broker-enforced idempotency. External exactly-once submission cannot be promised by a local database alone; ambiguous network outcomes must be reconciled before any further submission.

### Status and verification
- This step changed documentation only. No application code or database schema changed, no migration ran and no real broker session/order was used.
- No tests were rerun for the documentation-only design step. Existing historical CI results above remain historical evidence, not validation of live trading.
- Live order placement/reconciliation remains **not implemented and not enabled**. Required future work: schema/repository and concurrency tests; reconciliation-only service; sandbox-only outbox submission with crash/timeout drills; fill dedupe; staging restore/migration verification; operational alerts/runbook; broker/account and compliance checks; explicit authorization.
- Next action: cross-document consistency review and CI confirmation for this documentation commit series. Do not start live-order code until the design review gate is accepted.


## Roadmap and commit-integrity review — 2026-10-17
- Added [ROADMAP.md](ROADMAP.md) to consolidate the verified status, phased implementation plan and release gates across market-data, risk, live-order safety and deployment verification.
- Verified the prior documentation commit series exists on default branch `main`; latest prior progress commit `3263eda9d1329d17069dd4140162602631639a0b` has successful CI: [run 39040715054](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39040715054).
- The new roadmap commit is `3024aed473f28409bd075ec7e764576890c4ecfa`; its own CI must be checked separately before reporting it green.
- No application code or schema was changed by the roadmap addition. No tests were run locally, no production migration was run, and no real broker order was submitted.


## Phase 1 — durable live-order records and repository safeguards — 2026-10-17

### Implemented in `tradepro-improved`
- User-approved design: `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`. The approval authorizes storage/repository safeguards only; it does not authorize enabling live trading.
- Added `backend/app/models/live_order_records.py` with `LiveOrderIntent`, `LiveOrderEvent`, `LiveOrderOutbox`, and `BrokerFillIdentity`. Records include scoped idempotency uniqueness, canonical request hash storage, broker order identity uniqueness, optimistic version/attempt counters, audit correlation metadata, and stable broker trade ID uniqueness.
- Added additive Alembic revision `backend/alembic/versions/202610170002_live_order_durability.py`, registered the models in `backend/app/models/__init__.py`, and added `backend/app/repositories/live_order_repository.py`.
- Repository checks that both portfolio and broker connection belong to the authenticated user. It computes SHA-256 from deterministic canonical JSON plus user/portfolio/connection scope; the client cannot supply a hash that disagrees with the snapshot. Same key + same canonical payload returns the original intent; same key + different payload raises `IdempotencyConflict`. Intent, initial event and outbox row commit together; unique-key races roll back and re-read the winner.
- Added `backend/tests/test_live_order_repository.py` for atomic record creation, idempotent reuse, payload conflict, ownership isolation, invalid/non-finite payload rejection, broker-fill uniqueness, audit ownership and transaction rollback atomicity.
- Latest code/test checkpoint `dd36b48a92057ad50618f6f9941f908832c9cea3` passed GitHub Actions [run 39048147046](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048147046): **215 passed, 1 warning**, with simultaneous PostgreSQL idempotency and SQLite/PostgreSQL reversible migration checks. The later workflow change passed migration upgrade → downgrade → re-upgrade on clean SQLite: [run 39043763339](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39043763339).
- Two intermediate commits failed CI during the canonical-hash API/test-fixture transition; the later checkpoint corrected the mismatch and is green. Those failures are retained in Actions history rather than hidden.
- No real broker order was submitted. No production database was migrated. This code does not yet implement a dispatch worker, live-order API, broker reconciliation or broker fill ingestion. CI contention coverage now exists for PostgreSQL; backup-restored staging verification and broader stress/failure testing remain open.

### Remaining Phase 1 work
- PostgreSQL CI now covers simultaneous same-key creation and reversible migrations; retain the exact run evidence above.
- Verify migration downgrade/upgrade and constraints against a backup-restored staging copy of the actual deployment database engine.
- Continue to preserve PAPER/live isolation; live submission remains disabled.


### Credential-field persistence guard — 2026-10-17
- `backend/app/repositories/live_order_repository.py` recursively checks order snapshots and audit `safe_details` for credential-like key names and rejects non-finite/non-JSON values before persistence.
- `backend/tests/test_live_order_repository.py` verifies nested access-token and authorization-header fields are rejected and no audit rows are added for rejected details.
- This is defense-in-depth only: callers must still redact secret values, and no live API or broker submission was added.


### Phase 2 normalization foundation — 2026-10-17
- Added pure order-status normalization and regression tests. Official contract references: [Upstox order book](https://upstox.com/developer/api-documentation/get-order-book/), [order details](https://upstox.com/developer/api-documentation/get-order-details/), [order history](https://upstox.com/developer/api-documentation/get-order-history/) and [order-status appendix](https://upstox.com/developer/api-documentation/appendix/order-status/).
- Exact test commit `b37452210bf07ad03acee1495e0627fae1378582`: [run 39049395091](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39049395091) — 247 passed, 1 warning, SQLite/PostgreSQL 16 reversible migrations passed.
- Next: strict local-intent matching and ambiguity quarantine. No broker reads, order submission/cancellation, or live reconciliation worker was added.

### Phase 2 strict intent matching — 2026-10-17
- Added ReconciliationIntentCandidate, IntentMatchResult and match_broker_order_to_intent() in backend/app/services/live_order_reconciliation.py. This remains a pure helper; no database or broker I/O.
- Matching is restricted to the supplied authenticated broker-connection scope. An already-known broker order ID takes precedence; otherwise an exact non-empty broker tag must identify exactly one local intent. In both cases, required instrument, side, type, quantity, product and applicable limit/trigger prices must match. Missing fields are mismatches, not wildcards.
- Duplicate tag candidates return AMBIGUOUS; economic mismatches return ECONOMIC_MISMATCH; unknown/contradictory observations return NEEDS_REVIEW; absent correlation returns NO_MATCH. The helper never treats a tag as broker-enforced idempotency and never makes a resubmission decision.
- Regression coverage includes exact matching, existing broker-order ID matching, wrong instrument/quantity, missing product, duplicate tags, cross-connection isolation and unknown statuses.
- Exact test commit e9b594ffc2e81c37e1b41c8c44947212d206f3e9 passed [GitHub Actions run 39050424898](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39050424898): 255 passed, 1 warning, plus SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks.
- Remaining Phase 2 work: persist safe status transitions with audit/version checks, normalize and ingest broker trades idempotently, and test partial/out-of-order updates. No broker API reads, live order submissions, cancellations or production migrations were performed.


### Phase 2 — versioned reconciliation state persistence — 2026-10-17
- Added LiveOrderRepository.apply_reconciliation_transition() in backend/app/repositories/live_order_repository.py. It is a repository-only method: it does not call Upstox or trigger an order action.
- It uses an explicit state-transition allowlist, authenticated user ownership, expected-version and previous-state compare-and-set, broker order ID uniqueness, and one transaction for state/version/last-reconciled timestamp plus a BROKER_STATUS_RECONCILED audit event. Safe details reject credential-like keys. Repeated same-state observations at the current version are no-ops without duplicate audit events.
- Cancel/fill races are explicitly supported: CANCELLED may move to PARTIALLY_FILLED or FILLED when later broker trade evidence proves execution; terminal regressions such as FILLED → OPEN are rejected. RECONCILIATION_REQUIRED is frozen for manual resolution.
- Added tests for atomic state+event persistence, idempotent same-state observations, stale versions, terminal-state regression, cancel/fill race and secret-field rejection.
- Exact code checkpoint b3332b839b6f2c39bf2ae678e1aa62ac1f2a3409 passed [GitHub Actions run 39050941218](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39050941218): 261 passed, 1 warning; SQLite/PostgreSQL 16 migration checks passed.
- CI failures during this step were due to a malformed test import and then an undefined prior-state variable; both were corrected. Failed runs remain visible in Actions history. No broker API call, live order, production migration or fill ingestion occurred.
- Next: implement a pure, validated trade/fill normalizer and then a transactionally idempotent fill repository method keyed by (broker connection, broker trade ID).

### Phase 2 — validated broker trade identity persistence — 2026-10-17
- Added `normalize_upstox_trade()` in `backend/app/services/live_order_reconciliation.py`, a pure validator for documented per-order trade fields. It uses `trade_id` as the stable fill key, validates positive quantity/price and BUY/SELL, parses the documented exchange timestamp into UTC, and rejects malformed records.
- Added `LiveOrderRepository.record_broker_fill()` in `backend/app/repositories/live_order_repository.py`. It verifies broker connection ownership and any linked intent's user/connection scope; persists a single trade under the existing unique `(broker_connection_id, broker_trade_id)` constraint; and commits a `BROKER_FILL_RECORDED` event atomically when linked to an intent.
- Identical duplicate deliveries return the existing fill without another event. A duplicate trade ID with changed order/economic/time/metadata fields raises `LiveOrderVersionConflict`; credential-like keys in metadata are rejected. Cross-connection intent linking is rejected. This repository method performs no network calls and does not update positions, cash, P&L or the shared Order/Execution tables.
- Added normalization and repository tests for valid documented timestamps, malformed fields, idempotent replay, conflicting replay, account isolation and secret-field rejection. Exact code/test commit `001a6eed2bd7090e2c7a4d3a8f2f87e9d7fa62bc` passed [GitHub Actions run 39052203329](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052203329): 274 passed, 1 warning; SQLite/PostgreSQL 16 migration checks passed.
- Earlier fill-test run 39052095678 failed because the test tried to create two Upstox connections for one user, violating the existing unique `(user_id, broker)` constraint. The isolation test was corrected to use a second broker connection type; the later exact run passed.
- Official contract reference: [Upstox Get Order Trades](https://upstox.com/developer/api-documentation/get-trades-by-order/). No broker API read, real order, production migration, reconciliation worker, or live submission was performed.
- Remaining: validate a normalized fill against the matched intent's economic snapshot before persistence; aggregate partial fills and reconcile out-of-order status/fill evidence; then add a read-only broker reconciliation worker only after API contracts and failure handling are covered.


### Phase 2 — fill-to-intent economic validation — 2026-10-17
- Strengthened `record_broker_fill()` to require a linked intent already associated with the observed broker order ID. It compares instrument, side, order type and product against the immutable order snapshot; rejects missing/invalid requested quantity; enforces each fill and accumulated recorded quantity do not exceed the intent quantity; and enforces BUY limit/stop-limit fills are no higher than the limit, SELL fills no lower.
- Added tests for instrument mismatch, unlinked order ID, partial-fill aggregate overrun and both buy/sell limit-price violations. Exact code/test commit `b69939ece8edc47e1ae05f27c0d9e2144e87db04` passed [GitHub Actions run 39052939770](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052939770): 279 passed, 1 warning, with SQLite/PostgreSQL 16 migration checks.
- During development, CI caught test fixtures using fills priced above their own buy limit; fixtures were corrected to realistic limit-or-better fills. An intermediate run also caught tests not yet supplying the newly required product/order type fields. Final checkpoint is green.
- Remaining: reconcile out-of-order status vs fill events and actual broker-side trade list; ensure unmatched fills are quarantined/relinked safely; then build a read-only broker reconciliation worker. No network call, live order, production migration, or position/cash/P&L update was performed.


### Phase 2 — safe relinking of previously unmatched fills — 2026-10-17
- Added `LiveOrderRepository.link_existing_fill_to_intent()` for fills initially recorded without a local intent. It requires authenticated-user and broker-connection scope, exact already-linked broker order ID, instrument/side/product/order-type agreement, valid order quantity, limit-price protection and aggregate quantity ceilings.
- The link uses a conditional update that only changes an unlinked fill; repeat linking to the same intent is a no-op, while a different existing link or economic mismatch fails closed. The link and `BROKER_FILL_LINKED` audit event are committed atomically. Duplicate trade delivery without an intent can still be treated as an idempotent replay after later linking.
- Tests cover successful late linking, no duplicate audit on repeat link and rejection of an economic mismatch. Exact test commit `66802c2eae7adaddb8f1213c9c9a689e4190acaf` passed [run 39053352921](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053352921): 281 passed, 1 warning, with SQLite/PostgreSQL 16 migration checks.
- Still missing: real broker reads, worker retry/backoff, out-of-order status/fill reconciliation, fill revisions/sliced orders, and applying reconciled fills to shared order/execution/position/cash/P&L accounting. No real order or production migration occurred.


### Phase 2 — out-of-order status/fill evidence — 2026-10-17
- Added `resolve_order_state_with_fill_evidence()` and wired it into `LiveOrderRepository.apply_reconciliation_transition()` before idempotent same-state handling. Persisted fill identities now protect against stale active/cancel statuses overwriting execution evidence.
- Full persisted requested quantity resolves to `FILLED`; partial fill evidence with active statuses resolves to `PARTIALLY_FILLED`; partial fill plus cancellation resolves to `PARTIALLY_FILLED_CANCELLED`; contradictory partial-vs-filled/rejected evidence and invalid totals resolve to `RECONCILIATION_REQUIRED`.
- Audit events retain observed broker state, effective state, persisted fill quantity and resolution reason. Added parametrized normalizer/state tests and repository tests for stale OPEN, partial-fill cancellation and full-fill-vs-stale-cancel cases.
- Exact code/test checkpoint `59f562b62ef6af25ea3a5c6f15cab8a32d505da3` passed [GitHub Actions run 39056392873](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056392873): **294 passed, 1 warning**, plus SQLite/PostgreSQL 16 migration checks.
- One initial test run failed because two audit events shared the same timestamp precision and the test selected the wrong row; the test was corrected to select by resolved state, then the exact checkpoint passed. No broker API read, real order, production migration or accounting update occurred.
- Added [READ_ONLY_RECONCILIATION_WORKER_DESIGN.md](READ_ONLY_RECONCILIATION_WORKER_DESIGN.md), a design-only contract for the next read-only worker. It is not implemented yet.


### Phase 2 — narrow read-only Upstox client — 2026-10-17
- Added `backend/app/brokers/upstox/reconciliation_client.py` with fixed GET-only methods for order book, order details, order history by order ID or tag, and per-order trades. It intentionally does not expose place/modify/cancel methods.
- HTTP failures are categorized (401, 403, 429, 5xx, other client errors, timeout, network failure, non-JSON) without returning raw response bodies or exception text. A missing token fails before network access. Endpoint paths and parameters follow the official Upstox docs: [order book](https://upstox.com/developer/api-documentation/get-order-book/), [order history](https://upstox.com/developer/api-documentation/get-order-history/), [order details](https://upstox.com/developer/api-documentation/get-order-details/), [per-order trades](https://upstox.com/developer/api-documentation/get-trades-by-order/).
- Added mocked HTTP contract tests for paths/parameters, status classification, sanitization, timeout/network errors and absence of write methods. Exact test commit `10d9938d17c4c67649c5a4b9c305684ff8f36e52` passed [run 39056868434](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056868434): **309 passed, 1 warning**, plus SQLite/PostgreSQL 16 migration checks.
- This does not make any real Upstox request. No worker orchestration, token loading, retry/backoff, job lease, fill processing or accounting update has been implemented yet.


### Phase 2 — per-connection worker lease foundation — 2026-10-17
- Added `LiveReconciliationLease` and Alembic revision `202610170003` with a unique broker-connection key, lease token/expiry, generation, start/completion timestamps and sanitized error category.
- Added `LiveReconciliationLeaseRepository` with owner-scoped connection validation, bounded lease duration (1–3600 seconds), atomic claim/expiry reclaim, renewal restricted to the current unexpired token, and token-guarded completion.
- Added tests for second-worker exclusion, expiry/reclaim, stale owner rejection, valid completion, renewal/token/expiry handling, cross-user access and invalid lease durations.
- Exact test commit `4bbeb5f6ced81f66ae7720eb73557eebbc3409e9` passed [run 39057273255](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39057273255): **318 passed, 1 warning**, and SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks passed.
- This is only lease storage/repository code; the worker is not implemented, no broker reads occurred, and no live order or accounting side effect is possible from this repository.


### Phase 2 — leased read-only reconciliation worker — 2026-10-17
- Implemented `backend/app/services/live_order_reconciliation_worker.py` (worker code commit [`4ee8427`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/4ee8427f890f7c31021e30f7b36177e2f3f227c)). The worker accepts only `UpstoxReadOnlyReconciliationClient`, checks user ownership, Upstox broker identity and connected state, gets the token through `BrokerCredentialsService`, claims/renews/completes a per-connection lease, reads order book and daily trades, normalizes observations, matches intents, and stores/link fills with existing repository checks.
- Retries are bounded and limited to read-only transient failures (429, 5xx, timeout/network). Token/permission errors stop the job. Malformed envelopes fail before any fill/status persistence. Summaries expose safe counts/error categories only.
- Added worker regressions for successful matching/fill linking, repeat-run dedupe, failed trade read atomicity, Retry-After, cross-user rejection, busy lease, missing token, unmatched fills, UNKNOWN-to-FILLED recovery, 403 without retry, bounded 503 retries and malformed envelope/data cases.
- PostgreSQL concurrency test confirms simultaneous lease claims allow only one worker token; exact test commit [`bf0c2b7`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/bf0c2b707aaa023a961f899502ed9f2ae4d265a4).
- Latest exact code/test checkpoint [`bffeefc`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/bffeefc7921fd96c8fbeab1b201eb3088e87f497) passed [GitHub Actions run 39058734080](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39058734080): **338 passed, 1 warning**; SQLite/PostgreSQL 16 reversible migration checks passed.
- Important limits: worker is not scheduled or exposed through an API route; current pass reads order book and daily trades, not historical-day pagination. There is no persistent run-summary/manual-review queue and no aggregation into Order/Execution/Position/cash/P&L. All worker transport tests are mocked; no real Upstox request, order action, production migration or accounting update occurred.


### Phase 2 — durable run summaries — 2026-10-17
- Added `LiveReconciliationRun` and Alembic revision `202610170004_reconciliation_runs.py`; `LiveReconciliationRunRepository` validates owner/connection scope, terminal status, safe error-code format and exactly the approved non-negative integer counters.
- Integrated the worker lifecycle: a `RUNNING` row is persisted after lease acquisition; success/conflict/failure/lease-loss ends in a terminal row with start/completion timestamps, sanitized error code and count-only summary. If run-row creation fails, the worker attempts to release its lease; if final summary persistence fails, the worker does not report clean success.
- Added worker tests for successful summary persistence and sanitized failure summary. Exact code commit [`0e69fb2`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/0e69fb2efea692f2f675604ef3312cb1954ecc39) passed [run 39059271937](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059271937): **340 passed, 1 warning**, and reversible SQLite/PostgreSQL 16 migration checks.
- Remaining: manual-review issue records/visibility, stale RUNNING-run recovery, crash-boundary tests, official history/pagination semantics and a separately approved read-only sandbox verification. No real broker reads, order actions, production migration or accounting changes occurred.


### Phase 2 — durable manual-review issue queue foundation — 2026-10-17
- Added `LiveReconciliationIssue`, migration `202610170005_reconciliation_issues.py`, and `LiveReconciliationIssueRepository`. Issue records are scoped to the authenticated user and broker connection, optionally tied to a run/intent, deduplicated by connection + fingerprint, and re-opened/incremented when the same issue recurs.
- Issue types are allowlisted. Safe details are credential-key-checked, finite JSON and limited to 2,048 characters; the worker records reason codes and normalized broker identifiers, not raw response records or exception strings.
- Worker now persists issues for invalid order/trade records, unmatched/ambiguous/economically mismatched orders, trade persistence conflicts, fill-link conflicts and status-transition conflicts. Tests cover deduplication of repeated unmatched-order issues and safe invalid-trade issue persistence.
- The initial issue-queue CI run [`39059726263`](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059726263) failed because malformed trade normalization was handled by the persistence-conflict branch before `trade` existed. The loop was split into normalization and persistence error handling. Exact fix commit [`71b5668`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/71b5668533f0461c12374319e496665cbda7e61c) passed [run 39059749652](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059749652): **342 passed, 1 warning**; SQLite/PostgreSQL 16 migration checks passed.
- Remaining: UI/API visibility and safe issue resolution, stale run recovery, crash-boundary tests, and historical-day pagination. No real broker reads/order actions, production migration or accounting update occurred.


### Phase 2 — authenticated read-only run/issue listing — 2026-10-17
- Added `GET /api/v1/reconciliation/runs` and `GET /api/v1/reconciliation/issues`, Pydantic response schemas and `LiveReconciliationQueryRepository`. Both endpoints require authentication and scope queries by the current user's ID; filters are optional and page size is bounded to 1–100.
- Tests cover unauthenticated access, user A versus user B isolation, filtering by another user's connection returning no records, status filter validation, maximum limit and no token leakage in issue responses.
- Exact code commit [`f65b4ba`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/f65b4ba20ce9a1dacfe40580d8042cd98f36c19f) passed [run 39060230705](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39060230705): **345 passed, 1 warning**, and SQLite/PostgreSQL 16 upgrade/downgrade/re-upgrade checks.
- API is read-only; it cannot start a worker, resolve an issue, place/cancel orders or update portfolio accounting. Frontend UI, issue-resolution workflow, stale-run recovery, crash-boundary tests and historical trade pagination remain open.


### Phase 2 — reconciliation review UI — 2026-10-17
- Added `frontend/app/reconciliation/page.tsx` and a dashboard navigation item. It loads owner-scoped run summaries/issues, displays sanitized details and counters, filters issue status, and supports manual refresh. No trigger, resolve, retry or order mutation controls are exposed.
- Exact commit [`e4343dcb225c1f332b6c89399694d0a29a5df739`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e4343dcb225c1f332b6c89399694d0a29a5df739) passed [frontend checks](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39060564743) and [backend CI](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39060564787): TypeScript/Next.js build passed; 345 tests passed, 1 warning; reversible SQLite/PostgreSQL 16 migrations passed.
- Remaining: issue resolution workflow, stale `RUNNING` recovery, crash-boundary/restart tests, historical trade pagination and a separately approved read-only sandbox verification. No real broker request/order action or accounting update occurred.


## Reference repository comparison and current CI blocker — 2026-10-20

The targeted source/license comparison is documented in [REFERENCE_REPOSITORY_AUDIT.md](REFERENCE_REPOSITORY_AUDIT.md). Main findings: use the AI Trading Platform for layered domain boundaries, validated strategy-draft and unknown-submission patterns; Algo Options Platform for options-specific data/backtest ideas after validating the code; Kite Algo Bot for explainable signal gates and risk regression-test ideas; use OpenAlgo's broker capability matrix and docs as behavior reference only unless AGPL-3.0 obligations are intentionally accepted. No wholesale replacement or external source copy is recommended.

**Blocking defect discovered in current checked-in code:** backend pytest run [39113589752](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39113589752/job/117634693349) fails during collection because `backend/tests/test_live_fill_accounting_service.py` imports missing `app.models.broker_order`. The current tree also lacks `broker_trade_record.py`, `live_position.py`, and Alembic revisions `202610180006` and `202610180007`, despite references from `live_fill_accounting_service.py` and migration `202610180008`. The live-fill accounting work/migration chain must be completed or safely reverted and tested before claiming a green baseline or adding features. No live order was placed; original Tradepro remains untouched.


## Live-fill accounting recovery and verification — 2026-10-20

The three files deleted during the temporary rollback have been restored byte-for-byte from their pre-deletion Git blobs at their original paths. Supporting models and migration revisions have now been implemented in this repository.

- Restored originals: `backend/app/services/live_fill_accounting_service.py`, `backend/tests/test_live_fill_accounting_service.py`, `backend/alembic/versions/202610180008_execution_charge_provenance.py`.
- Added models: `backend/app/models/broker_order.py`, `backend/app/models/broker_trade_record.py`, `backend/app/models/live_position.py`; registered them in `backend/app/models/__init__.py`.
- Added migrations `202610180006_broker_trade_intake.py` (down revision `202610170005`) and `202610180007_live_position_execution_provenance.py` (down revision `202610180006`), completing the chain to revision `202610180008`.
- Updated `Execution` model to match charge-provenance migration and added a guard/test rejecting a broker trade quantity above the broker-confirmed child-order fill quantity.
- Exact code/test checkpoint `a906274b98f3f7e0c913f376128f4996b996c52b` passed GitHub Actions [run 39475387511](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39475387511): **355 passed, 1 warning**; Alembic upgrade → downgrade → re-upgrade passed on SQLite and PostgreSQL 16.
- Scope limitation: this is a tested accounting service/storage foundation, not a complete live-fill pipeline. The service remains unregistered; broker trade ingestion, invoking the service from reconciliation, shared live order/status accounting, production staging verification and real-account reconciliation remain outstanding. No real broker orders or production migrations were run. Live order submission remains disabled.
- Next action: continue the existing Phase 2 reconciliation release gates, inspect crash/recovery and broker-confirmed fill linkage, and only integrate live accounting through a separately reviewed, tested path. Do not delete the recovered files without explicit user approval.



## Test-baseline and branch divergence audit — 2026-10-21

- Confirmed GitHub Actions run [39140514552](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39140514552) at safety-branch SHA `9085d9fbdcc8ee2dd8baac6f5e73f92bd76cfa8b`: 456 passed, 8 skipped, 1 warning.
- Confirmed current `main` HEAD `074dd533bb84ac8102a6602f50cf9d0f57323a3d`, run [39476051343](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39476051343): 355 passed, 1 warning.
- Test-tree comparison: 35 test modules on `main`, 48 on `safety/fail-closed-trading-mode`; 23 test modules and 19 related API/model/service paths present on the safety branch are absent from `main`. The branches have materially different implementations and GitHub reports substantial divergence (389 commits ahead / 1,029 behind in the selected comparison). Do not treat the count difference as a same-branch deletion count, merge the branch wholesale, or transplant test files without their source dependencies.
- Migration graph on `main`: 14 revisions, one linear chain from `202608170001` to terminal head `202610180008`; no missing parent references. The current exact-head CI passes SQLite and PostgreSQL 16 upgrade/downgrade/re-upgrade checks.
- Current live-fill accounting is not end-to-end: its service is intentionally unregistered and reconciliation invocation, parent-order state integration, and full crash/replay verification remain outstanding. Live broker submission remains disabled.
- Next: port missing safety behavior in dependency-complete slices; add/port tests with the implementation, then require focused tests, full pytest, PostgreSQL concurrency/integration, and migration CI before marking each slice complete. No production broker orders or migrations were run.



## Upstox response-validation slice — 2026-10-21

- Added pure parser helpers at `backend/app/brokers/upstox/response_parsing.py` (commit `6a338820c37ec44632023327cf8e6fa671682ed0`) and regression coverage at `backend/tests/test_upstox_response_parsing.py` (commit `03d2607792e46272566b6871a452e612b1d6ca7a`).
- Exact-head [GitHub Actions run 39477976464](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39477976464) passed **406 tests, 1 warning**, including SQLite and PostgreSQL 16 reversible migration checks.
- The parser rejects malformed/failed payloads, mismatched order/trade identities, duplicate trade IDs, invalid quantities/prices, and inconsistent filled-quantity/average-price snapshots. Funds/pledged collateral remain distinct; brokerage estimate values are not treated as final executed charges.
- The parser is pure and currently not connected to broker network calls, reconciliation or accounting. Live submission remains disabled.
- Next review: adapt broker trade staging only after mapping the safety branch service/tests to current main's stricter `BrokerOrder`/`BrokerTradeRecord` schema and existing reconciliation worker. Do not copy incompatible service/model code wholesale.


## Broker trade staging port — audit result (2026-10-21)

- Added isolated broker trade staging service and tests: service commit `2d90405dfd785e3b71ec8cfc1e648458ff9c3289`; final tested service behavior includes mandatory exchange timestamp validation in commit `1d72eb1ad7621d5de74adcdfe1b637f6c7703639`, with final regression suite at `3f210e592c8aa2e643e536a04f186da8187bc06b`.
- Exact-head [run 39480002328](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39480002328) passed **431 tests, 1 warning**, plus SQLite and PostgreSQL 16 reversible migration checks.
- Porting surfaced real schema drift: current main requires broker connection binding and status on `BrokerOrder`, uses `BrokerOrder` as the child-order ID mapping, and requires `BrokerTradeRecord.exchange_timestamp`. Tests were adapted to those constraints instead of loosening production schema.
- Trade ingestion remains isolated staging only and must not mutate Execution, Position, portfolio cash or Order status. It is not yet integrated with the current reconciliation worker/fill coordinator. Live submission remains disabled.
- Test-tree audit matrix: [`SAFETY_BRANCH_PORT_MATRIX.md`](SAFETY_BRANCH_PORT_MATRIX.md). Do not merge the divergent safety branch wholesale or infer deleted functionality from raw test counts.


## Cumulative child-fill cap — audit result (2026-10-21)

- `LiveFillAccountingService.promote_trade` previously enforced `record.quantity <= child.filled_quantity` per record, but did not enforce the cumulative quantity already accounted against that child order. Distinct trade IDs could therefore individually pass a cap that the aggregate would exceed.
- Added a sum of prior `Execution.quantity` for the same child order and broker connection, after locking the child row and after the idempotent replay check. Promotion now rejects when prior accounted quantity plus the new trade exceeds broker-confirmed `filled_quantity`.
- Added regression test `test_cumulative_promoted_trades_cannot_exceed_child_fill_quantity`. Exact-head [run 39480669799](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39480669799) passed **432 tests, 1 warning**, plus SQLite/PostgreSQL 16 reversible migrations.
- This service remains unregistered. The reconciliation worker persists `BrokerFillIdentity`, whereas the staged accounting path reads `BrokerTradeRecord`; resolve this architecture split before integration or automatic promotion. No real broker request/order occurred.


## Broker child-order reconciliation — audit result (2026-10-21)

- Ported `backend/app/services/broker_child_order_reconciliation_service.py` and `backend/tests/test_broker_child_order_reconciliation.py` in commits `baf480dc6858cb6d0c8bedc4a0fae4aa2f608d48` and `0b1224b3df446a1fcfd1725adcde29a35f722631`.
- Adapted away historical `Order.broker_order_id` and branch-only `BrokerOrder.average_fill_price/status_checked_at/error` columns. Mainline child-order identity stays in `BrokerOrder`; status and filled quantity are persisted, while weighted average fill price is computed from trade records and compared with broker details.
- The service verifies ownership, connection/token stability, requested quantity, instrument/side, trade-quantity equality, weighted average price, non-regressing fill quantity and terminal-state monotonicity. It never updates parent Order/accounting.
- Exact-head [run 39481385581](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39481385581) passed **438 tests, 1 warning**, plus SQLite and PostgreSQL 16 reversible migrations.
- Remaining architecture gate: `LiveOrderReconciliationWorker` stores intent-linked `BrokerFillIdentity`; the manual Order staging/accounting flow uses `BrokerTradeRecord` and `BrokerOrder`. Keep these isolated until the intended workflow boundary and any bridge are explicitly designed. Live writes and automatic promotion remain disabled.


## Parent-order reconciliation lock guard — 2026-10-21

- Child reconciliation now locks/revalidates the owned parent Order after broker status I/O, checks LIVE mode and the pre-network instrument/side/quantity snapshot, then locks the BrokerOrder child before reading staged trade totals. This matches ingestion's parent→child lock order.
- Added a regression test that switches the local order to PAPER during the status read and confirms child status/fill quantity remain unchanged. Staged evidence remains available; no accounting rows are created.
- Exact code/test checkpoint `84f3a3e48a64b6e1d764a87a2b337b2a8f052741`, [CI run 39482592808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39482592808): **439 passed, 1 warning**, with SQLite/PostgreSQL 16 reversible migrations passing.
- This does not enable parent Order accounting or live submission. Keep `BrokerFillIdentity` and `BrokerTradeRecord` workflows isolated until their intended boundary is decided.



## Broker-write boundary guard — 2026-10-21

- Added an AST-based guard under `backend/scripts/check_broker_write_boundary.py` to detect unapproved source references to broker order-write methods and integrated it into the backend CI workflow.
- Added focused guard unit tests covering generic receiver aliases, the proposed central write boundary, adapter-definition exclusions, docstring false positives, and existing PAPER execution call sites.
- Latest implementation/config commit: `c563683b85d7801cd19dcf3d1c7784ec6e433d1f`; progress documentation is being updated separately.
- Historical broker-write-guard checkpoint superseded by current verified CI run [39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386): the guard passed on the latest code/test HEAD. The static guard does not prove safety against reflective/dynamic dispatch.
- Limitation: AST inspection cannot prove safety against reflection/dynamic dispatch. This guard supplements—not replaces—authorization, risk interlocks, integration tests, and code review. Live submission remains disabled.


## Broker-write guard review follow-up — 2026-10-21

Review found that the first AST guard exempted the entire Upstox adapter file and permitted any `service.place_order` reference in the portfolios module. These were broader than needed. The guard now scans the adapter normally and limits the known PAPER endpoint exceptions to their exact function names and call shapes. Added regressions for an unexpected adapter call and an unrelated helper in the portfolios module. This improves source-level detection but is not a substitute for runtime authorization or protection against reflective/dynamic dispatch. Exact-head CI remains unverified; the previous 439-pass result predates this change. Live order writes and automatic accounting promotion remain disabled.


## Exact-head broker-write guard verification — 2026-10-21

- Current `main` HEAD `975717b05a3aa5faa030f3f9e177dbcf6066daf3` passed [GitHub Actions run 39550130192](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39550130192): **447 passed, 1 warning**.
- Verified successful steps: full backend pytest, broker-write boundary AST guard, SQLite migration upgrade/downgrade/re-upgrade, and PostgreSQL 16 migration upgrade/downgrade/re-upgrade.
- The prior run on `6273a3178e37a27e47a8634564f634075f375f3e` failed; the latest commit corrected an expected line number in a broker-guard test. The current head is green.
- Remaining Phase 2 architectural gate: define whether `BrokerFillIdentity` and `BrokerTradeRecord` are separate workflows or need a transactional bridge. No integration or automatic promotion until ownership/account scoping, stable identity, conflict handling, idempotent replay, rollback and crash recovery are covered. Live broker submission remains disabled.

## Fill-workflow boundary audit — 2026-10-21

The intent reconciliation worker and manual-order accounting service currently use distinct persistence models and independent unique keys: `BrokerFillIdentity` is unique by broker connection/trade ID; `BrokerTradeRecord` is also unique by broker connection/trade ID, but the database cannot enforce uniqueness across the two tables. The worker links validated fill evidence to a `LiveOrderIntent`; the manual path links staged trades to `BrokerOrder` and promotes them only through explicit broker-reported charges.

Decision: keep the paths separate in this phase. No copy/dual-write/automatic promotion. Added worker regression assertions that successful reconciliation and replay do not create `BrokerTradeRecord`, `Execution`, or `LivePosition` rows and leave portfolio cash unchanged. Test commit `3683082509c4b331ab9c7ebceb928e925414de35`; exact-head CI pending. A future bridge requires canonical fill identity, owner/connection/intent/order linkage, deterministic cross-table conflict semantics, transaction-safe idempotency, rollback and crash-recovery tests.

## Orphaned reconciliation-run recovery review — 2026-10-21

A crash can leave a durable `LiveReconciliationRun` in `RUNNING`. Added `fail_orphaned_runs` as an explicit recovery primitive. It is owner/connection scoped, only targets runs started before a supplied cutoff, and refuses to mark them failed while a lease is unexpired. It writes only `FAILED`, completion time, and `WORKER_INTERRUPTED`; it preserves counters and does not re-read the broker or alter `BrokerFillIdentity`, `BrokerTradeRecord`, `Execution`, `LivePosition`, or portfolio cash. Tests cover the stale, active-lease, scope and input-validation cases. Exact-head CI remains pending for commits `c21dc711c9102c4a6f0aad36b404ba8c1b57d5f8`, `007383da7f0ca5a1793098288f610ed98de9eb71`, and `298caa0a1a05124cdf6fdc9d94ff0644f20295a5`.

## Exact-head stale-run recovery verification — 2026-10-21

- The on-demand worker now calls `fail_orphaned_runs` before claiming a new lease. Recovery is owner/connection scoped, only targets stale `RUNNING` rows, defers while a lease is active, and fails closed with `STALE_RUN_RECOVERY_FAILED` if recovery itself errors.
- Tests cover stale-run recovery through the worker, active-lease protection, and no broker call when recovery fails. SQLite timezone handling and SQLAlchemy ORM-evaluation behavior were corrected.
- Exact current code head `c1c0d8c6fbbb5dcc1389d2da77e911c815958d88`, [run 39551504884](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39551504884): **455 passed, 1 warning**; broker-write guard and SQLite/PostgreSQL 16 migration cycles passed.
- Important limitation: the summary schema stores counters only at run completion. `WORKER_INTERRUPTED` means counters may be incomplete; zero counters must not be interpreted as proof that no partial work persisted. Next: add PostgreSQL race coverage for recovery/lease claim and ensure the UI labels interrupted summaries as incomplete. Recovery does not retry broker reads or touch fills/accounting.


## Exact-head stale-run recovery race and UI verification — 2026-10-21

- Added a PostgreSQL race test between stale-run recovery and claiming an expired lease. It asserts a safe serialized outcome and prevents a run being marked orphaned after a new active lease wins.
- Added a visible `WORKER_INTERRUPTED` warning in the reconciliation review UI: summary counters may be incomplete, and zero values are not evidence that no fills were processed.
- Exact current code/test HEAD `d0437be8ef27c4e86d659a9b85bf42dbdb99ecc4`: [backend run 39552046237](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552046237) passed 456 tests, 1 warning, source guard and SQLite/PostgreSQL 16 migration cycles; [frontend run 39552046207](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552046207) passed TypeScript and Next.js build.
- Remaining review: crash window between releasing lease and finalizing the run summary, and inconsistent lease states. Recovery is metadata-only and does not mutate fills/accounting. Live submission and automatic promotion remain disabled.


## Phase 2 crash-window and lease-integrity audit — 2026-10-21

- Exact current main code/test head `0ce59a7965e3e96a425fa8ae30c841eb0cb755bc`: [CI run 39552821228](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552821228) passed 461 backend tests, 1 warning, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles.
- Fixed a lease-claim weakness: prior SQL treated a missing token **or** missing expiry as reclaimable, which could overwrite a half-populated lease. Claim now rejects inconsistent pairs and only reclaims both-null released rows or rows whose populated expiry has elapsed; row locking is requested where supported.
- Added recovery coverage for a crash after lease release but before run-summary persistence. The summary remains RUNNING until it is older than the recovery cutoff, then is marked FAILED/WORKER_INTERRUPTED before a subsequent run. Its counters remain incomplete and are not evidence that no fill work occurred.
- Remaining architectural question: lease completion and run-summary finalization are separate commits. Decide whether to unify them in a transaction; if not, retain explicit eventual-recovery semantics and test the lost-lease / finish-order edge cases. No broker write, fill promotion, or accounting mutation was added.


## Phase 2 atomic lifecycle finalization audit — 2026-10-21

- Exact verified code/test HEAD `8f967adaa2328f16a0a08a104c3ec394e62f9310`: [CI run 39553655005](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39553655005) passed 463 backend tests, 1 warning, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles.
- Replaced separate lease-completion and run-summary commits with `finish_with_lease`, which updates both records in one database transaction. If the run is no longer RUNNING or cannot be updated, rollback preserves the lease record.
- If a worker's lease token is stale, the run is marked `LEASE_LOST`; the repository does not clear the newer owner's token or expiry. Tests cover both rollback and stale-owner finalization.
- Worker-level failure coverage verifies the lease remains active when summary finalization fails; after simulated process loss and expiry, stale-run recovery marks the run `WORKER_INTERRUPTED` before a subsequent run. Summary counters remain incomplete and are not evidence that no fill work occurred.
- Remaining Phase 2 review: cancellation/unexpected exceptions and lease renewal/expiry under concurrent worker activity. No live broker writes, fill promotion, or accounting mutation was added.


## Phase 2 lease-loss and cancellation audit — 2026-10-21

- Exact verified code/test HEAD `2ac6bfaafd3475ee63360bd0049b0b6987236bc1`: [CI run 39553981172](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39553981172) passed 465 backend tests, 1 warning, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles.
- Added worker coverage for lease replacement before local persistence: the old worker stops before inserting fills, finalizes its run as `LEASE_LOST`, and does not release the new lease token.
- Added cancellation coverage: cancellation during broker read propagates, leaving the run/lease for expiry-based recovery. Once stale, the run becomes `FAILED/WORKER_INTERRUPTED` before the next run starts.
- Terminal run-summary and lease finalization remain one transaction. If terminal summary update fails, lease release is rolled back.
- Remaining audit: renewal cadence during large batches and expiry races around per-record persistence. Recovery summaries remain incomplete; no live broker write or accounting mutation was added.


## Phase 2 renewal-boundary and UI completeness audit — 2026-10-21

- Verified code/test HEAD `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`: backend [run 39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed 466 tests, 1 warning, broker-write guard, and SQLite/PostgreSQL 16 migration cycles; frontend [run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript/build.
- Lease renewal cadence is now every five records during trade/order processing. A test replaces the lease owner at the renewal boundary and verifies no subsequent record is persisted by the stale worker.
- The review UI warns on both `WORKER_INTERRUPTED` and `LEASE_LOST` because both may carry partial counters.
- Resolved on 2026-10-21: per-write transaction-level fencing now holds the lease row lock through persistence; slow-write/high-volume regression coverage passed backend CI run 39561621808 (470 passed, 1 warning).


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
