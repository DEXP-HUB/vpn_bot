from aiogram.methods import SendDocument, SendMessage
from aiogram.types import BufferedInputFile, Message
from fast_depends import inject
from .services import WireguardManager
from .repository import ConfigRepository
from ..bot.repository import UserRepository
from ..database import async_session_maker


@inject
async def provide_client_config(message: Message) -> SendDocument | SendMessage:
    """Dependency: создаёт и возвращает клиентский .conf файл."""
    config_repository = ConfigRepository(async_session_maker)
    config_to_db = await config_repository.get_config_by_name(message.text)

    if config_to_db is not None:
        return message.answer(text="Имя занято другим файлом. Попробуйте другое имя.")
    
    manager = WireguardManager(user_repository=UserRepository(async_session_maker))
    config_name = message.text or str(message.from_user.id)

    config_file = await manager.generate_client_config(
        config_name=config_name,
        telegram_id=message.from_user.id,
    )

    return message.answer_document(
        document=BufferedInputFile(config_file.read(), filename=config_file.name),
        caption="Конфигурация успешно сгенерирована ✅",
    )
