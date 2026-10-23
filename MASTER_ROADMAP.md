## PostgreSQL CI execution confirmation — 24 October 2026

- Inspected `.github/workflows/backend-tests.yml` and successful Backend pytest run [39921411680](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39921411680) on commit `db1053d7f7c53e1c57016f153f11c9897fa59682`. The workflow provisions PostgreSQL 16, sets `TEST_POSTGRES_URL` for `python -m pytest -q`, and the Backend pytest job completed successfully. Thus the `skipif(not TEST_POSTGRES_URL)` PostgreSQL-only tests were enabled for that run (job logs/test output should be consulted if exact per-test counts are needed).
- The workflow also passed Alembic upgrade/downgrade/re-upgrade checks on SQLite and PostgreSQL 16, the broker-write-boundary guard, and an isolated synthetic database/document-volume restore drill.
- The restore drill uses synthetic data created inside CI. It does not substitute for restoring the user's actual retained Oracle Cloud backup or validating an authentic account-specific Upstox contract note.
- The existing source-verification/promotion race test covers allocation-ledger functions, but the integrated concurrency scenario that races real `LiveFillAccountingService.promote_trade` against ledger verification/promotion remains open. Do not mark Phase 3 accounting sign-off complete until that integration gap is addressed or explicitly accepted with evidence.
- PR #6 remains draft/unmerged; live broker order submission remains disabled. All changes are confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains untouched.

---

## Phase 3 concurrency integration status — 24 October 2026

- Current branch head before this documentation update: `2cacf392e5104a8b16307395847239bba945c87b`; branch-head backend CI run [39920815737](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39920815737) passed. PR #6 is draft and unmerged.
- The PostgreSQL-only allocation concurrency suite already contains `test_concurrent_source_verification_and_promotion_serialize_on_evidence`. It concurrently runs the real `verify_component_allocation_ledger` and `promote_verified_component_allocations` functions against synthetic persisted evidence and asserts that both allocations finish reconciled under one reconciliation reference.
- This is a useful source-ledger race test, but it is not the same as a concurrent call to `LiveFillAccountingService.promote_trade` using the real `_load_reconciled_allocation_fees` path while ledger verification/promotion races. That end-to-end live-fill integration scenario remains unproven and is still an acceptance gate.
- The other PostgreSQL allocation test races competing fill sets for a source component and expects exactly one fill set to own that component. Tests are skipped locally without `TEST_POSTGRES_URL`; CI must be checked to confirm the PostgreSQL service actually ran these tests rather than only passing via skips.
- Next engineering task: add or extend a disposable-PostgreSQL integration test using reviewed synthetic evidence, real reconciled allocations, and the actual live-fill accounting service. Assert no partial execution/position writes on failed verification, exactly-once replay, and no acceptance of a conflicting/unreconciled ledger. Then verify the exact resulting head's job logs and test counts.
- Real account-specific broker contract-note validation and restoration from an actual retained Oracle Cloud PostgreSQL/document backup remain separate operational checks.
- Live broker order submission remains disabled. PR #6 stays draft/unmerged. All work remains confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains untouched.

---

## Final conflict-recovery review checkpoint — 24 October 2026

- Reviewed `LiveFillAccountingService.promote_trade` replay and `IntegrityError` recovery paths on branch head `78c66b50714175df7e6923fa0e9328b98bb30cf2`.
- Existing-execution replay locks and refreshes the broker trade record, checks its immutable execution snapshot, and compares execution identity, fill details, charge values and evidence before returning `inserted=False`; conflicting details fail closed.
- The integrity-conflict recovery rolls back the losing transaction, re-queries the execution by broker connection/trade identity, and only returns an idempotent result when the existing execution matches; otherwise it raises a conflict requiring review. Generic failures also roll back.
- Latest branch-head backend pytest CI passed in run [39920205395](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39920205395). The concurrent PostgreSQL test uses a test-only stub for the charge-ledger loader, so it verifies parent/child locking and duplicate-promotion behavior, not the real allocation verifier under the same concurrency interleaving. Ledger validation is covered by separate accounting tests. Do not overstate this as a full production-like concurrent allocation integration test.
- Review status: the inspected replay/rollback paths have coverage and no additional code change is justified by this inspection alone. Phase 3 accounting sign-off is still gated on a final review of the real verifier/promotion concurrency interaction and confirmation of exact-head CI after this documentation update.
- Real broker contract-note authenticity and a restore drill from an actual retained Oracle Cloud PostgreSQL/document backup remain outstanding operational acceptance checks.
- PR #6 stays draft and unmerged; live broker order submission remains disabled. Changes remain confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is untouched.

---

## Phase 3 accounting checkpoint — 24 October 2026

- The concurrent exact-replay PostgreSQL regression passed in implementation CI run [39919563611](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39919563611) for commit `f8441f6d11b863e3ad173282664663cd4985eeb2`. The test exercises two distinct fills and a simultaneous duplicate promotion, expecting two inserted executions and one idempotent replay.
- Documentation checkpoint run [39919590316](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39919590316) passed for commit `c99e4972cf4c2c902bddc076af6327c3bfd25fa7`.
- The next documentation CI checkpoint is still in progress: progress run `39919920878` succeeded, while handover run `39919925329` and audit run `39919932771` were in progress at last inspection. These are earlier documentation heads; any newly synchronized documentation needs its own exact-head CI.
- Accounting review remains open pending exact-head verification and final adversarial review. Passing tests are evidence for covered cases, not a guarantee against every possible concurrency interleaving.
- Real account-specific contract-note validation and restore of an actual retained Oracle Cloud PostgreSQL/document backup remain operational acceptance checks. Synthetic CI restore drills do not satisfy those real-environment checks.
- PR #6 remains draft and unmerged; live broker order submission remains disabled. All work is confined to `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` repository is out of scope.

