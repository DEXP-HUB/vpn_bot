import asyncio
import os

from aiogram import Dispatcher, Bot
from dotenv import load_dotenv

from .command import router as command_router
from .wireguard.router_configurator import router_configurator

load_dotenv()

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
dp = Dispatcher()

dp.include_router(command_router)
dp.include_router(router_configurator)


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
