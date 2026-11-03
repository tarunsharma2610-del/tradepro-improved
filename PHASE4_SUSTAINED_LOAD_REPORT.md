## Current verified Phase 4 checkpoint — 3 November 2026

- Repository: `tarunsharma2610-del/tradepro-improved` only; implementation branch: `phase4/operational-alerting`.
- Verified implementation commit: `e4910f3c93d556bf2c7c7d71df4a6b9f045a1f36`.
- Backend CI [#41669605371 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41669605371): **1,650 passed, 8 warnings**; broker-write boundary guard passed; SQLite and PostgreSQL 16 migration round-trips passed; synthetic PostgreSQL/document-volume restore drill passed.
- Security analysis [#41669605381 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41669605381): CodeQL and Python dependency audit passed.
- Durable PAPER stop-event process recovery remains verified by `test_sigkilled_execution_worker_recovers_paper_stop_without_redis`: a separate worker process is killed after the production claim commit; PostgreSQL-only recovery completes the event, rejects the stale token, and leaves one filled PAPER order/execution, a flat position and one cash mutation.
- Host watchdog now enumerates all Compose worker containers with `docker compose ps --all -q worker`, inspects each container, and reports `running`, `degraded`, `down`, or `unknown` fleet state. Tests cover mixed running/stopped replicas, all-stopped replicas, incomplete inspection, and restart-count transitions. These are unit tests with mocked Docker responses; a real Docker Compose multi-container fault drill and Oracle VM installation remain pending.
- PR #12 remains **OPEN, Draft, and unmerged**. No merge or live broker order-write enablement is authorized.
- Safety remains mandatory: PAPER-only; live broker `place_order`, `modify_order`, and `cancel_order` writes disabled; original `tarunsharma2610-del/Tradepro` untouched.
- Remaining Phase 4 gates: real multi-container/replica failure injection; realistic sustained load using full database handler work (not just dispatcher throughput); Oracle VM watchdog installation and failure drill; independent cloud/VM monitoring; final independent security/penetration review. CI is not production-scale performance certification or deployment sign-off.

Historical checkpoint notes below are retained as history; this section supersedes older "next step", test-count, commit, and PR-number summaries.
## Current verified Phase 4 checkpoint — 3 November 2026

- Repository: `tarunsharma2610-del/tradepro-improved` only; implementation branch: `phase4/operational-alerting`.
- Verified implementation commit: `b91a03b7ee70fcf4392bb4c4bcde783185ea1c24`.
- Backend CI [#41667865847 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41667865847): **1,647 passed, 8 warnings**; broker-write boundary guard passed; SQLite and PostgreSQL 16 migration round-trips passed; synthetic PostgreSQL/document-volume restore drill passed.
- Security analysis [#41667865822 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41667865822): CodeQL and Python dependency audit passed.
- New verified fault-injection coverage: `test_sigkilled_execution_worker_recovers_paper_stop_without_redis` starts a separate Python worker process on PostgreSQL 16, waits for the production claim path to commit and enter execution, kills that OS process, and recovers the event from PostgreSQL without Redis redelivery. It verifies a new claim token, rejection of the killed worker's stale token, exactly one filled PAPER order and execution, a flat position, and one cash-balance mutation.
- Existing Redis market-data worker process-kill/restart coverage, concurrent duplicate stop execution, indicator-exit/stop-event race, lease recovery, and database-level replay tests remain in place; this new test fills the distinct stop-execution process-crash gap rather than duplicating them.
- PR #12 remains **OPEN, Draft, and unmerged**. No merge or live broker order-write enablement is authorized.
- Safety remains mandatory: PAPER-only; live broker `place_order`, `modify_order`, and `cancel_order` writes disabled; original `tarunsharma2610-del/Tradepro` untouched.
- Remaining Phase 4 gates: multi-container/replica failure injection; realistic sustained load using full database handler work (not just dispatcher throughput); Oracle VM watchdog installation and failure drill; external VM monitoring; final independent security/penetration review. The current CI suite is not production-scale performance certification or deployment sign-off.

Historical checkpoint notes below are retained as history; this section supersedes their older "next step", test-count, commit, and PR-number summaries.
# Phase 4 Sustained Dispatch Benchmark — 3 November 2026

## Verified checkpoint

- Repository: `tarunsharma2610-del/tradepro-improved` only.
- PR #10: OPEN, Draft, unmerged.
- Exact verified head: `edec040c5bb43ea572419345c5ecd50b76ab1c86`.
- Backend CI #41645265983: SUCCESS on the exact head.
- Security CI #41645266170: SUCCESS on the exact head; CodeQL and dependency audit passed.
- Backend pytest: 1,632 passed, 8 warnings.
- Broker-write boundary guard passed.

## Concurrent dispatcher smoke benchmark

The retained `dispatch-benchmark-results.json` artifact reports:

| Measurement | Result |
|---|---:|
| Observations processed | 5,000 |
| Concurrent workers | 8 |
| Bounded queue capacity | 512 |
| Elapsed time | 0.044279 seconds |
| Synthetic throughput | 112,920.26 observations/second |
| p50 enqueue-to-handler latency | 3.2393 ms |
| p95 enqueue-to-handler latency | 4.3143 ms |
| p99 enqueue-to-handler latency | 4.4683 ms |
| Backpressure retries/rejections | 21 / 21 |

All 5,000 observations were eventually accepted and processed; queue and in-flight state returned to zero. Backpressure retries are expected behavior under a bounded queue and are not equivalent to permanently lost accepted observations.

## Interpretation and limitations

This is a short, synthetic in-process dispatcher/worker smoke benchmark on a GitHub-hosted runner. It is useful as a regression baseline for this test shape only. It does NOT measure Upstox network ingestion, PostgreSQL persistence, scanner-to-execution end-to-end latency, long-duration memory behavior, production throughput, or Oracle VM capacity. Do not use the throughput figure as a production SLA or capacity claim.

A production-relevant benchmark still needs longer steady-state runs, realistic producer rates, realistic handler/database work, multiple user/instrument distributions, queue pressure/recovery, CPU/memory measurements and p50/p95/p99 end-to-end latency.

## Operational alerting status

The inspected deployment compose stack contains PostgreSQL, Redis, backend, worker, frontend and Nginx; it does not currently define Prometheus, Alertmanager or an independent notification service. The application exposes admin-only Redis-aggregated PAPER dispatch counters and a 60-second active-worker heartbeat window, but no independently delivered operational alerts are verified.

Initial alert design candidates (not production-approved thresholds): missing worker heartbeat >60 seconds; Redis unavailable for three consecutive probes; handler failure streak >=5; queue occupancy >80% for 60 seconds; stale quote beyond its configured freshness limit. Alert delivery must be independent of the worker being monitored and must have retry/persistent-failure handling.

## Remaining Phase 4 work

1. Implement and test independent alert delivery and alert failure recovery.
2. Complete endpoint-by-endpoint authorization/IDOR and cross-user isolation audit.
3. Continue multi-replica crash-window and sustained-load testing with realistic handler work.
4. Synchronize maintained project documentation and verify the exact documentation head with Backend and Security CI.
5. Complete the final Phase 4 audit. Do not claim LIVE readiness or production security certification.

## Safety

PAPER remains mandatory. Live broker `place_order`, `modify_order`, and `cancel_order` writes remain disabled. PR #9 and PR #10 remain Draft/unmerged. Original `tarunsharma2610-del/Tradepro` is out of scope and untouched.


## Endpoint authorization and PAPER/LIVE audit addendum — 3 November 2026

### Scope and inspected routes

Source-reviewed the versioned API routers for portfolios, strategies, backtests, broker charge evidence, reconciliation, settings, users, and Upstox charge APIs. The review focused on authentication dependencies, owner scoping, child-resource lookups, admin-only operations, and execution-mode checks.

### Verified safeguards in source and existing regression tests

- Portfolio lookup is scoped through `PortfolioRepository.get_for_user(user.id, portfolio_id)`; child position/order/execution and broker snapshot reads occur only after the portfolio ownership check.
- Strategy routes first verify portfolio ownership; strategy reads/updates/deletes/evaluation are constrained to the route's portfolio. Activation also verifies PAPER mode.
- Backtest list/get/trades/delete operations use user-scoped repository methods.
- Broker connection and Analytics Token settings are user-scoped; credential/token values are not returned in API responses.
- Broker charge evidence is joined to the owning broker connection; cross-user access returns not found. Cross-user review is restricted to platform admins, and review also requires a different reviewer from the extractor.
- Reconciliation queries are filtered by the authenticated user's ID.
- Platform settings require the admin dependency.
- Upstox charge operations resolve the connected token through the authenticated user's broker connection.
- Existing API isolation tests cover cross-user portfolio, strategy, backtest, pending-order cancellation, broker evidence/reconciliation, broker credentials/tokens, market-data stream state, and OAuth callback state.
- Existing PAPER/LIVE tests verify immutable trading mode, LIVE order rejection before broker access, LIVE strategy activation denial, fail-closed LIVE positions/balances, and broker allocation constraints.

### MFA defect fixed in separate Draft PR #11

Source review found `mfa_verify` and `mfa_disable` called `response.delete_cookie` without accepting FastAPI's `Response` parameter. The route signatures now inject `Response`, and HTTP-level tests cover cookie clearing after MFA enable and disable.

- PR #11 head: `c11dc9de719a3fb417a0c9760b2cff944aed4d7a`.
- Backend CI #41646429604: SUCCESS; 1,633 tests passed, 8 warnings; broker-write boundary guard passed.
- Security CI #41646429541: SUCCESS; CodeQL and dependency audit passed.
- PR #11 remains Draft and unmerged.

### Audit limits / remaining review

This is a focused source-and-regression-test review, not a formal penetration test, independent security assessment, or certification. It does not establish that every deployment secret, reverse-proxy rule, cloud IAM policy, network ACL, database role, backup, or runtime host is correctly configured. Continue testing authorization against deployed PostgreSQL and multi-user sessions, review rate limits and file upload/storage boundaries, and run independent security testing before any public or LIVE use.

### Safety

PAPER remains mandatory. Live broker `place_order`, `modify_order`, and `cancel_order` writes remain disabled. PRs #9, #10, and #11 remain Draft/unmerged. Only `tradepro-improved` is in scope; original `Tradepro` is untouched.


## MFA factor replacement hardening — 3 November 2026

A deeper authentication review found that an authenticated user could call MFA enrollment while MFA was already enabled; the service would overwrite the stored encrypted secret without verifying the existing factor. This could permit replacement of an active factor from a compromised authenticated session.

### Correction submitted in Draft PR #11

- `AuthService.start_mfa_enrollment` now rejects replacement when `user.mfa_enabled` is true.
- The API maps the service rejection to HTTP 409 Conflict.
- Existing-factor replacement requires the user to prove the current factor through the password + TOTP disable flow before enrolling again.
- Added service-level regression coverage proving the encrypted original secret is unchanged.
- Added HTTP regression coverage proving an authenticated session cannot replace an already-enabled factor without disabling it through the protected flow.

Latest PR #11 head: `8061500a90ec4a3aeaa52cce51f850773ef0414e`. New backend and security CI are running; do not transfer the previous head's green status to this commit. Previous exact-head verification at `c11dc9de719a3fb417a0c9760b2cff944aed4d7a` passed (1,633 backend tests, 8 warnings; CodeQL and dependency audit passed), but is superseded by the new factor-replacement hardening commit.

### Remaining MFA review

Review enrollment pending-state expiry, TOTP attempt throttling, recovery codes, notification of security-factor changes, and deployment/session revocation behavior. Do not claim MFA security is fully complete based on these fixes alone.


## MFA enrollment password step-up — latest Draft PR #11 update

A third MFA hardening step now requires password reauthentication before initial enrollment. The service validates the password before generating or storing a new TOTP secret; the API returns 401 on incorrect password. Already-enabled factors continue to be non-replaceable from enrollment and return 409; replacement requires the existing password + current TOTP disable flow first.

Regression tests cover wrong-password rejection with no secret persisted, correct-password enrollment, and prevention of replacing an enabled factor. The API enrollment contract now requires a JSON password field.

Latest PR #11 head: `10657cf099aaed17c7d4a18f2878ebd4d48f9f1a`. Backend CI #41648211858 is running and Security CI #41648211953 is queued. Previous green checks apply only to earlier PR #11 heads and do not verify this update. MFA remains under review; recovery codes, pending enrollment expiry, attempt throttling, and security-change notifications are not yet verified.


## Exact-head MFA verification — 3 November 2026

Draft PR #11 MFA hardening is now verified on its latest head `10657cf099aaed17c7d4a18f2878ebd4d48f9f1a`.

- Backend workflow #41648211858: SUCCESS — 1,637 passed, 8 warnings; broker-write boundary guard passed.
- Security workflow #41648211953: SUCCESS — CodeQL and Python dependency vulnerability audit passed.
- PR #11 remains Draft/unmerged.

The changes require password reauthentication for initial MFA enrollment, reject replacement while an MFA factor is enabled, and inject FastAPI Response so MFA enable/disable can clear browser cookies. Earlier failed backend runs on intermediate commits are superseded by this exact-head green result.

Documentation checkpoint before this addendum was verified on `22570af88916ea2c940831051ed429da5a701319` (Backend #41648348189 and Security #41648348210 both SUCCESS). This addendum creates a new documentation commit and therefore requires fresh exact-head CI before it becomes a verified checkpoint.


## Operational alerting implementation — 3 November 2026

Draft PR #12 adds a PAPER worker-fleet alert monitor and admin-configured Telegram delivery. See `PHASE4_OPERATIONAL_ALERTING.md` for conditions, thresholds, configuration, tests, failure semantics, and remaining deployment gates.

- Alerts: dropped unique observations, exhausted dispatch retries, ≥5 handler failures per interval, ≥25 rejected observations per interval, no worker heartbeat for ≥60 seconds, and unavailable shared metrics; recovery notification on heartbeat return.
- Poll interval: 30 seconds; Redis-backed per-fingerprint cooldown: 300 seconds. Process-local cooldown is used if Redis is unavailable; cross-replica dedupe is not guaranteed during Redis outage.
- Admin-only encrypted platform key added: `ops_alert_telegram_chat_id`; configure it alongside `telegram_bot_token` through Settings → Platform.
- Monitor runs as an independent worker task. Delivery is best-effort and must not block/rollback PAPER execution.
- Automated tests cover threshold deltas, aggregate-only content, Telegram delivery/dedupe, invalid destination and missing-worker threshold.

PR #12 head is subject to exact-head Backend and Security CI. A successful CI run does not prove live Telegram delivery; a credentialed deployment smoke test and multi-replica fault-injection remain required. PAPER-only and broker-write restrictions remain unchanged. PR #12 is Draft/unmerged.


## Operational alert follow-up — 3 November 2026

Code review found and fixed a cooldown edge case: missing/invalid Telegram configuration previously could leave a Redis dedupe key active for the full five-minute cooldown. The monitor now releases that key so correcting the admin destination allows immediate retry. Added automated tests for two independent monitor instances sharing Redis (only one notification is sent for the same fleet delta) and configuration correction/retry without waiting for cooldown.

See `PHASE4_OPERATIONAL_ALERTING.md`. Latest alert code commit before this documentation sync: `4f7829a8019758b9eb0fc770dcae80d9cbb1c428`. Backend and Security CI are running for the code follow-up; this documentation sync itself will trigger fresh exact-head workflows. Do not treat earlier green CI as verification of these new tests. Worker heartbeat remains an exporter heartbeat only; external monitoring is required to detect total container/process loss.


## External worker watchdog — 3 November 2026

Added host-side watchdog files:
- `ops/worker_watchdog.py` inspects the Compose worker state and Docker restart count from outside the worker container.
- `ops/systemd/tradepro-worker-watchdog.service` and `ops/systemd/tradepro-worker-watchdog.timer` run the check as a root-owned oneshot each minute.
- `ops/worker-watchdog.env.example` documents an optional HTTPS incident webhook; real URLs/credentials must remain in a root-owned 0600 host file.
- `backend/tests/test_host_worker_watchdog.py` covers running/missing/unavailable Docker, state/restart transitions and HTTPS-only webhook enforcement.
- `PHASE4_EXTERNAL_WATCHDOG.md` is the installation runbook; `PHASE4_OPERATIONAL_ALERTING.md` records the integration boundary.

The watchdog only observes Docker state; Docker's existing restart policy remains responsible for restart. It does not call broker APIs. It is not installed on the Oracle VM yet. Without an HTTPS webhook, notifications remain in the host journal. VM/Docker daemon/systemd failure still requires independent cloud-provider instance monitoring. One-minute polling may miss short transient states, although Docker restart-count changes are detected.

Latest implementation commit before documentation synchronization: `996ccbcd9f52d539e17912940ce690ab9b9fa2d5`. Backend and Security CI were triggered on that commit; final documentation synchronization requires its own exact-head CI. Do not mark this checkpoint verified until both workflows pass on the final docs head.

PAPER-only remains mandatory; live broker `place_order`, `modify_order`, and `cancel_order` writes remain disabled. PR #12 remains Draft/unmerged; original `Tradepro` remains untouched.


## Real Redis multi-client alert test — 3 November 2026

Added a CI-backed integration test using two independent Redis clients against the workflow's Redis 7 service. Both concurrently attempt the same unique alert fingerprint via atomic Redis `SET NX EX`; exactly one claim and one Telegram send are required. See `PHASE4_OPERATIONAL_ALERTING.md`. This is stronger than the in-memory fake but does not replace multi-container fault injection or a credentialed Telegram deployment smoke test. Backend and Security CI must pass on the final documentation head before checkpoint verification.


## PostgreSQL worker-loss recovery test — 3 November 2026

Added a PostgreSQL 16-backed recovery-sweeper test for an expired EXECUTING PAPER stop event. It simulates worker loss after the claim transaction is committed, invokes the real expired-event sweeper without Redis redelivery, verifies claim-token rotation, and completes the durable event using the replacement token. The broker-facing execution method is stubbed; this test does not submit orders. See `PHASE4_PAPER_STOP_EVENT_POSTGRES_CONCURRENCY.md`.

This is a DB-backed recovery integration test, not an OS-level worker SIGKILL or a full end-to-end order-fill test. The prior PostgreSQL concurrency cases remain in place. The stop-event model docstring was corrected to reflect worker ownership. Exact-head Backend and Security CI must pass after the final documentation sync.


Follow-up test-harness correction: the stubbed `execute_claimed` method now uses an instance-method-compatible signature, so the PostgreSQL recovery-sweeper test exercises the handler call shape correctly. This creates a new exact-head CI requirement; previous runs on earlier commits do not verify this final correction.


## PostgreSQL recovery verification update — 3 November 2026

- Backend CI run [#41659743611](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41659743611) and Security analysis [#41659743654](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41659743654) both PASSED on exact commit `319cf01dedd3b8bb861d6d60f010f96b08e9697e`.
- Backend and Security results above validate the lease-timeline harness correction, but do not validate subsequent commits.
- Added an explicit PostgreSQL integration assertion that the original worker's claim token cannot complete the event after recovery and replacement-worker completion. This is committed as `794af153daa6d331d28a5e4aa7b3d3249de1a09e`.
- Exact-head Backend and Security CI for `794af153daa6d331d28a5e4aa7b3d3249de1a09e` and this documentation synchronization are required before declaring a verified checkpoint.
- Scope remains `tarunsharma2610-del/tradepro-improved` only. PAPER-only; live broker order writes disabled; PR #12 OPEN, Draft and unmerged; original `Tradepro` untouched.
- This DB-backed worker-loss simulation is not an OS-level SIGKILL or Oracle VM failure drill. External watchdog installation, real VM failure drill, sustained production-like load, and final security audit remain pending.


## Verified PostgreSQL recovery checkpoint — 3 November 2026

- Exact documentation and implementation head: `49f058614eb8ab02acb9a24b6870aaf7e17a83da`.
- Backend CI [#41664985664 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41664985664): **1,646 passed, 8 warnings**; broker-write boundary guard passed; PostgreSQL 16 migration/restore checks completed successfully.
- Security analysis [#41664985706 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41664985706): CodeQL and Python dependency vulnerability audit passed.
- The PostgreSQL recovery-sweeper test now also asserts that the original claim token cannot complete the event after the replacement worker has completed it.
- The test simulates worker loss by closing the original DB transaction and advancing the persisted lease timeline; it is not an OS-level process kill. Next reliability gate: isolated multi-process worker termination/restart against PostgreSQL 16, with a real SIGKILL/SIGTERM fault window and verification of one durable PAPER outcome, no duplicate ledger mutation, and stale-token rejection.
- Additional pending gates: Redis/worker multi-container failure injection; sustained production-like load with realistic DB handler work; Oracle VM watchdog installation and failure drill; external VM monitoring; final independent security/penetration review.
- Repository scope: `tarunsharma2610-del/tradepro-improved` only. PR #12 is OPEN, Draft and unmerged. PAPER-only remains mandatory; live broker order writes remain disabled; original `Tradepro` untouched.
