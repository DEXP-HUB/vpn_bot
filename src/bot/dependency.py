from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..database import async_session_maker
from .models import User
from .repository import UserRepository

# Минимальное и максимальное допустимые значения Telegram ID
TELEGRAM_ID_MIN = 1
TELEGRAM_ID_MAX = 9_999_999_999


async def provide_new_user(message: Message, state: FSMContext) -> str:
    """Dependency: валидирует telegram_id из текста сообщения и записывает нового пользователя в БД.

    Возвращает telegram_id при успехе, None — если валидация не прошла или пользователь уже существует.
    """
    user_data = await state.get_data()
    telegram_id = int(user_data["telegram_id"])
    name = message.text.strip()

    user_repository = UserRepository(async_session_maker)
    # Проверяем через репозиторий, не существует ли пользователь с таким telegram_id
    existing = await user_repository.get_user_id_by_telegram_id(telegram_id)

    if existing:
        return f"Пользователь с telegram_id {telegram_id} уже существует."

    try:
        await user_repository.add(User(telegram_id=telegram_id, name=name))
        return f"Пользователь {telegram_id} успешно добавлен."

    except IntegrityError:
        return f"Ошибка: пользователь с telegram_id {telegram_id} уже существует."


async def provide_deleted_user_by_id(message: Message) -> str:
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


async def provide_deleted_user_by_name(message: Message) -> str:
    """Dependency: валидирует имя пользователя из текста сообщения и удаляет пользователя из БД."""
    name = message.text.strip()

    user_repository = UserRepository(async_session_maker)
    user = await user_repository.get_user_name_by_name(name)

    if not user:
        return f"Пользователь с именем {name} не найден."

    is_deleted = await user_repository.delete_user_by_name(name)
    
    if not is_deleted:
        return f"Пользователь с именем {name} не найден."

    return f"Пользователь {name} успешно удалён."


async def provide_users_list() -> str:
    """Dependency: получает пользователей через репозиторий и возвращает готовый текст ответа."""
    user_repository = UserRepository(async_session_maker)
    users_list = await user_repository.list_all()

    if not users_list:
        return "Пользователи не найдены."

    lines = ["Список пользователей:"]
    
    for user in users_list:
        lines.append(f"{user.user_id}. telegram_id: {user.telegram_id}, name: {user.name}")

    return "\n".join(lines)
