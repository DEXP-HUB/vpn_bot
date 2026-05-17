import asyncio
import os

from dotenv import load_dotenv

from .bot.dispatcher import bot, dp, logger
from .database import init_db
from .utils import send_alert

load_dotenv()


async def main() -> None:
    try:
        # Создаём таблицы в базе данных при запуске
        admin_id = int(os.environ["ADMIN_ID"])
        interface_data = {
            "address": os.environ["VPN_ADDRESS"],
            "listen_port": int(os.environ["VPN_PORT"]),
            "post_up": os.environ["VPN_POST_UP"],
            "post_down": os.environ["VPN_POST_DOWN"],
            "private_key": os.environ["VPN_PRIVATE_KEY"],
            "interface_name": os.environ["VPN_INTERFACE_NAME"],
        }
        await init_db(admin_id, interface_data)
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
