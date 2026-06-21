from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
import logging

from app.utils.redis_storage import get_redis
from app.utils.texts import get_texts

logger = logging.getLogger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    """
    Anti-flood: ограничивает число событий от одного пользователя в окне времени.

    Реализовано через Redis (фиксированное окно). При недоступности Redis
    троттлинг "fail-open" — не блокирует пользователей.
    """

    def __init__(self, limit: int = 5, window: int = 3):
        """
        Args:
            limit: максимум событий за окно
            window: размер окна в секундах
        """
        self.limit = limit
        self.window = window

    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        user = event.from_user
        if not user:
            return await handler(event, data)

        try:
            redis = get_redis()
        except RuntimeError:
            # Redis ещё не инициализирован — не мешаем работе
            return await handler(event, data)

        count = await redis.register_event(user.id, self.window)

        if count > self.limit:
            # Предупреждаем один раз за окно, дальше просто молча отбрасываем
            if count == self.limit + 1:
                logger.info(f"Throttled user {user.id} ({count} events / {self.window}s)")
                texts = get_texts()
                warning = texts.get_user_text("too_fast")
                try:
                    if isinstance(event, CallbackQuery):
                        await event.answer(warning, show_alert=False)
                    else:
                        await event.answer(warning)
                except Exception as e:
                    logger.debug(f"Could not send throttle warning to {user.id}: {e}")
            return None  # событие отброшено

        return await handler(event, data)
