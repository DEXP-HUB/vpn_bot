import os

from dotenv import load_dotenv

from .bot import TelegramBot


load_dotenv()

bot = TelegramBot(token=os.getenv("TELEGRAM_BOT_TOKEN")).bot


@bot.message_handler(commands=["test"])
def handle_test_command(message) -> None:
    """Обрабатывает команду /test и отправляет тестовый ответ пользователю."""
    bot.send_message(chat_id=message.chat.id, text="Тестовая команда выполнена ✅")


if __name__ == "__main__":
    bot.infinity_polling()

