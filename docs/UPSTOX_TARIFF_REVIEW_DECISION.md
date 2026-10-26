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


## Authoritative exact-head checkpoint — 26 October 2026

- Repository: `tarunsharma2610-del/tradepro-improved`; branch: `phase3/durable-per-fill-charge-allocation`; verified implementation commit: `ac7d27f2c9922925483b5b906c484c0d5a4e3f53`.
- Backend CI [run #40287765745](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40287765745) passed on this exact commit. Backend pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade, and synthetic PostgreSQL/document-volume restore/evidence retention succeeded. Synthetic restore is not proof of actual Oracle Cloud recovery.
- Latest change approves identified effective-dated public Upstox STT/exchange-rate rules for **estimate-only** use. It does not approve account-specific actual charges, GST taxable-base composition, stamp duty, SEBI/DP/demat/other charges, unsupported exchange/segment mappings, or per-fill actual evidence. Candidate tariff entries remain DRAFT unless separately allowlisted/reviewed.
- Phase 3 remains in progress. Next gates: independently reviewed effective-dated tariff applicability and component-specific per-fill allocation acceptance; invoice/source-backed GST/IPFT/product evidence; final adversarial/migration/recovery review; exact-head sign-off. Do not repeat canonical live-fill integration.
- Safety unchanged: PAPER mode mandatory; live broker order writes, automatic live-fill promotion and automatic scheduling remain disabled; PR #6 remains open/draft/unmerged absent explicit user approval; original `Tradepro` is out of scope.
- Documentation sync must pass CI on its own resulting commit before further implementation. Historical entries remain historical.
