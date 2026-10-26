## Authoritative Phase 3 checkpoint — 26 October 2026

- Repository: `tarunsharma2610-del/tradepro-improved` only; branch `phase3/durable-per-fill-charge-allocation`; implementation head `a3f3473eb8f57b4fb6b83c95ddb18d8b3bd22e90`. Original `Tradepro` remains out of scope.
- Exact-head Backend CI: [run #40292395932 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40292395932). Backend tests, broker-write boundary, SQLite/PostgreSQL migration round-trips, and synthetic restore drill passed; synthetic restore is not proof of actual Oracle recovery.
- GST validation: supported Indian brokerage/market-charge estimate helper now accepts only 18% GST; tests reject 0%, 5%, 100%, and 100.01%. Taxable component names still require explicit approval/evidence. This does not determine the legal taxable base or make estimates actual booked charges.
- Brokerage order-level cap is applied once before deterministic paise-exact allocation by reviewed fill weights.
- Phase 3 remains IN PROGRESS: effective-dated tariff review; component-specific per-fill allocation acceptance; invoice/source-backed GST/IPFT and product/segment evidence; adversarial/migration/recovery review; final exact-head sign-off. Do not redo canonical live-fill integration.
- Public tariff data and calculator/aggregate APIs are estimate/research evidence, not account-specific actual per-fill evidence. Do not infer approval of GST base composition, stamp duty, unsupported mappings, or missing IPFT values.
- PAPER mandatory; live broker order writes, automatic live-fill promotion and automatic scheduling disabled. PR #6 remains open/draft/unmerged unless explicitly approved. Defer AI/open-source adaptations until Phase 3 acceptance. This documentation commit needs its own CI.

---

# Upstox public tariff review decision — 26 October 2026

## Decision

**Approve a narrow set of 18 effective-dated rules for public-schedule estimates only. Do not approve them as actual-charge evidence or as account-specific tariff rules.** The underlying candidate registry remains DRAFT; a separate explicit allowlist produces APPROVED copies only when every reviewed identity, source hash, retrieval date and source URL still matches.

## Evidence reviewed

- Official Upstox brokerage/charges page: https://upstox.com/brokerage-charges/
- Official NSE STT schedule: https://www.nseindia.com/static/products-services/equity-derivatives-securities-transaction-tax
- NSE Finance & Accounts Circular NSE/FA/73061 dated 27 February 2026, effective 1 March 2026: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf
- Repository excerpt snapshot: `docs/source_snapshots/UPSTOX_CHARGES_2026-10-24.md`
- Canonical source-payload SHA-256: `c59f7e940fde6b0d94ca1189766f16e5601c117d4a8c2bcd2415da0ecd6db420`

The NSE circular confirms combined outflow of ₹307/crore for cash, ₹183/crore for equity futures and ₹3,553/crore for equity options from 1 March 2026. The revised split is transaction charge plus ₹0.01/crore IPFT; do not add legacy ₹10/₹50-per-crore IPFT rates on top. Upstox's public page records the 1 April 2026 STT changes: futures sell-side 0.05%, options sell-side premium 0.15%, and exercised options 0.15% on intrinsic value on the purchaser side. Earlier effective windows remain separately represented.

## Approved estimate-only scope

The allowlist in `backend/app/services/upstox_public_estimate_rules.py` approves exactly 18 STT and exchange-charge identities, including their effective dates and source hash. `build_upstox_public_schedule_estimate_snapshot` labels outputs `PUBLIC_SCHEDULE_ESTIMATE_ONLY`. Rules use exact scope and effective dates; there are no wildcard fallbacks. The source candidate registry stays DRAFT and changed identities fail closed until review updates the allowlist and tests.

## Explicitly not approved

- Account-specific brokerage plan, API-order discounts or future brokerage changes without a supported effective date.
- GST taxable-base composition by product/invoice, stamp duty, SEBI turnover, DP/demat, clearing/other charges, and charge-component attribution.
- BSE cash scrip-group rates, BSE futures zero-charge assumptions, MCX commodities and currency derivatives.
- Any conversion of a brokerage calculator result or aggregate charge API response into per-fill actual evidence.
- Automatic quantity/notional allocation, guessed zero values, or live-order enablement.

The current public Upstox calculator page can display older STT/transaction values than the current official charges page and the NSE circular. Use it only as an estimate cross-check, not as the effective-dated tariff source of record.

## Actual-charge boundary

Actual per-fill accounting remains exclusively based on a reviewed contract-note evidence record, independently reviewed source components, canonical mapping snapshots, exact fill manifests/weights, and durable reconciled allocations. This estimate registry is not imported by `LiveFillAccountingService` and cannot promote charges.

## Re-review triggers

Re-review if the official pricing page changes, the source payload hash changes, a new product/segment is added, an effective date is revised, a BSE scrip group or MCX/currency rule is proposed, or the account's pricing plan is known to differ from the public schedule.


## Authoritative checkpoint — 26 October 2026 (documentation CI verified)

- Repository: `tarunsharma2610-del/tradepro-improved`; branch: `phase3/durable-per-fill-charge-allocation`.
- Latest implementation commit: `ac7d27f2c9922925483b5b906c484c0d5a4e3f53`; exact-head Backend CI [#40287765745 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40287765745).
- Documentation synchronization commit: `f90573d653c7103bf9cfdb1f867da97b176d3240`; its exact-head Backend CI [#40289107666 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40289107666). Backend tests, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore/evidence retention passed. Synthetic restore is not proof of actual Oracle Cloud recovery.
- Approved public Upstox STT/exchange rules are estimate-only. Account-specific actual charges, GST taxable-base composition, stamp duty, SEBI/DP/demat/other charges, unsupported exchange/segment mappings, and per-fill actual evidence remain unapproved. Candidate tariff entries remain DRAFT unless separately allowlisted and reviewed.
- Phase 3 remains in progress. Next gates: independently reviewed tariff applicability; component-specific per-fill allocation rules; invoice/source-backed GST/IPFT and product/segment evidence; final adversarial, migration and recovery review; exact-head acceptance sign-off. Do not repeat canonical live-fill integration.
- Safety: PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. PR #6 stays open/draft/unmerged without explicit user approval. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.
- This documentation commit’s CI is green. Continue only from this checkpoint and verify CI for every subsequent implementation/checkpoint commit. Historical entries do not supersede this checkpoint.
