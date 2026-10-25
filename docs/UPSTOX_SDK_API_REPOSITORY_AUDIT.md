## Canonical checkpoint reconciliation — 25 October 2026 (latest exact-head CI verified)

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **PR #6:** open, draft, unmerged.
- **Latest verified branch head before this documentation sync:** `e9440e2f31f9d4d108b9160608e653efffd2d9fc`. Exact-head Backend CI [run #40210391188](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40210391188) completed successfully on this exact SHA (25 October 2026).
- **Latest verified code/test checkpoint:** `50802e96e06756b57a9f930e0c54c680777922d4`; Backend CI [run #40209741299](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40209741299) passed on that exact SHA.
- **Verified gates:** backend pytest; broker-write safety boundary; SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade; synthetic PostgreSQL/document-volume restore drill. The synthetic restore does not prove actual Oracle Cloud recovery.
- **Concurrency acceptance gap closed:** PostgreSQL coverage races two promotion calls for the same reviewed component alongside verification; both promotions must return the complete allocation set and final reconciled rows must share one durable reference.
- **Next single implementation step:** integrate canonical snapshot allocation/reconciliation end-to-end with live-fill accounting (Phase 3 Gates 1C/5). Current live-fill accounting still validates raw source-component rows through the legacy six-row ledger. Add focused integration coverage for combined/split transaction/IPFT, exact replay, complete totals, and fail-closed rejection of extra/unmapped components. Do not silently drop or double-count charges; do not introduce generic quantity/notional allocation.
- **Remaining gates:** evidence-backed effective-dated tariff selection (Gate 2); approved per-fill rule wiring (Gate 3); invoice/source-backed GST/component acceptance (Gate 4); final adversarial/migration/restore review (Gate 6); final exact-head documentation/sign-off (Gate 7).
- **Upstox controls:** no unused SDK runtime dependency; Agent Skill is static-review-only and must not be executed or supplied live credentials. Brokerage calculator output is estimate-only; aggregate charge endpoints are not per-fill actual evidence. GST/IPFT/tariff candidates remain DRAFT until authentic applicable evidence and independent review support approval.
- **Safety invariants:** original `tarunsharma2610-del/Tradepro` remains out of scope and must stay untouched; PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. Do not merge PR #6 without explicit user approval.
- **Checkpoint protocol:** this 25-file documentation sync must pass CI on its own resulting commit before the next implementation change. Parent-commit CI does not verify a newer SHA.

---


# Upstox SDK and API Repository Audit

**Reviewed:** 24 October 2026  
**Repository:** `tarunsharma2610-del/tradepro-improved` only  
**Branch:** `phase3/durable-per-fill-charge-allocation`  
**Purpose:** Audit the current implementation before adding or replacing SDK dependencies. This is an evidence-based gap assessment, not a claim that live broker calls were made.

## Executive decision

**Do not add the SDK dependency blindly or rewrite the existing HTTP clients yet.** The backend currently uses a deliberate asynchronous HTTP implementation for REST calls, a custom V3 market-data WebSocket client, protobuf decoding, a narrow read-only reconciliation client, and validated response parsers. Replacing those paths wholesale with the official generated SDK could introduce synchronous calls into async services and weaken existing timeout, error-redaction, allowlist, or test guarantees.

The official Python SDK is relevant and should be evaluated in a small compatibility spike. Add it only where it provides a clear supported-endpoint/schema benefit and can preserve current safety and async behavior. The official Agent Skill is development guidance; it is not a production runtime dependency.

## Repository evidence

| Area | Observed implementation | Audit result |
|---|---|---|
| Python dependencies | `backend/requirements.txt` includes `httpx`, `websockets`, and `protobuf`; no `upstox-python-sdk` dependency is listed. | SDK is not currently declared as an app dependency. |
| OAuth | `backend/app/brokers/upstox/adapter.py` builds the authorization URL and exchanges the authorization code using direct HTTP. | Existing implementation; review OAuth state/redirect validation and token lifecycle separately before changing it. |
| Quotes and candles | The adapter uses documented V3 LTP and historical-candle REST paths via a shared HTTP helper. | Already integrated through REST; SDK adoption must be justified endpoint-by-endpoint. |
| Market-data feed V3 | `backend/app/services/upstox_market_data_streamer.py` requests a fresh authorized WebSocket URL, validates the host/scheme, decodes the V3 protobuf feed, bounds reconnects and rejects stale ticks. | A dedicated V3 implementation already exists. Avoid replacing it solely to use the SDK; compare reconnect/resubscribe, lifecycle, async, and stale-data behavior first. |
| Adapter stream hook | `UpstoxAdapter.get_market_data_stream_url` currently returns a not-implemented result and refers to the separate streaming service. | Potential interface inconsistency to reconcile; do not create a second stream implementation. |
| Read-only reconciliation | `backend/app/brokers/upstox/reconciliation_client.py` exposes fixed GET-only paths for order/trade reads, brokerage estimates, and aggregate trade charges, with bounded timeout and sanitized error categories. | Preserve this read-only boundary and its tests. |
| Brokerage estimate parsing | `backend/app/brokers/upstox/response_parsing.py` validates the documented charge response, distinguishes DP-plan minimum expense from the estimate total, and rejects partial/inconsistent totals. | Keep the endpoint classified as an estimate, not actual booked charge evidence. |
| Charge semantics | `backend/app/services/broker_charge_api_value_resolution.py` blocks the Upstox brokerage endpoint from `PER_FILL_ACTUAL` use and blocks the segment/FY charge endpoint from per-fill use. | Important accounting guard already exists; SDK adoption must not bypass it. |
| Tariff policy | `backend/app/services/upstox_tariff_candidates.py` keeps sourced tariff candidates in DRAFT; active tariff selection is fail-closed. | Do not activate candidate tariffs merely because the API/SDK returns values. |
| Live trading | The adapter contains an order POST method, but the app-level safety boundary and broker-write regression guard are separate controls. | Do not invoke SDK order-write methods during this work. Preserve PAPER mode and the live-write guard. |
| Agent Skill | Project policy already links the official Upstox Agent Skill repository and requires official-source review. | Skill can guide coding/review; do not run its trading examples or give it live credentials. |

## Official documentation reviewed

- [Upstox API catalogue](https://upstox.com/developer/api-documentation/) — lists account, market-data, streaming, portfolio, charges, sandbox, MCP, and Agent Skills capabilities.
- [SDK installation instructions](https://upstox.com/developer/api-documentation/installing-sdk/) — lists the Python package as `upstox-python-sdk`, installed with `pip install --upgrade upstox-python-sdk`.
- [Official Python SDK repository](https://github.com/upstox/upstox-python) — public generated SDK documentation identifies API v2 and documents V3 classes such as MarketDataStreamerV3 and OrderApiV3; verify the currently pinned package release and each method's coverage before adoption.
- [Brokerage Details API](https://upstox.com/developer/api-documentation/get-brokerage/) — `GET /v2/charges/brokerage` estimates charges for proposed order inputs. The DP-plan minimum expense is separately documented and is not included in the brokerage estimate total.
- [Trade Charges API](https://upstox.com/developer/api-documentation/get-trade-charges/) — returns a segment/financial-year charge breakdown; it is not per-fill evidence.
- [Authentication](https://upstox.com/developer/api-documentation/authentication/) — OAuth authorization-code flow and registered redirect URI requirements.
- [Agent Skills](https://upstox.com/developer/api-documentation/agent-skills/) and [official skill repository](https://github.com/upstox/upstox-skills) — coding-agent instructions and examples. Treat skills as untrusted executable development material: inspect before running and do not run trading-capable examples with live credentials.
- [Sandbox](https://upstox.com/developer/api-documentation/sandbox/) — supports documented order API testing in sandbox; this is distinct from the app's PAPER simulator and must use sandbox credentials/URLs only.

## Recommended implementation sequence

1. **Keep the current runtime unchanged during this audit.** No dependency was added and no live API request was made.
2. Build a version-pinned SDK compatibility spike in an isolated test environment: inspect available methods and response schemas for ChargeApi/get_brokerage, historical trades/charges, quote/candle endpoints, and V3 stream support. Record package version, Python compatibility, license, dependency impact, and generated-client limitations.
3. Compare each candidate SDK method with existing clients for async compatibility, timeout control, retry/backoff, response validation, error redaction, and testability. Do not replace a safer existing implementation just for uniformity.
4. First likely candidate for a bounded prototype is the brokerage estimate endpoint because official docs provide a specific SDK example. Keep it read-only and compare its normalized response with the existing parser using synthetic fixtures. No live credential is needed for unit tests.
5. If the SDK offers no material benefit or its synchronous generated client complicates the async architecture, retain the documented direct HTTP adapter and add contract tests against official schemas. Document the reason instead of adding an unused dependency.
6. Audit the Agent Skill separately as development-only: read `SKILL.md`, enumerate files/scripts, inspect commands and permissions, and adapt safe API examples into tests. Do not install it into production or execute order examples.
7. Reconcile the adapter's stream-hook interface with the existing V3 streamer without introducing duplicate connections. Add tests for lifecycle, reconnect, stale feed, and owner-scoped token access if this interface is changed.
8. After any implementation, update all affected docs, run backend tests and broker-write guard, verify exact-head GitHub Actions, and leave PR #6 draft/unmerged.

## Explicit non-goals and safety gates

- No account token or client secret was used or requested.
- No live Upstox API calls or orders were submitted.
- No SDK dependency was added in this audit commit.
- No tariff candidates were approved and no estimate/aggregate endpoint was promoted to actual per-fill evidence.
- PAPER mode remains mandatory; live order placement, modification, and cancellation remain disabled.
- Only `tarunsharma2610-del/tradepro-improved` may be changed. Original `tarunsharma2610-del/Tradepro` is out of scope.
- PR #6 must remain open, draft, and unmerged.

## Acceptance checklist for the SDK spike

- [ ] Exact package release and license reviewed; dependencies pinned within the project's policy.
- [ ] Required API methods and V3 support verified from that release's source/schema.
- [ ] Async behavior, timeout, retry, and error-redaction behavior tested.
- [ ] SDK response parsed through the existing validation/semantic guard layer.
- [ ] No order-write method is reachable from tests or app code introduced by the spike.
- [ ] Tests run without real credentials or live broker calls.
- [ ] Documentation and exact-head CI updated before considering the integration accepted.

## SDK source compatibility review — 24 October 2026

The official `upstox-python` tag `v2.30.0` declares package `upstox-python-sdk`, MIT licence, generated client code, and dependencies including `urllib3`, `six`, `certifi`, `python-dateutil`, `websocket-client`, `uuid`, and `protobuf`. The official `ChargeApi.get_brokerage` method is synchronous by default; its generated client offers `async_req=True` (thread-based) and `_request_timeout`, but this does not directly replace the current async `httpx` client and sanitized error/result abstraction.

**Compatibility decision:** do not add the SDK as a runtime dependency in this step. Our read-only reconciliation client already exposes the brokerage estimate endpoint and the existing parser validates components and semantic boundaries. No measurable benefit was found for replacing this specific call. Re-evaluate SDK adoption only for a concrete endpoint/schema gap or material correctness benefit; if adopted, isolate it behind the current client interface and preserve timeout/error redaction and parser gates.

The official Agent Skill static review is in [`docs/UPSTOX_AGENT_SKILL_SECURITY_REVIEW.md`](UPSTOX_AGENT_SKILL_SECURITY_REVIEW.md). The skill includes scripts capable of live order and GTT writes; its helper can fall back to a local config token and prints an API exception body in its smoke-test path. Do not execute its examples or install it wholesale in the app. No skill code was executed and no broker credentials or live API calls were used.

