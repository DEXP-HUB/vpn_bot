import asyncio
import os

from aiogram import Dispatcher, Bot
from dotenv import load_dotenv

from .command import router as command_router
from .database import init_db
from .logger import Logger
from .router_errors import router as errors_router
from .utils import send_alert
from .wireguard.router_configurator import router_configurator
from .users_manage import router as users_manage_router

load_dotenv()

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
dp = Dispatcher(name="Dispatcher")
logger = Logger.get_logger(dp.name)

dp.include_routers(command_router, router_configurator, users_manage_router, errors_router)


async def main() -> None:
    try:
        # Создаём таблицы в базе данных при запуске
        await init_db()
        logger.info("Database initialized")
        logger.info("Start polling")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.warning("Stop polling", exc_info=True)
    except Exception as e:
        # Срабатывает только при падении самого polling loop (сеть, токен и т.д.)
        logger.error("Polling loop crashed", exc_info=True)
        await send_alert(bot, "🔴 Бот упал!", exception=e)



if __name__ == "__main__":
    asyncio.run(main())
