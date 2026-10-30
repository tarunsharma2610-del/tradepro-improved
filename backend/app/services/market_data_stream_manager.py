"""In-process registry for per-user Upstox market streams.

Streams are ephemeral and restart with the API process. Analytics Tokens are
looked up from the encrypted connection store for each reconnect; they are
never sent to clients or logged.
"""
from uuid import UUID

from app.core.database import SessionLocal
from app.services.broker_credentials_service import BrokerCredentialsService
from app.services.upstox_market_data_streamer import MarketTick, UpstoxMarketDataStreamer


class MarketDataStreamManager:
    def __init__(self):
        self._streams: dict[UUID, UpstoxMarketDataStreamer] = {}

    async def start(self, user_id: UUID, instrument_keys: list[str], mode: str = "full") -> UpstoxMarketDataStreamer:
        current = self._streams.get(user_id)
        if current is not None:
            await current.stop()

        async def token_provider() -> str | None:
            db = SessionLocal()
            try:
                return BrokerCredentialsService(db).get_analytics_token(user_id, "upstox")
            finally:
                db.close()

        streamer = UpstoxMarketDataStreamer(token_provider, instrument_keys, mode=mode)
        self._streams[user_id] = streamer
        await streamer.start()
        return streamer

    async def stop(self, user_id: UUID) -> bool:
        streamer = self._streams.pop(user_id, None)
        if streamer is None:
            return False
        await streamer.stop()
        return True

    def get(self, user_id: UUID) -> UpstoxMarketDataStreamer | None:
        return self._streams.get(user_id)

    async def shutdown(self) -> None:
        streams = list(self._streams.items())
        self._streams.clear()
        for _, streamer in streams:
            await streamer.stop()


market_data_stream_manager = MarketDataStreamManager()
