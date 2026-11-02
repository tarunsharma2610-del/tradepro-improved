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


@pytest.mark.parametrize(
    "origins",
    [
        ["http://app.example.com"],
        ["*"],
        ["https://app.example.com/portal"],
        ["https://app.example.com?next=/"],
        ["https://user:password@app.example.com"],
    ],
)
def test_production_rejects_unsafe_cors_origins(monkeypatch, origins):
    import json

    monkeypatch.setenv("SECRET_KEY", "s" * 64)
    monkeypatch.setenv("MASTER_ENCRYPTION_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("CORS_ORIGINS", json.dumps(origins))

    with pytest.raises(ValidationError, match="production CORS_ORIGINS"):
        Settings(ENVIRONMENT="production", _env_file=None)


def test_production_accepts_exact_https_cors_origins(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "s" * 64)
    monkeypatch.setenv("MASTER_ENCRYPTION_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("CORS_ORIGINS", '["https://app.example.com", "https://admin.example.com:8443"]')

    configured = Settings(ENVIRONMENT="production", _env_file=None)

    assert configured.CORS_ORIGINS == ["https://app.example.com", "https://admin.example.com:8443"]


def test_development_allows_local_http_cors_origin(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", '["http://localhost:3000"]')

    configured = Settings(ENVIRONMENT="development", _env_file=None)

    assert configured.CORS_ORIGINS == ["http://localhost:3000"]
