<!-- Phase 3 checkpoint update — 27 Oct 2026. Latest code/test head 8feeb0cbb0c35e1e37012302c9075d43f1f33eb1 passed Backend CI #40458822529: 1,097 passed, 1 warning. Broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore and evidence retention passed. DP completeness checks require a consistent KNOWN + explicit valid finite nonnegative paise-exact amount, or NOT_APPLICABLE + no amount; invalid status, UNKNOWN-with-amount, KNOWN-without-amount, NOT_APPLICABLE-with-amount, NaN, negative and fractional-paise amounts fail closed. DP canonical manifests are checked against persisted broker trade → child order → local order mappings; only mapped equity-delivery SELL fills are accepted. Delivery SELL still requires reviewed/reconciled DP evidence and durable per-fill allocation; DP is included once in total and replay identity. Maintained docs are being synchronized after the green code run; exact-head CI on the final docs/checkpoint commit must pass before it is called green. PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled; original Tradepro repository out of scope. -->

## GST/IPFT statutory-engine implementation update — 26 October 2026 (code/test CI passed; docs head must be checked)

- Added `backend/app/services/statutory_stock_broking_gst.py` and `backend/tests/test_statutory_stock_broking_gst.py` on the current Phase 3 branch. The service implements CGST Act section 15's default taxable valuation, conditional CGST Rule 33 pure-agent exclusion requiring every evidence flag, and IGST Act section 12(12) recipient-location/fallback state selection for IGST versus CGST+SGST.
- Service/test changes are in commits `dcad71e148b89a2c384631b36090008c8fad193e` and `037ad2da02dca34c399e0ec454674c50ae65b5a7`, included in the verified checkpoint head above. Exact-head Backend CI [#40375335160 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40375335160) passed on checkpoint head `cc2d591cf74daea5d68b6ba704ae87a342cc96fd`: **1,051 passed, 1 warning**. Broker-write guard, SQLite/PostgreSQL 16 migration round-trips and synthetic restore drill passed. Later documentation commits are newer and still require exact-head CI verification.
- The statutory engine is a separate primitive and is not yet wired into actual per-fill accounting. It does not infer Rule 33 pure-agent status from a charge label; absent complete evidence, third-party recovery lines remain in the section 15 base. It keeps the Upstox published-schedule estimate separate from statutory valuation and does not override the unresolved API sample discrepancy.
- Regression coverage added for combined/separate exchange/IPFT values in the taxable base, Rule 33 all-conditions gate, same-state versus cross-state tax type, recipient-state fallback, invalid/missing money, duplicate line names, and paise rounding. Intra-state CGST/SGST tax heads are rounded independently to paise and the returned total equals the two heads.
- Remaining gates: run exact-head backend CI and fix failures; independently review tax-head rounding and legal policy; implement product/broker effective-dated mapping and IPFT resolver; complete DP/demat persistence + total reconciliation; integrate only reviewed policy paths; synchronize this checkpoint again to the final CI-verified head. Actual per-fill invoice evidence remains deferred until source records/deployment exist; no personal contract note is required.
- Official source basis: [CBIC stock-broking FAQ](https://cbic-gst.gov.in/sectoral-faq.html), [CGST Act section 15](https://cbic-gst.gov.in/hindi/CGST-bill-e.html), [Upstox Brokerage Details API](https://upstox.com/developer/api-documentation/get-brokerage/), and [Upstox public charges](https://upstox.com/brokerage-charges/).
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; PR #6/#7 Draft and unmerged; PAPER-only; live broker writes disabled; original `Tradepro` untouched.
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

## Deferred follow-up reminder — AI integration and Algory.app

- Do not start AI integration until Phase 3 is accepted. The persistent plan is [docs/AI_INTEGRATION_ALGORY_GAP_PLAN.md](docs/AI_INTEGRATION_ALGORY_GAP_PLAN.md); the master roadmap links it.
- The plan includes the Algory.app capability gap matrix and eight research-agent roles. At Phase 3 completion, re-audit current code/tests and decide only verified gaps; do not duplicate existing engines.
- Current work remains Phase 3 tariff/component evidence gates. PAPER mandatory; live broker order writes disabled; PR #6 stays draft/unmerged absent explicit approval; original Tradepro repository untouched.

---

## Historical checkpoint (superseded) — 26 October 2026 (latest verified CI)

- Target repository only: `tarunsharma2610-del/tradepro-improved`; branch `phase3/durable-per-fill-charge-allocation`; implementation/test head `44830ec48b50b4f470ec9ca95dd2d3f4339dd3df`. Do not modify original `Tradepro`.
- Exact-head Backend CI: [run #40294178677 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40294178677), including the test separating NSE/IPFT arithmetic reconciliation from GST taxable-base approval.
- GST estimate helper accepts exactly 18%; tests reject 0%, 5%, 100%, and 100.01%. This is a rate guard only; taxable component composition remains evidence/reviewer-controlled.
- ₹307/crore versus ₹306.99/crore transaction charge + ₹0.01/crore IPFT is arithmetic reconciliation only, not GST-base approval.
- Canonical live-fill integration is verified: six independently verified charge snapshots, source/mapping/fill evidence revalidated under lock, no raw-only fallback; brokerage cap applied once before deterministic paise-exact allocation.
- Remaining Phase 3 gates: effective-dated tariff applicability; component-specific per-fill allocation acceptance; invoice/source-backed GST/IPFT and product/segment evidence; adversarial/migration/recovery review; final exact-head documentation/sign-off. Do not redo canonical integration.
- Upstox public schedules/calculator are estimates; aggregate charges endpoint is not actual per-fill evidence. Null remains unknown, not zero. Synthetic restore is not actual Oracle recovery.
- PAPER mandatory; live broker writes, automatic live-fill promotion and automatic scheduling disabled. PR #6 stays open/draft/unmerged unless explicitly approved. Defer AI/open-source adaptations until Phase 3 acceptance. This docs commit needs its own CI.

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


## Phase 3 forward checkpoint — 25 October 2026

- Implementation now preserves additional documented Upstox source labels: `transaction_charges`, `clearing_charges`, `ipft`, `other_charges`, and `demat_transaction_charges`. These are evidence-intake vocabulary only and remain pending independent review.
- The allocation/source-component database constraints were expanded by migration `202610250019`; the API and regression tests cover intake. Live-fill accounting deliberately still requires exactly six reconciled components, so a separately reported IPFT or any extra component fails closed instead of being silently ignored or double-counted.
- Preserve the existing NSE/IPFT calculation: documented combined ₹307/crore versus ₹306.99 transaction + ₹0.01 IPFT yields the same ₹307 base and ₹55.26 GST at 18%. This arithmetic is already tested; it does not prove Upstox endpoint or contract-note field semantics.
- GST component composition remains product-, date- and invoice-dependent. No production tariff or API mapping is approved. Exact-head CI for the new code/migration/test changes is required before this checkpoint is called verified.
- PR #6 remains open/draft/unmerged; PAPER mode remains mandatory; live broker order writes and automatic generic quantity/notional allocation remain disabled. Work only in `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is out of scope.

## Upstox SDK/API audit checkpoint — 24 October 2026

**Start here:** [`docs/UPSTOX_SDK_API_REPOSITORY_AUDIT.md`](docs/UPSTOX_SDK_API_REPOSITORY_AUDIT.md).

- Repo boundary: `tarunsharma2610-del/tradepro-improved` only. Never touch original `tarunsharma2610-del/Tradepro`.
- PR #6 remains open, draft and unmerged. PAPER mode is mandatory; live order place/modify/cancel remain disabled.
- SDK is not currently declared in `backend/requirements.txt`; existing async `httpx` adapter, dedicated V3 protobuf/WebSocket streamer, read-only reconciliation client, and brokerage parser already cover multiple API functions.
- Do not add SDK blindly. Next: inspect the exact official Python SDK release, license, methods and dependency tree in an isolated environment; prototype only read-only brokerage-estimate response compatibility against synthetic fixtures. Preserve current timeout, sanitized errors, async operation and accounting semantic checks.
- Review official Upstox Agent Skill files/scripts as development-only reference; do not run trading examples or give the skill live credentials.
- No account token, live API call, or order was used during the audit. Brokerage estimate remains an estimate, aggregate charges remain aggregate, and all tariff candidates remain DRAFT.
- CI passed for prior head `3533c129af7f9ed4c3d741463a326b5a01cc3282` in [run #40116782403](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40116782403). Recheck CI for the final documentation head after these documentation commits.

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

The source register now marks the Upstox-page conflict partially reconciled for those NSE scopes, not fully approved. Account-specific API/contract-note reconciliation, effective-date/product-scope review and GST composition remain gates; this circular does not establish BSE/MCX rules. Candidate comment/test updates encode DRAFT combined rates (NSE cash 0.00307%, futures 0.00183%, options 0.03553%; BSE options 0.0325%) and forbid a separate IPFT candidate. Commits `68aae327`, `fc7fb146`, `c01cd66c`, and `777d0ee5` are included in the current PR head and covered by exact-head backend CI #40090309898 (786 passed, one warning). Their CI gate is closed; candidate source-rate approval and account-specific tariff validation remain open.

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

- Documentation checkpoint commit `3e0ae8034f333e082bfa11b6da50aec9e620f242` passed GitHub Actions Backend tests run [`40091642139`](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40091642139).
- Result: **787 passed, 1 warning** in pytest. Broker-write boundary guard passed; SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed; synthetic PostgreSQL/document-volume restore drill and evidence-artifact retention passed.
- The warning is a Starlette/AnyIO deprecation warning; the run also reports GitHub Actions Node.js 20 deprecation notices. No test or safety-guard failure was reported.
- This verifies commit `3e0ae803` only. Any new documentation commit must receive its own exact-head CI run before the checkpoint is considered green.
- Phase 3 remains open pending final accounting acceptance and tariff-source applicability decisions. PR #6 remains draft/unmerged; live broker order submission remains disabled. Work only in `tarunsharma2610-del/tradepro-improved`, never the original `tarunsharma2610-del/Tradepro`.

## Accounting acceptance CI — 24 October 2026

- Commit `0dee50af510c1f47e50093a3f796aef5fb32707b` passed Backend tests workflow [#40092273865](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40092273865).
- Pytest result: **787 passed, 1 warning in 48.24 seconds**. Broker-write boundary guard passed. SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed. Synthetic PostgreSQL/document-volume restore drill and evidence retention passed.
- The pytest warning is the Starlette/AnyIO `BlockingPortal` deprecation; the workflow also emitted Node.js 20 / dependency deprecation notices. No test or broker-write guard failure was reported.
- This validates commit `0dee50af` only. Any later change requires its own exact-head CI run.
- Acceptance remains open: tariff candidates are not approved; the current NSE source register explicitly limits what the NSE circular establishes, and actual Upstox invoice/contract-note evidence is still needed to approve product-scoped GST and tariff component mapping. Targeted rollback tests exist, but they are not exhaustive fault injection. PR #6 remains draft/unmerged and live broker order submission remains disabled. Work only in `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` is out of scope.

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

## Upstox P&L metadata API — 24 October 2026

- Added fixed-path read-only `get_profit_loss_report_metadata` for `GET /v2/trade/profit-loss/metadata`. It validates segment, financial year and optional date scope, and exposes the documented `trades_count` and `page_size_limit` metadata used to plan pagination of `/trade/profit-loss/data`.
- Added regression tests for normalized request scope, returned page-size metadata, and invalid scope/date rejection. The metadata endpoint contains no charge components and does not alter the contract-note evidence requirement.
- The metadata API and regression tests passed exact-head CI in [run #40093554718](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40093554718): 792 tests passed, 1 warning; broker-write guard, SQLite/PostgreSQL 16 migration checks, and synthetic restore/evidence retention passed.
- Tariff candidates remain DRAFT/non-selectable; PR #6 remains draft/unmerged; live broker order submission remains disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope.

## Latest verified checkpoint — 24 October 2026

- Exact-head CI for the Upstox P&L metadata API and its regression tests completed successfully in [run #40093554718](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40093554718): **792 tests passed, 1 warning**; broker-write boundary guard, SQLite migration round-trip, PostgreSQL 16 migration round-trip, isolated synthetic restore drill, and restore evidence retention all passed.
- The metadata endpoint is read-only and provides `trades_count` / `page_size_limit`; it informs pagination only. The P&L data endpoint remains trade-wise matching context, not per-fill charge evidence. The charges endpoint remains aggregate scope only.
- The three equity STT DRAFT candidates now use the source-stated 1 April 2023 effective date; candidates remain non-selectable. No charge-allocation or tariff-promotion gate has been bypassed.
- PR #6 remains draft/unmerged. Live broker order submission remains disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; the original `tarunsharma2610-del/Tradepro` is untouched.
- Next Phase 3 work: resume the durable per-fill charge-allocation acceptance audit, especially evidence identity/matching, rounding/residual handling, replay/idempotency, rollback, and aggregate variance regression coverage. Do not promote tariffs or allocate aggregate charge totals across fills without an approved deterministic policy and reviewed contract-note evidence.

## Variance rollback regression added — 24 October 2026

- Added `test_variance_insert_flush_failure_rolls_back_record_without_mutating_accounting` in `backend/tests/test_broker_charge_source_reconciliation_service.py`.
- The regression injects a failure at variance-record flush and asserts the nested savepoint leaves no variance row and does not mutate reviewed evidence, source component data, or pending allocation rows.
- Commit: `edbc0852a72978577d8da8651e8fdce932e9593d`. Exact-head CI must complete before this test is considered verified; the prior successful run does not cover this new test.
- Phase 3 acceptance remains open pending CI, source-backed tariff/GST mapping, and final charge-allocation acceptance. Tariff candidates remain DRAFT; live broker order submission remains disabled; PR #6 remains draft/unmerged.


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

## 2026-10-24 — IPFT regression checkpoint

Added tests for NSE combined rates (0.00307% cash equity, 0.00183% equity futures, 0.03553% equity options premium from 2026-03-01), no second IPFT candidate, combined-vs-split GST-base invariance, and no MCX scope leakage. Test commit: `69945f4854ea8ae7d20e7795b156750406759df7`; source-register update: `626298aa9d8c60712189a744c86a3327eac1bb50`.

Next: verify CI on the exact branch head, then add explicit normalization tests for authenticated API fields only after the API semantics are established. Do not infer field meaning from schema names. Need a dated Upstox contract note/tax invoice or authoritative support clarification for independent account-specific mapping. Keep tariff candidates DRAFT, PR #6 draft/unmerged, live broker order submission disabled, and do not touch original `Tradepro`.


## 2026-10-24 — IPFT CI checkpoint

Run #40101490646 passed for commit `a8166bafe77544bf958d0d393b71432379898b72`: **805 passed, 1 warning**, broker-write guard passed, SQLite/PostgreSQL 16 migration round-trips and synthetic restore drill passed. See https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40101490646.

Next work: test canonicalization only when API semantics are established, including missing vs null vs zero, combined vs split values, effective-date/product scope and GST base. A CI pass is not evidence of live Upstox field semantics. Keep tariffs DRAFT, PR #6 draft/unmerged and live broker writes disabled; never touch original `Tradepro`.


## Historical Upstox statement evidence — 24 October 2026

User supplied a redacted screenshot of an RKSV/Upstox Annual Global Transaction Statement for FY 2022–23, Futures & Options. Visible summary lines include transaction charges ₹111.61, brokerage ₹1,000.00, IGST ₹20.15, SEBI fees ₹0.22, stamp duty ₹3.00 and STT lines ₹0.32/₹51.89. No separate IPFT line is visible, but that does not prove IPFT was included in transaction charges. The annual summary is not an individual trade contract note and does not establish API field semantics. Source register updated in commit `9bb2fade8330e068022e5b2f6be0538e4f19206e`.

Next: if original PDF and a matching dated Upstox API response exist, reconcile them with historical rates and bases. Keep actual-charge promotion blocked on this evidence alone; tariff candidates DRAFT, PR #6 draft/unmerged, live broker writes disabled, original Tradepro untouched.

## 2026-10-24 — NSE IPFT handling clarification

Source register commit `6c85292d07d33e1e873293c40931895674f4e7fc` now states explicitly that the listed NSE combined exchange-charge rates effective 2026-03-01 already include the revised IPFT contribution. Existing candidate tests assert the rate/date scope and prohibit a separate IPFT candidate from being stacked on top. These candidates remain DRAFT/non-selectable; no tariff was activated.

Resume with exact-head CI for the new documentation commit, then review Upstox API field normalization (missing vs null vs numeric, combined vs split representation), GST taxable base, and remaining BSE/MCX source-backed schedules. PR #6 remains draft/unmerged, live broker writes disabled, and original `Tradepro` untouched.

## 2026-10-24 — Upstox API and BSE/MCX source cross-check

Source register updated in commit 2f6e55532e9704d4b41c9c736c38b1948ee5f05d: the Upstox brokerage endpoint is an estimate, while the trade-charge endpoint is a segment/FY summary. Keep missing, null, zero and numeric fields distinct; never infer per-fill actuals or double-count IPFT from a response schema alone. BSE/MCX comparison rates are research leads pending exact effective-dated exchange circulars and contract/scrip scope. Next: verify CI for the latest head, then source the governing BSE/MCX circulars and test API response normalization. Candidate rules stay DRAFT/non-selectable; PR #6 draft/unmerged; live broker writes disabled; original Tradepro untouched.

## 2026-10-24 — BSE/MCX tariff review

Source register updated in commit f978052402b2be79d99958427092a29eace83859. BSE equity requires date-specific scrip group/exclusivity data; the 2023 SENSEX nearest-expiry options notice describes monthly incremental premium-turnover slabs but is not enough to certify all 2026 BSE products; MCX FAQ confirms applicable statutory dues but is not a current tariff table. Next: verify exact-head CI, then implement/test response normalization and only add exchange rules when the exact governing current schedule and required input data are available. Do not activate generic BSE/MCX rates. Candidate rules DRAFT/non-selectable; PR #6 draft/unmerged; live broker writes disabled; original Tradepro untouched.


## Resume checkpoint — 24 October 2026 (after exact-head CI)

- Work only in `tarunsharma2610-del/tradepro-improved`; do not modify original `tarunsharma2610-del/Tradepro`.
- PR #6 head `5e256bc867409672a19025f0219c9d9c866ce898` is open, draft, and unmerged. Exact-head Backend tests workflow #40105708790 passed.
- Per-fill acceptance audit confirmed existing regression tests for exact fill-set manifests, source hash/document integrity, independent review provenance, reviewed-weight validation, exact source-total reconciliation, atomic/idempotent promotion, authorization recheck, rollback/fault injection, and variance-only comparisons with exact fill identity and aggregate-source rejection. Avoid duplicating these tests.
- Next work: build a component-by-component acceptance matrix tying each component to its calculation base, evidence source, effective-date scope, rounding, residual policy, GST treatment, and explicit promotion criteria. Keep any unresolved component fail-closed; do not enable automatic quantity/notional allocation or activate tariffs based on public schedules alone.
- User-provided FY 2022–23 annual statement is historical aggregate evidence only; it cannot prove IPFT inclusion or per-fill API mapping. A personal contract note is not a prerequisite for engineering work; use synthetic fixtures until genuine evidence is optionally available.
- All tariff candidates remain DRAFT/non-selectable; live broker order submission remains disabled. No PR merge without completed acceptance and user approval.


## Resume checkpoint — 24 October 2026 (component acceptance matrix)

- Added docs/PHASE3_CHARGE_COMPONENT_ACCEPTANCE_MATRIX.md at commit ac89f9ce84544ff4f53cb58bdf18e247d19177c9. It is an acceptance specification, not a tariff approval.
- The matrix covers brokerage, STT, exchange/IPFT, SEBI, stamp duty and GST; requires dated authoritative sources, correct calculation bases, explicit rounding/residual policy, no double counting, and independent review.
- CI workflow #40106537998 is running against the matrix head. Previous docs head 8a75153 passed workflow #40106273353. Verify exact-head CI before declaring this checkpoint green.
- Continue by mapping each acceptance row to existing code/tests and marking each item as implemented, missing, or blocked by source/review. Do not activate any tariff or automatic quantity/notional allocation. PR #6 remains draft/unmerged and live broker writes disabled.


## Resume checkpoint — 24 October 2026 (API field-state normalization)

- Acceptance matrix docs were verified by Backend workflow #40106582037 on matrix head f33953e903dcdd8655fa34eee9c612a36bd94b2c.
- Added `backend/app/services/broker_charge_api_normalization.py` and tests `backend/tests/test_broker_charge_api_normalization.py` to preserve absent/null/zero/value/invalid broker charge API field states and raw values. Test/code commits: 9fc9337e8dc2dbd45f8435260a8b0f57d3f856fa and f0e815c5b788744966bf2bacbfbe9c79dbfdd822.
- This does not assign business semantics to Upstox fields or prove IPFT bundling. The next task is exact-head CI, then reviewed API-version/field mapping tests and source-backed tariff gaps.
- PR #6 remains draft/unmerged; tariff candidates remain DRAFT/non-selectable; automatic quantity/notional allocation and live broker writes remain disabled. Work only in tradepro-improved.


## Resume checkpoint — 24 October 2026 (reviewed API field mapping gate)

- Workflow #40106757433 passed on commit `f0e815c5b788744966bf2bacbfbe9c79dbfdd822` for the field-state normalizer. Its backend, broker-write guard, migration and synthetic restore/evidence gates passed.
- Added `backend/app/services/broker_charge_api_mapping.py` and tests `backend/tests/test_broker_charge_api_mapping.py` to require an exact approved mapping by broker/endpoint/schema/field/scope/effective date. `UNKNOWN`, unapproved, missing and overlapping mappings fail closed. New mapping commits: `0461024f245d91e7114488d56d79e58722f9de9e` and `3a04aefc7e8bb9c0cf8e99889c5de89b4537dc63`.
- The new mapping is a guardrail only; no Upstox field semantics have been approved. Synthetic test fixtures are not evidence. Exact-head CI remains pending for the new mapping and docs.
- Continue by checking exact-head CI, then audit the acceptance matrix against code/tests and source-backed product-specific rules. Keep PR #6 draft/unmerged, tariffs DRAFT/non-selectable, automatic quantity/notional allocation disabled, and live broker writes disabled. Work only in `tradepro-improved`.


## Resume checkpoint — API mapping guard CI result

- Backend workflow #40106949357 passed for `3a04aefc7e8bb9c0cf8e99889c5de89b4537dc63` (API mapping guard + tests). Backend workflow #40106989369 passed for `cee4fa0fbd4eefc0850d26119bdc6fa11e3915a` (source-register docs).
- These runs validate those commits, not necessarily the current branch head after subsequent doc commits. Re-run exact-head CI before merge.
- No production Upstox field semantics are approved. Next: add a narrow controlled resolution function that combines normalized field state with an exact approved mapping and rejects aggregate scope for per-fill actual charges. Keep no fallback-by-name, no inference from null, no tariff activation, no automatic allocation, no live broker writes.


## Resume checkpoint — controlled API value resolution

- Added `backend/app/services/broker_charge_api_value_resolution.py` and tests `backend/tests/test_broker_charge_api_value_resolution.py` (code commit `3ca72caed52906b7d0749e204c1558a1e72c358e`, test commit `9734ace970b22031939eb87f9d99c1a5066f5097`).
- Resolver requires exact approved mapping and prevents aggregate summaries/estimates from being used as per-fill actual charges. Missing/null/invalid are unusable; zero remains an explicit value. It does not promote allocations.
- Synthetic fixture source is reserved and not authoritative; no Upstox production field semantics approved. CI for the resolver and later documentation commits must pass on exact head.


## 2026-10-24 — Charge API unusable-value provenance hardening

- Review found that `resolve_charge_api_value` retained the approved mapping's semantic and source fingerprint for usable values, but omitted source URL and SHA-256 provenance when the normalized field was `MISSING`, `NULL`, or `INVALID`. These values were already unusable, but their interpretation path was less auditable.
- Fixed the resolver to return approved mapping provenance for every normalized state while keeping missing/null/invalid values `usable=False`. Numeric zero remains a distinct present value; this change does not promote allocations or approve production Upstox mappings.
- Added regression coverage for missing, null, NaN, negative, boolean, and object values; assertions now require mapping source URL, source SHA-256, and semantic to remain present. Added mapping effective-date and estimate-vs-actual guard cases.
- Implementation commit: `845e9e0dc924f11ae89b96ef73c94c59c2efb4b4`. Test commit / branch head: `1d7e24b0ba8c89062ec1eeddb93d0c4cd22a226f`.
- Exact-head backend CI is running as workflow [#40107754617](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40107754617); do not mark this code/test head green until all workflow gates complete successfully.
- PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains out of scope.


## 2026-10-24 — Effective-date test fixture correction

- CI exposed one failing test among 850 total: the future-date case expected rejection while its synthetic mapping used `effective_to=None` (no end date). The resolver behavior was consistent with the fixture.
- Corrected the synthetic approved mapping to an explicit validity window ending `2026-12-31`, so both before-start and after-end cases test the intended boundary.
- Test fix commit: `9cb89301075a8b532ad634f2c9c60590b16deacc`. Awaiting CI for this commit and the final branch head; earlier run #40107829270 failed on the incorrect fixture and must not be treated as green.
- PR #6 remains draft/unmerged. Live broker order submission and automatic quantity/notional allocation remain disabled. Work stays in `tradepro-improved`; original `Tradepro` remains out of scope.


## 2026-10-24 — Intended-use semantic matrix regression tests

- Corrected effective-date fixture commit `9cb89301075a8b532ad634f2c9c60590b16deacc` passed its backend workflow (#40107967404); progress and handover documentation workflows also passed (#40107977310 and #40107980514). Latest branch documentation head `26daee136ab1e7b3dd9a9d985f986e063bb8f80e` passed workflow #40107984994. PR #6 remains draft/unmerged.
- Added resolver tests ensuring mapping semantics cannot be relabelled across intended use: per-fill actual, aggregate summary, and estimate; included valid semantic/use pairs and rejection of an unknown intended use. Test commit: `53ba96dc3700de75a64b415c095f6a5810efdaf0`.
- New test commit still requires CI. This test-only step does not approve production broker mappings, enable allocation promotion, or enable live broker order submission.
- Next accounting acceptance gap: test concurrent verification/promotion against a shared database with separate sessions, or explicitly document the limitation if the existing test harness cannot reliably exercise it. Keep lock order and rollback protections intact.
- Work remains in `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is out of scope.


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


## 2026-10-24 — Official tariff/API source audit

- Upstox Developer API `GET /v2/trade/profit-loss/charges` is scoped by segment, financial year and optional dates; it returns a `charges_breakdown` summary, not a documented per-fill record. Its published example has `charges.ipft: null`. Do not use this endpoint alone to ground actual per-fill charges; null remains distinct from zero. https://upstox.com/developer/api-documentation/get-trade-charges/
- NSE Finance & Accounts circular NSE/FA/73061 dated 27-Feb-2026 is effective 1-Mar-2026: combined member outflow ₹307/crore cash, ₹183/crore equity futures, ₹3,553/crore equity-options premium; IPFT contribution ₹0.01/crore each side. This is scoped exchange schedule evidence, not proof of Upstox's contract-note field mapping. https://nsearchives.nseindia.com/content/circulars/FA73061.pdf
- Upstox's public charges page lists newer effective-date summary tables alongside older historical tables. Apply effective-dated versioning; don't select stale rates based on page position. STT/CTT values also change from 1-Apr-2026 on the published page. https://upstox.com/brokerage-charges/
- No production mapping or tariff is approved. Keep mappings DRAFT; reject aggregate/estimate/null values for actual per-fill evidence; do not separately add IPFT where already included in combined exchange outflow.
- Latest code/test head before this note, `ee1b2a74d2a9f6141b9afbb6e06562b5cf263a9b`, passed Backend workflow #40110597753. This documentation change needs fresh CI verification.
- PR #6 remains draft/unmerged. Live order submission and automatic quantity/notional allocation remain disabled. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Aggregate endpoint hard guard added; CI pending

- Added a fail-closed resolver guard that blocks Upstox `/v2/trade/profit-loss/charges` from `PER_FILL_ACTUAL` use even if a registry row is incorrectly labelled per-fill. Official docs describe segment/financial-year/date-range aggregate `charges_breakdown`, not a per-fill schema.
- Regression test `test_official_upstox_aggregate_charges_endpoint_cannot_be_promoted_to_per_fill` verifies the endpoint restriction.
- Implementation `cdc07afdd8cc0c8d0b37d7e4aa8cdf1bf6eac651`; test `8ae749017a8ba0016f2c9adeb77eaff41fb5ae70`. Implementation CI is running; test workflow is queued. Await a green result before calling this safeguard verified.
- This does not approve production mappings/tariffs. Null remains distinct from zero; automatic quantity/notional allocation and live order submission remain disabled. PR #6 stays draft/unmerged. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Upstox brokerage calculator restricted to estimates; CI pending

- Official Upstox `GET /v2/charges/brokerage` takes proposed instrument, quantity, product, transaction type and price, returning a charge calculation; this is not proof of final booked per-fill charges. https://upstox.com/developer/api-documentation/get-brokerage/
- Resolver now blocks `/v2/charges/brokerage` from `PER_FILL_ACTUAL` and actual `AGGREGATE_SUMMARY` use even if a mapping is misleadingly labelled. Existing guard still blocks `/v2/trade/profit-loss/charges` from per-fill actual use. New regression tests cover both misuse cases.
- Implementation `3486d854dae2451858a858cb627602aca7338969`; tests `6c92101a1890a0f4d761e86ed3db047a269fd10d`. Prior head `6cc8b58f635fcb4f1b1cb3e5997099d074800a28` passed workflow #40111501429. CI for the new commits must be verified.
- Production mappings/tariffs remain unapproved; null is not zero; automatic quantity/notional allocation and live broker order submission remain disabled. PR #6 stays draft/unmerged. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.

## Upstox SDK/Agent Skill review checkpoint — 24 October 2026

Read [`docs/UPSTOX_SDK_API_REPOSITORY_AUDIT.md`](docs/UPSTOX_SDK_API_REPOSITORY_AUDIT.md) and [`docs/UPSTOX_AGENT_SKILL_SECURITY_REVIEW.md`](docs/UPSTOX_AGENT_SKILL_SECURITY_REVIEW.md).

- Static review only: official Python SDK tag `v2.30.0` and Agent Skill sources inspected; no package installed, skill executed, credentials used, live calls or orders made.
- The SDK's brokerage method is sync by default; the existing async `httpx` endpoint and parser already cover the same read-only feature. No runtime dependency was added without a measurable benefit.
- Skill includes real order/GTT scripts; helper can fall back to local config token and prints raw exception body in its profile smoke-test. Never run live-write examples with credentials or copy those patterns into app code.
- Continue Phase 3 per-fill charge allocation. Only adopt SDK runtime code for a concrete gap. Keep PR #6 draft/unmerged, PAPER mandatory, live writes disabled, and original `Tradepro` untouched.

---


## Phase 3 checkpoint — official GST/IPFT source cross-check (25 October 2026)

- Resumed the saved Phase 3 durable per-fill charge-allocation work. No framework code was integrated; current focus remains source-backed tariff acceptance and fail-closed accounting.
- Exact-head backend CI for prior head `7d4f2918b534ef9b4c3d32e7df22b754b21e6c8f` passed in run [40182196510](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40182196510). This verifies that head, not real-broker tariff authenticity or production restore.
- Current official Upstox charges page lists transaction charges effective 1 March 2026, STT effective 1 April 2026, GST bases by product, and says IPFT is combined with transaction charges while also showing an IPFT row. This does not establish whether a particular API `transaction` field is transaction-only or transaction-plus-IPFT. Do not double count IPFT or approve a field mapping until exact endpoint/schema semantics are verified.
- NSE confirms from 1 April 2026: options-sale STT 0.15% on premium (seller), exercised-option STT 0.15% on intrinsic value (purchaser), and futures-sale STT 0.05% (seller). CBIC says STT/stamp-duty/other-tax recoveries are outside GST value only where pure-agent conditions are met; otherwise Section 15/Rule 27 valuation applies. GST mapping must remain product/source-specific.
- No production field mapping or tariff was approved. Keep candidates DRAFT/non-selectable, preserve missing/null/zero distinctions, reviewed source-component evidence, paise-exact allocation, and fail-closed promotion. PAPER mandatory; live broker order writes disabled; PR #6 draft/unmerged; original `Tradepro` untouched.
- Official sources: https://upstox.com/brokerage-charges/ ; https://upstox.com/developer/api-documentation/get-brokerage/ ; https://upstox.com/developer/api-documentation/get-trade-charges/ ; https://www.nseindia.com/static/products-services/equity-derivatives-securities-transaction-tax ; https://cbic-gst.gov.in/sectoral-faq.html
- Next gate: continue component-by-component accounting acceptance and fault-injection/rollback review. Upstox's proposed-order brokerage calculator and segment/FY aggregate charges API are not proof of actual per-fill charges.


## Phase 3 resolver guard hardening — 25 October 2026

- Hardened source-level restrictions for Upstox aggregate-only `/v2/trade/profit-loss/charges` and estimate-only `/v2/charges/brokerage` endpoints. Guard canonicalizes broker-name casing and endpoint path spelling (trailing slash, query string, full URL) while reviewed mapping selection remains exact.
- Added regression tests so misleading approved mapping rows cannot convert aggregate/estimate data into per-fill actual accounting.
- Defensive code change only: no API field semantic or tariff approved. Production mappings remain unapproved, null is not zero, IPFT must not be double-counted, and charge-ledger promotion remains fail-closed.
- Exact-head CI for this code/documentation commit must be verified. PAPER mandatory; live broker writes disabled; PR #6 draft/unmerged; original `Tradepro` untouched.


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
- This is still not production tariff approval: GST composition, endpoint/schema semantics, authenticated real contract-note evidence, and per-fill allocation approval remain separate gates. No live broker writes or generic quantity/notional allocation were enabled.


## Representation-gate CI correction — 25 October 2026

- The first API regression run exposed two assertion-message mismatches: the validator correctly rejected ambiguous combined-plus-IPFT input and undeclared representation mode, but the tests expected different wording. Updated the tests to assert the validator's actual fail-closed error messages; no safety rule was weakened.
- Follow-up exact-head CI for commit `df344e9c64aeb6ec3f2f01fef01f3c05739d4800` and subsequent documentation synchronization is pending. Do not call the current head green until the full workflow completes.


## Source-label completeness gate — 25 October 2026

- Continued from the current Phase 3 branch head; reused the representation contract already present rather than repeating its implementation.
- Hardened `validate_charge_representation` so each normalized source component must have a retained original source label. Missing labels fail closed before review.
- Added a regression test for incomplete source labels and updated fixtures to retain one label per component.
- Exact-head CI must be checked for the final documentation head. No tariff/API mapping is approved, aggregate/estimate values are not promoted to per-fill actuals, and generic quantity/notional allocation remains disabled.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; PR #6 draft/unmerged; PAPER mandatory; live broker order writes disabled; original `Tradepro` out of scope.


## Authoritative IPFT/GST decision — 25 October 2026

This is the carried-forward project decision. Do not restart the IPFT/GST policy discussion or describe the agreed arithmetic as undecided. Keep the policy decision separate from the remaining source-evidence and production-approval gates.

### IPFT and NSE exchange-charge representation

Effective 1 March 2026, NSE circular NSE/FA/73061 records combined exchange-charge rates that include the IPFT contribution:
- Cash equity: ₹307.00 per crore.
- Equity futures: ₹183.00 per crore.
- Equity options: ₹3,553.00 per crore.

Canonical equivalent split arithmetic (transaction charges excluding IPFT, plus IPFT exactly once):
- Cash equity: ₹306.99 + ₹0.01 = ₹307.00 per crore.
- Equity futures: ₹182.99 + ₹0.01 = ₹183.00 per crore.
- Equity options: ₹3,552.99 + ₹0.01 = ₹3,553.00 per crore.

Rules:
1. For an explicitly reviewed combined source, preserve and use the combined transaction-charge amount; do not add a separate IPFT amount.
2. For an explicitly reviewed split source, use the transaction-charge amount excluding IPFT and add the separately evidenced IPFT amount once.
3. Never infer combined/split semantics from a field name alone. Preserve the original source label, endpoint/schema/version and raw value.
4. If the representation is missing, conflicting, null where an actual amount is required, or otherwise ambiguous, fail closed; do not silently substitute zero or promote it to actual per-fill accounting.
5. The combined/split validator is a representation safeguard, not proof of authentic source data or approval of a production API mapping.

Primary reference: NSE circular NSE/FA/73061, dated 27 February 2026, effective 1 March 2026: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf

### GST calculation policy

Use 18% GST on the applicable, evidence-backed taxable service-charge base, calculated from canonical components once. The working component policy recorded for Upstox is:
- Delivery: brokerage + transaction charges/IPFT + applicable demat transaction charges.
- Intraday, futures and options: brokerage + transaction charges/IPFT.
- Where transaction charges are represented as a combined amount that already includes IPFT, include that combined amount once; do not add IPFT again to the GST base.
- Where the source is split, combine transaction charges excluding IPFT with the separately evidenced IPFT exactly once.
- Apply pure-agent/exclusion treatment only where the applicable tax rule and invoice evidence support it; do not assume every charge is excluded from GST merely because it is statutory or separately labelled.
- Use the applicable product, segment and effective date, with documented rounding and invoice reconciliation. Do not reuse a taxable-base rule across products/dates without evidence.

Reference for published broker treatment: https://upstox.com/brokerage-charges/

### Decision versus remaining implementation gates

**Settled policy:** the combined-versus-split IPFT arithmetic above; IPFT must never be counted twice; GST is calculated from the applicable taxable canonical components once; unknown representation fails closed.

**Still required before production approval:** corroborate actual Upstox API/contract-note field semantics against authentic source evidence; approve effective-dated product/segment mappings and GST composition against invoices; test combined/split equivalence and no-double-count behavior in per-fill accounting; and pass exact-head CI. The Upstox Get Trade Charges endpoint is aggregate reconciliation evidence, not proof of actual per-fill charges. Do not label these remaining evidence/implementation gates as a reversal of the agreed calculation policy.

Safety remains unchanged: PAPER mode mandatory; live broker order writes disabled; PR #6 remains draft/unmerged pending review and user approval. All work is limited to `tarunsharma2610-del/tradepro-improved`; do not modify the original `tarunsharma2610-del/Tradepro`.

## Phase 3 execution-control documents — 25 October 2026

The detailed, Phase 3-only source of truth is now split into:
- `PHASE3_ROADMAP.md` — ordered remaining gates and exit criteria.
- `PHASE3_INSTRUCTIONS.md` — Phase 3 guardrails, repository/safety checks, evidence rules and verification workflow.
- `PHASE3_PROGRESS_REPORT.md` — gate-by-gate status and commit/CI evidence log.

Use these files before continuing Phase 3; do not recreate the plan from conversation history. Whole-project safeguards remain in force: only `tarunsharma2610-del/tradepro-improved`, never original `tarunsharma2610-del/Tradepro`; PAPER mode mandatory; live broker writes and automatic live-fill promotion/scheduling disabled; PR #6 remains draft/unmerged pending explicit user approval; preserve `BrokerFillIdentity` and `BrokerTradeRecord` separation; do not reopen Phase 2.

Verification boundary: exact-head CI passed on implementation SHA `97843aec1d9b0acc4d55d0fc4529b4ea5b81fd50` in [run #40187635881](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40187635881) (907 passed, 1 warning). The new Phase 3 planning/reporting documents were committed after that SHA. Therefore, this newer documentation HEAD must not be described as CI-verified until its own required workflow succeeds. Keep the Phase 3 report updated only after successful verification; record failed/pending runs honestly.

### Phase 3 next checkpoint — source-label association (2026-10-25)

- Current implementation HEAD at handover note: `fb147a3c5580091574bc71c35e7a641cf7386935`.
- Implemented explicit `labels_by_component` mapping in the representation contract and wired the persisted source-component label mapping into review validation; added adversarial unit tests.
- **Do not call this step complete yet:** exact-head CI is not verified. Next action is to inspect the workflow on the current branch HEAD, confirm the contract/API tests and required PostgreSQL/migration/safety jobs pass, and record the exact run/counts in `PHASE3_PROGRESS_REPORT.md`.
- Source-label association is structural only; authentic contract-note matching still requires independent review.
- Continue using `PHASE3_ROADMAP.md` and `PHASE3_INSTRUCTIONS.md`. Keep PAPER-only posture, live broker writes disabled, original Tradepro untouched and PR #6 draft/unmerged.

- CI follow-up: run [#40188703796](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40188703796) failed on `fb147a3c5580091574bc71c35e7a641cf7386935` because the negative test fixture used strict zip while intentionally supplying fewer labels. Fixed in `e2758ae3db5309641196f0cd0ce035591f6c03ac`; verify CI for the corrected/current HEAD before marking the source-label gate complete.

### Phase 3 next checkpoint — source-label authenticity guard (2026-10-25)

- Explicit component-to-label association passed CI on `d70b1535e7a8b8680b90dadbd926e06b4ae41a16` (run [#40188968279](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40188968279), 910 passed, 1 warning).
- A further gap was then found: missing source labels were replaced with normalized component names. Fixed intake to preserve missing labels as missing and block review; added API regression coverage in commits `460c9bba1a9cb6240ccdf86d39087107fe23589f` and `34e3d3e865660f96b432968565f2b8ceeb9c9184`.
- Current exact-head CI is pending. Verify latest HEAD before marking this gate complete. Then continue with effective-dated component rules and end-to-end per-fill accounting. Structural validation does not authenticate real source content.
- Keep PAPER-only posture, live broker writes disabled, original Tradepro untouched and PR #6 draft/unmerged.

- CI found an ordering regression in the missing-label guard: workflow [#40189211122](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40189211122) failed with 909 passed, 2 failed, 1 warning because the guard masked existing 403/422 authorization/fill validation responses. Corrected by moving label/representation checks after authorization and fill validation in `b92d0185f588e24d54510b36659944e77f498a6e`. Verify exact-head CI before proceeding.

### Phase 3 checkpoint — source-label authenticity guard

- Implementation `b92d0185f588e24d54510b36659944e77f498a6e` passed exact-head CI [#40189481491](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40189481491): 911 passed, 1 warning, 0 failures; broker-write guard, SQLite/PostgreSQL migration round-trips and synthetic restore passed.
- Documentation checkpoint `704d9d5caa8a893195d5213ae38b97c30639de96` passed [CI #40189515861](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40189515861).
- Latest report synchronization commit is newer and requires exact-head CI. Continue next with effective-dated component-rule scope and end-to-end per-fill reconciliation; do not activate draft tariffs or claim authentic Upstox mapping approval.



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

- Added `backend/app/services/broker_charge_canonical_allocation_plan.py` and `backend/tests/test_broker_charge_canonical_allocation_plan.py`. The new planning boundary composes reviewed-source canonicalization with deterministic largest-remainder paise allocation, producing per-fill allocations and source-row provenance without database writes or accounting approval.
- It explicitly supports only `EXPLICIT_REVIEWED` weights pending approved component-specific tariff rules. Contributing rows must share the same canonical sorted fill manifest, manifest hash, explicit weights, basis, and allocation-method version. Split transaction/IPFT rows are combined once into canonical exchange charges before allocation.
- Tightened `canonicalize_verified_component_records` to reject records where extractor and reviewer are the same user; added a regression test.
- Code commits: plan service `a3a51ce8257b2300ead83158c423772f420545f8`; plan tests `1dffc90897e524a3c4065740daf3b31f2aaabf03`; independent-reviewer guard `f17e75ab4cc8eef448dd4743b942a13b0af8d2d0`; guard test `18d69d5fee2a4a2668cdf32a8ad0661aba8adbe3`.
- Backend workflow `40193811936` was in progress at the latest check. Do not mark this code/test head green until CI completes and the newest test commit is covered. This planner is not yet wired into the database persistence/promotion service; persistence integration remains the next gate.
- Safety unchanged: work only in `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion remain disabled; GST/tariff/IPFT interpretations remain unapproved.


## CI follow-up — canonical allocation planner (25 October 2026)

- Backend workflow [#40193836363](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40193836363) passed on independent-reviewer test commit `18d69d5fee2a4a2668cdf32a8ad0661aba8adbe3`. Backend pytest, SQLite migration cycle, PostgreSQL 16 migration cycle, and synthetic PostgreSQL/document-volume restore drill all succeeded.
- A newer docs-only checkpoint commit triggered Backend workflow [#40193954195](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40193954195), which was still in progress at the last check. The code/test head is green; the latest documentation head is not yet confirmed green.
- Next: wait for exact latest-head CI, then connect the planning output to the locked persistence/reconciliation service using source-row provenance and canonical component identity. Do not promote accounting until the full transaction and replay/concurrency tests pass.


## Phase 3 checkpoint — verified canonical allocation persistence boundary (25 October 2026)

- Added `backend/app/services/broker_charge_verified_allocation_persistence_service.py`. It locks reviewed evidence and source rows, requires the approved `live-fill-accounting-component-set-v1` of six independently reviewed direct-mapped components, builds the verified canonical plan, and delegates to the existing idempotent allocation persistence service. It leaves all allocations `PENDING_RECONCILIATION`, never commits, and requires the caller to own the outer transaction.
- Added persistence-boundary regression tests in `backend/tests/test_broker_charge_allocation_persistence_service.py`, including successful direct-component allocation and rejection of an unapproved component-set version.
- Split transaction/IPFT canonical planning is supported, but persistence deliberately rejects it until a durable canonical-component ledger can link multiple raw source rows to one canonical exchange-charge component. This avoids misrepresenting a raw row as the canonical source.
- Implementation commit `d92219dcae765c2b8a305a825ae10c4596315f6a`; tests commit `9a837155260d0f2fef4cd9fd9dee458b2db13f90`. Exact-head Backend workflow [#40194167945](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40194167945) was in progress at the last check; do not mark the new persistence boundary green until it completes.
- Next: inspect exact-head CI; if green, implement the durable canonical-component/source-row association for combined/split transaction/IPFT, then add rollback, replay/conflict and PostgreSQL concurrency coverage around the integrated path.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 remains draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion disabled; tariff/GST/IPFT interpretations unapproved.


## Phase 3 checkpoint — durable canonical source snapshots (25 October 2026)

- Added `BrokerChargeCanonicalComponent` model, migration `202610250023_canonical_charge_components.py`, model registration, and `broker_charge_canonical_component_snapshot_service.py`.
- The materializer locks reviewed evidence and source rows, verifies the stored contract-note bytes against SHA-256/size, requires independent source review and the approved component-set version, canonicalizes all reviewed rows, and creates six versioned canonical snapshots in `PENDING_REVIEW`. Exact raw source row IDs, source fingerprint, mapping/representation version, amounts, fill manifest/weights, and allocation policy are preserved. Identical snapshots replay idempotently; changes to reviewed allocation metadata produce a new revision.
- Added tests for direct six-component snapshots, combined/split transaction/IPFT mapping into one exchange-charge snapshot, idempotent replay, unverified rows, tampered source documents, and revisioning after allocation-metadata changes.
- Latest code/test commit: `af14297ee904b7b021fc149e3ac3adf2cb0743f1`. Exact-head Backend workflow [#40194614746](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40194614746) was in progress at last check; do not call the new snapshot model/migration green until it completes.
- Next: verify migration/test CI, then add a distinct reviewer workflow for canonical snapshots and adapt allocation reconciliation to reference canonical snapshot IDs/source fingerprints rather than assuming one raw source row equals one canonical component.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion disabled; production tariff/GST/IPFT interpretations unapproved.


## Phase 3 CI correction — canonical snapshot test (25 October 2026)

- Backend workflow [#40194614746](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40194614746) reported 1 failure and 951 passes. The failure was test-only: the split transaction/IPFT snapshot test passed string UUIDs to a SQLAlchemy UUID column query. Fixed the test to convert the persisted source-row IDs to `UUID` objects in commit `0a7437b9b413f86832cc029b983751c25007e21a`.
- The prior run's migration/test result is not green overall. Verification of the correction is pending a new Backend CI result; do not report the canonical snapshot work as green yet.
- The migration/model and snapshot materializer remain on the Phase 3 branch only. No live-order or accounting-promotion behavior was enabled.


## CI follow-up — canonical snapshot UUID test correction (25 October 2026)

- Corrected the split transaction/IPFT test to pass UUID objects to SQLAlchemy. Exact code/test commit `0a7437b9b413f86832cc029b983751c25007e21a` passed Backend workflow [#40194933563](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40194933563): pytest, broker-write boundary, SQLite and PostgreSQL 16 migration cycles, and synthetic PostgreSQL/document-volume restore all succeeded.
- Documentation-only head `408af47077c18ecbe22418bad8cae109cf8741ef` triggered Backend workflow [#40195063845](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40195063845), which was in progress at the last check. Do not claim that later documentation head green until it completes.


## Phase 3 checkpoint — independent canonical snapshot review (25 October 2026)

- Added `broker_charge_canonical_component_review_service.py` to review canonical snapshots separately from raw source-row review. It rechecks the stored contract-note bytes, source-row IDs, current canonical mapping/amount, mapping and representation versions, and source fingerprint under locks. Only an active admin distinct from the snapshot creator, source reviewer, and extractors can mark a snapshot `VERIFIED` or `REJECTED`; decisions are immutable and exact replay is idempotent.
- Added tests for split transaction/IPFT review, independent reviewer enforcement, idempotent review replay, and rejection when a source locator changes after snapshot creation.
- New code/test commit `9bb7ebaeeaee62753ba7580cf1dc94400df5aea4`; Backend workflow [#40195392377](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40195392377) was queued at the latest check. Do not mark the new reviewer workflow green until CI completes.
- Next: verify this CI result, then extend allocation persistence/reconciliation to bind allocations to the verified canonical snapshot ID and its source fingerprint, including combined/split transaction/IPFT.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion disabled.


## Phase 3 checkpoint — allocations linked to verified canonical snapshots (25 October 2026)

- Added nullable `BrokerChargeAllocation.canonical_component_id` plus migration `202610250024_link_allocations_to_canonical_components.py`. Historical rows remain NULL; no inferred backfill.
- Added `broker_charge_canonical_allocation_persistence_service.py`. It requires a `VERIFIED` canonical snapshot, re-runs independent snapshot integrity/reviewer validation, delegates to the evidence-locked idempotent allocation writer, and persists the canonical snapshot foreign key on every allocation. It never commits or marks allocations reconciled. Split transaction/IPFT can now be planned, snapshotted, independently reviewed, and persisted against one canonical exchange-charge identity.
- Added integration coverage for split transaction/IPFT snapshot review and allocation persistence, exact ₹307.00 reconciliation, snapshot foreign-key linkage, pending-only status, and idempotent replay. Prior canonical snapshot CI failure was test-only (string IDs used in a UUID query) and fixed; corrected code/test commit `0a7437b9b413f86832cc029b983751c25007e21a` passed workflow [#40194933563](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40194933563). Independent snapshot review passed workflow [#40195392377](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40195392377).
- Latest canonical-allocation persistence test commit `be761f4064136662ea1e5c18fef0c2b40237a387`; Backend workflow [#40195695138](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40195695138) was in progress at last check. Do not call the new migration/persistence path green until it completes.
- Next: verify exact-head CI; then implement canonical-snapshot allocation verification and promotion so live-fill accounting validates canonical snapshot IDs and fingerprints instead of assuming one raw source row per canonical component.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion disabled.


## Phase 3 CI correction — canonical allocation foreign-key migration (25 October 2026)

- Workflow [#40195695138](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40195695138) found a migration portability failure: SQLite cannot ALTER-add the foreign-key constraint directly. The migration was corrected to use Alembic batch mode, and the model's FK name was aligned with the migration.
- Fix commits: migration `c4ee0e6910aa7b07bdd4bb7e4db1ca67ab27b110`; model `b7df1496ecf8d9c6553d85a68d2661d3b0ad99f0`. Exact-head Backend workflow [#40195975929](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40195975929) was in progress at last check; the FK migration is not yet declared green.


## Phase 3 — normalized source-to-canonical charge links (25 October 2026)

- Forward progress beyond the JSON manifest: added `BrokerChargeCanonicalSourceLink` and migration `202610250025_normalize_canonical_source_links.py`. The database now has one foreign-key row per canonical-snapshot/source-row relationship, with unique pair and ordered-source constraints. Migration backfills only from each snapshot's already-persisted ordered source-ID manifest; it does not infer mappings from labels or amounts.
- Snapshot creation now persists normalized source links and checks them on idempotent replay. Independent snapshot review requires the normalized link rows, their exact order, and the immutable manifest to agree. Missing or altered membership fails closed. Split transaction + IPFT therefore has explicit two-source-row-to-one-canonical-charge linkage in relational rows; allocations remain linked to that canonical snapshot.
- Previous branch head `4dbaf27fae124d11935c271f2f4cdec44015dbaa` passed Backend workflow [#40196030459](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40196030459), including the migration correction. New source-link model/migration/service/test commit `d1153a0f0751339f3ca82fc062701db0141d4749` requires fresh CI verification; do not call this latest normalized-link change green until its run finishes.
- Next gate: verify SQLite/PostgreSQL migration upgrade, downgrade/re-upgrade and tests on the normalized relationship; then extend promotion/reconciliation to require this relational source membership and verified canonical snapshot fingerprint.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 remains draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion disabled.


## Phase 3 — normalized source links and canonical reconciliation gate (25 October 2026)

- CI confirmed the normalized source-link migration on commit `d1153a0f0751339f3ca82fc062701db0141d4749`: Backend workflow [#40196529023](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40196529023) passed pytest, broker-write boundary, SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade, and synthetic restore drill.
- Added `broker_charge_canonical_allocation_reconciliation_service.py` to verify a per-fill ledger against the independently verified canonical snapshot, exact source fingerprint and normalized source links, fill manifest, deterministic paise allocation, INR/method/basis, row state and total. Promotion is atomic and idempotent; the durable reference includes snapshot ID, source fingerprint, fill-set hash and method version. It never commits the caller's transaction.
- Added tests for split transaction/IPFT -> one ₹307.00 canonical exchange-charge snapshot -> two linked per-fill allocations, normalized source-link enforcement, reconciliation promotion/replay, and blocking tampered allocation amounts. Test commit `621ce7cd289057a419be5eeff0262e158b18c001` has Backend workflow [#40196784435](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40196784435) in progress; do not call the new reconciliation path green until that run completes.
- Next: resolve any failures from run #40196784435; then test conflict/rollback and PostgreSQL concurrency for canonical promotion before treating it as a complete Phase 3 accounting gate.
- Safety unchanged: Improved repo only; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion remain disabled outside this gated reconciliation service.


## CI result update — canonical reconciliation gate (25 October 2026)

- Backend workflow [#40196784435](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40196784435) has now completed successfully for code/test commit `621ce7cd289057a419be5eeff0262e158b18c001`. The complete job passed pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade, and the synthetic PostgreSQL/document-volume restore drill.
- This green result covers the normalized source-link schema and canonical allocation reconciliation tests. Documentation-only commits after that code/test commit still need their own exact-head workflow result if triggered.
- Next: add explicit rollback/conflicting-set and PostgreSQL concurrent-promotion coverage; then verify exact-head CI again before considering the canonical reconciliation gate complete.

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
- Implementation commit: `07df26a88d5eb9cbebc76a5654e10e00e38de171`.
- Backend CI run #40204137793 completed successfully on that exact commit: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40204137793
- Root cause resolved in code: complete durable reconciliation references exceeded the prior 200-character database column. The model and migration `202610250026_widen_charge_reconciliation_reference.py` now allow 320 characters; downgrade explicitly refuses to truncate references longer than 200 characters.
- PostgreSQL concurrent-promotion test has passed as part of the successful Backend CI run. Treat the test as verified on the implementation commit; the documentation checkpoint itself still requires exact-head CI.
- Next: after documentation checkpoint CI is green, audit whether any conflicting-set/rollback/concurrency acceptance gap remains, add tests only for verified gaps, then rerun the full backend gate.
- Mandatory protocol: every CI failure → inspect full failure, fix root cause and rerun; every CI pass → update all 18 maintained checkpoint documents, commit a checkpoint with exact SHA/run/results/next step, then verify CI on that checkpoint commit itself.
- Safety: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched. PR #6 stays draft/unmerged. PAPER mode mandatory; live broker order writes disabled. GST/IPFT tariff acceptance remains a separate production-evidence gate; synthetic engineering work is not blocked.


## Authoritative checkpoint — 26 October 2026 (documentation CI verified)

- Repository: `tarunsharma2610-del/tradepro-improved`; branch: `phase3/durable-per-fill-charge-allocation`.
- Latest implementation commit: `ac7d27f2c9922925483b5b906c484c0d5a4e3f53`; exact-head Backend CI [#40287765745 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40287765745).
- Documentation synchronization commit: `f90573d653c7103bf9cfdb1f867da97b176d3240`; its exact-head Backend CI [#40289107666 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40289107666). Backend tests, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore/evidence retention passed. Synthetic restore is not proof of actual Oracle Cloud recovery.
- The approved public Upstox STT/exchange rules are estimate-only. Account-specific actual charges, GST taxable-base composition, stamp duty, SEBI/DP/demat/other charges, unsupported exchange/segment mappings, and per-fill actual evidence remain unapproved. Candidate tariff entries remain DRAFT unless separately allowlisted and reviewed.
- Phase 3 remains in progress. Next gates: independently reviewed tariff applicability; component-specific per-fill allocation rules; invoice/source-backed GST/IPFT and product/segment evidence; final adversarial, migration and recovery review; exact-head acceptance sign-off. Do not repeat canonical live-fill integration.
- Safety: PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. PR #6 stays open/draft/unmerged without explicit user approval. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.
- This documentation commit’s CI is green. Continue only from this checkpoint and verify CI for every subsequent implementation/checkpoint commit. Historical entries below or above this section do not supersede this checkpoint.


## GST/IPFT checkpoint — 26 October 2026

- Added regression test `test_gst_arithmetic_is_invariant_for_combined_vs_split_ipft_representation`: equivalent synthetic combined/split components yield ₹307.00 base and ₹55.26 GST at 18%. Arithmetic coverage only; not approval of taxable-base mapping.
- Exact test commit `8b4ae0b431d6aa03f1a8ae347a0b5fa7bda44c4f` passed exact-head Backend CI [run 40296066304](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40296066304). This does not prove tax compliance or account-specific reconciliation.
- NSE circular `NSE/FA/73061` (27 Feb 2026, effective 1 Mar 2026) states combined member outflows ₹307/crore cash, ₹183/crore equity futures and ₹3,553/crore equity-options premium, including ₹0.01/crore IPFT. [NSE source](https://nsearchives.nseindia.com/content/circulars/FA73061.pdf).
- Upstox's public schedule describes 18% GST on specified brokerage, transaction, IPFT and (equity delivery) demat charges and says IPFT is combined with transaction charges. [Upstox schedule](https://upstox.com/brokerage-charges/). CBIC says STT/stamp-duty recoveries are excluded only if Rule 33 pure-agent conditions are met; otherwise valuation under Section 15/rules applies. [CBIC FAQ](https://cbic-gst.gov.in/sectoral-faq.html), [Rule 33](https://cbic-gst.gov.in/valuation-rules.html).
- Actual GST accounting remains blocked pending product/segment-specific mapping review and reliable invoice/contract-note reconciliation. Never tax trade notional or all charges indiscriminately, nor add separate IPFT on top of a combined exchange rate. Candidate tariffs remain DRAFT.
- Next gate: test product-specific GST mapping, including equity delivery vs intraday/F&O and STT/stamp duty treatment based on pure-agent evidence; then exact-head CI and document sync. PAPER mandatory, live order writes disabled, PR #6 draft/unmerged, original `Tradepro` untouched.


## GST/API evidence checkpoint — 26 October 2026

- Implementation/test head `149d21fdbb82306ff1b800ff7d3ad33b99058d81`; exact-head Backend CI [#40296745348 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40296745348). Passing CI does not constitute legal approval of GST treatment.
- Source-backed Upstox GST component candidates now cover NSE/BSE equity delivery, equity intraday, equity futures and equity options. All remain `DRAFT`. Delivery includes `demat_charges`; the other categories do not. `exchange_charges` is the canonical combined transaction/IPFT component, so IPFT must not be counted twice. Trade notional is never a GST component.
- Official Upstox `GET /v2/charges/brokerage` calculates a quote for supplied instrument, quantity, product, side and price; response fields include GST, STT, stamp duty, transaction, clearing, IPFT and SEBI turnover. It is an estimate, not proof of actual executed-fill charges: https://upstox.com/developer/api-documentation/get-brokerage/.
- Official Upstox `GET /v2/trade/profit-loss/charges` returns a segment/financial-year date-range breakdown; `ipft` can be null. Treat it as aggregate reconciliation evidence, not per-fill attribution: https://upstox.com/developer/api-documentation/get-trade-charges/. Actual-charge approval still needs contract-note/tax-invoice and account-record reconciliation.
- Upstox's public schedule specifies 18% GST on brokerage + transaction charges + IPFT, with demat additionally for equity delivery, and says IPFT is combined with transaction charges: https://upstox.com/brokerage-charges/. NSE circular `NSE/FA/73061` supports revised combined NSE transaction/IPFT rates effective 1 March 2026: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf.
- CBIC permits exclusion of statutory recoveries such as STT/stamp duty only when pure-agent conditions are met; otherwise apply Section 15 and applicable valuation rules: https://cbic-gst.gov.in/sectoral-faq.html and https://cbic-gst.gov.in/valuation-rules.html. Do not hard-code universal exclusion without evidence.
- No GST candidate is promoted. Missing/null API fields remain unknown, not zero. Any later API ingestion must preserve raw response/hash, retrieval time, query segment/date range, schema version and invoice linkage. Do not use the brokerage calculator as actual-charge evidence or infer per-fill values from aggregate responses.
- Next gate: source-backed GST acceptance/reconciliation using actual invoice/contract-note evidence and per-product component sets, then exact-head CI and documentation verification. PAPER mandatory; live broker order writes disabled; PR #6 remains draft/unmerged; original `Tradepro` untouched.


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

## Latest checkpoint update — 26 October 2026 (tariff-source reconciliation)

- Current branch target remains `phase3/durable-per-fill-charge-allocation` in `tarunsharma2610-del/tradepro-improved` only. Do not modify original `tarunsharma2610-del/Tradepro`.
- Previous documentation checkpoint: `bc2188b720354bea8791a8e6df7bd7165ebe42cb`; exact-head Backend CI run [#40330911741](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40330911741) was started and must be checked for completion. Any newer docs commit requires its own exact-head CI pass.
- New evidence: current Upstox public tariff explicitly states GST base = brokerage + transaction + IPFT, plus demat/DP for equity delivery; it also states IPFT is combined with transaction charges from 1 March 2026. For estimates, represent that combined charge once; do not double-add IPFT. Source: https://upstox.com/brokerage-charges/ .
- Remaining conflict: Upstox Brokerage Details API's published example GST ₹1.02 matches 18% of transaction ₹5.68 alone, despite IPFT ₹0.17 shown separately; a third-party calculator uses another presentation for DP GST. These are documentation/calculator discrepancies, not proof of live API or invoice behaviour. Current ordinary-trade invoice or written broker clarification is still required before actual per-fill promotion.
- All four product GST component candidates remain `DRAFT`. No actual GST logic promoted by this documentation update. Aggregate charges and estimate APIs are not per-fill tax evidence.
- Next gate: confirm exact-head CI; obtain/inspect current Upstox ordinary-trade contract notes/tax invoices or written clarification for delivery, intraday, futures and options; then update product rules/tests only when evidence resolves the discrepancy.
- Safety unchanged: PAPER mode mandatory; live broker order writes and automatic live-fill promotion/scheduling disabled; PR #6 remains draft/unmerged unless user explicitly approves. Defer AI integrations including Algory.app until Phase 3 acceptance.


## Latest exact-head CI checkpoint — 26 October 2026

- Latest source/documentation head verified: `0ff70ee399a1b8fd3d7d3998dcc1c93cd89da7a3` on `phase3/durable-per-fill-charge-allocation`; exact-head Backend pytest workflow [#40331381116](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40331381116) completed successfully.
- All observed job steps passed: dependency install, full test suite, broker write boundary, SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade, isolated synthetic PostgreSQL/document-volume restore drill, and evidence retention.
- This CI result verifies the existing code/tests at `0ff70ee399a1b8fd3d7d3998dcc1c93cd89da7a3`; it does not certify a new docs-only commit until CI runs against that exact new head. Keep this note historical after the follow-up docs commit; check that commit's CI before calling the documentation checkpoint green.
- GST/IPFT decision unchanged: public-schedule estimate may count combined transaction/IPFT once; no legacy IPFT double-counting; actual per-fill GST component candidates remain `DRAFT` pending source/invoice or written broker clarification. Never request personal contract notes from the user; continue using public sources and clearly label unresolved points.
- Safety and scope unchanged: target `tarunsharma2610-del/tradepro-improved` only; original `Tradepro` untouched; PAPER mandatory; live broker order writes and automatic live-fill promotion/scheduling disabled; PR #6 remains draft/unmerged; AI/Algory work deferred until Phase 3 acceptance.


## GST/IPFT public evidence update — 26 October 2026

- See `GST_IPFT_PUBLIC_EVIDENCE_ADDENDUM.md` for the public-source findings, links and explicit decision gate.
- Current Upstox tariff wording supports estimates that count the combined transaction/IPFT amount once from 1 March 2026; do not double-count IPFT.
- The published Brokerage Details API sample (GST ₹1.02 vs transaction ₹5.68 and IPFT ₹0.17) remains inconsistent with that tariff wording. Public Upstox contract notes found for 21 May 2024 and 12 March 2025 are historical and do not resolve the post-March-2026 discrepancy.
- No actual GST component candidate promoted; delivery, intraday, futures and options remain DRAFT pending current public invoice evidence or written broker clarification. User's own contract note is not required.
- Branch: `phase3/durable-per-fill-charge-allocation`; repository: `tarunsharma2610-del/tradepro-improved` only. PAPER mandatory; live order writes and automatic live-fill promotion/scheduling disabled; PR #6 remains draft/unmerged. AI/Algory remains deferred until Phase 3 acceptance.


## GST/IPFT reconciliation checkpoint — 26 October 2026

- Current official Upstox schedule https://upstox.com/brokerage-charges/ lists GST at 18% of brokerage + transaction charges + IPFT, with demat/DP included for equity delivery. From 1-Mar-2026, Upstox publishes combined NSE transaction/IPFT totals: cash ₹307/crore, equity futures ₹183/crore, equity options ₹3,553/crore on premium. Do not add IPFT a second time. NSE source: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf (NSE/FA/73061, 27-Feb-2026).
- Unresolved discrepancy: Upstox Brokerage Details API example https://upstox.com/developer/api-documentation/get-brokerage/ shows transaction ₹5.68, IPFT ₹0.17, GST ₹1.02. ₹1.02 equals 18% of ₹5.68 rounded, not 18% of ₹5.85 (about ₹1.05). This is a documented-example conflict, not proof of a live production defect.
- Upstox Trades Charges API https://upstox.com/developer/api-documentation/get-trade-charges/ returns segment/date-range aggregate charges and may return IPFT null. Null means unknown, not zero; aggregate output is not per-fill proof.
- Public Upstox contract-note copies dated 11-Feb-2025, 21-May-2024 and 12-Mar-2025 are historical, third-party, unauthenticated and show differing printed bases. Use for schema/layout only, not current per-fill accounting.
- Estimate rules can follow the current tariff with effective-date/exchange/product handling and one combined transaction/IPFT amount. Actual per-fill GST promotion stays blocked pending current public invoice evidence or written Upstox clarification. Delivery, intraday, futures and options candidates remain DRAFT.
- Exact-head CI passed on previous head 996b126ff678b97441f0214ea817451ee1592203: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40341429226. Test suite, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips and synthetic restore/evidence retention all passed. New documentation commit requires its own exact-head CI.
- Scope/safety: only tarunsharma2610-del/tradepro-improved, branch phase3/durable-per-fill-charge-allocation; original Tradepro untouched. PAPER mandatory; live order writes and automatic live-fill promotion/scheduling disabled; PR #6 draft/unmerged. Do not ask user for a personal contract note. Defer AI/Algory until Phase 3 acceptance.


## GST estimate implementation update — 26 October 2026

- Added backend/app/services/upstox_public_gst_estimate.py and backend/tests/test_upstox_public_gst_estimate.py. This is a separate public-schedule estimate path, not actual-charge evidence. It requires an explicit component map and 18% GST, supports only reviewed exchange/product scopes from 1-Mar-2026, and returns source_kind PUBLIC_SCHEDULE_ESTIMATE_ONLY.
- Delivery estimate requires brokerage + exchange_charges + explicit demat_charges (zero only when known not applicable); other supported products require brokerage + exchange_charges. For NSE from 1-Mar-2026, exchange_charges is the combined transaction/IPFT amount and must be counted once; a separate ipft key is rejected. For BSE options use the applicable BSE exchange charge source and do not assume an NSE IPFT component.
- The Upstox API example still reports transaction ₹5.68 + IPFT ₹0.17 but GST ₹1.02, while 18% of ₹5.85 is about ₹1.05. The estimate helper follows the explicit published schedule and does not resolve this actual-billing/API-documentation conflict. Four actual GST candidates remain DRAFT.
- GST/IPFT acceptance scenarios are in GST_IPFT_ACCEPTANCE_MATRIX.md. Code/test head: 221493eb17729533cfaf855e2ce52532ef0903ac; exact-head CI run #40342805295 was pending when this note was authored. The documentation sync commit must also receive exact-head CI.
- Safety/scope unchanged: only tarunsharma2610-del/tradepro-improved; original Tradepro untouched; PAPER mandatory; live order writes and automatic live-fill promotion/scheduling disabled; PR #6 draft/unmerged; no personal contract note requested; AI/Algory deferred until Phase 3 acceptance.


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


## Resume point — cross-broker GST/IPFT work (26 October 2026)

Continue on branch `phase3/cross-broker-gst-ipft-resolution`, Draft PR #7: https://github.com/tarunsharma2610-del/tradepro-improved/pull/7. This is the active continuation; do not restart from an older checkpoint or work in the original Tradepro repo.

Research file: `docs/CROSS_BROKER_GST_IPFT_POLICY_RESEARCH_2026-10-26.md`. New policy primitive: `backend/app/services/broker_gst_component_policy.py`; tests: `backend/tests/test_broker_gst_component_policy.py`. The policy requires explicit broker/exchange/segment/product/effective date, source provenance, approved status and exact component set. IPFT modes distinguish combined transaction/IPFT from separate rows and reject duplicate representations.

Next steps in order:
1. Check workflow runs/checks for current PR head and fix any failures.
2. Integrate the generic policy into the existing Upstox public estimate helper without changing its estimate-only status; add cross-broker tests based on each broker's published component policy.
3. Implement/verify canonical DP/demat component persistence, total-charge reconciliation and migration tests, or keep delivery actual accounting explicitly blocked.
4. Update maintained docs/checkpoint to the exact final head and passing CI only.
5. Keep PR #6 Draft/unmerged, PAPER mandatory, live broker writes disabled, and original Tradepro untouched. No personal contract note is required for implementation of public rules; actual invoice acceptance remains evidence-gated.


## GST/IPFT latest continuation — 26 October 2026

The previous CI run #40358027077 failed on one test assertion message mismatch (1,023 passed, 1 failed). The test assertion has been corrected. The Upstox public GST estimate now calls the shared `GstComponentPolicy` calculator; NSE uses COMBINED IPFT representation, while BSE options uses NOT_APPLICABLE so it does not inherit NSE IPFT.

Implementation head before the next documentation sync: `393804cc5c21ba70a579b32a6736f6561569413b`. Check exact-head CI after documentation commits; no passing status has been confirmed for this head yet.

Continue with cross-broker published policy tests and canonical DP/demat persistence/migration. Keep broker candidates DRAFT, PR #6 Draft/unmerged, PAPER only, live writes disabled, and original Tradepro untouched. No personal contract note needed for public-rule implementation.


## Current GST/IPFT handover — 2026-10-26

The user supplied AI-generated sample contract-note structures for Zerodha, Groww, Angel One, Upstox retail, MCX, NSE-CD and an institutional clearer. Use them as candidate test shapes only, not as authoritative tariff/tax rules. The supplied Upstox assertions that SEBI must be included in the GST base and that DP is ₹18.50 base conflict with Upstox's currently published pricing page, which states GST on brokerage + transaction + IPFT and adds demat for equity delivery, and lists DP at ₹20 per scrip/day on delivery sells. Keep this mismatch explicitly documented.

New code: `backend/app/services/upstox_contract_note_text_extractor.py` plus `backend/tests/test_upstox_contract_note_text_extractor.py`. The extractor retains raw line text/line number and amount, flags duplicate component labels, identifies segment tags, and surfaces unmapped charge-like lines. It does not determine taxable base or approve accounting. `upstox_public_gst_estimate.py` no longer marks an internal policy APPROVED to calculate an estimate.

Next: confirm exact-head CI; then update the authoritative checkpoint to the successful exact commit/run. Continue the canonical DP/demat persistence + migration audit. Keep tariff candidates DRAFT, don't require personal contract notes, don't enable live writes, and don't merge PR #6 or #7.

## DP/demat mapping status — 26 October 2026

Source canonicalization now accepts an explicitly reviewed `demat_transaction_charges` row as a separate optional canonical component; it is never invented as zero when absent. Per-fill allocation planning also supports the separate component with a regression test, while preserving `accounting_approved=False` and `persisted=False`.

This does not yet make DP/demat persistable on an Execution. Next work must inspect the Alembic migration chain, add a nullable/backward-compatible field and migration, update total-charge recomputation and any serializer/repository/promotion code, and add idempotency plus delivery/non-delivery regression tests. Do not accept actual delivery accounting before those checks and exact-head CI pass.

## DP/demat CI failure and correction — 26 October 2026

Backend run #40362669264 failed (45 failed, 989 passed) because the first mapping change widened the source-component mapping consumed by the existing six-component live snapshot service. The correction keeps the approved six-component mapping contract intact and exposes optional DP/demat rows in a separate mapping. Allocation planning reads the optional mapping, while the live snapshot service fails closed if DP/demat is present because the Execution schema still cannot persist it. Verify CI on the latest PR head before checkpointing it as green.


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

- Exact-head Backend CI #40459846143 succeeded on code/test commit `9400bc9aa221e2cf3b735e49a8e9a6d351237f02`; see https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40459846143. Backend tests, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore checks passed. This does not establish production Oracle restore acceptance.
- Added API regression: invalid DP status through `ExecutionOut` cannot be represented as a complete charge total. DP status/amount consistency and delivery-SELL manifest eligibility remain fail-closed.
- Next gate: per-fill source-to-canonical mapping, identical/conflicting replay, rollback atomicity, and component applicability; then exact-head CI and synchronized checkpoint. Real contract-note and production Oracle backup/restore acceptance remain deferred until genuine evidence exists.
- Safety: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.

## Latest verified checkpoint — 27 October 2026 (per-fill allocation tamper rejection)

- Code/test commit `45b0fdc1622881fa0ed361bae6c28af64b59a5f1` passed exact-head Backend CI [#40460914796](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40460914796) (completed, success).
- Added `test_tampered_per_fill_allocation_amount_blocks_live_accounting`: changing a reviewed brokerage allocation by ₹0.01 must be rejected before execution/live-position promotion; paper-position quantity remains unchanged.
- Verifier audit confirms the allocation fill-set must match the reviewed manifest; allocation status, connection, currency, basis, method, source total and deterministic paise amount are validated. Existing tests cover missing component allocations, non-reconciled rows, exact replay, conflicting fill/evidence replay, and post-commit retry safety.
- Next gate: explicit fill-set mismatch and atomic rollback assertions as needed, then component applicability. Keep statutory/effective-dated GST/IPFT tariff acceptance distinct from estimates.
- Production contract-note reconciliation and real Oracle backup/restore remain deferred until genuine evidence exists. No personal contract note is required for current synthetic tests.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker writes disabled.

## Verified checkpoint — 27 October 2026 (source review and reconciliation gates)

- Exact-head CI passed for `c37edb0e5e7c8e98f5845a9cdf8df542ceb9242f`: [Backend CI #40461506443](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40461506443) — completed successfully.
- Source/reviewer audit: canonical component review locks snapshot and evidence, requires reviewed contract-note evidence and intact source document, validates unique canonical-order source manifest, source-row/link consistency, independent source-row verification, canonical mapping/version/amount, fingerprint freshness, and allocation metadata. Reviewer must be an active platform administrator distinct from snapshot creator, original evidence reviewer, and source extractors.
- Existing tests cover exact eligible-fill-set mismatch, source total mismatch, per-fill amount vs reviewed weights, tampered document, atomic/idempotent promotion, unauthorized reviewer, outer-transaction rollback, role recheck at promotion, flush-failure rollback, and variance identity/scope controls. Source canonicalization tests cover combined/split transaction+IPFT mapping, double-map rejection, optional DP treatment, missing/duplicate labels, and non-paise amounts.
- No duplicate tests added because these behaviors already have direct regression coverage. Next gap-focused gate: audit statutory/effective-dated tariff rule inputs and their evidence/provenance, including keeping estimate vs actual tax calculation separate; automatic allocation remains fail-closed until tariff rules exist.
- Actual contract-note reconciliation and production Oracle restore remain deferred until genuine source/backup evidence exists. Synthetic tests do not claim production acceptance.
- Safety: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.

## Verified checkpoint — 27 October 2026 (GST invoice-line normalization)

- Helper commit `57730a21da77fa583fe19c12740bd03eb779fed6` passed Backend CI [#40462246316](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40462246316).
- Regression-test commit `4290b46e55275e4a005b3661da327adc1b216028` passed Backend CI [#40462263615](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40462263615). Tests cover valid IGST, valid CGST+SGST, equivalent totals, mixed-mode rejection, incomplete pairs, missing tax lines, negative/non-finite and sub-paise amounts.
- `aggregate_gst_invoice_components()` normalizes invoice tax lines only. It does not determine jurisdiction, taxable base, statutory rate, Section 15/Rule 33 treatment, or actual invoice authenticity; those remain governed by source evidence and reviewed policy.
- Next: review statutory GST basis and effective-dated source registry/provenance, then IPFT inclusion/mapping by exchange/segment/date and instrument-side applicability. Estimates remain distinct from actual source-backed reconciliation; fail closed where approved rules/evidence are missing.
- Real contract-note acceptance and production Oracle backup/restore remain deferred until genuine evidence exists. No personal contract note required for synthetic regression work.
- Safety: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.


## Phase 3 resume update — 27 October 2026 (GST/IPFT source-policy gate)

- Confirmed documentation checkpoint `14027b5bc4293d2cc1ce5990a4ee23f60077fad5` passed Backend CI [#40462683805 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40462683805), including backend tests, broker-write guard, SQLite/PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore and evidence retention.
- Cross-broker public-source comparison added to `GST_IPFT_ACCEPTANCE_MATRIX.md` and `GST_IPFT_PUBLIC_EVIDENCE_ADDENDUM.md`: CBIC Rule 33 is conditional; Zerodha and Dhan list SEBI in the published GST base; Dhan includes IPFT/other tax; FYERS public pages conflict on SEBI/IPFT GST-base membership; Upstox has a separate published-schedule/API-example discrepancy; Angel One's table does not fully specify base membership. Therefore there is no evidenced universal hard-coded GST component set.
- Next: implement/verify a reviewed, effective-dated policy resolver keyed by broker + exchange + segment/product + source version, with explicit included/excluded component IDs, provenance/reviewer and conflict state. Keep combined/separate transaction/IPFT identity exactly-once; Rule 33 exclusion requires complete evidence; conflicting source or missing jurisdiction facts must remain unresolved. Add focused tests only for gaps not already covered.
- No actual GST candidate is approved by this research. Keep estimate output distinct from actual invoice reconciliation and fail closed where policy/evidence is unresolved. No personal contract note is required; real invoice and production Oracle restore acceptance remain deferred until genuine evidence exists.
- Safety: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled. Exact-head CI must be checked after the latest documentation commits.


## GST policy resolver hardening — 27 October 2026

- Audited existing `backend/app/services/broker_gst_component_policy.py` before changing it. It already provides effective-dated broker/exchange/segment/product selection, source URL/retrieval date/SHA-256 provenance, explicit combined/separate/not-applicable IPFT representation, exact component-set checking and an estimate-only calculation path. Avoid creating a parallel resolver.
- New code commit `eef5eebc1e1abfc37c92b4e50d5c35e9afddcbb4`: policy state `CONFLICT` now exists and any effective conflict for the exact scope/date blocks selection even if an approved policy also matches. This prevents silently preferring one of contradictory public sources.
- New test commit `761637aab1d5f36ed5bfc02ffb66ce8b31ab7820`: regression tests for a conflicting source blocking an approved candidate and for rejecting sub-paise component inputs rather than silently rounding them.
- The policy remains estimate-only. This does not approve any broker component set, does not integrate the statutory Rule 33 engine into actual accounting, and does not reconcile invoice-level GST. No broker policies are promoted to APPROVED by this change.
- Validation status: exact-head CI for these commits is not yet verified. Do not mark this increment green until the branch/PR workflow runs on the exact resulting head and all jobs pass. Next: inspect any CI result, fix failures, then synchronize maintained documents/checkpoint to the latest green head.


## Verified GST resolver hardening CI — 27 October 2026

- Service hardening commit `eef5eebc1e1abfc37c92b4e50d5c35e9afddcbb4` passed Backend CI [#40463452758](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463452758).
- Regression-test commit `761637aab1d5f36ed5bfc02ffb66ce8b31ab7820` passed Backend CI [#40463464076](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463464076). New coverage confirms an effective `CONFLICT` policy blocks selection despite an approved candidate, and sub-paise input is rejected.
- Documentation head `d604be9982dc9c37d3a4985abd89c85635b59106` passed Backend CI [#40463512765](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463512765). A newer checkpoint-only commit is pending its own exact-head CI; do not mark the latest branch head green until that run passes.
- The resolver is still estimate-only. No GST candidate or broker tariff has been promoted to approved actual accounting. PR #6/#7 remain Draft/unmerged, PAPER mandatory, live broker order writes disabled, original Tradepro repository out of scope.


## Confirmed statutory GST precision CI and resume point — 27 October 2026

- The initial code-only run for `58c841cb00f7f0137aece7bcd7c83d5a63ae81f9` failed because an older test still expected silent rounding of `0.025`. This was a test expectation conflict with the new fail-closed behavior, not an unresolved runtime regression in the final increment.
- Regression-test commit `c6e9dfb3e4cae6f93fd51a7f1f1facc86e7b804d` passed Backend CI [#40463868838 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463868838). It replaces the obsolete sub-paise rounding expectation with explicit rejection and a valid paise-precision test.
- Checkpoint commit `74015a285cb844a3735052d88cce9c2a2385e1ce` passed Backend CI [#40463883785 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463883785). This verifies the resulting head including the GST precision change, updated regression test and checkpoint document.
- Intermediate failed run: [#40463856382](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463856382); it was superseded by the successful regression and checkpoint runs above. Do not erase the failure from history; document the correction.
- Current implementation boundaries: statutory GST primitive applies Section 15 default inclusion and conditional Rule 33 pure-agent exclusion only when all modeled evidence flags are true; broker GST policy resolver remains an estimate-only source-specific path. Neither is yet a unified actual per-fill invoice acceptance path. No broker GST policy is approved here for actual accounting.
- Next Phase 3 task: audit the accounting charge reconciliation/promotion boundary and define a single reviewed path that consumes source-backed invoice line identities, statutory valuation evidence and effective-dated broker policy without letting estimates become actual ledger charges. If source provenance, Rule 33 facts, component identity, or GST invoice lines are missing/conflicting, actual accounting must fail closed. Add tests before integration; do not promote estimates or change live-trading safeguards.
- Safety unchanged: work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` is out of scope; PR #6/#7 Draft/unmerged; PAPER mode mandatory; live broker order writes disabled.


## 27 October 2026 — actual statement GST variance work

User supplied actual contract-note images. Do not ask for another personal note or revert to saying no real statement exists. Added `backend/app/services/gst_source_reconciliation.py` plus tests: preserves source GST, computes expected GST only on explicitly reviewed taxable base, returns variance. Statement fixture: brokerage ₹1,000.00 -> GST ₹180.00 match; visible transaction ₹111.61 + SEBI ₹0.22 = ₹111.83; 18% gives ₹20.13 while source GST-on-charges is ₹20.15, so +₹0.02 variance is review-required. IPFT is not separately labelled in the image and must remain unknown rather than guessed.

Public cross-check in `GST_IPFT_ACCEPTANCE_MATRIX.md` and `GST_IPFT_PUBLIC_EVIDENCE_ADDENDUM.md`: CBIC Section 15/Rule 33, NSE circular effective 1-Mar-2026 combined transaction/IPFT rates (count once), separate BSE/MCX tariffs, Upstox/Zerodha/Groww public descriptions. Public evidence does not explain the user's ₹0.02 discrepancy or establish universal invoice treatment. Estimates and actual-source tax lines remain separate; no automatic per-fill promotion without reviewed source-to-fill mapping.

Backend CI #40470168336 passed on source/test/docs head `f053393a10a21463d8ef299c3a18e4d3abeef9d2`; latest checkpoint documentation commit is `ba9bb1dc6decf00b4b684da95d40cd41e9bd6f65`, whose exact-head CI must be checked before claiming the final docs checkpoint is green. Continue from this state, not from the older GST research step. Safety unchanged: only tradepro-improved, PR #6/#7 draft/unmerged, PAPER mandatory, live broker writes disabled.


## Handover update — 27 October 2026: next task is API integration

Resume on `phase3/cross-broker-gst-ipft-resolution` in `tarunsharma2610-del/tradepro-improved` only. The user has repeated that Upstox charge API integration was agreed yesterday and expects implementation, not more cycles of GST/IPFT research. Source inspection confirmed the read-only client already has `get_brokerage_estimate` for `/v2/charges/brokerage` (estimate only) and `get_trade_charges` for `/v2/trade/profit-loss/charges` (aggregate only). The next code change must trace call sites and connect these to a typed, provenance-preserving reconciliation/orchestration layer; the integration is not yet verified complete. Never treat aggregate values as per-fill actuals or split them into fills as if reported by the broker. Use exact approved mappings; preserve null as unknown; prevent combined transaction/IPFT double count; retain the historical ₹20.15 GST source value and ₹0.02 visible-base variance without inventing a cause. Add tests, run exact-head CI, then update all maintained docs/checkpoint. PR #6/#7 remain Draft/unmerged; PAPER mode mandatory; live broker writes disabled; no original Tradepro changes.


### New code since the API-first continuation plan — 27 October 2026

Created `backend/app/services/upstox_charge_api_orchestration_service.py` and `backend/tests/test_upstox_charge_api_orchestration_service.py`. The wrapper classifies calculator responses as estimate-only and trade-charge responses as aggregate reconciliation only; neither can be used as per-fill actual. Tests cover classification, failed API response, null IPFT preservation, scope, and explicit trade date. This is not yet end-to-end UI or accounting-ledger wiring. Continue by locating the existing read-only reconciliation route and ledger contract, wiring aggregate results only as reconciliation context, adding route/ledger tests, then verify exact-head CI. The latest code/test commit before doc updates is `f98ed9e7f4b092c6d8e284d7461ee4aba46b72e4`; status/workflow lookup returned no runs, so CI is unverified rather than green.


### Authenticated API routes added — 27 October 2026

Added `backend/app/api/v1/upstox_charges.py`, registered in `backend/app/api/v1/router.py`. Routes: `GET /api/v1/upstox/charges/brokerage-estimate` and `GET /api/v1/upstox/charges/aggregate`. Both require authentication and the current user's connected Upstox connection; access token is decrypted only server-side. The former is estimate-only; the latter aggregate reconciliation-only; neither is per-fill actual evidence. CI passed on prior head `6021815de9bfa1213320daafb4eda866c93f3ec9`, but CI for route/router commits is in progress/queued. Add route-level tests, check CI against final exact head, then assess safe persistence of aggregate reconciliation context. Do not split aggregate totals across fills or mark GST/IPFT approved without evidence.


### Route-level tests added — 27 October 2026

Added `backend/tests/test_upstox_charge_api_routes.py`: validates estimate-only route response and null IPFT preservation, aggregate-only response classification, and invalid quantity rejection. Previous CI passed on `24b7b9ee728049f26b200cbee54571ae3c22b7bf` (run #40473895336). New test commit `ffb87c9af7c87d921eadf0198b7ba8704be65e76` is awaiting its own CI. Continue by checking that run, fixing any failures, then inspect the existing evidence/reconciliation schema to determine a safe aggregate-only persistence path; do not promote aggregate data to per-fill actual accounting.


## Resume handover — 27 October 2026 (Upstox aggregate API persistence)

Last confirmed relevant green results: route-test commit `ffb87c9af7c87d921eadf0198b7ba8704be65e76` / Backend CI #40474374635; documentation commit `10d105a344b08a21dfe50593f8683453a5d44bfc` / Backend CI #40474444724. These are not proof that subsequent docs commits are green.

Continue with a dedicated durable aggregate API reconciliation record, not the source-document evidence models. Record owner/connection, endpoint and API version, requested scope/window, fetched timestamp/status, response hash/provenance and sanitized payload. Enforce tenant ownership; never persist access tokens or secrets; distinguish estimate from aggregate response and preserve missing/null/invalid/zero semantics. No per-fill allocation or actual accounting promotion from aggregate API data. Add ownership, provenance, replay/idempotency and SQLite/PostgreSQL 16 migration round-trip tests, run the full safety/migration/restore CI suite, then update maintained docs and checkpoint with the exact green head.

Safety: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mode mandatory; live broker order writes disabled.



## Latest work — 27 October 2026: aggregate API persistence

Implemented `BrokerApiReconciliationRecord` and Alembic revision `202610270030`, then wired authenticated `GET /upstox/charges/aggregate` to persist a sanitized, immutable aggregate-only snapshot. Includes owner and broker-connection linkage, endpoint/API version, request scope, fetch timestamp/status, response hash and idempotency key; strips credential-like keys before persistence. No per-fill allocations or actual accounting promotion. Added route assertions for owner linkage, hash, sanitization and duplicate response idempotency. Code/test head `77bb07c0b6ee075e5e1eaa61ab0a5d138475953b`; CI #40475498978 was in progress, and #40475479511 was also running. Next: inspect exact-head CI and fix failures; verify SQLite/PostgreSQL migration round-trips, broker-write safety and synthetic restore; add owner-isolation/immutability tests as needed; only then mark green and resynchronize docs.

Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mode mandatory; live broker order writes disabled.


## Follow-up — 27 October 2026

Regression tests now cover rejection of another user's Upstox connection and rejection of updates to an existing aggregate evidence snapshot. Commit `688cb70e2d64b866fbb9b6f19c7675ab764a0ecf`; verify exact-head CI. Previous implementation head `77bb07c...` is green on Backend CI #40475498978, including migration round-trips on SQLite and PostgreSQL 16, broker-write boundary and synthetic restore. The added tests are not green until their own CI completes.


## CI follow-up — 27 October 2026

Regression CI failed because the ownership test called `make_user()` twice with the fixture's default unique email. Corrected to distinct email addresses in `977ad6b7e6eeae1346b28c03c2d83bb62ec93910`. The failed run had 1 failed / 1128 passed; later safety, migration and restore steps were skipped. Check CI on this exact head and fix any remaining failures before marking green.


## Verified checkpoint — 27 October 2026

The owner-isolation test fixture was corrected to use unique emails in `977ad6b7e6eeae1346b28c03c2d83bb62ec93910`. Backend CI #40476768203 and documentation CI #40476805191 passed. Backend workflow verified pytest, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore and retained evidence. Continue with the remaining Phase 3 accounting acceptance gates; aggregate API snapshots are not per-fill actuals. Keep PAPER mode mandatory, live order writes disabled, PR #6/#7 Draft/unmerged, and work only in `tradepro-improved`.



## Next checkpoint — GST policy edge cases — 27 October 2026

Commit `91212a0224f3bf4a01bff06c14764a404c1cbc67` adds regression coverage for zero vs missing components, invalid/nonfinite/negative amounts and inclusive/expired effective-date boundaries. Exact-head CI must pass all backend tests, broker-write safety, SQLite/PostgreSQL migration round-trips and synthetic restore before this is accepted. Upstox GST component candidates remain DRAFT until conflicting source evidence is independently resolved; no blanket approval.



## Verified checkpoint — GST policy edge tests — 27 October 2026

Backend CI #40477899628 passed on code/test commit `91212a0224f3bf4a01bff06c14764a404c1cbc67`, with pytest, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips and synthetic restore evidence all successful. Documentation-triggered runs #40477921259 and #40477930671 also passed. Next review charge-component applicability and estimate variance/replay/rollback tests; do not equate green tests with independent approval of the Upstox GST candidates. Maintain PAPER-only mode and disabled live broker writes; do not touch original `Tradepro` or merge PR #6/#7.



## Latest GST test increment — 27 October 2026

Commit `c010b7d010351465b87f8e6d844fc9171dfc5dad` adds paise-rounding and exact broker/exchange/segment/product policy-scope regression tests. Verify CI on this exact head before marking green. Prior green is `91212a0224f3bf4a01bff06c14764a404c1cbc67` / Backend CI #40477899628. Continue with uncovered accounting component-applicability and rollback boundaries; do not duplicate existing fill-set/digest/replay checks.



## Verified checkpoint — GST scope and rounding tests — 27 October 2026

Commit `c010b7d010351465b87f8e6d844fc9171dfc5dad` is green on Backend CI #40478376361. Pytest, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips and synthetic restore evidence all succeeded. Documentation CI #40478395488 was still running on `334a078...`; verify latest documentation heads. Next inspect accounting component applicability and rollback gaps, then continue authoritative GST/IPFT source validation. Keep PAPER mandatory, live writes disabled, PR #6/#7 Draft/unmerged, and original `Tradepro` untouched.



## Latest CI reconciliation — 27 October 2026

Verified green: GST scope/rounding tests at `c010b7d010351465b87f8e6d844fc9171dfc5dad` / Backend CI #40478376361; documentation-triggered runs #40478676089, #40478683982 and #40478691999 all completed successfully across tests, broker-write safety, SQLite/PostgreSQL 16 migration round-trips and synthetic restore. This new documentation update requires its own exact-head CI check. Continue by reviewing IPFT mode/component applicability and atomic rollback, then add only missing tests. Keep candidate statutory approval gated on authoritative evidence; PAPER mode mandatory and live writes disabled.



## Latest verified CI and rollback audit — 27 October 2026

Backend CI #40479126107 on `432a3d37...` and #40479142058 on `3f29c70b...` passed every step, including backend tests, broker-write safety, SQLite/PostgreSQL 16 migration round-trips and synthetic restore. `85ddf857...` had no workflow run in the current lookup, so no separate green claim is made for it. Existing live-fill tests already cover atomic rollback on staged rows, commit and flush failures; exact retry after post-commit refresh failure; canonical exchange/IPFT once; DP completeness; replay and quantity constraints. Next inspect source-to-canonical mapping completeness for any specific uncovered defect. Keep GST/IPFT candidates unapproved pending authoritative review, PAPER mandatory, live writes disabled, PR #6/#7 Draft/unmerged, and original `Tradepro` untouched.



## Source-to-canonical mapping checkpoint — 27 October 2026

CI runs #40479568869, #40479578088 and #40479585940 passed for the latest documentation commits. Canonical planning validates source provenance, independent review, shared fill manifest/fingerprint and explicit weights; plans are not accounting-approved. Split transaction/IPFT rows cannot be persisted in the six-component accounting model until a durable canonical-source relationship is added. Next design/review that migration and its SQLite/PostgreSQL tests before enabling split-row persistence. Preserve fail-closed behavior and statutory approval gates. PAPER mandatory, live writes disabled, PR #6/#7 Draft/unmerged, original `Tradepro` untouched.



## Refined next step — source-link schema exists; workflow integration remains — 27 October 2026

The normalized link model and migration already exist (`BrokerChargeCanonicalSourceLink`, `202610250025_normalize_canonical_source_links.py`). Do not duplicate the schema. The verified-allocation persistence service still validates the six-component set and rejects multi-source canonical plans, so the gap is safely integrating and revalidating source links through snapshot creation/review and allocation. Inspect those services/tests next; retain fail-closed behavior until atomic linkage, reviewer validation and paise reconciliation are proven. Prior CI #40479568869/#40479578088/#40479585940 passed; latest docs commits require their own CI. PAPER mandatory; live writes disabled; PR #6/#7 Draft/unmerged; original `Tradepro` untouched.



## Split-source path handover — 27 October 2026

CI #40480367450/#40480378523/#40480401549 passed on the prior documentation commits. Existing canonical snapshot tests already cover split transaction/IPFT, independent review, allocation persistence and missing source-link rejection. The legacy direct allocation adapter still blocks multi-source plans, so the next task is route/caller wiring audit—not duplicate schema or snapshot work. Verify all exposed APIs use the reviewed canonical snapshot path, retain fail-closed behavior, then check this documentation update's exact-head CI. PAPER mandatory; live writes disabled; PR #6/#7 Draft/unmerged; original `Tradepro` untouched.


## Route audit finding — aggregate response credential sanitization — 27 October 2026

The API wiring audit found a concrete safety gap in `backend/app/api/v1/upstox_charges.py`: aggregate API response payloads were sanitized before durable persistence but the HTTP response returned the raw payload. A credential-like field such as `access_token` could therefore be exposed to the authenticated caller even though it was not stored. Fixed by applying `_sanitize_api_value` to the aggregate response payload and added a route regression assertion that the field is absent from the HTTP response. Code commit `203947ee25437e5b4637d25f365f0d1df7575fb1`; test commit `7e17376a91c8d835e1af42377be49c499d013bea`. Exact-head CI is pending; do not mark this fix green until CI passes. The brokerage-estimate route was not changed. Split-charge canonical snapshot safeguards remain in place. PAPER mandatory; live broker writes disabled; PR #6/#7 Draft/unmerged; original `Tradepro` out of scope.


## Aggregate API response sanitization — CI verified — 27 October 2026

- Backend CI runs #40481297561, #40481317091, #40481339870 and #40481349885 all completed successfully. Every run passed pytest, broker-write boundary enforcement, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore, and retained restore evidence.
- The aggregate Upstox charge API now applies `_sanitize_api_value` to the HTTP response payload as well as the persisted evidence. Route regression coverage asserts that `access_token` is not returned. Aggregate responses remain explicitly `per_fill_actual=False`; this is evidence capture/reconciliation, not per-fill accounting promotion.
- Route-wiring audit continues: confirm exposed charge APIs cannot bypass independently reviewed canonical snapshots for split transaction/IPFT evidence. Existing fail-closed direct adapter remains unchanged.
- The latest documentation commits triggered by this note need their own CI verification. Do not call this documentation revision green until those exact-head runs pass. Safety unchanged: only `tradepro-improved`; original `Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.


## Handover — DP instrument applicability regression verified — 27 October 2026

The DP/demat manifest eligibility query now requires `Instrument.instrument_type == "EQUITY"` independently of the order's segment label. This closes a case where a derivatives instrument could pass the DP-specific gate if order metadata incorrectly claimed equity delivery. Test `test_demat_manifest_rejects_non_equity_instrument_even_if_order_segment_says_delivery` covers that case.

Implementation CI #40482878220 passed on `447e9703f4bcf43dc6392d0d3741caee7709ce95`; regression CI #40482895888 passed on `e62c9518df2edd9c80473b55f3a63a632a30121a`. Both include backend tests, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips and synthetic restore verification. Continue by auditing the component applicability matrix for supported instrument/segment/product/side combinations; update the checkpoint and maintained docs after each green head. This documentation commit needs its own exact-head CI.

Do not relax the six-component reconciliation contract, treat estimates as actuals, or bypass canonical source review. Production Oracle restore and genuine contract-note acceptance remain evidence-gated. PAPER mandatory; live broker writes disabled; PR #6/#7 Draft/unmerged; original `Tradepro` untouched/out of scope.


## 27 October 2026 — latest charge-total completeness CI checkpoint

- Latest verified code increment: commit `431db3a1de4b00afceefabf3def71c1ddb08a446` passed Backend pytest CI [#40484300318](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40484300318) (workflow completed successfully at 2026-10-27 09:56 UTC). This verifies the API-schema integration that derives `total_charges_complete` using the same reconciliation function as the execution model.
- The completeness service now requires a recognized DP/demat status, consistent amount applicability, valid core charge components, and exact equality between the persisted total and the recomputed total. A resolved DP status alone is not enough to mark a total complete.
- Prior intermediate attempts #40483567109, #40483589784 and #40483898638 failed; these are retained as history, not treated as green. Service-only CI #40483552159 passed. The schema-integrated code head #40484300318 is the latest successful code verification.
- This does not yet prove all Phase 3 gates pass. Next: verify regression coverage for stale/tampered totals and schema output; audit applicability across equity delivery/intraday, futures/options and product/side; then synchronize maintained docs and verify the resulting documentation head. Continue failing closed for missing/invalid charges and do not silently coerce unknown/inapplicable components to zero.
- GST/IPFT API resolution work remains in place; legal/tariff approval and actual broker evidence reconciliation are distinct gates. Synthetic restore is not production Oracle restore acceptance; real Oracle backup/restore can be accepted after deployment/backups exist; genuine personal contract note is not required for code-level work but actual broker reconciliation requires suitable real evidence.
- Safety unchanged: work only in `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is out of scope and must not be modified; PR #6/#7 remain Draft/unmerged; PAPER mode mandatory; live broker order writes remain disabled.
- Documentation changes in this entry themselves require CI on the resulting exact head before this documentation checkpoint is considered green.


## Resume update — 27 October 2026

- Verified code/test head before this documentation sync: `a0586b27e8ccda9446f01fd109e8986875c536b3`; Backend CI [#40484960486](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40484960486) completed successfully, including pytest, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips and synthetic restore/evidence retention.
- New checkpoint documentation commit: `e5e8270cbcee54e85a002a05f32156c356dd5e96`. CI for this documentation head must be checked before declaring docs green.
- Continue with supported instrument/segment/side/product applicability and fail-closed completeness/replay/rollback audit. Avoid duplicating existing regression tests. GST/IPFT policy and statutory valuation code are present; source-backed tariff approval and actual invoice/per-fill acceptance remain separate gates.
- PR #6/#7 remain Draft/unmerged; PAPER mode mandatory; live broker order writes disabled; only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` must not be modified.


## Annual GST statement reconciliation finding — 27 October 2026

- A user-provided Upstox/RKSV annual global transaction statement for FY 2022–23 was reviewed as annual aggregate evidence, not as an individual contract note. Its visible charge rows do not, by themselves, reconcile the reported aggregate “IGST on Charges” line to a unique taxable base at paise precision.
- Preserve original source-row labels exactly. Do not relabel an STT rounding row as SEBI fees. Establish the taxable base from underlying invoice/contract-note lines and the applicable historical policy; do not choose a charge merely because it makes the arithmetic match.
- The GST reconciliation helper correctly retains reported-vs-expected variance instead of inferring or rewriting the base. A small annual variance may reflect invoice-level tax rounding/aggregation or a charge not visible in summarized lines; this annual statement alone cannot distinguish these explanations.
- Do not use an annual AGS total to approve actual per-fill GST or promote canonical charge allocations. Next evidence gate: an itemized individual contract note or underlying invoice-level breakdown. Keep FY 2022–23 evidence separate from the 2026 public-schedule estimate policy.
- This is an evidence-scope clarification, not a change to GST/IPFT policy or a declaration that the broker billed incorrectly. No personal identifiers or account-specific figures are copied into this repository note.
- Latest code/test head remains `9eb278588b78d2a966cc196c15d7a4d9a6ae8868`; Backend CI [#40505176395 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40505176395). This documentation sync creates a new head and requires its own exact-head CI before it is marked green.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` out of scope; PR #6/#7 Draft and unmerged; PAPER mandatory; live broker order writes disabled.

## Resume point — historical GST invoice regression

The five January 2023 Upstox contract-note examples have been added as daily aggregate regression fixtures in `backend/tests/test_historical_upstox_contract_note_gst.py`. They validate the disclosed brokerage/transaction/SEBI taxable base and split GST totals. No distinct IPFT amount is shown in the supplied transcription, so the test does not convert absence into zero or create a per-fill IPFT amount. Use the historical effective tariff for the trade date; current API calculator results are estimates, not booked historical charges. Commits: `98f14aef1b3b541c2a6e07beb227b6f3f0471a42`, `547917868d28d3f46f1f549a8daa50d57fc4542d`. Exact-head CI remains to be verified.

## Effective-dated historical IPFT estimate gate — 27 October 2026

- Added `calculate_ipft_estimate_for_scope()` in `backend/app/services/broker_tariff_rules.py`. It requires an approved exact-scope `TariffRule`, NSE/FO/OPTIONS, explicit BUY/SELL, PREMIUM basis and INR_PER_CRORE; generic tariff calculation now fails closed for IPFT. The caller must supply the correct source-defined premium aggregation scope. This helper does not allocate aggregate IPFT to fills or certify booked charges.
- Added date-boundary tests for the official NSE schedule: ₹0.01/crore before 1 April 2023, ₹50/crore for equity options from 1 April 2023 through 28 February 2026, and rollback to ₹0.01/crore effective 1 March 2026. Sources: [NSE/FA/56129 (24 March 2023)](https://nsearchives.nseindia.com/content/circulars/FA56129.pdf) and [NSE/FA/73061 (27 February 2026)](https://nsearchives.nseindia.com/content/circulars/FA73061.pdf).
- These tests validate date selection and guarded estimate arithmetic; they do not activate production tariff records. No production rule is automatically approved by the tests, and actual IPFT remains distinct from the current Upstox calculator estimate and the supplied daily contract-note aggregates.
- The five historical GST invoice fixtures are in `backend/tests/test_historical_upstox_contract_note_gst.py`. The note transcription does not separately identify IPFT; missing is not zero. Exact-head CI for the latest code/test and documentation commits is pending verification.

- Resume by checking Backend CI for latest branch head, fixing any failure, then update this checkpoint to the successful exact head. Keep PR #6/#7 Draft/unmerged, PAPER mandatory, live writes disabled, and do not modify original `Tradepro`.

## Superseding decision — GST invoice regressions and API evidence scope (27 October 2026)

- The five user-provided January 2023 Upstox daily contract-note fixtures and effective-dated IPFT estimator tests are included in code/test head `fe4c8c484650a8b6e63f822a8c7581431c855d22`.
- Exact-head Backend CI [#40545398934 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40545398934): **1,149 passed, 1 warning**. Broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, and synthetic restore checks passed.
- GST daily-invoice calculation is now regression-validated for all five supplied dates. Do not reopen the basic 18% formula as an unresolved research question. The annual AGS two-paise variance remains an aggregate reconciliation note; it is not evidence of a broker error and must not block the GST implementation.
- The Upstox pre-trade brokerage calculator is estimate-only. The post-trade charges endpoint `/v2/trade/profit-loss/charges` is aggregate-only. Preserve these meanings through `broker_charge_api_value_resolution.py`; do not promote either response to per-fill booked charges. Reconcile contract-note actuals at the source's disclosed scope.
- IPFT is not a blocker to the validated GST formula. Use effective-dated IPFT only when the product/segment and source-supported premium basis apply. The supplied January 2023 note text has no separately identified IPFT line, so don't assume either a separately booked IPFT amount or that it is bundled. Preserve it as not separately disclosed; do not synthesize zero or an allocation. If no applicable IPFT rule/component is evidenced for a trade, leave it not applicable/unknown according to the source and product scope rather than holding up GST.
- The guarded estimator is for estimate calculation only and requires an approved effective-dated tariff rule and explicit scope. It does not activate a production tariff or prove historical booked IPFT.
- Next Phase 3 work should proceed to the remaining accounting acceptance gates (fill identity, replay/idempotency, atomic rollback and component applicability), while using these GST tests as regression coverage. Only revisit IPFT when an applicable source-backed tariff or actual source field requires it.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.


## Current continuation point — 27 October 2026

Continue from branch `phase3/cross-broker-gst-ipft-resolution` in `tarunsharma2610-del/tradepro-improved` only. The GST comparison helper now supports nested JSON paths (e.g. `data.charges.gst`) and tests preserve missing/null/zero distinctions. Commits: `ff2d69546e5aad37c519c6622f51018bf7706ad5` and `a6f88dc85dcb25d903e610aaf30ce395ec12d650`. Do not claim the new head green until CI on the final current head succeeds. Next: check/fix exact-head CI; integrate comparison only where reviewed valuation lines and supplier/place-of-supply inputs are available; continue per-fill accounting acceptance and verified tariff coverage. Keep PR #7 Draft, PAPER mode mandatory, live writes disabled, and original `Tradepro` repo untouched.


### Latest code increment — exact API field-path resolution (27 October 2026)

`resolve_charge_api_value` now reads only the exact approved dotted payload path; it cannot substitute a top-level field merely because its leaf name matches. Regression fixtures now exercise nested response data and missing-path behavior. Implementation/test commits: `aba4ffba23f96d976dad05a2dd6c46fefe188875`, `5ccaad1fcc464ee305746a380f889d7ee283d7c4`. Confirm CI on the newest commit before marking green. Continue with caller integration and component-by-component accounting acceptance; do not promote API estimates/aggregate summaries to per-fill actuals.


## Session resume checkpoint — 27 October 2026 (API-first charges decision; supersedes older next-step wording)

- **Resume from this checkpoint only.** Latest verified documentation head before this session sync: `72b03ee5b5c7487bb94815ea8b6fc3aabb6f8352`; exact-head Backend CI [#40553171858 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40553171858). The run completed successfully for backend pytest, broker-write boundary enforcement, SQLite upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL + document-volume restore, and restore-evidence retention. It is newer than the earlier failed CI and supersedes it for the tested commit.
- **User decision:** do not let a tiny GST/IPFT rounding discrepancy (including the discussed ₹0.20 annual aggregate variance / sub-paise arithmetic) block paper trading or the core app. The app does not need to independently recreate every broker billing detail before progressing.
- **Paper-trade approach:** use Upstox Brokerage Details API as an estimate where available; otherwise use the existing GST/brokerage/tax engine as a fallback. A target of roughly 95% practical accuracy is acceptable for paper-trading estimates, provided charges are labelled estimated and used consistently. Historical backtests should disclose that current tariffs may differ from historical tariffs.
- **Actual trades:** broker executes and collects actual charges. Import broker-reported post-trade charges/statements where available. Upstox post-trade Trade Charges API is aggregate evidence and must not be misrepresented as per-fill booked-charge evidence. Keep estimates separate from actuals; preserve reconciliation safeguards for imported records without blocking unrelated app development.
- **Do not reopen GST/IPFT from zero or chase tiny rounding differences as a release blocker.** Retain the existing GST engine, tariff/source evidence, API field-path resolver, reconciliation service and tests. Revisit only a concrete integration defect, material systematic variance, or a scope needing evidence.
- **Actual next technical work:** (1) inspect and wire the GST API-vs-engine comparison into the real charge-data flow using the correct charge lines and supplier/place-of-supply inputs; (2) finish genuinely uncovered component-by-component per-fill accounting acceptance—fill identity, paise totals, source-to-canonical mapping, replay/idempotency, rollback and segment/product applicability; (3) keep unsupported BSE/MCX tariff scopes explicitly estimated/unverified until source-backed; (4) synchronize maintained docs and run exact-head CI.
- **Evidence correction:** user has supplied genuine Upstox/RKSV contract-note evidence for 23, 24, 25, 27 and 30 January 2023. Do not state that no personal contract note exists or ask the user to provide it again. Production Oracle backup/restore acceptance remains deferred until deployment backups exist.
- **Safety invariants:** work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` is out of scope. PR #6 and PR #7 remain Draft/unmerged. PAPER mode mandatory; live broker order writes remain disabled. Do not merge.
- **First action next session:** verify the latest head and its CI, read this checkpoint's latest section, then continue from the caller-level API/GST integration and remaining accounting acceptance. Do not resume from the earlier failed CI or repeat already completed GST/IPFT research.


## API-first paper-trade charge estimation decision — 29 October 2026

- User-approved behavior: use Upstox's pre-trade Brokerage Details API for paper-fill charge estimates when it returns a complete, valid, internally consistent breakdown. Keep the existing deterministic local calculator as the automatic fallback if the API is unavailable, expired/unauthorized, incomplete, null/invalid, or inconsistent. This is estimation only, not live-trading/accounting promotion.
- Implementation added on the Phase 3 branch: `backend/app/services/paper_trade_charge_estimator.py` plus deterministic tests. `ExecutionService` now uses API-first estimates for market and matched limit paper fills and records `UPSTOX_API_ESTIMATE` versus `HARDCODED_FALLBACK` in the existing execution charge-source field. Components are accepted only when paise-exact supported components sum exactly to the API total; transaction, clearing and IPFT are combined once in the existing exchange-charge field. Unknown/incomplete fields fall back rather than block paper trading.
- Existing post-trade Upstox charges endpoint remains aggregate reconciliation evidence, not per-fill actuals. The API route already exists. GST reconciliation remains available without blocking paper-trade P&L.
- Implementation commits: `b90c09dc82a51181bc9eae422cb025eb79c65bcb`; default-enabled setting `UPSTOX_CHARGE_ESTIMATES_ENABLED`. CI disables network estimates only for the broad execution suite; mocked estimator tests cover API and fallback paths.
- Backend CI [#40755234415](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40755234415) — **SUCCESS** on code/test head `778e76d3554a3baedc41f0396276c1cb3dafc38f`: **1,197 passed, 1 warning**; broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic restore/evidence retention passed. Documentation sync head `d57dd476ecd6acebd4dc9e169912b877811a8166` still needs exact-head CI verification before it is called green.
- Next: continue the next uncovered Phase 3 accounting acceptance gate after CI recovery. Do not reopen GST/IPFT from zero or make minor estimate variance a paper-trading blocker. Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled; original `Tradepro` out of scope.


## Standard Upstox access-token lifecycle — audited 29 October 2026

- The standard OAuth authorization-code access token expires at 03:30 IST the following day; the current adapter records that expiry and `BrokerCredentialsService.get_access_token` refuses expired tokens. A regression test now covers the expired-token path.
- Do **not** invent a silent refresh-token grant or reuse a single-use authorization code. The official standard OAuth flow requires a new authorization-code exchange after user authorization; the documented extended/analytics-token facilities are separate token products with different read-only scopes and eligibility requirements, not a generic refresh token.
- In paper trading, an expired/unavailable token must not block a fill: the charge estimator uses the hardcoded deterministic fallback and records the fallback source. The API-first estimate remains best-effort.
- Live Upstox API calls have not been credential-tested in this CI environment. Do not label the real OAuth handshake or account-specific endpoint entitlements as end-to-end verified until a user-authorized integration test succeeds.
- Official references: https://upstox.com/developer/api-documentation/get-token/ and https://upstox.com/developer/api-documentation/authentication/ .


## Current resume point — 29 October 2026 (supersedes older next-step wording)

- Resume from the newest Phase 3 checkpoint, not any historical failed run. Code/test head `778e76d3554a3baedc41f0396276c1cb3dafc38f` passed Backend CI #40755234415 (1,197 passed, 1 warning); documentation head `d57dd476ecd6acebd4dc9e169912b877811a8166` passed exact-head Backend CI #40755635769.
- API-first paper charges are implemented: use the Upstox pre-trade Brokerage Details API only when supported components are complete, paise-exact and sum to the reported total; otherwise fall back locally without blocking paper fills. Persist the source as API estimate or local estimate. Never call these booked actuals.
- Upstox post-trade charges endpoint is aggregate-only. GST formula fixtures for the five supplied January 2023 notes are regression coverage at daily-note scope, not per-fill actual evidence. IPFT remains effective-dated/scope-guarded and not a blocker to GST or paper-trading progress.
- OAuth: standard token expiry is handled; don't invent refresh-token semantics. Real account credential/entitlement tests have not been claimed.
- Next: continue instrument/segment/product/side applicability audit; add only a genuinely missing test/guard. Check any caller-level GST/API comparison gap before wiring new code. BSE/MCX scopes without approved source-backed tariff remain explicitly estimated/unverified.
- Keep maintained docs synchronized and verify CI on the exact final head. Actual Oracle backup/restore acceptance waits for deployed backups.
- Invariants: work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` must not be modified. PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled; do not merge.


## Latest handover — 29 October 2026

Resume from code/test head `217e5c74878048d276de20929b57a6a2b5aa668d`. The Upstox brokerage estimate parser now rejects response bodies whose status is not `success`; regression coverage is added. BSE/MCX local fallback remains available for paper trading but explicitly marks exchange-specific tariffs unverified; regression cases cover BSE equity and MCX futures. Exact-head Backend CI #40875989690 was still running when this handover was written. Verify its final result before marking this code increment complete. Earlier runs #40875565498, #40875627719 and #40875648924 passed on earlier heads.


## Verified code checkpoint — 29 October 2026

Code/test head `217e5c74878048d276de20929b57a6a2b5aa668d` passed Backend CI #40875989690. All stages passed, including backend pytest, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore and evidence retention. The new unsuccessful-response-body guard and BSE/MCX unverified fallback labels are covered. Estimator source labels are `UPSTOX_API_ESTIMATE` and `HARDCODED_FALLBACK`. After documentation synchronization, verify the newest documentation-head CI separately.


## Current resume point — 29 October 2026

Follow the user's simplified policy: Upstox brokerage estimate API first; existing hardcoded calculator on API/token/invalid-response failure; paper trading continues. Do not treat exchange-by-exchange tariff certification as a Phase 3 blocker. Removed the BSE/MCX-specific fallback warning. Execution responses expose the standard disclaimer: “Estimated charges may differ from actual broker charges. For paper trading only; these are not actual booked charges.” Latest code commits: `3b3fe2aa981013cdb1d75b6014bd14c56361f5b2`, `5e803146c0992539da8fe93f3df6836e5232a276`, `134cc87386b0c19b6e1294b5c95ae9aac9d813d4`, `6f2a80b51266ec14cb8e89761c97caa675df1fe4`. Verify exact-head CI before marking this increment green.


## Current resume point — 29 October 2026 (latest fix set)

The earlier CI failures were actionable: stale fallback-call arguments caused API-error handling to raise instead of falling back, and legacy ExecutionOut fixtures lacked the newly exposed charge-source field. These are fixed. The execution response disclaimer now recognizes `UPSTOX_API_ESTIMATE` and `HARDCODED_FALLBACK`; contract-note actuals are not labeled estimates. The response schema keeps a backwards-compatible `PAPER_ESTIMATE` default. Regression tests cover these behaviors. Latest code commit before docs refresh: `83a8ae95ccfc8d0271bb07c67316a40eff6be509`. Historical runs #40877183503 and #40877198561 failed before the repairs. Run #40877487855 was still in progress but predates the last two repairs; exact latest-head CI is required. Continue from this point. Do not reopen GST/IPFT research or treat BSE/MCX tariff certification as a blocker.


## Follow-up audit — persisted estimate-source provenance

A caller-level audit found the execution service was collapsing the estimator's local fallback into generic `PAPER_ESTIMATE`. Both market and matched-limit fill paths now persist the distinct labels `PAPER_UPSTOX_API_ESTIMATE` and `PAPER_HARDCODED_FALLBACK`. The paper-only disclaimer covers both. Tests check fallback source persistence and disclaimer behavior. Commits: `01a891595b05c5ca5f1d6be92d778a786b70c5f2`, `e50f96eb398dd46d4c59168b1fb0d16ca27dacac`, `f109384089fdf59418bf9ef86678df48f186bccd`. Verify exact-head CI before marking green.


The last CI run on the prior PR merge head had 1,204 passed and 1 failed because a transient ORM row supplied `charge_source=None`; the schema default did not apply to explicit null. A before-validator now normalizes that legacy null to `PAPER_ESTIMATE` (commit `287dcc31807bc2b5677bc5128d2e65028c799017`). Verify the new exact-head CI before declaring green.


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


## Documentation-head verification — 29 October 2026

- The maintained-doc sync at `cd490b506cd973af75c3b96b585c18ff97e2f78f` passed exact-head Backend CI [#40884629622 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40884629622).
- This verifies the 27-document refresh for the Upstox response-schema validation increment. The CI result confirms the backend workflow passed; no test count is asserted because the run summary did not expose one.
- The latest code fix remains `404c1e11ef4f2557c791c720c8d9a3fbc4e93bc1`, passed Backend CI [#40883660756 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40883660756).
- Current focus: response schema is endpoint-specific, null/missing IPFT remains distinct from zero, estimates and aggregate summaries cannot become per-fill actuals, and PAPER/live-write safeguards remain unchanged. PR #6/#7 remain Draft/unmerged; original `tarunsharma2610-del/Tradepro` remains out of scope.


## Phase 4 resume pointer — 29 October 2026

Authoritative Phase 4 planning records:
- `PHASE4_ROADMAP.md`
- `PHASE4_PROGRESS.md`
- `PHASE4_LATEST_CI_CHECKPOINT.md`

Phase 4 branch: `phase4/roadmap-progress-checkpoints`; created from Phase 3 checkpoint `9add7f98ccf89f0c146e4367b79cdd5877104ff3`. This is planning/checkpoint scaffolding only. The Phase 4 repository audit (P4-0) has not yet been completed, and no Phase 4 feature implementation is claimed. Exact-head CI for the new documentation commits is pending verification.

Resume only after verifying the latest head and its own CI. Next task is P4-0 baseline audit and evidence-based gap matrix. Keep work exclusively in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` is out of scope. Do not update `main` or merge PR #6/#7 without explicit user authorization. PAPER mode mandatory; live `place_order`, `modify_order`, and `cancel_order` writes disabled. Upstox Brokerage Details is estimate-only; post-trade Trade Charges is aggregate reconciliation-only, never per-fill actual evidence. Real credentialed OAuth smoke test and production Oracle backup/restore remain deployment-gated.


## Phase 4 P4-0 continuation — 29 October 2026

- Static baseline audit saved in `PHASE4_P0_BASELINE_AUDIT.md`. Existing market-data streamer, strategy/risk services, paper execution/accounting, and backend migration/restore checks were found; do not rewrite them without a concrete gap.
- Safety hardening: `backend/app/core/config.py` now normalizes `TRADING_MODE` and rejects anything except `PAPER` at settings load; regression tests are in `backend/tests/test_trading_mode_safety.py`.
- Code commit: `791ae9858d80ddf5554db71f134db273e55be29b`; regression test commit: `1517b2947709f96083dc48e06edfebe32152d37f`.
- Draft PR #8: https://github.com/tarunsharma2610-del/tradepro-improved/pull/8 (base `phase3/cross-broker-gst-ipft-resolution`; head `phase4/roadmap-progress-checkpoints`). PR #8 is unmerged; PR #6/#7 remain unmerged; `main` unchanged.
- Backend CI run #40896797689 is running on exact head `4b4c78b60685f237fced74d1c9fc36117401515d`: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40896797689. Do not call green until completed successfully.
- Next resume step: inspect exact-head CI result; if green, continue P4-0B broker-write call-path audit and test coverage. If failed, inspect logs, fix on this Phase 4 branch, and rerun before a green checkpoint.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PAPER mandatory; live broker writes disabled; no merge authorized; aggregate post-trade API remains reconciliation-only.


## Phase 4 resume checkpoint — 29 October 2026 (latest verified code CI)

- Repository: `tarunsharma2610-del/tradepro-improved` only; branch: `phase4/roadmap-progress-checkpoints`.
- Draft PR #8: https://github.com/tarunsharma2610-del/tradepro-improved/pull/8; base is `phase3/cross-broker-gst-ipft-resolution`. PR remains unmerged. `main` has not been updated. PR #6/#7 remain unmerged.
- **Latest verified code/test head:** `13bcb6c6b25387916b8e653cb0ba8dd3ad3c31ad`.
- **Backend CI #40898908339: SUCCESS** on that exact head: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40898908339. Backend pytest, broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, and synthetic PostgreSQL/document-volume restore/evidence retention all passed.
- CI failure on earlier run #40896927805 was traced to the Upstox Brokerage Details test fixture asserting IPFT under the wrong field. Corrected fixture/assertion uses `data.charges.otherTaxes.ipft`, preserving null distinctly; the retry passed.
- P4-0 static audit saved in `PHASE4_P0_BASELINE_AUDIT.md`. PAPER-only config validation added in `backend/app/core/config.py`; tests added in `backend/tests/test_trading_mode_safety.py`.
- **Next step on resume:** verify the current branch head and latest CI (documentation updates can trigger a newer head/run); then continue P4-0B broker-write call-path audit and add targeted tests for every route into broker write methods, automated-entry kill switch, stale market data, and risk checks. Fix any failure and re-run before checkpointing green.
- Safeguards: work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` untouched; do not update `main` or merge PR #8/#7/#6 without explicit authorization; PAPER mode mandatory; live `place_order`, `modify_order`, `cancel_order` writes disabled; Upstox Brokerage Details remains estimate-only and aggregate Trade Charges remains reconciliation-only; no credentialed live smoke test or production Oracle restore claimed.

## Latest Phase 4 handover — 30 October 2026

Resume from branch `phase4/roadmap-progress-checkpoints`, latest verified code/test commit `24c34dac47e273f9377485dc697f9fa510808a72`. Exact-head Backend CI #41012821073 passed: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41012821073. PR #8 remains Draft and unmerged; do not merge or update `main`.

Completed since the previous checkpoint: P4-0B static AST broker-write guard now detects literal reflective dispatch via `getattr` for `place_order`, `modify_order`, and `cancel_order`. Regression tests cover rejecting write dispatch and permitting a non-write read method. An earlier run #41012807565 failed because test fixture escaping generated invalid Python; the fix is included in the green exact-head commit.

Next task: P4-0C audit/test automated-entry kill switch, confirm strategy exits remain available when new entries are disabled, inspect stale candle/market-data handling and risk enforcement at the execution boundary. Read `PHASE4_LATEST_CI_CHECKPOINT.md`, `PHASE4_PROGRESS.md`, and `PHASE4_ROADMAP.md` before continuing.

Non-negotiables: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` repository is out of scope; PAPER mode mandatory; live broker writes disabled; no main update or PR merge; don't promote charge estimates or aggregate APIs into per-fill actuals; no real Oracle restore or credentialed live smoke test claimed.

## Updated handover — Upstox-first data integration (30 October 2026)

User's standing direction: work smarter, not like a donkey. Use Upstox Developer Console, current official API docs, supported APIs, official SDKs and schemas/proto when they solve the problem. Audit existing code first. Do not add workaround layers or duplicate infrastructure before checking provider-supported capabilities. Any workaround needs a concrete reason and tests. Stale-data checks are safety nets, not the primary freshness solution.

Latest verified prior code head: c8704cf97af3b2a31cd19114ae56f51dd796b08; Backend CI #41013144850 passed on that head. New instruction/docs are not yet CI-verified.

Audit finding and next task: upstox_market_data_streamer.py already implements the V3 WebSocket/protobuf/reconnect path; adapter.py has V3 quote/historical-candle methods; candle_parsing.py still calls itself BEST-EFFORT; strategy execution fetches candles independently and does not yet consume a shared streaming/candle service. Verify official response contracts, then wire the existing V3 stream and REST warm-up/gap-recovery into a shared candle pipeline without changing the strategy's five-minute semantics. Test ordering, timestamps, instrument identity, disconnect/recovery and incomplete candles. Check SDK compatibility before adding dependencies; don't install an SDK just for appearances.

Official references: https://upstox.com/developer/api-documentation/v3/get-market-data-feed/ ; https://upstox.com/developer/api-documentation/v3/get-intra-day-candle-data/ ; https://upstox.com/developer/api-documentation/installing-sdk/.

Safeguards: only tarunsharma2610-del/tradepro-improved; original Tradepro is out of scope; PR #8 Draft/unmerged; no main update; PAPER mandatory; live broker writes disabled.

## Handover update — API-backed current-session candles (30 October 2026)

User directive remains: use official Upstox Developer Console/API/SDK/schema where useful, audit existing code, avoid workaround-first changes.

New code: optional BrokerAdapter.get_intraday_data; Upstox adapter calls the documented V3 intraday candle endpoint with encoded instrument key; strategy fetches historical and intraday V3 candles concurrently and merges timestamp-normalized records, preferring intraday on overlap. Exchange-local date boundaries use Asia/Kolkata. If either required source fails, strategy receives no candle set and holds rather than fabricating history. Added endpoint and source-merge tests.

Current head: d7c786fc164ed297df42f26493c994ceacd337a7. CI pending; last green run #41014529152 applies to earlier head 58e6674dab5c02f725f76401af358397fd47c161 only. Verify latest CI before claiming the current code is green.

Next task: check/fix CI, then audit worker process boundaries before wiring WebSocket stream. MarketDataStreamManager is in-process and cannot be assumed to be the same instance as the separate worker container. Consider streaming only for live LTP requirements; continue using V3 REST candles for five-minute indicators. SDK was reviewed but not added because no demonstrated benefit yet. No authenticated Upstox console/account test was performed.

Safeguards: work only in tarunsharma2610-del/tradepro-improved; PR #8 remains Draft/unmerged; no main update; PAPER-only; live broker writes disabled.

## Handover — timestamped Upstox full quotes (30 October 2026)

Prior exact head d2662b05d4910d9bf93e307fb08f10a1609405ee passed backend CI #41014929096 and migration CI #41014916708.

Added Full Market Quotes V3 because LTP V3 has no last-trade timestamp, while Full Market Quotes V3 includes instrument_token, last_price and last_trade_time. ExecutionService._get_ltp now prefers a fresh subscribed WebSocket tick and otherwise calls get_full_quote; REST quote is accepted only for the exact requested instrument, positive finite LTP, and last_trade_time no older than 15 seconds or more than 60 seconds in the future. Stale/missing quote rejects paper execution. Added endpoint and helper tests and updated execution/strategy fixtures.

Latest code head 65f8070e344eaa4cd8cb82c876732662d02cc3a3; exact-head CI queued/running, not yet green. API WebSocket registry remains process-local to API; worker is separate. Since worker paper fills already use REST fallback, don't add a Redis bridge or duplicate worker stream unless a measured requirement justifies it.

Official refs: https://upstox.com/developer/api-documentation/get-full-market-quote-v3/ ; https://upstox.com/developer/api-documentation/ltp-v3/
Safeguards unchanged: only tradepro-improved, PR #8 Draft/unmerged, main untouched, PAPER mandatory, live broker writes disabled.

## Handover — WebSocket timestamp integrity and CI correction (30 October 2026)

CI on earlier Full Market Quote V3 integration failed five existing assertions because the rejection text omitted "price"; invalid prices were already rejected. Corrected wording only in 90bb1f5bf9d43767043a653e68a55b374bf0c599.

Audited the streamer and fixed a substantive edge case: do not substitute packet currentTs for missing LTPC last-trade time (LTT). Packet receive time is not proof of a recent trade. Streamer now caches only finite positive LTP with positive exchange LTT; latest_tick validates exchange age and monotonic receive age. Added NaN/Infinity/missing-LTT tests. Current code head 4dd8420d4d787be049c956204e15bfdff9586f3e. CI #41015772900 running on this exact test head at handover; previous correction CI #41015671461 passed. Streamer code CI #41015756833 was still running. Check exact-head CI before claiming green.

Official docs: Full Market Quotes V3 https://upstox.com/developer/api-documentation/get-full-market-quote-v3/ ; Market Data Feed V3 https://upstox.com/developer/api-documentation/v3/get-market-data-feed/

## CI status correction — 30 October 2026

The exact code/test head 4dd8420d4d787be049c956204e15bfdff9586f3e passed Backend pytest (run #41015772900). WebSocket implementation head d7c74a20a4a46741123ebbf4809176e90199643c passed run #41015756833; wording-only correction head 90bb1f5bf9d43767043a653e68a55b374bf0c599 passed run #41015671461. Current synchronized docs head 2589db1e0a6446ea60d12a075d58ce43fa19ed93 is in CI run #41015946896; verify this exact head before calling the latest checkpoint green.

## Handover — 30 October 2026 (latest verified checkpoint)

Latest code/test head `3a74fbb788a63ca3b042ceec400dbc7a83f32571` passed exact-head Backend CI #41016468736: 1,240 passed, 1 warning. CI also passed broker-write boundary enforcement, SQLite and PostgreSQL 16 migration round-trips, and isolated synthetic PostgreSQL/document-volume restore drill.

Paper market execution uses Full Market Quotes V3 executable depth. BUY walks asks; SELL walks bids; the simulated fill is the quantity-weighted average for the requested quantity. Snapshot timestamp (not last_trade_time) determines book freshness; mismatched instrument, stale snapshot, invalid prices or insufficient depth rejects the order. Strategy fixtures were updated; obsolete LTPC-only stream monkeypatch removed.

Important next integration: official Upstox docs now distinguish standard daily access tokens from Analytics Tokens for market data and real-time streaming. Audit the existing broker token retrieval sites, add separately encrypted Analytics Token storage, route only supported market-data and stream APIs to it, and keep standard OAuth access token for account/trading scopes. Do not implement a fake refresh-token flow.

PR #8 remains Draft/unmerged; only `tarunsharma2610-del/tradepro-improved`; main and original Tradepro untouched; PAPER mandatory; live broker writes disabled.
 
## Upstox Analytics Token implementation — 30 October 2026

- Added separate encrypted `analytics_token_encrypted` and `analytics_token_expires_at` fields to per-user broker connections with migration `202610300031` (down revision `202610270030`).
- Added owner-scoped Settings API to save, inspect status and clear Analytics Token. Token is accepted from the user's Upstox Developer Apps > Analytics page; it is never returned, logged or included in API responses. Expiry is tracked as 365 days from local registration; confirm/renew against the Developer Console's actual expiry date.
- Analytics Token retrieval is independent of standard OAuth `is_connected` state and fails closed when missing/expired. Standard OAuth access-token path remains separate for operations not documented as Analytics Token eligible.
- Routed strategy historical/intraday candle fetch, paper market quote/charge estimation, queued paper limit-order quotes, and market WebSocket reconnects through Analytics Token. Broker order/trade ingestion continues to use standard OAuth until each endpoint's Analytics Token/static-IP eligibility is deliberately enabled.
- Analytics Token is read-only. It cannot place, modify or cancel orders. Live trading remains disabled; PAPER-only guard unchanged.
- Official docs: https://upstox.com/developer/api-documentation/analytics-token/ ; https://upstox.com/developer/api-documentation/announcements/analytics-token-static-ip/ ; https://upstox.com/developer/api-documentation/v3/get-market-data-feed/
- CI for this new implementation is pending. Do not mark it accepted until exact-head CI passes, including migration round-trip and token isolation tests.

## CI correction — 30 October 2026

- Latest implementation/test head: `083ab17a5150ea3be514438a16ea7c6c888c0be3`.
- Previous exact-head run #41017634485 had 1,242 passed and one test-only failure caused by SQLite returning a naive datetime in the expiry assertion. Corrected the test to normalize that value to UTC; production expiry checks already normalize it.
- Exact-head run #41017833952 is running. Acceptance remains pending until the exact head passes pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 migration round-trips, and synthetic restore drill.
- PAPER-only guard remains enforced; PR #8 remains Draft/unmerged; no main update; original Tradepro repository untouched.


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


## Phase 4 handover — 30 October 2026 (Redis publisher CI accepted)

Resume only in `tarunsharma2610-del/tradepro-improved`. Latest verified implementation head is `72b22a647f2b9a38ac7afc0aaee9547a67b16fcf`; Backend CI #41024607462 passed on this exact SHA: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41024607462. Draft PR #9 is open and targets `phase4/roadmap-progress-checkpoints`; do not merge. The Redis publisher and Upstox V3 callback wiring are implemented. Publisher uses per-user keys/channels, versioned TTL snapshots, freshness validation, and Pub/Sub notifications. Redis failures do not fall back to stale in-memory quotes. Next gate is docs exact-head CI, then independent Redis consumer with authoritative snapshot reads, user/schema/version/TTL/timestamp validation and reconnect recovery. Scanner and PAPER strategy integration are pending. PR #8/#9 stay Draft/unmerged; PAPER mandatory; live broker writes disabled; original Tradepro repo untouched.


## Phase 4 handover — Redis delivery checkpoint, 30 October 2026

Resume only in `tarunsharma2610-del/tradepro-improved`, branch `phase4/redis-market-data-publisher`, PR #9 Draft/unmerged. Latest verified code head `1c70e17a0ea54f8e8f219ae27d90aa46a02ea16e`; exact-head Backend CI #41026567279 passed: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41026567279. This includes backend pytest, broker-write safety, SQLite and PostgreSQL 16 migration round-trips, synthetic restore and evidence retention.

Redis 7 is now a CI service. Publisher version increment + snapshot + TTL + Pub/Sub notification are atomic via Lua. Real Redis integration tests cover tenant isolation, TTL, authoritative snapshot reads, consumer-instance restart recovery, and concurrent publishing. Earlier run #41026517896 failed only on a missing test import; fixed in the accepted head.

Next: implement bounded Redis reconnect/resubscription and recovery sweep after reconnect; test actual Redis server restart and independent OS processes. Only then integrate scanner and PAPER strategy. No scanner/strategy integration is currently claimed. PAPER mandatory; live broker writes disabled; PR #8/#9 Draft/unmerged; main untouched; original Tradepro untouched.


## Phase 4 handover — Redis version-counter lifecycle checkpoint, 30 October 2026

Resume only in `tarunsharma2610-del/tradepro-improved`, branch `phase4/redis-market-data-publisher`, PR #9 Draft/unmerged. Latest verified code head `3088e49cf24317f58f7e04a60d6cd54e065143b4`; exact-head Backend pytest CI #41031153316 passed: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41031153316.

The Redis publisher now keeps per-user/per-instrument version counters persistent while quote snapshots retain their TTL. A real Redis integration test verifies that after a snapshot is deleted/expired, the next publish increments the counter instead of resetting it. This resolves ordinary snapshot-expiry version regression. Redis process-restart recovery has its own test; do not claim independent OS-process delivery or full production readiness from it.

Next: audit consumer startup/reconnect snapshot recovery and worker lifecycle; add independent publisher/consumer OS-process tests; test multiple users/instruments under concurrency and restart. Then integrate scanner, then PAPER strategy. No scanner or strategy integration is currently claimed. PAPER mandatory; live broker writes disabled; PR #9 Draft/unmerged; main untouched; original Tradepro untouched.


## Phase 4 handover — Redis bounded epoch/version checkpoint, 30 October 2026

Resume only in `tarunsharma2610-del/tradepro-improved`, branch `phase4/redis-market-data-publisher`, PR #9 Draft/unmerged. Latest verified code head `7268edd6e7ddb7ef6d472799d1d0164b4210b135`; exact-head full Backend CI #41032764754 passed: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41032764754. This includes backend pytest, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document restore and evidence retention.

Redis publisher uses short-lived authoritative snapshots (15-second default) and bounded version-counter retention (24-hour default) with unique epochs. Lua atomically allocates epoch/version, writes snapshot and publishes notification. Counter expiry or Redis data loss creates a new epoch; consumer compares epoch plus version. Legacy integer counters are migrated on next publish.

Exact-head real Redis tests passed for snapshot TTL expiry, counter TTL expiry/new epoch, Pub/Sub disconnect recovery, Redis process restart, independent OS-process publisher/consumer delivery, two-user isolation and concurrent version ordering. Intermediate `85d8c30` failed because test fixtures lacked epoch fields; corrected in `cb52cb8`; final accepted head is `7268edd6e7ddb7ef6d472799d1d0164b4210b135`.

Important remaining gap: the consumer service is implemented and tested but `app/worker.py` does not yet run a managed Redis consumer registry. Strategy execution still uses its candle-based path. Next define durable user/instrument subscription discovery, implement worker lifecycle/dynamic subscriptions and test graceful shutdown/restart/load. Then integrate scanner, then PAPER strategy. No scanner/strategy Redis integration is currently claimed. PAPER mandatory; live broker writes disabled; PR #9 Draft/unmerged; main untouched; original Tradepro untouched.


## Phase 4 resume pointer — Upstox SDK/CAS audit (30 October 2026)

Resume from the Phase 4 branch phase4/redis-market-data-publisher. Exact-head CI #41036389075 passed on commit 2212be0e094bb41423193b4384b6c07511ff3d62. Durable subscription persistence/startup recovery code is in place; fixture fix is accepted. Official SDK comparison is documented in UPSTOX_SDK_COMPATIBILITY_AUDIT.md: do not add upstox-python-sdk dependency now because current async REST/WebSocket layers fit our architecture better; local V3 protobuf schema matches SDK 2.30.0. CAS field propagation is implemented in commit fe76751c54a720ffa5fcec7b4f3728b137447090 but its exact-head CI must pass before acceptance. Next: inspect/fix that CI, checkpoint green, then continue worker-managed Redis consumer lifecycle and only then scanner integration. PAPER mandatory; live broker writes disabled; PR #9 Draft/unmerged; original Tradepro untouched.


## PAUSED — next implementation plan to resume here (30 October 2026)

**Do not restart from an older checkpoint. Resume from the latest Phase 4 branch head and the sequence below.**

### Gate 0 — repair the current exact-head CI failure

- Latest code head: 0cd3e2273f831b9e7d4968899ef8fc6a5d14a59d.
- Workflow #41037359835 FAILED in pytest: 1,304 passed, 2 failed. Both failures are in tests/test_upstox_option_chain_api.py because the test FakeStreamer fixture does not define the newly exposed market_info attribute. Production parser/API work is not the failure identified by CI.
- On resume, inspect the FakeStreamer fixture and add a safe default market_info=None (and a focused assertion if appropriate). Do not weaken/remove the production market status field or its tests.
- Rerun full backend pytest, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic restore drill. Only checkpoint after all exact-head checks pass.

### Gate 1 — mixed feed-mode subscription implementation (next feature)

Borrow the useful design from official Upstox Python SDK v2.30.0, not its transport:

1. Replace the current one-mode-per-user stream assumption with a mode-indexed subscription registry for LTPC, full, option_greeks and full_d30 where officially supported.
2. Permit a user connection to carry different instruments in different feed modes concurrently, subject to current official Upstox limits.
3. Replay each mode's instrument set after every reconnect, using our own asyncio streamer and fresh token-provider call on reconnect.
4. Update durable subscription service/API reconciliation so subscribing, unsubscribing or changing one instrument's mode does not deactivate unrelated mode subscriptions.
5. Preserve user/broker ownership isolation, validate instrument keys and feed modes, and enforce per-mode plus combined connection limits from current official docs.
6. Restore mixed-mode desired subscriptions after API/worker restart.
7. Add tests for mixed modes, mode-specific changes, duplicate requests, limits, reconnect replay, token refresh, startup recovery, Redis delivery and tenant isolation.
8. Benchmark/verify against the official SDK's behaviour and record the comparison; do not add SDK dependency unless a separately proven benefit emerges.

### Gate 2 — only after mixed-mode tests and CI are green

- Integrate Redis quote consumers with the scanner's broad LTPC universe, selected full-depth instruments and selected option-Greeks contracts.
- Validate freshness, stream silence, mode correctness and missing-field behaviour at the scanner boundary.
- Keep PAPER mode mandatory and all live broker order writes disabled.

### Preserved architecture decision

Keep the existing async httpx/websockets adapter, application OAuth/token lifecycle, V3 protobuf decoder, Redis snapshot/version/epoch delivery, freshness validation and domain-level safeguards. Do not add upstox-python-sdk as a runtime dependency merely for parity; selectively borrow proven SDK capabilities. See UPSTOX_SDK_COMPATIBILITY_AUDIT.md.

### Safety and repository boundary

Work only in tarunsharma2610-del/tradepro-improved on phase4/redis-market-data-publisher. PR #9 remains Draft/unmerged. Do not modify tarunsharma2610-del/Tradepro. No live broker place/modify/cancel calls.


## Phase 4 update — 30 October 2026

- Latest verified code/test commit: `ef80d792c4d89abda1850b73f54f7b81bf16bbf7`.
- Exact-head Backend CI [#41057600440 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41057600440), including pytest, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, and synthetic restore/evidence checks.
- Feed-mode subscription persistence now replaces only the selected mode's desired instrument set; other modes remain active. Regression coverage added for independent `ltpc` and `full` subscriptions.
- CI failure #41057234551 was an outdated single-mode test expectation; corrected on the verified head.
- Next: implement and test mixed-mode V3 WebSocket subscribe/unsubscribe, reconnect replay, and Redis consumer lifecycle. Persistence tests do not yet prove end-to-end mixed-mode streaming.
- PR #9 remains Draft/unmerged. PAPER mode mandatory; live broker writes disabled; original `Tradepro` repository out of scope.


## Current handover — Phase 4 Redis consumer recovery — 30 October 2026

Resume from `phase4/redis-market-data-publisher` in `tarunsharma2610-del/tradepro-improved`, PR #9 Draft/unmerged.

- Latest code/test head: `a5e352bef2c78f27141b61bca5893fdfa0fd049a`; exact-head Backend CI #41061518847 is running. Do not mark accepted until it completes successfully.
- Prior head `f7c863977ed17a3d705b83db8dcc6b7ba421cccf` passed exact-head CI #41060945704.
- New regression tests cover Redis epoch rollover after volatile-data loss and idle Pub/Sub heartbeat. Redis consumer itself already performs authoritative snapshot recovery, resubscription, heartbeat and fail-closed freshness/tenant validation.
- Worker does not yet run Redis consumers. Current strategy worker still evaluates through candle path. Do not start scanner integration prematurely.
- Next: after CI passes, design worker consumer lifecycle with durable subscription discovery, a single-owner/lease mechanism (avoid duplicate listeners across worker replicas), graceful cancellation/shutdown and isolated failure handling. Then add integration tests and connect scanner/PAPER strategy.
- Preserve PAPER-only, live order writes disabled, no merge/deploy, and never modify `tarunsharma2610-del/Tradepro`.


## Current handover — verified Redis recovery checkpoint — 30 October 2026

Resume from `phase4/redis-market-data-publisher` in `tarunsharma2610-del/tradepro-improved`. Latest verified implementation head is `a5e352bef2c78f27141b61bca5893fdfa0fd049a`; exact-head Backend CI [#41061518847 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41061518847). Redis epoch rollover after volatile-data loss and idle Pub/Sub heartbeat regression tests passed. The fresh Upstox Analytics Token-on-reconnect test passed on prior exact head `f7c863977ed17a3d705b83db8dcc6b7ba421cccf` in CI #41060945704. Next work is worker-managed consumer lifecycle with durable subscription discovery, single-owner/lease coordination, cancellation and graceful shutdown. Do not connect scanner or PAPER strategy before this gate is accepted. PR #9 stays Draft/unmerged; PAPER mandatory; live writes disabled; original Tradepro untouched.
