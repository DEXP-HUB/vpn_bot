import asyncio

from .relouder import Relouder, get_project_root
from .main import main


def run_bot() -> None:
    """Запускает бота в отдельном процессе для корректного reload."""
    asyncio.run(main())


if __name__ == "__main__":
    # Запускаем watcher, который перезапускает бот при изменении файлов.
    Relouder(target=run_bot, project_root=get_project_root()).run()
