from telebot import TeleBot


class TelegramBot:
    """Основной класс Telegram-бота для управления VPN."""

    def __init__(self, token: str) -> None:
        """Инициализирует экземпляр бота TeleBot с переданным токеном."""
        self._bot = TeleBot(token)

    @property
    def bot(self) -> TeleBot:
        """Возвращает внутренний экземпляр TeleBot."""
        return self._bot
