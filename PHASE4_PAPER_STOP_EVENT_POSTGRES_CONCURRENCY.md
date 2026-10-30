# Phase 4 — PostgreSQL 16 PAPER stop-event claim concurrency

Date: 30 October 2026

## Test scope

Added PostgreSQL-only multi-session tests in `backend/tests/test_paper_stop_event_claim_postgres_concurrency.py`. Both tests use independent SQLAlchemy sessions, a two-worker thread pool and a synchronization barrier. They use the CI-provisioned PostgreSQL 16 service via `TEST_POSTGRES_URL`, create uniquely identified fixtures, and delete only their own rows. They do not drop shared database tables.

1. **Same quote identity race:** two workers race the same strategy/event/epoch/version. Required outcome: exactly one durable CLAIMED row and one duplicate/no-claim result; no unexpected exception; persisted claim token and attempt count exactly one.
2. **Distinct quote versions:** two workers race different quote versions for the same strategy/epoch. Required outcome: both durable claims survive serialization, with distinct versions and tokens.

## Existing lock behavior under test

The claim service locks portfolio → strategy → position. The portfolio row is the common serialization point for claims in one portfolio, while the database unique constraint remains the final duplicate identity guard. This test provides PostgreSQL evidence for those two properties; it is not a proof of multi-host production reliability or lease recovery.

## CI

Backend CI already provisions PostgreSQL 16 and exports `TEST_POSTGRES_URL`; the new file is auto-discovered by pytest. A successful exact-head CI run is required before accepting the concurrency milestone.

## Safety

Tests create only synthetic PAPER-domain database rows. No dispatcher integration, order creation, broker API call, live write, deployment or PR merge is included.
