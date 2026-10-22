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


import hashlib
from types import SimpleNamespace

from app.services.broker_charge_document_storage_service import (
    audit_contract_note_storage,
    store_document,
)


def test_storage_audit_reports_clean_store_without_mutating_files(tmp_path, db_session, make_user):
    from app.models.broker_charge_evidence import BrokerChargeEvidence
    from app.models.broker_connection import BrokerConnection

    user = make_user()
    connection = BrokerConnection(user_id=user.id, broker="upstox", api_key_encrypted="test-key", api_secret_encrypted="test-secret", redirect_uri="http://localhost/callback")
    db_session.add(connection)
    db_session.commit()
    key = "a" * 32
    content = b"contract note"
    digest, size = store_document(content, root=tmp_path, storage_key=key)
    row = BrokerChargeEvidence(
        broker_connection_id=connection.id,
        source_kind="CONTRACT_NOTE",
        source_filename="note.pdf",
        storage_key=key,
        source_sha256=digest,
        byte_size=size,
        received_by_user_id=user.id,
        status="RECEIVED",
    )
    db_session.add(row)
    db_session.commit()

    result = audit_contract_note_storage(db=db_session, root=tmp_path)
    assert result == {
        "missing_files": [],
        "integrity_mismatches": [],
        "invalid_storage_keys": [],
        "unreferenced_files": [],
    }
    assert (tmp_path / key).read_bytes() == content


def test_storage_audit_reports_missing_tampered_and_orphan_files_without_deleting(tmp_path, db_session, make_user):
    from app.models.broker_charge_evidence import BrokerChargeEvidence
    from app.models.broker_connection import BrokerConnection

    user = make_user()
    connection = BrokerConnection(user_id=user.id, broker="UPSTOX", name="test")
    db_session.add(connection)
    db_session.commit()

    missing_key = "b" * 32
    bad_key = "c" * 32
    orphan_key = "d" * 32
    (tmp_path / bad_key).write_bytes(b"tampered")
    (tmp_path / orphan_key).write_bytes(b"orphan")
    for key, content in ((missing_key, b"missing"), (bad_key, b"original")):
        db_session.add(BrokerChargeEvidence(
            broker_connection_id=connection.id,
            source_kind="CONTRACT_NOTE",
            source_filename="note.pdf",
            storage_key=key,
            source_sha256=hashlib.sha256(content).hexdigest(),
            byte_size=len(content),
            received_by_user_id=user.id,
            status="RECEIVED",
        ))
    db_session.commit()

    result = audit_contract_note_storage(db=db_session, root=tmp_path)
    assert [item["storage_key"] for item in result["missing_files"]] == [missing_key]
    assert [item["storage_key"] for item in result["integrity_mismatches"]] == [bad_key]
    assert [item["storage_key"] for item in result["unreferenced_files"]] == [orphan_key]
    assert (tmp_path / bad_key).read_bytes() == b"tampered"
    assert (tmp_path / orphan_key).read_bytes() == b"orphan"
