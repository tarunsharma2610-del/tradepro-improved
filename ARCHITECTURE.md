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
- Exact-head Backend CI: [run #40294178677 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40294178677). This includes the updated test separating NSE/IPFT arithmetic reconciliation from GST taxable-base approval.
- GST estimate helper accepts exactly 18%; tests reject 0%, 5%, 100%, and 100.01%. This is a rate guard only; taxable component composition remains evidence/reviewer-controlled.
- NSE/IPFT reconciliation of ₹307/crore versus ₹306.99/crore transaction charge + ₹0.01/crore IPFT is arithmetic only; it does not approve either component's GST treatment.
- Canonical live-fill integration is already verified: six independently verified charge snapshots; source hashes/links/mapping version, reviewed fill manifest/weights, INR totals, reconciliation and contract-note reference revalidated under lock; no raw-only fallback. Brokerage cap applied once before deterministic paise-exact allocation by reviewed weights.
- Remaining Phase 3 gates: effective-dated tariff applicability; component-specific per-fill allocation acceptance; invoice/source-backed GST/IPFT and product/segment evidence; adversarial/migration/recovery review; final exact-head docs/sign-off. Do not redo canonical integration.
- Upstox calculator/public schedules are estimates; aggregate charges endpoint is not actual per-fill evidence. Preserve null as unknown, never zero. Synthetic restore is not actual Oracle recovery.
- PAPER mandatory; live broker order writes, automatic live-fill promotion and automatic scheduling disabled. PR #6 open/draft/unmerged unless explicitly approved. Defer AI/open-source adaptations until Phase 3 acceptance. Documentation commit needs its own exact-head CI.

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

- Backend CI passed on commit `1fcbb06a78fd06226f0e0e6438cf72b422dc2d4e`: **563 passed, 1 warning**. Broker-write boundary guard, SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks, and the isolated synthetic database/document-volume restore drill all passed.
- This result validates that code commit only. Documentation changes require exact-head CI again.
- Synthetic restore evidence does not prove recovery of real Oracle Free Cloud data or authenticity of a real broker contract note.
- PR #6 remains draft and unmerged pending accounting/idempotency review and explicit user approval. Live broker writes remain disabled.
- Real contract-note and retained real-backup/restore evidence remain pending; the user plans to provide these later.
- Repository scope is `tarunsharma2610-del/tradepro-improved` only. Do not modify the original `tarunsharma2610-del/Tradepro`.

## Current Phase 3 checkpoint — 21 October 2026

- **Latest verified code/test HEAD:** `3963c2bf4e6ffe2bb33d327b10e2995cd243d003`. Exact-head [Backend CI run 39607630055](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39607630055) passed **484 tests, 1 warning in 29.34s**; the broker-write boundary guard passed, and SQLite/PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed.
- New Phase 3 guard: broker-reported live-fill charge references are trimmed for storage and rejected when longer than the `Execution.charge_reference` 200-character column limit. This prevents a predictable storage error from being misreported as a concurrent promotion conflict. Regression coverage is included in the 484-test result.
- The existing Phase 3 safety gates remain active: replay must match the accounted fill and exact charge evidence; only broker-reported, internally consistent charges with a non-empty audit reference are accepted; durable staged trade quantities must match broker-confirmed child fills before promotion; exchange-time ambiguity/out-of-order fills fail closed; paper positions and cash remain isolated.
- **Phase 3 remains in progress, not complete.** Remaining review includes coordinator/identity boundaries, charge provenance/allocation semantics, full partial-fill and crash/restart acceptance criteria, and any explicitly selected bridge design. Keep `BrokerFillIdentity` separate from manual `BrokerTradeRecord` unless a reviewed Phase 3 design explicitly authorizes a narrow bridge.
- Live broker submission, automatic accounting promotion, and automatic scheduling remain disabled. The original `tarunsharma2610-del/Tradepro` repository remains untouched. Phase 2 remains closed.
- This checkpoint describes the verified code commit above. The documentation synchronization commit will trigger its own CI; do not treat that documentation commit as green until its exact-head run passes. Older checkpoint entries below are historical audit trail, not current status.

---

## Current verified checkpoint — 21 October 2026

- **Last verified code/test checkpoint:** `00ee9bad0e962d92244da6f63da1e46ba058ad6f`; exact-head backend CI [run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) passed **472 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 reversible migration checks.
- **Last verified documentation checkpoint before this status refresh:** `391dfefc9580abf9537ee659877578033baae4fd`; exact-head backend CI [run 39568264419](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39568264419) passed.
- The Phase 2 audit covers the dependency/port matrix, broker-fill workflow boundary, idempotency and rollback, reconciliation crash recovery, transaction-level lease fencing, slow persistence, 20 concurrent expiry-boundary renewal/reclaim races, and official Upstox current-day API semantics.
- Official Upstox V2 [order-book](https://upstox.com/developer/api-documentation/get-order-book/) and [get-trades-for-day](https://upstox.com/developer/api-documentation/get-trade-history/) endpoints are current-day endpoints without documented pagination parameters. Historical trades use a separate [paginated API](https://upstox.com/developer/api-documentation/get-historical-trades/); it is not wired into the Phase 2 worker.
- **Phase 2 technical checklist is complete.** Before any Phase 3 work, require a passing exact-head CI run for the then-current `main` and explicit user approval; never infer a later commit is green from an earlier run.
- Live broker submission, automatic accounting promotion and automatic scheduling remain disabled. The original `Tradepro` repository remains untouched.

---

## Current verified checkpoint — 21 October 2026

- **Verified code/test checkpoint:** `00ee9bad0e962d92244da6f63da1e46ba058ad6f`; exact-head backend CI [run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) passed **472 tests, 1 warning**, the broker-write boundary guard, and SQLite/PostgreSQL 16 reversible migration checks.
- **Previously verified documentation checkpoint:** `a2e639f61e2c50070deb26d1a9a0741545c9737d`; exact-head backend CI [run 39568011689](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39568011689) passed. This is historical evidence for that SHA; every new commit still requires its own exact-head CI.
- The slow-persistence/lease-race audit is complete: the PostgreSQL row-lock test proves reclaim waits while a fenced write transaction is open; `test_postgres_high_volume_expiry_races_never_resurrect_stale_lease` passed 20 concurrent expiry-boundary renewal/reclaim races. Expired owners cannot renew, and ownership generation/token advance is verified.
- Official Upstox V2 [order-book](https://upstox.com/developer/api-documentation/get-order-book/) and [get-trades-for-day](https://upstox.com/developer/api-documentation/get-trade-history/) endpoints are current-day endpoints without documented pagination parameters. Historical trades use a separate [paginated API](https://upstox.com/developer/api-documentation/get-historical-trades/); it is not wired into the Phase 2 worker.
- Phase 2 technical audit and scope reconciliation are complete. Keep Phase 3 blocked until this final documentation commit's exact-head CI passes. Do not enable live broker submission, automatic accounting promotion or automatic scheduling. The original `Tradepro` repository remains untouched.

------

<!-- Authoritative checkpoint audit: 2026-10-21; supersedes older status notes below. -->
## Historical checkpoint audit — 21 October 2026 (superseded)

- **Repository/branch:** `tarunsharma2610-del/tradepro-improved`, `main`. The original `tarunsharma2610-del/Tradepro` repository is a protected baseline and must remain untouched.
- **Latest repository HEAD before this audit update:** `a297b1a356c133aaca0ed10079eb5226c03b747b` — documentation-only commit `docs: synchronize Phase 2 status with passing CI evidence`.
- **Latest code/test commit:** `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`. Recorded exact-commit backend CI run [39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed **466 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles. Frontend run [39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript and Next.js build.
- **Previously verified documentation CI:** commit `6407c5a05865c1be0ef673d3bb5e71c0231ef8da`, run [39556816828](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556816828), backend job completed successfully. The later documentation-only commit `a297b1a356c133aaca0ed10079eb5226c03b747b` was found on `main`; CI for that exact HEAD was not independently established before this audit update. Do not infer exact-head CI success from an earlier commit.
- **Phase 2 checkpoint verified in project records:** atomic run/lease finalization; stale-owner protection; cancellation and interrupted-run recovery; inconsistent lease token/expiry rejection; five-record renewal boundary; and incomplete-summary warnings for `WORKER_INTERRUPTED` and `LEASE_LOST`.
- **Historical audit disposition — superseded:** slow database persistence and high-volume lease-expiry/renewal races are now tested and passed in CI run [39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386).
- **Safety constraints remain:** no real broker orders in tests; live broker submission, automatic accounting promotion, and automatic scheduling remain disabled; keep `BrokerFillIdentity` separate from `BrokerTradeRecord`; do not wholesale-merge the divergent safety branch.
- Older checkpoint entries below are retained as history, not current instructions. This top section is the authoritative current state. After this documentation commit, verify CI for its exact HEAD before treating the checkpoint audit as fully closed.

<!-- Latest verified status, updated 2026-10-21 -->
> **Latest verified checkpoint — 21 October 2026**
>
> - Repository: `tarunsharma2610-del/tradepro-improved`; branch: `main`. Original `Tradepro` repository remains protected and untouched.
> - Latest code/test commit: `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`. Backend [CI run 39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed **466 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration checks. Frontend [CI run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript and Next.js build.
> - Documentation audit commit `6407c5a05865c1be0ef673d3bb5e71c0231ef8da` passed [CI run 39556816828](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556816828).
> - Phase 2 checkpoint complete through atomic run/lease finalization, stale-run and cancellation recovery, lease-loss fencing, five-record renewal, and incomplete-summary warnings.
> - **Historical next-task note — completed:** the slow-persistence lock test and 20-round concurrent expiry-boundary renewal/reclaim regression passed in CI run [39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386).
> - Deferred safety-branch work remains tracked in `SAFETY_BRANCH_PORT_MATRIX.md`; no wholesale branch merge. Keep live broker submission and automatic accounting promotion disabled. Keep `BrokerFillIdentity` separate from `BrokerTradeRecord`.
>
> The CI status above refers to the stated code and documentation commits. This documentation refresh will create a new commit and trigger its own CI run; do not call that new run passed until GitHub reports success.

# Architecture notes

## Credential tiers — why almost nothing lives in `.env`

Everything sensitive the platform ever handles falls into one of three tiers:

**Tier 0 — bootstrap secrets (`.env`, irreducible).**
`POSTGRES_PASSWORD`, `SECRET_KEY` (JWT signing), `MASTER_ENCRYPTION_KEY`
(encrypts everything in Tier 1 and 2). These have to exist before the app
can even open a database connection or decrypt anything stored in it — you
can't put the key to the safe inside the safe. `setup.sh` generates all
three for you; you should never need to hand-type one. This is the only
tier that lives in a file.

**Tier 1 — platform-wide integration keys (admin Settings UI, DB-encrypted).**
WhatsApp Business token, Telegram bot token, AI provider key, News API
key. One value each, shared by the whole platform, set once by whoever has
`is_admin = true`, editable without redeploying. See
`app/services/platform_settings_service.py`.

**Tier 2 — per-user broker credentials (user Settings UI, DB-encrypted).**
Each user's own Upstox API key/secret/access token. This has to be
per-user regardless of the `.env` question — in a multi-tenant SaaS, a
single global broker credential wouldn't make sense once there's more than
one user trading under their own broker account. See
`app/services/broker_credentials_service.py`.

Tiers 1 and 2 use the same encryption (Fernet, keyed by
`MASTER_ENCRYPTION_KEY`) and the same rule: a value is never sent back to
the browser in full, only masked (`app/core/encryption.py:mask_secret`),
and a broker connection is never marked `is_connected` on the strength of
having *saved* credentials — only after a real, successful call to the
broker's API (`BrokerCredentialsService._verify_and_update`). That
distinction exists on purpose: an earlier project in this line
(TradeBot AI) showed demo data instead of live prices because a
credentials-related assumption didn't hold up in production, and the
"never present fake data as real" rule this project runs on takes that
lesson literally, not just as a policy statement — see
`tests/test_broker_credentials.py` for the regression test written
specifically against that failure mode.

## The shared order/position/execution model (Phase 2)

`Order`, `Position`, and `Execution` (`app/models/order.py`,
`position.py`, `execution.py`) are the one conceptual model manual
trading uses now and auto-trading, backtesting, and live trading will use
later — not three separate implementations that happen to look similar.
Concretely: `Order.execution_reason` is `"MANUAL"` today and will be
`"STRATEGY"` or `"BACKTEST"` later; `Order.strategy_id` is unused today
and populated starting Phase 3. Adding those phases means new rows with
different values in existing columns, not new tables or a rewrite of
`ExecutionService`.

`Position.quantity` is signed (positive = long, negative = short) on
purpose — see `app/services/position_math.py`. This is what lets the same
column represent an intraday short sale or, later, a written option,
without a separate short-position concept bolted on afterward.

`ExecutionService.place_order()` never fills against an invented price.
MARKET orders fetch a real LTP from the user's connected broker
(`BrokerCredentialsService.get_access_token` +
`BrokerAdapter.get_quote`); if there's no live connection or the quote
call fails, the order is REJECTED with a specific reason and recorded as
such — not silently skipped, not filled at a guess. This is the same
"never present fake data as real" principle from Phase 1's broker
`is_connected` handling, applied to fills.

## Transaction cost engine

`app/services/transaction_costs.py` is pure — no DB, no I/O, just Decimal
arithmetic — specifically so its rate table is the one place to update
when STT, exchange charges, SEBI fees, stamp duty, or Upstox's brokerage
schedule change (which they do, on a government/exchange timetable no
one controls; the F&O STT hike that took effect 1 April 2026 is a recent
example). The module docstring records which rates were independently
corroborated at implementation time (STT, SEBI fee, stamp duty) versus
which are best-effort approximations worth reconfirming (exchange
transaction charges, the exact Upstox delivery-brokerage figure).

Every cost component (brokerage, STT, exchange charges, SEBI charges,
stamp duty, GST) is stored on `Execution` individually, not collapsed
into one number — the spec calls for preserving gross P&L, transaction
costs, and net P&L as distinct, auditable figures, and that only works if
the components survive past the moment they're calculated.

## Automated strategy trading (Phase 3)

`Strategy` (`app/models/strategy.py`) is the "no-code builder" — every
field on it is something a plain form field sets: which instrument, five
indicator weights, entry/exit score thresholds, a trailing-stop
percentage, a daily loss limit. There's no drag-and-drop canvas, no rule
DSL to parse — that tradeoff was made deliberately over attempting a full
visual programming surface in this pass.

Three modules stay separate on purpose, mirroring how `transaction_costs.py`
and `position_math.py` stayed separate from `execution_service.py` in
Phase 2:
- `indicators.py` — five pure functions, each candle-series-in,
  bounded-score-out. Nothing about strategies or weights here.
- `strategy_engine.py` — combines those five scores into one composite
  score (weighted average) and turns a score into an ENTER/HOLD/EXIT
  decision. Nothing about the database or the broker here.
- `risk_engine.py` — its own module because the architecture rules list
  risk management as separate from strategies/backtesting. Phase 3's one
  rule (daily-loss kill-switch) lives here so Phase 4's backtester and any
  future live-trading path can call the same check rather than
  reimplementing it.

`strategy_execution_service.py` is the only place these get wired
together with real data and a real broker call, and it does that by
calling `ExecutionService.place_order()` — the exact function manual
trading in Phase 2 calls — with `execution_reason="STRATEGY"` and the
strategy's id. A strategy's fills get the same cost engine, the same
position accounting, the same "never fill at a fabricated price" rule
manual orders get, because it's not a second implementation.

The background worker (`app/worker.py`) is a second entrypoint into the
same backend image (`python -m app.worker` instead of `uvicorn
app.main:app` — see `docker-compose.yml`'s `worker` service), not a
separate codebase or a Celery deployment. It evaluates every active
strategy on a fixed interval during NSE market hours, with each strategy
getting its own DB session so one failing evaluation can't corrupt or
block the others in the same pass.

## Multi-tenancy

Every table that belongs to a user (`broker_connections`, and everything
Phase 2+ adds — portfolios, orders, positions) is queried through a
repository method that takes `user_id` as a required argument and filters
by it. There is no repository method anywhere that fetches one of these
rows by its own id alone. See
`app/repositories/broker_connection_repository.py` for the pattern to
follow when Phase 2 adds portfolios/orders/positions repositories.

## Broker abstraction

`app/brokers/base.py` defines `BrokerAdapter` — authentication, quotes,
historical data, WebSocket streaming, orders, positions, holdings.
`app/brokers/upstox/adapter.py` is the first (and only, for now)
implementation. `app/brokers/registry.py` maps a string key (`"upstox"`)
to an adapter instance; nothing outside `app/brokers/` imports
`UpstoxAdapter` directly. Adding Zerodha or Groww later is a new file in
`app/brokers/zerodha/` plus one line in the registry — the trading engine
(Phase 2+) never changes.

## Phase roadmap

Phase 1 and 2 are in this delivery. Rough shape of what comes next — each
phase gets its own review before the next one starts:

1. **Foundation** *(done)* — auth, multi-tenancy, broker
   abstraction, tiered credentials, migrations, Docker/Nginx.
2. **Core trading engine + manual paper trading** *(done)* — instruments
   (seed set + best-effort Upstox sync), multi-portfolio accounts with
   configurable virtual capital, the shared order/position/execution
   model, the transaction-cost engine (brokerage/STT/GST/SEBI/exchange
   charges/stamp duty), manual market and limit order placement against
   real live prices. Not yet in Phase 2: WebSocket streaming, TradingView
   charts, and auto-filling limit orders — see README known limitations.
3. **Automated strategy trading** *(done)* — no-code strategy builder
   (typed form, not a visual canvas), a five-indicator scoring engine
   (RSI, SMA crossover, MACD, volume spike, momentum — the same factors
   an earlier project, AlgoEdge, used), trailing stops, a standalone risk
   engine with a per-strategy daily-loss kill-switch, and a background
   worker evaluating active strategies every 5 minutes during market
   hours. Strategy entries/exits run through the identical
   `ExecutionService.place_order()` manual trading uses — see below.
4. **Backtesting** *(done)* — reuses the exact same scoring
   (`strategy_engine.py`), trailing-stop (`position_math.py`), and
   cost-calculation (`transaction_costs.py`) functions live trading and
   strategies use, walked forward bar-by-bar over real historical candles
   instead of live broker calls, with a slippage assumption added since a
   backtest has to simulate market friction a live fill wouldn't need
   simulated. Runs as a standalone, user-scoped analysis tool — never
   touches a real portfolio's cash or positions.
5. **Intelligence layer** *(done)* — AI trading assistant grounded in
   real server-assembled context (never its own database access),
   market-news intelligence via RSS with ticker-and-company-name
   matching, Telegram notifications (linking + trade alerts), WhatsApp
   notifications (same hook, heavier real-world setup burden). See below.
6. **Analytics, polish, live-trading safeguards** *(done)* — portfolio
   analytics (realized P&L, win rate, cash-balance-over-time chart,
   honestly labeled as realized-only) and strategy comparison, an admin
   panel wired to Phase 1–5's previously API-only endpoints, per-user
   rate limiting on order placement and the AI assistant, and a full
   live-trading safeguards review grounded in current SEBI regulation —
   see `LIVE_TRADING_SAFEGUARDS.md`. Broader broker support (Zerodha,
   Groww) remains unimplemented; the `BrokerAdapter` interface from
   Phase 1 was built to make that additive when it happens.

## Backtesting (Phase 4)

`backtest_engine.py` is the walk-forward loop, and nothing else — every
calculation inside it is a function imported from somewhere else that
Phase 2 or 3 already built and tested: `compute_score`/`decide`
(`strategy_engine.py`), `check_trailing_stop`/`apply_fill`
(`position_math.py`), `calculate_costs` (`transaction_costs.py`). The
loop's only genuinely new logic is the bar-by-bar walk and
`_apply_slippage` — a backtest has to simulate the market friction a real
fill already reflects on its own. `backtest_service.py` fetches real
candles via the same `BrokerAdapter.get_historical_data` call and the
same `candle_parsing.py` module `strategy_execution_service.py` uses (not
a second parser), then persists what the pure engine returns.

`BacktestRun`/`BacktestTrade` are deliberately their own tables,
user-scoped rather than portfolio-scoped — a backtest is a what-if
analysis, and letting it write into a real `Portfolio`'s `cash_balance`
or `Position` rows would let a simulation corrupt real trading history.
Reusing the calculation logic (the architecture rule) and reusing the
storage (which the rule doesn't ask for, and which would be actively
harmful here) are different things.

## Intelligence layer (Phase 5)

Three genuinely separate concerns share the word "notification," and it's
worth keeping them separate in your head the way the code keeps them
separate in modules:

- **News** (`news_parsing.py` pure, `news_service.py` fetch/persist) —
  RSS ingestion, deduplicated by link, tagged by matching both an
  instrument's ticker AND a cleaned version of its company name against
  each article's title/summary. That second matching key isn't
  precautionary — testing against a genuinely live-fetched Business
  Standard headline ("ICICI Bank raises fresh $750 million") showed the
  exact ticker "ICICIBANK" never appears in real prose, only the company
  name does. Ticker-only matching would have silently tagged almost
  nothing.
- **AI assistant** (`ai_assistant_service.py`) — the model gets a
  server-assembled context block (real positions, real recent orders,
  real tagged news for held instruments) appended to the question, and
  nothing else. It has no tool access, no database connection, no way to
  look anything up on its own — the same "never present fake data as
  real" principle applied to an LLM, where the failure mode is
  plausible-sounding fabrication rather than an obvious bug.
- **Telegram / WhatsApp** (`telegram_notifier.py`, `whatsapp_notifier.py`,
  unified behind `notification_service.py`) — both are thin, verified
  wrappers around their respective platforms' current APIs. Telegram
  linking is a deep-link + `/start <code>` handshake, completed by the
  worker polling `getUpdates` rather than requiring a public webhook
  (this app doesn't have HTTPS configured yet — see known limitations —
  so a webhook wasn't a realistic Phase 5 option). `notification_service.py`
  is deliberately fire-and-forget from the caller's side: a channel
  failing (not configured, API error) never blocks or fails the trade
  that triggered it — notifications are a side effect of trading, not a
  precondition for it.

## Trading-mode safety

`TRADING_MODE` (`PAPER` / `LIVE`) is an environment variable, not a
database row or an API-settable value — flipping it requires editing the
environment and redeploying. That's deliberate: it means no bug, no bad
default, and no compromised admin session can turn live trading on by
itself. It stays `PAPER` through every phase above until live trading is
explicitly implemented and reviewed, per the project's own ground rules.

That review happened in Phase 6, then got more precise after a
follow-up question — see `LIVE_TRADING_SAFEGUARDS.md` for the full,
current analysis. The short version: India's retail algo-trading
framework (mandatory for all brokers since 1 April 2026) exempts
personal/family automated trading under a 10-orders-per-second threshold
from formal exchange registration — but that exemption is specifically
for *your own* trading, not for offering a strategy to other people.
Since this is a multi-tenant SaaS platform built around other users
running strategies, live trading for anyone but the platform's own
operator falls into "providing an algo to other traders," which needs
broker-mediated exchange registration regardless of how low any one
user's order frequency is. Nothing in the codebase currently acts on
`LIVE` even when set.


## Live order idempotency and reconciliation (Phase 1 storage implemented; live execution not implemented)

The live order path is a separate future workflow, not a mode switch on the current paper execution path. `ExecutionService.place_order()` creates PAPER orders; preserve that boundary and its regression test.

Reviewed design and implementation gates live in [`LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`](LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md). Core invariants:

- Persist a client intent, canonical request hash, risk decision, audit event and transactional dispatch/outbox record before any broker POST. Scope the unique idempotency key to the authenticated user and broker connection. Same key + same payload returns the existing intent; same key + different payload is a conflict.
- A local database cannot make an external broker POST exactly-once. If the network times out or the process crashes after a request may have reached Upstox, mark the outcome unknown and reconcile before any further submission. Never blindly retry an ambiguous POST.
- Upstox order tags support correlation/history lookup; do not assume they are broker-enforced idempotency tokens. Match by documented account/order attributes and tag, and freeze on multiple or mismatched matches.
- Persist broker order IDs and normalized status transitions. Treat broker acceptance as distinct from execution. Deduplicate individual fills by stable broker trade identity and reconcile partial fills/cancel races against broker trade records.
- Recheck risk and account-level kill switch at dispatch time. Unknown/pending intents reserve exposure until resolved. Paper execution must remain structurally unable to call the live placement method.
- Add schema only through reviewed additive migrations, test clean SQLite and staging copies of the deployed DB engine, and never migrate production during implementation.

Phase 1 includes durable idempotency schema and repository safeguards, including rejection of credential-like keys in persisted snapshots/audit details. Phase 2 now includes a pure Upstox order-status normalizer and a pure intent matcher. The matcher scopes candidates to one broker connection; uses an existing broker order ID or one exact correlation tag; and requires instrument, side, order type, quantity, product and applicable price fields to match. Multiple tag matches, economic mismatches, cross-connection candidates and unknown/contradictory observations are not auto-linked. The matcher performs no network calls. The repository now exposes a versioned reconciliation transition that updates an intent and appends a safe audit event in one transaction, rejects invalid regressions and stale versions, and treats repeat same-state observations as no-ops. No helper fetches broker data. A pure Upstox trade normalizer and repository-only `record_broker_fill()` now validate and persist individual broker trade identities idempotently; when linked to an intent, fill + audit event are atomic. Linked fills must match the already-associated broker order ID and intent instrument/side/product/order type; quantity ceilings and limit-price protection are checked before persistence. Previously unmatched fills can be linked later with account/order/economic checks and an atomic audit event. The read-only worker now exists in `app/services/live_order_reconciliation_worker.py`. It receives only `UpstoxReadOnlyReconciliationClient`, validates the user-owned Upstox connection and usable token, uses a durable per-connection lease, reads the order book and daily trades, retries only bounded read-only transient failures, and persists validated fill identities/status audit. It is not scheduled or wired to an API route, and current tests use mocks. There is no aggregation into Order/Execution/Position/cash/P&L and no live submission service. Keep live submission disabled. Official Upstox order-history/order-book/trade endpoints and links are documented in `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`.


## Roadmap and delivery gates
The ordered delivery sequence and evidence requirements are maintained in [ROADMAP.md](ROADMAP.md). This architecture document describes component boundaries; the roadmap is the source of truth for phase ordering and release gates. Phase 1 storage/repository implementation is CI-tested; Phase 2 has CI-tested order/trade normalization, strict matching, versioned status persistence, and individual fill identity persistence. Broker reads, a worker, partial-fill aggregation/accounting and live submission remain unimplemented. Live submission remains unimplemented.


## Out-of-order broker status and fill evidence — 2026-10-17
`resolve_order_state_with_fill_evidence()` combines the latest observed order state with deduplicated persisted fill quantity. Persisted full requested quantity resolves to `FILLED`; partial trades override stale active statuses to `PARTIALLY_FILLED`; partial trades plus cancellation become `PARTIALLY_FILLED_CANCELLED`; partial trades conflicting with `FILLED` or `REJECTED`, invalid quantity totals, and unknown conflicts become `RECONCILIATION_REQUIRED`. `LiveOrderRepository.apply_reconciliation_transition()` records both observed and resolved states plus the fill evidence count in its audit event. This remains repository/service logic only: no Upstox API reads, worker, or accounting updates exist. The next worker boundary is specified in [READ_ONLY_RECONCILIATION_WORKER_DESIGN.md](READ_ONLY_RECONCILIATION_WORKER_DESIGN.md).


## Read-only Upstox reconciliation client — 2026-10-17
`app/brokers/upstox/reconciliation_client.py` is a separate narrow client with fixed GET-only methods for order book, details, history and per-order trades. It has no place/modify/cancel methods and returns sanitized error categories rather than raw upstream error bodies. Contract tests use a mocked HTTP client; they do not make real Upstox requests. Exact test checkpoint [run 39056868434](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056868434) passed 309 tests, 1 warning. The worker implementation is present but not scheduled or wired to an API route. It validates connection ownership/token usability, applies bounded retry and a lease, and uses durable matching. CI mocks do not verify live account behavior; no real broker request has been made.


## Reconciliation worker lease — 2026-10-17
`LiveReconciliationLease` stores one lease per broker connection. `LiveReconciliationLeaseRepository` claims by compare-and-set, permits reclaim only after expiry, supports renewal only for the current unexpired token, and token-guards completion so an expired/stale worker cannot clear a newer lease. Alembic revision `202610170003` adds the table and CI verifies upgrade/downgrade/re-upgrade on SQLite and PostgreSQL 16. The lease is a foundation only; no worker invokes it yet.


## Read-only worker implementation — 2026-10-17
`LiveOrderReconciliationWorker` is an explicit on-demand service, not a scheduled background task. It validates connection ownership, Upstox broker identity and connection readiness before claiming the lease; retrieves a usable unexpired access token through `BrokerCredentialsService`; reads order book and daily trades through the fixed GET-only client; and uses bounded retry for 429/5xx/network/timeout responses. It normalizes and persists daily trade identities as unmatched, then matches order observations to one local intent and links fills only after repository economic/account checks. Missing fill evidence for a broker `complete` status leaves the intent `UNKNOWN`; later trade evidence can resolve it. The worker does not expose broker write methods and does not update accounting models. Mocked tests and PostgreSQL lease-claim concurrency passed in CI; no live Upstox request or production migration occurred. Remaining constraints: no scheduling/API trigger, no historical-day pagination/window logic, and no durable operator-facing run summary/manual-review queue.


## Durable reconciliation run summaries — 2026-10-17
`LiveReconciliationRun` records one row for each worker pass that acquires the per-connection lease. It stores owner/connection scope, start/completion timestamps, a finite status set, sanitized error category, and a whitelist of numeric counters only. `LiveReconciliationRunRepository` refuses unknown counter keys, negative/non-integer values, and unsafe error strings. Migration `202610170004` is reversible and tested on SQLite and PostgreSQL 16. The worker persists `RUNNING` before broker reads and a terminal result after releasing the lease. A process crash can leave a durable `RUNNING` row; detecting and presenting stale runs and manual-review issues is the next step. No raw broker body, credential or exception text is persisted.


## Durable manual-review issue records — 2026-10-17
`LiveReconciliationIssue` stores owner/connection scope, optional run/intent links, a whitelisted issue type, a SHA-256 fingerprint, broker order/trade IDs when safely normalized, `OPEN`/`RESOLVED` state, safe details, first/last-seen timestamps and occurrence count. The repository validates ownership, bounds the JSON details, rejects credential-like keys, deduplicates repeated occurrences per broker connection and reopens an issue if it recurs after resolution. The worker records issues instead of persisting raw broker rows or exception strings. Migration `202610170005` is CI-tested on SQLite/PostgreSQL 16. This is database persistence only: no operator UI/API or resolution endpoint exists yet.


## Owner-scoped reconciliation read API — 2026-10-17
`GET /api/v1/reconciliation/runs` and `GET /api/v1/reconciliation/issues` are authenticated read-only endpoints. They use `get_current_user`, filter every query by the authenticated `user_id`, support optional connection/status/type filters, and cap responses at 100 rows. Pydantic schemas expose only safe run counters and issue metadata/details, not raw broker records or credentials. Cross-user and unauthenticated route tests passed in [run 39060230705](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39060230705), 345 passed, 1 warning. There is no API to trigger reconciliation or resolve issues; those are separate reviewed changes.


## Reconciliation review UI — 2026-10-17
The dashboard links to `/reconciliation`, which reads only the owner-scoped `/api/v1/reconciliation/runs` and `/api/v1/reconciliation/issues` endpoints. It displays recent run counters, sanitized issue details and OPEN/RESOLVED filtering. It has no worker-trigger, issue-resolution or order-write controls. Exact commit `e4343dcb225c1f332b6c89399694d0a29a5df739` passed the frontend TypeScript/Next.js build and backend CI (345 passed, 1 warning). The page is UI-only and does not prove broker reconciliation has been run against a real account.


## Live-fill accounting recovery and verification — 2026-10-20

The deleted service, original tests and migration 0008 are restored to their original paths. Supporting models `BrokerOrder`, `BrokerTradeRecord`, `LivePosition` and migrations `202610180006` / `202610180007` were added to complete the chain. GitHub Actions [run 39475387511](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39475387511) passed **355 tests, 1 warning**, plus SQLite and PostgreSQL 16 migration upgrade → downgrade → re-upgrade checks at code/test checkpoint `a906274b98f3f7e0c913f376128f4996b996c52b`.

This is not a complete live-fill pipeline: the service remains unregistered, ingestion and reconciliation integration remain outstanding, and no real-account or production migration was performed. Keep live order submission disabled. Continue Phase 2 reconciliation release gates and crash/recovery/fill-linkage checks. Do not delete the recovered files without explicit user approval.


## Current live-order reconciliation versus manual-fill staging boundary — 2026-10-21

The codebase currently has two isolated models of broker trade evidence; do not conflate them:

1. The intent-based workflow uses `LiveOrderIntent` and `BrokerFillIdentity`. `LiveOrderReconciliationWorker` reads through the fixed GET-only Upstox client, links validated fills to intents, and records safe status/audit evidence. It does not mutate the shared `Order`, `Execution`, `Position`, `LivePosition`, or portfolio cash accounting path.
2. The manual Order-based staging workflow uses `BrokerOrder` and `BrokerTradeRecord`. `BrokerTradeIngestionService` stages broker-confirmed trades, and `BrokerChildOrderReconciliationService` validates aggregate staged trade quantity/weighted average price against broker order details before updating only child status and filled quantity. The parent `Order` and accounting are deliberately unchanged.
3. `LiveFillAccountingService` promotes a `BrokerTradeRecord` only with explicit broker-reported charges. It remains unregistered; its per-child aggregate guard prevents already-accounted plus new fill quantity from exceeding the broker-confirmed child fill total.

Before integrating these paths, decide whether they are separate supported workflows or require a common lifecycle. Do not dual-write or translate records without transaction-safe idempotency, account/intent linkage, conflict semantics, and replay/rollback tests. Current code/test checkpoint [run 39481385581](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39481385581) passed 438 tests, 1 warning, with SQLite/PostgreSQL 16 reversible migration checks. The worker and staging services are not scheduled or wired to automatic live execution; no real broker order was placed.


## Parent-order lock guard — 2026-10-21

After broker status I/O, child reconciliation locks/revalidates the owned parent Order, verifies LIVE mode and the pre-network instrument/side/quantity snapshot, then locks the BrokerOrder child before reading staged trade totals. This matches ingestion's parent→child lock order and blocks stale responses after a local order mode/economic change. A regression test switches the order to PAPER during the status read and confirms child state remains unchanged. Exact-head [run 39482592808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39482592808) passed **439 tests, 1 warning**, with SQLite/PostgreSQL 16 reversible migrations. No parent accounting or live submission is enabled.


## Explicit fill-workflow boundary decision — 2026-10-21

Decision: keep the intent-based reconciliation evidence path and manual-order trade staging/accounting path separate for this Phase 2 slice. The worker persists `BrokerFillIdentity` under `(broker_connection_id, broker_trade_id)` and links it to a `LiveOrderIntent` only after validated order matching. The manual Order path persists `BrokerTradeRecord` linked to `BrokerOrder`, with separate charge-validated accounting promotion. They currently have independent uniqueness constraints; the database does not provide cross-table deduplication.

Do not dual-write, copy, or promote one model into the other. Before a future bridge, define one canonical broker-fill identity, deterministic conflict handling when the same broker trade appears in both tables, owner/connection/intent/order linkage, transaction boundaries, idempotent replay, rollback, and crash recovery. The worker must remain read-only with respect to broker APIs and must not mutate `BrokerTradeRecord`, `Execution`, `LivePosition`, or portfolio cash. Regression coverage now enforces that boundary. No broker submission or automatic promotion is enabled.

## Reconciliation run crash-recovery boundary — 2026-10-21

`LiveReconciliationRunRepository.fail_orphaned_runs` is an explicit maintenance primitive for stale `RUNNING` run summaries. It is scoped to one user and broker connection and will not alter runs if that connection has an unexpired lease. It only records a terminal failure category and completion timestamp; it never invokes the broker, retries a request, links fills, or updates accounting. The method is not scheduled automatically. Callers must supply a timezone-aware stale cutoff; SQLite-loaded lease timestamps are normalized as UTC before Python comparisons.

## Phase 3 live-fill accounting checkpoint — 2026-10-21

- Latest reviewed code HEAD at this checkpoint: `ef60ec93d39543c644dfd557f6f73b48ab793b60`.
- Exact-head [Backend CI run 39609474410](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39609474410) completed successfully: **485 passed, 1 warning in 30.25s**; broker-write boundary guard passed; SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed.
- The one warning is non-failing; CI logs also report GitHub Actions Node.js 20 deprecation notices.
- Existing safeguards cover replay identity/charge validation, broker-confirmed fill quantities, cumulative child/order quantity limits, rejected-order protection, and atomic live-position/execution updates. This CI result verifies the current HEAD, not completion of all Phase 3 requirements.
- **Open Phase 3 requirement:** define and test the fee-allocation contract when a broker contract-note charge total covers multiple fills. The current API accepts a per-promotion breakdown and validates that its total equals its six components; it does not itself establish how a multi-fill contract-note total is allocated. Do not claim this issue resolved or wire in a coordinator/identity bridge until the rule is designed and regression-tested.
- Safety constraints unchanged: do not enable live broker submission, automatic accounting promotion, or automatic scheduling; keep `BrokerFillIdentity` and `BrokerTradeRecord` separate pending a reviewed bridge design. Phase 2 remains closed.


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


## Tariff estimate snapshot boundary (2026-10-23)

Tariff estimate snapshots are immutable, append-only audit records. Migration `202610240016` enforces this at the database layer with PostgreSQL and SQLite triggers rejecting UPDATE/DELETE; ORM guards and regression tests provide an additional layer. The snapshot's `ESTIMATE_ONLY` status is constrained separately. This record is not a broker actual and must never be used as the source amount for per-fill allocation. Actual per-fill charge allocation remains grounded in reviewed broker evidence and reconciled source components. Conditional/order-level tariff rules and variance-only estimate-versus-actual integration remain outstanding.


## Tariff snapshot transaction and audit guarantees (2026-10-23)

`TariffEstimateSnapshotRecord` remains `ESTIMATE_ONLY`, unique by idempotency key, and append-only at both ORM and database layers. Migration `202610240016` installs PostgreSQL/SQLite triggers blocking UPDATE/DELETE. Concurrent PostgreSQL tests validate exact replay convergence and conflicting-payload rejection. CI run 39960409771 passed 677 tests plus broker-write guard, migration round-trips and synthetic restore.

Architecture boundary: estimates can be compared to actuals for variance only. Per-fill actual allocation must originate from reviewed broker-evidenced source components. Conditional/order-level tariff caps, minimums, GST taxable-base composition and special charge models remain unsupported until modeled and tested.


## Estimate-versus-actual variance boundary (2026-10-23)

`TariffEstimateVarianceRecord` is a separate append-only audit table. The comparison service requires a valid estimate snapshot, exact broker fill identity, a VERIFIED source component, REVIEWED contract-note evidence with intact bytes, matching reviewer/broker/component/currency, and a manifest containing only that exact fill. It stores signed variance and percentage, but never mutates `BrokerChargeAllocation` rows or changes source/evidence status. CI run 39961777103 passed 680 tests plus broker-write, migration and synthetic restore checks.

Aggregate order-level/multi-fill variance is not supported. A single-fill estimate must not be compared to an aggregate actual amount. Advanced tariff caps, conditional rules and special component bases remain open.


## Verified exact PR-head CI 39962196672 — 2026-10-23
PR #6 head `c47bc3e3eeb4c8da4415132735d2d4ef457551f7` passed [CI](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39962196672): 680 passed, 1 warning; broker-write guard passed; no failed steps. Variance stays append-only and must not mutate allocation rows. Aggregate order/multi-fill actuals need an explicit scope model; advanced tariff shapes must be implemented and tested or fail closed.


## Aggregate variance scope proposal — 2026-10-23
The proposed design distinguishes a single `TRADE_FILL` from an `ORDER_FILL_SET` whose canonical exact member list is hashed and revalidated transactionally. Nonlinear/capped tariff calculations must occur at order scope. Variance records remain append-only and isolated from actual allocation/position/P&L writes. Aggregate support is not implemented yet.


## Variance scope integrity checks — 2026-10-23
Variance comparison now validates the canonical eligible-fill manifest's SHA-256 and confirms the linked broker fill side and trade date match the estimate snapshot. These checks fail closed before a variance record is written. Regression tests were added. Aggregate scope is still design-only; the current tariff calculator does not model caps/minimums, conditional rules or GST taxable-base composition.


## Exact-head CI evidence — 2026-10-23
CI run 39968000009 passed for code head `f5092df1d27a28006dccba929fdc41e9a1d63f1e`: 683 passed, 1 warning; broker-write guard, SQLite migration round-trip and isolated PostgreSQL 16 synthetic restore drill passed. This run is for the pre-documentation code head. Aggregate order/multi-fill variance is not implemented and tariff models lacking explicit support must fail closed.


## Aggregate variance scope implementation — 2026-10-23
Estimate snapshots carry `TRADE_FILL` or `ORDER_FILL_SET` scope and canonical fill-set metadata. Current snapshot builder schema is v4 (older v3 references are stale). Variance comparisons require exact equality with the reviewed component manifest and confirm all fills belong to the same broker order, connection, side, and trade date. Variance rows persist scope/digest and remain append-only/audit-only. Backend CI run [39979772325](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39979772325) passed on code/test commit `e54e405b74feee90e4658a6992fa208a3e2da5d3`, including SQLite/PostgreSQL 16 migration round-trips. The documentation synchronization itself remains subject to exact-head CI; no allocation or P&L mutation is permitted.


## Latest tariff-safety correction checkpoint — 2026-10-23
The tariff composition boundary is fail-closed: generic calculation rejects unsupported shapes, stamp duty routes through its dedicated BUY/product/basis checks and non-BUY requests are rejected before selection, and explicit GST composition verifies an approved GST rule before calculating from an explicit approved component set. Follow-up code commit `68dc2b6fa0a729cc77180725e581de61a88e9de1` passed CI run [39982723294](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39982723294), including tests, broker-write guard, SQLite/PostgreSQL 16 migration round-trips, and restore drill. Final docs head still needs CI; this remains estimate/validation logic, not charge allocation or P&L mutation.


## Tariff safety + Upstox charge-source research — 2026-10-23

Code commit `ce0b4bc17eaf1656334e10ca8d6e32a68f50593b` adds a fail-closed stamp-duty unit guard: the specialized stamp-duty calculator accepts only percentage-based approved rules; regression tests reject `INR_FIXED` and `INR_PER_CRORE`. Exact-head CI [39987357989](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39987357989) passed backend tests, broker-write boundary guard, SQLite and PostgreSQL 16 migration round-trips, and synthetic restore drill.

Official Upstox sources reviewed:
- Brokerage calculator API: https://upstox.com/developer/api-documentation/get-brokerage/ — order-scoped estimate with brokerage, taxes, transaction/clearing/IPFT/SEBI charges and DP-plan metadata; `dp_plan.min_expense` is a daily per-scrip sell minimum outside the brokerage calculation.
- Trade charges API: https://upstox.com/developer/api-documentation/get-trade-charges/ — segment/date-range charge breakdown including brokerage, GST, STT, stamp duty, transaction, clearing, IPFT, SEBI turnover and demat transaction charges.
- Historical trades API: https://upstox.com/developer/api-documentation/get-historical-trades/ — trade ID, exchange, segment, quantity, amount, side and trade date.
- Public tariff page: https://upstox.com/brokerage-charges/ — includes historical and newer effective-date rows; never activate rates from a flattened scrape without preserving effective periods and source snapshot.

API charge breakdowns are reconciliation/reference inputs, not automatically contract-note evidence or a substitute for reviewed actual source components. Do not store tokens. DP per-scrip/day minimums, STT/CTT tax-event cases and other conditional models remain unsupported until represented and tested explicitly. No active production tariff registry is enabled. PR #6 stays draft/unmerged; live broker writes remain disabled; original `Tradepro` remains out of scope.

Architecture reminder: the brokerage calculator API is an estimate path; contract-note source evidence and reviewed per-fill allocations remain separate immutable records.


## Generic conditional-charge guard — 2026-10-23
The next audit found that the generic rate calculator could apply plain rate×base arithmetic to STT/CTT and DP/demat components, despite these requiring event- or day/scrip-specific semantics. Commit `ee09183e5b8eeff0311431faa90b807d9b561ce7` adds an explicit fail-closed block for STT, CTT, DP, DP charges and demat/depository transaction charges in the generic calculator, with parameterized regression tests. Exact-head CI run [39988242077](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39988242077) passed. The synchronized documentation commit `b1207def7d828c960e6fffe9c6af8b9ed0177c07` also passed exact-head CI run [39988578238](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39988578238).

Audit note: the implementation constant is `tariff-estimate-snapshot-v4`; older design text saying snapshot v3 is stale and is corrected in the accompanying design-document update. Remaining gated models include STT/CTT event-specific rules, DP daily per-scrip minimums, conditional lesser-of pricing, and reviewed source-backed effective-date rates. No live tariff registry or live broker order writes are enabled.

Generic charge calculation now explicitly excludes conditional tax/depository components; they need specialized calculators and must not be treated as simple percentage calculations.

## Phase 3 checkpoint — aggregate variance test hardening (2026-10-24)
Order-fill-set variance remains audit-only: it must not allocate actual charges or mutate positions/P&L. Added database-backed regression cases for actual manifest-digest tampering, mixed broker-order membership, fill-side mismatch, and trade-date mismatch; each asserts no variance row is written on rejection. Exact-head CI is pending. Keep unsupported tariff semantics fail-closed and live broker writes disabled.

## CI verification — 2026-10-24
Exact-head backend CI passed on `bc8e5c1aa862589c660fd361d87f7df45d8ceb10` (run `40062975428`). Aggregate variance remains audit-only and must not allocate charges or mutate positions/P&L. Remaining acceptance work includes concurrency/replay review, reviewed-source revalidation, and explicit no-accounting-side-effect assertions. Keep live broker writes disabled.

## Phase 3 checkpoint — aggregate variance hardening (2026-10-24)
Added tests that variance comparison does not mutate reviewed evidence, verified source-component fields, or existing per-fill allocations, and rejects when evidence/component review state is revoked before comparison. CI for the new test commits is pending. The variance path remains audit-only and must not affect allocation, positions, or P&L.

## Upstox adapter design constraint — 2026-10-24
Use `UPSTOX_API_INTEGRATION_POLICY.md` as the canonical API inventory. Prefer one maintained Upstox adapter and the official Python SDK where endpoint/version support is adequate; use typed REST/WebSocket adapters only for documented SDK gaps. Do not create duplicate streams, brokers, charge ledgers or order engines. Keep estimates, broker-reported aggregates, trade/fill identity, reviewed actual evidence and per-fill allocations separate. Agent Skill/MCP access must not bypass auth, audit or live-order safety boundaries.

## Aggregate variance concurrency invariant — 2026-10-24
Exact-head CI run `40064129721` passed (738 passed, 1 warning). PostgreSQL race coverage confirms concurrent duplicate variance comparisons yield one `CREATED` and one `EXACT_REPLAY`, exactly one append-only `VARIANCE_ONLY` record, and no per-fill allocation writes. Variance remains audit-only. Next gate is explicit effective-dated component rules and controlled integration from approved rule calculation to the existing durable allocation ledger; do not create duplicate ledgers or adapters.

## Upstox read-only charge endpoints — 2026-10-24
The existing fixed-path `UpstoxReadOnlyReconciliationClient` now supports the official brokerage estimate, trade-charge aggregate and historical-trades GET endpoints. Exact-head CI run `40064514873` passed (744 passed, 1 warning). The official SDK was assessed; for these narrow reads, direct REST remains behind the existing façade to preserve fixed GET-only surface, validation and sanitized error handling without importing a broad generated SDK that also exposes trading methods. Next: immutable API-estimate provenance and comparison integration; do not write estimates into actual per-fill accounting.

## Upstox estimate-only snapshot boundary — 2026-10-24 (CI verified)
The Brokerage Details API response is normalized into separate component estimate snapshots in the existing immutable snapshot store. Each record carries API version/endpoint, canonical request parameters, UTC retrieval time, canonical response JSON + digest, total estimate and DP-plan minimum metadata. Variance comparison recomputes the response digest and rejects API estimates unless quantity, price, side and instrument match the exact reviewed fill set. This path does not create charge allocations or promote actuals. Exact-head CI run `40065219626` passed (**754 passed, 1 warning**).

## Brokerage calculation shape — 2026-10-24 (CI verified)
The guarded order-level brokerage calculator supports two explicit shapes: flat fee (`ORDER_FIXED` with `INR_FIXED`) and percentage-of-order-notional with rule-bound minimum/maximum caps. Snapshot calculation dispatches to the specialized order-brokerage entry point for both. No rate registry was activated and no allocation is created by this calculation. Exact-head CI run `40065607232` passed (**756 passed, 1 warning**).

## Source-backed tariff candidate boundary — 2026-10-24 (CI verified)
`backend/app/services/upstox_tariff_candidates.py` exposes 18 effective-dated research candidates sourced from the dated excerpt `docs/source_snapshots/UPSTOX_CHARGES_2026-10-24.md`. All candidates use `DRAFT` review state and therefore cannot be selected by the existing approved-rule selector. This provides a reviewable inventory without enabling rates. Source snapshot digest: `c59f7e940fde6b0d94ca1189766f16e5601c117d4a8c2bcd2415da0ecd6db420`. Exact-head CI run `40065979244` passed (**760 passed, 1 warning**).


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


## 2026-10-24 — Charge API unusable-value provenance hardening

- Review found that `resolve_charge_api_value` retained the approved mapping's semantic and source fingerprint for usable values, but omitted source URL and SHA-256 provenance when the normalized field was `MISSING`, `NULL`, or `INVALID`. These values were already unusable, but their interpretation path was less auditable.
- Fixed the resolver to return approved mapping provenance for every normalized state while keeping missing/null/invalid values `usable=False`. Numeric zero remains a distinct present value; this change does not promote allocations or approve production Upstox mappings.
- Added regression coverage for missing, null, NaN, negative, boolean, and object values; assertions require mapping source URL, source SHA-256, and semantic to remain present. Added mapping effective-date and estimate-vs-actual guard cases.
- Implementation commit: `845e9e0dc924f11ae89b96ef73c94c59c2efb4b4`. Test commit: `1d7e24b0ba8c89062ec1eeddb93d0c4cd22a226f`. Documentation checkpoint is being synchronized; exact-head CI must pass before verification is claimed.
- PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains out of scope.


## 2026-10-24 — Resolver acceptance and CI checkpoint

- Latest previously verified documentation head: `8214430f562f6f425cfc1b9b6a6b3b547832b68a`; backend workflow [#40108183667](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40108183667) succeeded on that head. New resolver test commits `0f05f52cbb7c3afbe1c159fb94837c9776eb9262` and `65e7b56de6b193423106d57101a11d54dcc7894c` add exact broker/endpoint/schema/field/scope matching and non-finite-number rejection cases; these newer commits still require CI.
- The mapping identity test fixtures use immutable dataclass replacement. Intended-use semantics remain explicit; missing/null/invalid states remain unusable and preserve mapping provenance; zero remains distinct.
- Accounting acceptance already covers replay/conflict, ledger reconciliation, lock order, rollback, reviewer authority and a PostgreSQL verification/promotion race. Re-check exact test and workflow status before claiming complete; CI does not establish production tariff correctness or broker-origin authenticity.
- Safety gates unchanged: PR #6 draft/unmerged; live broker order submission disabled; automatic quantity/notional allocation disabled; production Upstox mappings/tariffs unapproved. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` must remain untouched.


## 2026-10-24 — Resolver field-identity guard added; CI pending

- Review found a mapping-identity gap: the resolver selected a mapping by `field_path` but normalized the separate `field` argument without checking that it was the mapped field. A caller could otherwise pair the approved `charges.ipft` mapping with a different top-level payload field.
- Added a fail-closed check requiring the normalized payload field to match the terminal field name in the approved mapping path. Added a regression test proving a mismatched payload field is rejected.
- Implementation commit: `77aa77aec37dc535c3e427ca3f88c2ccb5e75ed8`; regression-test commit: `5c5482c7f7fa623707698f64b6a061351e5e5b87`. CI for these commits is pending; do not claim green until the latest branch head is verified.
- Prior backend workflow `40108552948` passed on earlier head `cf5497aec438a3b6c91ae4d67c445cdbacd7b34b`; this does not validate the new field-identity guard.
- Accounting concurrency review remains a separate acceptance item: existing promotion tests assert canonical lock order and rollback/idempotency, but the current test file does not itself demonstrate a genuinely concurrent two-session verification-versus-promotion race. Confirm whether another integration test exercises that race before marking the item complete.
- PR #6 remains draft/unmerged. Live broker order submission and automatic quantity/notional allocation remain disabled; production Upstox mappings/tariffs remain unapproved. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Latest resolver CI verified; PostgreSQL race coverage located

- Latest PR head `ed346e823cbfae8448fae0134c4ff864bfcc60ac` passed Backend workflow [#40109041654](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40109041654). This head includes the resolver payload-field/mapping-path identity guard and its regression test, plus the synchronized docs through this checkpoint.
- Located PostgreSQL-only integration coverage in `backend/tests/test_broker_charge_allocation_postgres_concurrency.py`: conflicting fill-set serialization; concurrent source verification and allocation promotion; full live-fill promotion racing ledger verification; and concurrent tariff estimate/variance persistence cases. These tests require `TEST_POSTGRES_URL`; their execution depends on the PostgreSQL CI job actually provisioning and running that suite.
- Therefore the earlier concern that no dedicated verification-versus-promotion race test exists is corrected: a dedicated test is present. Next verify the workflow job log confirms this PostgreSQL test was run rather than skipped, then inspect its assertions for accounting/position side effects.
- PR #6 remains draft/unmerged. Live broker order submission and automatic quantity/notional allocation remain disabled; production Upstox mappings/tariffs remain unapproved. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Accounting invariant audit checkpoint

- Reviewed `backend/app/services/live_fill_accounting_service.py` and its unit tests. New accounting writes (live position mutation and execution insert) are committed in one transaction; all exceptions roll back. A post-commit refresh failure is covered by retry-as-exact-replay tests.
- Verified test coverage for exact replay, conflicting fill/evidence payloads, unchanged paper position and portfolio cash, failed flush/commit rollback, charge totals matching six components, and deterministic paise allocation.
- Dedicated PostgreSQL concurrency tests exercise verification-vs-promotion, live-fill-vs-ledger verification, conflicting fill sets, and concurrent tariff snapshot replay/conflict. CI on head `bacbe9dd9dfa35d739bbcea2bfece6185dc391d0` passed workflow [#40109864007](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40109864007). This passing head predates the present audit-note commit(s); recheck CI on the new head.
- Remaining acceptance is not waived: ensure the PostgreSQL-only tests are exercised by required CI with `TEST_POSTGRES_URL`, verify latest branch checks after this documentation change, and continue authoritative tariff/API-field review. Synthetic test fixtures do not approve production tariff semantics.
- PR #6 remains draft/unmerged. Live broker order submission and automatic quantity/notional allocation remain disabled. Production Upstox mappings/tariffs remain unapproved. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Aggregate endpoint hard guard added; CI pending

- Resolver now blocks Upstox `/v2/trade/profit-loss/charges` from `PER_FILL_ACTUAL` use even if a mapping row is incorrectly labelled per-fill. Official documentation defines the endpoint as aggregate `charges_breakdown`, not per-fill evidence.
- Regression test `test_official_upstox_aggregate_charges_endpoint_cannot_be_promoted_to_per_fill` covers the guard. Implementation `cdc07afdd8cc0c8d0b37d7e4aa8cdf1bf6eac651`; test `8ae749017a8ba0016f2c9adeb77eaff41fb5ae70`. CI is pending for this test commit.
- Production field mappings and tariffs remain unapproved; null is not zero; automatic quantity/notional allocation and live order submission remain disabled. PR #6 stays draft/unmerged; original `Tradepro` remains untouched.


## 2026-10-24 — Upstox brokerage calculator restricted to estimates; CI pending

- Official Upstox `GET /v2/charges/brokerage` takes proposed instrument, quantity, product, transaction type and price, returning a charge calculation; this is not proof of final booked per-fill charges. https://upstox.com/developer/api-documentation/get-brokerage/
- Resolver now blocks `/v2/charges/brokerage` from `PER_FILL_ACTUAL` and actual `AGGREGATE_SUMMARY` use even if a mapping is misleadingly labelled. Existing guard still blocks `/v2/trade/profit-loss/charges` from per-fill actual use. New regression tests cover both misuse cases.
- Implementation `3486d854dae2451858a858cb627602aca7338969`; tests `6c92101a1890a0f4d761e86ed3db047a269fd10d`. Prior head `6cc8b58f635fcb4f1b1cb3e5997099d074800a28` passed workflow #40111501429. CI for the new commits must be verified.
- Production mappings/tariffs remain unapproved; null is not zero; automatic quantity/notional allocation and live broker order submission remain disabled. PR #6 stays draft/unmerged. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.

## Upstox SDK/API integration audit — 2026-10-24

The current Upstox integration deliberately combines asynchronous REST calls through `httpx`, a separate V3 protobuf/WebSocket market-data service, a read-only reconciliation client, and validated response parsing. The official Python SDK is not currently a declared backend dependency. Do not treat SDK adoption as a goal by itself: evaluate exact endpoint support, package version/licence/dependencies, asynchronous behavior, timeouts, retries, sanitized errors, and response-schema compatibility in an isolated spike. Keep the existing V3 stream unless the SDK demonstrably preserves its lifecycle, reconnect, resubscribe, and stale-feed controls. The brokerage calculator is estimate-only; aggregate segment/FY charge responses are not per-fill actual evidence. See [`docs/UPSTOX_SDK_API_REPOSITORY_AUDIT.md`](docs/UPSTOX_SDK_API_REPOSITORY_AUDIT.md) and [`UPSTOX_API_INTEGRATION_POLICY.md`](UPSTOX_API_INTEGRATION_POLICY.md). No live calls or order writes are permitted during this audit.

## SDK and Agent Skill compatibility decision — 2026-10-24

No official SDK runtime dependency is added as a result of the static compatibility review. The existing async `httpx` reconciliation client already calls the brokerage estimate endpoint, and its response is normalized by project-owned validators. The generated SDK's synchronous default and thread-based async option do not justify replacing this path without a concrete capability or correctness benefit. The upstream Agent Skill is development-only reference; its scripts include live order/GTT writes and must not run in the app runtime. See [SDK/API audit](docs/UPSTOX_SDK_API_REPOSITORY_AUDIT.md) and [Agent Skill security review](docs/UPSTOX_AGENT_SKILL_SECURITY_REVIEW.md).



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

- Added `BrokerChargeCanonicalSourceLink` and migration `202610250025_normalize_canonical_source_links.py`. The relational database now explicitly stores each canonical snapshot-to-source-row edge, including source order, with foreign keys and uniqueness constraints. Migration backfills solely from the snapshot's persisted ordered source-ID manifest and fails on malformed/duplicate manifests rather than inferring membership.
- Snapshot materialization persists normalized edges; idempotent replay and independent review compare the relational links with the immutable manifest. Review fails closed if any link is missing, reordered or inconsistent. This makes split transaction/IPFT (two raw source rows → one canonical exchange-charge snapshot → linked per-fill allocations) explicit and auditable.
- Previous branch head `4dbaf27fae124d11935c271f2f4cdec44015dbaa` passed Backend workflow [#40196030459](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40196030459). Normalized-link change `d1153a0f0751339f3ca82fc062701db0141d4749` is pending fresh CI verification.
- Next: verify the new migration on SQLite/PostgreSQL 16 including downgrade/re-upgrade and all tests; then bind accounting promotion/reconciliation to normalized source links and canonical snapshot fingerprints.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion disabled.


## Phase 3 — normalized source links and canonical reconciliation gate (25 October 2026)

- Normalized source-link migration passed Backend workflow [#40196529023](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40196529023), including pytest, broker-write boundary, SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade and synthetic restore drill.
- Added `broker_charge_canonical_allocation_reconciliation_service.py` to validate the independently verified snapshot, source fingerprint and normalized source links, fill manifest, deterministic paise amounts, INR/method/basis and exact total before atomic promotion. Reconciliation is idempotent and its durable reference binds snapshot ID, source fingerprint, fill-set hash and allocation method; caller owns commit/rollback.
- Added split transaction/IPFT source-link, promotion/replay and tamper-blocking tests. Commit `621ce7cd289057a419be5eeff0262e158b18c001` Backend workflow [#40196784435](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40196784435) was in progress at the checkpoint; do not call the new path green before completion.
- Next: resolve exact-head CI failures, then cover conflicting evidence, transaction rollback and PostgreSQL concurrent promotion.
- Safety unchanged: Improved repo only; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; no live broker writes enabled.


## CI result update — canonical reconciliation gate (25 October 2026)

- Backend workflow [#40196784435](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40196784435) completed successfully for code/test commit `621ce7cd289057a419be5eeff0262e158b18c001`. Pytest, broker-write boundary enforcement, SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade and synthetic PostgreSQL/document-volume restore all passed.
- This green result verifies the normalized source-link schema and canonical allocation reconciliation tests at that code/test head. Later docs-only commits need exact-head CI verification if triggered.
- Next: explicit rollback/conflicting-set and PostgreSQL concurrent-promotion coverage, then fresh exact-head CI. Live broker writes remain disabled; PR #6 stays draft/unmerged and PAPER remains mandatory.

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
- The approved public Upstox STT/exchange rules are estimate-only. Account-specific actual charges, GST taxable-base composition, stamp duty, SEBI/DP/demat/other charges, unsupported exchange/segment mappings, and per-fill actual evidence remain unapproved. Candidate tariff entries remain DRAFT unless separately allowlisted and reviewed.
- Phase 3 remains in progress. Next gates: independently reviewed tariff applicability; component-specific per-fill allocation rules; invoice/source-backed GST/IPFT and product/segment evidence; final adversarial, migration and recovery review; exact-head acceptance sign-off. Do not repeat canonical live-fill integration.
- Safety: PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. PR #6 stays open/draft/unmerged without explicit user approval. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.
- This documentation commit’s CI is green. Continue only from this checkpoint and verify CI for every subsequent implementation/checkpoint commit. Historical entries below or above this section do not supersede this checkpoint.


## GST/IPFT checkpoint — 26 October 2026

- Regression test `test_gst_arithmetic_is_invariant_for_combined_vs_split_ipft_representation` verifies equivalent synthetic representations produce ₹307.00 base and ₹55.26 GST at 18%; this is arithmetic coverage, not approval of real taxable-component mapping. Test commit `8b4ae0b431d6aa03f1a8ae347a0b5fa7bda44c4f` passed exact-head Backend CI [run 40296066304](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40296066304).
- NSE circular `NSE/FA/73061` dated 27 Feb 2026, effective 1 Mar 2026, specifies combined outflows ₹307/crore cash, ₹183/crore equity futures and ₹3,553/crore equity-options premium including ₹0.01/crore IPFT: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf. Upstox's public schedule describes 18% GST on specified brokerage, transaction, IPFT and equity-delivery demat charges and says IPFT is combined with transaction charges: https://upstox.com/brokerage-charges/.
- CBIC states STT/stamp-duty recoveries are outside GST value only where Rule 33 pure-agent conditions are met; otherwise valuation rules apply: https://cbic-gst.gov.in/sectoral-faq.html and https://cbic-gst.gov.in/valuation-rules.html.
- Production GST mapping remains blocked pending product/segment-specific review and reliable invoice/contract-note reconciliation. Never apply GST to trade notional or all charges indiscriminately, or count separate IPFT twice. Candidate tariff rules remain DRAFT.
- Next gate: component-level GST acceptance cases across equity delivery, intraday and F&O, then exact-head CI and maintained-doc synchronization. PAPER mode mandatory; live broker order writes disabled; PR #6 draft/unmerged; original `Tradepro` untouched.


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


## GST/IPFT reconciliation checkpoint — 26 October 2026

- Official Upstox schedule https://upstox.com/brokerage-charges/ states GST 18% on brokerage + transaction charges + IPFT, including DP/demat for equity delivery. From 1-Mar-2026, published NSE combined transaction/IPFT totals are cash ₹307/crore, equity futures ₹183/crore and equity options ₹3,553/crore on premium. Count combined rates once. NSE circular: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf.
- The official Upstox Brokerage Details API example https://upstox.com/developer/api-documentation/get-brokerage/ shows transaction ₹5.68, IPFT ₹0.17, GST ₹1.02; that GST matches 18% of ₹5.68 alone, not ₹5.85 (about ₹1.05). This remains an example/documentation conflict, not proof of a live defect.
- The Trades Charges API https://upstox.com/developer/api-documentation/get-trade-charges/ provides aggregate segment/date-range charges and may return IPFT null. Null is unknown, not zero; aggregate totals are not per-fill evidence.
- Historical public contract-note copies dated 2024/2025 are third-party and pre-current-tariff; differing printed taxable bases mean they cannot settle current actual-charge treatment. Use for layout/schema only.
- Estimate-only rule may follow current tariff with product/exchange/effective-date handling and combined transaction/IPFT counted once. Actual per-fill GST candidates for delivery, intraday, futures, options remain DRAFT pending current public invoice evidence or written Upstox clarification. No production actual-charge GST logic promoted.
- Previous exact-head CI passed on commit 996b126ff678b97441f0214ea817451ee1592203: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40341429226. Tests, broker-write boundary, SQLite/PostgreSQL 16 migrations, synthetic restore and evidence retention passed; the next documentation commit needs its own exact-head CI.
- Only tarunsharma2610-del/tradepro-improved is in scope; original Tradepro untouched. PAPER mandatory; live order writes and automatic live-fill promotion/scheduling disabled; PR #6 draft/unmerged; no personal contract note requested; AI/Algory deferred until Phase 3 acceptance.


## GST estimate implementation update — 26 October 2026

- Added backend/app/services/upstox_public_gst_estimate.py and backend/tests/test_upstox_public_gst_estimate.py: explicit public-schedule estimate-only GST path, 18%, supported scope from 1-Mar-2026, provenance fingerprint and PUBLIC_SCHEDULE_ESTIMATE_ONLY label. This does not approve actual GST component sets or promote charges.
- Component contract: delivery requires brokerage + exchange_charges + explicit demat_charges; other supported products require brokerage + exchange_charges. For NSE from 1-Mar-2026, exchange_charges is the combined transaction/IPFT total once; separate ipft key is rejected. BSE options use applicable BSE schedule and must not inherit an NSE IPFT assumption.
- Open discrepancy: Upstox Brokerage Details API example shows transaction ₹5.68, IPFT ₹0.17, GST ₹1.02; 18% of ₹5.85 is approximately ₹1.05. The helper follows public tariff wording for estimates only. Actual per-fill GST candidates remain DRAFT pending current public invoice evidence or written Upstox clarification.
- Acceptance matrix: GST_IPFT_ACCEPTANCE_MATRIX.md. Code/test head 221493eb17729533cfaf855e2ce52532ef0903ac; CI run #40342805295 was pending at note time. The next documentation commit needs its own exact-head CI.
- Safety unchanged: Tradepro Improved only, original Tradepro untouched, PAPER mandatory, live broker writes and automatic live-fill promotion/scheduling disabled, PR #6 draft/unmerged, no personal contract note requested, AI/Algory deferred.


## Authoritative GST decision — 26 October 2026

**Decision: implement the current official Upstox public-schedule GST base for estimates now; do not let the inconsistent API documentation sample block it.** Upstox's pricing page explicitly states GST at 18% on brokerage + transaction charges + IPFT, with demat charges additionally included for equity delivery. From 1-Mar-2026, NSE Circular NSE/FA/73061 defines combined transaction/IPFT outflows (cash ₹307/crore, futures ₹183/crore, options ₹3,553/crore premium); represent that as one exchange_charges component and never add IPFT twice. The supported estimate path sums brokerage + combined exchange_charges, and adds explicit demat_charges for delivery. STT, stamp duty and SEBI are not added to this published GST base.

The Brokerage Details API example showing transaction ₹5.68, IPFT ₹0.17 and GST ₹1.02 is internally inconsistent with that page: 18% × ₹5.68 = ₹1.0224 → ₹1.02; 18% × (₹5.68 + ₹0.17) = ₹1.053 → ₹1.05. Treat this as a documentation-example discrepancy, not evidence that current production billing is wrong. Public schedule takes precedence for estimates; the API example does not override it. Trades Charges API is aggregate and its ipft:null is unknown, not zero.

This resolves the public-schedule estimate rule. It does not certify account-specific invoice totals or per-fill actual GST. Keep actual accounting/promotion evidence-gated until invoice/source evidence or written broker clarification is available. A personal contract note from the user is not required. Official sources: https://upstox.com/brokerage-charges/ ; https://upstox.com/developer/api-documentation/get-brokerage/ ; https://upstox.com/developer/api-documentation/get-trade-charges/ ; https://nsearchives.nseindia.com/content/circulars/FA73061.pdf ; https://cbic-gst.gov.in/sectoral-faq.html


## Latest GST/IPFT implementation checkpoint — 26 October 2026

- Implementation + synchronized GST decision commit b75a97f6cd0043c185375cc253b84a1e6d6bfea1 passed exact-head Backend CI [#40345937942](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40345937942): 1,012 passed, 1 warning in 62.33s. Broker-write boundary guard, SQLite/PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore and evidence retention passed.
- Estimate decision: use 18% on brokerage + combined transaction/IPFT exchange charges; add explicit demat charges for equity delivery. Count IPFT once. Exclude STT, stamp duty and SEBI from the published estimate base. API example GST mismatch is a docs-example inconsistency and does not override the current Upstox schedule.
- Actual invoice/per-fill GST acceptance remains separate and evidence-gated; actual component-set candidates stay DRAFT. Do not request a personal contract note. Safety: PAPER mandatory, live order writes/promotion/scheduling disabled, PR #6 draft/unmerged, original Tradepro untouched.


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

- Backend CI #40459846143 passed on `9400bc9aa221e2cf3b735e49a8e9a6d351237f02`: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40459846143. Backend tests, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore checks passed.
- DP completeness API regression added: invalid DP status must not expose a complete total. `KNOWN` requires a valid paise-exact amount; `NOT_APPLICABLE` requires no amount; unresolved states remain incomplete. Delivery SELL needs reviewed DP evidence and exact per-fill allocation.
- Next gate: per-fill mapping, replay/idempotency, rollback atomicity and component applicability. Real invoice and production Oracle restore acceptance remain evidence-gated.
- Safety: PAPER mandatory; live broker writes disabled; PR #6/#7 Draft/unmerged; original `Tradepro` repository out of scope.


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

**Verified code checkpoint:** `3a0c464afcb10261d1590607f8440affd21295a0`, Backend CI [#40878367369 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40878367369): **1,207 passed, 1 warning**. Broker-write boundary, SQLite upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore, and restore-evidence retention passed. The new documentation head still requires its own CI run.

### Completed engineering scope

- Paise-exact deterministic per-fill allocation; source integrity/reviewer controls; canonical source-to-component mapping; explicit combined/split transaction-charge/IPFT handling.
- Idempotent replay and conflicting-replay rejection; locked charge verification; rollback protection for accounting/position mutation.
- Explicit DP/demat persistence and total completeness. Delivery SELL fails closed when required DP evidence is unknown, invalid, inconsistent, or missing.
- GST valuation and GST/API comparison primitives preserve Decimal/paise precision, state/place-of-supply, missing/null/zero distinctions, and review-required variances. They do not silently approve actual charges.
- Upstox Brokerage Details API first for PAPER estimates; hardcoded calculator fallback on unavailable/invalid/inconsistent responses. Persist source as `PAPER_UPSTOX_API_ESTIMATE` or `PAPER_HARDCODED_FALLBACK` and display: “Estimated charges may differ from actual broker charges. For paper trading only; these are not actual booked charges.”
- Post-trade Trade Charges API is aggregate-only evidence, never per-fill actuals; aggregate responses are sanitized before persistence/return.

### Non-blocking operational/release gates

Credentialed Upstox OAuth/API smoke testing and real Oracle/database-plus-document-volume restore acceptance require deployment and user-authorized credentials/backups. Tariffs without independently approved scope/date evidence remain estimate-only/fail-closed for actual accounting. Historical contract-note fixtures support regression tests; estimates and aggregate summaries never become booked per-fill actuals. These constraints do not block PAPER-mode engineering completion.

**Safety:** only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker writes disabled. Phase 4 is the next separate increment after exact documentation-head CI passes.


## Resume checkpoint — 29 October 2026 (Upstox response-schema validation)

- **Code/test head:** `404c1e11ef4f2557c791c720c8d9a3fbc4e93bc1`; exact-head Backend CI [#40883660756 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40883660756). The workflow result confirms success; its summary did not expose a reliable pytest count, so no count is asserted here.
- **Concrete fix:** `UpstoxChargeApiOrchestrationService` no longer marks arbitrary successful HTTP JSON as usable. Brokerage estimates require `status == "success"` and `data.charges`; post-trade aggregate charges require `status == "success"` and `data.charges_breakdown`. Wrong/missing schema returns `usable=false`, clears the payload and records `INVALID_RESPONSE_SCHEMA`.
- **Regression coverage:** valid endpoint-specific response fixtures plus incorrect endpoint schema, unsuccessful/missing status, and aggregate wrong-shape payload cases.
- **Evidence boundary:** Brokerage Details remains estimate-only; Trade Charges remains aggregate reconciliation-only and never per-fill actual evidence. Null IPFT must not be silently coerced to zero. This fix validates response shape; it does not approve tariffs or promote accounting.
- **Contract-note continuity:** previously supplied January 2023 Upstox/RKSV contract-note examples remain available as historical regression fixtures; do not ask the user to provide them again. Their scope must be respected when using them for GST totals versus per-fill allocations.
- **Next:** verify CI on the exact synchronized documentation head. Keep PR #6/#7 Draft and unmerged, PAPER mode mandatory, live broker writes disabled, and the original `tarunsharma2610-del/Tradepro` repository untouched.

## Market-data execution pricing — 30 October 2026

Paper market-order pricing uses Upstox Full Market Quotes V3 order-book depth, not LTP alone. BUY simulation consumes ask levels; SELL simulation consumes bid levels; the fill price is quantity-weighted across consumed levels. Snapshot timestamp determines book freshness; last_trade_time is not used as a proxy for snapshot freshness. Instrument identity, positive finite prices, timestamp bounds and sufficient displayed depth are mandatory. A missing/stale/invalid snapshot or insufficient depth rejects the paper order.

Token scopes are distinct: Analytics Token for officially supported market-data/streaming APIs; standard OAuth access token for account/portfolio/trading APIs. Keep credentials separately encrypted and never cross-fallback.
 
## Upstox Analytics Token implementation — 30 October 2026

- Added separate encrypted `analytics_token_encrypted` and `analytics_token_expires_at` fields to per-user broker connections with migration `202610300031` (down revision `202610270030`).
- Added owner-scoped Settings API to save, inspect status and clear Analytics Token. Token is accepted from the user's Upstox Developer Apps > Analytics page; it is never returned, logged or included in API responses. Expiry is tracked as 365 days from local registration; confirm/renew against the Developer Console's actual expiry date.
- Analytics Token retrieval is independent of standard OAuth `is_connected` state and fails closed when missing/expired. Standard OAuth access-token path remains separate for operations not documented as Analytics Token eligible.
- Routed strategy historical/intraday candle fetch, paper market quote/charge estimation, queued paper limit-order quotes, and market WebSocket reconnects through Analytics Token. Broker order/trade ingestion continues to use standard OAuth until each endpoint's Analytics Token/static-IP eligibility is deliberately enabled.
- Analytics Token is read-only. It cannot place, modify or cancel orders. Live trading remains disabled; PAPER-only guard unchanged.
- Official docs: https://upstox.com/developer/api-documentation/analytics-token/ ; https://upstox.com/developer/api-documentation/announcements/analytics-token-static-ip/ ; https://upstox.com/developer/api-documentation/v3/get-market-data-feed/
- CI for this new implementation is pending. Do not mark it accepted until exact-head CI passes, including migration round-trip and token isolation tests.

## Verified Analytics Token checkpoint — 30 October 2026

- Implementation head `083ab17a5150ea3be514438a16ea7c6c888c0be3` passed Backend CI #41017833952: 1,243 passed, 1 warning. Broker-write boundary, SQLite/PostgreSQL 16 migration round-trips and synthetic restore drill all passed.
- Analytics Token is stored separately encrypted, owner-scoped, expiry-checked and never returned in API output/logs. It is used only for documented read-only market-data/streaming/charge-estimate routes. Standard OAuth remains separate for account endpoints not enabled for Analytics Token or requiring static IP.
- Real token entry and live API smoke test remain a deployment/user setup gate; code CI is not proof of a real broker session.
- PAPER-only and live order-write safeguards unchanged; PR #8 remains Draft/unmerged; do not update main or the original Tradepro repository.


## Upstox V3 full market feed increment — 30 October 2026

- Audited the existing V3 streamer before changing it; retained the existing authorized-URL flow, TLS validation, protobuf decoder, reconnect loop, stale-tick rejection and callback contract.
- Extended `UpstoxMarketDataStreamer` to subscribe in official V3 `full` mode by default (five-level depth; Upstox documentation calls this `full`, not `full_d5`). LTPC and `option_greeks` remain explicit supported modes. `full_d30` is deliberately rejected because it is a Plus entitlement and not assumed available.
- Full-mode tick model now exposes bid/ask depth, option Greeks, OI, traded volume, average traded price, total buy/sell quantity and OHLC snapshots. Optional provider fields remain `None` when not supplied; proto3 scalar default zero is not represented as confirmed data. Existing freshness validation remains unchanged.
- Applied documented individual subscription limits: LTPC 5,000; option Greeks 3,000; full 2,000. The V3 docs also specify a 1,500 combined limit when mixing categories and per-user connection limits; cross-connection aggregate enforcement belongs in a user-scoped subscription manager and remains a follow-up, not claimed complete here.
- Added regression tests for full-feed decoding, absent-field semantics, mode-specific limits, and exact binary subscription request mode.
- Code/test head: `8ba7009ef478ec256ba8b882351bdf514a9e324e`. Exact-head CI is pending verification; no green status is claimed for this increment.
- Official contract checked: https://upstox.com/developer/api-documentation/v3/get-market-data-feed/ . The official documentation describes `full` as LTPC + five market levels + metadata + Greeks, and confirms India VIX instrument key `NSE_INDEX|India VIX`.
- Next: verify exact-head CI and fix any failures; then implement the official Option Chain REST endpoint using `oi`, `prev_oi`, volume and Greeks, with missing/null/zero kept distinct. Follow with a subscription manager and shared worker/API market-data pipeline.
- Safety: only `tarunsharma2610-del/tradepro-improved`; PR #8 remains Draft/unmerged; main and original Tradepro untouched; PAPER mode mandatory; live broker order writes disabled.


## Upstox option-chain + mode-correct streaming increment — 30 October 2026

- Exact preceding docs head `c00278fb33cc094a0f07d6a61d3ca9827f2dcdcf` passed Backend tests #41018852112 and #41018839615. These runs verify the preceding full-feed/doc checkpoint only, not the new code below.
- Added optional broker-adapter `get_option_chain` capability and Upstox implementation for the documented `GET /v2/option/chain` endpoint. The authenticated API route `GET /api/v1/market-data/option-chain` uses the separately stored Analytics Token only, validates exact ISO expiry or supported relative expiry keywords, and rejects MCX because Upstox documents that exchange as unsupported for this endpoint.
- Upstox's response supplies strike-wise call/put market data, OI, previous OI, volume, bid/ask and Greeks. The application adds `change_oi = oi - prev_oi` only when both source values are present and finite; otherwise the derived field is `null`. Original provider fields are retained and no missing/null value is converted to zero.
- Fixed a scope bug found during audit: the stream manager already retrieves Analytics Token, but the HTTP start route was still gating on daily OAuth. Stream start now correctly requires a valid Analytics Token; it does not require daily OAuth for public market-data streaming. The route reports the actual selected feed mode.
- Added explicit stream mode selection: `ltpc`, `option_greeks`, or `full`, defaulting to `full`. Mode-specific limits are validated before starting: LTPC 5,000; Option Greeks 3,000; Full 2,000. The user-scoped manager runs one stream per user, below Upstox's normal two-connection ceiling. No Plus-only Full D30 assumption.
- Option Greeks mode decodes the documented first-level bid/ask depth, Greeks and IV. Full mode retains D5 depth, OHLC and extended metadata parsing. Regression tests cover adapter endpoint/query/auth, provider errors, option-chain route, MCX rejection, expiry validation, OI delta semantics, Analytics Token-only stream authorization, selected modes and mode-specific limits.
- Code/test head: `42be7ad2a33c2e7a6db08842a5ec9c7c30154af5`. Exact-head CI for this increment is pending; do not claim green until the exact current PR head has passed backend tests and all safety/migration checks.
- Official contracts: https://upstox.com/developer/api-documentation/analytics-token/ ; https://upstox.com/developer/api-documentation/get-pc-option-chain/ ; https://upstox.com/developer/api-documentation/v3/get-market-data-feed/ ; official V3 proto: https://assets.upstox.com/feed/market-data-feed/v3/MarketDataFeed.proto . Analytics Token supports Option Chain and WebSocket without static IP; MCX Option Chain is not available.
- Next after exact-head CI: add/verify index + India VIX feed presets and subscription lifecycle management (subscribe/change_mode/unsubscribe) with per-user limits; then test WebSocket recovery and option-chain snapshot/stream consistency. Do not create a duplicate market-data service or Redis bridge without a proven process-boundary need.
- Safety: only `tarunsharma2610-del/tradepro-improved`; PR #8 remains Draft/unmerged; main and original Tradepro untouched; PAPER mode mandatory; live broker order writes disabled.


## Upstox V3 subscription lifecycle — 30 October 2026

- Verified the official V3 WebSocket contract directly: methods are `sub`, `unsub`, and `change_mode`; requests must be sent as binary protobuf-feed protocol frames containing JSON bytes. The V3 docs specify normal per-category individual limits of LTPC 5,000, Option Greeks 3,000 and Full 2,000; when categories are mixed, the combined limits are 2,000 for LTPC/Greeks and 1,500 for Full. This implementation deliberately uses one mode per user stream, so it enforces the corresponding individual limit and does not claim mixed-mode capacity.
- Added native live subscription management to the existing streamer: add instrument keys with `sub`, remove keys with `unsub`, and change the mode of the complete user stream with `change_mode`. It preserves the desired subscription set across reconnects and sends the current complete subscription/mode on the next connection.
- Mode changes invalidate cached ticks so depth/Greeks from a previous feed mode cannot be consumed as if they came from the newly selected mode. Unsubscribed ticks are removed. The final key cannot be removed via partial unsubscribe; use DELETE `/market-data/stream` to stop the stream.
- Added authenticated API endpoints: POST `/api/v1/market-data/stream/subscribe`, POST `/api/v1/market-data/stream/unsubscribe`, and POST `/api/v1/market-data/stream/change-mode`. Each is user-scoped, checks the Analytics Token, verifies active instrument keys before subscribing, and rejects requests when there is no running stream. Partial mixed-mode changes are intentionally rejected; change mode applies to all keys in the stream to keep one consistent parser/mode contract.
- Added tests for binary V3 control requests, dynamic subscribe/unsubscribe/change_mode, reconnect replay of updated desired state, per-mode limits, stale tick invalidation, active-instrument validation, and missing-stream conflict responses.
- Exact previous code/test head `e53ac0f9a24bf3a92a409fa548d59b41206a5042` passed Backend CI #41019403337. Current subscription-lifecycle head: `7aecd1e5b9a77a44fe3b0885a89a88e4826c2d33`; exact-head Backend CI #41019804917 is queued, and prior incremental runs are queued/running. Do not mark this lifecycle increment green until the latest exact head passes all backend, broker-write, SQLite/PostgreSQL migration and synthetic restore checks.
- Official source: https://upstox.com/developer/api-documentation/v3/get-market-data-feed/ (method semantics, binary request format, India VIX key, and individual/combined limits).
- Next after exact-head CI: add verified index/India VIX presets based on instrument-master keys, then reconnect/subscribe race tests and end-to-end quote fan-out to the scanner/strategy data path. No second stream service, Redis bridge, or live-order capability is being added without a demonstrated requirement.
- Safety: only `tarunsharma2610-del/tradepro-improved`; PR #8 remains Draft/unmerged; main and original Tradepro untouched; PAPER mode mandatory; live broker order writes disabled.


## Verified checkpoint — 30 October 2026 (subscription lifecycle CI green)

- Exact implementation commit `b87245002a24bb0bd002b7e0c7dc5bbc82085357` passed complete Backend CI run #41020300281: backend pytest, broker-write boundary, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration upgrade/downgrade/re-upgrade, synthetic PostgreSQL + document-volume restore drill, and restore evidence retention. Run: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41020300281
- The lifecycle-test correction now tests partial mode-change rejection with two subscribed instruments, so the test exercises the actual partial-subscription case instead of incorrectly treating a single-instrument complete-stream mode change as partial.
- Subscription lifecycle implementation includes authenticated user-scoped subscribe/unsubscribe/change-mode routes, active-instrument validation before subscribe, per-mode subscription limits, reconnect replay, and invalidation of cached ticks after mode changes. No live broker order capability was introduced.
- This is the accepted code/test checkpoint. Documentation synchronization is being committed separately; the exact documentation head must receive its own CI verification before the next code increment.
- Next implementation: index feed presets backed by dynamically resolved and locally validated Upstox instrument keys (Nifty 50, Nifty Bank, India VIX). Do not hardcode exchange tokens. Use the official Instrument Search API and Upstox developer documentation; preserve provider identifiers and source timestamps. Then implement freshness/recovery observability and scanner/strategy fan-out.
- Official references: https://upstox.com/developer/api-documentation/instrument-search/ ; https://upstox.com/developer/api-documentation/v3/get-market-data-feed/ ; India VIX key documented as `NSE_INDEX|India VIX`.
- Safety: work only in `tarunsharma2610-del/tradepro-improved`; PR #8 remains Draft/unmerged; do not change main or original `Tradepro`; PAPER mode mandatory; all live broker order writes remain disabled. No credentials or tokens in code, logs, docs or chat.


## Verified checkpoint — 30 October 2026 (rich market-data snapshot CI green)

- Exact implementation/test commit `036ad952ced862e94b2c4d3af75b79b43a0bbc28` passed full Backend CI run #41022649412: backend pytest, broker-write boundary, SQLite Alembic upgrade/downgrade/re-upgrade, PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade, isolated synthetic PostgreSQL + document-volume restore, and evidence retention. Run: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41022649412
- Corrected the missing-quote stream-status test to apply the normal authenticated-user dependency overrides. Production authentication remains required; the assertion that an absent latest quote is represented as unavailable remains in place.
- The stream status response now exposes the validated fresh tick snapshot fields needed by downstream read-only consumers: instrument key, LTP, exchange timestamp, receive time, depth, option Greeks, OI, traded volume, average traded price, total buy/sell quantities and OHLC. Missing quotes remain null; do not infer freshness from a missing tick.
- Index presets are implemented from the locally synchronized official Upstox instrument master and fail closed for missing/ambiguous matches. Do not hardcode dynamic exchange instrument identifiers.
- Architecture note: the existing WebSocket stream manager is process-local. A worker in a separate process cannot read its in-memory cache. Before scanner/strategy consumers depend on streamed ticks, implement and test a shared cross-process delivery layer using the Redis already present in deployment (or another justified existing shared store). Redis Pub/Sub alone is not durable: pair notification with a TTL-bounded latest-quote cache/snapshot, explicit timestamps, freshness checks, and reconnect/recovery semantics. On Redis loss or stale/missing quote, consumers must fail closed and retain existing candle freshness and PAPER/risk gates.
- Next work: audit current Redis configuration and Redis Python package APIs; define a small versioned quote envelope and namespaced user/instrument keys; implement publisher + cache write in the existing stream lifecycle; implement worker/API consumer with TTL and timestamp validation; test outage, reconnect, expiry, ownership isolation and process restart; only then connect scanner and paper strategy consumers.
- This checkpoint does not certify Redis fan-out, scanner integration or strategy integration as complete. No live broker order capability was introduced.
- Safety: work only in `tarunsharma2610-del/tradepro-improved`; PR #8 remains Draft/unmerged; main and original `Tradepro` untouched; PAPER mode mandatory; live broker order submission/modification/cancellation disabled; no credentials in code, logs, docs or chat.


## Phase 4 architecture addendum — Redis market quote publication (30 October 2026)

The Upstox V3 stream manager now routes its per-user asynchronous tick callback to `RedisMarketQuotePublisher`. The publisher writes a versioned latest-quote snapshot under a user-scoped key with TTL and publishes a per-user Pub/Sub notification. The snapshot is authoritative; Pub/Sub is only a wake-up signal. The publisher validates instrument-key shape, finite positive LTP, positive exchange timestamp, timezone-aware receive timestamp, and configured freshness bounds. Redis failure is logged and the tick is unavailable to downstream consumers; no in-memory fallback is permitted. The version counter also expires to avoid unbounded key retention. Exact-head Backend CI #41024607462 passed on `72b22a647f2b9a38ac7afc0aaee9547a67b16fcf`. Consumer-side validation/recovery and real cross-process tests are not yet implemented; scanner and strategy do not yet consume Redis snapshots.


## Phase 4 market-data delivery — Redis checkpoint (30 October 2026)

The Upstox V3 streamer remains the process-local WebSocket ingress and its existing async tick callback publishes validated ticks through `RedisMarketQuotePublisher`. Redis is the cross-process quote transport/cache; it is not a second market-data provider. The publisher uses a Lua script to atomically allocate per-user/per-instrument versions, write expiring authoritative snapshots, and publish lightweight wake-up notifications. Consumers must read and validate snapshots; Pub/Sub payloads are never trusted as quote values.

Backend CI provisions Redis 7 and PostgreSQL 16. Exact-head Backend CI #41026567279 passed on `1c70e17a0ea54f8e8f219ae27d90aa46a02ea16e`. Current limits: consumer reconnect/resubscribe after Redis outage, actual Redis server restart recovery, and independent OS-process tests remain pending. Scanner and strategy do not yet consume this shared quote stream. Downstream components must enforce user isolation, TTL, exchange timestamp, schema/version checks, and fail-closed stale-data handling.


## Phase 4 Redis version-counter lifecycle — 30 October 2026

Exact-head Backend pytest CI #41031153316 passed on `3088e49cf24317f58f7e04a60d6cd54e065143b4`: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41031153316. The Redis publisher no longer applies TTL to the version counter; the authoritative quote snapshot continues to expire. A real Redis integration test verifies that deleting/expiring a snapshot and publishing a subsequent tick produces the next version rather than resetting the version sequence.

This addresses ordinary snapshot expiry, not Redis data-loss epochs. A Redis server restart can erase volatile counters and snapshots; consumer-local high-water marks must be reset/reconciled safely and a post-reconnect authoritative snapshot sweep must occur. Persistent version keys also need an explicit bounded-retention/cleanup policy for instruments no longer subscribed. Independent OS-process delivery and sustained multi-tenant load remain pending; scanner and PAPER strategy do not yet consume this transport.


## Phase 4 Redis bounded epoch/version lifecycle — 30 October 2026

Exact-head full Backend CI #41032764754 passed on `7268edd6e7ddb7ef6d472799d1d0164b4210b135`: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41032764754. Redis quote snapshots retain a short TTL (15 seconds by default); per-user/per-instrument version state has bounded retention (24 hours by default) and includes a unique epoch. A Lua script atomically allocates epoch/version, writes the snapshot and publishes the notification. Legacy integer-only counters are migrated on the next publish.

When a counter expires or Redis loses volatile data, the next publish creates a new epoch and starts at version 1. Consumers compare epoch and version together, allowing a version reset only across epochs. Real Redis tests cover snapshot expiry, counter expiry/new epoch, Pub/Sub disconnect recovery, server process restart, independent OS-process delivery, two-user isolation and concurrent publishing.

Current architectural boundary: `RedisMarketQuoteConsumer` is implemented and tested, but the background worker does not yet manage consumer instances or durable per-user subscription discovery. `app/worker.py` still evaluates strategies through the existing historical/intraday candle path. Scanner and PAPER strategy Redis integrations remain future milestones. Multi-user/multi-instrument scale testing and worker lifecycle/shutdown testing remain pending.


## Phase 4 Redis consumer recovery and integration boundary — 30 October 2026

The Redis quote consumer validates user-scoped authoritative snapshots (schema, instrument, TTL, received/exchange timestamps, epoch and version), treats Pub/Sub events only as wake-up signals, sweeps snapshots after subscribe/reconnect, and uses Pub/Sub PING/PONG to detect idle dead connections. On connection failure it clears process-local epoch/version high-water marks before re-reading the authoritative snapshot, allowing a new Redis epoch to restart at version 1 after volatile data loss.

Backend CI #41060945704 passed on `f7c863977ed17a3d705b83db8dcc6b7ba421cccf`. New tests on `a5e352bef2c78f27141b61bca5893fdfa0fd049a` cover old epoch version 8 -> new epoch version 1 and idle Pub/Sub heartbeat; exact-head CI #41061518847 is pending.

Important boundary: `backend/app/worker.py` does not yet manage Redis consumer instances; strategy evaluation still uses the existing candle path. Durable subscription discovery, single-owner coordination across worker replicas, graceful consumer cancellation/shutdown, and scanner/PAPER strategy integration remain incomplete. Do not treat publisher/consumer tests as proof of end-to-end scanner delivery or production deployment.


## Phase 4 current checkpoint — 30 October 2026

The transactional PAPER stop-event claim implementation at `6ac3882a98f3c66abb4cd62848971b6277ab3be7` passed exact-head Backend CI #41080156436. The claim service validates tenant and strategy ownership, uses portfolio → strategy → position locks, rejects ambiguous shared-position ownership and duplicate quote identity, and stores a bounded claim lease. It is not connected to quote dispatch or order execution. Next gates: PostgreSQL 16 multi-worker concurrency, lease reclaim/crash recovery, explicit shared-position ownership, then controlled PAPER integration. PR #9 stays Draft/unmerged; PAPER-only; live broker writes disabled; original Tradepro repository out of scope.


## 2026-10-30 — Phase 4 PostgreSQL 16 stop-claim concurrency checkpoint

Exact implementation SHA `0d3700f0a12add3239457bc4009eb019d77c78a0` passed [Backend CI #41090051358](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41090051358). Verified: backend pytest with PostgreSQL 16 multi-session claim-race coverage, broker-write boundary, SQLite and isolated PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade, and synthetic PostgreSQL/document-volume restore. Migration validation is isolated in `tradepro_migration_check`. Next work is lifecycle transition and lease recovery design/testing; no broker order submission is in scope. PR #9 remains Draft/unmerged, PAPER mandatory, live writes disabled, and only Tradepro Improved is authorized.
