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

## Deferred future work recorded — 26 October 2026

- Added [AI integration and Algory.app gap plan](docs/AI_INTEGRATION_ALGORY_GAP_PLAN.md) and linked it from `MASTER_ROADMAP.md` and `HANDOVER.md`.
- This is planning/documentation only; no AI integration or strategy engine changes were made. Phase 3 remains the active priority. Resume AI/Algory audit only after Phase 3 acceptance.
- Exact-head CI for these documentation commits must be checked before declaring the documentation checkpoint green.

---

## Historical checkpoint (superseded) — 26 October 2026 (GST per-fill allocation test CI passed)

- Repository: `tarunsharma2610-del/tradepro-improved`; branch: `phase3/durable-per-fill-charge-allocation`; PR #6 remains open/draft.
- Implementation/test commit: `162e804c448cafa332e3c9a18f72ca4213d238ea`; exact-head Backend CI [#40298202486 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40298202486).
- Added `test_gst_allocation_plan_uses_only_reviewed_invoice_component_total` in `backend/tests/test_broker_charge_canonical_allocation_plan.py`. Synthetic reviewed GST source total ₹58.91 allocates ₹19.64 and ₹39.27 across two explicitly reviewed fill weights, reconciling exactly. This proves deterministic allocation only; it does not verify an actual invoice, approve GST treatment, persist accounting, or promote the plan.
- This checkpoint supersedes older checkpoint statements for current status; historical entries are retained for audit history only.
- Next gate: product/segment-specific charge-component acceptance and GST source reconciliation. Add only tests justified by source-backed mapping and invoice/contract-note evidence. Unknown/null values remain unknown; do not tax trade notional or double-count IPFT already included in combined exchange charges. All tariff candidates remain `DRAFT`.
- On every implementation change, verify exact-head CI. After this documentation checkpoint commit, verify CI again on that exact documentation commit.
- Safety: PAPER mandatory; live broker order writes and automatic live-fill promotion disabled; PR #6 stays draft/unmerged absent explicit authorization; original `tarunsharma2610-del/Tradepro` untouched. Phase 3 remains IN PROGRESS.

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


## Phase 3 forward checkpoint — 25 October 2026

- Implementation now preserves additional documented Upstox source labels: `transaction_charges`, `clearing_charges`, `ipft`, `other_charges`, and `demat_transaction_charges`. These are evidence-intake vocabulary only and remain pending independent review.
- The allocation/source-component database constraints were expanded by migration `202610250019`; the API and regression tests cover intake. Live-fill accounting deliberately still requires exactly six reconciled components, so a separately reported IPFT or any extra component fails closed instead of being silently ignored or double-counted.
- Preserve the existing NSE/IPFT calculation: documented combined ₹307/crore versus ₹306.99 transaction + ₹0.01 IPFT yields the same ₹307 base and ₹55.26 GST at 18%. This arithmetic is already tested; it does not prove Upstox endpoint or contract-note field semantics.
- GST component composition remains product-, date- and invoice-dependent. No production tariff or API mapping is approved. Exact-head CI for the new code/migration/test changes is required before this checkpoint is called verified.
- PR #6 remains open/draft/unmerged; PAPER mode remains mandatory; live broker order writes and automatic generic quantity/notional allocation remain disabled. Work only in `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is out of scope.

## Upstox SDK/API repository audit — 24 October 2026

- Audited only `tarunsharma2610-del/tradepro-improved` before changing runtime code. The detailed capability and gap matrix is in [`docs/UPSTOX_SDK_API_REPOSITORY_AUDIT.md`](docs/UPSTOX_SDK_API_REPOSITORY_AUDIT.md).
- Existing integration uses async `httpx` REST calls, a custom V3 protobuf/WebSocket streamer, a read-only reconciliation client, and validated brokerage-estimate parsing. `backend/requirements.txt` does not currently include `upstox-python-sdk`.
- Decision: do not add an unused dependency or wholesale-rewrite working clients. Next task is an isolated, version-pinned SDK compatibility spike (first candidate: read-only Brokerage Details API), with no real credentials or live calls. Audit Agent Skill scripts as development-only material before use.
- Existing endpoint semantics remain guarded: brokerage calculator is estimate-only; segment/FY charge API is aggregate-only; neither is per-fill actual evidence. Tariff candidates remain DRAFT.
- PR #6 remains open/draft/unmerged; PAPER mode mandatory; live broker order writes disabled; original `Tradepro` repository untouched.
- The prior PR head `3533c129af7f9ed4c3d741463a326b5a01cc3282` had a successful backend workflow [#40116782403](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40116782403). This audit introduces documentation commits, so exact-head CI must be checked again before calling the new documentation head green.

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

## CI failure correction — 24 October 2026

- The first evidence-identity CI attempt passed the pytest suite and broker-write boundary guard but failed the SQLite Alembic upgrade/downgrade/re-upgrade step. The migration was corrected to use Alembic batch mode for adding/dropping the nullable evidence foreign key, column, and index on SQLite.
- Review also found a replay contract mismatch: replay comparisons required evidence identity even when a retry omitted evidence metadata, despite the existing comment saying retries need not resubmit it. Exact replay now accepts omitted evidence ID only when all other execution/charge details match; when an evidence ID is supplied, it must match. New promotions still require reviewed evidence.
- Added a regression test for exact replay without resubmitted evidence metadata. The distinct-evidence-ID conflict test remains in place.
- Latest exact-head CI after these fixes is pending; do not mark this gate green until pytest, SQLite/PostgreSQL 16 migration round-trips, and safety checks complete on the same SHA.
- PR #6 remains draft/unmerged; live broker order submission remains disabled. All work remains confined to `tradepro-improved`.

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

## Latest Phase 3 checkpoint — 23 October 2026

- Exact-head CI [39911091610](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39911091610) passed on code commit `e3eda03b36c616d9655c01f71cc96a2f407fe513`: **566 passed, 1 warning**.
- Added and verified a PostgreSQL concurrency regression test that races source-component ledger verification against promotion. It confirms verification observes a complete pending or fully reconciled ledger, and final rows share one deterministic reconciliation reference.
- Broker-write boundary guard, SQLite/PostgreSQL 16 migration checks, and synthetic restore drill passed. Synthetic restore evidence is not proof of actual Oracle Free Cloud recovery.
- Next: continue accounting idempotency/conflicting-replay review, then run CI on the latest documentation head. PR #6 stays draft/unmerged pending review and explicit user approval. Real Upstox contract note and real backup/restore acceptance remain deferred until user-provided evidence.
- Safety boundary: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` remains out of scope. Live broker writes remain disabled.

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
- **Latest code/test commit:** `e56bf4c66f74b875a3ba8fe388138a9d688dd1e2` adds failed-commit rollback coverage. Exact-head backend CI [run 39564568154](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39564568154) passed 471 tests, 1 warning, source guard and SQLite/PostgreSQL 16 reversible migrations. Documentation HEAD `adb69aeb05b70ba4fa9095fc73d9dea033d31eec` passed [run 39565251793](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39565251793).
- **Exact-commit backend CI:** [run 39561621808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39561621808) passed **470 tests, 1 warning**, the broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles. It includes lease-fence ownership/expiry tests, a high-volume batch-stop regression, and a PostgreSQL contention test proving an expired lease cannot be reclaimed while a fenced persistence transaction still holds the row lock.
- **Documentation checkpoint CI:** [run 39561881539](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39561881539) passed on documentation commit `292cad087bf0febad7793dcec164ebb5435726e8`; this follow-up synchronizes the closure wording and design note.
- **Frontend:** no frontend files changed in this Phase 2 patch. The latest verified frontend CI remains [run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474), which passed TypeScript and Next.js build on code/test commit `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`.
- **Previously completed Phase 2 protections:** atomic run/lease finalization; stale-owner protection; cancellation and interrupted-run recovery; inconsistent token/expiry rejection; five-record renewal checks; and incomplete-summary warnings for `WORKER_INTERRUPTED` and `LEASE_LOST`.
- **Newly completed lease-expiry audit:** every worker-owned reconciliation persistence operation (fill identity, review issue, order transition and fill-to-intent link) now obtains a current, unexpired lease fence immediately before the write. The lease row is locked through the repository's persistence transaction, so a competing claimant must wait until that transaction commits or rolls back. Lease loss fails closed before the next mutation.
- **Scope clarification:** Phase 2's defined engineering checks are verified; remaining live-account safety, central broker-write/preflight and live-accounting coordinator work is explicitly classified as Phase 3/Phase 4 in the dependency matrix. Keep Phase 3 blocked until the final documentation sync passes exact-head CI.
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

## Latest continuation — accounting commit-failure rollback test (2026-10-21)

- **Commit:** [e56bf4c66f74b875a3ba8fe388138a9d688dd1e2](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e56bf4c66f74b875a3ba8fe388138a9d688dd1e2).
- Added test_failed_commit_rolls_back_execution_and_live_position in backend/tests/test_live_fill_accounting_service.py. The regression injects a commit failure and checks no live execution/position survives rollback and the paper position is unchanged.
- **Superseded historical checkpoint:** code/test CI [39564568154](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39564568154) passed 471 tests, 1 warning, source guard and SQLite/PostgreSQL 16 migration checks; documentation HEAD `0bd502f83118799d5564e8fd5724d01e8dc975af` passed [39566324985](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39566324985). Current status is recorded at the top of this file.
- Phase 2 workflow boundary remains explicit: BrokerFillIdentity and manual BrokerTradeRecord stay separate. Safety-branch dependency decisions are recorded in SAFETY_BRANCH_PORT_MATRIX.md; Phase 3/Phase 4-only live-safety features are deferred, not wholesale-merged.
- **Historical status note — superseded:** the latest code/test checkpoint and its CI are recorded at the top of this file. The current documentation synchronization must pass its own exact-head CI before Phase 2 is formally closed.

# Tradepro Improved — Progress Tracker

Last updated: 2026-10-21
Repository: https://github.com/tarunsharma2610-del/tradepro-improved
Branch: `main`
Starting HEAD before this documentation step: `2cf83089070e064c61f3b75fcb6b663021cbf625`
- `PROJECT_INSTRUCTIONS.md` commit: `8d7d9d8257f852f3d26e0564be8b521b0fe75764`
- `PROGRESS.md` initial commit: `9986380d8f4ee8939718c858ea9ab925da3f65b1`

## Historical checkpoint — formerly marked Current state
- [x] Separate improved repository exists; original `Tradepro` repo is to remain untouched.
- [x] Existing project structure, README, audit report, live-trading safeguards, Upstox adapter and execution service inspected in this session.
- [x] Persistent project instructions and progress tracking are being added.
- [x] Existing audit reports 167 backend tests passing in a prior GitHub Actions run and frontend typecheck/build passing. These are reported historical CI results, not tests rerun in this session.
- [x] Existing paper MARKET and LIMIT paths are described as implemented; paper LIMIT matching/cancel tests are reported as passing in prior CI.
- [ ] Live trading is NOT ready: execution service currently constructs PAPER orders; live placement and broker reconciliation are incomplete. Do not enable.
- [x] Multi-segment instrument sync, snapshot-gated expiry/delisting reconciliation, and user-scoped Upstox V3 WebSocket client/routes implemented. Live instrument-master sync to disposable SQLite verified; live authenticated WebSocket session still needs account-level verification.
- [x] Manual per-portfolio risk settings and enforcement implemented for daily realized loss, estimated exposure, per-order value, open/pending positions, and daily order count. Latest test run is being checked.
- [ ] OAuth schema migration needs staging verification before deployment.

## Current phase
**Phase G in progress — manual portfolio controls, snapshot reconciliation, WebSocket streaming and live BOD verification implemented; final CI verification and docs are in progress.**
- Added `PROJECT_INSTRUCTIONS.md` with the mandatory workflow and safety rules (commit `8d7d9d8257f852f3d26e0564be8b521b0fe75764`).
- Added this `PROGRESS.md` tracker (commit `9986380d8f4ee8939718c858ea9ab925da3f65b1`).
- Inspected `backend/app/services/execution_service.py`, `backend/app/services/strategy_execution_service.py`, `backend/app/services/risk_engine.py`, `backend/app/core/config.py`, `backend/app/models/order.py`, `backend/app/brokers/upstox/adapter.py`, and relevant execution tests.
- Confirmed the execution service currently creates orders with `trading_mode="PAPER"`; live broker order placement is not wired into this service. This is a deliberate safety boundary, not something to bypass.
- Confirmed the risk engine currently covers strategy-specific realized daily loss only; portfolio-wide loss/exposure/order-frequency caps are not present in the inspected module.
- Confirmed the Upstox adapter explicitly returns incomplete/not-implemented results for instrument-master sync and WebSocket streaming.
- Added a requirements-to-code/test gap map to `AUDIT_REPORT.md` (commit `ed0d18a0f03a45274ced3a4f237fbcca74f8ac2e`). It maps paper/live isolation, idempotency, risk limits, kill-switch scope, instrument sync, streaming, and migration verification.
- Corrected `README.md` so it no longer incorrectly lists the existing automated-entry kill switch as wholly unimplemented; it now distinguishes that switch from a global live-account kill switch (commit `611d5edbf476bc56682bb8af86ff8c216a38097e`).
- Confirmed the backend CI workflow run for the preceding documentation commit succeeded: [run 39036087413](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39036087413). This is documentation-change CI, not new application-code test coverage.
- Added `test_paper_market_order_never_calls_broker_live_order_endpoint` in `backend/tests/test_execution_service.py` (commit `07afe398ec85dffd00969355bb9362e9848f81ad`). It asserts the simulated order is `PAPER`, fills as expected using a mocked quote, and never awaits the broker's real `place_order` method.
- GitHub Actions backend workflow passed for that test commit, including the full pytest suite and SQLite Alembic migration verification: [run 39036217193](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39036217193). The Actions job is green; no live broker orders were submitted.
- Audit documentation commits: `ed0d18a0f03a45274ced3a4f237fbcca74f8ac2e` and `8940872208ca851f8ee27b4087aaa0e1445a8ae6`; README clarification commits: `611d5edbf476bc56682bb8af86ff8c216a38097e` and `ca35809b97f3eb970a94b61f4395b7036f2aa0ae`.
- Verified official Upstox documentation confirms the BOD instrument master is available as gzip-compressed JSON and recommends `instrument_key`; the current `InstrumentService` already syncs NSE_EQ only, while the adapter-level method remains a stub. See https://upstox.com/developer/api-documentation/instruments/.
- Updated the stale `InstrumentService` module docstring to reflect the actual scope (commit `3d28863309a224977764593688eb32a6161f13ff`).
- Refined `AUDIT_REPORT.md` after tests passed, recording the CI run and clarifying the existing sync is partial rather than wholly missing (commit `b9b8976482ac8b80cb3c39c8e448688b0c898769`).
- Added `backend/tests/test_instrument_service.py` with mocked successful gzip/JSON sync (NSE_EQ imported, NSE_FO ignored) and HTTP-failure/no-write coverage (commit `9f0e15ff274ce0b8aa3faa74aaa2427c2da750b0`). Backend CI passed including the full pytest suite and SQLite migration verification: [run 39036316771](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39036316771).

## Prior audit / CI evidence
See `AUDIT_REPORT.md` and `LIVE_TRADING_SAFEGUARDS.md`. Audit report links to a prior backend CI run (167 passed, 1 deprecation warning) and reports frontend typecheck/build success. Treat these as prior reported results unless verified again through current Actions.

## Rules for updating this file
After each coherent step, update this tracker with:
1. What changed and why.
2. Exact files changed.
3. Test commands/workflows actually executed and results.
4. Commit SHA and CI status when confirmed.
5. Any failures or unverified assumptions.
6. The next single action.

## Workstream continuation — 2026-10-17

### 1. Expiry and delisting management
- instrument_service.py derives snapshot keys from the official BOD master, checks for at least 1,000 valid normalized instruments (or at least 90% of the current active supported catalog, whichever is greater), and requires all major NSE/BSE/MCX segments before reconciliation.
- Unknown upstream instrument types still count as present keys, preventing false delisting when Upstox adds a new type. Missing keys and expired futures/options are reconciled in the same transaction as batch upsert only after the completeness gate passes. Failed or incomplete snapshots leave the existing catalog unchanged.
- instrument_repository.py reconciles snapshot absence and expiry atomically with the upsert.
- Added regression tests for deactivation of missing/expired contracts and protection against incomplete snapshots.

### 2. Upstox WebSocket market data
- Added official Upstox V3 protobuf schema and generated decoder under backend/app/brokers/upstox/proto/, plus the streamer and per-user manager services.
- Added authenticated endpoints: POST /api/v1/market-data/stream, GET /api/v1/market-data/stream, and DELETE /api/v1/market-data/stream. Start requires a connected Upstox OAuth session and active catalog keys. Portfolio UI now has Start/Stop controls and polls for fresh selected-instrument LTP.
- The client obtains a fresh one-time authorized WebSocket URL per reconnect, validates the Upstox host, keeps TLS verification enabled, sends the V3 binary subscription message, decodes protobuf frames, uses library ping/pong, reconnects with exponential backoff, and rejects stale exchange/receive timestamps.
- ExecutionService prefers a fresh subscribed WebSocket quote and falls back to authenticated REST LTP if the stream has no fresh quote. A stale stream tick is never used for a fill.
- Added mocked tests for protobuf decoding, stale data, stream configuration, fresh-stream preference and REST fallback. A real authenticated WebSocket connection has not been tested because no user's live OAuth token/session is available. Streams are in-process and ephemeral; multi-worker deployment needs shared stream state/cache.

### 3. Real instrument-master operational verification
- Added backend/scripts/verify_upstox_instrument_master.py and .github/workflows/upstox-live-verification.yml. The workflow downloads the real official Upstox BOD gzip JSON and syncs it into a disposable in-memory SQLite database; it never connects to the configured application database.
- Live verification succeeded in workflow run 39037390129: 123,930 active instruments imported and segment coverage validated. Counts: BCD_FO 10,422; BSE_EQ 13,096; BSE_FO 5,180; BSE_INDEX 79; MCX_FO 15,601; NCD_FO 8,644; NSE_COM 22,585; NSE_EQ 9,832; NSE_FO 38,352; NSE_INDEX 139. This is a real upstream download plus temporary-database sync, not a production sync.
- Verification link: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037390129

### 4. Manual portfolio management and risk controls
- Added six portfolio columns through migration 202610170001_portfolio_risk_controls.py: enable flag, max daily realized loss, max estimated open exposure, max order value, max open/pending positions and max orders per day. Limits remain disabled by default for existing portfolios.
- Added PortfolioRiskSettings validation, owner-scoped PATCH /api/v1/portfolios/{portfolio_id}/risk-settings and a portfolio UI form for manual rename/configuration. Starting capital/cash ledger is deliberately not editable after trading begins, to avoid rewriting historical accounting.
- Added portfolio_risk_service.py and wired checks into market-order submission, limit-order submission and limit fills. Pending limit-order exposure is included; reducing orders that close an existing position are allowed through risk caps so users are not trapped in positions. Exposure is estimated from position cost and pending limit notional, not exchange margin or live liquidation exposure.
- Added schema and order-risk regression tests. The migration passed clean SQLite Alembic verification in CI.

### Files changed in this workstream
- Backend: portfolio model/schema/API, portfolio risk service, execution service, instrument service/repository, WebSocket streamer/manager/API/schema, Upstox protobuf schema/decoder, main lifecycle, migration, verification script and requirements.
- Frontend: API client PATCH support and portfolio settings UI.
- Tests: instrument snapshot reconciliation, portfolio risk schema/order limits, WebSocket protobuf/stale handling and stream quote selection.
- Docs/workflows: README, audit report, project instructions, progress tracker and live master verification workflow.

### Current limitations / safety boundaries
- No production application database was written and no production migration was run.
- No real order was submitted. Live order placement/reconciliation is still unimplemented; TRADING_MODE=LIVE must not be enabled.
- The WebSocket code has mocked transport/decoder tests, but no live authenticated stream test; the manager is process-local and ephemeral.
- Exposure uses cost-basis estimates, not broker margin, greeks-based risk, or mark-to-market P&L. Daily loss cap is based on realized P&L only.
- OAuth schema migration needs backup-safe staging verification before deployment.

## Latest continuation step — portfolio position-cap regression test
- Inspected the current `PROJECT_INSTRUCTIONS.md`, `PROGRESS.md`, `README.md`, `AUDIT_REPORT.md`, current `main` tree and recent GitHub Actions before editing.
- Added `test_portfolio_open_position_cap_rejects_new_instrument` in `backend/tests/test_execution_service.py`. It proves a manually configured max-open-position cap rejects a new instrument when an existing position already occupies the cap; no real broker order is submitted.
- Commit: `3a518d8f7605ab066297b37dc18f4df4d225259c`.
- Backend CI passed: **195 tests passed, 1 warning**; SQLite Alembic migration verification passed. Workflow: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39039143042.

## Latest continuation step — exact-instrument quote safety
- Audited `_extract_ltp` in `backend/app/services/execution_service.py`. The old fallback scanned unrelated response entries when the requested key was absent, risking use of a different instrument's LTP.
- Removed the arbitrary-entry fallback; quote parsing now returns no price unless the exact requested `instrument_key` has a valid positive finite `last_price`.
- Added `test_quote_parser_uses_only_the_requested_instrument_key` in `backend/tests/test_execution_service.py`, covering both exact-key acceptance and wrong-key rejection.
- Code commit: `8bddac0ae09e43d91b3da990dc7a014f6721c325`; regression-test commit: `7403739c5a1f97aaed84e145958f9aa05f2f3f61`.
- CI passed: **196 tests passed, 1 warning**; SQLite Alembic migration verification passed. Workflow: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39039234333.

## Latest continuation step — daily order-count risk cap
- Added `test_portfolio_daily_order_cap_rejects_additional_order` in `backend/tests/test_execution_service.py`. It verifies cancelled orders do not consume the daily allowance, the first active order is accepted, and the next order is rejected at the configured cap.
- Commit: `167d67fdb953f0b75991e3e809062c845733b877`.
- Backend CI passed: **197 tests passed, 1 warning**; SQLite Alembic migration verification passed. Workflow: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39039335585.
- The exact-instrument quote safety change and max-open-position cap test are also recorded above; live trading remains disabled.

## Latest continuation step — WebSocket silence/reconnect regression
- Added `test_stream_reconnects_after_silence_timeout` to `backend/tests/test_upstox_market_data_streamer.py`, using a mocked socket and token provider. It verifies that a silent feed causes the client to reconnect and that the stream is marked disconnected after stopping.
- Commit: `ff417ec7ea3ed326c93d7c11703da07a18e2eb05`.
- Backend CI passed: **198 tests passed, 1 warning**; SQLite Alembic migration verification passed. Workflow: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39039414286.
- Live OAuth streaming still requires the user's authenticated session; no live account or order was used.

## Latest continuation step — WebSocket authorization URL validation
- Added parameterized tests in `backend/tests/test_upstox_market_data_streamer.py` proving authorization URLs are rejected when they use plain HTTP, an unrelated host, or a deceptive `upstox.com.evil.example` hostname.
- Commit: `c67c13ca30c4c2add6acab58633503f157b72420`.
- Backend CI passed: **201 tests passed, 1 warning**; SQLite Alembic migration verification passed. Workflow: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39039490249.
- Previous tested stream step: silence timeout triggers reconnect, while stream status returns disconnected after stop (commit `ff417ec7ea3ed326c93d7c11703da07a18e2eb05`, 198-test CI run).

## Latest continuation step — snapshot completeness regression
- Added `test_incomplete_snapshot_never_deactivates_existing_catalog` in `backend/tests/test_instrument_service.py`. A syntactically valid but incomplete master omitting required segments must fail before upsert/reconciliation, leaving the existing active catalog unchanged.
- Commit: `50bcca84080b771e65d8c727965d00745455ad6f`.
- Backend CI passed: **202 tests passed, 1 warning**; SQLite Alembic migration verification passed. Workflow: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39039577808.
- Cross-checked the stream auth/subscription implementation against official Upstox V3 docs: current auth endpoint is the V3 market-data authorize route; it returns a one-time `authorized_redirect_uri`; subscription is a binary V3 message; LTPC supports up to 5,000 keys on a single-category connection; and ping/pong heartbeats are expected. The current implementation uses `Accept: application/json`, binary subscription frames, and the official protobuf format. References: https://upstox.com/developer/api-documentation/get-market-data-feed-authorize-v3/ and https://upstox.com/developer/api-documentation/v3/get-market-data-feed/.

## Latest continuation step — official-format V3 authorization success path
- Added `test_authorization_accepts_official_upstox_v3_url_and_headers` to `backend/tests/test_upstox_market_data_streamer.py`. It checks that a valid `wss://xyz.upstox.com/...` URL is accepted and the official V3 authorize endpoint receives `Authorization: Bearer ...` and `Accept: application/json`.
- Commit: `da65b64aed2e733761db5c1659f6cb4c8ea93ac6`.
- Backend CI passed: **203 tests passed, 1 warning**; SQLite Alembic migration verification passed. Workflow: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39039645511.
- Official docs checked: V3 auth endpoint/one-time URL, binary subscription payload, LTPC subscription limit, protobuf feed, and ping/pong heartbeat. No discrepancy was found in the reviewed path. Real account streaming is still unverified.

## Next action
Review the live-order idempotency/reconciliation gap and write a safe implementation plan before any live-order code. Live order placement remains intentionally unimplemented; do not connect it to the paper execution service or submit real orders. Frontend TypeScript and production build passed for stream-control UI commit 6ec32fefda4ba357bde0fc5997cd32d6b58b4979: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037642093. The live instrument-master workflow passed with 123,930 active instruments in temporary SQLite: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037390129. Keep live trading disabled.


## Checkpoint — 2026-10-17 (verified against latest default-branch CI)
- Re-read `PROJECT_INSTRUCTIONS.md`, `PROGRESS.md`, `README.md` and `AUDIT_REPORT.md`. This checkpoint reconciles older audit text with the latest verified state.
- Latest CI after documentation changes: [39039714203](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39039714203) — **203 passed, 1 warning**; clean SQLite Alembic migration chain reached `202610170001` (manually configurable portfolio risk controls).
- Regression coverage already on `main`: portfolio daily order cap, incomplete instrument-master snapshot rejection, WebSocket silence reconnect, authorization URL allow/deny checks, and official-format V3 authorization success path. Do not duplicate tests without inspecting current files.
- Upstream instrument-master verification previously passed in disposable in-memory SQLite: **123,930 active instruments**; workflow [39037390129](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037390129). This is not a production sync.
- Frontend TypeScript/build passed for stream-control UI: [39037642093](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037642093). Stream manager is process-local; deploy one API worker until shared state is implemented.
- Still unverified: real OAuth-authenticated WebSocket; backup-safe staging migration against the actual deployed DB; multi-worker stream sharing; and live order workflow. Live order placement remains unimplemented and disabled.
- README refreshed in commit `92d328f5f16ac1df114f06249dc645165524fc11`; audit refreshed in commit `128bbf4265012acbde32e06b69af118ebdafed6f`. The latest documentation commit's CI run [39040259560](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39040259560) was still in progress at checkpoint time; do not claim it passed until completed.
- **Next step:** inspect broker adapter, order model, audit trail and execution service; write a design for idempotency keys, uncertain-submit handling and broker reconciliation before coding. Preserve paper/live isolation; do not submit live orders.


## Latest continuation — durable live-order idempotency/reconciliation design (2026-10-17)
- Re-read `PROJECT_INSTRUCTIONS.md`, `PROGRESS.md`, `README.md`, `AUDIT_REPORT.md`, `ARCHITECTURE.md`, `LIVE_TRADING_SAFEGUARDS.md`, order/execution models, order repository, execution service, broker interface, Upstox adapter and execution tests.
- Confirmed current boundary: `ExecutionService.place_order()` still constructs PAPER orders; no complete live orchestration, durable idempotency key, submit-attempt ledger, broker-fill dedupe identity or reconciliation workflow exists. The adapter methods alone do not make live trading safe.
- Created `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` as a design-only plan (commit `f74386a99722d761bcd23848f442cb754dd0e231`). It specifies additive intent/event/outbox/fill identity records, key+payload-hash semantics, uncertain-submit behavior, no blind retries, broker reconciliation, partial-fill dedupe, cancellation races, risk recheck, kill switch, migration gates, implementation phases and a regression-test matrix.
- Reviewed official Upstox documentation for Place Order V2/V3, Order History, Order Book, Order Details and Order Trades. A broker `tag` is treated as correlation/search, NOT as guaranteed broker-enforced idempotency. Sources are linked in the design file.
- No application code changed, no migration ran, no live broker session was used, and no orders were submitted. Tests were not rerun because this step only adds design documentation.
- Current phase: design review; implementation is deliberately not started.
- Next action: cross-link the reviewed design and correct status/roadmap language in `ARCHITECTURE.md`, `LIVE_TRADING_SAFEGUARDS.md`, `README.md`, `AUDIT_REPORT.md` and this progress tracker. Keep live submission disabled.


### Cross-document update — 2026-10-17
- Added the design-only document and cross-linked the safety boundary across architecture, safeguards, README, audit and persistent instructions.
- Commits:
  - Design: `f74386a99722d761bcd23848f442cb754dd0e231`
  - Progress checkpoint: `23038aec23be3ea84f5f7b311b58b07a7a20e79e`
  - Architecture: `dca8482b9f3959ed4708955aed25b1129e6d8673`
  - Live safeguards: `0543eb7fce6aa874bd565764ed89768c0b1c5146`
  - README: `230ff457e61136b249edaed435c9b3b9ef11a320`
  - Audit: `412f02f1864896bca8eba6239083e20aebefefcb`
  - Persistent instructions: `9b6133132d11aec17fa63d409ee476aceaaeb34c`
- Documentation CI verified green for design [run](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39040603270), progress [run](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39040613801), architecture [run](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39040622827), safeguards [run](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39040633919) and README [run](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39040640928). Audit run 39040650847 and instruction run 39040662516 were still in progress at the latest check; the newest progress commit CI is queued. Do not claim the entire series is green until those complete.
- This was documentation/design only; no application tests were rerun locally, no code/migration was added, and no broker order was submitted.
- Verified cross-links and design-only safety status in `ARCHITECTURE.md`, `LIVE_TRADING_SAFEGUARDS.md`, `README.md`, `AUDIT_REPORT.md` and `PROJECT_INSTRUCTIONS.md` against current default-branch contents.
- **Next action:** verify the remaining audit/instruction/progress CI runs, then pause at the design-review gate for user approval before Phase 1 schema/repository implementation.


## Repository completeness and roadmap checkpoint — 2026-10-17
- Rechecked the default `main` tree after the prior continuation. All seven live-order design/status documents exist: `PROJECT_INSTRUCTIONS.md`, `PROGRESS.md`, `README.md`, `AUDIT_REPORT.md`, `ARCHITECTURE.md`, `LIVE_TRADING_SAFEGUARDS.md`, `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`. No separate roadmap file existed, so added `ROADMAP.md` and linked it from README, architecture, audit and persistent instructions.
- Confirmed prior progress commit `3263eda9d1329d17069dd4140162602631639a0b` CI succeeded: [run 39040715054](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39040715054).
- New roadmap commit: `3024aed473f28409bd075ec7e764576890c4ecfa`.
- Cross-links/status commits: README `748a20b227c8f55d4c75276b36fa00c5f5075569`; instructions `25b4e39e6636ef527785dccdd7e627fe0a991447`; architecture `a6fd111534681e18392df6e9be6d1c09b9deb6f2`; audit `914d9d12f5872d3061770461b110dff1cf98cd29`.
- This is documentation/roadmap only. No live-order code, migration, or real broker order was executed. Each new commit's CI must be checked independently; do not use the previous green workflow as proof for later commits.
- Next: verify the newest branch tip and CI for every commit in this documentation series, ensure the final progress update itself is committed and green, and inspect final file links. Then pause for design approval before any schema/code implementation.

## Latest continuation — final documentation CI verified — 2026-10-17
- Re-read the persistent instructions, current progress tracker, README, audit, architecture, safeguards, live-order design and roadmap; checked the current `main` tree and relevant order/execution model and repository files.
- Confirmed `main` currently points to `5c288b7796083c6de8e210cd9e49a7e95daac72f` (`docs: record roadmap addition and repository completeness audit`).
- Verified GitHub Actions for that exact HEAD completed successfully: [workflow 39041041406](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39041041406). The preceding roadmap, README, instructions, architecture and audit documentation commits also have successful individual CI runs (39040992954, 39041003884, 39041013848, 39041020582, 39041026871). These are documentation CI runs, not new application-code tests.
- Cross-checked the design against current source: `Order` has no durable live-intent/idempotency/submit-attempt fields; `Execution` has no broker-fill identity uniqueness; `OrderRepository` commits ordinary create/save operations; the shared execution service remains PAPER-only. This supports the documented blocker rather than just assuming it.
- No source code or migration was changed, no local tests were run, no production/staging database was touched and no broker order was submitted.
- **Current gate remains Gate 0 — design review.** Per the persistent project instructions and roadmap, do not start Phase 1 schema/repository code until the user explicitly acknowledges/accepts the design review and that acknowledgement is recorded here. Live submission remains disabled.
- **Next action:** obtain explicit approval of `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` as the implementation design; then record that approval and begin Phase 1 with additive durable records and concurrency/transaction tests only (no broker POST).


## User design approval and Phase 1 start — 2026-10-17
- **Explicit approval recorded:** the user approved `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` for implementation and directed that changes be committed to this repository, with roadmap/audit and other required documents updated.
- Gate 0 design-acceptance requirement is satisfied. This approval authorizes Phase 1 durable records and repository safeguards only; it is **not** authorization to enable or submit real broker orders.
- Phase 1 scope: additive durable live-order intent, append-only event, transactional outbox and broker-fill identity records; uniqueness constraints; same-key/same-payload reuse and same-key/different-payload conflict; focused tests. Keep the existing PAPER execution path isolated and do not call broker order placement.
- Current verified base commit before implementation: `03dce02de8777fe02aa7cc8da485f118b9403a50`; its backend CI passed: [run 39041376889](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39041376889).
- Implementation status at start: no Phase 1 source changes or migration have been committed yet. Do not report completion until source, migration and tests are committed and the exact final commit's CI is checked.
- Next action: add the additive SQLAlchemy records and Alembic migration, register models, then implement repository idempotency transaction behavior and focused tests.


## Phase 1 implementation checkpoint — 2026-10-17 (latest status supersedes earlier gate notes)

### Approval and scope
- The user explicitly approved `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`; Gate 0 is complete. This is approval to implement durable records/repository safeguards, **not** approval to enable live order submission.
- Work is on `main` in `tradepro-improved` only. The original `Tradepro` repository remains untouched.

### Implemented and committed
- `backend/app/models/live_order_records.py`: durable `LiveOrderIntent`, `LiveOrderEvent`, `LiveOrderOutbox`, and `BrokerFillIdentity` models. Database constraints cover scoped client idempotency, broker order identity, one outbox row per intent, unique broker trade identity, nonnegative attempts and positive fill values.
- `backend/app/models/__init__.py`: registers the new models with SQLAlchemy metadata.
- `backend/alembic/versions/202610170002_live_order_durability.py`: additive migration after `202610170001`, with reversible table/index creation.
- `.github/workflows/backend-tests.yml`: CI now verifies a clean SQLite upgrade to head, downgrade to `202610170001`, and re-upgrade to head.
- `backend/app/repositories/live_order_repository.py`: validates authenticated-user ownership of both portfolio and broker connection; derives SHA-256 from deterministic canonical JSON plus user/portfolio/connection scope; same key + same payload reuses the existing intent; same key + different payload raises `IdempotencyConflict`; persists intent, initial audit event and outbox row in one transaction; handles a unique-key race by rollback and winner lookup.
- `backend/tests/test_live_order_repository.py`: covers transactionally created records, duplicate reuse, payload conflict, ownership isolation, invalid key/non-finite payload rejection, duplicate broker-fill identity, audit ownership, rollback atomicity and deterministic independent-session winner recovery. True simultaneous multi-transaction contention remains unverified.
- Updated `ROADMAP.md`, `AUDIT_REPORT.md`, `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`, `ARCHITECTURE.md`, `LIVE_TRADING_SAFEGUARDS.md`, `README.md` and `PROJECT_INSTRUCTIONS.md` to record approval, current implementation boundary and evidence.

### Verification
- Latest application-code/test commit: `c098d1c23bd4d422e6d86c56e43c2c65e22d8ab4`.
- Exact application-code/test commit GitHub Actions: [run 39043589541](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39043589541) — **212 tests passed, 1 warning**.
- CI workflow commit `01212a5c2cd5e8d5fa916cb7fdfe285ce5cc150c` passed [run 39043763339](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39043763339), including clean SQLite migration upgrade → downgrade to `202610170001` → re-upgrade. This is not a staging or production DB verification.
- The intermediate canonical-hash API/test mismatch caused two red runs (39043143640 and 39043156888); the fixture was corrected and the later exact code checkpoint passed. Failures are not concealed.
- Latest evidence-document commits: roadmap `3a0908abdb9654206f44dff81faec2e2e34dd0cb`; audit `55e0fa86449b7aa4cfccad2c96c8d97bb86cc148`; README `1e5c464217bc4f53be8df649a5354fc8ae8c209b`; design `6c49ce3fe1f34ee17a520f1c211090f1fc89b478`. Architecture `d8f8fb9be71edc7f29fed9d31579a63654a7aea4`, safeguards `c1bc5babe0e1ba700fbb048b213d37c7f2d01f39`, and instructions `a23e84155f3cdd8faea135cddb4906cf03a4723f` also reflect the Phase 1 boundary. These documentation commits and this progress update's exact-commit CI must be checked independently.
- No broker order POST, cancellation, live reconciliation, production migration or real-money test was performed.

### Remaining Phase 1 gates
- Add true simultaneous multi-transaction contention coverage against the deployment database engine; current independent-session test deterministically simulates the competing commit and exercises winner recovery.
- Verify migration downgrade/upgrade and constraints on a backup-restored staging copy of the actual deployment database engine.
- Review append-only audit enforcement and safe-details redaction policy before any API exposes these records.
- No live-order API, dispatcher worker or reconciliation service is part of this phase. Keep live trading disabled.

**Next action:** check CI for the documentation commits and this progress update; then continue with the concurrent unique-key test and staging-engine migration review.


## Continued Phase 1 — credential-field persistence guard — 2026-10-17

### Change
- Added _validate_safe_json() in backend/app/repositories/live_order_repository.py. It recursively rejects credential-like key names in order snapshots and audit event details (including nested access/refresh tokens, secrets, passwords, API keys, authorization headers and cookies) and rejects non-finite/non-JSON-compatible data before database persistence.
- Added tests in backend/tests/test_live_order_repository.py for nested access-token rejection in order snapshots, nested Authorization-header rejection in audit details, and rejection of non-object audit details.
- This is defense-in-depth key-name validation, not a guarantee that arbitrary secret values are detected. Callers must continue to redact secrets. No API route, broker call, order submission or reconciliation workflow was added.

### Verification
- Combined code/test checkpoint: 5508b272efe55997252e8d8a51fdd29761a1070b.
- Exact GitHub Actions run [39047300286](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39047300286) succeeded: **214 passed, 1 warning**. Clean SQLite migration upgrade → downgrade to 202610170001 → re-upgrade also succeeded in the same workflow.
- Commits: repository guard 46f85a345dfff6a673ee19d3760191a07eff2f5b; tests 5508b272efe55997252e8d8a51fdd29761a1070b.
- Evidence/docs updated: roadmap f245e5d0402f06c72889bdd308e284cf2d21e523; audit 2c781f27734b8642f1861f505242f108b3c2a6c7; README 518f2ac606c7b2513aa62a5d18daa175a40e701f; design e9218829e814db1ab9c09358705fc1f48ea549b8; architecture e5889f7ab3765eac1cbf937f85aa0f28d24919a2; safeguards 0f36d6a095bd4b5c02253b9e68dab46b948feeb2. Each documentation commit's own CI still needs exact-commit verification.
- No production migration or real broker action occurred.

### Next single action
- Verify the documentation commits' CI, then add a concurrency test appropriate to the actual deployment database engine. The engine and staging access must be confirmed before claiming true simultaneous contention or production-engine migration verification.


## PostgreSQL contention integration — implementation committed, verification pending — 2026-10-17

- Added backend/tests/test_live_order_postgres_concurrency.py. When TEST_POSTGRES_URL is set, it creates an isolated test schema, synchronizes two independent PostgreSQL sessions after both miss the idempotency lookup, then asserts both requests return one intent ID and only one intent/outbox/event exists.
- Updated .github/workflows/backend-tests.yml to provision PostgreSQL 16, run the concurrency test, and test Alembic upgrade → downgrade to 202610170001 → re-upgrade on PostgreSQL as well as SQLite.
- Commits: integration test 84b12804538a931980d29b6847e655e2bebc59b1; CI configuration e79d6f3bc758bd0e868d4be795eeef865e7c8ee9.
- The test-only commit passed the SQLite-only workflow, but the PostgreSQL-enabled workflow [39047545900](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39047545900) is still in progress at container initialization. PostgreSQL concurrency and PostgreSQL migration results are **not yet verified**. Do not mark the gate complete until the exact workflow reports success.
- No production database or broker was contacted; this PostgreSQL service is disposable CI infrastructure only.

### Next action
Check workflow 39047545900. If the PostgreSQL service starts, resolve any concurrency-test or migration failures, then update this tracker with the exact successful run. If service initialization times out, inspect and adjust the CI service configuration before proceeding.


## PostgreSQL integration failure analysis and correction — 2026-10-17

- The first PostgreSQL-enabled CI run [39047545900](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39047545900) failed in the concurrency test setup: the test inserted the broker connection in the same flush as its user without an ORM relationship ordering guarantee, triggering a foreign-key violation.
- Corrected the test setup to commit the parent user first, then insert the portfolio and broker connection. Fix commit: dd36b48a92057ad50618f6f9941f908832c9cea3.
- Verification rerun: [39048147046](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048147046). Status must be checked before marking this resolved; PostgreSQL test and migration verification remain pending until that exact run succeeds.


## PostgreSQL concurrency + reversible migration verification — passed — 2026-10-17

- Exact code/test commit: `dd36b48a92057ad50618f6f9941f908832c9cea3`.
- Exact GitHub Actions run [39048147046](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048147046) succeeded: **215 passed, 1 warning**.
- The test starts two independent PostgreSQL sessions and synchronizes them after both initially miss the same idempotency key; it verifies both requests return the same intent ID and that exactly one intent, outbox row and initial audit event exist.
- In the same successful run, Alembic upgrade → downgrade to `202610170001` → re-upgrade passed on both clean SQLite and PostgreSQL 16.
- The first PostgreSQL run failed because the test setup inserted child rows without first committing the parent user. This was corrected in `dd36b48a92057ad50618f6f9941f908832c9cea3`; the rerun is green. The failed run remains visible in Actions history.
- CI configuration commit: `e79d6f3bc758bd0e868d4be795eeef865e7c8ee9`; concurrency test commit: `84b12804538a931980d29b6847e655e2bebc59b1`; test setup fix: `dd36b48a92057ad50618f6f9941f908832c9cea3`.
- Updated design, roadmap, audit, architecture, README and project instructions to match the verified state. Documentation commits: roadmap `9d661313adcb9bb75e558a257ab4569979e14652`; audit `63baafc4822e032e65ea871fea0b0c52fb3a8998`; design `849e4a4fcf18bf255b402cc00b156158188049db`; architecture `0285b2bd8890bf26feba690b3159702077d5c18c`; README `889312894a57cb1b9eb2705e5e8317be1059cad4`; instructions `a347a1e68b5db844df7f83d8677f79c03ff37844`.
- No real broker order was submitted and no production database was migrated.

### Current gate and next action
- Automated Phase 1 concurrency and reversible migration checks are complete for SQLite and PostgreSQL 16.
- Phase 1 remains open until schema/constraints are verified on a backup-restored staging copy of the actual deployment database engine, and broader crash/rollback/contention checks are reviewed.
- Next: verify CI for each documentation commit; then confirm the deployment database engine and safe staging access before claiming staging verification. Do not start broker submission. Phase 2 is reconciliation-only and must remain unable to submit orders.


## Documentation CI verification — all current Phase 1 updates green — 2026-10-17

Each updated Markdown file's exact commit has its own successful GitHub Actions run:
- ROADMAP.md commit `9d661313adcb9bb75e558a257ab4569979e14652`: [run 39048272612](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048272612) — success.
- AUDIT_REPORT.md commit `63baafc4822e032e65ea871fea0b0c52fb3a8998`: [run 39048279286](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048279286) — success.
- LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md commit `849e4a4fcf18bf255b402cc00b156158188049db`: [run 39048287427](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048287427) — success.
- ARCHITECTURE.md commit `0285b2bd8890bf26feba690b3159702077d5c18c`: [run 39048295538](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048295538) — success.
- README.md commit `889312894a57cb1b9eb2705e5e8317be1059cad4`: [run 39048303900](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048303900) — success.
- PROJECT_INSTRUCTIONS.md commit `a347a1e68b5db844df7f83d8677f79c03ff37844`: [run 39048311971](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048311971) — success.
- PROGRESS.md commit `a6deeafe078915955725953b2bc9f21d0f48e0bf`: [run 39048329434](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048329434) — success.
- LIVE_TRADING_SAFEGUARDS.md commit `437fb1446ecddfed72c6e9773d0d1f95258f7ba2`: [run 39048342181](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048342181) — success.

The latest verified application/test checkpoint remains `dd36b48a92057ad50618f6f9941f908832c9cea3` with [run 39048147046](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048147046): 215 passed, 1 warning, plus SQLite/PostgreSQL 16 reversible migration checks. This is separate from the documentation commits' own green CI runs.

Actual deployment database engine and access to a backup-restored staging copy are not established by repository CI. Phase 1 remains open until that environment is verified. No live broker submission, production migration or reconciliation worker was introduced.


## Phase 2 — conservative broker order normalization — 2026-10-17

- Added `backend/app/services/live_order_reconciliation.py`, a pure normalization module with no network, database, submit or cancel capability.
- Added `backend/tests/test_live_order_reconciliation.py` for documented Upstox order statuses, partial/full-fill consistency, unknown statuses, missing fields, invalid quantities/prices and the cancelled-order pending-quantity edge case.
- The normalizer preserves the broker's raw status, maps only known documented statuses, rejects malformed/inconsistent fields, and flags unknown or contradictory observations as `RECONCILIATION_REQUIRED` rather than guessing.
- Source contract references: [Upstox order book](https://upstox.com/developer/api-documentation/get-order-book/), [order details](https://upstox.com/developer/api-documentation/get-order-details/), [order history](https://upstox.com/developer/api-documentation/get-order-history/) and [order-status appendix](https://upstox.com/developer/api-documentation/appendix/order-status/). These APIs report current-day order records; durable local history and cross-session recovery remain future work.
- Exact test commit: `b37452210bf07ad03acee1495e0627fae1378582`; GitHub Actions [run 39049395091](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39049395091) passed **247 tests, 1 warning**, including SQLite/PostgreSQL 16 reversible migration checks.
- Earlier implementation-only commit `c5f0f937367b9d74610d8ddef2885da6b309fa48` also passed existing CI: [run 39049387990](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39049387990).
- This is a tested Phase 2 foundation, not a complete reconciliation worker. It does not fetch broker data, persist status transitions, link broker orders to intents, import fills, or place/cancel orders. Live trading remains disabled.
- Next step: add strict local-intent-to-broker-record matching and duplicate/ambiguous-match handling with tests; do not link an order based on tag alone or unknown/mismatched economics.


### Phase 2 documentation CI verification — 2026-10-17

All four documentation commits for the normalization foundation have their own successful CI runs:
- `PROGRESS.md` commit `75d72b7fbd3de3e6f352a3f68579ab82b152f250`: [run 39049553343](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39049553343) — success.
- `ROADMAP.md` commit `edf44ae22ca540b2406ee332b508ef595b3bdd1e`: [run 39049563456](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39049563456) — success.
- `AUDIT_REPORT.md` commit `4e922603a3157afd866de07d4ce4ce99d891e997`: [run 39049572086](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39049572086) — success.
- `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` commit `7647296f2c4244027e1382633d5982ab009a9cc5`: [run 39049581913](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39049581913) — success.

The latest application-code test checkpoint remains `b37452210bf07ad03acee1495e0627fae1378582`, verified by [run 39049395091](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39049395091): 247 passed, 1 warning, plus SQLite/PostgreSQL 16 migration checks. The current work is only a normalization foundation; matching, durable status updates, fill ingestion and any broker I/O remain future work.


## Phase 2 — strict broker-order-to-intent matching — 2026-10-17

- Re-read PROJECT_INSTRUCTIONS.md, PROGRESS.md, README.md, AUDIT_REPORT.md, ROADMAP.md, ARCHITECTURE.md, LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md and LIVE_TRADING_SAFEGUARDS.md before continuing. Confirmed the repository target is tradepro-improved; original Tradepro remains untouched.
- Consulted current official Upstox order book, order details, order history and per-order trades docs. The order book/history are current-trading-day data, so a missing result is not proof an uncertain order was never accepted. References: [order book](https://upstox.com/developer/api-documentation/get-order-book/), [order details](https://upstox.com/developer/api-documentation/get-order-details/), [order history](https://upstox.com/developer/api-documentation/get-order-history/), [trades by order](https://upstox.com/developer/api-documentation/get-trades-by-order/).
- Updated backend/app/services/live_order_reconciliation.py: normalized broker price and trigger_price; added ReconciliationIntentCandidate, IntentMatchResult, and pure match_broker_order_to_intent(). Candidates are scoped to the requested broker connection. Match uses existing broker order ID when known, otherwise an exact non-empty tag that identifies one candidate, then requires economic-field equality. Duplicate candidates, cross-connection candidates, missing local economic fields, mismatches and unknown/contradictory observations are not auto-linked.
- Updated backend/tests/test_live_order_reconciliation.py with focused matching/ambiguity/isolation tests. Exact test commit: e9b594ffc2e81c37e1b41c8c44947212d206f3e9; [GitHub Actions run 39050424898](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39050424898) passed 255 tests, 1 warning, and clean SQLite/PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks.
- Implementation commit: f0f46e4ab364d2a304a1e8d2d4aafd7cd77b8ebd; test commit: e9b594ffc2e81c37e1b41c8c44947212d206f3e9.
- Documentation updated in ROADMAP.md, ARCHITECTURE.md, AUDIT_REPORT.md, README.md, LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md, and PROJECT_INSTRUCTIONS.md; exact per-commit CI results are being verified.
- Limitations: matching is pure and not persisted; no broker reads, API route, worker, order submission/cancellation, fill ingestion, production migration, or real order was performed. Deployment/staging DB verification remains unavailable because the project is not deployed.
- Next single action: implement a repository-only status transition with allowed-transition rules, optimistic version checks and atomic audit events; no broker I/O.


## Phase 2 — versioned reconciliation state persistence — 2026-10-17

- Added repository-only LiveOrderRepository.apply_reconciliation_transition() in backend/app/repositories/live_order_repository.py. It validates allowed transitions, enforces authenticated-user ownership and expected-version/previous-state compare-and-set, optionally stores the unique broker order ID, and commits the state/version/last-reconciled timestamp and BROKER_STATUS_RECONCILED audit event atomically.
- Safe event details are validated against credential-like keys. Repeated same-state observations at the current version are no-ops. Invalid terminal regressions are rejected; CANCELLED → PARTIALLY_FILLED/FILLED is allowed to represent later broker trade evidence in a cancel/fill race. RECONCILIATION_REQUIRED remains frozen for manual resolution.
- Added tests for atomic state/event persistence, same-state idempotency, stale-version conflict, terminal regression rejection, cancel/fill race and secret-field rejection.
- Code checkpoint commit b3332b839b6f2c39bf2ae678e1aa62ac1f2a3409 passed [GitHub Actions run 39050941218](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39050941218): **261 passed, 1 warning**, and SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks passed.
- Intermediate CI failures were not hidden: run 39050728922 / 39050744745 failed on a malformed test import; run 39050840969 exposed an undefined previous-state variable. Both were corrected; exact final code checkpoint above is green.
- Updated ROADMAP.md (f4e22341829300c8613bf14ac6f4f4f89444a6cd; removed a duplicate Phase 2 checklist item), ARCHITECTURE.md (bfbc8a33bd792c8561c8dfb81c17025c3ad926ce), AUDIT_REPORT.md (db2a2a6335754150fbbf4f7c0234a297b2f05395), README.md (56cb32553696898268d55f71bc0b43da5ddbf6c0), LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md (4021f51377f0a025a706969bec2cca62689d5855), LIVE_TRADING_SAFEGUARDS.md (99016f1ae2349b5fa800bda65930d1c14ef7a280), and PROJECT_INSTRUCTIONS.md (1fbd12d35202f51a332dcf8369244bbc0c8f2b51). Verify the CI run for each exact documentation commit before declaring docs fully verified.
- No broker API reads, fill ingestion, live order submission/cancellation, production migration or real order occurred. The project is not deployed; staging DB verification remains outstanding.
- Next single action: implement pure validation for Upstox per-order trade records, then a transactionally idempotent fill-ingestion repository operation using the existing unique broker-connection + broker-trade-ID constraint. Do not add broker API calls yet.


### Phase 2 documentation CI verification — 2026-10-17
The exact documentation commits for versioned reconciliation persistence have successful GitHub Actions runs:
- ROADMAP.md a25a9c4c4c50c6adc8eb7a2b997f241667e2cf79: [run 39051061693](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39051061693) — success.
- ARCHITECTURE.md bfbc8a33bd792c8561c8dfb81c17025c3ad926ce: [run 39051073011](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39051073011) — success.
- AUDIT_REPORT.md db2a2a6335754150fbbf4f7c0234a297b2f05395: [run 39051083433](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39051083433) — success.
- README.md 56cb32553696898268d55f71bc0b43da5ddbf6c0: [run 39051100719](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39051100719) — success.
- LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md 4021f51377f0a025a706969bec2cca62689d5855: [run 39051113701](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39051113701) — success.
- LIVE_TRADING_SAFEGUARDS.md 99016f1ae2349b5fa800bda65930d1c14ef7a280: [run 39051121157](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39051121157) — success.
- PROJECT_INSTRUCTIONS.md 1fbd12d35202f51a332dcf8369244bbc0c8f2b51: [run 39051130597](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39051130597) — success.
- Prior PROGRESS.md checkpoint 9b52357889ac335326173b1300009e8c7c94dd9f: [run 39051148864](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39051148864) — success.

The latest application-code checkpoint remains b3332b839b6f2c39bf2ae678e1aa62ac1f2a3409, [run 39050941218](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39050941218): 261 passed, 1 warning, and SQLite/PostgreSQL 16 migration checks passed. Documentation CI is separate from this application-code verification.

- Final roadmap cleanup commit f4e22341829300c8613bf14ac6f4f4f89444a6cd removes a duplicate fill-ingestion checklist line; roadmap cleanup CI passed [run 39051273827](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39051273827).


## Phase 2 — validated trade normalization and idempotent fill identity persistence — 2026-10-17

- Re-read `PROJECT_INSTRUCTIONS.md`, `ROADMAP.md`, `ARCHITECTURE.md`, `PROGRESS.md`, `AUDIT_REPORT.md`, `README.md`, `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` and `LIVE_TRADING_SAFEGUARDS.md` before implementation. Target remains `tradepro-improved`; original `Tradepro` was not modified.
- Consulted the official [Upstox Get Order Trades API](https://upstox.com/developer/api-documentation/get-trades-by-order/). Added `normalize_upstox_trade()` in `backend/app/services/live_order_reconciliation.py` to validate trade/order IDs, instrument, BUY/SELL, positive integer quantity, finite positive price, and exchange timestamp converted to UTC. It performs no network calls.
- Added `LiveOrderRepository.record_broker_fill()` in `backend/app/repositories/live_order_repository.py`. It scopes writes to an authenticated user's broker connection and optional intent in the same connection; stores individual trade identities under the existing unique `(broker_connection_id, broker_trade_id)` constraint; treats identical replays as no-ops; raises `LiveOrderVersionConflict` for reused IDs with changed payloads; and atomically commits a linked `BROKER_FILL_RECORDED` event. It rejects credential-like metadata keys. It does not update positions, cash, P&L, shared `Order`/`Execution`, or fetch broker data.
- Added normalization tests in `backend/tests/test_live_order_reconciliation.py` and repository tests in `backend/tests/test_live_order_repository.py` covering valid documented timestamp, malformed fields, idempotent replay, changed-payload conflict, connection isolation and credential rejection.
- One initial repository test run failed because the isolation test attempted two Upstox connections for one user, conflicting with the existing unique `(user_id, broker)` constraint. Changed the test's second connection to a distinct broker type; exact final code/test commit `001a6eed2bd7090e2c7a4d3a8f2f87e9d7fa62bc` passed [GitHub Actions run 39052203329](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052203329): **274 passed, 1 warning**, with SQLite/PostgreSQL 16 reversible migration checks.
- Code commits: normalizer `fe884209c8ba3474e7b00577c0ed17c5d7b3f796`; fill repository `9a8be276621afa9cd3bf0b39cf7b7197c78c878b`; normalizer tests `f27bd848c79d8fba33f0618b10d6df3c271292a8`; fill tests `efe0fa54610a6248cc281ca29b62a2dcfbf7ecbd`; corrected isolation test `001a6eed2bd7090e2c7a4d3a8f2f87e9d7fa62bc`.
- Documentation commits: `ROADMAP.md` fc34c20dfafb5adb0ced51a945233e8f644c9100; `ARCHITECTURE.md` 9afe7f552252a8e041d6bf52c805bb71fdbad5e2; `AUDIT_REPORT.md` 939e81b8a1acbef090ac0e81afe5c78f572a28a6; `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` 16718a9c977da1685957da213b055dcbf7a8d7fa; `README.md` fae2b9dbd5a6f7ed2c5a6a6de257d7045943ff75; `LIVE_TRADING_SAFEGUARDS.md` 188083da2ab4ddc7f7619834a7985d5ee9546dcb; `PROJECT_INSTRUCTIONS.md` 4c32f49f35434aeab2b2499ba47e7b0de35254ea. Exact documentation CI runs are being verified and will be recorded below.
- Remaining Phase 2 work: validate each normalized fill against the matched immutable intent snapshot, aggregate partial fills and reconcile out-of-order observations; then build a read-only broker reconciliation worker only after API/error/session contracts are tested. No broker API calls, order submission/cancellation, production migration or real order occurred. App is not deployed; staging DB verification remains outstanding.
- Next single action: implement fill-vs-intent economic validation before `record_broker_fill()` can accept a linked fill, with mismatch/quarantine tests. Keep live submission disabled.


### Phase 2 fill-persistence documentation CI verification — 2026-10-17
All documentation commits for the fill-identity checkpoint have successful GitHub Actions runs:
- `ROADMAP.md` fc34c20dfafb5adb0ced51a945233e8f644c9100: [run 39052328938](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052328938) — success.
- `ARCHITECTURE.md` 9afe7f552252a8e041d6bf52c805bb71fdbad5e2: [run 39052351579](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052351579) — success.
- `AUDIT_REPORT.md` 939e81b8a1acbef090ac0e81afe5c78f572a28a6: [run 39052366324](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052366324) — success.
- `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` 16718a9c977da1685957da213b055dcbf7a8d7fa: [run 39052382345](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052382345) — success.
- `README.md` fae2b9dbd5a6f7ed2c5a6a6de257d7045943ff75: [run 39052403682](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052403682) — success.
- `LIVE_TRADING_SAFEGUARDS.md` 188083da2ab4ddc7f7619834a7985d5ee9546dcb: [run 39052416578](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052416578) — success.
- `PROJECT_INSTRUCTIONS.md` 4c32f49f35434aeab2b2499ba47e7b0de35254ea: [run 39052428182](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052428182) — success.
- `PROGRESS.md` checkpoint 29eac681a6d93a83f05262c60f7eb4163b505c8c: [run 39052450839](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052450839) — success.

The exact final code/test checkpoint remains [run 39052203329](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052203329): **274 passed, 1 warning**, with SQLite/PostgreSQL 16 migration checks. The intermediate failure at run 39052095678 is documented above and was fixed before the passing checkpoint.


## Phase 2 — fill-to-intent economic validation — 2026-10-17

- Continued from the previous checkpoint and added pre-persistence checks in `LiveOrderRepository.record_broker_fill()`: the linked intent must already reference the same broker order ID; instrument, side, product and order type must match the immutable order snapshot; requested quantity must be a valid positive integer; each fill and aggregate persisted fills cannot exceed order quantity; BUY LIMIT/SL fills cannot exceed limit price and SELL LIMIT/SL fills cannot be below it.
- Added tests for mismatched instrument, missing broker-order link, aggregate partial-fill overrun and BUY/SELL limit-price violations.
- Final code/test commit `b69939ece8edc47e1ae05f27c0d9e2144e87db04` passed [GitHub Actions run 39052939770](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052939770): **279 passed, 1 warning**, and SQLite/PostgreSQL 16 reversible migration checks passed. Earlier CI runs in this step caught fixtures with invalid prices and missing new method arguments; fixtures were corrected before the green checkpoint.
- Documentation commits: `ROADMAP.md` cc919b11844b584518f74f7fda0793443f68b9ab; `ARCHITECTURE.md` eee0b6a08f4052a40f7dc17e2f8c3440775f4179; `AUDIT_REPORT.md` 262b7c49cd3e80a9a353ff898d8474a722c81b66; `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` d893483cc29e8e943ab2ba8191ada0139daaf9ef; `README.md` e0e5c92d0ac19c117aca982537c0ba44c84c4335; `LIVE_TRADING_SAFEGUARDS.md` 6ee838b3ffd09cc241f989b980b412e52d2fed89; `PROJECT_INSTRUCTIONS.md` b5b3c3bdb0c8cdbfd5287e651d52df31a4e762de. Exact CI results for these documentation commits are being checked.
- Important limitation: the code persists validated individual fill identities only. It does not fetch broker trades, quarantine/relink unmatched fills, reconcile out-of-order observations, or update the shared `Order`, `Execution`, `Position`, cash or P&L models. Live submission remains unavailable and disabled.
- Next single action: design and test safe handling for unmatched fills and out-of-order status/fill observations before implementing any broker-read worker.


### Phase 2 fill-economic-validation documentation CI verification — 2026-10-17
- `ROADMAP.md` cc919b11844b584518f74f7fda0793443f68b9ab: [run 39053082665](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053082665) — success.
- `ARCHITECTURE.md` eee0b6a08f4052a40f7dc17e2f8c3440775f4179: [run 39053098480](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053098480) — success.
- `AUDIT_REPORT.md` 262b7c49cd3e80a9a353ff898d8474a722c81b66: [run 39053112774](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053112774) — success.
- `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` d893483cc29e8e943ab2ba8191ada0139daaf9ef: [run 39053125136](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053125136) — success.
- `README.md` e0e5c92d0ac19c117aca982537c0ba44c84c4335: [run 39053145371](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053145371) — success.
- `LIVE_TRADING_SAFEGUARDS.md` 6ee838b3ffd09cc241f989b980b412e52d2fed89: [run 39053158840](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053158840) — success.
- `PROJECT_INSTRUCTIONS.md` b5b3c3bdb0c8cdbfd5287e651d52df31a4e762de: [run 39053172125](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053172125) — success.
- `PROGRESS.md` checkpoint e2e06037696e1f608a76610a521e0c0f41f26b2a: [run 39053194020](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053194020) — success.

Exact fill economic validation code/test checkpoint remains [run 39052939770](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052939770): **279 passed, 1 warning**, SQLite/PostgreSQL 16 migration checks passed. This documentation verification does not imply live broker integration or production readiness.


## Phase 2 — safe relinking of previously unmatched fills — 2026-10-17

- Added `LiveOrderRepository.link_existing_fill_to_intent()` so an individual fill can be safely recorded while intent matching is unresolved, then linked later after the intent's broker order ID is known. It revalidates user/connection scope, exact broker order ID, instrument, side, product, order type, requested quantity, limit-price protection and aggregate quantity ceiling.
- Linking uses conditional update on `intent_id IS NULL`; repeat linking to the same intent is a no-op, conflicting links and economic mismatches are rejected, and the link plus `BROKER_FILL_LINKED` audit event commit atomically. Adjusted duplicate delivery semantics so a replay without an intent remains idempotent even if that fill has since been safely linked.
- Added tests for successful late linking, repeat-link no-op/no duplicate audit and economic mismatch rejection. Exact test commit `66802c2eae7adaddb8f1213c9c9a689e4190acaf` passed [GitHub Actions run 39053352921](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053352921): **281 passed, 1 warning**, plus SQLite/PostgreSQL 16 migration checks.
- Documentation commits: `ROADMAP.md` 92724a8bc0685a5e1c2659adc884f52ec3547464; `ARCHITECTURE.md` 70f2d4cb8102092430131fa81bee877cbcd3e169; `AUDIT_REPORT.md` c3f16e80beed1ea7ce2d3e226f80e13676152b63; `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` 4130229c5b9f0d5d13ed00e0f18d71c0837d06eb; `README.md` e0b1bcda069fa2267f3d27817c8c1595f39c3ef0; `LIVE_TRADING_SAFEGUARDS.md` 98a49a064cbde8f916183923f9dbcc17774cb0dc; `PROJECT_INSTRUCTIONS.md` 5488ef3baba3187b6945b87265a63562b430325a. Exact documentation CI runs are being verified.
- Remaining Phase 2 work: broker status/fill out-of-order reconciliation, actual broker read worker with session/expiry/error handling, and applying reconciled fills to shared accounting models. No broker API call, real order, production migration or live accounting occurred.
- Next single action: add explicit tests and state rules for out-of-order broker status after fill evidence, then design a read-only reconciliation worker. Live submission remains disabled.


### Phase 2 unmatched-fill documentation CI verification — 2026-10-17
- `ROADMAP.md` 92724a8bc0685a5e1c2659adc884f52ec3547464: [run 39053474931](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053474931) — success.
- `ARCHITECTURE.md` 70f2d4cb8102092430131fa81bee877cbcd3e169: [run 39053488827](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053488827) — success.
- `AUDIT_REPORT.md` c3f16e80beed1ea7ce2d3e226f80e13676152b63: [run 39053502737](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053502737) — success.
- `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` 4130229c5b9f0d5d13ed00e0f18d71c0837d06eb: [run 39053515056](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053515056) — success.
- `README.md` e0b1bcda069fa2267f3d27817c8c1595f39c3ef0: [run 39053533797](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053533797) — success.
- `LIVE_TRADING_SAFEGUARDS.md` 98a49a064cbde8f916183923f9dbcc17774cb0dc: [run 39053545257](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053545257) — success.
- `PROJECT_INSTRUCTIONS.md` 5488ef3baba3187b6945b87265a63562b430325a: [run 39053678487](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053678487) — success.
- `PROGRESS.md` checkpoint e97cb3112612946d8a08f5d9618645026df66343: [run 39053579681](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053579681) — success.

The verified code checkpoint for unmatched fill relinking remains [run 39053352921](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053352921): 281 passed, 1 warning, with SQLite/PostgreSQL 16 migration checks.


### Final checkpoint — 2026-10-17
- Latest documentation-verification commit `c11c80d1c5cb0835fbcd59ebe6d0cd153ed97539` passed [GitHub Actions run 39053681082](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053681082).
- Latest implementation test evidence for safe unmatched-fill linking: [run 39053352921](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053352921), 281 passed, 1 warning; SQLite/PostgreSQL 16 migrations passed. Latest fill-to-intent economic validation: [run 39052939770](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052939770), 279 passed, 1 warning.
- All seven documentation commits for the unmatched-fill relinking checkpoint have successful exact-commit CI runs. No production deploy, database migration, broker API call, live order or live accounting occurred.
- Next implementation step remains explicit out-of-order status/fill reconciliation rules and tests, then design a read-only broker reconciliation worker with session expiry, rate-limit/backoff, and current-trading-day limitations before adding any broker reads.


## Phase 2 — out-of-order status/fill reconciliation — 2026-10-17

- Re-read `PROJECT_INSTRUCTIONS.md`, `PROGRESS.md`, `README.md`, `ROADMAP.md`, `ARCHITECTURE.md`, `AUDIT_REPORT.md`, `LIVE_TRADING_SAFEGUARDS.md` and `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` before making this step.
- Added pure `resolve_order_state_with_fill_evidence()` to `backend/app/services/live_order_reconciliation.py`; it resolves stale broker status against persisted deduplicated trade quantity and fails closed on contradictions.
- Wired the resolver into `LiveOrderRepository.apply_reconciliation_transition()` before same-state no-op logic. Audit records preserve observed broker state, resolved state, persisted fill quantity and reason.
- State rules: full requested fill quantity resolves to `FILLED`; partial fill plus stale active status resolves to `PARTIALLY_FILLED`; partial fill plus cancellation resolves to `PARTIALLY_FILLED_CANCELLED`; partial fill conflicting with `FILLED`/`REJECTED`, invalid quantity totals or overfill resolves to `RECONCILIATION_REQUIRED`.
- Added parameterized resolver tests and repository regression tests for stale OPEN after a partial fill, partial fill then cancel, and full persisted fill against stale cancellation.
- Exact code/test commit `59f562b62ef6af25ea3a5c6f15cab8a32d505da3` passed [GitHub Actions run 39056392873](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056392873): **294 passed, 1 warning**; SQLite/PostgreSQL 16 reversible migration checks passed.
- One earlier test run failed because it selected the wrong audit event when event timestamps tied at database precision. The assertion was made deterministic by selecting the event using its resolved state; the exact checkpoint above passed.
- Added design-only [READ_ONLY_RECONCILIATION_WORKER_DESIGN.md](READ_ONLY_RECONCILIATION_WORKER_DESIGN.md), commit `7fb6c86e837636a41d25a79610246ab711eab295`. It specifies a read-only client boundary, user/connection scoping, token and rate-limit handling, idempotent fills, safe audit, and failure recovery. No worker or broker reads are implemented yet.
- Updated docs: `ROADMAP.md` `e205cca474ba8263dc0b91ee156ea8dd06cd0bbc`; `ARCHITECTURE.md` `a5c411e3b3b88dac54348d3b9dea3bbf964d5694`; `AUDIT_REPORT.md` `59c02811698d24e634ea6024c0c1eb540643bc3f`; `README.md` `dd9450b77d2e16441d3765b2bd6189552805a12a`; `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` `5c6bd1f93e3b7fdaafee1bc83120467e455289d4`; `LIVE_TRADING_SAFEGUARDS.md` `311db585ed102db53778bd7f4634bca89f05ca73`; `PROJECT_INSTRUCTIONS.md` `5a2f42b5ccee2f5020c198748a8c2b4457350e02`. Exact documentation CI runs must be checked before calling this fully verified.
- No real Upstox API reads, order submission/cancellation, production migration or local portfolio accounting updates occurred. App remains undeployed; staging verification is still pending.
- Next step: implement a narrow read-only Upstox client/worker against official GET-only endpoints and mocked contract fixtures, with token-expiry, 403, 429/Retry-After, bounded 5xx retry, pagination, lease contention and repeated-run tests. Do not inject the full write-capable execution adapter; keep live submission disabled.


## Phase 2 — GET-only Upstox client boundary — 2026-10-17

- Added `backend/app/brokers/upstox/reconciliation_client.py` with fixed GET-only methods for order book, order details, order history (by order ID or tag), and per-order trades. It intentionally exposes no place/modify/cancel methods.
- The client returns sanitized error categories for missing token, 401, 403, 429, other 4xx, 5xx, timeout, network failure and non-JSON responses. It does not return raw error bodies or exception text.
- Added `backend/tests/test_upstox_reconciliation_client.py` contract tests for official endpoint paths/parameters, missing-token short-circuit, sanitized HTTP/network failures, and absence of write methods.
- Exact test commit `10d9938d17c4c67649c5a4b9c305684ff8f36e52` passed [GitHub Actions run 39056868434](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056868434): **309 passed, 1 warning**, plus SQLite/PostgreSQL 16 reversible migration checks. Tests use a mocked HTTP client; no Upstox request was made.
- Added [READ_ONLY_RECONCILIATION_WORKER_DESIGN.md](READ_ONLY_RECONCILIATION_WORKER_DESIGN.md) and updated roadmap, architecture, audit, README, reconciliation design, safeguards and project instructions. The exact docs CI runs for the previous out-of-order checkpoint passed: roadmap [39056606410](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056606410), architecture [39056618397](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056618397), audit [39056630473](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056630473), README [39056642292](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056642292), reconciliation design [39056653110](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056653110), safeguards [39056663764](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056663764), instructions [39056675913](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056675913), progress [39056709672](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056709672), worker design [39056552758](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056552758). All reported success.
- Latest remaining docs commits for the client boundary are: roadmap `59d7351fe91d34a17c860ad64ac6fea75a85b2df`; architecture `925e7f00ae56ce18037a2acc09858fac500cdabe`; audit `b0ff85bc6133ab61724e4ca99669ae1a41781f6c`; README `a1681218e43b55e36885a95af9b0db26430233ca`; reconciliation design `e91241dbf910279fa70c555fb74a4884917a36de`; safeguards `6f65fcdf68e81db1e433eaa8f3658014605d802b`; instructions `61dbece6164e0a8e5799a840e00fb524bf6781aa`; worker design `14625c1c2d7532263c4955e39e14eff2d2498671`. Their exact CI runs are being checked.
- Next implementation action: implement the worker orchestrator with user/connection ownership checks, token expiry checks, bounded retries and lease/concurrency controls. It must use this narrow GET-only client, never the general write-capable adapter. No broker polling, real order, production migration or accounting update has happened.


## Phase 2 — leased read-only reconciliation worker and failure-path tests — 2026-10-17

### Read instructions and current repo first
- Read `PROJECT_INSTRUCTIONS.md`, `PROGRESS.md`, `README.md`, `ROADMAP.md`, `ARCHITECTURE.md`, `AUDIT_REPORT.md`, `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`, `LIVE_TRADING_SAFEGUARDS.md` and `READ_ONLY_RECONCILIATION_WORKER_DESIGN.md`; inspected the current `main` tree, worker/client/repository/model/test code and latest GitHub Actions before editing.

### Implementation already on main and verified
- Worker commit [`4ee8427f890f7c31021e30f7b36177e2f3f227c3`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/4ee8427f890f7c31021e30f7b36177e2f3f227c3): `backend/app/services/live_order_reconciliation_worker.py`. It uses only the fixed GET-only client, validates user-owned Upstox connection and usable token, claims/renews/completes the durable lease, performs bounded retry for read-only transient errors, reads order book + daily trades, normalizes trades/orders, strictly matches intents, persists unmatched fills then links only after repository economic checks, and reconciles state against persisted trade evidence. No schedule/API route is wired.
- PostgreSQL concurrency test commit [`bf0c2b707aaa023a961f899502ed9f2ae4d265a4`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/bf0c2b707aaa023a961f899502ed9f2ae4d265a4) verifies two simultaneous lease claims allow only one lease owner.
- This continuation added `test_worker_does_not_retry_forbidden_response`, `test_worker_bounds_server_error_retries_before_any_mutation`, and parametrized malformed envelope/data cases in `backend/tests/test_live_order_reconciliation_worker.py` (commit [`bffeefc7921fd96c8fbeab1b201eb3088e87f497`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/bffeefc7921fd96c8fbeab1b201eb3088e87f497)). The tests prove 403 is not retried, 503 retries are bounded, malformed order-book envelopes fail before fill/status writes, and the intent remains unchanged.
- Exact latest code/test run [39058734080](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39058734080) passed **338 tests, 1 warning**; SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed.

### Documentation commits from this continuation
- `ROADMAP.md`: `ce41b45047ecfb0a2de1a1101c6be380013b67bc`
- `READ_ONLY_RECONCILIATION_WORKER_DESIGN.md`: `4af221c79f2d55818a820617521048855f613af2`
- `ARCHITECTURE.md`: `46f27dfb503c9eed64f7039ea0dafbe656d06c60`
- `AUDIT_REPORT.md`: `b62252599168d2f6eb91eed900851285d7fa13a1`
- `README.md`: `b729eb4e11605867dd23ce144ceab009159990b0`
- `LIVE_TRADING_SAFEGUARDS.md`: `69a3388db68b6fe7098bbf7ed56277d0eca06f59`
- `PROJECT_INSTRUCTIONS.md`: `2da55ce235d03c14eeca0aeec90d4d415db18ae1`
- `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`: documented in a separate commit during this continuation; verify the exact SHA and its CI result before calling all docs verified.

### Explicit limitations / what did not happen
- The worker is an on-demand Python service, not scheduled and not exposed by an API route. Tests use mocks. No real Upstox request, live order submission/modification/cancellation, production migration, or local Order/Execution/Position/cash/P&L update occurred.
- Current run reads order book and daily trades; historical-day/session pagination semantics are not implemented/verified. There is no durable operator-facing run-summary/manual-review queue yet. CI passing does not equal staging/production verification.
- Earlier worker implementation CI attempts had failures during iterative development; fixes were made in later commits. The latest exact run cited above is green; earlier failures remain visible in Actions.

### Next single action
Review official Upstox current-day trade/order-book response and history/window semantics; then add persistent, credential-safe reconciliation run summaries/manual-review visibility and crash-boundary tests. Keep live submission disabled and do not add any broker write method to the worker.


### Durable run-summary documentation verification — 2026-10-17
The eight-file documentation bundle commit [`091eab31cbc93b29b88118b61693c5fc4f763da2`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/091eab31cbc93b29b88118b61693c5fc4f763da2) updated `ROADMAP.md`, `ARCHITECTURE.md`, `AUDIT_REPORT.md`, `README.md`, `PROJECT_INSTRUCTIONS.md`, `LIVE_TRADING_SAFEGUARDS.md`, `READ_ONLY_RECONCILIATION_WORKER_DESIGN.md`, and `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`. Its exact workflow [39059521781](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059521781) passed **340 tests, 1 warning**, plus SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks. Earlier worker documentation commits also passed their own CI runs: roadmap 39058899956, worker design 39058934654, architecture 39058945827, audit 39058984056, README 39058992933, safeguards 39059003264 and instructions 39059012444. The current next implementation action is durable manual-review issue records with deduplication and safe detail fields; no UI/API exposure until separately reviewed.


### Manual-review issue queue documentation checkpoint — 2026-10-17
- Updated docs commit [`45dd099ddfda5107ec3502fbe5cb1fedbfce02d3`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/45dd099ddfda5107ec3502fbe5cb1fedbfce02d3) updated `ROADMAP.md`, `ARCHITECTURE.md`, `AUDIT_REPORT.md`, and `README.md`.
- Updated docs commit [`5ff6cad81664ed5827b5050a0021dc3a0c462209`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/5ff6cad81664ed5827b5050a0021dc3a0c462209) updated `PROJECT_INSTRUCTIONS.md`, `LIVE_TRADING_SAFEGUARDS.md`, `READ_ONLY_RECONCILIATION_WORKER_DESIGN.md`, and `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`.
- These docs describe the verified code checkpoint [`71b5668533f0461c12374319e496665cbda7e61c`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/71b5668533f0461c12374319e496665cbda7e61c), which passed [run 39059749652](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059749652): **342 passed, 1 warning**, plus SQLite/PostgreSQL 16 reversible migration checks. Exact CI for these two newest documentation commits is being verified separately.
- Current status: durable run summaries and deduplicated issue records are stored in the database; no operator-facing issue API/UI exists. The worker is not scheduled and remains GET-only. No live order actions, production migration or local accounting updates occurred.
- Next single action: implement authenticated read-only listing endpoints for reconciliation runs and issues, with strict current-user and broker-connection scoping, sanitized response schemas and cross-user isolation tests. Do not add issue-resolution mutation yet.


## Phase 2 — owner-scoped reconciliation read API — 2026-10-17

- Added `backend/app/api/v1/reconciliation.py` with authenticated read-only `GET /api/v1/reconciliation/runs` and `GET /api/v1/reconciliation/issues`; added Pydantic response schemas, `LiveReconciliationQueryRepository`, and mounted the router in `backend/app/api/v1/router.py`.
- Every query filters by current authenticated `user_id`; optional broker-connection/status/type filters and bounded limit (1–100) are supported. Schemas expose safe run counters and issue metadata/details only, not raw broker payloads or credentials. No route starts a worker or mutates an issue/order.
- Added `backend/tests/test_api_reconciliation_isolation.py`: unauthenticated requests rejected, owner sees only own run/issues, another user's connection filter returns an empty list, status/limit validation works, and response does not expose token fields.
- Exact code commit [`f65b4ba20ce9a1dacfe40580d8042cd98f36c19f`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/f65b4ba20ce9a1dacfe40580d8042cd98f36c19f) passed [run 39060230705](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39060230705): **345 passed, 1 warning**, plus SQLite/PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks.
- Documentation commit [`81b27463ca3709e8669a1f7c233128bf439646f0`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/81b27463ca3709e8669a1f7c233128bf439646f0) updated roadmap, architecture, audit and README. Documentation commit [`4a0c64294714a5ea951c195ca9878838d28b5e3d`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/4a0c64294714a5ea951c195ca9878838d28b5e3d) updated project instructions, safeguards, worker design and live-order design. Exact docs CI is being checked.
- Remaining: frontend review UI; separately authorized issue-resolution workflow; stale `RUNNING` recovery and crash/restart tests; official historical trade retrieval/pagination; no real read-only sandbox test yet. No live order action, production migration or accounting update occurred.
- Next single action: verify the latest documentation CI, then add frontend screens to view run history/open review issues without exposing secrets or enabling issue mutations.


## Reference-repository audit checkpoint — 2026-10-20

- Audited the current `tradepro-improved` tree and recent commits, plus relevant source/docs/tests/licences for four references: [AI Trading Platform](https://github.com/afnanadil2007-design/AI-Trading-Platform), [Algo Options Platform](https://github.com/iamadarsha/algo-options-platform), [OpenAlgo](https://github.com/marketcalls/openalgo), and [Kite Algo Bot](https://github.com/KoshIndia/kite-algo-bot).
- Added [REFERENCE_REPOSITORY_AUDIT.md](REFERENCE_REPOSITORY_AUDIT.md) with overlap, useful patterns, licence constraints, prioritized integration ideas and verification limitations. No external code was copied and no application code/schema was changed by the audit.
- **Historical blocker (resolved at code/test checkpoint `a906274`):** run 39113589752 failed collection because live-fill accounting dependencies were absent. The missing models and migration revisions have now been added; run 39475387511 passed 355 tests and SQLite/PostgreSQL 16 reversible migration checks. See the recovery checkpoint below.
- The protected original repository `tarunsharma2610-del/Tradepro` was read only; no write action was made against it. All audit documentation changes are confined to `tradepro-improved`.
- No live broker request/order, production migration, or production-data write was performed.
- **Temporary rollback on 2026-10-20, then recovery:** the three incomplete live-fill accounting files were removed to investigate a CI collection/migration-chain blocker, but the user requested restoration. All three original file contents have now been recovered from their pre-deletion Git blobs and restored to their original paths on `main` in commits `8c7fef18f7e23b31e072df7cc1b70a8c85f4ae44`, `bdbc1fb24f9c64a916c7a0fe7a012875e258265e`, and `28af2b521e8e840ab03546f22a1c08cf9b99e358`. No redesign or content rewrite was made to those recovered files.
- Removal commits: `eb0048bacd2e57c1d3348030fb9a97875304caa4`, `df68f0544b844d4c4dab14812bea5d89d6417e2e`, `bcaa08cc95bc1ac8e5709ff7f4ac3cb1d1ab3879`. No other application behavior was intentionally changed in this repair.
- **Validation status:** GitHub Actions must rerun on the repaired HEAD. Until the new workflow completes successfully, do not claim CI is green. No real broker orders or production migrations were run.
- **Next single action:** inspect the CI run triggered by this repair; if it passes, audit migration graph and then resume reconciliation gates. If it fails, fix the first new failure before proceeding.


## Live-fill accounting recovery and verification — 2026-10-20

The three files deleted during the temporary rollback have been restored byte-for-byte from their pre-deletion Git blobs at their original paths. Supporting models and migration revisions have now been implemented in this repository.

- Restored originals: `backend/app/services/live_fill_accounting_service.py`, `backend/tests/test_live_fill_accounting_service.py`, `backend/alembic/versions/202610180008_execution_charge_provenance.py`.
- Added models: `backend/app/models/broker_order.py`, `backend/app/models/broker_trade_record.py`, `backend/app/models/live_position.py`; registered them in `backend/app/models/__init__.py`.
- Added migrations `202610180006_broker_trade_intake.py` (down revision `202610170005`) and `202610180007_live_position_execution_provenance.py` (down revision `202610180006`), completing the chain to revision `202610180008`.
- Updated `Execution` model to match charge-provenance migration and added a guard/test rejecting a broker trade quantity above the broker-confirmed child-order fill quantity.
- Exact code/test checkpoint `a906274b98f3f7e0c913f376128f4996b996c52b` passed GitHub Actions [run 39475387511](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39475387511): **355 passed, 1 warning**; Alembic upgrade → downgrade → re-upgrade passed on SQLite and PostgreSQL 16.
- Scope limitation: this is a tested accounting service/storage foundation, not a complete live-fill pipeline. The service remains unregistered; broker trade ingestion, invoking the service from reconciliation, shared live order/status accounting, production staging verification and real-account reconciliation remain outstanding. No real broker orders or production migrations were run. Live order submission remains disabled.
- Next action: continue the existing Phase 2 reconciliation release gates, inspect crash/recovery and broker-confirmed fill linkage, and only integrate live accounting through a separately reviewed, tested path. Do not delete the recovered files without explicit user approval.


## Test-baseline and branch reconciliation — 2026-10-21

- Verified the exact 18 October safety checkpoint from GitHub Actions run [39140514552](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39140514552), commit `9085d9fbdcc8ee2dd8baac6f5e73f92bd76cfa8b`: **456 passed, 8 skipped, 1 warning**. This was the submission-gate checkpoint before later partial-fill and response-parser commits; CI for those later safety-branch commits was not established by that run.
- Verified current `main` HEAD `074dd533bb84ac8102a6602f50cf9d0f57323a3d` and GitHub Actions run [39476051343](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39476051343): **355 passed, 1 warning**. This is a real difference in the checked-out code/test suite, not just an unsupported estimate.
- Compared the recursive Git trees: current `main` contains 35 `backend/tests/test_*.py` files; `safety/fail-closed-trading-mode` contains 48. Twenty-three safety-branch test modules are absent from `main`, including broker trade ingestion, live account safety, broker-write boundary, live execution/recovery, fill-reconciliation coordinator/integration, Upstox response parsing, and live pre-trade/preflight coverage. The branches also differ in application code: 19 safety-branch API/model/service paths related to those tests are absent from `main`. The current `main` also has reconciliation-worker and live-fill accounting implementation that is not a drop-in match for the safety branch.
- GitHub compare reports the refs as diverged (389 commits ahead and 1,029 behind for the selected comparison). Therefore **do not merge or cherry-pick the safety branch wholesale** and do not copy tests without first porting/validating their required production code. The 101-test count difference is explained by materially different test trees; it is not yet evidence that exactly 101 tests were deleted from the same code line.
- Audited the 14 migration files on `main`: the chain is linear from `202608170001` through `202610180008`, with no missing parent revision and one terminal head `202610180008`. Current CI confirms SQLite and PostgreSQL 16 upgrade → downgrade → re-upgrade checks pass.
- Live-fill accounting remains a foundation only: `LiveFillAccountingService` is present but intentionally unregistered; broker-trade intake/reconciliation integration, shared parent-order state accounting, and end-to-end crash/replay verification remain outstanding. Live broker submission remains disabled; no live broker request or production migration was performed.
- Next safe step: create a controlled porting plan from the safety branch by grouping its missing tests with their required source/migration dependencies; port one coherent unit at a time onto `main`, run focused tests plus the complete backend/PostgreSQL migration suite, and update this log only with exact-head CI evidence. Keep the original `Tradepro` repository untouched.


## Upstox response-validation slice — CI VERIFIED (2026-10-21)

- Ported the pure response-validation module `backend/app/brokers/upstox/response_parsing.py` from the 18 October safety branch into `main` as commit [`6a33882`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/6a338820c37ec44632023327cf8e6fa671682ed0).
- Added its regression suite `backend/tests/test_upstox_response_parsing.py` in commit [`03d2607`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/03d2607792e46272566b6871a452e612b1d6ca7a). It covers order IDs/details/history/trades, strict fill quantity versus average-price consistency, funds and pledged-margin separation, margin estimates, and brokerage-estimate component consistency.
- Exact-head GitHub Actions [run 39477976464](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39477976464) passed: **406 passed, 1 warning**. SQLite and PostgreSQL 16 Alembic upgrade → downgrade → re-upgrade steps also passed.
- This is a pure parser/validation slice only. It makes no network requests, does not call a broker, does not alter accounting, and does not enable order submission. The parser is not yet wired into the current main reconciliation client/worker.
- Next: inspect how the current main reconciliation client consumes order/trade payloads; map the missing broker-trade-ingestion tests to current-main models and migrations before adapting a staging service. Preserve current stricter DB constraints and keep the service unregistered until the end-to-end path is reviewed.


## Broker trade staging port — verified checkpoint (2026-10-21)

- Ported `backend/app/services/broker_trade_ingestion_service.py` and `backend/tests/test_broker_trade_ingestion.py` from the safety branch as a dependency-complete first slice, then adapted the tests to current `main` schema constraints.
- Current-main `BrokerOrder` requires a non-null broker connection and status; tests now supply those fields. A historical test expecting an unbound child order to persist was replaced with a database-invariant test proving the stricter main schema rejects that state. A stale `Order.broker_order_id` fixture was removed because current main maps broker child IDs in `BrokerOrder` instead.
- Staging now rejects trades with missing/blank exchange timestamps because current-main `BrokerTradeRecord.exchange_timestamp` is non-null. A regression case covers this fail-closed behavior.
- Exact code/test checkpoint `3f210e592c8aa2e643e536a04f186da8187bc06b`, GitHub Actions [run 39480002328](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39480002328): **431 passed, 1 warning**. SQLite and PostgreSQL 16 Alembic upgrade → downgrade → re-upgrade checks passed.
- Service scope is staging only: it does not update `Execution`, `Position`, portfolio cash, or local `Order` status. It is not wired into the reconciliation worker or registered as an automatic/live submission path. No broker network call or real order was made by CI.
- Added [`SAFETY_BRANCH_PORT_MATRIX.md`](SAFETY_BRANCH_PORT_MATRIX.md), listing the 21 safety-only test modules and dependencies/port decisions. The historical 456-pass and newer 406-pass runs are different branch/test trees; do not interpret the 50-pass difference as 50 deleted tests.
- Next: review child-order reconciliation against current main's worker and repository; port only the required partial-fill/parent-order behavior with explicit idempotency, transaction rollback, and accounting-isolation tests. Keep live-write and fill-promotion paths disabled.


## Cumulative live-fill quantity guard — verified checkpoint (2026-10-21)

- Found a correctness gap in the unregistered `LiveFillAccountingService`: each staged trade was compared individually with the child order's filled quantity, so two distinct trade records could each pass even when their combined accounted quantity exceeded that child fill total.
- Added a per-child aggregate check that sums already-accounted `Execution.quantity` rows for the same broker connection/child order before promotion. The child order is locked first to serialize competing promotions on PostgreSQL. Replays of an already-accounted identical trade remain idempotent.
- Added regression coverage that promotes one trade, then proves a second distinct trade cannot overrun the same child's aggregate fill cap; the live position and paper position remain unchanged after rejection.
- Exact code/test checkpoint `5ad579f60e78dcb5fdee14dcdb17dc4c9d8956a1`, GitHub Actions [run 39480669799](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39480669799): **432 passed, 1 warning**. SQLite and PostgreSQL 16 reversible migration checks passed.
- This is defensive accounting-service validation only. `LiveFillAccountingService` remains deliberately unregistered; staged trades are not automatically promoted and live broker submission remains disabled.
- Architecture issue for next step: the read-only reconciliation worker currently stores trade identity in `BrokerFillIdentity`, while the staging/accounting path uses `BrokerTradeRecord`. Before wiring either path into the other, choose and document one authoritative flow (or a deliberate, transactional bridge) to prevent split-brain fill state and duplicate processing.


## Broker child-order reconciliation port — verified checkpoint (2026-10-21)

- Ported `BrokerChildOrderReconciliationService` and its regression suite from the safety branch, adapting it to current main's stricter `BrokerOrder` schema. Main's child row persists status and filled quantity; weighted average fill price is computed from validated staged trades and checked against the broker snapshot, not persisted to a nonexistent column.
- Reconciliation validates owner/order/connection mapping, rechecks the broker token after asynchronous reads, locks and refreshes the child row, requires staged trade quantity to equal broker-reported filled quantity, checks weighted average price, rejects quantity regressions and terminal-state conflicts, and changes only child-order metadata. It does not mutate parent `Order`, `Execution`, `Position`, or portfolio cash.
- Exact code/test checkpoint `0b1224b3df446a1fcfd1725adcde29a35f722631`, GitHub Actions [run 39481385581](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39481385581): **438 passed, 1 warning**. SQLite and PostgreSQL 16 reversible migration checks passed.
- The service is not wired to an API route or automatic worker. It uses mocked broker responses in tests; no real broker call/order was made by CI.
- Next: resolve the architecture boundary between the intent-based worker's `BrokerFillIdentity` and the legacy/manual-order staging/accounting path's `BrokerTradeRecord`. Decide whether these are intentionally separate workflows or require a transaction-safe bridge before connecting reconciliation to live accounting.


## Parent-order reconciliation lock guard — 2026-10-21

- Child reconciliation now locks/revalidates the owned parent Order after broker status I/O, checks LIVE mode and the pre-network instrument/side/quantity snapshot, then locks the BrokerOrder child before reading staged trade totals. This matches ingestion's parent→child lock order.
- Added a regression test that switches the local order to PAPER during the status read and confirms child status/fill quantity remain unchanged. Staged evidence remains available; no accounting rows are created.
- Exact code/test checkpoint `84f3a3e48a64b6e1d764a87a2b337b2a8f052741`, [CI run 39482592808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39482592808): **439 passed, 1 warning**, with SQLite/PostgreSQL 16 reversible migrations passing.
- This does not enable parent Order accounting or live submission. Keep `BrokerFillIdentity` and `BrokerTradeRecord` workflows isolated until their intended boundary is decided.



## Broker-write source guard — implementation checkpoint (2026-10-21)

- Added `backend/scripts/check_broker_write_boundary.py`, an AST-based source guard that rejects unapproved production references to `place_order`, `modify_order`, and `cancel_order`, while allowing the known PAPER execution call sites and the low-level Upstox adapter definitions.
- Added seven focused unit tests in `backend/tests/test_broker_write_boundary_guard.py` for unauthorized writes, generic receiver bypass, central write boundary, adapter definitions, docstring false positives, and approved PAPER call sites.
- Added a mandatory CI step to `.github/workflows/backend-tests.yml` that runs `python -m scripts.check_broker_write_boundary` against the real application source tree.
- Code/config commits: `fe6700528469a91100f3bf8862a6e4eca3831951` (guard), `c0d8f9293ba44d6abccd41818599fe7dfdcbd0a2` (tests), `e7885101dbbb850cd69c73e4d390177caaa21024` (fixture correction), and `c563683b85d7801cd19dcf3d1c7784ec6e433d1f` (CI integration).
- **Verification status:** the latest commit is `c563683b85d7801cd19dcf3d1c7784ec6e433d1f`. The connected GitHub workflow tool does not expose push-triggered run listings, so the CI result for this exact head is not yet verified here. Do not treat the earlier 439-pass run as verification of this guard. The next action is to inspect the workflow result for this exact head and fix any guard findings before proceeding.
- Scope remains static source protection, not proof against reflection/dynamic dispatch. Live broker order submission and automatic accounting promotion remain disabled.



### Source-guard fixture follow-up

- Corrected the docstring/newline fixture in `backend/tests/test_broker_write_boundary_guard.py`; follow-up commit `a9105fdfc2252c067782649c5c659460db042cc4`.
- This correction has not been independently run locally in this session. The exact-head CI gate remains open; check the workflow result for the current `main` head before proceeding.


## Broker-write guard hardening follow-up — 2026-10-21

- Reviewed the first AST guard and found its exemptions too broad: the entire Upstox adapter file was skipped, and any `service.place_order` reference in the portfolios module could pass regardless of function context.
- Narrowed exceptions to the exact known PAPER strategy call and the named PAPER `place_order` / `cancel_order` endpoint functions. The adapter file is now scanned normally; method definitions are not AST attribute references, while unexpected calls inside that file are detected.
- Added regression coverage for unexpected adapter calls and for a broker-write reference hidden in an unrelated helper in the otherwise approved portfolios module.
- Commits: `00c0986a0628cc6b55b842cfcf6e7fc01b071de4`, `30c1aa7b78de357e070f7cdb37b3719112ee8850`, newline correction `a75a15a0feae98fb2eb4d4301f199d33566c0acf` / `430d00ae787a250f5c7f425e2b72ad02a38c396a`.
- Historical broker-write-guard checkpoint superseded by current verified CI run [39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386): the guard passed on the latest code/test HEAD. The static guard still cannot prove safety against reflection/dynamic dispatch; live writes/accounting promotion remain disabled.


## Exact-head broker-write guard verification — 2026-10-21

- Verified current `main` HEAD `975717b05a3aa5faa030f3f9e177dbcf6066daf3`; GitHub Actions [run 39550130192](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39550130192) passed **447 tests, 1 warning**.
- The run confirms the real application-source broker-write guard passed, and SQLite plus PostgreSQL 16 upgrade → downgrade → re-upgrade migration checks passed.
- The immediately preceding run for `6273a3178e37a27e47a8634564f634075f375f3e` failed; the latest test fix corrected a line-number assertion in the guard test. This was a test assertion failure, not evidence that production broker logic was broken.
- Next Phase 2 work: review the dependency map and design the explicit boundary between intent-based `BrokerFillIdentity` and manual-order `BrokerTradeRecord` before any integration. Keep live submission and automatic accounting promotion disabled.

## Fill-workflow boundary review and regression guard — 2026-10-21

- Reviewed the current worker, repository, staging service, and accounting service. The intent path uses `BrokerFillIdentity`; the manual Order path uses `BrokerOrder` + `BrokerTradeRecord` and a separate explicit-charge accounting service. Their unique constraints are separate, so cross-table duplicate detection is not automatic.
- Decision: preserve them as separate workflows for now; do not dual-write or add a bridge until canonical identity, conflict semantics, ownership/account linkage, transaction, replay, rollback and crash-recovery rules are designed.
- Added assertions to `test_worker_links_trade_and_resolves_full_fill_without_order_write_methods` and `test_worker_repeat_run_deduplicates_fill_and_audit` proving reconciliation and replay do not create `BrokerTradeRecord`, `Execution`, or `LivePosition` rows and do not change portfolio cash.
- Test commit: `3683082509c4b331ab9c7ebceb928e925414de35`. Exact-head CI is pending; do not treat prior 447-pass CI as verification of this test change.
- Next: run the exact-head backend/source-guard/SQLite/PostgreSQL CI. If green, proceed to the next dependency-complete safety slice and add stale-run/crash-recovery coverage. Live order submission and automatic accounting promotion remain disabled.

## Orphaned reconciliation-run recovery — 2026-10-21

- Added `LiveReconciliationRunRepository.fail_orphaned_runs(...)` to mark stale `RUNNING` summaries as `FAILED` with the safe category `WORKER_INTERRUPTED` only when no unexpired lease currently owns the specified user/connection.
- The recovery operation is scoped to the authenticated owner and broker connection, only affects runs older than the explicit cutoff, preserves numeric summary counters, and does not retry broker requests or alter fill/accounting evidence. It locks the lease row where supported and releases the transaction when recovery is deferred.
- Added tests for stale-run recovery, active-lease protection, owner/connection and age scoping, and invalid cutoff times. Normalized SQLite's naive persisted UTC lease timestamps before comparison.
- Implementation commits: `c21dc711c9102c4a6f0aad36b404ba8c1b57d5f8`, `007383da7f0ca5a1793098288f610ed98de9eb71`, `298caa0a1a05124cdf6fdc9d94ff0644f20295a5`. Exact-head CI pending; do not claim green until the latest commit passes backend tests, guard, and both database migration checks.
- Recovery is currently an explicit repository operation, not automatically scheduled. Live broker submission and automatic accounting promotion remain disabled.

## Exact-head stale-run recovery verification — 2026-10-21

- Integrated stale-run recovery into the on-demand reconciliation worker before lease claim. Stale `RUNNING` summaries older than the lease-duration cutoff are marked `FAILED/WORKER_INTERRUPTED` only when no unexpired lease owns the user/connection. If recovery fails, the worker fails closed before claiming a lease or calling the broker.
- Active-lease protection is tested; expired orphan recovery is tested end-to-end through the worker; recovery-error handling is tested to make no broker calls. The repository method preserves stored counters and does not retry broker requests or mutate fill/accounting rows.
- Exact current code head `c1c0d8c6fbbb5dcc1389d2da77e911c815958d88`, [GitHub Actions run 39551504884](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39551504884): **455 tests passed, 1 warning**; broker-write guard and SQLite/PostgreSQL 16 migration cycles passed.
- Caveat: stale-run summary counters are not a durable progress ledger; `WORKER_INTERRUPTED` must be interpreted as incomplete/unknown work, not proof that zero fills occurred. No automatic broker retry, live order submission or accounting promotion is enabled.
- Next Phase 2 gate: add PostgreSQL concurrency coverage for orphan recovery versus lease claim and review the UI/API presentation of interrupted runs so incomplete counters are not shown as authoritative.


## Exact-head crash-recovery race and UI verification — 2026-10-21

- Added PostgreSQL concurrency coverage for orphan-run recovery racing an expired-lease claim. The test verifies the outcome is serialized: either the stale run is marked `FAILED/WORKER_INTERRUPTED` before a new lease wins, or an active new lease prevents recovery.
- The reconciliation review UI now explicitly warns that a `WORKER_INTERRUPTED` run's counters may be incomplete and zero values do not prove that no fills were processed.
- Exact current code/test HEAD `d0437be8ef27c4e86d659a9b85bf42dbdb99ecc4`: backend [run 39552046237](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552046237) passed **456 tests, 1 warning**, source guard and SQLite/PostgreSQL 16 migration cycles; frontend [run 39552046207](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552046207) passed TypeScript and Next.js build.
- This supersedes the previous pending verification note. Stale-run recovery remains metadata-only: it does not retry broker reads, promote fills or mutate accounting. Live submission and automatic promotion remain disabled.
- Next Phase 2 task: audit the crash window between lease release and run-summary persistence, and fail-closed behavior for inconsistent lease state (for example a non-null lease token with no expiry). Preserve idempotency and do not introduce automatic scheduling or broker writes without review.


## Phase 2 exact-head checkpoint — 2026-10-21

- Current verified code/test HEAD `0ce59a7965e3e96a425fa8ae30c841eb0cb755bc`: [backend CI run 39552821228](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552821228) passed **461 tests, 1 warning**, broker-write boundary guard, SQLite migration cycle, and PostgreSQL 16 migration cycle.
- Added fail-closed checks for inconsistent lease token/expiry state in both stale-run recovery and the lease claim repository. Claim predicates no longer treat either half-populated state as an expired lease.
- Added a crash-window regression test: lease release succeeds, terminal summary persistence fails, the run remains marked RUNNING, and later stale-run recovery marks it WORKER_INTERRUPTED before the next run.
- Crash-window test commit `cc01b7143bafba57ed20feaa6cef40c57f122c27` passed 459 tests; the latest exact-head run above includes the additional claim-state tests.
- Next: review whether lease completion and run-summary terminal persistence should be one atomic transaction; add tests for lost-lease / summary ordering before changing lifecycle semantics. Keep recovery metadata-only, preserve separate fill workflows, and keep live submission/accounting promotion disabled.


## Phase 2 atomic lifecycle finalization — 2026-10-21

- Current verified code/test HEAD: `8f967adaa2328f16a0a08a104c3ec394e62f9310`.
- Exact-head [backend CI run 39553655005](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39553655005) passed **463 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles.
- Added `LiveReconciliationRunRepository.finish_with_lease`: lease completion and terminal run-summary persistence now share one database transaction. If run finalization fails, the lease release rolls back too.
- Worker finalization now uses that atomic method. If the lease token is no longer owned, the run is finalized as `LEASE_LOST` without releasing the newer owner's lease.
- Tests cover atomic rollback on a terminal/missing run, protection of a newer lease, and recovery after a simulated worker crash/finalization failure. The worker leaves the lease intact until expiry if summary finalization fails, then stale-run recovery handles the incomplete run.
- Next: review cancellation/exception paths and lease renewal/expiry behavior under concurrent worker activity. Keep reconciliation read-only; no automatic broker writes, live submission, accounting promotion, or scheduler.


## Phase 2 lease-loss and cancellation checks verified — 2026-10-21

- Current verified code/test HEAD: `2ac6bfaafd3475ee63360bd0049b0b6987236bc1`.
- Exact-head [backend CI run 39553981172](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39553981172) passed **465 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles.
- Added a worker test that replaces the lease owner before local processing; the old worker stops before persisting fills, marks its run `LEASE_LOST`, and leaves the new owner's lease intact.
- Added cancellation coverage: cancellation during broker read leaves a RUNNING run and owned lease for expiry-based recovery; the next worker marks the stale run `WORKER_INTERRUPTED` before starting a fresh run.
- Atomic finalization remains in place: lease release and terminal run-summary update share one transaction; failed finalization rolls back lease release.
- Next: review whether lease renewal is frequent enough during large trade/order batches and confirm all cancellation/error paths converge on safe recovery. Keep broker access read-only and live submission/accounting promotion disabled.


## Phase 2 lease-renewal boundary and UI verification — 2026-10-21

- Current code/test HEAD: `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`; backend [run 39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed **466 tests, 1 warning**, broker-write guard, and SQLite/PostgreSQL 16 migration cycles; frontend [run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript/Next.js build. Latest documentation HEAD `7f9a1f3293ffc67579042a87b82cb2fb03ffba1f`; [CI run 39556090575](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556090575) passed.
- Reduced worker lease renewal interval from 25 to 5 records in both trade and order batches. Regression coverage proves a lost lease at a renewal boundary stops before persisting the next batch record; already-persisted fills remain idempotent evidence and the newer lease is preserved.
- The reconciliation UI now warns for both `WORKER_INTERRUPTED` and `LEASE_LOST` runs because their summary counters may be incomplete.
- Phase 2 lease-expiry audit closed: per-write transaction-level fencing and regression tests are implemented and verified by backend CI run 39561621808 (470 passed, 1 warning).


## Phase 3 live-fill accounting checkpoint — 2026-10-21

- Latest reviewed code HEAD at this checkpoint: `ef60ec93d39543c644dfd557f6f73b48ab793b60`.
- Exact-head [Backend CI run 39609474410](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39609474410) completed successfully: **485 passed, 1 warning in 30.25s**; broker-write boundary guard passed; SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed.
- The one warning is non-failing; CI logs also report GitHub Actions Node.js 20 deprecation notices.
- Existing safeguards cover replay identity/charge validation, broker-confirmed fill quantities, cumulative child/order quantity limits, rejected-order protection, and atomic live-position/execution updates. This CI result verifies the current HEAD, not completion of all Phase 3 requirements.
- **Open Phase 3 requirement:** define and test the fee-allocation contract when a broker contract-note charge total covers multiple fills. The current API accepts a per-promotion breakdown and validates that its total equals its six components; it does not itself establish how a multi-fill contract-note total is allocated. Do not claim this issue resolved or wire in a coordinator/identity bridge until the rule is designed and regression-tested.
- Safety constraints unchanged: do not enable live broker submission, automatic accounting promotion, or automatic scheduling; keep `BrokerFillIdentity` and `BrokerTradeRecord` separate pending a reviewed bridge design. Phase 2 remains closed.


## Phase 3 continuation — verified code baseline and fee-allocation gate (2026-10-21)

- Rechecked latest code baseline `ef60ec93d39543c644dfd557f6f73b48ab793b60`: [exact-head backend CI run 39609474410](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39609474410) passed **485 tests, 1 warning**; broker-write boundary guard and SQLite/PostgreSQL 16 migration cycles passed.
- The nine core documentation files were synchronized in the subsequent documentation commits ending at `ccb41cf892e2ce9c91fafa090930b171d56d6318`. The Actions history checked at this point did not contain a run for that documentation HEAD; do not describe that docs-only HEAD as independently CI-verified. This progress update is intended to trigger a fresh backend workflow on the new documentation commit.
- Phase 3 remains open. Before building a coordinator or bridging `BrokerFillIdentity` to `BrokerTradeRecord`, specify the provenance and allocation semantics for contract-note charges spanning multiple fills. The current promotion API accepts a per-fill `LiveFillChargeBreakdown`, checks that the supplied total equals its six components, and persists the supplied breakdown; it does not define or perform contract-note-level allocation.
- Do not guess fee allocation or silently duplicate a contract-note total across fills. Require a documented broker-evidence mapping or an explicit allocation algorithm with deterministic paise rounding, reconciliation against the original note total, and regression tests before implementation.
- Keep live broker submission, automatic accounting promotion, and automatic scheduling disabled. Phase 2 remains closed; no live broker actions were performed.


## Phase 3 charge-allocation model audit — 2026-10-21

- Audit recorded in `PHASE3_CHARGE_ALLOCATION_CONTRACT.md` (commit `6753229f0bad433119fe94754b383c440676b900`).
- `BrokerTradeRecord` currently has broker connection ID, broker order reference, broker trade ID, quantity, price, side, instrument token, and exchange timestamp; uniqueness is enforced on broker connection plus broker trade ID. The model does not currently carry contract-note charge totals, component-level source evidence, allocation basis/version, or reconciliation state.
- `LiveFillChargeBreakdown` is a per-promotion charge snapshot; validating its six components against its total does not prove how a contract-note total spanning multiple fills was allocated.
- The exact paths `backend/app/models/broker_fill_identity.py` and `backend/app/schemas/live_fill_accounting.py` were not found. Locate actual definitions via repository tree/search before designing any identity bridge; do not assume these paths exist.
- Relevant CI already exists at `.github/workflows/backend-tests.yml`: push to main, pull requests, and manual dispatch; it runs backend pytest with PostgreSQL 16 service, broker-write boundary guard, and SQLite/PostgreSQL Alembic upgrade/downgrade/re-upgrade checks. Therefore the missing item is not a wholly absent workflow. The missing items are the charge-allocation regression cases and an exact-HEAD run for the current docs commit.
- Last code baseline verified by run 39609474410 passed 485 tests, 1 warning. The latest docs/audit HEAD `6753229f0bad433119fe94754b383c440676b900` has no matching Actions run visible in the queried run history. The backend workflow has `push: main` and `workflow_dispatch`, but this GitHub tool surface does not expose a workflow-dispatch action; do not claim the latest HEAD is green until a matching run is visible.
- Next: inspect the repository tree and broker-specific trade/contract-note ingestion; establish supported fee evidence and allocation basis; implement persistence/migration plus regression tests; then verify exact code HEAD in backend CI. Live submission, automatic accounting promotion, and automatic scheduling remain disabled; Phase 2 remains closed.


## Phase 3 repository-boundary verification — 2026-10-21

- **Target repository:** `tarunsharma2610-del/tradepro-improved`, branch `main`. All Phase 3 implementation and documentation changes in this work are restricted to this repository.
- **Protected original repository audit:** checked recent commits in `tarunsharma2610-del/Tradepro`. Its latest commit remains `32c0207a61a6604d2f534dc020209dbfbf1413ea` (“Add Tradepro backend frontend and nginx”, 2026-10-17). No Phase 3 or charge-allocation commits from this work appear in its recent history. Do not write to that repository.
- **Model audit confirmed from actual files:** `backend/app/models/broker_trade_record.py` stores broker connection, child-order reference, broker trade ID, quantity, price, side, instrument token, and exchange timestamp; uniqueness is `(broker_connection_id, broker_trade_id)`. It does not store contract-note source totals or allocation state. `backend/app/models/execution.py` stores per-execution charge components, `charge_source`, and `charge_reference`, with uniqueness on `(broker_connection_id, broker_trade_id)`; it has no durable contract-note-to-multiple-fill allocation record in this model.
- **CI status:** the existing `.github/workflows/backend-tests.yml` already runs pytest with PostgreSQL 16, the broker-write boundary guard, and SQLite/PostgreSQL migration cycles. Required charge-allocation tests are not yet present as a complete coverage set. A passing earlier code CI does not verify this latest docs commit; no exact-HEAD run is claimed here.
- **Next Phase 3 action:** locate the actual broker trade/contract-note ingestion and identity definitions via the repository tree; confirm the broker's source evidence before designing schema or allocation basis. Do not guess fee allocation, add a speculative identity bridge, or enable live submission, automatic accounting promotion, or scheduling.
- Phase 2 remains closed. Original `Tradepro` remains untouched by this work.


## Phase 3 — broker ingestion evidence boundary (2026-10-21)

- Traced `backend/app/services/broker_trade_ingestion_service.py`: it stages normalized Upstox trade rows in `BrokerTradeRecord`; this path does not ingest contract-note fee totals or per-component charges.
- Traced `backend/app/services/broker_child_order_reconciliation_service.py`: it reconciles broker child-order status against staged trade quantity and average price, and does not create `Execution` rows or mutate accounting.
- Recorded detailed findings and the next evidence prerequisite in `PHASE3_CHARGE_ALLOCATION_CONTRACT.md` (commit `3cf9fc88411234783fb1a654c6e12f195247b94c`).
- CI gap classification: the existing backend workflow already covers pytest/PostgreSQL 16, broker-write boundary, and SQLite/PostgreSQL migration cycles. Add missing charge-allocation regressions to this workflow; do not create a duplicate CI workflow without a demonstrated need. Exact-HEAD CI must still be checked separately.
- No allocation schema or formula was added because contract-note evidence has not yet been found in the reviewed ingestion path. Phase 3 remains open; live broker submission, automatic accounting promotion, and automatic scheduling remain disabled. Original `Tradepro` repository remains untouched by this work.


## Phase 3 — official Upstox charge API review (2026-10-21)

- Reviewed official Upstox docs for historical trades, trade charges, and brokerage calculation. Historical trade rows include trade identity/economics but not documented per-trade fee components; the trade-charges endpoint is an aggregate by segment/date range/financial year; brokerage endpoint calculates fees and is not actual completed-trade charge evidence.
- Recorded API references and the fail-closed conclusion in `PHASE3_CHARGE_ALLOCATION_CONTRACT.md` (commit `754bdfe0cfb6f73464bf238f72f830d412c70006`).
- Next: inspect the official trade-wise P&L data/metadata response schema and actual contract-note/bill report options before choosing a source. Do not treat estimated brokerage calculations as broker-reported actual charges or allocate aggregate fees by guess.
- Existing backend CI workflow remains the correct place for feature tests. No separate CI workflow needed; exact-HEAD verification for the latest commits remains outstanding. Phase 3 open; live submission, automatic accounting promotion, and scheduling disabled.


## Phase 3 — contract-note source catalogue review (2026-10-21)

- Reviewed the official Upstox Swagger endpoint catalogue and developer API overview. The documented APIs reviewed expose historical trades, trade-wise P&L data/metadata, aggregate charges, and brokerage estimates; no contract-note download endpoint was identified in that catalogue review.
- This does not prove no downloadable contract-note export exists through the Upstox web/app or support channels. Source remains unresolved; do not allocate aggregate charges or treat estimates as actual broker charges. See `PHASE3_CHARGE_ALLOCATION_CONTRACT.md`, commit `70185e5efa937f57a20a9e8c20f2ce3fc1c5e510`.
- No code/migration change made in this step. Existing backend CI remains appropriate; missing feature regressions still need implementation once source evidence is established. Exact-HEAD CI remains unverified. Phase 3 remains open and live broker submission/automatic accounting promotion/scheduling remain disabled.


## Phase 3 — adapter and charge provenance audit (2026-10-21)

- Reviewed `backend/app/brokers/base.py`, `backend/app/brokers/upstox/adapter.py`, `backend/app/brokers/upstox/response_parsing.py`, ingestion service, and `Execution` model.
- Adapter contract has order/trade retrieval but no contract-note ingestion or actual-charge retrieval capability. `BrokerageChargeEstimate` explicitly represents estimates; `BrokerTrade` has no charge fields. `Execution` stores per-fill amounts/reference but no immutable source-note/allocation ledger.
- Detailed finding and safe design gate recorded in `PHASE3_CHARGE_ALLOCATION_CONTRACT.md` (commit `49f95bdd5f20ee99b21a573087c6e97a9bc03526`).
- No speculative API method, schema migration, or fee formula added. Next: settle supported evidence import path and retention/security policy, then implement source ledger + allocation transaction + regression tests. Existing `.github/workflows/backend-tests.yml` is the right CI; exact latest HEAD status must be verified before claiming green.


## Phase 3 — source-ledger implementation gate (2026-10-21)

- Confirmed against current adapter and model files: the adapter exposes trade retrieval/estimate capabilities but no actual-charge/contract-note ingestion operation; `Execution` stores per-fill fee components but is not linked to immutable source evidence.
- Contract-note design gate updated with the minimum read-only source-ledger/allocation-record invariants and 12 required regressions (commit `1db60bd6c94d23c9ce6bededcffc46458b333d4f`).
- No schema migration or allocation formula implemented because a supported source format and per-charge allocation basis are still unverified. This avoids creating misleading accounting records.
- Existing backend CI remains the appropriate workflow for the new tests. Latest docs commit must have its exact-head CI result checked; no green status is inferred from prior code runs. Original `Tradepro` repository remains untouched. Phase 3 open; live submission, automatic accounting promotion and scheduling disabled.


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

## Phase 3 continuation — source and code-path audit (2026-10-21)

- Public research located third-party text copies of Upstox contract notes and official Upstox documentation for manual contract-note access. These are field-discovery evidence only; no authenticated original PDF bytes, digital-signature verification, or component-specific fee allocation basis has been established.
- Inspected the live-fill accounting path in `broker_trade_ingestion_service.py`, `broker_child_order_reconciliation_service.py`, `broker_trade_record.py`, `live_fill_accounting_service.py`, and `execution.py`. Existing code stages broker trades separately, keeps reconciliation metadata-only, and requires a caller-supplied `BROKER_REPORTED` six-component charge breakdown whose total matches exactly. Execution rows retain source/reference and uniqueness prevents duplicate accounted fills. This does not authenticate the charge source or justify allocating aggregate note totals to individual fills.
- Added this code-path audit and the explicit no-speculative-allocation gate to `PHASE3_CHARGE_ALLOCATION_CONTRACT.md`; commit: `f4c9a20847a94cb0bd6dc52001d9e7d80830d90c`.
- **Current docs HEAD:** `f4c9a20847a94cb0bd6dc52001d9e7d80830d90c`. Exact-HEAD CI has not yet been confirmed. The workflow on push runs pytest, broker-write boundary guard, and SQLite/PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks. Do not mark this commit green until a successful run for this exact SHA is visible.
- **Next gate:** obtain authoritative documentation or an authenticated, privacy-safe sample establishing the real import file and component-level allocation basis. Until then, no production importer/schema migration or charge allocation formula is safe to implement. Live broker submission, automatic accounting promotion, and automatic scheduling remain disabled; Phase 2 remains closed; original `Tradepro` remains untouched.

## Official charge API cross-check — 2026-10-21

- Inspected official Upstox documentation for [trade-wise P&L](https://upstox.com/developer/api-documentation/get-profit-and-loss-report/), [trade charges](https://upstox.com/developer/api-documentation/get-trade-charges/), and [historical trades](https://upstox.com/developer/api-documentation/get-historical-trades/).
- Trade-wise P&L exposes trade economics and dates but not the actual per-fill charge breakdown required by the current Execution model. The charges endpoint provides aggregate totals/breakdown for date range, segment and financial year, not per-fill allocation records. Historical trade data does not document a complete actual-charge breakdown per fill.
- NSE's [revised contract-note FAQs](https://www.nseindia.com/static/trade/contract-note-faqs) describes trade-detail annexures and combined transaction-charge reporting, which does not prove unique per-fill mapping for every levy.
- Contract: PHASE3_CHARGE_ALLOCATION_CONTRACT.md, updated in commit 6ab4948c6c5978a2d7aadf75ece59f407f605674. Aggregate charges must not be allocated to fills by guessed proportional rules; symbol/date/average-price matching alone is not sufficient.
- **Current status:** the evidence gate remains open. Next safe work is to add/strengthen tests and interface-level rejection for any attempted use of aggregate charge reports as per-fill actuals, without introducing a production importer or speculative schema. Latest documentation commits still require exact-HEAD CI confirmation.

## Phase 3 negative-source regression coverage — 2026-10-21

- Extended `backend/tests/test_live_fill_accounting_service.py` to explicitly assert that source labels `AGGREGATE_CHARGES`, `TRADE_CHARGES_API`, and `BROKER_ESTIMATE` are rejected by live-fill promotion, alongside the existing estimated-charge rejection. This is regression coverage for the rule that period/segment aggregates and estimates are not per-fill actual-charge evidence.
- Test change commit: `b8fa3eca4d2f6181a81ac3efd4d714af10cf5a8c`.
- This is a test-only guard, not an importer or a new allocation mechanism. It does not prove actual-source authenticity; a caller could still mislabel data as `BROKER_REPORTED`, which is part of the outstanding source-provenance design gate.
- Latest code/test commit requires exact-HEAD CI. Do not claim the new cases passed until GitHub Actions reports success for the exact current HEAD, including pytest, broker-write guard, SQLite migration cycle and PostgreSQL 16 migration cycle.

## Handover checkpoint sync — 2026-10-21

- Handover refresh committed as 195ac861d91fa10e1e26b69e5975c5e696c5d446.
- Latest work remains the aggregate-charge rejection regression tests (commit b8fa3eca4d2f6181a81ac3efd4d714af10cf5a8c) and corresponding progress/handover records.
- Exact-HEAD CI remains unverified. Available GitHub status/run queries have not returned a matching run; do not infer success.
- No importer, allocation schema, or allocation formula was introduced. Phase 3 remains open pending authoritative per-component allocation evidence. Live submission, automatic accounting promotion, and automatic scheduling remain disabled; Phase 2 remains closed.

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

### Phase 3 source-to-ledger code review checkpoint — 2026-10-22

- Reviewed contract-note intake/storage, source-component review, per-fill allocation, ledger verification, and transactional promotion on this branch.
- Confirmed controls: document reads verify SHA-256 and byte size; transcribed components retain source locator and extraction/transcription version; a different authorized reviewer records the canonical eligible-fill manifest; verification checks exact fill set, reviewed source total, INR currency, method/basis, paise-exact sum, and reconciliation reference; promotion rechecks under locks and leaves the outer transaction to its caller.
- Limitation: this is a human-attestation workflow, not automatic contract-note parsing or cryptographic proof of broker origin. Tests use synthetic fixtures; no actual broker contract note was available for this review. Real source amounts/fill mapping remain unverified.
- Synthetic paired PostgreSQL/document restore passed on prior exact head `f15b74b3201720a7e40021b9da6a3c066bc85b23` (run 39757022342). Restore against real retained backups remains unexecuted.
- Documentation checkpoint only; live broker writes remain disabled, PR #6 remains draft/unmerged, and original `Tradepro` is out of scope. Fresh CI is required for any new head.

### Phase 3 continuation checkpoint — 2026-10-22 (pause point)

- Pause point saved after commit `f7c2dc5d402bb157c98ccbfd7e7d26f5c7d67e89` on `phase3/durable-per-fill-charge-allocation`.
- Added `backend/tests/test_broker_charge_source_component_api.py::test_non_admin_cannot_review_another_users_contract_note`, covering cross-user non-admin review denial and asserting the source component remains pending with no reviewer/fill-set fields recorded after denial.
- Exact-head GitHub Actions run `39759187947` was `in_progress` at last check for this commit. Do not claim it passed until rechecked: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39759187947
- Previous documented head `a6ffba6f1eebd370bd945780074d32cfc09f9fb0` had green CI run `39758399828`; that does not verify the newer test commit.
- Next action on resume: first check run `39759187947` and confirm its head SHA/conclusion, inspect failed steps if any, then continue Phase 3 security/reconciliation acceptance review.
- Real contract-note/source amount verification and real retained database/document backup restoration remain open; synthetic CI restore is not a real backup restore. Do not fabricate actual-source evidence.
- PR #6 remains draft/unmerged; live broker order submission remains disabled. All work is confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is out of scope.


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


## Exact-head CI verification — 23 October 2026

- **Passed:** latest component-allocation-policy documentation head `a46a63407f84ae785b18926a95bdd920fd5c39e6`, GitHub Actions [run 39928519469](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39928519469). Backend pytest job completed successfully, including test suite, broker-write boundary enforcement, SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade, synthetic PostgreSQL/document-volume restore, and restore-evidence retention.
- This verifies the exact policy-doc head. The checkpoint-only commit that records this result needs a new exact-head CI run of its own.
- Component-specific automatic tariff-derived allocation remains a design/implementation gate, not complete: effective-dated rules and regression coverage are still needed for brokerage caps/order-level charges, GST taxable base, buy-side stamp duty, side/product-specific STT, and segment/exchange charges. Do not equate generic paise-exact allocation with approved tax/contract attribution.
- Public Upstox contract-note research and third-party layout examples are documented; examples are not independently authenticated. A personal contract note is not required for continued engineering. Actual retained Oracle Cloud backup/restore remains a separate operational validation gate.
- PR #6 remains draft and unmerged pending acceptance review and explicit user approval. Live broker order writes remain disabled. Scope is exclusively `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains out of scope.


## Fail-closed allocation gate — CI verified 23 October 2026

- Commit `2e14ce6feed8357a85813ec5924e577879b2e4ca` passed GitHub Actions [run 39929331878](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39929331878). Backend pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore, evidence retention, and cleanup all completed successfully.
- The source-reconciliation verification gate now rejects `QUANTITY` and `NOTIONAL` allocation bases until component-specific effective-dated rules are approved. A regression test verifies unsupported notional allocation raises and rows remain `PENDING_RECONCILIATION`. Explicitly reviewed per-fill weights remain available, subject to existing provenance/reviewer/promotion checks.
- This is a conservative fail-closed safeguard, not completion of component-specific tariff automation. Still required: reviewed tests/rules for brokerage caps and multi-fill orders, GST taxable base, buy-side stamp duty, side/product-specific STT/CTT, exchange/segment charges and effective-date transitions. Ambiguous source scope must remain pending.
- Publicly shared Upstox contract-note examples are for layout/research only and are not independently authenticated. Actual Oracle Cloud backup recovery remains separate from synthetic restore CI.
- PR #6 remains draft and unmerged until acceptance gates are reviewed and the user explicitly approves. Live broker order writes remain disabled. Changes are confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains out of scope.


## Fail-closed allocation gate — CI verified 23 October 2026

- Commit `2e14ce6feed8357a85813ec5924e577879b2e4ca` passed GitHub Actions [run 39929331878](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39929331878). Backend pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore, evidence retention, and cleanup all completed successfully.
- Source-reconciliation verification now rejects `QUANTITY` and `NOTIONAL` allocation bases until component-specific effective-dated rules are approved. A regression test verifies unsupported notional allocation raises and rows remain `PENDING_RECONCILIATION`.
- This is a fail-closed safeguard, not completion of tariff automation. Still required: tests/rules for brokerage caps and multi-fill orders, GST taxable base, buy-side stamp duty, side/product-specific STT/CTT, exchange/segment charges and effective-date transitions. Ambiguous source scope must remain pending.
- Public Upstox contract-note examples are not independently authenticated. Actual Oracle Cloud backup recovery remains separate from synthetic restore CI.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains out of scope.


## Component-wide fail-closed regression coverage — 23 October 2026

- Commit `b976d29c8c20542ec155fe34337e110e9a7dc1db` passed GitHub Actions [run 39930456526](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39930456526). All job steps succeeded: backend pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore, evidence retention and cleanup.
- Expanded the source-reconciliation regression test across all six currently supported source component types (brokerage, STT, exchange charges, SEBI charges, stamp duty and GST) and both automatic bases (`QUANTITY`, `NOTIONAL`). Each unsupported basis is rejected and allocation rows remain `PENDING_RECONCILIATION`.
- This verifies fail-closed handling only. It does not implement or approve automatic tariff-derived allocation. Component-specific rules and tests remain required for brokerage caps/multi-fill orders, GST taxable base, buyer-side stamp duty, side/product-specific STT/CTT, exchange/segment charges, and effective-date transitions.
- PR #6 remains draft and unmerged pending acceptance review and explicit user approval. Live broker order writes remain disabled. Work remains confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is out of scope.


## Documentation checkpoint CI — 23 October 2026

- Exact commit `e5ade9dd831ff57efe8b33ba7014d5393b36ef4c` passed GitHub Actions [run 39930865283](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39930865283). Backend pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore, evidence retention, and cleanup all completed successfully.
- The fail-closed allocation safeguard remains active. Component-wide tests for the six currently supported charge types and both `QUANTITY`/`NOTIONAL` automatic bases passed on earlier code commit `b976d29c8c20542ec155fe34337e110e9a7dc1db` (run 39930456526).
- Next gate is actual component-specific tariff-rule implementation and tests; the current safeguards do not yet prove tariff correctness or complete Phase 3. PR #6 stays draft/unmerged pending acceptance review and explicit user approval. Live broker order writes remain disabled; only `tradepro-improved` is in scope.


## Exact-head CI confirmation — 23 October 2026

- Exact commit `ed6e88bc8f419496c83d1235da94cebeb2791f1e` passed GitHub Actions [run 39931215564](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39931215564). The complete backend job succeeded: pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade, synthetic PostgreSQL/document-volume restore, evidence retention and cleanup.
- This verifies the checkpoint head only. Component-specific tariff-derived allocation is still not implemented or approved. The fail-closed source-reconciliation gate and tests for all six supported component names across `QUANTITY` and `NOTIONAL` bases remain the current safeguard.
- Next engineering gate: inspect and implement tariff rules as effective-dated, component-specific calculations with provenance and regression fixtures before enabling any automatic allocation basis. Preserve pending reconciliation for unknown or ambiguous scope.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains outside scope.


## Exchange/SEBI arithmetic regression checkpoint — 23 October 2026

- Commit `b37e6cab7c9cbba0897e5c02161812d121ba2c7e` passed the full GitHub Actions backend workflow [run 39933579727](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39933579727). Pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore, evidence retention, and cleanup succeeded.
- Added explicit-base arithmetic helpers and regression tests for exchange and SEBI charges. These helpers do not select official tariffs or prove applicability; effective-dated exchange/segment/product-specific rules and per-fill attribution remain outstanding.
- Brokerage-cap, GST, stamp-duty, and STT/CTT arithmetic checkpoints have also passed their respective full CI runs. The current source-reconciliation gate remains fail-closed for automatic `QUANTITY`/`NOTIONAL` allocation pending approved component-specific rules.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched/out of scope.


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


## 2026-10-23 — Task B tariff snapshot checkpoint

- Added migration `202610240016_immutable_tariff_estimate_snapshots.py` after `202610240015`; PostgreSQL and SQLite reject direct SQL UPDATE/DELETE on `tariff_estimate_snapshot_records`.
- Added direct-SQL mutation/deletion regression tests and SQLite test-fixture triggers. Commit `bf9b3bc74cfa4047bc084bf6136e12c0a93a65c0` is the current PR #6 head.
- Exact-head GitHub Actions run 39959332425 passed: pytest, broker-write boundary, SQLite migration round-trip, PostgreSQL 16 migration round-trip, and synthetic restore drill.
- Tariff calculator remains intentionally limited to PERCENT, INR_PER_CRORE, and INR_FIXED. Conditional/order-scoped caps, full GST taxable-base composition, and other special charge models are not yet implemented; do not treat simplified rates as production-approved.
- Remaining Task B: add explicit PostgreSQL concurrent persistence/direct-SQL immutability coverage; finish tariff-to-estimate-versus-actual variance integration; keep actual contract-note components as the only source for per-fill actual allocation; sync all nine core docs at final acceptance.
- PR #6 remains draft/unmerged. Live broker order writes remain disabled. Original `Tradepro` repository remains out of scope.


## Task B verification addendum — 2026-10-23 (supersedes older pending/ORM-only notes)

- Database-level tariff snapshot immutability is implemented by migration `202610240016_immutable_tariff_estimate_snapshots.py`: PostgreSQL and SQLite reject direct SQL UPDATE/DELETE on `tariff_estimate_snapshot_records`. Direct-SQL SQLite regression tests cover both operations.
- Added a PostgreSQL race test for concurrent tariff snapshot persistence. It checks exact-replay convergence to one row and conflicting-payload fail-closed behavior. Latest code commit: `fd0e42917611f3b6c3f826cb2e99971fd3e2cce6`.
- Exact-code-head CI run [39960409771](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39960409771) passed: **677 passed, 1 warning**; broker-write guard passed; SQLite and PostgreSQL 16 migration downgrade/re-upgrade passed; synthetic PostgreSQL/document-volume restore passed.
- Tariff rules remain intentionally limited to PERCENT, INR_PER_CRORE, and INR_FIXED. Do not approve rules needing order-scoped caps/minimums, lesser-of conditions, full GST taxable-base composition, DP/depository models, or other unsupported bases until modeled and tested.
- Still open: variance-only integration between estimate snapshots and reviewed actual contract-note source components; estimates must never become actuals or source amounts for per-fill allocation. Keep PR #6 draft/unmerged, live broker order writes disabled, and original `Tradepro` out of scope.


## Task B variance integration checkpoint — 2026-10-23 (supersedes prior variance-open notes)

- Added estimate snapshot schema v2 with optional exact `source_trade_record_id` so variance comparisons can prove fill scope. Snapshots without that identity fail closed for comparison.
- Added append-only `TariffEstimateVarianceRecord`, migration `202610240017`, and `compare_estimate_to_reviewed_actual`. It requires a VERIFIED source component, REVIEWED contract-note evidence, matching reviewer/hash/component/currency, intact source document, matching Upstox connection and exact fill identity. It records estimated amount, actual amount, signed difference and percentage only; it never changes charge allocations.
- Variance comparison supports both `TRADE_FILL` and `ORDER_FILL_SET`; aggregate comparisons require exact canonical fill membership and same broker order, connection, side, and trade date. Records remain audit-only and do not allocate charges or mutate P&L.
- Added exact-replay, missing-fill-identity, direct-SQL immutability, and no-allocation-side-effect tests. Latest code commit `aa0999759caa795f5ef48c336e492635334852f0` passed CI run [39961777103](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39961777103): **680 passed, 1 warning**, broker-write guard, SQLite/PostgreSQL 16 migration round-trips, and synthetic restore drill passed.
- Still open: safe aggregate variance comparison for order-level contract-note components; richer tariff models for caps/minimums, conditional lesser-of rules, GST taxable base, DP/depository and other special bases. PR #6 stays draft/unmerged; live broker order writes disabled; original `Tradepro` out of scope.


## Verified exact PR-head CI 39962196672 — 2026-10-23
Current PR #6 head at verification: `c47bc3e3eeb4c8da4415132735d2d4ef457551f7`. [GitHub Actions](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39962196672) completed successfully: 680 passed, 1 warning; broker-write guard passed; no failed steps. Next work: design aggregate/order-level variance safely, close advanced tariff-rule semantics or fail closed, complete final accounting integration review, then rerun exact-head CI. PR stays draft/unmerged; live writes disabled; original Tradepro untouched.


## Aggregate variance design proposal recorded — 2026-10-23
Added a proposal to `docs/PHASE3_TARIFF_TO_FILL_ALLOCATION_DESIGN.md` for explicit `TRADE_FILL` versus `ORDER_FILL_SET` comparison scope. It requires canonical exact fill-set identity, source/reviewer/hash revalidation inside one transaction, order-scope calculation for capped/nonlinear fees, idempotent append-only variance, and no mutation of allocations/positions/P&L. This is design only, not implementation or approval. Required test matrix is in the design doc. Next: review proposal against actual tariff snapshot/schema implementation, then implement only after confirming existing types and migration conventions. PR #6 stays draft; live writes disabled.


## Variance scope integrity hardening — 2026-10-23
Audited `tariff_estimate_variance_service.py` and found two missing fail-closed checks: it compared the fill-manifest contents without verifying `eligible_fill_set_sha256`, and did not verify the identified broker fill's side/trade date against the estimate. Added canonical manifest serialization + SHA-256 validation and side/date matching, with regression tests for tampered digest and mismatched scope. Code commits: `4e9ebc871f45b0b3ecef0df935394d5ab2c0c340`, `c63afd70bea5ac0f090bacda0f7a41c67ce566b4`, `6e9362e09919a63dad4280b096ccf8886eda2aff`, `6ca045e2bbdd71d37dd77baf50df3881db2b1e71`. CI for this exact code head is not yet verified. Aggregate variance remains design-only; current tariff calculator supports only PERCENT, INR_PER_CRORE and INR_FIXED, with no active production rates, caps/minimums, conditional lesser-of rules, or explicit GST taxable-base model.


## Exact-head CI verified — 2026-10-23
Verified CI run [39968000009](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39968000009) for code head `f5092df1d27a28006dccba929fdc41e9a1d63f1e`: workflow succeeded, **683 passed, 1 warning**, broker-write boundary guard passed, SQLite migration round-trip and isolated PostgreSQL 16 synthetic restore drill completed. Warning is Starlette TestClient's deprecated `anyio.abc.BlockingPortal` alias; Node action deprecations are also logged. This CI validates the code head before this documentation-only checkpoint. Next: finish aggregate variance and advanced tariff-rule support; CI must run again on the resulting docs head. PR #6 remains draft/unmerged; live broker writes disabled.


## Aggregate fill-set variance implementation checkpoint — 2026-10-23
Started implementation of explicit `TRADE_FILL` and `ORDER_FILL_SET` variance scopes. Snapshot schema v3 captures canonical fill IDs and SHA-256; persistence stores the scope; migration `202610240018` adds snapshot/variance scope metadata and dialect-specific validation; variance comparison validates exact fill-set membership, same broker order, connection, side and trade date; variance records store scope/digest and replay compares them. Added snapshot canonicalization/duplicate/empty-set tests and aggregate comparison/replay/mismatch tests. Design and limitations are in `docs/PHASE3_TARIFF_TO_FILL_ALLOCATION_DESIGN.md`. Latest implementation CI is pending; do not treat this feature as accepted until exact-head CI and migration round-trip pass.


## Aggregate variance coverage and CI checkpoint — 2026-10-23
Added `backend/tests/test_tariff_estimate_variance_service.py` with database-backed tests for successful `ORDER_FILL_SET` comparison, exact replay idempotency, and rejection of a mismatched estimate fill manifest without creating a variance record. Backend CI run [39979772325](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39979772325) passed on code/test commit `e54e405b74feee90e4658a6992fa208a3e2da5d3`: test suite, broker-write boundary guard, SQLite and PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore drill. This document synchronization creates newer commits; re-run and verify CI on the final documentation head before accepting the gate. PR #6 stays draft/unmerged; live broker writes remain disabled.


## Latest tariff-safety correction checkpoint — 2026-10-23
Tariff calculator CI initially failed on commits `137b61a` and `55fc427`. Follow-up fix `68dc2b6fa0a729cc77180725e581de61a88e9de1` adds the missing APPROVED-status guard for explicit GST composition and rejects non-BUY stamp-duty requests before rule selection; it also aligns the GST guard message. Exact-head CI run [39982723294](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39982723294) passed: pytest, broker-write boundary guard, SQLite and PostgreSQL 16 migration round-trips, and synthetic restore drill. This documentation commit still requires its own exact-head CI. Tariff/accounting acceptance remains pending further rule coverage review; PR #6 remains draft/unmerged and live broker writes disabled.


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

## Aggregate variance regression coverage — 2026-10-24
Added database-backed rejection tests for tampered actual eligible-fill-set digest, fills assigned to different broker orders, side mismatch, and trade-date mismatch. Each negative case asserts no variance record is created. Existing coverage checks order-fill-set success, exact replay, and different-manifest rejection. Relevant test commits: `69ba34d54baa615cd3411ef88e662d29d4b04d92`, `b4e6e08490764a49573b353eff882c3bb6daea07`, `21c94b36f5006d66a46f07ae68d8b73f4524bc4a`, `16dc6b9964db1af85deeffffb3814a0ff526b951`. The first two CI runs exposed an invalid test that tried to mutate an immutable estimate snapshot; that test has been removed. CI for the current head is pending. PR #6 remains draft/unmerged; live broker writes disabled; original `Tradepro` untouched.

## Aggregate variance CI verification — 2026-10-24
Exact-head backend CI passed on `bc8e5c1aa862589c660fd361d87f7df45d8ceb10` in run `40062975428` (Backend pytest: success). Tests cover audit-only variance success, exact replay, different manifest rejection, tampered actual fill-set digest, mixed broker-order fills, side mismatch, and trade-date mismatch; rejected comparisons assert no variance record. Remaining acceptance items: concurrency/replay behavior, reviewed-source revalidation under concurrent change, and explicit no-allocation/no-position-or-P&L-side-effect assertions. PR #6 remains draft/unmerged; live broker writes disabled; original `Tradepro` untouched.

## Additional aggregate variance regression tests — 2026-10-24
Added `test_variance_comparison_does_not_change_reviewed_source_or_charge_allocations`, which checks source/evidence provenance and allocation ledger fields remain unchanged after a variance record is created. Added parameterized `test_variance_comparison_revalidates_review_state_before_writing`, which rejects stale evidence/component review states without writing a variance row. CI on the latest test head is pending. Remaining: exact-head CI, concurrency/replay acceptance, and final nine-document synchronization. PR #6 remains draft/unmerged; live broker writes disabled; original `Tradepro` untouched.

## Upstox API/SDK coverage policy — 2026-10-24
Created `UPSTOX_API_INTEGRATION_POLICY.md` and made it mandatory in `PROJECT_INSTRUCTIONS.md`. The policy requires an official-source capability matrix, official SDK/version assessment, Agent Skill/MCP review with safety limits, sandbox/rate-limit/auth review, and specific evaluation of brokerage estimate, historical trade charges and historical trades. Estimates and aggregate historical charges must not be treated as reviewed contract-note/per-fill evidence. Live broker writes remain disabled; exact-head CI for this documentation change is pending.

## Aggregate variance concurrency acceptance — 2026-10-24 (CI verified)
Added PostgreSQL race coverage `test_concurrent_variance_comparison_exact_replay_is_audit_only`. It verifies simultaneous comparisons yield one `CREATED` and one `EXACT_REPLAY`, one `VARIANCE_ONLY` row, and no allocation writes. Exact-head CI run `40064129721` passed on `dbff090610028cfb9f5a87585d9c8e697449cd23`: 738 passed, 1 warning. This closes aggregate-variance concurrency/replay alongside review-state, no-side-effect and mismatch tests. Next: source-backed effective-dated component-specific tariff rules and integration with durable per-fill allocation. Ambiguous QUANTITY/NOTIONAL rules remain fail-closed; PR #6 draft/unmerged; live broker writes disabled.

## Upstox read-only charge APIs — CI verified 2026-10-24
Added `get_brokerage_estimate` (`GET /v2/charges/brokerage`), `get_trade_charges` (`GET /v2/trade/profit-loss/charges`) and `get_historical_trades` (`GET /v2/charges/historical-trades`) to the existing fixed-path read-only Upstox client. Added mocked contract tests for query parameters, input validation, segment/financial-year/date scope, pagination and the DP-plan minimum metadata. Exact-head CI run `40064514873` passed on `5026e95e56ae52c40b238bc29c194ceae26c7898`: 744 passed, 1 warning. No live account call was made. Next: persist API estimates as immutable estimate-only snapshots with response provenance, then compare against reviewed actual evidence without converting estimates/aggregates into actuals. Current effective-dated tariff findings are recorded in `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`; rates remain inactive until reviewed and tested.

## Upstox immutable estimate snapshot integration — 2026-10-24 (CI verified)
Added `build_upstox_brokerage_api_snapshots` to normalize the official API response into component-level immutable estimate payloads, preserving request parameters, v2 endpoint, UTC retrieval time, canonical response JSON + SHA-256, total and DP-plan name/minimum. Persistence reuses `TariffEstimateSnapshotRecord` and the existing append-only/idempotent service. Variance comparison verifies response integrity and requires API request quantity, price, side and instrument to match the exact reviewed fill set. Added normalization, persistence/replay, malformed response, provenance tamper and fill-input mismatch tests. Exact-head CI run `40065219626` passed on commit `2c23ebfeb9d0d843620dc6dcf54b7279bb112662`: **754 passed, 1 warning**. Next: continue source-backed effective-dated tariff rules and approved per-fill integration.

## Flat per-order brokerage rule support — 2026-10-24 (CI verified)
Added explicit `ORDER_FIXED` + `INR_FIXED` support to the order brokerage calculation path and estimate snapshot builder, for flat per-executed-order brokerage. Existing `ORDER_NOTIONAL` percentage rules with embedded caps remain supported. Added tests for flat fee calculation and snapshot generation. No rates were activated. Exact-head CI run `40065607232` passed on `30db9920f640203c1045f1cb045d955bb41b5f86`: **756 passed, 1 warning**. Next: create a dated official-source excerpt archive and candidate effective-dated tariff rules in non-active review state, then test applicability boundaries.

## Upstox tariff source snapshot and DRAFT candidate registry — 2026-10-24 (CI verified)
Archived a dated normalized excerpt in `docs/source_snapshots/UPSTOX_CHARGES_2026-10-24.md` (canonical payload SHA-256 `c59f7e940fde6b0d94ca1189766f16e5601c117d4a8c2bcd2415da0ecd6db420`) and added 18 effective-dated candidate rows for STT and exchange charges. All candidate rows are deliberately `DRAFT`; no rate is active. NSE's official derivatives STT page corroborates the April 2026 futures/options/exercised-option rates. Stamp duty source is dated 2023 and requires current corroboration; exchange/IPFT combination needs review. Exact-head CI run `40065979244` passed on `f76ecde4ac785123de2980539138ce89ff660294`: **760 passed, 1 warning**. Next: source archive/review completion, explicit component applicability and boundary tests; keep auto-allocation fail-closed.


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

## Upstox estimate component-total reconciliation — 24 October 2026

- Latest code change `ce0d426142b8e70b5cd56d0832694a397258f563` adds a fail-closed check that normalized Upstox brokerage API estimate components sum to the API-reported total; the DP-plan minimum remains metadata and is excluded from the sum.
- Test commit `8136ccdabbc5326d59e2b8a6951ae02c3495ab62` adds regression cases for component/total mismatch and null-versus-zero distinction. Missing/null amounts are rejected rather than coerced to zero.
- Exact-head CI run [40082403073](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40082403073) was still in progress at this checkpoint; do not mark this change green until the run for the resulting latest head completes.
- This is estimate integrity only: no tariff rates were activated, no estimate promoted to actual charges, no per-fill charge allocation enabled, and no live broker orders sent. PR #6 remains draft/unmerged; original `Tradepro` remains out of scope.

## Upstox reconciliation CI failure and fixture correction — 24 October 2026

- CI run [40082403073](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40082403073) failed with **774 passed, 1 failed**. The failure was in `test_upstox_api_estimate_is_stable_for_exact_replay_but_response_changes_conflict`: its changed-STT fixture changed a component but left the aggregate `total` unchanged, so the new reconciliation guard correctly rejected it before the test reached replay-conflict handling.
- Corrected the test fixture to change the reported total consistently with the STT delta, preserving the intent of the replay-conflict test. Commit: `2a39a67cd1d2c8dab16e22425c87e247974c10cd`.
- A fresh backend CI run [40082588488](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40082588488) was queued for the corrected head. Do not mark the gate green until it completes and the final docs head is verified.
- The failure was a test-fixture inconsistency, not evidence that the reconciliation check should be weakened. Keep the guard fail-closed.

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


## 2026-10-24 — NSE IPFT representation reconciliation

- Researched current Upstox tariff page, Upstox Brokerage Details and Trade Charges API documentation, NSE Circular NSE/FA/73061 (27 Feb 2026, effective 1 Mar 2026), competitor tariff/support documentation, and historical trader forum discussions.
- Resolved the official rate arithmetic for NSE cash, equity futures, and equity options on premium: transaction-only ₹306.99/₹182.99/₹3,552.99 per crore plus IPFT ₹0.01 per crore, totals ₹307/₹183/₹3,553 per crore respectively.
- Upstox's current public percentages 0.00307%/0.00183%/0.03553% are the combined totals for these three scopes; do not add another ₹0.01/crore on top.
- Added detailed source-backed normalization policy and acceptance tests to `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md` in commit `295535e032a7ea542b67766c17e5186a83d54409`.
- Remaining: verify the authenticated Upstox API fields against a dated actual contract note/invoice; test combined-vs-split representation conflicts, nullable/missing/zero values, GST base invariance and cross-segment scope. BSE/MCX/currency/commodity are not covered by the NSE equity resolution.
- No tariff activated; API field mapping remains fail-closed pending tests and independent review. PR #6 remains draft/unmerged; live broker order submission remains disabled. Work remains limited to `tarunsharma2610-del/tradepro-improved`.

## 2026-10-24 — IPFT combined-rate regression coverage

- Added regression tests in `backend/tests/test_broker_tariff_rules.py`, commit `69945f4854ea8ae7d20e7795b156750406759df7`.
- Tests verify NSE combined exchange-charge candidate rates for cash equity, equity futures and equity options; confirm candidates remain DRAFT with no second IPFT tariff candidate; prove combined-vs-split representations yield the same GST calculation base; and guard against MCX scope leakage.
- Updated `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md` in commit `626298aa9d8c60712189a744c86a3327eac1bb50`.
- These tests prove internal rule consistency only. Authenticated API field semantics and account-specific contract-note/GST mapping remain unverified; BSE/MCX/currency tariff schedules need their own dated authoritative sources.
- Latest documentation/test head requires exact-head CI verification. Tariffs remain DRAFT/non-selectable, PR #6 stays draft/unmerged, and live broker order submission stays disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope.


## 2026-10-24 — IPFT checkpoint CI verified

- Exact-head CI passed for `a8166bafe77544bf958d0d393b71432379898b72`: workflow #40101490646, Backend pytest **805 passed, 1 warning**; broker-write guard, SQLite/PostgreSQL 16 migration round-trips and synthetic restore drill/evidence retention passed.
- Workflow: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40101490646
- This does not resolve authenticated Upstox API `transaction`/ `ipft` field semantics or account-specific GST reconciliation. NSE cash/equity futures/equity options rate arithmetic remains resolved only within the documented scope.
- Continue with API field normalization fixtures and evidence mapping; candidates remain DRAFT/non-selectable. PR #6 stays draft/unmerged; live broker writes remain disabled. Only `tradepro-improved` is in scope.


## Historical Upstox statement evidence — 24 October 2026

- Reviewed user-provided redacted screenshot of page 2 of an RKSV/Upstox Annual Global Transaction Statement for FY 2022–23, Futures & Options. Visible lines: IGST ₹20.15, SEBI fees ₹0.22, stamp duty ₹3.00, STT-RND ₹0.32, STT-SQUP ₹51.89, transaction charges ₹111.61, brokerage ₹1,000.00.
- No separate IPFT line is visible in the annual summary. This does not prove IPFT was included in transaction charges; annual statement presentation may aggregate or omit components. The screenshot is not an individual trade contract note and does not provide sufficient machine-readable turnover/API evidence to establish field semantics.
- Recorded limitations and safe evidence use in `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`, commit `9bb2fade8330e068022e5b2f6be0538e4f19206e`.
- Next: if available, reconcile original PDF + matching dated API response against historical segment rates and turnover/premium. Do not promote per-fill actual allocations from this statement alone. Tariff candidates remain DRAFT; PR #6 remains draft/unmerged; live broker writes remain disabled.

## IPFT research implementation checkpoint — 24 October 2026

- Clarified the effective-dated NSE rule in the source register: from 2026-03-01, the listed NSE equity delivery/intraday, equity futures, and equity options exchange-charge rates are combined outflows including the revised IPFT contribution. Do not add IPFT again on top.
- The existing candidate registry and tests already encode the combined rates and assert no separate `ipft` candidate; all candidate rules remain DRAFT/non-selectable.
- Source register update: commit `6c85292d07d33e1e873293c40931895674f4e7fc`.
- Still open: exact-head CI for the new docs commit; API `transaction`/ `ipft` response normalization for missing/null/numeric cases; independent approval and GST component mapping; BSE equity scrip groups and MCX source-backed rates. PR #6 remains draft/unmerged and live broker writes remain disabled.

## Public charge schedule cross-check — 24 October 2026

- Rechecked Upstox's official Brokerage Details API and Get Trade Charges API. They serve different purposes: order-specific estimate vs segment/FY aggregate charge summary. Preserve absent/null/zero/numeric IPFT values distinctly; a null aggregate sample is not proof of zero or of bundling.
- Added BSE/MCX scope cautions and public broker schedule cross-check to UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md in commit 2f6e55532e9704d4b41c9c736c38b1948ee5f05d. BSE scrip/index variations and MCX rates remain research leads until matched to governing exchange circulars.
- CI on this new docs head has not yet been confirmed. All tariff candidates remain DRAFT/non-selectable; PR #6 draft/unmerged; live broker writes disabled; original Tradepro untouched.

## BSE / MCX tariff review checkpoint — 24 October 2026

- Checked official BSE cash-equity master circular, BSE Notice 20231020-46, MCX circular archive, and MCX compliance FAQ. Recorded the current findings and strict scope limitations in UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md, commit f978052402b2be79d99958427092a29eace83859.
- Key implementation consequence: BSE scrip-group charges require dated scrip/exclusivity metadata; nearest-expiry SENSEX options require monthly cumulative turnover slab state; MCX rates require exact effective-dated product schedules and separate CTT/stamp/GST bases. The reviewed sources do not justify activating generic BSE/MCX rates.
- CI for this new documentation head is pending verification. All tariff candidates remain DRAFT/non-selectable; PR #6 draft/unmerged; live broker writes disabled; original Tradepro untouched.


## 2026-10-24 — Phase 3 exact-head CI and acceptance audit

- Rechecked open PR #6 metadata: head `5e256bc867409672a19025f0219c9d9c866ce898`, base `main`; PR remains draft and unmerged. Exact-head Backend tests workflow #40105708790 completed successfully on that head.
- Existing per-fill acceptance tests are present for exact eligible-fill identity, reviewed-weight validation (including malformed IDs, invalid/non-finite/negative weights, all-zero weights and duplicate IDs), source-total and per-fill amount matching, evidence/document integrity, idempotent promotion, authorization recheck, outer rollback, promotion flush failure, and variance-only comparison including order/fill-set scope, tamper detection, source-state revalidation, aggregate API evidence rejection, and variance insert failure rollback.
- These tests validate fail-closed workflow and internal consistency, not correctness of a real account's charge allocation basis or live broker tariff. Automatic QUANTITY/NOTIONAL allocation remains disabled; explicit reviewed weights are required. Tariff candidates remain DRAFT/non-selectable.
- Remaining Phase 3 gates: (1) independent accounting acceptance of the component-by-component policy and rounding/residual semantics; (2) authoritative, effective-dated tariff evidence for each supported exchange/segment/product and approved GST component mapping; (3) independent review of the completed acceptance matrix; (4) final PR review/merge decision. The FY 2022–23 annual statement screenshot does not establish per-fill API semantics or IPFT inclusion.
- Safety/scope unchanged: PR #6 stays draft/unmerged; live broker order submission stays disabled; only `tarunsharma2610-del/tradepro-improved` is in scope. Original `tarunsharma2610-del/Tradepro` must remain untouched.


## 2026-10-24 — Charge component acceptance matrix added

- Added docs/PHASE3_CHARGE_COMPONENT_ACCEPTANCE_MATRIX.md. It defines shared evidence/provenance, fill-set, decimal rounding/residual, replay/rollback and variance-only controls, plus component-specific gates for brokerage, STT, exchange/IPFT, SEBI, stamp duty and GST.
- Matrix explicitly separates settled NSE combined-rate arithmetic from unresolved Upstox API semantics, account-specific invoice treatment, BSE scrip/product scope and MCX product rates. It does not activate tariffs or enable automatic allocation.
- Previous docs-only head 8a75153 had successful Backend workflow #40106273353. The new matrix head ac89f9ce84544ff4f53cb58bdf18e247d19177c9 is pending exact-head CI in workflow #40106537998; do not mark the matrix head green until that run completes.
- Next: inspect exact-head CI, then use the matrix as the checklist for the remaining implementation/review gaps. PR #6 remains draft/unmerged; live broker writes disabled; original Tradepro untouched.


## 2026-10-24 — Broker charge API field-state normalization

- Added `backend/app/services/broker_charge_api_normalization.py` and regression tests in `backend/tests/test_broker_charge_api_normalization.py`.
- The helper preserves `MISSING`, `NULL`, `ZERO`, `VALUE`, and `INVALID` states and retains the raw JSON value; valid values are represented as Decimal strings. Boolean, object/list, non-finite, negative and malformed numeric values fail into `INVALID` rather than being coerced.
- This is a lossless normalization primitive only. It does not infer whether `transaction` includes IPFT, whether a response is aggregate vs per-fill, or whether a number is an actual charge. Those semantics still require a versioned, reviewed mapping and source evidence.
- Matrix-head CI passed in workflow #40106582037 for commit f33953e903dcdd8655fa34eee9c612a36bd94b2c. New helper/test commits are newer and need exact-head CI before being marked verified.
- Safety unchanged: candidates remain DRAFT/non-selectable, generic quantity/notional allocation disabled, PR #6 draft/unmerged, live broker writes disabled, original Tradepro untouched.


## 2026-10-24 — Reviewed API field mapping gate

- Backend workflow #40106757433 passed on the API field-state normalization test commit; all pipeline gates completed, including backend pytest, broker-write boundary, SQLite/PostgreSQL migration round-trips and synthetic restore/evidence retention. This is not CI for later commits.
- Added `backend/app/services/broker_charge_api_mapping.py` and tests `backend/tests/test_broker_charge_api_mapping.py`. Mapping selection requires exact broker, endpoint, schema version, field path, scope and effective date, plus `APPROVED` review state; missing/overlapping mappings and `UNKNOWN` semantics fail closed.
- The module is a registry/guard, not an approval of any Upstox field's actual semantics. Current fixture values are synthetic only. No production mapping was added or approved, and aggregate charges remain prohibited as per-fill actual evidence.
- Exact-head CI is required for the new mapping code/tests and subsequent docs. PR #6 remains draft/unmerged; tariff candidates non-selectable; automatic quantity/notional allocation and live broker writes disabled.


## 2026-10-24 — API mapping guard CI verification

- Verified Backend workflow #40106949357 passed on mapping-test commit `3a04aefc7e8bb9c0cf8e99889c5de89b4537dc63`; Backend workflow #40106989369 also passed on source-register documentation commit `cee4fa0fbd4eefc0850d26119bdc6fa11e3915a`.
- This verifies the mapping guard and field-state normalizer code/test commits are covered by successful CI, but does not mean every later documentation commit has exact-head CI. Re-run CI on the final current branch head before a merge decision.
- Review conclusion: API mapping guard is intentionally not wired to infer or auto-approve production Upstox field semantics. No live mapping has been approved. The next implementation gate is linking normalized API values to the exact approved mapping only at a controlled accounting boundary, with fail-closed rejection of aggregate data for per-fill actuals.


## 2026-10-24 — Controlled API value resolution

- Added `backend/app/services/broker_charge_api_value_resolution.py` and `backend/tests/test_broker_charge_api_value_resolution.py`.
- The resolver combines the field-state normalizer with exact approved mapping selection. It rejects aggregate summaries, estimates and component-only semantics when intended use is per-fill actual; preserves missing/null/invalid as unusable; and keeps numeric zero distinct from missing/null. It returns mapping provenance and does not promote ledger allocations.
- Synthetic fixtures use a reserved example.invalid URL and are tests only, not evidence of Upstox's live API semantics. No production field mapping was approved.
- Prior mapping and source-register commits passed workflows #40106949357 and #40106989369 respectively. Exact-head CI for this resolver and final documentation updates is still required.


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

- Backend workflow `40108183667` succeeded on prior head `8214430f562f6f425cfc1b9b6a6b3b547832b68a`. New resolver tests add exact broker/endpoint/schema/field/scope matching and non-finite-number rejection; newer commits still require CI.
- Mapping identity fixtures use immutable dataclass replacement. Intended-use semantics remain explicit; missing/null/invalid values remain unusable and retain provenance; numeric zero remains distinct.
- Accounting acceptance includes replay/conflict, ledger reconciliation, lock order, rollback, reviewer authority and PostgreSQL verification/promotion race coverage. Re-check exact test and workflow status before claiming complete. CI does not establish production tariff correctness or broker-origin authenticity.
- Safety gates unchanged: PR #6 draft/unmerged; live broker order submission and automatic quantity/notional allocation disabled; production Upstox mappings/tariffs unapproved. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Resolver field-identity guard added; CI pending

- Resolver now checks that the payload field name matches the terminal field in the selected approved mapping path. This closes a semantic mismatch where a caller could select `charges.ipft` but normalize another payload field.
- Implementation commit: `77aa77aec37dc535c3e427ca3f88c2ccb5e75ed8`; regression test commit: `5c5482c7f7fa623707698f64b6a061351e5e5b87`. CI for the latest commits is pending; previous green runs apply only to earlier heads.
- Existing accounting tests cover lock ordering, replay idempotency, conflicting evidence and rollback. A genuine concurrent two-session verification-versus-promotion race is not demonstrated in the inspected live-fill test file; locate/verify other integration coverage before marking complete.
- PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled; production Upstox mappings/tariffs remain unapproved. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Latest resolver CI verified; PostgreSQL race coverage located

- Latest PR head `ed346e823cbfae8448fae0134c4ff864bfcc60ac` passed Backend workflow [#40109041654](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40109041654). This verifies the field-identity guard and regression test at that head.
- Located PostgreSQL-only integration tests in `backend/tests/test_broker_charge_allocation_postgres_concurrency.py`, including concurrent source verification vs allocation promotion and live-fill promotion vs ledger verification, as well as conflicting fill-set and tariff estimate/variance persistence races.
- These tests require `TEST_POSTGRES_URL`. Verify the PostgreSQL workflow actually ran these tests rather than skipped them before treating concurrency acceptance as complete.
- PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled; production Upstox mappings/tariffs remain unapproved. Work only in `tradepro-improved`; original `Tradepro` remains untouched.


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

## Upstox SDK and Agent Skill review — 24 October 2026

- Completed a static source compatibility review of official `upstox-python` tag `v2.30.0` and the official Agent Skill. Details: [SDK/API repository audit](docs/UPSTOX_SDK_API_REPOSITORY_AUDIT.md) and [Agent Skill security review](docs/UPSTOX_AGENT_SKILL_SECURITY_REVIEW.md).
- SDK finding: generated `ChargeApi.get_brokerage` is synchronous by default (thread-based `async_req` is available). Existing async `httpx` read-only client and validated response parser already cover this endpoint, so no runtime SDK dependency was added without a demonstrated benefit.
- Skill finding: upstream helper can fall back to local `config.json` credentials and prints raw API exception body in its smoke-test path; order and GTT examples can perform real broker writes. Do not run these examples with live credentials or use skill confirmation as our safety boundary.
- No SDK/skill code was executed; no credentials, live calls or orders were used. This was a static source review, not a runtime SDK integration test.
- Next: continue the Phase 3 durable per-fill charge-allocation gates; consider SDK runtime integration only if a concrete endpoint/schema gap is identified. PAPER mode and live-write restrictions unchanged.

---


## Phase 3 checkpoint — official GST/IPFT source cross-check (25 October 2026)

- Resumed the saved Phase 3 durable per-fill charge-allocation work. No framework code was integrated; current focus remains source-backed tariff acceptance and fail-closed accounting.
- Exact-head backend CI for prior head `7d4f2918b534ef9b4c3d32e7df22b754b21e6c8f` passed in run [40182196510](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40182196510). This verifies that head, not real-broker tariff authenticity or production restore.
- Current official Upstox charges page lists transaction charges effective 1 March 2026, STT effective 1 April 2026, GST bases by product, and says IPFT is combined with transaction charges while also showing an IPFT row. This does not establish whether a particular API `transaction` field is transaction-only or transaction-plus-IPFT. Do not double count IPFT or approve a field mapping until exact endpoint/schema semantics are verified.
- NSE confirms from 1 April 2026: options-sale STT 0.15% on premium (seller), exercised-option STT 0.15% on intrinsic value (purchaser), and futures-sale STT 0.05% (seller). CBIC says STT/stamp-duty/other-tax recoveries are outside GST value only where pure-agent conditions are met; otherwise Section 15/Rule 27 valuation applies. GST mapping must remain product/source-specific.
- No production field mapping or tariff was approved. Keep candidates DRAFT/non-selectable, preserve missing/null/zero distinctions, reviewed source-component evidence, paise-exact allocation, and fail-closed promotion. PAPER mandatory; live broker order writes disabled; PR #6 draft/unmerged; original `Tradepro` untouched.
- Official sources: https://upstox.com/brokerage-charges/ ; https://upstox.com/developer/api-documentation/get-brokerage/ ; https://upstox.com/developer/api-documentation/get-trade-charges/ ; https://www.nseindia.com/static/products-services/equity-derivatives-securities-transaction-tax ; https://cbic-gst.gov.in/sectoral-faq.html
- Next gate: continue component-by-component accounting acceptance and fault-injection/rollback review. Upstox's proposed-order brokerage calculator and segment/FY aggregate charges API are not proof of actual per-fill charges.

- Current Phase 3 status: exact-head CI verified on prior head; GST/IPFT source interpretation remains unresolved for API field semantics; no tariff activation authorized.


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

### Phase 3 — explicit source-label association (2026-10-25)

Implemented a fail-closed association between each normalized charge component and its retained original source label. The representation validator now requires exact component-key coverage and checks label uniqueness/order; the contract-note review API supplies the explicit mapping from persisted rows. Added regression tests for missing, mismatched and wrong-component associations. Commits: `79dd66d8c429498501e9edfb35e73a1ca0b756b4`, `0146ecd75f0e6a625b21761d3195c896bba293f7`, `fb147a3c5580091574bc71c35e7a641cf7386935`. **Verification pending:** exact-head CI must pass before this is counted as a completed acceptance step. See `PHASE3_PROGRESS_REPORT.md`.

### Phase 3 — do not fabricate absent source labels (2026-10-25)

The source-component intake no longer substitutes the normalized component name when the original source label is absent. Missing labels remain missing, and review fails closed while keeping the component pending. Added an API regression test and supplied explicit labels in success fixtures. Commits: `460c9bba1a9cb6240ccdf86d39087107fe23589f`, `34e3d3e865660f96b432968565f2b8ceeb9c9184`. **Exact-head CI pending**; see `PHASE3_PROGRESS_REPORT.md`.

### Phase 3 — source-label authenticity guard verified (2026-10-25)

Missing original labels are no longer fabricated from normalized component names; review remains fail-closed and preserves existing authorization/fill-validation ordering. Implementation SHA `b92d0185f588e24d54510b36659944e77f498a6e` passed [CI #40189481491](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40189481491): 911 passed, 1 warning, 0 failures. Documentation SHA `704d9d5caa8a893195d5213ae38b97c30639de96` passed [CI #40189515861](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40189515861). The current progress-report synchronization commit still needs its own exact-head CI check. Authentic source review remains outstanding.



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
- Approved public Upstox STT/exchange rules are estimate-only. Account-specific actual charges, GST taxable-base composition, stamp duty, SEBI/DP/demat/other charges, unsupported exchange/segment mappings, and per-fill actual evidence remain unapproved. Candidate tariff entries remain DRAFT unless separately allowlisted and reviewed.
- Phase 3 remains in progress. Next gates: independently reviewed tariff applicability; component-specific per-fill allocation rules; invoice/source-backed GST/IPFT and product/segment evidence; final adversarial, migration and recovery review; exact-head acceptance sign-off. Do not repeat canonical live-fill integration.
- Safety: PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. PR #6 stays open/draft/unmerged without explicit user approval. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.
- This documentation commit’s CI is green. Continue only from this checkpoint and verify CI for every subsequent implementation/checkpoint commit. Historical entries do not supersede this checkpoint.


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


## GST/IPFT verification research checkpoint — 26 October 2026

- Research artifact: [docs/UPSTOX_GST_IPFT_VERIFICATION_2026-10-26.md](docs/UPSTOX_GST_IPFT_VERIFICATION_2026-10-26.md).
- Official Upstox public schedule and API docs, NSE circular NSE/FA/73061, CBIC stock-broking FAQs/valuation rules, and public historical contract-note examples were reviewed.
- Supported: 18% as Upstox's published GST rate; NSE combined transaction/IPFT outflow effective 2026-03-01 of ₹307/crore cash, ₹183/crore futures, ₹3,553/crore options premium, with ₹0.01/crore IPFT included. Do not double-count IPFT on top of the combined charge.
- Not approved: GST taxable-component sets for delivery/intraday/futures/options; BSE cash scrip-group/futures assumptions; stamp duty, SEBI, clearing/other and DP/demat tax-base composition. Public historical notes are unauthenticated and not current proof; API aggregate charges do not prove per-fill values. `ipft: null` is unknown, not zero.
- Next: targeted tests for combined-vs-split IPFT, null field semantics, effective-date boundaries and GST-base component guardrails; then exact-head CI. Do not enable production tariff or automatic per-fill allocation from this research alone.
- Safety unchanged: PAPER mandatory; live broker order writes and automatic live-fill promotion disabled; PR #6 open/draft/unmerged; original `Tradepro` untouched.


## Phase 3 CI failure and correction — 26 October 2026

- Exact tested PR merge ref for branch head `8f37b81914e1b46318d16d7c99ee5490449e8f06` failed backend pytest: **1,002 passed, 1 failed**. The sole failure was a brittle wording assertion in `test_gst_candidate_remains_draft_when_historical_note_conflicts_with_current_public_base`; the evidence text correctly described the note as “materially different from Upstox's current public pricing page”, while the test expected different wording. This was a test/evidence-text mismatch, not a GST candidate approval or calculation failure.
- Corrected the assertion in commit `f792627fb0ead15551e2506731b183e9b91482bb`. The resulting head's CI must be verified before claiming green; this checkpoint is not yet accepted.
- GST component sets remain DRAFT. The historical note is unauthenticated and not current proof; do not guess the taxable base. Safety remains unchanged: PAPER mandatory, live broker writes and automatic live-fill promotion disabled, PR #6 draft/unmerged, original `Tradepro` untouched.


## Public GST evidence follow-up — 26 October 2026

- Additional public searches found third-party indexed Upstox realized-P&L reports for FY 2025–26 and an Oct–Nov 2025 F&O period. They show GST and IPFT as separate aggregate report totals, but do not reveal the taxable-value component breakdown. A July 2026 Reddit discussion is anecdotal and cannot be used as a tariff authority.
- Re-read CBIC FAQ Q7/Q77: Section 15 valuation generally includes taxes except GST unless pure-agent Rule 33 conditions are met; the specific stockbroker recovery question likewise makes exclusion conditional. A fee label alone cannot settle the taxable base. Current official tariff wording and historical invoice copy remain unreconciled.
- Result: research broadened, but no approval. All four GST component sets stay DRAFT. No tax calculation or live accounting behavior changed. Exact-head CI must pass after the latest correction/documentation commit before the checkpoint can be called green.


## Follow-up correction to brittle evidence assertion — 26 October 2026

The first wording-only assertion adjustment still failed because the exact phrase in the evidence document is split by Markdown emphasis (`**materially different**`). Updated the regression test to assert the stable semantic phrase `materially different` rather than formatting-sensitive exact markup. This is a test-only wording fix; the evidence finding and all GST candidate DRAFT statuses are unchanged. The current exact-head CI run must pass before the checkpoint is accepted.


## Contract-note search findings and GST implementation direction — 26 October 2026

Located and reconciled three public Upstox contract-note copies. Historical printed bases differ: Feb 2025 ₹2.97 (brokerage ₹2.96 + turnover ₹0.01) -> IGST ₹0.53; May 2024 ₹77.56 (brokerage + SEBI + turnover + demat) -> IGST ₹13.96, with IPFT separately listed outside the base; March 2025 brokerage-only ₹2.75 -> IGST ₹0.50. Arithmetic rounds correctly. The copies are not authenticated/current, so they show historical billing presentation rather than a single universal/current actual-charge rule. For current public-schedule estimates, use Upstox's current official rule: 18% on brokerage + transaction charges + demat + IPFT, with IPFT included exactly once in the canonical combined transaction charge. Do not include SEBI in this current estimate base absent current source support. Actual per-fill GST remains gated on reviewed current invoice evidence.


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


## GST/IPFT continuation — 26 October 2026 (new draft branch; CI pending)

- Created branch `phase3/cross-broker-gst-ipft-resolution` from the existing Phase 3 branch; created Draft PR #7: https://github.com/tarunsharma2610-del/tradepro-improved/pull/7
- Added `docs/CROSS_BROKER_GST_IPFT_POLICY_RESEARCH_2026-10-26.md` with official NSE circular, CBIC pure-agent boundary, and broker-published Upstox/Zerodha/Angel One/Groww source observations.
- Added `backend/app/services/broker_gst_component_policy.py`: fail-closed exact-scope/effective-date policy selection; DRAFT policies cannot calculate; explicit component sets; combined/separate/not-applicable IPFT modes prevent duplicate representations; finite nonnegative decimal inputs and paise rounding.
- Added `backend/tests/test_broker_gst_component_policy.py` for IPFT mode validation, effective-date selection, duplicate/ambiguous rules, invalid amounts and exact component sets.
- **Not yet complete:** the new generic policy primitive is not yet wired into the existing Upstox estimate path; cross-broker candidates remain unapproved; canonical DP/demat persistence/migration is still a separate accounting gate; exact-head CI has not yet reported a run for the new PR head. Do not call this a completed GST fix until integration, tests and CI pass.
- Safety unchanged: PR #6 stays Draft/unmerged; PAPER mandatory; live broker writes disabled; original `tarunsharma2610-del/Tradepro` untouched; no personal contract note requested.


## GST/IPFT CI failure and fix — 26 October 2026

- CI run #40358027077 on prior head `59bdfd2cc66768eff882cdc1ffd00a9dade9c015` failed with 1 test failure and 1,023 passing. Failure was a test assertion expecting the wrong validation message (implementation correctly raised `SEPARATE IPFT mode requires...`); corrected the assertion.
- Routed `calculate_upstox_public_gst_estimate` through the shared `GstComponentPolicy` / `calculate_gst_estimate` policy module. IPFT mode is now `COMBINED` for NSE and `NOT_APPLICABLE` for the supported BSE options scope, avoiding an incorrect NSE-IPFT assumption for BSE.
- New implementation head: `393804cc5c21ba70a579b32a6736f6561569413b`. Exact-head CI result has not yet been returned; do not mark passing until checked.
- Still open: source-backed candidate/test coverage for other brokers, canonical DP/demat persistence/migration, and final exact-head passing CI. No tariff candidates activated. PR #6 remains Draft/unmerged; PAPER mandatory; live broker writes disabled; original Tradepro untouched.


## Phase 3 GST/IPFT update — user-supplied Upstox scenarios (2026-10-26)

- Added conservative Upstox contract-note text extraction and tests for NSE-EQ, NSE-F&O, NSE-CD and MCX tags; brokerage, transaction/exchange, SEBI, IPFT, DP/demat, clearing, STT, stamp duty and CGST/SGST/IGST labels; duplicate detection; and unmapped charge-like lines.
- Extracted line items are evidence only. No GST base is inferred, no duplicate line is silently overwritten, and no unknown component is silently dropped.
- Removed the implicit accounting-approval flaw in the Upstox public GST estimate helper: public schedule estimates no longer instantiate an accounting policy with `review_status="APPROVED"`.
- User-provided examples are not treated as approved tax law. Upstox's published GST formula states brokerage + transaction + IPFT, adding demat for equity delivery; it does not list SEBI in that formula. Its current public DP charge is ₹20 per scrip/day on delivery sells. The pasted ₹18.50 DP base and SEBI-in-GST-base claim remain unaccepted pending stronger evidence.
- Still blocked: canonical DP/demat accounting persistence/migration/allocation; verified dated MCX and NSE-CD tax-component matrix; independent tariff approval; actual per-fill invoice evidence. User is not required to provide a personal contract note.
- Exact-head CI for the latest implementation is pending; do not mark the change green until Actions confirms success.
- Safety unchanged: target repository only is `tarunsharma2610-del/tradepro-improved`; PR #6 and PR #7 stay Draft/unmerged; PAPER mode mandatory; live broker writes disabled; original `Tradepro` repository untouched.

## DP/demat canonical mapping follow-up — 26 October 2026

- Added optional `demat_transaction_charges` canonical mapping when a reviewed source row explicitly exists. Absence remains absent/unknown, not zero.
- Added deterministic per-fill allocation-plan support and tests for the separate DP/demat component; output remains `accounting_approved=False` and `persisted=False`.
- **Still not complete:** `Execution` database model/migration, DP/demat total-charge recomputation, persistence/promotion lock path, idempotency and delivery-vs-non-delivery tests. Actual delivery accounting remains blocked.
- Exact-head CI for these latest mapping/allocation changes and this document sync is pending verification.
- PR #6 and PR #7 remain Draft/unmerged; PAPER only; live broker writes disabled; original Tradepro repo untouched.

## DP/demat live-boundary correction — 26 October 2026

- The first DP/demat canonical mapping attempt failed exact-head Backend CI run #40362669264 (45 failed, 989 passed). Root cause: the optional component widened the existing six-component source mapping consumed by the live snapshot service, causing broad live-fill promotion tests to fail.
- Corrected the interface: the six-component `source_components_by_canonical` remains unchanged; optional DP/demat evidence is exposed separately as `optional_source_components_by_canonical`. Non-persisted allocation planning can use that optional mapping.
- The live canonical snapshot service now explicitly blocks promotion when DP/demat evidence is present until Execution persistence and total-charge reconciliation support it. This prevents silent dropping and preserves existing six-component live accounting.
- Re-run exact-head CI and checkpoint only after green. Current head is not yet verified.


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


## 27 October 2026 — API integration continuation

**Current focus:** wire existing Upstox charge API methods into the Phase 3 reconciliation/accounting boundary. The client already exposes a brokerage calculator endpoint (estimate-only) and a post-trade trade-charges endpoint (aggregate-only). Source-level guards, approved mapping resolver and public GST estimate helper exist; API-to-accounting orchestration is not yet verified complete. Next: inspect call sites and response schema, implement typed normalization/reconciliation with exact approved mapping/provenance, preserve missing/null/invalid/zero, reject aggregate-to-per-fill promotion, prevent transaction/IPFT double count, add focused tests, run exact-head CI, then synchronize docs. GST/IPFT research is not restarting; ₹20.15/₹0.02 historical discrepancy remains unexplained and must not block this integration. Safety remains PAPER mandatory, live broker writes disabled, PR #6/#7 Draft/unmerged, original Tradepro out of scope.


## 27 October 2026 — first API orchestration code increment

Added a typed wrapper for the existing read-only Upstox brokerage calculator and trade-charges APIs. It explicitly labels the calculator as estimate-only and the post-trade charges API as aggregate-reconciliation-only, sets `per_fill_actual=False` for both, preserves null IPFT and avoids returning failed API payloads as usable evidence. Added focused tests. This is a safe first integration seam; end-to-end route/ledger wiring remains incomplete. Latest code/test head before documentation sync: `f98ed9e7f4b092c6d8e284d7461ee4aba46b72e4`; CI lookup returned no status/workflow rows, so exact-head CI is unverified. Next: connect the wrapper to the existing read-only reconciliation route and persist aggregate context only, then run backend/safety/migration/restore CI and update the checkpoint from the exact green commit.


## 27 October 2026 — authenticated API route wiring

Added authenticated read-only endpoints `GET /api/v1/upstox/charges/brokerage-estimate` and `GET /api/v1/upstox/charges/aggregate`, registered in the API router. The handlers fetch only the authenticated user's Upstox connection and decrypt the access token server-side. The estimate stays estimate-only; the post-trade charges response stays aggregate-reconciliation-only; neither can be used as per-fill actuals. Prior CI passed on `6021815de9bfa1213320daafb4eda866c93f3ec9`; route/router CI runs #40473791107 and #40473806635 were in progress/queued at last check, so latest-head CI is not yet green. Remaining immediate work: route-level auth/token/error tests, verify exact-head CI, then review whether aggregate reconciliation context can be safely persisted. No live order writes added.


## 27 October 2026 — route tests and CI

Added route-level tests for the authenticated Upstox charge API endpoints: estimate/aggregate semantics, null IPFT preservation, and validation. Prior CI run #40473895336 passed on `24b7b9ee728049f26b200cbee54571ae3c22b7bf`; new test commit `ffb87c9af7c87d921eadf0198b7ba8704be65e76` still needs exact-head CI. Next: check the workflow, fix failures, then review the existing reconciliation/evidence model before any aggregate-only persistence. Keep aggregate results out of per-fill actual accounting.


## 27 October 2026 — verified API route CI and next persistence design

- Route-test commit `ffb87c9af7c87d921eadf0198b7ba8704be65e76` passed Backend CI [#40474374635](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40474374635).
- Documentation commit `10d105a344b08a21dfe50593f8683453a5d44bfc` passed Backend CI [#40474444724](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40474444724). Later documentation commits are not covered by those runs unless CI confirms them separately.
- Existing charge-evidence models are specifically for integrity-checked source documents and independently reviewed source components. Do not store aggregate API replies as fake contract-note evidence.
- Next: implement a dedicated owner-scoped aggregate API reconciliation record/migration with endpoint/version, request scope, fetched-at/status, response provenance/hash and sanitized payload; preserve missing/null/invalid/zero states; test authorization, idempotency, privacy and SQLite/PostgreSQL migration round-trips. This record remains reconciliation-only and must not create per-fill allocations or approve actual accounting.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.



## 27 October 2026 — aggregate API reconciliation persistence implemented; CI pending

Added an immutable owner-scoped aggregate API evidence model and migration `202610270030`, wired into the authenticated Upstox aggregate charges endpoint. Persists endpoint/scope/fetch status, response hash, sanitized payload and idempotency key. The route returns a record ID; no per-fill actual allocation or accounting promotion is possible from this evidence. Route tests assert ownership linkage, token stripping and duplicate-fetch idempotency. Code/test commit: `77bb07c0b6ee075e5e1eaa61ab0a5d138475953b`. Backend CI #40475498978 and #40475479511 were running at last check; exact-head CI and migration/safety/restore gates remain unverified until they complete. Continue with CI inspection/fixes, owner-isolation and immutability coverage, then sync docs to the confirmed green head.


## 27 October 2026 — owner-isolation and immutability tests added

Added cross-owner isolation and immutable-snapshot regression tests in commit `688cb70e2d64b866fbb9b6f19c7675ab764a0ecf`. Prior implementation head `77bb07c...` passed Backend CI #40475498978 (pytest, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, synthetic restore); the new tests still require CI on the exact new head. Do not count the new coverage as verified until that run completes.


## 27 October 2026 — CI failure diagnosed and test corrected

CI on the new ownership/immutability regression coverage failed with 1 failed and 1128 passed. The cross-owner test created two users using the fixture's identical default email, triggering a unique-email constraint before the authorization check. Fixed with distinct emails in commit `977ad6b7e6eeae1346b28c03c2d83bb62ec93910`. Await exact-head CI; safety, migration and restore gates were skipped after pytest failed and must be verified on the passing run.


## 27 October 2026 — owner-isolation regression fix verified green

Corrected the cross-owner regression test to use distinct emails in commit `977ad6b7e6eeae1346b28c03c2d83bb62ec93910`. Backend CI #40476768203 passed all gates: pytest, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic restore and retained evidence. Documentation CI #40476805191 also passed. Resume Phase 3 acceptance with component applicability, fill identity/paise totals, replay/rollback and effective-dated tariff/GST/IPFT checks; this does not mark Phase 3 complete.



## 27 October 2026 — GST policy edge-case tests added; CI pending

Added tests at `91212a0224f3bf4a01bff06c14764a404c1cbc67` for explicit zero versus missing taxable component, invalid/nonfinite/negative values and effective-date end boundaries. Existing coverage already checks IPFT representation modes, scoped policy selection, conflicts and paise precision. Upstox candidates remain DRAFT pending resolution of conflicting source evidence. Exact-head CI is not yet verified; previous green remains `977ad6b7...` (Backend CI #40476768203; documentation CI #40476805191).



## 27 October 2026 — GST policy edge tests verified green

Commit `91212a0224f3bf4a01bff06c14764a404c1cbc67` passed Backend CI #40477899628, including pytest, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic restore and retained evidence. Documentation-triggered Backend CI runs #40477921259 and #40477930671 also completed successfully. The tests cover explicit zero vs missing components, invalid/nonfinite/negative amounts and effective-date boundaries. Upstox candidate approval and Phase 3 completion remain gated; continue targeted review of variance/replay/rollback and component applicability.



## 27 October 2026 — GST scope and rounding tests added; CI pending

Added tests in `c010b7d010351465b87f8e6d844fc9171dfc5dad` for paise-level GST half-up rounding and rejection of policy scope mismatches across broker/exchange/segment/product. Exact-head CI is pending; prior green remains `91212a0224f3bf4a01bff06c14764a404c1cbc67` with Backend CI #40477899628. Existing variance coverage already exercises fill-set identity, quantity/date mismatch, response digest and conflicting replay.



## 27 October 2026 — GST scope and rounding tests verified green

Code/test commit `c010b7d010351465b87f8e6d844fc9171dfc5dad` passed Backend CI #40478376361, including pytest, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, synthetic restore and retained evidence. New tests cover half-up paise rounding and exact broker/exchange/segment/product policy scope. Documentation CI #40478395488 was still in progress on commit `334a078...` at refresh; verify all latest docs heads separately. Continue accounting component applicability/rollback review and statutory GST/IPFT source resolution; this does not complete Phase 3.



## 27 October 2026 — latest docs-triggered CI runs verified green

The GST scope/rounding code-test head `c010b7d010351465b87f8e6d844fc9171dfc5dad` passed Backend CI #40478376361. Documentation-triggered runs #40478676089, #40478683982 and #40478691999 are now also fully successful, including pytest, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic restore and retained evidence. This update triggers new documentation CI which must be checked on its exact commits. Next inspect IPFT representation/component applicability and atomic rollback; statutory GST/IPFT candidate approval remains separately gated.



## 27 October 2026 — documentation CI reconciled; rollback coverage audited

Backend CI #40479126107 (commit `432a3d37...`) and #40479142058 (commit `3f29c70b...`) both passed all steps, including pytest, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips and synthetic restore. Commit `85ddf857...` had no workflow result in the current lookup. Review of live-fill tests found existing coverage for staged-row rollback, commit/flush failures, safe exact replay after post-commit refresh failure, IPFT canonicalization once, DP completeness and fill/replay identity. Next inspect source-to-canonical component mapping completeness for a concrete gap; avoid duplicate tests. Statutory GST/IPFT approval remains separately gated.



## 27 October 2026 — source-to-canonical mapping review

Documentation CI #40479568869, #40479578088 and #40479585940 passed. Review of the canonical planner and verified source canonicalizer confirms checks for unique source IDs, evidence/hash binding, VERIFIED status, independent reviewer, INR currency, source locator, shared fill manifest/fingerprint and explicit reviewed weights; allocation plans reconcile to source totals but remain unapproved and unpersisted. Split transaction/IPFT persistence is intentionally blocked because the current six-component schema cannot durably link multiple source rows to one canonical component. Next assess a migration-backed canonical-source link; do not bypass the guard. Statutory GST/IPFT approval remains separate.



## 27 October 2026 — correction: normalized canonical source-link schema already exists

The durable source-link table is already implemented as `BrokerChargeCanonicalSourceLink` with migration `202610250025_normalize_canonical_source_links.py`; do not add a duplicate migration. The actual gap is workflow integration: `broker_charge_verified_allocation_persistence_service.py` still requires the six-component legacy set and rejects multi-source canonical plans. Next inspect snapshot creation/review to verify link persistence and revalidation; keep split mapping blocked unless its invariants can be proved. Prior documentation CI runs #40479568869, #40479578088 and #40479585940 passed; latest docs update requires its own CI.



## 27 October 2026 — split-source canonical snapshot coverage clarified

Docs commits `0ccfe419...`, `d8b62051...`, and `0468eb1c...` passed CI #40480367450, #40480378523 and #40480401549. Test review confirms the canonical snapshot workflow already supports split transaction/IPFT through snapshot creation, independent review, canonical allocation persistence and reconciliation; missing source-link rejection is tested. The older direct allocation adapter still rejects multi-source plans. Next inspect API/service callers to determine whether that legacy path is reachable and confirm routes use the reviewed snapshot path. Keep fail-closed behavior until wiring is verified.


## Route audit finding — aggregate response credential sanitization — 27 October 2026

The API wiring audit found a concrete safety gap in `backend/app/api/v1/upstox_charges.py`: aggregate API response payloads were sanitized before durable persistence but the HTTP response returned the raw payload. A credential-like field such as `access_token` could therefore be exposed to the authenticated caller even though it was not stored. Fixed by applying `_sanitize_api_value` to the aggregate response payload and added a route regression assertion that the field is absent from the HTTP response. Code commit `203947ee25437e5b4637d25f365f0d1df7575fb1`; test commit `7e17376a91c8d835e1af42377be49c499d013bea`. Exact-head CI is pending; do not mark this fix green until CI passes. The brokerage-estimate route was not changed. Split-charge canonical snapshot safeguards remain in place. PAPER mandatory; live broker writes disabled; PR #6/#7 Draft/unmerged; original `Tradepro` out of scope.


## Aggregate API response sanitization — CI verified — 27 October 2026

- Backend CI runs #40481297561, #40481317091, #40481339870 and #40481349885 all completed successfully. Every run passed pytest, broker-write boundary enforcement, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore, and retained restore evidence.
- The aggregate Upstox charge API now applies `_sanitize_api_value` to the HTTP response payload as well as the persisted evidence. Route regression coverage asserts that `access_token` is not returned. Aggregate responses remain explicitly `per_fill_actual=False`; this is evidence capture/reconciliation, not per-fill accounting promotion.
- Route-wiring audit continues: confirm exposed charge APIs cannot bypass independently reviewed canonical snapshots for split transaction/IPFT evidence. Existing fail-closed direct adapter remains unchanged.
- The latest documentation commits triggered by this note need their own CI verification. Do not call this documentation revision green until those exact-head runs pass. Safety unchanged: only `tradepro-improved`; original `Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.


## 27 October 2026 — DP instrument eligibility hardened and CI verified

- Found and fixed a distinct applicability gap: DP/demat manifest eligibility now independently requires the underlying instrument classification to be `EQUITY`, in addition to delivery segment, SELL side, exact instrument-token mapping, connection mapping and ownership.
- Regression test rejects an OPTIONS instrument mislabeled by its order segment as an equity-delivery SELL.
- Implementation commit `447e9703f4bcf43dc6392d0d3741caee7709ce95` passed CI #40482878220; test commit `e62c9518df2edd9c80473b55f3a63a632a30121a` passed exact-head CI #40482895888. Both workflows succeeded, including backend tests, broker-write safety, SQLite/PostgreSQL 16 migration checks and synthetic restore verification.
- Next: finish applicability audit across supported instrument/segment/product/side combinations, then update all maintained Phase 3 documents and verify the resulting documentation head. This doc update needs its own CI.
- Production Oracle restore and genuine contract-note acceptance remain deferred until evidence exists. GST/IPFT tariff approval remains separate. PAPER mandatory, live writes disabled, PR #6/#7 Draft/unmerged, original Tradepro out of scope.


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

## 27 October 2026 — historical contract-note GST fixtures

Added regression coverage for five user-provided Upstox daily contract notes dated 23, 24, 25, 27 and 30 January 2023. Tests verify the disclosed taxable value (brokerage + transaction charges + SEBI fees), split GST arithmetic and the statutory GST primitive's total against the invoice. These are daily aggregates, not per-fill charges. The source text does not separately identify IPFT, so missing IPFT is not recorded as zero. Test commits: `98f14aef1b3b541c2a6e07beb227b6f3f0471a42` and `547917868d28d3f46f1f549a8daa50d57fc4542d`. Exact-head CI is pending verification; do not report this increment as green until verified.

## Effective-dated historical IPFT estimate gate — 27 October 2026

- Added `calculate_ipft_estimate_for_scope()` in `backend/app/services/broker_tariff_rules.py`. It requires an approved exact-scope `TariffRule`, NSE/FO/OPTIONS, explicit BUY/SELL, PREMIUM basis and INR_PER_CRORE; generic tariff calculation now fails closed for IPFT. The caller must supply the correct source-defined premium aggregation scope. This helper does not allocate aggregate IPFT to fills or certify booked charges.
- Added date-boundary tests for the official NSE schedule: ₹0.01/crore before 1 April 2023, ₹50/crore for equity options from 1 April 2023 through 28 February 2026, and rollback to ₹0.01/crore effective 1 March 2026. Sources: [NSE/FA/56129 (24 March 2023)](https://nsearchives.nseindia.com/content/circulars/FA56129.pdf) and [NSE/FA/73061 (27 February 2026)](https://nsearchives.nseindia.com/content/circulars/FA73061.pdf).
- These tests validate date selection and guarded estimate arithmetic; they do not activate production tariff records. No production rule is automatically approved by the tests, and actual IPFT remains distinct from the current Upstox calculator estimate and the supplied daily contract-note aggregates.
- The five historical GST invoice fixtures are in `backend/tests/test_historical_upstox_contract_note_gst.py`. The note transcription does not separately identify IPFT; missing is not zero. Exact-head CI for the latest code/test and documentation commits is pending verification.

- Code/test commits: `19ed761219b46fc687eff74e8fe245fececdc3b0`, `f2d486b1b65af910fd9ca1dbc86be1a7c4385d7e`, `5b718ae5cd78e3c49814210f97c2671e95dad8fe`. Exact-head CI pending.

## Superseding decision — GST invoice regressions and API evidence scope (27 October 2026)

- The five user-provided January 2023 Upstox daily contract-note fixtures and effective-dated IPFT estimator tests are included in code/test head `fe4c8c484650a8b6e63f822a8c7581431c855d22`.
- Exact-head Backend CI [#40545398934 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40545398934): **1,149 passed, 1 warning**. Broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, and synthetic restore checks passed.
- GST daily-invoice calculation is now regression-validated for all five supplied dates. Do not reopen the basic 18% formula as an unresolved research question. The annual AGS two-paise variance remains an aggregate reconciliation note; it is not evidence of a broker error and must not block the GST implementation.
- The Upstox pre-trade brokerage calculator is estimate-only. The post-trade charges endpoint `/v2/trade/profit-loss/charges` is aggregate-only. Preserve these meanings through `broker_charge_api_value_resolution.py`; do not promote either response to per-fill booked charges. Reconcile contract-note actuals at the source's disclosed scope.
- IPFT is not a blocker to the validated GST formula. Use effective-dated IPFT only when the product/segment and source-supported premium basis apply. The supplied January 2023 note text has no separately identified IPFT line, so don't assume either a separately booked IPFT amount or that it is bundled. Preserve it as not separately disclosed; do not synthesize zero or an allocation. If no applicable IPFT rule/component is evidenced for a trade, leave it not applicable/unknown according to the source and product scope rather than holding up GST.
- The guarded estimator is for estimate calculation only and requires an approved effective-dated tariff rule and explicit scope. It does not activate a production tariff or prove historical booked IPFT.
- Next Phase 3 work should proceed to the remaining accounting acceptance gates (fill identity, replay/idempotency, atomic rollback and component applicability), while using these GST tests as regression coverage. Only revisit IPFT when an applicable source-backed tariff or actual source field requires it.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.


### 27 October 2026 — GST API comparison continuation

Added nested JSON field-path support to the GST estimate comparison service for the Upstox response shape (`data.charges.gst`) and regression coverage for exact match, missing path, explicit null, and malformed path. The service still distinguishes API estimate from actual booked accounting and never auto-approves a non-zero variance. Implementation/test commits: `ff2d69546e5aad37c519c6622f51018bf7706ad5`, `a6f88dc85dcb25d903e610aaf30ce395ec12d650`. Exact-head CI is pending; previous green CI is only for earlier commit `0b5902ea35621d613589f7c8762b4d6658df9104`. Remaining: caller integration with verified tax inputs, component applicability/accounting acceptance, BSE/MCX source tariff validation, and maintained-doc sync after green CI.


### 27 October 2026 — Exact API mapping path fix

Fixed API charge value resolution so a mapping such as `data.charges.ipft` reads that exact nested path instead of reading any top-level `ipft` field. This prevents a similarly named field outside the approved path from being treated as the mapped value. Tests now cover nested payloads and missing exact paths. Commits: `aba4ffba23f96d976dad05a2dd6c46fefe188875`, `5ccaad1fcc464ee305746a380f889d7ee283d7c4`. Latest CI must be verified on the updated final head.


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


## Resume update — 29 October 2026 (API-first estimates; checkpoint CI verified)

- Backend CI #40755234415 passed on code/test head `778e76d3554a3baedc41f0396276c1cb3dafc38f` (1,197 passed, 1 warning). The synchronized documentation head `d57dd476ecd6acebd4dc9e169912b877811a8166` also passed exact-head Backend CI #40755635769, including pytest, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, synthetic restore, and evidence retention.
- Paper fills now prefer a complete, internally consistent Upstox Brokerage Details API estimate and fall back to the deterministic local calculator on token/API/shape/amount/total failures. Charge source distinguishes API estimate from local estimate. Both remain estimates, not actual booked charges.
- Post-trade Trade Charges API remains aggregate reconciliation evidence; do not promote aggregate results to per-fill actuals. Standard OAuth expiry is handled; no generic refresh-token grant is assumed. Live credentialed end-to-end verification remains unclaimed.
- Accounting acceptance audit confirms exact six-component core reconciliation, evidence/reviewer/source integrity, deterministic per-fill allocation, exact replay/conflicting replay protections, rollback safeguards, and DP/demat gating for eligible delivery sells. Avoid duplicate tests.
- Next: continue the remaining instrument/segment/product/side applicability audit and identify only genuine uncovered cases. Integrate GST/API comparison only if a concrete caller-level gap is found. Keep unsupported BSE/MCX tariff scopes estimated/unverified. Do not restart GST/IPFT research or let tiny aggregate rounding variance block paper trading.
- Safety: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker writes disabled. Production Oracle restore acceptance waits for deployment backups.


## Latest work — 29 October 2026 (CI pending for new code head)

- Added strict Upstox brokerage estimate response-body status validation: only `status == "success"` is accepted; malformed/unsuccessful bodies fall back. Regression test added.
- Added explicit `exchange_specific_tariff_unverified` fallback marker for BSE/MCX instrument tokens when the local tariff calculator is used, without blocking paper trades. BSE equity and MCX futures regression cases added.
- Code/test head: `217e5c74878048d276de20929b57a6a2b5aa668d`; exact-head Backend CI #40875989690 was still in progress at documentation update. Do not record as passed until GitHub reports success.
- Previous docs heads passed #40875565498, #40875627719 and #40875648924; these are prior-head results.


## Verified code checkpoint — 29 October 2026

- Code/test head `217e5c74878048d276de20929b57a6a2b5aa668d` passed exact-head Backend CI **#40875989690 — SUCCESS**. All workflow stages passed: backend pytest, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic restore drill and retained evidence.
- The new API response-status regression and BSE/MCX local-fallback scope regression tests are included in this passing head.
- Actual estimate source labels in code are `UPSTOX_API_ESTIMATE` and `HARDCODED_FALLBACK`. Documentation has been corrected; verify the post-sync docs head separately.


## User-directed simplification — 29 October 2026

- Removed unnecessary BSE/MCX-specific fallback warning. Upstox Brokerage Details API remains first choice; on API/token/response failure, use the existing hardcoded estimate and allow paper trading to continue.
- Standard disclaimer is now available in the paper estimate object and exposed through execution responses: “Estimated charges may differ from actual broker charges. For paper trading only; these are not actual booked charges.”
- Regression tests now expect the same fallback behavior for BSE/MCX and other instruments. The hardcoded estimate is explicitly an approximation, never actual booked-charge evidence.
- Latest code changes: `3b3fe2aa981013cdb1d75b6014bd14c56361f5b2`, `5e803146c0992539da8fe93f3df6836e5232a276`, `134cc87386b0c19b6e1294b5c95ae9aac9d813d4`, `6f2a80b51266ec14cb8e89761c97caa675df1fe4`. Exact-head CI still required.


## Resume update — 29 October 2026 (fallback regression repaired)

- The previous backend runs #40877183503 and #40877198561 failed: tests exposed stale `instrument_token` keyword arguments on three fallback paths, plus the new execution-response `charge_source` field being required by legacy schema fixtures. Fixed the fallback call sites and restored the schema's backwards-compatible default `PAPER_ESTIMATE`.
- Found and fixed a real response-display gap: the execution response disclaimer previously matched `PAPER_*` labels only, not the actual estimate sources `UPSTOX_API_ESTIMATE` and `HARDCODED_FALLBACK`. It now returns the standard disclaimer for all three estimate sources and does not label `BROKER_CONTRACT_NOTE` as an estimate. Regression tests cover both cases.
- Code commits: `8e7aef511aa965b5f7b1619a4b1f2d6786880d72`, `b8ae6f0e33356aa05bd3e89a664e166eef9c3ae5`, `c8f2e900e203f9d66ebfde2f7ac6b18fa7d54387`, `83a8ae95ccfc8d0271bb07c67316a40eff6be509`.
- Runs #40877183503 and #40877198561 are failed historical runs and must not be treated as current-head status. Run #40877487855 was in progress when this note was written and started before the final two repairs; verify CI on the resulting latest head before marking this increment green.
- User-directed policy supersedes older wording: BSE/MCX fallback is not a blocker; use API first, hardcoded fallback on failure, and a common paper-only estimate disclaimer. No tariff certification detour.


## Follow-up audit — persisted estimate-source provenance

- Auditing the caller integration found one additional concrete mismatch: the execution service collapsed the hardcoded fallback into generic `PAPER_ESTIMATE`, despite the estimator knowing whether the Upstox API estimate or local fallback was used.
- Updated both market-fill and matched-limit-fill paths to persist `PAPER_UPSTOX_API_ESTIMATE` or `PAPER_HARDCODED_FALLBACK`. The disclaimer still applies to all paper estimate labels. Regression coverage now checks the persisted fallback label and all source-label disclaimer variants.
- Code/test commits: `01a891595b05c5ca5f1d6be92d778a786b70c5f2`, `e50f96eb398dd46d4c59168b1fb0d16ca27dacac`, `f109384089fdf59418bf9ef86678df48f186bccd`. Exact-head CI required.


- Follow-up CI on the earlier PR merge head reached 1,204 passed and 1 failed: a transient ORM execution row can expose `charge_source=None`, so a default alone did not preserve compatibility. Added a Pydantic before-validator that normalizes a null legacy source to `PAPER_ESTIMATE`; the failing execution-schema regression now covers this case. Fix commit: `287dcc31807bc2b5677bc5128d2e65028c799017`. New exact-head CI still required.


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

## Phase 4 progress checkpoint — 30 October 2026

- Latest code/test head: `24c34dac47e273f9377485dc697f9fa510808a72`.
- Exact-head Backend CI [#41012821073 passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41012821073).
- P4-0B: added static detection for literal `getattr` broker-write dispatch and regression tests. Corrected an initial test-fixture escaping error after CI #41012807565 failed; corrected exact-head run #41012821073 is green.
- CI covered backend pytest, broker-write boundary guard, SQLite and PostgreSQL 16 migration round-trips, and synthetic restore drill.
- P4-0B partial/static guard hardening is checkpointed, not a claim of mathematically complete live-write isolation; dynamic method names remain a static-analysis limitation.
- Next active work package: P4-0C — automated-entry kill switch, exit availability, stale market data, and risk-check enforcement. Audit before edits; add only targeted regression coverage for confirmed gaps.
- Continue safeguards: work only in `tarunsharma2610-del/tradepro-improved`; no main update or PR merge; PAPER-only; live broker writes disabled; real Oracle restore and credentialed smoke tests remain deployment-gated.

## Phase 4 — latest verified checkpoint (30 October 2026)

- Latest code/test head `3a74fbb788a63ca3b042ceec400dbc7a83f32571`.
- Exact-head Backend CI #41016468736 passed: 1,240 tests passed, 1 warning; broker-write boundary enforcement, SQLite and PostgreSQL 16 migration round-trips, and synthetic restore drill passed.
- Paper market orders now use Upstox Full Market Quotes V3 depth: BUY consumes asks, SELL consumes bids, with a quantity-weighted simulated fill price and fail-closed validation of snapshot age, instrument identity, price validity and available depth.
- OAuth audit identified official Analytics Token support for market data/streaming without daily reauthorization. Next: implement separate encrypted token storage and scope-aware routing; standard access token remains for account/trading APIs and expires daily.
- Safeguards: work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` untouched; PR #8 Draft/unmerged; no main update; PAPER mandatory; live broker order writes disabled.
 
## Upstox Analytics Token implementation — 30 October 2026

- Added separate encrypted `analytics_token_encrypted` and `analytics_token_expires_at` fields to per-user broker connections with migration `202610300031` (down revision `202610270030`).
- Added owner-scoped Settings API to save, inspect status and clear Analytics Token. Token is accepted from the user's Upstox Developer Apps > Analytics page; it is never returned, logged or included in API responses. Expiry is tracked as 365 days from local registration; confirm/renew against the Developer Console's actual expiry date.
- Analytics Token retrieval is independent of standard OAuth `is_connected` state and fails closed when missing/expired. Standard OAuth access-token path remains separate for operations not documented as Analytics Token eligible.
- Routed strategy historical/intraday candle fetch, paper market quote/charge estimation, queued paper limit-order quotes, and market WebSocket reconnects through Analytics Token. Broker order/trade ingestion continues to use standard OAuth until each endpoint's Analytics Token/static-IP eligibility is deliberately enabled.
- Analytics Token is read-only. It cannot place, modify or cancel orders. Live trading remains disabled; PAPER-only guard unchanged.
- Official docs: https://upstox.com/developer/api-documentation/analytics-token/ ; https://upstox.com/developer/api-documentation/announcements/analytics-token-static-ip/ ; https://upstox.com/developer/api-documentation/v3/get-market-data-feed/
- CI for this new implementation is pending. Do not mark it accepted until exact-head CI passes, including migration round-trip and token isolation tests.

## Verified Analytics Token checkpoint — 30 October 2026

- Implementation head `083ab17a5150ea3be514438a16ea7c6c888c0be3` passed exact-head Backend CI run #41017833952: **1,243 tests passed, 1 warning**.
- Passed broker-write boundary enforcement; SQLite upgrade/downgrade/re-upgrade; PostgreSQL 16 migration round-trips; isolated synthetic PostgreSQL/document-volume restore drill.
- New Analytics Token implementation is accepted at code/test level: separately encrypted per-user token, owner-scoped save/status/clear endpoints, expiry fail-closed retrieval, and routing for market data, strategy candles, paper quote/charge calls and WebSocket reconnects.
- This does not mean a real user token has been entered or live Upstox connectivity has been validated. User must generate/copy the Analytics Token from Developer Apps > Analytics and configure it in Settings once UI is available.
- PAPER-only, live writes disabled, PR #8 Draft/unmerged, main untouched, original Tradepro untouched.


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


## Phase 4 current progress — 30 October 2026 (Upstox SDK audit)

- Exact-head Backend CI #41036389075 passed on 2212be0e094bb41423193b4384b6c07511ff3d62 after the durable-subscription test fixture correction.
- Official Upstox SDK v2.30.0 compared against our REST adapter, OAuth flow, WebSocket streamer, protobuf, Redis delivery and instrument master. Audit saved in UPSTOX_SDK_COMPATIBILITY_AUDIT.md. Decision: retain our async implementation; no SDK dependency added.
- Found and implemented CAS feed-field propagation from the already matching official V3 protobuf schema into MarketTick, Redis snapshots and stream status. Code head fe76751c54a720ffa5fcec7b4f3728b137447090 is pending exact-head CI; do not call it accepted yet.
- Next: validate CAS CI, then complete worker-managed Redis consumer lifecycle and recovery before scanner integration. PAPER-only; live writes disabled; PR #9 Draft/unmerged; original Tradepro untouched.


## Phase 4 update — 30 October 2026

- Latest verified code/test commit: `ef80d792c4d89abda1850b73f54f7b81bf16bbf7`.
- Exact-head Backend CI [#41057600440 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41057600440), including pytest, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, and synthetic restore/evidence checks.
- Feed-mode subscription persistence now replaces only the selected mode's desired instrument set; other modes remain active. Regression coverage added for independent `ltpc` and `full` subscriptions.
- CI failure #41057234551 was an outdated single-mode test expectation; corrected on the verified head.
- Next: implement and test mixed-mode V3 WebSocket subscribe/unsubscribe, reconnect replay, and Redis consumer lifecycle. Persistence tests do not yet prove end-to-end mixed-mode streaming.
- PR #9 remains Draft/unmerged. PAPER mode mandatory; live broker writes disabled; original `Tradepro` repository out of scope.


## Phase 4 update — Redis consumer recovery — 30 October 2026

- Exact-head Backend CI #41060945704 passed on `f7c863977ed17a3d705b83db8dcc6b7ba421cccf`, including fresh Upstox Analytics Token retrieval and authorized V3 WebSocket URL refresh on reconnect.
- New code/test head `a5e352bef2c78f27141b61bca5893fdfa0fd049a` adds Redis consumer tests for a new epoch restarting at version 1 after Redis volatile-data loss and for idle Pub/Sub PING/PONG heartbeat. Exact-head CI #41061518847 is pending.
- Redis consumer is implemented and validates authoritative snapshots; it is not yet managed by the background worker. Strategy worker remains on the existing candle evaluation path. Scanner/PAPER Redis integration is not complete.
- Next: worker consumer lifecycle with durable subscription discovery, single-owner coordination and graceful shutdown; then scanner/PAPER integration after tests.
- PR #9 Draft/unmerged; PAPER-only; live writes disabled; original Tradepro untouched.


## Phase 4 checkpoint — Redis consumer epoch and heartbeat recovery — 30 October 2026

- Latest implementation/test head: `a5e352bef2c78f27141b61bca5893fdfa0fd049a`.
- Exact-head Backend CI [#41061518847 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41061518847). The Backend pytest job, Redis restart-recovery integration environment, broker-write boundary guard, SQLite upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore, and evidence retention all completed successfully.
- Regression coverage verifies recovery from Redis volatile-data loss when the new epoch restarts at version 1 after the prior epoch reached version 8, and verifies Pub/Sub PING/PONG on an idle listener connection.
- The preceding token-refresh test remains covered by exact-head CI #41060945704 on `f7c863977ed17a3d705b83db8dcc6b7ba421cccf`: each reconnect calls the token provider again and obtains a fresh authorized V3 WebSocket URL.
- Redis consumer validates authoritative snapshots and supports reconnect/resubscribe, snapshot sweep, heartbeat, tenant isolation and fail-closed freshness checks. These tests do not certify production Redis deployment or sustained production load.
- Not complete: managed worker consumer lifecycle, durable subscription discovery/ownership coordination, scanner integration, and PAPER strategy consumption of Redis quotes. Existing strategy execution still uses its candle path.
- Next: design and test worker-managed consumer lifecycle (single-owner/lease semantics, startup discovery, cancellation, graceful shutdown, replica coordination and isolated failure handling). Only after that gate passes, connect the scanner, then evaluate PAPER strategy consumption.
- Safety unchanged: PR #9 remains Draft/open/unmerged; PAPER mandatory; live broker order writes disabled; no deployment or credentialed live smoke test claimed; original `tarunsharma2610-del/Tradepro` remains out of scope.


## Phase 4 resume checkpoint — 30 October 2026

- Latest verified implementation head: `6ac3882a98f3c66abb4cd62848971b6277ab3be7`; Backend CI [#41080156436 SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41080156436), exact SHA, pytest passed with no failed steps.
- Added transactional PAPER stop-event claims: active user-owned portfolio and strategy/instrument relationship validation; portfolio → strategy → position locks; non-flat position required; shared portfolio/instrument position with multiple active strategies fails closed.
- Claim identity is unique by strategy/event/quote epoch/version; stores claim token, bounded lease and attempt count. Duplicate claim uses nested savepoint and returns no claim; caller owns commit/rollback.
- Tests cover duplicate claims, cross-user access, mismatched strategy/instrument, ambiguous shared position, flat/missing position and invalid inputs.
- Existing dispatcher remains isolated; it is not connected to claim service or order execution.
- Next: PostgreSQL 16 simultaneous-claim tests; event state transitions and lease reclaim; crash recovery tests; explicit shared-position allocation; only then connect dispatcher to existing PAPER execution with fresh depth, risk, kill switch and accounting.
- PR #9 remains Draft/unmerged. PAPER mandatory; live broker writes disabled. Original `tarunsharma2610-del/Tradepro` is out of scope. Documentation sync itself needs exact-head CI.
