import asyncio
import os

from aiogram import Dispatcher, Bot
from aiogram.types import Update
from dotenv import load_dotenv

from .command import router as command_router
from .wireguard.router_configurator import router_configurator
from .logger import Logger

load_dotenv()

logger = Logger.get_logger("aiogram")

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
dp = Dispatcher()

dp.include_routers(command_router, router_configurator)


@dp.update.outer_middleware()
async def logging_middleware(handler, event: Update, data: dict):
    user = event.event.from_user
    logger.info(f"[{user.id}] @{user.username} — {event.event_type}")
    return await handler(event, data)


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
