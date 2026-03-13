import os

from dotenv import load_dotenv

from bot import TelegramBot


load_dotenv()

bot = TelegramBot(token=os.getenv("TELEGRAM_BOT_TOKEN")).bot


