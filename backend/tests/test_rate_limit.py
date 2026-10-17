from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.middleware.rate_limit import UserRateLimiter, _check_and_increment


class _FakeRedis:
    """Minimal in-memory stand-in for the two Redis calls this module
    actually uses — a real Redis is exercised separately, see the
    infrastructure validation notes in README.md; this tests the
    threshold/expiry logic in isolation and fast."""

    def __init__(self):
        self.counts: dict[str, int] = {}

    def incr(self, key: str) -> int:
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    def expire(self, key: str, seconds: int) -> None:
        pass


def test_allows_requests_under_the_limit():
    fake = _FakeRedis()
    with patch("app.middleware.rate_limit._get_redis", return_value=fake):
        for _ in range(5):
            _check_and_increment("test:key", max_attempts=5, window_seconds=60)  # should not raise


def test_blocks_requests_over_the_limit():
    fake = _FakeRedis()
    with patch("app.middleware.rate_limit._get_redis", return_value=fake):
        for _ in range(5):
            _check_and_increment("test:key2", max_attempts=5, window_seconds=60)
        with pytest.raises(HTTPException) as exc_info:
            _check_and_increment("test:key2", max_attempts=5, window_seconds=60)

    assert exc_info.value.status_code == 429


def test_different_keys_have_independent_counters():
    fake = _FakeRedis()
    with patch("app.middleware.rate_limit._get_redis", return_value=fake):
        for _ in range(5):
            _check_and_increment("test:user-a", max_attempts=5, window_seconds=60)
        # A different key (e.g. a different user_id) starts fresh, unaffected by user-a's count.
        _check_and_increment("test:user-b", max_attempts=5, window_seconds=60)  # should not raise


def test_fails_open_when_redis_is_unavailable():
    import redis as redis_module

    with patch("app.middleware.rate_limit._get_redis", side_effect=redis_module.RedisError("down")):
        _check_and_increment("test:whatever", max_attempts=1, window_seconds=60)  # should not raise


def test_user_rate_limiter_keys_by_user_id_not_ip():
    """Confirms the actual key construction includes the user id — the
    whole point of UserRateLimiter over the IP-based RateLimiter."""
    fake = _FakeRedis()
    limiter = UserRateLimiter("test_action", max_attempts=3, window_seconds=60)
    fake_user = MagicMock()
    fake_user.id = "user-123"

    with patch("app.middleware.rate_limit._get_redis", return_value=fake):
        limiter(user=fake_user)

    assert any("user-123" in key for key in fake.counts)
