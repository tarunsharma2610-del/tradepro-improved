# Upstox Python SDK compatibility audit — 30 October 2026

## Decision

**Do not add `upstox-python-sdk` as a runtime dependency at this stage.** Keep the current asynchronous Upstox adapter and V3 market-data streamer. Reuse official SDK/API contracts selectively where they add fields or endpoint coverage that our implementation lacks.

Verified package: `upstox-python-sdk==2.30.0`, MIT licence, PyPI upload 7 September 2026. The official GitHub README still displays an older 2.23.0 version string, while the 2.30.0 release tag and PyPI release history confirm 2.30.0. Pin by verified release if later adopted; do not trust the stale README version line.

## Component comparison

| Area | Existing Tradepro Improved implementation | Official SDK 2.30.0 | Decision |
|---|---|---|---|
| REST transport | `httpx.AsyncClient`, async BrokerAdapter, typed BrokerCallResult, endpoint-specific methods | Generated synchronous client using urllib3 | Keep ours; no async/concurrency advantage from SDK |
| OAuth | Server-side OAuth state bound to user/connection, one-time nonce, encrypted credentials and tokens | Generated API methods/models for API calls | Keep ours; application state/security lifecycle is more specific |
| WebSocket | Native asyncio/websockets, TLS host validation, fresh authorized URL and token_provider on each reconnect | Callback/event streamer built on websocket-client; configurable finite auto-reconnect | Keep ours; dynamic token provider and bounded exponential retry are better aligned with app lifecycle |
| Subscription control | Current implementation applies one feed mode to the whole user stream | SDK maintains separate per-mode subscription sets and replays each set after reconnect | Borrow per-mode registry/replay design into our async streamer; do not adopt SDK transport |
| Protobuf | Checked-in official V3 schema and generated decoder | Bundled V3 schema/decoder | No dependency needed; schemas were compared and matched |
| Redis | User-isolated atomic snapshot/version/epoch and Pub/Sub pipeline | Not provided by SDK | Keep ours |
| Freshness/recovery | Exchange + receive timestamp checks, silence timeout, reconnect and fail-closed quotes | Not an application-level replacement | Keep ours |
| Instrument master | Official compressed BOD catalogue with completeness checks and upsert | Instrument search endpoints | Keep BOD catalogue as authoritative universe; use search API only for targeted discovery |
| Portfolio stream | Not currently in Phase 4 scope | PortfolioDataStreamer | Re-evaluate when read-only account/portfolio live updates are implemented |

## Concrete SDK/API finding reused

The official v2.30.0 release includes Closing Auction Session (CAS) market-data support. The SDK's `MarketDataFeedV3.proto` was compared with `backend/app/brokers/upstox/proto/MarketDataFeedV3.proto`; the schemas match, including `iep`, `rp`, `ieq`, `iiqTotal`, `iiqM`, and `casEligible`.

Our decoder previously ignored those fields. They are now carried in the MarketTick model, Redis quote snapshot and GET market-stream status response. Numeric proto3 scalar zero is represented as unavailable (`None`) because proto3 scalar presence cannot distinguish an omitted value from an explicit default zero. CAS eligibility is exposed as the protobuf boolean (false by default).

## Newer API coverage to plan

- SDK release 2.27.0 introduced Fundamentals and Market Information API coverage (financial statements, ratios, shareholding/corporate actions, FII/DII, OI, max pain and PCR). These are candidate scanner/research inputs, not reasons to replace our adapter.
- SDK release 2.30.0 added CAS fields to Full Market Quotes V3 and market feed.
- SDK instrument-search capabilities may complement, but must not replace, validated BOD instrument-master synchronization.

## Adoption gate

Reconsider adding the SDK only if a specific endpoint/model/feature cannot be implemented more safely or efficiently through our async adapter. Any adoption must:
1. Pin and verify an exact release and licence.
2. Compare endpoint support and response models against our adapter.
3. Keep synchronous SDK calls off the event loop if unavoidable (thread offload required).
4. Prove token handling, timeout/retry behaviour, error mapping and test coverage.
5. Preserve PAPER mode and the broker-write boundary; never expose live order methods through normal application paths.

No SDK package dependency was added. No live broker calls or credentials were used in this audit.


## Additional concrete gap — mixed feed modes

A deeper source-level comparison of the official v2.30.0 MarketDataStreamerV3 found that it maintains separate subscription sets for LTPC, full, option_greeks and full_d30, and replays each set when the socket opens. The current Tradepro Improved streamer has one user-wide mode and requires a mode change to cover every subscribed key. This prevents a mixed workload (broad LTPC universe, selected full-depth instruments, selected option-Greeks instruments) on one user stream.

**Decision: borrow the SDK's per-mode subscription registry and reconnect replay semantics**, while keeping our own asyncio/websockets transport, fresh token-provider call on every reconnect, bounded exponential retry, protobuf parsing, freshness checks and Redis publisher. Persist each instrument/mode identity in the existing durable subscription table. Do not add the SDK package just for this design pattern.

Implementation gate: after CAS field propagation passes exact-head CI, extend the streamer and subscription service to reconcile a mapping of feed mode to instrument keys; replay each mode after reconnect; allow mode-specific subscribe/unsubscribe/change-mode; enforce Upstox limits per mode and any combined connection limit from current official docs; add reconnect, persistence, tenant isolation and API tests before scanner integration.


## Implementation follow-through — mixed-mode stream and Redis recovery — 30 October 2026

The per-mode registry and reconnect replay decision above has been implemented in the Tradepro Improved streamer and durable subscription service. Startup restores independent LTPC, Option Greeks and Full mode sets; reconnect fetches a fresh Analytics Token and a new authorized V3 WebSocket URL. Exact-head Backend CI #41060945704 passed on `f7c863977ed17a3d705b83db8dcc6b7ba421cccf`.

Redis consumer recovery hardening adds tests for volatile-data-loss epoch rollover and idle Pub/Sub PING/PONG heartbeat on head `a5e352bef2c78f27141b61bca5893fdfa0fd049a`; exact-head CI #41061518847 is pending. The official SDK remains an audit/reference, not a runtime dependency.

Remaining: worker-managed Redis consumer lifecycle, durable subscription discovery, single-owner coordination, graceful shutdown and scanner/PAPER integration. These are separate gates; do not claim them complete based on streamer or Redis primitive tests.
