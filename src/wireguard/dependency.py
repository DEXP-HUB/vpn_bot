from aiogram.types import BufferedInputFile, Message
from fast_depends import inject

from .dataclasses import ClientConfigFiles
from .repository import ConfigRepository
from .services import WireguardManager
from .server import WireguardServer

from ..bot.repository import UserRepository
from ..bot.inline_keyboard import generate_inline_keyboard
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

    async def provide_client_config(self, message: Message) -> ClientConfigFiles | None:
        """Dependency: создаёт .conf файл и QR-код для клиента WireGuard."""
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
        config = BufferedInputFile(config_bytes, filename=config_file.name)
        qr_code = build_qr_file(
            config_text=config_bytes.decode("utf-8"),
            filename=f"{message.text}.png",
        )

        return ClientConfigFiles(config=config, qr_code=qr_code)


@inject
async def keyboard_configs() -> str:
    """Dependency: возвращает список всех конфигураций."""
    list_configs = await ConfigRepository(async_session_maker).list_all()
    return generate_inline_keyboard([(config.config_name, config.config_name) for config in list_configs])


@inject
async def delete_config(message: Message) -> str:
    """Dependency: удаляет конфигурацию из БД."""
    manager = WireguardManager(config_repository=ConfigRepository(async_session_maker))
    return await manager.remove_client_config(config_name=message.text)

