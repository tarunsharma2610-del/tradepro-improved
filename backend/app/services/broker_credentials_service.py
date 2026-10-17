"""
This is the service that replaces "put your Upstox key in .env": a user
calls POST /settings/broker with their key/secret, we encrypt and store it,
then walk them through the OAuth handshake and verify the connection with
a real call before ever marking it connected.
"""

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from sqlalchemy.orm import Session

from app.brokers.registry import get_broker_adapter
from app.core.config import settings
from app.core.encryption import decrypt_value, encrypt_value, mask_secret
from app.models.broker_connection import BrokerConnection
from app.repositories.broker_connection_repository import BrokerConnectionRepository
from app.schemas.broker import BrokerConnectionCreate


class BrokerCredentialsService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BrokerConnectionRepository(db)

    def list_connections(self, user_id: UUID) -> list[BrokerConnection]:
        return self.repo.list_for_user(user_id)

    def save_credentials(self, user_id: UUID, payload: BrokerConnectionCreate) -> BrokerConnection:
        return self.repo.upsert(
            user_id=user_id,
            broker=payload.broker,
            api_key_encrypted=encrypt_value(payload.api_key),
            api_secret_encrypted=encrypt_value(payload.api_secret),
            redirect_uri=payload.redirect_uri,
        )

    def get_authorize_url(self, user_id: UUID, broker: str) -> str:
        conn = self._require_connection(user_id, broker)
        adapter = get_broker_adapter(broker)
        api_key = decrypt_value(conn.api_key_encrypted)
        if api_key is None:
            raise ValueError("Stored API key could not be decrypted — was MASTER_ENCRYPTION_KEY rotated?")
        now = datetime.now(timezone.utc)
        state = jwt.encode(
            {
                "sub": str(user_id),
                "broker": broker,
                "connection_id": str(conn.id),
                "purpose": "broker_oauth",
                "nonce": secrets.token_urlsafe(24),
                "iat": now,
                "exp": now + timedelta(minutes=10),
            },
            settings.SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        return adapter.get_authorize_url(api_key, conn.redirect_uri, state=state)

    async def complete_oauth(self, user_id: UUID, broker: str, code: str, state: str) -> BrokerConnection:
        conn = self._require_connection(user_id, broker)
        self._validate_oauth_state(state, user_id=user_id, broker=broker, connection_id=conn.id)
        adapter = get_broker_adapter(broker)

        api_key = decrypt_value(conn.api_key_encrypted)
        api_secret = decrypt_value(conn.api_secret_encrypted)
        if api_key is None or api_secret is None:
            raise ValueError("Stored credentials could not be decrypted — was MASTER_ENCRYPTION_KEY rotated?")

        result = await adapter.exchange_code_for_token(api_key, api_secret, conn.redirect_uri, code)
        if not result.ok:
            conn.is_connected = False
            conn.last_error = result.error
            return self.repo.save(conn)

        token_result = result.data
        conn.access_token_encrypted = encrypt_value(token_result.access_token)
        conn.access_token_expires_at = token_result.expires_at

        # Don't trust the token exchange alone — confirm it actually works.
        await self._verify_and_update(conn, adapter, token_result.access_token)
        return self.repo.save(conn)

    async def test_connection(self, user_id: UUID, broker: str) -> tuple[bool, str]:
        conn = self._require_connection(user_id, broker)
        if not conn.access_token_encrypted:
            return False, "No access token on file yet — complete the broker login first."

        adapter = get_broker_adapter(broker)
        access_token = decrypt_value(conn.access_token_encrypted)
        if access_token is None:
            return False, "Stored access token could not be decrypted."

        ok = await self._verify_and_update(conn, adapter, access_token)
        self.repo.save(conn)
        return ok, conn.last_error or "Connected."

    def delete_connection(self, user_id: UUID, broker: str) -> None:
        conn = self._require_connection(user_id, broker)
        self.repo.delete(conn)

    def to_masked_out(self, conn: BrokerConnection) -> dict:
        api_key = decrypt_value(conn.api_key_encrypted)
        return {
            "id": conn.id,
            "broker": conn.broker,
            "api_key_masked": mask_secret(api_key) if api_key else "(undecryptable)",
            "is_connected": conn.is_connected,
            "last_connected_at": conn.last_connected_at,
            "last_error": conn.last_error,
            "created_at": conn.created_at,
        }

    def get_access_token(self, user_id: UUID, broker: str) -> str | None:
        """For internal use by the execution engine only — never exposed
        over the API. Returns None (not an exception) for any reason the
        token isn't usable right now, so callers can treat 'no live price
        available' uniformly regardless of why."""
        from datetime import datetime, timezone

        conn = self.repo.get_for_user(user_id, broker)
        if conn is None or not conn.is_connected or not conn.access_token_encrypted:
            return None
        expires_at = conn.access_token_expires_at
        if expires_at is not None:
            if expires_at.tzinfo is None:
                # Some DB drivers (SQLite in particular) don't round-trip
                # tzinfo on a DateTime(timezone=True) column even though we
                # always write UTC-aware values — treat a naive value as UTC
                # rather than letting the comparison below raise.
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at <= datetime.now(timezone.utc):
                return None
        return decrypt_value(conn.access_token_encrypted)

    # --- internal ---
    @staticmethod
    def _validate_oauth_state(state: str, *, user_id: UUID, broker: str, connection_id: UUID) -> None:
        """Validate the signed, short-lived state before exchanging the OAuth code."""
        try:
            claims = jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        except jwt.PyJWTError as exc:
            raise ValueError("Invalid or expired broker OAuth state. Restart the connection flow.") from exc

        if (
            claims.get("purpose") != "broker_oauth"
            or claims.get("sub") != str(user_id)
            or claims.get("broker") != broker
            or claims.get("connection_id") != str(connection_id)
            or not claims.get("nonce")
        ):
            raise ValueError("Broker OAuth state does not match this user and connection. Restart the connection flow.")

    def _require_connection(self, user_id: UUID, broker: str) -> BrokerConnection:
        conn = self.repo.get_for_user(user_id, broker)
        if conn is None:
            raise ValueError(f"No {broker} credentials saved for this user yet.")
        return conn

    @staticmethod
    async def _verify_and_update(conn: BrokerConnection, adapter, access_token: str) -> bool:
        from datetime import datetime, timezone

        result = await adapter.get_profile(access_token)
        if result.ok:
            conn.is_connected = True
            conn.last_connected_at = datetime.now(timezone.utc)
            conn.last_error = None
            return True
        conn.is_connected = False
        conn.last_error = result.error
        return False
