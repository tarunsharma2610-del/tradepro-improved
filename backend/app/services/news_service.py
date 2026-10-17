"""
The ticker-vs-name gap is real, not hypothetical: testing this against a
live-captured Business Standard headline ("ICICI Bank raises fresh $750
million") showed the exact ticker "ICICIBANK" never appears in a real
headline — only the company name does. So instrument matching here keys
on both the trading_symbol AND a cleaned version of the instrument's name
(corporate suffixes like "Ltd" stripped), not ticker alone.
"""

import re
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.models.news_feed_source import NewsFeedSource
from app.models.news_item import NewsItem
from app.repositories.news_repository import NewsRepository
from app.services.news_parsing import match_instruments, parse_rss

_CORPORATE_SUFFIXES = re.compile(r"\b(Ltd\.?|Limited|Pvt\.?|Private|Inc\.?|Corporation|Corp\.?)\b", re.IGNORECASE)


def _build_instrument_lookup(db: Session) -> dict[str, object]:
    from app.models.instrument import Instrument

    lookup: dict[str, object] = {}
    for instrument in db.query(Instrument).filter(Instrument.is_active.is_(True)).all():
        lookup[instrument.trading_symbol] = instrument
        cleaned_name = _CORPORATE_SUFFIXES.sub("", instrument.name).strip()
        if cleaned_name and cleaned_name.upper() != instrument.trading_symbol.upper():
            lookup[cleaned_name] = instrument
    return lookup


class NewsService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = NewsRepository(db)

    async def ingest_source(self, source: NewsFeedSource) -> tuple[int, str | None]:
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(source.rss_url, headers={"User-Agent": "Mozilla/5.0 (compatible; TradingPlatformNewsBot/1.0)"})
        except httpx.HTTPError as exc:
            return 0, f"Network error: {exc}"

        if resp.status_code != 200:
            return 0, f"Feed returned HTTP {resp.status_code}"

        parsed_items = parse_rss(resp.text)
        if not parsed_items:
            return 0, "Feed returned no parseable items"

        instrument_lookup = _build_instrument_lookup(self.db)
        added = 0
        for parsed in parsed_items:
            if self.repo.get_by_link(parsed.link) is not None:
                continue  # already ingested — RSS feeds repeat old items on every fetch

            text_for_matching = f"{parsed.title} {parsed.summary or ''}"
            matched = match_instruments(text_for_matching, instrument_lookup)

            news_item = NewsItem(
                source_id=source.id, title=parsed.title, link=parsed.link,
                summary=parsed.summary, published_at=parsed.published_at,
            )
            news_item.instruments = list({m.id: m for m in matched}.values())
            self.db.add(news_item)
            added += 1

        source.last_fetched_at = datetime.now(timezone.utc)
        source.last_error = None
        self.db.add(source)
        self.db.commit()
        return added, None

    async def ingest_all_active(self) -> dict[str, int]:
        results = {}
        for source in self.repo.list_active_sources():
            added, error = await self.ingest_source(source)
            if error:
                source.last_error = error
                self.db.add(source)
                self.db.commit()
            results[source.name] = added
        return results

    def seed_default_source(self) -> NewsFeedSource:
        """The one independently-verified working feed — see
        tests/test_news_parsing.py, which tests against genuinely
        real content captured from this exact URL."""
        existing = self.repo.get_by_url("https://www.business-standard.com/rss/home_page_top_stories.rss")
        if existing:
            return existing
        source = NewsFeedSource(
            name="Business Standard — Top Stories",
            rss_url="https://www.business-standard.com/rss/home_page_top_stories.rss",
            is_active=True,
        )
        return self.repo.create_source(source)
