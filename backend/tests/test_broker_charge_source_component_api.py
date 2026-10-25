from fastapi.testclient import TestClient
from decimal import Decimal
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.main import app
from app.models.broker_charge_evidence import BrokerChargeEvidence
from app.models.broker_charge_source_component import BrokerChargeSourceComponent
from app.models.broker_trade_record import BrokerTradeRecord
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


def _trade(db, connection):
    trade = BrokerTradeRecord(
        broker_connection_id=connection.id,
        broker_order_ref_id=uuid4(),
        broker_trade_id="source-component-fill-1",
        quantity=1,
        price=Decimal("100.0000"),
        side="BUY",
        instrument_token="NSE_EQ|TEST",
        exchange_timestamp="2026-10-22T10:00:00+05:30",
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return trade


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
    trade = _trade(db_session, connection)
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
            json={"confirm_source_matches": True, "eligible_fill_record_ids": [str(trade.id)]},
        )
        assert own_review.status_code == 409
        db_component = db_session.get(BrokerChargeSourceComponent, UUID(component["id"]))
        assert db_component.status == "PENDING_REVIEW"

        app.dependency_overrides[get_current_user] = lambda: reviewer
        reviewed = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components/{component['id']}/review",
            json={
                "confirm_source_matches": True,
                "eligible_fill_record_ids": [str(trade.id)],
                "rounding_policy": "largest-remainder-v1",
                "allocation_basis": "EXPLICIT_REVIEWED",
                "eligible_fill_weights": [{"fill_record_id": str(trade.id), "weight": "1"}],
                "allocation_basis": "EXPLICIT_REVIEWED",
                "eligible_fill_weights": [{"fill_record_id": str(trade.id), "weight": "1"}],
                "review_note": "Checked amount and eligible fill against source page 1.",
            },
        )
        assert reviewed.status_code == 200, reviewed.text
        assert reviewed.json()["status"] == "VERIFIED"
        assert reviewed.json()["reviewed_by_user_id"] == str(reviewer.id)
        db_session.refresh(db_component)
        assert db_component.reviewed_at is not None
        assert db_component.review_note == "Checked amount and eligible fill against source page 1."
        assert db_component.eligible_fill_ids_json == f'["{trade.id}"]'
        assert len(db_component.eligible_fill_set_sha256) == 64
        assert db_component.rounding_policy == "largest-remainder-v1"
        assert db_component.allocation_basis == "EXPLICIT_REVIEWED"
        assert db_component.eligible_fill_weights_json == f'[{{"fill_record_id":"{trade.id}","weight":"1"}}]'
        db_evidence = db_session.get(BrokerChargeEvidence, UUID(evidence["id"]))
        db_session.refresh(db_evidence)
        assert db_evidence.status == "REVIEWED"
        assert db_evidence.reviewed_by_user_id == reviewer.id
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



def test_rejected_evidence_cannot_be_corrected_in_place(
    db_session, make_user, monkeypatch, tmp_path
):
    extractor = make_user(email="revision-extractor@example.com")
    reviewer = make_user(email="revision-reviewer@example.com")
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
        base = {
            "component_name": "stt",
            "source_amount": "10.00",
            "currency": "INR",
            "source_locator": "page 1, STT row",
        }
        first = client.post(f"/api/v1/broker-charge-evidence/{evidence['id']}/components", json=base)
        assert first.status_code == 201, first.text
        assert first.json()["revision"] == 1

        app.dependency_overrides[get_current_user] = lambda: reviewer
        rejected = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components/{first.json()['id']}/reject",
            json={"confirm_source_matches": False, "review_note": "Amount did not match source."},
        )
        assert rejected.status_code == 200, rejected.text
        db_evidence = db_session.get(BrokerChargeEvidence, UUID(evidence["id"]))
        db_session.refresh(db_evidence)
        assert db_evidence.status == "REJECTED"

        # Keep rejected source evidence immutable; corrections require a new evidence record.
        app.dependency_overrides[get_current_user] = lambda: extractor
        second = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components",
            json={**base, "source_amount": "1.00"},
        )
        assert second.status_code == 409
        assert db_session.query(BrokerChargeSourceComponent).count() == 1
        original = db_session.get(BrokerChargeSourceComponent, UUID(first.json()["id"]))
        assert original.status == "REJECTED"
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)

