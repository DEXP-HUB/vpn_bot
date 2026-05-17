from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class Interface(Base):
    """Модель интерфейса WireGuard."""

    __tablename__ = "interfaces"

    interface_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    address: Mapped[str] = mapped_column(String, nullable=False)
    listen_port: Mapped[int] = mapped_column(nullable=False)
    post_up: Mapped[str] = mapped_column(String, nullable=False)
    post_down: Mapped[str] = mapped_column(String, nullable=False)
    private_key: Mapped[str] = mapped_column(String, nullable=False)
    interface_name: Mapped[str] = mapped_column(String, nullable=False)


class Config(Base):
    """Модель VPN-конфига, привязанного к пользователю."""

    __tablename__ = "configs"

    config_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )
    config_file: Mapped[str] = mapped_column(String, nullable=False)
    allowed_ips: Mapped[str] = mapped_column(String, nullable=False)
    config_name: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"), nullable=False, index=True
    )

    # Связь с пользователем, которому принадлежит конфиг.
    user = relationship("User", back_populates="configs")
