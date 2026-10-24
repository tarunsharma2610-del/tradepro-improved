# Phase 3 latest-head CI checkpoint — 24 October 2026

## Repository and safety
- Repository: `tarunsharma2610-del/tradepro-improved`.
- PR #6: `Phase 3: add durable per-fill charge allocation ledger`; keep draft and unmerged.
- Original `tarunsharma2610-del/Tradepro` is out of scope and must remain untouched.
- Live broker order submission remains disabled. This checkpoint does not authorize live trading or automatic accounting promotion.

## Exact-head CI verification
- PR branch: `phase3/durable-per-fill-charge-allocation`.
- Head checked: `e5fff2831a40fa591b697be29748f099d24aa464`.
- GitHub Actions backend workflow run: [40088597367](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40088597367).
- Result: completed successfully.
- Completed steps: backend pytest, broker-write boundary guard, SQLite Alembic upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and evidence-artifact retention.
- The workflow result validates the exact head above. The restore drill is synthetic and does not establish recovery of real Oracle Cloud data or broker-origin authenticity.

## Phase 3 implementation/review status
The PR describes durable per-fill allocations, evidence/component provenance, reviewer-approved allocation weights, source-total and per-fill verification, replay/conflict protection, and transactional promotion with a savepoint. These controls still require accounting/idempotency acceptance review; CI passing alone does not establish financial correctness or authenticity of uploaded documents.

## Next work
1. Review the latest diff for financial-accounting invariants and authorization boundaries, especially reviewer role revocation, source/fill set binding, duplicate replay, transaction rollback, and partial-fill/crash recovery.
2. Verify the new tariff-estimate snapshot and aggregate variance path remains estimate-only and cannot promote estimates as actual charges.
3. Record any findings and regression tests in the project documentation, then verify CI on the resulting exact HEAD.
4. Keep PR #6 draft/unmerged pending acceptance review and explicit approval.



## 2026-10-24 — Resolver acceptance and CI checkpoint

- Backend workflow `40108183667` succeeded on prior head `8214430f562f6f425cfc1b9b6a6b3b547832b68a`. New resolver tests add exact broker/endpoint/schema/field/scope matching and non-finite-number rejection; newer commits still require CI.
- Mapping identity fixtures use immutable dataclass replacement. Intended-use semantics remain explicit; missing/null/invalid values remain unusable and retain provenance; numeric zero remains distinct.
- Accounting acceptance includes replay/conflict, ledger reconciliation, lock order, rollback, reviewer authority and PostgreSQL verification/promotion race coverage. Re-check exact test and workflow status before claiming complete. CI does not establish production tariff correctness or broker-origin authenticity.
- Safety gates unchanged: PR #6 draft/unmerged; live broker order submission and automatic quantity/notional allocation disabled; production Upstox mappings/tariffs unapproved. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.
