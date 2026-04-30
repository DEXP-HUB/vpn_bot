from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..database import async_session_maker
from .models import User

# Минимальное и максимальное допустимые значения Telegram ID
TELEGRAM_ID_MIN = 1
TELEGRAM_ID_MAX = 9_999_999_999


async def provide_new_user(message: Message) -> str:
    """Dependency: валидирует telegram_id из текста сообщения и записывает нового пользователя в БД.

    Возвращает telegram_id при успехе, None — если валидация не прошла или пользователь уже существует.
    """
    raw = message.text.strip()

    telegram_id = int(raw)

    # Проверяем, что значение находится в допустимом диапазоне Telegram ID
    if not (TELEGRAM_ID_MIN <= telegram_id <= TELEGRAM_ID_MAX):
        return f"Ошибка: telegram_id должен быть в диапазоне {TELEGRAM_ID_MIN}–{TELEGRAM_ID_MAX}"

    async with async_session_maker() as session:
        # Проверяем, не существует ли пользователь с таким telegram_id
        existing = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        if existing:
            return f"Пользователь с telegram_id {telegram_id} уже существует."

        try:
            session.add(User(telegram_id=telegram_id))
            await session.commit()
            return f"Пользователь {telegram_id} успешно добавлен."
        except IntegrityError:
            await session.rollback()
            return f"Ошибка: пользователь с telegram_id {telegram_id} уже существует."


async def provide_deleted_user(message: Message) -> str:
    """Dependency: валидирует telegram_id из текста сообщения и удаляет пользователя из БД."""
    raw = message.text.strip()

    telegram_id = int(raw)

    # Проверяем, что значение находится в допустимом диапазоне Telegram ID
    if not (TELEGRAM_ID_MIN <= telegram_id <= TELEGRAM_ID_MAX):
        return f"Ошибка: telegram_id должен быть в диапазоне {TELEGRAM_ID_MIN}–{TELEGRAM_ID_MAX}"

    async with async_session_maker() as session:
        # Ищем пользователя по telegram_id, чтобы удалить его из БД
        user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        if not user:
            return f"Пользователь с telegram_id {telegram_id} не найден."

        await session.delete(user)
        await session.commit()
        return f"Пользователь {telegram_id} успешно удалён."
