from io import BytesIO

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message
from fast_depends import Depends, inject

from ..bot.middlewares import LoggingMessageMiddleware

from .dependency import provide_client_config

router_configurator = Router(name="RouterConfigurator")
router_configurator.message.middleware(LoggingMessageMiddleware(router_configurator.name))


@router_configurator.message(Command("generate_config"))
@inject
async def generate_config(
    message: Message,
    config_file: BytesIO = Depends(provide_client_config),
) -> None:
    """Генерирует конфигурацию для клиента WireGuard"""
    await message.answer_document(
        document=BufferedInputFile(config_file.read(), filename=config_file.name),
        caption="Конфигурация успешно сгенерирована ✅",
    ) 
