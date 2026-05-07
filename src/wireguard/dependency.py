from io import BytesIO

from aiogram.types import Message
from fast_depends import inject

from .services import WireguardManager


@inject
async def provide_client_config(message: Message) -> BytesIO:
    """Dependency: создаёт и возвращает клиентский .conf файл."""
    manager = WireguardManager()
    config_name = message.text or str(message.from_user.id)
    return await manager.generate_client_config(
        client_name=config_name,
        telegram_id=message.from_user.id,
    )
