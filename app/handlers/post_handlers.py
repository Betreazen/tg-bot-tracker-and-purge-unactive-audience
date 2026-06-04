from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
from datetime import datetime
from calendar import monthrange
import pytz

from app.database.connection import get_db
from app.database.models import ScheduledPost
from app.services.user_service import UserService
from app.utils.texts import get_texts
from app.utils.redis_storage import get_redis
from app.utils.config import get_config

logger = logging.getLogger(__name__)

post_router = Router()


class PostStates(StatesGroup):
    """States for post creation flow"""
    awaiting_content = State()
    preview = State()
    selecting_year = State()
    selecting_month = State()
    selecting_day = State()
    selecting_hour = State()


@post_router.callback_query(F.data == "admin_create_post")
async def start_post_creation(callback: CallbackQuery, state: FSMContext):
    """Start post creation process"""
    texts = get_texts()
    user_id = callback.from_user.id
    
    # Set state
    await state.set_state(PostStates.awaiting_content)
    
    # Create back button
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=texts.get_button_text("cancel"), callback_data="post_cancel")]
    ])
    
    await callback.message.edit_text(
        texts.get_post_creation_text("awaiting_content"),
        reply_markup=keyboard
    )
    await callback.answer()
    logger.info(f"Admin {user_id} started post creation")


@post_router.message(PostStates.awaiting_content)
async def receive_post_content(message: Message, state: FSMContext, bot: Bot):
    """Receive post content from admin"""
    texts = get_texts()
    redis = get_redis()
    config = get_config()
    user_id = message.from_user.id
    
    # Determine content type and extract data
    post_data = {}
    
    if message.text:
        post_data["type"] = "text"
        post_data["text"] = message.text
    elif message.photo:
        post_data["type"] = "photo"
        post_data["file_id"] = message.photo[-1].file_id
        post_data["text"] = message.caption or ""
    elif message.video:
        post_data["type"] = "video"
        post_data["file_id"] = message.video.file_id
        post_data["text"] = message.caption or ""
    elif message.animation:
        post_data["type"] = "animation"
        post_data["file_id"] = message.animation.file_id
        post_data["text"] = message.caption or ""
    else:
        await message.answer(texts.get_post_creation_text("invalid_content"))
        return
    
    # Save post data
    await redis.save_post_draft(user_id, post_data)
    
    # Show preview
    await show_post_preview(message, state, bot, post_data)


async def show_post_preview(message: Message, state: FSMContext, bot: Bot, post_data: dict):
    """Show post preview with actions"""
    texts = get_texts()
    config = get_config()
    
    # Create inline button for bot
    bot_info = await bot.get_me()
    bot_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=texts.get_button_text("open_bot"),
            url=f"https://t.me/{bot_info.username}"
        )]
    ])
    
    # Send preview
    preview_message = await message.answer(texts.get_post_creation_text("preview_title"))
    
    if post_data["type"] == "text":
        await message.answer(
            post_data["text"],
            reply_markup=bot_button
        )
    elif post_data["type"] == "photo":
        await message.answer_photo(
            post_data["file_id"],
            caption=post_data["text"] if post_data["text"] else None,
            reply_markup=bot_button
        )
    elif post_data["type"] == "video":
        await message.answer_video(
            post_data["file_id"],
            caption=post_data["text"] if post_data["text"] else None,
            reply_markup=bot_button
        )
    elif post_data["type"] == "animation":
        await message.answer_animation(
            post_data["file_id"],
            caption=post_data["text"] if post_data["text"] else None,
            reply_markup=bot_button
        )
    
    # Action buttons
    action_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=texts.get_button_text("send_now"), callback_data="post_send_now")],
        [InlineKeyboardButton(text=texts.get_button_text("schedule"), callback_data="post_schedule")],
        [InlineKeyboardButton(text=texts.get_button_text("cancel"), callback_data="post_cancel")]
    ])
    
    await message.answer(
        texts.get_post_creation_text("preview_description"),
        reply_markup=action_keyboard
    )
    
    await state.set_state(PostStates.preview)


