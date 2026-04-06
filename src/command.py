from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

WELCOME_TEXT = """
👋 Привет! Я VPN-бот на базе WireGuard.

Я помогу тебе быстро получить персональный VPN-конфиг и подключиться к защищённой сети.

🔧 Что я умею:
• /generate_config — сгенерировать конфигурационный файл WireGuard для твоего устройства

📦 Как начать:
1. Введи /generate_config
2. Получи готовый .conf файл
3. Импортируй его в приложение WireGuard на своём устройстве
4. Подключайся и пользуйся безопасным интернетом

❓ Если возникнут вопросы — обратись к администратору.
"""


@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer(WELCOME_TEXT)
