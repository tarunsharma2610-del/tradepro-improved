## Authoritative audit reconciliation — 25 October 2026

- **Repository/branch:** `tarunsharma2610-del/tradepro-improved` / `phase3/durable-per-fill-charge-allocation`. PR #6 remains draft and unmerged.
- **Last verified branch head before this documentation reconciliation:** `ecdaae1035779631bcb45ee5d50f60094c35d1ab`. Backend workflow [#40205635687](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40205635687) completed successfully on that exact SHA; the Backend pytest job passed.
- This confirms the inspected pre-reconciliation head, not any subsequent documentation commit. The final documentation head must receive its own exact-head CI check.
- These Upstox API/SDK/Agent Skill/source-register documents are part of the **18-document living checkpoint inventory**. The previous inventory omitted them; they were present in the repository.
- **SDK decision:** do not add an unused SDK runtime dependency or replace the existing async `httpx` client wholesale without a concrete documented capability/correctness benefit. Preserve timeout handling, error redaction, parser/semantic gates, and the broker-write boundary.
- **Agent Skill decision:** static-review reference only; do not execute examples, use live credentials, or import the skill wholesale. It contains live order/GTT examples and unsafe patterns. No real credentials, live calls, or orders were used in this audit.
- Brokerage calculator results remain estimates; the Trade Charges API is aggregate reconciliation evidence, not proof of actual per-fill charges. GST/IPFT/tariff candidates remain DRAFT until authentic account-specific source evidence and independent review support approval.
- **Safeguards:** only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` untouched; PAPER mandatory; live broker order writes disabled.

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
