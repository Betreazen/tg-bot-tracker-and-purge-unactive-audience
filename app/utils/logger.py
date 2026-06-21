import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(log_path: str, level: int = logging.INFO):
    """
    Setup logging configuration
    
    Args:
        log_path: Path to log file
        level: Logging level (default: INFO)
    """
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Console handler (всегда доступен — основной канал логов в Docker)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation — отказоустойчиво: если каталог логов недоступен
    # на запись (например, права на bind-mount), не роняем бот, пишем только в консоль.
    try:
        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except OSError as e:
        logging.warning(f"File logging disabled ({log_path}): {e}. Using console only.")
    
    # Suppress some verbose loggers
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    logging.info(f"Logging initialized. Log file: {log_path}")
