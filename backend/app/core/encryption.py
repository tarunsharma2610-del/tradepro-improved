"""
Encryption at rest for secrets stored in the database.

Everything that goes through here (a user's Upstox key/secret/token, an
admin's WhatsApp/Telegram/AI/News provider key) is encrypted with
MASTER_ENCRYPTION_KEY before it touches the database, and decrypted only
in-memory, on demand, server-side. The frontend never receives a decrypted
secret back — only a masked preview (see schemas/broker.py).

MASTER_ENCRYPTION_KEY itself is the one thing this scheme can't move into
the database (you can't lock the key to the safe inside the safe), so it
stays a bootstrap env var. Rotate it via `rotate_encryption_key` below if
it's ever compromised.
"""

from cryptography.fernet import Fernet, InvalidToken, MultiFernet

from app.core.config import settings


class EncryptionNotConfiguredError(RuntimeError):
    pass


def _fernet() -> MultiFernet:
    if not settings.MASTER_ENCRYPTION_KEY:
        raise EncryptionNotConfiguredError(
            "MASTER_ENCRYPTION_KEY is not set. Run setup.sh to generate one, "
            "or set it in your environment before storing any credentials."
        )
    # Comma-separated list supports zero-downtime key rotation: newest key
    # first (used for new encryptions), older keys still accepted for reads.
    keys = [k.strip() for k in settings.MASTER_ENCRYPTION_KEY.split(",") if k.strip()]
    return MultiFernet([Fernet(k.encode()) for k in keys])


def encrypt_value(plain_text: str) -> str:
    return _fernet().encrypt(plain_text.encode()).decode()


def decrypt_value(cipher_text: str) -> str | None:
    try:
        return _fernet().decrypt(cipher_text.encode()).decode()
    except InvalidToken:
        return None


def mask_secret(plain_text: str, visible: int = 4) -> str:
    """For display only, e.g. 'sk-abc...wxyz'. Never send the real value back to a client."""
    if len(plain_text) <= visible * 2:
        return "*" * len(plain_text)
    return f"{plain_text[:visible]}...{plain_text[-visible:]}"


def generate_key() -> str:
    """Used by setup.sh to generate a fresh MASTER_ENCRYPTION_KEY."""
    return Fernet.generate_key().decode()
