"""
This is the service that replaces "put your Upstox key in .env": a user
calls POST /settings/broker with their key/secret, we encrypt and store it,
then walk them through the OAuth handshake and verify the connection with
a real call before ever marking it connected.
"""

import hashlib
import hmac
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
        conn = self.repo.upsert(
            user_id=user_id,
            broker=payload.broker,
            api_key_encrypted=encrypt_value(payload.api_key),
            api_secret_encrypted=encrypt_value(payload.api_secret),
            redirect_uri=payload.redirect_uri,
        )
        # Any pending OAuth state was issued for the previous credential set.
        conn.oauth_state_nonce_hash = None
        conn.oauth_state_expires_at = None
        return self.repo.save(conn)

    def get_authorize_url(self, user_id: UUID, broker: str) -> str:
        conn = self._require_connection(user_id, broker)
        adapter = get_broker_adapter(broker)
        api_key = decrypt_value(conn.api_key_encrypted)
        if api_key is None:
            raise ValueError("Stored API key could not be decrypted — was MASTER_ENCRYPTION_KEY rotated?")
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=10)
        nonce = secrets.token_urlsafe(24)
        state = jwt.encode(
            {
                "sub": str(user_id),
                "broker": broker,
                "connection_id": str(conn.id),
                "purpose": "broker_oauth",
                "nonce": nonce,
                "iat": now,
                "exp": expires_at,
            },
            settings.SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        conn.oauth_state_nonce_hash = hashlib.sha256(nonce.encode("utf-8")).hexdigest()
        conn.oauth_state_expires_at = expires_at
        self.repo.save(conn)
        return adapter.get_authorize_url(api_key, conn.redirect_uri, state=state)

    async def complete_oauth(self, user_id: UUID, broker: str, code: str, state: str) -> BrokerConnection:
        conn = self._require_connection(user_id, broker)
        claims = self._validate_oauth_state(state, user_id=user_id, broker=broker, connection_id=conn.id)
        self._consume_oauth_nonce(conn, claims["nonce"])
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
    def _validate_oauth_state(state: str, *, user_id: UUID, broker: str, connection_id: UUID) -> dict:
        """Validate signature, expiry, and user/connection binding before exchanging the OAuth code."""
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
        return claims

    def _consume_oauth_nonce(self, conn: BrokerConnection, nonce: str) -> None:
        """Consume the nonce with a conditional database update to block concurrent replays."""
        expected_hash = conn.oauth_state_nonce_hash
        expires_at = conn.oauth_state_expires_at
        if not expected_hash or expires_at is None:
            raise ValueError("Broker OAuth state was already used or was not issued. Restart the connection flow.")

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        actual_hash = hashlib.sha256(nonce.encode("utf-8")).hexdigest()
        if expires_at <= now or not hmac.compare_digest(expected_hash, actual_hash):
            raise ValueError("Broker OAuth state is expired or has already been used. Restart the connection flow.")

        # The hash comparison is part of the UPDATE predicate, not just an
        # in-memory check, so only one concurrent callback can consume it.
        from sqlalchemy import update

        result = self.db.execute(
            update(BrokerConnection)
            .where(
                BrokerConnection.id == conn.id,
                BrokerConnection.oauth_state_nonce_hash == expected_hash,
                BrokerConnection.oauth_state_expires_at > now,
            )
            .values(oauth_state_nonce_hash=None, oauth_state_expires_at=None)
        )
        if result.rowcount != 1:
            self.db.rollback()
            raise ValueError("Broker OAuth state is expired or has already been used. Restart the connection flow.")

        self.db.commit()
        conn.oauth_state_nonce_hash = None
        conn.oauth_state_expires_at = None

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
