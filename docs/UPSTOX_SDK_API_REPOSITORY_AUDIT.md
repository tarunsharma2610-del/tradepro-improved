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



## Canonical latest Phase 3 checkpoint — 26 October 2026

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **Verified code/evidence head:** `d287da70ce184c904c6f9ede9e4a0edca5839f8f` (commit: “docs: reconcile public Upstox contract note GST examples”).
- **Exact-head CI:** PASS — [GitHub Actions run #40304398632](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40304398632), commit `d287da70ce184c904c6f9ede9e4a0edca5839f8f`; **1,004 passed, 1 warning**. Broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and restore-evidence retention also passed. This is CI evidence, not proof of a real Oracle recovery or broker-origin authenticity.
- **GST/IPFT research:** Three public third-party historical Upstox note copies were reconciled: 11-Feb-2025 base ₹2.97 / IGST ₹0.53; 21-May-2024 base ₹77.56 / IGST ₹13.96 (IPFT ₹0.11 listed outside that note's printed base); 12-Mar-2025 base ₹2.75 / IGST ₹0.50. Printed-base compositions differ historically. The current official Upstox schedule supports the **estimate-only** base of brokerage + transaction charges + demat where applicable + IPFT, with IPFT represented exactly once because it is combined with transaction charges. Do not add SEBI to this current estimate base without current applicable billing evidence; never calculate GST on trade notional or infer zero from missing/null fields.
- **Tax/accounting approval:** all four GST component candidates remain `DRAFT`. Historical public copies do not prove current actual per-fill billing across products/accounts. Actual-charge promotion stays gated; estimate logic and actual invoice reconciliation are distinct. Follow effective dates and preserve raw API/source evidence.
- **Next action when resuming:** continue Phase 3 from this exact commit and checkpoint. Next gate is component-specific GST acceptance cases for equity delivery, intraday, futures and options, then implementation review and exact-head CI; do not restart from earlier saved checkpoints.
- **Safety / PR:** PAPER mode mandatory; live broker `place_order`/`modify_order`/`cancel_order` and automatic live-fill promotion remain disabled. PR #6 remains open, draft and unmerged. Original `tarunsharma2610-del/Tradepro` is not the work target and must remain untouched.
- This checkpoint supersedes older statements in this document about CI being in progress or requiring verification for the pre-`d287da7` head. Historical notes remain history; this is the canonical resume point.


## Phase 3 CI synchronization — 26 October 2026 (GST/IPFT resolver)

- Latest verified code head: `13e201661d26b04c9bf75bb7e3aaf567ad1e69c4`; exact-head Backend CI [#40378072884 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40378072884): **1,056 passed, 1 warning**. Broker-write boundary, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill and retained restore evidence passed.
- Added scope/effective-date-selected GST policy resolution for `COMBINED`, `SEPARATE`, and `NOT_APPLICABLE` IPFT representation. It rejects double representation, wrong-exchange reuse, missing/extra components, and unapproved or out-of-window policies. This is estimate-policy plumbing, not actual invoice reconciliation or tariff approval.
- Next Phase 3 gate: persist optional DP/demat charges safely, migrate canonical accounting/persistence and total-charge recomputation, then integrate statutory GST valuation only through reviewed source-backed policy paths. Actual per-fill invoice acceptance remains evidence-gated; no personal contract note is required.
- Safety unchanged: PR #6/#7 Draft and unmerged; PAPER mandatory; live broker order writes and automatic live-fill promotion/scheduling disabled; original `tarunsharma2610-del/Tradepro` untouched and out of scope.
