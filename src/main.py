import asyncio

from dotenv import load_dotenv

from .bot.dispatcher import bot, dp, logger
from .database import init_db
from .utils import send_alert

load_dotenv()


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
