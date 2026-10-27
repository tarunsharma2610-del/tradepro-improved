# Phase 3 Latest CI Checkpoint — 27 October 2026

## Latest verified code checkpoint

- **Repository:** `tarunsharma2610-del/tradepro-improved`
- **Branch / PR:** `phase3/cross-broker-gst-ipft-resolution` / PR #7 (Draft, unmerged)
- **Code/test head:** `8feeb0cbb0c35e1e37012302c9075d43f1f33eb1`
- **Backend CI:** [#40458822529 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40458822529)
- **Test result:** 1,097 passed, 1 warning.
- **Verified gates:** broker-write boundary; SQLite migration upgrade/downgrade/re-upgrade; PostgreSQL 16 migration upgrade/downgrade/re-upgrade; synthetic PostgreSQL + document-volume restore; restore evidence retention.

## Documentation synchronization

Existing maintained Phase 3 documents were synchronized after the green code result, including handover, progress, master roadmap, project instructions, audit, architecture, requirements, changelog, roadmap, security, GST/IPFT acceptance/research/source registers, README, safeguards, Upstox evidence, Bhav audit, and the Algory AI-integration plan.

- Last multi-document synchronization commit: `00f919af6635f40ddfcf3ac6f8b8dcd20441671d`
- This checkpoint refresh is the final documentation commit for this increment. Exact-head CI must pass on this final checkpoint commit before the documentation head is marked green.
- PR #7 description has been updated to reflect DP integration and latest verified code CI; PR remains Draft/unmerged.
- Three candidate root paths (`TARIFF_RULE_SOURCE_REGISTER.md`, `SECURITY_AUDIT.md`, `PHASE3_ACCOUNTING_ACCEPTANCE.md`) were not present and were not created.

## Latest increment: DP amount validity and manifest eligibility

- `Execution.total_charges_complete` and `execution_charge_total_is_complete` return complete only for a consistent `KNOWN` state with an explicit finite, nonnegative, paise-exact amount, or `NOT_APPLICABLE` with no amount. Unknown, invalid or inconsistent states fail closed.
- DP canonical manifests are checked against persisted broker trade → child order → local order mappings. Every manifest fill must belong to the reviewed broker connection, and both trade and local order must be SELL with local order segment `EQUITY_DELIVERY`.
- Added regressions for invalid/inconsistent status/amount pairs (including NaN, negative and fractional-paise amounts), plus DP manifest rejection for BUY trades, intraday orders and mismatched order/trade sides, and acceptance of a correctly mapped delivery SELL.

## DP/demat accounting already implemented

1. DP is an optional canonical component separate from the six core charge components.
2. Canonical snapshot materialization supports component-specific eligible-fill manifests so DP can cover only eligible delivery sells.
3. Delivery SELL requires a reviewed/reconciled DP snapshot and durable allocation for that exact fill; missing DP evidence fails closed before accounting mutation.
4. DP is persisted in `Execution.demat_transaction_charges`, included exactly once in `total_charges`, and included in replay comparison.
5. `KNOWN` and `NOT_APPLICABLE` are distinct from `UNKNOWN`; unresolved totals must not be presented as complete.
6. Canonical DP allocation promotion is supported after independent review and deterministic per-fill allocation verification.

## Remaining Phase 3 gates — next work

1. Continue component-by-component accounting acceptance: exact fill identities, paise totals, source-to-canonical mappings, idempotent and conflicting replay, atomic rollback, and segment/product applicability.
2. Continue effective-dated tariff and statutory GST valuation review, including taxable-base inclusion, Rule 33 evidence gates, place-of-supply handling, and paise rounding. Public estimate output is not actual invoice-level acceptance.
3. Ensure API/UI totals remain visibly incomplete whenever applicability or any required component is unresolved.
4. Real contract-note acceptance and production Oracle backup/restore acceptance remain deferred until genuine evidence/deployment backups exist. Synthetic restore passing is not production acceptance.
5. Re-run safety, migration and restore gates after every code increment and synchronize maintained docs to the latest green code head.

## Safety / scope invariants

- PR #6 and PR #7 remain Draft/unmerged; do not merge.
- PAPER mode is mandatory. Live broker order writes remain disabled.
- Work only in `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` repository is out of scope.
- No personal contract note is available or required to continue synthetic testing.
- Do not restart GST/IPFT from zero; continue from the accounting acceptance audit.

## Verified checkpoint — 27 October 2026 (DP/demat completeness)

- Latest verified code/test commit: `9400bc9aa221e2cf3b735e49a8e9a6d351237f02` on `phase3/cross-broker-gst-ipft-resolution`.
- Exact-head Backend CI [#40459846143 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40459846143). Backend pytest, broker-write boundary enforcement, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, and synthetic PostgreSQL/document-volume restore checks passed. Synthetic restore is not production Oracle restore acceptance.
- Added API regression ensuring an invalid DP status serialized through `ExecutionOut` cannot report `total_charges_complete=true`. Existing status/amount consistency tests and DP manifest eligibility checks remain in place.
- DP rules: `KNOWN` requires a valid paise-exact amount; `NOT_APPLICABLE` requires no amount; `UNKNOWN`, invalid or inconsistent states are incomplete. Delivery SELL promotion requires reviewed DP snapshot and exact per-fill allocation; non-applicable DP cannot be silently included.
- Next gate: inspect acceptance coverage for per-fill source-to-canonical mapping, identical/conflicting replay, transaction rollback, and component applicability. After the next code change, rerun exact-head CI and synchronize maintained docs/checkpoints.
- Actual contract-note reconciliation and production Oracle backup/restore acceptance remain deferred until genuine evidence exists. Synthetic testing continues without a personal contract note.
- Safety: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` is out of scope. PR #6/#7 remain Draft/unmerged; PAPER mode mandatory; live broker order writes disabled.

## Latest verified checkpoint — 27 October 2026 (per-fill allocation tamper rejection)

- Code/test commit `45b0fdc1622881fa0ed361bae6c28af64b59a5f1` passed exact-head Backend CI [#40460914796](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40460914796) (completed, success).
- Added `test_tampered_per_fill_allocation_amount_blocks_live_accounting`: changing a reviewed brokerage allocation by ₹0.01 must be rejected before execution/live-position promotion; paper-position quantity remains unchanged.
- Verifier audit confirms the allocation fill-set must match the reviewed manifest; allocation status, connection, currency, basis, method, source total and deterministic paise amount are validated. Existing tests cover missing component allocations, non-reconciled rows, exact replay, conflicting fill/evidence replay, and post-commit retry safety.
- Next gate: explicit fill-set mismatch and atomic rollback assertions as needed, then component applicability. Keep statutory/effective-dated GST/IPFT tariff acceptance distinct from estimates.
- Production contract-note reconciliation and real Oracle backup/restore remain deferred until genuine evidence exists. No personal contract note is required for current synthetic tests.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker writes disabled.

## Documentation synchronization CI — 27 October 2026

- The synchronized documentation head `1694a656f4398594083363d9009da48b93b2f841` passed Backend CI run [#40461252201](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40461252201) (SUCCESS).
- The other maintained-doc commits also passed their associated runs: [#40461205056](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40461205056), [#40461210578](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40461210578), [#40461220291](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40461220291), [#40461231298](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40461231298), and [#40461244445](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40461244445).
- Acceptance review confirms existing tests already cover fill-manifest fingerprint mismatch and inconsistent split-source manifests, missing component allocations, unexpected separate IPFT allocation, allocation amount tampering, failed-commit rollback, and safe exact replay after post-commit response failure. Avoid duplicating these tests without identifying a distinct uncovered behavior.
- Next gate: compare the canonical component applicability policy to all supported instrument/segment/side cases, then add narrowly scoped regression tests only for uncovered cases and run exact-head CI. Keep invoice-backed actual GST and effective-dated statutory tariffs evidence-gated; estimates are not actual reconciliation.
- Safety remains unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.

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

## Latest checkpoint — 27 October 2026 (GST line normalization + official-source review)

- GST helper code `57730a21da77fa583fe19c12740bd03eb779fed6` passed Backend CI [#40462246316](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40462246316). Test commit `4290b46e55275e4a005b3661da327adc1b216028` passed [#40462263615](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40462263615).
- Invoice GST normalizer accepts either IGST or CGST+SGST pair; rejects mixed tax modes, incomplete pairs, missing lines, negative/non-finite and sub-paise amounts. It is not a statutory rate/jurisdiction/tax-base determination.
- Official-source review recorded in `GST_IPFT_ACCEPTANCE_MATRIX.md` and `GST_IPFT_PUBLIC_EVIDENCE_ADDENDUM.md`: CBIC Section 15/Rule 33, NSE circular NSE/FA/73061 effective 1 March 2026, and broker-specific Zerodha IPFT explanation. NSE member tariff data and one broker's presentation are evidence inputs, not universal client-invoice rules.
- Remaining: effective-dated reviewed GST rate/tax-base policy; exchange/segment/date-specific IPFT mapping and duplicate prevention; independently approved tariff evidence; full tests on final docs head. Actual invoice reconciliation remains evidence-gated.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.


## Verified checkpoint — 27 October 2026 (GST/IPFT documentation head CI)

- Documentation checkpoint commit `14027b5bc4293d2cc1ce5990a4ee23f60077fad5` passed Backend CI [#40462683805 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40462683805). Verified jobs: backend pytest, broker-write boundary enforcement, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration upgrade/downgrade/re-upgrade, synthetic PostgreSQL + document-volume restore, and retention of synthetic restore evidence. This CI run proves the tested repository state passed those gates; synthetic restore is not production Oracle acceptance.
- This closes the pending CI item for the GST normalization + public-source documentation increment. It does not make the GST taxable-base policy or any actual per-fill GST/IPFT candidate approved.
- Current GST work already in place: invoice-line normalization accepts IGST or a complete CGST+SGST pair and rejects mixed/incomplete/missing/invalid/non-paise amounts; statutory valuation logic is a separate primitive and remains subject to policy integration/review. The source audit identifies a real policy gap: CBIC Section 15/Rule 33 valuation guidance and broker-specific published GST bases are not identical in presentation. Do not infer a universal broker component set from one tariff page.
- Next gate: perform a focused cross-broker, exchange/segment/effective-date matrix review of the taxable base (including SEBI turnover, transaction/IPFT representation, DP/demat, STT and stamp duty), then encode only reviewed policy decisions with provenance and tests. Rule 33 pure-agent exclusion must require evidence; missing jurisdiction/source facts fail closed. Keep public estimates separate from actual invoice reconciliation and prevent transaction/IPFT double counting.
- Exact-head CI must be rerun after the next code/documentation change. Actual invoice reconciliation and production Oracle backup/restore remain deferred until genuine source/backup evidence exists; no personal contract note is required.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.


## Current resume point — 27 October 2026 (cross-broker GST source policy)

- Previously pending checkpoint CI is resolved: commit `14027b5bc4293d2cc1ce5990a4ee23f60077fad5` passed Backend CI [#40462683805 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40462683805).
- New public-source comparison was recorded in `GST_IPFT_ACCEPTANCE_MATRIX.md` and `GST_IPFT_PUBLIC_EVIDENCE_ADDENDUM.md`; `PROJECT_INSTRUCTIONS.md`, `PROGRESS.md` and `HANDOVER.md` were synchronized. Relevant docs commits: matrix `8660b581a1433a6ea72c1f73d6b7c28ccea7040d`; evidence addendum `424f3bb8e9d3667da31cae324830d1247f9cc433`; project instructions `aa602a539393bd7bb17209a80bef9760420391b5`; progress `e421e6664dd17785a3e47febb3bdf733392692a4`; handover `a6f9934d78b5f398092de01b7bb7c87c3870aac2`.
- Source result: no universal GST taxable-base component list is supported across the broker pages. CBIC Rule 33 is conditional; Zerodha/Dhan list SEBI in their published bases; Dhan includes IPFT/other tax; FYERS pages conflict; Upstox schedule/API example discrepancy remains; Angel One's table is insufficient to infer base membership. This is research evidence, not actual invoice approval.
- **Next implementation step:** audit existing policy resolver/candidate structures before changing code; implement explicit effective-dated broker/exchange/segment policy provenance and conflict handling only where missing. Preserve separate estimate and actual modes; included/excluded component identities must be reviewed; combined/separate transaction/IPFT must map exactly once; missing facts or conflicting sources fail closed. Add only uncovered regressions, then run exact-head CI.
- CI status for the newer documentation commits is **not yet verified** in this checkpoint; do not treat them as green until a run on the final head succeeds. Actual per-fill GST acceptance and production Oracle restore remain evidence-gated. No personal contract note required.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.


## GST policy resolver hardening — 27 October 2026

- Audited existing `backend/app/services/broker_gst_component_policy.py` before changing it. It already provides effective-dated broker/exchange/segment/product selection, source URL/retrieval date/SHA-256 provenance, explicit combined/separate/not-applicable IPFT representation, exact component-set checking and an estimate-only calculation path. Avoid creating a parallel resolver.
- New code commit `eef5eebc1e1abfc37c92b4e50d5c35e9afddcbb4`: policy state `CONFLICT` now exists and any effective conflict for the exact scope/date blocks selection even if an approved policy also matches. This prevents silently preferring one of contradictory public sources.
- New test commit `761637aab1d5f36ed5bfc02ffb66ce8b31ab7820`: regression tests for a conflicting source blocking an approved candidate and for rejecting sub-paise component inputs rather than silently rounding them.
- The policy remains estimate-only. This does not approve any broker component set, does not integrate the statutory Rule 33 engine into actual accounting, and does not reconcile invoice-level GST. No broker policies are promoted to APPROVED by this change.
- Validation status: exact-head CI for these commits is not yet verified. Do not mark this increment green until the branch/PR workflow runs on the exact resulting head and all jobs pass. Next: inspect any CI result, fix failures, then synchronize maintained documents/checkpoint to the latest green head.


## Follow-up CI result — GST policy conflict and paise validation (27 October 2026)

- Regression-test commit `761637aab1d5f36ed5bfc02ffb66ce8b31ab7820` passed Backend CI [#40463464076 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463464076). The run completed successfully for the new tests covering conflict-policy blocking and sub-paise rejection.
- The service hardening commit `eef5eebc1e1abfc37c92b4e50d5c35e9afddcbb4` also passed Backend CI [#40463452758 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463452758).
- Documentation-head workflow [#40463512765](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463512765) was still in progress at the time of this checkpoint update. Do not call the current docs head green until this exact-head run finishes successfully.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; PR #6 and #7 remain open Draft/unmerged; PAPER mandatory; live broker writes disabled; original `tarunsharma2610-del/Tradepro` out of scope.


## Statutory GST input precision follow-up — 27 October 2026

- Focused audit found the statutory valuation helper rounded input valuation lines to paise silently, unlike the GST component estimate path which now rejects sub-paise source amounts. For invoice/charge-line integrity this could hide malformed source data.
- Code commit `58c841cb00f7f0137aece7bcd7c83d5a63ae81f9` now rejects statutory valuation inputs that are not already paise precision. Test commit `c6e9dfb3e4cae6f93fd51a7f1f1facc86e7b804d` covers rejection and retains an explicit valid-paise rounding case for GST head arithmetic.
- CI for these new commits and the resulting documentation head is pending/unverified. Do not mark green until exact-head Backend CI succeeds. This is input-integrity hardening, not a change to the 18% rate or an approval of a broker-specific taxable base.
- Earlier hardening CI: service commit `eef5eebc1e1abfc37c92b4e50d5c35e9afddcbb4` passed [#40463452758](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463452758); test commit `761637aab1d5f36ed5bfc02ffb66ce8b31ab7820` passed [#40463464076](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463464076); docs head `d604be9982dc9c37d3a4985abd89c85635b59106` passed [#40463512765](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463512765).


## Confirmed statutory GST precision CI and resume point — 27 October 2026

- The initial code-only run for `58c841cb00f7f0137aece7bcd7c83d5a63ae81f9` failed because an older test still expected silent rounding of `0.025`. This was a test expectation conflict with the new fail-closed behavior, not an unresolved runtime regression in the final increment.
- Regression-test commit `c6e9dfb3e4cae6f93fd51a7f1f1facc86e7b804d` passed Backend CI [#40463868838 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463868838). It replaces the obsolete sub-paise rounding expectation with explicit rejection and a valid paise-precision test.
- Checkpoint commit `74015a285cb844a3735052d88cce9c2a2385e1ce` passed Backend CI [#40463883785 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463883785). This verifies the resulting head including the GST precision change, updated regression test and checkpoint document.
- Intermediate failed run: [#40463856382](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463856382); it was superseded by the successful regression and checkpoint runs above. Do not erase the failure from history; document the correction.
- Current implementation boundaries: statutory GST primitive applies Section 15 default inclusion and conditional Rule 33 pure-agent exclusion only when all modeled evidence flags are true; broker GST policy resolver remains an estimate-only source-specific path. Neither is yet a unified actual per-fill invoice acceptance path. No broker GST policy is approved here for actual accounting.
- Next Phase 3 task: audit the accounting charge reconciliation/promotion boundary and define a single reviewed path that consumes source-backed invoice line identities, statutory valuation evidence and effective-dated broker policy without letting estimates become actual ledger charges. If source provenance, Rule 33 facts, component identity, or GST invoice lines are missing/conflicting, actual accounting must fail closed. Add tests before integration; do not promote estimates or change live-trading safeguards.
- Safety unchanged: work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` is out of scope; PR #6/#7 Draft/unmerged; PAPER mode mandatory; live broker order writes disabled.


## Real-source GST/IPFT evidence added — 27 October 2026 (CI pending)

- Reviewed user-provided two-page statement image. Visible figures: brokerage ₹1,000.00; transaction charges ₹111.61; SEBI fees ₹0.22; GST on brokerage ₹180.00; GST on charges ₹20.15; stamp duty ₹3.00; STT lines ₹0.32, ₹1.21 and ₹51.89; total net value ₹4,487.73.
- ₹180.00 is exactly 18% of ₹1,000 brokerage. On the visible transaction + SEBI components, ₹111.61 + ₹0.22 = ₹111.83; 18% rounds to ₹20.13, but source GST-on-charges is ₹20.15. Record ₹0.02 as a reconciliation variance pending full line-level explanation; do not silently round/fudge it.
- No separately labelled IPFT line is visible; its inclusion in transaction charges remains unknown. This historic 2023 statement is aggregate summary evidence, not current tariff proof or per-fill GST allocation evidence.
- Updated GST_IPFT_ACCEPTANCE_MATRIX.md with the source figures, arithmetic, discrepancy and required system behavior. Update commit: 5987a6ac8fff32794e3b1a495187f88bacaa4396. Exact-head CI is not yet verified for this documentation update.
- Upstox public pricing states GST on brokerage + transaction + IPFT and DP for delivery; its brokerage API sample exposes transaction ₹5.68, IPFT ₹0.17 and GST ₹1.02 (18% of transaction alone), while its trade-charges API sample has ipft:null. Zerodha explains NSE IPFT can be included under exchange transaction charges. These are useful corroborating sources but do not explain the ₹0.02 in this user's statement or prove actual invoice treatment universally. Sources: https://upstox.com/brokerage-charges/ ; https://upstox.com/developer/api-documentation/get-brokerage/ ; https://upstox.com/developer/api-documentation/get-trade-charges/ ; https://support.zerodha.com/category/account-opening/resident-individual/ri-charges/articles/ipft-charges ; https://cbic-gst.gov.in/sectoral-faq.html.
- Next: inspect exact-head CI; then add a deterministic regression fixture for reported source tax lines vs computed expected GST, with explicit variance instead of silently changing source amounts. Keep estimate and actual invoice paths distinct; do not promote this aggregate statement as per-fill evidence.
- Safety unchanged: only tarunsharma2610-del/tradepro-improved; PR #6/#7 remain Draft/unmerged; PAPER mandatory; live broker order writes disabled; original tarunsharma2610-del/Tradepro out of scope.


## Cross-broker GST/IPFT research + source variance helper — 27 October 2026 (CI pending)

- Current public-source review recorded in `GST_IPFT_ACCEPTANCE_MATRIX.md` and `GST_IPFT_PUBLIC_EVIDENCE_ADDENDUM.md`: CBIC Section 15/Rule 33; NSE circular NSE/FA/73061 effective 1 March 2026; Upstox current pricing and API examples; Zerodha and Groww published fee/GST descriptions; BSE's 2025 equity master circular and cross-exchange NSE/BSE/MCX rate summary.
- Confirmed: GST framework is common law, but exchange tariff rates vary by exchange, segment, product, instrument and effective date. NSE combined transaction/IPFT totals effective 1 March 2026: cash ₹307/crore, equity futures ₹183/crore, equity options ₹3,553/crore premium per side. Use combined totals once; do not double-add IPFT. BSE scrip/product groups and MCX commodity schedules must be separately modeled; do not inherit NSE rates.
- CBIC Q77: STT/stamp/other third-party recoveries are excluded only if Rule 33 pure-agent conditions are actually satisfied; otherwise Section 15/Rule 27 valuation applies. Do not infer pure-agent status from component name alone.
- New helper `backend/app/services/gst_source_reconciliation.py` compares source-reported tax with tax on an explicitly reviewed base and returns expected tax, reported tax and variance without mutating source values. Test `backend/tests/test_gst_source_reconciliation.py` uses the user's statement: ₹1,000 brokerage -> ₹180 GST matches; visible transaction ₹111.61 + SEBI ₹0.22 -> base ₹111.83, expected GST ₹20.13 vs reported ₹20.15, variance +₹0.02.
- Code/test commits: `e30b453f54a08707c2a94ec881f23b0849fe4b37` and `7ecd0522ab7c72b80c070f3601bf8d22e857ea35`. Research/docs commits: `07570e9b341d1c89a3cde48f23de3be9e202d602` and `418f921cc370dcf9f5d318febadbe782b5a23a3b`. Previous docs head `a0097f113f8217178b4ad1a701780c313c069106` passed Backend CI #40469808678; new helper/test/docs head CI is pending verification.
- Limits: user statement does not separately label IPFT, so inclusion remains unknown. The Upstox Brokerage Details API example's ₹1.02 GST does not equal 18% of ₹5.68 + ₹0.17 (about ₹1.05); its aggregate API `ipft:null` is unknown, not zero. No public source located explains the user's ₹0.02 variance. Do not treat aggregate statement totals as per-fill evidence or claim every broker uses the same invoice presentation.
- Next: check exact-head CI; fix any failures and checkpoint the green head; then wire the variance helper only into review/reporting, not automatic promotion. Continue effective-dated exchange/product tariffs and actual source-to-fill accounting gates.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled; original `tarunsharma2610-del/Tradepro` out of scope.


## Verified source-GST variance regression checkpoint — 27 October 2026

- **Green Backend CI:** [run #40470168336](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40470168336) completed SUCCESS on commit `f053393a10a21463d8ef299c3a18e4d3abeef9d2`. This head includes the source GST variance helper/tests and GST/IPFT research/docs updates. Test-only commit `7ecd0522ab7c72b80c070f3601bf8d22e857ea35` also passed Backend CI #40470116527.
- Real statement regression: ₹1,000 brokerage -> reported GST ₹180.00 matches at 18%. Visible charges ₹111.61 transaction + ₹0.22 SEBI -> ₹111.83 base; expected GST ₹20.13, source reports ₹20.15; variance +₹0.02 retained explicitly. New helper does not infer the taxable base and does not mutate source tax values.
- Research findings and citations are in `GST_IPFT_ACCEPTANCE_MATRIX.md` and `GST_IPFT_PUBLIC_EVIDENCE_ADDENDUM.md`. NSE combined transaction/IPFT rates are effective-dated and counted once; BSE/MCX have separate tariffs; Rule 33 exclusion requires evidence. Upstox API sample mismatch remains documented, not silently papered over.
- This green run verifies regression handling and existing workflow checks; it does **not** certify the source's unexplained ₹0.02, identify the unlabeled IPFT amount, or approve actual per-fill GST promotion. Next work is to connect this helper to reviewer-facing reconciliation reporting and maintain actual/source estimate separation, then continue Phase 3 acceptance gates.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker writes disabled; original `tarunsharma2610-del/Tradepro` out of scope.


## Continuation checkpoint — 27 October 2026 (API integration is the next implementation task)

### Latest discussion and correction

The user reiterated that API integration was discussed yesterday and should be implemented instead of repeatedly reopening GST/IPFT research. Acknowledged gap: the repository has read-only Upstox API client methods and safety/semantics helpers, but the existence of those parts alone does **not** prove they are wired into the per-fill accounting flow. Do not claim integration complete until the service path and tests demonstrate it.

### Existing API capabilities verified in source

- `backend/app/brokers/upstox/reconciliation_client.py` has read-only `get_brokerage_estimate(...)` using `/v2/charges/brokerage`; it is estimate-only.
- The same client has `get_trade_charges(...)` using `/v2/trade/profit-loss/charges`; this is aggregate segment/FY evidence, not per-fill evidence.
- `broker_charge_api_value_resolution.py` enforces source-level endpoint guards, approved exact field mappings, provenance, and distinct MISSING/NULL/INVALID/ZERO states.
- `upstox_public_gst_estimate.py` calculates public-schedule estimates only. It must not be promoted to actual invoice evidence.
- `live_fill_accounting_service.py` requires reviewed actual charge evidence and canonical component snapshots; estimated or aggregate values must not bypass that gate.

### Immediate implementation plan (continue from here; do not restart tax research)

1. Trace the read-only API client call sites and the charge evidence/canonical snapshot services on this branch. Identify the supported response schema and current integration seam before changing contracts.
2. Add a narrow API orchestration/normalization layer that invokes the calculator for estimates and the aggregate charges endpoint for reconciliation context. Keep the two response types distinct and preserve request scope, response provenance, timestamps, endpoint, schema/version and missing/null/invalid/zero states.
3. Require exact approved field mappings before interpreting fields. Do not create APPROVED mappings merely to make tests pass; use official docs/schema evidence and leave unresolved fields unusable.
4. Never treat aggregate endpoint output as per-fill actual, never distribute aggregate totals across fills as though broker-reported actuals, and never treat `ipft: null` as zero. Preserve combined transaction/IPFT exactly once according to the reviewed scope policy.
5. Connect actual per-fill accounting only when genuine per-fill actual evidence and reviewed canonical allocations exist. For aggregate-only responses, create reconciliation context/variance only; do not promote accounting.
6. Add focused tests for both endpoint classifications, malformed/missing/null/zero fields, no double-counting of combined transaction/IPFT, estimate-versus-actual separation, scope/date validation, and fail-closed accounting integration. Run backend tests and safety/migration/restore workflows.
7. Synchronize the maintained checkpoint, GST/IPFT acceptance matrix, Upstox integration policy, progress and handover documents after code changes. Record CI only against the exact resulting commit; if CI fails, fix and rerun before checkpointing green.

### GST/IPFT decision carried forward

The practical route is API-first, not another loop of public research and not waiting for a personal contract note. The brokerage calculator is pre-trade estimate only; the post-trade charges API is aggregate evidence only unless official schema/contract proves a more granular scope. The historical ₹20.15 GST line remains source-reported with the visible-base ₹0.02 variance preserved; its cause is not established, and it is not a blocker to API wiring. Statutory GST valuation and the one-time transaction/IPFT treatment remain separate reviewed accounting rules; public schedule calculations remain estimates.

### Status at this checkpoint

- API client methods: **present**.
- API-to-accounting orchestration: **not yet verified/complete**; this is the next code task.
- Exact-head CI for the upcoming integration change: **not run yet**.
- Actual contract-note and production Oracle restore acceptance: deferred until genuine evidence/backups exist; synthetic tests continue.
- Safety unchanged: repository `tarunsharma2610-del/tradepro-improved` only; PR #6/#7 Draft/unmerged; PAPER mandatory; live order writes disabled.


## API orchestration implementation increment — 27 October 2026

- Added `backend/app/services/upstox_charge_api_orchestration_service.py`. It wraps the existing read-only client and returns a typed envelope preserving broker, endpoint, evidence kind, usable/error state, request scope and payload. Brokerage calculator output is explicitly `ESTIMATE_ONLY`; post-trade charges output is `AGGREGATE_RECONCILIATION_ONLY`. Both are hard-coded `per_fill_actual=False`.
- Added `backend/tests/test_upstox_charge_api_orchestration_service.py` covering scope/provenance classification, aggregate-vs-estimate distinction, API error fail-closed behavior, null IPFT preservation, and explicit trade-date validation.
- Commits for this increment: orchestration service `33750bcd748c2a59c77024df4fad61c865a2e9ef`; tests `f98ed9e7f4b092c6d8e284d7461ee4aba46b72e4`. Documentation updates are being applied after these code/test commits.
- **Honest scope limit:** this is the first safe API orchestration boundary, not yet proof that a UI endpoint or per-fill accounting workflow invokes it in production. It deliberately cannot promote either response into live-fill accounting. Next implementation step is to wire this service into the appropriate read-only API/reconciliation route and persist aggregate results as reconciliation context only, after confirming existing route and evidence-ledger contracts. Actual per-fill promotion still requires approved field mappings and reviewed canonical evidence.
- CI for the new code/test head has not been verified by the GitHub status/workflow tools yet; their response was empty. Do not mark this head green until the actual workflow result is confirmed. Run backend tests and the broker-write, migration and synthetic restore gates; fix any failures before creating a green checkpoint.


## Authenticated API route increment — 27 October 2026

- Added `backend/app/api/v1/upstox_charges.py` and registered it in `backend/app/api/v1/router.py`.
- Authenticated read-only routes now expose `GET /api/v1/upstox/charges/brokerage-estimate` and `GET /api/v1/upstox/charges/aggregate`. They only use the signed-in user's own Upstox connection, require a connected/decryptable access token, and call fixed GET-only client methods. Brokerage estimate responses remain `ESTIMATE_ONLY`; aggregate responses remain `AGGREGATE_RECONCILIATION_ONLY`; both return `per_fill_actual=false`. API errors are sanitized to categories by the client; no order-write method was added.
- Route commit: `0d47e997547dbe537e43d231e9f99d4f0c902252`; router registration commit: `9cacf82d16bffa21cadf6d4bf05291f46963260b`.
- CI #40473482706 passed on prior doc head `6021815de9bfa1213320daafb4eda866c93f3ec9`. New route CI runs #40473791107 and #40473806635 are in progress/queued on route commits; these do not yet certify the latest head. Next update checkpoint only after latest-head CI is complete.
- Still not end-to-end ledger persistence or per-fill actual accounting: aggregate results are exposed as read-only reconciliation context only; no automatic canonical allocation or accounting promotion occurs. Next steps: add route-level tests for ownership/token failure and endpoint classification; run exact-head backend/safety/migration/restore CI; then evaluate whether an explicitly reviewed aggregate reconciliation record should be persisted under existing ledger contracts. Never promote aggregate totals to fills.


## CI result and route-test continuation — 27 October 2026

- Confirmed successful Backend pytest workflow on documentation head `24b7b9ee728049f26b200cbee54571ae3c22b7bf`: [run #40473895336](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40473895336). The earlier API route/router commit workflows also completed successfully: #40473791107, #40473806635, #40473856715, #40473866947, #40473874400 and #40473885583.
- Added `backend/tests/test_upstox_charge_api_routes.py` in commit `ffb87c9af7c87d921eadf0198b7ba8704be65e76`. Coverage: estimate route response semantics and null-IPFT preservation, aggregate route never labelled per-fill actual, and invalid quantity rejected before any API call.
- **New test commit CI is pending** and must pass before the checkpoint is called green for this increment. The previous green CI result does not certify this later test commit.
- Current next steps: inspect the new test run; fix any failures and rerun; then examine the existing reconciliation/evidence model before deciding whether to persist aggregate API output as a reconciliation-only record. Do not persist into per-fill allocations or promote to actual accounting. Continue to keep docs/checkpoint synced after the final code head.


## Exact latest checkpoint refresh — 27 October 2026

- Latest documentation synchronization commit observed: `10d105a344b08a21dfe50593f8683453a5d44bfc` (PROGRESS.md update). The checkpoint itself is now being refreshed after the route-test commit so the next handover points at the actual newest doc/code sequence.
- Route test commit `ffb87c9af7c87d921eadf0198b7ba8704be65e76`: workflow [#40474374635](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40474374635) is still running the test suite at last poll.
- Latest docs head `10d105a344b08a21dfe50593f8683453a5d44bfc`: workflow [#40474444724](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40474444724) is still in progress. Earlier route/router and orchestration commits had successful CI; no success is inferred for the latest head until this run completes.
- Scope decision from inspecting existing evidence models: `BrokerChargeEvidence` is specifically a source-document/integrity record and `BrokerChargeSourceComponent` requires document-linked source hashes and independent review. Do not misuse either table to store API aggregate summaries. If durable API aggregate reconciliation history is required, add a dedicated source-kind/schema/migration and repository only after a focused design and migration test; until then the authenticated endpoint returns aggregate data as read-only reconciliation context, not a persisted accounting source.
- Immediate next steps: wait for test and exact latest-head CI; fix any failures; then design a dedicated aggregate API reconciliation evidence record with endpoint, scope/window, response hash, fetched timestamp, status and safe payload/provenance, without per-fill allocation links. Add SQLite/PostgreSQL migration tests and user-ownership tests before persistence. Never treat aggregate response as per-fill actual or change live-write safeguards.


## Resume update — aggregate Upstox API evidence design — 27 October 2026

- Route-test commit `ffb87c9af7c87d921eadf0198b7ba8704be65e76` passed Backend CI [#40474374635 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40474374635).
- Documentation commit `10d105a344b08a21dfe50593f8683453a5d44bfc` also passed Backend CI [#40474444724 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40474444724). These results establish the route-test commit and that documentation commit as green; they do not certify any later commit.
- API route tests now cover authenticated estimate/aggregate behavior, null IPFT preservation and validation. The estimate endpoint remains estimate-only; post-trade charges remain aggregate reconciliation context, not actual per-fill charges.
- Model inspection confirms the existing `BrokerChargeEvidence` and `BrokerChargeSourceComponent` structures are document-integrity/reviewer evidence records. Do not repurpose them for aggregate API payloads or fabricate source-document hashes/review state.
- Next implementation: a dedicated aggregate API reconciliation record and migration, capturing authenticated owner/connection, broker, endpoint/API version, request scope/window, fetch timestamp/status, response hash and sanitized response/provenance. Preserve absent/null/invalid/zero distinctions. Enforce owner scoping on reads/writes, avoid logging secrets/tokens, and retain aggregate-vs-estimate semantics. Do not create per-fill allocations or promote this record into actual accounting.
- Add focused ownership, response-provenance, idempotency/duplicate-fetch, sanitized-payload, and migration upgrade/downgrade/re-upgrade tests for SQLite and PostgreSQL 16. Then run backend tests, broker-write safety, migrations, and synthetic restore checks. Update this checkpoint again only with the exact commit and confirmed CI result.
- Scope unchanged: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` is out of scope. PR #6/#7 stay Draft/unmerged, PAPER mode is mandatory, and live broker order writes remain disabled.



## Implementation update — durable aggregate API reconciliation record — 27 October 2026

- Added `BrokerApiReconciliationRecord` and Alembic revision `202610270030` (parent `202610270029`) for owner-scoped, append-only aggregate API provenance. Stored fields include owner/connection IDs, broker, endpoint/API version, scope, fetch timestamp/status, HTTP/error status, sanitized response JSON, response SHA-256, and idempotency key.
- Wired the authenticated Upstox aggregate endpoint to persist the response as `AGGREGATE_RECONCILIATION_ONLY`, with `per_fill_actual=false`; the response includes the reconciliation record ID. Same owner + connection + endpoint + scope + identical sanitized response is idempotent. Credentials/tokens are stripped recursively from persisted response payload. No canonical per-fill allocation is created and the estimate endpoint remains estimate-only.
- Added route regression assertions for ownership linkage, response hash, token sanitization, aggregate-only status and duplicate-fetch idempotency.
- Code/test commit `77bb07c0b6ee075e5e1eaa61ab0a5d138475953b`; Backend CI [#40475498978](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40475498978) was in progress at checkpoint refresh. An earlier model/migration commit is also under CI [#40475479511](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40475479511). **Do not mark this increment green until exact-head CI finishes successfully**, including SQLite/PostgreSQL migration round-trips, broker-write boundary and synthetic restore.
- Remaining validation: inspect CI results; fix any failures; add/finalize tests for owner isolation and immutable-record behavior if gaps remain; update maintained docs/checkpoint to the exact green head. Production Oracle restore and genuine contract-note acceptance remain deferred until evidence exists.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` out of scope; PR #6/#7 remain Draft/unmerged; PAPER mandatory; live broker order writes disabled.



## Confirmed green checkpoint — aggregate API reconciliation persistence — 27 October 2026

- **Verified green code/test head:** `77bb07c0b6ee075e5e1eaa61ab0a5d138475953b` — [Backend CI #40475498978 SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40475498978).
- Confirmed job steps all succeeded: backend pytest, broker-write boundary, SQLite Alembic upgrade/downgrade/re-upgrade, PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade, isolated synthetic PostgreSQL + document-volume restore, and retained synthetic restore evidence.
- The green result applies to code/test head `77bb07c...`; subsequent documentation commits have separate CI runs and are not implied green by this result.
- Implementation in this checkpoint: dedicated `BrokerApiReconciliationRecord`, migration `202610270030`, authenticated Upstox aggregate route persistence, sanitized response payload, response SHA-256, owner/connection linkage, idempotency and route regression assertions. Aggregate records remain reconciliation-only; no per-fill allocation or actual accounting promotion.
- Next: finish explicit cross-owner isolation and immutable-record regression coverage; check latest documentation CI separately. Then proceed to next Phase 3 accounting acceptance gaps (component applicability, per-fill identity/paise totals, replay/rollback, effective-dated tariff and statutory GST/IPFT rule verification). Do not claim Phase 3 complete until all acceptance gates pass.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.


## Follow-up regression coverage — 27 October 2026

- Added tests at commit `688cb70e2d64b866fbb9b6f19c7675ab764a0ecf` for cross-owner connection isolation (the aggregate API must not be called for a connection owned by another user) and immutable snapshot behavior (updates must fail and original evidence remain unchanged after rollback).
- The prior implementation head `77bb07c...` has confirmed green Backend CI #40475498978, including pytest, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, and synthetic restore. The new test commit does not inherit that CI result. No CI run was visible for `688cb70...` at checkpoint refresh; verify the run on this exact head before marking the new regression coverage green.


## CI failure and corrective test fix — 27 October 2026

- Regression-test CI failed on commits `5f3a68a...` / `93a7984...`: **1 failed, 1128 passed**. Failure was in the new cross-owner test because fixture `make_user()` defaults to the same email (`tester@example.com`), so creating a second user violated the unique email constraint before exercising ownership logic.
- Corrected test to create `owner@example.com` and `other-owner@example.com` in commit `977ad6b7e6eeae1346b28c03c2d83bb62ec93910`. This is a test-fixture correction, not an application/accounting change. Exact-head CI is pending and must pass before accepting this coverage.
- The other failure was not observed; the job summary shows 1 failure and 1128 passes. Migration/safety/restore steps were skipped because pytest failed. Do not claim the new head green until the entire workflow succeeds.


## Confirmed green — owner isolation and immutable aggregate API evidence — 27 October 2026

- Corrected code/test head `977ad6b7e6eeae1346b28c03c2d83bb62ec93910` passed Backend CI [#40476768203](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40476768203). All workflow steps succeeded: pytest, broker-write boundary, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore, and retained restore evidence.
- Documentation CI [#40476805191](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40476805191) also passed.
- The failure was limited to the ownership test fixture using the same default email twice; the correction uses distinct emails. The owner-isolation and immutable-snapshot tests are now covered by the green backend run.
- Next: continue Phase 3 accounting acceptance with targeted component applicability, exact fill identity and paise totals, replay/rollback and tariff/GST/IPFT rules. Aggregate API snapshots remain reconciliation-only, not per-fill actuals. Phase 3 remains incomplete until remaining acceptance gates pass.
- Safety: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.



## GST policy boundary regression tests added — 27 October 2026

- Added three focused tests at code/test commit `91212a0224f3bf4a01bff06c14764a404c1cbc67`: a zero-valued taxable component is accepted as an explicit zero but omission is rejected; unknown extra components and nonfinite/negative/invalid monetary values fail closed; effective end dates are inclusive and expired policies are rejected.
- These tests supplement existing checks for exact scope, effective-dated policy selection, overlap/conflict rejection, COMBINED/SEPARATE/NOT_APPLICABLE IPFT representations, and paise precision. They do not approve the Upstox GST candidates; those remain DRAFT due unresolved conflicting historical source evidence.
- **CI for commit `91212a0...` is pending/unverified at checkpoint creation.** Do not treat the new tests as green until the exact-head Backend CI completes all pytest, broker-write boundary, SQLite/PostgreSQL migration and synthetic restore gates. If it fails, inspect logs, fix and rerun before checkpointing green.
- The previously verified head remains `977ad6b7...` with Backend CI #40476768203 and documentation CI #40476805191 green. The new commit does not inherit that status.



## Confirmed green — GST policy edge-case tests — 27 October 2026

- Code/test commit `91212a0224f3bf4a01bff06c14764a404c1cbc67` passed Backend CI [#40477899628](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40477899628). All steps succeeded: backend pytest, broker-write boundary, SQLite upgrade/downgrade/re-upgrade, PostgreSQL 16 upgrade/downgrade/re-upgrade, synthetic PostgreSQL/document-volume restore and retained restore evidence.
- The GST component policy regression additions cover explicit zero vs missing, unknown/nonfinite/negative/invalid amounts, and inclusive effective-end/expired policy behavior. Documentation commits also triggered Backend CI runs #40477921259 and #40477930671; all workflow steps are confirmed successful as well.
- This verifies tests and safeguards, not independent statutory approval of the four Upstox GST candidates and not Phase 3 completion. Keep candidate tariff/rule approval gated on primary-source conflict resolution and independent review.
- Next: examine tariff variance tests and charge component applicability/replay/rollback coverage; improve the most material uncovered gap, then verify exact-head CI and update checkpoint. Safety unchanged: only `tradepro-improved`; original `Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.



## Further GST regression coverage — exact scope and paise rounding — 27 October 2026

- Added tests at code/test commit `c010b7d010351465b87f8e6d844fc9171dfc5dad` for GST half-up paise rounding (18% of ₹0.03 rounds from ₹0.0054 to ₹0.01) and fail-closed policy selection when broker, exchange, segment or product differs.
- Exact-head Backend CI has not yet been verified. Previous green code/test commit remains `91212a0224f3bf4a01bff06c14764a404c1cbc67` / CI #40477899628. Do not treat the added tests as green until the new exact-head workflow passes pytest, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips and synthetic restore.
- Existing variance service already covers source-fill-set identity, quantity/date mismatch, response digest and conflicting replay; next work should focus on any untested component-applicability or rollback boundary rather than duplicating those tests.



## Confirmed green — GST scope and rounding regression tests — 27 October 2026

- Code/test commit `c010b7d010351465b87f8e6d844fc9171dfc5dad` passed Backend CI [#40478376361](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40478376361). All workflow steps succeeded: backend pytest, broker-write boundary, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore and retained restore evidence.
- Newly verified tests cover GST half-up paise rounding and fail-closed selection on broker/exchange/segment/product scope mismatch, in addition to the earlier zero-vs-missing, invalid monetary value and effective-date edge cases.
- Documentation commit `334a078449408beef42e1d761f264d6bb17def19` has Backend CI #40478395488 in progress at refresh; do not claim documentation CI green until it completes. More recent doc commits must likewise be checked on their exact heads.
- Next: continue with uncovered accounting component applicability and rollback boundaries; preserve existing variance service coverage for fill-set identity, quantity/date mismatch, response digest and conflicting replay. GST/IPFT candidate approval remains gated on authoritative effective-dated source resolution and independent review. Phase 3 is not complete.
- Safety unchanged: only `tradepro-improved`; original `Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.



## Confirmed green — latest GST policy test and documentation CI — 27 October 2026

- The code/test head containing GST scope and half-up paise rounding tests remains `c010b7d010351465b87f8e6d844fc9171dfc5dad`; Backend CI [#40478376361](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40478376361) passed.
- Documentation-triggered Backend CI runs [#40478676089](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40478676089), [#40478683982](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40478683982), and [#40478691999](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40478691999) are now confirmed complete with success for every step: pytest, broker-write boundary, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore, and retained restore evidence.
- Current maintained docs were fetched from the target branch and reflect the latest work. This new checkpoint update itself creates new documentation commits and those exact heads need CI verification; do not assume this update is green until those runs finish.
- Next: review IPFT representation mode/component applicability and atomic rollback behavior, add only missing regression tests, then verify exact-head CI. Existing variance replay protection is already covered. GST/IPFT statutory candidates remain unapproved until authoritative effective-dated sources and independent review resolve conflicts; green tests alone do not confer statutory approval.
- Safety unchanged: work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` is out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.



## CI reconciliation and atomic-promotion coverage review — 27 October 2026

- Documentation commits `432a3d37d88087470ebd7bd720dcd00473125be3` and `3f29c70be6db6bd4221b3c8f07ab718c134f44a1` both passed Backend CI: [#40479126107](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40479126107) and [#40479142058](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40479142058). All steps succeeded: pytest, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore and retained restore evidence. Commit `85ddf8579f68824903d599bc9d05ce5b511cf649` returned no workflow run in the current lookup; do not claim a separate run for it.
- Reviewed `test_live_fill_accounting_service.py`: existing coverage already exercises atomic rollback after staging, failed commit rollback, flush failure rollback, safe exact retry after post-commit refresh failure, and canonical exchange/IPFT once. Also covers DP/demat completeness, reviewed evidence, charge allocation completeness, replay identity and child-fill quantity constraints. Do not duplicate these cases without a distinct uncovered defect.
- Next focus: inspect the canonical-source mapping/persistence contract for how source rows map to the six-component live-fill set and whether a partial mapping can be mistaken for complete. If no concrete gap exists, proceed to remaining acceptance/evidence gates rather than adding redundant tests.
- Statutory GST/IPFT candidate approval remains gated on authoritative effective-dated evidence and independent review; passing tests do not approve the tariff. Safety unchanged: only `tradepro-improved`; original `Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.



## Source-to-canonical mapping review and documentation CI closure — 27 October 2026

- Documentation CI runs #40479568869, #40479578088, and #40479585940 all completed successfully for commits `95d67dfe108f7d8472f9e6a3f3f69205147f94ee`, `355a8453e85b8121ecfa60aed24ccc2e891d8770`, and `2c76c3559501133408870e155deacb7d9816865d` respectively.
- Reviewed `broker_charge_verified_allocation_persistence_service.py`, `broker_charge_canonical_allocation_plan.py`, `broker_charge_component_set_contract.py`, and `broker_charge_verified_component_canonicalization.py`. The planner requires unique persisted source IDs, same evidence/hash, VERIFIED status, reviewer distinct from extractor, INR currency, source locator, common reviewed fill manifest, fingerprinted fill IDs and explicit reviewed weights; allocations reconcile exactly to the canonical source total and remain marked non-persisted/non-approved at planning time.
- The persistence adapter deliberately blocks split transaction/IPFT persistence into the existing six-component model until a durable canonical-source ledger can link multiple source rows to one canonical component. Do not weaken this guard or mark aggregate plans as accounting-approved. A future schema migration is required before safely persisting these split representations.
- Next: identify a concrete schema/model path for a durable source-to-canonical relationship and assess migration compatibility before implementing it. Keep split rows blocked until migration and DB tests are ready. GST/IPFT statutory rule approval remains independently gated on authoritative effective-dated sources and review.
- Safety unchanged: only `tradepro-improved`; original `Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.



## Refined finding — canonical-source link schema already exists — 27 October 2026

- Correction to the prior next-step wording: the durable normalized source-link table is already present in model `BrokerChargeCanonicalSourceLink` and migration `202610250025_normalize_canonical_source_links.py`. The migration links canonical snapshots to source-component rows with foreign keys, unique source membership, unique per-snapshot ordinals and a nonnegative ordinal check. Do not create a duplicate table/migration.
- The remaining limitation is in `broker_charge_verified_allocation_persistence_service.py`: it still validates the legacy six-component set and explicitly rejects a plan whose provenance contains multiple source component names. The schema exists, but the persistence workflow does not yet safely consume it for split transaction/IPFT mapping.
- Safe next step: inspect canonical snapshot creation/review services and tests to ensure source links are written atomically with snapshots and revalidated during independent review. Then determine whether split mapping can be enabled without changing the six-component allocation contract; if not, retain the fail-closed block and document exact unmet invariant.
- Latest confirmed CI remains documentation runs #40479568869, #40479578088 and #40479585940 successful. The current documentation updates need exact-head CI verification. Statutory candidate approval remains gated on authoritative source evidence and independent review. Safety unchanged: only `tradepro-improved`; original `Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker writes disabled.



## Split-source snapshot workflow coverage clarified — 27 October 2026

- The latest docs commits `0ccfe4194331a802ae7117dc71a37537b2eede9b`, `d8b62051d92f6ec8d47cf14cb7a2a4fc23a88056`, and `0468eb1cccb19dbaa29351ba0e17b42b8ce8ec9f` passed Backend CI runs #40480367450, #40480378523, and #40480401549 respectively.
- Further review of `test_broker_charge_canonical_component_snapshot_service.py` confirms existing split transaction/IPFT tests cover snapshot creation, independent review, canonical snapshot allocation persistence, missing normalized source-link rejection, and reconciliation checks. Therefore split-source support is present in the canonical snapshot path; do not characterize the entire feature as absent.
- The legacy direct allocation adapter `broker_charge_verified_allocation_persistence_service.py` still rejects multi-source plans. Next audit route/service callers to confirm which path production APIs invoke and ensure no endpoint bypasses canonical snapshot review. Only consider enabling or deprecating the legacy path after caller and safety review.
- Next check exact-head CI for this documentation update, then verify route wiring and whether the legacy direct path is reachable. Preserve fail-closed behavior meanwhile. GST/IPFT tariff approval remains gated on authoritative effective-dated source review. PAPER mandatory; live broker order writes disabled; PR #6/#7 Draft/unmerged; original `Tradepro` out of scope.


## Route audit finding — aggregate response credential sanitization — 27 October 2026

The API wiring audit found a concrete safety gap in `backend/app/api/v1/upstox_charges.py`: aggregate API response payloads were sanitized before durable persistence but the HTTP response returned the raw payload. A credential-like field such as `access_token` could therefore be exposed to the authenticated caller even though it was not stored. Fixed by applying `_sanitize_api_value` to the aggregate response payload and added a route regression assertion that the field is absent from the HTTP response. Code commit `203947ee25437e5b4637d25f365f0d1df7575fb1`; test commit `7e17376a91c8d835e1af42377be49c499d013bea`. Exact-head CI is pending; do not mark this fix green until CI passes. The brokerage-estimate route was not changed. Split-charge canonical snapshot safeguards remain in place. PAPER mandatory; live broker writes disabled; PR #6/#7 Draft/unmerged; original `Tradepro` out of scope.


## Aggregate API response sanitization — CI verified — 27 October 2026

- Backend CI runs #40481297561, #40481317091, #40481339870 and #40481349885 all completed successfully. Every run passed pytest, broker-write boundary enforcement, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore, and retained restore evidence.
- The aggregate Upstox charge API now applies `_sanitize_api_value` to the HTTP response payload as well as the persisted evidence. Route regression coverage asserts that `access_token` is not returned. Aggregate responses remain explicitly `per_fill_actual=False`; this is evidence capture/reconciliation, not per-fill accounting promotion.
- Route-wiring audit continues: confirm exposed charge APIs cannot bypass independently reviewed canonical snapshots for split transaction/IPFT evidence. Existing fail-closed direct adapter remains unchanged.
- The latest documentation commits triggered by this note need their own CI verification. Do not call this documentation revision green until those exact-head runs pass. Safety unchanged: only `tradepro-improved`; original `Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.


## DP/demat instrument-applicability fix — exact-head CI verified — 27 October 2026

- Added an independent instrument classification check to the DP/demat manifest eligibility query: a fill must be a mapped `EQUITY` instrument as well as an `EQUITY_DELIVERY` SELL with matching broker connection, order/fill side, instrument token and ownership. This prevents an incorrectly classified OPTIONS/FUTURES instrument from passing the DP-specific eligibility gate solely because the order segment says delivery.
- Regression coverage: `test_demat_manifest_rejects_non_equity_instrument_even_if_order_segment_says_delivery` sets the instrument type to OPTIONS while retaining delivery-SELL order metadata and asserts rejection.
- Implementation commit `447e9703f4bcf43dc6392d0d3741caee7709ce95` passed Backend CI [#40482878220](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40482878220). Regression-test commit `e62c9518df2edd9c80473b55f3a63a632a30121a` passed exact-head Backend CI [#40482895888](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40482895888). Both workflows completed successfully, including pytest, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore verification.
- Next: continue component-applicability audit for supported instrument/segment/product combinations and confirm missing/inapplicable components are explicit rather than silently zeroed. Then synchronize maintained documents to the resulting verified head. This checkpoint documents CI for the code/test commits; this documentation edit itself still requires its own exact-head CI.
- Evidence limits unchanged: synthetic restore is not production Oracle restore acceptance; no genuine personal contract note is available/required for current code-level progress. GST/IPFT source/tariff approval remains separately evidence-gated. Safety unchanged: only `tradepro-improved`; original `Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.


## 27 October 2026 — latest charge-total completeness CI checkpoint

- Latest verified code increment: commit `431db3a1de4b00afceefabf3def71c1ddb08a446` passed Backend pytest CI [#40484300318](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40484300318) (workflow completed successfully at 2026-10-27 09:56 UTC). This verifies the API-schema integration that derives `total_charges_complete` using the same reconciliation function as the execution model.
- The completeness service now requires a recognized DP/demat status, consistent amount applicability, valid core charge components, and exact equality between the persisted total and the recomputed total. A resolved DP status alone is not enough to mark a total complete.
- Prior intermediate attempts #40483567109, #40483589784 and #40483898638 failed; these are retained as history, not treated as green. Service-only CI #40483552159 passed. The schema-integrated code head #40484300318 is the latest successful code verification.
- This does not yet prove all Phase 3 gates pass. Next: verify regression coverage for stale/tampered totals and schema output; audit applicability across equity delivery/intraday, futures/options and product/side; then synchronize maintained docs and verify the resulting documentation head. Continue failing closed for missing/invalid charges and do not silently coerce unknown/inapplicable components to zero.
- GST/IPFT API resolution work remains in place; legal/tariff approval and actual broker evidence reconciliation are distinct gates. Synthetic restore is not production Oracle restore acceptance; real Oracle backup/restore can be accepted after deployment/backups exist; genuine personal contract note is not required for code-level work but actual broker reconciliation requires suitable real evidence.
- Safety unchanged: work only in `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is out of scope and must not be modified; PR #6/#7 remain Draft/unmerged; PAPER mode mandatory; live broker order writes remain disabled.
- Documentation changes in this entry themselves require CI on the resulting exact head before this documentation checkpoint is considered green.


## Resumed checkpoint — 27 October 2026 (API reconciliation security increment)

- Verified branch: `phase3/cross-broker-gst-ipft-resolution`; PR #7 remains open, Draft and unmerged.
- Exact current code/test head before this documentation refresh: `a0586b27e8ccda9446f01fd109e8986875c536b3`.
- Backend workflow [#40484960486](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40484960486) completed successfully on that exact head. Verified steps: backend pytest, broker-write boundary enforcement, SQLite upgrade/downgrade/re-upgrade, PostgreSQL 16 upgrade/downgrade/re-upgrade, synthetic PostgreSQL/document-volume restore, and restore-evidence retention. The job result confirms success; this checkpoint does not infer a test count not exposed in the run summary.
- Recent security work remains: aggregate API responses are sanitized; aggregate charge responses are explicitly not per-fill actual evidence; the public charge API must not be used to approve actual per-fill accounting. The previously checked regression runs #40481297561 and #40481317091 also completed successfully.
- Component-applicability audit reviewed the current DP/demat gate: mapped broker trade, child/local order and instrument must match; DP eligibility requires SELL + EQUITY_DELIVERY + an EQUITY instrument. DP remains separate from the six core charge components and must be reviewed/reconciled before a delivery SELL can be accounted.
- Next implementation gate: inspect the complete supported instrument/segment/side/product matrix and ensure every required charge is either applicable with reviewed evidence or explicitly NOT_APPLICABLE; unknown or missing must keep totals incomplete. Then audit stale/tampered total and replay/rollback coverage without duplicating tests already present.
- GST/IPFT work is not restarting: effective-dated policy and statutory GST primitives exist, but actual invoice-backed accounting approval and product/broker tariff approvals remain separate evidence/reviewer gates. Public broker APIs/calculators and aggregate charges remain estimates/reconciliation evidence, not actual per-fill proof.
- This documentation refresh creates a new head; its own exact-head CI must pass before the documentation checkpoint is called green.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled. No real personal contract note is required for synthetic engineering tests; production Oracle restore acceptance waits until deployment backups exist.


## Annual GST statement reconciliation finding — 27 October 2026

- A user-provided Upstox/RKSV annual global transaction statement for FY 2022–23 was reviewed as annual aggregate evidence, not as an individual contract note. Its visible charge rows do not, by themselves, reconcile the reported aggregate “IGST on Charges” line to a unique taxable base at paise precision.
- Preserve original source-row labels exactly. Do not relabel an STT rounding row as SEBI fees. Establish the taxable base from underlying invoice/contract-note lines and the applicable historical policy; do not choose a charge merely because it makes the arithmetic match.
- The GST reconciliation helper correctly retains reported-vs-expected variance instead of inferring or rewriting the base. A small annual variance may reflect invoice-level tax rounding/aggregation or a charge not visible in summarized lines; this annual statement alone cannot distinguish these explanations.
- Do not use an annual AGS total to approve actual per-fill GST or promote canonical charge allocations. Next evidence gate: an itemized individual contract note or underlying invoice-level breakdown. Keep FY 2022–23 evidence separate from the 2026 public-schedule estimate policy.
- This is an evidence-scope clarification, not a change to GST/IPFT policy or a declaration that the broker billed incorrectly. No personal identifiers or account-specific figures are copied into this repository note.
- Latest code/test head remains `9eb278588b78d2a966cc196c15d7a4d9a6ae8868`; Backend CI [#40505176395 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40505176395). This documentation sync creates a new head and requires its own exact-head CI before it is marked green.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` out of scope; PR #6/#7 Draft and unmerged; PAPER mandatory; live broker order writes disabled.


## End-of-session resume checkpoint — 27 October 2026

- Verified current branch head before this checkpoint refresh: `98a2d2f6d440d0402d89c058b88b111d55cb4228`.
- Exact-head Backend tests CI [#40526675673 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40526675673). The previous code/test head CI [#40505176395 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40505176395) remains recorded as historical evidence.
- Latest GST finding: the user's FY 2022–23 Upstox/RKSV annual global transaction statement is aggregate evidence, not a per-order contract note. Its summarized charge rows do not uniquely establish the taxable base for the reported ₹20.15 “IGST on Charges” line. Preserve source labels exactly; the statement lists SEBI fees ₹0.22 and STT-RND ₹0.32, so do not relabel the latter as SEBI fees or assume it belongs in the GST base. This is an unresolved invoice-level evidence question, not proof the broker billed incorrectly.
- Code inspection confirmed `gst_source_reconciliation.py` compares a caller-reviewed taxable base against reported tax and retains any variance; `statutory_stock_broking_gst.py` uses CGST Act section 15 default inclusion and only applies a Rule 33 exclusion when all pure-agent evidence flags are true. These are primitives, not a substitute for broker-specific, effective-dated invoice evidence or independent approval.
- Documents synchronized on the current work increment: `PHASE3_LATEST_CI_CHECKPOINT.md`, `GST_IPFT_ACCEPTANCE_MATRIX.md`, `PROGRESS.md`, `HANDOVER.md`, `MASTER_ROADMAP.md`, `PROJECT_INSTRUCTIONS.md`, `AUDIT_REPORT.md`, `REQUIREMENTS_AUDIT.md`, `CHANGELOG.md`, and `ROADMAP.md`. The previous documentation commit CI is green; this checkpoint refresh itself will require its own exact-head CI before it is called green.
- Resume next session with the component-by-component accounting acceptance audit: supported instrument/segment/side/product matrix; required charges marked applicable or explicitly NOT_APPLICABLE; missing/unknown charges keep totals incomplete; audit paise-exact per-fill identities, replay/idempotency, tampered totals, atomic promotion and rollback tests. Do not duplicate existing tests without first inspecting coverage.
- GST/IPFT work is not being restarted. Continue from this checkpoint and use an itemized individual contract note/invoice breakdown if available to resolve the annual-statement variance. Do not block unrelated accounting acceptance work on that external evidence.
- Safety remains unchanged: modify only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` is out of scope; PR #6/#7 stay Draft/unmerged; PAPER mode mandatory; live broker order writes disabled. No real personal broker note is required for synthetic engineering tests; real Oracle restore acceptance waits for deployment backups.

## Historical Upstox contract-note GST regression — 27 October 2026

- Transcribed the five user-provided daily contract notes (23, 24, 25, 27 and 30 January 2023) into regression fixtures in `backend/tests/test_historical_upstox_contract_note_gst.py`.
- Test commits: fixture `98f14aef1b3b541c2a6e07beb227b6f3f0471a42`; place-of-supply comment clarification `547917868d28d3f46f1f549a8daa50d57fc4542d`.
- Cases assert each disclosed taxable value equals brokerage + transaction charges + SEBI fees; each daily brokerage GST and charges GST rounds to the contract note's figures; and the statutory GST valuation primitive reproduces the daily total IGST for the disclosed base.
- These are daily aggregate invoice fixtures, not per-fill charge evidence. The supplied text has no distinct IPFT line. Tests deliberately do not infer IPFT=0 or synthesize a separate amount. Historical IPFT tariff must be selected by trade date; a current API estimate is not historical booked-charge evidence.
- CI for the new test commit and any subsequent documentation head is not yet verified in this checkpoint. Do not mark it green until exact-head Backend CI passes. No GST/IPFT tariff was newly approved by this test-only change.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.

## Effective-dated historical IPFT estimate gate — 27 October 2026

- Added `calculate_ipft_estimate_for_scope()` in `backend/app/services/broker_tariff_rules.py`. It requires an approved exact-scope `TariffRule`, NSE/FO/OPTIONS, explicit BUY/SELL, PREMIUM basis and INR_PER_CRORE; generic tariff calculation now fails closed for IPFT. The caller must supply the correct source-defined premium aggregation scope. This helper does not allocate aggregate IPFT to fills or certify booked charges.
- Added date-boundary tests for the official NSE schedule: ₹0.01/crore before 1 April 2023, ₹50/crore for equity options from 1 April 2023 through 28 February 2026, and rollback to ₹0.01/crore effective 1 March 2026. Sources: [NSE/FA/56129 (24 March 2023)](https://nsearchives.nseindia.com/content/circulars/FA56129.pdf) and [NSE/FA/73061 (27 February 2026)](https://nsearchives.nseindia.com/content/circulars/FA73061.pdf).
- These tests validate date selection and guarded estimate arithmetic; they do not activate production tariff records. No production rule is automatically approved by the tests, and actual IPFT remains distinct from the current Upstox calculator estimate and the supplied daily contract-note aggregates.
- The five historical GST invoice fixtures are in `backend/tests/test_historical_upstox_contract_note_gst.py`. The note transcription does not separately identify IPFT; missing is not zero. Exact-head CI for the latest code/test and documentation commits is pending verification.

- New code/test commits: `19ed761219b46fc687eff74e8fe245fececdc3b0` (guarded IPFT helper), `f2d486b1b65af910fd9ca1dbc86be1a7c4385d7e` (date-boundary tests), `5b718ae5cd78e3c49814210f97c2671e95dad8fe` (test correction). CI runs are being checked; do not mark this increment green until the latest exact-head run completes successfully.

## Superseding decision — GST invoice regressions and API evidence scope (27 October 2026)

- The five user-provided January 2023 Upstox daily contract-note fixtures and effective-dated IPFT estimator tests are included in code/test head `fe4c8c484650a8b6e63f822a8c7581431c855d22`.
- Exact-head Backend CI [#40545398934 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40545398934): **1,149 passed, 1 warning**. Broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, and synthetic restore checks passed.
- GST daily-invoice calculation is now regression-validated for all five supplied dates. Do not reopen the basic 18% formula as an unresolved research question. The annual AGS two-paise variance remains an aggregate reconciliation note; it is not evidence of a broker error and must not block the GST implementation.
- The Upstox pre-trade brokerage calculator is estimate-only. The post-trade charges endpoint `/v2/trade/profit-loss/charges` is aggregate-only. Preserve these meanings through `broker_charge_api_value_resolution.py`; do not promote either response to per-fill booked charges. Reconcile contract-note actuals at the source's disclosed scope.
- IPFT is not a blocker to the validated GST formula. Use effective-dated IPFT only when the product/segment and source-supported premium basis apply. The supplied January 2023 note text has no separately identified IPFT line, so don't assume either a separately booked IPFT amount or that it is bundled. Preserve it as not separately disclosed; do not synthesize zero or an allocation. If no applicable IPFT rule/component is evidenced for a trade, leave it not applicable/unknown according to the source and product scope rather than holding up GST.
- The guarded estimator is for estimate calculation only and requires an approved effective-dated tariff rule and explicit scope. It does not activate a production tariff or prove historical booked IPFT.
- Next Phase 3 work should proceed to the remaining accounting acceptance gates (fill identity, replay/idempotency, atomic rollback and component applicability), while using these GST tests as regression coverage. Only revisit IPFT when an applicable source-backed tariff or actual source field requires it.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.


## Verified API-first GST/IPFT research checkpoint — 27 October 2026

- Latest verified code/test head before this documentation refresh: `64115efbcfd866fad68d67bd5abef4a0bc1b977f`.
- Exact-head Backend CI [#40547529549 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40547529549). Backend pytest, broker-write boundary, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore and evidence retention all passed.
- Research-confirmed Upstox sources: [Brokerage calculator](https://upstox.com/developer/api-documentation/get-brokerage/) is estimate-only and returns component breakdown including GST/IPFT; [post-trade charges](https://upstox.com/developer/api-documentation/get-trade-charges/) is segment/period aggregate evidence, not per-fill actual. Preserve null/missing/invalid/zero distinctions.
- Historical NSE finding: official circular FA73061 (27 Feb 2026) changes the transaction/IPFT split from 1 Mar 2026 while preserving the combined per-crore outflow: cash Rs 307/crore (306.99 transaction + 0.01 IPFT), equity futures Rs 183/crore (182.99 + 0.01), equity-options premium Rs 3,553/crore (3,552 + 0.01). Source: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf. Do not reuse these rates for BSE/MCX or retroactively apply them.
- GST decision: retain API-reported GST as estimate evidence and independently calculate a transparent Section 15 / Rule 33 cross-check. Pure-agent exclusion requires all Rule 33 evidence conditions; charge labels alone are insufficient. Store API GST, engine GST, taxable bases and variance separately; never silently overwrite or auto-approve a mismatch. Official CBIC FAQ: https://cbic-gst.gov.in/sectoral-faq.html.
- Existing `broker_charge_api_mapping.py` and `broker_charge_api_value_resolution.py` already enforce exact endpoint/schema/scope/date semantics and block Upstox estimate/aggregate endpoints from per-fill actual use. Existing null-vs-zero and endpoint-guard tests remain essential.
- Documentation update commit `72900a8fa1b3770f878c843bcb649d263de7259d` adds the API-first decision to `GST_CROSS_EXCHANGE_COVERAGE.md`. CI on the documentation-updated head must be checked before that head is called green.
- Next implementation gate: add/verify explicit API-to-engine comparison tests and source-backed historical IPFT boundary fixtures; preserve fail-closed behavior for unsupported BSE/MCX tariff scopes. Do not claim every exchange/product tariff is fully verified until those source scopes are implemented and tested.

Safety unchanged: work only in `tarunsharma2610-del/tradepro-improved`; PR #6/#7 remain Draft/unmerged; PAPER mode mandatory; live broker writes disabled.


## GST/IPFT closure work — API comparison implementation, 27 October 2026

- Added `backend/app/services/broker_gst_reconciliation.py` and `backend/tests/test_broker_gst_reconciliation.py` on this branch. The new service keeps broker-reported GST estimate separate from the independent statutory engine estimate and reports taxable base, tax type, variance and status.
- Any non-zero API-vs-engine variance remains reviewable, including a 1-paise rounding difference; tolerance does not auto-approve. Missing, null and invalid API fields remain unavailable; explicit numeric zero is preserved and checked as a real value. Sub-paise INR GST is rejected.
- Existing IPFT boundary tests already cover 31 Mar / 1 Apr 2023 and 28 Feb / 1 Mar 2026, including the old ₹50/crore period and the post-1 March 2026 ₹0.01/crore period. These are estimates for the guarded NSE equity-options scope only.
- Latest implementation commits before documentation synchronization: service `729b8b19499173d70b2c9efaf682403f521acbcf`, tests initially `fea1b12fa84391307e66994f10cfbec8dcbcbec9`, variance-review hardening `527861ed8ca6b6ad3604d8bc2ab4e61981a1294d`, and test expectation `2a069fef64958e6f5d7bd4a9abb33d7c944f314b`.
- Earlier baseline code/test head `64115efbcfd866fad68d67bd5abef4a0bc1b977f` passed Backend CI [#40547529549](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40547529549). CI for the new implementation and its documentation is pending; do not mark the newest head green until exact-head CI completes successfully.
- Coverage document updated in `GST_CROSS_EXCHANGE_COVERAGE.md`; documentation commit `5721f5d351379ced73a10b3572cd6d783ab55881`. Check CI on the final checkpoint commit after this update.
- Still outstanding for full Phase 3 acceptance: wire the comparison into the applicable API/data flow (without turning estimate values into actual accounting), prove the exact live Upstox response schema and mapping for the active API version, source/verify supported BSE/MCX tariff scopes, synchronize the maintained documents, and run exact-head CI. No live API request was made because authenticated user credentials are not available in this task context.

Safety unchanged: work only in `tarunsharma2610-del/tradepro-improved`; PR #6/#7 Draft/unmerged; PAPER mode mandatory; live broker order writes disabled.


## Next acceptance increment — nested Upstox GST response path

- Added dotted JSON field-path support in `backend/app/services/broker_gst_reconciliation.py` so the comparison can read nested broker responses such as `data.charges.gst` without flattening assumptions.
- Added regressions in `backend/tests/test_broker_gst_reconciliation.py` for nested GST exact match, missing intermediate path, explicit null and malformed field path.
- Implementation commit: `ff2d69546e5aad37c519c6622f51018bf7706ad5`; test commit: `a6f88dc85dcb25d903e610aaf30ce395ec12d650`.
- Previous exact-head CI [#40549308036 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40549308036) applies to earlier head `0b5902ea35621d613589f7c8762b4d6658df9104`, not this increment. CI must be confirmed on the final updated head before this increment is called green.
- Still open: wire this comparison into a caller that has authoritative valuation lines and supplier/place-of-supply state inputs; preserve estimate-only semantics. Complete component-by-component accounting acceptance and source-verified BSE/MCX tariff scope, then synchronize remaining maintained documents on a verified green head.
