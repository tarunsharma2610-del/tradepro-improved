# Phase 3 Working Instructions — Guardrails and Verification Rules

**This file governs Phase 3 work only.** Whole-project constraints in `PROJECT_INSTRUCTIONS.md` remain authoritative. If a Phase 3 instruction conflicts with a whole-project safety rule, follow the stricter rule and stop to document the conflict.
**Canonical Phase 3 plan:** `PHASE3_ROADMAP.md`
**Canonical Phase 3 status:** `PHASE3_PROGRESS_REPORT.md`

## 1. Repository, branch and PR identity checks — every session and before every write

- Target repository is exactly `tarunsharma2610-del/tradepro-improved`.
- Current working branch is expected to be `phase3/durable-per-fill-charge-allocation`; verify the actual ref/HEAD rather than assuming.
- Never write to or open a write workflow for `tarunsharma2610-del/Tradepro` (original repo).
- PR #6 must remain open, draft and unmerged unless the user explicitly approves merging. Verify its current state before making claims.
- Record starting HEAD, target branch, PR state, and latest workflow URL before implementation.
- If branch, repo, PR, or HEAD differs from the recorded checkpoint, stop and reconcile the state before editing. Do not create a parallel branch or duplicate implementation without a reason.

## 2. Trading and data safety

- PAPER mode is mandatory. No real broker order writes: do not enable `place_order`, `modify_order`, or `cancel_order`.
- Do not enable live mode, automatic live-fill promotion, background scheduling, or any bypass of the safety boundary.
- Preserve the distinct identities and responsibilities of `BrokerFillIdentity` and `BrokerTradeRecord`; do not merge broker-fill identity with manual trade staging.
- No secret, access token, client secret, account number, or private contract-note data may be committed or pasted into public docs/issues. Use synthetic fixtures for CI.
- A test pass is evidence only for what the test exercises. Synthetic fixtures and restore drills are not proof of authentic account data or real Oracle Cloud recovery.

## 3. Phase boundary

Phase 3 scope is durable per-fill charge allocation, source evidence, charge-component representation, effective-dated component rules, reconciliation, accounting idempotency/concurrency/rollback, and acceptance evidence.

Do not reopen completed Phase 2 work. Do not broaden this task into unrelated app features, deployment, strategy scheduling, or UI work. If a Phase 3 dependency exposes a genuine blocker outside scope, document it as a dependency and ask before expanding scope.

## 4. Source-of-truth hierarchy and accounting semantics

- Inspect repository implementation, migrations, tests and current docs before coding. Use existing tested code where correct; do not repeat already completed work.
- Use official exchange/broker documentation and circulars for public rules; use authentic contract-note/invoice evidence to establish actual booked values. Keep the source URL, publication/effective date, endpoint, schema/API version, raw label and review provenance.
- Public examples or API field names alone do not authenticate a user's actual source data.
- The Upstox brokerage calculator is a proposed-order estimate. Upstox Get Trade Charges is aggregate reconciliation evidence. Neither proves actual charge amounts for individual fills.
- Preserve raw source values and labels; normalize only with an explicit, versioned and reviewed mapping. Every retained label must be bound to its corresponding normalized component and amount, not merely counted.
- Null is not zero. Missing, ambiguous, contradictory, unsupported, stale, non-finite, invalid-precision or unreviewed values must fail closed and remain pending/rejected.
- Estimates, actual aggregate charges and per-fill actual ledger entries must remain distinct types/states. Never silently promote one to another.
- Keep tariff candidates DRAFT until source, product/segment, effective dates, calculation basis, precision, review identity and approval are supported.
- Automatic generic QUANTITY/NOTIONAL allocation remains disabled unless a reviewed component-specific rule explicitly permits it. Explicit reviewed weights must retain provenance and reviewer/promotion controls.

## 5. Settled IPFT/GST decision — do not restart the policy debate

NSE circular NSE/FA/73061 (27 February 2026; effective 1 March 2026) records combined exchange-charge rates including IPFT: cash equity ₹307.00/crore, equity futures ₹183.00/crore, equity options ₹3,553.00/crore. Equivalent split arithmetic with IPFT exactly once: cash ₹306.99 + ₹0.01; futures ₹182.99 + ₹0.01; options ₹3,552.99 + ₹0.01. Source: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf

- Explicit combined representation: use the combined amount; do not add separate IPFT.
- Explicit split representation: use transaction charges excluding IPFT plus separately evidenced IPFT exactly once.
- Never infer combined/split mode from the field name. Preserve raw values and source provenance; fail closed on missing/conflicting/ambiguous representation.
- Working GST policy is 18% on the applicable evidence-backed taxable service-charge base, counting canonical components once. Delivery: brokerage + transaction charges/IPFT + applicable demat charges. Intraday/futures/options: brokerage + transaction charges/IPFT. Pure-agent/exclusion treatment requires the applicable rule and invoice evidence; product/segment/effective date, rounding and invoice reconciliation remain open gates.
- The policy arithmetic is settled; authentic Upstox field semantics, invoice/tax-base corroboration and production approval are not thereby settled.

## 6. Engineering workflow — one verifiable increment at a time

