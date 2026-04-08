from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from .logger import Logger


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


class LoggingCallbackMiddleware(BaseMiddleware):
    """
    Мидлвер для логирования входящих callback-запросов (нажатия инлайн-кнопок).

    Перехватывает каждый CallbackQuery перед передачей в хендлер и записывает
    в лог информацию о пользователе и данных callback-а.

    :param logger_name: Имя логгера. По умолчанию — имя класса.
    """

    def __init__(self, logger_name: str = "LoggingCallbackMiddleware") -> None:
        # Создаём логгер с переданным именем при инициализации мидлвера
        self.logger = Logger.get_logger(logger_name)
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        user = event.from_user

        # Формируем читаемое имя пользователя для лога
        username = f"@{user.username}" if user.username else f"id={user.id}"
        full_name = user.full_name or "Unknown"

        self.logger.info(
            "Callback from %s (%s) [chat_id=%d]: data=%r",
            full_name,
            username,
            event.message.chat.id if event.message else 0,
            event.data,
        )

        return await handler(event, data)
