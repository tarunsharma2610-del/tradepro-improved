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