For each increment:
1. Read the Phase 3 roadmap/progress report, contract, component acceptance matrix, relevant code/tests, and latest CI before editing.
2. State the single acceptance gap being addressed and how existing tests differ from the missing coverage.
3. Implement the smallest safe change. Add tests that prove the new behavior and adversarial/failure behavior.
4. Run targeted tests. If they fail, diagnose root cause. Never weaken a guard, remove meaningful assertions, or change a test to expect unsafe behavior merely to get green.
5. Inspect the diff and migration effects. Check rollback, idempotency, provenance and auditability.
6. Commit implementation, tests and the directly relevant docs together when possible.
7. Verify the exact commit's GitHub Actions run. Confirm PostgreSQL-specific tests actually ran (not skipped), migration round-trips and safety guards passed, and the final suite count/warnings.
8. Until exact-head CI succeeds, label the step **implemented — verification pending**. Do not mark it complete based on an earlier SHA or a green run for a different commit.
9. After success, update `PHASE3_PROGRESS_REPORT.md`, `PROGRESS.md`, `HANDOVER.md`, and directly relevant Phase 3 contract/matrix/roadmap entries. Record exact SHA, CI URL, pass/fail/warning count, and next gate. Do not rewrite historical counts as if they belonged to the new run.
10. At session end, record exact HEAD, CI run, PR state, open blocker, next concrete action and unchanged safety state.

## 7A. Versioned component-set contract — next implementation gate

- The representation mode alone is insufficient for reproducible review; persist the exact supported representation-contract version with each transaction/IPFT source component.
- Legacy rows with a null contract version remain undeclared and must fail closed; never backfill the current version based on current code.
- Define the exact canonical component set consumed by live accounting separately from the wider source-component evidence vocabulary. Retaining a source line is not approval to allocate it.
- Test missing, extra, duplicate, legacy-version, mixed-mode, and inconsistent sibling version cases. Never silently drop an evidence component or widen the live-accounting component set without an approved mapping and migration plan.
- Representation contract version persistence was implemented in `1d327b145fe25d871a763985b5f746e12e107b75`; exact-head CI passed on the later verified checkpoint `f61cedd25f5982846774db3028fb646d2e108e07`.

## 7B. Source-to-canonical mapping gate

- Keep original transcribed rows immutable; mapping must not overwrite source labels, source amounts, or evidence locators.
- COMBINED transaction/IPFT maps the evidenced combined amount once to canonical `exchange_charges` and rejects a separate IPFT row.
- SPLIT transaction/IPFT combines transaction charges excluding IPFT and separately evidenced IPFT exactly once; mode and contract version must match across sibling rows.
- Do not map clearing, demat, other, or unsupported rows by guesswork. Until each has an approved canonical mapping and GST treatment, it blocks live accounting promotion.
- The pure mapping helper is implemented and CI-verified on `44c12acd133924711cd68c27f315d9298c6acfde`; it is not yet wired into API review or durable allocation.
- Next: wire the reviewed mapping through source review, durable canonical-component records, allocation verification and live-fill promotion. Add end-to-end tests for canonical amount reconciliation, exact paise behavior, replay/conflict handling, and no IPFT/GST double count.

## 7. Required evidence for the real live-fill accounting integration gate

The final PostgreSQL integration acceptance must exercise the real `LiveFillAccountingService.promote_trade` and `_load_reconciled_allocation_fees` path while allocation-ledger verification/promotion races. A stubbed loader alone is insufficient.

Cover at least:
- two distinct fills plus a concurrent duplicate promotion;
- exact replay versus conflicting replay;
- conflicting eligible-fill sets for one source component;
- pending/unreconciled/changed source evidence;
- reviewer authority and promotion preconditions;
- transaction rollback and absence of partial execution/position writes;
- deterministic lock ordering and PostgreSQL serialization behavior;
- source-total reconciliation, deterministic paise rounding and no IPFT/GST double count.

If a test does not exercise one of these paths, document that limitation rather than claiming broader coverage.

## 8. Documentation truthfulness rules

- Keep the dedicated Phase 3 files authoritative for detailed Phase 3 status; shared project docs link to them and summarize only the current checkpoint.
- Distinguish **implemented**, **tested locally**, **CI verified on exact HEAD**, **source verified**, **review approved**, and **production approved**. These statuses are not interchangeable.
- Do not assign a precise completion percentage unless the roadmap's weighted acceptance criteria are defined and evidenced. Prefer gate-by-gate status over invented percentages.
- Update progress only after a successful verification gate. A documentation commit does not complete an engineering/accounting gate.
- Never claim authentic Upstox evidence, tax/legal approval, real Oracle recovery, live trading readiness or Phase 3 closure unless that specific evidence exists.
- Keep historical failed CI as history; report current exact-head status separately. Do not hide failures or count reruns/duplicate workflow runs as separate completed engineering steps.

## 9. Phase 3 exit checklist

- [ ] Source labels are explicitly bound to normalized component and amount with adversarial tests.
- [ ] Effective-dated component-specific rules are reviewed and evidence-backed.
- [ ] Per-fill allocations reconcile exactly and preserve evidence/reviewer provenance.
- [ ] Combined/split IPFT equivalent results and no-double-count GST behavior are tested end-to-end.
- [ ] Real-service PostgreSQL concurrency, replay, conflict and rollback tests pass without skips.
- [ ] SQLite/PostgreSQL migration round-trips, safety-boundary checks and synthetic restore checks pass.
- [ ] Exact final HEAD CI is green and the run/commit/counts are recorded.
- [ ] Authentic source/invoice and actual Oracle restore gaps are completed or explicitly retained as external operational acceptance gates.
- [ ] Phase 3 docs are synchronized; PR #6 remains draft/unmerged until user approval.
- [ ] User explicitly approves Phase 3 closure and any subsequent change in trading safety posture.


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
