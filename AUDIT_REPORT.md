# Tradepro Improved — Initial Audit and Change Plan

Audit target: imported code on main in this repository. The original Tradepro repository is read-only and is not modified.

## Classification (static inspection; runtime verification pending)

| Area / requirement | Classification | Evidence / notes | Action |
|---|---|---|---|
| Existing FastAPI APIs, SQLAlchemy models/repositories | Working but requires verification | Existing routes/models and tests are present | Preserve; run tests before broad refactors |
| Paper market orders | Working but incomplete | ExecutionService obtains real Upstox LTP and records simulated fills/costs; test coverage exists | Retain existing implementation; expand only with tests |
| Paper limit orders | Missing fill matcher | LIMIT is persisted as PENDING; no matcher observed in service/worker | Track as follow-up; do not claim fills are supported |
| Live order placement | Incomplete / disabled | Adapter has order API methods, but shared execution service always creates PAPER orders and does not reconcile broker fills | Keep live trading disabled pending full order lifecycle and safety work |
| Strategy activation | Defect identified | Worker filters active strategies, but manual /evaluate endpoint calls service directly; service lacked its own active check | Add guard in service and regression test |
| Daily strategy loss control | Partial | Existing strategy-level realized-loss check is present; portfolio-wide loss/exposure/order-frequency limits not observed | Retain existing tested logic; add broader controls only with design/tests |
| OAuth state validation | Incomplete | Authorization URL state is derived from connection ID; callback endpoint accepts a code and does not validate returned state | Must implement an unpredictable, expiring, one-time state flow before live use |
| Upstox instrument sync / streaming | Missing | Adapter explicitly returns not-implemented results for instrument sync and market-data streaming | Follow-up using official docs; no invented endpoints |
| Frontend home page | Suspected defect | frontend/app/page.tsx appears to render broker connection settings, duplicating the dedicated broker settings page | Verify intended dashboard requirements before replacing |
| Frontend lint command | Requires verification | package script uses next lint while Next.js dependency is version 16 | Verify in CI; adjust only after observing failure |
| Database migrations | Present, require execution verification | Alembic migration files exist | Run migration checks in a suitable environment before schema changes |

## Changes in this commit

1. Strategy evaluation now returns HOLD immediately when a strategy is inactive. This closes a bypass in the manual evaluate path without changing worker behavior or active-strategy behavior.
2. A regression test verifies an inactive strategy does not call the broker adapter.

## Deliberately retained

- Existing shared paper execution service, cost calculations, position math, risk engine, strategy engine, models, and routes are retained.
- No schema migration was needed for the inactive-strategy guard.
- Live trading remains disabled. No real orders are submitted as part of this work.

## Verification status

- Source-level inspection completed for the areas listed above.
- The new test is committed but has NOT yet been executed in this environment. No test/build success is claimed here.
- OAuth hardening, broker reconciliation, order deduplication, instrument sync, streaming, limit matching, portfolio-wide controls, and frontend dashboard correction remain open work items.
