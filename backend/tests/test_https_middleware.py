import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.https import ProductionHTTPSMiddleware


@pytest.fixture
def protected_app():
    app = FastAPI()
    app.add_middleware(ProductionHTTPSMiddleware, enabled=True)

    @app.get("/private")
    def private():
        return {"ok": True}

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


def test_production_rejects_http_without_forwarded_https(protected_app):
    response = TestClient(protected_app).get("/private")
    assert response.status_code == 400
    assert response.text == "HTTPS is required."


def test_production_rejects_forwarded_http(protected_app):
    response = TestClient(protected_app).get("/private", headers={"X-Forwarded-Proto": "http"})
    assert response.status_code == 400


def test_production_accepts_forwarded_https(protected_app):
    response = TestClient(protected_app).get("/private", headers={"X-Forwarded-Proto": "https"})
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_health_endpoint_remains_available_for_container_healthchecks(protected_app):
    response = TestClient(protected_app).get("/health")
    assert response.status_code == 200


def test_development_middleware_can_be_disabled():
    app = FastAPI()
    app.add_middleware(ProductionHTTPSMiddleware, enabled=False)

    @app.get("/private")
    def private():
        return {"ok": True}

    assert TestClient(app).get("/private").status_code == 200