@post_router.callback_query(F.data == "post_send_now", PostStates.preview)
async def send_post_now(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Send post immediately"""
    texts = get_texts()
    config = get_config()
    redis = get_redis()
    user_id = callback.from_user.id
    
    # Get post data
    post_data = await redis.get_post_draft(user_id)
    if not post_data:
        await callback.answer(texts.get_error_text("unknown"), show_alert=True)
        return
    
    # Publish post
    success = await publish_post(bot, config.CHANNEL_ID, post_data, texts)
    
    if success:
        await callback.message.answer(texts.get_publication_text("published_success"))
        logger.info(f"Admin {user_id} published post immediately")
    else:
        await callback.message.answer(texts.get_publication_text("published_error", error="Failed to publish"))
    
    # Clear state and draft
    await state.clear()
    await redis.clear_post_draft(user_id)
    await callback.answer()


@post_router.callback_query(F.data == "post_schedule", PostStates.preview)
async def schedule_post(callback: CallbackQuery, state: FSMContext):
    """Start scheduling flow"""
    texts = get_texts()
    config = get_config()
    
    # Get current year and next few years
    tz = pytz.timezone(config.TIMEZONE)
    current_year = datetime.now(tz).year
    
    years = [current_year, current_year + 1]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(year), callback_data=f"year_{year}")] for year in years
    ] + [[InlineKeyboardButton(text=texts.get_button_text("back"), callback_data="post_cancel")]])
    
    await callback.message.edit_text(
        texts.get_scheduling_text("select_year"),
        reply_markup=keyboard
    )
    await state.set_state(PostStates.selecting_year)
    await callback.answer()


@post_router.callback_query(F.data.startswith("year_"), PostStates.selecting_year)
async def select_year(callback: CallbackQuery, state: FSMContext):
    """Select year"""
    texts = get_texts()
    year = int(callback.data.split("_")[1])
    
    await state.update_data(year=year)
    
    # Show months
    months = [
        ("Январь", 1), ("Февраль", 2), ("Март", 3), ("Апрель", 4),
        ("Май", 5), ("Июнь", 6), ("Июль", 7), ("Август", 8),
        ("Сентябрь", 9), ("Октябрь", 10), ("Ноябрь", 11), ("Декабрь", 12)
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=months[i][0], callback_data=f"month_{months[i][1]}"),
            InlineKeyboardButton(text=months[i+1][0], callback_data=f"month_{months[i+1][1]}")
        ] for i in range(0, 12, 2)
    ] + [[InlineKeyboardButton(text=texts.get_button_text("back"), callback_data="post_schedule")]])
    
    await callback.message.edit_text(
        texts.get_scheduling_text("select_month"),
        reply_markup=keyboard
    )
    await state.set_state(PostStates.selecting_month)
    await callback.answer()


@post_router.callback_query(F.data.startswith("month_"), PostStates.selecting_month)
async def select_month(callback: CallbackQuery, state: FSMContext):
    """Select month"""
    texts = get_texts()
    config = get_config()
    month = int(callback.data.split("_")[1])
    
    data = await state.get_data()
    year = data.get("year")
    await state.update_data(month=month)
    
    # Get days in month
    tz = pytz.timezone(config.TIMEZONE)
    current = datetime.now(tz)
    _, days_in_month = monthrange(year, month)
    
    # Filter out past days if current month
    start_day = 1
    if year == current.year and month == current.month:
        start_day = current.day
    
    if start_day > days_in_month:
        await callback.answer(texts.get_scheduling_text("no_days_available"), show_alert=True)
        return
    
    # Create day buttons (4 per row)
    day_buttons = []
    row = []
    for day in range(start_day, days_in_month + 1):
        row.append(InlineKeyboardButton(text=str(day), callback_data=f"day_{day}"))
        if len(row) == 4:
            day_buttons.append(row)
            row = []
    if row:
        day_buttons.append(row)
    
    day_buttons.append([InlineKeyboardButton(text=texts.get_button_text("back"), callback_data=f"year_{year}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=day_buttons)
    
    await callback.message.edit_text(
        texts.get_scheduling_text("select_day"),
        reply_markup=keyboard
    )
    await state.set_state(PostStates.selecting_day)
    await callback.answer()


@post_router.callback_query(F.data.startswith("day_"), PostStates.selecting_day)
async def select_day(callback: CallbackQuery, state: FSMContext):
    """Select day"""
    texts = get_texts()
    day = int(callback.data.split("_")[1])
    
    data = await state.get_data()
    await state.update_data(day=day)
    
    # Show hours (0-23)
    hour_buttons = []
    row = []
    for hour in range(24):
        row.append(InlineKeyboardButton(text=f"{hour:02d}:00", callback_data=f"hour_{hour}"))
        if len(row) == 4:
            hour_buttons.append(row)
            row = []
    if row:
        hour_buttons.append(row)
    
    hour_buttons.append([InlineKeyboardButton(text=texts.get_button_text("back"), callback_data=f"month_{data['month']}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=hour_buttons)
    
    await callback.message.edit_text(
        texts.get_scheduling_text("select_hour"),
        reply_markup=keyboard
    )
    await state.set_state(PostStates.selecting_hour)
    await callback.answer()


@post_router.callback_query(F.data.startswith("hour_"), PostStates.selecting_hour)
async def select_hour(callback: CallbackQuery, state: FSMContext):
    """Select hour and confirm schedule"""
    texts = get_texts()
    config = get_config()
    redis = get_redis()
    user_id = callback.from_user.id
    hour = int(callback.data.split("_")[1])
    
    data = await state.get_data()
    year = data.get("year")
    month = data.get("month")
    day = data.get("day")
    
    # Create scheduled datetime
    tz = pytz.timezone(config.TIMEZONE)
    scheduled_dt = tz.localize(datetime(year, month, day, hour, 0, 0))
    
    # Check if datetime is in the future
    if scheduled_dt <= datetime.now(tz):
        await callback.answer(texts.get_scheduling_text("invalid_datetime"), show_alert=True)
        return
    
    # Save scheduled post to database
    post_data = await redis.get_post_draft(user_id)
    if not post_data:
        await callback.answer(texts.get_error_text("unknown"), show_alert=True)
        return
    
    db = get_db()
    async with db.get_session() as session:
        scheduled_post = ScheduledPost(
            admin_id=user_id,
            content_type=post_data["type"],
            text=post_data.get("text"),
            file_id=post_data.get("file_id"),
            scheduled_time=scheduled_dt.replace(tzinfo=None),  # Store as naive datetime
            published=False
        )
        session.add(scheduled_post)
        await session.commit()
    
    # Clear state and draft
    await state.clear()
    await redis.clear_post_draft(user_id)
    
    await callback.message.answer(
        texts.get_scheduling_text("scheduled_success", datetime=scheduled_dt.strftime("%Y-%m-%d %H:%M"))
    )
    await callback.answer()
    logger.info(f"Admin {user_id} scheduled post for {scheduled_dt}")


@post_router.callback_query(F.data == "post_cancel")
async def cancel_post_creation(callback: CallbackQuery, state: FSMContext):
    """Cancel post creation"""
    texts = get_texts()
    redis = get_redis()
    user_id = callback.from_user.id
    
    # Clear state and draft
    await state.clear()
    await redis.clear_post_draft(user_id)
    
    await callback.message.answer(texts.get_post_creation_text("canceled"))
    await callback.answer()
    logger.info(f"Admin {user_id} canceled post creation")


async def publish_post(bot: Bot, channel_id: int, post_data: dict, texts) -> bool:
    """
    Publish post to channel
    
    Args:
        bot: Bot instance
        channel_id: Channel ID
        post_data: Post data dictionary
        texts: TextManager instance
        
    Returns:
        True if successful
    """
    try:
        # Get bot info for button
        bot_info = await bot.get_me()
        bot_button = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=texts.get_button_text("open_bot"),
                url=f"https://t.me/{bot_info.username}"
            )]
        ])
        
        if post_data["type"] == "text":
            await bot.send_message(
                channel_id,
                post_data["text"],
                reply_markup=bot_button
            )
        elif post_data["type"] == "photo":
            await bot.send_photo(
                channel_id,
                post_data["file_id"],
                caption=post_data["text"] if post_data["text"] else None,
                reply_markup=bot_button
            )
        elif post_data["type"] == "video":
            await bot.send_video(
                channel_id,
                post_data["file_id"],
                caption=post_data["text"] if post_data["text"] else None,
                reply_markup=bot_button
            )
        elif post_data["type"] == "animation":
            await bot.send_animation(
                channel_id,
                post_data["file_id"],
                caption=post_data["text"] if post_data["text"] else None,
                reply_markup=bot_button
            )
        
        return True
    except Exception as e:
        logger.error(f"Error publishing post: {e}")
        return False
