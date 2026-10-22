from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.main import app
from app.models.broker_connection import BrokerConnection


def _connection(db, user):
    connection = BrokerConnection(
        user_id=user.id,
        broker="upstox",
        api_key_encrypted="encrypted-key",
        api_secret_encrypted="encrypted-secret",
        redirect_uri="https://example.invalid/callback",
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)
    return connection


def test_contract_note_upload_and_download_are_owner_scoped_and_verified(
    db_session, make_user, monkeypatch, tmp_path
):
    user = make_user()
    connection = _connection(db_session, user)
    monkeypatch.setattr(settings, "BROKER_CHARGE_DOCUMENT_ROOT", str(tmp_path))

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        client = TestClient(app)
        uploaded = client.post(
            f"/api/v1/broker-charge-evidence/connections/{connection.id}/contract-notes",
            files={"file": ("../../note.bin", b"contract-note-bytes", "application/octet-stream")},
            data={"broker_report_reference": " CN-TEST-001 "},
        )
        assert uploaded.status_code == 201, uploaded.text
        payload = uploaded.json()
        assert payload["status"] == "RECEIVED"
        assert payload["source_filename"] == "note.bin"
        assert payload["broker_report_reference"] == "CN-TEST-001"

        downloaded = client.get(f"/api/v1/broker-charge-evidence/{payload['id']}/document")
        assert downloaded.status_code == 200
        assert downloaded.content == b"contract-note-bytes"
        assert downloaded.headers["cache-control"] == "no-store"

        storage_path = tmp_path / payload["id"].replace("-", "")
        storage_path.write_bytes(b"changed-bytes")
        tampered = client.get(f"/api/v1/broker-charge-evidence/{payload['id']}/document")
        assert tampered.status_code == 409
        assert "integrity check failed" in tampered.text
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


def test_contract_note_upload_rejects_unowned_broker_connection(db_session, make_user, monkeypatch, tmp_path):
    owner = make_user(email="owner@example.com")
    other_user = make_user(email="other@example.com")
    connection = _connection(db_session, owner)
    monkeypatch.setattr(settings, "BROKER_CHARGE_DOCUMENT_ROOT", str(tmp_path))

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: other_user
    try:
        client = TestClient(app)
        response = client.post(
            f"/api/v1/broker-charge-evidence/connections/{connection.id}/contract-notes",
            files={"file": ("note.bin", b"private", "application/octet-stream")},
            data={"broker_report_reference": "CN-OTHER"},
        )
        assert response.status_code == 404
        assert list(tmp_path.iterdir()) == []
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
