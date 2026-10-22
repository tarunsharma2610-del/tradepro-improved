import os
import uuid

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["MASTER_ENCRYPTION_KEY"] = "HuszwzTH0J4Uzhmkxh7WgSPUoZMkwOZDHZFlAZA-u24="  # test-only, not a real key
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
import app.models  # noqa: F401  (imports every model class -- registers all of them on Base.metadata; do not shrink this back down to a single-model import)
from app.models.user import User


@pytest.fixture(autouse=True)
def _clean_redis_rate_limits():
    """Without this, tests that hit real HTTP auth endpoints would share
    one rate-limit bucket (keyed by the test client's fixed fake IP)
    across the whole session if a real Redis happens to be reachable at
    the default URL -- enough registrations across the suite would trip
    the real limit, and a later test's login would legitimately 401
    because its registration got rate-limited, not because anything is
    broken. Confirmed by validating this suite against a real Postgres +
    Redis stack, where this exact thing happened before this fixture
    existed. Fails open (does nothing) if Redis isn't reachable, matching
    the application code's own fail-open behavior -- this suite passes the
    same way whether or not a local Redis happens to be running."""
    import redis

    try:
        redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True).flushdb()
    except redis.RedisError:
        pass
    yield


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    # SQLite's legacy driver mode may not emit a real BEGIN before SAVEPOINT.
    # Force explicit transaction boundaries so nested savepoint rollback tests
    # behave like the caller-owned transaction contract expected by services.
    @event.listens_for(engine, "connect")
    def _configure_sqlite_transaction_boundaries(dbapi_connection, _connection_record):
        dbapi_connection.isolation_level = None

    @event.listens_for(engine, "begin")
    def _begin_sqlite_transaction(connection):
        connection.exec_driver_sql("BEGIN")

    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def make_user(db_session):
    def _make(email: str = "tester@example.com", is_admin: bool = False) -> User:
        from app.core.security import hash_password

        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=hash_password("correct-horse-battery-staple"),
            full_name="Test User",
            is_admin=is_admin,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make
