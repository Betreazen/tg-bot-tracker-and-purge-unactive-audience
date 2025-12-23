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
        
        # Database Configuration
        self.DATABASE_URL: str = self._get_required("DATABASE_URL")
        
        # Redis Configuration
        self.REDIS_URL: str = self._get_required("REDIS_URL")
        
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
