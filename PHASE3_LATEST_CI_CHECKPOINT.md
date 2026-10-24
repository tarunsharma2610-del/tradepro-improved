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


## 2026-10-24 — Official tariff/API source audit

- The documented Upstox charges endpoint returns segment/financial-year/date-range aggregate breakdowns, not documented per-fill charge evidence; its example has `ipft: null`. Null remains distinct from zero and aggregate data cannot satisfy actual per-fill acceptance. https://upstox.com/developer/api-documentation/get-trade-charges/
- NSE/FA/73061 (27-Feb-2026; effective 1-Mar-2026) states combined outflow ₹307/crore cash, ₹183/crore equity futures and ₹3,553/crore equity-option premium, including ₹0.01/crore IPFT each side. Do not add IPFT a second time to those combined rates. https://nsearchives.nseindia.com/content/circulars/FA73061.pdf
- Upstox public pricing tables contain historical and newer effective-date values, including STT/CTT effective 1-Apr-2026. Tariff acceptance must bind broker, exchange, segment/product, basis, side and effective date; unresolved scopes remain blocked. https://upstox.com/brokerage-charges/
- These source findings do not approve production mappings. Backend workflow #40110597753 passed on prior head `ee1b2a74d2a9f6141b9afbb6e06562b5cf263a9b`; new docs require CI on the latest head. PR #6 draft/unmerged; live order submission and automatic quantity/notional allocation disabled.


## 2026-10-24 — Aggregate endpoint hard guard added; CI pending

- Added a fail-closed resolver guard that blocks Upstox `/v2/trade/profit-loss/charges` from `PER_FILL_ACTUAL` use even if a registry row is incorrectly labelled per-fill. Official docs describe segment/financial-year/date-range aggregate `charges_breakdown`, not a per-fill schema.
- Regression test `test_official_upstox_aggregate_charges_endpoint_cannot_be_promoted_to_per_fill` verifies the endpoint restriction.
- Implementation `cdc07afdd8cc0c8d0b37d7e4aa8cdf1bf6eac651`; test `8ae749017a8ba0016f2c9adeb77eaff41fb5ae70`. Implementation CI is running; test workflow is queued. Await a green result before calling this safeguard verified.
- This does not approve production mappings/tariffs. Null remains distinct from zero; automatic quantity/notional allocation and live order submission remain disabled. PR #6 stays draft/unmerged. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Upstox brokerage calculator restricted to estimates; CI pending

- Official Upstox `GET /v2/charges/brokerage` takes proposed instrument, quantity, product, transaction type and price, returning a charge calculation; this is not proof of final booked per-fill charges. https://upstox.com/developer/api-documentation/get-brokerage/
- Resolver now blocks `/v2/charges/brokerage` from `PER_FILL_ACTUAL` and actual `AGGREGATE_SUMMARY` use even if a mapping is misleadingly labelled. Existing guard still blocks `/v2/trade/profit-loss/charges` from per-fill actual use. New regression tests cover both misuse cases.
- Implementation `3486d854dae2451858a858cb627602aca7338969`; tests `6c92101a1890a0f4d761e86ed3db047a269fd10d`. Prior head `6cc8b58f635fcb4f1b1cb3e5997099d074800a28` passed workflow #40111501429. CI for the new commits must be verified.
- Production mappings/tariffs remain unapproved; null is not zero; automatic quantity/notional allocation and live broker order submission remain disabled. PR #6 stays draft/unmerged. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.
