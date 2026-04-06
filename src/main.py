import asyncio
import os

from aiogram import Dispatcher, Bot
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message
from dotenv import load_dotenv

from .wireguard.services import WireguardConfiguretor
from .bot.bot import bot

load_dotenv()

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
dp = Dispatcher()


@dp.message(Command("generate_config"))
async def generate_config(message: Message) -> None:
    """Генерирует конфигурацию для клиента WireGuard"""
    wireguard = WireguardConfiguretor.from_env()
    wireguard.create_client_keys(client_name="test")
    config_file = wireguard.create_client_config(client_name="test")
    wireguard.close()
    await message.answer_document(
        document=BufferedInputFile(config_file.read(), filename=config_file.name),
        caption="Конфигурация успешно сгенерирована ✅",
    )


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
