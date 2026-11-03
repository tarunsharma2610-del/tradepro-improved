from datetime import date

from pydantic import BaseModel, Field, field_validator


class Nifty500UniverseImport(BaseModel):
    """Validated constituent symbols copied from a dated official source file."""

    as_of_date: date
    source: str = Field(min_length=1, max_length=255)
    symbols: list[str] = Field(min_length=500, max_length=500)

    @field_validator("source")
    @classmethod
    def normalize_source(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("A source description is required.")
        return value

    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, values: list[str]) -> list[str]:
        normalized = [value.strip().upper() for value in values]
        if any(not value or len(value) > 50 for value in normalized):
            raise ValueError("Every constituent must have a valid trading symbol.")
        if len(set(normalized)) != 500:
            raise ValueError("Nifty 500 snapshot must contain exactly 500 unique symbols.")
        return normalized


class MarketUniverseSnapshotOut(BaseModel):
    snapshot_id: str
    universe_key: str
    as_of_date: date
    source: str
    member_count: int
