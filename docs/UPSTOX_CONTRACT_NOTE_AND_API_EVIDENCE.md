# Upstox contract-note evidence and API cross-check — 23 October 2026

## Finding

Public Upstox documentation provides instructions to download a user's real contract note and authenticated APIs for trade history and aggregate charges. The public documentation does **not** provide a genuine contract note belonging to this account, and the documented API surface reviewed here does not identify a contract-note PDF download endpoint. Do not treat sample JSON or an API response as an authentic original contract note.

## Official sources

1. [Accessing and downloading the contract note (Upstox Help Center)](https://upstox.com/help-center/how-can-i-access-and-download-the-contract-note-248457/)
   - In the Upstox app: My Account → Reports → Miscellaneous reports → select the relevant filters → report type `CONTRACT` → Get Report → select and download the report.
   - Upstox says the contract note is emailed to the registered email address within 24 hours.
2. [Understanding the contract note (Upstox Help Center)](https://upstox.com/help-center/understanding-the-contract-note-248458/)
   - Describes the note as the legal record of trades for the day, with trade identifiers/timing, instruments, transaction details, and charges.
3. [Get Trade History API](https://upstox.com/developer/api-documentation/get-historical-trades/)
   - Authenticated `GET /v2/charges/historical-trades`; retrieves trade history for the last three financial years, with pagination. The response includes fields such as trade ID, date, quantity, price, transaction type, symbol, and segment.
4. [Get Trades Charges API](https://upstox.com/developer/api-documentation/get-trade-charges/)
   - Authenticated `GET /v2/trade/profit-loss/charges`; returns a charge breakdown for a selected segment/financial year, including brokerage, GST, STT, stamp duty, transaction charges, clearing, IPFT, SEBI turnover, and demat transaction charges where applicable.
5. [Upstox API overview and Swagger UI](https://upstox.com/developer/api-documentation/) and [API Swagger](https://api.upstox.com/v2/swagger-ui/index.html)
   - The reviewed API catalogue lists trade history and P&L charge endpoints. We found no documented contract-note PDF endpoint in these public references during this review.

## What this means for Tradepro Improved

- **Real-document acceptance remains pending.** We need a contract note downloaded from the authenticated Upstox account or received through its registered email. Public web pages cannot supply that account-specific artifact.
- **API cross-checks are useful but not equivalent to the original note.** Trade History can reconcile executed trade identities and quantities. The P&L charges endpoint supplies a segment/financial-year charge breakdown; it is not a per-fill charge-allocation authority by itself.
- **Do not infer a charge allocation basis from the existence of an aggregate charge total.** Each component's basis must be justified by the source note, applicable charge calculation/rules, or an explicitly documented reviewer decision. Do not automatically spread every charge by quantity or notional.
- **Preserve provenance.** When real evidence becomes available, retain the original downloaded bytes, compute and record SHA-256, record report date/segment and source page/row locators, reconcile the note's trade list and totals against authenticated API responses, and record any mismatches. Keep the original immutable; corrections should be recorded as reviewed revisions.
- **Protect account access.** Never paste an Upstox password, PAN, OAuth access/refresh token, client secret, or session cookie into chat or commit it to GitHub. API validation should use the app's secure OAuth flow and read-only endpoints where possible.
- **No live trading needed for this acceptance step.** Use an existing past trading day's note and read-only trade/charges endpoints. Keep broker write operations disabled.

## Exact next acceptance steps

1. User downloads one genuine contract note from Upstox (prefer a day with a small number of fills and visible charge rows).
2. Store it securely and upload it to the project only when ready; redact unrelated personal identifiers if desired, but preserve trade identifiers, date, instrument, quantities, amounts, charge lines, and totals needed for reconciliation.
3. Match note trades to Upstox Trade History API rows; match the note's charge summary against the Charges API where the same date/segment scope is available.
4. Identify which charge components are genuinely source-reported per trade versus only aggregated. Do not claim fill-level verification for aggregate-only fields without a justified allocation policy.
5. Run acceptance tests against the actual document, record the evidence fingerprint and discrepancy report, then complete the Phase 3 merge review.

## Status

This is public-documentation research and an implementation plan, not proof that a real note has been obtained or validated. The synthetic restore drill is also not proof of restoring the user's real Oracle Free Cloud database. PR #6 remains draft/unmerged, and live broker writes remain disabled.
