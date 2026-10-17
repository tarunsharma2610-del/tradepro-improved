from uuid import UUID

from sqlalchemy.orm import Session

from app.models.platform_setting import PlatformSetting


class PlatformSettingRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[PlatformSetting]:
        return self.db.query(PlatformSetting).order_by(PlatformSetting.key).all()

    def get_by_key(self, key: str) -> PlatformSetting | None:
        return self.db.query(PlatformSetting).filter(PlatformSetting.key == key).first()

    def upsert(
        self, *, key: str, value_encrypted: str, description: str | None, updated_by_user_id: UUID
    ) -> PlatformSetting:
        setting = self.get_by_key(key)
        if setting is None:
            setting = PlatformSetting(key=key)
        setting.value_encrypted = value_encrypted
        if description is not None:
            setting.description = description
        setting.updated_by_user_id = updated_by_user_id
        self.db.add(setting)
        self.db.commit()
        self.db.refresh(setting)
        return setting
