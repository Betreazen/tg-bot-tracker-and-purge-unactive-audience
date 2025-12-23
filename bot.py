import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage as AiogramRedisStorage

from app.utils.config import load_config
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


async def on_startup(bot: Bot):
    """Execute on bot startup"""
    logger.info("Bot starting up...")
    
    # Load configuration
    config = load_config()
    logger.info("Configuration loaded")
    
    # Load texts
    load_texts()
    logger.info("Texts loaded")
    
    # Initialize database
    await init_db(config.DATABASE_URL)
    logger.info("Database initialized")
    
    # Initialize Redis
    await init_redis(config.REDIS_URL)
    logger.info("Redis initialized")
    
    # Start scheduler
    await start_scheduler(bot, check_interval=60)
    logger.info("Scheduler started")
    
    logger.info("Bot started successfully")


async def on_shutdown(bot: Bot):
    """Execute on bot shutdown"""
    logger.info("Bot shutting down...")
    
    # Stop scheduler
    await stop_scheduler()
    logger.info("Scheduler stopped")
    
    # Close Redis
    await close_redis()
    logger.info("Redis closed")
    
    # Close database
    await close_db()
    logger.info("Database closed")
    
    logger.info("Bot stopped successfully")


async def main():
    """Main function to run the bot"""
    # Setup logging (before loading config)
    setup_logging("logs/bot.log")
    
    # Load config
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return
    
    # Create bot instance
    bot = Bot(token=config.BOT_TOKEN)
    
    # Create Redis storage for FSM
    fsm_storage = AiogramRedisStorage.from_url(config.REDIS_URL)
    
    # Create dispatcher
    dp = Dispatcher(storage=fsm_storage)
    
    # Register routers
    # Admin router with middleware
    admin_router.message.middleware(AdminMiddleware())
    admin_router.callback_query.middleware(AdminMiddleware())
    post_router.message.middleware(AdminMiddleware())
    post_router.callback_query.middleware(AdminMiddleware())
    
    dp.include_router(admin_router)
    dp.include_router(post_router)
    dp.include_router(user_router)  # User router last (lowest priority)
    
    # Register startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Start polling
    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error during polling: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
