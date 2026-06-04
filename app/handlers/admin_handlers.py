from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command
import logging
from datetime import datetime
import os
import tempfile

from app.database.connection import get_db
from app.services.user_service import UserService
from app.utils.texts import get_texts
from app.utils.config import get_config

logger = logging.getLogger(__name__)

admin_router = Router()


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Get admin main menu keyboard"""
    texts = get_texts()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=texts.get_button_text("create_post"), callback_data="admin_create_post")],
        [InlineKeyboardButton(text=texts.get_button_text("statistics"), callback_data="admin_statistics")],
        [InlineKeyboardButton(text=texts.get_button_text("export_users"), callback_data="admin_export")],
        [InlineKeyboardButton(text=texts.get_button_text("close"), callback_data="admin_close")]
    ])
    return keyboard


@admin_router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Show admin menu"""
    texts = get_texts()
    user_id = message.from_user.id
    
    await message.answer(
        texts.get_admin_text("menu_title"),
        reply_markup=get_admin_menu_keyboard()
    )
    logger.info(f"Admin {user_id} opened admin menu")


@admin_router.callback_query(F.data == "admin_menu")
async def show_admin_menu(callback: CallbackQuery):
    """Show admin menu"""
    texts = get_texts()
    user_id = callback.from_user.id
    
    await callback.message.edit_text(
        texts.get_admin_text("menu_title"),
        reply_markup=get_admin_menu_keyboard()
    )
    await callback.answer()


@admin_router.callback_query(F.data == "admin_close")
async def close_admin_menu(callback: CallbackQuery):
    """Close admin menu"""
    user_id = callback.from_user.id
    
    await callback.message.delete()
    await callback.answer()
    logger.info(f"Admin {user_id} closed admin menu")


@admin_router.callback_query(F.data == "admin_statistics")
async def show_statistics(callback: CallbackQuery):
    """Show statistics"""
    texts = get_texts()
    user_id = callback.from_user.id
    
    # Get statistics
    db = get_db()
    async with db.get_session() as session:
        count = await UserService.count_users_with_username(session)
    
    # Format statistics message
    stats_text = texts.get_statistics_text("title") + "\n\n"
    if count > 0:
        stats_text += texts.get_statistics_text("total_users", count=count)
    else:
        stats_text += texts.get_statistics_text("no_users")
    
    # Create back button
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=texts.get_button_text("back"), callback_data="admin_menu")]
    ])
    
    await callback.message.edit_text(stats_text, reply_markup=keyboard)
    await callback.answer()
    logger.info(f"Admin {user_id} viewed statistics: {count} users")


@admin_router.callback_query(F.data == "admin_export")
async def export_users(callback: CallbackQuery):
    """Export users to file"""
    texts = get_texts()
    config = get_config()
    user_id = callback.from_user.id
    
    await callback.answer(texts.get_export_text("generating"))
    
    # Get users with username
    db = get_db()
    async with db.get_session() as session:
        users = await UserService.get_users_with_username(session)
    
    if not users:
        await callback.message.answer(texts.get_export_text("no_users"))
        return
    
    try:
        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"users_export_{timestamp}.txt"
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt') as f:
            temp_path = f.name
            for user in users:
                f.write(f"@{user.username}\n")
        
        # Send file
        file = FSInputFile(temp_path, filename=filename)
        await callback.message.answer_document(
            file,
            caption=texts.get_export_text("file_caption")
        )
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        await callback.message.answer(
            texts.get_export_text("success", count=len(users))
        )
        
        logger.info(f"Admin {user_id} exported {len(users)} users")
        
    except Exception as e:
        logger.error(f"Error exporting users: {e}")
        await callback.message.answer(
            texts.get_export_text("error", error=str(e))
        )
