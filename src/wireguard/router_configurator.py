from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from fast_depends import Depends, inject

from .dependency import ClientConfigFiles, ClientConfigProvider, configs
from .fsm import UserConfigStates
from .models import Config
from .repository import ConfigRepository
from ..bot.middlewares import AdminMessageMiddleware
from ..bot.middlewares import LoggingMessageMiddleware
from ..bot.repository import UserRepository
from ..database import async_session_maker

router_configurator = Router(name="RouterConfigurator")
router_configurator.message.middleware(LoggingMessageMiddleware(router_configurator.name))
router_configurator.message.middleware(
    AdminMessageMiddleware(user_repository=UserRepository(async_session_maker))
)
client_config_provider = ClientConfigProvider(
    config_repository=ConfigRepository(async_session_maker),
    user_repository=UserRepository(async_session_maker),
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
    message: Message,
    files: ClientConfigFiles | None = Depends(client_config_provider.provide_client_config),
) -> None:
    """Обрабатывает ввод названия конфигурации и генерирует конфигурацию"""
    if files is not None:
        await message.answer_document(
            document=files.config,
            caption="Конфигурация успешно сгенерирована ✅",
        )
        await message.answer_photo(
            photo=files.qr_code,
            caption="QR-код успешно сгенерирован ✅",
        )
    await state.clear()
    

@router_configurator.message(Command("configs_list"))
@inject
async def configs_list(
    message: Message,
    configs: list[Config] = Depends(configs),
) -> None:
    """Показывает список всех конфигураций"""
    await message.answer(f"Список всех конфигураций: {configs}")