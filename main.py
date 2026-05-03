import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from config import config, setup_logging
from database import create_tables
from bot.handlers import main_router
from bot.middlewares.auth import AuthMiddleware, LanguageMiddleware, ThrottlingMiddleware
from bot.utils.scheduler import setup_scheduler


async def main() -> None:
    setup_logging(config.log_level)
    logger.info("Starting Pochta Bot...")

    if not config.bot.token or config.bot.token == "your_bot_token_here":
        logger.error("BOT_TOKEN is not set. Copy .env.example to .env and fill it in.")
        sys.exit(1)

    # Try Redis for FSM storage, fall back to in-memory
    storage = MemoryStorage()
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(config.redis.url, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        from aiogram.fsm.storage.redis import RedisStorage
        storage = RedisStorage.from_url(config.redis.url)
        logger.info("Redis FSM storage connected: {}", config.redis.url)
    except Exception:
        logger.warning("Redis not available — using MemoryStorage for FSM")

    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=storage)

    # Register middlewares — order matters
    throttling = ThrottlingMiddleware()
    dp.message.middleware(throttling)
    dp.message.middleware(AuthMiddleware())
    dp.message.middleware(LanguageMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    dp.callback_query.middleware(LanguageMiddleware())

    dp.include_router(main_router)

    try:
        await create_tables()
        logger.info("Database ready")
    except Exception as e:
        logger.error("DB setup error: {}", e)
        logger.warning("Continuing without database — some features may not work")

    try:
        setup_scheduler(bot)
        logger.info("Scheduler started")
    except Exception as e:
        logger.warning("Scheduler failed to start: {}", e)

    if config.run_mode == "webhook" and config.webhook.url:
        from aiohttp import web
        from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

        webhook_url = f"{config.webhook.url}{config.webhook.path}"
        await bot.set_webhook(webhook_url)
        logger.info("Webhook set: {}", webhook_url)

        app = web.Application()
        SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=config.webhook.path)
        setup_application(app, dp, bot=bot)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host="0.0.0.0", port=config.webhook.port)
        await site.start()
        logger.info("Webhook server running on port {}", config.webhook.port)
        await asyncio.Event().wait()
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot started in polling mode. Send /start in Telegram.")
        try:
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        finally:
            await bot.session.close()
            logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped by user (Ctrl+C)")
        sys.exit(0)
