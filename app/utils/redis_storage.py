import json
import logging
from typing import Any, Optional
from redis.asyncio import Redis, ConnectionPool

logger = logging.getLogger(__name__)


class RedisStorage:
    """Redis storage for post drafts, subscription cache and FSM helpers"""

    def __init__(self, redis_url: str, namespace: str = "tg_bot"):
        """
        Initialize Redis connection

        Args:
            redis_url: Redis connection string (redis://...)
            namespace: Префикс ключей этого бота. Изолирует данные ботов даже
                при общем Redis (например, namespace = bot id).
        """
        self.pool = ConnectionPool.from_url(redis_url, decode_responses=True)
        self.redis = Redis(connection_pool=self.pool)
        self.namespace = namespace

    def _key(self, *parts) -> str:
        """Build namespaced Redis key."""
        return ":".join([self.namespace, *map(str, parts)])

    async def close(self):
        """Close Redis connection"""
        await self.redis.aclose()
        await self.pool.disconnect()
        logger.info("Redis connection closed")

    # FSM-состояниями управляет aiogram через свой RedisStorage; здесь храним
    # только черновики постов, кэш подписки и произвольные ключи.

    # Post Draft Management
    async def save_post_draft(self, user_id: int, data: dict, ttl: int = 3600) -> bool:
        """
        Save post draft data
        
        Args:
            user_id: User ID
            data: Draft data dictionary
            ttl: Time to live in seconds (default 1 hour)
            
        Returns:
            True if successful
        """
        try:
            key = self._key("post:draft", user_id)
            await self.redis.setex(key, ttl, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Error saving post draft: {e}")
            return False
    
    async def get_post_draft(self, user_id: int) -> Optional[dict]:
        """
        Get post draft data
        
        Args:
            user_id: User ID
            
        Returns:
            Draft data dictionary or None
        """
        try:
            key = self._key("post:draft", user_id)
            data = await self.redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error getting post draft: {e}")
            return None
    
    async def clear_post_draft(self, user_id: int) -> bool:
        """
        Clear post draft data
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful
        """
        try:
            key = self._key("post:draft", user_id)
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error clearing post draft: {e}")
            return False

    # Subscription cache — снижает число запросов get_chat_member к Telegram
    async def get_cached_subscription(self, user_id: int) -> Optional[bool]:
        """
        Получить закэшированный результат проверки подписки.

        Returns:
            True/False если в кэше, иначе None (нужно проверять заново).
        """
        try:
            value = await self.redis.get(self._key("sub", user_id))
            if value is None:
                return None
            return value == "1"
        except Exception as e:
            logger.error(f"Error reading subscription cache: {e}")
            return None

    async def set_cached_subscription(self, user_id: int, subscribed: bool, ttl: int = 300) -> bool:
        """Сохранить результат проверки подписки (по умолчанию на 5 минут)."""
        try:
            await self.redis.setex(self._key("sub", user_id), ttl, "1" if subscribed else "0")
            return True
        except Exception as e:
            logger.error(f"Error writing subscription cache: {e}")
            return False

    # Anti-flood: фиксированное окно через INCR + EXPIRE
    async def register_event(self, user_id: int, window: int) -> int:
        """
        Зарегистрировать событие пользователя и вернуть число событий в текущем окне.

        Returns:
            Текущий счётчик за окно (>= 1). При ошибке Redis возвращает 0,
            чтобы троттлинг не блокировал пользователей при сбое.
        """
        try:
            key = self._key("throttle", user_id)
            count = await self.redis.incr(key)
            if count == 1:
                await self.redis.expire(key, window)
            return count
        except Exception as e:
            logger.error(f"Error registering throttle event: {e}")
            return 0
    
    # Generic key-value operations
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a key-value pair
        
        Args:
            key: Key name
            value: Value (will be JSON serialized if dict/list)
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful
        """
        try:
            data = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            nkey = self._key(key)
            if ttl:
                await self.redis.setex(nkey, ttl, data)
            else:
                await self.redis.set(nkey, data)
            return True
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[str]:
        """
        Get value by key
        
        Args:
            key: Key name
            
        Returns:
            Value or None
        """
        try:
            return await self.redis.get(self._key(key))
        except Exception as e:
            logger.error(f"Error getting key {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """
        Delete key
        
        Args:
            key: Key name
            
        Returns:
            True if successful
        """
        try:
            await self.redis.delete(self._key(key))
            return True
        except Exception as e:
            logger.error(f"Error deleting key {key}: {e}")
            return False


# Global Redis instance
redis_storage: RedisStorage | None = None


async def init_redis(redis_url: str, namespace: str = "tg_bot") -> RedisStorage:
    """
    Initialize Redis connection

    Args:
        redis_url: Redis connection string
        namespace: Префикс ключей бота (например, его bot id)

    Returns:
        RedisStorage instance
    """
    global redis_storage
    redis_storage = RedisStorage(redis_url, namespace=namespace)
    logger.info(f"Redis connection initialized (namespace={namespace})")
    return redis_storage


async def close_redis():
    """Close Redis connection"""
    global redis_storage
    if redis_storage:
        await redis_storage.close()
        redis_storage = None


def get_redis() -> RedisStorage:
    """Get global Redis instance"""
    if redis_storage is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return redis_storage
