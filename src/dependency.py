from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .database import async_session_maker
from .models import User

# Минимальное и максимальное допустимые значения Telegram ID
TELEGRAM_ID_MIN = 1
TELEGRAM_ID_MAX = 9_999_999_999


async def provide_new_user(message: Message) -> int | None:
    """Dependency: валидирует telegram_id из текста сообщения и записывает нового пользователя в БД.

    Возвращает telegram_id при успехе, None — если валидация не прошла или пользователь уже существует.
    """
    raw = message.text.strip()

    # Проверяем, что сообщение содержит только цифры
    if not raw.isdigit():
        await message.answer("Ошибка: telegram_id должен быть целым положительным числом.")
        return None

    telegram_id = int(raw)

    # Проверяем, что значение находится в допустимом диапазоне Telegram ID
    if not (TELEGRAM_ID_MIN <= telegram_id <= TELEGRAM_ID_MAX):
        await message.answer(
            f"Ошибка: telegram_id должен быть в диапазоне "
            f"{TELEGRAM_ID_MIN}–{TELEGRAM_ID_MAX}."
        )
        return None

    async with async_session_maker() as session:
        # Проверяем, не существует ли пользователь с таким telegram_id
        existing = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        if existing:
            await message.answer(f"Пользователь с telegram_id {telegram_id} уже существует.")
            return None

        try:
            session.add(User(telegram_id=telegram_id))
            await session.commit()
            return telegram_id
        except IntegrityError:
            await session.rollback()
            await message.answer(
                f"Ошибка: пользователь с telegram_id {telegram_id} уже существует."
            )
            return None
