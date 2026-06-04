import json
import logging
from typing import Any, Optional
from redis.asyncio import Redis, ConnectionPool

logger = logging.getLogger(__name__)


class RedisStorage:
    """Redis storage for FSM and post drafts"""
    
    def __init__(self, redis_url: str):
        """
        Initialize Redis connection
        
        Args:
            redis_url: Redis connection string (redis://...)
        """
        self.pool = ConnectionPool.from_url(redis_url, decode_responses=True)
        self.redis = Redis(connection_pool=self.pool)
        
    async def close(self):
        """Close Redis connection"""
        await self.redis.close()
        await self.pool.disconnect()
        logger.info("Redis connection closed")
    
    # FSM State Management
    async def set_state(self, user_id: int, state: str, ttl: int = 3600) -> bool:
        """
        Set FSM state for user
        
        Args:
            user_id: User ID
            state: State name
            ttl: Time to live in seconds (default 1 hour)
            
        Returns:
            True if successful
        """
        try:
            key = f"fsm:state:{user_id}"
            await self.redis.setex(key, ttl, state)
            return True
        except Exception as e:
            logger.error(f"Error setting FSM state: {e}")
            return False
    
    async def get_state(self, user_id: int) -> Optional[str]:
        """
        Get FSM state for user
        
        Args:
            user_id: User ID
            
        Returns:
            State name or None
        """
        try:
            key = f"fsm:state:{user_id}"
            return await self.redis.get(key)
        except Exception as e:
            logger.error(f"Error getting FSM state: {e}")
            return None
    
    async def clear_state(self, user_id: int) -> bool:
        """
        Clear FSM state for user
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful
        """
        try:
            key = f"fsm:state:{user_id}"
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error clearing FSM state: {e}")
            return False
    
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
            key = f"post:draft:{user_id}"
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
            key = f"post:draft:{user_id}"
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
            key = f"post:draft:{user_id}"
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error clearing post draft: {e}")
            return False
    
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
            if ttl:
                await self.redis.setex(key, ttl, data)
            else:
                await self.redis.set(key, data)
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
            return await self.redis.get(key)
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
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting key {key}: {e}")
            return False


# Global Redis instance
redis_storage: RedisStorage | None = None


async def init_redis(redis_url: str) -> RedisStorage:
    """
    Initialize Redis connection
    
    Args:
        redis_url: Redis connection string
        
    Returns:
        RedisStorage instance
    """
    global redis_storage
    redis_storage = RedisStorage(redis_url)
    logger.info("Redis connection initialized")
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
