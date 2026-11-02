from datetime import date

import pytest

from app.models.instrument import Instrument
from app.models.market_universe import MarketUniverseMembership, MarketUniverseSnapshot
from app.services.market_universe_service import MarketUniverseImportError, MarketUniverseService


def _seed_nse_equities(db_session, start: int, count: int) -> list[str]:
    symbols = [f"TEST{index:04d}" for index in range(start, start + count)]
    db_session.add_all([
        Instrument(
            instrument_key=f"NSE_EQ|INE{index:09d}",
            exchange="NSE",
            segment="NSE_EQ",
            instrument_type="EQUITY",
            trading_symbol=symbol,
            name=symbol,
            lot_size=1,
            tick_size=0.05,
            is_active=True,
        )
        for index, symbol in enumerate(symbols, start=start)
    ])
    db_session.commit()
    return symbols


def test_nifty500_import_creates_auditable_exact_membership_snapshot(db_session):
    symbols = _seed_nse_equities(db_session, 1, 500)

    snapshot = MarketUniverseService(db_session).import_nifty500(
        symbols=symbols,
        as_of_date=date(2026, 11, 1),
        source="NSE official Nifty 500 constituent file",
    )

    assert snapshot.universe_key == "NIFTY_500"
    assert snapshot.member_count == 500
    assert snapshot.is_active is True
    assert snapshot.source == "NSE official Nifty 500 constituent file"
    members = (
        db_session.query(MarketUniverseMembership)
        .filter(MarketUniverseMembership.snapshot_id == snapshot.id)
        .all()
    )
    assert len(members) == 500
    active = MarketUniverseService(db_session).active_nifty500_instruments()
    assert len(active) == 500
    assert {item.trading_symbol for item in active} == set(symbols)


def test_invalid_nifty500_mapping_does_not_replace_existing_snapshot(db_session):
    first = _seed_nse_equities(db_session, 1, 500)
    service = MarketUniverseService(db_session)
    original = service.import_nifty500(
        symbols=first,
        as_of_date=date(2026, 11, 1),
        source="NSE official constituent file",
    )
    second = _seed_nse_equities(db_session, 501, 499)

    with pytest.raises(MarketUniverseImportError, match="not mapped"):
        service.import_nifty500(
            symbols=second + ["NOTMAPPED"],
            as_of_date=date(2026, 11, 2),
            source="NSE official constituent file",
        )

    db_session.refresh(original)
    assert original.is_active is True
    assert len(service.active_nifty500_instruments()) == 500


def test_nifty500_import_rejects_duplicate_symbols_before_database_writes(db_session):
    symbols = _seed_nse_equities(db_session, 1, 500)
    with pytest.raises(MarketUniverseImportError, match="500 unique"):
        MarketUniverseService(db_session).import_nifty500(
            symbols=symbols[:-1] + [symbols[0]],
            as_of_date=date(2026, 11, 1),
            source="NSE official constituent file",
        )
    assert db_session.query(MarketUniverseSnapshot).count() == 0


def test_nifty500_universe_excludes_bse_and_derivative_instruments(db_session):
    symbols = _seed_nse_equities(db_session, 1, 500)
    db_session.add(Instrument(
        instrument_key="BSE_EQ|INE999999999",
        exchange="BSE",
        segment="BSE_EQ",
        instrument_type="EQUITY",
        trading_symbol="TEST0001",
        name="Duplicate symbol on BSE",
        lot_size=1,
        tick_size=0.05,
        is_active=True,
    ))
    db_session.commit()

    snapshot = MarketUniverseService(db_session).import_nifty500(
        symbols=symbols,
        as_of_date=date(2026, 11, 1),
        source="NSE official constituent file",
    )
    active = MarketUniverseService(db_session).active_nifty500_instruments()
    assert snapshot.member_count == 500
    assert all(item.exchange == "NSE" and item.segment == "NSE_EQ" for item in active)


def test_duplicate_effective_date_is_rejected_without_deactivating_current_snapshot(db_session):
    symbols = _seed_nse_equities(db_session, 1, 500)
    service = MarketUniverseService(db_session)
    original = service.import_nifty500(
        symbols=symbols,
        as_of_date=date(2026, 11, 1),
        source="NSE official constituent file",
    )

    with pytest.raises(MarketUniverseImportError, match="already exists"):
        service.import_nifty500(
            symbols=symbols,
            as_of_date=date(2026, 11, 1),
            source="corrected copy of same date",
        )

    db_session.refresh(original)
    assert original.is_active is True
    assert len(service.active_nifty500_instruments()) == 500


def test_new_effective_date_atomically_replaces_active_snapshot_and_keeps_history(db_session):
    first_symbols = _seed_nse_equities(db_session, 1, 500)
    service = MarketUniverseService(db_session)
    first = service.import_nifty500(
        symbols=first_symbols,
        as_of_date=date(2026, 11, 1),
        source="NSE official constituent file",
    )
    second_symbols = _seed_nse_equities(db_session, 501, 500)
    second = service.import_nifty500(
        symbols=second_symbols,
        as_of_date=date(2026, 11, 2),
        source="NSE official revised constituent file",
    )

    db_session.refresh(first)
    assert first.is_active is False
    assert second.is_active is True
    assert db_session.query(MarketUniverseSnapshot).count() == 2
    active = service.active_nifty500_instruments()
    assert len(active) == 500
    assert {item.trading_symbol for item in active} == set(second_symbols)


def test_market_universe_membership_and_snapshot_content_are_database_immutable(db_session):
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError

    symbols = _seed_nse_equities(db_session, 1, 500)
    snapshot = MarketUniverseService(db_session).import_nifty500(
        symbols=symbols,
        as_of_date=date(2026, 11, 1),
        source="NSE official constituent file",
    )
    member = (
        db_session.query(MarketUniverseMembership)
        .filter(MarketUniverseMembership.snapshot_id == snapshot.id)
        .first()
    )

    mutations = [
        ("UPDATE market_universe_memberships SET trading_symbol = 'TAMPERED' WHERE id = :id", {"id": member.id.hex}),
        ("DELETE FROM market_universe_memberships WHERE id = :id", {"id": member.id.hex}),
        ("UPDATE market_universe_snapshots SET source = 'tampered' WHERE id = :id", {"id": snapshot.id.hex}),
        ("UPDATE market_universe_snapshots SET member_count = 1 WHERE id = :id", {"id": snapshot.id.hex}),
        ("DELETE FROM market_universe_snapshots WHERE id = :id", {"id": snapshot.id.hex}),
    ]
    for statement, params in mutations:
        with pytest.raises(IntegrityError):
            db_session.execute(text(statement), params)
        db_session.rollback()

    # Activation state is intentionally mutable so a complete newer snapshot
    # can replace the active one; immutable source content remains protected.
    db_session.execute(
        text("UPDATE market_universe_snapshots SET is_active = 0 WHERE id = :id"),
        {"id": snapshot.id.hex},
    )
    db_session.commit()
    db_session.refresh(snapshot)
    assert snapshot.is_active is False
    assert db_session.query(MarketUniverseMembership).filter(
        MarketUniverseMembership.snapshot_id == snapshot.id
    ).count() == 500