---

## Current acceptance clarification — 23 October 2026

- **Public contract-note research is complete for development:** third-party examples dated 12 March 2025 and 21 May 2024, plus a sample-note guide, were reviewed for structure and charge categories. See `docs/UPSTOX_CONTRACT_NOTE_AND_API_EVIDENCE.md`.
- The examples are not independently authenticated. No raw public document, personal identifier, or invented “real” evidence is stored in this repository. The checked-in Upstox-style fixture remains explicitly synthetic.
- **A personal/account-specific contract note is not required to continue or complete Phase 3 engineering.** It remains optional future validation for account-specific source authenticity and charge comparison; public aggregate figures must not be treated as proof of per-fill amounts.
- A separate real retained database/document backup and restore test remains a deployment/operational acceptance gate for the Oracle Free Cloud environment. Synthetic CI restore results do not prove recovery of real user data.
- Exact-head CI on commit `18c897a282ea5f8e7c6a55707ad24b6cf8da5b27` passed in [run 39915983869](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39915983869). This does not substitute for the next CI run after this documentation clarification.
- This section supersedes older checkpoint wording below that may imply a personal contract note is required before Phase 3 engineering can proceed. Historical notes remain for audit traceability.
- Scope: `tarunsharma2610-del/tradepro-improved` only. PR #6 remains draft/unmerged; live broker order writes remain disabled.

---

## Phase 3 allocation-weight integrity checkpoint — 23 October 2026

- Code review found that a charge ledger could sum to the correct source total while its individual per-fill amounts did not follow the reviewed allocation basis. Reconciliation now recomputes and verifies each fill's expected amount before promotion.
- Added migration `202610230013` and persisted canonical reviewer-approved weights for `EXPLICIT_REVIEWED`. Source review requires one weight per eligible fill; `QUANTITY` and `NOTIONAL` bases derive weights from persisted broker-trade quantity and price. The verifier checks the complete fill set, basis, method, total, and each per-fill allocation.
- Added regression coverage for a tampered per-fill split that preserves the aggregate total.
- Exact-head CI [run 39912330029](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39912330029) passed on code commit `776ee59485d79b880d7aee0f5c3ecb641eb7db3f`: **567 passed, 1 warning**. Broker-write boundary guard, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore all passed.
- This CI result validates that code commit only; the documentation commits now being synchronized require a new exact-head run. Synthetic restore evidence is not proof of recovery of actual Oracle Free Cloud data or authenticity of a real Upstox contract note.
- PR #6 remains draft/unmerged pending the final review and explicit user approval. Live broker writes remain disabled. Scope remains `tarunsharma2610-del/tradepro-improved`; do not modify original `tarunsharma2610-del/Tradepro`.

---

## Phase 3 checkpoint — concurrency, idempotency and rollback — 23 October 2026

- Exact-head CI passed on code commit `e3eda03b36c616d9655c01f71cc96a2f407fe513`: **566 passed, 1 warning** ([run 39911091610](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39911091610)).
- PostgreSQL verification-versus-promotion race regression passed. Existing regression coverage also checks idempotent promotion replay, changed totals/bases/fill sets, rejected mutation of reconciled rows, caller/accounting replay conflicts, outer-transaction rollback, and injected flush failure rollback.
- Documentation is being synchronized; exact-head CI must be rerun on the resulting latest documentation commit before the checkpoint is considered fully verified.
- Remaining Phase 3 gates: broader accounting review; real Upstox contract-note evidence and actual retained PostgreSQL/document backup plus Oracle Free Cloud restore proof are deferred until user has those records. Synthetic fixtures and CI restore artifacts are not substitutes for real evidence.
- PR #6 remains draft/unmerged pending review and explicit user approval. Live broker writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` must remain untouched.

---

## Phase 3 promotion rollback guard — 22 October 2026

- Exact-head CI run [39813721425](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39813721425) **PASSED** on commit `121741f32ff74c46ccc059f672b3e9f0e020ef14`: backend pytest **565 passed, 1 warning**; configured PostgreSQL 16 migration/safety checks completed successfully.
- Added a regression test that injects a flush failure during charge-allocation promotion and verifies that, after rollback/reload, all allocation rows remain `PENDING_RECONCILIATION` with no reconciliation reference.
- This CI result validates the above commit only. Any subsequent documentation commits require a fresh exact-head run.
- PR #6 remains open, draft, and unmerged pending continued accounting review and explicit user approval. Live broker order writes remain disabled.
- Synthetic restore evidence does not prove recovery of the user's real Oracle Free Cloud data or authenticity of a real broker contract note. Real-data acceptance remains deferred until the user supplies the evidence.
- Scope remains `tarunsharma2610-del/tradepro-improved` only. Do not modify original `tarunsharma2610-del/Tradepro`.

## Phase 3 exact-head CI checkpoint — 22 October 2026

