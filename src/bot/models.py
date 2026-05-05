from typing import TYPE_CHECKING

from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base
from ..wireguard.models import Config
    

class User(Base):
    """Модель пользователя Telegram в базе данных."""

    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    configs: Mapped[list["Config"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User id={self.user_id} telegram_id={self.telegram_id}>"
