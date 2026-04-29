from os import getenv

from aiogram import F, Router
from aiogram.types import Message
from dotenv import load_dotenv
from fast_depends import Depends, inject

from .dependency import provide_new_user
from .middlewares import AdminMessageMiddleware, LoggingMessageMiddleware

load_dotenv()

router = Router(name="Users")
router.message.middleware(LoggingMessageMiddleware(router.name))
router.message.middleware(AdminMessageMiddleware(int(getenv("ADMIN_ID"))))


@router.message(F.text)
@inject
async def add_user(
    message: Message,
    telegram_id: int | None = Depends(provide_new_user),
) -> None:
    if telegram_id is not None:
        await message.answer(f"Пользователь {telegram_id} успешно добавлен.")
