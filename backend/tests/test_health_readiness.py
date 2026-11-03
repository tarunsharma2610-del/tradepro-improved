from app.api.v1 import health


class _HealthyDatabase:
    def execute(self, _statement):
        return 1


class _UnavailableDatabase:
    def execute(self, _statement):
        raise RuntimeError("private database connection detail")


class _HealthyRedis:
    def ping(self):
        return True

    def close(self):
        return None


class _UnavailableRedis:
    def ping(self):
        raise RuntimeError("private redis connection detail")

    def close(self):
        return None


def test_readiness_is_healthy_only_when_database_and_redis_are_available(monkeypatch):
    monkeypatch.setattr(health.redis.Redis, "from_url", lambda *args, **kwargs: _HealthyRedis())

    response = health.readiness(db=_HealthyDatabase())

    assert response.status_code == 200
    assert response.body == b'{"status":"ready","database":true,"redis":true}'


def test_readiness_returns_503_when_database_is_unavailable(monkeypatch):
    monkeypatch.setattr(health.redis.Redis, "from_url", lambda *args, **kwargs: _HealthyRedis())

    response = health.readiness(db=_UnavailableDatabase())

    assert response.status_code == 503
    assert b'"database":false' in response.body
    assert b'"redis":true' in response.body
    assert b"private database connection detail" not in response.body


def test_readiness_returns_503_when_redis_is_unavailable(monkeypatch):
    monkeypatch.setattr(health.redis.Redis, "from_url", lambda *args, **kwargs: _UnavailableRedis())

    response = health.readiness(db=_HealthyDatabase())

    assert response.status_code == 503
    assert b'"database":true' in response.body
    assert b'"redis":false' in response.body
    assert b"private redis connection detail" not in response.body


def test_readiness_closes_redis_client(monkeypatch):
    client = _HealthyRedis()
    closed = []
    client.close = lambda: closed.append(True)
    monkeypatch.setattr(health.redis.Redis, "from_url", lambda *args, **kwargs: client)

    response = health.readiness(db=_HealthyDatabase())

    assert response.status_code == 200
    assert closed == [True]
