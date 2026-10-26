## CURRENT AUTHORITATIVE CHECKPOINT — 26 October 2026 (GST per-fill allocation test CI passed)

- Repository: `tarunsharma2610-del/tradepro-improved`; branch: `phase3/durable-per-fill-charge-allocation`; PR #6 remains open/draft.
- Implementation/test commit: `162e804c448cafa332e3c9a18f72ca4213d238ea`; exact-head Backend CI [#40298202486 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40298202486).
- Added `test_gst_allocation_plan_uses_only_reviewed_invoice_component_total` in `backend/tests/test_broker_charge_canonical_allocation_plan.py`. Synthetic reviewed GST source total ₹58.91 allocates ₹19.64 and ₹39.27 across two explicitly reviewed fill weights, reconciling exactly. This proves deterministic allocation only; it does not verify an actual invoice, approve GST treatment, persist accounting, or promote the plan.
- This checkpoint supersedes older checkpoint statements for current status; historical entries are retained for audit history only.
- Next gate: product/segment-specific charge-component acceptance and GST source reconciliation. Add only tests justified by source-backed mapping and invoice/contract-note evidence. Unknown/null values remain unknown; do not tax trade notional or double-count IPFT already included in combined exchange charges. All tariff candidates remain `DRAFT`.
- On every implementation change, verify exact-head CI. After this documentation checkpoint commit, verify CI again on that exact documentation commit.
- Safety: PAPER mandatory; live broker order writes and automatic live-fill promotion disabled; PR #6 stays draft/unmerged absent explicit authorization; original `tarunsharma2610-del/Tradepro` untouched. Phase 3 remains IN PROGRESS.

---

## Authoritative Phase 3 checkpoint — 26 October 2026 (latest verified CI)

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
