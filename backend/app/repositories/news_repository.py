from uuid import UUID

from sqlalchemy.orm import Session

from app.models.news_feed_source import NewsFeedSource
from app.models.news_item import NewsItem


class NewsRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- sources (admin-managed) ---
    def list_active_sources(self) -> list[NewsFeedSource]:
        return self.db.query(NewsFeedSource).filter(NewsFeedSource.is_active.is_(True)).all()

    def list_all_sources(self) -> list[NewsFeedSource]:
        return self.db.query(NewsFeedSource).order_by(NewsFeedSource.name).all()

    def get_by_url(self, rss_url: str) -> NewsFeedSource | None:
        return self.db.query(NewsFeedSource).filter(NewsFeedSource.rss_url == rss_url).first()

    def create_source(self, source: NewsFeedSource) -> NewsFeedSource:
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source

    def delete_source(self, source: NewsFeedSource) -> None:
        self.db.delete(source)
        self.db.commit()

    # --- items ---
    def get_by_link(self, link: str) -> NewsItem | None:
        return self.db.query(NewsItem).filter(NewsItem.link == link).first()

    def list_recent(self, limit: int = 50, instrument_id: UUID | None = None) -> list[NewsItem]:
        from app.models.news_item import news_item_instruments

        query = self.db.query(NewsItem)
        if instrument_id is not None:
            query = query.join(news_item_instruments).filter(news_item_instruments.c.instrument_id == instrument_id)
        return query.order_by(NewsItem.published_at.desc().nulls_last()).limit(limit).all()
