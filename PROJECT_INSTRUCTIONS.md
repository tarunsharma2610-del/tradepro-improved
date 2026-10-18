# Tradepro — Existing Codebase Audit, Improvement and Live Trading Upgrade

## 1. Objective

Improve the existing Tradepro codebase to deliver a reliable, secure trading platform supporting both **Paper Trading and Live Trading through Upstox**.

Create the improved version as a separate project. Do not modify, overwrite, or break the original project.

**Important principle: Preserve working functionality. Do not rewrite working code or change existing behavior unnecessarily.**

The goal is to improve and complete the existing application, not rebuild everything from scratch.

## 2. Audit Before Making Changes

First, inspect the entire existing codebase, including:
- Backend APIs, services, models and database schema.
- Frontend pages, components and existing user workflows.
- Strategy engine, scheduler and background workers.
- Paper-trading and order-execution logic.
- Upstox authentication, market data and broker integration.
- Risk management, portfolio accounting and P&L calculations.
- Backtesting, notifications, logging, configuration and deployment.
- Existing tests, dependencies and documentation.

For every requirement in this document, classify the existing implementation as:

1. **Working and complete:** Meets the requirement and passes appropriate tests.
2. **Working but incomplete:** Some functionality exists but requires improvement.
3. **Broken or incorrect:** Exists but does not work reliably or correctly.
4. **Missing:** Not implemented.
5. **Requires verification:** Cannot be confirmed from static inspection alone.

Verify functionality through existing tests and targeted tests where practical. Do not assume something works simply because its code exists.

## 3. Change Policy — Mandatory

Follow these rules throughout development:

- If a feature already works correctly, meets the requirements and has adequate test coverage, **leave it unchanged**.
- If a feature is partially implemented, improve the existing implementation rather than replacing it unnecessarily.
- If a feature is broken, fix the underlying problem.
- If a feature is missing, implement it using the existing architecture wherever practical.
- Refactor working code only when there is a demonstrable benefit, such as correcting a security vulnerability, preventing trading errors, fixing architectural conflicts or enabling a required feature.
- Do not remove working functionality, change APIs or database structures unnecessarily, or introduce avoidable breaking changes.
- Do not add duplicate services, models, pages or integrations when suitable implementations already exist.
- Before changing shared components, identify what depends on them and test for regressions.
- Preserve existing data and provide safe, tested database migrations whenever schema changes are necessary.
- If a proposed change is unnecessary, document that it was reviewed and retained as-is.

**A requirement being listed in this document does not automatically mean the code needs to change. Change only what the audit demonstrates needs changing.**

## 4. Paper Trading and Live Trading

Support both modes using the existing implementation wherever possible.

### Paper Trading
- Continue using real market data with simulated order execution.
- Support applicable order types, pending orders, fills, cancellations, slippage, charges, positions and P&L.
- Keep paper balances, orders, positions and performance separate from live trading.
- Ensure paper orders can never reach the real broker.

Retain existing paper-trading components if they already satisfy these requirements.

### Live Trading
- Use the official Upstox API for authorized real order placement.
- Track broker-confirmed orders, fills, rejections, cancellations, positions, holdings and available funds where supported.
- Handle partial fills, timeouts, retries, token expiry, API errors and reconnection safely.
- Do not mark orders as executed until confirmed by the broker.
- Prevent duplicate orders during retries, worker restarts and repeated strategy evaluations.
- Keep broker-specific operations separate from strategy logic where practical.

Audit the current code first. Reuse any existing, correctly implemented live-trading components and build only the missing pieces.

## 5. Trading Mode and Safety

Implement or improve the following only where necessary:
- Clear Paper/Live mode selection and visible mode indicators.
- Separate paper and live strategy configurations.
- Explicit authorization and confirmation before enabling live trading.
- Appropriate confirmation before the first live order.
- No automatic conversion of paper strategies or orders into live trading.
- Configurable limits for order value, position size, daily losses, exposure and order frequency.
- Validation of available funds, instrument eligibility, lot size, tick size and supported order types.
- Duplicate-order prevention and broker-state reconciliation.
- A kill switch that stops new automated entries.
- Safe handling of open orders and existing positions during failures.
- Audit logs for important trading actions and configuration changes.

