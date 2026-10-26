## Current working state — 26 October 2026 (DP/demat optional mapping regression fix pending CI)

- **Target repository only:** `tarunsharma2610-del/tradepro-improved`. PR #7 remains open/Draft/unmerged on `phase3/cross-broker-gst-ipft-resolution`; PR #6 also remains Draft/unmerged. Live broker writes remain disabled; PAPER mode only.
- **Latest code head:** `a85f2023ff28a54bcc2a04fe36a732561b1aa337`.
- **Latest completed exact-head CI before this fix:** Backend tests run [#40365836710 — FAILURE](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40365836710) on `69a4c9154370cf34f1f7c8a20a03d41d6e332081`: 46 failed, 988 passed. The failure root was snapshot materialization iterating the expanded allocation-plan component set (including optional `demat_transaction_charges`) while indexing the six-component canonical map, producing `KeyError: demat_transaction_charges`.
- **Fix committed at current head:** snapshot materialization now iterates the actual six-component canonical source mapping, preserving the six persisted live snapshots. DP/demat remains separately represented in the optional map and live snapshot promotion remains explicitly blocked when DP/demat evidence exists, pending Execution persistence and total-charge reconciliation.
- **CI status for current head:** no run result has been returned yet. Do not mark this head green or treat it as an acceptance checkpoint until exact-head CI passes.
- **GST/IPFT status:** current Upstox documentation indicates the P&L trade-charge API exposes a `charges_breakdown` object including `taxes.gst`, `charges.ipft`, `charges.sebi_turnover`, and `charges.demat_transaction`; the pre-trade brokerage API has a different response shape. Published current Upstox pricing states IPFT is combined with transaction charges from 1 March 2026 and GST base differs from the older proposed calculation. Keep adapter shapes distinct, apply effective-dated broker/segment rules, use Decimal/paise arithmetic, and prevent IPFT double counting. Do not treat an estimate or aggregated P&L response as approved actual per-fill evidence without fill-level provenance/reconciliation.
- **Next steps:** confirm current-head CI; fix any remaining failures; add/verify GST base and effective-dated IPFT tests for relevant brokers/segments; sync all maintained docs to the resulting verified head; save a new checkpoint only after CI success.
- User does not trade in their demat account and is not expected to provide a personal contract note. Public broker docs/examples can inform parsing and tariff research but do not replace actual per-fill acceptance evidence.

## Latest verified green checkpoint (superseded for current work)

- Backend tests [#40362044307 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40362044307) on exact head `20c7fb144f621f07f4ef9ecda622fd74fbf736d6`.
- Newer run #40362669264 failed after DP/demat mapping widened the six-component contract. The current branch contains the correction but has not yet earned a new green checkpoint.

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
- GST estimate helper accepts exactly 18%; tests reject 0%, 5%, 100%, and 100.01%. Rate guard does not approve the taxable base; components need reviewer and invoice/source evidence.
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


# Phase 3 — Latest CI Checkpoint

**Checkpoint date:** 25 October 2026  
**Repository:** `tarunsharma2610-del/tradepro-improved`  
**Branch:** `phase3/durable-per-fill-charge-allocation`  
**PR:** #6 — open, draft, unmerged

## Latest verified implementation

- End-of-day exact commit: `075b16af03cf6be4897c381378f68db76a6cbba6`.
- Exact-head Backend CI [#40211145592 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40211145592).
- Resume next: integrate canonical snapshot allocation/reconciliation into live-fill accounting, testing split transaction/IPFT, exact replay, complete totals, and fail-closed unsupported-component rejection.
- Do not repeat the completed concurrency acceptance work.


## Phase 3 status
Implemented and previously verified: normalized canonical source links; immutable reviewed snapshots; split transaction + IPFT provenance; durable per-fill allocation persistence; canonical ledger verification; deterministic paise allocation; promotion/replay checks; tampered-allocation rejection; rollback assertions; incomplete-fill-set rejection; PostgreSQL concurrent-promotion coverage.

**Next step:** integrate canonical snapshot allocation/reconciliation with live-fill accounting and add focused end-to-end tests for split transaction/IPFT mapping, exact replay, and rejection of unsupported components. This documentation update requires its own exact-head CI.

## Required checkpoint protocol
After every CI run, refresh PR head and inspect that exact run. On failure, diagnose full logs, fix root cause and rerun. On success, update all 18 maintained checkpoint documents with exact SHA/run/result/next step, commit the checkpoint, then verify CI on that checkpoint commit. Never inherit a parent's green result as proof a child commit is green.

## Safeguards
Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched. PR #6 stays draft/unmerged absent explicit authorization. PAPER mode is mandatory and live broker order writes remain disabled. Production GST/IPFT tariff acceptance is a separate evidence gate; unapproved tariff candidates remain DRAFT.


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


## GST/IPFT verification research — 26 October 2026 (work in progress)

- Research evidence and decision matrix: [docs/UPSTOX_GST_IPFT_VERIFICATION_2026-10-26.md](docs/UPSTOX_GST_IPFT_VERIFICATION_2026-10-26.md).
- Current official Upstox schedule states 18% GST on brokerage + transaction charges + IPFT, plus demat for equity delivery. NSE circular NSE/FA/73061 supports the combined NSE charge from 1 March 2026: ₹307/crore cash, ₹183/crore futures and ₹3,553/crore options premium, including ₹0.01/crore IPFT. Never add IPFT twice.
- CBIC confirms brokerage is taxable and statutory-recovery exclusion depends on Rule 33 pure-agent conditions. This does not resolve every product-specific GST component in Upstox's billing. Public historical contract-note copies are not authenticated/current proof; aggregate API data is not per-fill proof and nullable IPFT stays unknown.
- Decision: all four GST component-set candidates remain DRAFT. Continue with focused regression tests and resolve taxable-base mapping before any approval. This is a source-research checkpoint only; exact-head CI is required after the documentation commit.
- PR #6 remains open/draft/unmerged; PAPER mandatory; live broker writes and automatic live-fill promotion disabled; original `Tradepro` untouched.


## Latest exact-head CI correction — 26 October 2026

- Failed run: [Backend tests #40302129087](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40302129087), tested PR merge ref `6c5c5f84846e8fbc170d653194565ddc4361fa6b` containing branch commit `8f37b81914e1b46318d16d7c99ee5490449e8f06`.
- Result: 1,002 passed, 1 failed. Sole failure was the evidence regression test expecting the phrase `conflicts with the current Upstox public pricing page`; the document actually says `materially different from Upstox's current public pricing page`. The evidence and DRAFT safety behavior were intact; the assertion was over-specific.
- Correction pushed to branch: `f792627fb0ead15551e2506731b183e9b91482bb` (`test: fix GST evidence wording assertion`). This does not imply CI passed. Verify the latest workflow against this exact branch head and record the result before proceeding to another Phase 3 gate.
- No GST candidate approved. Historical public note remains unauthenticated/out of date and cannot resolve current GST-base mapping. PAPER mandatory; live broker order writes and automatic live-fill promotion disabled; PR #6 open/draft/unmerged; original `Tradepro` untouched.


## Additional GST-source search — 26 October 2026

Publicly indexed Upstox realized-P&L reports for FY 2025–26 show aggregate GST and IPFT totals separately, and a 2025 F&O report also lists SEBI/stamp duty/transaction totals, but none supplies the GST taxable-value composition. A July 2026 Reddit discussion is anecdotal only. CBIC FAQ Q7/Q77 and Rule 33 make pure-agent exclusion conditional; a charge label alone does not decide whether an amount is in the taxable base. No new source resolves the current Upstox tariff versus historical-note discrepancy. GST candidates remain DRAFT. Current branch has a test-assertion fix and documentation updates; verify CI on the latest exact head before marking checkpoint green.


## Follow-up correction to brittle evidence assertion — 26 October 2026

The first wording-only assertion adjustment still failed because the exact phrase in the evidence document is split by Markdown emphasis (`**materially different**`). Updated the regression test to assert the stable semantic phrase `materially different` rather than formatting-sensitive exact markup. This is a test-only wording fix; the evidence finding and all GST candidate DRAFT statuses are unchanged. The current exact-head CI run must pass before the checkpoint is accepted.


## GST/IPFT invoice evidence checkpoint update — 26 October 2026

Direct public contract-note search now includes 11-Feb-2025, 21-May-2024 and 12-Mar-2025 Upstox note copies, with component sums and GST rounding independently reconciled. These historical third-party copies show different printed bases; they do not establish one universal/current actual-charge rule. The current official Upstox page does support the estimate-only direction: 18% on brokerage + transaction charges + demat + IPFT, with IPFT combined into transaction charges and counted once. Do not add SEBI to this current estimate base without current billing evidence. This narrows the research issue: public-schedule estimate direction is set, while actual-account invoice reconciliation remains a separate review gate. Exact-head CI must be checked before acceptance.


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


## GST/IPFT public evidence continuation — 26 October 2026

- Public research addendum committed as [GST_IPFT_PUBLIC_EVIDENCE_ADDENDUM.md](GST_IPFT_PUBLIC_EVIDENCE_ADDENDUM.md). Sources include current Upstox tariff, Brokerage Details API example, and publicly indexed Upstox contract notes dated 21 May 2024 and 12 March 2025.
- Current tariff supports an estimate model with combined transaction/IPFT represented once from 1 March 2026; the API example's GST ₹1.02 versus transaction ₹5.68 + IPFT ₹0.17 remains inconsistent. Historical notes predate current tariff changes and do not resolve the current discrepancy.
- No user-owned contract note is requested. No actual GST logic is promoted. All four actual GST component candidates remain DRAFT pending current post-1-March-2026 invoice evidence or written Upstox clarification. See the addendum for source URLs and reasoning.
- Latest branch head before this addendum was `edabea70b1782e029a0c695eb9543adada731a6c`; exact-head Backend tests run [#40337814532](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40337814532) completed successfully. That run does not verify this new docs commit; CI must be checked against the resulting new head before declaring the checkpoint green.
- Safety unchanged: target `tarunsharma2610-del/tradepro-improved` only; original `Tradepro` untouched; PAPER mode mandatory; live broker writes and automatic live-fill promotion/scheduling disabled; PR #6 draft/unmerged; AI/Algory deferred until Phase 3 acceptance.

- Documentation synchronization follow-up: public GST/IPFT evidence addendum and matching notes are now synced in `UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`, `HANDOVER.md`, and `PROGRESS.md`; the subsequent exact-head CI run must validate this final documentation head.


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


## Cross-broker GST/IPFT work in progress — 26 October 2026

- New active work branch: `phase3/cross-broker-gst-ipft-resolution`.
- Draft PR #7: https://github.com/tarunsharma2610-del/tradepro-improved/pull/7
- Research added: `docs/CROSS_BROKER_GST_IPFT_POLICY_RESEARCH_2026-10-26.md`.
- Generic policy primitive added: `backend/app/services/broker_gst_component_policy.py`; regression tests added: `backend/tests/test_broker_gst_component_policy.py`.
- Current head at this checkpoint update: `eb4e6953428ec7da773558b800118ed8b1ef50fc` (research + implementation primitive + tests before this documentation sync).
- CI status: **not yet verified** for the new PR/head; do not mark green until a workflow run reports success on the exact final head.
- Remaining: wire policy into Upstox estimate helper, add source-backed cross-broker policy candidates/tests, resolve canonical DP/demat persistence and migration gap, then synchronize documentation to exact passing CI commit.
- This is an incremental foundation, not the full GST/IPFT resolution. Tariff candidates remain DRAFT; actual invoice acceptance remains evidence-gated. PR #6 stays Draft/unmerged; PAPER mandatory; live broker writes disabled; original Tradepro untouched.


## GST/IPFT latest checkpoint update — 26 October 2026 (CI fix pending verification)

- Previous exact-head CI run #40358027077: **failed** at `59bdfd2cc66768eff882cdc1ffd00a9dade9c015` with 1,023 passed / 1 failed. Failure was an incorrect expected error-message regex in the new test, not a calculation assertion.
- Fixed the expected message and wired the existing Upstox public GST estimate through the shared GST component policy module.
- IPFT mode is scoped: NSE uses COMBINED (one canonical exchange_charges input); BSE options uses NOT_APPLICABLE and must not inherit NSE IPFT.
- Implementation head after fixes: `393804cc5c21ba70a579b32a6736f6561569413b`.
- Exact-head CI: **pending / not yet reported**. This is not a passing checkpoint. Check workflow run and fix any remaining failures before checkpointing green.
- Remaining gates: source-backed cross-broker tariff policies/tests, DP/demat canonical persistence and migration, synchronized final commit and successful exact-head CI.
- Safety: PR #6 Draft/unmerged; PAPER mandatory; live broker writes disabled; original Tradepro untouched; no personal contract note requested.
