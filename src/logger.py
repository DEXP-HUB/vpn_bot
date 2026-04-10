import logging
import os


class Logger:
    """
    Фабрика логгеров для Telegram-бота.

    Каждый уникальный `name` получает свой независимый экземпляр logging.Logger
    с общим форматом и обработчиками (файл + консоль). Повторный вызов с тем же
    именем возвращает уже существующий экземпляр без переинициализации.
    """

    # Словарь хранит по одному логгеру на каждое уникальное имя
    _instances: dict[str, logging.Logger] = {}

    @classmethod
    def get_logger(cls, name: str = "bot") -> logging.Logger:
        """
        Возвращает логгер с заданным именем.

        При первом вызове с конкретным `name` создаёт логгер, настраивает
        файловый обработчик (bot.log в корне проекта) и консольный, затем
        кэширует его.
        При повторном вызове с тем же именем возвращает кэшированный экземпляр.

        :param name: Имя логгера (отображается в строке лога). По умолчанию "bot".
        :return: Настроенный экземпляр logging.Logger.
        """
        if name in cls._instances:
            return cls._instances[name]

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Формируем путь к файлу логов в корне проекта (на уровень выше `src`).
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        log_path = os.path.join(project_root, "bot.log")
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        cls._instances[name] = logger
        return logger
