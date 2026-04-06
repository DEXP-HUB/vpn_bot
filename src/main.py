import os

from dotenv import load_dotenv

from .bot import TelegramBot
from .wireguard.services import WireguardConfiguretor

load_dotenv()

bot = TelegramBot(token=os.getenv("TELEGRAM_BOT_TOKEN")).bot


@bot.message_handler(commands=["generate_config"])
def generate_config(message) -> None:
    """Генерирует конфигурацию для клиента WireGuard"""
    wireguard = WireguardConfiguretor.from_env()
    wireguard.create_client_keys(client_name="test")
    config_file = wireguard.create_client_config(client_name="test")
    bot.send_document(
        chat_id=message.chat.id, 
        document=config_file, 
        caption="Конфигурация успешно сгенерирована ✅",
    )
    wireguard.close()


if __name__ == "__main__":
    bot.infinity_polling()
