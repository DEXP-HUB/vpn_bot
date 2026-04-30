from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class User(Base):
    """Модель пользователя Telegram в базе данных."""

    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<User id={self.user_id} telegram_id={self.telegram_id}>"
