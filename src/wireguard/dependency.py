from io import BytesIO

from aiogram.types import Message
from fast_depends import inject

from .services import WireguardManager


@inject
def provide_client_config(message: Message) -> BytesIO:
    """Dependency: создаёт и возвращает клиентский .conf файл."""
    manager = WireguardManager()
    return manager.generate_client_config(
        client_name=message.from_user.username,
    )
