"""
Middlewares — run on every incoming message/callback before handlers.
"""
import time
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from loguru import logger

from database import get_session, UserRepo
from config import config


class AuthMiddleware(BaseMiddleware):
    """
    Checks the database for the user on every request.
    Blocks access if the user is banned.
    Injects db_user into handler data as data["user"].
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        tg_user = data.get("event_from_user")
        if not tg_user:
            return await handler(event, data)

        data["is_admin"] = tg_user.id in config.bot.admin_ids

        async with get_session() as session:
            db_user = await UserRepo.get(session, tg_user.id)

            if db_user and db_user.is_blocked:
                lang = db_user.language
                msg = (
                    "⛔ Sizning akkauntingiz bloklangan.\nAdmin bilan bog'laning."
                    if lang == "uz" else
                    "⛔ Ваш аккаунт заблокирован.\nСвяжитесь с администратором."
                )
                if isinstance(event, Message):
                    await event.answer(msg)
                elif isinstance(event, CallbackQuery):
                    await event.answer(msg, show_alert=True)
                return

            data["user"] = db_user

        return await handler(event, data)


class LanguageMiddleware(BaseMiddleware):
    """
    Reads the user's language from db and injects it as data["lang"].
    Falls back to "uz" if user is not registered yet.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        db_user = data.get("user")
        data["lang"] = db_user.language if db_user else "uz"
        return await handler(event, data)


class ThrottlingMiddleware(BaseMiddleware):
    """
    Simple in-process rate limiter — 1 request per second per user.
    Uses a local dict so it works without Redis.
    Admins are never throttled.
    """
    RATE_LIMIT = 1.0  # seconds

    def __init__(self) -> None:
        self._last_call: Dict[int, float] = defaultdict(float)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        tg_user = data.get("event_from_user")
        if not tg_user:
            return await handler(event, data)

        if tg_user.id in config.bot.admin_ids:
            return await handler(event, data)

        now = time.monotonic()
        last = self._last_call[tg_user.id]
        if now - last < self.RATE_LIMIT:
            if isinstance(event, Message):
                await event.answer("⏳ Biroz kutib turing...")
            elif isinstance(event, CallbackQuery):
                await event.answer("⏳", show_alert=False)
            return

        self._last_call[tg_user.id] = now
        return await handler(event, data)
