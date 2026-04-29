from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class User(Base):
    """Модель пользователя Telegram в базе данных."""

    __tablename__ = "users"

    # Внутренний идентификатор пользователя (первичный ключ)
    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Идентификатор пользователя в Telegram (уникальный)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)

    # Никнейм пользователя в Telegram (может быть пустым)
    user_name: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Имя пользователя в Telegram
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)

    def __repr__(self) -> str:
        return f"<User id={self.user_id} telegram_id={self.telegram_id} first_name={self.first_name!r}>"