def test_non_admin_cannot_review_another_users_contract_note(
    db_session, make_user, monkeypatch, tmp_path
):
    owner = make_user(email="source-owner-nonadmin-test@example.com")
    reviewer = make_user(email="source-reviewer-nonadmin-test@example.com")
    connection = _connection(db_session, owner)
    trade = _trade(db_session, connection)
    monkeypatch.setattr(settings, "BROKER_CHARGE_DOCUMENT_ROOT", str(tmp_path))

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: owner
    try:
        client = TestClient(app)
        evidence = _upload_note(client, connection)
        created = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components",
            json={
                "component_name": "brokerage",
                "source_amount": "20.00",
                "currency": "INR",
                "source_locator": "page 1, brokerage row",
            },
        )
        assert created.status_code == 201, created.text
        component_id = UUID(created.json()["id"])

        # A different user is not automatically authorized to review evidence
        # owned by someone else; only the platform-admin role crosses this boundary.
        app.dependency_overrides[get_current_user] = lambda: reviewer
        response = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components/{component_id}/review",
            json={
                "confirm_source_matches": True,
                "eligible_fill_record_ids": [str(trade.id)],
            },
        )
        assert response.status_code == 404
        component = db_session.get(BrokerChargeSourceComponent, component_id)
        assert component.status == "PENDING_REVIEW"
        assert component.reviewed_by_user_id is None
        assert component.eligible_fill_ids_json is None
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


def test_source_review_rejects_fill_from_another_broker_connection(
    db_session, make_user, monkeypatch, tmp_path
):
    owner = make_user(email="source-owner-fill-boundary@example.com")
    reviewer = make_user(email="source-reviewer-fill-boundary@example.com")
    reviewer.is_admin = True
    db_session.commit()
    connection = _connection(db_session, owner)
    other_owner = make_user(email="source-other-owner-fill-boundary@example.com")
    other_connection = _connection(db_session, other_owner)
    foreign_trade = _trade(db_session, other_connection)
    monkeypatch.setattr(settings, "BROKER_CHARGE_DOCUMENT_ROOT", str(tmp_path))

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: owner
    try:
        client = TestClient(app)
        evidence = _upload_note(client, connection)
        created = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components",
            json={
                "component_name": "brokerage",
                "source_amount": "20.00",
                "currency": "INR",
                "source_locator": "page 1, brokerage row",
            },
        )
        assert created.status_code == 201, created.text
        component_id = UUID(created.json()["id"])

        app.dependency_overrides[get_current_user] = lambda: reviewer
        response = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components/{component_id}/review",
            json={
                "confirm_source_matches": True,
                "eligible_fill_record_ids": [str(foreign_trade.id)],
            },
        )
        assert response.status_code == 422
        assert "evidence broker connection" in response.text
        component = db_session.get(BrokerChargeSourceComponent, component_id)
        assert component.status == "PENDING_REVIEW"
        assert component.reviewed_by_user_id is None
        assert component.eligible_fill_ids_json is None
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


def test_source_rejection_requires_same_reviewer_after_evidence_reviewed(
    db_session, make_user, monkeypatch, tmp_path
):
    owner = make_user(email="source-owner-reviewer-consistency@example.com")
    reviewer_one = make_user(email="source-reviewer-one-consistency@example.com")
    reviewer_two = make_user(email="source-reviewer-two-consistency@example.com")
    reviewer_one.is_admin = True
    reviewer_two.is_admin = True
    db_session.commit()
    connection = _connection(db_session, owner)
    trade = _trade(db_session, connection)
    monkeypatch.setattr(settings, "BROKER_CHARGE_DOCUMENT_ROOT", str(tmp_path))

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: owner
    try:
        client = TestClient(app)
        evidence = _upload_note(client, connection)
        first = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components",
            json={
                "component_name": "brokerage",
                "source_amount": "20.00",
                "currency": "INR",
                "source_locator": "page 1, brokerage row",
            },
        )
        second = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components",
            json={
                "component_name": "gst",
                "source_amount": "3.60",
                "currency": "INR",
                "source_locator": "page 1, GST row",
            },
        )
        assert first.status_code == 201, first.text
        assert second.status_code == 201, second.text

        app.dependency_overrides[get_current_user] = lambda: reviewer_one
        reviewed = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components/{first.json()['id']}/review",
            json={
                "confirm_source_matches": True,
                "eligible_fill_record_ids": [str(trade.id)],
                "rounding_policy": "largest-remainder-v1",
                "allocation_basis": "EXPLICIT_REVIEWED",
                "eligible_fill_weights": [{"fill_record_id": str(trade.id), "weight": "1"}],
            },
        )
        assert reviewed.status_code == 200, reviewed.text

        app.dependency_overrides[get_current_user] = lambda: reviewer_two
        rejected = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components/{second.json()['id']}/reject",
            json={
                "confirm_source_matches": False,
                "review_note": "Independent mismatch review.",
            },
        )
        assert rejected.status_code == 409
        assert "same authorized reviewer" in rejected.text
        pending = db_session.get(BrokerChargeSourceComponent, UUID(second.json()["id"]))
        assert pending.status == "PENDING_REVIEW"
        assert pending.reviewed_by_user_id is None
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


