## Canonical checkpoint reconciliation — 25 October 2026 (end-of-day verified checkpoint)

- **Work only in:** `tarunsharma2610-del/tradepro-improved`, branch `phase3/durable-per-fill-charge-allocation`. Never modify original `tarunsharma2610-del/Tradepro`.
- **End-of-day verified commit:** `075b16af03cf6be4897c381378f68db76a6cbba6`. Branch head matched this SHA.
- **Exact-head Backend CI:** [Run #40211145592 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40211145592), completed 25 October 2026 at 16:21:33 UTC (21:51:33 India time) on this exact SHA.
- **PR #6:** open, draft, unmerged. Do not merge without explicit user approval.
- **Completed:** PostgreSQL concurrency acceptance for two concurrent promotions of one reviewed component racing verification; 25 maintained documents synchronized; root charge-source register marked legacy duplicate, with `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md` canonical.
- **Verified CI gates:** Backend pytest, broker-write safety boundary, SQLite/PostgreSQL 16 migration upgrade-downgrade-re-upgrade, synthetic PostgreSQL/document-volume restore drill. Synthetic restore does not prove actual Oracle Cloud recovery.
- **NEXT STEP — resume here only:** integrate canonical snapshot allocation/reconciliation into `live_fill_accounting_service`. Current accounting still verifies raw source-component rows through the legacy six-row ledger. Audit existing canonical APIs first, then implement a fail-closed end-to-end path for reviewed source evidence, including combined/split transaction/IPFT, exact replay, complete totals, and rejection of extra/unmapped components. Add focused tests only for integration gaps; do not repeat completed concurrency work or duplicate existing tests. Never silently drop/double-count charges or add generic quantity/notional allocation.
- **Remaining Phase 3 gates:** (2) authentic effective-dated tariff applicability; (3) approved component-specific per-fill allocation rules; (4) invoice/source-backed GST/IPFT/component acceptance; (6) final adversarial, migration, and recovery review; (7) exact-head docs/sign-off. Keep candidates DRAFT absent authentic applicable evidence and independent review.
- **Upstox safeguards:** no unused SDK runtime dependency; Agent Skill static-review-only; brokerage calculator estimate-only; aggregate charge API is not per-fill actual evidence.
- **Trading safeguards:** PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling disabled.
- **Resume protocol:** check branch head and latest CI first, then read this checkpoint plus Phase 3 roadmap/instructions. Continue from the next step above; do not restart completed work. Every new commit requires its own exact-head CI before being called verified.
- **Documentation-sync note:** this records the verified state of `075b16a`; any subsequent documentation commit must receive its own exact-head CI before implementation resumes.

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