- Latest exact-head workflow: [GitHub Actions run 39808404362](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39808404362) **PASSED** on commit `1fcbb06a78fd06226f0e0e6438cf72b422dc2d4e`.
- Backend pytest: **563 passed, 1 warning**. Broker-write boundary guard passed. SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed. Isolated synthetic PostgreSQL/database + document-volume restore drill and evidence-retention step passed.
- This supersedes earlier “CI pending” notes for commits before this exact head only. Do not treat older commits' results as validation of this head.
- The restore drill uses synthetic data and does not prove restoration of the user's real Oracle Free Cloud database or authentic broker contract-note files.
- PR #6 remains open, draft, and unmerged. Keep it draft until the accounting/idempotency review and user approval. Live broker write operations remain disabled.
- Next: review durable per-fill accounting idempotency/rollback and reconcile any remaining Phase 3 acceptance gates; real broker-note and retained real-backup evidence can be supplied later by the user.
- Repository scope remains `tarunsharma2610-del/tradepro-improved` only; do not modify the original `tarunsharma2610-del/Tradepro`.



## Phase 3 live-accounting integration gate — 22 October 2026

- Code change prepared to require all six charge components to be backed by a currently VERIFIED source-component record and a complete RECONCILED per-fill allocation ledger for the exact broker trade. It rechecks canonical fill manifests, evidence fingerprints, INR currency, approved allocation method/basis, component sums, and caller-versus-ledger amount consistency under transaction row locks.
- Accounting tests use synthetic reviewed-source/allocation rows only. They are not evidence from a real Upstox contract note and do not establish broker-document authenticity.
- Exact-head CI passed on commit `1fcbb06a78fd06226f0e0e6438cf72b422dc2d4e`; see the Phase 3 exact-head CI checkpoint at the top of this file. Keep PR #6 draft/unmerged and live broker write operations disabled.
- Real contract-note verification and an actual retained PostgreSQL backup/document backup plus an Oracle Free Cloud restore drill remain pending user-provided evidence.
- Scope: `tarunsharma2610-del/tradepro-improved` only; never modify original `Tradepro`.
## Phase 3 source-reconciliation safety correction — 22 October 2026

- Code review identified a safety gap in `backend/app/services/broker_charge_allocation_persistence_service.py`: the service previously marked rows `RECONCILED` merely because calculated allocations summed to the caller-provided component total. That is arithmetic reconciliation, not independent verification of a broker contract-note source total.
- Fixed in commit `fce01b98ce33760e3361991e8d2ffba01b0ad281`: newly persisted allocations remain `PENDING_RECONCILIATION`; this service clears the reconciliation reference and does not promote them to `RECONCILED`. A separate source-verification workflow must establish provenance and validate the source component total before promotion.
- Updated regression expectation in commit `8c38ab8ecc8114f392e11ea988ac25c3d7c8e2df` to assert pending status and no reconciliation reference even when arithmetic totals match.
- **Historical CI note superseded:** exact-head CI passed on commit `1fcbb06a78fd06226f0e0e6438cf72b422dc2d4e`; see the Phase 3 exact-head CI checkpoint at the top of this file.
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

## Superseded checkpoint history — 21 October 2026


## Superseded checkpoint history — 21 October 2026

- **Current main HEAD:** `0bd502f83118799d5564e8fd5724d01e8dc975af`. Its exact-head backend CI [run 39566324985](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39566324985) passed. Code/test checkpoint `e56bf4c66f74b875a3ba8fe388138a9d688dd1e2` passed [run 39564568154](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39564568154): 471 tests, 1 warning, broker-write guard and SQLite/PostgreSQL 16 reversible migration cycles.
- The dependency/port matrix and `BrokerFillIdentity` versus manual `BrokerTradeRecord` workflow boundary are reviewed. No bridge or dual-write is approved in Phase 2.
- Phase 2 closure is in final consistency review: stale historical status statements in long-form audit documents are being aligned to the current verified checkpoint. Do not start Phase 3 until that review and its exact-head CI pass. Features classified as Phase 3/4 remain deferred by design.
- Live broker submission, automatic accounting promotion and automatic scheduling remain disabled. The original `Tradepro` repository remains untouched.

---
# Tradepro Improved — Master Roadmap

Last reviewed: 2026-10-21  
Repository: `tarunsharma2610-del/tradepro-improved`  
Working branch: `main`

## Rules of execution
1. Work only in this improved repository; never modify the original `Tradepro` repository.
2. Read `PROJECT_INSTRUCTIONS.md`, `PROGRESS.md`, `AUDIT_REPORT.md`, `ARCHITECTURE.md`, and `HANDOVER.md` before substantive work.
3. Implement one coherent slice at a time. No wholesale branch merges or unreviewed test-file copying.
4. No real broker orders in tests. Live order submission stays disabled.
5. Record exact commit SHAs and CI run URLs; don't label a checkpoint green until the run corresponds to the exact code HEAD.

## Historical checkpoint — formerly marked Current verified baseline
- Latest verified `main` HEAD: `0bd502f83118799d5564e8fd5724d01e8dc975af`; exact-head backend CI passed [run 39566324985](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39566324985).
- Latest code/test checkpoint `e56bf4c66f74b875a3ba8fe388138a9d688dd1e2` passed 471 tests, 1 warning, broker-write guard and SQLite/PostgreSQL 16 migration cycles in [run 39564568154](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39564568154).
- Older 439-pass run [39481385581](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39481385581) is historical baseline evidence only.
- 18 October safety checkpoint: [run 39140514552](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39140514552), SHA `9085d9fbdcc8ee2dd8baac6f5e73f92bd76cfa8b`, 456 passed, 8 skipped, 1 warning. It belongs to a materially different, diverged branch.
- Tree audit: `main` has 38 test modules; the safety branch has 48. Twenty safety-branch test modules remain absent from main; see `SAFETY_BRANCH_PORT_MATRIX.md` for the dependency map. This explains why the test suites differ, but doesn't mean 101 tests were removed from an identical code line.
- Migration graph: 14 files, one linear path from `202608170001` to `202610180008`; no missing parents. The live-fill service is present but unregistered.

