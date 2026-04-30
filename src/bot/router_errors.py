from aiogram import Bot, Router
from aiogram.types import ErrorEvent

from ..logger import Logger
from ..utils import send_alert

router = Router(name="ErrorsRouter")
logger = Logger.get_logger(router.name)


@router.errors()
async def handle_errors(event: ErrorEvent, bot: Bot) -> None:
    """Перехватывает необработанные исключения в хендлерах и уведомляет администратора."""
    logger.error("Unhandled exception in handler", exc_info=event.exception)
    await send_alert(bot, "⚠️ Ошибка в хендлере!", exception=event.exception)
