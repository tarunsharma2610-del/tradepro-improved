from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.main import app
from app.models.broker_charge_source_component import BrokerChargeSourceComponent
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


def _upload_note(client, connection):
    response = client.post(
        f"/api/v1/broker-charge-evidence/connections/{connection.id}/contract-notes",
        files={"file": ("contract-note.bin", b"source-contract-note", "application/octet-stream")},
        data={"broker_report_reference": "CN-SOURCE-001"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_source_component_is_pending_until_different_reviewer_confirms_source(
    db_session, make_user, monkeypatch, tmp_path
):
    extractor = make_user(email="extractor@example.com")
    reviewer = make_user(email="reviewer@example.com")
    reviewer.is_admin = True
    db_session.commit()
    connection = _connection(db_session, extractor)
    monkeypatch.setattr(settings, "BROKER_CHARGE_DOCUMENT_ROOT", str(tmp_path))

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: extractor
    try:
        client = TestClient(app)
        evidence = _upload_note(client, connection)
        response = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components",
            json={
                "component_name": "brokerage",
                "source_amount": "20.00",
                "currency": "INR",
                "source_locator": "page 1, brokerage row",
            },
        )
        assert response.status_code == 201, response.text
        component = response.json()
        assert component["status"] == "PENDING_REVIEW"
        assert component["source_sha256"] == evidence["source_sha256"]
        assert component["parser_version"] == "manual-transcription-v1"

        own_review = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components/{component['id']}/review",
            json={"confirm_source_matches": True},
        )
        assert own_review.status_code == 409
        db_component = db_session.get(BrokerChargeSourceComponent, __import__("uuid").UUID(component["id"]))
        assert db_component.status == "PENDING_REVIEW"

        app.dependency_overrides[get_current_user] = lambda: reviewer
        reviewed = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components/{component['id']}/review",
            json={"confirm_source_matches": True, "review_note": "Checked amount against source page 1."},
        )
        assert reviewed.status_code == 200, reviewed.text
        assert reviewed.json()["status"] == "VERIFIED"
        assert reviewed.json()["reviewed_by_user_id"] == str(reviewer.id)
        db_session.refresh(db_component)
        assert db_component.reviewed_at is not None
        assert db_component.review_note == "Checked amount against source page 1."
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


def test_source_component_creation_fails_closed_if_document_is_tampered(
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
        evidence = _upload_note(client, connection)
        (tmp_path / evidence["id"].replace("-", "")).write_bytes(b"tampered")
        response = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components",
            json={
                "component_name": "stt",
                "source_amount": "0.00",
                "currency": "INR",
                "source_locator": "page 1, STT row",
            },
        )
        assert response.status_code == 409
        assert "integrity check failed" in response.text
        assert db_session.query(BrokerChargeSourceComponent).count() == 0
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


def test_source_component_rejects_invalid_currency_and_duplicate_component(
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
        evidence = _upload_note(client, connection)
        base = {
            "component_name": "gst",
            "source_amount": "3.60",
            "currency": "INR",
            "source_locator": "page 1, GST row",
        }
        invalid = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components",
            json={**base, "currency": "USD"},
        )
        assert invalid.status_code == 422
        first = client.post(f"/api/v1/broker-charge-evidence/{evidence['id']}/components", json=base)
        assert first.status_code == 201, first.text
        duplicate = client.post(f"/api/v1/broker-charge-evidence/{evidence['id']}/components", json=base)
        assert duplicate.status_code == 409
        assert db_session.query(BrokerChargeSourceComponent).count() == 1
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
