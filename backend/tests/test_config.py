import pytest
from cryptography.fernet import Fernet
from pydantic import ValidationError

from app.core.config import Settings


def test_production_requires_explicit_stable_secret_key(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("MASTER_ENCRYPTION_KEY", raising=False)

    with pytest.raises(ValidationError, match="SECRET_KEY must be explicitly configured"):
        Settings(ENVIRONMENT="production", _env_file=None)


def test_production_requires_master_encryption_key(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "s" * 64)
    monkeypatch.delenv("MASTER_ENCRYPTION_KEY", raising=False)

    with pytest.raises(ValidationError, match="MASTER_ENCRYPTION_KEY must be configured"):
        Settings(ENVIRONMENT="production", _env_file=None)


def test_production_accepts_explicit_bootstrap_secrets(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "s" * 64)
    monkeypatch.setenv("MASTER_ENCRYPTION_KEY", Fernet.generate_key().decode())

    configured = Settings(ENVIRONMENT="production", _env_file=None)

    assert configured.SECRET_KEY == "s" * 64
    assert configured.MASTER_ENCRYPTION_KEY


def test_development_keeps_local_secret_fallback(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("MASTER_ENCRYPTION_KEY", raising=False)

    configured = Settings(ENVIRONMENT="development", _env_file=None)

    assert len(configured.SECRET_KEY) >= 32
