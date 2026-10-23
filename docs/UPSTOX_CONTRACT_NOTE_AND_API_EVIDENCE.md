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
