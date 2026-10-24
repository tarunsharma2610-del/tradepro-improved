## Brokerage cap entrypoint integration — 23 October 2026

- The previous exact-head implementation CI passed on commit [3445a748b3fbd3944362ed6e46873bffc30fd384](https://github.com/tarunsharma2610-del/tradepro-improved/commit/3445a748b3fbd3944362ed6e46873bffc30fd384): **712 passed, 1 warning**; SQLite/PostgreSQL migration round-trips, broker-write boundary guard, synthetic restore drill and evidence retention also passed.
- Follow-up review found the general `calculate_charge_for_trade` entry point selected an approved brokerage rule but bypassed the rule-bound minimum/maximum caps. Fixed it to route order-notional brokerage through `calculate_order_brokerage`, and added regression test `test_trade_charge_entrypoint_applies_caps_from_selected_brokerage_rule`. Code/test commits: [d6d60a03732ab322785d5e020f0521a4b96162c9](https://github.com/tarunsharma2610-del/tradepro-improved/commit/d6d60a03732ab322785d5e020f0521a4b96162c9) and [78f5f27135137a1d8f0882d2c0a91d013f6e8556](https://github.com/tarunsharma2610-del/tradepro-improved/commit/78f5f27135137a1d8f0882d2c0a91d013f6e8556).
- **The entrypoint follow-up has not yet been validated by CI.** Earlier 712-pass results do not cover these later code/test commits. CI for the resulting latest documentation head must complete before this gate is marked green.
- The cap-aware snapshot schema v4 records minimum/maximum values in the snapshot and rule fingerprint; same-event cap changes are conflicting replays. These helper functions do not prove official Upstox rates or legal/tax applicability, and the snapshot builder does not itself persist or promote charges.
- Automatic quantity/notional allocation remains disabled until reviewed, effective-dated component-specific tariff rules exist. Existing variance tests keep estimate-vs-actual comparisons review-only and do not promote charge ledger entries.
- PR #6 remains draft/unmerged. Live broker order writes remain disabled. Synthetic restore is not actual Oracle Cloud recovery. All work remains in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` is out of scope.

---

## Rule-bound brokerage caps and passing CI — 23 October 2026

- Order-level brokerage minimum/maximum caps are now fields on the validated `TariffRule`, and are accepted only for order-notional brokerage rules. Caps must be finite, nonnegative, and paise-precise; minimum cannot exceed maximum.
- `calculate_order_brokerage` reads caps from the reviewed rule rather than caller-supplied parameters. Tariff estimate snapshot schema is now v4; snapshots include the cap values and include them in the rule fingerprint. Changing a cap for the same event produces a conflicting replay rather than a silent overwrite.
- Exact-head backend workflow [39976363279](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39976363279) passed on commit [3445a748b3fbd3944362ed6e46873bffc30fd384](https://github.com/tarunsharma2610-del/tradepro-improved/commit/3445a748b3fbd3944362ed6e46873bffc30fd384): **712 passed, 1 warning**. Broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and evidence retention passed.
- The warning is a Starlette/AnyIO deprecation warning; the workflow also reports Node.js action-runtime deprecation warnings. They did not fail the run. Do not claim that this CI head verifies any later documentation-only commit until CI is checked for that exact head.
- This implementation does not establish official Upstox tariff rates or tax-law applicability; caps/rates must come from a reviewed source record. The snapshot helper itself does not persist estimates or promote them into actual charges. Synthetic restore is not actual Oracle Cloud recovery.
- Next accounting gate: verify aggregate order-level estimate-versus-actual variance handling, then rerun exact-head CI and synchronize all nine documents after any further changes. PR #6 remains draft/unmerged; live broker order writes remain disabled.
- All work is confined to `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` repository is out of scope.

---

## Brokerage cap precision and CI checkpoint — 23 October 2026

- Brokerage minimum and maximum inputs now reject values with more than two decimal places, avoiding sub-paise cap ambiguity. Regression tests cover sub-paise minimum and maximum values.
- Exact-head workflow run [39975215770](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39975215770) passed on commit [d650471895e6938b175434eff20b7d7421abb046](https://github.com/tarunsharma2610-del/tradepro-improved/commit/d650471895e6938b175434eff20b7d7421abb046): **709 passed, 1 warning**. Broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and evidence retention completed successfully.
- The remaining warning is a third-party `starlette.testclient` / AnyIO deprecation warning; GitHub Actions also emitted Node.js action-runtime deprecation warnings. These did not fail the run and should be tracked separately from accounting correctness.
- The nine project documents are now being synchronized after this green code/test head. A new CI run for the resulting documentation commit is required before claiming that latest documentation head is green.
- This run's restore evidence is synthetic; it does not prove recovery of actual Oracle Cloud production data. Calculation helpers validate structure and precision, not official Upstox rates or legal/tax applicability.
- PR #6 remains draft/unmerged pending accounting acceptance review and explicit user approval. Live broker order writes remain disabled. All work remains in `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` repository is out of scope.

---

## Latest Phase 3 CI checkpoint — 23 October 2026

- Stamp-duty regression setup was corrected in commit [c98d13d86031ffe173546dbbc9c8b0234e02456e](https://github.com/tarunsharma2610-del/tradepro-improved/commit/c98d13d86031ffe173546dbbc9c8b0234e02456e): invalid-basis test cases now explicitly select the intended `BUY` transaction side so each case reaches the basis guard it is designed to exercise.
- Exact-head GitHub Actions run [39974055917](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39974055917) passed on that code/test commit: **707 passed, 1 warning**. Broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and evidence retention all passed.
- Existing tests already cover inclusive effective-date boundaries, expiry of old tariff rules, overlapping approved-rule rejection, deterministic largest-remainder paise allocation, input-order independence, zero-weight residual handling, and exact source-total reconciliation. Do not duplicate these tests; review whether the rules are wired into real reviewed component-specific tariff selection before enabling automatic allocation.
- Brokerage and GST calculation helpers and stamp-duty side/product/base guards are arithmetic safeguards only. They do not establish official Upstox tariff rates or tax-law applicability. Authentic contract-note verification and actual Oracle Cloud backup recovery remain separate evidence/deployment gates.
- The documentation files are being synchronized after this green code/test head. Rerun CI on the resulting latest documentation commit before claiming the complete latest head is green.
- PR #6 remains draft/unmerged pending accounting acceptance review and explicit user approval. Live broker order writes remain disabled. Work is exclusively in `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` repository is out of scope.

---


## Phase 3 — durable per-fill charge allocation verification — 23 October 2026

- Latest test refinement commit: [e73c9cbb8b5c4e34abe9874b548dbae5cbf762af](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e73c9cbb8b5c4e34abe9874b548dbae5cbf762af). The PostgreSQL concurrency test now only treats the expected `ValueError` for pending/unreconciled allocation rows as a valid fail-closed outcome; unexpected exceptions fail the test.
- Exact-head GitHub Actions run [39971530839](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39971530839) passed: **688 passed, 1 warning**. Broker-write boundary guard, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and retained restore evidence all passed.
- This run validates synthetic test fixtures and restore mechanics only. It does not validate an authentic personal Upstox contract note or prove restoration of the user's actual Oracle Cloud backup.
- The nine required project documents are being synchronized after this green code/test head; rerun CI on the resulting latest documentation commit before calling the documentation checkpoint current.
- PR #6 remains draft/unmerged pending complete accounting/idempotency review and explicit user approval. Live broker order submission remains disabled. All work is limited to `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` repository is out of scope.

---

---

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

## Concurrent exact-replay verification — 24 October 2026

- The PostgreSQL concurrency regression for two distinct fills plus a concurrent duplicate promotion passed in implementation CI run `39919563611` on commit `f8441f6d11b863e3ad173282664663cd4985eeb2`.
- The latest documentation checkpoint also passed in run `39919590316` on head `c99e4972cf4c2c902bddc076af6327c3bfd25fa7`. PR #6 currently points to that exact head, remains draft and unmerged.
- Reviewed existing regression coverage includes changed execution detail rejection, changed evidence rejection, omitted evidence metadata on exact replay, conflicting evidence IDs, failed-commit rollback, non-reconciled/missing per-fill allocations, charge-ledger mismatch, exchange-time ordering, and cumulative quantity caps.
- This supports the reviewed replay/rollback behaviors but does not establish live operational readiness. Real retained Oracle backup restore and account-specific authentic contract-note validation remain outstanding operational checks.
- Live broker order submission remains disabled. All changes are confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains untouched.

---

## Concurrent exact-replay regression — 24 October 2026

- Adversarial review found that PostgreSQL concurrency coverage exercised two distinct fills racing for the same parent/child order, but did not explicitly exercise two simultaneous calls promoting the exact same broker trade with identical evidence.
- Extended the existing PostgreSQL-only live-fill concurrency test to launch three concurrent promotions: two distinct confirmed fills plus a duplicate call for the first trade using the same evidence. Expected outcome is exactly two inserted executions and one idempotent replay, with the live position and execution count reflecting only the two distinct fills.
- Test change committed as `f8441f6d11b863e3ad173282664663cd4985eeb2`. Exact-head CI is pending; do not consider this race covered until the PostgreSQL concurrency test passes on the final head.
- PR #6 remains draft/unmerged; live broker order submission remains disabled; all work is limited to `tradepro-improved`.

---

## Deterministic row-lock ordering follow-up — 24 October 2026

- Latest documentation CI runs `39918605262`, `39918611978`, and `39918618265` completed successfully on their respective commits.
- Continued adversarial review found that the allocation verifier locked allocation rows and trade rows without explicit deterministic ordering, while live-fill accounting locks component allocation rows in sorted fill-ID order. Although the PostgreSQL concurrency suite passes, making lock acquisition order explicit reduces avoidable deadlock risk across verifier/promotion paths.
- Updated the source reconciliation verifier to lock allocation rows by `broker_trade_record_id, id` and trade rows by `BrokerTradeRecord.id`. This is a targeted concurrency hardening change; exact-head CI is pending and required before claiming it verified.
- PR #6 remains draft/unmerged. Live broker order submission remains disabled. All work stays in `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains untouched.
- Real account-specific contract-note authenticity and restoration of an actual retained Oracle PostgreSQL/document backup remain separate operational checks, not synthetic CI claims.

---

## Current accounting review status — 24 October 2026

- Exact-head CI for the latest PR head `fe723b6929e4a8ce429470b339519e4ee9616e4c` passed in [run 39918318386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39918318386): backend pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore, and evidence-retention steps all succeeded.
- The evidence-identity migration and replay regression passed in an earlier successful exact-head run; the subsequent lock-order correction also passed in run `39918291052`, and all three documentation commits passed their respective CI runs. This is CI evidence for the current code/doc heads, not a proof of all possible concurrency behavior.
- Accounting review remains open for final adversarial review and merge approval. PR #6 remains draft and unmerged; live broker order submission remains disabled.
- The synthetic restore drill does not prove recovery of actual Oracle Free Cloud data. Real retained backup/restore acceptance and authentic account-specific broker evidence remain separate future operational checks.
- All changes remain confined to `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` repository is out of scope.

---

## Live-fill evidence-identity idempotency fix — 24 October 2026

- Review found that exact replay compared the visible charge reference and amounts but did not persist/compare the reviewed evidence row identity on `Execution`. That could make a different evidence record with the same reference and amounts indistinguishable during replay.
- Added nullable `executions.charge_evidence_id` with a foreign key to `broker_charge_evidence.id`, plus migration `202610240014` (down revision `202610230013`). Nullable preserves compatibility with paper/history rows.
- Live-fill promotion persists the reviewed evidence ID. The shared exact-execution comparison now requires evidence-ID equality, which also applies to the concurrent `IntegrityError` recovery path.
- Added a regression test: a second evidence ID with the same visible reference and identical charge values must be rejected as a conflicting replay; only one execution/position update may remain.
- Code and migration commits are on `phase3/durable-per-fill-charge-allocation` in `tarunsharma2610-del/tradepro-improved` only. Exact-head CI for the resulting head is pending; do not call this change verified until backend tests, SQLite/PostgreSQL 16 migration round-trips, and the broker-write boundary guard pass on that exact SHA.
- PR #6 remains open, draft, and unmerged. Live broker order submission remains disabled. The original `tarunsharma2610-del/Tradepro` repository is out of scope.
- Real contract-note authenticity and an actual paired PostgreSQL/document-volume restore remain separate operational gates; neither is required to continue synthetic engineering tests.

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

## Public Upstox contract-note example review — 23 October 2026

- Located publicly shared examples purporting to be Upstox contract notes: [12 March 2025 example on Scribd](https://www.scribd.com/document/971660843/CW-T-3JCTYG-20250312-NSE-66319975-1), [21 May 2024 example on Scribd](https://www.scribd.com/document/735902961/CW-T-842243-20240521-NSE-35749411), and [Quicko's sample-note guide](https://learn.quicko.com/download-contract-note-upstox-trader). These are third-party/public copies; broker-origin authenticity is not independently verified. They may expose personal information, so do not copy raw documents or identifiers into this repository.
- Structural review supports fields for trade/order identifiers and timestamps, instrument, buy/sell, quantity, rate/WAP, brokerage, net rate, trade obligation, and charge/tax summary. One public example says trade-wise levies are available on request, so its aggregate summary cannot independently prove the correct charge amount for each fill.
- Public examples are sufficient for document-layout/field coverage and synthetic parser/accounting tests. A personal note is NOT a prerequisite for continuing Phase 3. Real source-origin verification and account-specific API comparisons remain optional future validation; do not label a public copy or synthetic fixture as authenticated account evidence.
- Exact-head CI run [39914355718](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39914355718) completed successfully on head `b79c52b03d97c46da9df5a575f79fee581802ff6`: backend tests, broker-write boundary guard, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore, and evidence-retention steps passed. This is synthetic CI coverage, not a real-data restore or broker-origin verification.
- Scope remains `tarunsharma2610-del/tradepro-improved` only. PR #6 remains draft/unmerged; live broker write operations remain disabled.

---

## Upstox contract-note/API research — 23 October 2026

- Public Upstox Help Center documentation explains how to download the user's authentic contract note from My Account → Reports → Miscellaneous reports → report type `CONTRACT`, and says it is emailed within 24 hours.
- Official authenticated API docs expose historical trade history (`GET /v2/charges/historical-trades`) and an aggregate segment/financial-year charge breakdown (`GET /v2/trade/profit-loss/charges`). These are valuable cross-checks, but neither is a substitute for the original contract-note document; the reviewed public API catalogue did not expose a contract-note PDF endpoint.
- Research notes and exact source links: `docs/UPSTOX_CONTRACT_NOTE_AND_API_EVIDENCE.md`.
- No authentic account-specific note has been retrieved. Real-document acceptance is pending user-provided evidence. Do not fabricate this evidence or claim API-only data validates the original note. Do not share credentials/tokens. Keep all broker-write actions disabled.

---

## Phase 3 allocation-weight integrity checkpoint — 23 October 2026

- Code review found that a charge ledger could sum to the correct source total while its individual per-fill amounts did not follow the reviewed allocation basis. Reconciliation now recomputes and verifies each fill's expected amount before promotion.
- Added migration `202610230013` and persisted canonical reviewer-approved weights for `EXPLICIT_REVIEWED`. Source review requires one weight per eligible fill; `QUANTITY` and `NOTIONAL` bases derive weights from persisted broker-trade quantity and price. The verifier checks the complete fill set, basis, method, total, and each per-fill allocation.
- Added regression coverage for a tampered per-fill split that preserves the aggregate total.
- Exact-head CI [run 39912330029](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39912330029) passed on code commit `776ee59485d79b880d7aee0f5c3ecb641eb7db3f`: **567 passed, 1 warning**. Broker-write boundary guard, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore all passed.
- This CI result validates that code commit only; the documentation commits now being synchronized require a new exact-head run. Synthetic restore evidence is not proof of recovery of actual Oracle Free Cloud data or authenticity of a real Upstox contract note.
- PR #6 remains draft/unmerged pending the final review and explicit user approval. Live broker writes remain disabled. Scope remains `tarunsharma2610-del/tradepro-improved`; do not modify original `tarunsharma2610-del/Tradepro`.

---

## Phase 3 latest exact-head CI — 23 October 2026

- Exact-head CI run [39911091610](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39911091610) **PASSED** on commit `e3eda03b36c616d9655c01f71cc96a2f407fe513`.
- Backend pytest: **566 passed, 1 warning**. The PostgreSQL concurrency regression test for simultaneous source-ledger verification and promotion passed. Broker-write boundary guard, SQLite and PostgreSQL 16 migration checks, and the isolated synthetic restore drill all passed.
- The new race test uses synthetic records/document content. It improves software concurrency coverage but does not validate a real Upstox contract note or restore the user's actual Oracle Free Cloud database.
- This CI result applies only to the stated commit. Documentation commits or later code changes need a fresh exact-head run.
- PR #6 remains open, draft, and unmerged. Continue transaction/idempotency review before recommending merge; live broker write operations remain disabled.
- Repository scope remains exclusively `tarunsharma2610-del/tradepro-improved`; do not modify original `tarunsharma2610-del/Tradepro`.

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

<!-- Authoritative checkpoint audit: 2026-10-21; updated after Phase 2 lease-fencing verification. -->
## Authoritative checkpoint audit — 21 October 2026

- **Repository/branch:** `tarunsharma2610-del/tradepro-improved`, `main`. The original `tarunsharma2610-del/Tradepro` repository is a protected baseline and must remain untouched.
- **Latest code/test commit:** `e56bf4c66f74b875a3ba8fe388138a9d688dd1e2` adds failed-commit rollback coverage. Exact-head backend CI [run 39564568154](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39564568154) passed 471 tests, 1 warning, broker-write guard and SQLite/PostgreSQL 16 reversible migrations. Documentation HEAD `adb69aeb05b70ba4fa9095fc73d9dea033d31eec` also passed [run 39565251793](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39565251793).
- **Exact-commit backend CI:** [run 39561621808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39561621808) passed **470 tests, 1 warning**, the broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles. It includes lease-fence ownership/expiry tests, a high-volume batch-stop regression, and a PostgreSQL contention test proving an expired lease cannot be reclaimed while a fenced persistence transaction still holds the row lock.
- **Documentation checkpoint CI:** [run 39561881539](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39561881539) passed on documentation commit `292cad087bf0febad7793dcec164ebb5435726e8`; this follow-up synchronizes the closure wording and design note.
- **Frontend:** no frontend files changed in this Phase 2 patch. The latest verified frontend CI remains [run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474), which passed TypeScript and Next.js build on code/test commit `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`.
- **Previously completed Phase 2 protections:** atomic run/lease finalization; stale-owner protection; cancellation and interrupted-run recovery; inconsistent token/expiry rejection; five-record renewal checks; and incomplete-summary warnings for `WORKER_INTERRUPTED` and `LEASE_LOST`.
- **Newly completed lease-expiry audit:** every worker-owned reconciliation persistence operation (fill identity, review issue, order transition and fill-to-intent link) now obtains a current, unexpired lease fence immediately before the write. The lease row is locked through the repository's persistence transaction, so a competing claimant must wait until that transaction commits or rolls back. Lease loss fails closed before the next mutation.
- **Scope clarification:** Phase 2's defined engineering checks are verified, including the dependency/port matrix, identity boundary, rollback coverage, full backend suite, PostgreSQL concurrency, source guard and reversible migrations. The final documentation sync must pass exact-HEAD CI before Phase 3 begins. Phase 3/4-only safety features remain deferred by design.
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

## Authoritative continuation checkpoint — 21 October 2026

- Latest code/test commit: [e56bf4c66f74b875a3ba8fe388138a9d688dd1e2](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e56bf4c66f74b875a3ba8fe388138a9d688dd1e2), adding a regression test that simulates database commit failure during live-fill promotion and asserts rollback leaves no Execution/LivePosition and does not alter the paper position.
- **Exact-head CI is not yet confirmed.** The commit-status query returned no statuses and the available workflow lookup returned no runs; neither result proves pass or failure. Verify the actual GitHub Actions run for this commit before closing Phase 2.
- The earlier reconciliation crash-recovery/lease-fencing checkpoint remains verified by backend run [39561621808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39561621808) (470 passed, 1 warning; source guard and SQLite/PostgreSQL 16 reversible migrations passed). This older run does not cover the newest test.
- The workflow-boundary decision is resolved for Phase 2: keep BrokerFillIdentity (intent-reconciliation evidence) separate from manual BrokerTradeRecord staging. Do not bridge or dual-write them. The dependency/port matrix is SAFETY_BRANCH_PORT_MATRIX.md; defer Phase 3/Phase 4-only safety, coordinator, charge-adjustment, and broker-write features instead of merging the safety branch wholesale.
- **Previous verified checkpoint:** code/test HEAD `00ee9bad0e962d92244da6f63da1e46ba058ad6f` passed [CI run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386). Current documentation sync and its exact-head CI status are recorded in the top checkpoint. Keep live broker submission, automatic accounting promotion, and automatic scheduling disabled. Original Tradepro remains untouched.

# Tradepro Improved — Handover

Last reviewed: 2026-10-21  
Repository: https://github.com/tarunsharma2610-del/tradepro-improved  
Working branch: `main`

## Non-negotiable safeguards
- Work only in this repository. The original `tarunsharma2610-del/Tradepro` repository is a protected baseline and must remain untouched.
- Preserve existing behavior and use small, reviewable changes. Inspect the current branch before every change.
- Never place real broker orders in tests. Keep live order submission disabled; PAPER remains the safe default.
- Do not claim tests or migrations passed unless the exact run/commit proves it. Do not deploy production migrations without backup and staging verification.
- Do not merge or cherry-pick `safety/fail-closed-trading-mode` wholesale: the branch is materially divergent from `main`.

## Historical checkpoint — formerly marked Current main-branch baseline
- Latest verified code/test checkpoint: `84f3a3e48a64b6e1d764a87a2b337b2a8f052741`.
- GitHub Actions [run 39482592808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39481385581): **439 passed, 1 warning**. SQLite and PostgreSQL 16 Alembic upgrade → downgrade → re-upgrade checks passed.
- Documentation commits after that code checkpoint record the baseline discrepancy and branch comparison. Exact-head CI after those documentation commits must be checked before calling the latest HEAD green.
- Current `main` has 38 `backend/tests/test_*.py` modules, including Upstox response parsing, broker trade staging and child-order reconciliation. The 18 October safety checkpoint at `9085d9fbdcc8ee2dd8baac6f5e73f92bd76cfa8b` recorded **456 passed, 8 skipped, 1 warning** in [run 39140514552](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39140514552), with 48 test modules on that branch. Twenty-two test modules and 19 related API/model/service paths from that branch remain absent on `main`. This is a different code/test tree, not proof that exactly 101 tests were deleted from the same commit line.
- GitHub reports the selected branch comparison as divergent (389 commits ahead / 1,029 behind). Port behavior and tests in dependency-complete slices; do not copy isolated tests that import absent services.
- Migration audit: 14 revision files form a linear chain from `202608170001` through terminal head `202610180008`, with no missing parent reference. CI verifies reversible migration cycles on SQLite and PostgreSQL 16.

## Historical checkpoint — formerly marked Current implementation boundaries
- The app has a FastAPI backend and Next.js frontend, paper trading, instrument sync, Upstox market-data streaming, portfolio risk controls, and a read-only reconciliation UI/worker foundation.
- The live-fill accounting service and supporting broker-order/trade/live-position models exist on `main`; the service remains intentionally unregistered.
- Broker-confirmed trade ingestion into reconciliation, one-transaction promotion into Execution/live positions with charge provenance, parent-order status accounting, and end-to-end crash/replay recovery are not yet complete.
- Live order submission is not implemented as a safe end-to-end path. Do not enable it. No real broker request or production migration was performed in the verified checkpoint.

## Immediate next task
Build a dependency map between the safety branch's missing tests and the source/migrations they require. Select one coherent behavior slice (start with broker trade staging and response parsing), inspect current `main` implementations, port only the required behavior, add compatible regression tests, run focused tests and full backend/PostgreSQL/migration CI, then record exact commit and run IDs in `PROGRESS.md` and `AUDIT_REPORT.md`.

## Required working sequence
Read `PROJECT_INSTRUCTIONS.md`, `PROGRESS.md`, `AUDIT_REPORT.md`, `ARCHITECTURE.md`, and this handover. Then: inspect → map requirement/source/test dependencies → make one minimal change → run targeted tests → run relevant full suite and migrations → commit → update progress/audit → inspect exact-head CI. Keep all broker writes disabled.



## Resume checkpoint — broker-write source guard (2026-10-21)

This update supersedes the earlier "Immediate next task" paragraph above.

- Latest code/config commit: `c563683b85d7801cd19dcf3d1c7784ec6e433d1f`; current docs have been advanced in subsequent commits. Verify actual `main` HEAD before further writes.
- Added `backend/scripts/check_broker_write_boundary.py`, seven focused tests, and a required backend CI step. Documentation now records this guard.
- The previous 439-pass run applies to commit `84f3a3e48a64b6e1d764a87a2b337b2a8f052741`, not automatically to the new source-guard changes. The connected workflow tool does not list push-triggered runs; exact-head CI must be checked before claiming this step passed.
- First next action: inspect the CI result for current `main`; if it fails, read the guard findings and correct the scanner or narrowly document proven PAPER-only exceptions. Never blanket-ignore a broker-write call.
- After exact-head CI, continue the mapped safety-branch audit with one dependency-complete slice. Keep the intent worker's `BrokerFillIdentity` and manual-order `BrokerTradeRecord` paths separate until a reviewed bridge is designed. No live broker submission or automatic fill promotion.


## Resume note — tightened broker-write source guard (2026-10-21)

- Current work narrowed AST guard exemptions: the whole Upstox adapter is scanned, and the portfolios endpoint exception is limited to the actual `place_order` and `cancel_order` functions. Added tests for unexpected adapter calls and an unrelated helper in the same module.
- Relevant commits: `00c0986a0628cc6b55b842cfcf6e7fc01b071de4`, `30c1aa7b78de357e070f7cdb37b3719112ee8850`, `a75a15a0feae98fb2eb4d4301f199d33566c0acf`, `430d00ae787a250f5c7f425e2b72ad02a38c396a`.
- **Current verified checkpoint:** code/test HEAD `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`; documentation HEAD `ee3a3889e32b90b105ee2c2ca4fe6ca7c958d84e`.
- **Do next:** the completeness audit found no missing implementation within the read-only reconciliation recovery slice through the renewal-boundary checkpoint. Continue with the documented single-slow-record/high-volume lease-expiry audit; do not restart recovery unless new evidence identifies a concrete gap. Keep live submission and automatic accounting promotion disabled.


## Verified resume checkpoint — 2026-10-21

- Current `main` HEAD `975717b05a3aa5faa030f3f9e177dbcf6066daf3` is verified green: [GitHub Actions run 39550130192](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39550130192), **447 passed, 1 warning**. The AST broker-write guard passed; SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks passed.
- The preceding commit's CI failure was caused by an incorrect expected line number in the guard test; the assertion was corrected in the current head. No current CI failure is open.
- Resume Phase 2 by reviewing the dependency map and deciding whether `BrokerFillIdentity` and `BrokerTradeRecord` represent separate workflows or need a carefully specified transactional bridge. Do not connect them before defining identity, owner/account scope, conflict handling, idempotent replay, rollback and crash recovery.
- Keep live broker submission and automatic accounting promotion disabled.

## Resume checkpoint — fill-workflow boundary review (2026-10-21)

- Latest code/test commit: `3683082509c4b331ab9c7ebceb928e925414de35` adds regression assertions that the intent-based reconciliation worker never creates manual `BrokerTradeRecord` staging rows, `Execution`, or `LivePosition`, and does not change portfolio cash, including on replay. Exact-head CI is pending.
- Architecture decision: keep `BrokerFillIdentity` and `BrokerTradeRecord` separate for now. They represent the intent-based reconciliation evidence path and the manual Order staging/accounting path, respectively. Their independent uniqueness constraints do not deduplicate across tables.
- Do not bridge or dual-write until canonical fill identity, owner/connection/order/intent linkage, conflict semantics, atomicity, idempotent replay, rollback and crash recovery are designed and tested.
- Next: verify exact-head CI, then continue Phase 2 stale-run/crash-recovery review. Live broker submission and automatic accounting promotion remain disabled.

## Resume checkpoint — orphaned run recovery (2026-10-21)

- Added explicit recovery for stale `RUNNING` reconciliation summaries. `fail_orphaned_runs` only marks a run `FAILED/WORKER_INTERRUPTED` when it is older than the cutoff and the scoped broker connection has no unexpired lease; it does not rerun broker I/O or touch fills/accounting.
- Tests cover stale run, active lease, user/connection scoping, cutoff validation. SQLite timestamp normalization and active-lease transaction rollback are included.
- Latest implementation commits: `c21dc711c9102c4a6f0aad36b404ba8c1b57d5f8`, `007383da7f0ca5a1793098288f610ed98de9eb71`, `298caa0a1a05124cdf6fdc9d94ff0644f20295a5`. Verify CI for the exact latest head before further changes.
- The recovery method is not wired to a scheduler yet. Keep the two fill workflows separate; no live broker submission or automatic accounting promotion.

## Latest verified checkpoint — stale-run recovery (2026-10-21)

- Exact current code head `c1c0d8c6fbbb5dcc1389d2da77e911c815958d88`, [GitHub Actions run 39551504884](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39551504884): **455 passed, 1 warning**; broker-write guard and SQLite/PostgreSQL 16 migration cycles passed.
- Worker recovery now runs before lease claim. Stale owner/connection-scoped `RUNNING` summaries become `FAILED/WORKER_INTERRUPTED` only when no unexpired lease is active; a recovery error prevents lease claim and broker I/O.
- Next: test recovery/lease-claim races on PostgreSQL and ensure interrupted run summaries are presented as incomplete. The stored summary counters are not incremental; zero values with `WORKER_INTERRUPTED` are not proof of no partial work.
- Keep `BrokerFillIdentity` and `BrokerTradeRecord` separate, live broker submission disabled, and automatic accounting promotion disabled.


## Latest verified checkpoint — orphan recovery race and UI warning (2026-10-21)

- Exact current code/test HEAD `d0437be8ef27c4e86d659a9b85bf42dbdb99ecc4`: [backend run 39552046237](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552046237) passed **456 tests, 1 warning**, source guard, SQLite/PostgreSQL 16 migration cycles; [frontend run 39552046207](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552046207) passed TypeScript and Next.js build.
- PostgreSQL concurrency test now races orphan recovery against expired-lease claim and asserts that recovery and lease ownership cannot both win. The UI explicitly labels `WORKER_INTERRUPTED` counters as incomplete.
- Next: audit the crash window between lease release and summary persistence, and inconsistent lease state (token present but expiry missing). Keep recovery metadata-only, preserve separate fill workflows, and keep live submission/accounting promotion disabled.


## Resume checkpoint — Phase 2 lease/crash recovery (2026-10-21)

- Current verified code/test HEAD: `0ce59a7965e3e96a425fa8ae30c841eb0cb755bc`.
- Exact-head [backend CI run 39552821228](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552821228) passed 461 tests, 1 warning, broker-write boundary guard, SQLite migration cycle, and PostgreSQL 16 migration cycle. Frontend TypeScript/build last passed on `d0437be8ef27c4e86d659a9b85bf42dbdb99ecc4`; no frontend files changed after that.
- Both `fail_orphaned_runs` and `LiveReconciliationLeaseRepository.claim` reject a lease with exactly one of token/expiry populated. Claim SQL only reclaims a released (both NULL) or expired lease.
- Regression coverage verifies a crash after lease release but before terminal summary persistence; after the run ages past the cutoff, the next worker marks it `FAILED/WORKER_INTERRUPTED` and proceeds with a new run. This is eventual recovery, not atomic completion.
- Next: decide whether run-summary finish and lease completion should share a transaction, then cover lost-lease and summary-ordering edge cases. Do not enable live submission, automatic accounting promotion, or a scheduler. Keep `BrokerFillIdentity` and `BrokerTradeRecord` separate.


## Latest verified checkpoint — atomic reconciliation lifecycle (2026-10-21)

- Current verified code/test HEAD: `8f967adaa2328f16a0a08a104c3ec394e62f9310`.
- Exact-head [CI run 39553655005](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39553655005) passed 463 tests, 1 warning, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles.
- Run finalization and lease release now execute in one transaction. A summary update failure rolls back lease release; a stale worker cannot release a newer lease and marks its run `LEASE_LOST` instead.
- The previous simulated-crash test now asserts the lease remains claimed when finalization fails, then verifies eventual orphan recovery after expiry. A repository-level rollback test and a stale-owner/new-owner regression test pass.
- Next: audit cancellation, unexpected exception, and lease renewal/expiry paths. Keep fill workflows separate and all live submission/accounting promotion disabled.


## Latest verified checkpoint — lease loss and cancellation recovery (2026-10-21)

- Current verified code/test HEAD: `2ac6bfaafd3475ee63360bd0049b0b6987236bc1`.
- Exact-head [backend CI run 39553981172](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39553981172) passed 465 tests, 1 warning, broker-write guard, and SQLite/PostgreSQL 16 migration cycles.
- Worker now has regression coverage for losing lease ownership before local persistence and for cancellation during broker read followed by expiry-based recovery. A stale owner cannot write fill evidence or release the replacement owner's lease.
- Run-summary terminalization and lease release are atomic; failure rolls back lease release. The crash/cancellation recovery marker remains `WORKER_INTERRUPTED`, whose summary counters are incomplete.
- Next: review lease-renewal cadence for large batches and inspect any remaining cancellation/unexpected-error paths. Keep all live broker writes and automatic accounting promotion disabled.


## Latest verified checkpoint — documentation audit and renewal boundary (2026-10-21)

- Code/test HEAD: `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`; backend [run 39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380): 466 passed, 1 warning, guard and migrations passed; frontend [run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474): TypeScript/build passed. Latest documentation commit `7f9a1f3293ffc67579042a87b82cb2fb03ffba1f` passed [CI run 39556090575](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556090575).
- Lease renewal now occurs every 5 records during trade/order batches. A regression test simulates lease replacement at a renewal boundary and verifies the worker stops before writing the next record, keeps the new lease owner intact, and marks the run `LEASE_LOST`.
- UI warning now covers `LEASE_LOST` as well as `WORKER_INTERRUPTED`, because neither terminal status guarantees a complete summary.
- Phase 2 lease-expiry audit closed: per-write transaction-level fencing is implemented and verified by backend CI run 39561621808 (470 passed, 1 warning). Do not reopen unless new evidence identifies a regression.


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

## Phase 3 checkpoint refresh — aggregate charge rejection tests (2026-10-21)

- Latest GitHub main commit at refresh: 89d274d08f1ee85bdcb0f0118ce753d1d05bba2c (progress docs commit).
- Added negative-source regression cases in backend/tests/test_live_fill_accounting_service.py at commit b8fa3eca4d2f6181a81ac3efd4d714af10cf5a8c: AGGREGATE_CHARGES, TRADE_CHARGES_API, and BROKER_ESTIMATE are rejected by the existing live-fill promotion validation. This is not source authentication and does not solve the possibility of a caller mislabelling aggregate data as BROKER_REPORTED.
- Official Upstox API schema cross-check is recorded in PHASE3_CHARGE_ALLOCATION_CONTRACT.md and PROGRESS.md: trade-wise P&L is not a complete actual per-fill charge source; the trade charges endpoint is aggregate by period/segment. Do not allocate aggregate levies by guessed proportions or match fills using only symbol/date/average price.
- **Exact-HEAD CI is not verified for 89d274d...** GitHub status/run queries returned no matching records through the available connector. This absence is not evidence of success; do not report the added tests as passed until the workflow run for the exact SHA is visible.
- **Next step:** resolve the CI evidence gap and continue source-provenance design. Do not add a speculative importer or schema migration until an authoritative component-specific allocation basis is available.
- Safety unchanged: live broker submission, automatic accounting promotion, and automatic scheduling remain disabled. Phase 2 remains closed. All changes stay in tradepro-improved; original Tradepro remains untouched.

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
- Commit: `66fda569b1e4879d270a970cb5b6d216c2f55f9c`.
- Exact-head GitHub Actions run `39923699033` completed successfully: **570 passed, 1 warning in 30.89s**; broker-write boundary guard passed; SQLite and PostgreSQL 16 migration checks and the synthetic database/document-volume restore drill passed.
- Run: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39923699033
- Scope safeguard: work is in `tarunsharma2610-del/tradepro-improved` only. PR #6 remains draft and unmerged; live broker order writes remain disabled.
- Evidence limitation: the test uses synthetic reviewed-document bytes and synthetic PostgreSQL fixtures. It does not establish authenticity against a real Upstox contract note or a real Oracle-host backup restore.


## Exact-head CI checkpoint — 2026-10-23

- Verified PR #6 head `f75471c5bc64bc9ede61c7dc621d1200e97fa078` with GitHub Actions run [39927004048](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39927004048): Backend pytest job completed successfully; broker-write boundary guard, SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks, synthetic PostgreSQL/document-volume restore drill, and evidence-retention step all passed.
- This result applies to that exact PR head. Any documentation commit creates a new head and must receive its own CI verification before the checkpoint is considered current.
- Synthetic restore evidence is not proof of restoring the user's real Oracle Cloud database/document backup. Actual retained-backup restore and authenticated real broker-source validation remain separate acceptance items.
- The integrated concurrency test that races real `LiveFillAccountingService.promote_trade` with allocation-ledger verification/promotion remains an open Phase 3 acceptance gate; do not treat the accounting review as complete yet.
- PR #6 remains draft and unmerged pending acceptance-gate review and explicit user approval. Live broker order writes remain disabled. All changes remain confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains out of scope.


## Follow-up verification — 23 October 2026 (supersedes stale pending wording)

- Exact current head `3c592de0bb2262ec4753196dfba26d7a31c70986` passed GitHub Actions Backend tests in [run 39927573489](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39927573489). The job passed pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade, synthetic PostgreSQL/document-volume restore, and restore-evidence retention.
- Code inspection confirms `backend/tests/test_broker_charge_allocation_postgres_concurrency.py::test_live_fill_promotion_races_with_component_ledger_verification` exists. It races `LiveFillAccountingService.promote_trade` against `verify_component_allocation_ledger` using synthetic persisted evidence and asserts no errors, one inserted execution, one live position, and reconciled component allocations. The CI job passed this PostgreSQL-enabled integration suite.
- Therefore, earlier checkpoint text describing this exact integrated race test as still absent is superseded. Remaining Phase 3 acceptance is broader review of charge-component allocation policy and evidence provenance, source authenticity limits for public examples, plus separate real Oracle backup/restore validation; synthetic tests do not prove real-account authenticity or actual backup recovery.
- PR #6 remains draft/open/unmerged until all acceptance gates are reviewed and the user explicitly approves. Live broker order writes remain disabled. Scope remains only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains outside scope.


## Component-specific allocation policy review — 23 October 2026

- Added `PHASE3_COMPONENT_ALLOCATION_POLICY.md` documenting the key distinction between deterministic allocation arithmetic and a justified charge-specific attribution basis.
- Public references reviewed: [Upstox brokerage/charges](https://upstox.com/brokerage-charges/), [Upstox brokerage calculator](https://upstox.com/calculator/brokerage-calculator/), [NSE levies/STT](https://www.nseindia.com/static/invest/first-time-investor-sebi-turnover-fees-stt-other-levies), and [NSE stamp duty](https://www.nseindia.com/static/invest/first-time-investor-stamp-duty-charges-taxes). Public tariff pages show effective-date and segment/product differences; rates must not be hardcoded as timeless or inferred from historical sample notes.
- Policy gap: the generic allocator's support for QUANTITY, NOTIONAL and EXPLICIT_REVIEWED is not blanket approval for those bases for every component. Brokerage/order caps, GST tax-base composition, buy-side-only stamp duty, side/product-specific STT and exchange charges, and account/scrip-level fees need component-appropriate rules and tests. The new policy file records the acceptance matrix and tests still required.
- Exact head before this policy-doc addition, `6d922d3436dcf2b3def7b5c77665056be173fab1`, passed Backend tests in [run 39928182307](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39928182307), including pytest, broker-write guard, SQLite/PostgreSQL 16 migration round-trips, and synthetic restore/evidence retention. The new policy documentation commit and subsequent doc-sync commit(s) require their own exact-head CI before being marked verified.
- PR #6 remains draft/open/unmerged pending policy gates, full acceptance review and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` is out of scope.


## Fail-closed allocation gate — CI verified 23 October 2026

- Commit `2e14ce6feed8357a85813ec5924e577879b2e4ca` passed GitHub Actions [run 39929331878](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39929331878). Backend pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore, evidence retention, and cleanup all completed successfully.
- The source-reconciliation verification gate now rejects `QUANTITY` and `NOTIONAL` allocation bases until component-specific effective-dated rules are approved. A regression test verifies unsupported notional allocation raises and rows remain `PENDING_RECONCILIATION`. Explicitly reviewed per-fill weights remain available, subject to existing provenance/reviewer/promotion checks.
- This is a conservative fail-closed safeguard, not completion of component-specific tariff automation. Still required: reviewed tests/rules for brokerage caps and multi-fill orders, GST taxable base, buy-side stamp duty, side/product-specific STT/CTT, exchange/segment charges and effective-date transitions. Ambiguous source scope must remain pending.
- Publicly shared Upstox contract-note examples are for layout/research only and are not independently authenticated. Actual Oracle Cloud backup recovery remains separate from synthetic restore CI.
- PR #6 remains draft and unmerged until acceptance gates are reviewed and the user explicitly approves. Live broker order writes remain disabled. Changes are confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains out of scope.


## Phase 3 charge-calculation checkpoint — 23 October 2026

- Verified code/test commit `b37e6cab7c9cbba0897e5c02161812d121ba2c7e` passed the full Backend pytest workflow: [run 39933579727](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39933579727). Steps passed included pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade, synthetic PostgreSQL/document-volume restore, evidence retention, and cleanup.
- The branch now has arithmetic helpers/regression coverage for brokerage caps, GST on an explicit taxable base, buyer-side stamp duty, STT/CTT on an explicit base, and exchange/SEBI charges on explicit bases. These are arithmetic helpers, not a verified tariff engine: they do not establish official effective-dated rates, applicability by exchange/segment/instrument/product/side, exemptions, or per-fill attribution.
- Latest exchange/SEBI test commit: `b37e6cab7c9cbba0897e5c02161812d121ba2c7e` (CI passed). Documentation checkpoint commit `1c3906551903acc0bb5a4450c7b8a56b3f9a659a` was created afterward; exact-head CI has not yet returned a workflow result.
- Remaining Phase 3 gates: source and version official effective-dated tariffs with provenance; model applicability and taxable/calculation bases; connect rule evaluation to durable per-fill allocations; test rounding, caps, effective-date transitions, replay/idempotency, and reconciliation; verify full CI on the final documentation/code head.
- Automatic `QUANTITY`/`NOTIONAL` allocation remains fail-closed until the relevant component-specific rules are reviewed and accepted. Do not promote ambiguous or unsupported charges.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. All changes are confined to `tarunsharma2610-del/tradepro-improved`; the original `Tradepro` repository is out of scope and must remain untouched.


## Exact-head documentation CI result — 23 October 2026

- Exact checkpoint commit `d0de363bd0b034582754b41de17ae991f6c043aa` passed GitHub Actions [run 39934671391](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39934671391). This verifies the nine-document checkpoint head at the time of the run.
- Resume from the `phase3/durable-per-fill-charge-allocation` branch in `tarunsharma2610-del/tradepro-improved`. Next work: obtain/record official Upstox and statutory charge-rule sources with effective dates and provenance; model applicability by exchange/segment/instrument/product/side; then implement and test tariff-driven durable per-fill allocation and reconciliation.
- Arithmetic helpers are groundwork only, not a verified tariff engine. Keep unknown/ambiguous allocation fail-closed. PR #6 stays draft and unmerged until acceptance gates and explicit user approval. Live broker order writes remain disabled. Original `Tradepro` is outside scope and must remain untouched.


## Exact-head CI confirmation for saved checkpoint — 23 October 2026

- The nine-document checkpoint head `c2959ffed34f6dd1c299bdb36091b987df06c11a` passed full GitHub Actions run [39935827529](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39935827529). Verified steps: backend pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade, isolated synthetic PostgreSQL/document-volume restore, evidence retention and cleanup.
- Resume work on `phase3/durable-per-fill-charge-allocation`. Next engineering task: verify and record current official Upstox, exchange and statutory charge rules with URLs, effective dates, applicability and provenance. Then implement tariff-driven component calculation and durable per-fill allocation, with regression tests for effective-date transitions, rounding, order caps, replay and reconciliation.
- Existing helpers for brokerage cap, GST, stamp duty, STT/CTT, exchange and SEBI charges are arithmetic groundwork only. They do not constitute a verified tariff engine. Keep unsupported/ambiguous scopes fail-closed.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Work only in `tarunsharma2610-del/tradepro-improved`; the original `Tradepro` repository remains outside scope.


## Upstox charge-rule source register — 23 October 2026

- Added `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md` at commit `de97bd3bfe90e82b888181cf109ed6a1b8e41d41`. It records the official Upstox brokerage pricing page, Brokerage Details API, Get Trades Charges API, and official contract-note guidance, with their limits and implementation requirements.
- Key source URLs: https://upstox.com/brokerage-charges/ ; https://upstox.com/developer/api-documentation/get-brokerage/ ; https://upstox.com/developer/api-documentation/get-trade-charges/ ; https://upstox.com/help-center/how-can-i-access-and-download-the-contract-note-248457/ ; https://upstox.com/help-center/understanding-the-contract-note-248458/
- Research indicates the pricing page contains historical and current rate sections, including STT/CTT changes effective 1 April 2026 and NSE transaction-charge changes effective 1 March 2026. Therefore, do not hardcode a single timeless rate or use a rate from the wrong effective period. BSE scrip-group variation, commodity/currency segments, option premium/futures turnover, DP charges, GST base composition and per-crore unit normalization require explicit rules.
- The authenticated brokerage API can calculate supported orders from instrument, quantity, product, side and price; the trades-charges API provides a segment/financial-year breakdown. Treat the latter as aggregate reconciliation only, not per-fill evidence.
- Next: implement a versioned tariff-rule model with effective dates, explicit normalized units/bases, source provenance and review status; add applicability/rounding/effective-date regression tests before wiring rules into durable per-fill allocation. Unknown or ambiguous cases remain fail-closed.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Effective-dated tariff registry groundwork — 23 October 2026

- Added `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md` (commit `de97bd3bfe90e82b888181cf109ed6a1b8e41d41`) documenting official Upstox pricing/API/contract-note sources, rate effective-date cautions, API limitations and the required provenance fields.
- Added `backend/app/services/broker_tariff_rules.py` (commit `0ec5590579c67c2575c8c4c72cf75bc56605120b`), a fail-closed rule selector requiring exact broker/exchange/segment/product/side/component/basis match, an effective date, source URL and SHA-256-shaped provenance, and APPROVED status. It rejects missing and overlapping rules and intentionally ships without active rates.
- Added `backend/tests/test_broker_tariff_rules.py` (commit `74240f2cc0af05befeee1fa97f988f2372a73be6`) covering exact-scope selection, review-state gating, scope mismatch, effective-date boundaries, overlap and invalid provenance/rates. CI has not yet returned a result for this latest test commit; do not mark it verified until the full workflow passes.
- This is rule-selection groundwork, not a complete tariff calculator and not proof that any specific rate is legally applicable. The next step is CI verification, then source-reviewed rules for specific segments/components and integration with durable per-fill allocation/reconciliation.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Tariff amount calculation and CI checkpoint — 23 October 2026

- Both the tariff registry regression-test commit `74240f2cc0af05befeee1fa97f988f2372a73be6` and its nine-document checkpoint `14fa83fe144228bb81a3b935b48b73c7f454afe2` passed their full Backend tests workflows: [code run 39953794565](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39953794565) and [documentation run 39953906848](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39953906848).
- Added `calculate_tariff_amount` to `backend/app/services/broker_tariff_rules.py`, with distinct `PERCENT`, `INR_PER_CRORE`, and `INR_FIXED` units and paise rounding. Added tests for units, rounding and invalid bases. Latest test commit is `782d2d2c63905adfa6862f43abcdc057c47894a7`; its CI is pending and must be verified before treating the new calculation as green.
- No live tariff rates are activated. The new calculator requires a previously selected approved rule; rule selection still fails closed for missing or overlapping rules. This does not yet integrate the registry with durable per-fill allocation or prove component-specific legal applicability.
- Next: verify CI on the latest code commit, then build reviewed, source-backed test fixtures for exact tariff applicability and connect approved component calculations to durable allocation/reconciliation without enabling ambiguous QUANTITY/NOTIONAL allocation.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Tariff calculation safety refinement — 23 October 2026

- Confirmed prior tariff-calculator code CI passed: [run 39954309954](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39954309954). The prior nine-document checkpoint CI also passed: [run 39954408580](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39954408580).
- Tightened `calculate_tariff_amount` so it refuses non-`TariffRule` values and any rule whose review status is not `APPROVED`. Added regression tests for DRAFT, REVIEWED and REJECTED rules.
- Latest safety-fix test commit: `83a70bdc88dfbc2cfabe8e80b8adfc858b516a6e`. Its full CI is pending; no green status should be inferred yet.
- Active rates remain intentionally absent pending rule-by-rule source verification and approval. Next: verify CI, then implement only specifically sourced rules with explicit applicability, normalized unit, basis, effective date and provenance before connecting to durable per-fill allocation.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Scoped tariff-calculation entry point — 23 October 2026

- Confirmed prior safety-fix code CI passed: [run 39954730200](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39954730200). The previous nine-document checkpoint also passed: [run 39954836920](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39954836920).
- Added `calculate_charge_for_trade` to `backend/app/services/broker_tariff_rules.py` (commit `d2d9c0c99a0cf31bca96fbde39c615b2569b1a97`) to select exactly one approved rule for the full trade scope/date and then calculate using its declared unit. Added tests for calculation result and fail-closed behavior without an approved match (commit `98c514d59d1b1da986a1d00117c2653c1e82d4c6`).
- Latest code CI is pending; do not mark this addition green until full Backend pytest, broker-write boundary, migrations and restore workflow pass.
- This entry point does not persist charge rows or allocate across fills. No production tariff rates are enabled. Next: verify CI, then design a persistence/integration boundary that records the selected rule version and calculation basis alongside the durable source component and per-fill allocation ledger.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Tariff CI verification and estimate/allocation boundary — 23 October 2026

- Verified full Backend CI passed for tariff calculation commit `98c514d59d1b1da986a1d00117c2653c1e82d4c6`: [run 39955151533](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39955151533). Verified the nine-document checkpoint CI passed for `2a5c3cf5075c2ab217603868f6272cc366784b26`: [run 39955284700](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39955284700). Both include pytest, broker-write boundary, SQLite and PostgreSQL migration downgrade/re-upgrade, and isolated synthetic restore steps.
- Added `docs/PHASE3_TARIFF_TO_FILL_ALLOCATION_DESIGN.md` (commit `a49b37509db1658ce7026f8328a35e26422afaad`) to define the boundary between a tariff estimate, actual broker-evidenced source charge and reviewed per-fill allocation; it sets out idempotency, immutable rule snapshots, component-specific acceptance gates and safety constraints.
- Next: CI-check this design/documentation checkpoint, then implement persistence for estimates as a separate, immutable, idempotent record before wiring estimates into source-charge reconciliation. Estimates must never be represented as contract-note actuals or automatically promoted into accounting.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Immutable tariff-estimate snapshot groundwork — 23 October 2026

- Added `backend/app/services/tariff_estimate_snapshot.py` (commit `00ec9fcd449fb9c9c091b29ebc7c68377246242b`) with canonical JSON snapshots, rule/source provenance, SHA-256 fingerprints, explicit calculation base/rounding metadata, stable idempotency keys and exact-replay/conflict comparison.
- Added `backend/tests/test_tariff_estimate_snapshot.py` (commit `f89517a3ca0bc034dc84da6d2239f0fd18026990`) for deterministic serialization, exact replay, conflicting base replay, changed rule, unapproved rules, invalid base, missing identity and effective-date rejection.
- This is a deterministic snapshot and replay-comparison layer only; it does NOT yet persist estimates. Durable enforcement still requires a database table with a unique idempotency constraint, transactional insert/read comparison and a migration tested on SQLite/PostgreSQL. No estimate can become a broker actual or source component.
- Latest code CI must be verified before this work is considered green. Next: confirm test and migration conventions, add durable persistence plus migration, concurrency-safe idempotency, and tests proving rollback/replay behaviour.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Snapshot CI verification and idempotency correction — 23 October 2026

- Verified CI passed for the immutable snapshot implementation `f89517a3ca0bc034dc84da6d2239f0fd18026990`: [code run 39956149855](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39956149855). Verified the associated nine-document checkpoint passed: [run 39956272786](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39956272786). Both runs completed pytest, broker-write boundary, SQLite and PostgreSQL migration downgrade/re-upgrade, and synthetic restore checks successfully.
- Code review identified an idempotency-key flaw: including the tariff rule fingerprint in the key would allow the same trade/component event with a changed rule to receive a new key instead of conflicting. Corrected `tariff_estimate_snapshot.py` so event key is stable across rate/rule changes, and changed the regression test to require a same-event rule change to fail as a conflicting replay.
- Latest correction commits: `204574082c7953ac08262a9f51801f04fd09ead7` and test `fafa26b6fb686471ac38a041256659b273f97712`. CI for this correction is pending.
- The snapshot remains in-memory/canonical only. Durable database persistence is not implemented yet; adding a table/migration requires identifying the current Alembic head and testing a unique idempotency constraint with transactional exact-replay/conflict behavior.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Durable estimate-only tariff persistence — 23 October 2026

- Verified the previous idempotency-correction code CI passed: [run 39956721476](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39956721476). Verified the previous nine-document checkpoint CI passed: [run 39956881266](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39956881266).
- Added `TariffEstimateSnapshotRecord` model and model registration (commits `08fec41026dabf250bd8756e0a711c20bbbf1e2a`, `0f47e07abd8bad51e4a7e11a851c726dd9008882`), Alembic revision `202610240015` after `202610240014` (commit `d98f5e259c610f8a5d392461ea1b75f6b9471912`), and `persist_tariff_estimate_snapshot` (commit `bc8b7bb2666e73cf30aa3fa4a796ebfe4e4874e5`).
- Added persistence regression tests for create/exact replay, changed-base conflict, changed-rule conflict, and estimate-only status (commit `cc121e7c710038ee25a434634a86ec4296cd0d68`). The unique database idempotency key is the concurrency arbiter; the service uses a nested transaction and leaves the outer commit to its caller.
- Latest implementation CI is pending; do not consider durable persistence verified until full pytest, broker-write boundary, SQLite/PostgreSQL migration downgrade/re-upgrade and synthetic restore checks pass.
- The database record stores only estimate snapshot JSON and a digest and has a database constraint that fixes status at `ESTIMATE_ONLY`; it does not create or modify contract-note actual charge/source-component rows.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Persistence CI result and append-only enforcement — 23 October 2026

- Full CI passed for durable estimate persistence implementation commit `cc121e7c710038ee25a434634a86ec4296cd0d68`: [run 39957564616](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39957564616). Backend pytest, broker-write boundary, SQLite and PostgreSQL migration downgrade/re-upgrade, and synthetic restore steps all succeeded.
- Review then identified that the database row had no ORM-level guard against updates to the snapshot payload. Added an append-only SQLAlchemy `before_update` guard to `TariffEstimateSnapshotRecord` (commit `596d4396bfaa58da3f4bf8ad11978370cfc8edf2`) and a regression test proving payload mutation is rejected (commit `af07ad77c3c7621774f49771c5d9cb4665778c03`).
- The append-only guard is an ORM protection, not a database trigger; direct SQL updates outside the ORM are not blocked by this guard. Consider a portable DB-level immutability trigger only if required by the release threat model. The unique key and ESTIMATE_ONLY check remain database-enforced.
- Latest append-only change CI and this documentation checkpoint's CI are pending. Do not treat them as verified until all jobs complete successfully.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Handover checkpoint — 2026-10-23

Current target is only `tarunsharma2610-del/tradepro-improved`, branch `phase3/durable-per-fill-charge-allocation`. PR #6 remains draft and unmerged; do not enable broker order writes.

Latest head `bf9b3bc74cfa4047bc084bf6136e12c0a93a65c0` adds direct-SQL snapshot immutability tests. Migration `202610240016` installs PostgreSQL and SQLite triggers rejecting UPDATE/DELETE for `tariff_estimate_snapshot_records`. Exact-head CI run [39959332425](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39959332425) passed pytest, broker-write guard, SQLite and PostgreSQL migration round-trips, and synthetic restore drill.

Next: (1) add PostgreSQL concurrent estimate-persistence tests and confirm DB-trigger behavior on both dialects; (2) extend tariff model for order-scoped caps/conditional rules before using such rules; (3) compare approved-rule estimates against reviewed actual source components as variance-only records; (4) never promote an estimate into the per-fill actual ledger; (5) verify final docs and CI before requesting merge approval. Real broker-note authenticity and retained Oracle backup restore remain separate operational checks.


## Handover update — 2026-10-23

Task B progress is verified on `tarunsharma2610-del/tradepro-improved`, branch `phase3/durable-per-fill-charge-allocation`. Commit `fd0e42917611f3b6c3f826cb2e99971fd3e2cce6` adds the PostgreSQL concurrent estimate persistence test and fixes its fixture imports. CI run [39960409771](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39960409771) passed: 677 tests, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic restore drill.

Migration `202610240016` enforces append-only tariff snapshots via PostgreSQL/SQLite triggers; direct SQL UPDATE/DELETE regression tests were added. Remaining Task B: integrate variance-only estimate-versus-actual comparison with reviewed contract-note source components, and model/test conditional order-level caps, minimums, GST taxable bases and other special tariff bases before approving those rule types. Do not promote estimates into the per-fill actual ledger. PR #6 remains draft/unmerged; live broker order writes disabled; original `Tradepro` untouched.


## Handover update — variance-only comparison (2026-10-23)

Implemented a separate append-only variance record and service. Snapshot schema v2 can retain an exact broker fill UUID. The service requires that identity and an actual source component whose reviewed manifest contains exactly that one fill, plus reviewed/hash-verified contract-note evidence, matching component/currency/reviewer, and the matching broker connection. It calculates signed actual-minus-estimate variance and percentage, but never changes allocation rows or promotes an estimate.

Migration `202610240017` creates the variance table and database-level append-only triggers. Tests cover exact replay, missing identity fail-closed, SQL UPDATE/DELETE rejection, and unchanged allocation statuses. CI run [39961777103](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39961777103) passed 680 tests and all broker-write, migration and synthetic restore checks.

Limit: only one-fill source components are comparable today. Aggregate order-level contract-note components require a separately designed aggregate estimate/linkage model. Tariff caps/minimums and special component bases remain unsupported. PR #6 draft/unmerged; live broker order writes disabled; original `Tradepro` untouched.


## Verified exact PR-head CI 39962196672 — 2026-10-23
Verified PR #6 head `c47bc3e3eeb4c8da4415132735d2d4ef457551f7`: [CI completed successfully](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39962196672), 680 passed and 1 warning; broker-write guard passed and no steps failed. Continue with aggregate variance design, advanced tariff-rule support/fail-closed validation, and final accounting integration review. PR remains draft/unmerged; live writes disabled; only Tradepro Improved is in scope.


## Aggregate variance design proposal — 2026-10-23
Recorded a non-implemented proposal in `docs/PHASE3_TARIFF_TO_FILL_ALLOCATION_DESIGN.md`: explicit single-fill/order-fill-set scopes; canonical exact member-fill digest; order-scope computation for caps/nonlinear tariffs; exact replay/conflict/concurrency protections; immutable variance-only records; no accounting side effects. This is not yet implemented or approved. Next inspect actual tariff snapshot/service/schema and migration conventions before coding; retain draft PR and disabled live writes.


## Variance validation hardening — 2026-10-23
The variance service now checks the canonical eligible-fill manifest digest against `eligible_fill_set_sha256` and validates the identified broker fill's side and trade date against the estimate. Regression tests cover digest tampering and scope mismatch. Latest code head: `6ca045e2bbdd71d37dd77baf50df3881db2b1e71`; exact-head CI has not yet been verified. Aggregate variance is still design-only. Tariff calculator supports only percent, INR-per-crore and fixed units; no production rates or advanced cap/minimum/conditional/GST-base models are enabled.


## Exact-head CI verified — 2026-10-23
[CI run 39968000009](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39968000009) passed for code head `f5092df1d27a28006dccba929fdc41e9a1d63f1e`: 683 tests passed, 1 warning; broker-write guard passed; SQLite migration checks and isolated PostgreSQL 16 synthetic restore drill completed. The warning is a Starlette TestClient/AnyIO deprecation; Node action deprecation notices also appeared. This run precedes the documentation-only updates. Continue aggregate variance and tariff-rule coverage, then verify CI on the new docs head. PR remains draft/unmerged; live writes disabled.


## Aggregate variance implementation checkpoint — 2026-10-23
Implemented explicit `TRADE_FILL` / `ORDER_FILL_SET` variance scope in persistence, migration `202610240018`, and comparison validation. Aggregate comparisons require exact canonical fill membership and all fills to belong to the same broker order, connection, side, and trade date. The current snapshot builder is schema v4, including cap-aware fields; older v3 references in this checkpoint are stale. Tests cover successful aggregate comparison, exact replay, and mismatched estimate manifest, in addition to snapshot canonicalization/duplicate/empty-set cases. Backend CI run [39979772325](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39979772325) passed on code/test commit `e54e405b74feee90e4658a6992fa208a3e2da5d3`, including the broker-write boundary guard, SQLite and PostgreSQL 16 migration round-trips, and synthetic restore drill. Documentation commits made after that tested commit still need exact-head CI. Keep PR draft and live writes disabled.


## Latest tariff-safety correction checkpoint — 2026-10-23
Two tariff-safety CI runs failed after the first guard/test patch. Commit `68dc2b6fa0a729cc77180725e581de61a88e9de1` corrected the GST explicit-component error wording, enforces the GST rule's APPROVED status in the dedicated composition function, and rejects stamp-duty SELL requests before selection. CI run [39982723294](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39982723294) passed all jobs: backend pytest, broker-write boundary guard, SQLite and PostgreSQL 16 migration round-trips, synthetic restore drill. Documentation sync follows and needs exact-head CI. Do not merge PR #6 or enable live order writes; continue advanced tariff-rule review before accounting acceptance.


## Tariff safety + Upstox charge-source research — 2026-10-23

Code commit `ce0b4bc17eaf1656334e10ca8d6e32a68f50593b` adds a fail-closed stamp-duty unit guard: the specialized stamp-duty calculator accepts only percentage-based approved rules; regression tests reject `INR_FIXED` and `INR_PER_CRORE`. Exact-head CI [39987357989](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39987357989) passed backend tests, broker-write boundary guard, SQLite and PostgreSQL 16 migration round-trips, and synthetic restore drill.

Official Upstox sources reviewed:
- Brokerage calculator API: https://upstox.com/developer/api-documentation/get-brokerage/ — order-scoped estimate with brokerage, taxes, transaction/clearing/IPFT/SEBI charges and DP-plan metadata; `dp_plan.min_expense` is a daily per-scrip sell minimum outside the brokerage calculation.
- Trade charges API: https://upstox.com/developer/api-documentation/get-trade-charges/ — segment/date-range charge breakdown, including brokerage, GST, STT, stamp duty, transaction, clearing, IPFT, SEBI turnover and demat transaction charges.
- Historical trades API: https://upstox.com/developer/api-documentation/get-historical-trades/ — trade ID, exchange, segment, quantity, amount, side and trade date.
- Public tariff page: https://upstox.com/brokerage-charges/ — includes historical and newer effective-date rows; never activate rates from a flattened scrape without preserving effective periods and source snapshot.

API charge breakdowns are reconciliation/reference inputs, not automatically contract-note evidence and not a substitute for reviewed actual source components. Do not store tokens. DP per-scrip/day minimums, STT/CTT tax-event cases, and other conditional models remain unsupported until represented and tested explicitly. No active production tariff registry is enabled. PR #6 stays draft/unmerged; live broker writes remain disabled; original `Tradepro` remains out of scope.


## Generic conditional-charge guard — 2026-10-23
The next audit found that the generic rate calculator could apply plain rate×base arithmetic to STT/CTT and DP/demat components, despite these requiring event- or day/scrip-specific semantics. Commit `ee09183e5b8eeff0311431faa90b807d9b561ce7` adds an explicit fail-closed block for STT, CTT, DP, DP charges and demat/depository transaction charges in the generic calculator, with parameterized regression tests. Exact-head CI run [39988242077](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39988242077) passed. The synchronized documentation commit `b1207def7d828c960e6fffe9c6af8b9ed0177c07` also passed exact-head CI run [39988578238](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39988578238).

Audit note: the implementation constant is `tariff-estimate-snapshot-v4`; older design text saying snapshot v3 is stale and is corrected in the accompanying design-document update. Remaining gated models include STT/CTT event-specific rules, DP daily per-scrip minimums, conditional lesser-of pricing, and reviewed source-backed effective-date rates. No live tariff registry or live broker order writes are enabled.

## Resume checkpoint — 2026-10-24
Latest test commit: `16dc6b9964db1af85deeffffb3814a0ff526b951` on `phase3/durable-per-fill-charge-allocation`. Regression tests cover tampered actual manifest digest, fills from different orders, fill-side mismatch, and trade-date mismatch; rejected comparisons assert zero variance rows. CI is pending for the latest head. Next: verify exact-head CI, fix any failures, then verify all nine checkpoint documents. PR #6 remains draft/unmerged; live broker order writes remain disabled; work only in `tarunsharma2610-del/tradepro-improved`.

CI verification note — 2026-10-24: the nine-document synchronization is committed as `2a9c9a40f6b62144fa2d13fbdc674dfd5c4de5dd`. The test-only head `16dc6b9964db1af85deeffffb3814a0ff526b951` passed run [40062815547](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40062815547); exact-head verification after the documentation synchronization remains pending.

## Resume checkpoint — 2026-10-24 (CI verified)
Current head `bc8e5c1aa862589c660fd361d87f7df45d8ceb10` passed backend CI in run `40062975428`. Aggregate variance negative tests cover actual manifest digest, mixed orders, side and trade-date mismatches, with no-write assertions. Next gate: review/add concurrency and source revalidation/no-accounting-side-effect coverage before moving to durable per-fill charge allocation follow-up. PR #6 stays draft/unmerged; live broker order writes disabled; only `tarunsharma2610-del/tradepro-improved` is in scope.

## Resume checkpoint — 2026-10-24
New tests added on the Phase 3 branch: `test_variance_comparison_does_not_change_reviewed_source_or_charge_allocations` and `test_variance_comparison_revalidates_review_state_before_writing` (parameterized for evidence and component state). They cover no allocation/source mutation and fail-closed review-state revalidation. CI for current test head is pending. Next: verify latest-head CI, then reconcile concurrency/replay acceptance. PR #6 remains draft/unmerged; live broker writes disabled; work only in `tarunsharma2610-del/tradepro-improved`.

## Upstox audit instruction for future work — 2026-10-24
Read `UPSTOX_API_INTEGRATION_POLICY.md` before any Upstox-related task. Audit relevant current official APIs, SDK endpoint-version coverage, official Agent Skills and read-only MCP, sandbox, rate limits and regulatory/static-IP requirements. Explicitly evaluate `/v2/charges/brokerage`, `/v2/trade/profit-loss/charges`, and `/v2/charges/historical-trades`; keep estimates, broker historical aggregates and reviewed contract-note/per-fill evidence separate. Do not connect account-scoped MCP without explicit authorization or let agent skills place live orders. PR #6 remains draft/unmerged; live writes disabled.

## Resume checkpoint — 2026-10-24 (aggregate variance gate CI passed)
Code/test commit `dbff090610028cfb9f5a87585d9c8e697449cd23` passed exact-head CI run `40064129721` (738 passed, 1 warning). Added PostgreSQL concurrency test `test_concurrent_variance_comparison_exact_replay_is_audit_only`: simultaneous identical comparisons return one `CREATED` and one `EXACT_REPLAY`, persist exactly one immutable `VARIANCE_ONLY` row, and create no charge allocations. Existing tests cover review-state rejection and no mutation of reviewed evidence/components/allocation rows. Next: implement/verify effective-dated component-specific tariff applicability and connect only approved calculations to the durable per-fill ledger; test brokerage caps/multi-fill, GST base composition, buy-side stamp duty, segment/product/side/date transitions and replay/rounding. Do not infer missing tariffs. PR #6 remains draft/unmerged; live writes disabled; only `tradepro-improved` is in scope.

## Resume checkpoint — 2026-10-24 (Upstox charge API client CI passed)
Head `5026e95e56ae52c40b238bc29c194ceae26c7898` passed exact-head CI run `40064514873` (744 passed, 1 warning). The existing `UpstoxReadOnlyReconciliationClient` now has tested fixed GET methods for the Brokerage Details API, aggregate Trade Charges API, and paginated Historical Trades API. Tests use a mocked HTTP client; no real Upstox account or token was used. Next: build the estimate-only normalization/persistence boundary that stores request scope, API version, retrieval time and response digest, then wire it to the existing variance-only comparison workflow. Do not treat calculator results or historical aggregate charges as actual per-fill evidence. SDK decision: official SDK supports these endpoints, but the narrow existing REST façade is retained for these read-only calls because it enforces fixed GET-only methods and sanitized error categories; reassess for broader API needs. Live broker writes disabled; PR #6 draft/unmerged; only `tradepro-improved` in scope.

## Resume checkpoint — 2026-10-24 (Upstox estimate snapshot CI passed)
Current code commit `2c23ebfeb9d0d843620dc6dcf54b7279bb112662` passed exact-head CI run `40065219626` (**754 passed, 1 warning**). Brokerage API output is normalized into component-level estimate-only snapshots retaining request/response provenance, API version/endpoint, retrieval timestamp, response JSON/digest, total and DP-plan minimum metadata. The existing immutable persistence/idempotency layer is reused; no new ledger or migration was introduced. API-estimate variance comparison verifies response digest and requires request quantity, price, side and instrument to match the exact reviewed fill set. PR #6 remains draft/unmerged, live broker writes disabled, and only `tradepro-improved` is in scope.

## Checkpoint — flat brokerage rule shape supported (2026-10-24)
Commit `30db9920f640203c1045f1cb045d955bb41b5f86` passed exact-head CI run `40065607232` (**756 passed, 1 warning**). Order brokerage now supports `ORDER_FIXED`/`INR_FIXED` flat fees and existing `ORDER_NOTIONAL`/`PERCENT` rules with minimum/maximum caps; estimate snapshots use the matching guarded calculation. This is calculation-shape support only; no public tariff rate was activated. Next: archive official Upstox/NSE source excerpts with a reproducible digest, add DRAFT effective-dated candidate rules, and test scope/effective-date transitions while keeping automatic allocation fail-closed. PR #6 remains draft/unmerged; live broker writes disabled; only `tradepro-improved` in scope.

## Resume checkpoint — Upstox DRAFT tariff candidates (2026-10-24)
Head `f76ecde4ac785123de2980539138ce89ff660294` passed exact-head CI run `40065979244` (**760 passed, 1 warning**). Added normalized official-source excerpt `docs/source_snapshots/UPSTOX_CHARGES_2026-10-24.md` with canonical payload SHA-256 `c59f7e940fde6b0d94ca1189766f16e5601c117d4a8c2bcd2415da0ecd6db420`, plus 18 effective-dated STT/exchange-charge candidates. All remain `DRAFT` and are rejected by the selector. No rates activated. Source excerpt is not byte-for-byte HTML; archive original source bytes where possible. Current stamp-duty reference is dated 2023, and transaction/IPFT combination still needs resolution. Next: finish source verification and add tests before approving any rule. PR #6 remains draft/unmerged, live broker writes disabled, only `tradepro-improved` in scope.


## Fixed-order brokerage entrypoint regression — 24 October 2026

- Audit found that `calculate_charge_for_trade` routed percentage-based `ORDER_NOTIONAL` brokerage through `calculate_order_brokerage`, but flat-fee `ORDER_FIXED` brokerage fell through to the generic calculator, which intentionally rejects that basis.
- Fixed the shared entry point to route both `ORDER_NOTIONAL` and `ORDER_FIXED` brokerage through the guarded order-level calculator. Added regression test `test_trade_charge_entrypoint_supports_flat_fixed_order_brokerage` asserting a flat INR 20 fee is returned through the full scope-selection entry point.
- Implementation commit: `1634989d29734f1d5ffdcfee826384a512eaafe7`; regression-test commit: `928c0207ff8de5f4852225ab6b9e0fabe97f6e12`.
- Exact-head backend CI run 40066706304 was in progress at documentation time; do not mark this fix green until that run completes. Recheck CI after these documentation updates because they change the branch head.
- No tariff candidate was activated, no charge was promoted to the actual ledger, and no live broker order was sent. Original `tarunsharma2610-del/Tradepro` remains out of scope.


## Brokerage basis/unit validation hardening — 24 October 2026

- Latest verified prior head: Backend pytest workflow run [40066838844](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40066838844) passed for the flat fixed-order brokerage entry-point regression.
- Additional fail-closed hardening now rejects inconsistent brokerage rule shapes at construction: `ORDER_FIXED` requires `INR_FIXED`, and `ORDER_NOTIONAL` requires `PERCENT`. This prevents invalid basis/unit combinations from surviving registry validation and failing only during calculation.
- Implementation commit: `4faa6a062264b2396cb00e380c5cbbe16449ec91`; regression-test commit: `26ea299b78be463651768b2ab93fa6443d5350c5`.
- CI for these new commits is pending and must be checked on the exact latest branch head before this change is considered verified. Do not reuse the earlier green run as evidence for these commits.
- No official tariff rate was activated, no estimate was promoted to actual per-fill accounting, and no live broker order was sent. PR #6 remains draft/unmerged; work stays in `tarunsharma2610-del/tradepro-improved`, not the original `Tradepro` repository.


## Brokerage rule validation CI correction — 24 October 2026

- Backend CI run [40067041722](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40067041722) failed with 2 tests failing and 762 passing. The failure exposed that generic rate-unit arithmetic tests used a default `brokerage/ORDER_NOTIONAL` rule while intentionally testing `INR_PER_CRORE` and `INR_FIXED`; the new brokerage shape guard correctly rejected those inconsistent test fixtures.
- Corrected the generic unit test matrix to use semantically appropriate component/basis pairs: `brokerage/ORDER_NOTIONAL/PERCENT`, `sebi_turnover/TURNOVER/INR_PER_CRORE`, and `other_fee/ORDER_FIXED/INR_FIXED`. This preserves the guard rather than weakening production validation.
- Test-fix commit: `6ba333fe0339838042ffd25a141c4805318418bc`. A new CI result for this exact commit has not yet been observed; do not mark it green until confirmed.
- No tariff rules were activated and no charge allocations or live broker orders were created. PR #6 remains draft/unmerged; original `tarunsharma2610-del/Tradepro` remains out of scope.


## Generic tariff test basis correction — 24 October 2026

- Backend CI run [40067217326](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40067217326) completed with 763 passed and 1 failed. The remaining failure was the generic unit-arithmetic test using `ORDER_FIXED`, which is intentionally excluded from generic calculation bases and must use the specialized brokerage entry point.
- Corrected the test fixture to use supported generic basis `NOTIONAL` for the generic `INR_FIXED` arithmetic case. The production guard is unchanged. Test correction commit: `7c7dadff65885918fc0e01d0aa8deaf1b6d1bb16`.
- CI for this correction and subsequent documentation updates must be checked on the exact latest PR head. No green result is claimed until verified.
- No tariffs were activated; no actual charges were promoted or per-fill ledger writes made; no live broker orders were sent. PR #6 remains draft and unmerged. Work is limited to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains untouched.


## Official tariff-source recheck — 24 October 2026

- Rechecked the official Upstox charges page on 2026-10-24 and recorded the findings in `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`. It lists 1 April 2026 STT/CTT changes and 1 March 2026 NSE transaction-charge changes, and states IPFT is combined with transaction charges while separately listing ₹0.01/crore (options on premium) plus GST. Current candidate rows represent transaction charges only; IPFT composition/effective-date treatment must be resolved before approval.
- The same page's ₹10/order API-order brokerage note is explicitly valid only through 31 December 2025 (excluding GTT); do not treat it as current pricing. Current authenticated API-order-specific terms remain unverified.
- NSE's official stamp-duty page is still marked updated 03/10/2023, so it is not a fresh 2026 publication. Independent current statutory corroboration remains a release gate.
- No tariff candidate was approved or activated, no estimate was promoted to actual per-fill accounting, and no live broker order was sent. Source excerpt remains normalized rather than byte-for-byte HTML. Exact-head CI must be checked after these documentation changes; prior green CI does not cover the new head.


## Brokerage tariff effective-date gate — 24 October 2026

- Reconfirmed the official Upstox public page lists current brokerage examples: equity delivery/options ₹20 per executed order; equity intraday ₹20 or 0.1% (whichever lower); equity futures ₹20 or 0.05% (whichever lower). The current source excerpt does not establish a precise effective_from date for these brokerage terms.
- A trial draft-registry addition was reverted because populating the required `effective_from` with the retrieval date would falsely imply a published effective date. No brokerage candidates with guessed effective dates remain in the tariff registry. Before registering these rows, obtain a source that establishes the effective date or explicitly model an evidence-backed “current as observed” rule state without pretending the retrieval date is the tariff effective date.
- Existing calculation helpers can model flat per-order brokerage and capped percentage brokerage (`maximum_inr`), but helper capability is not source approval. The published “whichever lower” semantics must have a regression test before a reviewed rule is eligible for use.
- The preceding verified Backend pytest run was [40067742361](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40067742361), successful on the then-current head. Later registry/documentation commits need exact-head CI confirmation; do not reuse that run as proof for later commits.
- No rates were activated, no estimates were promoted into actual accounting, and no live broker order was sent. PR #6 remains draft/unmerged and the original `Tradepro` repository remains out of scope.


## Order-brokerage cap regression coverage — 24 October 2026

- Added regression coverage for percentage brokerage below/at the maximum cap, minimum-floor behavior, simultaneous minimum/maximum bounds, and flat `ORDER_FIXED/INR_FIXED` brokerage. Tests call the specialized order-level calculation helper and assert paise-precise outputs; flat order fees reject percentage caps.
- Test commit: `48447dafb11d7d83a09f4f64a55020405fa167a4`. This is not yet CI-verified; run and inspect CI for the exact latest PR head before treating the tests as passing.
- This covers arithmetic only. It does not approve any live tariff row, define the allocation of one order's brokerage across multiple fills, or establish that public examples match a particular authenticated account plan. Per-fill allocation and actual-charge promotion remain blocked pending policy/evidence and durable accounting acceptance tests.
- PR #6 remains draft/unmerged; no live broker orders were sent; original `Tradepro` remains out of scope.

## CI follow-up — fixed-fee cap regression test — 24 October 2026

- Latest documentation head before this correction, `5b155c4b3f75606b426262f938b420f7a2217d74`, failed backend pytest: **768 passed, 1 failed**. Failure was isolated to `test_fixed_order_brokerage_is_flat_and_rejects_caps`: the test expected calculation-time rejection, but `TariffRule` correctly rejects an invalid fixed-fee rule at construction time.
- Corrected the regression test to assert the rule-construction `ValueError` using the actual validation message. Test-only commit: [47aa91e2696bb6388af73ede568dfe89c4cbead7](https://github.com/tarunsharma2610-del/tradepro-improved/commit/47aa91e2696bb6388af73ede568dfe89c4cbead7).
- CI for this correction and the resulting documentation head is **pending verification**; do not describe the latest head as green until the exact SHA has a successful run. This is a test correction, not a production guard relaxation.
- PR #6 remains draft/unmerged. Live broker order submission remains disabled. All work is confined to `tarunsharma2610-del/tradepro-improved`; do not modify original `tarunsharma2610-del/Tradepro`.

## Exact-head CI passed — 24 October 2026

- Verified successful GitHub Actions backend workflow [40081403001](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40081403001) against exact head `ff9675f5489f4148079b3ee7cd4a97810e352b4b`: **769 passed, 1 warning in 44.10s**. Broker-write boundary guard passed; SQLite and PostgreSQL 16 migration round-trips passed; synthetic PostgreSQL/document-volume restore drill passed and evidence artifact was uploaded.
- The preceding test-only correction [47aa91e](https://github.com/tarunsharma2610-del/tradepro-improved/commit/47aa91e2696bb6388af73ede568dfe89c4cbead7) asserts that a fixed-fee tariff rule with a maximum cap is rejected at rule construction. This does not weaken production validation.
- The single pytest warning is a Starlette/AnyIO deprecation warning. GitHub Actions also logged Node.js 20 action-runtime deprecation warnings. These did not fail the run.
- Aggregate `ORDER_FILL_SET` variance tests and the variance-only persistence service are present; this successful suite includes their tests. Variance records remain audit-only and do not promote charges or create per-fill allocations. Source-backed effective tariff applicability, charge composition, and durable accounting acceptance remain open gates.
- Synthetic restore is not actual Oracle Cloud recovery. PR #6 remains draft/unmerged. Live broker order execution and automatic accounting promotion remain disabled. All work stays in `tarunsharma2610-del/tradepro-improved`; never modify original `tarunsharma2610-del/Tradepro`.

## Next resume point — Upstox estimate reconciliation gate — 24 October 2026

- In `backend/app/services/tariff_estimate_snapshot.py`, estimate normalization now rejects a reported total that differs from the sum of normalized component amounts. DP-plan minimum metadata is not part of that component sum.
- In `backend/tests/test_tariff_estimate_snapshot.py`, regression tests cover total mismatch and ensure a null component is not treated as an explicit zero.
- Code commit: `ce0d426142b8e70b5cd56d0832694a397258f563`; tests commit: `8136ccdabbc5326d59e2b8a6951ae02c3495ab62`.
- CI run [40082403073](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40082403073) was still in progress at handover. Verify CI for the final documentation head before calling this gate green.
- Follow-up after CI: design explicit versioned component mapping and component-specific treatment for transaction/clearing/IPFT, nullable fields, and DP/demat per-scrip/day semantics. Keep unsupported components fail-closed; API estimates and aggregate totals are not actual per-fill evidence.
- Safety: PR #6 remains draft/unmerged; live broker writes remain disabled; all work only in `tarunsharma2610-del/tradepro-improved`, never the original `tarunsharma2610-del/Tradepro`.

## CI failure/fix — resume from corrected test head — 24 October 2026

- Run [40082403073](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40082403073) failed: **774 passed, 1 failed**. The changed-STT replay-conflict test changed STT but left the fixture's API total unchanged, so the newly added component-total check correctly failed first.
- Fixed the fixture to set total to `209.27` for STT `176.00` while keeping all other component amounts unchanged. This isolates replay conflict behavior without bypassing the reconciliation guard.
- Fix commit: `2a39a67cd1d2c8dab16e22425c87e247974c10cd`. Fresh run [40082588488](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40082588488) was queued at the time of this note.
- Next: inspect the run to completion, fix any remaining failures, then synchronize the remaining checkpoint docs and verify CI for the resulting exact latest head. Keep PR #6 draft/unmerged and live broker writes disabled.

## Upstox estimate reconciliation — corrected test and exact-head CI verified — 24 October 2026

- The corrected test fixture commit is [2a39a67](https://github.com/tarunsharma2610-del/tradepro-improved/commit/2a39a67cd1d2c8dab16e22425c87e247974c10cd). It updates the reported total consistently with the STT change so the replay-conflict test exercises replay behavior rather than failing the aggregate-reconciliation guard.
- Exact-head backend CI run [40082629274](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40082629274) passed on the then-current branch head [7e373f2](https://github.com/tarunsharma2610-del/tradepro-improved/commit/7e373f2f2ff0d2c7faae8397765df2d35b901599). Pytest, broker-write boundary guard, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and restore-evidence retention all passed. This confirms the previously failing workflow was corrected.
- This documentation synchronization creates a newer head, so CI must be checked again on the final resulting head before the documentation gate is called green.
- API estimates remain estimate-only. No candidate tariff rates were activated, no estimate was promoted into actual charges, and automatic per-fill allocation remains disabled pending reviewed component-specific rules and durable accounting acceptance.
- PR #6 remains draft/unmerged. Live broker order writes remain disabled. Work only in `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` is out of scope.

## Upstox component provenance checkpoint — 24 October 2026

- Upstox estimate normalization preserves `transaction`, `clearing`, `ipft`, and `sebi_turnover` as distinct components; it does not collapse them into a generic exchange-charge value.
- The component-separation regression test passed on exact PR head [0112f92](https://github.com/tarunsharma2610-del/tradepro-improved/commit/0112f92f065156e93069332be0a3665c601ab940), via [Backend tests run #40083185015](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40083185015). Pytest, broker-write boundary guard, SQLite/PostgreSQL migration round-trips, synthetic restore drill, and evidence-retention steps passed.
- Intermediate run #40083176492 failed at pytest before the test commit; it is superseded by the passing test-head run above.
- Estimate normalization is not tariff activation or actual-charge evidence. Do not map aggregate trade-charge outputs to individual fills or enable automatic transaction/clearing/IPFT allocation without reviewed component-specific semantics, source evidence, and an exact eligible-fill manifest.
- Open item: verify effective-dated component composition and GST taxable-base rules from official sources and reviewed fixtures; prevent IPFT double-counting where the tariff presentation combines it with transaction charges.
- PR #6 remains draft/unmerged; live broker order writes remain disabled. Work only in `tarunsharma2610-del/tradepro-improved`, never the original `tarunsharma2610-del/Tradepro`.

## PostgreSQL allocation concurrency CI — 24 October 2026

- Corrected PostgreSQL concurrency test fixture now creates valid portfolio, instrument, application-order, and broker-order prerequisites before broker fills. The initial fixture failed on a foreign-key constraint because it used random, non-persisted broker-order IDs; fixed in [fc0c539](https://github.com/tarunsharma2610-del/tradepro-improved/commit/fc0c539dc24f87a705207a16a98789fd63d928f8).
- Exact corrected head passed [Backend CI #40084015153](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40084015153): **777 passed, 1 warning**. CI set `TEST_POSTGRES_URL`; the PostgreSQL concurrency integration ran, alongside broker-write boundary checks, SQLite/PostgreSQL migration round-trips, and synthetic database/document restore with retained evidence.
- This verifies allocation persistence/concurrency only; it does not authorize tariff activation or automatic charge allocation. Keep transaction, clearing, IPFT and SEBI components distinct until official component-composition and GST taxable-base rules are reviewed; prevent IPFT double-counting.
- PR #6 remains draft/unmerged; live broker order writes remain disabled. Work only in `tarunsharma2610-del/tradepro-improved`, never the original `tarunsharma2610-del/Tradepro`.


## Upstox tariff coverage audit and exact-head CI — 24 October 2026

- Exact-head backend workflow [#40084947829](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40084947829) passed on commit `19fc2dcb6ba80d33324a58520fe1215fc4b8c36c`: **778 passed, 1 warning**. `TEST_POSTGRES_URL` was set; PostgreSQL concurrency tests ran. Broker-write boundary guard, SQLite/PostgreSQL migration round-trips, and synthetic PostgreSQL/document-volume restore passed. The single Python warning is a Starlette/AnyIO deprecation warning; CI also emits Node action-runtime deprecation warnings.
- Follow-up source coverage matrix added to `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`. It keeps brokerage, STT/CTT, stamp duty, exchange transaction charges, IPFT/clearing, SEBI turnover, GST, DP/demat and other fees separately scoped, with explicit unresolved gates. Current Upstox page/API evidence does not justify generic wildcard rules or automatic per-fill allocation from aggregate charge totals.
- No new tariff rule was approved or activated. DRAFT candidates remain non-selectable; tariff-driven automatic per-fill allocation remains disabled for unreviewed components. Resolve source/effective-date gaps, GST taxable base, transaction/IPFT inclusion, and DP per-scrip/day allocation before review/approval.
- PR #6 remains draft and unmerged; live broker order writes remain disabled. All work is confined to `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` remains out of scope.


## Phase 3 latest completed-work checkpoint — 24 October 2026

- **Verified regression-test commit:** `fd4253ce51f812886fa081eeae3499533bfe4e20`. Exact-head backend CI [run #40085703204](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40085703204) completed successfully: **780 tests passed**, with one Starlette/AnyIO deprecation warning (`anyio.abc.BlockingPortal`). CI set `TEST_POSTGRES_URL`, so PostgreSQL-specific tests were enabled. Alembic upgrade/downgrade checks through `202610240018`, broker-write boundary guard, and synthetic PostgreSQL/document-volume restore drill succeeded.
- **Latest code/test work:** `backend/tests/test_upstox_tariff_candidates.py` now checks candidate effective-window overlap for identical dimensions and enforces narrow-scoped exchange-charge candidate rows that remain DRAFT, without silently introducing an IPFT rule. These are scope/consistency guardrails; they do not validate or approve the rate values themselves.
- **Tariff audit status:** `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md` contains the component coverage matrix and approval gates for brokerage, STT/CTT, stamp duty, exchange transaction charges, IPFT/clearing, SEBI turnover, GST, DP/demat and other fees. Still unresolved: official effective-date/applicability evidence for all supported tuples; whether transaction-charge schedules include IPFT; product-specific GST taxable-component sets; and a reviewed basis for allocating aggregate/API and DP charges to fills.
- **Next step before further Phase 3 implementation:** use official, dated sources and appropriately scoped read-only API evidence to close these gates and add component-boundary fixtures. Do not infer per-fill actuals from aggregate totals. No DRAFT candidate was approved or activated in this work.
- **Safety / repo boundary:** work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` is out of scope and must remain untouched. PR #6 remains draft and unmerged. Live broker `place_order`, `modify_order`, and `cancel_order` execution remains disabled; PAPER mode remains mandatory.
- **CI scope note:** run #40085703204 validates the code at commit `fd4253ce...`; the documentation checkpoint commit that follows this note still requires its own CI result before it can be called green.


## Documentation checkpoint CI result — 24 October 2026

- The documentation checkpoint commit `177264164a9e495fc570fa4d5990aea3866317e5` passed exact-head workflow [#40086364594](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40086364594). Backend pytest reached 100% with **780 passing tests and one Starlette/AnyIO deprecation warning**. CI explicitly configured `TEST_POSTGRES_URL`; PostgreSQL-specific tests were enabled. Broker-write boundary guard passed, Alembic migration checks through `202610240018` completed, and synthetic PostgreSQL plus document-volume restore evidence was uploaded.
- This CI result validates commit `177264164...`; any subsequent documentation commit must be verified independently before its CI can be called green.
