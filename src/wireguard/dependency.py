from aiogram.types import BufferedInputFile, Message
from fast_depends import inject

from .models import Config
from .repository import ConfigRepository
from .services import WireguardManager
from ..bot.repository import UserRepository
from ..database import async_session_maker
from ..utils import build_qr_file


@inject
async def provide_client_config(message: Message) -> None:
    """Dependency: создаёт клиентский .conf файл и отправляет его вместе с QR-кодом."""
    config_repository = ConfigRepository(async_session_maker)
    config_to_db = await config_repository.get_config_by_name(message.text)

    if config_to_db is not None:
        await message.answer(text="Имя занято другим файлом. Попробуйте другое имя.")
        return None
    
    manager = WireguardManager(user_repository=UserRepository(async_session_maker))
    config_name = message.text or str(message.from_user.id)

    config_file = await manager.generate_client_config(
        config_name=config_name,
        telegram_id=message.from_user.id,
    )

    config_bytes = config_file.getvalue()
    qr_code = build_qr_file(
        config_text=config_bytes.decode("utf-8"),
        filename=f"{config_name}.png",
    )

    await message.answer_document(
        document=BufferedInputFile(config_bytes, filename=config_file.name),
        caption="Конфигурация успешно сгенерирована ✅",
    )
    await message.answer_photo(
        photo=qr_code,
        caption="QR-код успешно сгенерирован ✅",
    )
    return None

@inject
async def configs(message: Message) -> list[Config]:
    """Dependency: возвращает список всех конфигураций."""
    return await ConfigRepository(async_session_maker).list_all()