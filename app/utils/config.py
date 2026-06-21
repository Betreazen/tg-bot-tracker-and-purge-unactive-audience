import os
from typing import List
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class Config:
    """Application configuration loaded from environment variables"""
    
    def __init__(self):
        """Load configuration from .env file"""
        load_dotenv()
        
        # Telegram Bot Configuration
        self.BOT_TOKEN: str = self._get_required("BOT_TOKEN")
        self.CHANNEL_ID: int = int(self._get_required("CHANNEL_ID"))
        self.CHANNEL_USERNAME: str = self._get_required("CHANNEL_USERNAME")
        self.ADMIN_IDS: List[int] = self._parse_admin_ids(self._get_required("ADMIN_IDS"))
        
        # Timezone
        self.TIMEZONE: str = os.getenv("TIMEZONE", "Europe/Moscow")

        # Database: строку подключения собираем из частей (единый источник правды).
        # Можно переопределить целиком через DATABASE_URL, если нужно.
        self.POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres")
        self.POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
        self.POSTGRES_DB: str = os.getenv("POSTGRES_DB", "tg_bot_db")
        self.POSTGRES_USER: str = os.getenv("POSTGRES_USER", "tg_bot_user")
        self.POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "tg_bot_password")
        self.DATABASE_URL: str = os.getenv("DATABASE_URL") or (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

        # Redis: аналогично — собираем из частей или берём готовый REDIS_URL
        self.REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
        self.REDIS_PORT: str = os.getenv("REDIS_PORT", "6379")
        self.REDIS_DB: str = os.getenv("REDIS_DB", "0")
        self.REDIS_URL: str = os.getenv("REDIS_URL") or (
            f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        )

        # Logging
        self.LOG_PATH: str = os.getenv("LOG_PATH", "logs/bot.log")

        logger.info("Configuration loaded successfully")
        
    def _get_required(self, key: str) -> str:
        """
        Get required environment variable
        
        Args:
            key: Environment variable name
            
        Returns:
            Environment variable value
            
        Raises:
            ValueError: If environment variable is not set
        """
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    def _parse_admin_ids(self, admin_ids_str: str) -> List[int]:
        """
        Parse comma-separated admin IDs
        
        Args:
            admin_ids_str: Comma-separated admin IDs
            
        Returns:
            List of admin IDs
        """
        try:
            return [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]
        except ValueError as e:
            raise ValueError(f"Invalid admin IDs format: {e}")
    
    def is_admin(self, user_id: int) -> bool:
        """
        Check if user is admin
        
        Args:
            user_id: User ID to check
            
        Returns:
            True if user is admin
        """
        return user_id in self.ADMIN_IDS


# Global config instance
config: Config | None = None


def load_config() -> Config:
    """
    Load configuration
    
    Returns:
        Config instance
    """
    global config
    config = Config()
    return config


def get_config() -> Config:
    """
    Get global config instance
    
    Returns:
        Config instance
        
    Raises:
        RuntimeError: If config is not initialized
    """
    if config is None:
        raise RuntimeError("Config not initialized. Call load_config() first.")
    return config
