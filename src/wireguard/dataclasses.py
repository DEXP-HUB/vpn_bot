from dataclasses import dataclass
from aiogram.types import BufferedInputFile

@dataclass
class WireGuardKeys:
    """Ключи WireGuard для клиента."""

    private_key: str
    public_key: str


@dataclass
class ClientConfigFiles:
    """Файлы клиентской конфигурации для отправки пользователю."""
    
    config: BufferedInputFile
    qr_code: BufferedInputFile
