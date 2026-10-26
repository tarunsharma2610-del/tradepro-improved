## Authoritative Phase 3 checkpoint — 26 October 2026 (latest verified CI)

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
- **Documentation-sync note:** the 25-file checkpoint sync commit `c3166b05a132fe2339cebc7940e5cb1aa71152cf` passed exact-head Backend CI [#40286698642](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40286698642). This follow-up roadmap/status edit must pass its own exact-head CI before implementation resumes.

---


---


# Phase 3 Progress Report — Durable Per-Fill Charge Accounting

**Last updated:** 2026-10-25  
**Repository:** `tarunsharma2610-del/tradepro-improved`  
**Branch:** `phase3/durable-per-fill-charge-allocation`  
**Pull request:** [#6](https://github.com/tarunsharma2610-del/tradepro-improved/pull/6) — open, draft, unmerged at last verified status  
**Phase 3 plan:** [`PHASE3_ROADMAP.md`](PHASE3_ROADMAP.md)  
**Phase 3 rules:** [`PHASE3_INSTRUCTIONS.md`](PHASE3_INSTRUCTIONS.md)

## Current checkpoint — exact-head status

- Latest verified implementation head: `255fc208eed4bc8b922977717209d27912055377`; exact-head Backend CI [#40286205714](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40286205714) passed: **962 passed, 1 warning**.
- CI passed backend pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade, synthetic PostgreSQL/document-volume restore, and evidence-artifact retention. Synthetic restore does not prove actual Oracle Cloud recovery.
- Canonical live-fill integration is now implemented and CI-verified: six canonical snapshots are required; every component's source, mapping, reviewed fill set/weights, allocation ledger and durable reconciliation reference is revalidated; fees are read from the canonical per-fill rows only. Raw-only legacy allocations are not a fallback.
- End-to-end coverage includes direct and combined/split transaction/IPFT representation, exact replay, missing/unreconciled/extra allocation rejection, and a PostgreSQL race between actual live-fill accounting and canonical allocation promotion.
- PR #6 remains open/draft/unmerged; PAPER mode remains mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled; original `Tradepro` remains out of scope.

## Status vocabulary

- **CI verified:** exact commit SHA is covered by a successful required workflow.
- **Implemented, verification pending:** code exists but exact-head CI has not yet passed.
- **Evidence/review pending:** implementation or arithmetic exists, but authentic source evidence or independent approval is missing.
- **Complete:** all roadmap acceptance criteria for the gate have passed; docs record evidence and no unacknowledged blockers remain.

Do not infer completion percentages from test count or number of documentation updates. Use the acceptance gates below.

## Gate-by-gate status

| Gate | Status | Evidence / remaining work |
|---|---|---|
| Durable allocation ledger, deterministic paise allocation, source-total reconciliation, replay/conflict controls and review/promotion safeguards | **Implemented; prior CI verified** | Current known exact-head run #40187635881 passed on SHA `97843aec1d9b0acc4d55d0fc4529b4ea5b81fd50`. Reconfirm relevant tests remain enabled in final CI. |
| Source evidence intake and representation validation | **Implemented; source approval pending** | Versioned combined/split IPFT representation, raw-label retention and missing/ambiguous/conflicting input rejection exist. Explicit source-label → normalized-component association and missing-label rejection are implemented and CI-verified on the cited source-label guard commit; authentic transcription still requires independent review against the original note. |
| IPFT combined/split arithmetic | **Canonical mapping and end-to-end equivalence tested; tax approval pending** | NSE circular NSE/FA/73061: cash ₹307.00/crore, futures ₹183.00/crore, options ₹3,553.00/crore combined; split equivalent is ₹306.99+₹0.01, ₹182.99+₹0.01, ₹3,552.99+₹0.01. Canonical live-fill tests prove the exchange-charge total is counted once; GST/tariff applicability remains open. |
| GST taxable composition and invoice reconciliation | **Evidence/review pending** | Working 18% canonical taxable-base policy is documented; authentic invoice/tax-base validation by product, segment and effective date remains open. |
| Effective-dated component tariff rules and actual API/contract-note mapping | **Partially closed for estimate-only STT/exchange rules** | New explicit allowlist approves 18 effective-dated public-schedule rules for estimates only; source hash and exact rule identities are allowlisted. Candidate registry remains DRAFT. Account-specific brokerage, GST, stamp, SEBI, DP/demat, other charges and unsupported exchange/segment mappings remain open; calculator is not tariff source-of-record or per-fill actual evidence. |
| Canonical per-fill allocation wired to live-fill accounting | **Implemented; exact-head CI verified** | Live accounting requires six independently verified canonical snapshots and reconciled allocations, exact fill manifest/weights and source totals; combined/split IPFT canonicalizes once. **Approved tariff/component-specific rule selection remains open.** Generic QUANTITY/NOTIONAL allocation remains disabled unless component-specific rules approve it. |
| Real live-fill service vs canonical allocation verification/promotion concurrency | **Partially verified; broader gate open** | PostgreSQL exact-head CI now exercises the real `LiveFillAccountingService.promote_trade` path against canonical allocation promotion. Pending fail-closed/retry, exact replay and no-partial-write behavior are covered. Remaining: broader multi-fill duplicate replay, conflicting fill-set/source-change races and additional fault injection. |
| Migrations, adversarial review and restore | **Prior synthetic CI checks passed; final review open** | Recheck SQLite and PostgreSQL 16 upgrade/downgrade/re-upgrade, broker-write boundary, evidence retention and synthetic restore on final HEAD. Actual retained Oracle backup restore is a separate operational check. |
| Dedicated Phase 3 roadmap/instructions/progress reporting | **Updated; current status edit CI pending** | The 25-file checkpoint sync passed CI; the subsequent gate-status correction is the current documentation head and must pass exact-head CI before implementation resumes. |
| Phase 3 sign-off / PR merge | **Not complete** | All acceptance gates and evidence gaps must be reconciled; PR #6 remains draft/unmerged until explicit user approval. No live-trading enablement is included in Phase 3 closure. |

## Next actions — in order

1. **Verify the current documentation/status commit's exact-head CI** before further implementation.
2. **Close Gate 2:** review the dated official Upstox/NSE source snapshot against exact product, segment, side, basis and effective dates. Keep candidates DRAFT where the public source does not prove account-specific scope; do not use the brokerage calculator as actual-charge evidence.
3. **Close Gates 3–4:** approve only supported component-specific allocation/tax rules; reconcile GST bases, brokerage caps, STT/CTT, stamp duty, demat/other charges and invoice totals. Preserve actual-vs-estimate separation and fail closed where evidence is missing.
4. **Finish Gate 5 adversarial coverage:** concurrent multi-fill replay/conflicting fill sets, source/reviewer mutation, and any demonstrated rollback gaps. Do not duplicate already passing tests.
5. **Run final adversarial review, migrations, broker-write guard and restore checks** on the exact final head. Synthetic restore is not an actual Oracle Cloud recovery.
6. **Synchronize checkpoint docs and verify exact-head CI**; then request explicit user acceptance before any merge. PR #6 stays draft/unmerged; no live-order writes or automatic promotion are enabled.

## Verified step log

| Date | Commit / workflow | Result |
|---|---|---|
| 2026-10-26 | `255fc208eed4bc8b922977717209d27912055377`; [CI #40286205714](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40286205714) | **Passed:** 962 passed, 1 warning, 0 failures; broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, synthetic restore and evidence retention passed. Canonical live-fill integration and combined/split IPFT tests are included. |
| 2026-10-26 | `c3166b05a132fe2339cebc7940e5cb1aa71152cf`; [CI #40286698642](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40286698642) | **Passed:** 25 maintained checkpoint documents synchronized and exact-head Backend CI succeeded. This follow-up status edit requires its own exact-head CI. |
| 2026-10-26 | `c73fbf612c8bea42190583f416b383980601e587`; [CI #40287039937](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40287039937) | **Passed:** 962 passed, 1 warning. Gate-status corrections, canonical live-fill tests, broker-write guard, migration round-trips and synthetic restore passed. The current tariff-review change must pass its own exact-head CI. |
| 2026-10-25 | `97843aec1d9b0acc4d55d0fc4529b4ea5b81fd50`; [CI #40187635881](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40187635881) | **Passed:** 907 passed, 1 warning, 0 failures. This result applies to that SHA only. |
| 2026-10-25 | New Phase 3 roadmap and instruction documents | Committed after the verified implementation SHA; exact-head CI is pending and must be recorded here only after it succeeds. |

## Required update rule for every future successful step

After a code/test step is merged into the working branch (not the PR base) and exact-head CI succeeds, append a dated row to this report containing:
- what changed and the acceptance criterion it closes;
- implementation/test commit SHA;
- exact workflow URL and conclusion;
- test pass/fail/skip/warning counts and confirmation that PostgreSQL-specific tests ran;
- any evidence limitation that remains;
- the next single concrete action.

If CI fails or is still running, update status to **verification pending/failed** with the exact SHA and run link; never mark the gate complete. Do not backfill success from a different commit or repeat a completed step as if new work.

## 2026-10-25 implementation checkpoint — explicit source-label association

**Status: implemented; exact-head CI verification pending.**

- Changed `backend/app/services/broker_charge_representation_contract.py` to require an explicit `labels_by_component` association, with exact component-key coverage, non-empty/unique labels and consistency with retained raw-label order.
- Changed `backend/app/api/v1/broker_charge_evidence.py` to pass the explicit component-to-label mapping derived from each persisted source-component row during review validation.
- Added regression coverage in `backend/tests/test_broker_charge_representation_contract.py` for missing associations, wrong component sets and inconsistent label mapping/order.
- Implementation commits: `79dd66d8c429498501e9edfb35e73a1ca0b756b4`, `0146ecd75f0e6a625b21761d3195c896bba293f7`, `fb147a3c5580091574bc71c35e7a641cf7386935`.
- Current implementation HEAD at time of entry: `fb147a3c5580091574bc71c35e7a641cf7386935`. No CI result for this exact HEAD has been verified yet; do not mark the gate complete until the exact-head workflow passes.
- Limitation: structural mapping proves which persisted label is associated with a normalized component row; it does not independently authenticate that the transcribed label/amount matches the original contract note. Independent source review remains required.
- Next action: verify exact-head CI, confirm focused tests and API review tests pass, fix any failures without weakening safeguards, then update this report with the successful run and counts.

### CI failure and corrective test-fixture update

- Workflow [#40188703796](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40188703796) on implementation SHA `fb147a3c5580091574bc71c35e7a641cf7386935` **failed** during pytest. The failure was in the new test helper: `zip(..., strict=True)` raised while constructing an intentionally malformed fixture, so the validator was never exercised. This was a test-fixture error, not evidence that the production validator failed.
- Corrective test commit: `e2758ae3db5309641196f0cd0ce035591f6c03ac`; the helper now allows the malformed fixture to reach validation, and the assertion checks the validator's fail-closed component-key error.
- Verification for the corrected commit remains pending until its own CI result is checked. The earlier failed run is retained as history; it is not counted as a successful step.

### Successful verification — explicit source-label association (2026-10-25)

- Exact implementation HEAD `d70b1535e7a8b8680b90dadbd926e06b4ae41a16` passed workflow [#40188968279](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40188968279).
- Test result: **910 passed, 1 warning, 0 failures**. Broker-write boundary guard passed; migration/restore workflow steps completed successfully, including a synthetic PostgreSQL/document-volume restore drill. The synthetic drill does not establish real Oracle account recovery.
- This verifies the explicit component-to-source-label mapping change and its current tests on that SHA. Authentic transcription against real contract notes remains a separate evidence/review gate.
- The next discovered gap is that the intake API still substitutes the normalized component name when `source_label` is omitted. That fabricates a source label rather than preserving the absence of source evidence. Next step: stop substituting normalized names and fail closed at review until a genuine source label is supplied; add API regression tests.

### 2026-10-25 — stop fabricating missing source labels (verification pending)

- Identified a follow-on evidence gap after the label-association gate passed: intake used `payload.source_label or payload.component_name`, silently inventing an apparent source label when none was transcribed.
- Updated intake to preserve a missing label as `None`; review now rejects a component without a non-empty original source label and leaves it pending. The representation validator no longer substitutes normalized component names for missing sibling labels.
- Added an API regression test proving missing label remains missing and cannot be reviewed; updated successful-review fixtures to include explicit source labels.
- Code/test commits: `460c9bba1a9cb6240ccdf86d39087107fe23589f`, `34e3d3e865660f96b432968565f2b8ceeb9c9184`.
- Current code HEAD at time of writing: `34e3d3e865660f96b432968565f2b8ceeb9c9184`. CI is pending for the code and any subsequent documentation commit. Do not mark this gate complete until exact-head CI passes.
- Evidence limitation: requiring a label ensures explicit transcription; only independent review against the integrity-checked original note can confirm the label and amount are authentic.

### CI correction history — review validation order

- Workflow [#40189211122](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40189211122) failed on `34e3d3e865660f96b432968565f2b8ceeb9c9184`: **909 passed, 2 failed, 1 warning**. Both failures showed the new missing-label rejection ran before existing authorization / eligible-fill validation, changing the expected 403/422 responses.
- Corrected in `b92d0185f588e24d54510b36659944e77f498a6e` by moving the new representation/source-label checks after the existing authorization and fill/weight validations but before any state mutation. This preserves fail-closed label handling without bypassing the established validation order.
- The failure is retained as history. Exact-head CI for the correction and the current documentation HEAD must pass before the source-label authenticity guard can be marked complete.

### Successful verification — missing source-label guard (2026-10-25)

- Corrected review-validation ordering in `b92d0185f588e24d54510b36659944e77f498a6e`; exact-head workflow [#40189481491](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40189481491) passed: **911 passed, 1 warning, 0 failures**.
- Verified steps include broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration upgrade/downgrade/re-upgrade, and synthetic PostgreSQL/document-volume restore drill.
- Documentation checkpoint `704d9d5caa8a893195d5213ae38b97c30639de96` also passed exact-head workflow [#40189515861](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40189515861).
- The source-label guard is **CI verified** on the implementation SHA above. It prevents fabricated labels and preserves prior authorization/fill-validation ordering. Authentic source transcription still requires independent review.
- The current progress-report synchronization commit is newer than those two verified SHAs; verify its exact-head CI before describing the current branch head as green.



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
- Root cause fixed: PostgreSQL rejected complete durable reconciliation references because the column was limited to 200 characters. Model and migration `202610250026_widen_charge_reconciliation_reference.py` now support 320 characters; downgrade refuses truncation.
- PostgreSQL concurrent-promotion coverage is implemented and passed in the run above. Documentation checkpoint commit still requires exact-head CI verification.
- Next: once checkpoint CI passes, audit for any demonstrated conflicting-set/rollback test gap and add only missing coverage.
- Protocol: every CI failure → diagnose/fix/rerun; every CI pass → update all 18 maintained checkpoint documents, commit exact SHA/run/results/next step, then verify CI on the checkpoint commit.
- Safeguards: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker order writes disabled. GST/IPFT production tariff acceptance is a separate gate.


## Authoritative checkpoint — 26 October 2026 (documentation CI verified)

- Repository: `tarunsharma2610-del/tradepro-improved`; branch: `phase3/durable-per-fill-charge-allocation`.
- Latest implementation commit: `ac7d27f2c9922925483b5b906c484c0d5a4e3f53`; exact-head Backend CI [#40287765745 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40287765745).
- Documentation synchronization commit: `f90573d653c7103bf9cfdb1f867da97b176d3240`; its exact-head Backend CI [#40289107666 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40289107666). Backend tests, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore/evidence retention passed. Synthetic restore is not proof of actual Oracle Cloud recovery.
- Approved public Upstox STT/exchange rules are estimate-only. Account-specific actual charges, GST taxable-base composition, stamp duty, SEBI/DP/demat/other charges, unsupported exchange/segment mappings, and per-fill actual evidence remain unapproved. Candidate tariff entries remain DRAFT unless separately allowlisted and reviewed.
- Phase 3 remains in progress. Next gates: independently reviewed tariff applicability; component-specific per-fill allocation rules; invoice/source-backed GST/IPFT and product/segment evidence; final adversarial, migration and recovery review; exact-head acceptance sign-off. Do not repeat canonical live-fill integration.
- Safety: PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. PR #6 stays open/draft/unmerged without explicit user approval. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.
- This documentation commit’s CI is green. Continue only from this checkpoint and verify CI for every subsequent implementation/checkpoint commit. Historical entries do not supersede this checkpoint.


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
