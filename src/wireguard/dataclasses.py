from dataclasses import dataclass

from aiogram.types import BufferedInputFile, InlineKeyboardMarkup

@dataclass
class WireGuardKeys:
    """Ключи WireGuard для клиента."""

    private_key: str
    public_key: str


@dataclass
class ClientConfigFiles:
    """Файлы клиентской конфигурации для отправки пользователю."""
    
    config: BufferedInputFile = None
    qr_code: BufferedInputFile = None
    inline_keyboard: InlineKeyboardMarkup = None