## Roadmap and gates

### Phase 1 — Baseline reconciliation and documentation
- [x] Verify the exact 18 October CI checkpoint and current main CI checkpoint.
- [x] Compare test-tree and application-path differences across the two branches.
- [x] Audit the current main migration graph.
- [x] Record findings in `PROGRESS.md` and `AUDIT_REPORT.md`; restore current handover/roadmap documents on main.
- [x] Verify CI after documentation commits against the exact new HEAD; latest code/test CI run 39561621808 passed and documentation commits have their own Actions runs.

### Phase 2 — Port missing safety behavior in dependency-complete slices
- [x] Build and maintain the file-by-file dependency/port matrix in SAFETY_BRANCH_PORT_MATRIX.md, including required models, services, API routes, migrations, configuration, and explicit defer/block decisions.
- [x] Port pure Upstox response parsing and regression tests as an isolated, read-only validation slice; exact-head CI passed 406 tests.
- [x] Port broker trade staging with current-main schema adaptations and fail-closed timestamp validation; exact-head CI passed 431 tests.
- [x] Add cumulative live-fill accounting guard so already-accounted trades plus a new trade cannot exceed the broker-confirmed child fill quantity.
- [x] Port child-order status/fill reconciliation with strict current-main schema adaptation; exact-head CI passed 438 tests.
- [x] Resolve the current workflow boundary: keep intent-based BrokerFillIdentity separate from manual Order BrokerTradeRecord/BrokerOrder; no bridge or dual-write is permitted in Phase 2.
- [x] Add focused regression coverage for idempotent trade identity, partial-fill aggregation, overfill rejection, batch rollback, malformed/inconsistent broker data, and paper-accounting isolation; latest addition covers failed-commit rollback (commit `e56bf4c66f74b875a3ba8fe388138a9d688dd1e2`; exact-head CI passed in run 39564568154).
- [x] Run focused tests, full backend pytest, PostgreSQL concurrency/integration tests, and reversible migrations on SQLite/PostgreSQL 16 (exact-head CI run 39564568154: 471 passed, 1 warning; source guard and SQLite/PostgreSQL 16 migration cycles passed).
- [x] Commit the slice and synchronize progress/audit with exact-head CI evidence (code/test commit `e56bf4c66f74b875a3ba8fe388138a9d688dd1e2`; documentation HEAD `0bd502f83118799d5564e8fd5724d01e8dc975af` passed run 39566324985. Any further changes require new exact-head CI before Phase 3).

### Phase 3 — Live-fill accounting correctness
- [ ] Review `LiveFillAccountingService`, charge provenance, position math, and broker trade/order linkage.
- [ ] Implement a reviewed coordinator path for broker-confirmed trades with connection-scoped identity and transaction-safe idempotency.
- [ ] Prove replay safety, concurrency behavior, rollback behavior, partial fills, out-of-order updates, and crash/restart recovery.
- [ ] Ensure the paper `Position`, paper portfolio cash, and local order state cannot be changed by staged trades before validated promotion.
- [ ] Verify parent-order partial-fill and terminal-state behavior with integration tests.
- [ ] Keep the service unregistered until all gates pass and the path has been reviewed.

### Phase 4 — Live-trading release gates (blocked)
- [ ] Final race-safe safety interlock across authorization, intent claim, kill switch and broker request lifecycle.
- [ ] Broker status/fill/cancel reconciliation and ambiguous-outcome recovery.
- [ ] Account-level risk controls, circuit breaker, credential/token lifecycle and operational alerts.
- [ ] Exact-head unit, PostgreSQL concurrency/integration, migration, frontend build/typecheck, and security/source-guard checks.
- [ ] Backup-safe staging verification with no real-money order.
- [ ] Explicit user approval before any change that enables live submission.

## Historical checkpoint — formerly marked Current status and constraints
- Paper trading remains the usable execution mode. The current mainline includes portfolio risk controls, instrument-master sync, Upstox streaming, a read-only reconciliation interface/worker foundation, and live-fill accounting storage/service foundations.
- No claim of complete live trading, broker order submission, end-to-end live accounting, or production readiness is allowed.
- The original repository remains untouched. No production migrations or real broker orders have been performed.



## Broker-write source guard checkpoint — 2026-10-21

- [x] Add AST source guard for unapproved broker order-write references.
- [x] Add focused unit tests for blocked and explicitly allowed call sites.
- [x] Add guard invocation to `.github/workflows/backend-tests.yml`.
- [x] Verify the broker-write guard on exact current code/test HEAD; latest verified code/test run 39561621808 passed 470 tests and the guard.
- [ ] If CI identifies legitimate PAPER call sites or unapproved write references, review each finding and narrow the guard exceptions only when the actual code path is proven PAPER-only.
- [x] Review the dependency-mapped safety-branch port decisions; the current matrix now classifies each listed safety-only test by compatible port, Phase 3/Phase 4 dependency, or separate schema/product review. Keep BrokerFillIdentity and BrokerTradeRecord separate.
- Live broker writes and automatic accounting promotion remain disabled.


