from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class MarketDataStreamStart(BaseModel):
    instrument_keys: list[str] = Field(min_length=1, max_length=5000)
    mode: Literal["ltpc", "option_greeks", "full"] = "full"

    @field_validator("instrument_keys")
    @classmethod
    def validate_instrument_keys(cls, values: list[str]) -> list[str]:
        normalized = list(dict.fromkeys(value.strip() for value in values if value.strip()))
        if not normalized:
            raise ValueError("Provide at least one instrument_key.")
        if any("|" not in value or len(value) > 100 for value in normalized):
            raise ValueError("Each instrument_key must be a segment-prefixed Upstox key.")
        return normalized

    @model_validator(mode="after")
    def validate_mode_limit(self):
        limits = {"ltpc": 5000, "option_greeks": 3000, "full": 2000}
        if len(self.instrument_keys) > limits[self.mode]:
            raise ValueError(f"{self.mode} mode supports at most {limits[self.mode]} instrument keys per connection.")
        return self



class MarketDataStreamKeys(BaseModel):
    instrument_keys: list[str] = Field(min_length=1, max_length=5000)
    mode: Literal["ltpc", "option_greeks", "full"] | None = None

    @field_validator("instrument_keys")
    @classmethod
    def validate_instrument_keys(cls, values: list[str]) -> list[str]:
        normalized = list(dict.fromkeys(value.strip() for value in values if value.strip()))
        if not normalized:
            raise ValueError("Provide at least one instrument_key.")
        if any("|" not in value or len(value) > 100 for value in normalized):
            raise ValueError("Each instrument_key must be a segment-prefixed Upstox key.")
        return normalized


class MarketDataStreamChangeMode(MarketDataStreamKeys):
    mode: Literal["ltpc", "option_greeks", "full"]
