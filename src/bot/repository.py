from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import InstrumentedAttribute

from ..database import AbstractSQLRepository
from .models import User


class UserRepository(AbstractSQLRepository[User]):
    """Репозиторий для работы с пользователями."""

    @property
    def model(self) -> type[User]:
        """Возвращает модель User."""
        return User

    @property
    def pk_column(self) -> InstrumentedAttribute[Any]:
        """Возвращает первичный ключ модели User."""
        return User.user_id

    async def get_user_id_by_telegram_id(self, telegram_id: int) -> User | None:
        """Возвращает пользователя по telegram_id."""
        async with self._session_maker() as session:
            return await session.scalar(
                select(self.pk_column).where(User.telegram_id == telegram_id)
            )

    async def get_user_name_by_name(self, name: str) -> int | None:
        """Возвращает пользователя по имени."""
        async with self._session_maker() as session:
            return await session.scalar(
                select(self.pk_column).where(User.name == name)
            )

    async def delete_user_by_name(self, name: str) -> bool:
        """Удаляет пользователя по имени."""
        async with self._session_maker() as session:
            user = await session.scalar(select(User).where(User.name == name))
            if user is None:
                return False

            await session.delete(user)
            await session.commit()
            return True