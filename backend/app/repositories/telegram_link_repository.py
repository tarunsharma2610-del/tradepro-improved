from uuid import UUID

from sqlalchemy.orm import Session

from app.models.telegram_link import TelegramBotState, TelegramLink


class TelegramLinkRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_for_user(self, user_id: UUID) -> TelegramLink | None:
        return self.db.query(TelegramLink).filter(TelegramLink.user_id == user_id).first()

    def get_by_code(self, link_code: str) -> TelegramLink | None:
        return self.db.query(TelegramLink).filter(TelegramLink.link_code == link_code).first()

    def upsert_code(self, user_id: UUID, link_code: str) -> TelegramLink:
        link = self.get_for_user(user_id)
        if link is None:
            link = TelegramLink(user_id=user_id)
        link.link_code = link_code
        link.telegram_chat_id = None
        link.linked_at = None
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link

    def save(self, link: TelegramLink) -> TelegramLink:
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link

    def delete(self, link: TelegramLink) -> None:
        self.db.delete(link)
        self.db.commit()

    def get_bot_state(self) -> TelegramBotState:
        state = self.db.query(TelegramBotState).first()
        if state is None:
            state = TelegramBotState(last_update_id=0)
            self.db.add(state)
            self.db.commit()
            self.db.refresh(state)
        return state

    def save_bot_state(self, state: TelegramBotState) -> None:
        self.db.add(state)
        self.db.commit()
