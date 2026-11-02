import pytest
from cryptography.fernet import Fernet, MultiFernet, InvalidToken

from app.core.encryption import encrypt_value, decrypt_value
from app.models.broker_connection import BrokerConnection
from app.models.platform_setting import PlatformSetting
from app.models.user import User
from app.services.encryption_key_rotation import rotate_database_encryption_key


def test_rotation_reencrypts_all_secret_columns_without_changing_plaintext(db_session, monkeypatch):
    old_key = Fernet.generate_key().decode()
    new_key = Fernet.generate_key().decode()
    old_cipher = MultiFernet([Fernet(old_key.encode())])

    user = User(
        email="rotation@example.com",
        password_hash="not-used-in-this-test",
        full_name="Rotation Test",
        mfa_secret_encrypted=old_cipher.encrypt(b"totp-secret").decode(),
    )
    broker = BrokerConnection(
        user_id=user.id,
        broker="upstox",
        api_key_encrypted=old_cipher.encrypt(b"api-key").decode(),
        api_secret_encrypted=old_cipher.encrypt(b"api-secret").decode(),
        redirect_uri="https://example.com/callback",
        access_token_encrypted=old_cipher.encrypt(b"access-token").decode(),
        analytics_token_encrypted=old_cipher.encrypt(b"analytics-token").decode(),
    )
    setting = PlatformSetting(
        key="provider_key",
        value_encrypted=old_cipher.encrypt(b"provider-secret").decode(),
    )
    db_session.add_all([user, broker, setting])
    db_session.commit()

    counts = rotate_database_encryption_key(
        db_session, new_primary_key=new_key, old_keys=[old_key]
    )
    db_session.commit()

    new_cipher = MultiFernet([Fernet(new_key.encode())])
    assert new_cipher.decrypt(broker.api_key_encrypted.encode()) == b"api-key"
    assert new_cipher.decrypt(broker.api_secret_encrypted.encode()) == b"api-secret"
    assert new_cipher.decrypt(broker.access_token_encrypted.encode()) == b"access-token"
    assert new_cipher.decrypt(broker.analytics_token_encrypted.encode()) == b"analytics-token"
    assert new_cipher.decrypt(setting.value_encrypted.encode()) == b"provider-secret"
    assert new_cipher.decrypt(user.mfa_secret_encrypted.encode()) == b"totp-secret"
    assert counts == {"broker_connections": 1, "platform_settings": 1, "users": 1}


def test_rotation_requires_a_distinct_old_key(db_session):
    key = Fernet.generate_key().decode()
    with pytest.raises(ValueError, match="distinct old encryption key"):
        rotate_database_encryption_key(db_session, new_primary_key=key, old_keys=[key])


def test_rotation_fails_closed_on_unreadable_ciphertext(db_session):
    old_key = Fernet.generate_key().decode()
    new_key = Fernet.generate_key().decode()
    user = User(email="badcipher@example.com", password_hash="x", full_name="Bad")
    broker = BrokerConnection(
        user_id=user.id, broker="upstox", api_key_encrypted="not-a-fernet-token",
        api_secret_encrypted="also-invalid", redirect_uri="https://example.com/callback"
    )
    db_session.add_all([user, broker])
    db_session.commit()

    with pytest.raises(InvalidToken):
        rotate_database_encryption_key(db_session, new_primary_key=new_key, old_keys=[old_key])
