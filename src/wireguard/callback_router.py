from fast_depends import Depends, inject

from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, Message, CallbackQuery, BufferedInputFile

from .dataclasses import ClientConfigFiles
from .models import Config
from .dependency import config_data


from ..bot.middlewares import AdminMessageMiddleware, LoggingMessageMiddleware
from ..bot.repository import UserRepository

from ..database import async_session_maker


callback_router = Router(name="CallbackRouter")
callback_router.message.middleware(LoggingMessageMiddleware(callback_router.name))
callback_router.message.middleware(
    AdminMessageMiddleware(user_repository=UserRepository(async_session_maker))
)


@callback_router.callback_query(F.data)
@inject
async def config_user(call: CallbackQuery, config: ClientConfigFiles = Depends(config_data)) -> None:
    await call.message.delete()
    await call.message.answer_document(
        document=config.config, 
        caption="Конфигурация пользователя", 
        reply_markup=config.inline_keyboard,
    )



