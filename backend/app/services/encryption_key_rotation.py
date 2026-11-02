"""Transactional re-encryption of database secrets during MASTER_ENCRYPTION_KEY rotation.

Deployment procedure:
1. Keep the old key(s) available and configure MASTER_ENCRYPTION_KEY as
   "NEW_PRIMARY,OLD_KEY_1,...".
2. Run this service once from an authenticated maintenance command inside a
   database transaction, then verify the returned counts and commit.
3. Keep old keys configured until backups/restore tests are complete. Removing
   an old key before every database copy is re-encrypted makes those copies
   permanently unreadable.
4. A failed row raises and the caller must roll back the whole transaction.
"""
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet, MultiFernet

from app.models.broker_connection import BrokerConnection
from app.models.platform_setting import PlatformSetting
from app.models.user import User


def rotate_database_encryption_key(
    db: Session, *, new_primary_key: str, old_keys: list[str]
) -> dict[str, int]:
    """Re-encrypt all known encrypted columns; does not commit the transaction.

    No plaintext is returned or logged. Any invalid ciphertext aborts the
    operation so the caller can roll back rather than silently skip a secret.
    """
    new_fernet = Fernet(new_primary_key.encode())
    old_fernets = [Fernet(key.encode()) for key in old_keys if key and key != new_primary_key]
    if not old_fernets:
        raise ValueError("At least one distinct old encryption key is required.")
    cipher = MultiFernet([new_fernet, *old_fernets])

    counts = {"broker_connections": 0, "platform_settings": 0, "users": 0}
    broker_fields = (
        "api_key_encrypted",
        "api_secret_encrypted",
        "access_token_encrypted",
        "analytics_token_encrypted",
    )
    for row in db.query(BrokerConnection).yield_per(200):
        changed = False
        for field in broker_fields:
            value = getattr(row, field)
            if value:
                setattr(row, field, cipher.rotate(value.encode()).decode())
                changed = True
        if changed:
            counts["broker_connections"] += 1

    for row in db.query(PlatformSetting).yield_per(200):
        row.value_encrypted = cipher.rotate(row.value_encrypted.encode()).decode()
        counts["platform_settings"] += 1

    for row in db.query(User).filter(User.mfa_secret_encrypted.isnot(None)).yield_per(200):
        row.mfa_secret_encrypted = cipher.rotate(row.mfa_secret_encrypted.encode()).decode()
        counts["users"] += 1

    db.flush()
    return counts
