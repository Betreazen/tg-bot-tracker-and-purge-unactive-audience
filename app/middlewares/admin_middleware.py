from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
import logging

from app.utils.config import get_config

logger = logging.getLogger(__name__)


class AdminMiddleware(BaseMiddleware):
    """Middleware to check if user is admin"""
    
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        """
        Check if user is admin before handling event
        
        Args:
            handler: Next handler
            event: Event (Message or CallbackQuery)
            data: Event data
            
        Returns:
            Handler result or None if unauthorized
        """
        config = get_config()
        user = event.from_user
        
        if not user:
            return
        
        # Check if user is admin
        if not config.is_admin(user.id):
            logger.warning(f"Unauthorized access attempt by user {user.id}")
            # Don't respond to unauthorized users - just ignore
            return
        
        # User is admin - proceed with handler
        return await handler(event, data)
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
import logging

from app.utils.config import get_config

logger = logging.getLogger(__name__)


class AdminMiddleware(BaseMiddleware):
    """Middleware to check if user is admin"""
    
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        """
        Check if user is admin before handling event
        
        Args:
            handler: Next handler
            event: Event (Message or CallbackQuery)
            data: Event data
            
        Returns:
            Handler result or None if unauthorized
        """
        config = get_config()
        user = event.from_user
        
        if not user:
            return
        
        # Check if user is admin
        if not config.is_admin(user.id):
            logger.warning(f"Unauthorized access attempt by user {user.id}")
            # Don't respond to unauthorized users - just ignore
            return
        
        # User is admin - proceed with handler
        return await handler(event, data)
