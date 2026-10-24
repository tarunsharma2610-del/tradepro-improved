# Phase 3 accounting acceptance coverage — 24 October 2026

## Latest documentation-head CI
- Commit: `02061f46bde64c2fd692a86b1621ad2c1a189141`.
- Run: [40088958619](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40088958619) — **success**.
- Backend pytest, broker-write boundary guard, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic restore drill, and evidence retention all completed successfully.
- CI result is tied to the above commit; this new coverage note itself triggers a newer run and must not be called green until verified.

## Coverage confirmed by test inspection
- Rejects estimated, aggregate, unsupported, malformed, negative, and paise-overprecision charge inputs for live accounting.
- Blocks missing or non-reconciled component allocations and caller amounts that disagree with the ledger.
- Requires persisted reviewed contract-note evidence for new promotions.
- Protects exact replay and rejects conflicting source identity or charge evidence.
- Tests ambiguous/ealier trade timestamps and out-of-order promotion.
- Tests partial fills on cancelled orders, quantity boundaries, staged-fill completeness, and cumulative fill limits.
- PostgreSQL-only concurrency test races source verification against allocation promotion and asserts a reconciled final ledger without errors.

## Residual acceptance gaps / limits
- The PostgreSQL race test is for component verification vs allocation promotion; it is not a full concurrent live-fill accounting promotion race test.
- Test inspection did not establish fault injection after every individual accounting write/savepoint boundary. Treat comprehensive rollback-on-each-failure-point as still requiring explicit confirmation.
- CI's synthetic restore drill is not a real Oracle Cloud restore exercise.
- No CI/test result proves uploaded contract notes are authentic broker-issued documents; source hashes prove byte integrity after intake, not issuer authenticity.
- Reviewer-role revocation policy needs an explicit product/security decision: current review validates persisted reviewer identity and timestamp; it does not re-evaluate whether the reviewer is still an administrator at the later accounting-promotion time.

## Next action
Inspect the remaining accounting tests for cumulative fill and failure-injection coverage, then add regression tests only where a specific gap is confirmed. Keep PR #6 draft/unmerged, live broker order submission disabled, and all work confined to `tarunsharma2610-del/tradepro-improved`.