### Broker-write guard review follow-up — 2026-10-21
- [x] Review guard exception scope and identify broad adapter-file and module-wide endpoint exemptions.
- [x] Restrict exceptions to the exact approved PAPER call sites by file, function and attribute chain.
- [x] Add regressions proving unexpected adapter calls and unrelated helper calls are rejected.
- [x] Verify backend CI for the current code/test HEAD; latest verified run 39561621808 passed 470 tests and the guard.
- [x] Record the Phase 2 workflow-boundary decision: keep BrokerFillIdentity and BrokerTradeRecord separate; any future bridge requires a separately reviewed Phase 3 design with identity, owner/account scoping, replay, conflict, rollback, and recovery semantics.


### Exact-head verification update — 2026-10-21
- [x] Verify current `main` head `975717b05a3aa5faa030f3f9e177dbcf6066daf3` in [GitHub Actions run 39550130192](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39550130192): **447 passed, 1 warning**.
- [x] Confirm broker-write AST guard passes on the actual application source.
- [x] Confirm SQLite and PostgreSQL 16 migration upgrade → downgrade → re-upgrade checks pass.
- [x] Fix the failed guard-test line-number assertion from the previous run.
- [x] Review the `BrokerFillIdentity` versus `BrokerTradeRecord` workflow boundary; decision for the current phase is to keep them separate. Any future bridge remains blocked until identity, scoping, idempotency, conflict, rollback and recovery semantics are designed.
- Live broker submission and automatic accounting promotion remain disabled.

### Fill-workflow boundary decision — 2026-10-21
- [x] Inspect intent reconciliation, `BrokerFillIdentity`, manual staging `BrokerTradeRecord`, and `LiveFillAccountingService`.
- [x] Decide to keep the two workflows isolated in the current phase; their uniqueness constraints are separate and do not provide cross-table deduplication.
- [x] Add regression assertions that the read-only reconciliation worker/replay cannot create manual staging rows or accounting rows, nor change portfolio cash.
- [x] Verify CI for the recovery work in subsequent exact-head runs; latest reconciliation lease-fencing verification is backend run 39561621808 (470 passed, 1 warning).
- [x] Continue with stale reconciliation-run recovery and crash-boundary tests before any coordinator/bridge design; subsequent Phase 2 sections below record the completed recovery, atomic finalization, cancellation, and lease-fencing tests.
- [ ] Any future bridge must define canonical identity, account scoping, conflicts, transaction/idempotency, rollback and crash recovery. Live submission and automatic promotion remain disabled.

### Phase 2 — reconciliation crash recovery slice (2026-10-21)
- [x] Add owner/connection-scoped stale-run recovery for `RUNNING` summaries when no unexpired lease exists.
- [x] Preserve existing counters and use safe error code `WORKER_INTERRUPTED`; do not retry broker requests or mutate fill/accounting state.
- [x] Add tests for stale recovery, active-lease protection, ownership/connection isolation and cutoff validation.
- [x] Verify exact-head CI after implementation and timestamp-normalization fixes; subsequent exact-head runs are recorded below.
- [x] Review the crash window between lease release and terminal summary persistence; later work made run finalization and lease release atomic and added rollback/recovery tests. Operational invocation remains gated; no automatic scheduling or broker writes.

## Phase 2 — stale-run recovery integration verified (2026-10-21)

- [x] Add owner/connection-scoped recovery of stale `RUNNING` reconciliation summaries before a new lease is claimed.
- [x] Defer recovery while an unexpired lease exists; fail closed without claiming a lease or calling the broker if recovery errors.
- [x] Add worker-level tests for stale-run recovery, active-lease protection, and recovery-error behavior.
- [x] Exact-head [run 39551504884](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39551504884) for `c1c0d8c6fbbb5dcc1389d2da77e911c815958d88`: 455 passed, 1 warning; source guard and SQLite/PostgreSQL 16 migration cycles passed.
- [x] Add PostgreSQL concurrency coverage for stale-run recovery racing a lease claim; see the verified race/UI gates below.
- [x] Surface interrupted-run summaries as incomplete; the reconciliation UI warns for `WORKER_INTERRUPTED` and `LEASE_LOST`.
- Live submission and automatic accounting promotion remain disabled.


## Phase 2 — stale-run recovery race/UI gates verified (2026-10-21)

- [x] Add PostgreSQL concurrency coverage for recovery racing an expired-lease claim.
- [x] Display a clear incomplete-summary warning when a run has `WORKER_INTERRUPTED`.
- [x] Exact code/test HEAD `d0437be8ef27c4e86d659a9b85bf42dbdb99ecc4`: [backend run 39552046237](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552046237) passed 456 tests, 1 warning, source guard and both migration cycles; [frontend run 39552046207](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552046207) passed TypeScript and Next.js build.
- [x] Audit crash between lease release and durable run-summary finish, including lease-token/expiry inconsistency; atomic finalization and focused recovery regressions passed CI.
- Recovery remains owner/connection-scoped and metadata-only. Keep `BrokerFillIdentity` and `BrokerTradeRecord` separate; live submission and automatic accounting promotion remain disabled.


