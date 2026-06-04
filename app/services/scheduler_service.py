import asyncio
from datetime import datetime
from typing import Optional
import pytz
import logging
from aiogram import Bot
from sqlalchemy import select

from app.database.connection import get_db
from app.database.models import ScheduledPost
from app.utils.config import get_config
from app.utils.texts import get_texts
from app.handlers.post_handlers import publish_post

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for checking and publishing scheduled posts"""
    
    def __init__(self, bot: Bot, check_interval: int = 60):
        """
        Initialize scheduler service
        
        Args:
            bot: Bot instance
            check_interval: Check interval in seconds (default 60)
        """
        self.bot = bot
        self.check_interval = check_interval
        self._task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Start scheduler task"""
        if self._running:
            logger.warning("Scheduler already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("Scheduler service started")
    
    async def stop(self):
        """Stop scheduler task"""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Scheduler service stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self._running:
            try:
                await self._check_and_publish_posts()
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
            
            # Wait for next check
            await asyncio.sleep(self.check_interval)
    
    async def _check_and_publish_posts(self):
        """Check for posts that need to be published"""
        config = get_config()
        texts = get_texts()
        tz = pytz.timezone(config.TIMEZONE)
        current_time = datetime.now(tz).replace(tzinfo=None)
        
        db = get_db()
        async with db.get_session() as session:
            # Get unpublished posts that are due
            result = await session.execute(
                select(ScheduledPost).where(
                    ScheduledPost.published == False,
                    ScheduledPost.scheduled_time <= current_time
                )
            )
            posts_to_publish = result.scalars().all()
            
            for post in posts_to_publish:
                try:
                    # Prepare post data
                    post_data = {
                        "type": post.content_type,
                        "text": post.text,
                        "file_id": post.file_id
                    }
                    
                    # Publish post
                    success = await publish_post(self.bot, config.CHANNEL_ID, post_data, texts)
                    
                    if success:
                        # Mark as published
                        post.published = True
                        await session.commit()
                        logger.info(f"Published scheduled post {post.id}")
                        
                        # Notify admin
                        try:
                            await self.bot.send_message(
                                post.admin_id,
                                texts.get_publication_text("scheduled_published")
                            )
                        except Exception as e:
                            logger.error(f"Error notifying admin {post.admin_id}: {e}")
                    else:
                        logger.error(f"Failed to publish scheduled post {post.id}")
                        
                        # Notify admin about failure
                        try:
                            await self.bot.send_message(
                                post.admin_id,
                                texts.get_publication_text("published_error", error="Publication failed")
                            )
                        except Exception as e:
                            logger.error(f"Error notifying admin {post.admin_id}: {e}")
                        
                        # Mark as published to avoid retrying
                        post.published = True
                        await session.commit()
                        
                except Exception as e:
                    logger.error(f"Error publishing scheduled post {post.id}: {e}")
                    await session.rollback()


# Global scheduler instance
scheduler: Optional[SchedulerService] = None


async def start_scheduler(bot: Bot, check_interval: int = 60):
    """
    Start scheduler service
    
    Args:
        bot: Bot instance
        check_interval: Check interval in seconds
    """
    global scheduler
    scheduler = SchedulerService(bot, check_interval)
    await scheduler.start()


async def stop_scheduler():
    """Stop scheduler service"""
    global scheduler
    if scheduler:
        await scheduler.stop()
        scheduler = None