def test_rejecting_component_marks_evidence_rejected_and_blocks_other_reviews(
    db_session, make_user, monkeypatch, tmp_path
):
    owner = make_user(email="source-owner-terminal-reject@example.com")
    reviewer = make_user(email="source-reviewer-terminal-reject@example.com")
    reviewer.is_admin = True
    db_session.commit()
    connection = _connection(db_session, owner)
    trade = _trade(db_session, connection)
    monkeypatch.setattr(settings, "BROKER_CHARGE_DOCUMENT_ROOT", str(tmp_path))

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: owner
    try:
        client = TestClient(app)
        evidence = _upload_note(client, connection)
        components = []
        for name, amount in (("brokerage", "20.00"), ("gst", "3.60")):
            created = client.post(
                f"/api/v1/broker-charge-evidence/{evidence['id']}/components",
                json={
                    "component_name": name,
                    "source_amount": amount,
                    "currency": "INR",
                    "source_locator": f"page 1, {name} row",
                },
            )
            assert created.status_code == 201, created.text
            components.append(created.json())

        app.dependency_overrides[get_current_user] = lambda: reviewer
        rejected = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components/{components[0]['id']}/reject",
            json={
                "confirm_source_matches": False,
                "review_note": "Source component does not match the note.",
            },
        )
        assert rejected.status_code == 200, rejected.text
        db_evidence = db_session.get(BrokerChargeEvidence, UUID(evidence["id"]))
        db_session.refresh(db_evidence)
        assert db_evidence.status == "REJECTED"
        assert db_evidence.reviewed_by_user_id == reviewer.id

        # Rejected evidence is terminal: the owner cannot append a new
        # component and thereby make this evidence look reviewable again.
        app.dependency_overrides[get_current_user] = lambda: owner
        add_after_rejection = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components",
            json={
                "component_name": "stt",
                "source_amount": "10.00",
                "currency": "INR",
                "source_locator": "page 1, STT row",
            },
        )
        assert add_after_rejection.status_code == 409
        app.dependency_overrides[get_current_user] = lambda: reviewer

        blocked = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components/{components[1]['id']}/review",
            json={
                "confirm_source_matches": True,
                "eligible_fill_record_ids": [str(trade.id)],
            },
        )
        assert blocked.status_code == 409
        assert "Rejected contract-note evidence" in blocked.text
        pending = db_session.get(BrokerChargeSourceComponent, UUID(components[1]["id"]))
        assert pending.status == "PENDING_REVIEW"
        assert pending.reviewed_by_user_id is None
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)

def test_non_admin_owner_cannot_review_or_reject_component_transcribed_by_other_user(
    db_session, make_user, monkeypatch, tmp_path
):
    owner = make_user(email="source-owner-admin-gate-test@example.com")
    transcriber = make_user(email="source-transcriber-admin-gate-test@example.com")
    connection = _connection(db_session, owner)
    trade = _trade(db_session, connection)
    monkeypatch.setattr(settings, "BROKER_CHARGE_DOCUMENT_ROOT", str(tmp_path))

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: owner
    try:
        client = TestClient(app)
        evidence = _upload_note(client, connection)
        created = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components",
            json={
                "component_name": "brokerage",
                "source_amount": "20.00",
                "currency": "INR",
                "source_locator": "page 1, brokerage row",
            },
        )
        assert created.status_code == 201, created.text
        component_id = UUID(created.json()["id"])

        # Simulate a previously transcribed record whose transcriber differs
        # from the current owner/reviewer. The documented policy still requires
        # a platform administrator for either approval or rejection.
        component = db_session.get(BrokerChargeSourceComponent, component_id)
        component.extracted_by_user_id = transcriber.id
        db_session.commit()

        review = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components/{component_id}/review",
            json={
                "confirm_source_matches": True,
                "eligible_fill_record_ids": [str(trade.id)],
            },
        )
        assert review.status_code == 403, review.text

        rejection = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components/{component_id}/reject",
            json={
                "confirm_source_matches": False,
                "review_note": "Source amount needs independent administrator review.",
            },
        )
        assert rejection.status_code == 403, rejection.text

        db_session.refresh(component)
        assert component.status == "PENDING_REVIEW"
        assert component.reviewed_by_user_id is None
        evidence_row = db_session.get(BrokerChargeEvidence, UUID(evidence["id"]))
        assert evidence_row.status == "RECEIVED"
        assert evidence_row.reviewed_by_user_id is None
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)



