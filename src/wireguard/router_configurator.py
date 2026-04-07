from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from .services import WireguardConfiguretor

router_configurator = Router()


@router_configurator.message(Command("generate_config"))
async def generate_config(message: Message) -> None:
    """Генерирует конфигурацию для клиента WireGuard"""
    wireguard = WireguardConfiguretor.from_env()
    wireguard.create_client_keys(
        client_name=message.from_user.username
    )
    config_file = wireguard.create_client_config(
        client_name=message.from_user.username
    )
    wireguard.close()

    await message.answer_document(
        document=BufferedInputFile(config_file.read(), filename=config_file.name),
        caption="Конфигурация успешно сгенерирована ✅",
    ) 
