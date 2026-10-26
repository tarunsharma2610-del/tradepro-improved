<!-- Phase 3 continuation sync: 27 October 2026. Latest verified code/test head: 31ce2a10bcc789c223608c6566082b24aea7358c; Backend CI #40383076131 SUCCESS. Current maintained-doc synchronization head at the time of this update: fbcefc1ae44f863b5d16d5e32fd819d277b0ead8; documentation CI #40384521664 SUCCESS. DP/demat Execution persistence and central charge-total recomputation are implemented; next gate is focused audit of unknown-vs-zero semantics, delivery/non-delivery rules, migration round-trips, idempotency, rollback, and integration with per-fill allocation/reconciliation. GST/IPFT implementation is not being restarted. PR #6/#7 stay Draft/unmerged; PAPER mandatory; live broker writes disabled; original Tradepro repository out of scope. -->

## Canonical checkpoint reconciliation — 26 October 2026 (canonical live-fill integration verified)

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. Never modify original `tarunsharma2610-del/Tradepro`.
- **Latest verified implementation head before this documentation sync:** `255fc208eed4bc8b922977717209d27912055377`. Exact-head Backend CI [run #40286205714 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40286205714): **962 passed, 1 warning**. Broker-write boundary guard, SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade, synthetic PostgreSQL/document-volume restore, and restore-evidence retention all passed. Synthetic restore does not prove actual Oracle Cloud recovery.
- **PR #6:** open, draft, unmerged. Do not merge without explicit user approval.
- **Phase 3 integration completed on this head:** `LiveFillAccountingService` now requires exactly six independently verified canonical charge snapshots. It revalidates each canonical ledger and its source hashes/links/mapping version, reviewed fill manifest and weights, INR totals, durable reconciliation references, and the contract-note reference under lock. There is no fallback to raw-only legacy allocation rows. Extra, unmapped, unlinked, or foreign-connection per-fill allocations fail closed.
- **Integration tests:** canonical snapshot creation → independent review → allocation → reconciliation; direct and combined/split transaction/IPFT source lines canonicalize to one exchange-charge component; exact replay, missing/unreconciled/extra allocations, and PostgreSQL live-fill-versus-ledger promotion race. No live broker order writes are enabled.
- **Remaining Phase 3 gates:** (2) independently reviewed effective-dated tariff applicability; (3) approved component-specific per-fill allocation rules; (4) invoice/source-backed GST/IPFT and product-specific component acceptance; (6) final adversarial, migration and recovery review; (7) exact-head documentation/sign-off. Official public tariff snapshots are research evidence, not proof of account-specific actual charges; candidate rates remain DRAFT until the required review is recorded. Synthetic restore is not a real Oracle recovery test.
- **Upstox controls:** no unused SDK runtime dependency; Agent Skill remains development/static-review-only; brokerage calculator is estimate-only; aggregate charge endpoints are not per-fill actual evidence.
- **Safety invariants:** PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. Keep PR #6 unmerged until explicit approval.
- **Next step:** resume at the remaining Phase 3 tariff/component evidence gates. Do not repeat canonical snapshot integration. Do not begin the separate AI/open-source adaptations until Phase 3 acceptance is complete.
- **Documentation-sync note:** this multi-document commit must pass its own exact-head CI before the next implementation change.

---


---


# Upstox Agent Skill Security and Compatibility Review

**Reviewed:** 24 October 2026  
**Repository scope:** `tarunsharma2610-del/tradepro-improved` only  
**Upstream skill inspected:** `upstox/upstox-skills`, branch `master`  
**SDK source inspected:** `upstox/upstox-python`, tag `v2.30.0`  
**Review type:** static source review; no skill was installed or executed and no broker credentials were used.

## Summary

The official Upstox Agent Skill is MIT-licensed and provides useful API instructions and examples. It is not safe to install and execute wholesale inside the Tradepro Improved application or grant it live broker credentials. Its declared capabilities include live order placement, modification, cancellation, GTT orders and portfolio/market-data access. Treat it as development-only reference material, review updates before use, and extract only applicable documentation/patterns into project-controlled tests.

## Files and behaviors inspected

- `skills/upstox/SKILL.md`: identifies itself as capable of live trading; includes SDK install/setup, v2/v3 method guidance, confirmation and sandbox recommendations.
- `skills/upstox/scripts/upstox_helpers.py`: creates an SDK client from environment variables, but also falls back to a local `config.json` token. Its profile smoke-test exception handler prints `ApiException.body`; do not run this helper unchanged in a production-like environment because broker error bodies may contain sensitive response data.
- `skills/upstox/scripts/validate_order.py`: validates basic fields and can warn when an F&O lot-size check is skipped. It is a useful example but is not a substitute for Tradepro's own authorization, risk checks, lot-size validation, paper/live mode enforcement, idempotency and audit logging.
- `skills/upstox/examples/place_equity_order.py`: can call live `OrderApiV3.place_order` after an interactive confirmation. It is a real broker write, not a paper simulator.
- `skills/upstox/examples/place_gtt_order.py`: can call `OrderApiV3.place_gtt_order` after confirmation. It is also a broker write.
- `package.json` and `LICENSE`: upstream skill declares MIT license. License does not remove trading or credential risks.

## SDK compatibility finding

Official tag `v2.30.0` identifies package `upstox-python-sdk`, MIT license, and generated SDK clients. The official `ChargeApi.get_brokerage` method is synchronous by default and accepts an `async_req` option that returns a request thread; it also accepts `_request_timeout` in the generated HTTP method. That is not equivalent to our existing async `httpx` implementation with sanitized error categories and validated JSON parsing.

**Decision:** no production SDK dependency or runtime replacement in this step. The source review does not establish a measurable benefit for this endpoint: our existing read-only reconciliation client already calls the same official endpoint and our parser enforces semantic and component-total checks. A package-level test would only be useful if a future endpoint is missing or the generated response model materially improves correctness. Do not introduce a duplicate brokerage client just to claim SDK usage.

## Required safety rules

1. Never place the Agent Skill or its example scripts in the production app runtime.
2. Never execute its live-order examples or GTT examples as part of CI or routine audits.
3. Never supply a live access token to a coding agent or skill script. Do not put tokens in chat, Git, fixtures, issue text, logs, or error output.
4. Do not use the skill's local `config.json` token fallback in our app. Use the app's established secret storage and owner-scoped token lifecycle.
5. Preserve the app-level PAPER-only requirement and live broker write guard. The skill's own interactive confirmation is not an authorization boundary.
6. Use the official SDK only behind existing project service interfaces after a separate reviewed implementation decision; normalize all responses through existing parsers and semantic gates.
7. For any future SDK spike, use synthetic fixtures or sandbox credentials only, pin exact package version, review dependencies/license, and test error redaction, timeouts, async behavior, and order-write unreachability.
8. Re-review the upstream skill at a specific commit before adopting changes; do not blindly run `npx skills add` in a repository that contains broker credentials or has live write capabilities.

## Acceptance result

- [x] Official SDK version/source and Brokerage Details method inspected.
- [x] Agent Skill metadata, helper, validation script, live equity-order example, GTT example and license inspected.
- [x] SDK value assessed against current async REST implementation.
- [x] No runtime dependency added; no code executed from the skill.
- [x] No live credentials, API calls or orders used.
- [ ] Future endpoint-specific SDK integration only if a documented capability gap or correctness benefit is identified.

## Scope safeguards

Only `tarunsharma2610-del/tradepro-improved` may be changed. Original `tarunsharma2610-del/Tradepro` is out of scope. PR #6 must remain open, draft and unmerged. PAPER mode remains mandatory and live order placement, modification and cancellation remain disabled.


## Canonical latest Phase 3 checkpoint — 26 October 2026

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **Verified code/evidence head:** `d287da70ce184c904c6f9ede9e4a0edca5839f8f` (commit: “docs: reconcile public Upstox contract note GST examples”).
- **Exact-head CI:** PASS — [GitHub Actions run #40304398632](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40304398632), commit `d287da70ce184c904c6f9ede9e4a0edca5839f8f`; **1,004 passed, 1 warning**. Broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and restore-evidence retention also passed. This is CI evidence, not proof of a real Oracle recovery or broker-origin authenticity.
- **GST/IPFT research:** Three public third-party historical Upstox note copies were reconciled: 11-Feb-2025 base ₹2.97 / IGST ₹0.53; 21-May-2024 base ₹77.56 / IGST ₹13.96 (IPFT ₹0.11 listed outside that note's printed base); 12-Mar-2025 base ₹2.75 / IGST ₹0.50. Printed-base compositions differ historically. The current official Upstox schedule supports the **estimate-only** base of brokerage + transaction charges + demat where applicable + IPFT, with IPFT represented exactly once because it is combined with transaction charges. Do not add SEBI to this current estimate base without current applicable billing evidence; never calculate GST on trade notional or infer zero from missing/null fields.
- **Tax/accounting approval:** all four GST component candidates remain `DRAFT`. Historical public copies do not prove current actual per-fill billing across products/accounts. Actual-charge promotion stays gated; estimate logic and actual invoice reconciliation are distinct. Follow effective dates and preserve raw API/source evidence.
- **Next action when resuming:** continue Phase 3 from this exact commit and checkpoint. Next gate is component-specific GST acceptance cases for equity delivery, intraday, futures and options, then implementation review and exact-head CI; do not restart from earlier saved checkpoints.
- **Safety / PR:** PAPER mode mandatory; live broker `place_order`/`modify_order`/`cancel_order` and automatic live-fill promotion remain disabled. PR #6 remains open, draft and unmerged. Original `tarunsharma2610-del/Tradepro` is not the work target and must remain untouched.
- This checkpoint supersedes older statements in this document about CI being in progress or requiring verification for the pre-`d287da7` head. Historical notes remain history; this is the canonical resume point.
