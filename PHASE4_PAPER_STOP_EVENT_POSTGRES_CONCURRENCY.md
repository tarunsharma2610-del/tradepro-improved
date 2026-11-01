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


## Lifecycle and lease-recovery concurrency extension — 1 November 2026

Verified on exact head `aaf64fcf1431f7fa998d61c9cc3efd9b251437a6`, Backend CI #41097352266 SUCCESS.

Additional PostgreSQL 16 independent-session tests cover:

1. Two workers racing to reclaim one expired claim: exactly one rotates the token; the other loses without error.
2. Two workers racing an event at its retry limit: neither can exceed the attempt budget; the event is terminalized as FAILED.
3. Caller rollback after CLAIMED → EXECUTING restores the prior durable state and token.
4. Recovery of an expired EXECUTING lease rotates ownership; the stale worker cannot complete, while the new token can proceed.
5. Retryable delay and stale-token behavior are also covered by service-level tests.

These tests prove the implemented database state transitions under the CI PostgreSQL 16 service; they do not prove production multi-host reliability or authorize dispatcher/order integration.
