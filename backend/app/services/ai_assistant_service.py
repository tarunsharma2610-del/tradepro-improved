"""
The assistant only ever sees what's explicitly assembled into its context
below (positions, recent orders, relevant news) — it never has its own
access to the database or the broker. This is deliberate: it's the same
"never present fake data as real" principle as everywhere else in this
project, applied to an LLM specifically, where the failure mode is
plausible-sounding fabrication rather than an obvious bug.
"""

import httpx
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.repositories.news_repository import NewsRepository
from app.services.platform_settings_service import PlatformSettingsService

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
MODEL = "claude-sonnet-5"  # change here if the admin wants a different model — not exposed as a setting in this phase
MAX_TOKENS = 1024

SYSTEM_PROMPT = """You are a trading assistant embedded in a paper trading platform for Indian markets.

You can only see the account data explicitly given to you below — you have no other access to
the user's account, the broker, or live market prices. If something isn't in the context provided,
say so plainly rather than guessing or estimating a number.

Be concise and concrete. When discussing money, use the exact figures given, not rounded or
invented ones. This is a PAPER (simulated) trading account — never suggest real-money financial
advice, and note the simulated nature of the data if it's relevant to the question."""


class AssistantError(Exception):
    pass


class AIAssistantService:
    def __init__(self, db: Session):
        self.db = db
        self.platform_settings = PlatformSettingsService(db)

    async def ask(self, portfolio: Portfolio, question: str) -> str:
        api_key = self.platform_settings.get_decrypted("ai_provider_api_key")
        if not api_key:
            raise AssistantError("No AI provider key configured — an admin needs to set one in platform settings.")

        context = self._build_context(portfolio)
        user_message = f"{context}\n\nQuestion: {question}"

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    ANTHROPIC_API_URL,
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": ANTHROPIC_VERSION,
                        "content-type": "application/json",
                    },
                    json={
                        "model": MODEL,
                        "max_tokens": MAX_TOKENS,
                        "system": SYSTEM_PROMPT,
                        "messages": [{"role": "user", "content": user_message}],
                    },
                )
            except httpx.HTTPError as exc:
                raise AssistantError(f"Network error contacting the AI provider: {exc}")

        if resp.status_code != 200:
            raise AssistantError(f"AI provider returned an error ({resp.status_code}): {resp.text[:300]}")

        body = resp.json()
        text_blocks = [block["text"] for block in body.get("content", []) if block.get("type") == "text"]
        if not text_blocks:
            raise AssistantError("AI provider response didn't contain a text answer.")

        return "\n".join(text_blocks)

    def _build_context(self, portfolio: Portfolio) -> str:
        positions = (
            self.db.query(Position)
            .filter(Position.portfolio_id == portfolio.id, Position.quantity != 0)
            .all()
        )
        recent_orders = (
            self.db.query(Order)
            .filter(Order.portfolio_id == portfolio.id)
            .order_by(Order.placed_at.desc())
            .limit(10)
            .all()
        )

        lines = [
            f"Portfolio: {portfolio.name}",
            f"Virtual capital (starting): Rs {portfolio.virtual_capital}",
            f"Current cash balance: Rs {portfolio.cash_balance}",
            "",
            "Open positions:" if positions else "Open positions: none",
        ]
        instrument_ids = set()
        for p in positions:
            lines.append(
                f"- {p.instrument.trading_symbol}: {p.quantity} shares, avg price Rs {p.avg_price}, "
                f"realized P&L Rs {p.realized_pnl} (unrealized P&L not available — would need a live quote)"
            )
            instrument_ids.add(p.instrument_id)

        lines.append("")
        lines.append("Recent orders:" if recent_orders else "Recent orders: none")
        for o in recent_orders:
            detail = f"rejected ({o.rejection_reason})" if o.status == "REJECTED" else o.status
            lines.append(f"- {o.side} {o.quantity} {o.instrument.trading_symbol} — {detail} ({o.execution_reason.lower()})")

        if instrument_ids:
            news_items = []
            for iid in instrument_ids:
                news_items.extend(NewsRepository(self.db).list_recent(limit=3, instrument_id=iid))
            if news_items:
                lines.append("")
                lines.append("Recent news mentioning held instruments:")
                for n in news_items[:8]:
                    lines.append(f"- {n.title}")

        return "\n".join(lines)