## Phase 2 — lease integrity and crash-window recovery verified (2026-10-21)
- [x] Fail closed on inconsistent token/expiry pairs during stale-run recovery.
- [x] Harden lease claim to reject inconsistent state and restrict reclaim to both-null released leases or expired leases.
- [x] Test the crash window where lease completion commits but terminal run-summary persistence fails; verify eventual stale-run recovery before the next worker proceeds.
- [x] Exact-head [CI run 39552821228](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552821228): 461 tests passed, 1 warning; broker-write guard and SQLite/PostgreSQL 16 migration cycles passed.
- [x] Make lease completion and run-summary finish transactionally atomic; lost-lease, rollback, and terminal-state ordering regressions passed CI.
- Safety remains unchanged: read-only reconciliation only; no live order submission or automatic accounting promotion.


## Phase 2 — atomic run/lease finalization verified (2026-10-21)
- [x] Finalize terminal run summary and release matching lease in one database transaction.
- [x] Roll back lease release when run finalization cannot update exactly one RUNNING row.
- [x] Mark stale-owner completion as `LEASE_LOST` without releasing the current lease owner.
- [x] Worker regression covers summary-finalization failure, retained lease, expiry, and eventual orphan recovery.
- [x] Exact-head [CI run 39553655005](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39553655005): 463 tests passed, 1 warning; broker-write guard and SQLite/PostgreSQL 16 migration cycles passed.
- [x] Audit cancellation/unexpected exception and lease renewal/expiry paths under concurrent worker activity; regression tests and transaction-level fencing passed CI.
- Safety remains unchanged: read-only reconciliation only; no live order submission or automatic accounting promotion.


## Phase 2 — lease-loss and cancellation recovery verified (2026-10-21)
- [x] Test that lease loss before local processing prevents fill persistence and does not release the newer lease owner.
- [x] Test cancellation during broker read leaves a recoverable RUNNING summary/lease; after expiry, a subsequent worker marks it `WORKER_INTERRUPTED` before starting fresh.
- [x] Preserve atomic run-summary finalization and lease release; rollback keeps the lease when terminal summary persistence fails.
- [x] Exact-head [CI run 39553981172](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39553981172): 465 tests passed, 1 warning; broker-write guard and SQLite/PostgreSQL 16 migration cycles passed.
- [x] Review lease-renewal cadence for large batches and test expiry races around per-record persistence; transaction-level fencing and regression tests passed exact-code CI run 39561621808.
- Safety remains unchanged: read-only reconciliation only; no live order submission or automatic accounting promotion.


## Phase 2 — renewal-boundary and UI completeness gates verified (2026-10-21)
- [x] Reduce renewal cadence to every 5 records in trade and order batches.
- [x] Test that lease loss at a renewal boundary stops before the next record is persisted and preserves the replacement owner's lease.
- [x] Warn in the reconciliation UI for both `WORKER_INTERRUPTED` and `LEASE_LOST` incomplete summaries.
- [x] Backend [CI run 39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380): 466 passed, 1 warning; broker-write guard and SQLite/PostgreSQL 16 migration cycles passed.
- [x] Frontend [CI run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474): TypeScript and Next.js build passed.
- [x] Audit a single slow persistence operation and high-volume processing for lease-expiry races; add transaction-level fencing and regression tests. Verified by backend CI run 39561621808 (470 passed, 1 warning).
- Safety remains unchanged: read-only reconciliation only; no live order submission or automatic accounting promotion.


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

## Phase 3 source-document access and integrity audit — 22 October 2026

- Audited the existing `BrokerChargeEvidence` model and `require_reviewed_charge_evidence` service on `phase3/durable-per-fill-charge-allocation`. The model persists filename, SHA-256, byte size, parser-version metadata, report reference, and review provenance, but explicitly stores the original document outside the table.
- No broker-contract-note-specific upload/retrieval endpoint or storage adapter was found in the audited application entrypoint, API route locations, service paths, and configuration. This is a scoped audit finding, not proof that no generic file handling exists elsewhere.
- The current evidence validator checks evidence identity/connection, source kind, reviewed status, reviewer identity/timestamp, and report reference. It does not retrieve the original bytes, recompute SHA-256/byte size, or parse an authoritative charge-component total.
- **Step 1 remains in progress; no source-storage implementation is claimed.** Before implementation, define a private, persistent, non-web-served storage boundary and a stable evidence-ID-to-object mapping. Retrieval must enforce authorization, prevent path traversal, verify the exact byte count and SHA-256 before parsing, and fail closed on missing/changed content. Do not treat a matching hash alone as proof of broker authenticity.
- Next implementation should add a configurable storage adapter and durable object key tied to the evidence record, then authenticated upload/retrieval and integrity tests. Choose the deployment-backed persistent volume only after confirming the Docker/VM volume layout; do not silently store source documents in an ephemeral container filesystem or Git.
- The prior successful PR-head CI run applies to its exact tested commit only; documentation updates require a fresh CI run on the resulting exact head. PR #6 remains draft/unmerged. Live broker submission and automatic accounting promotion remain disabled. All work stays in `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is not the target.

## Phase 3 private contract-note storage implementation — 22 October 2026

