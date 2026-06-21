import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TextManager:
    """Manager for loading and accessing text messages from texts.json"""
    
    def __init__(self, texts_file: str = "texts.json"):
        """
        Initialize text manager
        
        Args:
            texts_file: Path to texts.json file
        """
        with open(texts_file, "r", encoding="utf-8") as f:
            self.texts: Dict[str, Any] = json.load(f)
    
    def get(self, *keys: str, **kwargs) -> str:
        """
        Get text by nested keys
        
        Args:
            *keys: Nested keys to access text
            **kwargs: Format parameters for text
            
        Returns:
            Formatted text string
        """
        value = self.texts
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = None
            if value is None:
                break

        if isinstance(value, str):
            try:
                return value.format(**kwargs) if kwargs else value
            except (KeyError, IndexError) as e:
                logger.warning(f"Text formatting failed for keys {keys}: {e}")
                return value

        # Ключ не найден или это не строка — логируем и возвращаем безопасную заглушку
        logger.warning(f"Missing text for keys: {'.'.join(keys)}")
        return f"[{'.'.join(keys)}]"
    
    def get_user_text(self, key: str, **kwargs) -> str:
        """Get user text"""
        return self.get("user", key, **kwargs)
    
    def get_admin_text(self, key: str, **kwargs) -> str:
        """Get admin text"""
        return self.get("admin", key, **kwargs)
    
    def get_button_text(self, key: str) -> str:
        """Get button text"""
        return self.get("buttons", key)
    
    def get_post_creation_text(self, key: str, **kwargs) -> str:
        """Get post creation text"""
        return self.get("post_creation", key, **kwargs)
    
    def get_scheduling_text(self, key: str, **kwargs) -> str:
        """Get scheduling text"""
        return self.get("scheduling", key, **kwargs)
    
    def get_publication_text(self, key: str, **kwargs) -> str:
        """Get publication text"""
        return self.get("publication", key, **kwargs)
    
    def get_statistics_text(self, key: str, **kwargs) -> str:
        """Get statistics text"""
        return self.get("statistics", key, **kwargs)
    
    def get_export_text(self, key: str, **kwargs) -> str:
        """Get export text"""
        return self.get("export", key, **kwargs)
    
    def get_error_text(self, key: str, **kwargs) -> str:
        """Get error text"""
        return self.get("errors", key, **kwargs)


# Global text manager instance
text_manager: TextManager | None = None


def load_texts(texts_file: str = "texts.json") -> TextManager:
    """
    Load texts from file
    
    Args:
        texts_file: Path to texts.json file
        
    Returns:
        TextManager instance
    """
    global text_manager
    text_manager = TextManager(texts_file)
    return text_manager


def get_texts() -> TextManager:
    """
    Get global text manager instance
    
    Returns:
        TextManager instance
        
    Raises:
        RuntimeError: If text manager is not initialized
    """
    if text_manager is None:
        raise RuntimeError("Text manager not initialized. Call load_texts() first.")
    return text_manager
