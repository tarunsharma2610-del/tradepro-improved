from pydantic import BaseModel, Field, field_validator


class MarketDataStreamStart(BaseModel):
    instrument_keys: list[str] = Field(min_length=1, max_length=5000)

    @field_validator("instrument_keys")
    @classmethod
    def validate_instrument_keys(cls, values: list[str]) -> list[str]:
        normalized = list(dict.fromkeys(value.strip() for value in values if value.strip()))
        if not normalized:
            raise ValueError("Provide at least one instrument_key.")
        if any("|" not in value or len(value) > 100 for value in normalized):
            raise ValueError("Each instrument_key must be a segment-prefixed Upstox key.")
        return normalized
