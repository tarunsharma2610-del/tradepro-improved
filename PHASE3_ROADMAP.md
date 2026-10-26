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


# Phase 3 Completion Roadmap — Durable Per-Fill Charge Accounting

**Scope:** Phase 3 only. This file is the execution order for remaining Phase 3 work; it does not replace the whole-project guardrails in `PROJECT_INSTRUCTIONS.md`.
**Repository:** `tarunsharma2610-del/tradepro-improved`
**Working branch:** `phase3/durable-per-fill-charge-allocation`
**Latest verified code/test checkpoint:** `50802e96e06756b57a9f930e0c54c680777922d4`; exact-head Backend CI [#40209741299](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40209741299) succeeded. See the current checkpoint at the top of this file.
**PR:** [#6](https://github.com/tarunsharma2610-del/tradepro-improved/pull/6), open, draft, unmerged at baseline.
**Status rule:** Roadmap status only changes after code/docs are committed and the relevant verification succeeds. A test written, local pass, or an older green run is not completion evidence for a later HEAD.

## Non-negotiable guardrails

1. Work only in `tarunsharma2610-del/tradepro-improved`; never edit the original `tarunsharma2610-del/Tradepro`.
2. PAPER mode remains mandatory. Do not enable or send live broker order writes; do not enable automatic live-fill promotion or scheduling.
3. Keep `BrokerFillIdentity` separate from `BrokerTradeRecord`; do not conflate broker-fill identity with manual trade staging.
4. Keep PR #6 draft/unmerged until the user explicitly approves merge after acceptance review.
5. Do not reopen Phase 2 or silently widen scope beyond Phase 3 charge accounting.
6. Do not weaken guards to make tests green. Preserve raw broker evidence, source labels, endpoint/schema/version, review identity and audit trail. Null is not zero; ambiguity fails closed.
7. Do not promote estimates or aggregate charge endpoints as actual per-fill charges. The Upstox brokerage calculator is an estimate; Get Trade Charges is aggregate reconciliation evidence, not per-fill actual evidence.
8. Keep the agreed IPFT/GST policy below as settled. Remaining evidence gates do not mean the policy itself is undecided.

## Agreed IPFT/GST policy — carry forward, do not re-litigate

NSE circular NSE/FA/73061 (27 February 2026; effective 1 March 2026) gives combined exchange-charge rates including IPFT: cash equity ₹307.00/crore, equity futures ₹183.00/crore, equity options ₹3,553.00/crore. Equivalent split arithmetic with IPFT once: ₹306.99 + ₹0.01, ₹182.99 + ₹0.01, and ₹3,552.99 + ₹0.01 respectively. Source: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf

- Explicit combined representation: use the combined amount; never add IPFT again.
- Explicit split representation: use transaction charges excluding IPFT plus separately evidenced IPFT exactly once.
- Never infer representation from a field name. Preserve original label and source provenance. Missing, ambiguous, conflicting or invalid representations fail closed.
- Working GST policy: 18% on the applicable evidence-backed taxable service-charge base using canonical components once. Delivery: brokerage + transaction charges/IPFT + applicable demat transaction charges. Intraday/futures/options: brokerage + transaction charges/IPFT. Pure-agent/exclusion treatment requires applicable rules and invoice evidence. Effective date, product/segment, rounding and invoice reconciliation remain evidence gates.
- Published Upstox charge reference: https://upstox.com/brokerage-charges/

## Ordered completion plan

### Gate 0 — Establish the exact baseline and audit the actual gap
**Status: baseline and documentation head CI passed through `56ee81e2fb4f9c45031bbe5edea49dd0df061e5d`; current implementation/doc checkpoint pending exact-head CI.**
- Re-read this roadmap, `PHASE3_INSTRUCTIONS.md`, `PHASE3_PROGRESS_REPORT.md`, the allocation contract, component acceptance matrix, current source and tests.
- Confirm branch and repository before every write; inspect current diff/HEAD; check PR #6 and exact-head CI.
- Specifically inspect whether each retained source label is bound to its own normalized component and amount, not merely whether label count equals component count.
**Accept when:** actual implementation gaps are listed with file/test references; no duplicate work is planned.

### Gate 1 — Close source-label-to-component/amount binding
**Status: implemented and CI verified on `b92d0185f588e24d54510b36659944e77f498a6e`; authentic transcription review remains separate.**
- Ensure every raw label maps explicitly to exactly one normalized component and its exact raw amount/value/provenance; reject reordered, duplicated, omitted, contradictory or mismatched label/component/amount associations.
- Preserve source order and raw payload/provenance for audit; do not infer API semantics from spelling alone.
- Add focused positive and adversarial regression tests.
**Accept when:** each label-to-component relationship is explicit and fail-closed; the implementation and regression suite passed on the cited SHA. Independent comparison with authentic contract notes remains an evidence gate.

### Gate 1A — Persist and enforce a versioned component-set contract
**Status: implemented and CI verified at `f61cedd25f5982846774db3028fb646d2e108e07`; mapping of source rows to canonical components remains open.**
- Persist the representation-contract version used to review transaction/IPFT source rows; do not infer versions for legacy rows.
- Define the expected canonical live-accounting component set separately from the broader source-evidence vocabulary. Evidence-only components must be retained without being silently mapped, dropped, or promoted.
- Reject missing/extra/duplicate component sets, mixed combined/split declarations, unsupported contract versions, and legacy rows lacking a version.
**Accept when:** migration `202610250022` round-trips on SQLite and PostgreSQL; adversarial contract tests reject missing/extra/duplicate/legacy/unreviewed rows; exact-head CI [#40191140007](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40191140007) passed with 917 tests and 1 warning. Source-to-canonical mapping remains a separate gate.

### Gate 1B — Define combined/split source-to-canonical mapping
**Status: pure contract implemented and CI verified at `44c12acd133924711cd68c27f315d9298c6acfde`; integration remains open.**
- Preserve raw `transaction_charges` and `ipft` rows, labels, amounts, source locators, evidence digest and the persisted representation-contract version.
- Under explicit reviewed COMBINED mode, map the evidenced combined amount once to canonical `exchange_charges`; reject any separate IPFT row in that representation.
- Under explicit reviewed SPLIT mode, combine transaction charges excluding IPFT with separately evidenced IPFT exactly once into canonical `exchange_charges`. Do not use field names alone to infer mode.
- Define deterministic canonical amount and source-total reconciliation; keep both raw rows immutable and auditable. Clearing, demat, other or unsupported lines remain blockers until an explicit reviewed mapping and GST treatment exists.
**Accept when:** the pure mapping tests cover combined/split equivalence, missing/mixed/conflicting representation, exact paise amounts and unsupported extras. Those unit tests passed in [CI #40191589060](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40191589060); end-to-end ledger integration and no-double-count tests remain open.

### Gate 1C — Integrate canonicalization with source review and durable allocation
**Status: implemented; exact-head CI verified on 26 October 2026.** Backend CI [#40286205714](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40286205714) passed on implementation head `255fc208eed4bc8b922977717209d27912055377` (962 passed, 1 warning).
- `live_fill_accounting_service` now locks all six canonical snapshots in deterministic component order before evidence locking, validates each through `verify_canonical_component_allocation_ledger`, and derives actual fees only from six reconciled allocations linked to their matching canonical snapshots.
- Revalidation covers source-byte digest and links, mapping/representation versions, exact reviewed fill manifest and weights, INR source totals, durable reconciliation references, reviewer authority, and the contract-note reference under lock.
- There is no raw-only legacy allocation fallback. Extra, unmapped, unlinked, or foreign-connection per-fill allocation rows fail closed.
- End-to-end tests cover direct and combined/split transaction/IPFT source representations mapping to one exchange-charge component, exact replay, missing/unreconciled/extra allocations, and the PostgreSQL live-fill-versus-ledger promotion race.
**Acceptance result:** canonicalization, source review, allocation persistence, reconciliation and live-fill consumption use the same canonical mapping. Tariff applicability and invoice/tax acceptance remain separate open gates below.

### Gate 2 — Complete evidence-backed component and tariff-rule selection
**Status: partially closed for public-schedule estimate rules; actual-account applicability remains open.**
- A new explicit allowlist approves exactly 18 effective-dated STT/exchange-charge identities for public-schedule estimates only. The original candidate registry remains DRAFT; changes to rate, scope, effective date, source URL or source hash fail closed until re-review.
- The approved subset covers the public STT transitions and exchange-charge rates corroborated by the dated Upstox source snapshot and NSE/FA/73061. It does not establish a user's account-specific brokerage plan or actual booked charges.
- GST composition, stamp duty, SEBI turnover, DP/demat, clearing/other charges, BSE cash scrip groups, BSE futures, MCX and currency rules remain unapproved/unsupported until their exact scope and effective-date evidence is verified.
- The current public brokerage calculator may display stale rates; it is an estimate cross-check, not the effective-dated source of record.
**Accept when:** all in-scope estimate rules are approved and versioned, overlapping/expired rules fail closed, and actual-charge evidence remains separate from estimates. Unsupported product/segment rules must remain blocked.

### Gate 3 — Wire approved rules into per-fill allocation
**Status: partially implemented; source-specific rule approval remains open.**
- Canonical source-component intake, reviewed representation, exact eligible-fill manifest, independently reviewed explicit weights, deterministic paise allocation and durable canonical ledger are now wired end-to-end. Approved tariff/component-rule selection is still open.
- Support largest-remainder rounding and exact source-total reconciliation without losing source provenance.
- Test combined/split IPFT equivalence and prove IPFT/GST base are not counted twice end-to-end.
- Preserve separation between estimates, aggregate broker reconciliation, actual source evidence and per-fill ledger entries.
**Accept when:** every accepted source total reconciles exactly; each fill allocation is traceable; unsupported rules or incomplete evidence remain pending/rejected.

### Gate 4 — Reconcile GST and other component-specific rules
**Status: open; policy is settled, invoice/source validation is not.**
- Validate taxable-base composition against authentic contract-note/invoice evidence and applicable product/segment/effective-date rules.
- Verify rounding and invoice totals, including delivery vs intraday/futures/options differences.
- Review brokerage minimum/maximum caps, multi-fill order brokerage, STT/CTT side/product treatment, stamp duty and effective-date boundaries.
- Record exceptions and source citations. Do not treat the working GST policy as legally validated for every product/date without evidence.
**Accept when:** component rules and invoice reconciliation are reviewed and tests cover both ordinary and boundary cases.

### Gate 5 — Prove live-fill accounting integration, concurrency and rollback
**Status: partially verified; broader adversarial acceptance remains open.**
- PostgreSQL test `test_live_fill_promotion_races_with_component_ledger_verification` now races the real `LiveFillAccountingService.promote_trade` path against `promote_verified_canonical_component_allocations` using canonical snapshots and actual reconciled allocation rows; it is not a stubbed loader.
- The test permits a fail-closed first attempt while brokerage allocation is pending, then verifies retry/replay, one execution/position, and a complete reconciled six-component ledger. It passed as part of exact-head CI [#40286205714](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40286205714).
- Existing tests cover exact replay, conflicting payloads, reviewer revocation, staged-row/flush/commit rollback, and source/allocation mismatch rejection.
- Remaining: broaden concurrent duplicate replay across multiple fills, conflicting fill-set races, source/review mutation during promotion, and fault-injection coverage beyond the existing targeted boundaries. Do not call this exhaustive.
**Accept when:** no interleaving permits unverified or conflicting allocations to be promoted, replay is exactly-once, and failures leave no partial accounting writes.

### Gate 6 — Adversarial review, migration and restore evidence
**Status: open final engineering review.**
- Run targeted regression suite and full backend suite.
- Verify SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade, broker-write boundary checks, evidence-retention checks and synthetic restore drill.
- Review migrations for reversibility, constraint integrity, locking order, idempotency and audit retention.
- Keep synthetic CI restore clearly distinguished from restoring an actual retained Oracle Cloud backup. Real-environment recovery remains a separate operational check.
**Accept when:** all automated gates pass and the review records remaining real-environment evidence gaps honestly.

### Gate 7 — Exact-head CI, documentation sync and Phase 3 sign-off
**Status: open for this roadmap commit and final implementation.**
- Run/check the complete required GitHub Actions workflow on the exact final branch HEAD; record run URL, commit SHA, pass/fail counts, warnings and PostgreSQL/migration job outcomes.
- After a successful implementation step, update the Phase 3 progress report and handover/checkpoint docs with only verified facts. Keep a short entry in the shared progress/change log and maintain the Phase 3 instructions if a guardrail changes.
- Recheck PR #6 is still draft/unmerged; do not merge without explicit user approval.
**Accept when:** all engineering gates are passed, evidence gaps are explicitly accepted or closed, docs match the code/CI HEAD, and the user approves Phase 3 closure.

## Definition of Phase 3 complete

Phase 3 is not complete just because the tests are green or the docs exist. Completion requires: component/source provenance intact; reviewed effective-dated component rules; exact per-fill reconciliation and no double counting; live-fill accounting concurrency/idempotency/rollback proven against real service paths; full exact-head CI green; migrations and audit trail verified; outstanding authentic Upstox/invoice and real Oracle restore checks either completed or clearly declared as external operational gates; and explicit user approval before merge or any live-trading change.

## Progress update protocol

For every step:
1. Record the starting commit and exact scope.
2. Inspect existing code/tests/docs before editing; do not duplicate already-covered behavior.
3. Make the smallest safe change plus regression tests.
4. Run targeted tests; investigate failures without weakening safeguards.
5. Commit code/tests and relevant Phase 3 docs.
6. Verify exact-HEAD CI and required jobs. Until it passes, mark the step **implemented, verification pending**, not complete.
7. Only after successful verification update `PHASE3_PROGRESS_REPORT.md`, `PROGRESS.md`, `HANDOVER.md`, and any directly affected Phase 3 docs with commit SHA and CI link.
8. End each session with the current HEAD, successful CI run, open gate, next concrete action, and safety state.


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
- **Next single implementation step:** integrate the verified canonical snapshot allocation/reconciliation path with live-fill accounting, preserving source provenance and safely handling combined/split transaction/IPFT. Add focused integration tests for exact replay, six-component totals, and rejection of extra/unmapped components; then run the full backend CI gate.
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
