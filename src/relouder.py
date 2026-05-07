from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from watchfiles import run_process


@dataclass(slots=True)
class Relouder:
    """Отвечает за автоперезапуск проекта при изменении файлов."""

    target: Callable[..., Any]
    project_root: str | Path | None = None
    recursive: bool = True

    def __post_init__(self) -> None:
        """Нормализует путь проекта и подготавливает его для watcher."""
        if self.project_root is None:
            # По умолчанию наблюдаем за директорией, где находится этот файл.
            self.project_root = Path(__file__).resolve().parent
        else:
            self.project_root = Path(self.project_root).resolve()

    def run(self) -> None:
        """Запускает процесс и перезапускает его при изменении кода."""
        run_process(
            str(self.project_root),
            target=self.target,
            recursive=self.recursive,
        )


def get_project_root() -> str:
    """Возвращает абсолютный путь до корня проекта."""
    return os.path.dirname(os.path.abspath(__file__))
