from fast_depends import Depends, inject

from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, Message, CallbackQuery, BufferedInputFile

from .dataclasses import ClientConfigFiles
from .models import Config
from .dependency import config_file, qr_config, config_data, delete_by_callback, keyboard_configs


from ..bot.middlewares import AdminMessageMiddleware, LoggingMessageMiddleware, LoggingCallbackMiddleware
from ..bot.repository import UserRepository

from ..database import async_session_maker


callback_router = Router(name="CallbackRouter")
callback_router.callback_query.middleware(LoggingCallbackMiddleware(callback_router.name))
callback_router.message.middleware(
    AdminMessageMiddleware(user_repository=UserRepository(async_session_maker))
)


@callback_router.callback_query(F.data.startswith("QR-"))
@inject
async def get_qr_code(call: CallbackQuery, qr: ClientConfigFiles = Depends(qr_config)) -> None:
    """
    Callback Тригер: Реагирует на Callback Data с префиксом QR- 
    вызывает Dependancy qr_config для получения qr кода конфига
    и отпровляет его пользователю в виде фото.
    """

    await call.message.delete()
    await call.message.answer_photo(photo=qr.qr_code, reply_markup=qr.inline_keyboard)


@callback_router.callback_query(F.data.startswith("config-"))
@inject
async def get_config_file(call: CallbackQuery, config: ClientConfigFiles = Depends(config_file)) -> None:
    """
    Callback Тригер: Реагирует на Callback Data с префиксом config-
    вызывает Dependancy config_file для получения конфиг файла
    и отпровляет его пользователю.
    """

    await call.message.delete()
    await call.message.answer_document(document=config.config, reply_markup=config.inline_keyboard)


@callback_router.callback_query(F.data.startswith("delete-"))
@inject
async def delete_config_user(call: CallbackQuery, status: str | None = Depends(delete_by_callback)) -> None:
    """
    Callback Тригер: Реагирует на Callback Data с префиксом delete-
    вызывает Dependancy delete_by_callback для удаления конфиг файла
    и отпровляет статус пользователю.
    """
    await call.message.delete()
    await call.message.answer(status)


@callback_router.callback_query(F.data == "Назад")
@inject
async def back_to_list(
    call: CallbackQuery,  
    keyboard_configs: InlineKeyboardMarkup = Depends(keyboard_configs)
) -> None:
    """Показывает список всех конфигураций"""
    await call.message.delete()
    await call.message.answer(f"Список всех конфигураций", reply_markup=keyboard_configs)




@callback_router.callback_query(F.data)
@inject
async def config_user(call: CallbackQuery, config: ClientConfigFiles = Depends(config_data)) -> None:
    """
    Callback Тригер: Реагирует на Callback Data
    вызывает Dependancy config_data для получения всех 
    конфигов пользователей и отпровляет список с клавиатурой из конфигов
    """
    await call.message.delete()
    await call.message.answer_document(
        document=config.config, 
        caption="Конфигурация пользователя", 
        reply_markup=config.inline_keyboard,
    )