Do not duplicate or replace risk controls that are already correct and adequately tested. Extend them where there are gaps.

## 6. Strategies, Execution and Accounting

Review existing functionality before changing it.

Ensure the platform can:
- Create, edit, backtest, activate, pause and stop strategies.
- Check strategy activation and trading mode before generating orders.
- Attribute orders, trades and positions correctly to their portfolio and strategy.
- Apply risk checks before order submission.
- Handle entries, exits, stop-losses, targets and supported trailing-stop logic.
- Track pending, partially filled, rejected, cancelled and completed orders correctly.
- Calculate realized and unrealized P&L using reliable execution data.
- Account for brokerage, taxes and other applicable charges where supported.
- Keep paper results and live results separate.

Resolve existing model or database conflicts only when the audit identifies a real correctness problem. Preserve compatible existing structures wherever possible.

## 7. Upstox Integration

Audit the current Upstox integration and complete missing or defective functionality for:
- OAuth authorization and callback validation.
- Secure token storage and expiry handling.
- Instrument master and contract validation.
- Quotes, candles and WebSocket market data where supported.
- Order placement, modification, cancellation and reconciliation.
- Trade book, positions, holdings, funds and margin information where supported.
- Rate limits, network errors and reconnection handling.

Use current official Upstox documentation. Do not invent endpoints or claim support for features the API does not provide.

Keep any correctly working integration unchanged unless a specific defect or required improvement is demonstrated.

## 8. Risk, Security and Reliability

Verify and improve as required:
- Risk limits enforced by the backend before live order submission.
- Protection against stale market data, duplicate execution and runaway strategy loops.
- Secure handling of API credentials and access tokens.
- Proper authentication and authorization for sensitive actions.
- Validated OAuth state and callbacks.
- Safe logging without secrets or access tokens.
- Consistent order state after restarts and broker disconnections.
- Appropriate market hours, holidays and end-of-day handling.
- Monitoring, error reporting and recovery procedures.

Prioritize changes that prevent unauthorized orders, duplicate orders, incorrect accounting or uncontrolled financial losses.

## 9. Frontend and User Experience

Inspect existing pages before creating or replacing any.

Retain working pages and components. Fix or add only what is needed to provide:
- Clear Paper/Live mode status.
- Strategy and portfolio management.
- Orders, positions, holdings and trade history.
- Funds and margin information where available.
- P&L, trading costs and risk-limit status.
- Broker connection status and actionable error messages.
- Live-trading confirmation and emergency controls.

Avoid duplicate pages, unnecessary redesigns and changes to working workflows without a clear reason.

## 10. Testing and Regression Prevention

Before modifying the application:
- Record the current working baseline.
- Run existing tests and available frontend build, lint and type checks.
- Record pre-existing failures instead of attributing them automatically to new changes.

For each modification:
- Add or update targeted tests.
- Run the relevant existing tests.
- Run regression tests for dependent features.
- Verify that unaffected workflows still work.
- Test paper/live isolation and live-trading safety.

Use mocks or supported test environments for broker testing. Never place real orders merely to verify the implementation without explicit authorization.

Do not claim tests passed unless they were actually executed.

## 11. Implementation Workflow

Work in the following order:

1. Inspect the codebase and document the current implementation.
2. Create a requirements audit mapping each requirement to existing files, services and tests.
3. Identify actual gaps, defects, security risks and incomplete features.
4. Prepare a prioritized change plan with the reason for each proposed change.
5. Implement the smallest safe set of changes that satisfies the requirements.
6. Test each change and check for regressions.
7. Review the completed application against every requirement.
8. Document what was retained unchanged, what was improved, what was added and what remains incomplete.

Keep the original project untouched and work only in the separate new project or branch designated for the improved version.

## 12. Required Deliverables

