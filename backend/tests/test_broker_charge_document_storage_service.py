import hashlib

import pytest

from app.services.broker_charge_document_storage_service import (
    delete_document,
    read_verified_document,
    store_document,
)


def test_store_and_read_document_verifies_bytes_and_size(tmp_path):
    original = b"%PDF-1.7\ncontract note fixture\n"
    key = "a" * 32

    digest, size = store_document(original, root=tmp_path, storage_key=key)

    assert digest == hashlib.sha256(original).hexdigest()
    assert size == len(original)
    assert read_verified_document(
        root=tmp_path, storage_key=key, expected_sha256=digest, expected_size=size
    ) == original
    assert (tmp_path / key).stat().st_mode & 0o777 == 0o600


def test_read_rejects_modified_document(tmp_path):
    key = "b" * 32
    digest, size = store_document(b"original", root=tmp_path, storage_key=key)
    (tmp_path / key).write_bytes(b"tampered")

    with pytest.raises(ValueError, match="integrity check failed"):
        read_verified_document(root=tmp_path, storage_key=key, expected_sha256=digest, expected_size=size)


def test_read_rejects_missing_document(tmp_path):
    with pytest.raises(ValueError, match="document is missing"):
        read_verified_document(
            root=tmp_path, storage_key="c" * 32, expected_sha256="0" * 64, expected_size=1
        )


@pytest.mark.parametrize("key", ["../outside", "/etc/passwd", "not-a-uuid", "d" * 31])
def test_storage_key_rejects_path_traversal(tmp_path, key):
    with pytest.raises(ValueError, match="storage key"):
        read_verified_document(root=tmp_path, storage_key=key, expected_sha256="0" * 64, expected_size=1)


def test_empty_document_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="must not be empty"):
        store_document(b"", root=tmp_path, storage_key="e" * 32)


def test_delete_uses_validated_storage_key(tmp_path):
    key = "f" * 32
    store_document(b"source", root=tmp_path, storage_key=key)
    delete_document(root=tmp_path, storage_key=key)
    assert not (tmp_path / key).exists()
