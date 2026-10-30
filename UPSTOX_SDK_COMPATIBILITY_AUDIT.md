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
| Subscription control | Async subscribe/unsubscribe/change-mode, key validation and limits | Equivalent control methods | Keep ours; no missing feature established |
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
