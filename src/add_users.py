from aiogram import F, Router
from aiogram.types import Message
from dotenv import load_dotenv
from os import getenv

from .middlewares import LoggingMessageMiddleware, AdminMessageMiddleware

load_dotenv()

router = Router(name="Users")
router.message.middleware(LoggingMessageMiddleware(router.name))
router.message.middleware(AdminMessageMiddleware(int(getenv("ADMIN_ID"))))


@router.message(F.text)
async def add_message(message: Message) -> None:
    await message.answer(message.text)
