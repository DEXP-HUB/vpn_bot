from typing import Any

from sqlalchemy.orm import InstrumentedAttribute

from .models import Config
from ..bot.models import User
from ..database import AbstractSQLRepository, async_session_maker


class ConfigRepository(AbstractSQLRepository[Config]):
    """Репозиторий для работы с VPN-конфигами."""

    @property
    def model(self) -> type[Config]:
        """Возвращает модель Config."""
        return Config

    @property
    def pk_column(self) -> InstrumentedAttribute[Any]:
        """Возвращает первичный ключ модели Config."""
        return Config.config_id
