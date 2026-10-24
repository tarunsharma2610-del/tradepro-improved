# Phase 3 reviewer-authority fix and exact-head CI — 24 October 2026

## Scope and safety
- Repository: `tarunsharma2610-del/tradepro-improved`.
- PR #6 remains open, draft, and unmerged.
- Live broker order submission remains disabled.
- Original `tarunsharma2610-del/Tradepro` is out of scope and must remain untouched.

## Reviewer-authority follow-up
- Code commit: [`f0499bc50f513369ff166239e3a1d588f008ebbd`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/f0499bc50f513369ff166239e3a1d588f008ebbd).
- Regression test commit: [`c707d9ad53b4906bea9a376a4fcf9a8f74629a50`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/c707d9ad53b4906bea9a376a4fcf9a8f74629a50).
- Live-fill accounting now revalidates that the recorded source reviewer is an active platform administrator at promotion time. The reviewer row is locked after evidence/component/allocation locks to preserve lock order.
- Regression tests cover reviewer administrator-role revocation and account deactivation; rejected promotion must not create a live execution or live position and must leave the paper position unchanged.

## Exact-head CI
- Backend workflow run [`40089715163`](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40089715163) for the regression-test commit completed successfully.
- Verified successful steps: dependency installation, backend pytest, broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and evidence-artifact retention.
- The separate code-commit run [`40089713242`](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40089713242) also completed successfully.
- The workflow jobs passed; this does not independently prove production financial correctness, authentic broker issuance of uploaded documents, or recovery of a real Oracle Cloud deployment.

## Remaining acceptance gates
1. Explicitly establish fault-injection rollback coverage at each important accounting write/savepoint boundary.
2. Add/confirm a full concurrent live-fill promotion race test, separate from source-verification-versus-allocation-promotion concurrency.
3. Keep the reviewer-authority policy documented: current active-admin status is required at promotion time.
4. Synchronize project progress/handover/roadmap records with this follow-up and rerun CI on the final documentation head.
5. Do not merge PR #6 until accounting acceptance review is explicitly closed.

## Decision
The reviewer-authority code and regression tests pass CI. Phase 3 accounting acceptance remains open because the remaining rollback and concurrent live-fill promotion gates are not yet closed.


## 2026-10-24 — Resolver acceptance and CI checkpoint

- Backend workflow `40108183667` succeeded on prior head `8214430f562f6f425cfc1b9b6a6b3b547832b68a`. New resolver tests add exact broker/endpoint/schema/field/scope matching and non-finite-number rejection; newer commits still require CI.
- Mapping identity fixtures use immutable dataclass replacement. Intended-use semantics remain explicit; missing/null/invalid values remain unusable and retain provenance; numeric zero remains distinct.
- Accounting acceptance includes replay/conflict, ledger reconciliation, lock order, rollback, reviewer authority and PostgreSQL verification/promotion race coverage. Re-check exact test and workflow status before claiming complete. CI does not establish production tariff correctness or broker-origin authenticity.
- Safety gates unchanged: PR #6 draft/unmerged; live broker order submission and automatic quantity/notional allocation disabled; production Upstox mappings/tariffs unapproved. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Resolver field-identity guard added; CI pending

- Resolver now checks that the payload field name matches the terminal field in the selected approved mapping path. This closes a semantic mismatch where a caller could select `charges.ipft` but normalize another payload field.
- Implementation commit: `77aa77aec37dc535c3e427ca3f88c2ccb5e75ed8`; regression test commit: `5c5482c7f7fa623707698f64b6a061351e5e5b87`. CI for the latest commits is pending; previous green runs apply only to earlier heads.
- Existing accounting tests cover lock ordering, replay idempotency, conflicting evidence and rollback. A genuine concurrent two-session verification-versus-promotion race is not demonstrated in the inspected live-fill test file; locate/verify other integration coverage before marking complete.
- PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled; production Upstox mappings/tariffs remain unapproved. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.
