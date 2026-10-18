from pathlib import Path

from scripts.check_broker_write_boundary import find_violations


def test_unapproved_adapter_write_reference_is_rejected(tmp_path):
    app = tmp_path / "app"
    (app / "api").mkdir(parents=True)
    (app / "api" / "orders.py").write_text(
        "async def route(adapter):\n    return await adapter.place_order(token, payload)\n",
        encoding="utf-8",
    )

    violations = find_violations(app)

    assert len(violations) == 1
    assert "api/orders.py:2" in violations[0]
    assert "place_order" in violations[0]


def test_only_named_boundary_file_may_reference_write_methods(tmp_path):
    app = tmp_path / "app"
    (app / "services").mkdir(parents=True)
    (app / "services" / "live_broker_write_service.py").write_text(
        "async def submit(adapter):\n    return await adapter.place_order(token, payload)\n",
        encoding="utf-8",
    )

    assert find_violations(app) == []


def test_adapter_definitions_are_excluded_but_other_references_are_not(tmp_path):
    app = tmp_path / "app"
    (app / "brokers" / "upstox").mkdir(parents=True)
    (app / "brokers" / "upstox" / "adapter.py").write_text(
        "async def place_order(self, token, payload):\n    ...\n",
        encoding="utf-8",
    )
    (app / "services").mkdir(parents=True)
    (app / "services" / "recovery.py").write_text(
        "async def recover(adapter):\n    fn = adapter.cancel_order\n",
        encoding="utf-8",
    )

    violations = find_violations(app)

    assert len(violations) == 1
    assert "services/recovery.py:2" in violations[0]
    assert "cancel_order" in violations[0]
