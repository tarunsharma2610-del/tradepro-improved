"""Private, persistent storage and integrity verification for contract-note bytes."""
from __future__ import annotations

import hashlib
import os
import re
import tempfile
from pathlib import Path

_STORAGE_KEY_RE = re.compile(r"^[0-9a-f]{32}$")


def _document_path(root: str | Path, storage_key: str) -> Path:
    if not isinstance(storage_key, str) or not _STORAGE_KEY_RE.fullmatch(storage_key):
        raise ValueError("Invalid contract-note storage key.")
    base = Path(root).expanduser().resolve()
    candidate = (base / storage_key).resolve()
    if candidate.parent != base:
        raise ValueError("Invalid contract-note storage path.")
    return candidate


def store_document(content: bytes, *, root: str | Path, storage_key: str) -> tuple[str, int]:
    """Atomically persist bytes with private permissions; return SHA-256 and byte count."""
    if not isinstance(content, bytes) or not content:
        raise ValueError("Contract-note document must not be empty.")
    destination = _document_path(root, storage_key)
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(destination.parent, 0o700)
    fd, temporary_name = tempfile.mkstemp(prefix=".upload-", dir=str(destination.parent))
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, destination)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise
    return hashlib.sha256(content).hexdigest(), len(content)


def read_verified_document(
    *, root: str | Path, storage_key: str, expected_sha256: str, expected_size: int
) -> bytes:
    """Read only when bytes match the evidence fingerprint and recorded size."""
    path = _document_path(root, storage_key)
    try:
        content = path.read_bytes()
    except FileNotFoundError as exc:
        raise ValueError("Contract-note source document is missing.") from exc
    actual_sha256 = hashlib.sha256(content).hexdigest()
    if len(content) != expected_size or actual_sha256 != expected_sha256:
        raise ValueError("Contract-note source integrity check failed.")
    return content


def delete_document(*, root: str | Path, storage_key: str) -> None:
    """Remove a stored document using its validated opaque key."""
    path = _document_path(root, storage_key)
    try:
        path.unlink()
    except FileNotFoundError:
        pass
