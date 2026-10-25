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
