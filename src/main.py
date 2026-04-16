import asyncio
import os

from aiogram import Dispatcher, Bot
from dotenv import load_dotenv

from .command import router as command_router
from .wireguard.router_configurator import router_configurator
from .logger import Logger

load_dotenv()

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
dp = Dispatcher(name="Dispatcher")
logger = Logger.get_logger(dp.name)

dp.include_routers(command_router, router_configurator)



async def main() -> None:
    try:
        logger.info("Start polling")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.warning("Stop polling", exc_info=True)
    except Exception as e:
        logger.error("Error", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
