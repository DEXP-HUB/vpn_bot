from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .base import Base

# URL для подключения к базе данных SQLite (файл будет создан автоматически)
DATABASE_URL = "sqlite+aiosqlite:///./vpn_bot.db"

# Асинхронный движок SQLAlchemy
engine = create_async_engine(DATABASE_URL, echo=False)

# Фабрика асинхронных сессий
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Создаёт все таблицы в базе данных, если они ещё не существуют."""
    # Импорт моделей необходим для регистрации их метаданных в Base перед созданием таблиц
    from . import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
