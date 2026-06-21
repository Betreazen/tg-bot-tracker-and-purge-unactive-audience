import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage as AiogramRedisStorage, DefaultKeyBuilder
from aiogram.exceptions import (
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramUnauthorizedError,
)

from app.utils.config import load_config, get_config
from app.utils.logger import setup_logging
from app.utils.texts import load_texts
from app.database.connection import init_db, close_db
from app.utils.redis_storage import init_redis, close_redis
from app.services.scheduler_service import start_scheduler, stop_scheduler

from app.handlers.user_handlers import user_router
from app.handlers.admin_handlers import admin_router
from app.handlers.post_handlers import post_router
from app.middlewares.admin_middleware import AdminMiddleware

logger = logging.getLogger(__name__)

# Максимальная задержка между попытками переподключения polling (секунды)
MAX_POLLING_BACKOFF = 60


async def on_startup(bot: Bot):
    """Execute on bot startup. Config/texts are already loaded in main()."""
    logger.info("Bot starting up...")
    config = get_config()

    # Initialize database (with internal retry — устойчиво к ещё не поднятой БД)
    await init_db(config.DATABASE_URL)
    logger.info("Database initialized")

    # Initialize Redis (namespace = bot id → изоляция данных при общем Redis)
    await init_redis(config.REDIS_URL, namespace=f"bot:{bot.id}")
    logger.info("Redis initialized")

    # Start scheduler
    await start_scheduler(bot, check_interval=60)
    logger.info("Scheduler started")

    logger.info("Bot started successfully")


async def on_shutdown(bot: Bot):
    """Execute on bot shutdown"""
    logger.info("Bot shutting down...")

    await stop_scheduler()
    logger.info("Scheduler stopped")

    await close_redis()
    logger.info("Redis closed")

    await close_db()
    logger.info("Database closed")

    logger.info("Bot stopped successfully")


def build_dispatcher(config) -> Dispatcher:
    """Create dispatcher with Redis FSM storage namespaced per bot."""
    # with_bot_id/with_destiny — изолируют FSM-состояния по конкретному боту,
    # чтобы даже при общем Redis состояния разных ботов не пересекались.
    fsm_storage = AiogramRedisStorage.from_url(
        config.REDIS_URL,
        key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True),
    )

    dp = Dispatcher(storage=fsm_storage)

    # Admin routers with middleware
    admin_router.message.middleware(AdminMiddleware())
    admin_router.callback_query.middleware(AdminMiddleware())
    post_router.message.middleware(AdminMiddleware())
    post_router.callback_query.middleware(AdminMiddleware())

    dp.include_router(admin_router)
    dp.include_router(post_router)
    dp.include_router(user_router)  # User router last (lowest priority)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    return dp


async def main():
    """Main function to run the bot"""
    # Setup logging first
    setup_logging("logs/bot.log")

    # Load config and texts once (fail fast on misconfiguration)
    try:
        config = load_config()
        load_texts()
    except Exception as e:
        logger.critical(f"Failed to load configuration/texts: {e}")
        return

    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties())
    dp = build_dispatcher(config)

    # Supervisor loop: переживает сетевые сбои Telegram без падения контейнера.
    backoff = 1
    try:
        while True:
            try:
                logger.info("Starting bot polling...")
                await dp.start_polling(bot, handle_signals=True)
                # Чистый выход (получен сигнал остановки) — выходим из цикла.
                logger.info("Polling finished cleanly")
                break
            except TelegramUnauthorizedError:
                # Неверный/отозванный токен — ретраить бессмысленно, падаем громко.
                logger.critical("Bot token is invalid or revoked. Check BOT_TOKEN. Exiting.")
                break
            except (TelegramNetworkError, TelegramRetryAfter) as e:
                logger.warning(f"Network error during polling, retrying in {backoff}s: {e}")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, MAX_POLLING_BACKOFF)
            except asyncio.CancelledError:
                logger.info("Polling cancelled, shutting down")
                raise
            except Exception as e:
                logger.exception(f"Unexpected error during polling, retrying in {backoff}s: {e}")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, MAX_POLLING_BACKOFF)
            else:
                backoff = 1
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.getLogger(__name__).info("Bot stopped by user/system")
