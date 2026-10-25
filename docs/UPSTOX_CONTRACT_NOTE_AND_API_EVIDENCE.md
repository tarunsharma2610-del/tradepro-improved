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
