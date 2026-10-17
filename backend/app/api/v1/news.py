from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_admin
from app.models.user import User
from app.repositories.news_repository import NewsRepository
from app.schemas.news import NewsFeedSourceCreate, NewsFeedSourceOut, NewsItemOut
from app.services.news_service import NewsService

router = APIRouter(prefix="/news", tags=["news"])


@router.get("", response_model=list[NewsItemOut])
def list_news(
    instrument_id: UUID | None = Query(default=None),
    limit: int = Query(default=30, le=100),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return NewsRepository(db).list_recent(limit=limit, instrument_id=instrument_id)


@router.get("/sources", response_model=list[NewsFeedSourceOut])
def list_sources(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return NewsRepository(db).list_all_sources()


@router.post("/sources", response_model=NewsFeedSourceOut, status_code=status.HTTP_201_CREATED)
def add_source(payload: NewsFeedSourceCreate, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    from app.models.news_feed_source import NewsFeedSource

    repo = NewsRepository(db)
    if repo.get_by_url(payload.rss_url) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "This feed URL is already registered.")
    return repo.create_source(NewsFeedSource(name=payload.name, rss_url=payload.rss_url, is_active=True))


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(source_id: UUID, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    repo = NewsRepository(db)
    source = next((s for s in repo.list_all_sources() if s.id == source_id), None)
    if source is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Source not found.")
    repo.delete_source(source)


@router.post("/seed-default-source", response_model=NewsFeedSourceOut)
def seed_default_source(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return NewsService(db).seed_default_source()


@router.post("/ingest", response_model=dict)
async def ingest_now(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    """Manual trigger, same as instruments/seed and instruments/sync —
    the worker also runs this periodically once sources exist (see
    app/worker.py), this endpoint is for testing without waiting."""
    results = await NewsService(db).ingest_all_active()
    return {"ingested_per_source": results}
