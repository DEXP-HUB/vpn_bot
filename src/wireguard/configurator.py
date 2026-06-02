import os
import ipaddress
import dotenv

from src.database import async_session_maker
from src.utils import RemoteCommandExecutor, SshConnection
from .repository import ConfigRepository, InterfaceRepository
from .dataclasses import WireGuardKeys
from .models import Config, Interface

dotenv.load_dotenv()


class WireguardConfiguretor:
    """Генерирует ключи WireGuard на удалённом сервере через SSH."""

    def __init__(
        self, 
        executor: RemoteCommandExecutor, 
        repository: ConfigRepository,
        interface_repository: InterfaceRepository,
    ) -> None:
        self._executor = executor
        self._config_repository = repository
        self._interface_repository = interface_repository

    @classmethod
    def from_env(cls, test: bool = bool(int(os.getenv("TEST")))) -> "WireguardConfiguretor":
        """Создаёт экземпляр WireguardConfiguretor, используя параметры SSH из .env."""
        if test:
            connection = SshConnection.from_env()
            client = connection.connect()
            executor = RemoteCommandExecutor(client)
            # Вызывающий обязан закрыть клиент через close().
            instance = cls(
                executor,
                ConfigRepository(async_session_maker),
                InterfaceRepository(async_session_maker),
            )
            instance._client = client  # type: ignore[attr-defined]
            return instance

        return cls(
            RemoteCommandExecutor(),
            ConfigRepository(async_session_maker),
            InterfaceRepository(async_session_maker),
        )

    @staticmethod
    def build_client_config(
        *,
        private_key: str,
        allowed_ips: str,
        server_public_key: str,
        endpoint: str,
        dns: str = "1.1.1.1, 1.0.0.1",
    ) -> str:
        """
        Формирует текст клиентского WireGuard-конфига для хранения в БД.
        """
        return (
            "[Interface]\n"
            f"PrivateKey = {private_key}\n"
            f"Address = {allowed_ips}\n"
            f"DNS = {dns}\n"
            "\n"
            "[Peer]\n"
            f"PublicKey = {server_public_key}\n"
            f"Endpoint = {endpoint}\n"
            "AllowedIPs = 0.0.0.0/0\n"
            "PersistentKeepalive = 20\n"
        )

    @property
    def get_endpoint(self) -> str:
        return f"{os.getenv('SSH_HOST')}:{os.getenv('VPN_PORT')}"

    @property
    def server_public_key(self) -> str:
        return self._executor.run("wg show wg0 public-key").strip()

    def close(self) -> None:
        """Закрывает SSH-соединение, созданное в from_env()."""
        client = getattr(self, "_client", None)
        if client is not None:
            client.close()
        
    async def calc_next_allowed_ip(
        self,
        *,
        base_network: str = "10.0.0.0/24",
    ) -> str:
        """
        Вычисляет следующий свободный AllowedIPs для нового клиента на основе данных в БД.
        """
        network = ipaddress.ip_network(base_network, strict=False)
        used_ips: set[ipaddress.IPv4Address] = set()

        allowed_ips_values = await self._config_repository.get_allowed_ips()

        for allowed_ip in allowed_ips_values:
            try:
                iface = ipaddress.ip_interface(allowed_ip)
                
            except ValueError:
                continue

            if iface.ip in network:
                used_ips.add(iface.ip)

        # Резервируем первый адрес сети и, при необходимости, адрес сервера.
        candidates = (ip for ip in network.hosts())
        # Пропустить первый адрес (например, 10.0.0.1 для сервера).
        next(candidates, None)

        for ip in candidates:
            if ip not in used_ips:
                return f"{ip}/32"

        raise RuntimeError("В подсети WireGuard не осталось свободных адресов AllowedIPs.")

    async def create_client_keys(
        self,
        config_name: str = "test_config",
    ) -> None:
        """
        Создаёт приватный и публичный ключи клиента WireGuard в /etc/wireguard.

        Приватный ключ:  /etc/wireguard/<client_name>_privatekey
        Публичный ключ:  /etc/wireguard/<client_name>_publickey
        """
        private_path = f"/etc/wireguard/{config_name}_privatekey"
        public_path = f"/etc/wireguard/{config_name}_publickey"

        command = (
            f"cd /etc/wireguard && "
            f"wg genkey | tee {private_path} | wg pubkey | tee {public_path}"
        )
        self._executor.run(command)

        public_key = self._executor.run(f"cat {public_path}").strip()
        private_key = self._executor.run(f"cat {private_path}").strip()

        command_delete = f"rm {public_path} {private_path}"
        self._executor.run(command_delete)
        
        return WireGuardKeys(private_key=private_key, public_key=public_key)

    async def save_config_to_db(
        self,
        *,
        config_file: str,
        allowed_ips: str,
        config_name: str,
        user_id: int,
        public_key: str,
    ) -> Config:
        """
        Сохраняет клиентский WireGuard-конфиг в таблицу ``configs``.
        """
        config = Config(
            config_file=config_file,
            allowed_ips=allowed_ips,
            config_name=config_name,
            user_id=user_id,
            public_key=public_key,
        )
        await self._config_repository.add(config)