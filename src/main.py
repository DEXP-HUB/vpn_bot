import asyncio
import os

from dotenv import load_dotenv

from .bot.dispatcher import bot, dp, logger
from .bot.models import User
from .bot.repository import UserRepository
from .database import async_session_maker, init_db
from .utils import send_alert

load_dotenv()


async def main() -> None:
    try:
        # Создаём таблицы в базе данных при запуске
        await init_db()
        logger.info("Database initialized")
        user_repository = UserRepository(async_session_maker)
        admin_id = int(os.getenv("ADMIN_ID"))

        # Добавляем администратора только один раз, чтобы не нарушать unique telegram_id.
        if await user_repository.get_user_id_by_telegram_id(admin_id) is None:
            await user_repository.add(User(telegram_id=admin_id))
            logger.info("Admin user added")

        else:
            logger.info("Admin user already exists")

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
