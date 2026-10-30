<!-- Phase 3 checkpoint update — 27 Oct 2026. Latest code/test head 8feeb0cbb0c35e1e37012302c9075d43f1f33eb1 passed Backend CI #40458822529: 1,097 passed, 1 warning. Broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore and evidence retention passed. DP completeness checks require a consistent KNOWN + explicit valid finite nonnegative paise-exact amount, or NOT_APPLICABLE + no amount; invalid status, UNKNOWN-with-amount, KNOWN-without-amount, NOT_APPLICABLE-with-amount, NaN, negative and fractional-paise amounts fail closed. DP canonical manifests are checked against persisted broker trade → child order → local order mappings; only mapped equity-delivery SELL fills are accepted. Delivery SELL still requires reviewed/reconciled DP evidence and durable per-fill allocation; DP is included once in total and replay identity. Maintained docs are being synchronized after the green code run; exact-head CI on the final docs/checkpoint commit must pass before it is called green. PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled; original Tradepro repository out of scope. -->

## GST/IPFT statutory-engine implementation update — 26 October 2026 (code/test CI passed; docs head must be checked)

- Added `backend/app/services/statutory_stock_broking_gst.py` and `backend/tests/test_statutory_stock_broking_gst.py` on the current Phase 3 branch. The service implements CGST Act section 15's default taxable valuation, conditional CGST Rule 33 pure-agent exclusion requiring every evidence flag, and IGST Act section 12(12) recipient-location/fallback state selection for IGST versus CGST+SGST.
- Service/test changes are in commits `dcad71e148b89a2c384631b36090008c8fad193e` and `037ad2da02dca34c399e0ec454674c50ae65b5a7`, included in the verified checkpoint head above. Exact-head Backend CI [#40375335160 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40375335160) passed on checkpoint head `cc2d591cf74daea5d68b6ba704ae87a342cc96fd`: **1,051 passed, 1 warning**. Broker-write guard, SQLite/PostgreSQL 16 migration round-trips and synthetic restore drill passed. Later documentation commits are newer and still require exact-head CI verification.
- The statutory engine is a separate primitive and is not yet wired into actual per-fill accounting. It does not infer Rule 33 pure-agent status from a charge label; absent complete evidence, third-party recovery lines remain in the section 15 base. It keeps the Upstox published-schedule estimate separate from statutory valuation and does not override the unresolved API sample discrepancy.
- Regression coverage added for combined/separate exchange/IPFT values in the taxable base, Rule 33 all-conditions gate, same-state versus cross-state tax type, recipient-state fallback, invalid/missing money, duplicate line names, and paise rounding. Intra-state CGST/SGST tax heads are rounded independently to paise and the returned total equals the two heads.
- Remaining gates: run exact-head backend CI and fix failures; independently review tax-head rounding and legal policy; implement product/broker effective-dated mapping and IPFT resolver; complete DP/demat persistence + total reconciliation; integrate only reviewed policy paths; synchronize this checkpoint again to the final CI-verified head. Actual per-fill invoice evidence remains deferred until source records/deployment exist; no personal contract note is required.
- Official source basis: [CBIC stock-broking FAQ](https://cbic-gst.gov.in/sectoral-faq.html), [CGST Act section 15](https://cbic-gst.gov.in/hindi/CGST-bill-e.html), [Upstox Brokerage Details API](https://upstox.com/developer/api-documentation/get-brokerage/), and [Upstox public charges](https://upstox.com/brokerage-charges/).
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; PR #6/#7 Draft and unmerged; PAPER-only; live broker writes disabled; original `Tradepro` untouched.
## Latest authoritative checkpoint — 26 October 2026, 21:06 IST

This section supersedes earlier statements in this file that identify an older commit or CI run as the latest checkpoint. Historical entries below are retained for audit history.
- **Verified Phase 3 correction — 26 Oct 2026, 22:45 IST:** backend CI [#40366645906 PASSED](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40366645906) on code head `f9d302fce03e504985e96582a7af71b14fd89f28`: 1,034 passed, 1 warning; broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, and synthetic restore drill passed. Fix: DP/demat optional amount now reads from `optional_canonical_components`; live snapshot materialization remains limited to the core six-component map. This green run verifies the correction, not completion of GST/IPFT acceptance. Current work remains Phase 3; PR #7 Draft/unmerged, PAPER-only, live writes disabled.

- **Latest GST/IPFT working update — 26 Oct 2026:** working branch is `phase3/cross-broker-gst-ipft-resolution`, PR #7 remains Draft/unmerged. A failed backend run #40365836710 (46 failed, 988 passed) exposed a DP/demat optional-component `KeyError` because the allocation planner read the six-component amount map for an optional amount. Fixes on the current branch separate `optional_canonical_components` and make the allocation planner read that map for DP/demat; snapshot materialization iterates only the six-component canonical source map. Latest code change at time of update: `c0607aff672a9792410513e7564cd5f3c8d7f371`. Exact-head CI has not yet been confirmed; this is not a green checkpoint. Do not claim success until the current head's backend tests and safety/migration checks pass. PAPER-only; live broker writes remain disabled; do not modify original `Tradepro`.


- **Only target repository:** [tarunsharma2610-del/tradepro-improved](https://github.com/tarunsharma2610-del/tradepro-improved). Branch: `phase3/durable-per-fill-charge-allocation`. Latest documentation commit before this sync: `73c4a7cdcde4490bd520d5e75cc87fe1b4ffa310`. Exact-head documentation CI [#40346810442 PASSED](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40346810442).
- GST estimate implementation commit `b75a97f6cd0043c185375cc253b84a1e6d6bfea1`; exact-head CI [#40345937942 PASSED](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40345937942): 1,012 tests passed, 1 warning. Broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic restore/evidence-retention checks passed.
- **GST estimate decision:** apply 18% to brokerage + combined exchange transaction/IPFT charge exactly once; include explicit demat/DP charges additionally for equity delivery. Do not add STT, stamp duty, SEBI or trade notional to this published GST estimate base. Upstox's Brokerage Details API sample arithmetic conflicts with the explicit public schedule; the sample does not override the schedule or prove live billing is wrong. Sources: [Upstox pricing](https://upstox.com/brokerage-charges/), [Brokerage Details API](https://upstox.com/developer/api-documentation/get-brokerage/), [Trades Charges API](https://upstox.com/developer/api-documentation/get-trade-charges/), [NSE transaction/IPFT circular](https://nsearchives.nseindia.com/content/circulars/FA73061.pdf).
- **New Phase 3 gap found:** `demat_transaction_charges` is intentionally blocked by source-to-canonical mapping; canonical live accounting and `Execution` currently support six components only. Equity-delivery actual-charge accounting with a DP/demat charge is therefore not accepted yet. The estimate helper can include a demat amount, but that does not mean actual accounting can persist/reconcile it. Keep this fail-closed; do not drop DP charges or fold them into another component. Next implementation gate: product-aware canonical demat/DP component and total-charge persistence, migration, idempotency, allocation, and delivery/non-delivery regression tests—or keep delivery actual accounting unsupported until complete.
- Actual per-fill GST/invoice acceptance remains evidence-gated. Public schedules and calculators support estimates, not account-specific actuals; aggregate API values and null fields are not per-fill invoice proof. User is not required to provide a personal contract note. Actual tariff candidates remain DRAFT.
- Phase 3 remains IN PROGRESS; PR #6 remains open/draft/unmerged. PAPER mandatory; live broker order writes, automatic live-fill promotion and automatic scheduling remain disabled. Original `tarunsharma2610-del/Tradepro` must not be modified. AI/Algory integrations remain deferred until Phase 3 acceptance.

---

## Historical checkpoint (superseded) — 26 October 2026 (latest verified CI)

- Target repository only: `tarunsharma2610-del/tradepro-improved`; branch `phase3/durable-per-fill-charge-allocation`; implementation/test head `44830ec48b50b4f470ec9ca95dd2d3f4339dd3df`. Do not modify original `Tradepro`.
- Exact-head Backend CI: [run #40294178677 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40294178677), including the test separating NSE/IPFT arithmetic reconciliation from GST taxable-base approval.
- GST estimate helper accepts exactly 18%; tests reject 0%, 5%, 100%, and 100.01%. Rate guard does not approve taxable-base composition; component inclusion needs reviewer and invoice/source evidence.
- ₹307/crore versus ₹306.99/crore transaction charge + ₹0.01/crore IPFT is arithmetic reconciliation only, not GST-base approval.
- Canonical live-fill integration is verified: six independently verified charge snapshots, evidence revalidated under lock, no raw-only fallback; brokerage cap applied once before deterministic paise-exact allocation.
- Remaining Phase 3 gates: effective-dated tariff applicability; component-specific per-fill allocation acceptance; invoice/source-backed GST/IPFT and product/segment evidence; adversarial/migration/recovery review; final exact-head docs/sign-off.
- Upstox public schedules/calculator are estimates; aggregate charges endpoint is not actual per-fill evidence. Null remains unknown, not zero. Synthetic restore is not actual Oracle recovery.
- PAPER mandatory; live broker writes, automatic live-fill promotion and automatic scheduling disabled. PR #6 open/draft/unmerged unless explicitly approved. Defer AI/open-source adaptations until Phase 3 acceptance. Documentation commit needs its own CI.

---

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

## Canonical maintained checkpoint-document inventory — 25 October 2026

The maintained checkpoint inventory contains **18 living documents**. The prior 14-document list accidentally omitted the Upstox API policy, SDK/repository audit, Agent Skill security review, and charge-rule source register. These four are now included in the checkpoint inventory.

1. `PROGRESS.md`
2. `HANDOVER.md`
3. `MASTER_ROADMAP.md`
4. `ROADMAP.md`
5. `PROJECT_INSTRUCTIONS.md`
6. `AUDIT_REPORT.md`
7. `ARCHITECTURE.md`
8. `REQUIREMENTS_AUDIT.md`
9. `CHANGELOG.md`
10. `SECURITY_CONTROL_ENDPOINT_AUDIT.md`
11. `PHASE3_LATEST_CI_CHECKPOINT.md`
12. `PHASE3_PROGRESS_REPORT.md`
13. `PHASE3_ROADMAP.md`
14. `PHASE3_INSTRUCTIONS.md`
15. `UPSTOX_API_INTEGRATION_POLICY.md`
16. `docs/UPSTOX_SDK_API_REPOSITORY_AUDIT.md`
17. `docs/UPSTOX_AGENT_SKILL_SECURITY_REVIEW.md`
18. `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`

`docs/source_snapshots/UPSTOX_CHARGES_2026-10-24.md` is an immutable, dated source-evidence artifact, not a rolling checkpoint document. Preserve it as historical evidence; when sources change, add a new dated snapshot rather than rewriting the old one.

After each CI result, update the current status/next step across all 18 living documents. Record the exact SHA and run result, distinguish verified implementation from unverified later documentation commits, and never inherit a parent's green status.
---

## Phase 3 forward checkpoint — 25 October 2026

- New evidence-intake vocabulary covers separate Upstox transaction, clearing, IPFT, other and demat transaction charge labels. Database migration `202610250019` expands source-component and allocation constraints; API intake remains pending-review only.
- Live-fill promotion still requires exactly six reconciled components. This intentionally fails closed for separate IPFT/clearing/demat/other lines; next implementation gate is a versioned component-set and combined-vs-split representation contract, with no silent omission or double count.
- Existing NSE combined-vs-split IPFT arithmetic tests remain authoritative for that narrow rule. Upstox endpoint/schema/contract-note semantics and product/date/invoice-specific GST composition are still unapproved.
- New implementation head requires exact-head CI verification. PR #6 remains draft/unmerged, PAPER mode mandatory, live broker writes disabled, and original `Tradepro` out of scope.

# Integration selection, cost and implementation policy — 24 October 2026

This section is the standing integration policy for the whole Tradepro Improved application. Apply it to future architecture, implementation, audits, deployment plans, and documentation. It is a decision framework, not a claim that every listed integration is already implemented.

## Mandatory project and safety constraints
- Work only in `tarunsharma2610-del/tradepro-improved`. Never edit the original `tarunsharma2610-del/Tradepro` repository.
- Keep PR #6 draft/unmerged until its acceptance gates pass and the user explicitly approves merging.
- PAPER mode remains the default and mandatory during development. Real broker order placement, modification, and cancellation must remain blocked until a separately reviewed and explicitly approved live-trading gate. Researching or connecting an API must never silently enable order writes.
- Before adding an integration, inspect the existing code, project instructions, architecture, requirements and roadmap; check the provider's current official documentation, SDK, pricing, rate limits, terms and data licensing. Prefer existing dependencies and official APIs. Do not duplicate functionality or add a service merely because it exists.
- Classify every integration as **required**, **optional**, or **future** and record its purpose, implementation status, evidence/source, cost model, secret/data handling, resource impact, fallback, tests and acceptance gate in the relevant project documents. Clearly distinguish free software from free hosting, free API access, free market data and free messaging; they are not equivalent.
- Prefer free/open-source and self-hosted components for this personal/friends-only app. Paid services, paid plans, paid API quotas, and chargeable usage must remain optional and disabled unless the user explicitly approves the cost. Recheck current pricing before activation.
- Keep API keys, OAuth tokens, refresh tokens, webhook secrets, database credentials and private contract notes out of source control, logs and public artifacts. Use environment/secret configuration, least privilege, redaction and documented rotation/revocation procedures.
- Every provider integration must have timeout/retry/backoff, rate-limit handling, error/stale-data state, idempotency where applicable, observability, tests, and a safe failure mode. Broker/account data must be scoped to the authenticated owner.

## Integration inventory and cost expectations

| Integration / component | Intended role | Cost expectation and policy |
|---|---|---|
| **Upstox Developer API and official Python SDK** | Primary Indian broker: OAuth, profile/funds/holdings/positions/orders/trades, instruments, historical and live market data, and brokerage/charge endpoints where officially supported. Use only documented endpoints and SDK versions; verify entitlement, rate limits, API terms and segment availability. | API access/subscription may be free under current published terms, but trades incur brokerage/statutory/exchange charges and data/API entitlements can change. Treat estimates as estimates; do not treat aggregate charge endpoints as per-fill actuals. |
| **Broker adapters / future brokers (e.g. Zerodha, Groww if supported and approved)** | Isolated adapter interface so a future broker can be added without coupling strategy/accounting logic to one provider. | No integration until official APIs, eligibility, pricing, data rights and implementation effort are verified. Do not assume a broker has an accessible public trading API or that its API is free. Upstox remains first priority. |
| **PostgreSQL** | Durable application/accounting database, transactions, migrations, constraints and concurrency guarantees. | Database software is free/open-source; managed hosting, storage, backup and network usage may cost. Self-host initially where appropriate. |
| **Redis** | Cache, rate-limit coordination, short-lived coordination/queue support only where required. | Software is free/open-source; managed hosting costs extra. Keep optional if the existing design works without it and monitor RAM use. Never use volatile cache as the source of truth for trades, fills, charges or audit evidence. |
| **FastAPI, SQLAlchemy, Alembic** | Backend API, ORM and database migrations. | Open-source; hosting and operations are not automatically free. Pin compatible versions and run migration tests. |
| **Next.js and React** | Web frontend and dashboard. | Open-source; deployment/build hosting may cost. Prefer self-hosting on the selected VM while it is sufficient. |
| **TradingView Lightweight Charts** | Interactive charts where useful. | Open-source/free library; it does **not** provide exchange market data, TradingView's paid platform features, or a data licence. Supply authorized data from the broker/other licensed source. Any separate TradingView product/API requires its own terms and cost review. |
| **GitHub repository and GitHub Actions** | Source control, pull requests, review and CI. | Free tier has quotas/usage limits; recheck current plan limits. Keep CI for tests, migrations, broker-write guards, dependency/security checks and build verification. Do not claim a commit is verified until the exact head's checks finish. |
| **Oracle Cloud VM / other hosting** | Initial private deployment and background worker. | Always Free resources are quota/region/eligibility dependent; extra resources, egress, storage, IPs or usage may cost. Verify the account's actual allowance before deployment. Size services to the low-memory VM and avoid unnecessary containers. |
| **Domain name + HTTPS/TLS (Let's Encrypt)** | Private web access and encrypted transport. | A domain generally costs money; Let's Encrypt certificates are free. TLS does not make an exposed application private by itself; configure authentication, firewall, secure cookies, proxy headers and renewal. |
| **Telegram Bot API** | Optional alerts/notifications and operational messages. | Bot API is generally free to use; users still need to configure a bot and protect its token. Handle delivery failures and avoid sending credentials, sensitive account data or full contract notes. |
| **WhatsApp Business Platform/API** | Optional WhatsApp alerts if needed. | Do not assume free. Business/provider fees, conversation/template pricing, setup and policy requirements may apply. Keep disabled until the user approves a provider and cost; Telegram or in-app notifications are the lower-cost fallback. |
| **Monitoring: structured logs, health endpoints; Prometheus/Grafana if needed** | Service health, latency, queue/worker status, errors and resource pressure. | Basic app logs/health checks can be self-hosted at no licence cost. Prometheus/Grafana OSS are free to self-host, but consume VM CPU/RAM/disk. Start with lightweight logging and health checks; add dashboards only when justified. |
| **Sentry or another hosted error tracker** | Optional error aggregation and alerting. | May offer a free tier with quotas, but hosted events and data retention are limited and plans can change. Optional only; redact secrets, tokens, personal data and broker payloads before sending anything. Local structured logs are the fallback. |
| **Backups and recovery** | Encrypted database and private evidence backups, retention and tested restore. | Local tools are free; off-VM object storage and extra capacity may cost. Keep backups encrypted and access-controlled, and test actual restore. A synthetic CI restore drill is not proof that a real Oracle VM backup can be restored. |
| **Secrets management** | Secure OAuth/API credentials and deployment secrets. | Environment files outside Git may be free for a single-VM setup but require strict permissions and rotation. Hosted secret vaults may cost. Never commit real `.env` files or expose secrets in logs/CI artifacts. |
| **Market data / exchange data licensing** | Live quotes, historical candles, instrument masters and scanners. | Broker API access does not automatically mean unrestricted redistribution or all-segment data rights. Confirm the current broker/exchange terms, user entitlement, retention and display/use restrictions. Never scrape or use unauthorized feeds. |
| **AI/API integrations** | Optional future assistance for research or strategy explanations. | Not required for core trading. Hosted AI APIs may be paid and can send sensitive code/data externally. Do not add or enable without explicit approval, a cost limit, privacy review and a non-AI fallback. |
| **Email/SMS/push and other notification providers** | Future alert channels only if Telegram/in-app alerts are insufficient. | Often quota-limited or paid. Treat as optional and record provider-specific pricing and consent requirements before activation. |

## Official documentation to consult
- Upstox developer API catalogue and current endpoint/SDK documentation: https://upstox.com/developer/api-documentation/ and https://github.com/upstox/upstox-python
- Upstox published charges and brokerage calculator: https://upstox.com/brokerage-charges/ and https://upstox.com/developer/api-documentation/get-brokerage/
- PostgreSQL: https://www.postgresql.org/docs/
- Redis: https://redis.io/docs/
- GitHub Actions usage limits: https://docs.github.com/en/actions/administering-github-actions/usage-limits-billing-and-administration
- Oracle Cloud Free Tier: https://www.oracle.com/cloud/free/
- Telegram Bot API: https://core.telegram.org/bots/api
- TradingView Lightweight Charts: https://github.com/tradingview/lightweight-charts
- Let's Encrypt: https://letsencrypt.org/
- Prometheus: https://prometheus.io/ ; Grafana: https://grafana.com/oss/
- Sentry pricing/quotas: https://sentry.io/pricing/

Provider prices, free quotas, endpoints, supported segments and terms change. These links are starting points, not permanent guarantees; check them again at implementation/activation time.

## Acceptance rule
No integration is considered complete merely because a dependency is listed or a credential exists. Record implementation and test evidence, failure behaviour, current cost/terms, data rights, security review and owner approval. Keep uncertain or paid integrations inactive. For trading/accounting integrations, also verify idempotency, reconciliation, audit trail, replay/rollback behaviour and fail-closed safety. Update `PROJECT_INSTRUCTIONS.md`, `ARCHITECTURE.md`, `MASTER_ROADMAP.md`, `REQUIREMENTS_AUDIT.md`, `PROGRESS.md`, `HANDOVER.md`, `CHANGELOG.md` and other applicable checkpoint documents whenever this policy changes or an integration is implemented.

---

## Upstox charge API usage rule — 24 October 2026

- For Upstox-related implementation or charge audits, inspect current official API documentation, SDK examples and the relevant official pricing/circular sources before changing code. Do not invent paths or infer capabilities from endpoint names.
- Use the official [Brokerage Details API](https://upstox.com/developer/api-documentation/get-brokerage/) (`GET /v2/charges/brokerage`) for order-input-based charge estimates. It is not the final actual charge for an executed fill.
- Use the official [Get Profit and Loss on Trades API](https://upstox.com/developer/api-documentation/get-trade-charges/) selected-scope charge breakdown (aggregate, not per-trade) for reconciliation, alongside the broker-issued contract note/tax invoice. Preserve request dimensions, raw response/digest, retrieval time, API version and evidence linkage.
- Treat the API field list and public brokerage page as reconciliation inputs, not automatic approval of legal/tax treatment. Product, segment, exchange, effective date and GST taxable-component mapping must be reviewed; unknown/conflicting cases fail closed. Do not double-count legacy IPFT rates against the combined NSE schedule effective 1 March 2026.
- No automatic tariff activation, charge-ledger promotion, or live broker order submission may be enabled by source discovery alone. Keep candidate rules inactive until evidence and independent review gates are satisfied. See `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`.

## Brokerage cap entrypoint integration — 23 October 2026

- The previous exact-head implementation CI passed on commit [3445a748b3fbd3944362ed6e46873bffc30fd384](https://github.com/tarunsharma2610-del/tradepro-improved/commit/3445a748b3fbd3944362ed6e46873bffc30fd384): **712 passed, 1 warning**; SQLite/PostgreSQL migration round-trips, broker-write boundary guard, synthetic restore drill and evidence retention also passed.
- Follow-up review found the general `calculate_charge_for_trade` entry point selected an approved brokerage rule but bypassed the rule-bound minimum/maximum caps. Fixed it to route order-notional brokerage through `calculate_order_brokerage`, and added regression test `test_trade_charge_entrypoint_applies_caps_from_selected_brokerage_rule`. Code/test commits: [d6d60a03732ab322785d5e020f0521a4b96162c9](https://github.com/tarunsharma2610-del/tradepro-improved/commit/d6d60a03732ab322785d5e020f0521a4b96162c9) and [78f5f27135137a1d8f0882d2c0a91d013f6e8556](https://github.com/tarunsharma2610-del/tradepro-improved/commit/78f5f27135137a1d8f0882d2c0a91d013f6e8556).
- **The entrypoint follow-up has not yet been validated by CI.** Earlier 712-pass results do not cover these later code/test commits. CI for the resulting latest documentation head must complete before this gate is marked green.
- The cap-aware snapshot schema v4 records minimum/maximum values in the snapshot and rule fingerprint; same-event cap changes are conflicting replays. These helper functions do not prove official Upstox rates or legal/tax applicability, and the snapshot builder does not itself persist or promote charges.
- Automatic quantity/notional allocation remains disabled until reviewed, effective-dated component-specific tariff rules exist. Existing variance tests keep estimate-vs-actual comparisons review-only and do not promote charge ledger entries.
- PR #6 remains draft/unmerged. Live broker order writes remain disabled. Synthetic restore is not actual Oracle Cloud recovery. All work remains in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` is out of scope.

---

## Rule-bound brokerage caps and passing CI — 23 October 2026

- Order-level brokerage minimum/maximum caps are now fields on the validated `TariffRule`, and are accepted only for order-notional brokerage rules. Caps must be finite, nonnegative, and paise-precise; minimum cannot exceed maximum.
- `calculate_order_brokerage` reads caps from the reviewed rule rather than caller-supplied parameters. Tariff estimate snapshot schema is now v4; snapshots include the cap values and include them in the rule fingerprint. Changing a cap for the same event produces a conflicting replay rather than a silent overwrite.
- Exact-head backend workflow [39976363279](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39976363279) passed on commit [3445a748b3fbd3944362ed6e46873bffc30fd384](https://github.com/tarunsharma2610-del/tradepro-improved/commit/3445a748b3fbd3944362ed6e46873bffc30fd384): **712 passed, 1 warning**. Broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and evidence retention passed.
- The warning is a Starlette/AnyIO deprecation warning; the workflow also reports Node.js action-runtime deprecation warnings. They did not fail the run. Do not claim that this CI head verifies any later documentation-only commit until CI is checked for that exact head.
- This implementation does not establish official Upstox tariff rates or tax-law applicability; caps/rates must come from a reviewed source record. The snapshot helper itself does not persist estimates or promote them into actual charges. Synthetic restore is not actual Oracle Cloud recovery.
- Next accounting gate: verify aggregate order-level estimate-versus-actual variance handling, then rerun exact-head CI and synchronize all nine documents after any further changes. PR #6 remains draft/unmerged; live broker order writes remain disabled.
- All work is confined to `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` repository is out of scope.

---

## Brokerage cap precision and CI checkpoint — 23 October 2026

- Brokerage minimum and maximum inputs now reject values with more than two decimal places, avoiding sub-paise cap ambiguity. Regression tests cover sub-paise minimum and maximum values.
- Exact-head workflow run [39975215770](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39975215770) passed on commit [d650471895e6938b175434eff20b7d7421abb046](https://github.com/tarunsharma2610-del/tradepro-improved/commit/d650471895e6938b175434eff20b7d7421abb046): **709 passed, 1 warning**. Broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and evidence retention completed successfully.
- The remaining warning is a third-party `starlette.testclient` / AnyIO deprecation warning; GitHub Actions also emitted Node.js action-runtime deprecation warnings. These did not fail the run and should be tracked separately from accounting correctness.
- The nine project documents are now being synchronized after this green code/test head. A new CI run for the resulting documentation commit is required before claiming that latest documentation head is green.
- This run's restore evidence is synthetic; it does not prove recovery of actual Oracle Cloud production data. Calculation helpers validate structure and precision, not official Upstox rates or legal/tax applicability.
- PR #6 remains draft/unmerged pending accounting acceptance review and explicit user approval. Live broker order writes remain disabled. All work remains in `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` repository is out of scope.

---

## Latest Phase 3 CI checkpoint — 23 October 2026

- Stamp-duty regression setup was corrected in commit [c98d13d86031ffe173546dbbc9c8b0234e02456e](https://github.com/tarunsharma2610-del/tradepro-improved/commit/c98d13d86031ffe173546dbbc9c8b0234e02456e): invalid-basis test cases now explicitly select the intended `BUY` transaction side so each case reaches the basis guard it is designed to exercise.
- Exact-head GitHub Actions run [39974055917](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39974055917) passed on that code/test commit: **707 passed, 1 warning**. Broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and evidence retention all passed.
- Existing tests already cover inclusive effective-date boundaries, expiry of old tariff rules, overlapping approved-rule rejection, deterministic largest-remainder paise allocation, input-order independence, zero-weight residual handling, and exact source-total reconciliation. Do not duplicate these tests; review whether the rules are wired into real reviewed component-specific tariff selection before enabling automatic allocation.
- Brokerage and GST calculation helpers and stamp-duty side/product/base guards are arithmetic safeguards only. They do not establish official Upstox tariff rates or tax-law applicability. Authentic contract-note verification and actual Oracle Cloud backup recovery remain separate evidence/deployment gates.
- The documentation files are being synchronized after this green code/test head. Rerun CI on the resulting latest documentation commit before claiming the complete latest head is green.
- PR #6 remains draft/unmerged pending accounting acceptance review and explicit user approval. Live broker order writes remain disabled. Work is exclusively in `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` repository is out of scope.

---


## Phase 3 — durable per-fill charge allocation verification — 23 October 2026

- Latest test refinement commit: [e73c9cbb8b5c4e34abe9874b548dbae5cbf762af](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e73c9cbb8b5c4e34abe9874b548dbae5cbf762af). The PostgreSQL concurrency test now only treats the expected `ValueError` for pending/unreconciled allocation rows as a valid fail-closed outcome; unexpected exceptions fail the test.
- Exact-head GitHub Actions run [39971530839](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39971530839) passed: **688 passed, 1 warning**. Broker-write boundary guard, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and retained restore evidence all passed.
- This run validates synthetic test fixtures and restore mechanics only. It does not validate an authentic personal Upstox contract note or prove restoration of the user's actual Oracle Cloud backup.
- The nine required project documents are being synchronized after this green code/test head; rerun CI on the resulting latest documentation commit before calling the documentation checkpoint current.
- PR #6 remains draft/unmerged pending complete accounting/idempotency review and explicit user approval. Live broker order submission remains disabled. All work is limited to `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` repository is out of scope.

---

---

## PostgreSQL CI execution confirmation — 24 October 2026

- Inspected `.github/workflows/backend-tests.yml` and successful Backend pytest run [39921411680](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39921411680) on commit `db1053d7f7c53e1c57016f153f11c9897fa59682`. The workflow provisions PostgreSQL 16, sets `TEST_POSTGRES_URL` for `python -m pytest -q`, and the Backend pytest job completed successfully. Thus the `skipif(not TEST_POSTGRES_URL)` PostgreSQL-only tests were enabled for that run (job logs/test output should be consulted if exact per-test counts are needed).
- The workflow also passed Alembic upgrade/downgrade/re-upgrade checks on SQLite and PostgreSQL 16, the broker-write-boundary guard, and an isolated synthetic database/document-volume restore drill.
- The restore drill uses synthetic data created inside CI. It does not substitute for restoring the user's actual retained Oracle Cloud backup or validating an authentic account-specific Upstox contract note.
- The existing source-verification/promotion race test covers allocation-ledger functions, but the integrated concurrency scenario that races real `LiveFillAccountingService.promote_trade` against ledger verification/promotion remains open. Do not mark Phase 3 accounting sign-off complete until that integration gap is addressed or explicitly accepted with evidence.
- PR #6 remains draft/unmerged; live broker order submission remains disabled. All changes are confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains untouched.

---

## Phase 3 concurrency integration status — 24 October 2026

- Current branch head before this documentation update: `2cacf392e5104a8b16307395847239bba945c87b`; branch-head backend CI run [39920815737](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39920815737) passed. PR #6 is draft and unmerged.
- The PostgreSQL-only allocation concurrency suite already contains `test_concurrent_source_verification_and_promotion_serialize_on_evidence`. It concurrently runs the real `verify_component_allocation_ledger` and `promote_verified_component_allocations` functions against synthetic persisted evidence and asserts that both allocations finish reconciled under one reconciliation reference.
- This is a useful source-ledger race test, but it is not the same as a concurrent call to `LiveFillAccountingService.promote_trade` using the real `_load_reconciled_allocation_fees` path while ledger verification/promotion races. That end-to-end live-fill integration scenario remains unproven and is still an acceptance gate.
- The other PostgreSQL allocation test races competing fill sets for a source component and expects exactly one fill set to own that component. Tests are skipped locally without `TEST_POSTGRES_URL`; CI must be checked to confirm the PostgreSQL service actually ran these tests rather than only passing via skips.
- Next engineering task: add or extend a disposable-PostgreSQL integration test using reviewed synthetic evidence, real reconciled allocations, and the actual live-fill accounting service. Assert no partial execution/position writes on failed verification, exactly-once replay, and no acceptance of a conflicting/unreconciled ledger. Then verify the exact resulting head's job logs and test counts.
- Real account-specific broker contract-note validation and restoration from an actual retained Oracle Cloud PostgreSQL/document backup remain separate operational checks.
- Live broker order submission remains disabled. PR #6 stays draft/unmerged. All work remains confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains untouched.

---

## Final conflict-recovery review checkpoint — 24 October 2026

- Reviewed `LiveFillAccountingService.promote_trade` replay and `IntegrityError` recovery paths on branch head `78c66b50714175df7e6923fa0e9328b98bb30cf2`.
- Existing-execution replay locks and refreshes the broker trade record, checks its immutable execution snapshot, and compares execution identity, fill details, charge values and evidence before returning `inserted=False`; conflicting details fail closed.
- The integrity-conflict recovery rolls back the losing transaction, re-queries the execution by broker connection/trade identity, and only returns an idempotent result when the existing execution matches; otherwise it raises a conflict requiring review. Generic failures also roll back.
- Latest branch-head backend pytest CI passed in run [39920205395](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39920205395). The concurrent PostgreSQL test uses a test-only stub for the charge-ledger loader, so it verifies parent/child locking and duplicate-promotion behavior, not the real allocation verifier under the same concurrency interleaving. Ledger validation is covered by separate accounting tests. Do not overstate this as a full production-like concurrent allocation integration test.
- Review status: the inspected replay/rollback paths have coverage and no additional code change is justified by this inspection alone. Phase 3 accounting sign-off is still gated on a final review of the real verifier/promotion concurrency interaction and confirmation of exact-head CI after this documentation update.
- Real broker contract-note authenticity and a restore drill from an actual retained Oracle Cloud PostgreSQL/document backup remain outstanding operational acceptance checks.
- PR #6 stays draft and unmerged; live broker order submission remains disabled. Changes remain confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is untouched.

---

## Phase 3 accounting checkpoint — 24 October 2026

- The concurrent exact-replay PostgreSQL regression passed in implementation CI run [39919563611](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39919563611) for commit `f8441f6d11b863e3ad173282664663cd4985eeb2`. The test exercises two distinct fills and a simultaneous duplicate promotion, expecting two inserted executions and one idempotent replay.
- Documentation checkpoint run [39919590316](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39919590316) passed for commit `c99e4972cf4c2c902bddc076af6327c3bfd25fa7`.
- The next documentation CI checkpoint is still in progress: progress run `39919920878` succeeded, while handover run `39919925329` and audit run `39919932771` were in progress at last inspection. These are earlier documentation heads; any newly synchronized documentation needs its own exact-head CI.
- Accounting review remains open pending exact-head verification and final adversarial review. Passing tests are evidence for covered cases, not a guarantee against every possible concurrency interleaving.
- Real account-specific contract-note validation and restore of an actual retained Oracle Cloud PostgreSQL/document backup remain operational acceptance checks. Synthetic CI restore drills do not satisfy those real-environment checks.
- PR #6 remains draft and unmerged; live broker order submission remains disabled. All work is confined to `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` repository is out of scope.

---

## Current acceptance clarification — 23 October 2026

- **Public contract-note research is complete for development:** third-party examples dated 12 March 2025 and 21 May 2024, plus a sample-note guide, were reviewed for structure and charge categories. See `docs/UPSTOX_CONTRACT_NOTE_AND_API_EVIDENCE.md`.
- The examples are not independently authenticated. No raw public document, personal identifier, or invented “real” evidence is stored in this repository. The checked-in Upstox-style fixture remains explicitly synthetic.
- **A personal/account-specific contract note is not required to continue or complete Phase 3 engineering.** It remains optional future validation for account-specific source authenticity and charge comparison; public aggregate figures must not be treated as proof of per-fill amounts.
- A separate real retained database/document backup and restore test remains a deployment/operational acceptance gate for the Oracle Free Cloud environment. Synthetic CI restore results do not prove recovery of real user data.
- Exact-head CI on commit `18c897a282ea5f8e7c6a55707ad24b6cf8da5b27` passed in [run 39915983869](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39915983869). This does not substitute for the next CI run after this documentation clarification.
- This section supersedes older checkpoint wording below that may imply a personal contract note is required before Phase 3 engineering can proceed. Historical notes remain for audit traceability.
- Scope: `tarunsharma2610-del/tradepro-improved` only. PR #6 remains draft/unmerged; live broker order writes remain disabled.

---

## Phase 3 allocation-weight integrity checkpoint — 23 October 2026

- Code review found that a charge ledger could sum to the correct source total while its individual per-fill amounts did not follow the reviewed allocation basis. Reconciliation now recomputes and verifies each fill's expected amount before promotion.
- Added migration `202610230013` and persisted canonical reviewer-approved weights for `EXPLICIT_REVIEWED`. Source review requires one weight per eligible fill; `QUANTITY` and `NOTIONAL` bases derive weights from persisted broker-trade quantity and price. The verifier checks the complete fill set, basis, method, total, and each per-fill allocation.
- Added regression coverage for a tampered per-fill split that preserves the aggregate total.
- Exact-head CI [run 39912330029](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39912330029) passed on code commit `776ee59485d79b880d7aee0f5c3ecb641eb7db3f`: **567 passed, 1 warning**. Broker-write boundary guard, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore all passed.
- This CI result validates that code commit only; the documentation commits now being synchronized require a new exact-head run. Synthetic restore evidence is not proof of recovery of actual Oracle Free Cloud data or authenticity of a real Upstox contract note.
- PR #6 remains draft/unmerged pending the final review and explicit user approval. Live broker writes remain disabled. Scope remains `tarunsharma2610-del/tradepro-improved`; do not modify original `tarunsharma2610-del/Tradepro`.

---

## Phase 3 promotion rollback guard — 22 October 2026

- Exact-head CI run [39813721425](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39813721425) **PASSED** on commit `121741f32ff74c46ccc059f672b3e9f0e020ef14`: backend pytest **565 passed, 1 warning**; configured PostgreSQL 16 migration/safety checks completed successfully.
- Added a regression test that injects a flush failure during charge-allocation promotion and verifies that, after rollback/reload, all allocation rows remain `PENDING_RECONCILIATION` with no reconciliation reference.
- This CI result validates the above commit only. Any subsequent documentation commits require a fresh exact-head run.
- PR #6 remains open, draft, and unmerged pending continued accounting review and explicit user approval. Live broker order writes remain disabled.
- Synthetic restore evidence does not prove recovery of the user's real Oracle Free Cloud data or authenticity of a real broker contract note. Real-data acceptance remains deferred until the user supplies the evidence.
- Scope remains `tarunsharma2610-del/tradepro-improved` only. Do not modify original `tarunsharma2610-del/Tradepro`.

## Phase 3 exact-head CI checkpoint — 22 October 2026

- Latest exact-head workflow: [GitHub Actions run 39808404362](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39808404362) **PASSED** on commit `1fcbb06a78fd06226f0e0e6438cf72b422dc2d4e`.
- Backend pytest: **563 passed, 1 warning**. Broker-write boundary guard passed. SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed. Isolated synthetic PostgreSQL/database + document-volume restore drill and evidence-retention step passed.
- This supersedes earlier “CI pending” notes for commits before this exact head only. Do not treat older commits' results as validation of this head.
- The restore drill uses synthetic data and does not prove restoration of the user's real Oracle Free Cloud database or authentic broker contract-note files.
- PR #6 remains open, draft, and unmerged. Keep it draft until the accounting/idempotency review and user approval. Live broker write operations remain disabled.
- Next: review durable per-fill accounting idempotency/rollback and reconcile any remaining Phase 3 acceptance gates; real broker-note and retained real-backup evidence can be supplied later by the user.
- Repository scope remains `tarunsharma2610-del/tradepro-improved` only; do not modify the original `tarunsharma2610-del/Tradepro`.

## Phase 3 source-reconciliation safety correction — 22 October 2026

- Code review identified a safety gap in `backend/app/services/broker_charge_allocation_persistence_service.py`: the service previously marked rows `RECONCILED` merely because calculated allocations summed to the caller-provided component total. That is arithmetic reconciliation, not independent verification of a broker contract-note source total.
- Fixed in commit `fce01b98ce33760e3361991e8d2ffba01b0ad281`: newly persisted allocations remain `PENDING_RECONCILIATION`; this service clears the reconciliation reference and does not promote them to `RECONCILED`. A separate source-verification workflow must establish provenance and validate the source component total before promotion.
- Updated regression expectation in commit `8c38ab8ecc8114f392e11ea988ac25c3d7c8e2df` to assert pending status and no reconciliation reference even when arithmetic totals match.
- **Historical CI note superseded:** exact-head CI passed on commit `1fcbb06a78fd06226f0e0e6438cf72b422dc2d4e`; see the Phase 3 exact-head CI checkpoint at the top of this file.
- This deliberately fails closed: matching a number supplied by the caller is not treated as proof that it came from an authentic contract note. Contract-note authenticity/parser, component-specific allocation methodology, source-total verification, and controlled accounting integration remain open Phase 3 gates.
- Keep PR #6 draft/unmerged pending exact-head CI and broader review. Live broker submission and automatic accounting promotion remain disabled.
- Scope remains exclusively `tarunsharma2610-del/tradepro-improved`; do not modify original `Tradepro`.

---

## Phase 3 allocation edge-case hardening — 22 October 2026

- Code review found a rounding edge case in `backend/app/services/broker_charge_allocation_service.py`: when a source total was one paise and a zero-weight fill ID sorted before positive-weight IDs, the deterministic largest-remainder tie-break could assign that paise to a fill whose weight was zero.
- Fixed in commit `1f04b5d0c0fc07af15eadd4fe7c70f14ff054f91`: only strictly positive-weight fills participate in residual ranking. Zero-weight fills remain in the result at INR 0.00.
- Added regression coverage in commit `347f9588485bd7452d949dd816ba6966196354f6` for the one-paise/tied-remainder case and the two-paise case.
- **Verification pending:** CI for these code/test commits and the following documentation commits must pass on the exact latest branch head before this fix is called verified. The prior PostgreSQL concurrency success does not include this new change.
- Existing successful PostgreSQL concurrency run: `39737580271` on `d59e7d8`, `527 passed, 1 warning`, with `TEST_POSTGRES_URL` set. New allocation edge-case fix is a separate code change and needs fresh CI.
- Source authenticity, component-appropriate allocation policy, exact source-total reconciliation against real contract-note data, and accounting integration remain release gates. Keep PR #6 draft/unmerged; live broker submission and automatic accounting promotion remain disabled.
- Scope remains exclusively `tarunsharma2610-del/tradepro-improved`; do not modify original `Tradepro`.

---

## Phase 3 PostgreSQL concurrency verification — 22 October 2026

- **Verified green:** GitHub Actions run `39737580271`, commit `d59e7d8a613471c3134b8d0c6dcdb326713ce7eb`, completed successfully. Job `Backend pytest` passed; log summary: `527 passed, 1 warning in 32.20s`.
- The test job environment explicitly set `TEST_POSTGRES_URL` to the dedicated PostgreSQL 16 service. The suite reported no skipped tests, so the opt-in PostgreSQL integration test was not skipped in this run.
- The preceding fixture corrections addressed (1) missing `Base` import and (2) parent user row not flushed before dependent records. The subsequent exact-head run is green.
- This is evidence that the new PostgreSQL concurrency integration test completed successfully in the suite. Keep its specific invariant documented: competing independent sessions target one evidence/component with different fill sets; only one allocation should persist, without partial/mixed rows.
- Remaining gates are not closed by this test: authenticated contract-note provenance/schema, reviewed charge-component allocation methodology and residual handling, reconciliation against source totals, and controlled integration with live-fill accounting still need review/acceptance. Live broker order submission and automatic accounting promotion remain disabled.
- PR #6 remains draft/unmerged pending review of the full change and its broader release gates.
- Scope remains exclusively `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is not the target.

---

## PostgreSQL concurrency-test fixture correction — 22 October 2026

- Inspected failed workflow `39737225306` on commit `d6a9cab`. PostgreSQL test failed during fixture setup, before the race assertion: the `broker_connections.user_id` foreign key referenced a user not yet flushed to PostgreSQL. The suite result was `1 failed, 526 passed, 1 warning`.
- Fixed in code commit `0c4d5133a1224fbac5b0eb2cafb3b7c195612d40`: explicitly flush the user parent row before adding dependent portfolio/instrument/connection rows. No production behavior was changed.
- **Pending:** exact-head CI for `0c4d513` and subsequent documentation commits. Do not infer that the concurrency test passes from this fixture correction alone.
- Acceptance remains: on PostgreSQL, two independent sessions race different fill sets against the same evidence/component; exactly one complete allocation set succeeds, the other fails closed, and no partial/mixed ledger remains.
- PR #6 remains draft/unmerged until this test and exact-head CI pass. Contract-note authenticity, allocation methodology review, and accounting integration remain separate gates. Live broker submission and automatic accounting promotion remain disabled.
- Scope remains exclusively `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is not the target.

---

## PostgreSQL concurrency-test CI correction — 22 October 2026

- First run of the new integration test failed before reaching the race assertion: `NameError: Base is not defined` in test schema setup. Suite result was `1 failed, 526 passed, 1 warning` on commit `1859179`.
- Fixed by importing `Base` from `app.core.database` in commit `eb4b6c4`. This is a test setup correction only; it does not weaken production checks.
- **Pending verification:** CI for `eb4b6c4` and the documentation commits is not yet confirmed green. The PostgreSQL test's runtime race behavior remains unverified until it executes successfully against the CI PostgreSQL 16 service.
- The test provisions isolated records and races two independent sessions against one evidence/component. Acceptance criterion: exactly one allocation request succeeds, the other fails closed, and exactly one allocation row remains.
- Keep PR #6 draft/unmerged until exact-head CI passes and the concurrency result is inspected. Evidence authenticity, valid charge basis, and integration with live accounting remain separate gates. Live broker submission and automatic accounting promotion remain disabled.
- All work stays in `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is not the target.

---

## Phase 3 PostgreSQL concurrency test added — 22 October 2026

- Added `backend/tests/test_broker_charge_allocation_postgres_concurrency.py`, an opt-in integration test that uses `TEST_POSTGRES_URL`, two independent SQLAlchemy sessions and concurrent threads to race incompatible single-fill allocations against one reviewed evidence record/component. The expected result is exactly one winner and one persisted allocation, with no mixed/partial fill set.
- The existing `.github/workflows/backend-tests.yml` provisions PostgreSQL 16 and exports `TEST_POSTGRES_URL`; the integration test creates ORM metadata in that dedicated CI test database because pytest runs before the later Alembic migration verification step.
- Test setup was corrected to build the required portfolio → instrument → order → broker-order → broker-trade foreign-key chain. Test commits: `a69e083`, `4b5e8cc`, `1859179`.
- **Pending:** this new PostgreSQL concurrency test has not yet been confirmed green by exact-head CI. A green prior run does not cover these commits. If CI fails, inspect the test output and correct the fixture or concurrency assumptions before claiming safety.
- The evidence-row `SELECT ... FOR UPDATE` is the serialization point. This integration test is the empirical verification needed; SQLite-only unit tests are insufficient.
- PR #6 remains draft/unmerged pending successful exact-head CI and review. Contract-note authenticity, component-appropriate allocation basis and live accounting integration remain separate release gates. Live broker submission and automatic accounting promotion remain disabled.
- Scope remains exclusively `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is not the target.

---

## Phase 3 continuation — PostgreSQL concurrency test still required — 22 October 2026

- Latest confirmed successful workflow remains `39735969492` on commit `a94760f66d5405a563cca25960c95f00ba2a4e5f`; it is a PR-triggered backend-tests run. No later code change is represented by that result.
- Rechecked the allocation persistence service and test setup. The default test fixture explicitly forces SQLite in-memory; it does not exercise PostgreSQL row locks. The workflow file is named `.github/workflows/backend-tests.yml` (not `ci.yml`).
- Source evidence is locked with SQLAlchemy `with_for_update()` before fill rows and existing allocations are queried. This is a plausible PostgreSQL serialization point but is not yet race-tested with two independent transactions.
- Next step remains an opt-in integration test using a dedicated PostgreSQL test database/URL and two independent sessions racing different fill sets against the same evidence/component. The test must assert one complete winner and one fail-closed conflict, with no partial rows. CI must provision PostgreSQL or clearly report the integration test as skipped; a skipped test is not proof of safety.
- Keep PR #6 draft/unmerged pending that test and exact-head green CI. Source document authenticity, allocation-basis review and accounting-service integration remain separate release gates. Live broker order submission and automatic accounting promotion remain disabled.
- All changes in this project remain confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is not the target.

---

## Phase 3 checkpoint — concurrency safeguard and verification boundary — 22 October 2026

- Confirmed latest recorded successful GitHub Actions run for this branch: `39735332590`, commit `9ed382f5872faaf2c20f71e4292ac5cc3baf322f` (backend tests, success).
- The source-evidence `SELECT ... FOR UPDATE` lock is implemented in `backend/app/services/broker_charge_allocation_persistence_service.py` before fill-set lookup/allocation persistence. This is intended to serialize concurrent allocations for the same evidence on PostgreSQL.
- **Important verification limit:** the green run is for commit `9ed382f`; it does not include any later changes. The current test file still lacks a PostgreSQL-backed concurrent allocation test. Do not claim race-safety has been empirically proven until that test runs against PostgreSQL with two independent sessions/transactions.
- Next implementation step: add an opt-in integration test using a dedicated PostgreSQL test URL (e.g. `TEST_POSTGRES_URL`) that starts two transactions attempting incompatible fill sets against one evidence/component; verify the second waits/re-reads the ledger and fails closed without partial rows. If CI does not provide a PostgreSQL service for pytest, add a dedicated PostgreSQL test job rather than treating SQLite `FOR UPDATE` behavior as equivalent.
- After the test, run full exact-head CI, inspect logs, and update this checkpoint with the observed result. Keep PR #6 draft/unmerged until verified.
- Charge-note authenticity, appropriate per-component allocation methodology, and accounting-service integration remain review gates. No automatic accounting promotion or live broker submission is enabled.
- Scope remains exclusively `tarunsharma2610-del/tradepro-improved`; do not modify original `Tradepro`.

---

## Phase 3 concurrent allocation serialization — 22 October 2026

- Latest previously verified CI head `9e07a5c95401ab3ccfd6c32a8223721dd573b928` passed, including backend pytest, broker write-boundary enforcement, and Alembic upgrade/downgrade/re-upgrade on SQLite and PostgreSQL 16.
- Code commit `34dd6cebb424f50963a3ca788de37490d39bdb60` adds a row-level lock on the reviewed `BrokerChargeEvidence` record before locking fill rows and inspecting/inserting component allocations. Rationale: locking only the target fills does not serialize two concurrent requests using disjoint fill sets against the same evidence/component; both could otherwise observe an empty ledger and insert different subsets. PostgreSQL's evidence-row lock provides a per-source serialization point.
- **Pending validation:** run exact-head CI for `34dd6ce` and the documentation commits. SQLite does not enforce `FOR UPDATE`; green SQLite tests alone are not proof of concurrency behavior. Add or run a PostgreSQL-backed concurrent test before treating race safety as fully verified.
- No live accounting promotion was enabled. Evidence authenticity and the economic correctness of a selected allocation basis remain review-gated.
- PR #6 stays draft/unmerged. All changes remain confined to `tarunsharma2610-del/tradepro-improved`, not original `Tradepro`.

---

## Replay-basis test correction — 22 October 2026

- Latest CI failed on head `bac124af41342293e5bceba8d5641e85184bee16`: `525 passed, 1 failed, 1 warning`. The new test supplied `ALTERNATE_REVIEWED`, which is intentionally not a supported allocation basis; validation rejected it before replay-conflict detection.
- Test-only correction committed as `6b91827d6a4a01ea93009d664d467ca32d5ec342`: the test now uses `QUANTITY`, a supported basis distinct from the original `EXPLICIT_REVIEWED`, so it exercises the intended changed-basis replay guard without weakening production validation.
- **Pending:** exact-head CI for `6b91827` and documentation updates must pass before replay-basis coverage is marked green.
- Concurrency review remains open: unique evidence/trade/component rows protect duplicate per-fill rows, but do not alone prove correct handling of concurrent conflicting fill sets. PostgreSQL integration coverage is required.
- PR #6 stays draft/unmerged. Live broker submission and automatic accounting promotion remain gated. All work stays in `tarunsharma2610-del/tradepro-improved`, not original `Tradepro`.

---

## Phase 3 rollback CI verified; replay-basis test added — 22 October 2026

- CI run `39734057700` passed for commit `85e022e630682da50b1b9e906a8b5986e541d97b`. This confirms the explicit SQLite transaction-boundary correction fixed the rollback test on that head.
- Added a new regression test to reject a replay that changes the reviewed allocation basis, while preserving the existing exact-replay behavior. Test commits: `3f912a1b02cea3880cd7020dea88fa9cbf1185f9` and helper correction `25695e5fc6a1d65f9344bd44f3229c9fa90a69a0`.
- **Pending verification:** the new replay-basis test and following documentation commits have not yet passed exact-head CI. Do not count them as green until CI completes.
- Concurrency note: the model has a unique constraint on evidence + trade + component, which prevents duplicate rows for a fill, but it does not by itself serialize concurrent requests that race with different fill sets. Before merge, add/review a database-backed concurrency strategy and test on PostgreSQL; SQLite alone cannot prove row-lock semantics.
- Still not proven: contract-note authenticity, legally/economically appropriate allocation basis, and integration with live accounting. No automatic accounting promotion is enabled.
- PR #6 remains draft/unmerged. Work remains confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is not the target.

---

## SQLite rollback test infrastructure correction — 22 October 2026

- Latest exact-head CI `39733775193` failed again: `524 passed, 1 failed`. The explicit session transaction still did not roll back the rows because SQLite's legacy driver transaction mode did not issue a physical `BEGIN` before the service's nested SAVEPOINT.
- Test-only infrastructure correction committed as `d49e3cdfae519dc7d7f80bdcda882fcaa6842c51`: configure the in-memory SQLite test engine with explicit transaction boundaries (disable driver-managed implicit transaction control and emit `BEGIN` on SQLAlchemy's begin event). This is the documented SQLAlchemy pattern for reliable SAVEPOINT behavior; it changes test setup, not production database code.
- **Pending:** rerun CI for this commit and documentation updates; only mark rollback coverage resolved if the test passes.
- If the rollback test still fails, stop and replace it with a database-specific integration test rather than weakening the assertion. Concurrent conflicting replay tests remain next after green CI.
- PR #6 stays draft/unmerged; live broker submission and automatic accounting promotion remain gated. Work is limited to `tarunsharma2610-del/tradepro-improved`, not original `Tradepro`.

---

## Rollback-test CI failure and correction — 22 October 2026

- CI run `39733515473` failed at commit `c9adf3b9da90e1a2d350c216ccdb923ac3ba41a8`: **524 passed, 1 failed, 1 warning**. The only failure was the new rollback test, which assumed the shared SQLite test session had a real outer transaction. The fixture commits setup records, and SQLite can release a SAVEPOINT without an explicit outer `BEGIN`.
- Corrective test commit: `f941b4bf32c8be77ad4c8c17811632ed77b540f0`. The test now starts an explicit outer transaction around the allocation service and rolls that transaction back before asserting no allocation rows remain. This tests caller-owned transaction rollback instead of relying on SQLite's implicit transaction behavior.
- **Pending verification:** exact-head CI for `f941b4b` and the documentation commits must pass before this rollback regression is considered resolved.
- No application transaction semantics were changed by this test-only correction. The service still leaves commit/rollback to its caller. Remaining follow-up: concurrent conflicting replay tests and database-level serialization review.
- Keep PR #6 draft/unmerged; live broker submission and automatic accounting promotion remain gated. Work is limited to `tarunsharma2610-del/tradepro-improved`, not original `Tradepro`.

---

## Phase 3 rollback test checkpoint — 22 October 2026

- Exact-head CI verified green for the corrected connection-safety assertion and latest documentation head `a19313ccba7c2fe79c6ac588d3acb81cd4168dce`; run `39733212480` and latest docs run `39733267668` both completed successfully.
- Added `test_outer_transaction_rollback_removes_all_new_allocations` in commit `c9adf3b9da90e1a2d350c216ccdb923ac3ba41a8`. It confirms the persistence service does not commit on the caller's behalf and a caller rollback removes all allocation rows created in that transaction.
- **Pending:** run exact-head CI for the rollback test and subsequent documentation commits. Do not count this new test as passed until the run succeeds.
- Remaining review: database-level uniqueness already guards duplicate evidence/trade/component rows; simultaneous imports can still require stronger serialization/unique source-component identity and explicit conflicting concurrent replay coverage. Source-document authenticity and allocation-basis suitability remain manual/review-gated; no accounting promotion is wired.
- Keep PR #6 draft/unmerged and live broker submission/automatic accounting promotion gated. Changes remain confined to `tarunsharma2610-del/tradepro-improved`, not original `Tradepro`.

---

## Follow-up CI diagnosis — 22 October 2026

- The corrected-fixture CI run `39732808218` failed after executing the tests: **523 passed, 1 failed, 1 warning**. The remaining failure was an overly specific expected error-message regex in the cross-connection rejection test; the service correctly rejected the trade with `Every broker trade record must belong to the evidence connection.`
- Fix committed as `6ff7d5bfc442f7fa06f6df9299b23199faf04d3d`: align the assertion with the service's actual safety error. This is a test assertion correction, not a relaxation of the connection guard.
- The exact-head CI for `6ff7d5b` must be checked before declaring the regression resolved.
- Next after CI passes: add explicit rollback coverage, then review concurrent/replayed allocation behavior and database constraints. Keep PR #6 draft/unmerged until the full required checks pass.
- Live broker submission and automatic accounting promotion remain gated. Work is limited to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains out of scope.

---

## CI failure analysis and correction — 22 October 2026

- Latest persistence-test CI failed on commit `f7d84cd695192e59bee12f1de625e570746a2e88`: backend pytest reported `519 passed, 1 warning, 5 errors`.
- Root cause from the job log: all five new persistence tests requested a `reviewed_evidence` fixture that did not exist. This was test setup failure, not evidence that the allocation assertions passed.
- Corrective commit `a1149cbff48357fd9aab006de7fe3435a89cbed0` adds a local fixture creating a user, broker connection, and reviewed contract-note evidence row using the actual model fields. The new commit must still pass exact-head CI before this issue can be considered resolved.
- Next: verify CI for the corrected head. If green, add rollback and concurrency/replay tests. If it fails, inspect job logs and fix before proceeding.
- No merge; no live-accounting promotion. Work is confined to `tarunsharma2610-del/tradepro-improved`, not original `Tradepro`.

---

## Phase 3 persistence-test checkpoint — 22 October 2026

- Added database-backed tests for successful component allocation and exact source-total reconciliation, idempotent identical replay, conflicting replay with changed total, cross-connection trade rejection, and changed fill-set rejection without partial rows.
- Tests use the existing isolated SQLAlchemy test-session fixture. They are committed to the Phase 3 branch; exact-head CI for this test commit and the documentation commits still needs verification.
- Review note: the current persistence service marks a component `RECONCILED` as soon as stored allocations sum to the source total. This is arithmetic reconciliation only, not proof that the chosen allocation basis is correct or the source document is authentic. No live-fill accounting promotion is wired to it.
- **Next:** verify exact-head CI; fix test/migration issues. Then add explicit transaction rollback coverage and consider DB-level concurrency/idempotency enforcement for simultaneous identical/conflicting imports before any merge.
- Live broker submission and automatic accounting promotion remain gated. All changes are confined to `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` is not the target.

---

## Phase 3 transactional allocation persistence checkpoint — 22 October 2026

- Added `backend/app/services/broker_charge_allocation_persistence_service.py` to validate reviewed contract-note evidence, enforce that every referenced persisted broker trade belongs to the same broker connection, and persist per-fill component allocations in a database savepoint.
- Replay handling: identical replay requests return the existing allocation rows; changed fill sets, totals, allocation values, basis, method version, currency, or rejected rows fail closed. Allocations are marked `RECONCILED` only when the full fill set exists and the sum equals the source component total exactly.
- This service uses the existing deterministic largest-remainder utility and writes a reconciliation reference. It does not authenticate the original contract-note document, choose an economically/legal basis, parse broker files, or enable accounting promotion.
- **Validation still required:** exact-head CI and DB-backed integration tests for successful allocation, identical replay, conflicting replay, cross-connection fill rejection, partial failure rollback, and migration upgrade/downgrade/re-upgrade. Treat the implementation as unverified until those pass.
- **Next:** run CI, add database-backed persistence tests and repair issues found; then review concurrency/idempotency behavior and synchronize the PR description/docs. Do not merge until exact-head CI is green.
- Keep live broker submission and automatic accounting promotion gated. Changes remain limited to `tarunsharma2610-del/tradepro-improved`; do not modify the original `tarunsharma2610-del/Tradepro`.

---

## Phase 3 allocation-math checkpoint — 22 October 2026

- Added `backend/app/services/broker_charge_allocation_service.py` with deterministic largest-remainder allocation math using Decimal values and integer paise, stable fill-ID tie-breaking, explicit method version, and source-total equality check.
- Added regression tests for source-total reconciliation, input-order independence, tie-breaking, zero weights, invalid/negative/non-finite values, unsupported basis, and paise precision.
- **Important limitation:** this is a pure allocation-math utility, not yet the durable persistence/orchestration service. It does not read reviewed evidence, bind trade rows to a connection, write immutable ledger rows, reconcile stored component totals across all fills, or gate execution promotion. A caller must select an explicitly reviewed basis appropriate to the charge component; no basis is inferred here.
- Existing schema migration/model slice had CI success at PR head `1505b71198f7f9f42ad749588597b7c8bb63eb0d`, run [39730707245](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39730707245). The newer service/tests/docs commits still require exact-head CI verification.
- **Next:** verify latest CI and correct failures; then implement a transactional persistence service that validates reviewed evidence + same-connection trades, inserts replay-safe rows, and marks a component reconciled only when the allocations sum exactly to its source total. Add DB-backed tests for idempotency, conflicting replays, foreign-connection evidence/trades, and rollback.
- Keep live broker submission and automatic accounting promotion gated. All work remains in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` must remain untouched.

---

## Phase 3 allocation-ledger implementation checkpoint — 22 October 2026

- **Branch:** `phase3/durable-per-fill-charge-allocation` (based on verified main `54342a69249c9a790544c415842ec74c9ddf57fb`).
- **Initial implementation slice:** added `BrokerChargeAllocation` model and migration `202610220010`, registered the model, and added schema-contract tests. Ledger fields capture source evidence, broker connection, broker trade record, charge component, source component total, allocated amount in INR paise precision, allocation basis, method version, reconciliation state, and an optional reconciliation reference.
- **Idempotency constraint:** unique `(evidence_id, broker_trade_record_id, charge_component)`; supported components and nonnegative amounts are database-constrained. New rows default to `PENDING_RECONCILIATION`.
- **Not yet complete:** this is the durable schema foundation only. There is not yet a persistence/allocation service, cross-record validation that evidence and trade belong to the same connection, immutable-update enforcement, deterministic rounding/residual algorithm, source-total reconciliation, or linkage to execution promotion. Do not claim live accounting is using this ledger.
- **Verification:** exact-head CI has not yet been observed for this branch. Do not merge until backend tests and SQLite/PostgreSQL migration upgrade/downgrade/re-upgrade checks pass.
- **Next:** validate migration/tests, add a service that uses Decimal/paise arithmetic only when an explicitly reviewed basis is authorized, enforces evidence/connection/trade binding and replay-safe inserts, and reconciles each source component total exactly. Ambiguous allocations must remain pending and block promotion.
- **Safety/scope:** keep live broker submission and automatic accounting promotion gated. All changes are limited to `tarunsharma2610-del/tradepro-improved`; do not modify original `tarunsharma2610-del/Tradepro`.

---

<!-- Phase 3 checkpoint sync: 2026-10-21; branch phase3/reviewed-charge-evidence-gate; commit 42a7418c674d92af9d099b1095d90af660678e2b; exact-head CI run 39638875688 passed. -->

## Latest verified Phase 3 checkpoint — 21 October 2026

- **Code/test commit:** `42a7418c674d92af9d099b1095d90af660678e2b` on `phase3/reviewed-charge-evidence-gate` in `tarunsharma2610-del/tradepro-improved`.
- **Exact-head CI:** GitHub Actions run [39638875688](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39638875688) completed successfully. Backend pytest, broker-write boundary enforcement, SQLite migration upgrade/downgrade/re-upgrade, and PostgreSQL 16 migration checks passed.
- **New regression coverage:** rejects charge evidence from non-contract-note sources and mismatched reviewer identities. Existing evidence validation covers connection binding, reference matching, reviewed status, reviewer identity and review timestamp.
- **Scope and safety:** PR #5 remains open and unmerged as of this checkpoint. Evidence metadata/hash and a review status are provenance/workflow controls, not cryptographic proof of broker authenticity. Contract-note parsing/import, immutable per-fill charge allocation, deterministic paise rounding/residual handling, source-total reconciliation, and complete replay/partial-fill/crash-recovery acceptance remain unfinished.
- **Next:** continue with a reviewed contract-note import boundary and a durable, idempotent per-fill allocation ledger; do not invent charge splits. Keep live broker submission, automatic accounting promotion and automatic scheduling disabled until release gates pass.
- **Repository constraint:** changes must remain in `tarunsharma2610-del/tradepro-improved`; do not modify the original `tarunsharma2610-del/Tradepro` repository.

---

<!-- Authoritative checkpoint refresh: 21 October 2026. Scope: tradepro-improved only. -->

## Authoritative Phase 3 checkpoint — 21 October 2026

- **Current code-and-documentation HEAD before this documentation sync:** `4fe58dd11b018d1f85000540ad2ec1b7f6f52ae5`. Its exact-HEAD push CI [run 39633514414](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39633514414) completed successfully. Backend pytest, broker-write boundary guard, and SQLite/PostgreSQL 16 migration upgrade-downgrade-reupgrade checks all passed.
- **Evidence-ledger implementation:** `6c0a382eb9fea7f386433cfdb65a65cbc53f218e`; migration correction: `c17f522bf68121a6d162a4d858cd9de8b95d45d1`. Their CI runs [39633266180](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39633266180) and [39633330531](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39633330531) both passed.
- **Implemented:** `BrokerChargeEvidence` model and migration `202610210009`; captures broker connection, report metadata, filename, SHA-256 fingerprint, byte size, parser version, and review status. Tests cover persistence, duplicate-fingerprint rejection per connection, and database constraints.
- **Limits:** a hash detects byte-level changes but does not prove broker origin. The ledger does not yet retain document bytes, import/parse the broker document, establish authenticity, or allocate charge components to fills. `REVIEWED` is a workflow status, not automatic approval to promote live accounting.
- **Next Phase 3 gate:** build a fail-closed, idempotent contract-note import/review boundary and inspect a real redacted broker contract note before selecting charge-specific allocation rules. Then implement immutable per-fill allocation records, paise rounding/residual rules, source-total reconciliation, and replay/crash/partial-fill tests.
- **Phase 3 remains in progress.** Keep live broker submission, automatic accounting promotion, and automatic scheduling disabled. Phase 2 remains closed. All changes must stay in `tarunsharma2610-del/tradepro-improved`; do not modify `tarunsharma2610-del/Tradepro`.
- Older checkpoints below are historical; this section is authoritative until replaced by a later verified checkpoint.

---

## Historical checkpoint — formerly marked Current Phase 3 checkpoint — 21 October 2026

- **Latest verified code/test HEAD:** `3963c2bf4e6ffe2bb33d327b10e2995cd243d003`. Exact-head [Backend CI run 39607630055](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39607630055) passed **484 tests, 1 warning in 29.34s**; the broker-write boundary guard passed, and SQLite/PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed.
- New Phase 3 guard: broker-reported live-fill charge references are trimmed for storage and rejected when longer than the `Execution.charge_reference` 200-character column limit. This prevents a predictable storage error from being misreported as a concurrent promotion conflict. Regression coverage is included in the 484-test result.
- The existing Phase 3 safety gates remain active: replay must match the accounted fill and exact charge evidence; only broker-reported, internally consistent charges with a non-empty audit reference are accepted; durable staged trade quantities must match broker-confirmed child fills before promotion; exchange-time ambiguity/out-of-order fills fail closed; paper positions and cash remain isolated.
- **Phase 3 remains in progress, not complete.** Remaining review includes coordinator/identity boundaries, charge provenance/allocation semantics, full partial-fill and crash/restart acceptance criteria, and any explicitly selected bridge design. Keep `BrokerFillIdentity` separate from manual `BrokerTradeRecord` unless a reviewed Phase 3 design explicitly authorizes a narrow bridge.
- Live broker submission, automatic accounting promotion, and automatic scheduling remain disabled. The original `tarunsharma2610-del/Tradepro` repository remains untouched. Phase 2 remains closed.
- This checkpoint describes the verified code commit above. The documentation synchronization commit will trigger its own CI; do not treat that documentation commit as green until its exact-head run passes. Older checkpoint entries below are historical audit trail, not current status.

---

## Historical checkpoint — formerly marked Current verified checkpoint — 21 October 2026

- **Last verified code/test checkpoint:** `00ee9bad0e962d92244da6f63da1e46ba058ad6f`; exact-head backend CI [run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) passed **472 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 reversible migration checks.
- **Last verified documentation checkpoint before this status refresh:** `391dfefc9580abf9537ee659877578033baae4fd`; exact-head backend CI [run 39568264419](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39568264419) passed.
- The Phase 2 audit covers the dependency/port matrix, broker-fill workflow boundary, idempotency and rollback, reconciliation crash recovery, transaction-level lease fencing, slow persistence, 20 concurrent expiry-boundary renewal/reclaim races, and official Upstox current-day API semantics.
- Official Upstox V2 [order-book](https://upstox.com/developer/api-documentation/get-order-book/) and [get-trades-for-day](https://upstox.com/developer/api-documentation/get-trade-history/) endpoints are current-day endpoints without documented pagination parameters. Historical trades use a separate [paginated API](https://upstox.com/developer/api-documentation/get-historical-trades/); it is not wired into the Phase 2 worker.
- **Phase 2 technical checklist is complete.** Before any Phase 3 work, require a passing exact-head CI run for the then-current `main` and explicit user approval; never infer a later commit is green from an earlier run.
- Live broker submission, automatic accounting promotion and automatic scheduling remain disabled. The original `Tradepro` repository remains untouched.

------

## Historical checkpoint — formerly marked Current verified checkpoint — 21 October 2026

- **Latest CI-verified `main` HEAD:** `7798f03200ba823d51bdd359539594b38e9830e1`; exact-head backend CI [run 39567592850](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567592850) passed.
- **Latest code/test checkpoint:** `00ee9bad0e962d92244da6f63da1e46ba058ad6f`; exact-head backend CI [run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) passed **472 tests, 1 warning**, the broker-write boundary guard and SQLite/PostgreSQL 16 reversible migration checks.
- The slow-persistence/lease-race audit is complete: the PostgreSQL row-lock test proves reclaim waits while a fenced write transaction is open; `test_postgres_high_volume_expiry_races_never_resurrect_stale_lease` passed 20 concurrent expiry-boundary renewal/reclaim races. Expired owners cannot renew, and ownership generation/token advance is verified.
- Official Upstox V2 order-book and get-trades-for-day endpoints are current-day endpoints without documented pagination parameters. Historical trades are a separate paginated API; that API is not wired into the Phase 2 worker.
- **Current task:** synchronize the remaining historical architecture/roadmap/reference-audit notes. This documentation commit needs its own exact-head CI and a final stale-status scan before Phase 2 is formally closed. Phase 3 remains blocked until then.
- Live broker submission, automatic accounting promotion and automatic scheduling remain disabled. The original `Tradepro` repository remains untouched.

------

<!-- Authoritative checkpoint audit: 2026-10-21; supersedes older status notes below. -->
## Superseding current checkpoint — 21 October 2026

- Latest test commit: [e56bf4c66f74b875a3ba8fe388138a9d688dd1e2](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e56bf4c66f74b875a3ba8fe388138a9d688dd1e2), adding failed-commit rollback coverage. Exact-head backend CI [run 39564568154](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39564568154) passed 471 tests, 1 warning, the broker-write guard and SQLite/PostgreSQL 16 reversible migrations. Documentation HEAD `adb69aeb05b70ba4fa9095fc73d9dea033d31eec` passed [run 39565251793](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39565251793).
- Reconciliation crash recovery and per-write lease fencing are complete on the earlier verified checkpoint [39561621808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39561621808): 470 passed, 1 warning, source guard and SQLite/PostgreSQL 16 reversible migrations.
- Phase 2 workflow boundary: keep BrokerFillIdentity separate from manual BrokerTradeRecord; no bridge/dual-write. Follow SAFETY_BRANCH_PORT_MATRIX.md for phase-aware dependency decisions. Do not wholesale-merge the divergent safety branch or introduce real broker orders.
- Phase 2 engineering checks are verified. Complete the synchronized-documentation checkpoint and confirm its exact-head CI before starting Phase 3. Preserve PAPER defaults; live submission, automatic accounting promotion and scheduling remain disabled. Original Tradepro must remain untouched.

## Authoritative checkpoint audit — 21 October 2026

- **Repository/branch:** `tarunsharma2610-del/tradepro-improved`, `main`. The original `tarunsharma2610-del/Tradepro` repository is a protected baseline and must remain untouched.
- **Latest repository HEAD before this audit update:** `a297b1a356c133aaca0ed10079eb5226c03b747b` — documentation-only commit `docs: synchronize Phase 2 status with passing CI evidence`.
- **Latest code/test commit:** `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`. Recorded exact-commit backend CI run [39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed **466 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles. Frontend run [39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript and Next.js build.
- **Previously verified documentation CI:** commit `6407c5a05865c1be0ef673d3bb5e71c0231ef8da`, run [39556816828](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556816828), backend job completed successfully. The later documentation-only commit `a297b1a356c133aaca0ed10079eb5226c03b747b` was found on `main`; CI for that exact HEAD was not independently established before this audit update. Do not infer exact-head CI success from an earlier commit.
- **Phase 2 checkpoint verified in project records:** atomic run/lease finalization; stale-owner protection; cancellation and interrupted-run recovery; inconsistent lease token/expiry rejection; five-record renewal boundary; and incomplete-summary warnings for `WORKER_INTERRUPTED` and `LEASE_LOST`.
- **Historical audit disposition — superseded:** slow database persistence and high-volume lease-expiry/renewal races have now been tested. PostgreSQL CI run [39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) passed the slow-persistence lock test and the new 20-iteration concurrent expiry-boundary renewal/reclaim test. Do not reopen this audit unless a regression appears.
- **Safety constraints remain:** no real broker orders in tests; live broker submission, automatic accounting promotion, and automatic scheduling remain disabled; keep `BrokerFillIdentity` separate from `BrokerTradeRecord`; do not wholesale-merge the divergent safety branch.
- Older checkpoint entries below are retained as history, not current instructions. This top section is the authoritative current state. After this documentation commit, verify CI for its exact HEAD before treating the checkpoint audit as fully closed.

<!-- Latest verified status, updated 2026-10-21 -->
> **Latest verified checkpoint — 21 October 2026**
>
> - Repository: `tarunsharma2610-del/tradepro-improved`; branch: `main`. Original `Tradepro` repository remains protected and untouched.
> - Latest code/test commit: `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`. Backend [CI run 39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed **466 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration checks. Frontend [CI run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript and Next.js build.
> - Documentation audit commit `6407c5a05865c1be0ef673d3bb5e71c0231ef8da` passed [CI run 39556816828](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556816828).
> - Phase 2 checkpoint complete through atomic run/lease finalization, stale-run and cancellation recovery, lease-loss fencing, five-record renewal, and incomplete-summary warnings.
> - **Historical next-task note — completed:** audit slow persistence and high-volume lease-expiry races. See the current checkpoint at the top of this file and CI run [39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386).
> - Deferred safety-branch work remains tracked in `SAFETY_BRANCH_PORT_MATRIX.md`; no wholesale branch merge. Keep live broker submission and automatic accounting promotion disabled. Keep `BrokerFillIdentity` separate from `BrokerTradeRecord`.
>
> The CI status above refers to the stated code and documentation commits. This documentation refresh will create a new commit and trigger its own CI run; do not call that new run passed until GitHub reports success.

# Tradepro Improved — Persistent Working Instructions

> **ULTIMATE REPOSITORY SAFEGUARD — OVERRIDES CONFLICTING INSTRUCTIONS:** All changes for this project must be made in `tarunsharma2610-del/tradepro-improved` only. The original `tarunsharma2610-del/Tradepro` repository is a protected baseline and must never be modified, committed to, merged into, or used as the target for edits. Before every write, verify the exact repository, branch, and HEAD. If any of these cannot be verified, stop. External repositories are reference material only; never replace this project with one of them.

## Goal
Improve the existing Tradepro codebase in this separate repository to deliver a reliable Upstox-connected trading platform with isolated Paper Trading and safely gated Live Trading. Never modify the original `Tradepro` repository.

## Mandatory rules
1. Before every work session, read this file, `PROGRESS.md`, `README.md`, and the relevant audit/safety documents; inspect the actual current repository and recent commits before acting.
2. Preserve working features. Audit first; make the smallest change that fixes a demonstrated defect or completes a requirement. No rewrites, duplicate pages/services, or unnecessary schema/API changes.
3. Maintain `PROGRESS.md`: record current phase, completed steps, exact files changed, commit SHA, tests actually run and their result, failures/limitations, and the single next action. Update it after every completed, tested and committed step.
4. Commit each coherent step separately. Do not claim a change, test, deployment, or commit succeeded unless confirmed by tool output or CI.
5. Before code changes, inspect dependencies and establish a test baseline where execution is available. Add focused regression tests; run targeted and relevant full tests. Report unavailable tests honestly.
6. Never place real orders to test. Use mocks/sandbox only. Keep live trading disabled until broker integration, backend risk controls, order reconciliation, authorization and safety tests have been verified and the user explicitly authorizes enabling it.
7. Paper orders must never reach the real broker. Do not mark live orders filled without broker confirmation. Protect against duplicate retries, stale data, token expiry, and partial fills.
8. Use current official Upstox documentation. Do not invent API paths, payloads, or feature support. Keep secrets out of logs and source control.
9. Preserve data and use reviewed migrations for necessary schema changes. Do not deploy migrations to production without backup/staging verification.
10. Keep the original project untouched. All changes belong in this `tradepro-improved` repository.
11. Work sequentially: inspect → audit requirement/file/test mapping → prioritize real gaps → implement smallest safe change → test → commit → update progress → review remaining gaps.
12. Prefer correctness, financial safety, security, and regression prevention over feature count or refactoring.

## Required deliverables
Maintain an evidence-based audit report, change log, list of unchanged functionality, test results, deployment/migration instructions, limitations/manual setup, and a clear statement of what Paper/Live functions are actually implemented and verified.

## Known high-priority gaps from current audit
- Live order placement remains unavailable and must stay disabled. The intent-based Phase 2 path has pure order/trade normalization, strict intent matching, versioned status persistence, idempotent `BrokerFillIdentity` storage, and an explicit on-demand GET-only reconciliation worker with leases, safe run/issues records, and owner-scoped read API/UI; tests use mocks and no real-account read has been verified. A separate manual `Order` path now has `BrokerTradeIngestionService`, `BrokerChildOrderReconciliationService`, `BrokerOrder`/`BrokerTradeRecord` staging, and an unregistered `LiveFillAccountingService`. These two paths are not connected: do not assume `BrokerFillIdentity` and `BrokerTradeRecord` are interchangeable. The Phase 2 decision is to keep them separate and prohibit a bridge/dual-write in Phase 2; any bridge is a separate reviewed Phase 3 design. No worker-to-accounting promotion, shared live Order/Execution/Position/cash/P&L lifecycle, or live broker submission is enabled. Read `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` before live-order code. Do not assume Upstox tags provide broker-enforced idempotency.
- Portfolio-wide risk controls are configurable per portfolio and enforced on paper/strategy order paths; continue checking threshold/boundary and concurrent-order behavior.
- Instrument-master sync has a completeness-gated reconciliation policy and passed a real upstream download into disposable SQLite; never point the verification script at the production DB.
- Upstox V3 streaming client/routes exist with mocked tests; a real OAuth session and deployment topology still need verification. The manager is process-local; use one API worker until shared stream state is implemented.
- OAuth migration is CI-tested on clean SQLite but still requires backup-safe staging verification.
- Do not implement any of these blindly: inspect the current code and official API docs first.


## Live-order implementation gate (added 2026-10-17)
Before implementing any live-order code, read `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`, `LIVE_TRADING_SAFEGUARDS.md`, `ARCHITECTURE.md`, current broker API documentation and current tests. The user approved the design on 2026-10-17; the approval is recorded in `PROGRESS.md`. Phase 1 durable records/repository safeguards have passed the current automated PostgreSQL concurrency test and clean SQLite/PostgreSQL 16 reversible-migration checks ([run 39048147046](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048147046)); actual deployment-engine staging verification is still required. Continue only the approved reconciliation-only phase: pure matching and repository-only reconciliation safeguards may be implemented with tests. Do not add broker submission, cancellation, or network-driven worker behavior before the roadmap gates are satisfied and the user explicitly authorizes that scope.

Mandatory invariants: durable intent and unique key + canonical payload hash; persist intent/outbox/audit before network I/O; never blindly retry an ambiguous POST; reconcile order history/book/trades before recovery; deduplicate broker fills by stable identity; recheck risk and account kill switch at dispatch; preserve paper/live isolation; never use a real order for testing. Update audit, README, architecture and progress after each tested/committed step. Keep live submission disabled until the user explicitly authorizes a controlled release after all gates pass.


## Roadmap and commit verification
Before continuing implementation, read `ROADMAP.md` along with `PROGRESS.md`, `AUDIT_REPORT.md` and `ARCHITECTURE.md`. After each change, update the progress tracker, commit the change to `tradepro-improved`, verify the commit is on `main`, and check the workflow result for that exact commit. Never infer a newer commit passed because an older workflow passed. Keep live submission disabled until all roadmap gates and explicit authorization are complete.


## Historical checkpoint — formerly marked Current Phase 2 checkpoint — 2026-10-17
Out-of-order broker status resolution against persisted fill evidence is implemented and verified by [run 39056392873](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056392873): 294 tests passed, 1 warning; SQLite/PostgreSQL 16 migrations passed. Before adding broker reads, read [READ_ONLY_RECONCILIATION_WORKER_DESIGN.md](READ_ONLY_RECONCILIATION_WORKER_DESIGN.md). The next implementation step is a narrowly typed read-only Upstox client and worker; it must not expose place/modify/cancel methods. No live submission, broker polling or accounting updates are enabled.


### Read-only client sub-step — 2026-10-17
`backend/app/brokers/upstox/reconciliation_client.py` and its mocked contract tests are implemented. Exact run [39056868434](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056868434) passed 309 tests, 1 warning. This is only the transport boundary, not a worker: next add orchestration using this narrow client, verify user/connection ownership and token expiry before network I/O, add bounded 429/5xx retry and job leases, and keep the worker read-only. Never call methods on the general order execution adapter from the reconciliation worker.


### Lease foundation — 2026-10-17
The durable per-connection reconciliation lease model, reversible migration and repository are implemented and CI-tested: [run 39057273255](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39057273255), 318 passed, 1 warning. The lease is not yet connected to a worker. Next implement worker orchestration using only `UpstoxReadOnlyReconciliationClient`, and add PostgreSQL concurrency tests; never use the general write-capable broker adapter for reconciliation.


### Read-only reconciliation worker checkpoint — 2026-10-17
`backend/app/services/live_order_reconciliation_worker.py` is implemented and mocked-CI-tested. It injects only `UpstoxReadOnlyReconciliationClient`, validates the authenticated user's owned Upstox connection and token usability, claims/renews/completes `LiveReconciliationLease`, reads order book and daily trades, applies bounded read-only retries, strictly matches orders, and persists/deduplicates fills. Latest test commit `bffeefc7921fd96c8fbeab1b201eb3088e87f497` passed [run 39058734080](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39058734080): 338 passed, 1 warning; SQLite/PostgreSQL 16 migration checks passed. No real broker request or order action occurred. The worker is not scheduled or exposed via API. Next: inspect official current-day/history pagination semantics, add durable job summaries/manual-review visibility and crash-boundary tests. Do not enable live order submission or connect the worker to a write-capable adapter.


### Durable worker run summaries — 2026-10-17
`LiveReconciliationRun`, migration `202610170004`, and `LiveReconciliationRunRepository` are implemented. Worker passes persist a `RUNNING` record after lease acquisition and a terminal record with safe status/error and whitelisted non-negative numeric counters. No raw payload, credential or exception text is stored. Test commit `0e69fb2efea692f2f675604ef3312cb1954ecc39` passed [run 39059271937](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059271937): 340 passed, 1 warning; SQLite/PostgreSQL 16 migrations passed. Next: add a durable manual-review issue queue and stale-run recovery, then cover crash/restart boundaries. Keep worker unscheduled and live submission disabled.


### Manual-review issue queue checkpoint — 2026-10-17
`LiveReconciliationIssue` and migration `202610170005` are implemented. `LiveReconciliationIssueRepository` validates user/connection/run/intent ownership, accepts only whitelisted issue types, rejects credential-like fields and oversized details, deduplicates by fingerprint per connection, and increments/reopens recurring issues. The worker records safe issues for invalid rows, unmatched orders, and persistence/link/status conflicts. Exact fix commit `71b5668533f0461c12374319e496665cbda7e61c` passed [run 39059749652](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059749652): 342 passed, 1 warning; SQLite/PostgreSQL 16 migrations passed. Next: expose issues through a read-only owner-scoped API/UI and add a separately authorized resolution workflow, plus stale-run recovery and crash/restart tests. Do not expose raw broker data or credentials.


### Owner-scoped reconciliation read API — 2026-10-17
Authenticated GET endpoints `GET /api/v1/reconciliation/runs` and `/issues` now list the current user's safe run summaries/issues only. The repository filters by `user_id`, limits are capped at 100, and typed response schemas omit raw broker records and credentials. Exact code commit `f65b4ba20ce9a1dacfe40580d8042cd98f36c19f` passed [run 39060230705](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39060230705): 345 passed, 1 warning; SQLite/PostgreSQL 16 migration checks passed. No run trigger or issue mutation route exists. Next: add frontend review UI and stale-run recovery/crash-boundary tests, then assess historical trade retrieval from official docs.


### Reconciliation review UI — 2026-10-17
`frontend/app/reconciliation/page.tsx` is now linked from the dashboard. It displays run summaries and sanitized manual-review issues from the authenticated read-only endpoints and supports status filtering/manual refresh. It does not trigger the worker or mutate issues/orders. Commit `e4343dcb225c1f332b6c89399694d0a29a5df739` passed frontend TypeScript/Next.js checks and backend CI: 345 passed, 1 warning, SQLite/PostgreSQL 16 migrations passed. Next: stale-run recovery and crash-boundary tests, then official historical-trade pagination semantics. Keep issue resolution and live submission disabled until separately designed/reviewed.


## Reference repository audit and current blocking checkpoint — 2026-10-20

The targeted comparison is recorded in [REFERENCE_REPOSITORY_AUDIT.md](REFERENCE_REPOSITORY_AUDIT.md). It reviewed AI Trading Platform (MIT), Algo Options Platform (MIT), OpenAlgo (AGPL-3.0) and Kite Algo Bot (MIT). Do not copy OpenAlgo source without an intentional AGPL compliance decision. Use references to fill demonstrated gaps only; preserve existing Tradepro Improved architecture and avoid duplicate engines.

## Live-fill accounting recovery and verification — 2026-10-20

The deleted service, original tests and migration 0008 are restored to their original paths. Supporting models `BrokerOrder`, `BrokerTradeRecord`, `LivePosition` and migrations `202610180006` / `202610180007` were added to complete the chain. GitHub Actions [run 39475387511](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39475387511) passed **355 tests, 1 warning**, plus SQLite and PostgreSQL 16 migration upgrade → downgrade → re-upgrade checks at code/test checkpoint `a906274b98f3f7e0c913f376128f4996b996c52b`.

This is not a complete live-fill pipeline: the service remains unregistered, ingestion and reconciliation integration remain outstanding, and no real-account or production migration was performed. Keep live order submission disabled. Continue Phase 2 reconciliation release gates and crash/recovery/fill-linkage checks. Do not delete the recovered files without explicit user approval.


## Current safety checkpoint — 2026-10-21

- Current code/test checkpoint: `84f3a3e48a64b6e1d764a87a2b337b2a8f052741`; GitHub Actions [run 39482592808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39481385581) passed **439 tests, 1 warning**, including SQLite/PostgreSQL 16 reversible migration checks.
- The safety branch's 18 October run passed 456 tests, while main's earlier parser checkpoint passed 406. These runs used different test trees. Main now has 38 test modules; the safety branch has 48, with 20 safety-only modules remaining. See `SAFETY_BRANCH_PORT_MATRIX.md`; do not infer deleted functionality from raw counts.
- Broker trade staging and child-order reconciliation are implemented as an isolated manual-Order path. They update staged records and child metadata, not parent-order accounting. The live accounting service remains unregistered.
- Before further integration, inspect the intent-based `BrokerFillIdentity` worker path versus the manual `BrokerTradeRecord` path and explicitly document whether they are distinct by design or need a safe bridge. Keep live writes and automatic accounting promotion disabled.


### Broker-write guard follow-up — 2026-10-21
The AST source guard was tightened after review: no whole-file Upstox adapter exemption remains, and PAPER portfolio exceptions are restricted to the named endpoint functions. Regression tests cover unexpected adapter calls and unrelated helpers. The exact current `main` head still requires CI verification; do not mark this checkpoint green based on the earlier 439-pass run. Keep live submission and automatic accounting promotion disabled.


### Exact-head verification — 2026-10-21
Current main `975717b05a3aa5faa030f3f9e177dbcf6066daf3` passed [GitHub Actions run 39550130192](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39550130192): **447 passed, 1 warning**, broker-write source guard passed, and SQLite/PostgreSQL 16 reversible migrations passed. The previous CI failure was a guard-test line-number assertion, corrected in this head. Continue Phase 2 by reviewing the `BrokerFillIdentity` and `BrokerTradeRecord` workflow boundary; do not bridge them until transactional identity, ownership, conflict, replay, rollback and recovery rules are explicit. Live submission and automatic accounting promotion remain disabled.

### Fill-workflow boundary rule — 2026-10-21
Keep intent-based `BrokerFillIdentity` reconciliation and manual-order `BrokerTradeRecord` staging/accounting separate unless a reviewed coordinator is explicitly implemented. Their independent unique constraints do not prevent the same broker trade from appearing in both tables. Never dual-write or promote worker evidence automatically. Any future bridge must define canonical identity, owner/connection/order/intent scoping, conflicts, transaction-safe idempotency, rollback and crash recovery. Regression tests added at `3683082509c4b331ab9c7ebceb928e925414de35` enforce that the worker and its replay do not create manual staging/accounting rows or change portfolio cash; exact-head CI must be verified before the next code slice.

### Reconciliation crash-recovery rule — 2026-10-21
Stale reconciliation summaries may be marked `FAILED/WORKER_INTERRUPTED` only through owner/connection-scoped recovery and only when no unexpired lease is active. Preserve the summary counters. Never retry broker calls or change fill/accounting rows as part of run-summary recovery. The current `fail_orphaned_runs` method is not automatically scheduled; do not wire it into background execution until exact-head CI and crash-boundary behavior are reviewed. Live broker submission and automatic accounting promotion remain disabled.

## Historical checkpoint — formerly marked Current Phase 2 checkpoint — 2026-10-21

- Verify against main HEAD `0ce59a7965e3e96a425fa8ae30c841eb0cb755bc` and [CI run 39552821228](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552821228): 461 backend tests passed, 1 warning; broker-write guard and SQLite/PostgreSQL 16 migration cycles passed.
- Lease token and expiry must be both present or both absent. Do not allow claims or orphan recovery to silently overwrite half-populated lease records.
- `WORKER_INTERRUPTED` means reconciliation counters may be incomplete. Do not infer no fills from zero counters and do not auto-retry broker requests or promote accounting.
- Next work: review lease completion versus terminal run-summary persistence for transaction atomicity; add focused lost-lease and crash-ordering tests before lifecycle changes.
- Keep `BrokerFillIdentity` and `BrokerTradeRecord` separate; live broker submission, automatic accounting promotion, and automatic scheduling remain disabled.


## Historical checkpoint — formerly marked Current Phase 2 checkpoint — 2026-10-21

- Verified code/test HEAD `8f967adaa2328f16a0a08a104c3ec394e62f9310`; [CI run 39553655005](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39553655005) passed 463 backend tests, 1 warning, broker-write guard, and SQLite/PostgreSQL 16 migration cycles.
- Use `LiveReconciliationRunRepository.finish_with_lease` for worker terminalization. Do not split lease release and run-summary persistence into separate commits.
- If lease ownership has changed, preserve the newer lease and terminalize the old run as `LEASE_LOST`. If summary persistence fails, roll back lease release and allow expiry/recovery to handle the incomplete run.
- Next: audit cancellation/unexpected exception paths and lease renewal/expiry under concurrency. `WORKER_INTERRUPTED` means counters may be incomplete.
- Keep `BrokerFillIdentity` and `BrokerTradeRecord` separate; live submission, automatic accounting promotion, and automatic scheduling remain disabled.


## Historical checkpoint — formerly marked Current Phase 2 checkpoint — 2026-10-21

- Verified code/test HEAD `2ac6bfaafd3475ee63360bd0049b0b6987236bc1`; [CI run 39553981172](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39553981172) passed 465 backend tests, 1 warning, broker-write guard, and SQLite/PostgreSQL 16 migration cycles.
- Worker terminalization must use the atomic run/lease finalization method. Stale lease owners are marked `LEASE_LOST` without clearing a newer owner's token.
- Cancellation during broker reads is expected to leave a recoverable RUNNING summary/lease; after expiry, recovery marks it `WORKER_INTERRUPTED`. Its counters must not be treated as complete.
- Next: audit lease-renewal cadence for large batches and test expiry races around per-record persistence.
- Keep `BrokerFillIdentity` and `BrokerTradeRecord` separate; live submission, automatic accounting promotion, and automatic scheduling remain disabled.


## Historical checkpoint — formerly marked Current Phase 2 checkpoint — 2026-10-21

- Code/test HEAD `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`; backend [run 39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed 466 tests, guard and migrations; frontend [run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript/build. Latest documentation commit `7f9a1f3293ffc67579042a87b82cb2fb03ffba1f` passed [CI run 39556090575](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556090575).
- Renew the reconciliation lease every 5 records during trade/order batches. If ownership is lost, stop before the next record and do not clear the replacement owner's lease.
- UI must warn for both `WORKER_INTERRUPTED` and `LEASE_LOST`; summary counters can be partial.
- Next: inspect a single slow persistence operation and high-volume processing for lease-expiry races; add transaction-level fencing if needed.
- Keep `BrokerFillIdentity` and `BrokerTradeRecord` separate; live submission, automatic accounting promotion, and automatic scheduling remain disabled.


## Phase 3 live-fill accounting checkpoint — 2026-10-21

- Latest reviewed code HEAD at this checkpoint: `ef60ec93d39543c644dfd557f6f73b48ab793b60`.
- Exact-head [Backend CI run 39609474410](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39609474410) completed successfully: **485 passed, 1 warning in 30.25s**; broker-write boundary guard passed; SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed.
- The one warning is non-failing; CI logs also report GitHub Actions Node.js 20 deprecation notices.
- Existing safeguards cover replay identity/charge validation, broker-confirmed fill quantities, cumulative child/order quantity limits, rejected-order protection, and atomic live-position/execution updates. This CI result verifies the current HEAD, not completion of all Phase 3 requirements.
- **Open Phase 3 requirement:** define and test the fee-allocation contract when a broker contract-note charge total covers multiple fills. The current API accepts a per-promotion breakdown and validates that its total equals its six components; it does not itself establish how a multi-fill contract-note total is allocated. Do not claim this issue resolved or wire in a coordinator/identity bridge until the rule is designed and regression-tested.
- Safety constraints unchanged: do not enable live broker submission, automatic accounting promotion, or automatic scheduling; keep `BrokerFillIdentity` and `BrokerTradeRecord` separate pending a reviewed bridge design. Phase 2 remains closed.


## Phase 3 checkpoint refresh — 2026-10-21

- **Repository boundary:** all current Phase 3 work is confined to `tarunsharma2610-del/tradepro-improved`, branch `main`. The original `tarunsharma2610-del/Tradepro` is a protected baseline and must not be modified.
- **Current HEAD at audit start:** `3b5c8831d4f3475eee320176b3c06bdbd5364bd2` (source-ledger design-gate documentation). The documentation synchronization commit created after this note requires its own exact-HEAD CI result.
- **Latest confirmed backend CI during this audit:** [run 39618611385](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39618611385) completed successfully on **commit `49f95bdd5f20ee99b21a573087c6e97a9bc03526`**, with **485 passed, 1 warning in 30.65s**. The broker-write boundary guard and SQLite/PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade steps passed. This run is an older SHA, not current HEAD; do not label later commits green based on it.
- **Phase 3 status:** in progress. Current blocker is verified actual-charge evidence and an approved allocation basis. Reviewed Upstox documented APIs provide trade data, aggregate charges, or estimates, but no verified per-fill actual-charge source/contract-note ingestion capability was found in the reviewed adapter/API catalogue. Do not treat estimates as actual charges or allocate aggregate totals by guess.
- **Next engineering sequence:** establish authoritative source format and retention/security boundary; then implement immutable source evidence and per-fill allocation records, migration, transactional reconciliation/idempotency, and required regression tests; finally verify exact-HEAD CI.
- **Safety:** live broker submission, automatic accounting promotion, and automatic scheduling remain disabled. Phase 2 remains closed. This checkpoint is status tracking, not a claim that Phase 3 charge allocation is implemented.

## Phase 3 source-document access and integrity audit — 22 October 2026

- Audited the existing `BrokerChargeEvidence` model and `require_reviewed_charge_evidence` service on `phase3/durable-per-fill-charge-allocation`. The model persists filename, SHA-256, byte size, parser-version metadata, report reference, and review provenance, but explicitly stores the original document outside the table.
- No broker-contract-note-specific upload/retrieval endpoint or storage adapter was found in the audited application entrypoint, API route locations, service paths, and configuration. This is a scoped audit finding, not proof that no generic file handling exists elsewhere.
- The current evidence validator checks evidence identity/connection, source kind, reviewed status, reviewer identity/timestamp, and report reference. It does not retrieve the original bytes, recompute SHA-256/byte size, or parse an authoritative charge-component total.
- **Step 1 remains in progress; no source-storage implementation is claimed.** Before implementation, define a private, persistent, non-web-served storage boundary and a stable evidence-ID-to-object mapping. Retrieval must enforce authorization, prevent path traversal, verify the exact byte count and SHA-256 before parsing, and fail closed on missing/changed content. Do not treat a matching hash alone as proof of broker authenticity.
- Next implementation should add a configurable storage adapter and durable object key tied to the evidence record, then authenticated upload/retrieval and integrity tests. Choose the deployment-backed persistent volume only after confirming the Docker/VM volume layout; do not silently store source documents in an ephemeral container filesystem or Git.
- The prior successful PR-head CI run applies to its exact tested commit only; documentation updates require a fresh CI run on the resulting exact head. PR #6 remains draft/unmerged. Live broker submission and automatic accounting promotion remain disabled. All work stays in `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is not the target.

## Phase 3 private contract-note storage implementation — 22 October 2026

- Added a configurable `BROKER_CHARGE_DOCUMENT_ROOT` (default `/var/lib/tradepro/contract-notes`) and a named Docker volume mounted only into backend and worker containers. The volume is not mounted into Nginx or the frontend.
- Added authenticated upload and download endpoints under `/api/v1/broker-charge-evidence`. Upload is restricted to a broker connection owned by the authenticated user, has a 10 MiB limit, uses an application-generated UUID key, records SHA-256, exact byte size, and uploader identity (`received_by_user_id`), and leaves evidence in `RECEIVED` status. It does not auto-review or promote accounting.
- Added a storage service that writes atomically with restrictive directory/file permissions, validates opaque storage keys against path traversal, and verifies both byte count and SHA-256 before returning source bytes. Missing or changed source bytes fail closed.
- Added Alembic revision `202610220011` to add nullable `storage_key` for backwards compatibility with existing evidence metadata; legacy rows without stored source bytes return unavailable rather than pretending the source was verified.
- Added storage-service tests for successful retrieval, tampering, missing documents, invalid/path-traversal keys, empty content, and deletion, plus API tests for owner-scoped upload/download and tamper rejection. **CI and migration upgrade/downgrade checks on the exact latest head remain required before treating the implementation as verified.**
- SHA-256 only establishes byte-for-byte continuity with the recorded upload; it does not establish that the document genuinely originated from the broker. Independent source-component parsing/review, persisted component provenance, full fill-set/amount/currency/rounding reconciliation, and atomic promotion remain later Phase 3 gates.
- PR #6 remains draft/unmerged. Live broker submission and automatic accounting promotion remain disabled. Scope remains exclusively `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is not the target.

## Phase 3 durable source-component provenance — 22 October 2026

- Added `BrokerChargeSourceComponent` and Alembic revision `202610220012` to persist a charge component's evidence ID, exact source SHA-256, component name, INR amount, source page/row locator, extraction method, parser-version field, extracting user, status, reviewer, review timestamp, and review note.
- This first workflow is explicitly **manual transcription**, versioned as `manual-transcription-v1`; it does not claim that a broker-specific parser exists or that the amount was machine-extracted. No PDF/CSV parser or broker document format was assumed.
- Added authenticated endpoints to record a component as `PENDING_REVIEW`, verify the original file's stored fingerprint/size before recording or reviewing, and require a distinct platform administrator (the existing `is_admin` role) to confirm the amount against the original source before it becomes `VERIFIED`. Rejected components remain rejected; duplicate component entries and non-INR currencies fail closed.
- Added API regression tests for pending-before-review behavior, same-user review rejection, distinct-reviewer verification, tampered-source rejection, invalid currency, and duplicate component prevention.
- CI run [39742979087](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39742979087) passed on code head `c1004fb5718592fb76ccf50c4007a0d8aec11fb7`: 542 tests passed, 1 warning; broker-write boundary guard and SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks passed. **This documentation synchronization creates a newer head, so recheck exact-head CI before merge.** This is source-component provenance, not the final reconciliation gate: allocation totals must still match verified source components, exact eligible fill sets, currency, and rounding policy under a transaction before any future promotion is considered.
- PR #6 stays draft/unmerged. Live broker order submission and automatic accounting promotion remain disabled. All changes target `tarunsharma2610-del/tradepro-improved`, never original `Tradepro`.

## Phase 3 allocation-ledger verification — 22 October 2026

- Added `verify_component_allocation_ledger` as a fail-closed verifier for a reviewed source component and its allocation rows. It rechecks the stored document fingerprint/size and validates component/evidence review provenance.
- Source-component review persists the canonical sorted eligible trade-record UUID set, its SHA-256 manifest fingerprint, the approved `largest-remainder-v1` method, and the reviewer-approved allocation basis. The reviewer must identify persisted fills from the same broker connection; duplicate/missing/cross-connection IDs are rejected.
- Verification requires the allocation ledger's exact fill set to equal the reviewed manifest, every source total to equal the independently reviewed component amount, currency/method/basis to match, and the paise-exact allocated sum to equal the source amount. Evidence, component, allocation rows, and fills are locked during verification.
- Transactional promotion is implemented in `promote_verified_component_allocations` in `broker_charge_allocation_reconciliation_service.py`. It calls the verifier while holding the transaction locks, requires the authorized source-component reviewer, promotes the entire eligible set to `RECONCILED` with a deterministic durable reference, and supports exact idempotent replay. It uses a savepoint and does not commit the caller's outer transaction; callers must commit only with the enclosing accounting operation. It is service-only, not exposed as a public API endpoint.
- Mismatched source bytes, provenance, fill set, amount, currency, method, basis, mixed/rejected statuses, or stale references fail closed; the full set remains pending or the transaction rolls back. No partial promotion is allowed.
- Tests cover exact verification, fill-set/source-total/tampered-source failures, successful atomic promotion, idempotent replay, wrong-reviewer rejection, and outer-transaction rollback. CI run [39745393196](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39745393196) passed on code head `007c41796da7413823a98f92360d93af074ab88e`: **549 tests passed, 1 warning**; broker-write guard and SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks passed.
- CI run [39745820117](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39745820117) passed on exact head `5139146d48cb3f5906db77014a93b5d20ead3146`: 549 tests passed, 1 warning; broker-write guard and SQLite/PostgreSQL 16 migration round-trips passed. This is a historical exact-head checkpoint; every later code or documentation commit must receive its own exact-head CI verification before merge. PR #6 remains draft/unmerged. Live broker order submission remains disabled.

## Phase 3 transactional allocation promotion — 22 October 2026

- Added `promote_verified_component_allocations` as an internal service (not an API endpoint). It re-runs the source-document, review-provenance, exact fill-set, amount, INR currency, rounding-method, approved-basis, and total checks while locking the relevant evidence, component, allocation, and trade rows.
- Promotion sets the complete eligible allocation set to `RECONCILED` and writes a deterministic durable reference tying the component UUID, source SHA-256, and eligible-fill-set SHA-256. It rejects mixed, rejected, stale-reference, incomplete, or mismatched sets.
- The operation runs inside a savepoint and **never commits the caller's transaction**. The caller must commit only after the whole enclosing transaction succeeds. A repeated exact promotion is idempotent; tests cover successful promotion, replay, unauthorized actor rejection, and outer-transaction rollback.
- This internal service is not wired to an automatic accounting path or exposed as an API endpoint. Live broker submission remains disabled; the service does not itself create accounting entries or send orders.
- CI run [39745393196](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39745393196) passed on promotion-code head `007c41796da7413823a98f92360d93af074ab88e`: 549 tests passed, 1 warning; broker-write guard and SQLite/PostgreSQL 16 migration round-trips passed. Step 4 code is verified at that head; any subsequent code or documentation commits require another exact-head CI check before merge. PR #6 remains draft/unmerged and all changes remain exclusively in `tarunsharma2610-del/tradepro-improved`.

## Phase 3 final audit follow-up — 22 October 2026

- Preserved rejected source-component history: each evidence/component pair now uses a positive revision number; a new transcription is allowed only after prior revisions for that component are rejected. Pending or verified duplicates remain blocked, and the unique evidence/component/revision constraint protects concurrent attempts.
- Promotion now rechecks that the recorded reviewer is still an active platform administrator at promotion time, in addition to matching the reviewed component identity. Loss of authorization fails closed and leaves allocations pending.
- Exact-head CI run [39746382703](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39746382703) passed on `6870fdc8a0bee91f486a250351eac1beb7edbf3d`: 551 tests passed, 1 warning; broker-write guard and SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks passed. Any later commit requires a fresh exact-head CI check before merge.
- PR #6 remains draft/unmerged. Live broker order submission remains disabled, and allocation promotion is still an internal transaction-owned service rather than a public API endpoint.


## Phase 3 exact-head verification checkpoint — 22 October 2026

- Current reviewed PR head at checkpoint start: `2d524632a98167e360be249a5bf255a55cae6daf` on `phase3/durable-per-fill-charge-allocation` in `tarunsharma2610-del/tradepro-improved`.
- Exact-head GitHub Actions run [39746755812](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39746755812) completed successfully: 551 tests passed, 1 warning; broker-write boundary guard passed; SQLite and PostgreSQL 16 migration round-trip checks passed. This supersedes earlier notes in this document that described this commit's CI as pending.
- The PostgreSQL concurrency test exists at `backend/tests/test_broker_charge_allocation_postgres_concurrency.py`; it requires CI's dedicated `TEST_POSTGRES_URL`. The previous documented successful PostgreSQL race run is still a separate earlier commit; confirm the current run's test job environment/logs before claiming this exact run exercised the race test.
- Document storage writes atomically to a private file and verifies SHA-256 and byte count on retrieval. Deployment backup/restore and cleanup of orphaned files remain operational follow-ups; code-level storage tests do not prove production recovery procedures.
- Outstanding review gates: confirm the current CI run executed the PostgreSQL race test; review transaction/authorization behavior and accounting integration; verify deployment volume backup/restore; assess broker-source authenticity limitations. SHA-256 proves byte continuity against recorded evidence, not broker-origin authenticity.
- PR #6 remains draft and unmerged pending review and explicit approval. No live broker order submission or automatic accounting posting is enabled. Scope remains `tarunsharma2610-del/tradepro-improved`; do not modify original `Tradepro`.


## Follow-up: upload rollback cleanup and residual orphan risk — 22 October 2026

- Re-reviewed `backend/app/api/v1/broker_charge_evidence.py` at PR #6 branch `phase3/durable-per-fill-charge-allocation`. After writing the private document, the upload endpoint commits the evidence row; on `IntegrityError` or other caught exceptions it rolls back the database session and attempts `delete_document` for the generated storage key. This is an existing compensating cleanup path and should not be described as entirely absent.
- Residual risk remains: process termination between successful file write and database commit, or failure during the compensating delete, can leave an unreferenced object. Current tests prove basic storage/read integrity but do not demonstrate crash injection or production orphan reconciliation.
- Safe next improvement: add a read-only audit command/service that enumerates only validated 32-hex storage keys and compares them with database `storage_key` values; report missing referenced files, mismatched hashes/sizes, and unreferenced files without deleting anything. Cleanup should be a separate explicit, audited operation with age/grace-period checks and approval; never delete automatically during audit.
- Operational validation still required: coordinated backup and isolated restore of both PostgreSQL `postgres_data` and `broker_charge_documents`, then verify each restored evidence object's storage key, SHA-256, and byte size. Compose mounts confirm shared runtime volume wiring, not a backup guarantee.
- Last verified CI before this documentation follow-up: run [39747922164](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39747922164) passed for commit `f87dd096b2e2f4044b1eb67fa63e277bceb136c9`; rerun and verify CI after the final documentation commit before treating this checkpoint as closed.
- PR #6 remains draft/unmerged pending final review and explicit approval. SHA-256 verifies byte continuity against recorded metadata, not broker-origin authenticity. No automatic accounting posting or live broker order submission is enabled. Scope remains `tarunsharma2610-del/tradepro-improved`; do not modify original `Tradepro`.


## Read-only contract-note storage audit checkpoint — 22 October 2026

- Implemented `audit_contract_note_storage` in `backend/app/services/broker_charge_document_storage_service.py`. It compares evidence rows to files in the configured storage root and reports missing files, size/SHA-256 mismatches, invalid storage keys, duplicate database keys, and unreferenced opaque-key files. The audit is read-only and never deletes files.
- Added regression tests for a clean store and for missing, tampered, and unreferenced files. Exact-head CI run [39749195128](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39749195128) passed on commit `e7214e970b8e2fa3e966dc339141288a30154038`: **553 passed, 1 warning**; broker-write boundary guard passed; SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks passed.
- The endpoint-level database-rollback plus cleanup-failure path is covered by a regression test. Still required: interrupted-process/crash recovery validation, an isolated coordinated PostgreSQL-plus-document-volume restore drill, and final accounting/idempotency review.
- Do not automatically delete orphaned files. Cleanup remains a separate approved, audited operation with grace-period safeguards. SHA-256 demonstrates byte continuity against recorded evidence, not broker-origin authenticity.
- PR #6 remains draft/unmerged pending final review and explicit approval. Live broker order submission remains disabled. Scope is `tarunsharma2610-del/tradepro-improved`; do not modify original `Tradepro`.


## Upload cleanup regression checkpoint — 22 October 2026

- Added a regression test for the contract-note cleanup helper when storage deletion raises `OSError`; the failure is logged and does not escape the helper, allowing the upload handler to preserve its original database exception.
- Exact-head GitHub Actions run [39750696319](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39750696319) passed on commit `279ea3e6f170dc991c243b57372b86e86db065ee`: **554 passed, 1 warning**. Broker-write boundary guard and SQLite/PostgreSQL 16 migration checks passed.
- Upload-recovery coverage is now stronger: an endpoint-level regression test forces database commit failure plus compensating file-deletion failure, then verifies the orphan is reported by the read-only storage audit. This is a simulated integration test, not a production restore drill.
- Remaining gates: coordinated PostgreSQL + contract-note-volume restore drill; independently reviewed source-origin evidence; final allocation replay/idempotency and promotion transaction review; CI verification after the next documentation or code change.
- PR #6 remains draft/unmerged. Live broker order submission remains disabled. Scope is `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is not the target.


### Phase 3 checkpoint — 2026-10-22 (contract-note upload recovery integration)

- Added a real upload-endpoint regression test that forces the evidence database commit to fail after the source bytes are written, then forces compensating file deletion to fail. The test verifies the original database exception remains visible, no evidence row persists, and the read-only storage audit identifies the unreferenced opaque-key file without deleting it.
- CI run 39752136518 passed on test commit 5cfa76e14add51a34e6bc157ad328c74d9f2a33b: 555 passed, 1 warning; broker-write boundary guard passed; SQLite and PostgreSQL 16 migration checks completed successfully.
- This validates the simulated endpoint/database/storage failure path; it is not a production-volume backup/restore drill and does not establish contract-note authenticity beyond recorded SHA-256/size continuity.
- Remaining gates: coordinated database plus document-volume backup/restore drill; final source-evidence, exact fill-set, currency/rounding, idempotency, and atomic-promotion review; synchronize this checkpoint across all nine documents and rerun CI on the final documentation commit.
- Scope/safety unchanged: only `tarunsharma2610-del/tradepro-improved`; PR #6 remains draft/unmerged; live broker order submission remains disabled.


### Phase 3 restore-drill gate

- Do not mark backup/restore complete based on Compose volume declarations or unit tests. In an isolated environment, take a consistent PostgreSQL backup and a matching snapshot/archive of the `broker_charge_documents` volume, restore both into an isolated stack, run the storage audit, verify representative evidence hashes/sizes and database-to-file references, then record the backup identifiers, timestamps, commands, results, and any missing/mismatched/unreferenced files. No production restore has been performed by this checkpoint.


### CI verification checkpoint — 2026-10-22

- Documentation commit `13a406891b286dd8077ee1430c1d62f3b6086309` passed GitHub Actions run `39753249388` for the backend pytest workflow. That run alone establishes the backend test result; do not attribute broker-write guard or SQLite/PostgreSQL migration checks to it without separate exact-commit job evidence.
- This CI result applies to that exact commit only. These documentation updates will create a new head and require a fresh CI result before being called verified.
- Production backup/restore remains unperformed. The required isolated drill must restore PostgreSQL and `broker_charge_documents` together, then validate source hashes/sizes and database/file references; do not infer restore success from CI or volume declarations.


### Exact-head CI scope correction — 2026-10-22

- Latest verified head before this note, `bb46a17dd8578ccce1858ed820584a4348c05e8f`, passed GitHub Actions run `39753596786`: **555 passed, 1 warning in 39.40s** in the Backend pytest job.
- The run queried for that SHA exposes only the Backend pytest job. Therefore this exact-head result does not independently establish the broker-write guard or SQLite/PostgreSQL migration round-trip checks; cite earlier runs for those only at their own SHAs.
- This note creates a new documentation head; verify CI on the resulting exact head before considering it fully checkpointed. The coordinated database + document-volume restore drill remains unperformed.


### Phase 3 backup/restore runbook checkpoint — 2026-10-22

- Added `docs/PHASE3_BACKUP_RESTORE_DRILL.md`, a step-by-step isolated procedure for paired PostgreSQL + `broker_charge_documents` backup, restore into a separate target, SHA-256 artifact verification, storage-audit acceptance, and recorded reviewer sign-off.
- The runbook is a procedure only. No actual coordinated backup/restore has been performed or claimed by this commit. Keep the worker stopped in the target until integrity checks pass; never restore over production or enable live broker orders for this drill.
- Latest prior documentation commit `8b3c87da67aea8d21cca8a6748b7d27b88a1878a` passed backend pytest in run `39754157399`. This new runbook and documentation checkpoint creates a new head and requires fresh CI verification.


### Phase 3 exact-head CI and acceptance checkpoint — 2026-10-22

- GitHub Actions run 39754635028 passed on PR head 17e9f9d220e504c2a522d8c98289c2765bf02dd2: backend pytest reported 555 passed, 1 warning in 39.64s; the broker-write boundary guard passed; SQLite and PostgreSQL 16 migration round-trip checks passed in this run's job logs. Verify the exact run if this branch advances.
- Accounting acceptance remains under review: code-level checks cover exact fill-set matching, deterministic paise-level largest-remainder allocation, conflict/replay rejection, PostgreSQL evidence-row serialization, and transactional promotion. This is not proof that real contract-note source amounts or production restore have been independently validated.
- The isolated coordinated PostgreSQL + broker_charge_documents restore drill has NOT been executed. Do not claim restore success. Restore into a separate target, verify artifact checksums, file sizes and SHA-256 fingerprints, database/file references and read-only storage audit, retain logs and reviewer sign-off, and keep workers/live broker writes disabled throughout.
- PR #6 remains draft and unmerged. All work is limited to tarunsharma2610-del/tradepro-improved; the original Tradepro repository is out of scope. Live broker order submission remains disabled.
- This documentation checkpoint creates a new commit/head and therefore requires CI verification on the resulting exact head before the checkpoint is considered fully verified.


### Exact-head CI completion — 2026-10-22

- GitHub Actions run 39755207327 completed successfully on commit 5744e8433a5a486938f6e2d6bed5b705ecaea869. Backend pytest passed; broker-write boundary guard passed; SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks all passed. See https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39755207327.
- This confirms that commit only. The following documentation checkpoint will create a new head and must itself receive fresh CI verification.
- Coordinated isolated restore drill remains unexecuted; do not claim recovery acceptance. PR #6 remains draft/unmerged; live broker submission remains disabled; original Tradepro remains out of scope.


### GitHub-only environment clarification and latest CI result — 2026-10-22

- User confirmed Tradepro Improved exists on GitHub only; do not assume a user-local Docker checkout/host. All project work remains restricted to tarunsharma2610-del/tradepro-improved; original Tradepro is out of scope.
- GitHub Actions run 39755480864 passed on commit 1d1533d70eca904e9650a813c671927475cacd36. Backend test suite, broker-write boundary guard, SQLite migration round-trip, and PostgreSQL 16 migration round-trip all succeeded. Run: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39755480864.
- Restore drill is still NOT executed. Since no user-local environment should be assumed, the next recovery step must be provisioned as a disposable isolated CI/cloud environment or explicitly established as unavailable. Do not claim restore success absent captured execution evidence, checksums, storage audit, counts, and reviewer sign-off.
- PR #6 remains draft/unmerged; live broker order submission remains disabled. Any new commit requires its own exact-head CI verification.


### Synthetic restore CI coverage — 2026-10-22

- Added a GitHub Actions step to create a synthetic PostgreSQL evidence table and a synthetic opaque-key document, capture a PostgreSQL custom-format dump plus document archive, verify backup checksums, restore both into a separate temporary database/directory, and compare the restored file SHA-256/byte size and database metadata.
- The workflow retains the synthetic evidence bundle as artifact `synthetic-restore-drill-evidence` for 14 days, including checksum manifest, synthetic dump/archive, result record and expected/restored metadata. This is synthetic CI evidence only, not recovery evidence for real contract-note backups or production data.
- New workflow commits require exact-head CI to finish green before considering this automation validated. The actual coordinated restore drill using real retained backup artifacts remains outstanding; do not claim full recovery acceptance.
- Project is GitHub-only; do not assume a local Docker host. All work remains limited to tarunsharma2610-del/tradepro-improved; original Tradepro is out of scope. PR #6 remains draft/unmerged and live broker order submission remains disabled.


### Latest synthetic restore workflow acceptance checkpoint — 2026-10-22

- GitHub Actions run 39756592781 completed with conclusion success on exact head 98b8260adf17fbee2d6cfe51fcd86175584334c4. Backend tests, broker-write boundary guard, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document archive restore, and evidence-retention step all passed. Run: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39756592781.
- GitHub retained artifact `synthetic-restore-drill-evidence` (artifact ID 12415978081, size 2208 bytes, SHA-256 digest `e2d18437b94a16b1b649ee94deaf81428d35406ab54a731bfef1750c7f360fe2`, expiry 2026-11-05). This confirms synthetic test evidence only; it is not proof of restoring actual retained contract-note backups. Artifact run: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39756592781.
- Accounting acceptance remains open pending independent verification of original contract-note source/component amounts, exact fill identities, paise-level totals, replay/conflict behavior and enclosing-transaction rollback/atomic promotion. The code review alone does not close those gates.
- No local Docker host is assumed; user confirmed Tradepro Improved is GitHub-only. A restore against real retained backup artifacts remains outstanding. All work stays in tarunsharma2610-del/tradepro-improved; original Tradepro is out of scope. PR #6 remains draft/unmerged and live broker order submission remains disabled.
- This checkpoint changes documentation and must receive fresh CI on the resulting exact head before it can be called CI-verified.

### Phase 3 source-to-ledger review follow-up — 2026-10-22

- The documentation checkpoint commit `0c74960c9b0bb1590aa14ef709f55e691b3ac5e2` passed exact-head GitHub Actions run `39757964236`: backend pytest, broker-write boundary guard, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document restore, and evidence artifact retention all passed.
- Further review confirms allocation persistence serializes on the evidence row, validates that target fills belong to the same broker connection, rejects conflicting replay/fill sets, and keeps allocations pending until separate source-ledger verification and promotion.
- The workflow records human transcription and reviewer attestation; it does not automatically parse or independently authenticate a broker's component amount. A real contract note and real backup set were not available, so both acceptance gates remain open.
- PR #6 stays draft/unmerged; live broker writes remain disabled; original `Tradepro` is out of scope. This is a code-review/CI checkpoint, not a claim that real-source reconciliation or real-backup restore is complete.


## Phase 3 checkpoint — lock-order regression verified (22 October 2026)

- Latest exact-head CI run [39817017949](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39817017949) passed on commit `7809e8d7981a19625142dc73e689caa2976c97d6`: backend pytest **565 passed, 1 warning**.
- Live-fill accounting now defers target allocation-row locks until after source-component verification, refreshes target allocations under lock, and fails closed if their state changed. The regression test checks lock-order invariants rather than a brittle exact query prefix.
- A preceding implementation run failed on an outdated test expectation; the test was corrected and the latest run passed.
- PostgreSQL concurrency coverage exists for competing allocation requests on one evidence record. Concurrent source verification versus promotion, deadlock/retry handling, and conflicting fill-set replay still need further review.
- Real contract-note authenticity and a real retained Oracle Cloud database/document restore remain deferred until real evidence is available. Synthetic restore testing does not prove real-data recovery.
- PR #6 remains open/draft/unmerged pending review and explicit user approval. Live broker order writes remain disabled.
- Scope remains `tarunsharma2610-del/tradepro-improved` only; do not modify original `tarunsharma2610-del/Tradepro`.


## 2026-10-23 — live-fill/ledger concurrency checkpoint

- Added PostgreSQL integration test `test_live_fill_promotion_races_with_component_ledger_verification` in `backend/tests/test_broker_charge_allocation_postgres_concurrency.py`.
- Commit: `66fda569b1e4879d270a970cb5b6d216c2f55f9c`; exact-head CI run `39923699033` passed: **570 passed, 1 warning in 30.89s**. Broker-write boundary guard, SQLite/PostgreSQL 16 migration checks, and synthetic database/document-volume restore drill passed.
- CI: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39923699033
- Safety: only `tarunsharma2610-del/tradepro-improved` changed; PR #6 remains draft/unmerged and live broker order writes remain disabled.
- Limitation: fixtures and document bytes are synthetic; authentic Upstox contract-note validation and a real Oracle-host backup restore remain outstanding.


## Exact-head CI checkpoint — 2026-10-23

- Verified PR #6 head `f75471c5bc64bc9ede61c7dc621d1200e97fa078` with GitHub Actions run [39927004048](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39927004048): Backend pytest job completed successfully; broker-write boundary guard, SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks, synthetic PostgreSQL/document-volume restore drill, and evidence-retention step all passed.
- This result applies to that exact PR head. Any documentation commit creates a new head and must receive its own CI verification before the checkpoint is considered current.
- Synthetic restore evidence is not proof of restoring the user's real Oracle Cloud database/document backup. Actual retained-backup restore and authenticated real broker-source validation remain separate acceptance items.
- The integrated concurrency test that races real `LiveFillAccountingService.promote_trade` with allocation-ledger verification/promotion remains an open Phase 3 acceptance gate; do not treat the accounting review as complete yet.
- PR #6 remains draft and unmerged pending acceptance-gate review and explicit user approval. Live broker order writes remain disabled. All changes remain confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains out of scope.


## Follow-up verification — 23 October 2026 (supersedes stale pending wording)

- Exact current head `3c592de0bb2262ec4753196dfba26d7a31c70986` passed GitHub Actions Backend tests in [run 39927573489](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39927573489). The job passed pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade, synthetic PostgreSQL/document-volume restore, and restore-evidence retention.
- Code inspection confirms `backend/tests/test_broker_charge_allocation_postgres_concurrency.py::test_live_fill_promotion_races_with_component_ledger_verification` exists. It races `LiveFillAccountingService.promote_trade` against `verify_component_allocation_ledger` using synthetic persisted evidence and asserts no errors, one inserted execution, one live position, and reconciled component allocations. The CI job passed this PostgreSQL-enabled integration suite.
- Therefore, earlier checkpoint text describing this exact integrated race test as still absent is superseded. Remaining Phase 3 acceptance is broader review of charge-component allocation policy and evidence provenance, source authenticity limits for public examples, plus separate real Oracle backup/restore validation; synthetic tests do not prove real-account authenticity or actual backup recovery.
- PR #6 remains draft/open/unmerged until all acceptance gates are reviewed and the user explicitly approves. Live broker order writes remain disabled. Scope remains only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains outside scope.


## Component-specific allocation policy review — 23 October 2026

- Added `PHASE3_COMPONENT_ALLOCATION_POLICY.md` documenting the key distinction between deterministic allocation arithmetic and a justified charge-specific attribution basis.
- Public references reviewed: [Upstox brokerage/charges](https://upstox.com/brokerage-charges/), [Upstox brokerage calculator](https://upstox.com/calculator/brokerage-calculator/), [NSE levies/STT](https://www.nseindia.com/static/invest/first-time-investor-sebi-turnover-fees-stt-other-levies), and [NSE stamp duty](https://www.nseindia.com/static/invest/first-time-investor-stamp-duty-charges-taxes). Public tariff pages show effective-date and segment/product differences; rates must not be hardcoded as timeless or inferred from historical sample notes.
- Policy gap: the generic allocator's support for QUANTITY, NOTIONAL and EXPLICIT_REVIEWED is not blanket approval for those bases for every component. Brokerage/order caps, GST tax-base composition, buy-side-only stamp duty, side/product-specific STT and exchange charges, and account/scrip-level fees need component-appropriate rules and tests. The new policy file records the acceptance matrix and tests still required.
- Exact head before this policy-doc addition, `6d922d3436dcf2b3def7b5c77665056be173fab1`, passed Backend tests in [run 39928182307](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39928182307), including pytest, broker-write guard, SQLite/PostgreSQL 16 migration round-trips, and synthetic restore/evidence retention. The new policy documentation commit and subsequent doc-sync commit(s) require their own exact-head CI before being marked verified.
- PR #6 remains draft/open/unmerged pending policy gates, full acceptance review and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` is out of scope.


## Fail-closed allocation gate — CI verified 23 October 2026

- Commit `2e14ce6feed8357a85813ec5924e577879b2e4ca` passed GitHub Actions [run 39929331878](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39929331878). Backend pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore, evidence retention, and cleanup all completed successfully.
- The source-reconciliation verification gate now rejects `QUANTITY` and `NOTIONAL` allocation bases until component-specific effective-dated rules are approved. A regression test verifies unsupported notional allocation raises and rows remain `PENDING_RECONCILIATION`. Explicitly reviewed per-fill weights remain available, subject to existing provenance/reviewer/promotion checks.
- This is a conservative fail-closed safeguard, not completion of component-specific tariff automation. Still required: reviewed tests/rules for brokerage caps and multi-fill orders, GST taxable base, buy-side stamp duty, side/product-specific STT/CTT, exchange/segment charges and effective-date transitions. Ambiguous source scope must remain pending.
- Publicly shared Upstox contract-note examples are for layout/research only and are not independently authenticated. Actual Oracle Cloud backup recovery remains separate from synthetic restore CI.
- PR #6 remains draft and unmerged until acceptance gates are reviewed and the user explicitly approves. Live broker order writes remain disabled. Changes are confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains out of scope.


## Phase 3 charge-calculation checkpoint — 23 October 2026

- Verified code/test commit `b37e6cab7c9cbba0897e5c02161812d121ba2c7e` passed the full Backend pytest workflow: [run 39933579727](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39933579727). Steps passed included pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade, synthetic PostgreSQL/document-volume restore, evidence retention, and cleanup.
- The branch now has arithmetic helpers/regression coverage for brokerage caps, GST on an explicit taxable base, buyer-side stamp duty, STT/CTT on an explicit base, and exchange/SEBI charges on explicit bases. These are arithmetic helpers, not a verified tariff engine: they do not establish official effective-dated rates, applicability by exchange/segment/instrument/product/side, exemptions, or per-fill attribution.
- Latest exchange/SEBI test commit: `b37e6cab7c9cbba0897e5c02161812d121ba2c7e` (CI passed). Documentation checkpoint commit `1c3906551903acc0bb5a4450c7b8a56b3f9a659a` was created afterward; exact-head CI has not yet returned a workflow result.
- Remaining Phase 3 gates: source and version official effective-dated tariffs with provenance; model applicability and taxable/calculation bases; connect rule evaluation to durable per-fill allocations; test rounding, caps, effective-date transitions, replay/idempotency, and reconciliation; verify full CI on the final documentation/code head.
- Automatic `QUANTITY`/`NOTIONAL` allocation remains fail-closed until the relevant component-specific rules are reviewed and accepted. Do not promote ambiguous or unsupported charges.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. All changes are confined to `tarunsharma2610-del/tradepro-improved`; the original `Tradepro` repository is out of scope and must remain untouched.


## Exact-head documentation CI result — 23 October 2026

- Exact checkpoint commit `d0de363bd0b034582754b41de17ae991f6c043aa` passed GitHub Actions [run 39934671391](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39934671391). This verifies the nine-document checkpoint head at the time of the run.
- Resume from the `phase3/durable-per-fill-charge-allocation` branch in `tarunsharma2610-del/tradepro-improved`. Next work: obtain/record official Upstox and statutory charge-rule sources with effective dates and provenance; model applicability by exchange/segment/instrument/product/side; then implement and test tariff-driven durable per-fill allocation and reconciliation.
- Arithmetic helpers are groundwork only, not a verified tariff engine. Keep unknown/ambiguous allocation fail-closed. PR #6 stays draft and unmerged until acceptance gates and explicit user approval. Live broker order writes remain disabled. Original `Tradepro` is outside scope and must remain untouched.


## Exact-head CI confirmation for saved checkpoint — 23 October 2026

- The nine-document checkpoint head `c2959ffed34f6dd1c299bdb36091b987df06c11a` passed full GitHub Actions run [39935827529](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39935827529). Verified steps: backend pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade, isolated synthetic PostgreSQL/document-volume restore, evidence retention and cleanup.
- Resume work on `phase3/durable-per-fill-charge-allocation`. Next engineering task: verify and record current official Upstox, exchange and statutory charge rules with URLs, effective dates, applicability and provenance. Then implement tariff-driven component calculation and durable per-fill allocation, with regression tests for effective-date transitions, rounding, order caps, replay and reconciliation.
- Existing helpers for brokerage cap, GST, stamp duty, STT/CTT, exchange and SEBI charges are arithmetic groundwork only. They do not constitute a verified tariff engine. Keep unsupported/ambiguous scopes fail-closed.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Work only in `tarunsharma2610-del/tradepro-improved`; the original `Tradepro` repository remains outside scope.


## Upstox charge-rule source register — 23 October 2026

- Added `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md` at commit `de97bd3bfe90e82b888181cf109ed6a1b8e41d41`. It records the official Upstox brokerage pricing page, Brokerage Details API, Get Trades Charges API, and official contract-note guidance, with their limits and implementation requirements.
- Key source URLs: https://upstox.com/brokerage-charges/ ; https://upstox.com/developer/api-documentation/get-brokerage/ ; https://upstox.com/developer/api-documentation/get-trade-charges/ ; https://upstox.com/help-center/how-can-i-access-and-download-the-contract-note-248457/ ; https://upstox.com/help-center/understanding-the-contract-note-248458/
- Research indicates the pricing page contains historical and current rate sections, including STT/CTT changes effective 1 April 2026 and NSE transaction-charge changes effective 1 March 2026. Therefore, do not hardcode a single timeless rate or use a rate from the wrong effective period. BSE scrip-group variation, commodity/currency segments, option premium/futures turnover, DP charges, GST base composition and per-crore unit normalization require explicit rules.
- The authenticated brokerage API can calculate supported orders from instrument, quantity, product, side and price; the trades-charges API provides a segment/financial-year breakdown. Treat the latter as aggregate reconciliation only, not per-fill evidence.
- Next: implement a versioned tariff-rule model with effective dates, explicit normalized units/bases, source provenance and review status; add applicability/rounding/effective-date regression tests before wiring rules into durable per-fill allocation. Unknown or ambiguous cases remain fail-closed.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Effective-dated tariff registry groundwork — 23 October 2026

- Added `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md` (commit `de97bd3bfe90e82b888181cf109ed6a1b8e41d41`) documenting official Upstox pricing/API/contract-note sources, rate effective-date cautions, API limitations and the required provenance fields.
- Added `backend/app/services/broker_tariff_rules.py` (commit `0ec5590579c67c2575c8c4c72cf75bc56605120b`), a fail-closed rule selector requiring exact broker/exchange/segment/product/side/component/basis match, an effective date, source URL and SHA-256-shaped provenance, and APPROVED status. It rejects missing and overlapping rules and intentionally ships without active rates.
- Added `backend/tests/test_broker_tariff_rules.py` (commit `74240f2cc0af05befeee1fa97f988f2372a73be6`) covering exact-scope selection, review-state gating, scope mismatch, effective-date boundaries, overlap and invalid provenance/rates. CI has not yet returned a result for this latest test commit; do not mark it verified until the full workflow passes.
- This is rule-selection groundwork, not a complete tariff calculator and not proof that any specific rate is legally applicable. The next step is CI verification, then source-reviewed rules for specific segments/components and integration with durable per-fill allocation/reconciliation.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Tariff amount calculation and CI checkpoint — 23 October 2026

- Both the tariff registry regression-test commit `74240f2cc0af05befeee1fa97f988f2372a73be6` and its nine-document checkpoint `14fa83fe144228bb81a3b935b48b73c7f454afe2` passed their full Backend tests workflows: [code run 39953794565](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39953794565) and [documentation run 39953906848](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39953906848).
- Added `calculate_tariff_amount` to `backend/app/services/broker_tariff_rules.py`, with distinct `PERCENT`, `INR_PER_CRORE`, and `INR_FIXED` units and paise rounding. Added tests for units, rounding and invalid bases. Latest test commit is `782d2d2c63905adfa6862f43abcdc057c47894a7`; its CI is pending and must be verified before treating the new calculation as green.
- No live tariff rates are activated. The new calculator requires a previously selected approved rule; rule selection still fails closed for missing or overlapping rules. This does not yet integrate the registry with durable per-fill allocation or prove component-specific legal applicability.
- Next: verify CI on the latest code commit, then build reviewed, source-backed test fixtures for exact tariff applicability and connect approved component calculations to durable allocation/reconciliation without enabling ambiguous QUANTITY/NOTIONAL allocation.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Tariff calculation safety refinement — 23 October 2026

- Confirmed prior tariff-calculator code CI passed: [run 39954309954](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39954309954). The prior nine-document checkpoint CI also passed: [run 39954408580](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39954408580).
- Tightened `calculate_tariff_amount` so it refuses non-`TariffRule` values and any rule whose review status is not `APPROVED`. Added regression tests for DRAFT, REVIEWED and REJECTED rules.
- Latest safety-fix test commit: `83a70bdc88dfbc2cfabe8e80b8adfc858b516a6e`. Its full CI is pending; no green status should be inferred yet.
- Active rates remain intentionally absent pending rule-by-rule source verification and approval. Next: verify CI, then implement only specifically sourced rules with explicit applicability, normalized unit, basis, effective date and provenance before connecting to durable per-fill allocation.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Scoped tariff-calculation entry point — 23 October 2026

- Confirmed prior safety-fix code CI passed: [run 39954730200](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39954730200). The previous nine-document checkpoint also passed: [run 39954836920](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39954836920).
- Added `calculate_charge_for_trade` to `backend/app/services/broker_tariff_rules.py` (commit `d2d9c0c99a0cf31bca96fbde39c615b2569b1a97`) to select exactly one approved rule for the full trade scope/date and then calculate using its declared unit. Added tests for calculation result and fail-closed behavior without an approved match (commit `98c514d59d1b1da986a1d00117c2653c1e82d4c6`).
- Latest code CI is pending; do not mark this addition green until full Backend pytest, broker-write boundary, migrations and restore workflow pass.
- This entry point does not persist charge rows or allocate across fills. No production tariff rates are enabled. Next: verify CI, then design a persistence/integration boundary that records the selected rule version and calculation basis alongside the durable source component and per-fill allocation ledger.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Tariff CI verification and estimate/allocation boundary — 23 October 2026

- Verified full Backend CI passed for tariff calculation commit `98c514d59d1b1da986a1d00117c2653c1e82d4c6`: [run 39955151533](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39955151533). Verified the nine-document checkpoint CI passed for `2a5c3cf5075c2ab217603868f6272cc366784b26`: [run 39955284700](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39955284700). Both include pytest, broker-write boundary, SQLite and PostgreSQL migration downgrade/re-upgrade, and isolated synthetic restore steps.
- Added `docs/PHASE3_TARIFF_TO_FILL_ALLOCATION_DESIGN.md` (commit `a49b37509db1658ce7026f8328a35e26422afaad`) to define the boundary between a tariff estimate, actual broker-evidenced source charge and reviewed per-fill allocation; it sets out idempotency, immutable rule snapshots, component-specific acceptance gates and safety constraints.
- Next: CI-check this design/documentation checkpoint, then implement persistence for estimates as a separate, immutable, idempotent record before wiring estimates into source-charge reconciliation. Estimates must never be represented as contract-note actuals or automatically promoted into accounting.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Immutable tariff-estimate snapshot groundwork — 23 October 2026

- Added `backend/app/services/tariff_estimate_snapshot.py` (commit `00ec9fcd449fb9c9c091b29ebc7c68377246242b`) with canonical JSON snapshots, rule/source provenance, SHA-256 fingerprints, explicit calculation base/rounding metadata, stable idempotency keys and exact-replay/conflict comparison.
- Added `backend/tests/test_tariff_estimate_snapshot.py` (commit `f89517a3ca0bc034dc84da6d2239f0fd18026990`) for deterministic serialization, exact replay, conflicting base replay, changed rule, unapproved rules, invalid base, missing identity and effective-date rejection.
- This is a deterministic snapshot and replay-comparison layer only; it does NOT yet persist estimates. Durable enforcement still requires a database table with a unique idempotency constraint, transactional insert/read comparison and a migration tested on SQLite/PostgreSQL. No estimate can become a broker actual or source component.
- Latest code CI must be verified before this work is considered green. Next: confirm test and migration conventions, add durable persistence plus migration, concurrency-safe idempotency, and tests proving rollback/replay behaviour.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Snapshot CI verification and idempotency correction — 23 October 2026

- Verified CI passed for the immutable snapshot implementation `f89517a3ca0bc034dc84da6d2239f0fd18026990`: [code run 39956149855](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39956149855). Verified the associated nine-document checkpoint passed: [run 39956272786](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39956272786). Both runs completed pytest, broker-write boundary, SQLite and PostgreSQL migration downgrade/re-upgrade, and synthetic restore checks successfully.
- Code review identified an idempotency-key flaw: including the tariff rule fingerprint in the key would allow the same trade/component event with a changed rule to receive a new key instead of conflicting. Corrected `tariff_estimate_snapshot.py` so event key is stable across rate/rule changes, and changed the regression test to require a same-event rule change to fail as a conflicting replay.
- Latest correction commits: `204574082c7953ac08262a9f51801f04fd09ead7` and test `fafa26b6fb686471ac38a041256659b273f97712`. CI for this correction is pending.
- The snapshot remains in-memory/canonical only. Durable database persistence is not implemented yet; adding a table/migration requires identifying the current Alembic head and testing a unique idempotency constraint with transactional exact-replay/conflict behavior.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Durable estimate-only tariff persistence — 23 October 2026

- Verified the previous idempotency-correction code CI passed: [run 39956721476](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39956721476). Verified the previous nine-document checkpoint CI passed: [run 39956881266](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39956881266).
- Added `TariffEstimateSnapshotRecord` model and model registration (commits `08fec41026dabf250bd8756e0a711c20bbbf1e2a`, `0f47e07abd8bad51e4a7e11a851c726dd9008882`), Alembic revision `202610240015` after `202610240014` (commit `d98f5e259c610f8a5d392461ea1b75f6b9471912`), and `persist_tariff_estimate_snapshot` (commit `bc8b7bb2666e73cf30aa3fa4a796ebfe4e4874e5`).
- Added persistence regression tests for create/exact replay, changed-base conflict, changed-rule conflict, and estimate-only status (commit `cc121e7c710038ee25a434634a86ec4296cd0d68`). The unique database idempotency key is the concurrency arbiter; the service uses a nested transaction and leaves the outer commit to its caller.
- Latest implementation CI is pending; do not consider durable persistence verified until full pytest, broker-write boundary, SQLite/PostgreSQL migration downgrade/re-upgrade and synthetic restore checks pass.
- The database record stores only estimate snapshot JSON and a digest and has a database constraint that fixes status at `ESTIMATE_ONLY`; it does not create or modify contract-note actual charge/source-component rows.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Persistence CI result and append-only enforcement — 23 October 2026

- Full CI passed for durable estimate persistence implementation commit `cc121e7c710038ee25a434634a86ec4296cd0d68`: [run 39957564616](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39957564616). Backend pytest, broker-write boundary, SQLite and PostgreSQL migration downgrade/re-upgrade, and synthetic restore steps all succeeded.
- Review then identified that the database row had no ORM-level guard against updates to the snapshot payload. Added an append-only SQLAlchemy `before_update` guard to `TariffEstimateSnapshotRecord` (commit `596d4396bfaa58da3f4bf8ad11978370cfc8edf2`) and a regression test proving payload mutation is rejected (commit `af07ad77c3c7621774f49771c5d9cb4665778c03`).
- The append-only guard is an ORM protection, not a database trigger; direct SQL updates outside the ORM are not blocked by this guard. Consider a portable DB-level immutability trigger only if required by the release threat model. The unique key and ESTIMATE_ONLY check remain database-enforced.
- Latest append-only change CI and this documentation checkpoint's CI are pending. Do not treat them as verified until all jobs complete successfully.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Tariff snapshot safety rules (2026-10-23)

- Work only in `tarunsharma2610-del/tradepro-improved`; never change the original `Tradepro` repository.
- Tariff snapshots are append-only: preserve migration `202610240016` and its PostgreSQL/SQLite triggers and tests.
- A tariff estimate is never an actual broker charge. Do not use an estimate to fill a missing contract-note component or promote it into per-fill actual allocation.
- Do not approve/ship tariff rules that need order-level caps, minimums, conditional lesser-of logic, GST taxable-base composition, or special charge models until those behaviors are explicitly represented and tested.
- PR #6 stays draft/unmerged pending Task B acceptance and explicit user approval. Live broker order writes stay disabled.


## Task B checkpoint rules (2026-10-23)

- Database-level tariff snapshot immutability is required; preserve migration `202610240016` and PostgreSQL/SQLite direct-SQL protections/tests.
- PostgreSQL concurrency tests must retain exact-replay and conflicting-payload race coverage.
- Tariff rules support only PERCENT, INR_PER_CRORE and INR_FIXED today. Do not approve unsupported order-level caps/minimums, conditional lesser-of logic, GST taxable bases or special charge models until represented and tested.
- Keep estimate snapshots separate from reviewed actual contract-note source components. Estimates may support variance analysis only and must never be promoted into the actual per-fill allocation ledger.
- Scope remains `tarunsharma2610-del/tradepro-improved`; PR #6 stays draft/unmerged and live broker order writes remain disabled.


## Variance comparison safety rules (2026-10-23)

- Use snapshot schema v2 exact `source_trade_record_id` when comparing an estimate to actual evidence. Missing identity must fail closed.
- Variance comparison is permitted only against a VERIFIED component from REVIEWED, hash-verified contract-note evidence, with matching broker connection, component, currency and reviewer and an exact one-fill manifest.
- Variance records are append-only audit comparisons. Never modify allocation rows or promote estimates to actual charges from this service.
- Do not compare a single-fill estimate with a multi-fill/order-level actual total. Aggregate variance needs a separately reviewed linkage/aggregation design.
- PR #6 stays draft/unmerged; live broker order writes remain disabled; work only in `tarunsharma2610-del/tradepro-improved`.


## Verified exact PR-head CI 39962196672 — 2026-10-23
Current PR #6 head `c47bc3e3eeb4c8da4415132735d2d4ef457551f7` passed [CI](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39962196672): 680 passed, 1 warning; broker-write guard passed; no failed steps. Continue aggregate variance design and tariff-rule coverage; unsupported shapes must fail closed. Re-run CI on the final intended head and synchronize all nine core docs before merge review. Do not merge or enable live broker writes without explicit authorization; only `tarunsharma2610-del/tradepro-improved` is in scope.


## Aggregate variance implementation guard — 2026-10-23
The proposed design in `docs/PHASE3_TARIFF_TO_FILL_ALLOCATION_DESIGN.md` is not implementation approval. First inspect existing tariff snapshot models, variance service, migration chain, and tests. Preserve single-fill compatibility; order-level comparisons require exact canonical fill-set identity and scope-correct tariff calculations. Fail closed on ambiguous evidence and never mutate actual allocations or P&L from variance comparison.


## Variance scope validation guard — 2026-10-23
Before recording estimate-versus-actual variance, validate the canonical eligible-fill manifest against its stored SHA-256 and match the linked broker fill's side/trade date to the estimate. Keep tests for tampered digest and mismatched scope. Verify CI for the exact current code head before proceeding. Aggregate variance and advanced tariff rule shapes remain unsupported until implemented/tested; do not activate unreviewed production rates.


## Exact-head CI checkpoint — 2026-10-23
CI run 39968000009 passed on code head `f5092df1d27a28006dccba929fdc41e9a1d63f1e`: 683 passed, 1 warning; broker-write boundary guard passed; SQLite migration and isolated PostgreSQL 16 synthetic restore checks completed. Run CI on the latest docs head before treating the whole checkpoint as green. Aggregate variance remains unimplemented; advanced tariff shapes must be implemented/tested or fail closed. Keep PR draft and live writes disabled.


## Aggregate variance implementation guard — 2026-10-23
Explicit `TRADE_FILL` / `ORDER_FILL_SET` scope is implemented with exact canonical fill identity, same-order/connection/side/date validation, replay/conflict handling, and migration `202610240018`. Snapshot builder is schema v4; disregard older v3 references. Aggregate success, exact replay, and mismatched-manifest regression tests passed in backend CI run [39979772325](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39979772325) on commit `e54e405b74feee90e4658a6992fa208a3e2da5d3`. That run also passed the broker-write boundary guard, SQLite/PostgreSQL 16 migration round-trips, and synthetic restore drill. Documentation commits made afterward require their own exact-head CI. Preserve append-only evidence and variance records; do not merge or enable live writes.


## Latest tariff-safety correction checkpoint — 2026-10-23
The first tariff safety patch had failing CI; do not report it as green. Follow-up commit `68dc2b6fa0a729cc77180725e581de61a88e9de1` adds the missing APPROVED-status guard to GST explicit composition and early rejection for stamp-duty SELL requests. CI run [39982723294](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39982723294) passed all backend, broker-write boundary, SQLite/PostgreSQL 16 migration, and restore-drill steps. Run CI again on the final docs head; preserve draft PR status and keep live broker writes disabled.


## Tariff safety + Upstox charge-source research — 2026-10-23

Code commit `ce0b4bc17eaf1656334e10ca8d6e32a68f50593b` adds a fail-closed stamp-duty unit guard: the specialized stamp-duty calculator accepts only percentage-based approved rules; regression tests reject `INR_FIXED` and `INR_PER_CRORE`. Exact-head CI [39987357989](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39987357989) passed backend tests, broker-write boundary guard, SQLite and PostgreSQL 16 migration round-trips, and synthetic restore drill.

Official Upstox sources reviewed:
- Brokerage calculator API: https://upstox.com/developer/api-documentation/get-brokerage/ — order-scoped estimate with brokerage, taxes, transaction/clearing/IPFT/SEBI charges and DP-plan metadata; `dp_plan.min_expense` is a daily per-scrip sell minimum outside the brokerage calculation.
- Trade charges API: https://upstox.com/developer/api-documentation/get-trade-charges/ — segment/date-range charge breakdown, including brokerage, GST, STT, stamp duty, transaction, clearing, IPFT, SEBI turnover and demat transaction charges.
- Historical trades API: https://upstox.com/developer/api-documentation/get-historical-trades/ — trade ID, exchange, segment, quantity, amount, side and trade date.
- Public tariff page: https://upstox.com/brokerage-charges/ — includes historical and newer effective-date rows; never activate rates from a flattened scrape without preserving effective periods and source snapshot.

API charge breakdowns are reconciliation/reference inputs, not automatically contract-note evidence and not a substitute for reviewed actual source components. Do not store tokens. DP per-scrip/day minimums, STT/CTT tax-event cases, and other conditional models remain unsupported until represented and tested explicitly. No active production tariff registry is enabled. PR #6 stays draft/unmerged; live broker writes remain disabled; original `Tradepro` remains out of scope.


## Generic conditional-charge guard — 2026-10-23
The next audit found that the generic rate calculator could apply plain rate×base arithmetic to STT/CTT and DP/demat components, despite these requiring event- or day/scrip-specific semantics. Commit `ee09183e5b8eeff0311431faa90b807d9b561ce7` adds an explicit fail-closed block for STT, CTT, DP, DP charges and demat/depository transaction charges in the generic calculator, with parameterized regression tests. Exact-head CI run [39988242077](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39988242077) passed. The synchronized documentation commit `b1207def7d828c960e6fffe9c6af8b9ed0177c07` also passed exact-head CI run [39988578238](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39988578238).

Audit note: the implementation constant is `tariff-estimate-snapshot-v4`; older design text saying snapshot v3 is stale and is corrected in the accompanying design-document update. Remaining gated models include STT/CTT event-specific rules, DP daily per-scrip minimums, conditional lesser-of pricing, and reviewed source-backed effective-date rates. No live tariff registry or live broker order writes are enabled.

## Phase 3 work-control reminder — 2026-10-24
Verify CI against the latest branch head, not an earlier commit. Aggregate variance must remain audit-only, fail closed on source/fill-scope integrity mismatches, and leave actual allocation, positions and P&L untouched. Synchronize all nine checkpoint documents after meaningful changes. Never modify original `tarunsharma2610-del/Tradepro`; keep PR #6 draft/unmerged and broker order submission disabled.

## Phase 3 CI and acceptance rule — 2026-10-24
The latest verified test head `bc8e5c1aa862589c660fd361d87f7df45d8ceb10` passed backend CI (run `40062975428`). Do not equate green CI with full Phase 3 acceptance: verify concurrency/replay, reviewed-source revalidation, and no-accounting-side-effect invariants before advancing. Keep variance audit-only, fail closed on scope mismatches, never modify original `tarunsharma2610-del/Tradepro`, keep PR #6 draft/unmerged, and leave broker order submission disabled.

## Phase 3 acceptance reminder — 2026-10-24
Variance comparisons must remain audit-only, preserve reviewed evidence/component and allocation state, and revalidate current review status before writing. New regression tests have been added; do not mark them verified until CI passes on the latest branch head. Never modify original `tarunsharma2610-del/Tradepro`; keep PR #6 draft/unmerged and broker order submission disabled.

## Mandatory Upstox API/SDK/agent-tool policy — 2026-10-24
For every relevant upgrade, read `UPSTOX_API_INTEGRATION_POLICY.md`. Audit the current official Upstox API catalogue, endpoint/version support, official SDKs and examples, brokerage calculator, historical trade-charge/trade-history APIs, market data/WebSocket, options, sandbox, rate limits, developer community, official Agent Skills and read-only MCP where relevant. Use all capabilities relevant and permitted for this project, not every endpoint blindly. Treat calculator output as an estimate, not actual per-fill evidence. The Agent Skill may execute live orders: never allow it to bypass PAPER mode or order-write safeguards. Account-scoped MCP requires explicit authorization. Live broker order writes remain disabled.

## Phase 3 variance acceptance checkpoint — 2026-10-24
Aggregate variance concurrency/replay passed exact-head CI run `40064129721` on commit `dbff090610028cfb9f5a87585d9c8e697449cd23` (738 passed, 1 warning). PostgreSQL coverage verifies concurrent duplicate comparisons produce one `CREATED`, one `EXACT_REPLAY`, one immutable audit record, and no allocation writes. Next gate: source-backed effective-dated component-specific tariff applicability and approved rule-to-per-fill integration. Unsupported bases remain fail-closed; PR #6 draft/unmerged; live broker writes disabled.

## Upstox read-only charge APIs added — 2026-10-24
The existing `UpstoxReadOnlyReconciliationClient` now exposes `get_brokerage_estimate`, `get_trade_charges`, and `get_historical_trades`, with fixed GET paths, input validation and sanitized upstream errors. Exact-head CI run `40064514873` passed on `5026e95e56ae52c40b238bc29c194ceae26c7898` (744 passed, 1 warning). These endpoints have not been called against a real account; no tokens or live orders were used. API calculator output is estimate-only, trade charges are aggregate, and historical trades are references—not contract-note/per-fill charge evidence. See `UPSTOX_API_INTEGRATION_POLICY.md` and `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`.

## Upstox API estimate snapshot integration — 2026-10-24 (CI verified)
Added a builder that normalizes the official Upstox Brokerage Details response into six component-level `ESTIMATE_ONLY` snapshots (brokerage, STT, stamp duty, GST, exchange charges = transaction + clearing + IPFT, and SEBI charges). Snapshots retain sanitized request parameters, API version/endpoint, UTC retrieval timestamp, canonical full response JSON + SHA-256, total estimate and separate DP-plan minimum metadata. Persistence reuses the existing append-only snapshot store. Variance comparison recomputes the response digest and requires request quantity, price, side and instrument to match the exact reviewed fill set before comparison. Exact-head CI run `40065219626` passed on `2c23ebfeb9d0d843620dc6dcf54b7279bb112662`: **754 passed, 1 warning**. Estimates never create allocations; PR #6 remains draft/unmerged and live broker writes disabled.

## Brokerage tariff shape support — 2026-10-24 (CI verified)
Extended `calculate_order_brokerage` and estimate snapshots to support explicit `ORDER_FIXED` / `INR_FIXED` rules for flat per-executed-order brokerage, alongside existing `ORDER_NOTIONAL` / `PERCENT` rules with rule-bound minimum/maximum caps. This is arithmetic/shape support only; no unreviewed rate was activated. Exact-head CI run `40065607232` passed on `30db9920f640203c1045f1cb045d955bb41b5f86`: **756 passed, 1 warning**. Next: source-archived, effective-dated candidate tariff rules remain DRAFT until independently reviewed and boundary-tested.

## Effective-dated Upstox tariff candidates — 2026-10-24 (CI verified)
Added `docs/source_snapshots/UPSTOX_CHARGES_2026-10-24.md`, a dated normalized excerpt of official Upstox and NSE charge pages. Canonical extracted-payload SHA-256: `c59f7e940fde6b0d94ca1189766f16e5601c117d4a8c2bcd2415da0ecd6db420`. Added `upstox_tariff_candidate_rules()` with 18 effective-dated STT and exchange-charge candidate rows. Every row is `DRAFT`, so `select_tariff_rule` refuses them; exchange/IPFT composition remains unresolved and stamp duty needs a more current statutory source. Exact-head CI run `40065979244` passed on `f76ecde4ac785123de2980539138ce89ff660294`: **760 passed, 1 warning**. Do not activate rates without source archival, independent review and component-specific tests.


## Fixed-order brokerage entrypoint regression — 24 October 2026

- Audit found that `calculate_charge_for_trade` routed percentage-based `ORDER_NOTIONAL` brokerage through `calculate_order_brokerage`, but flat-fee `ORDER_FIXED` brokerage fell through to the generic calculator, which intentionally rejects that basis.
- Fixed the shared entry point to route both `ORDER_NOTIONAL` and `ORDER_FIXED` brokerage through the guarded order-level calculator. Added regression test `test_trade_charge_entrypoint_supports_flat_fixed_order_brokerage` asserting a flat INR 20 fee is returned through the full scope-selection entry point.
- Implementation commit: `1634989d29734f1d5ffdcfee826384a512eaafe7`; regression-test commit: `928c0207ff8de5f4852225ab6b9e0fabe97f6e12`.
- Exact-head backend CI run 40066706304 was in progress at documentation time; do not mark this fix green until that run completes. Recheck CI after these documentation updates because they change the branch head.
- No tariff candidate was activated, no charge was promoted to the actual ledger, and no live broker order was sent. Original `tarunsharma2610-del/Tradepro` remains out of scope.


## Brokerage basis/unit validation hardening — 24 October 2026

- Latest verified prior head: Backend pytest workflow run [40066838844](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40066838844) passed for the flat fixed-order brokerage entry-point regression.
- Additional fail-closed hardening now rejects inconsistent brokerage rule shapes at construction: `ORDER_FIXED` requires `INR_FIXED`, and `ORDER_NOTIONAL` requires `PERCENT`. This prevents invalid basis/unit combinations from surviving registry validation and failing only during calculation.
- Implementation commit: `4faa6a062264b2396cb00e380c5cbbe16449ec91`; regression-test commit: `26ea299b78be463651768b2ab93fa6443d5350c5`.
- CI for these new commits is pending and must be checked on the exact latest branch head before this change is considered verified. Do not reuse the earlier green run as evidence for these commits.
- No official tariff rate was activated, no estimate was promoted to actual per-fill accounting, and no live broker order was sent. PR #6 remains draft/unmerged; work stays in `tarunsharma2610-del/tradepro-improved`, not the original `Tradepro` repository.


## Brokerage rule validation CI correction — 24 October 2026

- Backend CI run [40067041722](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40067041722) failed with 2 tests failing and 762 passing. The failure exposed that generic rate-unit arithmetic tests used a default `brokerage/ORDER_NOTIONAL` rule while intentionally testing `INR_PER_CRORE` and `INR_FIXED`; the new brokerage shape guard correctly rejected those inconsistent test fixtures.
- Corrected the generic unit test matrix to use semantically appropriate component/basis pairs: `brokerage/ORDER_NOTIONAL/PERCENT`, `sebi_turnover/TURNOVER/INR_PER_CRORE`, and `other_fee/ORDER_FIXED/INR_FIXED`. This preserves the guard rather than weakening production validation.
- Test-fix commit: `6ba333fe0339838042ffd25a141c4805318418bc`. A new CI result for this exact commit has not yet been observed; do not mark it green until confirmed.
- No tariff rules were activated and no charge allocations or live broker orders were created. PR #6 remains draft/unmerged; original `tarunsharma2610-del/Tradepro` remains out of scope.


## Generic tariff test basis correction — 24 October 2026

- Backend CI run [40067217326](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40067217326) completed with 763 passed and 1 failed. The remaining failure was the generic unit-arithmetic test using `ORDER_FIXED`, which is intentionally excluded from generic calculation bases and must use the specialized brokerage entry point.
- Corrected the test fixture to use supported generic basis `NOTIONAL` for the generic `INR_FIXED` arithmetic case. The production guard is unchanged. Test correction commit: `7c7dadff65885918fc0e01d0aa8deaf1b6d1bb16`.
- CI for this correction and subsequent documentation updates must be checked on the exact latest PR head. No green result is claimed until verified.
- No tariffs were activated; no actual charges were promoted or per-fill ledger writes made; no live broker orders were sent. PR #6 remains draft and unmerged. Work is limited to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains untouched.


## Official tariff-source recheck — 24 October 2026

- Rechecked the official Upstox charges page on 2026-10-24 and recorded the findings in `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`. It lists 1 April 2026 STT/CTT changes and 1 March 2026 NSE transaction-charge changes, and states IPFT is combined with transaction charges while separately listing ₹0.01/crore (options on premium) plus GST. Current candidate rows represent transaction charges only; IPFT composition/effective-date treatment must be resolved before approval.
- The same page's ₹10/order API-order brokerage note is explicitly valid only through 31 December 2025 (excluding GTT); do not treat it as current pricing. Current authenticated API-order-specific terms remain unverified.
- NSE's official stamp-duty page is still marked updated 03/10/2023, so it is not a fresh 2026 publication. Independent current statutory corroboration remains a release gate.
- No tariff candidate was approved or activated, no estimate was promoted to actual per-fill accounting, and no live broker order was sent. Source excerpt remains normalized rather than byte-for-byte HTML. Exact-head CI must be checked after these documentation changes; prior green CI does not cover the new head.


## Brokerage tariff effective-date gate — 24 October 2026

- Reconfirmed the official Upstox public page lists current brokerage examples: equity delivery/options ₹20 per executed order; equity intraday ₹20 or 0.1% (whichever lower); equity futures ₹20 or 0.05% (whichever lower). The current source excerpt does not establish a precise effective_from date for these brokerage terms.
- A trial draft-registry addition was reverted because populating the required `effective_from` with the retrieval date would falsely imply a published effective date. No brokerage candidates with guessed effective dates remain in the tariff registry. Before registering these rows, obtain a source that establishes the effective date or explicitly model an evidence-backed “current as observed” rule state without pretending the retrieval date is the tariff effective date.
- Existing calculation helpers can model flat per-order brokerage and capped percentage brokerage (`maximum_inr`), but helper capability is not source approval. The published “whichever lower” semantics must have a regression test before a reviewed rule is eligible for use.
- The preceding verified Backend pytest run was [40067742361](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40067742361), successful on the then-current head. Later registry/documentation commits need exact-head CI confirmation; do not reuse that run as proof for later commits.
- No rates were activated, no estimates were promoted into actual accounting, and no live broker order was sent. PR #6 remains draft/unmerged and the original `Tradepro` repository remains out of scope.


## Order-brokerage cap regression coverage — 24 October 2026

- Added regression coverage for percentage brokerage below/at the maximum cap, minimum-floor behavior, simultaneous minimum/maximum bounds, and flat `ORDER_FIXED/INR_FIXED` brokerage. Tests call the specialized order-level calculation helper and assert paise-precise outputs; flat order fees reject percentage caps.
- Test commit: `48447dafb11d7d83a09f4f64a55020405fa167a4`. This is not yet CI-verified; run and inspect CI for the exact latest PR head before treating the tests as passing.
- This covers arithmetic only. It does not approve any live tariff row, define the allocation of one order's brokerage across multiple fills, or establish that public examples match a particular authenticated account plan. Per-fill allocation and actual-charge promotion remain blocked pending policy/evidence and durable accounting acceptance tests.
- PR #6 remains draft/unmerged; no live broker orders were sent; original `Tradepro` remains out of scope.

## CI follow-up — fixed-fee cap regression test — 24 October 2026

- Latest documentation head before this correction, `5b155c4b3f75606b426262f938b420f7a2217d74`, failed backend pytest: **768 passed, 1 failed**. Failure was isolated to `test_fixed_order_brokerage_is_flat_and_rejects_caps`: the test expected calculation-time rejection, but `TariffRule` correctly rejects an invalid fixed-fee rule at construction time.
- Corrected the regression test to assert the rule-construction `ValueError` using the actual validation message. Test-only commit: [47aa91e2696bb6388af73ede568dfe89c4cbead7](https://github.com/tarunsharma2610-del/tradepro-improved/commit/47aa91e2696bb6388af73ede568dfe89c4cbead7).
- CI for this correction and the resulting documentation head is **pending verification**; do not describe the latest head as green until the exact SHA has a successful run. This is a test correction, not a production guard relaxation.
- PR #6 remains draft/unmerged. Live broker order submission remains disabled. All work is confined to `tarunsharma2610-del/tradepro-improved`; do not modify original `tarunsharma2610-del/Tradepro`.

## Exact-head CI passed — 24 October 2026

- Verified successful GitHub Actions backend workflow [40081403001](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40081403001) against exact head `ff9675f5489f4148079b3ee7cd4a97810e352b4b`: **769 passed, 1 warning in 44.10s**. Broker-write boundary guard passed; SQLite and PostgreSQL 16 migration round-trips passed; synthetic PostgreSQL/document-volume restore drill passed and evidence artifact was uploaded.
- The preceding test-only correction [47aa91e](https://github.com/tarunsharma2610-del/tradepro-improved/commit/47aa91e2696bb6388af73ede568dfe89c4cbead7) asserts that a fixed-fee tariff rule with a maximum cap is rejected at rule construction. This does not weaken production validation.
- The single pytest warning is a Starlette/AnyIO deprecation warning. GitHub Actions also logged Node.js 20 action-runtime deprecation warnings. These did not fail the run.
- Aggregate `ORDER_FILL_SET` variance tests and the variance-only persistence service are present; this successful suite includes their tests. Variance records remain audit-only and do not promote charges or create per-fill allocations. Source-backed effective tariff applicability, charge composition, and durable accounting acceptance remain open gates.
- Synthetic restore is not actual Oracle Cloud recovery. PR #6 remains draft/unmerged. Live broker order execution and automatic accounting promotion remain disabled. All work stays in `tarunsharma2610-del/tradepro-improved`; never modify original `tarunsharma2610-del/Tradepro`.

## Upstox estimate reconciliation — corrected test and exact-head CI verified — 24 October 2026

- The corrected test fixture commit is [2a39a67](https://github.com/tarunsharma2610-del/tradepro-improved/commit/2a39a67cd1d2c8dab16e22425c87e247974c10cd). It updates the reported total consistently with the STT change so the replay-conflict test exercises replay behavior rather than failing the aggregate-reconciliation guard.
- Exact-head backend CI run [40082629274](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40082629274) passed on the then-current branch head [7e373f2](https://github.com/tarunsharma2610-del/tradepro-improved/commit/7e373f2f2ff0d2c7faae8397765df2d35b901599). Pytest, broker-write boundary guard, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and restore-evidence retention all passed. This confirms the previously failing workflow was corrected.
- This documentation synchronization creates a newer head, so CI must be checked again on the final resulting head before the documentation gate is called green.
- API estimates remain estimate-only. No candidate tariff rates were activated, no estimate was promoted into actual charges, and automatic per-fill allocation remains disabled pending reviewed component-specific rules and durable accounting acceptance.
- PR #6 remains draft/unmerged. Live broker order writes remain disabled. Work only in `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` is out of scope.

## Upstox component provenance checkpoint — 24 October 2026

- Upstox estimate normalization preserves `transaction`, `clearing`, `ipft`, and `sebi_turnover` as distinct components; it does not collapse them into a generic exchange-charge value.
- The component-separation regression test passed on exact PR head [0112f92](https://github.com/tarunsharma2610-del/tradepro-improved/commit/0112f92f065156e93069332be0a3665c601ab940), via [Backend tests run #40083185015](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40083185015). Pytest, broker-write boundary guard, SQLite/PostgreSQL migration round-trips, synthetic restore drill, and evidence-retention steps passed.
- Intermediate run #40083176492 failed at pytest before the test commit; it is superseded by the passing test-head run above.
- Estimate normalization is not tariff activation or actual-charge evidence. Do not map aggregate trade-charge outputs to individual fills or enable automatic transaction/clearing/IPFT allocation without reviewed component-specific semantics, source evidence, and an exact eligible-fill manifest.
- Open item: verify effective-dated component composition and GST taxable-base rules from official sources and reviewed fixtures; prevent IPFT double-counting where the tariff presentation combines it with transaction charges.
- PR #6 remains draft/unmerged; live broker order writes remain disabled. Work only in `tarunsharma2610-del/tradepro-improved`, never the original `tarunsharma2610-del/Tradepro`.

## PostgreSQL allocation concurrency CI — 24 October 2026

- Corrected PostgreSQL concurrency test fixture now creates valid portfolio, instrument, application-order, and broker-order prerequisites before broker fills. The initial fixture failed on a foreign-key constraint because it used random, non-persisted broker-order IDs; fixed in [fc0c539](https://github.com/tarunsharma2610-del/tradepro-improved/commit/fc0c539dc24f87a705207a16a98789fd63d928f8).
- Exact corrected head passed [Backend CI #40084015153](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40084015153): **777 passed, 1 warning**. CI set `TEST_POSTGRES_URL`; the PostgreSQL concurrency integration ran, alongside broker-write boundary checks, SQLite/PostgreSQL migration round-trips, and synthetic database/document restore with retained evidence.
- This verifies allocation persistence/concurrency only; it does not authorize tariff activation or automatic charge allocation. Keep transaction, clearing, IPFT and SEBI components distinct until official component-composition and GST taxable-base rules are reviewed; prevent IPFT double-counting.
- PR #6 remains draft/unmerged; live broker order writes remain disabled. Work only in `tarunsharma2610-del/tradepro-improved`, never the original `tarunsharma2610-del/Tradepro`.


## Upstox tariff coverage audit and exact-head CI — 24 October 2026

- Exact-head backend workflow [#40084947829](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40084947829) passed on commit `19fc2dcb6ba80d33324a58520fe1215fc4b8c36c`: **778 passed, 1 warning**. `TEST_POSTGRES_URL` was set; PostgreSQL concurrency tests ran. Broker-write boundary guard, SQLite/PostgreSQL migration round-trips, and synthetic PostgreSQL/document-volume restore passed. The single Python warning is a Starlette/AnyIO deprecation warning; CI also emits Node action-runtime deprecation warnings.
- Follow-up source coverage matrix added to `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`. It keeps brokerage, STT/CTT, stamp duty, exchange transaction charges, IPFT/clearing, SEBI turnover, GST, DP/demat and other fees separately scoped, with explicit unresolved gates. Current Upstox page/API evidence does not justify generic wildcard rules or automatic per-fill allocation from aggregate charge totals.
- No new tariff rule was approved or activated. DRAFT candidates remain non-selectable; tariff-driven automatic per-fill allocation remains disabled for unreviewed components. Resolve source/effective-date gaps, GST taxable base, transaction/IPFT inclusion, and DP per-scrip/day allocation before review/approval.
- PR #6 remains draft and unmerged; live broker order writes remain disabled. All work is confined to `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` remains out of scope.


## Phase 3 latest completed-work checkpoint — 24 October 2026

- **Verified regression-test commit:** `fd4253ce51f812886fa081eeae3499533bfe4e20`. Exact-head backend CI [run #40085703204](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40085703204) completed successfully: **780 tests passed**, with one Starlette/AnyIO deprecation warning (`anyio.abc.BlockingPortal`). CI set `TEST_POSTGRES_URL`, so PostgreSQL-specific tests were enabled. Alembic upgrade/downgrade checks through `202610240018`, broker-write boundary guard, and synthetic PostgreSQL/document-volume restore drill succeeded.
- **Latest code/test work:** `backend/tests/test_upstox_tariff_candidates.py` now checks candidate effective-window overlap for identical dimensions and enforces narrow-scoped exchange-charge candidate rows that remain DRAFT, without silently introducing an IPFT rule. These are scope/consistency guardrails; they do not validate or approve the rate values themselves.
- **Tariff audit status:** `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md` contains the component coverage matrix and approval gates for brokerage, STT/CTT, stamp duty, exchange transaction charges, IPFT/clearing, SEBI turnover, GST, DP/demat and other fees. Still unresolved: official effective-date/applicability evidence for all supported tuples; whether transaction-charge schedules include IPFT; product-specific GST taxable-component sets; and a reviewed basis for allocating aggregate/API and DP charges to fills.
- **Next step before further Phase 3 implementation:** use official, dated sources and appropriately scoped read-only API evidence to close these gates and add component-boundary fixtures. Do not infer per-fill actuals from aggregate totals. No DRAFT candidate was approved or activated in this work.
- **Safety / repo boundary:** work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` is out of scope and must remain untouched. PR #6 remains draft and unmerged. Live broker `place_order`, `modify_order`, and `cancel_order` execution remains disabled; PAPER mode remains mandatory.
- **CI scope note:** run #40085703204 validates the code at commit `fd4253ce...`; the documentation checkpoint commit that follows this note still requires its own CI result before it can be called green.


## Documentation checkpoint CI result — 24 October 2026

- The documentation checkpoint commit `177264164a9e495fc570fa4d5990aea3866317e5` passed exact-head workflow [#40086364594](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40086364594). Backend pytest reached 100% with **780 passing tests and one Starlette/AnyIO deprecation warning**. CI explicitly configured `TEST_POSTGRES_URL`; PostgreSQL-specific tests were enabled. Broker-write boundary guard passed, Alembic migration checks through `202610240018` completed, and synthetic PostgreSQL plus document-volume restore evidence was uploaded.
- This CI result validates commit `177264164...`; any subsequent documentation commit must be verified independently before its CI can be called green.


## Phase 3 source-conflict and candidate guardrail checkpoint — 24 October 2026

- Added an explicit finding to `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`: the current official Upstox charges page presents conflicting IPFT schedules. One table says ₹0.10/lakh for equity/futures and ₹0.50/lakh for options premium (₹10/crore and ₹50/crore); a later table says ₹0.01/crore for each. The page also says IPFT is combined with transaction charges while the API schema exposes `transaction` and `ipft` separately. These statements are not reconciled; do not infer inclusivity or add both amounts. GST base remains component-mapped and review-gated.
- Added regression test `test_unresolved_charge_components_are_not_added_as_tariff_candidates` to `backend/tests/test_upstox_tariff_candidates.py`. The candidate inventory must contain only the currently inventoried STT and exchange-charge categories, all DRAFT; GST, IPFT, stamp duty, brokerage, SEBI and DP/demat remain absent until scope/source/basis are reviewed.
- The existing candidate date-window and narrow-scope tests remain in place. These tests validate inventory guardrails, not rate correctness or tariff approval.
- Prior verified CI: workflow [#40085703204](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40085703204) passed on `fd4253ce51f812886fa081eeae3499533bfe4e20` with 780 tests. Documentation commit `5f3ef28897e3400bc5e415f5b4fcf7534a4fc07d` also passed [workflow #40086759124](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40086759124). The source-register update and latest regression-test commit have separate CI runs in progress; do not call their CI green until the exact-head runs complete.
- No DRAFT tariff candidate approved or activated. PR #6 remains draft/unmerged; live broker order writes remain disabled. Work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` stays untouched.


## Exact-head verification of IPFT guardrails — 24 October 2026

- Source-register update commit `96c687c1667257d894506c8cb7f8ab715d3612bc` passed CI: [run #40086827314](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40086827314).
- Latest candidate-regression commit `a6868241dce9c827d1c9f6918a192647af0168e3` passed CI: [run #40086856952](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40086856952). Pytest output reached 100%; **781 tests passed, 1 Starlette/AnyIO deprecation warning**. `TEST_POSTGRES_URL` was set; PostgreSQL-specific tests were enabled. Broker-write boundary guard passed; Alembic checks reached `202610240018`; synthetic PostgreSQL/document-volume restore evidence uploaded.
- The new regression test ensures unresolved charge categories (GST, IPFT, stamp duty, brokerage, SEBI and DP/demat) cannot silently enter the candidate inventory; only STT and exchange-charge research candidates remain, all DRAFT. It does not validate the numeric rates or authorize tariff selection.
- Official Upstox page discrepancy documented in the charge-rule register: one IPFT table lists ₹0.10/lakh (equity/futures) and ₹0.50/lakh (options premium), while a later table lists ₹0.01/crore and says IPFT is combined with transaction charges. This is unresolved; no IPFT or GST calculator/rule is approved, and no double counting is permitted.
- Documentation commit `ad6bfbee7da84453677f7a9a441bf7a79ded4c2e` has its own CI run [#40086974735](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40086974735); its final status was pending at the time of this note. The following documentation commit must also pass its own exact-head CI before being marked green.
- PR #6 remains draft/unmerged; live broker order writes remain disabled. Work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` stays untouched.


## Phase 3 API source-boundary regression checkpoint — 24 October 2026

- Added `test_aggregate_trade_charges_api_evidence_cannot_be_promoted_as_contract_note` in `backend/tests/test_broker_charge_source_reconciliation_service.py`. It tags evidence as `UPSTOX_TRADE_CHARGES_API`, asserts the contract-note verification path rejects it, and verifies pending allocations remain unpromoted with no reconciliation reference.
- Updated `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md` to distinguish the Brokerage Details API (request-scoped estimate) from Get Trade Charges API (segment/financial-year/date-range report), and from reviewed contract-note evidence. Aggregate totals must not be spread across fills without an independently reviewed basis; preserve raw component fields and avoid IPFT double counting.
- Code/test commit `426a0612b34b4fcf4e95ac23aeefcc6b0f990a4b` passed exact-head backend CI [run #40087358324](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40087358324): **782 tests passed, 1 Starlette/AnyIO deprecation warning**. `TEST_POSTGRES_URL` was set; broker-write boundary guard passed.
- Latest source-register commit `3040cb1b139643b8849928e23fa6b7af3dccde64` also passed exact-head CI [run #40087367504](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40087367504).
- Tariff activation blockers remain: conflicting/unclearly dated IPFT rows on the public Upstox page; exact transaction/IPFT inclusivity; product-specific GST taxable-component sets; effective-date/applicability proof; and reviewed per-fill attribution for actual charges. Candidate inventory remains STT and exchange-charge research rows only, all DRAFT.
- Safety: PR #6 stays draft/unmerged; live broker `place_order`, `modify_order`, and `cancel_order` remain disabled. Work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` remains untouched.


## Exact-head documentation CI confirmation — 24 October 2026

- Latest checkpoint commit `cbf83ad8c11d38390d82d42883c7e2c72f04a42a` passed exact-head backend CI [run #40087629909](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40087629909). The Backend pytest job completed successfully. This run validates the docs-only checkpoint, not any subsequent commit.
- The latest source-boundary test commit `426a0612b34b4fcf4e95ac23aeefcc6b0f990a4b` passed [run #40087358324](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40087358324): 782 tests passed, one Starlette/AnyIO deprecation warning; `TEST_POSTGRES_URL` was configured and the broker-write boundary guard passed.
- The API source register distinguishes request-specific Brokerage Details estimates, date/segment-scoped Get Trade Charges aggregates, and reviewed contract-note evidence. Regression coverage prevents the aggregate API evidence type from being promoted through the contract-note fill-allocation verification path.
- Open Phase 3 tariff gates remain: contradictory public IPFT rates and uncertain inclusivity; source-backed effective dates/applicability; product-specific GST taxable-component mapping; and a reviewed per-fill attribution basis for aggregate/DP charges. No candidate was approved or activated.
- Safety remains unchanged: work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` is untouched. PR #6 remains draft/unmerged; live broker `place_order`, `modify_order`, and `cancel_order` execution remains disabled.


## NSE IPFT source reconciliation — 24 October 2026

Primary source: [NSE Circular NSE/FA/73061, 27 February 2026](https://nsearchives.nseindia.com/content/circulars/FA73061.pdf), effective 1 March 2026. It shows combined member outflow rates of ₹307/crore/side for cash market, ₹183/crore/side for equity futures and ₹3,553/crore/side on options premium, split into transaction charges and ₹0.01/crore IPFT contribution. The legacy ₹10/₹50-per-crore IPFT schedule must not be added to the newer combined rates.

The source register marks the Upstox-page conflict partially reconciled for those NSE scopes, not fully approved. Account-specific API/contract-note reconciliation, effective-date/product-scope review and GST composition remain gates; this circular does not establish BSE/MCX rules. Candidate comment/test updates encode DRAFT combined rates (NSE cash 0.00307%, futures 0.00183%, options 0.03553%; BSE options 0.0325%) and forbid a separate IPFT candidate. Commits `68aae327`, `fc7fb146`, `c01cd66c`, and `777d0ee5` are included in the current PR head and covered by exact-head backend CI #40090309898 (786 passed, one warning). Their CI gate is closed; candidate source-rate approval and account-specific tariff validation remain open.

Previously verified: checkpoint commit `cbf83ad8c11d38390d82d42883c7e2c72f04a42a` passed [CI #40087629909](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40087629909). API source-boundary test commit `426a0612b34b4fcf4e95ac23aeefcc6b0f990a4b` passed [CI #40087358324](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40087358324): 782 tests passed, one deprecation warning.

Safety: work only in `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched. PR #6 remains draft/unmerged; live broker order writes remain disabled.


## GST component and NSE IPFT source audit — 24 October 2026

- Primary NSE Circular NSE/FA/73061 (27 February 2026; effective 1 March) reconciles the current NSE combined charge schedule: ₹307/crore/side cash, ₹183/crore/side futures, ₹3,553/crore/side options premium, with ₹0.01/crore IPFT contribution inside the total. Never add the legacy ₹10/₹50 IPFT rows on top. Source register documents the covered scopes and remaining account-specific validation.
- Reviewed Upstox's GST component statement and CBIC Stock Broking Services FAQ Q77–78 / Rule 33. Upstox lists brokerage + transaction + IPFT for intraday/F&O and adds demat for equity delivery; CBIC says STT/stamp-duty/other tax recoveries are excluded only if pure-agent conditions are met. Exact GST base remains unapproved until matched to an actual invoice/contract note; do not apply 18% to all charges or assume exclusions.
- Latest code/test commit `fc7fb1463091ae070ad9d82b8aea380506b9482b` passed [CI #40088003373](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40088003373): 782 tests passed, one Starlette/AnyIO warning; PostgreSQL was configured and broker-write guard passed. Source-register commit `777d0ee536f6809f01c5cea96b9a3b9b4d4f1e32` passed [CI #40088089474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40088089474). The current code/test head `81a67b64ec92cdf9178b4ec0ac9b5e3fc1d1e472` passed exact-head backend CI #40090835774 (786 passed, one warning), including the new post-commit refresh-failure/retry regression test. Later documentation-only commits should not be described as code/test failures; no new run has yet been returned for the subsequent docs-only head.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched. PR #6 remains draft/unmerged; live broker order writes disabled.


## Phase 3 latest-head checkpoint — 24 October 2026
- Coverage documentation commit `05f2dfdd6e0222fb091df17c15e1c72fe6d90cd1` has completed exact-head backend CI successfully: [run #40089127877](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40089127877). Backend pytest, broker-write boundary guard, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and evidence-artifact retention all passed.
- This green result applies to commit `05f2dfdd6e0222fb091df17c15e1c72fe6d90cd1`; any subsequent documentation or code commit requires its own exact-head CI before being called green.
- Acceptance review still open: verify rollback at important accounting write/failure boundaries; distinguish source-verification concurrency coverage from a full concurrent live-fill promotion race; decide/test reviewer-admin revocation semantics; maintain clear evidence that uploaded document hashes prove byte continuity, not broker-origin authenticity.
- Keep PR #6 draft/unmerged pending accounting acceptance. Live broker order submission stays disabled. Work only in `tarunsharma2610-del/tradepro-improved`; never modify original `tarunsharma2610-del/Tradepro`.


## Phase 3 accounting follow-up — 24 October 2026
- Regression commit `735dffc5194463893e5c57741d40da5ccfee7ed1` passed backend CI run [40089896692](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40089896692). The test suite, broker-write boundary guard, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic restore drill, and evidence retention all passed.
- The existing PostgreSQL concurrency suite already includes `test_live_fill_promotion_races_with_component_ledger_verification`. It races full live-fill accounting promotion against component-ledger promotion; it asserts no unhandled errors, permits a fail-closed pending-allocation result, checks that blocked promotion leaves no execution/position, retries safely, and verifies exact replay plus conflicting-charge rejection. Therefore this specific race test is present; do not keep describing it as missing. The exact-head backend workflow #40090309898 passed 785 tests with `TEST_POSTGRES_URL` configured; the PostgreSQL concurrency test was not skipped. This closes the test-execution-confirmation sub-gate; accounting acceptance review remains open.
- Rollback coverage now includes a failure after accounting rows are staged and a failed-commit path; continue checking whether any materially distinct write/flush boundary remains uncovered rather than claiming every conceivable failure point is tested.
- Reviewer authority is revalidated at live-fill promotion: the recorded reviewer must still be an active platform administrator. Tests cover role revocation and deactivation.
- Phase 3 remains open until the latest-head CI result is confirmed, accounting/rollback acceptance is reviewed, and all checkpoint documents are synchronized. PR #6 remains draft/unmerged; live broker order submission remains disabled. Work only in `tarunsharma2610-del/tradepro-improved`; never modify original `tarunsharma2610-del/Tradepro`.


## Latest exact-head CI verification — 24 October 2026
- Verified the current PR #6 head `81a67b64ec92cdf9178b4ec0ac9b5e3fc1d1e472` against backend workflow [#40090835774](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40090835774): **786 tests passed, 1 warning**. This includes the new post-commit refresh-failure/retry regression test. Broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and evidence retention all passed.
- The rule-bound brokerage-cap entrypoint follow-up commits `d6d60a03732ab322785d5e020f0521a4b96162c9` and `78f5f27135137a1d8f0882d2c0a91d013f6e8556` also have successful backend runs [#39977035981](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39977035981) and [#39977054423](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39977054423). The PR description was corrected to reflect those passing runs.
- The latest exact-head green status supersedes earlier notes that CI for the reviewer/rollback or tariff-cap follow-ups was still pending. Any subsequent commit still needs its own exact-head CI.
- Phase 3 acceptance remains open for final financial-accounting/rollback review and sign-off. The PostgreSQL live-fill/component-ledger race test exists; keep its scope distinct from any separate concurrency guarantees not directly covered. PR #6 remains draft/unmerged; live broker order submission remains disabled. Work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` remains untouched.


## Post-commit recovery regression — 24 October 2026
- Added `test_post_commit_refresh_failure_is_safe_to_retry_as_exact_replay` in commit [`81a67b64ec92cdf9178b4ec0ac9b5e3fc1d1e472`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/81a67b64ec92cdf9178b4ec0ac9b5e3fc1d1e472).
- Exact-head backend CI [#40090835774](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40090835774) passed **786 tests, 1 warning**. Broker-write guard, SQLite/PostgreSQL migration checks, synthetic restore drill, and evidence retention also passed.
- This covers the post-commit/pre-response interruption case: rollback cannot undo a committed transaction, so retry must return the existing execution without applying the fill twice. Phase 3 remains open for final acceptance/sign-off; PR #6 stays draft/unmerged and live broker order submission remains disabled.

## Exact-head CI checkpoint — 24 October 2026

- Documentation checkpoint commit `3e0ae8034f333e082bfa11b6da50aec9e620f242` passed GitHub Actions Backend tests run [`40091642139`](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40091642139): **787 passed, 1 warning**.
- Broker-write boundary guard passed. SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed. Synthetic PostgreSQL/document-volume restore drill and evidence-artifact retention passed.
- The warning is a Starlette/AnyIO deprecation warning; GitHub Actions also emitted Node.js 20 deprecation notices. No test or safety-guard failure was reported.
- This result applies to commit `3e0ae803` only; subsequent documentation commits require their own exact-head CI run.
- Phase 3 remains open pending final accounting acceptance and tariff-source applicability decisions. PR #6 remains draft/unmerged and live broker order submission remains disabled. Work only in `tarunsharma2610-del/tradepro-improved`; never the original `tarunsharma2610-del/Tradepro`.

## Upstox trade-wise P&L endpoint boundary — 24 October 2026

- The official `GET /v2/trade/profit-loss/data` endpoint (`https://upstox.com/developer/api-documentation/get-profit-and-loss-report/`) returns paginated trade-wise realized P&L rows, not a documented per-fill charge breakdown. Use it as matching context only; do not claim it proves charge components for each fill.
- Keep it distinct from `GET /v2/trade/profit-loss/charges`, which returns selected-scope aggregate charge totals/components, and `GET /v2/charges/brokerage`, which estimates charges for an input order.
- The read-only client method `get_profit_loss_report` must remain fixed-path GET-only, validate segment/FY/date/pagination inputs, sanitize errors, and never add broker order-write methods. Preserve OAuth tokens out of logs/fixtures.
- Actual charge allocation still requires reviewed contract-note evidence and exact matching; do not distribute aggregate charges across fills without a separately approved allocation policy.

- The official `GET /v2/trade/profit-loss/metadata` endpoint (`https://upstox.com/developer/api-documentation/get-report-meta-data/`) supplies `trades_count` and `page_size_limit` for a segment/FY/date scope. Use this metadata to guide pagination for `/trade/profit-loss/data`; do not hardcode an assumed page size beyond the documented API limit. It provides no charge components and does not authorize charge allocation.

## GST valuation and combined IPFT guard — 24 October 2026

- Upstox's public charges page says GST is 18% on brokerage, transaction charges and IPFT (plus demat charges for equity delivery), while also stating IPFT is combined with transaction charges. Do not add the combined-rate schedule and separate IPFT again or assume the GST base is proven by field names alone.
- CBIC's stock-broking FAQ (Q77, Rule 33 pure-agent treatment) says statutory recoveries such as STT and stamp duty are outside the broker's GST value only when pure-agent conditions are met; otherwise section 15 / Rule 27 valuation applies. Treat this as a scope warning, not a universal component mapping.
- Keep GST composition and impacted tariffs unapproved until dated account-specific Upstox tax-invoice/contract-note evidence establishes the exact segment/product/effective-date mapping. Preserve separate source components and fail closed on unresolved differences; no tax/tariff promotion from public text alone.


## 2026-10-24 — Variance rollback regression exact-head verification

- Follow-up fix commit: `5e036d7fcc1f5f439d4054700366d284d7b78061`.
- Fixed the rollback regression assertion to compare allocation snapshots in stable UUID order. This preserves checks of row identity, status, amount, and reconciliation reference while avoiding reliance on unspecified SQL row ordering.
- Exact-head GitHub Actions run [#40096380843](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40096380843) completed successfully: **793 passed, 1 warning**; broker-write boundary guard passed; SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks passed; synthetic PostgreSQL/document-volume restore drill completed.
- The prior failed run exposed a test-ordering issue, not evidence of an accounting mutation; the corrected regression now passes in the full backend suite.
- Phase 3 is **not complete**: source-backed Upstox tariff/GST mapping, final per-fill allocation acceptance, and final merge gates remain open. Tariff candidates remain DRAFT/non-selectable. PR #6 remains draft/unmerged. Live broker order submission remains disabled.
- Scope guard: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` remains out of scope and must not be modified.


## 2026-10-24 — Upstox charge-source register

- Added [`UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`](UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md) documenting the official Upstox Brokerage Details API (`GET /v2/charges/brokerage`) and Profit and Loss on Trades API as distinct estimate vs realized-charge evidence sources.
- Added [`CHANGELOG.md`](CHANGELOG.md) to record this Phase 3 checkpoint and the verified 793-pass code CI result.
- No effective-dated tariff was approved: official API schemas alone do not prove the user's active brokerage plan or current legal/exchange rates. All tariff candidates remain DRAFT/non-selectable pending authoritative dated sources and independent review.
- Existing arithmetic tests cover deterministic largest-remainder paise allocation, mapping-order independence, zero-weight exclusion from residual distribution, invalid inputs and order brokerage-cap arithmetic. Ledger verification remains fail-closed for generic QUANTITY/NOTIONAL allocation until component-specific rules are approved; only explicitly reviewed weights can be promoted.
- Exact-head CI for the latest documentation-only commits is still required before treating the branch checkpoint as fully verified. PR #6 remains draft/unmerged; live broker order submission remains disabled.
- Scope remains `tarunsharma2610-del/tradepro-improved` only; do not modify the original `tarunsharma2610-del/Tradepro` repository.


## 2026-10-24 — Exact documentation-head CI verification

- The exact documentation head `3f9e20bd70b218bff2837967da04b53732968c2b` passed [Backend CI run #40097569588](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40097569588).
- Result: **793 passed, 1 warning in 41.64s**. Broker-write boundary guard passed. SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks passed. Synthetic PostgreSQL/document-volume restore drill passed and evidence was retained.
- This closes the exact-head CI verification gate for the Upstox charge-source register and the documentation checkpoint that preceded this note. This new note itself is documentation-only and is not included in that already completed CI run.
- Phase 3 acceptance remains open: effective-dated Upstox/exchange/tax tariff evidence and independent approval, final per-fill allocation/accounting acceptance, and PR merge gates remain outstanding. Candidate tariff rules remain DRAFT/non-selectable. PR #6 remains draft/unmerged. Live broker order submission remains disabled.
- Repository boundary: `tarunsharma2610-del/tradepro-improved` only. The original `tarunsharma2610-del/Tradepro` must not be modified.


## 2026-10-24 — Reviewed fill-ID input validation hardening

- Added defensive validation in `backend/app/services/broker_charge_source_reconciliation_service.py`: each reviewed allocation-weight `fill_record_id` must be a string before UUID parsing. This prevents malformed JSON values such as `null`, numbers, or arrays from escaping the expected validation path as an unexpected exception.
- Added parameterized regression coverage in `backend/tests/test_broker_charge_source_reconciliation_service.py` for `null`, numeric, and list-valued fill IDs. Expected behavior is a controlled `ValueError`; no allocation is promoted by this validation path.
- Code commit: `10febb7a14c779ab7e308b9175ff4f16ad5fec44`; regression test commit: `067e76687eda71aa81aae1df6b8b16133cf42d86`.
- CI for this new code/test head is not yet reported by GitHub Actions at the time of this note; the previous 793-pass run does not verify these new changes. Combined commit status currently reports no status checks for the new head, so this fix remains unverified pending CI.
- Phase 3 remains open: effective-dated tariff source approval, per-fill accounting acceptance, exact-head CI and final PR review remain required. PR #6 stays draft/unmerged; live broker order submission remains disabled.
- Repository boundary remains `tarunsharma2610-del/tradepro-improved` only; do not modify original `tarunsharma2610-del/Tradepro`.


## 2026-10-24 — Reviewed fill-ID validation CI result

- Exact code/test head `ddeed926a16f235de777025db1053d9e110bbc11` passed GitHub Actions run [#40099389651](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40099389651).
- Result: **796 passed, 1 warning in 43.75s**. Broker-write boundary guard passed; SQLite and PostgreSQL migration upgrade/downgrade/re-upgrade checks passed; synthetic PostgreSQL/document-volume restore drill passed.
- This CI includes the new parameterized regression tests rejecting malformed reviewed `fill_record_id` values (null, numeric, list) before UUID parsing. It does not yet include the documentation-only updates made after this code/test head.
- Phase 3 remains open: component-by-component per-fill accounting acceptance, authoritative effective-dated tariff evidence and independent review, and final PR gates remain outstanding. Tariff candidates stay DRAFT/non-selectable. PR #6 remains draft/unmerged. Live broker order submission remains disabled.
- Scope guard: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` must remain untouched.


## 2026-10-24 — Invalid reviewed-weight regression coverage

- Added regression tests in `backend/tests/test_broker_charge_source_reconciliation_service.py` for negative weights, non-finite weights (`NaN`, `Infinity`), malformed decimal values, all-zero weight sets, and duplicate fill IDs in the reviewed weights manifest.
- Each case must fail closed before allocation promotion and leave ledger rows in `PENDING_RECONCILIATION`.
- Test commit: `cb577cd1c917da9f2af1e5a01607dd42377067ca`. GitHub Actions backend workflow #40099823190 was still running at the time of this documentation update; do not treat the prior 796-pass run as verification of these new tests. The new documentation commits will also require exact-head CI verification.
- Phase 3 remains open: allocation acceptance, authoritative effective-dated tariff evidence and independent review, exact-head CI, and final PR gates are pending. PR #6 remains draft/unmerged; live broker order submission remains disabled.
- Scope guard: work only in `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` must remain untouched.


## 2026-10-24 — Reviewed-weight validation tests CI verified

- Backend workflow [#40099906234](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40099906234) passed for code/test head `0d563f060055bb31c14a20f407a5f4b577843d48`: **802 passed, 1 warning in 48.62s**.
- The run includes the new invalid reviewed-weight regression cases (negative, NaN, Infinity, malformed decimal, all-zero and duplicate fill IDs), in addition to the malformed fill-ID tests. Broker-write boundary guard passed and synthetic restore-drill evidence was uploaded. The workflow also exercised PostgreSQL 16 migration downgrade/upgrade checks.
- This run verifies the code/test head before this documentation update, not the documentation commits below. A fresh exact-head CI result is required before treating the current branch tip as fully verified.
- Phase 3 remains open: per-component accounting acceptance and authoritative, effective-dated tariff evidence with independent review remain pending. PR #6 stays draft/unmerged; live broker order submission remains disabled.
- Repository scope is `tarunsharma2610-del/tradepro-improved` only. Do not modify original `tarunsharma2610-del/Tradepro`.


## 2026-10-24 — Charge API unusable-value provenance hardening

- Review found that `resolve_charge_api_value` retained the approved mapping's semantic and source fingerprint for usable values, but omitted source URL and SHA-256 provenance when the normalized field was `MISSING`, `NULL`, or `INVALID`. These values were already unusable, but their interpretation path was less auditable.
- Fixed the resolver to return approved mapping provenance for every normalized state while keeping missing/null/invalid values `usable=False`. Numeric zero remains a distinct present value; this change does not promote allocations or approve production Upstox mappings.
- Added regression coverage for missing, null, NaN, negative, boolean, and object values; assertions require mapping source URL, source SHA-256, and semantic to remain present. Added mapping effective-date and estimate-vs-actual guard cases.
- Implementation commit: `845e9e0dc924f11ae89b96ef73c94c59c2efb4b4`. Test commit: `1d7e24b0ba8c89062ec1eeddb93d0c4cd22a226f`. Documentation checkpoint is being synchronized; exact-head CI must pass before verification is claimed.
- PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains out of scope.


## 2026-10-24 — Resolver acceptance and CI checkpoint

- Backend workflow `40108183667` succeeded on prior head `8214430f562f6f425cfc1b9b6a6b3b547832b68a`. New resolver tests add exact broker/endpoint/schema/field/scope matching and non-finite-number rejection; newer commits still require CI.
- Mapping identity fixtures use immutable dataclass replacement. Intended-use semantics remain explicit; missing/null/invalid values remain unusable and retain provenance; numeric zero remains distinct.
- Accounting acceptance includes replay/conflict, ledger reconciliation, lock order, rollback, reviewer authority and PostgreSQL verification/promotion race coverage. Re-check exact test and workflow status before claiming complete. CI does not establish production tariff correctness or broker-origin authenticity.
- Safety gates unchanged: PR #6 draft/unmerged; live broker order submission and automatic quantity/notional allocation disabled; production Upstox mappings/tariffs unapproved. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Resolver field-identity guard added; CI pending

- Resolver now checks that the payload field name matches the terminal field in the selected approved mapping path. This closes a semantic mismatch where a caller could select `charges.ipft` but normalize another payload field.
- Implementation commit: `77aa77aec37dc535c3e427ca3f88c2ccb5e75ed8`; regression test commit: `5c5482c7f7fa623707698f64b6a061351e5e5b87`. CI for the latest commits is pending; previous green runs apply only to earlier heads.
- Existing accounting tests cover lock ordering, replay idempotency, conflicting evidence and rollback. A genuine concurrent two-session verification-versus-promotion race is not demonstrated in the inspected live-fill test file; locate/verify other integration coverage before marking complete.
- PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled; production Upstox mappings/tariffs remain unapproved. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Latest resolver CI verified; PostgreSQL race coverage located

- Latest PR head `ed346e823cbfae8448fae0134c4ff864bfcc60ac` passed Backend workflow [#40109041654](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40109041654). This verifies the field-identity guard and regression test at that head.
- Located PostgreSQL-only integration tests in `backend/tests/test_broker_charge_allocation_postgres_concurrency.py`, including concurrent source verification vs allocation promotion and live-fill promotion vs ledger verification, as well as conflicting fill-set and tariff estimate/variance persistence races.
- These tests require `TEST_POSTGRES_URL`. Verify the PostgreSQL workflow actually ran these tests rather than skipped them before treating concurrency acceptance as complete.
- PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled; production Upstox mappings/tariffs remain unapproved. Work only in `tradepro-improved`; original `Tradepro` remains untouched.


## 2026-10-24 — Official tariff/API source audit

- Upstox's `GET /v2/trade/profit-loss/charges` is a segment/financial-year/date-range aggregate `charges_breakdown`, not a documented per-fill record; its example returns `charges.ipft: null`. Do not map this response directly to actual per-fill evidence. Null is not zero. https://upstox.com/developer/api-documentation/get-trade-charges/
- NSE circular NSE/FA/73061 (27-Feb-2026, effective 1-Mar-2026) sets combined member outflow at ₹307/crore cash, ₹183/crore equity futures, ₹3,553/crore equity-option premium, including ₹0.01/crore IPFT contribution each side. This does not approve a broker-specific payload mapping. https://nsearchives.nseindia.com/content/circulars/FA73061.pdf
- Upstox's charges page contains both historical and newer effective-date tables; use effective-dated rules and account for its published STT/CTT transition from 1-Apr-2026. Avoid stale rates and double-counting separately stated IPFT where the exchange rate is combined. https://upstox.com/brokerage-charges/
- Production mappings/tariffs remain unapproved. PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled. Work only in `tradepro-improved`; original `Tradepro` remains untouched.
- The implementation head `ee1b2a74d2a9f6141b9afbb6e06562b5cf263a9b` passed workflow #40110597753; the present documentation commits need their own CI verification.


## 2026-10-24 — Upstox brokerage calculator restricted to estimates; CI pending

- Official Upstox `GET /v2/charges/brokerage` calculates charges from proposed order inputs; it is not proof of final booked per-fill charges. https://upstox.com/developer/api-documentation/get-brokerage/
- Resolver blocks this endpoint from `PER_FILL_ACTUAL` and actual `AGGREGATE_SUMMARY` use, even if a mapping is misleadingly labelled. `/v2/trade/profit-loss/charges` remains aggregate-only for per-fill purposes. Regression tests cover both mislabelled cases.
- Implementation `3486d854dae2451858a858cb627602aca7338969`; tests `6c92101a1890a0f4d761e86ed3db047a269fd10d`. The prior head passed workflow #40111501429; latest implementation/test CI must be verified.
- Production mappings/tariffs unapproved; null is not zero; automatic quantity/notional allocation and live order submission disabled. PR #6 draft/unmerged. Only `tradepro-improved` is in scope; original `Tradepro` untouched.

## Upstox SDK/API audit checkpoint (2026-10-24)

Before further Upstox implementation, read `UPSTOX_API_INTEGRATION_POLICY.md` and `docs/UPSTOX_SDK_API_REPOSITORY_AUDIT.md`. The current backend has async `httpx` REST calls, a dedicated V3 protobuf/WebSocket market-data service, a read-only reconciliation client, and a validated brokerage-estimate parser; `upstox-python-sdk` is not declared in `backend/requirements.txt`. Do not add the SDK blindly or replace working clients wholesale. First inspect the exact official package release, licence, dependencies, endpoint coverage, and async/error-handling fit in an isolated compatibility spike. Begin with read-only brokerage-estimate parsing against synthetic fixtures; no real credentials or live calls are needed. Inspect the official Upstox Agent Skill and its scripts before running them; development guidance only, never live-order authority. Preserve estimate-vs-actual accounting gates, PAPER mode, the broker-write guard, and all repository/PR safeguards. Only work in `tarunsharma2610-del/tradepro-improved`; PR #6 remains draft/unmerged; never modify original `tarunsharma2610-del/Tradepro`.

### SDK/Agent Skill review outcome (2026-10-24)

Read [`docs/UPSTOX_SDK_API_REPOSITORY_AUDIT.md`](docs/UPSTOX_SDK_API_REPOSITORY_AUDIT.md) and [`docs/UPSTOX_AGENT_SKILL_SECURITY_REVIEW.md`](docs/UPSTOX_AGENT_SKILL_SECURITY_REVIEW.md) before future Upstox SDK/skill changes. The official Python SDK v2.30.0 is generated and its brokerage method is synchronous by default; existing async `httpx` plus validated parsing already covers this endpoint. Do not add an unused SDK dependency. The upstream Agent Skill includes live order/GTT scripts; never execute them with live credentials, never copy its local config-token fallback or raw API exception-body printing into the app, and do not treat its interactive confirmation as an app authorization boundary. Use it only as reviewed development reference. PAPER mode and live-write safeguards remain mandatory.



## Phase 3 checkpoint — official GST/IPFT source cross-check (25 October 2026)

- Resumed the saved Phase 3 durable per-fill charge-allocation work. No framework code was integrated; current focus remains source-backed tariff acceptance and fail-closed accounting.
- Exact-head backend CI for prior head `7d4f2918b534ef9b4c3d32e7df22b754b21e6c8f` passed in run [40182196510](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40182196510). This verifies that head, not real-broker tariff authenticity or production restore.
- Current official Upstox charges page lists transaction charges effective 1 March 2026, STT effective 1 April 2026, GST bases by product, and says IPFT is combined with transaction charges while also showing an IPFT row. This does not establish whether a particular API `transaction` field is transaction-only or transaction-plus-IPFT. Do not double count IPFT or approve a field mapping until exact endpoint/schema semantics are verified.
- NSE confirms from 1 April 2026: options-sale STT 0.15% on premium (seller), exercised-option STT 0.15% on intrinsic value (purchaser), and futures-sale STT 0.05% (seller). CBIC says STT/stamp-duty/other-tax recoveries are outside GST value only where pure-agent conditions are met; otherwise Section 15/Rule 27 valuation applies. GST mapping must remain product/source-specific.
- No production field mapping or tariff was approved. Keep candidates DRAFT/non-selectable, preserve missing/null/zero distinctions, reviewed source-component evidence, paise-exact allocation, and fail-closed promotion. PAPER mandatory; live broker order writes disabled; PR #6 draft/unmerged; original `Tradepro` untouched.
- Official sources: https://upstox.com/brokerage-charges/ ; https://upstox.com/developer/api-documentation/get-brokerage/ ; https://upstox.com/developer/api-documentation/get-trade-charges/ ; https://www.nseindia.com/static/products-services/equity-derivatives-securities-transaction-tax ; https://cbic-gst.gov.in/sectoral-faq.html
- Next gate: continue component-by-component accounting acceptance and fault-injection/rollback review. Upstox's proposed-order brokerage calculator and segment/FY aggregate charges API are not proof of actual per-fill charges.


## Phase 3 resolver guard hardening — 25 October 2026

- Hardened source-level restrictions for Upstox aggregate-only `/v2/trade/profit-loss/charges` and estimate-only `/v2/charges/brokerage` endpoints. Guard canonicalizes broker-name casing and endpoint path spelling (trailing slash, query string, full URL) while reviewed mapping selection remains exact.
- Added regression tests so misleading approved mapping rows cannot convert aggregate/estimate data into per-fill actual accounting.
- Defensive code change only: no API field semantic or tariff approved. Production mappings remain unapproved, null is not zero, IPFT must not be double-counted, and charge-ledger promotion remains fail-closed.
- Exact-head CI for this code/documentation commit must be verified. PAPER mandatory; live broker writes disabled; PR #6 draft/unmerged; original `Tradepro` untouched.


## Versioned exchange-charge representation contract — 25 October 2026

- Added `backend/app/services/broker_charge_representation_contract.py` with pinned contract version `exchange-charge-representation-v1`. The validator requires an explicit reviewed representation mode, preserves original source labels, validates normalized component names and paise-precision amounts, and rejects combined transaction charges plus a separate IPFT amount to prevent double counting.
- Added `backend/tests/test_broker_charge_representation_contract.py` covering combined versus split representations, equivalent ₹307.00 exchange-charge base, duplicate IPFT rejection, missing components, unknown/inferred modes, invalid amounts, raw-label retention, and unsupported component labels.
- This contract validates representation only. It deliberately returns `accounting_approved: false`; it does not authenticate a source document, approve a broker API mapping, decide GST taxable composition, allocate aggregate amounts to fills, or enable live accounting. Existing promotion remains fail-closed.
- The implementation and test commits are `3c9ac46ea58257ba4c9c87b1b664eee14c6bd35a` and `be505e3dbc0e93eaa25a012d6a9afba81712e9ab`. Exact-head CI for the latest docs/code head must be checked before this checkpoint is called verified.
- PR #6 remains draft/open/unmerged; PAPER mode remains mandatory; live broker order writes and automatic generic quantity/notional allocation remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Persisted transaction/IPFT representation gate — 25 October 2026

- Added migration `202610250020` and nullable `source_label` / `representation_mode` fields on `broker_charge_source_components`. Existing rows retain their normalized component name as a source-label fallback, but representation mode is deliberately left undeclared rather than inferred.
- Source-component intake now preserves the original label and optional explicit mode. Review of `transaction_charges` / `ipft` rows invokes the versioned representation validator and remains blocked when mode is missing, when combined mode also has a separate IPFT row, when split mode lacks either row, or when sibling rows disagree on mode. Rejected review attempts leave rows pending.
- Added API regression tests for persisted label/mode, combined-plus-separate-IPFT rejection, and missing-mode rejection. Exact-head CI is required before calling this checkpoint verified.
- GST composition, endpoint/schema semantics, authenticated real contract-note evidence, and per-fill allocation approval remain separate gates. No live broker writes or generic quantity/notional allocation were enabled.


## Representation-gate CI correction — 25 October 2026

- The first API regression run exposed two assertion-message mismatches: the validator correctly rejected ambiguous combined-plus-IPFT input and undeclared representation mode, but the tests expected different wording. Updated the tests to assert the validator's actual fail-closed error messages; no safety rule was weakened.
- Follow-up exact-head CI for commit `df344e9c64aeb6ec3f2f01fef01f3c05739d4800` and subsequent documentation synchronization is pending. Do not call the current head green until the full workflow completes.


## Source-label completeness gate — 25 October 2026

- The representation contract now rejects intake where the retained source-label count differs from the normalized component count; regression coverage exercises missing labels. This preserves provenance and does not approve field semantics or actual charge accounting.
- Confirm exact-head CI after documentation synchronization. Tariff candidates remain DRAFT; API mappings and GST composition remain unapproved; no generic quantity/notional allocation or live broker order writes are enabled.
- Work only in `tarunsharma2610-del/tradepro-improved`; PR #6 remains draft/unmerged; PAPER mode remains mandatory; original `Tradepro` is out of scope.


## Authoritative IPFT/GST decision — 25 October 2026

This is the carried-forward project decision. Do not restart the IPFT/GST policy discussion or describe the agreed arithmetic as undecided. Keep the policy decision separate from the remaining source-evidence and production-approval gates.

### IPFT and NSE exchange-charge representation

Effective 1 March 2026, NSE circular NSE/FA/73061 records combined exchange-charge rates that include the IPFT contribution:
- Cash equity: ₹307.00 per crore.
- Equity futures: ₹183.00 per crore.
- Equity options: ₹3,553.00 per crore.

Canonical equivalent split arithmetic (transaction charges excluding IPFT, plus IPFT exactly once):
- Cash equity: ₹306.99 + ₹0.01 = ₹307.00 per crore.
- Equity futures: ₹182.99 + ₹0.01 = ₹183.00 per crore.
- Equity options: ₹3,552.99 + ₹0.01 = ₹3,553.00 per crore.

Rules:
1. For an explicitly reviewed combined source, preserve and use the combined transaction-charge amount; do not add a separate IPFT amount.
2. For an explicitly reviewed split source, use the transaction-charge amount excluding IPFT and add the separately evidenced IPFT amount once.
3. Never infer combined/split semantics from a field name alone. Preserve the original source label, endpoint/schema/version and raw value.
4. If the representation is missing, conflicting, null where an actual amount is required, or otherwise ambiguous, fail closed; do not silently substitute zero or promote it to actual per-fill accounting.
5. The combined/split validator is a representation safeguard, not proof of authentic source data or approval of a production API mapping.

Primary reference: NSE circular NSE/FA/73061, dated 27 February 2026, effective 1 March 2026: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf

### GST calculation policy

Use 18% GST on the applicable, evidence-backed taxable service-charge base, calculated from canonical components once. The working component policy recorded for Upstox is:
- Delivery: brokerage + transaction charges/IPFT + applicable demat transaction charges.
- Intraday, futures and options: brokerage + transaction charges/IPFT.
- Where transaction charges are represented as a combined amount that already includes IPFT, include that combined amount once; do not add IPFT again to the GST base.
- Where the source is split, combine transaction charges excluding IPFT with the separately evidenced IPFT exactly once.
- Apply pure-agent/exclusion treatment only where the applicable tax rule and invoice evidence support it; do not assume every charge is excluded from GST merely because it is statutory or separately labelled.
- Use the applicable product, segment and effective date, with documented rounding and invoice reconciliation. Do not reuse a taxable-base rule across products/dates without evidence.

Reference for published broker treatment: https://upstox.com/brokerage-charges/

### Decision versus remaining implementation gates

**Settled policy:** the combined-versus-split IPFT arithmetic above; IPFT must never be counted twice; GST is calculated from the applicable taxable canonical components once; unknown representation fails closed.

**Still required before production approval:** corroborate actual Upstox API/contract-note field semantics against authentic source evidence; approve effective-dated product/segment mappings and GST composition against invoices; test combined/split equivalence and no-double-count behavior in per-fill accounting; and pass exact-head CI. The Upstox Get Trade Charges endpoint is aggregate reconciliation evidence, not proof of actual per-fill charges. Do not label these remaining evidence/implementation gates as a reversal of the agreed calculation policy.

Safety remains unchanged: PAPER mode mandatory; live broker order writes disabled; PR #6 remains draft/unmerged pending review and user approval. All work is limited to `tarunsharma2610-del/tradepro-improved`; do not modify the original `tarunsharma2610-del/Tradepro`.

## Phase 3 execution-control documents — 25 October 2026

The detailed, Phase 3-only source of truth is now split into:
- `PHASE3_ROADMAP.md` — ordered remaining gates and exit criteria.
- `PHASE3_INSTRUCTIONS.md` — Phase 3 guardrails, repository/safety checks, evidence rules and verification workflow.
- `PHASE3_PROGRESS_REPORT.md` — gate-by-gate status and commit/CI evidence log.

Use these files before continuing Phase 3; do not recreate the plan from conversation history. Whole-project safeguards remain in force: only `tarunsharma2610-del/tradepro-improved`, never original `tarunsharma2610-del/Tradepro`; PAPER mode mandatory; live broker writes and automatic live-fill promotion/scheduling disabled; PR #6 remains draft/unmerged pending explicit user approval; preserve `BrokerFillIdentity` and `BrokerTradeRecord` separation; do not reopen Phase 2.

Verification boundary: exact-head CI passed on implementation SHA `97843aec1d9b0acc4d55d0fc4529b4ea5b81fd50` in [run #40187635881](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40187635881) (907 passed, 1 warning). The new Phase 3 planning/reporting documents were committed after that SHA. Therefore, this newer documentation HEAD must not be described as CI-verified until its own required workflow succeeds. Keep the Phase 3 report updated only after successful verification; record failed/pending runs honestly.



## Phase 3 forward checkpoint — persisted representation-contract version (2026-10-25)

- Audited the actual branch and confirmed the previous source-label authenticity guard is already implemented and CI-verified at `b92d0185f588e24d54510b36659944e77f498a6e`; this task does not repeat that work.
- Added nullable `representation_contract_version` to `BrokerChargeSourceComponent` and migration `202610250021`. Null is retained for legacy/undeclared rows; the migration does not infer a version for historical records.
- The source-component intake API now accepts, stores, and returns the version. Review of transaction/IPFT components requires the supported persisted version and requires sibling transaction/IPFT rows to agree on both mode and version before the existing combined/split validator runs.
- Added API regression assertions for persistence and response round-trip. Implementation commit: `1d327b145fe25d871a763985b5f746e12e107b75`. Exact-head backend workflow [#40190287853](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40190287853) was **in progress when this checkpoint was written**; do not mark the implementation CI-verified until its conclusion is successful. The documentation commit will require its own exact-head CI as well.
- This is an auditability step, not tariff approval, source authenticity proof, GST approval, or authorization to promote more components. Live accounting still requires its existing six-component set; extra components remain fail-closed. Paper mode and live-order safeguards are unchanged; PR #6 stays draft/unmerged; original `Tradepro` remains out of scope.
- Next single implementation gate: define and persist an explicit versioned component-set contract that distinguishes supported canonical accounting components from retained evidence-only components, then add tests proving missing, extra, duplicate, mixed-representation, and legacy-version rows cannot be silently omitted or promoted.


### CI correction history — persisted representation-contract version (2026-10-25)

- Workflow [#40190287853](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40190287853) failed on `1d327b145fe25d871a763985b5f746e12e107b75` due to one existing API regression assertion expecting the previous validation error wording. The underlying fail-closed mode check was still rejecting the request; the test stopped on the message mismatch.
- Corrected the response wording without relaxing validation in commit `db1ee170629fcb853b5c6e46f0d9d8654056bc44`. The failure remains recorded as history and is not counted as a successful verification.
- Workflow [#40190403007](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40190403007) was triggered for documentation HEAD `0abfa9a1ed5dcd553f1b92010ec86b41ccf77a2b`; that SHA predates the wording correction and must not be treated as verification of `db1ee170629fcb853b5c6e46f0d9d8654056bc44`. Exact-head CI for the corrected implementation and current documentation head remains pending.
- Next action: confirm the corrected exact-head workflow succeeds, then add explicit missing-version API regression coverage and continue the versioned component-set contract. No tariff candidates are promoted; live accounting still requires the existing six canonical components.


## Phase 3 forward checkpoint — versioned canonical component set (2026-10-25)

- Added `broker_charge_component_set_contract.py` with explicit `live-fill-accounting-component-set-v1` and the exact six canonical accounting components: brokerage, STT, exchange charges, SEBI charges, stamp duty, and GST.
- Added nullable `component_set_version` to source-component records via migration `202610250022`. No version is backfilled for legacy records. Canonical components receive the current set version only during independent review; evidence-only components remain unversioned and cannot be silently counted as canonical.
- Live-fill promotion now checks the full non-rejected source-component set before accounting: missing/extra/duplicate components, null/unsupported versions, and unreviewed rows fail closed. Additional evidence labels are preserved but block promotion until an explicit reviewed mapping exists. The prior six-allocation check remains in place.
- Added contract tests for exact set, missing/extra/duplicate components, legacy version and unreviewed rows. Updated the real PostgreSQL race fixture to declare the set version explicitly.
- Implementation/test checkpoint: `f61cedd25f5982846774db3028fb646d2e108e07`. Exact-head CI [#40191140007](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40191140007) passed: **917 passed, 1 warning, 0 failures**. Broker-write boundary guard, SQLite/PostgreSQL migration round-trips through migration `202610250022`, and synthetic restore drill passed. Synthetic restore does not prove actual Oracle Cloud recovery.
- Prior failed CI remains documented: run [#40190926423](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40190926423) exposed a missing set-version value in the PostgreSQL concurrency fixture; the fixture was corrected in the verified commit above. It is not counted as a successful run.
- This does not yet map raw `transaction_charges` + `ipft` source rows to canonical `exchange_charges`, approve tariffs/GST, or enable promotion of evidence-only rows. Live broker writes remain disabled; PR #6 remains draft/unmerged; original `Tradepro` remains untouched.
- Next single implementation gate: define and test an explicit, versioned source-to-canonical mapping for combined versus split transaction/IPFT evidence, preserving both raw source rows while producing one canonical exchange-charge amount only when the representation is explicitly reviewed. Other unsupported source components must continue to block promotion.


## Phase 3 forward checkpoint — combined/split source canonicalization contract (2026-10-25)

- Added `broker_charge_source_canonicalization.py` and focused tests. The pure contract maps explicit COMBINED transaction/IPFT source representation to one canonical `exchange_charges` amount, or sums SPLIT transaction charges plus separately evidenced IPFT exactly once. It retains source-row associations in its result and rejects ambiguous/mixed versions, double mapping, duplicate/missing labels, invalid amounts, and unsupported clearing/demat/other components.
- Exact-head CI [#40191589060](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40191589060) passed on implementation/test commit `44c12acd133924711cd68c27f315d9298c6acfde`: **930 passed, 1 warning, 0 failures**. Broker-write boundary guard and synthetic restore drill passed. Synthetic restore is not actual Oracle recovery.
- Important boundary: this is a tested pure canonicalization contract, **not yet wired into the API review flow or durable allocation ledger**. It does not authenticate source notes, approve tariffs/GST, allocate canonical totals to fills, or enable live accounting. Do not count the end-to-end mapping gate as complete.
- Current branch/PR safety remains unchanged: work only in `tarunsharma2610-del/tradepro-improved`; PR #6 stays draft/unmerged; PAPER mode mandatory; live broker writes disabled; original `Tradepro` untouched.
- Next single implementation gate: wire this canonicalization contract into reviewed source-component validation and per-fill allocation persistence so raw source rows remain immutable, canonical exchange charges reconcile exactly, and promotion cannot omit or double-count source components.


## Phase 3 checkpoint — verified source-component canonicalization adapter (25 October 2026)

- Added `backend/app/services/broker_charge_verified_component_canonicalization.py` and focused tests in `backend/tests/test_broker_charge_verified_component_canonicalization.py`.
- The adapter accepts only persisted `VERIFIED` rows tied to the expected evidence ID and matching SHA-256, with INR currency, reviewer identity/timestamp, unique row IDs, and source locators. It delegates the six-component and combined/split transaction/IPFT rules to the existing canonicalization contract and returns source-record provenance.
- Output explicitly remains `accounting_approved=false`. This is a validation adapter, not yet the transaction-owning persistence/promotion integration. It does not prove broker-origin authenticity, establish GST/tariff applicability, or enable automatic allocation.
- Implementation commit: `d3a2fc076a4309f23edbb14b0a47ba41fec0b557`; regression-test commit: `c8e3748f12c5674b1b77e76ff8fcf9b8f3dc68a6`. Backend workflow [#40192336466](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40192336466) passed on code/test commit `c8e3748f12c5674b1b77e76ff8fcf9b8f3dc68a6`; Backend pytest and the synthetic PostgreSQL/document-volume restore drill succeeded. Subsequent commits only synchronize documentation; no application code changed after the tested code/test head. No workflow run is associated with the latest docs-only head, so report the code/test head as green but do not claim a separately verified exact-head CI run for the latest docs commit.
- Next implementation gate: integrate this adapter into the existing locked source-component verification/allocation-promotion path; persist canonical totals and source-row associations atomically, and test duplicate/replay/conflict, rollback, partial fill sets, and PostgreSQL concurrency before enabling any accounting promotion.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 remains draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion remain disabled; production tariff/GST/IPFT interpretations remain unapproved.


## Phase 3 checkpoint — canonical source-to-allocation planning (25 October 2026)

- Added `backend/app/services/broker_charge_canonical_allocation_plan.py` and `backend/tests/test_broker_charge_canonical_allocation_plan.py`. The planning boundary composes reviewed-source canonicalization with deterministic paise allocation, returning per-fill amounts and source-row provenance without database writes or accounting approval.
- Only `EXPLICIT_REVIEWED` weights are enabled pending approved component-specific tariff rules. Contributing source rows must share the canonical fill manifest/hash, explicit weights, basis and allocation-method version. Split transaction/IPFT values are combined once into canonical exchange charges before allocation.
- Tightened the verified-source adapter to reject same-user extraction and review; added regression coverage.
- Commits: planner `a3a51ce8257b2300ead83158c423772f420545f8`; planner tests `1dffc90897e524a3c4065740daf3b31f2aaabf03`; independent-reviewer guard `f17e75ab4cc8eef448dd4743b942a13b0af8d2d0`; guard test `18d69d5fee2a4a2668cdf32a8ad0661aba8adbe3`.
- Backend workflow `40193811936` was in progress at the latest check. Do not mark the newest code/test head green until CI completes and covers the latest test commit. Database persistence/promotion integration remains the next gate.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion disabled; GST/tariff/IPFT interpretations unapproved.


## CI follow-up — canonical allocation planner (25 October 2026)

- Backend workflow [#40193836363](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40193836363) passed on independent-reviewer test commit `18d69d5fee2a4a2668cdf32a8ad0661aba8adbe3`. Backend pytest, SQLite migration cycle, PostgreSQL 16 migration cycle, and synthetic PostgreSQL/document-volume restore drill all succeeded.
- A newer docs-only checkpoint commit triggered Backend workflow [#40193954195](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40193954195), still in progress at last check. Code/test head is green; latest documentation head is not yet confirmed green.
- Next: wait for exact latest-head CI, then connect planning output to the locked persistence/reconciliation service using source-row provenance and canonical component identity. Do not promote accounting until transaction and replay/concurrency tests pass.


## Phase 3 checkpoint — verified canonical allocation persistence boundary (25 October 2026)

- Added `backend/app/services/broker_charge_verified_allocation_persistence_service.py`. It locks reviewed evidence and source rows, requires the approved `live-fill-accounting-component-set-v1` of six independently reviewed direct-mapped components, builds the verified canonical plan, and delegates to the existing idempotent allocation persistence service. It leaves allocations `PENDING_RECONCILIATION`, never commits, and requires caller-owned outer transaction.
- Added persistence-boundary tests in `backend/tests/test_broker_charge_allocation_persistence_service.py` for successful direct-component allocation and rejection of an unapproved component-set version.
- Split transaction/IPFT planning is supported, but persistence deliberately rejects it until a durable canonical-component ledger links multiple raw source rows to one canonical exchange-charge component.
- Implementation commit `d92219dcae765c2b8a305a825ae10c4596315f6a`; tests commit `9a837155260d0f2fef4cd9fd9dee458b2db13f90`. Exact-head Backend workflow [#40194167945](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40194167945) was in progress at last check; do not mark the new boundary green until it completes.
- Next: inspect exact-head CI; if green, implement durable canonical-component/source-row associations for combined/split transaction/IPFT, then add rollback, replay/conflict and PostgreSQL concurrency tests.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion disabled; tariff/GST/IPFT interpretations unapproved.


## Phase 3 checkpoint — durable canonical source snapshots (25 October 2026)

- Added `BrokerChargeCanonicalComponent` model, migration `202610250023_canonical_charge_components.py`, model registration, and `broker_charge_canonical_component_snapshot_service.py`.
- The materializer locks reviewed evidence and source rows, verifies stored contract-note bytes against SHA-256/size, requires independent source review and the approved component-set version, canonicalizes reviewed rows, and creates six versioned canonical snapshots in `PENDING_REVIEW`. It preserves exact raw source row IDs, source fingerprint, mapping/representation version, amounts, fill manifest/weights, and allocation policy. Identical snapshots replay idempotently; changes to reviewed allocation metadata create a new revision.
- Tests cover direct snapshots, split transaction/IPFT mapping to one exchange-charge snapshot, idempotent replay, unverified rows, tampered source documents, and revisioning after allocation-metadata changes.
- Latest code/test commit: `af14297ee904b7b021fc149e3ac3adf2cb0743f1`. Exact-head Backend workflow [#40194614746](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40194614746) was in progress at last check; do not call the new snapshot model/migration green until it completes.
- Next: verify migration/test CI, then add a distinct reviewer workflow for canonical snapshots and adapt allocation reconciliation to reference canonical snapshot IDs/source fingerprints rather than assuming one raw source row equals one canonical component.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion disabled; production tariff/GST/IPFT interpretations unapproved.


## Phase 3 CI correction — canonical snapshot test (25 October 2026)

- Backend workflow [#40194614746](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40194614746) reported 1 failure and 951 passes. The failure was test-only: the split transaction/IPFT snapshot test passed string UUIDs to a SQLAlchemy UUID column query. Fixed the test to convert persisted source-row IDs to `UUID` objects in commit `0a7437b9b413f86832cc029b983751c25007e21a`.
- The prior run is not green overall. Verification of the correction is pending a new Backend CI result; do not report canonical snapshot work as green yet.
- The migration/model and snapshot materializer remain on the Phase 3 branch only. No live-order or accounting-promotion behavior was enabled.


## CI follow-up — canonical snapshot UUID test correction (25 October 2026)

- Corrected the split transaction/IPFT test to pass UUID objects to SQLAlchemy. Exact code/test commit `0a7437b9b413f86832cc029b983751c25007e21a` passed Backend workflow [#40194933563](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40194933563): pytest, broker-write boundary, SQLite and PostgreSQL 16 migration cycles, and synthetic PostgreSQL/document-volume restore all succeeded.
- Documentation-only head `408af47077c18ecbe22418bad8cae109cf8741ef` triggered Backend workflow [#40195063845](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40195063845), which was in progress at the last check. Do not claim that later documentation head green until it completes.


## Phase 3 checkpoint — independent canonical snapshot review (25 October 2026)

- Added `broker_charge_canonical_component_review_service.py` to review canonical snapshots separately from raw source-row review. It rechecks stored contract-note bytes, source-row IDs, current canonical mapping/amount, mapping and representation versions, and source fingerprint under locks. Only an active admin distinct from the snapshot creator, source reviewer, and extractors can mark a snapshot `VERIFIED` or `REJECTED`; decisions are immutable and exact replay is idempotent.
- Added tests for split transaction/IPFT review, independent reviewer enforcement, idempotent review replay, and rejection when a source locator changes after snapshot creation.
- New code/test commit `9bb7ebaeeaee62753ba7580cf1dc94400df5aea4`; Backend workflow [#40195392377](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40195392377) was queued at the latest check. Do not mark the new reviewer workflow green until CI completes.
- Next: verify this CI result, then extend allocation persistence/reconciliation to bind allocations to the verified canonical snapshot ID and source fingerprint, including combined/split transaction/IPFT.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion disabled.


## Phase 3 checkpoint — allocations linked to verified canonical snapshots (25 October 2026)

- Added nullable `BrokerChargeAllocation.canonical_component_id` plus migration `202610250024_link_allocations_to_canonical_components.py`. Historical rows remain NULL; no inferred backfill.
- Added `broker_charge_canonical_allocation_persistence_service.py`. It requires a `VERIFIED` canonical snapshot, re-runs independent snapshot integrity/reviewer validation, delegates to the evidence-locked idempotent allocation writer, and persists the canonical snapshot foreign key on every allocation. It never commits or marks allocations reconciled. Split transaction/IPFT can now be planned, snapshotted, independently reviewed, and persisted against one canonical exchange-charge identity.
- Added integration coverage for split transaction/IPFT snapshot review and allocation persistence, exact ₹307.00 reconciliation, snapshot foreign-key linkage, pending-only status, and idempotent replay. Corrected canonical snapshot code/test commit `0a7437b9b413f86832cc029b983751c25007e21a` passed workflow [#40194933563](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40194933563); independent snapshot review passed [#40195392377](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40195392377).
- Latest persistence test commit `be761f4064136662ea1e5c18fef0c2b40237a387`; Backend workflow [#40195695138](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40195695138) was in progress at last check. Do not call the new migration/persistence path green until it completes.
- Next: verify exact-head CI; then implement canonical-snapshot allocation verification and promotion so live-fill accounting validates canonical snapshot IDs and fingerprints instead of assuming one raw source row per canonical component.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion disabled.


## Phase 3 — normalized source-to-canonical charge links (25 October 2026)

- Added `BrokerChargeCanonicalSourceLink` and migration `202610250025_normalize_canonical_source_links.py`. The relational database now explicitly stores each canonical snapshot-to-source-row edge, including source order, with foreign keys and uniqueness constraints. Migration backfills solely from the snapshot's persisted ordered source-ID manifest and fails on malformed/duplicate manifests rather than inferring membership.
- Snapshot materialization persists normalized edges; idempotent replay and independent review compare the relational links with the immutable manifest. Review fails closed if any link is missing, reordered or inconsistent. This makes split transaction/IPFT (two raw source rows → one canonical exchange-charge snapshot → linked per-fill allocations) explicit and auditable.
- Previous branch head `4dbaf27fae124d11935c271f2f4cdec44015dbaa` passed Backend workflow [#40196030459](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40196030459). Normalized-link change `d1153a0f0751339f3ca82fc062701db0141d4749` is pending fresh CI verification.
- Next: verify the new migration on SQLite/PostgreSQL 16 including downgrade/re-upgrade and all tests; then bind accounting promotion/reconciliation to normalized source links and canonical snapshot fingerprints.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion disabled.


## Phase 3 — normalized source links and canonical reconciliation gate (25 October 2026)

- Normalized source-link migration passed Backend workflow [#40196529023](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40196529023), including pytest, broker-write boundary, SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade and synthetic restore drill.
- Added `broker_charge_canonical_allocation_reconciliation_service.py` to validate the independently verified snapshot, source fingerprint and normalized source links, fill manifest, deterministic paise amounts, INR/method/basis and exact total before atomic promotion. Reconciliation is idempotent and its durable reference binds snapshot ID, source fingerprint, fill-set hash and allocation method; caller owns commit/rollback.
- Added split transaction/IPFT source-link, promotion/replay and tamper-blocking tests. Commit `621ce7cd289057a419be5eeff0262e158b18c001` Backend workflow [#40196784435](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40196784435) was in progress at the checkpoint; do not call the new path green before completion.
- Next: resolve exact-head CI failures, then cover conflicting evidence, transaction rollback and PostgreSQL concurrent promotion.
- Safety unchanged: Improved repo only; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; no live broker writes enabled.


## CI result update — canonical reconciliation gate (25 October 2026)

- Backend workflow [#40196784435](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40196784435) completed successfully for code/test commit `621ce7cd289057a419be5eeff0262e158b18c001`. Pytest, broker-write boundary enforcement, SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade and synthetic PostgreSQL/document-volume restore all passed.
- This green result verifies the normalized source-link schema and canonical allocation reconciliation tests at that code/test head. Later docs-only commits need exact-head CI verification if triggered.
- Next: explicit rollback/conflicting-set and PostgreSQL concurrent-promotion coverage, then fresh exact-head CI. Live broker writes remain disabled; PR #6 stays draft/unmerged and PAPER remains mandatory.

## AUTHORITATIVE CURRENT STATE — supersedes older next-step notes (25 October 2026)

Historical entries remain historical records; they must not override this current checkpoint.

- Repository: `tarunsharma2610-del/tradepro-improved` only. Branch: `phase3/durable-per-fill-charge-allocation`. PR #6 is open, draft, and unmerged. Never work in original `tarunsharma2610-del/Tradepro`.
- Latest verified implementation/test head: `3d8c4e1425825e6b996500ce9f24630d6352ff5e`.
- Exact-head Backend workflow [#40200645237](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40200645237) completed successfully. Pytest, broker-write boundary enforcement, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration upgrade/downgrade/re-upgrade, and synthetic PostgreSQL/document-volume restore all passed.
- Latest test `test_canonical_reconciliation_rejects_incomplete_allocation_fill_set` removes one row from a two-fill canonical set and confirms promotion fails closed, leaving the remaining row pending without a reconciliation reference.
- Completed; do not repeat: normalized canonical/source links, reviewed immutable snapshots, split transaction + IPFT provenance, durable per-fill allocations, canonical ledger verification, deterministic paise allocation, promotion/replay, tampered-allocation rejection, existing rollback assertions, and incomplete-fill-set rejection.
- **Next single implementation step:** inspect existing coverage and add PostgreSQL concurrent-promotion tests proving concurrent attempts cannot create partial/mixed states or inconsistent durable references. Add conflicting-set/rollback tests only where a real gap remains. Then run the full backend CI gate.
- CI protocol: on failure, diagnose/fix/rerun. On pass, update all 18 maintained checkpoint documents with exact SHA/run/result and next step, commit checkpoint, then verify CI on the checkpoint commit itself. Before resuming, refresh the live PR head and read docs from that exact SHA.
- GST/IPFT production tariff/account-specific acceptance is a separate evidence gate and does not block synthetic engineering tests. Unapproved tariff candidates remain DRAFT.
- Safety: PAPER mandatory; live broker order writes disabled; PR #6 stays draft/unmerged absent explicit authorization; original `Tradepro` untouched.



## Verified checkpoint — 2026-10-25
- Implementation commit: `07df26a88d5eb9cbebc76a5654e10e00e38de171`.
- Backend CI run #40204137793 completed successfully on that exact commit: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40204137793
- Root cause resolved in code: complete durable reconciliation references exceeded the prior 200-character database column. The model and migration `202610250026_widen_charge_reconciliation_reference.py` now allow 320 characters; downgrade explicitly refuses to truncate references longer than 200 characters.
- PostgreSQL concurrent-promotion test has passed as part of the successful Backend CI run. Treat the test as verified on the implementation commit; the documentation checkpoint itself still requires exact-head CI.
- Next: after documentation checkpoint CI is green, audit whether any conflicting-set/rollback/concurrency acceptance gap remains, add tests only for verified gaps, then rerun the full backend gate.
- Mandatory protocol: every CI failure → inspect full failure, fix root cause and rerun; every CI pass → update all 18 maintained checkpoint documents, commit a checkpoint with exact SHA/run/results/next step, then verify CI on that checkpoint commit itself.
- Safety: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched. PR #6 stays draft/unmerged. PAPER mode mandatory; live broker order writes disabled. GST/IPFT tariff acceptance remains a separate production-evidence gate; synthetic engineering work is not blocked.


## Authoritative checkpoint — 26 October 2026 (documentation CI verified)

- Repository: `tarunsharma2610-del/tradepro-improved`; branch: `phase3/durable-per-fill-charge-allocation`.
- Latest implementation commit: `ac7d27f2c9922925483b5b906c484c0d5a4e3f53`; exact-head Backend CI [#40287765745 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40287765745).
- Documentation synchronization commit: `f90573d653c7103bf9cfdb1f867da97b176d3240`; its exact-head Backend CI [#40289107666 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40289107666). Backend tests, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore/evidence retention passed. Synthetic restore is not proof of actual Oracle Cloud recovery.
- Approved public Upstox STT/exchange rules are estimate-only. Account-specific actual charges, GST taxable-base composition, stamp duty, SEBI/DP/demat/other charges, unsupported exchange/segment mappings, and per-fill actual evidence remain unapproved. Candidate tariff entries remain DRAFT unless separately allowlisted and reviewed.
- Phase 3 remains in progress. Next gates: independently reviewed tariff applicability; component-specific per-fill allocation rules; invoice/source-backed GST/IPFT and product/segment evidence; final adversarial, migration and recovery review; exact-head acceptance sign-off. Do not repeat canonical live-fill integration.
- Safety: PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. PR #6 stays open/draft/unmerged without explicit user approval. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.
- This documentation commit’s CI is green. Continue only from this checkpoint and verify CI for every subsequent implementation/checkpoint commit. Historical entries do not supersede this checkpoint.


## GST/IPFT checkpoint — 26 October 2026

- Regression test `test_gst_arithmetic_is_invariant_for_combined_vs_split_ipft_representation` verifies equivalent synthetic representations produce ₹307.00 base and ₹55.26 GST at 18%; this is arithmetic coverage, not approval of real taxable-component mapping. Test commit `8b4ae0b431d6aa03f1a8ae347a0b5fa7bda44c4f` passed exact-head Backend CI [run 40296066304](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40296066304).
- NSE circular `NSE/FA/73061` dated 27 Feb 2026, effective 1 Mar 2026, specifies combined outflows ₹307/crore cash, ₹183/crore equity futures and ₹3,553/crore equity-options premium including ₹0.01/crore IPFT: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf. Upstox's public schedule describes 18% GST on specified brokerage, transaction, IPFT and equity-delivery demat charges and says IPFT is combined with transaction charges: https://upstox.com/brokerage-charges/.
- CBIC states STT/stamp-duty recoveries are outside GST value only where Rule 33 pure-agent conditions are met; otherwise valuation rules apply: https://cbic-gst.gov.in/sectoral-faq.html and https://cbic-gst.gov.in/valuation-rules.html.
- Production GST mapping remains blocked pending product/segment-specific review and reliable invoice/contract-note reconciliation. Never apply GST to trade notional or all charges indiscriminately, or count separate IPFT twice. Candidate tariff rules remain DRAFT.
- Next gate: component-level GST acceptance cases across equity delivery, intraday and F&O, then exact-head CI and maintained-doc synchronization. PAPER mode mandatory; live broker order writes disabled; PR #6 draft/unmerged; original `Tradepro` untouched.


## Canonical latest Phase 3 checkpoint — 26 October 2026

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **Verified code/evidence head:** `d287da70ce184c904c6f9ede9e4a0edca5839f8f` (commit: “docs: reconcile public Upstox contract note GST examples”).
- **Exact-head CI:** PASS — [GitHub Actions run #40304398632](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40304398632), commit `d287da70ce184c904c6f9ede9e4a0edca5839f8f`; **1,004 passed, 1 warning**. Broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and restore-evidence retention also passed. This is CI evidence, not proof of a real Oracle recovery or broker-origin authenticity.
- **GST/IPFT research:** Three public third-party historical Upstox note copies were reconciled: 11-Feb-2025 base ₹2.97 / IGST ₹0.53; 21-May-2024 base ₹77.56 / IGST ₹13.96 (IPFT ₹0.11 listed outside that note's printed base); 12-Mar-2025 base ₹2.75 / IGST ₹0.50. Printed-base compositions differ historically. The current official Upstox schedule supports the **estimate-only** base of brokerage + transaction charges + demat where applicable + IPFT, with IPFT represented exactly once because it is combined with transaction charges. Do not add SEBI to this current estimate base without current applicable billing evidence; never calculate GST on trade notional or infer zero from missing/null fields.
- **Tax/accounting approval:** all four GST component candidates remain `DRAFT`. Historical public copies do not prove current actual per-fill billing across products/accounts. Actual-charge promotion stays gated; estimate logic and actual invoice reconciliation are distinct. Follow effective dates and preserve raw API/source evidence.
- **Next action when resuming:** continue Phase 3 from this exact commit and checkpoint. Next gate is component-specific GST acceptance cases for equity delivery, intraday, futures and options, then implementation review and exact-head CI; do not restart from earlier saved checkpoints.
- **Safety / PR:** PAPER mode mandatory; live broker `place_order`/`modify_order`/`cancel_order` and automatic live-fill promotion remain disabled. PR #6 remains open, draft and unmerged. Original `tarunsharma2610-del/Tradepro` is not the work target and must remain untouched.
- This checkpoint supersedes older statements in this document about CI being in progress or requiring verification for the pre-`d287da7` head. Historical notes remain history; this is the canonical resume point.

## Canonical resume checkpoint — 26 October 2026 (latest branch head verified)

- **Target:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **PR #6:** open, draft, unmerged. Never modify original `tarunsharma2610-del/Tradepro`.
- **Latest branch head before this documentation synchronization:** `5c929ff933d627dd81d5c32ec863843c2ef0f19b` (`docs: record deferred Algory plan in progress checkpoint`). Exact-head Backend CI **PASS**, run [#40315135121](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40315135121): **1,004 passed, 1 warning**. Broker-write boundary guard, SQLite and PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore and evidence retention also passed. Synthetic restore does not prove real Oracle recovery.
- **GST/IPFT finding:** the current official Upstox page supports an 18% **public-schedule estimate** base of brokerage + combined transaction/IPFT charges + delivery demat where applicable. Count combined transaction/IPFT once. CBIC FAQ Q77 makes exclusion of STT/stamp duty/other recoveries conditional on Rule 33 pure-agent conditions. Three public historical third-party notes show differing printed taxable bases (11-Feb-2025 ₹2.97/IGST ₹0.53; 21-May-2024 ₹77.56/IGST ₹13.96, with IPFT separately outside that printed base; 12-Mar-2025 ₹2.75/IGST ₹0.50). These notes are not authenticated current evidence and do not settle present account-specific billing.
- **Decision:** all four product GST component candidates remain `DRAFT`; actual per-fill GST promotion is blocked pending reviewed current source/invoice mapping. Never tax trade notional, infer zero from missing/null fields, or double-count IPFT. The Upstox aggregate charges endpoint is not per-fill evidence; the brokerage calculator is estimate-only.
- **Next gate:** continue Phase 3 product/segment-specific GST component acceptance and evidence reconciliation, adding tests only for demonstrated gaps. Do not repeat canonical live-fill integration or restart from older checkpoints. Defer AI/open-source adaptations, including Algory.app, until Phase 3 acceptance.
- **Safety:** PAPER mode mandatory; live broker order writes and automatic live-fill promotion/scheduling remain disabled. Do not merge PR #6 without explicit user approval. The documentation-sync commit must itself pass exact-head CI before it becomes the next validated checkpoint.

## Canonical checkpoint update — 26 October 2026, after cross-repository GST/IPFT audit

- Validated parent commit: `0e15bba3bfa425296f4104c96be6d10e3b42bf40`; Backend tests PASS on exact SHA, run [#40329710846](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40329710846). This documentation-only sync needs its own exact-head CI pass before it is the next validated checkpoint.
- Target repo/branch: `tarunsharma2610-del/tradepro-improved`, `phase3/durable-per-fill-charge-allocation` only. Never edit original `tarunsharma2610-del/Tradepro`.
- GST/IPFT: all four product component candidates remain `DRAFT`. OpenAlgo is architecture inspiration only; the inspected India preset is not an Upstox tax authority. Shoonya's hard-coded example is unverified; NautilusTrader applies to fee-model mechanics, not Indian tax rules.
- Discrepancy: Upstox's documented brokerage API example GST arithmetic does not align with current public tariff wording. This flags a docs-example discrepancy, not proof of live API miscalculation.
- Evidence gate: obtain current ordinary-trade Upstox contract notes/tax invoices or written broker clarification for delivery, intraday, futures and options. Reconcile taxable value against printed components and effective date. Historical rights-entitlement notes and estimate/aggregate APIs do not satisfy this gate.
- Invariants: count combined transaction/IPFT once; never add legacy IPFT on top of combined tariff; never tax trade notional; missing/null is unknown, not zero; do not treat aggregate charges or estimates as actual per-fill GST evidence.
- Next: continue Phase 3 evidence reconciliation and targeted tests only where supported by evidence. Do not repeat canonical live-fill integration. Defer AI/open-source integration including Algory.app until Phase 3 acceptance.
- Safety: PAPER mode mandatory; live broker order writes and automatic live-fill promotion/scheduling disabled; PR #6 stays draft/unmerged absent explicit user approval.


## GST/IPFT reconciliation checkpoint — 26 October 2026

- Official Upstox schedule https://upstox.com/brokerage-charges/ says GST is 18% on brokerage + transaction charges + IPFT, and includes DP/demat for equity delivery. From 1-Mar-2026, published NSE combined transaction/IPFT totals are cash ₹307/crore, equity futures ₹183/crore and equity options ₹3,553/crore on premium. Never add IPFT twice. NSE circular: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf (NSE/FA/73061, 27-Feb-2026).
- Open discrepancy: official Upstox Brokerage Details API example https://upstox.com/developer/api-documentation/get-brokerage/ shows transaction ₹5.68 + IPFT ₹0.17 but GST ₹1.02, matching 18% of ₹5.68 rather than ₹5.85 (approx ₹1.05). Treat as docs-example mismatch, not proven live production defect.
- Upstox Trades Charges API https://upstox.com/developer/api-documentation/get-trade-charges/ is aggregate by segment/date range and may return IPFT null; null is unknown, not zero, and aggregate output is not per-fill proof.
- Public third-party contract-note copies from 2024/2025 are historical, unauthenticated, pre-current-tariff and show differing taxable bases. They support historical layout/schema checks only.
- Estimate may follow current schedule with effective-date/product/exchange handling and combined transaction/IPFT counted once. Actual per-fill GST candidates for delivery, intraday, futures and options remain DRAFT pending current public invoice evidence or written Upstox clarification. No actual-charge logic promoted.
- Previous exact-head CI passed on 996b126ff678b97441f0214ea817451ee1592203: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40341429226 (tests, broker-write boundary, SQLite/PostgreSQL migration round-trips, synthetic restore and evidence retention). The next docs commit must pass its own exact-head CI.
- Scope: repository tarunsharma2610-del/tradepro-improved only; original Tradepro untouched. PAPER mandatory; live order writes and automatic live-fill promotion/scheduling disabled; PR #6 draft/unmerged; do not ask user for a personal contract note; defer AI/Algory until Phase 3 acceptance.


## GST estimate implementation update — 26 October 2026

- Added backend/app/services/upstox_public_gst_estimate.py and backend/tests/test_upstox_public_gst_estimate.py. This is public-schedule estimate logic only, not actual-charge evidence; it uses explicit components and an 18% GST rule and labels results PUBLIC_SCHEDULE_ESTIMATE_ONLY.
- Supported scopes from 1-Mar-2026: NSE EQ delivery/intraday, NSE FO futures/options, and BSE FO options. Delivery requires brokerage, exchange_charges and explicit demat_charges; other scopes require brokerage and exchange_charges. NSE exchange_charges includes combined transaction/IPFT once; separate ipft is rejected. For BSE options use applicable BSE charge source, do not assume an NSE IPFT component.
- Official Upstox API sample conflict remains: transaction ₹5.68 + IPFT ₹0.17 but GST ₹1.02; 18% of ₹5.85 is about ₹1.05. Estimate follows tariff wording, actual per-fill billing remains unresolved. Four actual GST component candidates remain DRAFT.
- See GST_IPFT_ACCEPTANCE_MATRIX.md. Code/test head 221493eb17729533cfaf855e2ce52532ef0903ac had CI run #40342805295 pending at note time; this documentation commit also needs exact-head CI.
- Scope/safety: only tarunsharma2610-del/tradepro-improved; original Tradepro untouched; PAPER mandatory; live writes and automatic live-fill promotion/scheduling disabled; PR #6 draft/unmerged; no personal contract note required; defer AI/Algory until Phase 3 acceptance.


## Authoritative GST decision — 26 October 2026

**Decision: implement the current official Upstox public-schedule GST base for estimates now; do not let the inconsistent API documentation sample block it.** Upstox's pricing page explicitly states GST at 18% on brokerage + transaction charges + IPFT, with demat charges additionally included for equity delivery. From 1-Mar-2026, NSE Circular NSE/FA/73061 defines combined transaction/IPFT outflows (cash ₹307/crore, futures ₹183/crore, options ₹3,553/crore premium); represent that as one exchange_charges component and never add IPFT twice. The supported estimate path sums brokerage + combined exchange_charges, and adds explicit demat_charges for delivery. STT, stamp duty and SEBI are not added to this published GST base.

The Brokerage Details API example showing transaction ₹5.68, IPFT ₹0.17 and GST ₹1.02 is internally inconsistent with that page: 18% × ₹5.68 = ₹1.0224 → ₹1.02; 18% × (₹5.68 + ₹0.17) = ₹1.053 → ₹1.05. Treat this as a documentation-example discrepancy, not evidence that current production billing is wrong. Public schedule takes precedence for estimates; the API example does not override it. Trades Charges API is aggregate and its ipft:null is unknown, not zero.

This resolves the public-schedule estimate rule. It does not certify account-specific invoice totals or per-fill actual GST. Keep actual accounting/promotion evidence-gated until invoice/source evidence or written broker clarification is available. A personal contract note from the user is not required. Official sources: https://upstox.com/brokerage-charges/ ; https://upstox.com/developer/api-documentation/get-brokerage/ ; https://upstox.com/developer/api-documentation/get-trade-charges/ ; https://nsearchives.nseindia.com/content/circulars/FA73061.pdf ; https://cbic-gst.gov.in/sectoral-faq.html


## Latest GST/IPFT implementation checkpoint — 26 October 2026

- Latest implementation + synchronized GST decision commit: b75a97f6cd0043c185375cc253b84a1e6d6bfea1.
- Exact-head Backend CI: PASS, run [#40345937942](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40345937942): 1,012 passed, 1 warning in 62.33s. Broker-write boundary guard, SQLite and PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore/evidence retention passed. Synthetic restore is not proof of real Oracle recovery.
- Public GST estimate rule resolved: 18% on brokerage + combined transaction/IPFT exchange_charges, with explicit demat_charges additionally for equity delivery. Never double-count IPFT; do not add STT, stamp duty or SEBI to this published estimate base. API example mismatch is a documentation-example discrepancy; it does not override the published Upstox schedule.
- Actual account invoice/per-fill GST is still evidence-gated; actual candidate records remain DRAFT. User is not required to supply a personal contract note. This does not block public-schedule estimate implementation.
- Scope/safety unchanged: only tarunsharma2610-del/tradepro-improved; original Tradepro untouched; PAPER mandatory; live broker order writes and automatic live-fill promotion/scheduling disabled; PR #6 remains open/draft/unmerged; AI/Algory deferred until Phase 3 acceptance.


## Cross-broker GST implementation update — 26 October 2026

New official-source comparison confirms the taxable GST component set must not be copied from one broker to another:
- Zerodha states GST on brokerage + SEBI charges + transaction charges: https://zerodha.com/charges/
- Dhan states GST on brokerage + transaction charges + SEBI turnover + IPFT/other tax: https://dhan.co/pricing/
- FYERS states GST on brokerage + exchange transaction + clearing + SEBI turnover + NSE IPFT: https://fyers.in/charges-list
- Upstox publishes brokerage + transaction charges + IPFT, with demat charges additionally for equity delivery: https://upstox.com/brokerage-charges/
- Angel One lists transaction charges and IPFT as separate rows; its published table alone does not settle whether a displayed exchange rate is combined for every effective period: https://www.angelone.in/exchange-transaction-charges
- NSE circular NSE/FA/73061 effective 2026-03-01 specifies total outflow as transaction + IPFT: cash ₹306.99 + ₹0.01 per crore, futures ₹182.99 + ₹0.01, options ₹3,552 + ₹0.01. Never add old IPFT rates on top of a combined total: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf
- CBIC stock-broking FAQ says STT/stamp-duty/other tax recoveries are outside GST value only when Rule 33 pure-agent conditions are met; otherwise section 15/Rule 27 valuation applies: https://cbic-gst.gov.in/sectoral-faq.html

Code now includes a generic public-schedule estimate function for source-backed DRAFT/REVIEWED policies. It preserves broker/scope/date/source provenance, requires an exact component set, uses Decimal and paise rounding, and cannot approve a policy or promote actual accounting. Added tests use differing broker component sets as fixtures only; they are not a production-approved tariff registry. Actual invoice reconciliation, policy review, DP/demat persistence and exact-head CI remain separate gates. PAPER-only; live writes disabled; PR #6 and #7 remain Draft/unmerged; original Tradepro repository remains out of scope.


## Session checkpoint sync — 26 October 2026

- Verified exact-head Backend CI run [#40368554399 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40368554399) on code head `9d3f255480da9a71980a9d3819fbb69a34835753`; Backend pytest job completed successfully.
- GST public-schedule estimate helper and tests are present at this head. This is estimate-only; it does not approve actual accounting or promote estimated amounts as actual charges.
- Statutory direction from CBIC: use CGST Act section 15 and CGST Rules Rule 33/Rule 27 with the CBIC stock-broking FAQ. Pure-agent exclusion is conditional on evidence; do not automatically include/exclude every STT, stamp, transaction, IPFT, SEBI or demat line. IGST Act section 12(12) provides the stock-broking place-of-supply rule; state comparison determines IGST vs CGST+SGST. Sources: https://cbic-gst.gov.in/sectoral-faq.html ; https://cbic-gst.gov.in/valuation-rules.html ; https://cbic-gst.gov.in/central-excise-rules.html
- Next session: implement a standalone statutory GST valuation engine and focused tests (Section 15 inclusion, documented Rule 33 evidence, state-based tax split, Decimal/paise rounding, fail-closed missing facts). That engine is **not yet implemented**, so GST/IPFT acceptance is not complete. IPFT combined/separate representation and DP/demat persistence/reconciliation remain separate gates.
- No personal contract note is available or required to continue implementation. Public sources support research but do not prove actual per-fill accounting acceptance.
- Safety: only `tarunsharma2610-del/tradepro-improved`; PR #6 and #7 remain Draft/unmerged; PAPER-only; live order writes disabled; original `tarunsharma2610-del/Tradepro` out of scope.


## Phase 3 CI synchronization — 26 October 2026 (GST/IPFT resolver)

- Latest verified code head: `13e201661d26b04c9bf75bb7e3aaf567ad1e69c4`; exact-head Backend CI [#40378072884 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40378072884): **1,056 passed, 1 warning**. Broker-write boundary, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill and retained restore evidence passed.
- Added scope/effective-date-selected GST policy resolution for `COMBINED`, `SEPARATE`, and `NOT_APPLICABLE` IPFT representation. It rejects double representation, wrong-exchange reuse, missing/extra components, and unapproved or out-of-window policies. This is estimate-policy plumbing, not actual invoice reconciliation or tariff approval.
- Next Phase 3 gate: persist optional DP/demat charges safely, migrate canonical accounting/persistence and total-charge recomputation, then integrate statutory GST valuation only through reviewed source-backed policy paths. Actual per-fill invoice acceptance remains evidence-gated; no personal contract note is required.
- Safety unchanged: PR #6/#7 Draft and unmerged; PAPER mandatory; live broker order writes and automatic live-fill promotion/scheduling disabled; original `tarunsharma2610-del/Tradepro` untouched and out of scope.


## Phase 3 CI synchronization — 26 October 2026 (DP/demat snapshot gate)

- Latest verified code head: `6a6a3560aff18bb94d34b77640058a17d2a208b8`; exact-head Backend CI [#40381396722 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40381396722): **1,057 passed, 1 warning**. Broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore drill and retained restore evidence passed.
- Optional `demat_transaction_charges` can now be represented as a distinct pending canonical snapshot and allocated into the durable per-fill allocation ledger when source rows are independently reviewed. Migration expands the canonical snapshot vocabulary. It does **not** authorize final accounting: DP/demat reconciliation promotion deliberately fails closed until Execution persistence and total-charge recomputation are implemented.
- Next Phase 3 gate: add dedicated optional Execution DP/demat persistence and a single verified total-charge recomputation path, with migration/idempotency/rollback and delivery-vs-non-delivery tests. Keep actual invoice/per-fill acceptance evidence-gated; no personal contract note is required.
- Safety unchanged: PR #6/#7 Draft and unmerged; PAPER mandatory; live broker order writes and automatic live-fill promotion/scheduling disabled; original `tarunsharma2610-del/Tradepro` untouched and out of scope.

## Verified checkpoint — 27 October 2026 (DP/demat completeness)

- Exact-head Backend CI #40459846143 passed on `9400bc9aa221e2cf3b735e49a8e9a6d351237f02`: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40459846143. Backend tests, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore passed; synthetic restore is not production Oracle acceptance.
- API regression added for invalid DP status through `ExecutionOut`; inconsistent status/amount and ineligible DP manifest cases fail closed. Next: per-fill source mapping, replay/idempotency conflicts, rollback atomicity, and component applicability.
- Actual contract-note and production Oracle backup/restore acceptance remain evidence-gated. Safety: target only `tradepro-improved`; original `Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker writes disabled.


## Phase 3 resume update — 27 October 2026 (GST/IPFT source-policy gate)

- Confirmed documentation checkpoint `14027b5bc4293d2cc1ce5990a4ee23f60077fad5` passed Backend CI [#40462683805 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40462683805), including backend tests, broker-write guard, SQLite/PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore and evidence retention.
- Cross-broker public-source comparison added to `GST_IPFT_ACCEPTANCE_MATRIX.md` and `GST_IPFT_PUBLIC_EVIDENCE_ADDENDUM.md`: CBIC Rule 33 is conditional; Zerodha and Dhan list SEBI in the published GST base; Dhan includes IPFT/other tax; FYERS public pages conflict on SEBI/IPFT GST-base membership; Upstox has a separate published-schedule/API-example discrepancy; Angel One's table does not fully specify base membership. Therefore there is no evidenced universal hard-coded GST component set.
- Next: implement/verify a reviewed, effective-dated policy resolver keyed by broker + exchange + segment/product + source version, with explicit included/excluded component IDs, provenance/reviewer and conflict state. Keep combined/separate transaction/IPFT identity exactly-once; Rule 33 exclusion requires complete evidence; conflicting source or missing jurisdiction facts must remain unresolved. Add focused tests only for gaps not already covered.
- No actual GST candidate is approved by this research. Keep estimate output distinct from actual invoice reconciliation and fail closed where policy/evidence is unresolved. No personal contract note is required; real invoice and production Oracle restore acceptance remain deferred until genuine evidence exists.
- Safety: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled. Exact-head CI must be checked after the latest documentation commits.


## GST policy resolver hardening — 27 October 2026

- Audited existing `backend/app/services/broker_gst_component_policy.py` before changing it. It already provides effective-dated broker/exchange/segment/product selection, source URL/retrieval date/SHA-256 provenance, explicit combined/separate/not-applicable IPFT representation, exact component-set checking and an estimate-only calculation path. Avoid creating a parallel resolver.
- New code commit `eef5eebc1e1abfc37c92b4e50d5c35e9afddcbb4`: policy state `CONFLICT` now exists and any effective conflict for the exact scope/date blocks selection even if an approved policy also matches. This prevents silently preferring one of contradictory public sources.
- New test commit `761637aab1d5f36ed5bfc02ffb66ce8b31ab7820`: regression tests for a conflicting source blocking an approved candidate and for rejecting sub-paise component inputs rather than silently rounding them.
- The policy remains estimate-only. This does not approve any broker component set, does not integrate the statutory Rule 33 engine into actual accounting, and does not reconcile invoice-level GST. No broker policies are promoted to APPROVED by this change.
- Validation status: exact-head CI for these commits is not yet verified. Do not mark this increment green until the branch/PR workflow runs on the exact resulting head and all jobs pass. Next: inspect any CI result, fix failures, then synchronize maintained documents/checkpoint to the latest green head.


## Verified GST resolver hardening CI — 27 October 2026

- Service hardening commit `eef5eebc1e1abfc37c92b4e50d5c35e9afddcbb4` passed Backend CI [#40463452758](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463452758).
- Regression-test commit `761637aab1d5f36ed5bfc02ffb66ce8b31ab7820` passed Backend CI [#40463464076](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463464076). New coverage confirms an effective `CONFLICT` policy blocks selection despite an approved candidate, and sub-paise input is rejected.
- Documentation head `d604be9982dc9c37d3a4985abd89c85635b59106` passed Backend CI [#40463512765](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463512765). A newer checkpoint-only commit is pending its own exact-head CI; do not mark the latest branch head green until that run passes.
- The resolver is still estimate-only. No GST candidate or broker tariff has been promoted to approved actual accounting. PR #6/#7 remain Draft/unmerged, PAPER mandatory, live broker order writes disabled, original Tradepro repository out of scope.


## Confirmed statutory GST precision CI and resume point — 27 October 2026

- The initial code-only run for `58c841cb00f7f0137aece7bcd7c83d5a63ae81f9` failed because an older test still expected silent rounding of `0.025`. This was a test expectation conflict with the new fail-closed behavior, not an unresolved runtime regression in the final increment.
- Regression-test commit `c6e9dfb3e4cae6f93fd51a7f1f1facc86e7b804d` passed Backend CI [#40463868838 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463868838). It replaces the obsolete sub-paise rounding expectation with explicit rejection and a valid paise-precision test.
- Checkpoint commit `74015a285cb844a3735052d88cce9c2a2385e1ce` passed Backend CI [#40463883785 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463883785). This verifies the resulting head including the GST precision change, updated regression test and checkpoint document.
- Intermediate failed run: [#40463856382](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463856382); it was superseded by the successful regression and checkpoint runs above. Do not erase the failure from history; document the correction.
- Current implementation boundaries: statutory GST primitive applies Section 15 default inclusion and conditional Rule 33 pure-agent exclusion only when all modeled evidence flags are true; broker GST policy resolver remains an estimate-only source-specific path. Neither is yet a unified actual per-fill invoice acceptance path. No broker GST policy is approved here for actual accounting.
- Next Phase 3 task: audit the accounting charge reconciliation/promotion boundary and define a single reviewed path that consumes source-backed invoice line identities, statutory valuation evidence and effective-dated broker policy without letting estimates become actual ledger charges. If source provenance, Rule 33 facts, component identity, or GST invoice lines are missing/conflicting, actual accounting must fail closed. Add tests before integration; do not promote estimates or change live-trading safeguards.
- Safety unchanged: work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` is out of scope; PR #6/#7 Draft/unmerged; PAPER mode mandatory; live broker order writes disabled.


## Phase 3 execution note — DP/demat applicability guard — 27 October 2026

A DP/demat manifest is eligible only for mapped equity-delivery SELL fills whose underlying `Instrument.instrument_type` is `EQUITY`. Do not infer equity classification from an order segment string alone. Regression test `test_demat_manifest_rejects_non_equity_instrument_even_if_order_segment_says_delivery` and exact-head Backend CI #40482895888 passed on commit `e62c9518df2edd9c80473b55f3a63a632a30121a`; implementation CI #40482878220 passed on `447e9703f4bcf43dc6392d0d3741caee7709ce95`.

Continue the Phase 3 component-applicability audit without duplicating existing tests. Never promote estimates to actual per-fill charges or bypass canonical source/reviewer checks. After every CI pass, update the checkpoint and relevant maintained docs, then wait for CI on the documentation head. Keep PAPER mandatory, live broker order writes disabled, PR #6/#7 Draft/unmerged, and the original `Tradepro` repository out of scope.


## Annual GST statement reconciliation finding — 27 October 2026

- A user-provided Upstox/RKSV annual global transaction statement for FY 2022–23 is annual aggregate evidence, not an individual contract note. Its visible charge rows do not by themselves establish a unique taxable base for the reported aggregate GST at paise precision.
- Preserve source-row labels exactly; do not relabel an STT rounding row as SEBI fees. Determine the base from underlying invoice/contract-note lines and the historical policy, not by selecting a charge merely to force arithmetic to match.
- The reconciliation helper retains reported-vs-expected variance instead of inferring or rewriting the base. Annual variance may reflect invoice-level rounding/aggregation or a charge omitted from the summarized lines; the annual statement alone cannot distinguish these.
- Do not use annual AGS totals to approve actual per-fill GST or promote canonical allocations. Next evidence gate: an itemized individual contract note or invoice-level breakdown. Keep FY 2022–23 evidence separate from the 2026 public-schedule estimate policy.
- This clarifies evidence scope; it does not change GST/IPFT policy or establish that the broker billed incorrectly. Personal identifiers and account-specific figures are intentionally not copied into this repository note.
- Latest code/test head before documentation sync: `9eb278588b78d2a966cc196c15d7a4d9a6ae8868`; Backend CI [#40505176395 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40505176395). This documentation update requires exact-head CI before it is marked green.
- Safety: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` out of scope; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled.

## Historical contract-note GST handling — 27 October 2026

- Use the five January 2023 Upstox contract-note fixtures in `backend/tests/test_historical_upstox_contract_note_gst.py` as daily aggregate regression evidence.
- Do not apply current IPFT rates retroactively; select policy by trade date. The provided note transcription does not separately disclose IPFT, which is not evidence of a zero amount.
- Keep invoice actuals, aggregate API summaries and current brokerage-calculator estimates semantically separate. Do not convert daily totals to per-fill values without reviewed source-row mapping and allocation evidence.
- New fixture commits: `98f14aef1b3b541c2a6e07beb227b6f3f0471a42`, `547917868d28d3f46f1f549a8daa50d57fc4542d`. Verify exact-head CI before marking this increment green.

## Effective-dated historical IPFT estimate gate — 27 October 2026

- Added `calculate_ipft_estimate_for_scope()` in `backend/app/services/broker_tariff_rules.py`. It requires an approved exact-scope `TariffRule`, NSE/FO/OPTIONS, explicit BUY/SELL, PREMIUM basis and INR_PER_CRORE; generic tariff calculation now fails closed for IPFT. The caller must supply the correct source-defined premium aggregation scope. This helper does not allocate aggregate IPFT to fills or certify booked charges.
- Added date-boundary tests for the official NSE schedule: ₹0.01/crore before 1 April 2023, ₹50/crore for equity options from 1 April 2023 through 28 February 2026, and rollback to ₹0.01/crore effective 1 March 2026. Sources: [NSE/FA/56129 (24 March 2023)](https://nsearchives.nseindia.com/content/circulars/FA56129.pdf) and [NSE/FA/73061 (27 February 2026)](https://nsearchives.nseindia.com/content/circulars/FA73061.pdf).
- These tests validate date selection and guarded estimate arithmetic; they do not activate production tariff records. No production rule is automatically approved by the tests, and actual IPFT remains distinct from the current Upstox calculator estimate and the supplied daily contract-note aggregates.
- The five historical GST invoice fixtures are in `backend/tests/test_historical_upstox_contract_note_gst.py`. The note transcription does not separately identify IPFT; missing is not zero. Exact-head CI for the latest code/test and documentation commits is pending verification.

- After tests pass, synchronize the maintained checkpoint/docs to the exact green head; if CI fails, fix it before saving a green checkpoint. Do not mark a source-backed tariff as approved solely because synthetic date-boundary tests pass.


## Session resume checkpoint — 27 October 2026 (API-first charges decision; supersedes older next-step wording)

- **Resume from this checkpoint only.** Latest verified documentation head before this session sync: `72b03ee5b5c7487bb94815ea8b6fc3aabb6f8352`; exact-head Backend CI [#40553171858 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40553171858). The run completed successfully for backend pytest, broker-write boundary enforcement, SQLite upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL + document-volume restore, and restore-evidence retention. It is newer than the earlier failed CI and supersedes it for the tested commit.
- **User decision:** do not let a tiny GST/IPFT rounding discrepancy (including the discussed ₹0.20 annual aggregate variance / sub-paise arithmetic) block paper trading or the core app. The app does not need to independently recreate every broker billing detail before progressing.
- **Paper-trade approach:** use Upstox Brokerage Details API as an estimate where available; otherwise use the existing GST/brokerage/tax engine as a fallback. A target of roughly 95% practical accuracy is acceptable for paper-trading estimates, provided charges are labelled estimated and used consistently. Historical backtests should disclose that current tariffs may differ from historical tariffs.
- **Actual trades:** broker executes and collects actual charges. Import broker-reported post-trade charges/statements where available. Upstox post-trade Trade Charges API is aggregate evidence and must not be misrepresented as per-fill booked-charge evidence. Keep estimates separate from actuals; preserve reconciliation safeguards for imported records without blocking unrelated app development.
- **Do not reopen GST/IPFT from zero or chase tiny rounding differences as a release blocker.** Retain the existing GST engine, tariff/source evidence, API field-path resolver, reconciliation service and tests. Revisit only a concrete integration defect, material systematic variance, or a scope needing evidence.
- **Actual next technical work:** (1) inspect and wire the GST API-vs-engine comparison into the real charge-data flow using the correct charge lines and supplier/place-of-supply inputs; (2) finish genuinely uncovered component-by-component per-fill accounting acceptance—fill identity, paise totals, source-to-canonical mapping, replay/idempotency, rollback and segment/product applicability; (3) keep unsupported BSE/MCX tariff scopes explicitly estimated/unverified until source-backed; (4) synchronize maintained docs and run exact-head CI.
- **Evidence correction:** user has supplied genuine Upstox/RKSV contract-note evidence for 23, 24, 25, 27 and 30 January 2023. Do not state that no personal contract note exists or ask the user to provide it again. Production Oracle backup/restore acceptance remains deferred until deployment backups exist.
- **Safety invariants:** work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` is out of scope. PR #6 and PR #7 remain Draft/unmerged. PAPER mode mandatory; live broker order writes remain disabled. Do not merge.
- **First action next session:** verify the latest head and its CI, read this checkpoint's latest section, then continue from the caller-level API/GST integration and remaining accounting acceptance. Do not resume from the earlier failed CI or repeat already completed GST/IPFT research.


## API-first paper-trade charge estimation decision — 29 October 2026

- User-approved behavior: use Upstox's pre-trade Brokerage Details API for paper-fill charge estimates when it returns a complete, valid, internally consistent breakdown. Keep the existing deterministic local calculator as the automatic fallback if the API is unavailable, expired/unauthorized, incomplete, null/invalid, or inconsistent. This is estimation only, not live-trading/accounting promotion.
- Implementation added on the Phase 3 branch: `backend/app/services/paper_trade_charge_estimator.py` plus deterministic tests. `ExecutionService` now uses API-first estimates for market and matched limit paper fills and records `PAPER_UPSTOX_API_ESTIMATE` versus `PAPER_ESTIMATE` in the existing execution charge-source field. Components are accepted only when paise-exact supported components sum exactly to the API total; transaction, clearing and IPFT are combined once in the existing exchange-charge field. Unknown/incomplete fields fall back rather than block paper trading.
- Existing post-trade Upstox charges endpoint remains aggregate reconciliation evidence, not per-fill actuals. The API route already exists. GST reconciliation remains available without blocking paper-trade P&L.
- Implementation commits: `b90c09dc82a51181bc9eae422cb025eb79c65bcb`; default-enabled setting `UPSTOX_CHARGE_ESTIMATES_ENABLED`. CI disables network estimates only for the broad execution suite; mocked estimator tests cover API and fallback paths.
- Backend CI [#40755234415](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40755234415) — **SUCCESS** on code/test head `778e76d3554a3baedc41f0396276c1cb3dafc38f`: **1,197 passed, 1 warning**; broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic restore/evidence retention passed. Documentation sync head `d57dd476ecd6acebd4dc9e169912b877811a8166` still needs exact-head CI verification before it is called green.
- Next: continue the next uncovered Phase 3 accounting acceptance gate after CI recovery. Do not reopen GST/IPFT from zero or make minor estimate variance a paper-trading blocker. Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled; original `Tradepro` out of scope.


## Authoritative Phase 3 engineering closure — 29 October 2026

This section supersedes older status/next-step notes above; earlier entries remain as historical audit trail.

**Status: Phase 3 engineering acceptance is complete for the agreed PAPER-mode scope.** This is not authorization to enable live broker writes, promote estimates to booked actuals, or merge Draft PRs.

**Verified exact code/checkpoint head before this documentation closure:** `3a0c464afcb10261d1590607f8440affd21295a0`, Backend CI [#40878367369 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40878367369). Backend pytest: **1,207 passed, 1 warning**. Broker-write boundary, SQLite upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and retained restore evidence all passed.

### Phase 3 engineering exit criteria completed

- Deterministic paise-exact per-fill charge allocation, source-document integrity and reviewer controls, canonical source-to-component mapping, and explicit combined/split transaction-charge/IPFT representation.
- Replay/idempotency and conflicting-replay rejection; component totals revalidated under locks; rollback safeguards protect accounting/position mutations.
- Optional DP/demat persistence and total-charge completeness are explicit. Delivery SELL cannot be treated as complete when DP evidence is missing, unknown, invalid, or inconsistent.
- GST valuation and GST/API comparison primitives are implemented with Decimal/paise validation, state/place-of-supply handling, missing/null/zero distinctions, and review-required variance states. Estimates/comparisons never silently approve actual accounting.
- Upstox Brokerage Details API is the preferred PAPER estimate. Invalid/unavailable API results use the deterministic hardcoded calculator. The source label is preserved as `PAPER_UPSTOX_API_ESTIMATE` or `PAPER_HARDCODED_FALLBACK`; both expose: “Estimated charges may differ from actual broker charges. For paper trading only; these are not actual booked charges.”
- Upstox post-trade Trade Charges API remains aggregate reconciliation evidence and is explicitly prohibited from per-fill actual promotion. Aggregate responses are sanitized before persistence/return.
- CI on the verified code head passed the complete backend and safety/migration/restore workflow.

### Explicit non-blocking operational/release gates

These are not reasons to keep Phase 3 engineering open, but remain mandatory before any live-money release or claim of production acceptance:

1. Run a user-authorized, credentialed Upstox OAuth/API smoke test in the deployed environment; CI does not prove account-specific entitlements or token validity.
2. Run and retain a real Oracle/database-plus-document-volume backup/restore drill after deployment; synthetic restore is not production backup acceptance.
3. Keep any broker/exchange/segment/product/date tariff without independently approved source evidence in estimate-only/fail-closed status for actual accounting. This does not block PAPER trading.
4. Real contract-note data remains the source for actual booked charges. Historical contract-note fixtures are regression evidence; API estimates and aggregate summaries must never be represented as per-fill booked actuals.
5. The GST/API comparison remains diagnostic, not automatic invoice approval. No GST/IPFT variance silently rewrites a charge or blocks ordinary PAPER simulation.

**Safety invariants unchanged:** only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` untouched; PR #6/#7 remain Draft and unmerged; PAPER mode mandatory; live broker order writes disabled.

**Next project phase:** proceed to Phase 4 as a separate increment after this documentation-head CI passes. Keep Upstox developer integration and UI work in their planned later order; do not mix them into Phase 3 or merge the Draft PRs without explicit authorization.

## Final documentation-head CI verification — 29 October 2026

The documentation sync head `5bb6d06e764c00b1ab406409889a2cde9e74dacf` passed Backend CI #40880169125 — SUCCESS: 1,207 passed, 1 warning; broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic restore drill, and evidence retention all passed.


## Resume checkpoint — 29 October 2026 (Upstox response-schema validation)

- **Code/test head:** `404c1e11ef4f2557c791c720c8d9a3fbc4e93bc1`; exact-head Backend CI [#40883660756 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40883660756). The workflow result confirms success; its summary did not expose a reliable pytest count, so no count is asserted here.
- **Concrete fix:** `UpstoxChargeApiOrchestrationService` no longer marks arbitrary successful HTTP JSON as usable. Brokerage estimates require `status == "success"` and `data.charges`; post-trade aggregate charges require `status == "success"` and `data.charges_breakdown`. Wrong/missing schema returns `usable=false`, clears the payload and records `INVALID_RESPONSE_SCHEMA`.
- **Regression coverage:** valid endpoint-specific response fixtures plus incorrect endpoint schema, unsuccessful/missing status, and aggregate wrong-shape payload cases.
- **Evidence boundary:** Brokerage Details remains estimate-only; Trade Charges remains aggregate reconciliation-only and never per-fill actual evidence. Null IPFT must not be silently coerced to zero. This fix validates response shape; it does not approve tariffs or promote accounting.
- **Contract-note continuity:** previously supplied January 2023 Upstox/RKSV contract-note examples remain available as historical regression fixtures; do not ask the user to provide them again. Their scope must be respected when using them for GST totals versus per-fill allocations.
- **Next:** verify CI on the exact synchronized documentation head. Keep PR #6/#7 Draft and unmerged, PAPER mode mandatory, live broker writes disabled, and the original `tarunsharma2610-del/Tradepro` repository untouched.

## Standing engineering rule — official Upstox capabilities first (30 October 2026)

**Work smarter: audit and use the Upstox Developer Console, official current API documentation, supported APIs, SDKs, and supplied schemas/proto whenever they materially solve the problem.** Before adding custom polling, parsing, retries, stale-data patches, compatibility shims, or duplicate infrastructure:
1. Check the current official Upstox API/SDK contract and deprecation notices.
2. Audit Tradepro Improved's existing integration and reusable services first.
3. Prefer the supported API/SDK and existing shared integration over a bespoke workaround.
4. Implement the smallest correct end-to-end integration; use proportionate validation and fail-closed handling as defense in depth.
5. Verify against official response examples/schema and deterministic tests. Use authorized Developer Console/account checks only when access is available; never claim live verification without performing it.
6. Explain why a supported API/SDK cannot solve the issue before choosing a workaround.

For market data, assess Upstox Market Data Feed V3 (protobuf/WebSocket), V3 intraday and historical candle endpoints, token/authorization lifecycle, and official Python SDK (upstox-python-sdk) where appropriate. Connect existing streaming and REST layers to strategy/candle processing rather than treating a local freshness threshold as the primary solution. Preserve candle semantics, instrument identity, timestamps, gap recovery, and reconnect behavior. Freshness checks remain safety nets, not substitutes for correct API integration.

Do not add work merely to appear busy. Identify the actual gap, use provider-supported capabilities when available, reuse existing code, test the full path, and document genuine limitations. Safeguards remain: only tarunsharma2610-del/tradepro-improved; PAPER-only; live broker writes disabled; no main update or PR merge without explicit authorization.

## Upstox token-scope rule — 30 October 2026

Use the official Upstox Analytics Token for supported market-data and real-time streaming endpoints where the current Developer documentation specifies it; use the standard OAuth access token only for endpoints requiring account/portfolio/trading permissions. Store token types separately, encrypted, masked in responses, and never silently substitute one for the other. Standard access tokens expire at 3:30 AM IST the following day; do not invent an unsupported refresh-token flow. Before implementation, audit all token call sites and confirm each endpoint's documented authorization scope.
 
## Upstox Analytics Token implementation — 30 October 2026

- Added separate encrypted `analytics_token_encrypted` and `analytics_token_expires_at` fields to per-user broker connections with migration `202610300031` (down revision `202610270030`).
- Added owner-scoped Settings API to save, inspect status and clear Analytics Token. Token is accepted from the user's Upstox Developer Apps > Analytics page; it is never returned, logged or included in API responses. Expiry is tracked as 365 days from local registration; confirm/renew against the Developer Console's actual expiry date.
- Analytics Token retrieval is independent of standard OAuth `is_connected` state and fails closed when missing/expired. Standard OAuth access-token path remains separate for operations not documented as Analytics Token eligible.
- Routed strategy historical/intraday candle fetch, paper market quote/charge estimation, queued paper limit-order quotes, and market WebSocket reconnects through Analytics Token. Broker order/trade ingestion continues to use standard OAuth until each endpoint's Analytics Token/static-IP eligibility is deliberately enabled.
- Analytics Token is read-only. It cannot place, modify or cancel orders. Live trading remains disabled; PAPER-only guard unchanged.
- Official docs: https://upstox.com/developer/api-documentation/analytics-token/ ; https://upstox.com/developer/api-documentation/announcements/analytics-token-static-ip/ ; https://upstox.com/developer/api-documentation/v3/get-market-data-feed/
- CI for this new implementation is pending. Do not mark it accepted until exact-head CI passes, including migration round-trip and token isolation tests.

## Verified Analytics Token checkpoint — 30 October 2026

- Implementation head `083ab17a5150ea3be514438a16ea7c6c888c0be3` passed Backend CI #41017833952: 1,243 passed, 1 warning. Broker-write boundary, SQLite/PostgreSQL 16 migration round-trips and synthetic restore drill all passed.
- Analytics Token is stored separately encrypted, owner-scoped, expiry-checked and never returned in API output/logs. It is used only for documented read-only market-data/streaming/charge-estimate routes. Standard OAuth remains separate for account endpoints not enabled for Analytics Token or requiring static IP.
- Real token entry and live API smoke test remain a deployment/user setup gate; code CI is not proof of a real broker session.
- PAPER-only and live order-write safeguards unchanged; PR #8 remains Draft/unmerged; do not update main or the original Tradepro repository.


## Upstox option-chain + mode-correct streaming increment — 30 October 2026

- Exact preceding docs head `c00278fb33cc094a0f07d6a61d3ca9827f2dcdcf` passed Backend tests #41018852112 and #41018839615. These runs verify the preceding full-feed/doc checkpoint only, not the new code below.
- Added optional broker-adapter `get_option_chain` capability and Upstox implementation for the documented `GET /v2/option/chain` endpoint. The authenticated API route `GET /api/v1/market-data/option-chain` uses the separately stored Analytics Token only, validates exact ISO expiry or supported relative expiry keywords, and rejects MCX because Upstox documents that exchange as unsupported for this endpoint.
- Upstox's response supplies strike-wise call/put market data, OI, previous OI, volume, bid/ask and Greeks. The application adds `change_oi = oi - prev_oi` only when both source values are present and finite; otherwise the derived field is `null`. Original provider fields are retained and no missing/null value is converted to zero.
- Fixed a scope bug found during audit: the stream manager already retrieves Analytics Token, but the HTTP start route was still gating on daily OAuth. Stream start now correctly requires a valid Analytics Token; it does not require daily OAuth for public market-data streaming. The route reports the actual selected feed mode.
- Added explicit stream mode selection: `ltpc`, `option_greeks`, or `full`, defaulting to `full`. Mode-specific limits are validated before starting: LTPC 5,000; Option Greeks 3,000; Full 2,000. The user-scoped manager runs one stream per user, below Upstox's normal two-connection ceiling. No Plus-only Full D30 assumption.
- Option Greeks mode decodes the documented first-level bid/ask depth, Greeks and IV. Full mode retains D5 depth, OHLC and extended metadata parsing. Regression tests cover adapter endpoint/query/auth, provider errors, option-chain route, MCX rejection, expiry validation, OI delta semantics, Analytics Token-only stream authorization, selected modes and mode-specific limits.
- Code/test head: `42be7ad2a33c2e7a6db08842a5ec9c7c30154af5`. Exact-head CI for this increment is pending; do not claim green until the exact current PR head has passed backend tests and all safety/migration checks.
- Official contracts: https://upstox.com/developer/api-documentation/analytics-token/ ; https://upstox.com/developer/api-documentation/get-pc-option-chain/ ; https://upstox.com/developer/api-documentation/v3/get-market-data-feed/ ; official V3 proto: https://assets.upstox.com/feed/market-data-feed/v3/MarketDataFeed.proto . Analytics Token supports Option Chain and WebSocket without static IP; MCX Option Chain is not available.
- Next after exact-head CI: add/verify index + India VIX feed presets and subscription lifecycle management (subscribe/change_mode/unsubscribe) with per-user limits; then test WebSocket recovery and option-chain snapshot/stream consistency. Do not create a duplicate market-data service or Redis bridge without a proven process-boundary need.
- Safety: only `tarunsharma2610-del/tradepro-improved`; PR #8 remains Draft/unmerged; main and original Tradepro untouched; PAPER mode mandatory; live broker order writes disabled.


## Upstox V3 subscription lifecycle — 30 October 2026

- Verified the official V3 WebSocket contract directly: methods are `sub`, `unsub`, and `change_mode`; requests must be sent as binary protobuf-feed protocol frames containing JSON bytes. The V3 docs specify normal per-category individual limits of LTPC 5,000, Option Greeks 3,000 and Full 2,000; when categories are mixed, the combined limits are 2,000 for LTPC/Greeks and 1,500 for Full. This implementation deliberately uses one mode per user stream, so it enforces the corresponding individual limit and does not claim mixed-mode capacity.
- Added native live subscription management to the existing streamer: add instrument keys with `sub`, remove keys with `unsub`, and change the mode of the complete user stream with `change_mode`. It preserves the desired subscription set across reconnects and sends the current complete subscription/mode on the next connection.
- Mode changes invalidate cached ticks so depth/Greeks from a previous feed mode cannot be consumed as if they came from the newly selected mode. Unsubscribed ticks are removed. The final key cannot be removed via partial unsubscribe; use DELETE `/market-data/stream` to stop the stream.
- Added authenticated API endpoints: POST `/api/v1/market-data/stream/subscribe`, POST `/api/v1/market-data/stream/unsubscribe`, and POST `/api/v1/market-data/stream/change-mode`. Each is user-scoped, checks the Analytics Token, verifies active instrument keys before subscribing, and rejects requests when there is no running stream. Partial mixed-mode changes are intentionally rejected; change mode applies to all keys in the stream to keep one consistent parser/mode contract.
- Added tests for binary V3 control requests, dynamic subscribe/unsubscribe/change_mode, reconnect replay of updated desired state, per-mode limits, stale tick invalidation, active-instrument validation, and missing-stream conflict responses.
- Exact previous code/test head `e53ac0f9a24bf3a92a409fa548d59b41206a5042` passed Backend CI #41019403337. Current subscription-lifecycle head: `7aecd1e5b9a77a44fe3b0885a89a88e4826c2d33`; exact-head Backend CI #41019804917 is queued, and prior incremental runs are queued/running. Do not mark this lifecycle increment green until the latest exact head passes all backend, broker-write, SQLite/PostgreSQL migration and synthetic restore checks.
- Official source: https://upstox.com/developer/api-documentation/v3/get-market-data-feed/ (method semantics, binary request format, India VIX key, and individual/combined limits).
- Next after exact-head CI: add verified index/India VIX presets based on instrument-master keys, then reconnect/subscribe race tests and end-to-end quote fan-out to the scanner/strategy data path. No second stream service, Redis bridge, or live-order capability is being added without a demonstrated requirement.
- Safety: only `tarunsharma2610-del/tradepro-improved`; PR #8 remains Draft/unmerged; main and original Tradepro untouched; PAPER mode mandatory; live broker order writes disabled.


## Verified checkpoint — 30 October 2026 (subscription lifecycle CI green)

- Exact implementation commit `b87245002a24bb0bd002b7e0c7dc5bbc82085357` passed complete Backend CI run #41020300281: backend pytest, broker-write boundary, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration upgrade/downgrade/re-upgrade, synthetic PostgreSQL + document-volume restore drill, and restore evidence retention. Run: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41020300281
- The lifecycle-test correction now tests partial mode-change rejection with two subscribed instruments, so the test exercises the actual partial-subscription case instead of incorrectly treating a single-instrument complete-stream mode change as partial.
- Subscription lifecycle implementation includes authenticated user-scoped subscribe/unsubscribe/change-mode routes, active-instrument validation before subscribe, per-mode subscription limits, reconnect replay, and invalidation of cached ticks after mode changes. No live broker order capability was introduced.
- This is the accepted code/test checkpoint. Documentation synchronization is being committed separately; the exact documentation head must receive its own CI verification before the next code increment.
- Next implementation: index feed presets backed by dynamically resolved and locally validated Upstox instrument keys (Nifty 50, Nifty Bank, India VIX). Do not hardcode exchange tokens. Use the official Instrument Search API and Upstox developer documentation; preserve provider identifiers and source timestamps. Then implement freshness/recovery observability and scanner/strategy fan-out.
- Official references: https://upstox.com/developer/api-documentation/instrument-search/ ; https://upstox.com/developer/api-documentation/v3/get-market-data-feed/ ; India VIX key documented as `NSE_INDEX|India VIX`.
- Safety: work only in `tarunsharma2610-del/tradepro-improved`; PR #8 remains Draft/unmerged; do not change main or original `Tradepro`; PAPER mode mandatory; all live broker order writes remain disabled. No credentials or tokens in code, logs, docs or chat.


## Verified checkpoint — 30 October 2026 (rich market-data snapshot CI green)

- Exact implementation/test commit `036ad952ced862e94b2c4d3af75b79b43a0bbc28` passed full Backend CI run #41022649412: backend pytest, broker-write boundary, SQLite Alembic upgrade/downgrade/re-upgrade, PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade, isolated synthetic PostgreSQL + document-volume restore, and evidence retention. Run: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41022649412
- Corrected the missing-quote stream-status test to apply the normal authenticated-user dependency overrides. Production authentication remains required; the assertion that an absent latest quote is represented as unavailable remains in place.
- The stream status response now exposes the validated fresh tick snapshot fields needed by downstream read-only consumers: instrument key, LTP, exchange timestamp, receive time, depth, option Greeks, OI, traded volume, average traded price, total buy/sell quantities and OHLC. Missing quotes remain null; do not infer freshness from a missing tick.
- Index presets are implemented from the locally synchronized official Upstox instrument master and fail closed for missing/ambiguous matches. Do not hardcode dynamic exchange instrument identifiers.
- Architecture note: the existing WebSocket stream manager is process-local. A worker in a separate process cannot read its in-memory cache. Before scanner/strategy consumers depend on streamed ticks, implement and test a shared cross-process delivery layer using the Redis already present in deployment (or another justified existing shared store). Redis Pub/Sub alone is not durable: pair notification with a TTL-bounded latest-quote cache/snapshot, explicit timestamps, freshness checks, and reconnect/recovery semantics. On Redis loss or stale/missing quote, consumers must fail closed and retain existing candle freshness and PAPER/risk gates.
- Next work: audit current Redis configuration and Redis Python package APIs; define a small versioned quote envelope and namespaced user/instrument keys; implement publisher + cache write in the existing stream lifecycle; implement worker/API consumer with TTL and timestamp validation; test outage, reconnect, expiry, ownership isolation and process restart; only then connect scanner and paper strategy consumers.
- This checkpoint does not certify Redis fan-out, scanner integration or strategy integration as complete. No live broker order capability was introduced.
- Safety: work only in `tarunsharma2610-del/tradepro-improved`; PR #8 remains Draft/unmerged; main and original `Tradepro` untouched; PAPER mode mandatory; live broker order submission/modification/cancellation disabled; no credentials in code, logs, docs or chat.


## Phase 4 continuation instruction — Redis publisher checkpoint (30 October 2026)

Resume from exact verified code head `72b22a647f2b9a38ac7afc0aaee9547a67b16fcf`, Backend CI #41024607462 SUCCESS. Do not restart or repeat publisher work. Publisher and Upstox stream callback wiring are complete; Redis consumer, reconnect recovery, cross-process tests, scanner and PAPER strategy integration are not. First verify the latest docs-sync commit and exact-head CI. Then implement consumer using Redis snapshot as source of truth and Pub/Sub only as notification. Validate tenant/user scope, schema version, monotonic version, TTL and exchange timestamp; recover after missed notifications/restarts by reading latest snapshot. Fail closed on unavailable/stale data. Work only in `tarunsharma2610-del/tradepro-improved`; no main update/merge; PR #8/#9 Draft; PAPER mandatory; live broker writes disabled; original Tradepro out of scope.


## Phase 4 continuation rules — Redis checkpoint (30 October 2026)

- Continue only in `tarunsharma2610-del/tradepro-improved`; never modify original `tarunsharma2610-del/Tradepro`.
- Latest verified Phase 4 code head: `1c70e17a0ea54f8e8f219ae27d90aa46a02ea16e`; Backend CI #41026567279 passed on exact head. Treat subsequent commits as unverified until their own CI completes.
- Redis quote publisher uses atomic Lua for version increment, authoritative snapshot/expiry, and Pub/Sub notification. Consumers must always fetch/validate the snapshot.
- Next gates: reconnect/resubscribe and recovery after Redis outage; actual Redis server restart test; independent process test; scanner integration; PAPER strategy integration. Do not skip gates or claim integration prematurely.
- PAPER mode mandatory. Live `place_order`, `modify_order`, and `cancel_order` writes remain disabled. Do not merge PR #8/#9 or update main without explicit authorization. Preserve Phase 3 accounting safeguards and all fail-closed freshness/risk controls.
- Use official Upstox Developer Console, API docs, SDKs and supplied protobuf schemas when appropriate; audit existing capabilities before adding duplicate services or workaround layers.


## Phase 4 continuation checkpoint — 30 October 2026

- Latest verified code head: `3088e49cf24317f58f7e04a60d6cd54e065143b4`; exact-head Backend pytest CI #41031153316 passed.
- Redis quote snapshots retain TTL; per-instrument version counters no longer expire, preventing version regression after ordinary snapshot expiry. Real Redis integration coverage was added.
- Do not interpret this as proof of independent OS-process delivery or complete production readiness. Next audit startup/reconnect authoritative snapshot sweep, consumer/worker lifecycle and shutdown; add independent-process and multi-user/multi-instrument tests.
- Persistent version keys need an explicit retention/cleanup policy; do not add counter TTL back without epoch-safe version semantics.
- Only modify `tarunsharma2610-del/tradepro-improved`; never original `tarunsharma2610-del/Tradepro`. PR #9 remains Draft/unmerged; do not update main or merge without explicit authorization. PAPER mandatory; live `place_order`, `modify_order`, and `cancel_order` writes disabled. Preserve Phase 3 accounting safeguards and fail-closed freshness/risk controls.
- Prefer official Upstox Developer Console, API docs, SDKs and protobuf contracts when relevant; audit existing support before adding duplicate services.


## Phase 4 continuation checkpoint — 30 October 2026

- Latest verified code head: `7268edd6e7ddb7ef6d472799d1d0164b4210b135`; exact-head full Backend CI #41032764754 passed, including pytest, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips and synthetic restore/evidence retention.
- Redis quote snapshots use short TTL; version counters use bounded 24-hour default retention and a unique epoch. Atomic Lua allocates epoch/version, stores snapshot and publishes notification. Legacy integer counters migrate on next publish.
- Consumer compares epoch plus version; counter expiry or Redis data loss starts a new epoch, so a new version 1 is not mistaken for a regression.
- Real Redis tests passed for snapshot TTL expiry, counter TTL expiry/new epoch, Pub/Sub disconnect recovery, Redis process restart, independent OS-process delivery, two-user isolation and concurrent publishing.
- Important: consumer service is tested but not yet managed by `app/worker.py`; strategy execution remains candle-based. Scanner and PAPER strategy Redis consumption are not complete. Next implement durable user/instrument subscription discovery and a managed worker consumer lifecycle, then scanner, then PAPER strategy.
- Multi-user/multi-instrument sustained-load testing remains pending. Do not claim production-scale readiness.
- Only modify `tarunsharma2610-del/tradepro-improved`; never original `tarunsharma2610-del/Tradepro`. PR #9 remains Draft/unmerged; do not update main or merge without explicit authorization. PAPER mandatory; live `place_order`, `modify_order`, and `cancel_order` writes disabled. Preserve Phase 3 accounting safeguards and fail-closed freshness/risk controls.
- Prefer official Upstox Developer Console, API docs, SDKs and protobuf contracts when relevant; audit existing support before adding duplicate services.



## Official SDK/API reuse rule — reinforced 30 October 2026

Before implementing or extending any broker integration, inspect current official Developer Console capabilities, API docs, SDK package/release notes, protobuf schemas, examples and known issues/forums. Compare each capability against the current repo implementation before writing code. Reuse an official component only when it materially improves correctness, coverage or maintainability; do not add dependencies ceremonially. Keep our domain adapter, async lifecycle, validation, tenant isolation, Redis delivery, freshness and risk/accounting controls when they are stronger. Record the comparison and explicit adopt/retain decision in a maintained audit note. The Upstox v2.30.0 audit is in UPSTOX_SDK_COMPATIBILITY_AUDIT.md.


## SDK capability comparison rule — mixed modes

Do not stop an SDK audit at feature-name parity. Compare actual source behaviour and lifecycle. The Upstox SDK v2.30.0 uses per-mode subscription sets and replays them on reconnect; our current single-mode stream is a gap. Borrow this design into our own async implementation after the pending CAS CI passes. Future audits should compare mode combinations, limits, reconnect semantics, token refresh, and error handling—not just method names.


## Phase 4 latest checkpoint — 30 October 2026

- Exact implementation SHA `6ac3882a98f3c66abb4cd62848971b6277ab3be7` passed Backend CI #41080156436: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41080156436.
- Transactional PAPER stop-event claim service validates user/portfolio/strategy/instrument ownership, locks portfolio → strategy → position, rejects flat positions and ambiguous shared-position ownership, and persists unique quote identity with claim token/lease/attempt metadata. Duplicate claims are safely rejected through a savepoint.
- This service is storage/claim coordination only; it is not connected to the dispatcher or order execution.
- Next: PostgreSQL 16 multi-worker race tests, lease reclaim/state transitions, crash recovery, shared-position ownership policy, then gated PAPER integration.
- PR #9 remains Draft/unmerged; PAPER mandatory; live broker writes disabled; original Tradepro repository out of scope. Documentation commits require exact-head CI.


## Phase 4 checkpoint — 30 October 2026

The exact implementation SHA `0d3700f0a12add3239457bc4009eb019d77c78a0` passed [Backend CI #41090051358](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41090051358). Coverage includes PostgreSQL 16 concurrent PAPER stop-event claims (same-identity duplicate suppression and distinct quote versions), broker-write boundary enforcement, SQLite and isolated PostgreSQL migration round trips, and synthetic restore. The migration database is separate from the concurrency test database. Follow-up: implement claim-token-guarded state transitions and lease expiry/reclamation tests before dispatcher-to-PAPER integration. Preserve scope: only `tarunsharma2610-del/tradepro-improved`; PR #9 Draft/unmerged; PAPER mandatory; live broker writes disabled; no deployment.
