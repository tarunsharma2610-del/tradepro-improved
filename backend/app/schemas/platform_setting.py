from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# Keys the app knows how to use today. Adding a new integration in a later
# phase means adding its key here, not inventing a new storage mechanism.
KNOWN_PLATFORM_SETTING_KEYS = {
    "whatsapp_api_token",
    "whatsapp_phone_number_id",  # WhatsApp Cloud API needs both this and the token — see whatsapp_notifier.py
    "telegram_bot_token",
    "ai_provider_api_key",
    "news_api_key",
}


class PlatformSettingUpdate(BaseModel):
    key: str = Field(max_length=100)
    value: str = Field(min_length=1, max_length=2000)
    description: str | None = Field(default=None, max_length=255)


class PlatformSettingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    value_masked: str
    description: str | None
    updated_at: datetime
