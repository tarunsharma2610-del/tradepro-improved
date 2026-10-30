import pytest
from fastapi.testclient import TestClient

from app.core.deps import get_current_user, get_db
from app.main import app
from app.models.instrument import Instrument
from app.models.broker_connection import BrokerConnection


def _overrides(db_session, user):
    def override_db():
        yield db_session
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: user


def _ensure_broker_connection(db_session, user):
    """Provide the persisted broker owner row required by durable subscriptions."""
    db_session.add(BrokerConnection(
        user_id=user.id,
        broker="upstox",
        api_key_encrypted="test-encrypted-api-key",
        api_secret_encrypted="test-encrypted-api-secret",
        redirect_uri="https://example.test/oauth/callback",
    ))
    db_session.commit()


def _clear():
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def test_option_chain_uses_analytics_token_and_official_adapter(monkeypatch, db_session, make_user):
    from app.api.v1 import market_data

    user = make_user()
    _overrides(db_session, user)
    calls = {}

    monkeypatch.setattr(
        market_data.BrokerCredentialsService,
        "get_analytics_token",
        lambda self, user_id, broker: "analytics-token",
    )

    class FakeAdapter:
        async def get_option_chain(self, token, instrument_key, expiry_date):
            calls.update(token=token, instrument_key=instrument_key, expiry_date=expiry_date)
            return type("Result", (), {"ok": True, "data": {"status": "success", "data": [{"call_options": {"market_data": {"oi": 1250, "prev_oi": 1000}}, "put_options": {"market_data": {"oi": 800, "prev_oi": None}}}]}})()

    monkeypatch.setattr(market_data, "get_broker_adapter", lambda broker: FakeAdapter())
    try:
        response = TestClient(app).get(
            "/api/v1/market-data/option-chain",
            params={"instrument_key": "NSE_INDEX|Nifty 50", "expiry_date": "current_week"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["data"][0]["call_options"]["market_data"]["change_oi"] == 250
        assert response.json()["data"][0]["put_options"]["market_data"]["change_oi"] is None
        assert calls == {
            "token": "analytics-token",
            "instrument_key": "NSE_INDEX|Nifty 50",
            "expiry_date": "current_week",
        }
    finally:
        _clear()


@pytest.mark.parametrize("expiry", ["2026/10/30", "tomorrow", "20261030"])
def test_option_chain_rejects_unsupported_expiry_format(expiry, db_session, make_user):
    from app.api.v1 import market_data

    user = make_user()
    _overrides(db_session, user)
    try:
        response = TestClient(app).get(
            "/api/v1/market-data/option-chain",
            params={"instrument_key": "NSE_INDEX|Nifty 50", "expiry_date": expiry},
        )
        assert response.status_code == 422
    finally:
        _clear()


def test_option_chain_rejects_mcx_before_provider_call(db_session, make_user):
    user = make_user()
    _overrides(db_session, user)
    try:
        response = TestClient(app).get(
            "/api/v1/market-data/option-chain",
            params={"instrument_key": "MCX_INDEX|CRUDEOIL", "expiry_date": "current_month"},
        )
        assert response.status_code == 422
        assert "does not currently support MCX" in response.text
    finally:
        _clear()


def test_stream_start_requires_analytics_token_not_daily_oauth(monkeypatch, db_session, make_user):
    from app.api.v1 import market_data

    user = make_user()
    db_session.add(Instrument(
        instrument_key="NSE_INDEX|Nifty 50",
        exchange="NSE",
        segment="NSE_INDEX",
        instrument_type="INDEX",
        trading_symbol="NIFTY50",
        name="Nifty 50",
        is_active=True,
    ))
    db_session.commit()
    _ensure_broker_connection(db_session, user)
    _overrides(db_session, user)

    monkeypatch.setattr(
        market_data.BrokerCredentialsService,
        "get_analytics_token",
        lambda self, user_id, broker: "analytics-token",
    )

    class FakeStreamer:
        market_info = None
        connected = True
        running = True
        mode = "full"
        instrument_keys = ["NSE_INDEX|Nifty 50"]
        subscriptions_by_mode = {"full": ["NSE_INDEX|Nifty 50"]}

    async def fake_start(user_id, keys, mode="full"):
        assert keys == ["NSE_INDEX|Nifty 50"]
        assert mode == "full"
        return FakeStreamer()

    monkeypatch.setattr(market_data.market_data_stream_manager, "start", fake_start)
    try:
        response = TestClient(app).post(
            "/api/v1/market-data/stream",
            json={"instrument_keys": ["NSE_INDEX|Nifty 50"]},
        )
        assert response.status_code == 202, response.text
        assert response.json()["mode"] == "full"
    finally:
        _clear()


def test_stream_start_fails_closed_without_analytics_token(monkeypatch, db_session, make_user):
    from app.api.v1 import market_data

    user = make_user()
    _overrides(db_session, user)
    monkeypatch.setattr(
        market_data.BrokerCredentialsService,
        "get_analytics_token",
        lambda self, user_id, broker: None,
    )
    try:
        response = TestClient(app).post(
            "/api/v1/market-data/stream",
            json={"instrument_keys": ["NSE_INDEX|Nifty 50"]},
        )
        assert response.status_code == 400
        assert "Analytics Token" in response.text
    finally:
        _clear()



def test_stream_start_accepts_option_greeks_mode(monkeypatch, db_session, make_user):
    from app.api.v1 import market_data

    user = make_user()
    db_session.add(Instrument(
        instrument_key="NSE_FO|12345",
        exchange="NSE",
        segment="NSE_FO",
        instrument_type="OPTIONS",
        trading_symbol="NIFTY-TEST-CE",
        name="Nifty test call",
        is_active=True,
    ))
    db_session.commit()
    _ensure_broker_connection(db_session, user)
    _overrides(db_session, user)
    monkeypatch.setattr(
        market_data.BrokerCredentialsService,
        "get_analytics_token",
        lambda self, user_id, broker: "analytics-token",
    )

    class FakeStreamer:
        market_info = None
        connected = True
        running = True
        mode = "option_greeks"
        instrument_keys = ["NSE_FO|12345"]
        subscriptions_by_mode = {"option_greeks": ["NSE_FO|12345"]}

    async def fake_start(user_id, keys, mode="full"):
        assert keys == ["NSE_FO|12345"]
        assert mode == "option_greeks"
        return FakeStreamer()

    monkeypatch.setattr(market_data.market_data_stream_manager, "start", fake_start)
    try:
        response = TestClient(app).post(
            "/api/v1/market-data/stream",
            json={"instrument_keys": ["NSE_FO|12345"], "mode": "option_greeks"},
        )
        assert response.status_code == 202, response.text
        assert response.json()["mode"] == "option_greeks"
    finally:
        _clear()


def test_stream_schema_enforces_mode_specific_limits():
    from app.schemas.market_data import MarketDataStreamStart
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="2000"):
        MarketDataStreamStart(
            instrument_keys=[f"NSE_FO|{index}" for index in range(2001)],
            mode="full",
        )
    with pytest.raises(ValidationError, match="3000"):
        MarketDataStreamStart(
            instrument_keys=[f"NSE_FO|{index}" for index in range(3001)],
            mode="option_greeks",
        )



def test_stream_lifecycle_routes_use_user_scoped_stream_and_validate_active_keys(monkeypatch, db_session, make_user):
    from app.api.v1 import market_data

    user = make_user()
    for key, symbol in [("NSE_INDEX|Nifty 50", "NIFTY50"), ("NSE_INDEX|India VIX", "INDIAVIX")]:
        db_session.add(Instrument(
            instrument_key=key,
            exchange="NSE",
            segment="NSE_INDEX",
            instrument_type="INDEX",
            trading_symbol=symbol,
            name=symbol,
            is_active=True,
        ))
    db_session.commit()
    _ensure_broker_connection(db_session, user)
    _overrides(db_session, user)
    monkeypatch.setattr(
        market_data.BrokerCredentialsService,
        "get_analytics_token",
        lambda self, user_id, broker: "analytics-token",
    )

    class FakeStreamer:
        market_info = None
        running = True
        mode = "full"
        instrument_keys = ["NSE_INDEX|Nifty 50"]
        subscriptions = {"ltpc": set(), "option_greeks": set(), "full": {"NSE_INDEX|Nifty 50"}}

        @property
        def subscriptions_by_mode(self):
            return {mode: sorted(keys) for mode, keys in self.subscriptions.items() if keys}

        async def subscribe(self, keys, mode=None):
            target = mode or self.mode
            self.subscriptions[target].update(keys)
            self.instrument_keys = sorted(set().union(*self.subscriptions.values()))
            return "sent"

        async def unsubscribe(self, keys):
            for mode_keys in self.subscriptions.values():
                mode_keys.difference_update(keys)
            self.instrument_keys = sorted(set().union(*self.subscriptions.values()))
            return "sent"

        async def change_mode(self, keys, mode):
            for mode_keys in self.subscriptions.values():
                mode_keys.difference_update(keys)
            self.subscriptions[mode].update(keys)
            self.instrument_keys = sorted(set().union(*self.subscriptions.values()))
            self.mode = mode
            return "sent"

    streamer = FakeStreamer()
    monkeypatch.setattr(market_data.market_data_stream_manager, "get", lambda user_id: streamer)
    try:
        client = TestClient(app)
        subscribed = client.post(
            "/api/v1/market-data/stream/subscribe",
            json={"instrument_keys": ["NSE_INDEX|India VIX"]},
        )
        assert subscribed.status_code == 202, subscribed.text
        assert subscribed.json()["instrument_count"] == 2

        changed = client.post(
            "/api/v1/market-data/stream/change-mode",
            json={"instrument_keys": streamer.instrument_keys, "mode": "ltpc"},
        )
        assert changed.status_code == 202, changed.text
        assert changed.json()["mode"] == "ltpc"

        unsubscribed = client.post(
            "/api/v1/market-data/stream/unsubscribe",
            json={"instrument_keys": ["NSE_INDEX|India VIX"]},
        )
        assert unsubscribed.status_code == 202, unsubscribed.text
        assert streamer.instrument_keys == ["NSE_INDEX|Nifty 50"]

        invalid = client.post(
            "/api/v1/market-data/stream/subscribe",
            json={"instrument_keys": ["NSE_INDEX|UNKNOWN"]},
        )
        assert invalid.status_code == 422
    finally:
        _clear()


def test_stream_lifecycle_routes_require_existing_stream(monkeypatch, db_session, make_user):
    from app.api.v1 import market_data

    user = make_user()
    _overrides(db_session, user)
    monkeypatch.setattr(
        market_data.BrokerCredentialsService,
        "get_analytics_token",
        lambda self, user_id, broker: "analytics-token",
    )
    monkeypatch.setattr(market_data.market_data_stream_manager, "get", lambda user_id: None)
    try:
        response = TestClient(app).post(
            "/api/v1/market-data/stream/subscribe",
            json={"instrument_keys": ["NSE_INDEX|India VIX"]},
        )
        assert response.status_code == 409
    finally:
        _clear()



def test_index_presets_resolve_only_active_nse_index_catalog_rows(db_session, make_user):
    user = make_user()
    rows = [
        ("NSE_INDEX|Nifty 50", "Nifty 50", "NIFTY"),
        ("NSE_INDEX|Nifty Bank", "Nifty Bank", "BANKNIFTY"),
        ("NSE_INDEX|India VIX", "India VIX", "INDIAVIX"),
        # Same label in another exchange/segment must not be selected.
        ("BSE_INDEX|Nifty 50", "Nifty 50", "NIFTY"),
        ("NSE_EQ|NIFTY", "Nifty 50 ETF", "NIFTYETF"),
    ]
    for key, name, symbol in rows:
        db_session.add(Instrument(
            instrument_key=key,
            exchange="BSE" if key.startswith("BSE_") else "NSE",
            segment=key.split("|", 1)[0],
            instrument_type="INDEX" if "_INDEX|" in key else "EQUITY",
            trading_symbol=symbol,
            name=name,
            is_active=True,
        ))
    db_session.commit()
    _overrides(db_session, user)
    try:
        response = TestClient(app).get("/api/v1/market-data/index-presets")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["source"] == "upstox_bod_instrument_master"
        presets = {item["preset"]: item for item in body["presets"]}
        assert presets["nifty_50"]["available"] is True
        assert presets["nifty_50"]["instrument"]["instrument_key"] == "NSE_INDEX|Nifty 50"
        assert presets["nifty_bank"]["instrument"]["instrument_key"] == "NSE_INDEX|Nifty Bank"
        assert presets["india_vix"]["instrument"]["instrument_key"] == "NSE_INDEX|India VIX"
    finally:
        _clear()


def test_index_presets_fail_closed_for_missing_or_ambiguous_catalog_entries(db_session, make_user):
    user = make_user()
    for key, name, symbol in [
        ("NSE_INDEX|Nifty 50", "Nifty 50", "NIFTY"),
        ("NSE_INDEX|Nifty 50 Duplicate", "Nifty 50", "NIFTY50"),
    ]:
        db_session.add(Instrument(
            instrument_key=key,
            exchange="NSE",
            segment="NSE_INDEX",
            instrument_type="INDEX",
            trading_symbol=symbol,
            name=name,
            is_active=True,
        ))
    db_session.commit()
    _overrides(db_session, user)
    try:
        response = TestClient(app).get("/api/v1/market-data/index-presets")
        assert response.status_code == 200, response.text
        presets = {item["preset"]: item for item in response.json()["presets"]}
        assert presets["nifty_50"]["available"] is False
        assert presets["nifty_50"]["reason"] == "ambiguous_catalog_match"
        assert presets["nifty_bank"]["available"] is False
        assert presets["nifty_bank"]["reason"] == "not_found"
        assert presets["india_vix"]["available"] is False
    finally:
        _clear()



def test_stream_status_exposes_fresh_full_feed_fields_for_scanner_consumers(monkeypatch, make_user):
    from datetime import datetime, timezone
    from app.api.v1 import market_data
    from app.services.upstox_market_data_streamer import MarketTick

    user = make_user()
    tick = MarketTick(
        instrument_key="NSE_INDEX|Nifty 50",
        ltp=24500.5,
        exchange_timestamp_ms=1_798_000_000_000,
        received_at=datetime.now(timezone.utc),
        received_monotonic=1.0,
        depth=({"bid_quantity": 10, "bid_price": 24500.0, "ask_quantity": 12, "ask_price": 24501.0},),
        option_greeks=None,
        open_interest=123456.0,
        volume_traded_today=98765,
        average_traded_price=24490.0,
        total_buy_quantity=1000.0,
        total_sell_quantity=900.0,
        ohlc=({"interval": "1d", "open": 24400.0, "high": 24600.0, "low": 24350.0, "close": 24500.5, "volume": 98765, "timestamp_ms": 1_798_000_000_000},),
    )

    class FakeStreamer:
        market_info = None
        running = True
        connected = True
        mode = "full"
        instrument_keys = ["NSE_INDEX|Nifty 50"]
        subscriptions_by_mode = {"full": ["NSE_INDEX|Nifty 50"]}

        def latest_tick(self, key):
            return tick if key == tick.instrument_key else None

    _overrides(None, user)
    monkeypatch.setattr(market_data.market_data_stream_manager, "get", lambda user_id: FakeStreamer())
    try:
        response = TestClient(app).get("/api/v1/market-data/stream")
        assert response.status_code == 200, response.text
        body = response.json()
        quote = body["quotes"]["NSE_INDEX|Nifty 50"]
        assert quote["instrument_key"] == "NSE_INDEX|Nifty 50"
        assert quote["ltp"] == 24500.5
        assert quote["depth"][0]["bid_price"] == 24500.0
        assert quote["open_interest"] == 123456.0
        assert quote["volume_traded_today"] == 98765
        assert quote["average_traded_price"] == 24490.0
        assert quote["ohlc"][0]["interval"] == "1d"
        assert quote["stale"] is False
    finally:
        _clear()


def test_stream_status_represents_stale_or_missing_quotes_as_unavailable(monkeypatch, db_session, make_user):
    from app.api.v1 import market_data

    user = make_user()

    class FakeStreamer:
        market_info = None
        running = True
        connected = True
        mode = "full"
        instrument_keys = ["NSE_INDEX|India VIX"]
        subscriptions_by_mode = {"full": ["NSE_INDEX|India VIX"]}

        def latest_tick(self, key):
            return None

    _overrides(db_session, user)
    monkeypatch.setattr(market_data.market_data_stream_manager, "get", lambda user_id: FakeStreamer())
    try:
        response = TestClient(app).get("/api/v1/market-data/stream")
        assert response.status_code == 200
        assert response.json()["quotes"]["NSE_INDEX|India VIX"] is None
    finally:
        _clear()
