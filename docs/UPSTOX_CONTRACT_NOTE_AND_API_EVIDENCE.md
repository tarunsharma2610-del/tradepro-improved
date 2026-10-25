## Canonical checkpoint reconciliation — 25 October 2026 (after exact-head CI)

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **PR #6:** open, draft, unmerged.
- **Latest verified code/test commit:** `50802e96e06756b57a9f930e0c54c680777922d4`. Exact-head Backend CI [run #40209741299](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40209741299) completed successfully on that SHA.
- **Verified:** backend pytest; broker-write boundary enforcement; SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade; synthetic PostgreSQL/document-volume restore drill. The synthetic restore does not prove actual Oracle Cloud recovery.
- **Concurrency acceptance gap closed:** the PostgreSQL test now races two promotion calls for the same reviewed component alongside verification; both promotion calls must return the full allocation set, and the final ledger must contain complete reconciled rows with one consistent durable reference.
- **Next single implementation step:** close the canonical-ledger integration gap (Phase 3 Gates 1C/5). Canonical snapshot materialization/review/allocation/reconciliation services exist, but `live_fill_accounting_service` still verifies raw source-component rows and the legacy six-row source ledger. Audit the intended canonical snapshot path and implement/test a fail-closed end-to-end route from reviewed source rows (including combined/split transaction/IPFT) through canonical snapshot allocation/reconciliation into live-fill accounting. Do not silently drop or double-count extra source components; do not add generic quantity/notional allocation.
- **Remaining gates:** evidence-backed effective-dated tariff selection (Gate 2), approved per-fill rule wiring (Gate 3), invoice/source-backed GST/component acceptance (Gate 4), final adversarial/migration/restore review (Gate 6), and final exact-head docs/sign-off (Gate 7) remain open.
- **Upstox decisions:** no unused SDK runtime dependency; Agent Skill remains static-review-only and must not be executed or given live credentials. Brokerage calculator output is estimate-only; aggregate charge endpoints are not per-fill actual evidence. GST/IPFT/tariff candidates remain DRAFT until authentic applicable evidence and independent review support approval.
- **Safeguards:** original `tarunsharma2610-del/Tradepro` is out of scope and must remain untouched; PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. Do not merge PR #6 without explicit user approval.

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

# Upstox contract-note evidence and API cross-check — 23 October 2026

## Finding

Public Upstox documentation provides instructions to download a user's real contract note and authenticated APIs for trade history, brokerage calculation, and aggregate charges. The public documentation reviewed does not provide a genuine contract note belonging to this account, and we found no documented contract-note PDF download endpoint. Do not treat generated fixtures, sample JSON, or an API response as an authentic original contract note.

## Publicly shared examples reviewed

1. [Upstox contract note dated 12 March 2025 (third-party Scribd copy)](https://www.scribd.com/document/971660843/CW-T-3JCTYG-20250312-NSE-66319975-1). The indexed text shows contract-note header, trade rows, brokerage, IGST on brokerage, STT and net payable/receivable summary. It says trade-wise levies are available on request, so the displayed summary is not per-fill proof for all charges.
2. [Upstox contract note dated 21 May 2024 (third-party Scribd copy)](https://www.scribd.com/document/735902961/CW-T-842243-20240521-NSE-35749411). Useful as a second historical layout example.
3. [Quicko guide with an Upstox sample image](https://learn.quicko.com/download-contract-note-upstox-trader). Useful for field names/layout, but older and not a source for current rates.

These third-party copies purport to be Upstox-issued; authenticity has not been independently verified. They contain or may expose personal identifiers. Do not reproduce identifiers or commit raw copies. Use them only to review layout and guide synthetic fixtures; historical amounts are not current tariff evidence.

## Acceptance decision

**Completed for development scope:** public-format research and field/category review. A personal contract note is not required to continue Phase 3, and no new trade is required. Synthetic fixtures remain the repeatable automated test input.

**Still distinct and not claimed complete:** broker-origin authenticity verification, account-specific API reconciliation, and per-fill attribution of any charge shown only in aggregate. An aggregate total alone cannot prove per-fill allocations.

## Official sources

1. [Accessing and downloading the contract note (Upstox Help Center)](https://upstox.com/help-center/how-can-i-access-and-download-the-contract-note-248457/)
   - In the Upstox app: My Account → Reports → Miscellaneous reports → select the relevant filters → report type `CONTRACT` → Get Report → select and download the report.
   - Upstox says the contract note is emailed to the registered email address within 24 hours.
2. [Understanding the contract note (Upstox Help Center)](https://upstox.com/help-center/understanding-the-contract-note-248458/)
   - Describes the note as the legal record of the day's trades, with trade identifiers/timing, instruments, transaction details, and charges.
3. [Get Trade History API](https://upstox.com/developer/api-documentation/get-historical-trades/)
   - Authenticated `GET /v2/charges/historical-trades`; retrieves trade history for the last three financial years, with pagination. The response includes fields such as trade ID, date, quantity, price, transaction type, symbol, and segment.
4. [Get Trades Charges API](https://upstox.com/developer/api-documentation/get-trade-charges/)
   - Authenticated `GET /v2/trade/profit-loss/charges`; returns a charge breakdown for a selected segment/financial year, including brokerage, GST, STT, stamp duty, transaction charges, clearing, IPFT, SEBI turnover, and demat transaction charges where applicable.
5. [Brokerage Details API](https://upstox.com/developer/api-documentation/get-brokerage/)
   - Authenticated `GET /v2/charges/brokerage`; calculates an order's brokerage/charges for specified instrument, quantity, product, transaction type, and price.
6. [Upstox brokerage and charges](https://upstox.com/brokerage-charges/) and [brokerage calculator](https://upstox.com/calculator/brokerage-calculator/)
   - Public references for the published tariff and illustrative charge calculations. Tariffs/rates must be versioned by effective date and applied with the relevant segment/exchange/transaction rules.
7. [Upstox API overview and Swagger UI](https://upstox.com/developer/api-documentation/) and [API Swagger](https://api.upstox.com/v2/swagger-ui/index.html)
   - The reviewed API catalogue lists trade history, brokerage calculation, and P&L charge endpoints. We found no documented contract-note PDF endpoint in these public references during this review.

## Generated synthetic fixture

To avoid blocking implementation on a private document, the following explicitly synthetic fixtures were created in this repository:

- [Synthetic Upstox-style contract-note fixture (human-readable)](fixtures/SYNTHETIC_UPSTOX_CONTRACT_NOTE_FIXTURE.md)
- [Synthetic Upstox-style charge fixture (JSON)](fixtures/synthetic_upstox_contract_note_fixture.json)

These use invented trades and identifiers plus illustrative public-rate assumptions. They are suitable for parser, allocation, rounding, replay, and tampering tests only. They are **not issued by Upstox, not real contract notes, and not proof of a real trade or actual account charges**. The rates and rounding are a test fixture, not a production rate engine. Production calculations must use date-effective rules and should cross-check against the authenticated Upstox API where available.

## What this means for Tradepro Improved

- **A real note is not a prerequisite for continuing Phase 3 engineering.** Use synthetic fixtures for repeatable automated tests. Mark only real-document acceptance as pending until a genuine note is available.
- **API cross-checks are useful but not equivalent to the original note.** Trade History can reconcile executed trade identities and quantities. The P&L charges endpoint supplies a segment/financial-year charge breakdown; it is not a per-fill charge-allocation authority by itself.
- **Do not infer a charge allocation basis from an aggregate charge total.** Each component's basis must be justified by applicable rules, source evidence, or an explicitly documented reviewer decision. Do not automatically spread every charge by quantity or notional.
- **Preserve provenance.** When real evidence becomes available, retain the original downloaded bytes, compute and record SHA-256, record report date/segment and source page/row locators, reconcile the note's trade list and totals against authenticated API responses, and record mismatches. Keep the original immutable; corrections should be recorded as reviewed revisions.
- **Protect account access.** Never paste an Upstox password, PAN, OAuth access/refresh token, client secret, or session cookie into chat or commit it to GitHub. Use the app's secure OAuth flow and read-only endpoints for API validation.
- **No live trading is needed** for this acceptance step. Use a past trading day's note if/when available and read-only trade/charges endpoints. Keep broker write operations disabled.

## Acceptance steps when a real note becomes available

1. Obtain an authentic note through the user's Upstox account or registered email; no new trade is required if a suitable historical note exists.
2. Keep the original bytes and source metadata; redact unrelated identifiers if sharing a copy, but preserve the fields required for reconciliation.
3. Match note trades to Upstox Trade History API rows and compare charge summaries with the Charges API where date/segment scope matches.
4. Identify which components are actually reported per trade versus only aggregated. Do not claim fill-level verification for aggregate-only fields without a justified allocation policy.
5. Run acceptance tests against the real document and record the fingerprint and discrepancy report.

## Status

Public-format review is complete using the linked third-party examples; no personal note is required to proceed. The examples are not independently authenticated and are not copied into the repository. Synthetic fixtures are available for repeatable tests. Account-specific verification is optional future validation, not a Phase 3 development blocker. The synthetic fixtures are available for development tests. They do not prove authenticity of a real broker note or successful recovery of the user's real Oracle Free Cloud database. PR #6 remains draft/unmerged pending exact-head CI and final accounting/idempotency review; live broker writes remain disabled.


## 2026-10-24 — Resolver acceptance and CI checkpoint

- Backend workflow `40108183667` succeeded on prior head `8214430f562f6f425cfc1b9b6a6b3b547832b68a`. New resolver tests add exact broker/endpoint/schema/field/scope matching and non-finite-number rejection; newer commits still require CI.
- Mapping identity fixtures use immutable dataclass replacement. Intended-use semantics remain explicit; missing/null/invalid values remain unusable and retain provenance; numeric zero remains distinct.
- Accounting acceptance includes replay/conflict, ledger reconciliation, lock order, rollback, reviewer authority and PostgreSQL verification/promotion race coverage. Re-check exact test and workflow status before claiming complete. CI does not establish production tariff correctness or broker-origin authenticity.
- Safety gates unchanged: PR #6 draft/unmerged; live broker order submission and automatic quantity/notional allocation disabled; production Upstox mappings/tariffs unapproved. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Resolver field-identity guard added; CI pending

- Resolver now verifies that the payload field matches the terminal field in the approved mapping path. Implementation `77aa77aec37dc535c3e427ca3f88c2ccb5e75ed8`; regression test `5c5482c7f7fa623707698f64b6a061351e5e5b87`. CI is pending for these and subsequent documentation commits.
- The field-identity guard is a code correctness safeguard, not approval of production Upstox field semantics or tariffs. Existing live-fill tests cover lock order, replay idempotency and rollback; genuine concurrent verification-versus-promotion coverage still needs confirmation.
- PR #6 remains draft/unmerged. Live order submission and automatic quantity/notional allocation remain disabled. Work only in `tradepro-improved`; original `Tradepro` remains untouched.


## 2026-10-24 — Latest resolver CI and PostgreSQL concurrency suite verified

- Backend workflow [#40109041654](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40109041654) passed on head `ed346e823cbfae8448fae0134c4ff864bfcc60ac`: **872 passed, 1 warning**; broker-write boundary guard passed.
- Dedicated PostgreSQL concurrency tests cover competing fill sets, source verification vs allocation promotion, and live-fill promotion vs ledger verification. The successful test summary has no skipped tests, confirming the collected suite ran in CI's synthetic database environment.
- This is not approval of production Upstox tariff/field mappings. PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled; original `Tradepro` remains out of scope.


## 2026-10-24 — Official tariff/API source audit

- Upstox's `GET /v2/trade/profit-loss/charges` accepts segment, financial year and optional date bounds; documented output is aggregate `charges_breakdown`, not a per-fill schema. Example `charges.ipft` is null. Treat it as aggregate reconciliation evidence only, and never coerce null to zero. https://upstox.com/developer/api-documentation/get-trade-charges/
- NSE circular NSE/FA/73061 dated 27-Feb-2026 applies from 1-Mar-2026: combined member outflow ₹307/crore cash, ₹183/crore equity futures and ₹3,553/crore equity-options premium; included IPFT contribution is ₹0.01/crore each side. Use effective-dated rate versioning and guard against double counting. This circular does not establish Upstox-specific contract-note JSON field semantics. https://nsearchives.nseindia.com/content/circulars/FA73061.pdf
- Upstox's public charges page shows newer effective-date summary values alongside historical tables and lists a STT/CTT change effective 1-Apr-2026. Use the matching date/scope and prefer official exchange/statutory notices for rate authority. https://upstox.com/brokerage-charges/
- Acceptance: aggregate API response, null IPFT, stale tariff, combined-vs-split IPFT and effective-date boundary must fail closed when actual per-fill evidence is required. Production mappings and tariffs remain DRAFT/non-selectable.
- Latest prior implementation head `ee1b2a74d2a9f6141b9afbb6e06562b5cf263a9b` passed workflow #40110597753; rerun CI on the resulting documentation head.
- PR #6 remains draft/unmerged; live order submission and automatic quantity/notional allocation remain disabled; original `Tradepro` remains untouched.


## 2026-10-24 — Upstox brokerage calculator restricted to estimates; CI pending

- Official Upstox `GET /v2/charges/brokerage` takes proposed instrument, quantity, product, transaction type and price, returning a charge calculation; this is not proof of final booked per-fill charges. https://upstox.com/developer/api-documentation/get-brokerage/
- Resolver now blocks `/v2/charges/brokerage` from `PER_FILL_ACTUAL` and actual `AGGREGATE_SUMMARY` use even if a mapping is misleadingly labelled. Existing guard still blocks `/v2/trade/profit-loss/charges` from per-fill actual use. New regression tests cover both misuse cases.
- Implementation `3486d854dae2451858a858cb627602aca7338969`; tests `6c92101a1890a0f4d761e86ed3db047a269fd10d`. Prior head `6cc8b58f635fcb4f1b1cb3e5997099d074800a28` passed workflow #40111501429. CI for the new commits must be verified.
- Production mappings/tariffs remain unapproved; null is not zero; automatic quantity/notional allocation and live broker order submission remain disabled. PR #6 stays draft/unmerged. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Phase 3 checkpoint — official GST/IPFT source cross-check (25 October 2026)

- Upstox's current public charges schedule lists the March 2026 transaction-charge schedule, April 2026 STT schedule, product-specific GST bases, and says IPFT is combined with transaction charges while also listing IPFT. The public wording does not prove whether a specific API `transaction` field is transaction-only or combined with IPFT.
- NSE's official STT table confirms effective 1 April 2026: options sale 0.15% on premium, exercised option 0.15% on intrinsic value, and futures sale 0.05%. CBIC's stock-broking FAQ says statutory recoveries are outside GST value only when pure-agent conditions are met; otherwise Section 15/Rule 27 valuation applies.
- No API field mapping or production tariff was approved. Do not double-count IPFT or infer actual per-fill charges from proposed-order/aggregate APIs. Keep tariff candidates DRAFT/non-selectable and preserve fail-closed reviewed component allocation.
- Exact-head CI for previous head `7d4f2918b534ef9b4c3d32e7df22b754b21e6c8f` passed (run [40182196510](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40182196510)); the new documentation head needs fresh CI. PAPER mandatory; live broker writes disabled; PR #6 remains draft/unmerged; original `Tradepro` untouched.
- Sources: https://upstox.com/brokerage-charges/ ; https://www.nseindia.com/static/products-services/equity-derivatives-securities-transaction-tax ; https://cbic-gst.gov.in/sectoral-faq.html


## Resolver endpoint-alias guard — 25 October 2026

- Aggregate charges and brokerage calculator endpoints remain disallowed as per-fill actual evidence even if the mapping registry contains a misleadingly labelled approved row.
- Guard checks canonicalize broker name and endpoint path for safety restrictions, covering trailing slashes, query strings, absolute URLs and broker-name casing. Registry selection remains exact and version/date/scope-bound.
- Regression tests cover both restricted endpoints. This does not resolve transaction/IPFT semantics or establish contract-note actual charges; no production mapping is approved.


## Phase 3 checkpoint — verified source-component canonicalization adapter (25 October 2026)

- Added `backend/app/services/broker_charge_verified_component_canonicalization.py` and focused tests in `backend/tests/test_broker_charge_verified_component_canonicalization.py`.
- The adapter accepts only persisted `VERIFIED` rows tied to the expected evidence ID and matching SHA-256, with INR currency, reviewer identity/timestamp, unique row IDs, and source locators. It delegates six-component and combined/split transaction/IPFT rules to the existing canonicalization contract and returns source-record provenance.
- Output remains `accounting_approved=false`. This is a validation adapter, not yet the transaction-owning persistence/promotion integration. It does not prove broker-origin authenticity, establish GST/tariff applicability, or enable automatic allocation.
- Implementation commit `d3a2fc076a4309f23edbb14b0a47ba41fec0b557`; regression-test commit `c8e3748f12c5674b1b77e76ff8fcf9b8f3dc68a6`. Exact-head CI is not yet verified; observed Backend workflow `40192323693` was in progress on the earlier implementation commit and does not validate the added tests. Do not call the latest head green.
- Next gate: integrate this adapter into the existing locked source-component verification/allocation-promotion path; persist canonical totals and source-row associations atomically; test duplicate/replay/conflict, rollback, partial fill sets, and PostgreSQL concurrency.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion disabled; production tariff/GST/IPFT interpretations unapproved.


## CI correction — verified source-component canonicalization adapter (25 October 2026)

- Backend workflow [#40192336466](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40192336466) passed on code/test commit `c8e3748f12c5674b1b77e76ff8fcf9b8f3dc68a6`; Backend pytest and the synthetic PostgreSQL/document-volume restore drill succeeded.
- Subsequent commits only synchronize documentation; no application code changed after the tested code/test head. No workflow run is associated with the latest docs-only head, so the code/test head is green, but the latest docs commit does not have separately verified exact-head CI.


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

- Added `BrokerChargeCanonicalSourceLink` and migration `202610250025_normalize_canonical_source_links.py`. The relational database now explicitly stores each canonical snapshot-to-source-row edge, including source order, with foreign keys and uniqueness constraints. Migration backfills solely from the snapshot's persisted ordered source-ID manifest and fails on malformed/duplicate manifests rather than inferring membership.
- Snapshot materialization persists normalized edges; idempotent replay and independent review compare the relational links with the immutable manifest. Review fails closed if any link is missing, reordered or inconsistent. This makes split transaction/IPFT (two raw source rows → one canonical exchange-charge snapshot → linked per-fill allocations) explicit and auditable.
- Previous branch head `4dbaf27fae124d11935c271f2f4cdec44015dbaa` passed Backend workflow [#40196030459](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40196030459). Normalized-link change `d1153a0f0751339f3ca82fc062701db0141d4749` is pending fresh CI verification.
- Next: verify the new migration on SQLite/PostgreSQL 16 including downgrade/re-upgrade and all tests; then bind accounting promotion/reconciliation to normalized source links and canonical snapshot fingerprints.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion disabled.


## Phase 3 — normalized source links and canonical reconciliation gate (25 October 2026)

- Normalized source-link migration passed Backend workflow [#40196529023](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40196529023), including pytest, broker-write boundary, SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade and synthetic restore drill.
- Added `broker_charge_canonical_allocation_reconciliation_service.py` to validate the independently verified snapshot, source fingerprint and normalized source links, fill manifest, deterministic paise amounts, INR/method/basis and exact total before atomic promotion. Reconciliation is idempotent and its durable reference binds snapshot ID, source fingerprint, fill-set hash and allocation method; caller owns commit/rollback.
- Added split transaction/IPFT source-link, promotion/replay and tamper-blocking tests. Commit `621ce7cd289057a419be5eeff0262e158b18c001` Backend workflow [#40196784435](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40196784435) was in progress at the checkpoint; do not call the new path green before completion.
- Next: resolve exact-head CI failures, then cover conflicting evidence, transaction rollback and PostgreSQL concurrent promotion.
- Safety unchanged: Improved repo only; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; no live broker writes enabled.


## CI result update — canonical reconciliation gate (25 October 2026)

- Backend workflow [#40196784435](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40196784435) completed successfully for code/test commit `621ce7cd289057a419be5eeff0262e158b18c001`. Pytest, broker-write boundary enforcement, SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade and synthetic PostgreSQL/document-volume restore all passed.
- This green result verifies the normalized source-link schema and canonical allocation reconciliation tests at that code/test head. Later docs-only commits need exact-head CI verification if triggered.
- Next: explicit rollback/conflicting-set and PostgreSQL concurrent-promotion coverage, then fresh exact-head CI. Live broker writes remain disabled; PR #6 stays draft/unmerged and PAPER remains mandatory.
