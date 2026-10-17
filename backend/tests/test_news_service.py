from unittest.mock import AsyncMock, patch

import pytest

from app.models.news_feed_source import NewsFeedSource
from app.services.instrument_service import InstrumentService
from app.services.news_service import NewsService
from tests.test_news_parsing import REAL_SAMPLE_RSS


def _mock_response(text: str, status: int = 200):
    mock_resp = type("R", (), {"status_code": status, "text": text})()
    return patch(
        "app.services.news_service.httpx.AsyncClient.get",
        new=AsyncMock(return_value=mock_resp),
    )


@pytest.fixture()
def source(db_session) -> NewsFeedSource:
    s = NewsFeedSource(name="Test Source", rss_url="https://example.com/rss", is_active=True)
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)
    return s


@pytest.mark.asyncio
async def test_ingest_source_stores_items_from_real_content_and_tags_icici(db_session, source):
    InstrumentService(db_session).seed_defaults()  # includes ICICIBANK with name "ICICI Bank Ltd"
    service = NewsService(db_session)

    with _mock_response(REAL_SAMPLE_RSS):
        added, error = await service.ingest_source(source)

    assert error is None
    assert added == 3

    from app.repositories.news_repository import NewsRepository

    items = NewsRepository(db_session).list_recent(limit=10)
    assert len(items) == 3

    icici_item = next(i for i in items if "ICICI" in i.title)
    assert len(icici_item.instruments) == 1
    assert icici_item.instruments[0].trading_symbol == "ICICIBANK"

    apple_item = next(i for i in items if "Apple" in i.title)
    assert apple_item.instruments == []  # Apple isn't in the seeded NSE instrument set


@pytest.mark.asyncio
async def test_ingest_source_is_idempotent_on_a_second_fetch(db_session, source):
    InstrumentService(db_session).seed_defaults()
    service = NewsService(db_session)

    with _mock_response(REAL_SAMPLE_RSS):
        first_added, _ = await service.ingest_source(source)
    with _mock_response(REAL_SAMPLE_RSS):
        second_added, _ = await service.ingest_source(source)

    assert first_added == 3
    assert second_added == 0  # same links — RSS feeds repeat old items every fetch

    from app.repositories.news_repository import NewsRepository

    assert len(NewsRepository(db_session).list_recent(limit=100)) == 3


@pytest.mark.asyncio
async def test_ingest_source_records_a_clear_error_on_http_failure(db_session, source):
    service = NewsService(db_session)
    with _mock_response("", status=404):
        added, error = await service.ingest_source(source)

    assert added == 0
    assert "404" in error


@pytest.mark.asyncio
async def test_ingest_source_handles_unparseable_response_without_crashing(db_session, source):
    service = NewsService(db_session)
    with _mock_response("not xml at all"):
        added, error = await service.ingest_source(source)

    assert added == 0
    assert error is not None


def test_seed_default_source_is_idempotent(db_session):
    service = NewsService(db_session)
    first = service.seed_default_source()
    second = service.seed_default_source()
    assert first.id == second.id

    from app.repositories.news_repository import NewsRepository

    assert len(NewsRepository(db_session).list_active_sources()) == 1


def test_instrument_lookup_matches_company_name_not_just_ticker(db_session):
    """Direct regression test for the exact gap testing surfaced: a real
    headline says 'ICICI Bank', not the ticker 'ICICIBANK'."""
    from app.services.news_service import _build_instrument_lookup

    InstrumentService(db_session).seed_defaults()
    lookup = _build_instrument_lookup(db_session)

    assert "ICICIBANK" in lookup
    assert any("ICICI Bank" in k for k in lookup)  # the cleaned company name is also a key