- Added a configurable `BROKER_CHARGE_DOCUMENT_ROOT` (default `/var/lib/tradepro/contract-notes`) and a named Docker volume mounted only into backend and worker containers. The volume is not mounted into Nginx or the frontend.
- Added authenticated upload and download endpoints under `/api/v1/broker-charge-evidence`. Upload is restricted to a broker connection owned by the authenticated user, has a 10 MiB limit, uses an application-generated UUID key, records SHA-256, exact byte size, and uploader identity (`received_by_user_id`), and leaves evidence in `RECEIVED` status. It does not auto-review or promote accounting.
- Added a storage service that writes atomically with restrictive directory/file permissions, validates opaque storage keys against path traversal, and verifies both byte count and SHA-256 before returning source bytes. Missing or changed source bytes fail closed.
- Added Alembic revision `202610220011` to add nullable `storage_key` for backwards compatibility with existing evidence metadata; legacy rows without stored source bytes return unavailable rather than pretending the source was verified.
- Added storage-service tests for successful retrieval, tampering, missing documents, invalid/path-traversal keys, empty content, and deletion, plus API tests for owner-scoped upload/download and tamper rejection. **CI and migration upgrade/downgrade checks on the exact latest head remain required before treating the implementation as verified.**
- SHA-256 only establishes byte-for-byte continuity with the recorded upload; it does not establish that the document genuinely originated from the broker. Independent source-component parsing/review, persisted component provenance, full fill-set/amount/currency/rounding reconciliation, and atomic promotion remain later Phase 3 gates.
- PR #6 remains draft/unmerged. Live broker submission and automatic accounting promotion remain disabled. Scope remains exclusively `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is not the target.

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


## Contract-note storage recovery review — 22 October 2026

- Reviewed `backend/app/services/broker_charge_document_storage_service.py`, its storage tests, and `docker-compose.yml` at PR #6 head `af10cc19c4d3df6ec3cac5a77732d1a2b4ae5b57`.
- API and worker share the named `broker_charge_documents` Docker volume mounted at `/var/lib/tradepro/contract-notes`; Compose also defines a separate `postgres_data` volume. This establishes shared runtime storage wiring, not a verified production backup/restore procedure.
- File writes use a private directory/file mode, a temporary file, file flush/fsync, and atomic replace. Reads recompute SHA-256 and byte size against the evidence record. Existing unit tests cover modified/missing bytes, path traversal, empty content, and deletion.
- Failure/recovery limitation: the filesystem write and database evidence insert are not one atomic transaction. A database rollback after a successful file write can leave an orphaned file. No verified production orphan scanner/cleanup workflow or coordinated database-plus-volume restore drill has been demonstrated at this checkpoint. Do not delete unreferenced files automatically until a grace period, audit log, and dry-run verification are implemented.
- Operational acceptance gate: document encrypted backups for both `postgres_data` and `broker_charge_documents`; restore both to an isolated environment; verify every restored evidence record's storage key, byte count, and SHA-256; report missing/corrupt/unreferenced objects; require explicit approval before cleanup. Test interrupted upload, database rollback after file write, missing file, tampered file, and restore mismatch.
- Storage integrity is not broker-origin authenticity. Keep source-component review and exact allocation reconciliation fail-closed. No automatic accounting posting or live broker order submission is enabled.
- PR #6 remains draft/unmerged pending operational recovery and final review. Scope is `tarunsharma2610-del/tradepro-improved`; do not modify original `Tradepro`.


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


### Phase 3 exact-head CI and acceptance checkpoint — 2026-10-22

- GitHub Actions run 39754635028 passed on PR head 17e9f9d220e504c2a522d8c98289c2765bf02dd2: backend pytest reported 555 passed, 1 warning in 39.64s; the broker-write boundary guard passed; SQLite and PostgreSQL 16 migration round-trip checks passed in this run's job logs. Verify the exact run if this branch advances.
- Accounting acceptance remains under review: code-level checks cover exact fill-set matching, deterministic paise-level largest-remainder allocation, conflict/replay rejection, PostgreSQL evidence-row serialization, and transactional promotion. This is not proof that real contract-note source amounts or production restore have been independently validated.
- The isolated coordinated PostgreSQL + broker_charge_documents restore drill has NOT been executed. Do not claim restore success. Restore into a separate target, verify artifact checksums, file sizes and SHA-256 fingerprints, database/file references and read-only storage audit, retain logs and reviewer sign-off, and keep workers/live broker writes disabled throughout.
- PR #6 remains draft and unmerged. All work is limited to tarunsharma2610-del/tradepro-improved; the original Tradepro repository is out of scope. Live broker order submission remains disabled.
- This documentation checkpoint creates a new commit/head and therefore requires CI verification on the resulting exact head before the checkpoint is considered fully verified.


### Exact-head CI completion — 2026-10-22

- GitHub Actions run 39755207327 completed successfully on commit 5744e8433a5a486938f6e2d6bed5b705ecaea869. Backend pytest passed; broker-write boundary guard passed; SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks all passed. See https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39755207327.
- This confirms that commit only. The following documentation checkpoint will create a new head and must itself receive fresh CI verification.
- Coordinated isolated restore drill remains unexecuted; do not claim recovery acceptance. PR #6 remains draft/unmerged; live broker submission remains disabled; original Tradepro remains out of scope.


### GitHub-only environment clarification and latest CI result — 2026-10-22

- User confirmed Tradepro Improved exists on GitHub only; do not assume a user-local Docker checkout/host. All project work remains restricted to tarunsharma2610-del/tradepro-improved; original Tradepro is out of scope.
- GitHub Actions run 39755480864 passed on commit 1d1533d70eca904e9650a813c671927475cacd36. Backend test suite, broker-write boundary guard, SQLite migration round-trip, and PostgreSQL 16 migration round-trip all succeeded. Run: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39755480864.
- Restore drill is still NOT executed. Since no user-local environment should be assumed, the next recovery step must be provisioned as a disposable isolated CI/cloud environment or explicitly established as unavailable. Do not claim restore success absent captured execution evidence, checksums, storage audit, counts, and reviewer sign-off.
- PR #6 remains draft/unmerged; live broker order submission remains disabled. Any new commit requires its own exact-head CI verification.


