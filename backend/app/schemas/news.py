from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.instrument import InstrumentBrief


class NewsFeedSourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    rss_url: str = Field(min_length=1, max_length=500)


class NewsFeedSourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    rss_url: str
    is_active: bool
    last_fetched_at: datetime | None
    last_error: str | None


class NewsItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    link: str
    summary: str | None
    published_at: datetime | None
    instruments: list[InstrumentBrief]
