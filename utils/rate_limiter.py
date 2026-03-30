"""
Rate Limiter Middleware - Lucien Bot

In-memory sliding window rate limiter per user_id.
No external dependencies. Single-instance only.
"""
import os
import time
import logging
from typing import Any
from collections import defaultdict
from dataclasses import dataclass, field
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
from aiogram.dispatcher.flags import get_flag

logger = logging.getLogger(__name__)

# Config from env with defaults (per user decisions)
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "5"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))


@dataclass
class SlidingWindow:
    """Sliding window tracker for a single user."""
    timestamps: list = field(default_factory=list)

    def is_allowed(self, max_requests: int, window_seconds: int) -> bool:
        now = time.time()
        cutoff = now - window_seconds
        # Remove expired timestamps
        self.timestamps = [ts for ts in self.timestamps if ts > cutoff]
        if len(self.timestamps) >= max_requests:
            return False
        self.timestamps.append(now)
        return True


class RateLimitMiddleware(BaseMiddleware):
    """
    aiogram middleware that rate limits users on protected commands.

    Usage:
        from utils.rate_limiter import RateLimitMiddleware
        dp.middleware.setup(RateLimitMiddleware())
    """

    def __init__(self):
        self._windows: dict[int, SlidingWindow] = defaultdict(SlidingWindow)

    async def __call__(
        self,
        handler,
        event: TelegramObject,
        data: dict,
    ) -> Any:
        user: TgUser | None = data.get("user")
        if not user:
            return await handler(event, data)

        # Check if this handler is marked as rate-limited
        is_protected = get_flag(data, "rate_limited")
        if not is_protected:
            return await handler(event, data)

        user_id = user.id
        window = self._windows[user_id]
        allowed = window.is_allowed(RATE_LIMIT_MAX, RATE_LIMIT_WINDOW)

        if not allowed:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            # Send rate limit message via bot
            bot = data.get("bot")
            if bot and hasattr(event, "answer"):
                try:
                    await event.answer(
                        "🎩 <b>Lucien:</b>\n\n"
                        "<i>El ritmo de tus peticiones excede los límites que Diana permite. "
                        "Respira... y vuelve a intentarlo en un momento.</i>",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
            return  # Block the handler

        return await handler(event, data)


from aiogram.dispatcher.flags import FlagGenerator


def _rate_limited_impl(value: bool = True):
    """Returns a decorator that marks a handler as rate-limited."""
    flag = FlagGenerator()
    # Access the attribute to get FlagDecorator, then call it
    return getattr(flag, "rate_limited")(value)


def rate_limited():
    """Decorator to mark a handler as rate-limited."""
    return _rate_limited_impl(True)
