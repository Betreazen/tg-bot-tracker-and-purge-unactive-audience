from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram import Bot
import logging

from app.database.connection import get_db
from app.services.user_service import UserService
from app.utils.config import get_config
from app.utils.texts import get_texts

logger = logging.getLogger(__name__)

user_router = Router()


async def check_subscription(bot: Bot, user_id: int, channel_id: int, max_retries: int = 3) -> bool:
    """
    Check if user is subscribed to the channel with retry logic
    
    Args:
        bot: Bot instance
        user_id: User ID
        channel_id: Channel ID
        max_retries: Maximum number of retry attempts
        
    Returns:
        True if user is subscribed
    """
    for attempt in range(max_retries):
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            # Member status can be: creator, administrator, member, restricted, left, kicked
            is_subscribed = member.status in ["creator", "administrator", "member", "restricted"]
            logger.info(f"Subscription check for user {user_id}: {is_subscribed} (status: {member.status})")
            return is_subscribed
        except Exception as e:
            logger.error(f"Error checking subscription for user {user_id} (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                # Last attempt failed
                return False
    return False


@user_router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    """Handle /start command"""
    config = get_config()
    texts = get_texts()
    user = message.from_user
    
    if not user:
        return
    
    # Check if user is admin - show them how to access admin panel
    if config.is_admin(user.id):
        await message.answer(
            "👋 Добро пожаловать, администратор!\n\n"
            "Используйте команду /admin для доступа к панели управления."
        )
        logger.info(f"Admin {user.id} used /start command")
        return
    
    logger.info(f"User {user.id} started bot")
    
    # Check subscription
    is_subscribed = await check_subscription(bot, user.id, config.CHANNEL_ID)
    
    if not is_subscribed:
        # User is not subscribed - send notification and don't save
        await message.answer(
            texts.get_user_text("not_subscribed", channel_username=config.CHANNEL_USERNAME)
        )
        logger.info(f"User {user.id} is not subscribed to channel")
        return
    
    # User is subscribed - save/update user data
    db = get_db()
    async with db.get_session() as session:
        try:
            await UserService.create_or_update_user(
                session=session,
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            # Check if this is first time user
            existing_user = await UserService.get_user(session, user.id)
            if existing_user and existing_user.first_seen_at == existing_user.last_seen_at:
                # First time user
                await message.answer(texts.get_user_text("welcome"))
            else:
                # Returning user
                await message.answer(texts.get_user_text("activity_confirmed"))
                
        except Exception as e:
            logger.error(f"Error processing user {user.id}: {e}")
            await message.answer(texts.get_error_text("database"))


@user_router.message(F.text)
async def handle_any_message(message: Message, bot: Bot):
    """Handle any text message from user"""
    config = get_config()
    texts = get_texts()
    user = message.from_user
    
    if not user:
        return
    
    # Check if user is admin - admins are handled by different router
    if config.is_admin(user.id):
        return
    
    logger.info(f"User {user.id} sent message")
    
    # Check subscription
    is_subscribed = await check_subscription(bot, user.id, config.CHANNEL_ID)
    
    if not is_subscribed:
        await message.answer(
            texts.get_user_text("not_subscribed", channel_username=config.CHANNEL_USERNAME)
        )
        return
    
    # User is subscribed - update user data
    db = get_db()
    async with db.get_session() as session:
        try:
            await UserService.create_or_update_user(
                session=session,
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            await message.answer(texts.get_user_text("activity_confirmed"))
        except Exception as e:
            logger.error(f"Error processing user {user.id}: {e}")


@user_router.callback_query(F.data == "user_action")
async def handle_any_callback(callback_query, bot: Bot):
    """Handle any callback query from user"""
    config = get_config()
    texts = get_texts()
    user = callback_query.from_user
    
    if not user:
        return
    
    # Check if user is admin
    if config.is_admin(user.id):
        return
    
    logger.info(f"User {user.id} sent callback")
    
    # Check subscription
    is_subscribed = await check_subscription(bot, user.id, config.CHANNEL_ID)
    
    if not is_subscribed:
        await callback_query.answer(
            texts.get_user_text("not_subscribed", channel_username=config.CHANNEL_USERNAME),
            show_alert=True
        )
        return
    
    # User is subscribed - update user data
    db = get_db()
    async with db.get_session() as session:
        try:
            await UserService.create_or_update_user(
                session=session,
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            await callback_query.answer(texts.get_user_text("activity_confirmed"))
        except Exception as e:
            logger.error(f"Error processing user {user.id}: {e}")
            await callback_query.answer()