Provide:
- The separate improved codebase.
- An audit report showing which requirements were already satisfied.
- A change log explaining each meaningful modification and why it was necessary.
- A list of existing functionality deliberately retained unchanged.
- Test results, including any failures or unverified areas.
- Database migration and deployment instructions where applicable.
- A list of remaining limitations and manual configuration steps.
- Confirmation of which Paper Trading and Live Trading capabilities are actually implemented and verified.

## Final Instruction

**Audit first, preserve what works, fix what is broken, improve what is incomplete, and build what is missing. Do not rewrite the project merely to follow this specification.**

Correctness, security, financial safety and regression prevention take priority over unnecessary refactoring or adding more code.

Live Trading must remain disabled until its broker integration, risk controls, order reconciliation, security checks and relevant end-to-end tests have been verified. Enabling real trading requires explicit user authorization.


## Continuation checkpoint — 18 October 2026

Before starting any continuation, read the latest authoritative checkpoint at the end of `MASTER_ROADMAP.md`, `PROGRESS.md`, `AUDIT_REPORT.md`, and `HANDOVER.md`. Do not restart a task already marked completed. The latest roadmap task was a real-service integration test for the existing reconcile-before-promote coordinator—not creation of another coordinator. Continue by checking the latest code commit and CI result, fixing only demonstrated failures, then update the checkpoint files with verified evidence. Keep live trading disabled, do not call order-write endpoints, do not merge PR #1, and do not touch the original `Tradepro` repository.

 
### Superseding checkpoint — integration tests now exercise fresh intake

The integration test was refined in commit `4d8941f436bed1f61b46c4123a4a7c6d5c6b6f88` so each scenario starts with no staged trade rows; the real ingestion service must insert broker-returned trades before status reconciliation/promotion. This supersedes the earlier test-only SHA `b5783d421f64fcb8e7f1d75f1af5185fd9029f59`. CI remains unverified; check the latest commit before claiming the task complete.

## Superseding verified checkpoint — 18 October 2026: real-service fill reconciliation integration

### Exact verification evidence
- Latest tested code/test SHA: `c779f2543ea1f20efbd8b7dca38a9c2aed201749`.
- GitHub Actions [run #39118955335](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39118955335): **success**. Full suite: **385 passed, 1 skipped, 1 warning in 34.01s**. SQLite migration upgrade passed, PostgreSQL 16 migration upgrade passed, and PostgreSQL concurrency integration passed (**1 passed in 0.35s**).
- This exact-head run verifies the fresh-ingestion integration test refinement from commit `4d8941f436bed1f61b46c4123a4a7c6d5c6b6f88` and fixes for nondeterministic child order assertions and deleted ORM fixture access.
- The real-service integration test now begins with no staged trade rows: mocked Upstox trade reads must be inserted by the real `BrokerTradeIngestionService` before official status reconciliation and promotion. Repeated reconciliation/promotion is idempotent; sibling status failure prevents any fill accounting; charge-estimate failure creates no Execution/LivePosition rows; paper cash/positions and parent Order state remain unchanged.
- PostgreSQL 16 verifies migration compatibility and concurrent charge adjustments/fill promotion. Lock scoping explicitly avoids PostgreSQL's `FOR UPDATE` nullable outer-join error.

### Release status and caveats
- All broker API responses in tests are mocked. No live Upstox API requests or real orders were sent.
- The coordinator, fill promotion and charge-adjustment services remain unregistered in order routes/workers. Live order submission remains disabled.
- Frontend build/staging, real broker contracts, exchange holiday coverage, operational monitoring, account-level kill switch and broker-error circuit breaker remain outstanding. PR #1 remains draft/open/unmerged; original `Tradepro` untouched.

### Next distinct task
Implement and test the **persisted account-level live kill switch and broker-error circuit breaker**: durable state, fail-closed read behavior, reason/timestamp/audit trail, threshold-triggered circuit trips, manual-reset policy and account-wide scope across portfolios. Keep it unregistered from order submission until separately reviewed; do not merge PR #1 or enable live trading.

This checkpoint supersedes prior notes saying CI for `4d8941f436bed1f61b46c4123a4a7c6d5c6b6f88` was pending. The latest verified test SHA is `c779f2543ea1f20efbd8b7dca38a9c2aed201749`.
