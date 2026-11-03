from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
import redis

from app.core.config import settings
from app.core.deps import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "database": db_ok}


@router.get("/ready")
def readiness(db: Session = Depends(get_db)):
    """Return readiness only when both durable storage and Redis are reachable.

    This endpoint intentionally exposes dependency booleans only: never return
    connection strings, exception text, credentials, or infrastructure details.
    Bounded Redis socket timeouts keep an unavailable cache from hanging probes.
    """
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    redis_ok = False
    client = None
    try:
        client = redis.Redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        redis_ok = bool(client.ping())
    except Exception:
        redis_ok = False
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                redis_ok = False

    ready = db_ok and redis_ok
    return JSONResponse(
        status_code=200 if ready else 503,
        content={
            "status": "ready" if ready else "not_ready",
            "database": db_ok,
            "redis": redis_ok,
        },
    )
