from typing import Any

from sqlalchemy import select
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

    async def get_allowed_ips(self) -> list[str]:
        """Возвращает все AllowedIPs, сохранённые в базе данных."""
        async with self._session_maker() as session:
            rows = await session.scalars(select(Config.allowed_ips))
            return list(rows.all())

    async def get_config_by_name(self, config_name: str) -> Config | None:
        """Возвращает конфиг по config_name."""
        async with self._session_maker() as session:
            return await session.scalar(
                select(Config).where(Config.config_name == config_name)
            )
