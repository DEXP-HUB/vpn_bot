from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.methods import SendDocument, SendMessage
from aiogram.types import Message
from fast_depends import Depends, inject
from ..bot.middlewares import LoggingMessageMiddleware

from .dependency import provide_client_config
from .fsm import UserConfigStates
from ..bot.middlewares import AdminMessageMiddleware
from ..bot.repository import UserRepository
from ..database import async_session_maker

router_configurator = Router(name="RouterConfigurator")
router_configurator.message.middleware(LoggingMessageMiddleware(router_configurator.name))
router_configurator.message.middleware(
    AdminMessageMiddleware(user_repository=UserRepository(async_session_maker))
)


@router_configurator.message(Command("generate_config"))
async def generate_config(
    message: Message,
    state: FSMContext,
) -> None:
    """Генерирует конфигурацию для клиента WireGuard"""
    await state.set_state(UserConfigStates.waiting_add_user_config)
    await message.answer("Введите введите название конфигурации:")


@router_configurator.message(UserConfigStates.waiting_add_user_config, F.text)
@inject
async def process_generate_config(
    state: FSMContext,
    send_command: SendDocument | SendMessage = Depends(provide_client_config),
) -> None:
    """Обрабатывает ввод названия конфигурации и генерирует конфигурацию"""
    await send_command
    await state.clear()
    
