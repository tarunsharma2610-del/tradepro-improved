> **AUTHORITATIVE CURRENT STATUS — 18 October 2026**
>
> This block supersedes older “current status”, “latest verified”, and “next task” statements elsewhere in this document. Dated entries below are historical evidence and must not be read as current status unless their commit SHA matches the current branch head.
>
> - Repository: `tarunsharma2610-del/tradepro-improved`; working branch: `safety/fail-closed-trading-mode`.
> - PR #1: open, draft, unmerged. Do not merge without explicit user authorization. Original `tarunsharma2610-del/Tradepro` must remain untouched.
> - Branch head reported by PR API at the documentation review: `15ff31122ba2f7e2f9f2ac1c1a7e80d6b77c80d1`.
> - Latest broker parser test workflow observed: GitHub Actions run #722, SHA `e6a69138e2fd132da0b7a526c35f40aea4630432`, conclusion `success`. This is **not** the same SHA as the branch head above. Therefore exact-head CI is **NOT VERIFIED** by that run.
> - Recent reconciliation changes: commit `e9a69472e54b84333134568a559fa2592dcc12ce` adds staged partial-fill replay/overfill/rollback regression coverage; `c2e881103e961aaa999e94ff2436fd1f91c80140` rejects order snapshots where average price contradicts filled quantity; `e6a69138e2fd132da0b7a526c35f40aea4630432` adds negative parser test cases.
> - Trade staging is not fill accounting. Broker-confirmed fills have **not** been proven to promote exactly once into executions and atomically update cash, positions, fees, and P&L. Parent/child terminal-state and cancellation-after-partial-fill behavior remain open for end-to-end verification.
> - Safety-control, durable intent/claim, account-bound recovery, and authorization foundations are documented in PR #1, but they do not constitute a complete broker-write path. `prepare_order_intent` and `validate_claimed_submission` are not permission to submit an order; the final check-to-network-I/O race remains unresolved.
> - Mandatory safety: `TRADING_MODE=PAPER`; `LIVE_ORDER_SUBMISSION_ENABLED=false`; no live `place_order`, `modify_order`, or `cancel_order`; no real orders in tests; no changes to original `Tradepro`.
>
> **Audit rule:** each finding must remain explicitly open until source inspection and a relevant test on a verified commit demonstrate closure. This status block does not mark any open security or requirements finding resolved.
>
> **Evidence links:** [PR #1](https://github.com/tarunsharma2610-del/tradepro-improved/pull/1) · [workflow #722](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39143953569) · [partial-fill regression commit](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e9a69472e54b84333134568a559fa2592dcc12ce) · [parser fix](https://github.com/tarunsharma2610-del/tradepro-improved/commit/c2e881103e961aaa999e94ff2436fd1f91c80140) · [parser tests](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e6a69138e2fd132da0b7a526c35f40aea4630432)
>
> ---
# Order-entry, worker, retry and broker-write path inventory

**Review date:** 18 October 2026  
**Branch:** `safety/fail-closed-trading-mode`  
**Review type:** Static source-path inventory; no runtime order submission performed.  
**Purpose:** Map current order-capable paths before designing a safety-control API or connecting the preflight coordinator.

## Executive result

The reviewed application currently has one shared paper-order service and two main callers: the authenticated manual portfolio order route and strategy evaluation (called either from an authenticated “evaluate now” route or the scheduled worker). The paper service rejects any `TRADING_MODE` other than `PAPER`, and it only persists paper orders. Its cancel operation explicitly rejects non-paper orders. This is an important current fail-closed boundary.

The Upstox adapter does implement broker `place_order`, `modify_order`, and `cancel_order` network methods, but the reviewed application services/routes do not call these write methods. The live execution/preflight/recovery/reconciliation services are unregistered and do not submit orders. This is not yet proof that every possible indirect/dynamic call site in every runtime environment is impossible; the inventory is source review and should be backed by automated repository-wide call-site checks and tests before a live path is ever enabled.

**Disposition:** No route/worker wiring change is safe yet. Keep `LIVE_ORDER_SUBMISSION_ENABLED=false`, `TRADING_MODE=PAPER`, and PR #1 draft/open.

## Path inventory

| Entry point / component | Current behavior | Safety status / required follow-up |
|---|---|---|
| `POST /api/v1/portfolios/{portfolio_id}/orders` in `backend/app/api/v1/portfolios.py` | Authenticated user; applies order rate limit; calls `ExecutionService.place_order`. | Service is PAPER-only and rejects LIVE/unknown mode before portfolio lookup. If future live routing is introduced, this must dispatch through one central coordinator and must not allow direct service bypass. |
| `DELETE /api/v1/portfolios/{portfolio_id}/orders/{order_id}` | Calls `ExecutionService.cancel_order`. | Service only cancels pending PAPER orders; no broker cancel call. Future live cancel requires separate status-aware workflow and safety/audit policy. |
| `POST /api/v1/portfolios/{portfolio_id}/strategies/{strategy_id}/evaluate` | Authenticated owner route; immediately calls `StrategyExecutionService.evaluate`. | Strategy entry and exit both use shared PAPER-only `ExecutionService.place_order`; service mode guard prevents live orders. Need ensure any future strategy-triggered LIVE intent uses same central coordinator as manual entry. |
| Scheduled worker `backend/app/worker.py:run_once` | Matches pending limit orders, lists active strategies, evaluates each with `StrategyExecutionService`. | Matcher is PAPER-only; strategy service shares PAPER-only execution service. Worker has no live preflight registration. Add integration only after all call sites and concurrency behavior are tested. |
| `ExecutionService.place_order` | Creates PAPER order rows; reads broker quote for price; applies virtual cash/fees/accounting; no broker order POST. | The authoritative current service boundary: refuses non-PAPER mode. Do not weaken or remove this guard until a separately reviewed live submitter is fully gated. |
| `ExecutionService.match_pending_limit_orders` | Background fills crossed pending PAPER limit orders using quotes. | Local paper fill/accounting, not broker order submission. Must remain mode-scoped and never match LIVE rows. |
| `StrategyExecutionService._enter` / `_exit` | Sends strategy entry and exit intents to `ExecutionService.place_order`; idempotency key based on strategy/signal/candle timestamp. | PAPER-only through shared service. Existing `AUTOMATED_ENTRIES_ENABLED` disables entries but intentionally leaves exits available; it is not a universal live kill switch. |
| `LiveExecutionService.preflight` | Validates local intent, env interlocks, user confirmation, account-wide risk gate, connection and credentials; returns a plan only. | No broker write; disabled unless environment flags and risk gate are supplied. Not registered to routes/workers. |
| `LivePreflightCoordinator.preflight` | Checks persisted account safety, gathers read-only Upstox snapshots, revalidates credentials/connection and returns a non-secret plan. | No broker write; not registered to routes/workers. Not an execution authorization token; callers must not infer submission is safe solely because a plan exists. |
| `LiveOrderRecoveryService.prepare_intent` | Persists stable LIVE intent after calling `LiveExecutionService.preflight`; idempotent intent identity. | Does not submit. Note it does **not** use `LivePreflightCoordinator` yet, so persistent account safety and fresh broker snapshot checks are not composed through this path. Do not expose or invoke as an order API before design and integration tests close this gap. |
| `LiveOrderRecoveryService.mark_submission_unknown` / `recover_by_tag` | Marks recovery state and looks up order history/tag; does not blindly resubmit. | Recovery/read-only only. Ensure any future submitter persists a pre-POST state and routes ambiguous outcomes to recovery, never automatic duplicate POST. |
| `LiveOrderFillReconciliationCoordinator.reconcile_and_promote` | Reads broker child-order status/trades and promotes staged fills after reconciliation. | Reconciliation/accounting, not submission. Must be gated by ownership, mapped child orders, consistent statuses and audit events; test no partial promotion on ambiguous siblings. |
| `UpstoxAdapter.place_order` | Implements POST to Upstox V3 order/place. | Broker-write primitive exists. Static search did not find an application call site in the reviewed service paths. This method is a high-risk sink: future code must only invoke it from one reviewed submitter after all gates and durable intent commit. |
| `UpstoxAdapter.modify_order` | Implements PUT to Upstox V3 order/modify. | Broker-write primitive exists; no reviewed application caller found. Future use needs order ownership, status confirmation and audit. |
| `UpstoxAdapter.cancel_order` | Implements DELETE to Upstox V3 order/cancel. | Broker-write primitive exists; no reviewed application caller found. Future use needs ownership, idempotency and post-request broker status confirmation. |
| `BrokerReconciliationService` / broker child reconciliation | Reads broker status, trades and history; stores reconciliation data. | Read/repair path, not a place-order path. Review separately for status mutation and audit behavior before exposing as operator controls. |

## Important distinctions

- **A broker adapter method is not an active order route by itself.** The three write methods exist, but this review did not find a production service call to them.
- **Paper quotes are broker reads, not live order submissions.** `ExecutionService` may use Upstox quote endpoints for paper fills without using Upstox order-write endpoints.
- **The preflight coordinator is not wired.** Passing its checks creates a plan, not an order, and does not guarantee the rest of the system enforces the same decision.
- **Safety state is not a universal interlock yet.** It is checked inside `LivePreflightCoordinator`, but paper execution and worker paths are not routed through it; paper mode remains protected by the PAPER-only service guard.
- **The env flag is an additional guard, not a complete authorization model.** Keep `LIVE_ORDER_SUBMISSION_ENABLED=false`; do not treat changing `TRADING_MODE` alone as enabling supported live execution.

## Required work before any live order route exists

1. Design one internal submission service that is the only allowed caller of broker order-write primitives.
2. Compose account-wide safety, fresh broker snapshots, risk/margin/market-data gates, ownership, explicit confirmation, env interlocks and durable idempotent intent in that service. Do not treat a plan returned by preflight as a bypassable boolean.
3. Make durable intent + audit event atomic; persist submission-attempt/unknown state before network POST; recover ambiguous outcomes by broker tag without blind retries.
4. Keep the existing PAPER service explicitly paper-only; do not branch inside it to live unless there is a reviewed design and comprehensive tests.
5. Add automated source/test guardrails that fail CI if route/worker/other service code calls adapter `place_order`, `modify_order`, or `cancel_order` outside the approved submission/cancel service.
6. Add HTTP and service tests for every manual/strategy/worker path, fail-closed flags, missing/stale safety state, audit-write failure, duplicate/replay, timeout/unknown submission, concurrency, cancellation and reconciliation.
7. Separately resolve the findings in `SECURITY_CONTROL_ENDPOINT_AUDIT.md`: least-privilege safety permissions, operator audit reads, step-up auth, CSRF/origin policy, event redaction, atomic state/event persistence and append-only enforcement.
8. Only after review and CI evidence, connect routes/workers. Keep live order submission disabled until explicit release approval.

## Scope limitations

This is a static code-path review of the current branch, not a runtime trace, penetration test, broker sandbox test or production sign-off. Repository code search returned no call-site matches for `.place_order(`, `.modify_order(`, `.cancel_order(`, `LiveOrderRecoveryService`, or `LivePreflightCoordinator` in the indexed search, so conclusions are grounded primarily in direct inspection of the route, service, worker and adapter files listed above. Repeat the search against a fresh checkout/CI source scan before any live activation.
