# Changelog

Changes that materially affect safety, accounting, integrations, or acceptance gates are recorded here.

## 2026-10-24 — Phase 3 accounting acceptance and Upstox source register

- Added `UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md` to separate broker estimates, realized charge evidence, and effective-dated tariff rules.
- Recorded the official Upstox Brokerage Details API and Profit and Loss on Trades API as relevant integration/evidence sources, with strict limits on what each source proves.
- Kept all tariff candidates DRAFT/non-selectable until authoritative source documents, effective dates, applicability, calculation bases, rounding and independent review are recorded.
- Verified the variance rollback regression fix at code commit `5e036d7fcc1f5f439d4054700366d284d7b78061`: Backend CI #40096380843 passed 793 tests with 1 warning; broker-write guard, SQLite/PostgreSQL 16 migration checks and synthetic restore drill passed.
- Latest documentation-only commits have not yet received a fresh exact-head CI result. PR #6 remains draft/unmerged. Live broker order submission remains disabled.
- Scope: `tarunsharma2610-del/tradepro-improved` only. Original `tarunsharma2610-del/Tradepro` remains out of scope.
