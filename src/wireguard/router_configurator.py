from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, Message, CallbackQuery
from fast_depends import Depends, inject

from .dependency import ClientConfigFiles, ClientConfigProvider, keyboard_configs
from .dependency import delete_config as delete_config_dependency
from .fsm import UserConfigStates
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
    await message.answer("Введите название конфигурации:")


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
    keyboard_configs: InlineKeyboardMarkup = Depends(keyboard_configs),
) -> None:
    """Показывает список всех конфигураций"""
    await message.answer(f"Список всех конфигураций", reply_markup=keyboard_configs)


@router_configurator.message(Command("delete_config"))
async def delete_config(
    message: Message,
    state: FSMContext,
) -> None:
    """Удаляет конфигурацию"""
    await state.set_state(UserConfigStates.waiting_delete_user_config)
    await message.answer("Введите название конфигурации для удаления:")


@router_configurator.message(UserConfigStates.waiting_delete_user_config, F.text)
@inject
async def process_delete_config(
    state: FSMContext,
    message: Message,
    status: str = Depends(delete_config_dependency),
) -> None:
    """Обрабатывает ввод названия конфигурации и удаляет конфигурацию"""
    await message.answer(status)
    await state.clear()

