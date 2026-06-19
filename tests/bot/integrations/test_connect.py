import pytest
import os
import dotenv

from aiogram import Bot
from aiogram.client.session import aiohttp


dotenv.load_dotenv()


@pytest.mark.asyncio
async def test_bot_connection():
    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    
    try:
        me = await bot.get_me()
        assert me is not None
        assert me.username is not None
        print(f"✅ Бот @{me.username} успешно подключён к API")
    except Exception as e:
        pytest.fail(f"❌ Не удалось подключиться к API: {e}")
    finally:
        await bot.session.close()