<!-- Phase 3 checkpoint update — 27 Oct 2026. Latest code/test head 8feeb0cbb0c35e1e37012302c9075d43f1f33eb1 passed Backend CI #40458822529: 1,097 passed, 1 warning. Broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore and evidence retention passed. DP completeness checks require a consistent KNOWN + explicit valid finite nonnegative paise-exact amount, or NOT_APPLICABLE + no amount; invalid status, UNKNOWN-with-amount, KNOWN-without-amount, NOT_APPLICABLE-with-amount, NaN, negative and fractional-paise amounts fail closed. DP canonical manifests are checked against persisted broker trade → child order → local order mappings; only mapped equity-delivery SELL fills are accepted. Delivery SELL still requires reviewed/reconciled DP evidence and durable per-fill allocation; DP is included once in total and replay identity. Maintained docs are being synchronized after the green code run; exact-head CI on the final docs/checkpoint commit must pass before it is called green. PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled; original Tradepro repository out of scope. -->

## Latest authoritative checkpoint — 26 October 2026, 21:06 IST

This section supersedes earlier statements in this file that identify an older commit or CI run as the latest checkpoint. Historical entries below are retained for audit history.
- **Verified Phase 3 correction — 26 Oct 2026, 22:45 IST:** backend CI [#40366645906 PASSED](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40366645906) on code head `f9d302fce03e504985e96582a7af71b14fd89f28`: 1,034 passed, 1 warning; broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, and synthetic restore drill passed. Fix: DP/demat optional amount now reads from `optional_canonical_components`; live snapshot materialization remains limited to the core six-component map. This green run verifies the correction, not completion of GST/IPFT acceptance. Current work remains Phase 3; PR #7 Draft/unmerged, PAPER-only, live writes disabled.

- **Latest GST/IPFT working update — 26 Oct 2026:** working branch is `phase3/cross-broker-gst-ipft-resolution`, PR #7 remains Draft/unmerged. A failed backend run #40365836710 (46 failed, 988 passed) exposed a DP/demat optional-component `KeyError` because the allocation planner read the six-component amount map for an optional amount. Fixes on the current branch separate `optional_canonical_components` and make the allocation planner read that map for DP/demat; snapshot materialization iterates only the six-component canonical source map. Latest code change at time of update: `c0607aff672a9792410513e7564cd5f3c8d7f371`. Exact-head CI has not yet been confirmed; this is not a green checkpoint. Do not claim success until the current head's backend tests and safety/migration checks pass. PAPER-only; live broker writes remain disabled; do not modify original `Tradepro`.


- **Only target repository:** [tarunsharma2610-del/tradepro-improved](https://github.com/tarunsharma2610-del/tradepro-improved). Branch: `phase3/durable-per-fill-charge-allocation`. Latest documentation commit before this sync: `73c4a7cdcde4490bd520d5e75cc87fe1b4ffa310`. Exact-head documentation CI [#40346810442 PASSED](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40346810442).
- GST estimate implementation commit `b75a97f6cd0043c185375cc253b84a1e6d6bfea1`; exact-head CI [#40345937942 PASSED](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40345937942): 1,012 tests passed, 1 warning. Broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic restore/evidence-retention checks passed.
- **GST estimate decision:** apply 18% to brokerage + combined exchange transaction/IPFT charge exactly once; include explicit demat/DP charges additionally for equity delivery. Do not add STT, stamp duty, SEBI or trade notional to this published GST estimate base. Upstox's Brokerage Details API sample arithmetic conflicts with the explicit public schedule; the sample does not override the schedule or prove live billing is wrong. Sources: [Upstox pricing](https://upstox.com/brokerage-charges/), [Brokerage Details API](https://upstox.com/developer/api-documentation/get-brokerage/), [Trades Charges API](https://upstox.com/developer/api-documentation/get-trade-charges/), [NSE transaction/IPFT circular](https://nsearchives.nseindia.com/content/circulars/FA73061.pdf).
- **New Phase 3 gap found:** `demat_transaction_charges` is intentionally blocked by source-to-canonical mapping; canonical live accounting and `Execution` currently support six components only. Equity-delivery actual-charge accounting with a DP/demat charge is therefore not accepted yet. The estimate helper can include a demat amount, but that does not mean actual accounting can persist/reconcile it. Keep this fail-closed; do not drop DP charges or fold them into another component. Next implementation gate: product-aware canonical demat/DP component and total-charge persistence, migration, idempotency, allocation, and delivery/non-delivery regression tests—or keep delivery actual accounting unsupported until complete.
- Actual per-fill GST/invoice acceptance remains evidence-gated. Public schedules and calculators support estimates, not account-specific actuals; aggregate API values and null fields are not per-fill invoice proof. User is not required to provide a personal contract note. Actual tariff candidates remain DRAFT.
- Phase 3 remains IN PROGRESS; PR #6 remains open/draft/unmerged. PAPER mandatory; live broker order writes, automatic live-fill promotion and automatic scheduling remain disabled. Original `tarunsharma2610-del/Tradepro` must not be modified. AI/Algory integrations remain deferred until Phase 3 acceptance.

---

## Historical checkpoint (superseded) — 26 October 2026 (latest verified CI)

- Target repository only: `tarunsharma2610-del/tradepro-improved`; branch `phase3/durable-per-fill-charge-allocation`; implementation/test head `44830ec48b50b4f470ec9ca95dd2d3f4339dd3df`. Do not modify original `Tradepro`.
- Exact-head Backend CI: [run #40294178677 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40294178677), including the test separating NSE/IPFT arithmetic reconciliation from GST taxable-base approval.
- GST estimate helper accepts exactly 18%; tests reject 0%, 5%, 100%, and 100.01%. Rate guard does not approve taxable-base composition; component inclusion needs reviewer and invoice/source evidence.
- ₹307/crore versus ₹306.99/crore transaction charge + ₹0.01/crore IPFT is arithmetic reconciliation only, not GST-base approval.
- Canonical live-fill integration is verified: six independently verified charge snapshots, evidence revalidated under lock, no raw-only fallback; brokerage cap applied once before deterministic paise-exact allocation.
- Remaining Phase 3 gates: effective-dated tariff applicability; component-specific per-fill allocation acceptance; invoice/source-backed GST/IPFT and product/segment evidence; adversarial/migration/recovery review; final exact-head docs/sign-off.
- Upstox public schedules/calculator are estimates; aggregate charges endpoint is not actual per-fill evidence. Null remains unknown, not zero. Synthetic restore is not actual Oracle recovery.
- PAPER mandatory; live broker writes, automatic live-fill promotion and automatic scheduling disabled. PR #6 open/draft/unmerged unless explicitly approved. Defer AI/open-source adaptations until Phase 3 acceptance. Documentation commit needs its own CI.

---

## Canonical checkpoint reconciliation — 26 October 2026 (canonical live-fill integration verified)

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. Never modify original `tarunsharma2610-del/Tradepro`.
- **Latest verified implementation head before this documentation sync:** `255fc208eed4bc8b922977717209d27912055377`. Exact-head Backend CI [run #40286205714 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40286205714): **962 passed, 1 warning**. Broker-write boundary guard, SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade, synthetic PostgreSQL/document-volume restore, and restore-evidence retention all passed. Synthetic restore does not prove actual Oracle Cloud recovery.
- **PR #6:** open, draft, unmerged. Do not merge without explicit user approval.
- **Phase 3 integration completed on this head:** `LiveFillAccountingService` now requires exactly six independently verified canonical charge snapshots. It revalidates each canonical ledger and its source hashes/links/mapping version, reviewed fill manifest and weights, INR totals, durable reconciliation references, and the contract-note reference under lock. There is no fallback to raw-only legacy allocation rows. Extra, unmapped, unlinked, or foreign-connection per-fill allocations fail closed.
- **Integration tests:** canonical snapshot creation → independent review → allocation → reconciliation; direct and combined/split transaction/IPFT source lines canonicalize to one exchange-charge component; exact replay, missing/unreconciled/extra allocations, and PostgreSQL live-fill-versus-ledger promotion race. No live broker order writes are enabled.
- **Remaining Phase 3 gates:** (2) independently reviewed effective-dated tariff applicability; (3) approved component-specific per-fill allocation rules; (4) invoice/source-backed GST/IPFT and product-specific component acceptance; (6) final adversarial, migration and recovery review; (7) exact-head documentation/sign-off. Official public tariff snapshots are research evidence, not proof of account-specific actual charges; candidate rates remain DRAFT until the required review is recorded. Synthetic restore is not a real Oracle recovery test.
- **Upstox controls:** no unused SDK runtime dependency; Agent Skill remains development/static-review-only; brokerage calculator is estimate-only; aggregate charge endpoints are not per-fill actual evidence.
- **Safety invariants:** PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. Keep PR #6 unmerged until explicit approval.
- **Next step:** resume at the remaining Phase 3 tariff/component evidence gates. Do not repeat canonical snapshot integration. Do not begin the separate AI/open-source adaptations until Phase 3 acceptance is complete.
- **Documentation-sync note:** this multi-document commit must pass its own exact-head CI before the next implementation change.

---


---


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

<!-- Authoritative checkpoint audit: 2026-10-21; supersedes older status notes below. -->
## Superseding verification note — 21 October 2026

- Latest code/test commit: [e56bf4c66f74b875a3ba8fe388138a9d688dd1e2](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e56bf4c66f74b875a3ba8fe388138a9d688dd1e2), adding failed-commit rollback coverage for live-fill accounting.
- Exact-head CI for this commit is verified: [run 39564568154](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39564568154) passed 471 tests, 1 warning, the broker-write boundary guard and SQLite/PostgreSQL 16 reversible migrations. The subsequent documentation HEAD `adb69aeb05b70ba4fa9095fc73d9dea033d31eec` passed [run 39565251793](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39565251793).
- Phase 2 workflow boundary: resolved by keeping BrokerFillIdentity and manual BrokerTradeRecord independent. No bridge or dual-write is approved. SAFETY_BRANCH_PORT_MATRIX.md is the dependency map; live account-safety endpoints, charge adjustments, preflight, central broker-write service and actual live submission are not silently treated as Phase 2-complete.
- Historical checkpoint note: Phase 2 engineering checks and the cited code/test CI were verified on their respective commits. See the top checkpoint for current-head documentation CI and Phase 2 closure status.

## Historical checkpoint — formerly marked Current verified checkpoint — 21 October 2026

- The reconciliation crash-recovery/lease-fencing sub-slice is complete; backend CI run 39561621808 passed 470 tests, 1 warning, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles.
- The defined Phase 2 dependency/port matrix and workflow-boundary decision are complete; the code/test checkpoint and current documentation HEAD have passing exact-head backend CI (runs 39564568154 and 39566324985). Phase 3 accounting integration and Phase 4 live-trading release gates remain blocked by design while final historical-status consistency review is completed.
- The latest documentation HEAD `0bd502f83118799d5564e8fd5724d01e8dc975af` passed exact-head backend CI [run 39566324985](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39566324985). Any subsequent commit requires its own exact-head CI verification.
- Live broker submission, automatic accounting promotion and automatic scheduling remain disabled.

- Current `main` HEAD is the latest documentation synchronization commit; the verified code/test checkpoint is `fe07b77b193da1232787384efb38cb589e0d71b6`. Check the live repository HEAD and Actions page for the newest documentation-only commit and its CI result.
- Latest exact-HEAD backend CI: [run 39562094642](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39562094642) passed **470 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles.
- Phase 2 slow-persistence/high-volume lease-expiry audit is complete. The PostgreSQL slow-persistence lock test and new 20-iteration concurrent expiry-boundary renewal/reclaim regression passed exact-head CI run [39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386): 472 tests, 1 warning; source guard and SQLite/PostgreSQL 16 migration cycles passed.
- Latest frontend CI remains [run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474), passing TypeScript and Next.js build; no frontend code changed in this checkpoint.
- Documentation files were synchronized in commit `f369839f20efed60f62abdbc329fe6d4454faeaa`. Historical references to earlier commits and counts below are historical records, not current status.
- Phase 3 is not started. External-repository borrowing remains paused; live broker submission, automatic accounting promotion, and automatic scheduling remain disabled.


- **Repository/branch:** `tarunsharma2610-del/tradepro-improved`, `main`. The original `tarunsharma2610-del/Tradepro` repository is a protected baseline and must remain untouched.
- **Latest repository HEAD before this audit update:** `a297b1a356c133aaca0ed10079eb5226c03b747b` — documentation-only commit `docs: synchronize Phase 2 status with passing CI evidence`.
- **Latest code/test commit:** `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`. Recorded exact-commit backend CI run [39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed **466 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles. Frontend run [39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript and Next.js build.
- **Previously verified documentation CI:** commit `6407c5a05865c1be0ef673d3bb5e71c0231ef8da`, run [39556816828](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556816828), backend job completed successfully. The later documentation-only commit `a297b1a356c133aaca0ed10079eb5226c03b747b` was found on `main`; CI for that exact HEAD was not independently established before this audit update. Do not infer exact-head CI success from an earlier commit.
- **Phase 2 checkpoint verified in project records:** atomic run/lease finalization; stale-owner protection; cancellation and interrupted-run recovery; inconsistent lease token/expiry rejection; five-record renewal boundary; and incomplete-summary warnings for `WORKER_INTERRUPTED` and `LEASE_LOST`.
- **Historical audit disposition — superseded:** the slow-persistence and high-volume lease-expiry/renewal race audit is now complete. Existing transaction-level fencing plus the two PostgreSQL regression tests cover the demonstrated row-lock and stale-owner behavior; no production-code change was required for this audit.
- **Safety constraints remain:** no real broker orders in tests; live broker submission, automatic accounting promotion, and automatic scheduling remain disabled; keep `BrokerFillIdentity` separate from `BrokerTradeRecord`; do not wholesale-merge the divergent safety branch.
- Older checkpoint entries below are retained as history, not current instructions. This top section is the authoritative current state. After this documentation commit, verify CI for its exact HEAD before treating the checkpoint audit as fully closed.

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

## Scope and inventory
The recursive Git tree inventory now contains 219 files, including backend application code/tests, frontend routes/components, migrations, configuration, documentation and deployment files. The second-pass review covered the primary API routes, models/repositories, trading/accounting/strategy/risk services, Upstox adapter, auth/OAuth, middleware, frontend workflows, migrations, CI and deployment configuration. The full automated backend suite and CI migration check were run; this remains a static review, not a production end-to-end test.

## Requirement matrix

Status meanings: **Complete in current scope** means existing implementation and relevant automated coverage were found; **Partial** means useful code exists but the complete requirement is not met; **Missing** means no implementation was found; **Verify in staging** means static inspection/CI cannot prove operational behavior.

| Requirement | Status | Existing evidence / finding | Change decision |
|---|---|---|---|
| Preserve separate improved repository | Complete | `tradepro-improved` is separate; changes are confined to `safety/fail-closed-trading-mode`. | Keep original `Tradepro` untouched. |
| Backend API and user/portfolio isolation | Complete in tested scope | Authenticated routes and ownership checks; tests cover cross-user portfolio, strategy, backtest and order access. | Retain; add regressions if shared paths change. |
| Password/MFA/session security | Partial | Argon2id password hashes, JWT access/refresh tokens, TOTP MFA, httpOnly cookie use and rate limits exist. Refresh-token revocation/session inventory is not present in the reviewed model. | Do not rewrite; review only if a requirement or defect demands it. |
| Upstox OAuth and credential storage | Mostly complete; staging verification required | Credentials are encrypted at rest and masked in responses; OAuth state is signed, bound to user/connection, expires, and uses a one-time DB nonce. Access-token expiry is checked. Real broker login was not tested here. | Preserve existing implementation; keep OAuth tests. |
| Real quotes and historical candles | Partial | Upstox LTP and historical candle methods exist; paper orders reject absent/invalid quotes instead of inventing prices. WebSocket streaming is a stub. | Keep existing quote/candle path; implement streaming only with verified API docs and tests. |
| Instrument master | Partial | Official Upstox docs list the complete JSON BOD instrument file and fields including segment, instrument type, lot size and tick size. The current importer still filters to `NSE_EQ` only and does not map derivative contract fields. The tick-size unit/normalization is not yet verified, so tick-increment enforcement is not safe yet. The adapter's separate `sync_instruments` method remains a stub. Seed list contains ten equities. | Expand only after implementing and testing full field mapping, tick-size units, expiries/strikes, contract quantities and supported-segment validation. |
| Paper order placement and accounting | Implemented with operational limitations | Shared `ExecutionService` uses real quotes for simulated market fills; pending LIMIT matching and cancellation exist. Paper fill writes now update order status, aggregate position, cash and execution in one transaction, with a regression test proving rollback on execution-persistence failure. Strategy-owned allocation is separately tracked. Derivatives are rejected until instrument sizing and risk accounting are verified. | Preserve paper/live separation; add tests for any accounting changes and never route paper orders to the broker. |
| Paper/live isolation | Partial; safety guard now added on branch | Baseline service always writes `trading_mode="PAPER"`; `TRADING_MODE` previously only warned at startup. Branch adds a fail-closed check in `ExecutionService.place_order` and a regression test. CI passed on PR branch. This is not live execution. | Keep guard while no separate live execution service exists; review its effect on PAPER orders if environment is set to LIVE. |
| Atomic live-fill accounting | Partial; unregistered promotion coordinator tested | Coordinator validates a staged trade, obtains an explicit Upstox `APPROVED_ESTIMATE`, revalidates identity after async I/O, then writes connection-scoped `LivePosition` + `Execution` atomically. Replay reuses persisted provenance; unsupported DP allocation fails closed. Actual per-trade charges remain unverified; no route/worker wiring. | Audit child-order cumulative-fill invariants and contract-note reconciliation; verify PostgreSQL/staging before any route/worker wiring. |\n| Live order lifecycle | Partial; read-only status check foundation added | Adapter has broker `place_order`, `get_order_status`, `get_order_book`, `get_positions`, and `get_holdings` methods. The safety branch now stores optional broker order metadata and adds a read-only service to check a known LIVE order's broker status after ownership/session/order-ID validation. It validates any returned broker order ID and records the raw status without changing local FILLED/CANCELLED state or cash/positions. An authenticated read-only broker-status endpoint is now exposed for orders that already have a stored broker ID. Live placement is still absent; no automatic reconciliation of partial fills, cancellation, timeouts or restart recovery exists. | Build and review a separate live lifecycle; only map statuses and account for fills after verified payload contracts and reconciliation tests. Do not replace paper execution. |
| Duplicate-order prevention/idempotency | Partial | Optional client idempotency key and a per-portfolio database uniqueness constraint protect matching API retries. Strategy entries also check their strategy-owned position under the portfolio lock, preventing a second fill when overlapping evaluations race. The frontend and strategy scheduler do not yet consistently supply idempotency keys, and broker-side idempotency/unknown-timeout reconciliation are missing. | Keep DB constraints and fill guards; wire stable retry keys into callers and implement broker correlation/reconciliation before live execution. |
| Risk controls | Partial | Strategy-level realized daily-loss checks and an automated-entry kill switch exist. The safety branch adds a portfolio-wide realized daily-loss guard for automated strategy entries (default 2%) and a single-order notional cap for paper orders (default 25% of starting virtual capital), both configurable. The order cap uses price × quantity as represented by current paper accounting; derivative multipliers/lot sizes are not yet verified. Neither is a complete live risk system. Portfolio-wide exposure and a broker-error circuit breaker remain missing. | Keep controls server-side; add exposure/circuit-breaker and verify derivative contract sizing before live use. |
| Strategy engine/scheduler | Partial | Five-indicator scoring, trailing-stop logic, worker cadence and isolated per-strategy sessions exist. New strategy-position allocations stop a strategy from closing a manual/other-strategy position and calculate strategy P&L on its own entry basis. The fill path also rejects duplicate entries for a strategy that already owns a position. Exchange holiday handling and stable evaluation-level idempotency remain incomplete. | Preserve engine; retain strategy-allocation regression tests and add calendar/evaluation-key safeguards as needed. |
| Orders/P&L/costs/analytics/backtesting | Partial to complete by feature | Decimal-based cost calculation, position math, backtests, realized analytics and tests exist. Live broker-confirmed fills/unrealized P&L are not supported because live execution is absent. Cost rates and live-market assumptions require periodic verification. | Retain tested paper/backtest logic; do not imply live-accounting parity. |
| Frontend workflows | Partial | Dashboard, portfolios, orders, strategies, backtests, analytics, broker settings, notifications and admin pages exist. Dashboard explicitly says live trading is not enabled; no live mode workflow/confirmation UI exists. | Do not add duplicate pages; add UI only after backend live workflow is safe. |
| Audit logs and operational visibility | Partial | Audit log writes exist for important auth/broker/settings events; no complete order lifecycle audit/reconciliation dashboard or circuit-breaker status exists. | Extend existing logging when execution lifecycle is implemented. |
| Database migrations | Existing chain; staging verification required | Six original revisions plus three forward safety-branch revisions exist. The latest migration adds strategy-owned position tracking and backfills legacy strategy executions/positions. CI checks a clean SQLite upgrade; a real existing production database has not been upgraded in staging. | Keep migrations forward-only, test clean upgrades and data backfills, and back up/verify staging before production. |
| Deployment and CI | Partial | GitHub Actions cover backend tests/migrations and frontend typecheck/build. Compose deploys Postgres, Redis, backend, worker, frontend and Nginx. Nginx is HTTP-only until TLS setup; production configuration still needs environment-specific verification. | Keep CI; validate deployment and TLS before OAuth/live use. |

## Baseline and verification evidence
- Main branch's existing audit records a previous backend run of 167 passing tests and a successful frontend typecheck/build. These are historical results.
- Latest verified backend CI: **188 tests passed, 1 warning**, and the full Alembic chain upgraded a clean SQLite database: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39030941704. Latest frontend TypeScript/build checks passed: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39030941702. The migration's legacy-data backfill path is reviewed in code but not yet exercised against a copy of a populated production database.
- This backend workflow result does not prove a real Upstox session, market feed, broker order, production database, TLS configuration, or live-trading behavior.
- No real broker orders were placed.

## Prioritized change plan
1. **Next:** audit `BrokerOrder`, execution/fill models, migrations and reconciliation services; implement the smallest additive, transaction-safe broker trade/fill idempotency and partial-fill aggregation foundation.
2. Test repeated trade IDs, concurrent/replayed intake, quantity aggregation and rollback with mocked broker responses. Never double-count or mutate PAPER accounting.
3. Keep the preflight coordinator unregistered from routes/workers and live submission disabled.
4. Complete broker-confirmed order status/fill/cancel reconciliation, account-level kill switch, broker-error circuit breaker and operational recovery.
5. Verify derivative mapping, tick/lot sizes and margin treatment before enabling non-equity segments.
6. Run backend tests, SQLite/PostgreSQL migration checks, frontend typecheck/build and staging verification. Keep live trading disabled until all release gates and explicit review are complete.

## Retained unchanged after review
- Existing paper order/accounting engine, order and position models, cost engine, strategy scoring, backtest engine, notification integrations, OAuth/credential encryption, existing pages, and current migration history.
- Existing adapter methods for broker order/status/book/positions/holdings are to be reused where correct, not duplicated.
- The original `Tradepro` repository and its `main` branch remain untouched.

## Release gate
Live trading is **NOT READY**. No live order placement should be enabled until current official API contracts, durable idempotency, risk limits, broker-confirmed fills, cancellation/timeout/restart reconciliation, credential/session controls, kill switch, audit trail, tests, deployment controls, and required broker/compliance authorization have been verified.


## Verification update — 17 October 2026

- The strategy-position migration backfill is no longer only statically reviewed: `backend/tests/test_strategy_position_migration.py` creates a populated database at revision `202610170002`, upgrades to head and verifies closed/open allocations, per-execution realized P&L, legacy over-sell behavior and preservation of aggregate portfolio accounting.
- CI on commit `1fe681246cb88a9505302a1763128c51ab72802d`: [backend 190 passed, 1 warning, migration upgrade passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39031526388); [frontend TypeScript/build passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39031526360).
- Remaining unverified items are populated PostgreSQL/staging migration execution, production rollout and all live broker order lifecycle behavior.


## Idempotency verification update — 17 October 2026

- The manual order UI's existing retry-key behavior was inspected and retained unchanged: it reuses the same key after a failed response and clears it after a successful response or when the user changes order parameters.
- Strategy order submissions now use deterministic keys for strategy + side + latest candle timestamp. Orders are not submitted automatically when that timestamp is missing. Existing-key validation now includes strategy/manual execution reason and strategy ID.
- Regression tests cover same-candle retry, invalid candle timestamp and cross-scope key reuse. Latest CI: [backend 193 passed, 1 warning and migration upgrade passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032153163); [frontend checks passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032153157).
- The complete live order lifecycle is still not implemented; this idempotency is a paper/strategy safeguard, not broker-side idempotency.


## Upstox order endpoint audit — 17 October 2026

- Current official Upstox documentation marks the legacy V2 place-order endpoint as deprecated and documents Place Order V3 at `https://api-hft.upstox.com/v3/order/place`; the V3 response uses `data.order_ids`. See [Place Order V3](https://upstox.com/developer/api-documentation/v3/place-order/) and the legacy [Place Order API](https://upstox.com/developer/api-documentation/place-order/).
- Updated the isolated adapter and mocked test only. The method is still not wired to `ExecutionService`; live trading remains disabled.
- Current official docs also provide V3 modify and cancel endpoints. The base adapter interface does not yet expose either operation; this is a verified gap for the next task. See [Modify Order V3](https://upstox.com/developer/api-documentation/v3/modify-order/) and [Cancel Order V3](https://upstox.com/developer/api-documentation/v3/cancel-order/).
- Latest CI for endpoint correction: [backend 193 passed, 1 warning, migration passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032413141); [frontend passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032413150).


## Upstox V3 modify/cancel adapter update — 17 October 2026

- Added `modify_order` and `cancel_order` to the adapter interface and Upstox V3 implementation. The official endpoints are documented at [Modify Order V3](https://upstox.com/developer/api-documentation/v3/modify-order/) and [Cancel Order V3](https://upstox.com/developer/api-documentation/v3/cancel-order/).
- Mocked regression tests verify the V3 routes and arguments. These adapter methods are not wired to the app's order management, do not submit orders during tests, and do not mutate local accounting.
- Latest CI: [backend 195 passed, 1 warning and migration upgrade passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032570839); [frontend checks passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032570823).
- Remaining: separate live order lifecycle, broker-side idempotency, response handling for one-or-many order IDs, confirmed modify/cancel state, partial-fill and restart reconciliation, and live risk controls.


## Live execution readiness audit — 17 October 2026

- Safety guard: `ExecutionService.place_order` rejects LIVE/unknown mode before order creation. Keep it until a separate service is independently reviewed.
- Authentication: OAuth state has signature, expiry, user/broker/connection binding and single-use nonce; credentials/tokens are encrypted; expired access tokens return unavailable. Refresh-token automation is not present.
- Risk/instruments: strategy and automated-entry portfolio loss guards and a paper notional cap exist. They do not amount to a live/manual pre-trade risk system. Instrument validation is deliberately equity-only; derivative contracts/tick sizes/lot/margin remain unverified.
- Order lifecycle: V3 adapter methods exist for place/modify/cancel, but they are not wired. V3 place response may return multiple `order_ids`; the local model lacks partial-fill state. Current broker status reconciliation is read-only and does not reconcile trades, fills, cash, positions, timeout/restart ambiguity or broker/local mismatches.
- Immediate safe improvement selected: the official [Get Order Details API](https://upstox.com/developer/api-documentation/get-order-details/) documents `data.order_id` and `data.status`. Require the response ID to be present and match the requested broker order before storing its status.


## Broker status identity validation — 17 October 2026

- The read-only status checker now rejects missing/blank broker `order_id` values as well as mismatches. This matches the documented [Get Order Details response](https://upstox.com/developer/api-documentation/get-order-details/), which returns `data.order_id` and `data.status`.
- Mocked tests confirm no local order status/fill state is inferred on malformed identity responses. CI: [backend 195 passed, 1 warning and migration check passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032760874); [frontend passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032760872).
- Next gap: the adapter lacks a per-order trade lookup, needed as a foundation for partial-fill reconciliation. Add read-only adapter support only; do not mutate local accounting yet.


## Read-only per-order trade lookup — 17 October 2026

- Added `get_order_trades` to the adapter contract and Upstox implementation. Official documentation specifies `GET https://api.upstox.com/v2/order/trades?order_id=...` and returns a list of trade records, including `trade_id`, `quantity`, `average_price` and `order_id`: [Get Order Trades](https://upstox.com/developer/api-documentation/get-trades-by-order/).
- Mocked test passes in CI. This method is not wired to reconciliation/accounting yet.
- Next safe foundation: read-only Order History lookup by stable tag or order ID to help recover a lost submission response without blindly resubmitting.
- Latest CI: [backend 197 passed, 1 warning, migration check passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032909906); [frontend passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032909935).


## Read-only order-history lookup — 17 October 2026

- Added `get_order_history` to the adapter contract and Upstox implementation using the official [Get Order History API](https://upstox.com/developer/api-documentation/get-order-history/). It accepts `order_id`, `tag`, or both; rejects empty queries, blank identifiers and tags longer than 40 characters before network access.
- Mocked tests cover tag and order-ID queries plus invalid inputs. After fixing a missing test import found by CI, latest result is [200 backend tests passed, 1 warning, migration check passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033094768) and [frontend passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033094833).
- This method is not wired into a live submit/recovery workflow. Next deliverable is a reviewed live order state-machine design; no live submission yet.


## Live order state-machine design — 17 October 2026

- Added [`LIVE_ORDER_STATE_MACHINE.md`](LIVE_ORDER_STATE_MACHINE.md), a design-only specification grounded in official Upstox docs for Place Order V3, Modify/Cancel V3, Order Details, Order History and Order Trades.
- The design identifies the missing data model for one local order to multiple broker order IDs, unique trade IDs and partial fills; it also defines timeout recovery by stable tag, broker-confirmed cancel/modify states, atomic fill accounting, restart recovery and account-level risk gates.
- This is documentation only; no live submission or accounting behavior changed. Next task is additive model/migration support with tests, still not wired to execution.


## Broker-order schema foundation — 17 October 2026

- Added migration `202610170004_live_broker_order_state.py`, a `BrokerOrder` child model for one-to-many broker IDs, a unique nullable stable tag on local orders, wider order status field, and nullable execution fields for child-order linkage and per-broker unique trade IDs.
- Populated migration test upgrades from revision 003 and verifies preservation of paper data, multi-child mapping, duplicate ID/trade rejection and `PARTIALLY_FILLED` storage. Latest CI: [201 passed, 1 warning, clean migration](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033460748); [frontend passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033460785).
- Schema only: no live execution or reconciliation path uses these new fields yet. Next step is pure response validation/mapping helpers before any live service is wired.


## Pure Upstox response validation — 17 October 2026

- Added `backend/app/brokers/upstox/response_parsing.py` with typed, pure parsers for Place Order V3 IDs, Order Details, Order History and Order Trades. No network/database calls and no live execution wiring.
- Tests cover malformed payloads, mismatched IDs, duplicate place IDs/trade IDs, invalid quantity/price and valid empty history/trades. Official docs show Order History may contain repeated order IDs as a timeline; this is accepted.
- Latest CI: [223 passed, 1 warning, clean SQLite migration](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033704367); [frontend passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033704247).
- Next audit: define all-order live risk preflight and account circuit-breaker requirements before any live service is implemented.


## Live pre-trade risk gap audit — 17 October 2026

- Current `RiskEngine` is for strategy entries and uses realized P&L; manual orders bypass it and unrealized drawdown is not included. The paper order cap, virtual-cash checks and holdings protection in `ExecutionService` are not a live risk system.
- No broker funds/margin method exists in `BrokerAdapter`. Current official Upstox [Funds & Margin V3](https://upstox.com/developer/api-documentation/get-funds-and-margin-v3/) was released on 10 April 2026 and returns `available_to_trade.total` plus detailed cash/pledge balances. It requires `Api-Version: 3.0` and uses `GET https://api.upstox.com/v3/user/get-funds-and-margin` without a segment parameter. See the [release announcement](https://upstox.com/developer/api-documentation/announcements/get-funds-and-margin-v3/).
- Other live risk gaps: max notional/exposure/position limits for all order sources, realized+unrealized daily loss, order rate/frequency, stale quote and market-session guards, and a live account kill switch/circuit breaker.
- Next safe implementation: read-only funds/margin adapter support with mocked tests. Do not use it to approve an order until risk controls and the separate live service are complete.


## Funds & Margin V3 adapter update — 17 October 2026

- Added read-only `get_funds_and_margin` to the broker interface and Upstox adapter using `GET https://api.upstox.com/v3/user/get-funds-and-margin`, with required `Api-Version: 3.0` header. Official docs show `available_to_trade.total`, `cash_available_to_trade.total`, and `pledge_available_to_trade.total`; the service is unavailable from 00:00 to 05:30 IST and returns 423 during maintenance. [Official V3 docs](https://upstox.com/developer/api-documentation/get-funds-and-margin-v3/).
- Mocked tests verify URL, header, response shape and maintenance error propagation. The data is not yet used by risk checks.
- Latest CI: [225 passed, 1 warning, clean migration](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033992221); [frontend passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033992223).
- Next: parse this nested response into a typed object and preserve separate cash vs pledged margin fields before any risk logic uses it.


## Funds & Margin V3 parser — 17 October 2026

- Added a pure typed parser for the official Funds & Margin V3 response. It keeps `available_to_trade.total`, `cash_available_to_trade.total`, and `pledge_available_to_trade.total` distinct; parses realized/unrealized loss; and supports signed unsettled-profit/loss amounts. It rejects malformed structure and non-finite/negative available balances.
- Tests cover valid response, missing nested fields, NaN/Infinity, negative available balances, malformed unsettled profit and error/423 envelopes. Latest CI: [235 passed, 1 warning, migration passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39034164505); [frontend passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39034164514).
- Next: read-only instrument margin calculation API support, still not used to authorize orders.


## Instrument margin calculation adapter — 17 October 2026

- Added read-only `BrokerAdapter.get_margin_details` and Upstox `POST /v2/charges/margin` call. Local validation caps requests at 20 instruments, rejects duplicate/empty keys, non-positive/non-integer quantities, unsupported transaction/product values, and invalid optional prices. Tests use mocks only.
- Latest CI: [238 passed, 1 warning, clean SQLite migration](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39035755714); [frontend checks passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39035755707).
- Status: read-only adapter foundation only. Response remains untyped/raw and does not authorize orders. Next: audit official response schema and add a typed parser only if no suitable existing parser exists.


## Upstox Margin Details parser — 18 October 2026

- Classification: **implemented in code; test execution requires CI confirmation**. Added typed `MarginEstimate` / `MarginBreakdown` models and pure `parse_margin_details` for documented `required_margin`, `final_margin`, and per-instrument margin components.
- Validation includes successful response envelope, non-empty margins array, required fields, and finite non-negative numeric values. Added valid-response and malformed/error regression tests.
- Code commits: `3c4dd6ac0d7d88a18916c241d28a224fc5031d5d`; tests `6995f64429b44134edfa5985ad4f50c3b54cfcab`.
- Safety classification unchanged: read-only estimate parsing only; no order approval, live submission, or account-risk decision consumes these values. Live trading remains not implemented.
- Verification gap: available Actions results show successful backend/frontend runs for the earlier verified commit, but no run could be confirmed for the current PR head. Do not mark these new tests passed until CI for the current head is inspected.


## Status correction — 18 October 2026 (supersedes stale next-step notes)

The following are now present in the branch: `BrokerAdapter.get_margin_details`, the Upstox `POST /v2/charges/margin` implementation with local request validation, pure `parse_margin_details`, and unit tests for success/error/malformed response shapes. Older notes saying the adapter method or typed parser is still missing are historical snapshots, not current status. The parser is read-only and is not used to authorize orders.

The current blocker is verification: the GitHub integration returned no workflow run and no commit status for the current PR head when checked. Earlier CI results (238 backend tests, one warning, migration/frontend checks green) belong to an older commit and do not verify the margin parser changes. No pass/fail conclusion is possible from the available evidence. Inspect or trigger the configured workflow from GitHub Actions and record actual results before advancing.

`MASTER_ROADMAP.md` is now the current sequencing guide. After this verification gate, the next implementation phase is a separate, initially unregistered `LiveExecutionService` with mocked tests, while preserving the current PAPER-only execution guard. Do not merge the draft PR, place real orders, or enable live trading.


## Status update — broker trade ingestion (18 October 2026)

| Requirement | Status | Evidence / limitation | Next action |
|---|---|---|---|
| Normalize broker trade-book rows | Implemented in parser; validation pending on current head | `parse_order_trades` returns typed `BrokerTrade` values and validates broker order ID, trade ID, quantity, price and side. | Verify parser tests on current head. |
| Persist broker trade rows idempotently | Implemented; verification pending | `BrokerTradeRecord` and `BrokerTradeIngestionService` stage rows with a unique `(broker_connection_id, broker_trade_id)` key. Exact replay is skipped; conflicting reuse is rejected. | Run test suite and migration check. |
| Tenant isolation and parent/child broker mapping | Implemented in intake service; verification pending | Service requires the authenticated owner, a LIVE local order, a mapped child broker order, and a child-order connection matching that owner's broker connection. | Verify negative-path tests. |
| Account-scoped broker identifiers | Schema change implemented; migration verification pending | Migration 006 changes broker child-order and execution uniqueness to include broker connection; legacy child rows are backfilled when identifiable. | Test populated legacy rows and current migration chain on SQLite; verify PostgreSQL separately. |
| Promote staged broker trades into accounted executions | Missing | Intake intentionally does not mutate cash, positions, order status, execution ledger or P&L. Actual fee handling and atomic live accounting are not complete. | Design and test a separate reconciliation/accounting step only after current intake CI is green. |
| Current branch CI | Requires verification | Current head `32eea17c141d4cfbc727eed2ff2a1b40d21dbba3` returned no workflow runs/statuses through the connected integration; local network could not clone GitHub. | Obtain exact-SHA backend and migration results; do not infer success. |


### Verification note — 18 October 2026

Migration 006 now has a targeted populated-data test for backfilling broker connection IDs on legacy broker child-order and execution rows. This is test code added, not a verified pass. Current head is `a68c336e4a35ccc0bfe4d6539760ad03e40672f1`; current-head CI must be checked before this requirement is marked verified.


Final verification note: code/test target `a68c336e4a35ccc0bfe4d6539760ad03e40672f1`; documentation-only commits followed it. The PR head observed at the last check (`1b0056d9739cd55d50cd5484cddf955aa8bf07db`) had no workflow run/status returned. Keep ingestion and migration requirements marked “verification pending.”


## Phase 2 follow-up audit — 18 October 2026

| Requirement | Current status | Evidence | Remaining gate |
|---|---|---|---|
| Bind ingested trades to the exact user's broker connection | Code hardened; verification pending | Commit `2cdbbe290f8b661cb91110dbb4e165fcef36f800` resolves the connection using the broker child order's connection ID plus owner and broker; null/unowned mappings fail closed. | Run cross-user binding regression test on current code. |
| Require instrument identity before staging broker fills | Code hardened; verification pending | Intake now rejects missing/non-text tokens and mismatches against the local instrument key. | Run parser + ingestion tests against current head and confirm Upstox trade-book payload contains the expected instrument token. |
| Malformed broker trade side | Code hardened; verification pending | Non-string/blank side input now returns a controlled validation error rather than an attribute error. | Run new negative-path tests. |
| Current-head backend/migration verification | Blocked/pending | Code/test target `264aa4c609d522cd01d07e8213bfee6f14c7a2bf`; no Actions run returned for this branch/head. | Manually dispatch `.github/workflows/backend-tests.yml` on the safety branch and record actual results. |

No live-order, execution-ledger, position, cash, order-status or P&L behavior was added by this continuation. The live-trading release gate remains closed.


Additional regression: commit `264aa4c609d522cd01d07e8213bfee6f14c7a2bf` adds coverage that legacy broker child orders left without a determinable connection are rejected by ingestion. Latest code/test target is `264aa4c609d522cd01d07e8213bfee6f14c7a2bf`; this test has been added but not executed on current-head CI.


## Phase 2 migration audit continuation — 18 October 2026

A further audit found that migration `202610180006` used an arbitrary `LIMIT 1` to infer a legacy broker connection. That is unsafe if data cannot establish a unique match. The migration now backfills `broker_orders` and linked `executions` only when exactly one owner/broker connection match exists; rows without a determinable connection stay NULL and the ingestion service rejects them. This preserves fail-closed behavior and avoids silently binding legacy records to an arbitrary account.

- Migration hardening commit: `81faa9f0225a8b50f1036b5316e747517c3f02ed`.
- Migration regression coverage commit: `203c7fcf47626ea85c4dce9762c165a2cd74ab26`, refined to model a legacy owner with no matching broker connection in `d2f7f87c82b286e54284da2a8c186be0ea28e852` and `669a3fb98cd47dccea7e75a1301c74c01c4a3ce3`.
- Latest code/test target: `669a3fb98cd47dccea7e75a1301c74c01c4a3ce3`.
- Verification: still pending. Current-head Actions query returns no run/status; do not claim tests or migrations pass until the configured workflow runs against this target.
- Next action remains the backend pytest + SQLite Alembic workflow gate. No live service wiring, production migration, PR merge, or live order is authorized by this checkpoint.


## Verified CI checkpoint — 18 October 2026

GitHub Actions run [#39109239829](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39109239829) completed successfully on commit `8a256828d202e25e3fba77b496f0da01899969b9` (safety branch). Evidence from the job log:

- Backend pytest: **266 passed, 1 warning, in 16.08s**.
- SQLite migration check: **`alembic upgrade head` succeeded**, including revisions `202610180005` and `202610180006`.
- Warning: Starlette test-client deprecation for `anyio.abc.BlockingPortal`; no test failure.
- Workflow job and overall run conclusion: **success**.

This verifies the code present at that SHA in CI. It does not validate PostgreSQL migration behavior, live broker connectivity, real order submission, live accounting, frontend build, or production deployment. Keep those as separate gates.


## Authoritative continuation checkpoint — 18 October 2026 (supersedes older pending-CI and next-task notes)

### Latest verified state

- Latest verified code/workflow SHA: `677fcf882e0ce1e6e02be3bb8df0d074b8fbf220`; commits after this SHA update documentation only and do not change the verified backend code.
- GitHub Actions [run #39109587876](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39109587876) on that exact SHA: **286 passed, 1 warning in 18.93s**, followed by successful SQLite `alembic upgrade head`. Run conclusion: success.
- Earlier verified baseline run #39109239829 had 266 passed; the newer 286-test run includes the new preflight tests. Do not use older “CI pending” paragraphs below as current status.
- The single Python warning is the existing Starlette/AnyIO deprecation. No test or migration failures occurred in the verified run.

### Completed in this continuation

1. Hardened migration 006 so it backfills broker connection IDs only when a unique owner/broker match exists; unresolved legacy rows remain unbound. Added regression coverage.
2. Added a separate `LiveExecutionService` preflight-only module and default-off `LIVE_ORDER_SUBMISSION_ENABLED` environment interlock.
3. Preflight requires `TRADING_MODE=LIVE`, the separate default-off interlock, explicit per-request confirmation, an injected reviewed account-wide risk gate, owned/active portfolio, active supported equity instrument, verified Upstox connection and usable token. Invalid inputs and risk-gate failures block.
4. The service returns a non-secret preflight plan only. It creates no Order row, does not call any broker adapter, does not persist a tag/intent, and does not change cash, positions, executions or trade staging. It is not registered to any API or worker. Live trading remains disabled.
5. Backend workflow now runs on `safety/**` pushes and relevant backend/workflow changes, while documentation-only changes do not retrigger backend CI.

### Next implementation task

**Stable idempotency/tag recovery for ambiguous submissions — design and mocked tests only.** Audit existing `Order.idempotency_key`, `broker_tag`, and adapter `get_order_history(tag=...)` behavior. Add a deterministic tag/intent persistence design and tests proving a retry never submits a second POST after a timeout. Do not implement or invoke real broker submission in this task; do not wire the service into routes/workers; do not merge PR #1 or enable live trading. After code/test commit, update progress, audit, requirements, roadmap, changelog, architecture, state-machine and handover files with exact CI evidence.

## Authoritative checkpoint — 18 October 2026 (idempotent live intent and tag recovery)

### Historical checkpoint — formerly marked Current verified implementation
- Latest code/test SHA: `de2e2b7524f09b1be2d4378a9b5ac29bdf26f9e7`. GitHub Actions [run #39110239225](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39110239225) completed successfully: **296 passed, 1 warning in 22.04s**; SQLite `alembic upgrade head` passed.
- Added `backend/app/services/live_order_recovery_service.py`: deterministic opaque 40-character broker tag, durable LIVE intent persistence, idempotency-key replay with exact-payload validation, submission-unknown state persistence, and read-only recovery through Upstox order-history-by-tag.
- Added `backend/tests/test_live_order_recovery_service.py`: stable tag, repeated intent, key/payload mismatch, fail-closed preflight, timeout/no-match no-resubmit, mismatched tag/intent, sliced child-order quantity reconciliation and repeated recovery.
- No `place_order` call is made by the new service. No API route or worker invokes it. Recovery stores broker child IDs only and does not infer order status/fills or change cash, positions, executions or P&L.
- The CI warning is a dependency/runner deprecation warning; test and SQLite migration steps passed. This run does not verify PostgreSQL migration, real broker API behavior, frontend build, or production deployment.
- Code and tests were committed separately: service `4990f28e7b8cfeadca85598abfac8111c8fe7130`; tests `de2e2b7524f09b1be2d4378a9b5ac29bdf26f9e7`.

### Next task
Implement a concrete, testable **account-wide live pre-trade risk gate** and inject it into the preflight path: current positions/exposure, order-value and order-frequency limits, market-session/stale-quote requirements, and broker funds/margin checks with fail-closed behavior. Mock all external calls. Do not add a broker POST, wire any route/worker, merge PR #1, or enable live trading in that task.

### Release status
PR #1 remains draft/open/unmerged. Original `Tradepro` remains untouched. Live trading remains **NOT READY**; no real orders have been submitted.

## Authoritative checkpoint — 18 October 2026: Upstox risk snapshots and official session calendar

### Verified code and tests
- Latest verified code/test SHA: `c683fbd16d114b2a41a80a646fc91ee2d4cf25eb`. GitHub Actions [run #39111682177](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39111682177) succeeded: **315 passed, 1 warning in 25.97s**; SQLite Alembic migration verification passed.
- Added strict read-only parsers in `backend/app/brokers/upstox/risk_snapshot_parsing.py` for full market quotes, open positions, official market holidays, special sessions and NSE timings.
- Added adapter calls for full quote, positions, funds/margin, estimated margin and official calendar endpoints, plus `backend/app/services/upstox_live_risk_snapshot_service.py` to collect and validate snapshots. It includes quotes for broker positions and unresolved live-order instruments, respects Upstox's 500-key quote limit, and contains no order-placement call.
- Added mocked regression coverage for malformed/naive quote timestamps, instrument identity mismatch, duplicate positions, holidays/special sessions, provider failure and the read-only collector. Current CI: 315 passed.
- The collector is not wired into a route, worker or order submission. Live mode remains disabled; no real broker requests or real orders were used in these tests.

### Remaining caveats
- The adapter/parser contract has been verified against mocks, not live Upstox responses. Broker-specific response fields and official calendar behavior need documented API-contract review before staging.
- Snapshot collection uses the currently supplied access token; safe orchestration from the user's encrypted connection into a fresh snapshot bundle and the synchronous risk gate is not yet implemented.
- Full live order status/fill/cancel reconciliation, connection-scoped fill idempotency and live accounting remain incomplete. PostgreSQL migration, exact-head frontend build and staging remain unverified.

### Next task
Implement a separate asynchronous, **preflight-only coordinator** that obtains a valid per-user Upstox token through the existing credential service, collects read-only risk snapshots, injects the snapshot-backed providers into `AccountWideLiveRiskGate`, and then invokes the existing `LiveExecutionService.preflight` contract without submitting or persisting an order. Add mocked tests for wrong user/connection, token expiry/provider failures, stale snapshots and successful preflight. Keep it unregistered: no route/worker, no broker POST, no live-mode enablement.

### Release status
PR #1 remains draft/open/unmerged. Original `Tradepro` remains untouched. Live trading is **NOT READY** and disabled. No real orders have been submitted.

## Authoritative checkpoint — 18 October 2026: reconcile-before-promote coordinator

### Verified code and CI evidence
- Latest verified code/test SHA: `cfa038fe49dfde1c441f77d5c4a12fcb13ba695a`. GitHub Actions [run #39118263100](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39118263100) succeeded.
- Full backend suite: **380 passed, 1 skipped, 1 warning in 27.98s**; SQLite Alembic upgrade passed; PostgreSQL 16 Alembic upgrade passed; PostgreSQL concurrency integration passed (**1 passed in 0.36s**).
- Added unregistered `LiveOrderFillReconciliationCoordinator`. It reconciles every mapped Upstox child order and its durable trade list before promoting any staged fill for that conceptual parent order. If any child fails reconciliation, none of the parent's fills are promoted.
- Multiple fills require distinct timezone-aware exchange timestamps, preventing ambiguous position-accounting order. Promotion stops at the first charge/accounting failure; completed fills are reported and retries remain idempotent.
- Regression tests cover successful chronological promotion, sibling reconciliation failure, missing/duplicate timestamps, and promotion failure. The parent Order remains unchanged; the coordinator contains no order-placement call and is not registered to routes/workers.

### Remaining caveats
- Coordinator tests currently inject fake reconciliation/promotion collaborators; the separate PostgreSQL integration test covers real SQLAlchemy service concurrency with synthetic records, not live Upstox behavior.
- Contract-note references remain caller supplied and not independently authenticated. Frontend build, staging, monitoring, account-level kill switch, broker-error circuit breaker, and complete production live lifecycle remain unverified/incomplete.
- PR #1 remains draft/open/unmerged; original `Tradepro` is untouched; live trading remains disabled and not ready.

### Next task
Add a service-level integration test that composes the **real** `BrokerChildOrderReconciliationService`, `BrokerTradeIngestionService`, `LiveFillPromotionService`, and `LiveFillAccountingService` with a fully mocked read-only Upstox adapter and charge estimator. Verify reconciliation happens before promotion, repeated runs are idempotent, failures leave no accounting rows, and paper cash/positions remain unchanged. Keep all promotion services unregistered; no order submission, PR merge, or live-mode enablement.

### Release status
Live trading is **NOT READY** and disabled. No real orders have been submitted.


## Requirements audit update — 18 October 2026

- **Requirement:** broker-confirmed fills must be reconciled before live accounting, retries must not duplicate executions, and paper/live accounting must remain isolated.
- **Change:** commit `b5783d421f64fcb8e7f1d75f1af5185fd9029f59` adds service-level integration coverage against the real existing reconciliation, ingestion, promotion and accounting services. It does not add a second coordinator or change production runtime wiring.
- **Classification:** tests added; verification **pending CI** at this checkpoint. Do not classify as verified until the workflow for the exact commit succeeds.
- **Remaining caveat:** mocks verify application orchestration and response parsing, not live Upstox behavior or production deployment. No real order submission is tested or authorized.


### Latest test evidence status

The latest test commit is `4d8941f436bed1f61b46c4123a4a7c6d5c6b6f88`, superseding `b5783d421f64fcb8e7f1d75f1af5185fd9029f59`. The test now exercises fresh durable trade insertion through the real ingestion service. CI is still pending/unverified for this exact SHA.

## Superseding verified checkpoint — 18 October 2026: real-service fill reconciliation integration

### Exact verification evidence
- Latest tested code/test SHA: `c779f2543ea1f20efbd8b7dca38a9c2aed201749`.
- GitHub Actions [run #39118955335](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39118955335): **success**. Full suite: **385 passed, 1 skipped, 1 warning in 34.01s**. SQLite migration upgrade passed, PostgreSQL 16 migration upgrade passed, and PostgreSQL concurrency integration passed (**1 passed in 0.35s**).
- This exact-head run verifies the fresh-ingestion integration test refinement from commit `4d8941f436bed1f61b46c4123a4a7c6d5c6b6f88` and fixes for nondeterministic child order assertions and deleted ORM fixture access.
- The real-service integration test now begins with no staged trade rows: mocked Upstox trade reads must be inserted by the real `BrokerTradeIngestionService` before official status reconciliation and promotion. Repeated reconciliation/promotion is idempotent; sibling status failure prevents any fill accounting; charge-estimate failure creates no Execution/LivePosition rows; paper cash/positions and parent Order state remain unchanged.
- PostgreSQL 16 verifies migration compatibility and concurrent charge adjustments/fill promotion. Lock scoping explicitly avoids PostgreSQL's `FOR UPDATE` nullable outer-join error.

### Release status and caveats
- All broker API responses in tests are mocked. No live Upstox API requests or real orders were sent.
- The coordinator, fill promotion and charge-adjustment services remain unregistered in order routes/workers. Live order submission remains disabled.
- Frontend build/staging, real broker contracts, exchange holiday coverage, operational monitoring, account-level kill switch and broker-error circuit breaker remain outstanding. PR #1 remains draft/open/unmerged; original `Tradepro` untouched.

### Next distinct task
Implement and test the **persisted account-level live kill switch and broker-error circuit breaker**: durable state, fail-closed read behavior, reason/timestamp/audit trail, threshold-triggered circuit trips, manual-reset policy and account-wide scope across portfolios. Keep it unregistered from order submission until separately reviewed; do not merge PR #1 or enable live trading.

This checkpoint supersedes prior notes saying CI for `4d8941f436bed1f61b46c4123a4a7c6d5c6b6f88` was pending. The latest verified test SHA is `c779f2543ea1f20efbd8b7dca38a9c2aed201749`.


## Requirement update — partial promotion recovery

- Requirement: a charge/accounting failure after earlier fills have been promoted must stop subsequent processing and allow safe retries without duplicating earlier executions.
- Added test coverage in commit `1a3475c69d3a93ece7bfad22ace4dce52231bfa1`, using the real reconciliation, ingestion, promotion and accounting services with broker reads/charge estimates mocked.
- Status: **pending exact-SHA CI**. Do not mark verified until the workflow for this SHA passes. No production wiring or real broker order was introduced.


## Requirement — durable account-wide kill switch and broker circuit breaker

- Implemented service logic in `backend/app/services/live_account_safety_service.py`, durable schema in migration `202610180009`, and tests in `backend/tests/test_live_account_safety_service.py`.
- Expected contract: absent/stale/unknown safety state blocks; new state is latched off; threshold of consecutive broker errors opens the circuit and trips the kill switch; repeated idempotency keys do not double-count; successful broker calls do not auto-close the circuit; manual reset requires a fresh passing health check, zero error count, explicit actor and reason.
- Status: implementation committed, **verification pending** on head `57939799b7e8b436d5095924b86a89ce380a956e`. Await backend pytest and SQLite/PostgreSQL migration CI; PostgreSQL concurrency coverage remains a follow-up.
- Not wired into order submission and does not authorize live trading.


### Reset gate test refinement

Latest test code SHA: `c97be866828bd47a23f22fc44fac2d3359e70f35`. The test now isolates the broker-error counter reset condition by recording a passing health check while the counter is still nonzero, then clearing the counter via broker success and recording another passing health check before manual reset. CI/migration verification remains pending.

## Superseding verified checkpoint — 18 October 2026: account-safety PostgreSQL concurrency

- Code/test target SHA: [872eab69082b231117184d80b1bb4a7a96c15b6b](https://github.com/tarunsharma2610-del/tradepro-improved/commit/872eab69082b231117184d80b1bb4a7a96c15b6b). This includes the PostgreSQL account-safety concurrency tests and the workflow change that runs them alongside the existing charge-adjustment concurrency test.
- GitHub Actions [run #608](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39120699215): **success**. Full backend suite: **395 passed, 4 skipped, 1 warning in 29.36s**. SQLite Alembic upgrade passed. PostgreSQL 16 Alembic upgrade passed. Dedicated PostgreSQL integration: **4 passed in 0.44s**.
- PostgreSQL safety coverage now proves: two concurrent submissions with the same broker-error idempotency key count once; two distinct concurrent broker errors serialize and trip the circuit exactly at the configured threshold; concurrent manual resets permit only one reset and preserve the audit trail.
- Migration issue resolved: removed duplicate revision 202610180009_live_account_safety.py; canonical safety migration is 202610180010_live_account_safety.py, chained after 202610180009_live_charge_adjustment_ledger.py. The prior duplicate-revision failure is superseded by successful run #606 and then run #608.
- The account safety service remains unregistered from order submission. These tests use a real PostgreSQL test database and synthetic test users only; no live broker API or order-write endpoint was called. PR #1 remains draft/open/unmerged; original Tradepro remains untouched.
- **Next task:** add read-only preflight composition coverage using the existing LivePreflightCoordinator, AccountWideLiveRiskGate, and persisted LiveAccountSafetyService decision. Fail closed on any denial/error; do not register the composition with order routes/workers or enable live order submission.

## Superseding verified checkpoint — 18 October 2026: safety-aware read-only preflight composition

- Code/test target SHA: [3e73efd441315294970cb652ddeb9b37b00b67b9](https://github.com/tarunsharma2610-del/tradepro-improved/commit/3e73efd441315294970cb652ddeb9b37b00b67b9). The coordinator change is in commit [866336676b24b0da34fe833263b0f2c33204bf17](https://github.com/tarunsharma2610-del/tradepro-improved/commit/866336676b24b0da34fe833263b0f2c33204bf17).
- GitHub Actions [run #611](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39121063921): **success**. Full backend suite: **398 passed, 4 skipped, 1 warning in 29.51s**. SQLite Alembic upgrade passed; PostgreSQL 16 Alembic upgrade passed; PostgreSQL integration passed (**4 passed in 0.41s**).
- LivePreflightCoordinator now checks the persisted account-wide LiveAccountSafetyService decision after local intent/ownership validation and before credentials or any broker snapshot. Missing safety state, a tripped latch/open circuit, stale health or an unexpected safety-check exception blocks preflight. The service is injectable for testing; default construction uses the same preflight clock.
- Regression tests prove missing state, a tripped latch, and an unexpected safety-check exception all block before any read-only broker call. Existing successful preflight tests explicitly establish a passing health check and manual reset in the test fixture.
- This is read-only preflight composition only. LivePreflightCoordinator remains unregistered from order routes/workers, no broker order-write method is called, live trading remains disabled, PR #1 stays draft/open/unmerged, and the original Tradepro repository remains untouched.
- **Next task:** audit authentication/authorization and operator audit visibility for any future safety-control endpoint. Do not create or wire a control route until that review is complete; keep live order submission disabled.


## Security and operator-audit requirements — 18 October 2026

New review: [SECURITY_CONTROL_ENDPOINT_AUDIT.md](SECURITY_CONTROL_ENDPOINT_AUDIT.md), commit [10d87d9d9010b2c48ebcf25c832a2ea574100889](https://github.com/tarunsharma2610-del/tradepro-improved/commit/10d87d9d9010b2c48ebcf25c832a2ea574100889).

- [x] Inspect existing auth/JWT dependency, admin guard, MFA routes, audit model/helper, API router and relevant route tests.
- [x] Identify current protections and missing operator audit visibility.
- [ ] Define least-privilege safety permissions and cross-account query boundaries.
- [ ] Define step-up authentication and CSRF/origin controls for privileged mutations.
- [ ] Define atomic safety-state + audit-event persistence, append-only enforcement and strict redacted event schema.
- [ ] Add HTTP-level negative, replay, audit-failure and concurrent-reset tests after API design approval.
- [ ] Audit all manual, strategy, worker, retry/recovery and broker-write entry points before live safety wiring.

No endpoint or live execution wiring was added in this audit step. Production/security sign-off remains open.


## Order-entry path inventory requirements — 18 October 2026

See [ORDER_ENTRY_PATH_INVENTORY.md](ORDER_ENTRY_PATH_INVENTORY.md), commit [a477489c7e2d5b6883c299c1e9a8aee1cbef055f](https://github.com/tarunsharma2610-del/tradepro-improved/commit/a477489c7e2d5b6883c299c1e9a8aee1cbef055f).

- [x] Inventory manual order/cancel route, strategy immediate-evaluation route, scheduled worker, paper execution service and adapter write primitives.
- [x] Record that current order service rejects LIVE/unknown modes and is PAPER-only.
- [x] Record the LiveOrderRecoveryService composition gap: it uses LiveExecutionService, not LivePreflightCoordinator.
- [ ] Implement one reviewed central broker-write service as the only caller of adapter place/modify/cancel methods.
- [ ] Add source-call guardrails and fail-closed tests for every route/worker/strategy entry point.
- [ ] Resolve auth/operator-audit design findings and atomic state/audit persistence before creating safety-control routes.
- [ ] Verify all order paths in CI and explicit broker sandbox tests before any live-enable decision.


## Requirements checkpoint — central write and operator safety controls (18 October 2026)

Design requirements are consolidated in `CENTRAL_BROKER_WRITE_BOUNDARY_DESIGN.md`. New explicit gates: only one production broker-write service; no unapproved direct adapter calls (CI-enforced); account-wide safety/risk/freshness checks for submit/modify; narrowly defined risk-reducing cancellation semantics; durable intent+event before external I/O; no blind retry on ambiguous broker outcomes; least-privilege scopes; server-derived actor; recent MFA step-up for reset; CSRF/Origin controls; tenant-scoped paginated audit reads; strict redaction; PostgreSQL append-only protection; and service/API/worker/PostgreSQL concurrency tests.

Status is **design specified, implementation pending**. Do not treat the requirements as satisfied. Live submission stays disabled.


### CI guard verification — 18 October 2026

The source-call guard requirement now has a CI implementation and a passing verification on code SHA `bdf208efcc32b44a6367157dd2ab0aab946e6574`, run #617: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39123311281. Backend suite 402 passed / 4 skipped; migrations and PostgreSQL concurrency checks passed. Mark only the guardrail requirement as verified; central writer, safety permissions/API, atomic event semantics, DB-enforced immutability and end-to-end enforcement remain pending.


## Safety audit storage requirement checkpoint — 18 October 2026

Partially implemented: request fingerprint and idempotency mismatch rejection; unique state-version audit sequence; DB triggers rejecting UPDATE/DELETE in SQLite and PostgreSQL; transaction rollback test when audit insertion fails; PostgreSQL trigger tests; and stale expected-version validation for manual reset.

Still pending: exact-head CI green confirmation; operational restrictions against privileged trigger removal; endpoint-level mandatory expected-version enforcement; authorization/MFA/CSRF; and central broker-write integration. The latest CI run `39124312326` was pending when this note was written, so do not mark all storage requirements verified yet.


### Storage-hardening verification update

The exact-head CI run #39124312326 failed one stale-version test due to a mutable ORM fixture reference; the test was corrected in commit `6cd0ced108e35d715359d649a463d80709dd1fb1`. Run #39124498280 is pending, so database immutability and the final test matrix are not yet marked fully verified.


### Storage verification superseding pending status — 18 October 2026

The storage hardening changes passed CI run #625 on SHA `6cd0ced108e35d715359d649a463d80709dd1fb1`: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39124498280. Backend tests 406 passed / 5 skipped; SQLite and PostgreSQL migrations passed; five PostgreSQL integration tests passed including append-only enforcement. Mark only these storage/transaction controls verified. Authorization, MFA, CSRF, safety endpoints, central writer and end-to-end composition remain open.


## 18 October 2026 — safety authorization foundation (partial; CI pending)

- Implemented the safety_permissions user grant field with default-empty migration, allowlisted permission dependency, malformed JWT subject 401 normalization, and a reusable cookie-Origin mutation dependency.
- Added tests for explicit grant enforcement, no implicit is_admin grant, invalid permission names, malformed signed subject, and Origin policy.
- Open: recent-MFA step-up, trusted grant management, wiring guards into safety endpoints, tenant-scoped safety/audit queries, endpoint-level negative HTTP matrix, and CI verification for these commits. No safety route was registered.

### Follow-up correction — 18 October 2026

The Origin guard now requires an exact Origin serialization match (including rejecting a trailing slash), and unused imports were removed from the user model. Follow-up commits: f7c08e2605fb7f7828792154570af79cf5ccf724 and 4337d0ce4ef645914f32c56db87c81699c04763e. CI/status lookup has returned no run/status for the authorization changes; do not claim tests or migration passed until a workflow result is tied to the code/test SHA. Recent-MFA step-up and route wiring remain outstanding.

## Superseding checkpoint — recent-MFA step-up foundation (18 October 2026)

- Added a dedicated `POST /api/v1/auth/mfa/step-up` challenge. It requires an authenticated active user, MFA already enabled, fresh password verification and a valid TOTP code; it is rate-limited and applies the configured same-origin guard to cookie-authenticated requests. Successful challenges return a purpose-bound `step_up` JWT with `scope=safety.reset`, `amr=[pwd,totp]`, a verification timestamp, and a five-minute expiry. Failed credentials are audited without logging credentials or the token.
- Added `require_recent_safety_mfa`, which requires the separate `X-Safety-Step-Up` header, validates token type and purpose, verifies recent MFA and issuance timestamps, and binds the token to the authenticated user. It is not yet attached to a safety reset route because no safety-control routes have been exposed.
- Added unit/dependency tests for missing/wrong-scope/stale/user-mismatched step-up tokens and HTTP tests for success, invalid password and accounts without MFA. These tests are committed but **not yet verified by a GitHub Actions run for the latest code/test SHA**; do not claim they pass until exact-head CI is green.
- Latest code/test commit for this checkpoint: `ee8968f9d7d8698703e59911c7091d5f7c870c23`. Related commits: `325d9a854c05bb7dead6f6f626bf749383804a8e`, `9b65f92b060c0745c1e84e535ec5397cdf490b5d`, `1450a3d0dd8c3629e72142fe06cec699be7202f0`, `0bf5f86d9dd07ecaebe10b93149841647dfbccdf`, `1afd892fb1fa7aaf6c1b0028c248b59e06ec9994`, `aaad1d020cb629cb6d554bd08ff02d25fb1c4666`, and `ee8968f9d7d8698703e59911c7091d5f7c870c23`.
- Remaining authorization gates: trusted safety-permission provisioning, tenant-scoped/paginated audit reads, route-level permission + Origin + step-up enforcement, comprehensive negative HTTP tests, and latest-head CI. The helper does not solve these by itself. The safety status/audit/trip/reset routes and central broker-write service remain absent/unwired.
- Keep PR #1 draft/open/unmerged, keep `TRADING_MODE=PAPER` and `LIVE_ORDER_SUBMISSION_ENABLED=false`, never call broker order-write endpoints, and leave the original `Tradepro` repository untouched. Phase 2 remains incomplete.

### Superseding MFA guard correction

The step-up verifier now also denies a token if the authenticated user's MFA has since been disabled; regression coverage was added. Latest code/test commit: `ecf09e800c0dc7fc83d200d603f510348433aa58` (guard change `8a46241e766b9504c3a9bc3ba182043bac98a75d`). Exact-head GitHub Actions/status remains unverified; prior CI results do not cover this change. This remains a foundation only: the dependency is not wired to a safety-reset endpoint because those endpoints do not yet exist.

## Superseding checkpoint — audited safety-permission provisioning (18 October 2026)

- Added `PUT /api/v1/admin/users/{user_id}/safety-permissions` for one explicit grant/revoke operation at a time. The request schema only accepts the four defined `safety.*` scopes; arbitrary scopes are rejected by validation.
- The actor must be a platform admin, must pass the five-minute user-bound password+TOTP step-up, and cookie-authenticated mutations must pass the configured Origin guard. `is_admin` alone is not enough. Self-grants are rejected; revocation remains allowed for an admin's own account to support removal of access.
- Target user's permission list and the audit record (`safety.permission.grant/revoke`, actor ID, target ID and scope) are committed in the same DB transaction. The route does not grant access to read other users' audit data and does not expose the safety status/audit/trip/reset endpoints.
- Added HTTP regression tests for missing step-up denial, self-grant denial, and grant/revoke behavior with audit evidence. **These tests have not been executed in this environment and exact-head CI has not been confirmed.** Treat them as committed, unverified tests, not passing tests.
- Relevant commits: endpoint `ed1cae900a326a4922dbf42a5dbe2b7ed9d50d13`; constrained schema `8a50e8176d25e26a58f52649b21ab01cafa60cad`; test additions `b1b326e7ff409b84d2feab438f69275678939d2f`; formatting follow-up `1d464907a2aec9d0a4e257cb960bf32b24d032ee`.
- Remaining gates: CI on latest code/test SHA, independent review of the permission-provisioning threat model, tenant-scoped audit reads, safety status/audit/trip/reset routes with explicit permission enforcement, state/event atomicity at endpoint level, central broker-write service and end-to-end path enforcement.
- Continue to keep PR #1 draft/open/unmerged and keep live order submission disabled. Phase 2 is incomplete; original `Tradepro` remains untouched.

### Follow-up correction and verification checkpoint (18 October 2026)

- Corrected the safety-permission endpoint import formatting and cleaned test imports after reviewing the committed source through GitHub. Latest test-file commit: `ae46db76e86ea28116bcaf80b9a02c64eb713e9b`; endpoint import correction: `3ef5d32ddeb97ffbd43c61acb74945dd4f564729`.
- The repository connector did not expose a local test runner, and GitHub Actions/combined-status lookups returned no run/status for the latest code/test SHA. Tests remain **unexecuted/unverified**; the older CI run is not evidence for these changes. The next action must be to get CI running on the current branch head and resolve any failures before adding further security-sensitive behavior.
- Phase 2 remains incomplete. Keep PR #1 draft/open/unmerged, preserve PAPER-only defaults and live-order submission disabled, and leave the original `Tradepro` repository untouched.

## Phase 2 checkpoint — tenant-scoped safety audit read (18 October 2026)

- Added `GET /api/v1/admin/safety/audit`, protected by the explicit `safety.audit.read` permission. It accepts bounded pagination (`limit=1..100`, `offset=0..100000`), returns a page envelope and uses a stable `created_at DESC, id DESC` order.
- The SQL query scopes rows to `AuditLog.user_id == authenticated_user.id` and `action LIKE 'safety.%'` before counting or pagination. The caller cannot provide a target user ID; unrelated audit actions and other users' events are not returned. This is an actor-scoped view of safety events, not an administrator-wide or target-account audit browser.
- Added HTTP regression tests for permission denial, pagination bounds, and tenant isolation / filtering. **The tests are committed but have not been executed locally; exact-head GitHub Actions status has not been confirmed.** Do not call the feature CI-verified yet.
- Relevant commits: endpoint `d608f4fdd8a9f10b0647fbe4083d35809b27061f`; response schemas `d46c9268c7c05ca9e207898ca80674df56883a03`; tenant isolation tests `eda5a3589765211105457e2b8950d0c20f00f011`; follow-up import/test cleanup `584b774e175b1aecd74784286bd5fca566e1be6d`.
- Remaining Phase 2 work: run/fix CI on the latest branch head; implement persistent safety status and kill-switch trip/reset routes with the correct permission, Origin and MFA gates; decide and document operator-vs-account audit visibility before expanding audit scope; ensure atomic state/event transactions and concurrency semantics; implement the central broker-write service and enforce it across every execution path. Live trading remains disabled and PR #1 remains draft/open/unmerged.

## Phase 2 checkpoint — authenticated safety control endpoints (18 October 2026)

- Added and registered `backend/app/api/v1/safety.py` with three user-scoped endpoints: `GET /api/v1/safety/status` requires `safety.status.read`; `POST /api/v1/safety/kill-switch/trip` requires `safety.kill_switch.trip`, cookie-Origin validation and an `Idempotency-Key`; `POST /api/v1/safety/kill-switch/reset` requires `safety.reset`, a fresh user-bound password+TOTP step-up token, cookie-Origin validation, an idempotency key, and a required `expected_version`.
- Status reads only the authenticated user's Upstox account safety state. Missing state is reported as blocked/unsafe without initializing or creating a state. Trip initializes missing state in the safe/tripped state before applying the idempotent trip. Reset delegates to the existing transaction-safe service and returns conflict if state/version/health requirements are not met.
- Reset deliberately does **not** accept a client assertion that a health check passed. The existing service requires a recent persisted `HEALTH_CHECK_PASSED` event, zero consecutive broker errors, and matching expected state version. No new public health-check endpoint was added because a caller-supplied “passed” flag would be unsafe without real broker/session/account snapshot validation.
- Added HTTP regression tests for permission denial, safe missing-state response, trip behavior, required idempotency key, reset MFA denial, reset blocked without a fresh successful health check, and cookie-Origin rejection. **These tests have not been executed in this environment.** GitHub Actions lookup exposed no PR-triggered run for the latest test commit and combined status was empty; the connector's workflow-run lookup filters to PR-triggered runs, so this is not proof that no push-triggered run exists. Exact-head test status remains unverified.
- Relevant commits: safety route/import cleanup `267da864b5187cfad91ac68b76ba86cf06b7848f`; schema `01f0deb4949cd13072fb2feda9924e0a97eaf5cf`; router registration `fc95e748197be9e8848c990f55079fbd8afc4a30`; endpoint tests `3ae21dac71edb449835124f99794f510c8b80761`.
- Review caveat: the existing `GET /api/v1/admin/safety/audit` still reads legacy `AuditLog` rows with `safety.*` action names; the durable state-transition history is in `LiveAccountSafetyEvent`. Before treating operator audit visibility as complete, update that endpoint to read the immutable event table and scope by the associated state owner and authorized actor.
- Remaining gates: run and fix CI on the current branch head; fix the safety audit endpoint's event source; perform security review of the grant/reset token purpose boundaries; add negative HTTP tests for every route and error path; verify atomic state/event concurrency at endpoint level; implement the central broker-write service and enforce it across API, strategy worker, recovery and adapter paths. Keep `TRADING_MODE=PAPER`, `LIVE_ORDER_SUBMISSION_ENABLED=false`, PR #1 draft/open/unmerged, and original `Tradepro` untouched. Phase 2 is incomplete.


## Superseding Phase 2 checkpoint — immutable safety audit source (18 October 2026)

- Updated `GET /api/v1/admin/safety/audit` to read `LiveAccountSafetyEvent` joined to `LiveAccountSafetyState`, rather than the legacy `AuditLog` table. Tenant scoping is performed in SQL using the authenticated user's state ownership before counting and pagination; callers cannot select another user/state. Output omits idempotency keys and request fingerprints and exposes only the safety event fields needed for audit review.
- Reworked the tenant-isolation/pagination HTTP test to seed durable safety events for two different account owners and a non-safety legacy audit row. It checks that only the authenticated tenant's immutable safety events are returned and sensitive replay metadata is not serialized.
- Commits: endpoint `cd68384c48a98f2bd2ded054f37bb04d24885b12`; regression test `7913f821a7ac194c537adf911a4ef39ba4410e41`.
- Verification status: exact-head CI/status lookup returned no runs/statuses for the latest test commit. Tests have **not** been run in this environment; treat this change as committed but unverified until GitHub Actions runs against the current branch head. No live broker write was called.
- Next: verify/fix current-head CI; then review reset/idempotency and endpoint transaction behavior, followed by central broker-write boundary implementation and enforcement across API, strategy workers, recovery/retry and adapter paths. Phase 2 remains incomplete. Keep PAPER mode, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.


## Authorization/MFA route-matrix verification checkpoint — 18 October 2026

- During matrix review, identified a compatibility defect in the first scoped-MFA dependency refactor: existing direct unit tests and callers invoke `require_recent_safety_mfa(step_up_token=..., user=...)`, so turning that function itself into a factory would break those calls. Corrected by restoring `require_recent_safety_mfa` as the default `safety.reset` validator and adding `require_recent_safety_mfa_scope(scope)` for FastAPI route dependencies. Reset and admin permission routes now explicitly use their corresponding scope-specific dependency.
- Added route-level regression coverage proving a `safety.reset` token cannot grant safety permissions; existing coverage includes non-admin privilege denial, direct cross-purpose rejection, stale tokens, disabled MFA, wrong user/scope, Origin checks, default-deny permissions, tenant isolation, idempotency-header validation, and safe reset requiring fresh health evidence.
- Relevant commits: dependency compatibility fix `24b463894eca1fde37381bef66d47366a806fe32`; route wiring `0cfc3e290dbc730af9fb854954a95875809ad3cf` and `17088f172d40aa106d1cd1d5f8b674c056919a86`; test matrix update `6e77aa77a7c0bba84d2aae539b37fa6228c088b9`; route-level cross-purpose test `c40edddbeb8b65ec468ae0419897d1cd6cc2c325`.
- CI: GitHub Actions backend workflow is running for the preceding dependency/test commit (`39132630566`) and queued for latest route-level test commit (`39132698515`). The preceding run has not yet reached pytest; do not mark the matrix passed until latest-head workflow concludes. Monitor [latest workflow run](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39132698515).
- Still outstanding: wait for latest-head CI; fix any failures and re-run; verify SQLite/PostgreSQL migrations and concurrency checks. This is a route-matrix review, not a complete authorization/security certification. PAPER mode remains mandatory, live broker order submission remains disabled, PR #1 remains draft/open/unmerged, and Phase 2 is incomplete.


## CI failure triage update — 18 October 2026

- GitHub Actions run `39132630566` failed at `Run test suite`: `433 passed, 5 skipped, 1 failed`. The single failure was `test_non_admin_cannot_request_permission_management_step_up`, which returned 401 rather than the expected 403 because its test fixture enabled MFA but did not mock TOTP verification. The authorization code was not reached by that test.
- Fixed the test fixture to mock a valid `123456` TOTP code, isolating the authorization behavior under test. Fix commit: `b5c96fc5115bd4b9fae7be6fc0a168d55c5ace9c`.
- A new backend CI run is in progress for the fix: [run 39132803282](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39132803282). Do not consider the suite green until this exact-head run finishes successfully. Previous failures skipped migrations/concurrency stages because pytest failed first.


## CI verification result — PASS (18 October 2026)

- Backend workflow run `39132803282` passed for backend commit `b5c96fc5115bd4b9fae7be6fc0a168d55c5ace9c`: broker-write boundary guard passed; full backend suite **435 passed, 5 skipped, 1 warning**; SQLite Alembic upgrade passed; PostgreSQL 16 Alembic upgrade passed; PostgreSQL account-safety/charge-adjustment concurrency tests **5 passed**. One Starlette/AnyIO deprecation warning remains non-blocking.
- The earlier failing test was corrected by mocking valid TOTP in the non-admin purpose-denial test; the passing run confirms the corrected test setup and current backend changes. Documentation-only commits followed, so the tested application code is unchanged, but the docs commit itself did not trigger backend CI due workflow path filters.
- This is evidence for the current authorization/MFA test changes and listed CI gates, not a complete security certification or Phase 2 completion. Continue with broader authorization route matrix and broker-write boundary implementation; live order submission remains disabled and PAPER mode remains mandatory.


## MFA HTTP route-matrix follow-up — 18 October 2026

- Added two missing HTTP-level cases to `backend/tests/test_api_authorization.py`: cookie-authenticated `POST /api/v1/auth/mfa/step-up` without an Origin header must return 403; unsupported step-up purpose `safety.live_trade` must be rejected by request validation with 422. These complement existing tests for missing/disabled MFA, wrong password, non-admin privileged-purpose denial, reset-vs-admin token scope separation, stale/user-bound tokens, cross-origin mutations, permission denial, and reset health prerequisites.
- Test commit: `58778259324119379c69b03c822c13849b223d22`. GitHub Actions run [#39133596645](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39133596645) is running; broker-write boundary guard has passed and pytest is in progress at time of this note. Do not claim the new tests pass until the run completes and its pytest/migration/PostgreSQL steps conclude successfully.
- Review outcome so far: reset and permission-management routes explicitly use distinct MFA scopes; platform-admin status alone does not grant safety permissions; user audit is tenant-scoped to immutable safety events. The matrix is broader but not exhaustive, and no independent security certification is implied.
- Next after CI: fix only demonstrated failures; if green, proceed to the central broker-write authorization/gating design and enumerate every order-write path before wiring anything. Keep PAPER mode, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.


## MFA HTTP route-matrix CI result — PASS (18 October 2026)

- GitHub Actions [run #39133596645](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39133596645) passed for test commit `58778259324119379c69b03c822c13849b223d22`: broker-write boundary guard passed; backend suite **437 passed, 5 skipped, 1 warning in 28.01s**; SQLite Alembic migration passed; PostgreSQL 16 Alembic migration passed; PostgreSQL safety/charge-adjustment concurrency tests **5 passed**.
- This run verifies the added missing-Origin and unsupported-purpose HTTP tests plus the existing MFA/authorization matrix at that tested code SHA. Later documentation-only commits did not alter application code. One non-blocking Starlette/AnyIO deprecation warning remains.
- This does not certify every auth route or complete Phase 2. Next task: map all broker order-write entry points and design a single fail-closed broker-write authorization gate, then test that all paths are blocked in PAPER mode and remain disabled absent explicit future approval. Do not wire real order submission in this task. Keep PR #1 open/unmerged and original `Tradepro` untouched.


## Central broker-write boundary — deny-all foundation (18 October 2026)

- Added `backend/app/services/live_broker_write_service.py` as the single planned choke point for place/modify/cancel operations. This is intentionally a deny-all foundation: every write method raises `LiveExecutionBlocked` with an explicit no-request-sent message. It does not import or call a broker adapter, and it is not registered with routes, strategy workers, recovery, or any execution path.
- Added `backend/tests/test_live_broker_write_service.py` covering all three write verbs and asserting each fails closed. Commits: service `3726484932e4d46d9f92a7ff41cb5b761cfb1720`; tests `f4442607b8b71df7fffbf4354ea11a532efb99d6`.
- Verification pending at this note: the backend workflow for test commit `f4442607b8b71df7fffbf4354ea11a532efb99d6` has passed the broker-write source guard and is in pytest. See [run #39134040222](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39134040222). Do not claim tests/migrations passed until the run concludes.
- This does **not** complete the broker-write service. Next design must enumerate the persisted-intent lifecycle, ownership, user confirmation, account safety state, fresh pre-trade risk, token/connection stability, and timeout/recovery behavior before any adapter call can be implemented. Do not wire it or enable live orders. PAPER mode, disabled live submission, PR #1 draft/open/unmerged, and original `Tradepro` untouched remain mandatory.


## Central broker-write deny-all CI result — PASS (18 October 2026)

- GitHub Actions [run #39134040222](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39134040222) passed for test commit `f4442607b8b71df7fffbf4354ea11a532efb99d6`: broker-write source guard passed; full backend suite **440 passed, 5 skipped, 1 warning in 32.49s**; SQLite Alembic upgrade passed; PostgreSQL 16 Alembic upgrade passed; PostgreSQL safety/charge-adjustment concurrency tests **5 passed**. A separate workflow for the service-only commit also passed.
- The deny-all broker-write service remains deliberately unwired and makes no adapter calls. This step proves the central choke-point stub refuses place/modify/cancel; it does not verify live submission (which remains disabled) and is not a complete broker-write implementation.
- Documentation-only checkpoint commits followed. Next: inspect every existing order-writing entry point and add a call-graph/inventory, then design the central gate around ownership, persisted intent/idempotency, account-level safety latch, live pre-trade risk, explicit confirmation, and ambiguous timeout recovery. Keep PAPER mode, live submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.


## Broker-write path inventory and guard hardening — 18 October 2026

- Added `BROKER_WRITE_PATH_INVENTORY.md` documenting current adapter definitions, PAPER execution routes, read-only live preflight/recovery/reconciliation, and controls required before any live write is implemented. Commit `68f528edf4fe2dcb958161943b878b5863bbcd74`.
- Strengthened `backend/scripts/check_broker_write_boundary.py` to reject broker-write method references regardless of receiver name, rather than relying on adapter-like variable names. It now permits only the known PAPER `self.execution.place_order` calls in `strategy_execution_service.py` and the existing `ExecutionService(...).place_order/cancel_order` endpoints in `api/v1/portfolios.py`. The first strict run correctly exposed those two existing PAPER API call sites as exceptions that needed explicit, narrowly-scoped allowlisting; no live adapter write path was identified in those failures.
- Added guard tests for generic receiver bypass, central-service adapter-call rejection, and the approved PAPER call sites. Test updates are committed through `e9c31a043465e3d09223894ddfe45629cfc0302e`.
- CI for the latest guard/test fix is in progress: [run #39134878791](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39134878791). Do not treat this guard hardening as verified until the exact-head workflow passes. The preceding strict-guard failures were expected detection/allowlist gaps and prevented pytest/migration stages from running.
- Live broker writes remain unimplemented and denied by the central service. Keep PAPER mode mandatory, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.

## Central safety-preflight + durable intent composition — VERIFIED (18 October 2026)

- Added LiveOrderRecoveryService.persist_preflighted_intent(...). It accepts only a LiveOrderPreflight plan, verifies user/portfolio/instrument/broker and exact intent fields, rechecks the currently connected Upstox connection ID, then persists one stable PENDING_SUBMISSION LIVE intent with an opaque broker tag and portfolio-scoped idempotency key. It does not call a broker order endpoint.
- Updated LiveBrokerWriteService to expose prepare_order_intent(...): run LivePreflightCoordinator.preflight first (environment interlocks, explicit confirmation, ownership/instrument validation, persisted account safety latch, fresh read-only broker risk snapshots and account-wide risk gate), then persist the plan. If preflight fails, persistence is not attempted.
- Place/modify/cancel methods remain unconditional deny-all; this service does not send real orders and is not registered with routes/workers. PAPER-only ExecutionService is unchanged.
- Added tests for preflight-before-persistence, no persistence on denied preflight, exact plan matching, idempotent intent replay, and broker connection change after preflight.
- Verified GitHub Actions run #39136080295 on code/test SHA 27c4a4e5ed9fd9d864e38816c945e37371ee22f7: broker-write source guard passed; backend 448 passed, 5 skipped, 1 warning in 39.34s; SQLite migration upgrade passed; PostgreSQL 16 migration upgrade passed; PostgreSQL safety/charge-adjustment concurrency tests 5 passed.
- Code commits: recovery persistence 66675d34bee98cdc6c0f24388f4fb097e79348ac; central composition 4d8268ca86e08a36025182a8e46f43b18ba951e6; orchestration tests ab010e8106b02b182594c0a664df34647a234bdb; persistence tests 27c4a4e5ed9fd9d864e38816c945e37371ee22f7.
- Remaining: review persisted intent status transitions and duplicate/concurrent races, require account safety to be rechecked at any future submission boundary, and design broker-confirmed submission/recovery with ambiguous outcomes. No submit method is approved. Keep PAPER mode, live submission disabled, PR #1 draft/open/unmerged, and original Tradepro untouched.

## Post-preflight instrument revalidation — VERIFIED (18 October 2026)

- Hardened persist_preflighted_intent to re-read the instrument row after asynchronous broker snapshots and reject missing/inactive instruments or any instrument-key change since the preflight plan was produced. This closes the same time-of-check/time-of-use gap already covered for broker-connection identity.
- Added regression test mutating the instrument key after snapshot-plan creation; persistence is rejected and no LIVE Order row is created.
- GitHub Actions [run #39136563051](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39136563051) passed on code/test SHA c40689ac227ab56ca58993072112d6fd575aff46: broker-write source guard passed; backend **449 passed, 5 skipped, 1 warning in 32.68s**; SQLite and PostgreSQL 16 migrations passed; PostgreSQL safety/charge-adjustment concurrency tests **5 passed**.
- Next: add concurrency/state-transition tests around persisted intent creation and submission-unknown marking. Any future submitter must recheck the account safety latch and independent interlocks immediately before network I/O. Actual place/modify/cancel remain denied and no live broker order request is enabled.

## Concurrent order-intent and submission-state checkpoint — VERIFIED (18 October 2026)

- Changed `LiveOrderRecoveryService.mark_submission_unknown` to use a SQL compare-and-set update restricted to tagged LIVE intents in `PENDING_SUBMISSION` or `SUBMISSION_UNKNOWN`. It reloads after commit and refuses to overwrite a concurrently written terminal/reconciled state. Repeated transition to `SUBMISSION_UNKNOWN` is idempotent.
- Added unit coverage for repeated `SUBMISSION_UNKNOWN` and refusal to transition a terminal `FILLED` order back into recovery.
- Added PostgreSQL independent-session concurrency tests for two simultaneous identical intent-persistence requests (exactly one durable Order row and shared ID) and two simultaneous `SUBMISSION_UNKNOWN` transitions (both return the same safe state). Updated `.github/workflows/backend-tests.yml` to actually execute `test_live_order_recovery_postgres.py`; this integration coverage was not included by the prior workflow.
- Verified GitHub Actions [run #39137705194](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39137705194), SHA `3626e0cdb8a5b7b3fe012fd00b07d2b7bc3bbe26`: broker-write source guard passed; backend **450 passed, 7 skipped, 1 warning**; SQLite and PostgreSQL 16 migrations passed; PostgreSQL integration tests **7 passed** (including the two new order-recovery concurrency cases).
- Recovery lifecycle review: timeout, lookup failure, invalid response, no match, and identity mismatch remain review-required outcomes; the service never blindly retries a broker POST. Recovered broker IDs are identity mapping only and do not imply fill/accounting confirmation.
- Remaining: production-grade submit/modify/cancel remains intentionally unimplemented and denied. Before any future broker POST, implement a separately reviewed submission state machine that commits a unique submission claim, rechecks account safety and independent interlocks immediately before I/O, handles crash/timeout ambiguity via read-only recovery, and requires broker-confirmed state reconciliation. Keep PAPER mode mandatory, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.

## Submission-claim state separation — VERIFIED (18 October 2026)

- Added `SUBMISSION_CLAIMED` as a distinct, durable state before any future broker network I/O. `claim_submission_attempt` uses a SQL compare-and-set from `PENDING_SUBMISSION`; only one concurrent worker can win. This is a local database operation only and contains no broker write call.
- Read-only tag recovery now accepts `SUBMISSION_CLAIMED` as well as pending/unknown states, because a process crash after committing a claim cannot prove whether a request was sent. The recovery rule remains conservative: no-match, lookup error, malformed response or identity mismatch never authorizes an automatic resubmit.
- Added unit tests for one-time claim semantics and a PostgreSQL independent-session concurrency test requiring exactly one winner. Existing concurrent duplicate-intent and `SUBMISSION_UNKNOWN` transition tests remain enabled in the PostgreSQL CI step.
- Verified GitHub Actions [run #39138626298](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39138626298), SHA `b18841ff591eb943c25d3f85894d824923f2f371`: broker-write source guard passed; backend **451 passed, 8 skipped, 1 warning**; SQLite and PostgreSQL 16 migrations passed; PostgreSQL integration tests **8 passed**.
- Safety boundary: this is state-machine groundwork only. No adapter place/modify/cancel call was added, no live submission route or worker was enabled, and no real order was sent. Before any future submitter is considered, require a dedicated reviewed protocol that rechecks the account safety latch and independent interlocks immediately before I/O, handles claim-crash ambiguity via read-only recovery, and only accepts broker-confirmed reconciliation. Keep PAPER mode mandatory, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.

## Broker-account binding for recovery — VERIFIED (18 October 2026)

- Added nullable `orders.broker_connection_id` with FK/index and Alembic revision `202610180013`. New live intents persist the exact broker connection ID validated by preflight. Legacy rows are intentionally not backfilled because the currently connected account cannot prove which account was used originally.
- Read-only recovery now fails closed before calling order history if the original connection is missing, disconnected, or differs from the currently verified connection. Existing child mappings are reused only when connection ID, broker name, and stable tag match the persisted intent.
- Added regression tests proving a disconnected/original-connection mismatch and a legacy unbound intent produce `UNKNOWN_REQUIRES_REVIEW`, make no order-history call, create no child mapping, and never invoke a broker write. Migration runs are verified on SQLite and PostgreSQL 16.
- Verified GitHub Actions [run #39139728102](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39139728102), SHA `9cb7ab055a0cd55028f0001aa90d647f1518b667`: broker-write source guard passed; backend **453 passed, 8 skipped, 1 warning**; SQLite and PostgreSQL 16 migrations passed; PostgreSQL integration tests **8 passed**.
- Remaining: this is still recovery identity binding, not broker submission. No place/modify/cancel network write is enabled. Any future submitter must perform a fresh account safety/interlock check immediately before I/O, commit and honor the single-winner claim, and route crashes/timeouts into read-only reconciliation. Keep PAPER mode mandatory, live submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.

## Fresh pre-submission interlock revalidation — VERIFIED (18 October 2026)

- Added `LiveOrderRecoveryService.validate_claimed_submission(user_id, order_id)` as a validation-only primitive for any future separately reviewed submitter. It requires `TRADING_MODE=LIVE`, `LIVE_ORDER_SUBMISSION_ENABLED=true`, a user-owned tagged LIVE intent in `SUBMISSION_CLAIMED`, the original still-connected broker connection, automated-entry enablement for strategy orders, and a positive `LiveAccountSafetyService.check_allowed` result.
- The method does not call a broker adapter and no current write method invokes it. It explicitly documents that a future submitter must still solve the race between this check and network I/O; this check alone is not a safe live-submit implementation.
- Added regression tests for disabled runtime submission flag, missing account-wide safety state, and disconnected original broker connection. The first CI attempt exposed a test-fixture reference error; that fixture was corrected and the latest run is green.
- Verified GitHub Actions [run #39140514552](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39140514552), SHA `9085d9fbdcc8ee2dd8baac6f5e73f92bd76cfa8b`: broker-write source guard passed; backend **456 passed, 8 skipped, 1 warning**; SQLite and PostgreSQL 16 migrations passed; PostgreSQL integration tests **8 passed**.
- Remaining: no actual broker order write is enabled. A future submitter must implement a race-safe final interlock protocol (e.g. coordinated safety-state lock/version and claim semantics), without holding unsafe database locks across network I/O, and must handle post-request crashes through read-only reconciliation. Keep PAPER mode mandatory, live submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.


## Main-branch continuation note — 2026-10-21

The current main-branch checkpoint is summarized at the top of this file. Historical branch-specific findings and commit references below remain useful context, but the safety branch was not merged wholesale. For the latest Phase 2 status, follow `PROGRESS.md`, `HANDOVER.md`, `MASTER_ROADMAP.md`, and `AUDIT_REPORT.md`.


## Main-branch continuation note — 2026-10-21

The latest verified main-branch Phase 2 checkpoint is summarized at the top of this file. Historical branch-specific findings remain useful context, but the safety branch was not merged wholesale. See `PROGRESS.md`, `HANDOVER.md`, `MASTER_ROADMAP.md`, and `AUDIT_REPORT.md` for current lifecycle changes.


## Main-branch continuation note — 2026-10-21

The latest verified main-branch Phase 2 checkpoint is summarized at the top of this file. Historical branch-specific findings remain useful context, but the safety branch was not merged wholesale. See `PROGRESS.md`, `HANDOVER.md`, `MASTER_ROADMAP.md`, and `AUDIT_REPORT.md` for current lifecycle changes.


## Main-branch continuation note — 2026-10-21

The latest verified main-branch Phase 2 checkpoint is summarized at the top of this file. Historical branch-specific findings remain useful context, but the safety branch was not merged wholesale. See `PROGRESS.md`, `HANDOVER.md`, `MASTER_ROADMAP.md`, and `AUDIT_REPORT.md` for current lifecycle changes.


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

- The documentation checkpoint commit `0c74960c9b0bb1590aa14ef709f55e691b3ac5e2` passed exact-head GitHub Actions run `39757964236`: backend pytest, broker-write boundary guard, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document restore, and evidence artifact retention all passed.
- Further review confirms allocation persistence serializes on the evidence row, validates that target fills belong to the same broker connection, rejects conflicting replay/fill sets, and keeps allocations pending until separate source-ledger verification and promotion.
- The workflow records human transcription and reviewer attestation; it does not automatically parse or independently authenticate a broker's component amount. A real contract note and real backup set were not available, so both acceptance gates remain open.
- PR #6 stays draft/unmerged; live broker writes remain disabled; original `Tradepro` is out of scope. This is a code-review/CI checkpoint, not a claim that real-source reconciliation or real-backup restore is complete.


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


## Requirement status addendum — tariff snapshots (2026-10-23)

- [x] Durable estimate-only snapshot storage with canonical payload, digest, stable idempotency key and exact-replay/conflict checks.
- [x] Database-enforced append-only behavior for direct SQL UPDATE/DELETE on PostgreSQL and SQLite (migration `202610240016`); regression tests added.
- [x] Exact-head CI run 39959332425 passed pytest, broker-write guard, SQLite/PostgreSQL migration round-trips, and synthetic restore drill.
- [ ] Dedicated PostgreSQL concurrency test for simultaneous same-key tariff snapshot persistence and conflicting payloads.
- [ ] Complete component-aware tariff modeling for order caps/minimums, conditional rates, GST taxable bases and special charge models before approving those rule types.
- [ ] End-to-end variance-only comparison between estimate snapshots and reviewed actual contract-note components; actual per-fill allocation must continue to derive only from actual evidence.


## Requirement status — Task B verification (2026-10-23)

- [x] Canonical estimate-only snapshot persistence, digest, idempotency, exact replay and conflicting-replay rejection.
- [x] Database-level append-only guards on PostgreSQL and SQLite; direct SQL UPDATE/DELETE regression tests.
- [x] PostgreSQL concurrency coverage for exact-replay and conflicting-payload snapshot insert races.
- [x] Exact-code-head CI run 39960409771: 677 passed, 1 warning; broker-write guard, SQLite/PostgreSQL 16 migration round-trips, and synthetic restore drill passed.
- [ ] Variance-only comparison of tariff estimates against reviewed actual contract-note components, with no estimate promotion to actual/per-fill ledger.
- [ ] Explicit component-specific conditional/order-level caps, minimums, GST taxable bases and special tariff models before approving those rule types.


## Task B variance requirements — 2026-10-23

- [x] Snapshot schema v2 can retain an exact broker fill identity; missing identity fails closed for comparison.
- [x] Append-only variance record/migration stores estimate, reviewed actual, signed difference and percentage without changing accounting allocations.
- [x] Variance service validates reviewed contract-note evidence, stored document integrity, source/component hashes, reviewer provenance, broker connection, component/currency and exact single-fill scope.
- [x] Exact replay, missing-identity rejection, direct SQL immutability and no-allocation-side-effect tests.
- [x] CI run 39961777103: 680 passed, 1 warning; broker-write guard, SQLite/PostgreSQL 16 migration round-trips and synthetic restore passed.
- [ ] Aggregate variance comparison for multi-fill/order-level actual components.
- [ ] Conditional/order-level caps, minimums, GST taxable base and special tariff models before approving those rule types.


## Verified exact PR-head CI 39962196672 — 2026-10-23
- [x] Exact PR #6 head `c47bc3e3eeb4c8da4415132735d2d4ef457551f7` CI passed: 680 tests, 1 warning; broker-write guard passed; no failed steps ([run](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39962196672)).
- [ ] Design/test safe aggregate variance for order-level/multi-fill contract-note components.
- [ ] Implement/test advanced conditional tariffs, caps/minimums, GST bases and special charge bases, or reject unsupported shapes explicitly.
- [ ] Complete final accounting replay/conflict/rollback/concurrency integration review.
- [ ] Re-run exact-head CI and synchronize all nine docs before a human merge gate. Keep PR draft and live writes disabled until explicitly approved.


## Aggregate variance scope — design only — 2026-10-23
- [x] Documented proposed `TRADE_FILL` versus `ORDER_FILL_SET` scope and exact fill-set digest requirements.
- [x] Defined fail-closed behavior for missing/extra/duplicate/changed fill identities and source/reviewer/hash mismatch.
- [x] Defined order-scope calculation for caps/nonlinear tariffs, immutable variance-only behavior and required concurrency/replay/rollback tests.
- [ ] Review design against current implementation/schema; implement and test aggregate comparison only after review.
- [ ] Keep advanced tariff models unsupported until source-backed rules and executable examples pass.


## Variance validation hardening — 2026-10-23
- [x] Compare canonical actual eligible-fill manifest SHA-256 to stored digest before variance calculation.
- [x] Verify identified broker fill side and trade date match estimate scope.
- [x] Add regression tests for tampered digest and side/date mismatch; require zero variance writes on rejection.
- [ ] Run and inspect CI on exact latest code head `6ca045e2bbdd71d37dd77baf50df3881db2b1e71`.
- [ ] Implement aggregate order/multi-fill variance after design review.
- [ ] Implement source-backed advanced tariff semantics or reject unsupported rule types; no production tariff registry should be activated prematurely.


## Exact-head CI verification — 2026-10-23
- [x] CI passed for code head `f5092df1d27a28006dccba929fdc41e9a1d63f1e`: 683 passed, 1 warning; broker-write guard passed; SQLite migration round-trip and isolated PostgreSQL 16 synthetic restore drill completed ([run 39968000009](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39968000009)).
- [ ] Verify CI again on the latest documentation head after this checkpoint.
- [ ] Implement/test aggregate order/multi-fill variance.
- [ ] Implement source-backed advanced tariff semantics or reject unsupported shapes explicitly.
- [ ] Complete accounting replay/conflict/rollback/concurrency review before merge consideration.


## Aggregate variance coverage — 2026-10-23
- [x] Add explicit `TRADE_FILL` / `ORDER_FILL_SET` snapshot scope and canonical fill-set digest.
- [x] Persist comparison scope and digest on variance records; compare these on replay.
- [x] Require exact reviewed fill manifest and same broker order/connection/side/trade date for order-fill-set comparison.
- [x] Test fill-set canonicalization, duplicates, empty set, successful aggregate comparison, exact replay, and mismatched manifest.
- [x] Verify backend CI on code/test commit `e54e405b74feee90e4658a6992fa208a3e2da5d3`: test suite, broker-write guard, SQLite/PostgreSQL 16 migration round-trips, synthetic restore drill (run [39979772325](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39979772325)).
- [ ] Verify exact-head CI after the nine-document synchronization.
- [ ] Complete advanced tariff rule coverage/fail-closed review and final accounting acceptance.


## Latest tariff-safety correction checkpoint — 2026-10-23
- [x] Add APPROVED-status enforcement inside explicit GST component composition.
- [x] Reject stamp-duty SELL requests before generic rule selection.
- [x] Correct regression expectation to match the explicit GST component-set guard message.
- [x] Verify code commit `68dc2b6fa0a729cc77180725e581de61a88e9de1` in CI run [39982723294](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39982723294): pytest, broker-write boundary guard, SQLite/PostgreSQL 16 migration round-trips, and synthetic restore drill all passed.
- [ ] Verify CI on the following nine-document synchronization commit.
- [ ] Complete remaining advanced tariff-rule review and final accounting acceptance.


## Tariff safety + Upstox charge-source research — 2026-10-23

Code commit `ce0b4bc17eaf1656334e10ca8d6e32a68f50593b` adds a fail-closed stamp-duty unit guard: the specialized stamp-duty calculator accepts only percentage-based approved rules; regression tests reject `INR_FIXED` and `INR_PER_CRORE`. Exact-head CI [39987357989](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39987357989) passed backend tests, broker-write boundary guard, SQLite and PostgreSQL 16 migration round-trips, and synthetic restore drill.

Official Upstox sources reviewed:
- Brokerage calculator API: https://upstox.com/developer/api-documentation/get-brokerage/ — order-scoped estimate with brokerage, taxes, transaction/clearing/IPFT/SEBI charges and DP-plan metadata; `dp_plan.min_expense` is a daily per-scrip sell minimum outside the brokerage calculation.
- Trade charges API: https://upstox.com/developer/api-documentation/get-trade-charges/ — segment/date-range charge breakdown including brokerage, GST, STT, stamp duty, transaction, clearing, IPFT, SEBI turnover and demat transaction charges.
- Historical trades API: https://upstox.com/developer/api-documentation/get-historical-trades/ — trade ID, exchange, segment, quantity, amount, side and trade date.
- Public tariff page: https://upstox.com/brokerage-charges/ — includes historical and newer effective-date rows; never activate rates from a flattened scrape without preserving effective periods and source snapshot.

API charge breakdowns are reconciliation/reference inputs, not automatically contract-note evidence or a substitute for reviewed actual source components. Do not store tokens. DP per-scrip/day minimums, STT/CTT tax-event cases and other conditional models remain unsupported until represented and tested explicitly. No active production tariff registry is enabled. PR #6 stays draft/unmerged; live broker writes remain disabled; original `Tradepro` remains out of scope.

- [x] Add exact-head CI result for stamp-duty unit guard.
- [x] Record official Upstox charge API source contracts and keep API estimates distinct from actual contract-note evidence.
- [ ] Implement and test unsupported DP per-scrip/day and STT/CTT tax-event models before enabling them.


## Generic conditional-charge guard — 2026-10-23
The next audit found that the generic rate calculator could apply plain rate×base arithmetic to STT/CTT and DP/demat components, despite these requiring event- or day/scrip-specific semantics. Commit `ee09183e5b8eeff0311431faa90b807d9b561ce7` adds an explicit fail-closed block for STT, CTT, DP, DP charges and demat/depository transaction charges in the generic calculator, with parameterized regression tests. Exact-head CI run [39988242077](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39988242077) passed. The synchronized documentation commit `b1207def7d828c960e6fffe9c6af8b9ed0177c07` also passed exact-head CI run [39988578238](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39988578238).

Audit note: the implementation constant is `tariff-estimate-snapshot-v4`; older design text saying snapshot v3 is stale and is corrected in the accompanying design-document update. Remaining gated models include STT/CTT event-specific rules, DP daily per-scrip minimums, conditional lesser-of pricing, and reviewed source-backed effective-date rates. No live tariff registry or live broker order writes are enabled.

- [x] Block generic arithmetic for STT/CTT and DP/demat components; parameterized regression tests added.
- [ ] Verify CI on the exact code commit and synchronized documentation commit.

## Aggregate variance coverage review — 2026-10-24
Regression coverage added for corrupted actual fill-set digest, mixed-order fill sets, side mismatch, and trade-date mismatch; all negative cases assert no variance record is created. Existing tests cover order-fill-set success, exact replay, and different-manifest rejection. Acceptance remains pending current-head CI and review of concurrency, source/reviewer/hash revalidation, and no accounting side effects.

## Aggregate variance acceptance — 2026-10-24
Backend CI passed on head `bc8e5c1aa862589c660fd361d87f7df45d8ceb10` (run `40062975428`). Present tests cover audit-only success, idempotent replay, different manifest, tampered actual manifest digest, cross-order fill set, side mismatch and date mismatch. Still verify concurrent duplicate comparisons, source/component review-state revalidation, and no charge allocation or position/P&L changes on either success or rejection before marking the gate complete.

## Aggregate variance additional requirements — 2026-10-24
Regression coverage added for source/evidence/allocation immutability during variance comparison and fail-closed rejection when evidence or component review status is revoked before the write. Latest-head CI is pending. Concurrency/replay acceptance remains open.

## Upstox integration requirements — 2026-10-24
Required: maintain a current official-source capability matrix; evaluate SDK coverage/version mismatches; review official examples, Agent Skills and read-only MCP where relevant; use sandbox/contract tests; honour rate limits, token handling and regulatory/static-IP controls; assess brokerage estimate, historical charges and historical trades endpoints. Estimated/historical totals must not be promoted as reviewed actual per-fill evidence. See `UPSTOX_API_INTEGRATION_POLICY.md`.

## Aggregate variance concurrency requirement — 2026-10-24 (verified)
Exact-head CI run `40064129721` passed (738 passed, 1 warning). Concurrent identical variance comparisons have PostgreSQL integration coverage for single-record persistence, idempotent replay and zero allocation side effects. Combined with review-state revalidation and source/allocation immutability tests, the aggregate variance gate is accepted. Still required: official-source effective-dated component/product/segment/side rules; brokerage caps and multi-fill semantics; explicit GST taxable component composition; buy-side stamp duty; supported effective-date transitions; and rule-to-ledger tests. Do not enable generic automatic allocation before those gates pass.

## Upstox charge API requirements — 2026-10-24 (client CI passed)
The read-only client now covers the brokerage estimate endpoint, segment/FY aggregate trade charges and paginated historical trades; tests validate endpoint/query scope and invalid input rejection. Exact-head CI run `40064514873` passed (744 passed, 1 warning). Remaining: immutable request/response provenance and snapshot persistence; tests that estimate data cannot alter allocations/positions/P&L; and source-reviewed effective-dated tariff rules before automatic charge calculation. Historical charges are aggregates, historical trades are trade references, and neither alone proves actual per-fill charges.

## Upstox API estimate persistence requirement — 2026-10-24 (verified)
Implementation normalizes brokerage API response components into immutable estimate-only snapshots and records request parameters, API version/endpoint, UTC retrieval timestamp, full canonical response JSON + SHA-256, total estimate and DP-plan minimum metadata. Replay uses the existing idempotency constraints; variance comparison verifies response digest and exact fill input matching. Tests cover component mapping, replay, invalid response, digest tampering and quantity mismatch. Exact-head CI run `40065219626` passed (**754 passed, 1 warning**).

## Flat order brokerage requirement — 2026-10-24 (verified)
The calculation engine and estimate snapshot builder support explicit flat per-order brokerage (`ORDER_FIXED`/`INR_FIXED`) and existing capped percentage brokerage (`ORDER_NOTIONAL`/`PERCENT`). Regression tests verify both calculation and snapshot shape. No rate data was activated. Exact-head CI run `40065607232` passed (**756 passed, 1 warning**).

## Effective-dated tariff source requirement — 2026-10-24 (candidate stage verified)
Added dated source excerpt with canonical payload SHA-256 `c59f7e940fde6b0d94ca1189766f16e5601c117d4a8c2bcd2415da0ecd6db420` and 18 effective-dated candidate rows for STT/exchange charges. All candidates are DRAFT and unselectable. Remaining before any rate activation: archive original source bytes where possible, independently corroborate stamp duty, resolve IPFT/transaction-charge composition, define full component/product/side/base boundaries and add transition tests. Exact-head CI run `40065979244` passed (**760 passed, 1 warning**).


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


## Phase 3 source-conflict and candidate guardrail checkpoint — 24 October 2026

- Added an explicit finding to `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`: the current official Upstox charges page presents conflicting IPFT schedules. One table says ₹0.10/lakh for equity/futures and ₹0.50/lakh for options premium (₹10/crore and ₹50/crore); a later table says ₹0.01/crore for each. The page also says IPFT is combined with transaction charges while the API schema exposes `transaction` and `ipft` separately. These statements are not reconciled; do not infer inclusivity or add both amounts. GST base remains component-mapped and review-gated.
- Added regression test `test_unresolved_charge_components_are_not_added_as_tariff_candidates` to `backend/tests/test_upstox_tariff_candidates.py`. The candidate inventory must contain only the currently inventoried STT and exchange-charge categories, all DRAFT; GST, IPFT, stamp duty, brokerage, SEBI and DP/demat remain absent until scope/source/basis are reviewed.
- The existing candidate date-window and narrow-scope tests remain in place. These tests validate inventory guardrails, not rate correctness or tariff approval.
- Prior verified CI: workflow [#40085703204](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40085703204) passed on `fd4253ce51f812886fa081eeae3499533bfe4e20` with 780 tests. Documentation commit `5f3ef28897e3400bc5e415f5b4fcf7534a4fc07d` also passed [workflow #40086759124](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40086759124). The source-register update and latest regression-test commit have separate CI runs in progress; do not call their CI green until the exact-head runs complete.
- No DRAFT tariff candidate approved or activated. PR #6 remains draft/unmerged; live broker order writes remain disabled. Work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` stays untouched.


## Exact-head verification of IPFT guardrails — 24 October 2026

- Source-register update commit `96c687c1667257d894506c8cb7f8ab715d3612bc` passed CI: [run #40086827314](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40086827314).
- Latest candidate-regression commit `a6868241dce9c827d1c9f6918a192647af0168e3` passed CI: [run #40086856952](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40086856952). Pytest output reached 100%; **781 tests passed, 1 Starlette/AnyIO deprecation warning**. `TEST_POSTGRES_URL` was set; PostgreSQL-specific tests were enabled. Broker-write boundary guard passed; Alembic checks reached `202610240018`; synthetic PostgreSQL/document-volume restore evidence uploaded.
- The new regression test ensures unresolved charge categories (GST, IPFT, stamp duty, brokerage, SEBI and DP/demat) cannot silently enter the candidate inventory; only STT and exchange-charge research candidates remain, all DRAFT. It does not validate the numeric rates or authorize tariff selection.
- Official Upstox page discrepancy documented in the charge-rule register: one IPFT table lists ₹0.10/lakh (equity/futures) and ₹0.50/lakh (options premium), while a later table lists ₹0.01/crore and says IPFT is combined with transaction charges. This is unresolved; no IPFT or GST calculator/rule is approved, and no double counting is permitted.
- Documentation commit `ad6bfbee7da84453677f7a9a441bf7a79ded4c2e` has its own CI run [#40086974735](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40086974735); its final status was pending at the time of this note. The following documentation commit must also pass its own exact-head CI before being marked green.
- PR #6 remains draft/unmerged; live broker order writes remain disabled. Work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` stays untouched.


## Phase 3 API source-boundary regression checkpoint — 24 October 2026

- Added `test_aggregate_trade_charges_api_evidence_cannot_be_promoted_as_contract_note` in `backend/tests/test_broker_charge_source_reconciliation_service.py`. It tags evidence as `UPSTOX_TRADE_CHARGES_API`, asserts the contract-note verification path rejects it, and verifies pending allocations remain unpromoted with no reconciliation reference.
- Updated `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md` to distinguish the Brokerage Details API (request-scoped estimate) from Get Trade Charges API (segment/financial-year/date-range report), and from reviewed contract-note evidence. Aggregate totals must not be spread across fills without an independently reviewed basis; preserve raw component fields and avoid IPFT double counting.
- Code/test commit `426a0612b34b4fcf4e95ac23aeefcc6b0f990a4b` passed exact-head backend CI [run #40087358324](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40087358324): **782 tests passed, 1 Starlette/AnyIO deprecation warning**. `TEST_POSTGRES_URL` was set; broker-write boundary guard passed.
- Latest source-register commit `3040cb1b139643b8849928e23fa6b7af3dccde64` also passed exact-head CI [run #40087367504](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40087367504).
- Tariff activation blockers remain: conflicting/unclearly dated IPFT rows on the public Upstox page; exact transaction/IPFT inclusivity; product-specific GST taxable-component sets; effective-date/applicability proof; and reviewed per-fill attribution for actual charges. Candidate inventory remains STT and exchange-charge research rows only, all DRAFT.
- Safety: PR #6 stays draft/unmerged; live broker `place_order`, `modify_order`, and `cancel_order` remain disabled. Work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` remains untouched.


## Exact-head documentation CI confirmation — 24 October 2026

- Latest checkpoint commit `cbf83ad8c11d38390d82d42883c7e2c72f04a42a` passed exact-head backend CI [run #40087629909](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40087629909). The Backend pytest job completed successfully. This run validates the docs-only checkpoint, not any subsequent commit.
- The latest source-boundary test commit `426a0612b34b4fcf4e95ac23aeefcc6b0f990a4b` passed [run #40087358324](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40087358324): 782 tests passed, one Starlette/AnyIO deprecation warning; `TEST_POSTGRES_URL` was configured and the broker-write boundary guard passed.
- The API source register distinguishes request-specific Brokerage Details estimates, date/segment-scoped Get Trade Charges aggregates, and reviewed contract-note evidence. Regression coverage prevents the aggregate API evidence type from being promoted through the contract-note fill-allocation verification path.
- Open Phase 3 tariff gates remain: contradictory public IPFT rates and uncertain inclusivity; source-backed effective dates/applicability; product-specific GST taxable-component mapping; and a reviewed per-fill attribution basis for aggregate/DP charges. No candidate was approved or activated.
- Safety remains unchanged: work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` is untouched. PR #6 remains draft/unmerged; live broker `place_order`, `modify_order`, and `cancel_order` execution remains disabled.


## NSE IPFT source reconciliation — 24 October 2026

Primary source: [NSE Circular NSE/FA/73061, 27 February 2026](https://nsearchives.nseindia.com/content/circulars/FA73061.pdf), effective 1 March 2026. It shows combined member outflow rates of ₹307/crore/side for cash market, ₹183/crore/side for equity futures and ₹3,553/crore/side on options premium, split into transaction charges and ₹0.01/crore IPFT contribution. The legacy ₹10/₹50-per-crore IPFT schedule must not be added to the newer combined rates.

The source register marks the Upstox-page conflict partially reconciled for those NSE scopes, not fully approved. Account-specific API/contract-note reconciliation, effective-date/product-scope review and GST composition remain gates; this circular does not establish BSE/MCX rules. Candidate comment/test updates encode DRAFT combined rates (NSE cash 0.00307%, futures 0.00183%, options 0.03553%; BSE options 0.0325%) and forbid a separate IPFT candidate. Commits `68aae327`, `fc7fb146`, `c01cd66c`, and `777d0ee5` are included in the current PR head and covered by exact-head backend CI #40090309898 (786 passed, one warning). Their CI gate is closed; candidate source-rate approval and account-specific tariff validation remain open.

Previously verified: checkpoint commit `cbf83ad8c11d38390d82d42883c7e2c72f04a42a` passed [CI #40087629909](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40087629909). API source-boundary test commit `426a0612b34b4fcf4e95ac23aeefcc6b0f990a4b` passed [CI #40087358324](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40087358324): 782 tests passed, one deprecation warning.

Safety: work only in `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched. PR #6 remains draft/unmerged; live broker order writes remain disabled.


## GST component and NSE IPFT source audit — 24 October 2026

- Primary NSE Circular NSE/FA/73061 (27 February 2026; effective 1 March) reconciles the current NSE combined charge schedule: ₹307/crore/side cash, ₹183/crore/side futures, ₹3,553/crore/side options premium, with ₹0.01/crore IPFT contribution inside the total. Never add the legacy ₹10/₹50 IPFT rows on top. Source register documents the covered scopes and remaining account-specific validation.
- Reviewed Upstox's GST component statement and CBIC Stock Broking Services FAQ Q77–78 / Rule 33. Upstox lists brokerage + transaction + IPFT for intraday/F&O and adds demat for equity delivery; CBIC says STT/stamp-duty/other tax recoveries are excluded only if pure-agent conditions are met. Exact GST base remains unapproved until matched to an actual invoice/contract note; do not apply 18% to all charges or assume exclusions.
- Latest code/test commit `fc7fb1463091ae070ad9d82b8aea380506b9482b` passed [CI #40088003373](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40088003373): 782 tests passed, one Starlette/AnyIO warning; PostgreSQL was configured and broker-write guard passed. Source-register commit `777d0ee536f6809f01c5cea96b9a3b9b4d4f1e32` passed [CI #40088089474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40088089474). The current code/test head `81a67b64ec92cdf9178b4ec0ac9b5e3fc1d1e472` passed exact-head backend CI #40090835774 (786 passed, one warning), including the new post-commit refresh-failure/retry regression test. Later documentation-only commits should not be described as code/test failures; no new run has yet been returned for the subsequent docs-only head.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched. PR #6 remains draft/unmerged; live broker order writes disabled.


## Phase 3 latest-head checkpoint — 24 October 2026
- Coverage documentation commit `05f2dfdd6e0222fb091df17c15e1c72fe6d90cd1` has completed exact-head backend CI successfully: [run #40089127877](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40089127877). Backend pytest, broker-write boundary guard, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and evidence-artifact retention all passed.
- This green result applies to commit `05f2dfdd6e0222fb091df17c15e1c72fe6d90cd1`; any subsequent documentation or code commit requires its own exact-head CI before being called green.
- Acceptance review still open: verify rollback at important accounting write/failure boundaries; distinguish source-verification concurrency coverage from a full concurrent live-fill promotion race; decide/test reviewer-admin revocation semantics; maintain clear evidence that uploaded document hashes prove byte continuity, not broker-origin authenticity.
- Keep PR #6 draft/unmerged pending accounting acceptance. Live broker order submission stays disabled. Work only in `tarunsharma2610-del/tradepro-improved`; never modify original `tarunsharma2610-del/Tradepro`.


## Phase 3 accounting follow-up — 24 October 2026
- Regression commit `735dffc5194463893e5c57741d40da5ccfee7ed1` passed backend CI run [40089896692](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40089896692). The test suite, broker-write boundary guard, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic restore drill, and evidence retention all passed.
- The existing PostgreSQL concurrency suite already includes `test_live_fill_promotion_races_with_component_ledger_verification`. It races full live-fill accounting promotion against component-ledger promotion; it asserts no unhandled errors, permits a fail-closed pending-allocation result, checks that blocked promotion leaves no execution/position, retries safely, and verifies exact replay plus conflicting-charge rejection. Therefore this specific race test is present; do not keep describing it as missing. The exact-head backend workflow #40090309898 passed 785 tests with `TEST_POSTGRES_URL` configured; the PostgreSQL concurrency test was not skipped. This closes the test-execution-confirmation sub-gate; accounting acceptance review remains open.
- Rollback coverage now includes a failure after accounting rows are staged and a failed-commit path; continue checking whether any materially distinct write/flush boundary remains uncovered rather than claiming every conceivable failure point is tested.
- Reviewer authority is revalidated at live-fill promotion: the recorded reviewer must still be an active platform administrator. Tests cover role revocation and deactivation.
- Phase 3 remains open until the latest-head CI result is confirmed, accounting/rollback acceptance is reviewed, and all checkpoint documents are synchronized. PR #6 remains draft/unmerged; live broker order submission remains disabled. Work only in `tarunsharma2610-del/tradepro-improved`; never modify original `tarunsharma2610-del/Tradepro`.


## Latest exact-head CI verification — 24 October 2026
- Verified the current PR #6 head `81a67b64ec92cdf9178b4ec0ac9b5e3fc1d1e472` against backend workflow [#40090835774](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40090835774): **786 tests passed, 1 warning**. This includes the new post-commit refresh-failure/retry regression test. Broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and evidence retention all passed.
- The rule-bound brokerage-cap entrypoint follow-up commits `d6d60a03732ab322785d5e020f0521a4b96162c9` and `78f5f27135137a1d8f0882d2c0a91d013f6e8556` also have successful backend runs [#39977035981](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39977035981) and [#39977054423](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39977054423). The PR description was corrected to reflect those passing runs.
- The latest exact-head green status supersedes earlier notes that CI for the reviewer/rollback or tariff-cap follow-ups was still pending. Any subsequent commit still needs its own exact-head CI.
- Phase 3 acceptance remains open for final financial-accounting/rollback review and sign-off. The PostgreSQL live-fill/component-ledger race test exists; keep its scope distinct from any separate concurrency guarantees not directly covered. PR #6 remains draft/unmerged; live broker order submission remains disabled. Work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` remains untouched.


## Post-commit recovery regression — 24 October 2026
- Added `test_post_commit_refresh_failure_is_safe_to_retry_as_exact_replay` in commit [`81a67b64ec92cdf9178b4ec0ac9b5e3fc1d1e472`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/81a67b64ec92cdf9178b4ec0ac9b5e3fc1d1e472).
- Exact-head backend CI [#40090835774](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40090835774) passed **786 tests, 1 warning**. Broker-write guard, SQLite/PostgreSQL migration checks, synthetic restore drill, and evidence retention also passed.
- This covers the post-commit/pre-response interruption case: rollback cannot undo a committed transaction, so retry must return the existing execution without applying the fill twice. Phase 3 remains open for final acceptance/sign-off; PR #6 stays draft/unmerged and live broker order submission remains disabled.

## Exact-head CI checkpoint — 24 October 2026

- Documentation checkpoint commit `3e0ae8034f333e082bfa11b6da50aec9e620f242` passed GitHub Actions Backend tests run [`40091642139`](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40091642139): **787 passed, 1 warning**.
- Broker-write boundary guard passed. SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed. Synthetic PostgreSQL/document-volume restore drill and evidence-artifact retention passed.
- The warning is a Starlette/AnyIO deprecation warning; GitHub Actions also emitted Node.js 20 deprecation notices. No test or safety-guard failure was reported.
- This result applies to commit `3e0ae803` only; subsequent documentation commits require their own exact-head CI run.
- Phase 3 remains open pending final accounting acceptance and tariff-source applicability decisions. PR #6 remains draft/unmerged and live broker order submission remains disabled. Work only in `tarunsharma2610-del/tradepro-improved`; never the original `tarunsharma2610-del/Tradepro`.

## Upstox charge API audit and exact-head CI checkpoint — 24 October 2026

- Added official API guidance to `PROJECT_INSTRUCTIONS.md` and expanded `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`: use Brokerage Details API (`GET /v2/charges/brokerage`) for estimates; use supported P&L charge breakdowns for a selected reporting scope (aggregate, not per-trade) for reconciliation; compare realized charges with authenticated trade history and an actual broker-issued contract note/tax invoice.
- Exact branch head `640ebfba38a96c7d84d4ffc3501afcd2278b551b` passed Backend workflow [#40092513016](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40092513016): **787 passed, 1 warning in 48.85s**. Broker-write boundary guard, SQLite/PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore drill, and evidence retention passed.
- Warning: Starlette/AnyIO `BlockingPortal` deprecation. Workflow also reports Node.js 20 and dependency deprecation notices. No test or broker-write guard failure was reported.
- Source discovery is not approval: no account-specific Upstox response or contract-note fixture was verified here. GST taxable-component mapping and tariff scope/effective dates remain unapproved; candidate rules remain inactive. Do not double-count legacy IPFT with the current combined NSE transaction schedule.
- Future documentation/code commits need their own exact-head CI run. This entry records the successful run above only.
- PR #6 remains draft/unmerged; live broker order submission remains disabled. Work only in `tarunsharma2610-del/tradepro-improved`; never modify the original `tarunsharma2610-del/Tradepro`.

## Upstox API coverage and tariff-source correction — 24 October 2026

- Added read-only `get_profit_loss_report` for official `GET /v2/trade/profit-loss/data`, with fixed endpoint, segment/financial-year/date/pagination validation, and regression coverage. The API supplies paginated trade-wise realized P&L rows but does not document per-row charge components; do not treat it as per-fill charge evidence.
- Kept the three Upstox surfaces distinct: `/charges/brokerage` is a request-specific estimate; `/trade/profit-loss/charges` returns selected-scope aggregate charge components; `/trade/profit-loss/data` returns trade-wise P&L rows. Contract-note evidence and reviewed allocation rules remain required for charge promotion.
- Corrected DRAFT equity STT candidates for delivery buy/sell (0.1%) and intraday sell (0.025%) to the source-stated 1 April 2023 effective date rather than incorrectly implying a new 1 April 2026 effective date. Added regression coverage. All candidate rules remain DRAFT and non-selectable.
- Intermediate backend CI run [#40093110292](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40093110292) passed **789 tests, 1 warning** plus broker-write guard; however, this run predates the final effective-date correction. Latest exact-head validation is still running in [#40093198960](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40093198960); do not mark the latest head green until it completes successfully.
- PR #6 remains draft/unmerged and live broker order submission remains disabled. All work is in `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` remains out of scope.


## 2026-10-24 — Variance rollback regression exact-head verification

- Follow-up fix commit: `5e036d7fcc1f5f439d4054700366d284d7b78061`.
- Fixed the rollback regression assertion to compare allocation snapshots in stable UUID order. This preserves checks of row identity, status, amount, and reconciliation reference while avoiding reliance on unspecified SQL row ordering.
- Exact-head GitHub Actions run [#40096380843](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40096380843) completed successfully: **793 passed, 1 warning**; broker-write boundary guard passed; SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks passed; synthetic PostgreSQL/document-volume restore drill completed.
- The prior failed run exposed a test-ordering issue, not evidence of an accounting mutation; the corrected regression now passes in the full backend suite.
- Phase 3 is **not complete**: source-backed Upstox tariff/GST mapping, final per-fill allocation acceptance, and final merge gates remain open. Tariff candidates remain DRAFT/non-selectable. PR #6 remains draft/unmerged. Live broker order submission remains disabled.
- Scope guard: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` remains out of scope and must not be modified.


## 2026-10-24 — Upstox charge-source register

- Added [`UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`](UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md) documenting the official Upstox Brokerage Details API (`GET /v2/charges/brokerage`) and Profit and Loss on Trades API as distinct estimate vs realized-charge evidence sources.
- Added [`CHANGELOG.md`](CHANGELOG.md) to record this Phase 3 checkpoint and the verified 793-pass code CI result.
- No effective-dated tariff was approved: official API schemas alone do not prove the user's active brokerage plan or current legal/exchange rates. All tariff candidates remain DRAFT/non-selectable pending authoritative dated sources and independent review.
- Existing arithmetic tests cover deterministic largest-remainder paise allocation, mapping-order independence, zero-weight exclusion from residual distribution, invalid inputs and order brokerage-cap arithmetic. Ledger verification remains fail-closed for generic QUANTITY/NOTIONAL allocation until component-specific rules are approved; only explicitly reviewed weights can be promoted.
- Exact-head CI for the latest documentation-only commits is still required before treating the branch checkpoint as fully verified. PR #6 remains draft/unmerged; live broker order submission remains disabled.
- Scope remains `tarunsharma2610-del/tradepro-improved` only; do not modify the original `tarunsharma2610-del/Tradepro` repository.


## 2026-10-24 — Exact documentation-head CI verification

- The exact documentation head `3f9e20bd70b218bff2837967da04b53732968c2b` passed [Backend CI run #40097569588](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40097569588).
- Result: **793 passed, 1 warning in 41.64s**. Broker-write boundary guard passed. SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks passed. Synthetic PostgreSQL/document-volume restore drill passed and evidence was retained.
- This closes the exact-head CI verification gate for the Upstox charge-source register and the documentation checkpoint that preceded this note. This new note itself is documentation-only and is not included in that already completed CI run.
- Phase 3 acceptance remains open: effective-dated Upstox/exchange/tax tariff evidence and independent approval, final per-fill allocation/accounting acceptance, and PR merge gates remain outstanding. Candidate tariff rules remain DRAFT/non-selectable. PR #6 remains draft/unmerged. Live broker order submission remains disabled.
- Repository boundary: `tarunsharma2610-del/tradepro-improved` only. The original `tarunsharma2610-del/Tradepro` must not be modified.


## 2026-10-24 — Reviewed fill-ID input validation hardening

- Added defensive validation in `backend/app/services/broker_charge_source_reconciliation_service.py`: each reviewed allocation-weight `fill_record_id` must be a string before UUID parsing. This prevents malformed JSON values such as `null`, numbers, or arrays from escaping the expected validation path as an unexpected exception.
- Added parameterized regression coverage in `backend/tests/test_broker_charge_source_reconciliation_service.py` for `null`, numeric, and list-valued fill IDs. Expected behavior is a controlled `ValueError`; no allocation is promoted by this validation path.
- Code commit: `10febb7a14c779ab7e308b9175ff4f16ad5fec44`; regression test commit: `067e76687eda71aa81aae1df6b8b16133cf42d86`.
- CI for this new code/test head is not yet reported by GitHub Actions at the time of this note; the previous 793-pass run does not verify these new changes. Combined commit status currently reports no status checks for the new head, so this fix remains unverified pending CI.
- Phase 3 remains open: effective-dated tariff source approval, per-fill accounting acceptance, exact-head CI and final PR review remain required. PR #6 stays draft/unmerged; live broker order submission remains disabled.
- Repository boundary remains `tarunsharma2610-del/tradepro-improved` only; do not modify original `tarunsharma2610-del/Tradepro`.


## 2026-10-24 — Reviewed fill-ID validation CI result

- Exact code/test head `ddeed926a16f235de777025db1053d9e110bbc11` passed GitHub Actions run [#40099389651](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40099389651).
- Result: **796 passed, 1 warning in 43.75s**. Broker-write boundary guard passed; SQLite and PostgreSQL migration upgrade/downgrade/re-upgrade checks passed; synthetic PostgreSQL/document-volume restore drill passed.
- This CI includes the new parameterized regression tests rejecting malformed reviewed `fill_record_id` values (null, numeric, list) before UUID parsing. It does not yet include the documentation-only updates made after this code/test head.
- Phase 3 remains open: component-by-component per-fill accounting acceptance, authoritative effective-dated tariff evidence and independent review, and final PR gates remain outstanding. Tariff candidates stay DRAFT/non-selectable. PR #6 remains draft/unmerged. Live broker order submission remains disabled.
- Scope guard: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` must remain untouched.


## 2026-10-24 — Invalid reviewed-weight regression coverage

- Added regression tests in `backend/tests/test_broker_charge_source_reconciliation_service.py` for negative weights, non-finite weights (`NaN`, `Infinity`), malformed decimal values, all-zero weight sets, and duplicate fill IDs in the reviewed weights manifest.
- Each case must fail closed before allocation promotion and leave ledger rows in `PENDING_RECONCILIATION`.
- Test commit: `cb577cd1c917da9f2af1e5a01607dd42377067ca`. GitHub Actions backend workflow #40099823190 was still running at the time of this documentation update; do not treat the prior 796-pass run as verification of these new tests. The new documentation commits will also require exact-head CI verification.
- Phase 3 remains open: allocation acceptance, authoritative effective-dated tariff evidence and independent review, exact-head CI, and final PR gates are pending. PR #6 remains draft/unmerged; live broker order submission remains disabled.
- Scope guard: work only in `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` must remain untouched.


## 2026-10-24 — Reviewed-weight validation tests CI verified

- Backend workflow [#40099906234](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40099906234) passed for code/test head `0d563f060055bb31c14a20f407a5f4b577843d48`: **802 passed, 1 warning in 48.62s**.
- The run includes the new invalid reviewed-weight regression cases (negative, NaN, Infinity, malformed decimal, all-zero and duplicate fill IDs), in addition to the malformed fill-ID tests. Broker-write boundary guard passed and synthetic restore-drill evidence was uploaded. The workflow also exercised PostgreSQL 16 migration downgrade/upgrade checks.
- This run verifies the code/test head before this documentation update, not the documentation commits below. A fresh exact-head CI result is required before treating the current branch tip as fully verified.
- Phase 3 remains open: per-component accounting acceptance and authoritative, effective-dated tariff evidence with independent review remain pending. PR #6 stays draft/unmerged; live broker order submission remains disabled.
- Repository scope is `tarunsharma2610-del/tradepro-improved` only. Do not modify original `tarunsharma2610-del/Tradepro`.


## 2026-10-24 — Charge API unusable-value provenance hardening

- Review found that `resolve_charge_api_value` retained the approved mapping's semantic and source fingerprint for usable values, but omitted source URL and SHA-256 provenance when the normalized field was `MISSING`, `NULL`, or `INVALID`. These values were already unusable, but their interpretation path was less auditable.
- Fixed the resolver to return approved mapping provenance for every normalized state while keeping missing/null/invalid values `usable=False`. Numeric zero remains a distinct present value; this change does not promote allocations or approve production Upstox mappings.
- Added regression coverage for missing, null, NaN, negative, boolean, and object values; assertions require mapping source URL, source SHA-256, and semantic to remain present. Added mapping effective-date and estimate-vs-actual guard cases.
- Implementation commit: `845e9e0dc924f11ae89b96ef73c94c59c2efb4b4`. Test commit: `1d7e24b0ba8c89062ec1eeddb93d0c4cd22a226f`. Documentation checkpoint is being synchronized; exact-head CI must pass before verification is claimed.
- PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains out of scope.


## 2026-10-24 — Resolver acceptance and CI checkpoint

- Backend workflow `40108183667` succeeded on prior head `8214430f562f6f425cfc1b9b6a3b547832b68a`. New resolver tests add exact broker/endpoint/schema/field/scope matching and non-finite-number rejection; newer commits still require CI.
- Mapping identity fixtures use immutable dataclass replacement. Intended-use semantics remain explicit; missing/null/invalid values remain unusable and retain provenance; numeric zero remains distinct.
- Accounting acceptance includes replay/conflict, ledger reconciliation, lock order, rollback, reviewer authority and PostgreSQL verification/promotion race coverage. Re-check exact test and workflow status before claiming complete. CI does not establish production tariff correctness or broker-origin authenticity.
- Safety gates unchanged: PR #6 draft/unmerged; live broker order submission and automatic quantity/notional allocation disabled; production Upstox mappings/tariffs unapproved. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Resolver field-identity guard added; CI pending

- Resolver now checks that the payload field name matches the terminal field in the selected approved mapping path. This closes a semantic mismatch where a caller could select `charges.ipft` but normalize another payload field.
- Implementation commit: `77aa77aec37dc535c3e427ca3f88c2ccb5e75ed8`; regression test commit: `5c5482c7f7fa623707698f64b6a061351e5e5b87`. CI for latest commits is pending; previous green runs apply only to earlier heads.
- Existing accounting tests cover lock ordering, replay idempotency, conflicting evidence and rollback. A genuine concurrent two-session verification-versus-promotion race is not demonstrated in the inspected live-fill test file; verify other integration coverage before marking complete.
- PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled; production Upstox mappings/tariffs remain unapproved. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Latest resolver CI and PostgreSQL concurrency suite verified

- Latest implementation/documentation checkpoint `ed346e823cbfae8448fae0134c4ff864bfcc60ac` passed Backend pytest workflow [#40109041654](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40109041654): **872 passed, 1 warning**, with the broker-write boundary guard also passing.
- Dedicated PostgreSQL concurrency tests are present in `backend/tests/test_broker_charge_allocation_postgres_concurrency.py`, including source verification vs allocation promotion and live-fill promotion vs ledger verification. The successful CI summary reports no skipped tests, so this run exercised the collected suite; the race tests are part of that test set.
- This confirms test execution and safeguards in the synthetic PostgreSQL test environment; it does not establish production broker tariff correctness or approve any real Upstox field mapping.
- PR #6 remains draft/unmerged. Live broker order submission and automatic quantity/notional allocation remain disabled. Work only in `tradepro-improved`; original `Tradepro` remains untouched.


## 2026-10-24 — Aggregate endpoint hard guard added; CI pending

- Resolver now blocks Upstox `/v2/trade/profit-loss/charges` from `PER_FILL_ACTUAL` use even if a mapping row is incorrectly labelled per-fill. Official documentation defines the endpoint as aggregate `charges_breakdown`, not per-fill evidence.
- Regression test `test_official_upstox_aggregate_charges_endpoint_cannot_be_promoted_to_per_fill` covers the guard. Implementation `cdc07afdd8cc0c8d0b37d7e4aa8cdf1bf6eac651`; test `8ae749017a8ba0016f2c9adeb77eaff41fb5ae70`. CI is pending for this test commit.
- Production field mappings and tariffs remain unapproved; null is not zero; automatic quantity/notional allocation and live order submission remain disabled. PR #6 stays draft/unmerged; original `Tradepro` remains untouched.


## 2026-10-24 — Upstox brokerage calculator restricted to estimates; CI pending

- Official Upstox `GET /v2/charges/brokerage` takes proposed instrument, quantity, product, transaction type and price, returning a charge calculation; this is not proof of final booked per-fill charges. https://upstox.com/developer/api-documentation/get-brokerage/
- Resolver now blocks `/v2/charges/brokerage` from `PER_FILL_ACTUAL` and actual `AGGREGATE_SUMMARY` use even if a mapping is misleadingly labelled. Existing guard still blocks `/v2/trade/profit-loss/charges` from per-fill actual use. New regression tests cover both misuse cases.
- Implementation `3486d854dae2451858a858cb627602aca7338969`; tests `6c92101a1890a0f4d761e86ed3db047a269fd10d`. Prior head `6cc8b58f635fcb4f1b1cb3e5997099d074800a28` passed workflow #40111501429. CI for the new commits must be verified.
- Production mappings/tariffs remain unapproved; null is not zero; automatic quantity/notional allocation and live broker order submission remain disabled. PR #6 stays draft/unmerged. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.

## Upstox SDK/API integration audit — 24 October 2026

- **Evidence:** [`docs/UPSTOX_SDK_API_REPOSITORY_AUDIT.md`](docs/UPSTOX_SDK_API_REPOSITORY_AUDIT.md), official Upstox API catalogue, SDK installation page, official Python SDK source, brokerage estimate endpoint and aggregate trade-charge endpoint.
- **Current status:** direct async REST clients and a dedicated V3 stream already exist; the official Python SDK is not declared as a backend dependency. Brokerage estimate parsing and semantic controls already exist.
- **Requirement:** use official SDK capabilities where they materially improve correctness/maintenance, but preserve async timeout/retry/error handling, parser validation, read-only boundaries and accounting semantics. SDK support must be verified per endpoint and exact package release.
- **Next acceptance task:** isolated, pinned compatibility spike for the read-only brokerage-estimate method using synthetic response fixtures. Do not add the package to production dependencies until the spike demonstrates value and CI passes.
- **Agent Skill:** development-only reference; inspect scripts before running; no live credentials or order-write examples. No account access or live API call was used in the audit.

## Upstox SDK/Agent Skill review gate — 2026-10-24

- **Evidence:** [SDK/API audit](docs/UPSTOX_SDK_API_REPOSITORY_AUDIT.md) and [Agent Skill security review](docs/UPSTOX_AGENT_SKILL_SECURITY_REVIEW.md), official SDK tag v2.30.0 and upstream Agent Skill source.
- **Finding:** current async `httpx` read-only brokerage call and response parser already cover the endpoint. SDK method is synchronous by default; no measurable benefit justified a runtime dependency in this step.
- **Security:** upstream skill can place live orders and GTTs; its helper has a local config token fallback and raw API-body print path. Development reference only; never run live-write examples with credentials or rely on its confirmation as app authorization.
- **Acceptance status:** static source review complete; runtime SDK integration test not performed and SDK is not installed in backend dependencies. Any future adoption requires a concrete gap, pinned version, tests and exact-head CI.


## Phase 3 checkpoint — official GST/IPFT source cross-check (25 October 2026)

- Current official Upstox charges page lists transaction charges effective 1 March 2026, STT effective 1 April 2026, GST bases by product, and says IPFT is combined with transaction charges while also showing an IPFT row. This does not prove whether any particular API `transaction` field is transaction-only or transaction-plus-IPFT.
- NSE confirms from 1 April 2026: options-sale STT 0.15% on premium, exercised-option STT 0.15% on intrinsic value, and futures-sale STT 0.05%. CBIC says STT/stamp-duty/other-tax recoveries are outside GST value only when pure-agent conditions are met; otherwise Section 15/Rule 27 valuation applies.
- No production mapping or tariff was approved. Keep tariff candidates DRAFT/non-selectable, do not double-count IPFT, and preserve fail-closed per-fill accounting. Exact-head CI for prior head `7d4f2918b534ef9b4c3d32e7df22b754b21e6c8f` passed in run [40182196510](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40182196510); this docs update requires fresh exact-head CI.
- Continue Phase 3 component-by-component accounting acceptance and fault-injection/rollback review. PAPER mandatory, live broker writes disabled, PR #6 draft/unmerged, original `Tradepro` untouched. Sources: https://upstox.com/brokerage-charges/ ; https://www.nseindia.com/static/products-services/equity-derivatives-securities-transaction-tax ; https://cbic-gst.gov.in/sectoral-faq.html


## Phase 3 resolver guard hardening — 25 October 2026

- Hardened source-level restrictions for Upstox aggregate-only `/v2/trade/profit-loss/charges` and estimate-only `/v2/charges/brokerage` endpoints. Guard canonicalizes broker-name casing and endpoint path spelling (trailing slash, query string, full URL) while reviewed mapping selection remains exact.
- Added regression tests so misleading approved mapping rows cannot convert aggregate/estimate data into per-fill actual accounting.
- Defensive code change only: no API field semantic or tariff approved. Production mappings remain unapproved, null is not zero, IPFT must not be double-counted, and charge-ledger promotion remains fail-closed.
- Exact-head CI for this code/documentation commit must be verified. PAPER mandatory; live broker writes disabled; PR #6 draft/unmerged; original `Tradepro` untouched.

## Phase 3 forward checkpoint — 25 October 2026

- The source-evidence intake vocabulary now supports documented Upstox transaction, clearing, IPFT, other and demat transaction labels through migration `202610250019`. This stores pending source evidence only.
- Live-fill accounting remains fail-closed on anything beyond the six currently reconciled components. A versioned component-set contract must precede any promotion of separately reported IPFT or other additional components.
- NSE combined-vs-split IPFT arithmetic is already covered by regression tests; actual Upstox field semantics and GST component composition still require independent endpoint/schema and contract-note/invoice evidence.
- Exact-head CI is required for the new migration/code/test head. PR #6 remains draft/unmerged, PAPER mandatory, live broker writes disabled, original `Tradepro` untouched.



## Versioned exchange-charge representation contract — 25 October 2026

- Added `backend/app/services/broker_charge_representation_contract.py` with pinned contract version `exchange-charge-representation-v1`. The validator requires an explicit reviewed representation mode, preserves original source labels, validates normalized component names and paise-precision amounts, and rejects combined transaction charges plus a separate IPFT amount to prevent double counting.
- Added `backend/tests/test_broker_charge_representation_contract.py` covering combined versus split representations, equivalent ₹307.00 exchange-charge base, duplicate IPFT rejection, missing components, unknown/inferred modes, invalid amounts, raw-label retention, and unsupported component labels.
- This contract validates representation only. It deliberately returns `accounting_approved: false`; it does not authenticate a source document, approve a broker API mapping, decide GST taxable composition, allocate aggregate amounts to fills, or enable live accounting. Existing promotion remains fail-closed.
- The implementation and test commits are `3c9ac46ea58257ba4c9c87b1b664eee14c6bd35a` and `be505e3dbc0e93eaa25a012d6a9afba81712e9ab`. Exact-head CI for the latest docs/code head must be checked before this checkpoint is called verified.
- PR #6 remains draft/open/unmerged; PAPER mode remains mandatory; live broker order writes and automatic generic quantity/notional allocation remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Persisted transaction/IPFT representation gate — 25 October 2026

- Added migration `202610250020` and nullable `source_label` / `representation_mode` fields on `broker_charge_source_components`. Existing rows retain their normalized component name as a source-label fallback, but representation mode is deliberately left undeclared rather than inferred.
- Source-component intake now preserves the original label and optional explicit mode. Review of `transaction_charges` / `ipft` rows invokes the versioned representation validator and remains blocked when mode is missing, when combined mode also has a separate IPFT row, when split mode lacks either row, or when sibling rows disagree on mode. Rejected review attempts leave rows pending.
- Added API regression tests for persisted label/mode, combined-plus-separate-IPFT rejection, and missing-mode rejection. Exact-head CI is required before calling this checkpoint verified.
- GST composition, endpoint/schema semantics, authenticated real contract-note evidence, and per-fill allocation approval remain separate gates. No live broker writes or generic quantity/notional allocation were enabled.


## Representation-gate CI correction — 25 October 2026

- The first API regression run exposed two assertion-message mismatches: the validator correctly rejected ambiguous combined-plus-IPFT input and undeclared representation mode, but the tests expected different wording. Updated the tests to assert the validator's actual fail-closed error messages; no safety rule was weakened.
- Follow-up exact-head CI for commit `df344e9c64aeb6ec3f2f01fef01f3c05739d4800` and subsequent documentation synchronization is pending. Do not call the current head green until the full workflow completes.


## Source-label completeness gate — 25 October 2026

- Source representation validation now requires one retained original label per normalized charge component. Missing labels fail closed before review; this is provenance hardening, not proof of API/contract-note semantics.
- Exact-head CI must pass after this documentation commit. Rates/mappings remain unapproved, aggregate and estimate amounts cannot be promoted to per-fill actuals, and live order writes remain disabled.
- Scope remains `tarunsharma2610-del/tradepro-improved` only; PR #6 draft/unmerged; PAPER mandatory; original `Tradepro` untouched.


## Authoritative IPFT/GST decision — 25 October 2026

This is the carried-forward project decision. Do not restart the IPFT/GST policy discussion or describe the agreed arithmetic as undecided. Keep the policy decision separate from remaining source-evidence and production-approval gates.

### IPFT and NSE exchange-charge representation

Effective 1 March 2026, NSE circular NSE/FA/73061 records combined exchange-charge rates that include the IPFT contribution:
- Cash equity: ₹307.00 per crore.
- Equity futures: ₹183.00 per crore.
- Equity options: ₹3,553.00 per crore.

Canonical equivalent split arithmetic (transaction charges excluding IPFT, plus IPFT exactly once):
- Cash equity: ₹306.99 + ₹0.01 = ₹307.00 per crore.
- Equity futures: ₹182.99 + ₹0.01 = ₹183.00 per crore.
- Equity options: ₹3,552.99 + ₹0.01 = ₹3,553.00 per crore.

Rules: combined source means use the combined amount and do not add IPFT; split source means use transaction charges excluding IPFT plus separately evidenced IPFT exactly once. Never infer mode from a field name. Preserve original labels, endpoint/schema/version and raw values. Missing, conflicting or ambiguous representation fails closed; null is not zero. This validator guards representation only and does not authenticate the source or approve a production API mapping.

Primary reference: NSE circular NSE/FA/73061, dated 27 February 2026, effective 1 March 2026: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf

### GST calculation policy

Use 18% GST on the applicable evidence-backed taxable service-charge base, using canonical components once. The working Upstox component policy recorded for the project is:
- Delivery: brokerage + transaction charges/IPFT + applicable demat transaction charges.
- Intraday, futures and options: brokerage + transaction charges/IPFT.
- If transaction charges already include IPFT, include the combined amount once; do not add IPFT again to the GST base. If split, combine transaction charges excluding IPFT with separately evidenced IPFT exactly once.
- Pure-agent/exclusion treatment applies only where the applicable tax rule and invoice evidence support it; do not assume all statutory or separately labelled charges are automatically excluded.
- Use product/segment/effective-date-specific rules, documented rounding and invoice reconciliation. Do not reuse a taxable base across products/dates without evidence.

Reference: https://upstox.com/brokerage-charges/

### Settled policy versus remaining gates

Settled policy: combined/split arithmetic above; never double-count IPFT; calculate GST from applicable canonical taxable components once; unknown representation fails closed.

Still required before production approval: corroborate actual Upstox API/contract-note field semantics with authentic evidence; approve effective-dated product/segment mappings and GST composition against invoices; test combined/split equivalence and no-double-count behavior in per-fill accounting; pass exact-head CI. Upstox Get Trade Charges is aggregate reconciliation evidence, not proof of actual per-fill charges. These evidence/implementation gates do not reverse the agreed calculation policy.

Safety: PAPER mode mandatory; live broker order writes disabled; PR #6 draft/unmerged pending review and user approval. Work only in `tarunsharma2610-del/tradepro-improved`; do not modify original `tarunsharma2610-del/Tradepro`.


## Phase 3 forward checkpoint — persisted representation-contract version (2026-10-25)

- Audited the actual branch and confirmed the previous source-label authenticity guard is already implemented and CI-verified at `b92d0185f588e24d54510b36659944e77f498a6e`; this task does not repeat that work.
- Added nullable `representation_contract_version` to `BrokerChargeSourceComponent` and migration `202610250021`. Null is retained for legacy/undeclared rows; the migration does not infer a version for historical records.
- The source-component intake API now accepts, stores, and returns the version. Review of transaction/IPFT components requires the supported persisted version and requires sibling transaction/IPFT rows to agree on both mode and version before the existing combined/split validator runs.
- Added API regression assertions for persistence and response round-trip. Implementation commit: `1d327b145fe25d871a763985b5f746e12e107b75`. Exact-head backend workflow [#40190287853](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40190287853) was **in progress when this checkpoint was written**; do not mark the implementation CI-verified until its conclusion is successful. The documentation commit will require its own exact-head CI as well.
- This is an auditability step, not tariff approval, source authenticity proof, GST approval, or authorization to promote more components. Live accounting still requires its existing six-component set; extra components remain fail-closed. Paper mode and live-order safeguards are unchanged; PR #6 stays draft/unmerged; original `Tradepro` remains out of scope.
- Next single implementation gate: define and persist an explicit versioned component-set contract that distinguishes supported canonical accounting components from retained evidence-only components, then add tests proving missing, extra, duplicate, mixed-representation, and legacy-version rows cannot be silently omitted or promoted.


### CI correction history — persisted representation-contract version (2026-10-25)

- Workflow [#40190287853](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40190287853) failed on `1d327b145fe25d871a763985b5f746e12e107b75` due to one existing API regression assertion expecting the previous validation error wording. The underlying fail-closed mode check was still rejecting the request; the test stopped on the message mismatch.
- Corrected the response wording without relaxing validation in commit `db1ee170629fcb853b5c6e46f0d9d8654056bc44`. The failure remains recorded as history and is not counted as a successful verification.
- Workflow [#40190403007](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40190403007) was triggered for documentation HEAD `0abfa9a1ed5dcd553f1b92010ec86b41ccf77a2b`; that SHA predates the wording correction and must not be treated as verification of `db1ee170629fcb853b5c6e46f0d9d8654056bc44`. Exact-head CI for the corrected implementation and current documentation head remains pending.
- Next action: confirm the corrected exact-head workflow succeeds, then add explicit missing-version API regression coverage and continue the versioned component-set contract. No tariff candidates are promoted; live accounting still requires the existing six canonical components.


## Phase 3 forward checkpoint — versioned canonical component set (2026-10-25)

- Added `broker_charge_component_set_contract.py` with explicit `live-fill-accounting-component-set-v1` and the exact six canonical accounting components: brokerage, STT, exchange charges, SEBI charges, stamp duty, and GST.
- Added nullable `component_set_version` to source-component records via migration `202610250022`. No version is backfilled for legacy records. Canonical components receive the current set version only during independent review; evidence-only components remain unversioned and cannot be silently counted as canonical.
- Live-fill promotion now checks the full non-rejected source-component set before accounting: missing/extra/duplicate components, null/unsupported versions, and unreviewed rows fail closed. Additional evidence labels are preserved but block promotion until an explicit reviewed mapping exists. The prior six-allocation check remains in place.
- Added contract tests for exact set, missing/extra/duplicate components, legacy version and unreviewed rows. Updated the real PostgreSQL race fixture to declare the set version explicitly.
- Implementation/test checkpoint: `f61cedd25f5982846774db3028fb646d2e108e07`. Exact-head CI [#40191140007](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40191140007) passed: **917 passed, 1 warning, 0 failures**. Broker-write boundary guard, SQLite/PostgreSQL migration round-trips through migration `202610250022`, and synthetic restore drill passed. Synthetic restore does not prove actual Oracle Cloud recovery.
- Prior failed CI remains documented: run [#40190926423](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40190926423) exposed a missing set-version value in the PostgreSQL concurrency fixture; the fixture was corrected in the verified commit above. It is not counted as a successful run.
- This does not yet map raw `transaction_charges` + `ipft` source rows to canonical `exchange_charges`, approve tariffs/GST, or enable promotion of evidence-only rows. Live broker writes remain disabled; PR #6 remains draft/unmerged; original `Tradepro` remains untouched.
- Next single implementation gate: define and test an explicit, versioned source-to-canonical mapping for combined versus split transaction/IPFT evidence, preserving both raw source rows while producing one canonical exchange-charge amount only when the representation is explicitly reviewed. Other unsupported source components must continue to block promotion.


## Phase 3 forward checkpoint — combined/split source canonicalization contract (2026-10-25)

- Added `broker_charge_source_canonicalization.py` and focused tests. The pure contract maps explicit COMBINED transaction/IPFT source representation to one canonical `exchange_charges` amount, or sums SPLIT transaction charges plus separately evidenced IPFT exactly once. It retains source-row associations in its result and rejects ambiguous/mixed versions, double mapping, duplicate/missing labels, invalid amounts, and unsupported clearing/demat/other components.
- Exact-head CI [#40191589060](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40191589060) passed on implementation/test commit `44c12acd133924711cd68c27f315d9298c6acfde`: **930 passed, 1 warning, 0 failures**. Broker-write boundary guard and synthetic restore drill passed. Synthetic restore is not actual Oracle recovery.
- Important boundary: this is a tested pure canonicalization contract, **not yet wired into the API review flow or durable allocation ledger**. It does not authenticate source notes, approve tariffs/GST, allocate canonical totals to fills, or enable live accounting. Do not count the end-to-end mapping gate as complete.
- Current branch/PR safety remains unchanged: work only in `tarunsharma2610-del/tradepro-improved`; PR #6 stays draft/unmerged; PAPER mode mandatory; live broker writes disabled; original `Tradepro` untouched.
- Next single implementation gate: wire this canonicalization contract into reviewed source-component validation and per-fill allocation persistence so raw source rows remain immutable, canonical exchange charges reconcile exactly, and promotion cannot omit or double-count source components.


## Phase 3 checkpoint — verified source-component canonicalization adapter (25 October 2026)

- Added `backend/app/services/broker_charge_verified_component_canonicalization.py` and focused tests in `backend/tests/test_broker_charge_verified_component_canonicalization.py`.
- The adapter accepts only persisted `VERIFIED` rows tied to the expected evidence ID and matching SHA-256, with INR currency, reviewer identity/timestamp, unique row IDs, and source locators. It delegates the six-component and combined/split transaction/IPFT rules to the existing canonicalization contract and returns source-record provenance.
- Output explicitly remains `accounting_approved=false`. This is a validation adapter, not yet the transaction-owning persistence/promotion integration. It does not prove broker-origin authenticity, establish GST/tariff applicability, or enable automatic allocation.
- Implementation commit: `d3a2fc076a4309f23edbb14b0a47ba41fec0b557`; regression-test commit: `c8e3748f12c5674b1b77e76ff8fcf9b8f3dc68a6`. Backend workflow [#40192336466](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40192336466) passed on code/test commit `c8e3748f12c5674b1b77e76ff8fcf9b8f3dc68a6`; Backend pytest and the synthetic PostgreSQL/document-volume restore drill succeeded. Subsequent commits only synchronize documentation; no application code changed after the tested code/test head. No workflow run is associated with the latest docs-only head, so report the code/test head as green but do not claim a separately verified exact-head CI run for the latest docs commit.
- Next implementation gate: integrate this adapter into the existing locked source-component verification/allocation-promotion path; persist canonical totals and source-row associations atomically, and test duplicate/replay/conflict, rollback, partial fill sets, and PostgreSQL concurrency before enabling any accounting promotion.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 remains draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion remain disabled; production tariff/GST/IPFT interpretations remain unapproved.


## Phase 3 checkpoint — canonical source-to-allocation planning (25 October 2026)

- Added `backend/app/services/broker_charge_canonical_allocation_plan.py` and `backend/tests/test_broker_charge_canonical_allocation_plan.py`. The planning boundary composes reviewed-source canonicalization with deterministic paise allocation, returning per-fill amounts and source-row provenance without database writes or accounting approval.
- Only `EXPLICIT_REVIEWED` weights are enabled pending approved component-specific tariff rules. Contributing source rows must share the canonical fill manifest/hash, explicit weights, basis and allocation-method version. Split transaction/IPFT values are combined once into canonical exchange charges before allocation.
- Tightened the verified-source adapter to reject same-user extraction and review; added regression coverage.
- Commits: planner `a3a51ce8257b2300ead83158c423772f420545f8`; planner tests `1dffc90897e524a3c4065740daf3b31f2aaabf03`; independent-reviewer guard `f17e75ab4cc8eef448dd4743b942a13b0af8d2d0`; guard test `18d69d5fee2a4a2668cdf32a8ad0661aba8adbe3`.
- Backend workflow `40193811936` was in progress at the latest check. Do not mark the newest code/test head green until CI completes and covers the latest test commit. Database persistence/promotion integration remains the next gate.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion disabled; GST/tariff/IPFT interpretations unapproved.


## CI follow-up — canonical allocation planner (25 October 2026)

- Backend workflow [#40193836363](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40193836363) passed on independent-reviewer test commit `18d69d5fee2a4a2668cdf32a8ad0661aba8adbe3`. Backend pytest, SQLite migration cycle, PostgreSQL 16 migration cycle, and synthetic PostgreSQL/document-volume restore drill all succeeded.
- A newer docs-only checkpoint commit triggered Backend workflow [#40193954195](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40193954195), still in progress at last check. Code/test head is green; latest documentation head is not yet confirmed green.
- Next: wait for exact latest-head CI, then connect planning output to the locked persistence/reconciliation service using source-row provenance and canonical component identity. Do not promote accounting until transaction and replay/concurrency tests pass.


## Phase 3 checkpoint — verified canonical allocation persistence boundary (25 October 2026)

- Added `backend/app/services/broker_charge_verified_allocation_persistence_service.py`. It locks reviewed evidence and source rows, requires the approved `live-fill-accounting-component-set-v1` of six independently reviewed direct-mapped components, builds the verified canonical plan, and delegates to the existing idempotent allocation persistence service. It leaves allocations `PENDING_RECONCILIATION`, never commits, and requires caller-owned outer transaction.
- Added persistence-boundary tests in `backend/tests/test_broker_charge_allocation_persistence_service.py` for successful direct-component allocation and rejection of an unapproved component-set version.
- Split transaction/IPFT planning is supported, but persistence deliberately rejects it until a durable canonical-component ledger links multiple raw source rows to one canonical exchange-charge component.
- Implementation commit `d92219dcae765c2b8a305a825ae10c4596315f6a`; tests commit `9a837155260d0f2fef4cd9fd9dee458b2db13f90`. Exact-head Backend workflow [#40194167945](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40194167945) was in progress at last check; do not mark the new boundary green until it completes.
- Next: inspect exact-head CI; if green, implement durable canonical-component/source-row associations for combined/split transaction/IPFT, then add rollback, replay/conflict and PostgreSQL concurrency tests.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion disabled; tariff/GST/IPFT interpretations unapproved.


## Phase 3 checkpoint — durable canonical source snapshots (25 October 2026)

- Added `BrokerChargeCanonicalComponent` model, migration `202610250023_canonical_charge_components.py`, model registration, and `broker_charge_canonical_component_snapshot_service.py`.
- The materializer locks reviewed evidence and source rows, verifies stored contract-note bytes against SHA-256/size, requires independent source review and the approved component-set version, canonicalizes reviewed rows, and creates six versioned canonical snapshots in `PENDING_REVIEW`. It preserves exact raw source row IDs, source fingerprint, mapping/representation version, amounts, fill manifest/weights, and allocation policy. Identical snapshots replay idempotently; changes to reviewed allocation metadata create a new revision.
- Tests cover direct snapshots, split transaction/IPFT mapping to one exchange-charge snapshot, idempotent replay, unverified rows, tampered source documents, and revisioning after allocation-metadata changes.
- Latest code/test commit: `af14297ee904b7b021fc149e3ac3adf2cb0743f1`. Exact-head Backend workflow [#40194614746](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40194614746) was in progress at last check; do not call the new snapshot model/migration green until it completes.
- Next: verify migration/test CI, then add a distinct reviewer workflow for canonical snapshots and adapt allocation reconciliation to reference canonical snapshot IDs/source fingerprints rather than assuming one raw source row equals one canonical component.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion disabled; production tariff/GST/IPFT interpretations unapproved.


## Phase 3 CI correction — canonical snapshot test (25 October 2026)

- Backend workflow [#40194614746](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40194614746) reported 1 failure and 951 passes. The failure was test-only: the split transaction/IPFT snapshot test passed string UUIDs to a SQLAlchemy UUID column query. Fixed the test to convert persisted source-row IDs to `UUID` objects in commit `0a7437b9b413f86832cc029b983751c25007e21a`.
- The prior run is not green overall. Verification of the correction is pending a new Backend CI result; do not report canonical snapshot work as green yet.
- The migration/model and snapshot materializer remain on the Phase 3 branch only. No live-order or accounting-promotion behavior was enabled.


## CI follow-up — canonical snapshot UUID test correction (25 October 2026)

- Corrected the split transaction/IPFT test to pass UUID objects to SQLAlchemy. Exact code/test commit `0a7437b9b413f86832cc029b983751c25007e21a` passed Backend workflow [#40194933563](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40194933563): pytest, broker-write boundary, SQLite and PostgreSQL 16 migration cycles, and synthetic PostgreSQL/document-volume restore all succeeded.
- Documentation-only head `408af47077c18ecbe22418bad8cae109cf8741ef` triggered Backend workflow [#40195063845](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40195063845), which was in progress at the last check. Do not claim that later documentation head green until it completes.


## Phase 3 checkpoint — independent canonical snapshot review (25 October 2026)

- Added `broker_charge_canonical_component_review_service.py` to review canonical snapshots separately from raw source-row review. It rechecks stored contract-note bytes, source-row IDs, current canonical mapping/amount, mapping and representation versions, and source fingerprint under locks. Only an active admin distinct from the snapshot creator, source reviewer, and extractors can mark a snapshot `VERIFIED` or `REJECTED`; decisions are immutable and exact replay is idempotent.
- Added tests for split transaction/IPFT review, independent reviewer enforcement, idempotent review replay, and rejection when a source locator changes after snapshot creation.
- New code/test commit `9bb7ebaeeaee62753ba7580cf1dc94400df5aea4`; Backend workflow [#40195392377](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40195392377) was queued at the latest check. Do not mark the new reviewer workflow green until CI completes.
- Next: verify this CI result, then extend allocation persistence/reconciliation to bind allocations to the verified canonical snapshot ID and source fingerprint, including combined/split transaction/IPFT.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion disabled.


## Phase 3 checkpoint — allocations linked to verified canonical snapshots (25 October 2026)

- Added nullable `BrokerChargeAllocation.canonical_component_id` plus migration `202610250024_link_allocations_to_canonical_components.py`. Historical rows remain NULL; no inferred backfill.
- Added `broker_charge_canonical_allocation_persistence_service.py`. It requires a `VERIFIED` canonical snapshot, re-runs independent snapshot integrity/reviewer validation, delegates to the evidence-locked idempotent allocation writer, and persists the canonical snapshot foreign key on every allocation. It never commits or marks allocations reconciled. Split transaction/IPFT can now be planned, snapshotted, independently reviewed, and persisted against one canonical exchange-charge identity.
- Added integration coverage for split transaction/IPFT snapshot review and allocation persistence, exact ₹307.00 reconciliation, snapshot foreign-key linkage, pending-only status, and idempotent replay. Corrected canonical snapshot code/test commit `0a7437b9b413f86832cc029b983751c25007e21a` passed workflow [#40194933563](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40194933563); independent snapshot review passed [#40195392377](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40195392377).
- Latest persistence test commit `be761f4064136662ea1e5c18fef0c2b40237a387`; Backend workflow [#40195695138](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40195695138) was in progress at last check. Do not call the new migration/persistence path green until it completes.
- Next: verify exact-head CI; then implement canonical-snapshot allocation verification and promotion so live-fill accounting validates canonical snapshot IDs and fingerprints instead of assuming one raw source row per canonical component.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion disabled.


## Phase 3 — normalized source-to-canonical charge links (25 October 2026)

- Added `BrokerChargeCanonicalSourceLink` and migration `202610250025_normalize_canonical_source_links.py`. The database stores a foreign-key row per canonical snapshot/source-row relationship, with uniqueness constraints for each pair and source order. Existing links are backfilled only from the snapshot's persisted ordered source-ID manifest; no mapping is inferred from labels or amounts.
- Snapshot creation persists normalized links and checks them on idempotent replay. Independent review requires normalized links, order and manifest to agree; missing or altered membership fails closed. This explicitly represents split transaction + IPFT as two raw rows belonging to one canonical exchange-charge snapshot.
- Previous branch head `4dbaf27fae124d11935c271f2f4cdec44015dbaa` passed Backend workflow [#40196030459](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40196030459). New normalized-link change `d1153a0f0751339f3ca82fc062701db0141d4749` awaits fresh CI verification.
- Next: verify migration upgrade/downgrade/re-upgrade on SQLite and PostgreSQL 16, then require normalized source membership and canonical snapshot fingerprint in promotion/reconciliation.
- Safety: only the Improved repository; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion remain disabled.


## Phase 3 — normalized source links and canonical reconciliation gate (25 October 2026)

- Normalized source-link migration passed Backend workflow [#40196529023](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40196529023), including pytest, broker-write boundary, SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade and synthetic restore drill.
- Added `broker_charge_canonical_allocation_reconciliation_service.py`: verifies canonical snapshot approval and fingerprint, normalized source-row links, exact reviewed fill manifest, deterministic paise amounts, INR/method/basis, totals and state; atomic promotion/replay uses a durable snapshot/fingerprint/fill-set reference and never commits the caller's transaction.
- Added split transaction/IPFT normalized-link, successful promotion/replay and tamper-blocking tests. Commit `621ce7cd289057a419be5eeff0262e158b18c001` Backend workflow [#40196784435](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40196784435) was in progress at checkpoint; latest reconciliation code is not marked green until completed.
- Next: fix any exact-head CI failures, then add conflict/rollback and PostgreSQL concurrency coverage before closing this Phase 3 gate.
- Safety: Improved repository only; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes remain blocked.


## CI result update — canonical reconciliation gate (25 October 2026)

- Backend workflow [#40196784435](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40196784435) completed successfully for code/test commit `621ce7cd289057a419be5eeff0262e158b18c001`. Pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade, and synthetic PostgreSQL/document-volume restore all passed.
- This verifies the normalized source-link schema and canonical allocation reconciliation tests at that code/test head. Later docs-only commits still need exact-head CI verification if a workflow is triggered.
- Next: explicit rollback/conflicting-set and PostgreSQL concurrent-promotion coverage, followed by fresh exact-head CI.

## AUTHORITATIVE CURRENT STATE — supersedes older next-step notes (25 October 2026)

Historical entries remain historical records; they must not override this current checkpoint.

- Repository: `tarunsharma2610-del/tradepro-improved` only. Branch: `phase3/durable-per-fill-charge-allocation`. PR #6 is open, draft, and unmerged. Never work in original `tarunsharma2610-del/Tradepro`.
- Latest verified implementation/test head: `3d8c4e1425825e6b996500ce9f24630d6352ff5e`.
- Exact-head Backend workflow [#40200645237](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40200645237) completed successfully. Pytest, broker-write boundary enforcement, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration upgrade/downgrade/re-upgrade, and synthetic PostgreSQL/document-volume restore all passed.
- Latest test `test_canonical_reconciliation_rejects_incomplete_allocation_fill_set` removes one row from a two-fill canonical set and confirms promotion fails closed, leaving the remaining row pending without a reconciliation reference.
- Completed; do not repeat: normalized canonical/source links, reviewed immutable snapshots, split transaction + IPFT provenance, durable per-fill allocations, canonical ledger verification, deterministic paise allocation, promotion/replay, tampered-allocation rejection, existing rollback assertions, and incomplete-fill-set rejection.
- **Next single implementation step:** inspect existing coverage and add PostgreSQL concurrent-promotion tests proving concurrent attempts cannot create partial/mixed states or inconsistent durable references. Add conflicting-set/rollback tests only where a real gap remains. Then run the full backend CI gate.
- CI protocol: on failure, diagnose/fix/rerun. On pass, update all 18 maintained checkpoint documents with exact SHA/run/result and next step, commit checkpoint, then verify CI on the checkpoint commit itself. Before resuming, refresh the live PR head and read docs from that exact SHA.
- GST/IPFT production tariff/account-specific acceptance is a separate evidence gate and does not block synthetic engineering tests. Unapproved tariff candidates remain DRAFT.
- Safety: PAPER mandatory; live broker order writes disabled; PR #6 stays draft/unmerged absent explicit authorization; original `Tradepro` untouched.



## Verified checkpoint — 2026-10-25
- Implementation commit `07df26a88d5eb9cbebc76a5654e10e00e38de171` passed Backend CI run #40204137793 on the exact commit: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40204137793
- Resolved the PostgreSQL reconciliation-reference length failure by widening `broker_charge_allocations.reconciliation_reference` from 200 to 320 characters and adding migration `202610250026_widen_charge_reconciliation_reference.py`; downgrade refuses destructive truncation.
- PostgreSQL concurrent-promotion coverage is now implemented and passed in that run. The latest docs checkpoint still requires its own exact-head CI verification.
- Next: after checkpoint CI passes, audit for a demonstrated conflicting-set/rollback coverage gap; add tests only if missing.
- After every CI: on failure diagnose/fix/rerun; on success update all 18 maintained checkpoint documents, commit checkpoint, and verify CI on that checkpoint commit.
- Safety: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker order writes disabled. GST/IPFT production tariff acceptance remains separate.


## Authoritative checkpoint — 26 October 2026 (documentation CI verified)

- Repository: `tarunsharma2610-del/tradepro-improved`; branch: `phase3/durable-per-fill-charge-allocation`.
- Latest implementation commit: `ac7d27f2c9922925483b5b906c484c0d5a4e3f53`; exact-head Backend CI [#40287765745 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40287765745).
- Documentation synchronization commit: `f90573d653c7103bf9cfdb1f867da97b176d3240`; its exact-head Backend CI [#40289107666 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40289107666). Backend tests, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore/evidence retention passed. Synthetic restore is not proof of actual Oracle Cloud recovery.
- Approved public Upstox STT/exchange rules are estimate-only. Account-specific actual charges, GST taxable-base composition, stamp duty, SEBI/DP/demat/other charges, unsupported exchange/segment mappings, and per-fill actual evidence remain unapproved. Candidate tariff entries remain DRAFT unless separately allowlisted and reviewed.
- Phase 3 remains in progress. Next gates: independently reviewed tariff applicability; component-specific per-fill allocation rules; invoice/source-backed GST/IPFT and product/segment evidence; final adversarial, migration and recovery review; exact-head acceptance sign-off. Do not repeat canonical live-fill integration.
- Safety: PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. PR #6 stays open/draft/unmerged without explicit user approval. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.
- This documentation commit’s CI is green. Continue only from this checkpoint and verify CI for every subsequent implementation/checkpoint commit. Historical entries do not supersede this checkpoint.


## GST/IPFT checkpoint — 26 October 2026

- Regression test `test_gst_arithmetic_is_invariant_for_combined_vs_split_ipft_representation` verifies equivalent synthetic representations produce ₹307.00 base and ₹55.26 GST at 18%; arithmetic coverage only, not approval of real taxable-component mapping. Test commit `8b4ae0b431d6aa03f1a8ae347a0b5fa7bda44c4f` passed exact-head Backend CI [run 40296066304](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40296066304).
- Official references: NSE circular `NSE/FA/73061` (27 Feb 2026; effective 1 Mar 2026) for combined transaction/IPFT outflows https://nsearchives.nseindia.com/content/circulars/FA73061.pdf; Upstox GST schedule https://upstox.com/brokerage-charges/; CBIC stock-broking FAQ and valuation Rule 33 https://cbic-gst.gov.in/sectoral-faq.html and https://cbic-gst.gov.in/valuation-rules.html.
- Production GST mapping remains blocked pending product/segment-specific review and reliable invoice/contract-note reconciliation. Never apply GST to trade notional/all charges indiscriminately or count separate IPFT twice; STT/stamp duty exclusion requires pure-agent conditions. Candidate tariffs remain DRAFT.
- Next gate: component-level GST acceptance cases across equity delivery, intraday and F&O, then exact-head CI and maintained-doc synchronization. PAPER mandatory, live broker order writes disabled, PR #6 draft/unmerged, original `Tradepro` untouched.


## Canonical latest Phase 3 checkpoint — 26 October 2026

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **Verified code/evidence head:** `d287da70ce184c904c6f9ede9e4a0edca5839f8f` (commit: “docs: reconcile public Upstox contract note GST examples”).
- **Exact-head CI:** PASS — [GitHub Actions run #40304398632](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40304398632), commit `d287da70ce184c904c6f9ede9e4a0edca5839f8f`; **1,004 passed, 1 warning**. Broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and restore-evidence retention also passed. This is CI evidence, not proof of a real Oracle recovery or broker-origin authenticity.
- **GST/IPFT research:** Three public third-party historical Upstox note copies were reconciled: 11-Feb-2025 base ₹2.97 / IGST ₹0.53; 21-May-2024 base ₹77.56 / IGST ₹13.96 (IPFT ₹0.11 listed outside that note's printed base); 12-Mar-2025 base ₹2.75 / IGST ₹0.50. Printed-base compositions differ historically. The current official Upstox schedule supports the **estimate-only** base of brokerage + transaction charges + demat where applicable + IPFT, with IPFT represented exactly once because it is combined with transaction charges. Do not add SEBI to this current estimate base without current applicable billing evidence; never calculate GST on trade notional or infer zero from missing/null fields.
- **Tax/accounting approval:** all four GST component candidates remain `DRAFT`. Historical public copies do not prove current actual per-fill billing across products/accounts. Actual-charge promotion stays gated; estimate logic and actual invoice reconciliation are distinct. Follow effective dates and preserve raw API/source evidence.
- **Next action when resuming:** continue Phase 3 from this exact commit and checkpoint. Next gate is component-specific GST acceptance cases for equity delivery, intraday, futures and options, then implementation review and exact-head CI; do not restart from earlier saved checkpoints.
- **Safety / PR:** PAPER mode mandatory; live broker `place_order`/`modify_order`/`cancel_order` and automatic live-fill promotion remain disabled. PR #6 remains open, draft and unmerged. Original `tarunsharma2610-del/Tradepro` is not the work target and must remain untouched.
- This checkpoint supersedes older statements in this document about CI being in progress or requiring verification for the pre-`d287da7` head. Historical notes remain history; this is the canonical resume point.

## Canonical resume checkpoint — 26 October 2026 (latest branch head verified)

- **Target:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **PR #6:** open, draft, unmerged. Never modify original `tarunsharma2610-del/Tradepro`.
- **Latest branch head before this documentation synchronization:** `5c929ff933d627dd81d5c32ec863843c2ef0f19b` (`docs: record deferred Algory plan in progress checkpoint`). Exact-head Backend CI **PASS**, run [#40315135121](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40315135121): **1,004 passed, 1 warning**. Broker-write boundary guard, SQLite and PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore and evidence retention also passed. Synthetic restore does not prove real Oracle recovery.
- **GST/IPFT finding:** the current official Upstox page supports an 18% **public-schedule estimate** base of brokerage + combined transaction/IPFT charges + delivery demat where applicable. Count combined transaction/IPFT once. CBIC FAQ Q77 makes exclusion of STT/stamp duty/other recoveries conditional on Rule 33 pure-agent conditions. Three public historical third-party notes show differing printed taxable bases (11-Feb-2025 ₹2.97/IGST ₹0.53; 21-May-2024 ₹77.56/IGST ₹13.96, with IPFT separately outside that printed base; 12-Mar-2025 ₹2.75/IGST ₹0.50). These notes are not authenticated current evidence and do not settle present account-specific billing.
- **Decision:** all four product GST component candidates remain `DRAFT`; actual per-fill GST promotion is blocked pending reviewed current source/invoice mapping. Never tax trade notional, infer zero from missing/null fields, or double-count IPFT. The Upstox aggregate charges endpoint is not per-fill evidence; the brokerage calculator is estimate-only.
- **Next gate:** continue Phase 3 product/segment-specific GST component acceptance and evidence reconciliation, adding tests only for demonstrated gaps. Do not repeat canonical live-fill integration or restart from older checkpoints. Defer AI/open-source adaptations, including Algory.app, until Phase 3 acceptance.
- **Safety:** PAPER mode mandatory; live broker order writes and automatic live-fill promotion/scheduling remain disabled. Do not merge PR #6 without explicit user approval. The documentation-sync commit must itself pass exact-head CI before it becomes the next validated checkpoint.

## Canonical checkpoint update — 26 October 2026, after cross-repository GST/IPFT audit

- Validated parent commit: `0e15bba3bfa425296f4104c96be6d10e3b42bf40`; Backend tests PASS on exact SHA, run [#40329710846](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40329710846). This documentation-only sync needs its own exact-head CI pass before it is the next validated checkpoint.
- Target repo/branch: `tarunsharma2610-del/tradepro-improved`, `phase3/durable-per-fill-charge-allocation` only. Never edit original `tarunsharma2610-del/Tradepro`.
- GST/IPFT: all four product component candidates remain `DRAFT`. OpenAlgo is architecture inspiration only; the inspected India preset is not an Upstox tax authority. Shoonya's hard-coded example is unverified; NautilusTrader applies to fee-model mechanics, not Indian tax rules.
- Discrepancy: Upstox's documented brokerage API example GST arithmetic does not align with current public tariff wording. This flags a docs-example discrepancy, not proof of live API miscalculation.
- Evidence gate: obtain current ordinary-trade Upstox contract notes/tax invoices or written broker clarification for delivery, intraday, futures and options. Reconcile taxable value against printed components and effective date. Historical rights-entitlement notes and estimate/aggregate APIs do not satisfy this gate.
- Invariants: count combined transaction/IPFT once; never add legacy IPFT on top of combined tariff; never tax trade notional; missing/null is unknown, not zero; do not treat aggregate charges or estimates as actual per-fill GST evidence.
- Next: continue Phase 3 evidence reconciliation and targeted tests only where supported by evidence. Do not repeat canonical live-fill integration. Defer AI/open-source integration including Algory.app until Phase 3 acceptance.
- Safety: PAPER mode mandatory; live broker order writes and automatic live-fill promotion/scheduling disabled; PR #6 stays draft/unmerged absent explicit user approval.


## GST/IPFT reconciliation checkpoint — 26 October 2026

- Official Upstox schedule https://upstox.com/brokerage-charges/ says GST is 18% on brokerage + transaction charges + IPFT, and includes DP/demat for equity delivery. From 1-Mar-2026, published NSE combined transaction/IPFT totals are cash ₹307/crore, equity futures ₹183/crore and equity options ₹3,553/crore on premium. Never add IPFT twice. NSE circular: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf (NSE/FA/73061, 27-Feb-2026).
- Open discrepancy: official Upstox Brokerage Details API example https://upstox.com/developer/api-documentation/get-brokerage/ shows transaction ₹5.68 + IPFT ₹0.17 but GST ₹1.02, matching 18% of ₹5.68 rather than ₹5.85 (approx ₹1.05). Treat as docs-example mismatch, not proven live production defect.
- Upstox Trades Charges API https://upstox.com/developer/api-documentation/get-trade-charges/ is aggregate by segment/date range and may return IPFT null; null is unknown, not zero, and aggregate output is not per-fill proof.
- Public third-party contract-note copies from 2024/2025 are historical, unauthenticated, pre-current-tariff and show differing taxable bases. They support historical layout/schema checks only.
- Estimate may follow current schedule with effective-date/product/exchange handling and combined transaction/IPFT counted once. Actual per-fill GST candidates for delivery, intraday, futures and options remain DRAFT pending current public invoice evidence or written Upstox clarification. No actual-charge logic promoted.
- Previous exact-head CI passed on 996b126ff678b97441f0214ea817451ee1592203: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40341429226 (tests, broker-write boundary, SQLite/PostgreSQL migration round-trips, synthetic restore and evidence retention). The next docs commit must pass its own exact-head CI.
- Scope: repository tarunsharma2610-del/tradepro-improved only; original Tradepro untouched. PAPER mandatory; live order writes and automatic live-fill promotion/scheduling disabled; PR #6 draft/unmerged; do not ask user for a personal contract note; defer AI/Algory until Phase 3 acceptance.


## GST estimate implementation update — 26 October 2026

- Added backend/app/services/upstox_public_gst_estimate.py and backend/tests/test_upstox_public_gst_estimate.py. This is public-schedule estimate logic only, not actual-charge evidence; it uses explicit components and an 18% GST rule and labels results PUBLIC_SCHEDULE_ESTIMATE_ONLY.
- Supported scopes from 1-Mar-2026: NSE EQ delivery/intraday, NSE FO futures/options, and BSE FO options. Delivery requires brokerage, exchange_charges and explicit demat_charges; other scopes require brokerage and exchange_charges. NSE exchange_charges includes combined transaction/IPFT once; separate ipft is rejected. For BSE options use applicable BSE charge source, do not assume an NSE IPFT component.
- Official Upstox API sample conflict remains: transaction ₹5.68 + IPFT ₹0.17 but GST ₹1.02; 18% of ₹5.85 is about ₹1.05. Estimate follows tariff wording, actual per-fill billing remains unresolved. Four actual GST component candidates remain DRAFT.
- See GST_IPFT_ACCEPTANCE_MATRIX.md. Code/test head 221493eb17729533cfaf855e2ce52532ef0903ac had CI run #40342805295 pending at note time; this documentation commit also needs exact-head CI.
- Scope/safety: only tarunsharma2610-del/tradepro-improved; original Tradepro untouched; PAPER mandatory; live writes and automatic live-fill promotion/scheduling disabled; PR #6 draft/unmerged; no personal contract note required; defer AI/Algory until Phase 3 acceptance.


## Authoritative GST decision — 26 October 2026

**Decision: implement the current official Upstox public-schedule GST base for estimates now; do not let the inconsistent API documentation sample block it.** Upstox's pricing page explicitly states GST at 18% on brokerage + transaction charges + IPFT, with demat charges additionally included for equity delivery. From 1-Mar-2026, NSE Circular NSE/FA/73061 defines combined transaction/IPFT outflows (cash ₹307/crore, futures ₹183/crore, options ₹3,553/crore premium); represent that as one exchange_charges component and never add IPFT twice. The supported estimate path sums brokerage + combined exchange_charges, and adds explicit demat_charges for delivery. STT, stamp duty and SEBI are not added to this published GST base.

The Brokerage Details API example showing transaction ₹5.68, IPFT ₹0.17 and GST ₹1.02 is internally inconsistent with that page: 18% × ₹5.68 = ₹1.0224 → ₹1.02; 18% × (₹5.68 + ₹0.17) = ₹1.053 → ₹1.05. Treat this as a documentation-example discrepancy, not evidence that current production billing is wrong. Public schedule takes precedence for estimates; the API example does not override it. Trades Charges API is aggregate and its ipft:null is unknown, not zero.

This resolves the public-schedule estimate rule. It does not certify account-specific invoice totals or per-fill actual GST. Keep actual accounting/promotion evidence-gated until invoice/source evidence or written broker clarification is available. A personal contract note from the user is not required. Official sources: https://upstox.com/brokerage-charges/ ; https://upstox.com/developer/api-documentation/get-brokerage/ ; https://upstox.com/developer/api-documentation/get-trade-charges/ ; https://nsearchives.nseindia.com/content/circulars/FA73061.pdf ; https://cbic-gst.gov.in/sectoral-faq.html


## Latest GST/IPFT implementation checkpoint — 26 October 2026

- Latest implementation + synchronized GST decision commit: b75a97f6cd0043c185375cc253b84a1e6d6bfea1.
- Exact-head Backend CI: PASS, run [#40345937942](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40345937942): 1,012 passed, 1 warning in 62.33s. Broker-write boundary guard, SQLite and PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore/evidence retention passed. Synthetic restore is not proof of real Oracle recovery.
- Public GST estimate rule resolved: 18% on brokerage + combined transaction/IPFT exchange_charges, with explicit demat_charges additionally for equity delivery. Never double-count IPFT; do not add STT, stamp duty or SEBI to this published estimate base. API example mismatch is a documentation-example discrepancy; it does not override the published Upstox schedule.
- Actual account invoice/per-fill GST is still evidence-gated; actual candidate records remain DRAFT. User is not required to supply a personal contract note. This does not block public-schedule estimate implementation.
- Scope/safety unchanged: only tarunsharma2610-del/tradepro-improved; original Tradepro untouched; PAPER mandatory; live broker order writes and automatic live-fill promotion/scheduling disabled; PR #6 remains open/draft/unmerged; AI/Algory deferred until Phase 3 acceptance.


## Cross-broker GST implementation update — 26 October 2026

New official-source comparison confirms the taxable GST component set must not be copied from one broker to another:
- Zerodha states GST on brokerage + SEBI charges + transaction charges: https://zerodha.com/charges/
- Dhan states GST on brokerage + transaction charges + SEBI turnover + IPFT/other tax: https://dhan.co/pricing/
- FYERS states GST on brokerage + exchange transaction + clearing + SEBI turnover + NSE IPFT: https://fyers.in/charges-list
- Upstox publishes brokerage + transaction charges + IPFT, with demat charges additionally for equity delivery: https://upstox.com/brokerage-charges/
- Angel One lists transaction charges and IPFT as separate rows; its published table alone does not settle whether a displayed exchange rate is combined for every effective period: https://www.angelone.in/exchange-transaction-charges
- NSE circular NSE/FA/73061 effective 2026-03-01 specifies total outflow as transaction + IPFT: cash ₹306.99 + ₹0.01 per crore, futures ₹182.99 + ₹0.01, options ₹3,552 + ₹0.01. Never add old IPFT rates on top of a combined total: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf
- CBIC stock-broking FAQ says STT/stamp-duty/other tax recoveries are outside GST value only when Rule 33 pure-agent conditions are met; otherwise section 15/Rule 27 valuation applies: https://cbic-gst.gov.in/sectoral-faq.html

Code now includes a generic public-schedule estimate function for source-backed DRAFT/REVIEWED policies. It preserves broker/scope/date/source provenance, requires an exact component set, uses Decimal and paise rounding, and cannot approve a policy or promote actual accounting. Added tests use differing broker component sets as fixtures only; they are not a production-approved tariff registry. Actual invoice reconciliation, policy review, DP/demat persistence and exact-head CI remain separate gates. PAPER-only; live writes disabled; PR #6 and #7 remain Draft/unmerged; original Tradepro repository remains out of scope.


## Session checkpoint sync — 26 October 2026

- Verified exact-head Backend CI run [#40368554399 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40368554399) on code head `9d3f255480da9a71980a9d3819fbb69a34835753`; Backend pytest job completed successfully.
- GST public-schedule estimate helper and tests are present at this head. This is estimate-only; it does not approve actual accounting or promote estimated amounts as actual charges.
- Statutory direction from CBIC: use CGST Act section 15 and CGST Rules Rule 33/Rule 27 with the CBIC stock-broking FAQ. Pure-agent exclusion is conditional on evidence; do not automatically include/exclude every STT, stamp, transaction, IPFT, SEBI or demat line. IGST Act section 12(12) provides the stock-broking place-of-supply rule; state comparison determines IGST vs CGST+SGST. Sources: https://cbic-gst.gov.in/sectoral-faq.html ; https://cbic-gst.gov.in/valuation-rules.html ; https://cbic-gst.gov.in/central-excise-rules.html
- Next session: implement a standalone statutory GST valuation engine and focused tests (Section 15 inclusion, documented Rule 33 evidence, state-based tax split, Decimal/paise rounding, fail-closed missing facts). That engine is **not yet implemented**, so GST/IPFT acceptance is not complete. IPFT combined/separate representation and DP/demat persistence/reconciliation remain separate gates.
- No personal contract note is available or required to continue implementation. Public sources support research but do not prove actual per-fill accounting acceptance.
- Safety: only `tarunsharma2610-del/tradepro-improved`; PR #6 and #7 remain Draft/unmerged; PAPER-only; live order writes disabled; original `tarunsharma2610-del/Tradepro` out of scope.


## Phase 3 CI synchronization — 26 October 2026 (GST/IPFT resolver)

- Latest verified code head: `13e201661d26b04c9bf75bb7e3aaf567ad1e69c4`; exact-head Backend CI [#40378072884 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40378072884): **1,056 passed, 1 warning**. Broker-write boundary, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill and retained restore evidence passed.
- Added scope/effective-date-selected GST policy resolution for `COMBINED`, `SEPARATE`, and `NOT_APPLICABLE` IPFT representation. It rejects double representation, wrong-exchange reuse, missing/extra components, and unapproved or out-of-window policies. This is estimate-policy plumbing, not actual invoice reconciliation or tariff approval.
- Next Phase 3 gate: persist optional DP/demat charges safely, migrate canonical accounting/persistence and total-charge recomputation, then integrate statutory GST valuation only through reviewed source-backed policy paths. Actual per-fill invoice acceptance remains evidence-gated; no personal contract note is required.
- Safety unchanged: PR #6/#7 Draft and unmerged; PAPER mandatory; live broker order writes and automatic live-fill promotion/scheduling disabled; original `tarunsharma2610-del/Tradepro` untouched and out of scope.


## Phase 3 CI synchronization — 26 October 2026 (DP/demat snapshot gate)

- Latest verified code head: `6a6a3560aff18bb94d34b77640058a17d2a208b8`; exact-head Backend CI [#40381396722 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40381396722): **1,057 passed, 1 warning**. Broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore drill and retained restore evidence passed.
- Optional `demat_transaction_charges` can now be represented as a distinct pending canonical snapshot and allocated into the durable per-fill allocation ledger when source rows are independently reviewed. Migration expands the canonical snapshot vocabulary. It does **not** authorize final accounting: DP/demat reconciliation promotion deliberately fails closed until Execution persistence and total-charge recomputation are implemented.
- Next Phase 3 gate: add dedicated optional Execution DP/demat persistence and a single verified total-charge recomputation path, with migration/idempotency/rollback and delivery-vs-non-delivery tests. Keep actual invoice/per-fill acceptance evidence-gated; no personal contract note is required.
- Safety unchanged: PR #6/#7 Draft and unmerged; PAPER mandatory; live broker order writes and automatic live-fill promotion/scheduling disabled; original `tarunsharma2610-del/Tradepro` untouched and out of scope.

## Verified checkpoint — 27 October 2026 (DP/demat completeness)

- Exact-head Backend CI #40459846143 passed on `9400bc9aa221e2cf3b735e49a8e9a6d351237f02`: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40459846143. Backend tests, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore passed; synthetic restore is not production Oracle acceptance.
- API regression added for invalid DP status through `ExecutionOut`; inconsistent status/amount and ineligible DP manifest cases fail closed. Next: per-fill source mapping, replay/idempotency conflicts, rollback atomicity, and component applicability.
- Actual contract-note and production Oracle backup/restore acceptance remain evidence-gated. Safety: target only `tradepro-improved`; original `Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker writes disabled.


## Annual GST statement reconciliation finding — 27 October 2026

- A user-provided Upstox/RKSV annual global transaction statement for FY 2022–23 is annual aggregate evidence, not an individual contract note. Its visible charge rows do not by themselves establish a unique taxable base for the reported aggregate GST at paise precision.
- Preserve source-row labels exactly; do not relabel an STT rounding row as SEBI fees. Determine the base from underlying invoice/contract-note lines and the historical policy, not by selecting a charge merely to force arithmetic to match.
- The reconciliation helper retains reported-vs-expected variance instead of inferring or rewriting the base. Annual variance may reflect invoice-level rounding/aggregation or a charge omitted from the summarized lines; the annual statement alone cannot distinguish these.
- Do not use annual AGS totals to approve actual per-fill GST or promote canonical allocations. Next evidence gate: an itemized individual contract note or invoice-level breakdown. Keep FY 2022–23 evidence separate from the 2026 public-schedule estimate policy.
- This clarifies evidence scope; it does not change GST/IPFT policy or establish that the broker billed incorrectly. Personal identifiers and account-specific figures are intentionally not copied into this repository note.
- Latest code/test head before documentation sync: `9eb278588b78d2a966cc196c15d7a4d9a6ae8868`; Backend CI [#40505176395 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40505176395). This documentation update requires exact-head CI before it is marked green.
- Safety: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.


## API-first paper-trade charge estimation decision — 29 October 2026

- User-approved behavior: use Upstox's pre-trade Brokerage Details API for paper-fill charge estimates when it returns a complete, valid, internally consistent breakdown. Keep the existing deterministic local calculator as the automatic fallback if the API is unavailable, expired/unauthorized, incomplete, null/invalid, or inconsistent. This is estimation only, not live-trading/accounting promotion.
- Implementation added on the Phase 3 branch: `backend/app/services/paper_trade_charge_estimator.py` plus deterministic tests. `ExecutionService` now uses API-first estimates for market and matched limit paper fills and records `PAPER_UPSTOX_API_ESTIMATE` versus `PAPER_ESTIMATE` in the existing execution charge-source field. Components are accepted only when paise-exact supported components sum exactly to the API total; transaction, clearing and IPFT are combined once in the existing exchange-charge field. Unknown/incomplete fields fall back rather than block paper trading.
- Existing post-trade Upstox charges endpoint remains aggregate reconciliation evidence, not per-fill actuals. The API route already exists. GST reconciliation remains available without blocking paper-trade P&L.
- Implementation commits: `b90c09dc82a51181bc9eae422cb025eb79c65bcb`; default-enabled setting `UPSTOX_CHARGE_ESTIMATES_ENABLED`. CI disables network estimates only for the broad execution suite; mocked estimator tests cover API and fallback paths.
- Backend CI [#40755234415](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40755234415) — **SUCCESS** on code/test head `778e76d3554a3baedc41f0396276c1cb3dafc38f`: **1,197 passed, 1 warning**; broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic restore/evidence retention passed. Documentation sync head `d57dd476ecd6acebd4dc9e169912b877811a8166` still needs exact-head CI verification before it is called green.
- Next: continue the next uncovered Phase 3 accounting acceptance gate after CI recovery. Do not reopen GST/IPFT from zero or make minor estimate variance a paper-trading blocker. Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled; original `Tradepro` out of scope.


## Authoritative Phase 3 engineering closure — 29 October 2026

This section supersedes older status/next-step notes above; earlier entries remain as historical audit trail.

**Status: Phase 3 engineering acceptance is complete for the agreed PAPER-mode scope.** This is not authorization to enable live broker writes, promote estimates to booked actuals, or merge Draft PRs.

**Verified exact code/checkpoint head before this documentation closure:** `3a0c464afcb10261d1590607f8440affd21295a0`, Backend CI [#40878367369 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40878367369). Backend pytest: **1,207 passed, 1 warning**. Broker-write boundary, SQLite upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and retained restore evidence all passed.

### Phase 3 engineering exit criteria completed

- Deterministic paise-exact per-fill charge allocation, source-document integrity and reviewer controls, canonical source-to-component mapping, and explicit combined/split transaction-charge/IPFT representation.
- Replay/idempotency and conflicting-replay rejection; component totals revalidated under locks; rollback safeguards protect accounting/position mutations.
- Optional DP/demat persistence and total-charge completeness are explicit. Delivery SELL cannot be treated as complete when DP evidence is missing, unknown, invalid, or inconsistent.
- GST valuation and GST/API comparison primitives are implemented with Decimal/paise validation, state/place-of-supply handling, missing/null/zero distinctions, and review-required variance states. Estimates/comparisons never silently approve actual accounting.
- Upstox Brokerage Details API is the preferred PAPER estimate. Invalid/unavailable API results use the deterministic hardcoded calculator. The source label is preserved as `PAPER_UPSTOX_API_ESTIMATE` or `PAPER_HARDCODED_FALLBACK`; both expose: “Estimated charges may differ from actual broker charges. For paper trading only; these are not actual booked charges.”
- Upstox post-trade Trade Charges API remains aggregate reconciliation evidence and is explicitly prohibited from per-fill actual promotion. Aggregate responses are sanitized before persistence/return.
- CI on the verified code head passed the complete backend and safety/migration/restore workflow.

### Explicit non-blocking operational/release gates

These are not reasons to keep Phase 3 engineering open, but remain mandatory before any live-money release or claim of production acceptance:

1. Run a user-authorized, credentialed Upstox OAuth/API smoke test in the deployed environment; CI does not prove account-specific entitlements or token validity.
2. Run and retain a real Oracle/database-plus-document-volume backup/restore drill after deployment; synthetic restore is not production backup acceptance.
3. Keep any broker/exchange/segment/product/date tariff without independently approved source evidence in estimate-only/fail-closed status for actual accounting. This does not block PAPER trading.
4. Real contract-note data remains the source for actual booked charges. Historical contract-note fixtures are regression evidence; API estimates and aggregate summaries must never be represented as per-fill booked actuals.
5. The GST/API comparison remains diagnostic, not automatic invoice approval. No GST/IPFT variance silently rewrites a charge or blocks ordinary PAPER simulation.

**Safety invariants unchanged:** only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` untouched; PR #6/#7 remain Draft and unmerged; PAPER mode mandatory; live broker order writes disabled.

**Next project phase:** proceed to Phase 4 as a separate increment after this documentation-head CI passes. Keep Upstox developer integration and UI work in their planned later order; do not mix them into Phase 3 or merge the Draft PRs without explicit authorization.

## Final documentation-head CI verification — 29 October 2026

The documentation sync head `5bb6d06e764c00b1ab406409889a2cde9e74dacf` passed Backend CI #40880169125 — SUCCESS: 1,207 passed, 1 warning; broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic restore drill, and evidence retention all passed.


## Resume checkpoint — 29 October 2026 (Upstox response-schema validation)

- **Code/test head:** `404c1e11ef4f2557c791c720c8d9a3fbc4e93bc1`; exact-head Backend CI [#40883660756 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40883660756). The workflow result confirms success; its summary did not expose a reliable pytest count, so no count is asserted here.
- **Concrete fix:** `UpstoxChargeApiOrchestrationService` no longer marks arbitrary successful HTTP JSON as usable. Brokerage estimates require `status == "success"` and `data.charges`; post-trade aggregate charges require `status == "success"` and `data.charges_breakdown`. Wrong/missing schema returns `usable=false`, clears the payload and records `INVALID_RESPONSE_SCHEMA`.
- **Regression coverage:** valid endpoint-specific response fixtures plus incorrect endpoint schema, unsuccessful/missing status, and aggregate wrong-shape payload cases.
- **Evidence boundary:** Brokerage Details remains estimate-only; Trade Charges remains aggregate reconciliation-only and never per-fill actual evidence. Null IPFT must not be silently coerced to zero. This fix validates response shape; it does not approve tariffs or promote accounting.
- **Contract-note continuity:** previously supplied January 2023 Upstox/RKSV contract-note examples remain available as historical regression fixtures; do not ask the user to provide them again. Their scope must be respected when using them for GST totals versus per-fill allocations.
- **Next:** verify CI on the exact synchronized documentation head. Keep PR #6/#7 Draft and unmerged, PAPER mode mandatory, live broker writes disabled, and the original `tarunsharma2610-del/Tradepro` repository untouched.


## Phase 4 current checkpoint — 30 October 2026

The transactional PAPER stop-event claim implementation at `6ac3882a98f3c66abb4cd62848971b6277ab3be7` passed exact-head Backend CI #41080156436. The claim service validates tenant and strategy ownership, uses portfolio → strategy → position locks, rejects ambiguous shared-position ownership and duplicate quote identity, and stores a bounded claim lease. It is not connected to quote dispatch or order execution. Next gates: PostgreSQL 16 multi-worker concurrency, lease reclaim/crash recovery, explicit shared-position ownership, then controlled PAPER integration. PR #9 stays Draft/unmerged; PAPER-only; live broker writes disabled; original Tradepro repository out of scope.
