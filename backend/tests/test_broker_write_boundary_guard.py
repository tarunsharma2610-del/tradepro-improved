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


def test_central_boundary_must_not_call_adapter_until_reviewed(tmp_path):
    app = tmp_path / "app"
    (app / "services").mkdir(parents=True)
    (app / "services" / "live_broker_write_service.py").write_text(
        "async def submit(adapter):\n    return await adapter.place_order(token, payload)\n",
        encoding="utf-8",
    )

    violations = find_violations(app)
    assert len(violations) == 1
    assert "services/live_broker_write_service.py:2" in violations[0]


def test_adapter_definitions_need_no_file_wide_exemption(tmp_path):
    app = tmp_path / "app"
    adapter = app / "brokers" / "upstox"
    adapter.mkdir(parents=True)
    (adapter / "adapter.py").write_text(
        "async def place_order(self, token, payload):\n    ...\n"
        "async def recovery(self, client):\n    return client.cancel_order(token, order)\n",
        encoding="utf-8",
    )

    violations = find_violations(app)
    assert len(violations) == 1
    assert "brokers/upstox/adapter.py:4" in violations[0]
    assert "cancel_order" in violations[0]


def test_docstring_mentions_are_not_treated_as_adapter_calls(tmp_path):
    app = tmp_path / "app"
    (app / "services").mkdir(parents=True)
    (app / "services" / "preflight.py").write_text(
        '\'\'\'Never call adapter.place_order from preflight.\'\'\'\n'
        "def check():\n    return True\n",
        encoding="utf-8",
    )

    assert find_violations(app) == []


def test_generic_receiver_cannot_bypass_broker_write_guard(tmp_path):
    app = tmp_path / "app"
    (app / "services").mkdir(parents=True)
    (app / "services" / "unexpected.py").write_text(
        "async def submit(client):\n    return await client.place_order(token, payload)\n",
        encoding="utf-8",
    )

    violations = find_violations(app)

    assert len(violations) == 1
    assert "unexpected.py:2" in violations[0]


def test_known_paper_execution_service_call_is_allowed(tmp_path):
    app = tmp_path / "app"
    (app / "services").mkdir(parents=True)
    (app / "services" / "strategy_execution_service.py").write_text(
        "async def submit(self, user, request):\n    return await self.execution.place_order(user, request)\n",
        encoding="utf-8",
    )

    assert find_violations(app) == []


def test_known_paper_http_order_endpoints_are_allowed(tmp_path):
    app = tmp_path / "app"
    (app / "api" / "v1").mkdir(parents=True)
    (app / "api" / "v1" / "portfolios.py").write_text(
        "async def place_order(payload):\n    service = ExecutionService(db)\n    return await service.place_order(token, payload)\n"
        "def cancel_order(ExecutionService, db):\n    return ExecutionService(db).cancel_order(user, portfolio, order)\n",
        encoding="utf-8",
    )

    assert find_violations(app) == []


def test_same_file_cannot_hide_write_reference_in_unapproved_function(tmp_path):
    app = tmp_path / "app"
    (app / "api" / "v1").mkdir(parents=True)
    (app / "api" / "v1" / "portfolios.py").write_text(
        "async def place_order(payload):\n    service = ExecutionService(db)\n    return await service.place_order(token, payload)\n"
        "async def unrelated_helper(client):\n    return await client.cancel_order(token, order)\n",
        encoding="utf-8",
    )

    violations = find_violations(app)
    assert len(violations) == 1
    assert "portfolios.py:5" in violations[0]
