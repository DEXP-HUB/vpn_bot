import logging
import os


class Logger:
    """
    Фабрика логгеров для Telegram-бота.

    Реализует паттерн Singleton: логгер создаётся один раз и переиспользуется
    при последующих вызовах get_logger(). Логи уровней INFO, WARNING и ERROR
    записываются в файл src/bot.log и дублируются в консоль.
    """

    _instance: logging.Logger | None = None

    @classmethod
    def get_logger(cls, name: str = None) -> logging.Logger:
        """
        Возвращает единственный экземпляр логгера.

        При первом вызове создаёт логгер с именем `name`, настраивает два
        обработчика — файловый (src/bot.log) и консольный — и сохраняет его
        в атрибуте класса. При повторных вызовах возвращает уже созданный
        экземпляр без переинициализации.

        :param name: Имя логгера (отображается в строке лога). По умолчанию None.
        :return: Настроенный экземпляр logging.Logger.
        """
        if cls._instance is not None:
            return cls._instance

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        log_path = os.path.join(os.path.dirname(__file__), "bot.log")
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        cls._instance = logger
        return logger
