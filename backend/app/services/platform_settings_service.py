from uuid import UUID

from sqlalchemy.orm import Session

from app.core.encryption import decrypt_value, encrypt_value, mask_secret
from app.repositories.platform_setting_repository import PlatformSettingRepository
from app.schemas.platform_setting import KNOWN_PLATFORM_SETTING_KEYS


class PlatformSettingsService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PlatformSettingRepository(db)

    def list_settings(self) -> list[dict]:
        return [self._to_masked_out(s) for s in self.repo.list_all()]

    def set_setting(self, *, key: str, value: str, description: str | None, admin_user_id: UUID) -> dict:
        if key not in KNOWN_PLATFORM_SETTING_KEYS:
            raise ValueError(
                f"Unknown setting key '{key}'. Known keys: {sorted(KNOWN_PLATFORM_SETTING_KEYS)}. "
                "Add new integrations to schemas/platform_setting.py first."
            )
        setting = self.repo.upsert(
            key=key,
            value_encrypted=encrypt_value(value),
            description=description,
            updated_by_user_id=admin_user_id,
        )
        return self._to_masked_out(setting)

    def get_decrypted(self, key: str) -> str | None:
        """For internal use only (e.g. the WhatsApp/Telegram/AI service
        modules in later phases) — never exposed over the API."""
        setting = self.repo.get_by_key(key)
        if setting is None:
            return None
        return decrypt_value(setting.value_encrypted)

    @staticmethod
    def _to_masked_out(setting) -> dict:
        decrypted = decrypt_value(setting.value_encrypted)
        return {
            "key": setting.key,
            "value_masked": mask_secret(decrypted) if decrypted else "(undecryptable)",
            "description": setting.description,
            "updated_at": setting.updated_at,
        }
