from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from ..logger import Logger
from ..bot.repository import UserRepository


class AdminMessageMiddleware(BaseMiddleware):
    """
    Мидлвер для проверки прав администратора на входящих сообщениях.

    Пропускает дальше только сообщения от пользователя с указанным admin_id.
    Остальные сообщения отбрасываются без вызова хендлера.

    :param admin_id: Telegram ID администратора.
    """

    def __init__(self, user_repository: UserRepository) -> None:
        # Сохраняем ID администратора для последующих проверок
        self._user_repository = user_repository
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
    
        if self._user_repository is not None:
            # Проверяем числится ли пользователь в базе данных
            if await self._user_repository.get_user_id_by_telegram_id(event.from_user.id) is not None:
                return await handler(event, data)

        return None


class LoggingMessageMiddleware(BaseMiddleware):
    """
    Мидлвер для логирования входящих сообщений от пользователей.

    Перехватывает каждое входящее Message перед передачей в хендлер,
    записывает в лог информацию о пользователе и тексте сообщения.

    :param logger_name: Имя логгера. По умолчанию — имя класса.
    """

    def __init__(self, logger_name: str = "LoggingMessageMiddleware") -> None:
        # Создаём логгер с переданным именем при инициализации мидлвера
        self.logger = Logger.get_logger(logger_name)
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        user = event.from_user

        # Формируем читаемое имя пользователя для лога
        username = f"@{user.username}" if user.username else f"id={user.id}"
        full_name = user.full_name or "Unknown"

        self.logger.info(
            "Message from %s (%s) [chat_id=%d]: %s",
            full_name,
            username,
            event.chat.id,
            event.text or f"<{event.content_type}>",
        )

        return await handler(event, data)

