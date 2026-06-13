from os import getenv

from dotenv import load_dotenv
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from .middlewares import LoggingMessageMiddleware, AdminMessageMiddleware
from .repository import UserRepository
from ..database import async_session_maker

load_dotenv()

router = Router(name="CommandRouter")

# Мидлвер логирует все входящие сообщения, обрабатываемые этим роутером
router.message.middleware(LoggingMessageMiddleware(router.name))
router.message.middleware(AdminMessageMiddleware(
    user_repository=UserRepository(async_session_maker)
    )
)


WELCOME_TEXT = """
👋 Привет! Я VPN-бот на базе WireGuard.

Я помогу тебе быстро получить персональный VPN-конфиг и подключиться к защищённой сети.

🔧 Что я умею:
• /generate_config — сгенерировать конфигурационный файл WireGuard для твоего устройства

📦 Как начать:
1. Введи /generate_config
2. Получи готовый .conf файл
3. Импортируй его в приложение WireGuard на своём устройстве

📥 Скачать WireGuard:
• Windows: https://download.wireguard.com/windows-client/wireguard-installer.exe
• macOS: https://apps.apple.com/app/wireguard/id1451685025
• Android: https://play.google.com/store/apps/details?id=com.wireguard.android
• iOS: https://apps.apple.com/app/wireguard/id1441195209
"""


HELP_TEXT = """
• /start Начать работу с ботом,
• /generate_config Сгенерировать конфигурационный файл WireGuard для твоего устройства,
• /configs_list Показать список всех конфигураций,
• /add_user_by_id Добавить пользователя по telegram_id,
• /delete_user_id Удалить пользователя по telegram_id,
• /delete_user_name Удалить пользователя по имени,
• /users Показать список всех пользователей,
"""


@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer(WELCOME_TEXT)


@router.message(Command("help"))
async def help(message: Message) -> None:
    await message.answer(HELP_TEXT)