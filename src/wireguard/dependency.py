from aiogram.types import BufferedInputFile, Message
from fast_depends import inject

from .models import Config
from .repository import ConfigRepository
from .services import WireguardManager
from ..bot.repository import UserRepository
from ..database import async_session_maker
from ..utils import build_qr_file


class ClientConfigProvider:
    """Создаёт клиентский WireGuard-конфиг и отправляет его пользователю."""

    def __init__(
        self,
        config_repository: ConfigRepository,
        user_repository: UserRepository,
    ) -> None:
        self._config_repository = config_repository
        self._user_repository = user_repository

    async def provide_client_config(self, message: Message) -> bytes | None:
        """Dependency: создаёт клиентский .conf файл и отправляет его вместе с QR-кодом."""
        config_to_db = await self._config_repository.get_config_by_name(message.text)

        if config_to_db is not None:
            await message.answer(text="Имя занято другим файлом. Попробуйте другое имя.")
            return None
        
        manager = WireguardManager(user_repository=self._user_repository)
        
        config_name = message.text or str(message.from_user.id)

        config_file = await manager.generate_client_config(
            config_name=config_name,
            telegram_id=message.from_user.id,
        )

        config_bytes = config_file.getvalue()

        return config_bytes

    async def qr_code_generator(self, message: Message) -> BufferedInputFile | None:
        """Генерирует QR-код из клиентского WireGuard-конфига."""
        config_bytes = await self.provide_client_config(message)

        if config_bytes is None:
            return None

        qr_code = build_qr_file(
            config_text=config_bytes.decode("utf-8"),
            filename=f"{message.text}.png",
        )
        return qr_code


@inject
async def configs(message: Message) -> list[Config]:
    """Dependency: возвращает список всех конфигураций."""
    return await ConfigRepository(async_session_maker).list_all()