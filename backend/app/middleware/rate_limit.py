"""
Minimal Redis-backed rate limiter. IP-keyed limiters guard unauthenticated
endpoints (login/register) where there's no user identity yet to key on.
User-keyed limiters guard authenticated endpoints where the user is the
more precise identity — multiple legitimate users can share an IP behind
NAT/a corporate proxy, but a user_id always means one account.
"""

import redis
from fastapi import Depends, HTTPException, Request, status

from app.core.config import settings
from app.core.deps import get_current_user
from app.models.user import User

_redis_client: redis.Redis | None = None


def _get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


def _check_and_increment(key: str, max_attempts: int, window_seconds: int) -> None:
    """Shared by both limiter flavors below. Fails open on Redis being
    briefly unavailable — see the module-level reasoning in
    tests/conftest.py's _clean_redis_rate_limits fixture, which exists
    specifically because this fail-open behavior is real and was
    confirmed against a live Redis, not just assumed."""
    try:
        r = _get_redis()
        count = r.incr(key)
        if count == 1:
            r.expire(key, window_seconds)
    except redis.RedisError:
        return

    if count > max_attempts:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many attempts. Try again in a few minutes.")


class RateLimiter:
    """IP-keyed — for endpoints with no authenticated user yet."""

    def __init__(self, key_prefix: str, max_attempts: int, window_seconds: int):
        self.key_prefix = key_prefix
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds

    def __call__(self, request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        _check_and_increment(f"ratelimit:{self.key_prefix}:ip:{client_ip}", self.max_attempts, self.window_seconds)


class UserRateLimiter:
    """User-keyed — for authenticated endpoints. Depends on
    get_current_user itself, so using this as a route dependency also
    enforces authentication as a side effect (harmless — every route this
    is used on already requires auth via its own explicit dependency)."""

    def __init__(self, key_prefix: str, max_attempts: int, window_seconds: int):
        self.key_prefix = key_prefix
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds

    def __call__(self, user: User = Depends(get_current_user)) -> None:
        _check_and_increment(f"ratelimit:{self.key_prefix}:user:{user.id}", self.max_attempts, self.window_seconds)


login_rate_limit = RateLimiter("login", max_attempts=10, window_seconds=300)
register_rate_limit = RateLimiter("register", max_attempts=5, window_seconds=3600)

# Order placement: generous enough for legitimate rapid manual trading,
# tight enough to stop a runaway frontend bug or script from flooding the
# broker with requests under one account.
order_rate_limit = UserRateLimiter("place_order", max_attempts=30, window_seconds=60)

# The assistant costs real money per call (the admin's own AI provider
# key) — this exists for cost control at least as much as abuse
# prevention, so it's deliberately tighter than order placement.
assistant_rate_limit = UserRateLimiter("assistant_ask", max_attempts=20, window_seconds=3600)
