from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import pytz
import logging

from app.database.models import User
from app.utils.config import get_config

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing users"""
    
    @staticmethod
    def get_current_time() -> datetime:
        """Get current time in configured timezone"""
        config = get_config()
        tz = pytz.timezone(config.TIMEZONE)
        # Return timezone-naive datetime for PostgreSQL compatibility
        return datetime.now(tz).replace(tzinfo=None)
    
    @staticmethod
    async def get_user(session: AsyncSession, user_id: int) -> Optional[User]:
        """
        Get user by ID
        
        Args:
            session: Database session
            user_id: User ID
            
        Returns:
            User object or None
        """
        try:
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    @staticmethod
    async def create_or_update_user(
        session: AsyncSession,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> Tuple[User, bool]:
        """
        Create new user or update existing user

        Args:
            session: Database session
            user_id: User ID
            username: Username (without @)
            first_name: First name
            last_name: Last name

        Returns:
            (User, created) — created=True если пользователь создан впервые
        """
        try:
            user = await UserService.get_user(session, user_id)
            current_time = UserService.get_current_time()
            created = user is None

            if user:
                # Update existing user
                user.username = username
                user.first_name = first_name
                user.last_name = last_name
                user.last_seen_at = current_time
                logger.info(f"Updated user {user_id} (username: {username})")
            else:
                # Create new user
                user = User(
                    user_id=user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    first_seen_at=current_time,
                    last_seen_at=current_time
                )
                session.add(user)
                logger.info(f"Created new user {user_id} (username: {username})")

            await session.commit()
            return user, created
        except Exception as e:
            logger.error(f"Error creating/updating user {user_id}: {e}")
            await session.rollback()
            raise
    
    @staticmethod
    async def count_users_with_username(session: AsyncSession) -> int:
        """
        Count users with username
        
        Args:
            session: Database session
            
        Returns:
            Count of users with username
        """
        try:
            result = await session.execute(
                select(func.count(User.user_id)).where(User.username.isnot(None))
            )
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error counting users: {e}")
            return 0
    
    @staticmethod
    async def get_users_with_username(session: AsyncSession) -> list[User]:
        """
        Get all users with username
        
        Args:
            session: Database session
            
        Returns:
            List of users with username
        """
        try:
            result = await session.execute(
                select(User).where(User.username.isnot(None))
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting users with username: {e}")
            return []
