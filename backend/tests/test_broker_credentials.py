"""
This test exists because of a real bug in an earlier project: broker
credentials were entered but the app kept showing demo data instead of
live prices, traced back to how settings were being persisted/read. The
scenario here is exactly that: save credentials, then read them back
through a *separate* repository instance (simulating a fresh request
after a restart, not just re-reading the same Python object), and confirm
what comes back is byte-for-byte what was saved.

Actual Upstox network calls (get_profile, exchange_code_for_token) aren't
exercised here — that needs real credentials and belongs in a manual /
integration test, not an automated unit test.
"""

from app.core.encryption import decrypt_value
from app.repositories.broker_connection_repository import BrokerConnectionRepository
from app.schemas.broker import BrokerConnectionCreate
from app.services.broker_credentials_service import BrokerCredentialsService


def test_saved_credentials_survive_a_fresh_read(db_session, make_user):
    user = make_user()
    service = BrokerCredentialsService(db_session)

    payload = BrokerConnectionCreate(
        broker="upstox",
        api_key="live-api-key-123",
        api_secret="live-api-secret-456",
        redirect_uri="https://example.com/callback",
    )
    service.save_credentials(user.id, payload)

    # Fresh repository instance against the same session — the point is to
    # not rely on any in-memory Python object still holding the plaintext.
    fresh_repo = BrokerConnectionRepository(db_session)
    reloaded = fresh_repo.get_for_user(user.id, "upstox")

    assert reloaded is not None
    assert reloaded.api_key_encrypted != "live-api-key-123"  # must be encrypted, not plaintext
    assert decrypt_value(reloaded.api_key_encrypted) == "live-api-key-123"
    assert decrypt_value(reloaded.api_secret_encrypted) == "live-api-secret-456"
    assert reloaded.is_connected is False  # not connected until a real API call verifies it


def test_masked_output_never_contains_the_full_secret(db_session, make_user):
    user = make_user()
    service = BrokerCredentialsService(db_session)

    payload = BrokerConnectionCreate(
        broker="upstox", api_key="live-api-key-123", api_secret="s3cr3t", redirect_uri="https://example.com/cb"
    )
    conn = service.save_credentials(user.id, payload)
    out = service.to_masked_out(conn)

    assert "live-api-key-123" not in str(out)
    assert out["api_key_masked"] != "live-api-key-123"
    assert out["is_connected"] is False


def test_saving_new_credentials_invalidates_the_old_session(db_session, make_user):
    """If a user updates their API key, any previously-obtained access
    token for the old key must not silently keep being treated as valid."""
    user = make_user()
    service = BrokerCredentialsService(db_session)

    first = service.save_credentials(
        user.id,
        BrokerConnectionCreate(broker="upstox", api_key="key-1", api_secret="secret-1", redirect_uri="https://x/cb"),
    )
    first.is_connected = True
    first.access_token_encrypted = "pretend-token"
    db_session.add(first)
    db_session.commit()

    updated = service.save_credentials(
        user.id,
        BrokerConnectionCreate(broker="upstox", api_key="key-2", api_secret="secret-2", redirect_uri="https://x/cb"),
    )

    assert updated.is_connected is False
    assert updated.access_token_encrypted is None


def test_list_connections_only_returns_the_requesting_users_own(db_session, make_user):
    user_a = make_user(email="a@example.com")
    user_b = make_user(email="b@example.com")
    service = BrokerCredentialsService(db_session)

    service.save_credentials(
        user_a.id,
        BrokerConnectionCreate(broker="upstox", api_key="a-key", api_secret="a-secret", redirect_uri="https://x/cb"),
    )
    service.save_credentials(
        user_b.id,
        BrokerConnectionCreate(broker="upstox", api_key="b-key", api_secret="b-secret", redirect_uri="https://x/cb"),
    )

    a_connections = service.list_connections(user_a.id)
    assert len(a_connections) == 1
    assert decrypt_value(a_connections[0].api_key_encrypted) == "a-key"


def test_oauth_state_is_signed_and_bound_to_user_and_connection(db_session, make_user):
    from urllib.parse import parse_qs, urlparse

    import jwt
    import pytest

    from app.core.config import settings

    user = make_user()
    service = BrokerCredentialsService(db_session)
    service.save_credentials(
        user.id,
        BrokerConnectionCreate(broker="upstox", api_key="api-key", api_secret="api-secret", redirect_uri="https://example.com/cb"),
    )

    url = service.get_authorize_url(user.id, "upstox")
    state = parse_qs(urlparse(url).query)["state"][0]
    claims = jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert claims["sub"] == str(user.id)
    assert claims["broker"] == "upstox"
    assert claims["purpose"] == "broker_oauth"

    with pytest.raises(ValueError, match="does not match"):
        service._validate_oauth_state(state, user_id=user.id, broker="upstox", connection_id=__import__("uuid").uuid4())
