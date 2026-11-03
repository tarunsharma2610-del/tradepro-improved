"""PAPER operational alerting for worker-fleet dispatch health.

Alerts are aggregate-only and best-effort: they never participate in order
execution or accounting. Telegram delivery is opt-in and uses an admin-only,
encrypted platform setting for the destination chat ID.
"""
import asyncio
import logging
import re
import time
from collections.abc import Callable
from typing import Any

from app.core.database import SessionLocal
from app.services import telegram_notifier
from app.services.market_data_metrics import fleet_snapshot
from app.services.platform_settings_service import PlatformSettingsService

logger = logging.getLogger("trading_platform.operational_alerts")

ALERT_COOLDOWN_SECONDS = 300
NO_WORKER_ALERT_SECONDS = 60
METRIC_FAILURE_ALERT_THRESHOLD = 5
REJECTED_ALERT_THRESHOLD = 25

_DEDUPE_PREFIX = "tradepro:ops-alert:v1:"


def evaluate_dispatch_alerts(
    snapshot: dict[str, Any],
    previous_counters: dict[str, int] | None,
) -> list[tuple[str, str]]:
    """Return stable fingerprint/message pairs; never include user/instrument IDs."""
    counters = snapshot.get("counters") or {}
    if previous_counters is None:
        return []

    alerts: list[tuple[str, str]] = []
    dropped = max(0, int(counters.get("market_quote_dispatch_dropped_unique_total", 0)) -
                  int(previous_counters.get("market_quote_dispatch_dropped_unique_total", 0)))
    exhausted = max(0, int(counters.get("market_quote_dispatch_exhausted_total", 0)) -
                    int(previous_counters.get("market_quote_dispatch_exhausted_total", 0)))
    failures = max(0, int(counters.get("market_quote_dispatch_handler_failures_total", 0)) -
                   int(previous_counters.get("market_quote_dispatch_handler_failures_total", 0)))
    rejected = max(0, int(counters.get("market_quote_dispatch_rejected_total", 0)) -
                   int(previous_counters.get("market_quote_dispatch_rejected_total", 0)))

    if dropped:
        alerts.append(("dispatch_dropped", f"PAPER market-data dispatcher dropped {dropped} unique observation(s). Check queue capacity and worker throughput."))
    if exhausted:
        alerts.append(("dispatch_exhausted", f"PAPER market-data dispatch exhausted retries for {exhausted} observation(s). Check worker logs and stop-event recovery."))
    if failures >= METRIC_FAILURE_ALERT_THRESHOLD:
        alerts.append(("dispatch_handler_failures", f"PAPER market-data handlers recorded {failures} failures in the latest monitoring interval."))
    if rejected >= REJECTED_ALERT_THRESHOLD:
        alerts.append(("dispatch_rejections", f"PAPER market-data dispatcher rejected {rejected} observations in the latest monitoring interval."))
    return alerts


class OperationalAlertMonitor:
    """Poll fleet metrics and deliver deduplicated aggregate alerts to Telegram."""

    def __init__(
        self,
        redis_client,
        *,
        interval_seconds: float = 30,
        cooldown_seconds: int = ALERT_COOLDOWN_SECONDS,
        no_worker_seconds: int = NO_WORKER_ALERT_SECONDS,
        session_factory: Callable = SessionLocal,
        metrics_reader: Callable = fleet_snapshot,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        if interval_seconds <= 0 or cooldown_seconds < 1 or no_worker_seconds < 1:
            raise ValueError("Operational alert intervals must be positive.")
        self.redis = redis_client
        self.interval_seconds = interval_seconds
        self.cooldown_seconds = cooldown_seconds
        self.no_worker_seconds = no_worker_seconds
        self.session_factory = session_factory
        self.metrics_reader = metrics_reader
        self.monotonic = monotonic
        self._previous_counters: dict[str, int] | None = None
        self._zero_workers_since: float | None = None
        self._local_sent_at: dict[str, float] = {}
        self._metrics_unavailable = False

    async def _send(self, fingerprint: str, message: str) -> bool:
        dedupe_key = f"{_DEDUPE_PREFIX}{fingerprint}"
        try:
            claimed = bool(await self.redis.set(
                dedupe_key, "1", nx=True, ex=self.cooldown_seconds
            ))
            if not claimed:
                return False
        except Exception:
            # Redis may itself be the failing dependency. Fall back to a
            # process-local cooldown so an outage does not cause log spam.
            now = self.monotonic()
            if now - self._local_sent_at.get(fingerprint, float("-inf")) < self.cooldown_seconds:
                return False
            self._local_sent_at[fingerprint] = now

        db = self.session_factory()
        try:
            settings = PlatformSettingsService(db)
            token = settings.get_decrypted("telegram_bot_token")
            chat_id_raw = settings.get_decrypted("ops_alert_telegram_chat_id")
            if not token or not chat_id_raw or not re.fullmatch(r"-?\d{1,20}", chat_id_raw.strip()):
                logger.warning("PAPER operational alert not delivered: Telegram operations destination is not configured.")
                return False
            result = await telegram_notifier.send_message(
                token, int(chat_id_raw), f"Tradepro PAPER operational alert\n{message}"
            )
            if not result.ok:
                logger.error("PAPER operational alert delivery failed: Telegram request was rejected or unavailable.")
                try:
                    await self.redis.delete(dedupe_key)
                except Exception:
                    pass
                return False
            logger.warning("PAPER operational alert delivered: %s", fingerprint)
            return True
        except Exception:
            logger.exception("PAPER operational alert delivery failed.")
            try:
                await self.redis.delete(dedupe_key)
            except Exception:
                pass
            return False
        finally:
            db.close()

    async def run_once(self) -> None:
        try:
            snapshot = await self.metrics_reader(self.redis)
            self._metrics_unavailable = False
        except Exception:
            if not self._metrics_unavailable:
                await self._send(
                    "metrics_unavailable",
                    "Shared Redis market-data metrics are unavailable. Check Redis connectivity and worker health.",
                )
            self._metrics_unavailable = True
            return

        counters = {
            str(key): int(value)
            for key, value in (snapshot.get("counters") or {}).items()
        }
        now = self.monotonic()
        worker_count = int(snapshot.get("worker_count", 0))
        if worker_count <= 0:
            if self._zero_workers_since is None:
                self._zero_workers_since = now
            elif now - self._zero_workers_since >= self.no_worker_seconds:
                await self._send(
                    "no_active_workers",
                    "No active PAPER market-data metrics workers have reported a heartbeat for at least one minute.",
                )
        else:
            if self._zero_workers_since is not None:
                await self._send(
                    "workers_recovered",
                    f"PAPER market-data worker heartbeat recovered; active worker count is {worker_count}.",
                )
            self._zero_workers_since = None

        for fingerprint, message in evaluate_dispatch_alerts(snapshot, self._previous_counters):
            await self._send(fingerprint, message)
        self._previous_counters = counters

    async def run_forever(self) -> None:
        while True:
            try:
                await self.run_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("PAPER operational alert monitor failed this pass.")
            await asyncio.sleep(self.interval_seconds)