def test_documented_upstox_charge_components_can_be_preserved_as_pending_source_evidence(
    db_session, make_user, monkeypatch, tmp_path
):
    owner = make_user(email="upstox-component-vocabulary@example.com")
    connection = _connection(db_session, owner)
    monkeypatch.setattr(settings, "BROKER_CHARGE_DOCUMENT_ROOT", str(tmp_path))

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: owner
    expected_components = {
        "transaction_charges",
        "clearing_charges",
        "ipft",
        "other_charges",
        "demat_transaction_charges",
    }
    try:
        client = TestClient(app)
        evidence = _upload_note(client, connection)
        created_names = set()
        for name in sorted(expected_components):
            response = client.post(
                f"/api/v1/broker-charge-evidence/{evidence['id']}/components",
                json={
                    "component_name": name,
                    "source_amount": "0.01",
                    "currency": "INR",
                    "source_locator": f"page 1, raw source row: {name}",
                },
            )
            assert response.status_code == 201, response.text
            created_names.add(response.json()["component_name"])
            assert response.json()["status"] == "PENDING_REVIEW"

        assert created_names == expected_components
        stored_names = {
            row.component_name
            for row in db_session.query(BrokerChargeSourceComponent)
            .filter(BrokerChargeSourceComponent.evidence_id == UUID(evidence["id"]))
            .all()
        }
        assert expected_components <= stored_names
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


def test_transaction_ipft_representation_is_persisted_and_combined_mode_rejects_separate_ipft(
    db_session, make_user, monkeypatch, tmp_path
):
    extractor = make_user(email="representation-extractor@example.com")
    reviewer = make_user(email="representation-reviewer@example.com")
    reviewer.is_admin = True
    db_session.commit()
    connection = _connection(db_session, extractor)
    trade = _trade(db_session, connection)
    monkeypatch.setattr(settings, "BROKER_CHARGE_DOCUMENT_ROOT", str(tmp_path))

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: extractor
    try:
        client = TestClient(app)
        evidence = _upload_note(client, connection)
        base = {
            "source_amount": "307.00",
            "currency": "INR",
            "source_locator": "page 1, exchange transaction charge row",
            "representation_mode": "COMBINED_TRANSACTION_AND_IPFT",
        }
        transaction = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components",
            json={**base, "component_name": "transaction_charges", "source_label": "Transaction Charges (includes IPFT)"},
        )
        ipft = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components",
            json={**base, "component_name": "ipft", "source_label": "IPFT", "source_amount": "0.01"},
        )
        assert transaction.status_code == 201, transaction.text
        assert ipft.status_code == 201, ipft.text
        assert transaction.json()["source_label"] == "Transaction Charges (includes IPFT)"
        assert transaction.json()["representation_mode"] == "COMBINED_TRANSACTION_AND_IPFT"
        assert transaction.json()["status"] == "PENDING_REVIEW"

        app.dependency_overrides[get_current_user] = lambda: reviewer
        reviewed = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components/{transaction.json()['id']}/review",
            json={
                "confirm_source_matches": True,
                "eligible_fill_record_ids": [str(trade.id)],
                "rounding_policy": "largest-remainder-v1",
                "allocation_basis": "EXPLICIT_REVIEWED",
                "eligible_fill_weights": [{"fill_record_id": str(trade.id), "weight": "1"}],
            },
        )
        assert reviewed.status_code == 409
        assert "must not also include a separate IPFT amount" in reviewed.text
        stored = db_session.get(BrokerChargeSourceComponent, UUID(transaction.json()["id"]))
        assert stored.status == "PENDING_REVIEW"
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


def test_transaction_charge_source_cannot_be_reviewed_without_representation_mode(
    db_session, make_user, monkeypatch, tmp_path
):
    extractor = make_user(email="representation-missing-extractor@example.com")
    reviewer = make_user(email="representation-missing-reviewer@example.com")
    reviewer.is_admin = True
    db_session.commit()
    connection = _connection(db_session, extractor)
    trade = _trade(db_session, connection)
    monkeypatch.setattr(settings, "BROKER_CHARGE_DOCUMENT_ROOT", str(tmp_path))

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: extractor
    try:
        client = TestClient(app)
        evidence = _upload_note(client, connection)
        created = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components",
            json={
                "component_name": "transaction_charges",
                "source_label": "Transaction Charges",
                "source_amount": "307.00",
                "currency": "INR",
                "source_locator": "page 1, exchange charge row",
            },
        )
        assert created.status_code == 201, created.text
        app.dependency_overrides[get_current_user] = lambda: reviewer
        reviewed = client.post(
            f"/api/v1/broker-charge-evidence/{evidence['id']}/components/{created.json()['id']}/review",
            json={
                "confirm_source_matches": True,
                "eligible_fill_record_ids": [str(trade.id)],
                "rounding_policy": "largest-remainder-v1",
                "allocation_basis": "EXPLICIT_REVIEWED",
                "eligible_fill_weights": [{"fill_record_id": str(trade.id), "weight": "1"}],
            },
        )
        assert reviewed.status_code == 409
        assert "representation mode must be explicitly reviewed" in reviewed.text
        stored = db_session.get(BrokerChargeSourceComponent, UUID(created.json()["id"]))
        assert stored.status == "PENDING_REVIEW"
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
