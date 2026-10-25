# Phase 3 Completion Roadmap — Durable Per-Fill Charge Accounting

**Scope:** Phase 3 only. This file is the execution order for remaining Phase 3 work; it does not replace the whole-project guardrails in `PROJECT_INSTRUCTIONS.md`.
**Repository:** `tarunsharma2610-del/tradepro-improved`
**Working branch:** `phase3/durable-per-fill-charge-allocation`
**Baseline checked:** 2026-10-25, branch HEAD `97843aec1d9b0acc4d55d0fc4529b4ea5b81fd50`; exact-head backend CI run [40187635881](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40187635881) succeeded (reported 907 passed, 1 warning).
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
**Status: implementation committed; exact-head CI pending.**
- Persist the representation-contract version used to review transaction/IPFT source rows; do not infer versions for legacy rows.
- Define the expected canonical live-accounting component set separately from the broader source-evidence vocabulary. Evidence-only components must be retained without being silently mapped, dropped, or promoted.
- Reject missing/extra/duplicate component sets, mixed combined/split declarations, unsupported contract versions, and legacy rows lacking a version.
**Accept when:** schema migration round-trips on SQLite and PostgreSQL; adversarial API/service tests prove the set is exact and version-consistent; exact-head CI passes.

### Gate 2 — Complete evidence-backed component and tariff-rule selection
**Status: open.**
- Inventory each charge component: brokerage, transaction charges/IPFT, STT/CTT, GST, stamp duty, applicable demat charges, clearing/other charges only where supported.
- Require product/segment/side, effective dates, source record, reviewer/approval and precise rule identity where relevant.
- Keep unverified rates and mappings DRAFT. Do not use generic quantity/notional allocation unless a reviewed component-specific rule explicitly supports that basis.
- Treat official documentation, API schemas and authentic contract notes/invoices as separate evidence types; public examples alone do not authenticate the user's actual booked values.
**Accept when:** approved rules are scoped and versioned, overlapping/expired rules fail closed, and no unsupported component is silently dropped or guessed.

### Gate 3 — Wire approved rules into per-fill allocation
**Status: open.**
- Connect validated source-component intake, reviewed representation, approved tariff/component rules, exact eligible-fill manifest, approved weights, deterministic paise allocation and durable ledger.
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
**Status: open acceptance gate.**
- Add/verify a PostgreSQL integration test that races the real `LiveFillAccountingService.promote_trade` / `_load_reconciled_allocation_fees` path against allocation-ledger verification/promotion; do not substitute a test stub for this acceptance.
- Cover two distinct fills plus concurrent duplicate replay; conflicting fill sets; pending/unreconciled evidence; reviewer authority; verification/source changes during promotion; transaction rollback; no partial execution/position writes; exact replay vs conflicting replay.
- Confirm PostgreSQL-only tests actually execute in CI, not pass via skip.
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
