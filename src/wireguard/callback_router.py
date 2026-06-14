from fast_depends import Depends, inject

from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, Message, CallbackQuery, BufferedInputFile

from .models import Config
from .dependency import config_data

from ..logger import Logger

callback_router = Router(name="CallbackRouter")
callback_logger = Logger.get_logger(callback_router.name)


@callback_router.callback_query(F.data)
@inject
async def config_user(call: CallbackQuery, config: BufferedInputFile = Depends(config_data)) -> None:
    await call.message.answer_document(document=config, caption="Конфигурация пользователя")



