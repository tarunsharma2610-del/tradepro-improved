from types import SimpleNamespace
from uuid import uuid4

from app.services.broker_instrument_reconciliation_service import reconcile_broker_instruments


def test_reconciles_only_exact_instrument_key_and_validates_symbol_exchange():
    instrument_id = uuid4()
    master = [SimpleNamespace(
        id=instrument_id,
        instrument_key="NSE_EQ|INE528G01035",
        exchange="NSE",
        trading_symbol="YESBANK",
    )]
    result = reconcile_broker_instruments([
        {"instrument_key": "NSE_EQ|INE528G01035", "exchange": "NSE", "trading_symbol": "YESBANK"},
        {"instrument_key": "NSE_EQ|UNKNOWN", "exchange": "NSE", "trading_symbol": "YESBANK"},
        {"instrument_key": "NSE_EQ|INE528G01035", "exchange": "BSE", "trading_symbol": "YESBANK"},
        {"instrument_key": "NSE_EQ|INE528G01035", "exchange": "NSE", "trading_symbol": "OTHER"},
        {"instrument_key": "", "exchange": "NSE", "trading_symbol": "YESBANK"},
    ], master)
    assert [row["status"] for row in result] == [
        "MATCHED", "UNMAPPED", "IDENTITY_CONFLICT", "IDENTITY_CONFLICT", "MISSING_BROKER_KEY"
    ]
    assert result[0]["instrument_id"] == str(instrument_id)
    assert all(row.get("instrument_id") is None for row in result[1:])


def test_duplicate_broker_keys_are_ambiguous_not_guessed():
    master = [SimpleNamespace(
        id=uuid4(),
        instrument_key="NSE_EQ|INE528G01035",
        exchange="NSE",
        trading_symbol="YESBANK",
    )]
    result = reconcile_broker_instruments([
        {"instrument_key": "NSE_EQ|INE528G01035"},
        {"instrument_key": "NSE_EQ|INE528G01035"},
    ], master)
    assert [row["status"] for row in result] == ["AMBIGUOUS", "AMBIGUOUS"]


def test_duplicate_master_keys_are_ambiguous():
    master = [
        SimpleNamespace(id=uuid4(), instrument_key="NSE_EQ|INE528G01035", exchange="NSE", trading_symbol="YESBANK"),
        SimpleNamespace(id=uuid4(), instrument_key="NSE_EQ|INE528G01035", exchange="NSE", trading_symbol="YESBANK"),
    ]
    result = reconcile_broker_instruments([
        {"instrument_key": "NSE_EQ|INE528G01035", "exchange": "NSE", "trading_symbol": "YESBANK"}
    ], master)
    assert result[0]["status"] == "AMBIGUOUS"
    assert result[0]["instrument_id"] is None


def test_non_dict_source_rows_are_reported_invalid():
    assert reconcile_broker_instruments([None], []) == [
        {"row_index": 0, "status": "INVALID_SOURCE_ROW", "instrument_id": None}
    ]
