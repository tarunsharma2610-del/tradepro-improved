from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class User(BaseModel):
    """Every other tenant-owned table (portfolios, orders, broker
    connections, ...) hangs off user_id. Ownership of that id is what every
    query must be filtered by — see core/deps.py: get_current_user."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Platform admin: the only role that can read/write platform_settings
    # (WhatsApp/Telegram/AI/News keys). Regular users never see these.
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # MFA (TOTP). The secret is stored encrypted (see core/encryption.py) —
    # it's as sensitive as a password, so it gets the same treatment as
    # broker credentials, not plaintext in a column.
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret_encrypted: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # E.164 format (e.g. "+919876543210"). Not encrypted — a phone number
    # here is a notification destination, not a credential; nothing about
    # it grants access to anything. Nullable: WhatsApp notifications are
    # opt-in.
    whatsapp_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.email}>"
