## Canonical checkpoint reconciliation — 25 October 2026 (after exact-head CI)

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **PR #6:** open, draft, unmerged.
- **Latest verified code/test commit:** `50802e96e06756b57a9f930e0c54c680777922d4`. Exact-head Backend CI [run #40209741299](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40209741299) completed successfully on that SHA.
- **Verified:** backend pytest; broker-write boundary enforcement; SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade; synthetic PostgreSQL/document-volume restore drill. The synthetic restore does not prove actual Oracle Cloud recovery.
- **Concurrency acceptance gap closed:** the PostgreSQL test now races two promotion calls for the same reviewed component alongside verification; both promotion calls must return the full allocation set, and the final ledger must contain complete reconciled rows with one consistent durable reference.
- **Next single implementation step:** close the canonical-ledger integration gap (Phase 3 Gates 1C/5). Canonical snapshot materialization/review/allocation/reconciliation services exist, but `live_fill_accounting_service` still verifies raw source-component rows and the legacy six-row source ledger. Audit the intended canonical snapshot path and implement/test a fail-closed end-to-end route from reviewed source rows (including combined/split transaction/IPFT) through canonical snapshot allocation/reconciliation into live-fill accounting. Do not silently drop or double-count extra source components; do not add generic quantity/notional allocation.
- **Remaining gates:** evidence-backed effective-dated tariff selection (Gate 2), approved per-fill rule wiring (Gate 3), invoice/source-backed GST/component acceptance (Gate 4), final adversarial/migration/restore review (Gate 6), and final exact-head docs/sign-off (Gate 7) remain open.
- **Upstox decisions:** no unused SDK runtime dependency; Agent Skill remains static-review-only and must not be executed or given live credentials. Brokerage calculator output is estimate-only; aggregate charge endpoints are not per-fill actual evidence. GST/IPFT/tariff candidates remain DRAFT until authentic applicable evidence and independent review support approval.
- **Safeguards:** original `tarunsharma2610-del/Tradepro` is out of scope and must remain untouched; PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. Do not merge PR #6 without explicit user approval.

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