### Synthetic restore CI coverage — 2026-10-22

- Added a GitHub Actions step to create a synthetic PostgreSQL evidence table and a synthetic opaque-key document, capture a PostgreSQL custom-format dump plus document archive, verify backup checksums, restore both into a separate temporary database/directory, and compare the restored file SHA-256/byte size and database metadata.
- The workflow retains the synthetic evidence bundle as artifact `synthetic-restore-drill-evidence` for 14 days, including checksum manifest, synthetic dump/archive, result record and expected/restored metadata. This is synthetic CI evidence only, not recovery evidence for real contract-note backups or production data.
- New workflow commits require exact-head CI to finish green before considering this automation validated. The actual coordinated restore drill using real retained backup artifacts remains outstanding; do not claim full recovery acceptance.
- Project is GitHub-only; do not assume a local Docker host. All work remains limited to tarunsharma2610-del/tradepro-improved; original Tradepro is out of scope. PR #6 remains draft/unmerged and live broker order submission remains disabled.


### Latest synthetic restore workflow acceptance checkpoint — 2026-10-22

- GitHub Actions run 39756592781 completed with conclusion success on exact head 98b8260adf17fbee2d6cfe51fcd86175584334c4. Backend tests, broker-write boundary guard, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document archive restore, and evidence-retention step all passed. Run: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39756592781.
- GitHub retained artifact `synthetic-restore-drill-evidence` (artifact ID 12415978081, size 2208 bytes, SHA-256 digest `e2d18437b94a16b1b649ee94deaf81428d35406ab54a731bfef1750c7f360fe2`, expiry 2026-11-05). This confirms synthetic test evidence only; it is not proof of restoring actual retained contract-note backups. Artifact run: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39756592781.
- Accounting acceptance remains open pending independent verification of original contract-note source/component amounts, exact fill identities, paise-level totals, replay/conflict behavior and enclosing-transaction rollback/atomic promotion. The code review alone does not close those gates.
- No local Docker host is assumed; user confirmed Tradepro Improved is GitHub-only. A restore against real retained backup artifacts remains outstanding. All work stays in tarunsharma2610-del/tradepro-improved; original Tradepro is out of scope. PR #6 remains draft/unmerged and live broker order submission remains disabled.
- This checkpoint changes documentation and must receive fresh CI on the resulting exact head before it can be called CI-verified.

### Phase 3 source-to-ledger review follow-up — 2026-10-22

- The documentation checkpoint commit `0c74960c9b0bb1590aa14ef709f55e691b3ac5e2` passed its exact-head GitHub Actions run `39757964236`: backend pytest, broker-write boundary guard, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document restore, and evidence artifact retention all passed.
- Further review confirms allocation persistence serializes on the evidence row, checks target trades belong to the broker connection, rejects conflicting replay/fill sets, and keeps rows pending until the separate source-ledger verification and promotion workflow.
- The endpoint records human transcription and reviewer attestation; it does not automatically parse or independently authenticate the broker's stated component amount. A real contract note and real backup set were not available, so those acceptance gates remain open.
- PR #6 stays draft/unmerged, live broker writes remain disabled, and all work is confined to `tarunsharma2610-del/tradepro-improved`. This entry is a record of review/CI status, not a claim that real-source reconciliation or real-backup restore is complete.


## Phase 3 checkpoint — lock-order regression verified (22 October 2026)

- Latest exact-head CI run [39817017949](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39817017949) passed on commit `7809e8d7981a19625142dc73e689caa2976c97d6`: backend pytest **565 passed, 1 warning**.
- Live-fill accounting now defers target allocation-row locks until after source-component verification, refreshes target allocations under lock, and fails closed if their state changed. The regression test checks lock-order invariants rather than a brittle exact query prefix.
- A preceding implementation run failed on an outdated test expectation; the test was corrected and the latest run passed.
- PostgreSQL concurrency coverage exists for competing allocation requests on one evidence record. Concurrent source verification versus promotion, deadlock/retry handling, and conflicting fill-set replay still need further review.
- Real contract-note authenticity and a real retained Oracle Cloud database/document restore remain deferred until real evidence is available. Synthetic restore testing does not prove real-data recovery.
- PR #6 remains open/draft/unmerged pending review and explicit user approval. Live broker order writes remain disabled.
- Scope remains `tarunsharma2610-del/tradepro-improved` only; do not modify original `tarunsharma2610-del/Tradepro`.


## 2026-10-23 — live-fill/ledger concurrency checkpoint

- Added PostgreSQL integration test `test_live_fill_promotion_races_with_component_ledger_verification` in `backend/tests/test_broker_charge_allocation_postgres_concurrency.py`.
- Commit: `66fda569b1e4879d270a970cb5b6d216c2f55f9c`; exact-head CI run `39923699033` passed: **570 passed, 1 warning in 30.89s**. Broker-write boundary guard, SQLite/PostgreSQL 16 migration checks, and synthetic database/document-volume restore drill passed.
- CI: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39923699033
- Safety: only `tarunsharma2610-del/tradepro-improved` changed; PR #6 remains draft/unmerged and live broker order writes remain disabled.
- Limitation: fixtures and document bytes are synthetic; authentic Upstox contract-note validation and a real Oracle-host backup restore remain outstanding.
