from io import BytesIO

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message
from fast_depends import Depends, inject

from ..bot.middlewares import LoggingMessageMiddleware

from .dependency import provide_client_config
from .fsm import UserConfigStates

router_configurator = Router(name="RouterConfigurator")
router_configurator.message.middleware(LoggingMessageMiddleware(router_configurator.name))


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
    message: Message,
    state: FSMContext,
    config_name: BytesIO = Depends(provide_client_config),
) -> None:
    """Обрабатывает ввод названия конфигурации и генерирует конфигурацию"""
    await message.answer("Конфигурация успешно сгенерирована ✅")
    await message.answer_document(
        document=BufferedInputFile(config_name.read(), filename=config_name.name),
        caption="Конфигурация успешно сгенерирована ✅",
    ) 
    await state.clear()