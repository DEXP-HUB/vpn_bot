import os

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from dotenv import load_dotenv

from .command import router as command_router
from .router_errors import router as errors_router
from .users_manage import router as users_manage_router

from ..logger import Logger
from ..wireguard.router_configurator import router_configurator
from ..wireguard.callback_router import callback_router


load_dotenv()

# Экземпляры бота и диспетчера, используемые во всём приложении
bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
dp = Dispatcher(name="Dispatcher")
logger = Logger.get_logger(dp.name)

dp.include_routers(
    command_router, router_configurator, users_manage_router, errors_router, callback_router,
)
