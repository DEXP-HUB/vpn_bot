from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select
from sqlalchemy.orm import InstrumentedAttribute

from .base import Base


# URL для подключения к базе данных SQLite (файл будет создан автоматически)
DATABASE_URL = "sqlite+aiosqlite:///./vpn_bot.db"

# Асинхронный движок SQLAlchemy
engine = create_async_engine(DATABASE_URL, echo=False)

# Фабрика асинхронных сессий
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

ModelType = TypeVar("ModelType")


async def init_db() -> None:
    """Создаёт все таблицы в базе данных, если они ещё не существуют."""

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class AbstractSQLRepository(ABC, Generic[ModelType]):
    """Базовый абстрактный репозиторий для работы с SQL-моделями."""

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]) -> None:
        # Фабрика сессий нужна, чтобы каждый метод работал в отдельной транзакции.
        self._session_maker = session_maker

    @property
    @abstractmethod
    def model(self) -> type[ModelType]:
        """ORM-модель, с которой работает конкретный репозиторий."""

    @property
    @abstractmethod
    def pk_column(self) -> InstrumentedAttribute[Any]:
        """Первичный ключ ORM-модели для универсальных запросов."""

    async def add(self, entity: ModelType) -> ModelType:
        """Сохраняет сущность в БД и возвращает обновлённый объект."""
        async with self._session_maker() as session:
            session.add(entity)
            await session.commit()
            await session.refresh(entity)
            return entity

    async def get_by_id(self, entity_id: int) -> ModelType | None:
        """Возвращает сущность по первичному ключу или None, если запись не найдена."""
        async with self._session_maker() as session:
            stmt = select(self.model).where(self.pk_column == entity_id)
            return await session.scalar(stmt)

    async def list_all(self) -> list[ModelType]:
        """Возвращает все записи модели."""
        async with self._session_maker() as session:
            stmt = select(self.model)
            rows = await session.scalars(stmt)
            return list(rows.all())

    async def update_by_id(self, entity_id: int, **values: Any) -> ModelType | None:
        """Обновляет запись по id и возвращает обновлённую сущность."""
        async with self._session_maker() as session:
            stmt = select(self.model).where(self.pk_column == entity_id)
            entity = await session.scalar(stmt)

            if entity is None:
                return None

            # Обновляем только существующие поля модели, игнорируя лишние ключи.
            for field_name, field_value in values.items():
                if hasattr(entity, field_name):
                    setattr(entity, field_name, field_value)

            await session.commit()
            await session.refresh(entity)
            
            return entity

    async def delete_by_id(self, entity_id: int) -> bool:
        """Удаляет запись по id и возвращает True, если удаление выполнено."""
        async with self._session_maker() as session:
            stmt = select(self.model).where(self.pk_column == entity_id)
            entity = await session.scalar(stmt)
            if entity is None:
                return False

            await session.delete(entity)
            await session.commit()
            return True
