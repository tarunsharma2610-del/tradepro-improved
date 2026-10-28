"""
Bootstrap configuration.

DESIGN RULE (read this before adding a new setting here):
This file should hold ONLY the small set of secrets that must exist
before the application can talk to its own database, i.e. the
"key to the safe" secrets. Nothing else belongs here.

Everything else — broker API keys (per user), WhatsApp/Telegram/AI/News
provider keys (platform-level) — is configured through the app itself
(Settings UI) and stored encrypted in the database using
MASTER_ENCRYPTION_KEY below. See ARCHITECTURE.md, "Credential tiers".
"""

import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Tier 0: bootstrap secrets (must be env vars, no way around it) ---
    DATABASE_URL: str = "postgresql+psycopg2://trading:trading@localhost:5432/trading_platform"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = secrets.token_urlsafe(48)
    MASTER_ENCRYPTION_KEY: str = ""  # required in real deployments; see setup.sh
    # Private persistent volume mounted into API and worker containers.
    BROKER_CHARGE_DOCUMENT_ROOT: str = "/var/lib/tradepro/contract-notes"

    # --- App-level, non-secret config (fine to have sane defaults) ---
    ENVIRONMENT: str = "development"
    APP_NAME: str = "Trading Platform"
    API_V1_PREFIX: str = "/api/v1"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    JWT_ALGORITHM: str = "HS256"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Trading mode safety switch — see PAPER/LIVE separation in ARCHITECTURE.md
    # and the full safeguards design (regulatory landscape + what's actually
    # required before this could mean anything) in LIVE_TRADING_SAFEGUARDS.md.
    # This can ONLY be flipped by editing the environment and redeploying,
    # deliberately — never through the API, so live trading can never be
    # switched on by a bug, a bad setting, or a compromised admin session.
    # Nothing in this codebase currently acts on LIVE even if set — see that
    # doc for exactly why flipping this alone was never going to be enough.
    TRADING_MODE: str = "PAPER"

    # Emergency stop for automated strategy entries. Set AUTOMATED_ENTRIES_ENABLED=false
    # in the backend environment and restart the API/worker to block new entries.
    # Strategy exits remain enabled so existing positions can still be closed.
    AUTOMATED_ENTRIES_ENABLED: bool = True
    # Use Upstox's pre-trade charge calculator for paper fills; deterministic local rates remain fallback.
    UPSTOX_CHARGE_ESTIMATES_ENABLED: bool = True

    @property
    def is_live_trading_enabled(self) -> bool:
        return self.TRADING_MODE.upper() == "LIVE"


settings = Settings()
