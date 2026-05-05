from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class Config(Base):
    """Модель VPN-конфига, привязанного к пользователю."""

    __tablename__ = "configs"

    config_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    config_file: Mapped[str] = mapped_column(String, nullable=False)
    alowed_ips: Mapped[str] = mapped_column(String, nullable=False)
    config_name: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"), nullable=False, index=True
    )

    # Связь с пользователем, которому принадлежит конфиг.
    user = relationship("User", back_populates="configs")
