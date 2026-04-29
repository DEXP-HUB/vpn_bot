from os import getenv

from aiogram import F, Router
from aiogram.types import Message
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .database import async_session_maker
from .middlewares import AdminMessageMiddleware, LoggingMessageMiddleware
from .models import User

load_dotenv()

router = Router(name="Users")
router.message.middleware(LoggingMessageMiddleware(router.name))
router.message.middleware(AdminMessageMiddleware(int(getenv("ADMIN_ID"))))

# Минимальное и максимальное допустимые значения Telegram ID
TELEGRAM_ID_MIN = 1
TELEGRAM_ID_MAX = 9_999_999_999


@router.message(F.text)
async def add_user(message: Message) -> None:
    raw = message.text.strip()

    # Проверяем, что сообщение содержит только цифры
    if not raw.isdigit():
        await message.answer("Ошибка: telegram_id должен быть целым положительным числом.")
        return

    telegram_id = int(raw)

    # Проверяем, что значение находится в допустимом диапазоне Telegram ID
    if not (TELEGRAM_ID_MIN <= telegram_id <= TELEGRAM_ID_MAX):
        await message.answer(
            f"Ошибка: telegram_id должен быть в диапазоне "
            f"{TELEGRAM_ID_MIN}–{TELEGRAM_ID_MAX}."
        )
        return

    async with async_session_maker() as session:
        # Проверяем, не существует ли пользователь с таким telegram_id
        existing = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        if existing:
            await message.answer(f"Пользователь с telegram_id {telegram_id} уже существует.")
            return

        try:
            session.add(User(telegram_id=telegram_id))
            await session.commit()
            await message.answer(f"Пользователь {telegram_id} успешно добавлен.")
        except IntegrityError:
            await session.rollback()
            await message.answer(f"Ошибка: пользователь с telegram_id {telegram_id} уже существует.")
