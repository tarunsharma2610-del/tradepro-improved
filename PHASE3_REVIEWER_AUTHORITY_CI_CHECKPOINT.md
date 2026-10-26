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


## 2026-10-24 — Latest resolver CI verified; PostgreSQL race coverage located

- Latest PR head `ed346e823cbfae8448fae0134c4ff864bfcc60ac` passed Backend workflow [#40109041654](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40109041654). This verifies the field-identity guard and regression test at that head.
- Located PostgreSQL-only integration tests in `backend/tests/test_broker_charge_allocation_postgres_concurrency.py`, including concurrent source verification vs allocation promotion and live-fill promotion vs ledger verification, as well as conflicting fill-set and tariff estimate/variance persistence races.
- These tests require `TEST_POSTGRES_URL`. Verify the PostgreSQL workflow actually ran these tests rather than skipped them before treating concurrency acceptance as complete.
- PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled; production Upstox mappings/tariffs remain unapproved. Work only in `tradepro-improved`; original `Tradepro` remains untouched.


## 2026-10-24 — Upstox brokerage calculator restricted to estimates; CI pending

- Official Upstox `GET /v2/charges/brokerage` calculates charges from proposed order inputs; it is not proof of final booked per-fill charges. https://upstox.com/developer/api-documentation/get-brokerage/
- Resolver blocks this endpoint from `PER_FILL_ACTUAL` and actual `AGGREGATE_SUMMARY` use, even if a mapping is misleadingly labelled. `/v2/trade/profit-loss/charges` remains aggregate-only for per-fill purposes. Regression tests cover both mislabelled cases.
- Implementation `3486d854dae2451858a858cb627602aca7338969`; tests `6c92101a1890a0f4d761e86ed3db047a269fd10d`. The prior head passed workflow #40111501429; latest implementation/test CI must be verified.
- Production mappings/tariffs unapproved; null is not zero; automatic quantity/notional allocation and live order submission disabled. PR #6 draft/unmerged. Only `tradepro-improved` is in scope; original `Tradepro` untouched.


## Authoritative exact-head checkpoint — 26 October 2026

- Repository: `tarunsharma2610-del/tradepro-improved`; branch: `phase3/durable-per-fill-charge-allocation`; verified implementation commit: `ac7d27f2c9922925483b5b906c484c0d5a4e3f53`.
- Backend CI [run #40287765745](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40287765745) passed on this exact commit. Backend pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade, and synthetic PostgreSQL/document-volume restore/evidence retention succeeded. Synthetic restore is not proof of actual Oracle Cloud recovery.
- Latest change approves identified effective-dated public Upstox STT/exchange-rate rules for **estimate-only** use. It does not approve account-specific actual charges, GST taxable-base composition, stamp duty, SEBI/DP/demat/other charges, unsupported exchange/segment mappings, or per-fill actual evidence. Candidate tariff entries remain DRAFT unless separately allowlisted/reviewed.
- Phase 3 remains in progress. Next gates: independently reviewed effective-dated tariff applicability and component-specific per-fill allocation acceptance; invoice/source-backed GST/IPFT/product evidence; final adversarial/migration/recovery review; exact-head sign-off. Do not repeat canonical live-fill integration.
- Safety unchanged: PAPER mode mandatory; live broker order writes, automatic live-fill promotion and automatic scheduling remain disabled; PR #6 remains open/draft/unmerged absent explicit user approval; original `Tradepro` is out of scope.
- Documentation sync must pass CI on its own resulting commit before further implementation. Historical entries remain historical.
