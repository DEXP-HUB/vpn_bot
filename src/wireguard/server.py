import ipaddress
import shlex
import dotenv
import os

from src.database import async_session_maker
from src.utils import RemoteCommandExecutor, SshConnection

from .repository import ConfigRepository, InterfaceRepository
from .models import Config, Interface


dotenv.load_dotenv()


class WireguardServer:
    """Управляет сервером WireGuard."""

    def __init__(
        self, 
        executor: RemoteCommandExecutor, 
        config_repository: ConfigRepository,
        interface_repository: InterfaceRepository,
    ) -> None:
        self._executor = executor
        self._config_repository = config_repository
        self._interface_repository = interface_repository

    @classmethod
    def from_env(cls, test: bool = bool(int(os.getenv("TEST")))) -> "WireguardServer":
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

    @staticmethod
    def _build_interface_config(
        *,
        interface: Interface,
        configs: list[Config],
    ) -> str:
        """Формирует серверный wg0.conf из интерфейса и клиентских пиров."""
        sorted_configs = sorted(
            configs,
            key=lambda config: ipaddress.ip_interface(config.allowed_ips).ip,
        )
        config_parts = [
            "[Interface]\n"
            f"Address = {interface.address}\n"
            f"ListenPort = {interface.listen_port}\n"
            f"PrivateKey = {interface.private_key}\n"
            f"PostUp = {interface.post_up}\n"
            f"PostDown = {interface.post_down}\n"
        ]

        for config in sorted_configs:
            config_parts.append(
                "\n"
                f"# Client: {config.config_name}\n"
                "[Peer]\n"
                f"PublicKey = {config.public_key}\n"
                f"AllowedIPs = {config.allowed_ips}\n"
            )

        return "".join(config_parts)

    def close(self) -> None:
        """Закрывает SSH-соединение, созданное в from_env()."""
        client = getattr(self, "_client", None)
        if client is not None:
            client.close()

    async def rebuild_interface_config(
        self,
        *,
        interface_name: str = "wg0",
        wg_conf_path: str = "/etc/wireguard/wg0.conf",
    ) -> None:
        """Пересобирает wg0.conf из данных БД и записывает его на сервер."""
        interface = await self._interface_repository.get_interface_by_name(interface_name)

        if interface is None:
            raise ValueError(f"Интерфейс с interface_name='{interface_name}' не найден в базе данных.")

        configs = await self._config_repository.list_all()
        wg_config = self._build_interface_config(interface=interface, configs=configs)
        command = f"cat > {shlex.quote(wg_conf_path)}"

        self._executor.run_with_stdin(command, wg_config)

    def add_peer_live(
        self,
        *,
        public_key: str,
        allowed_ips: str,
        interface: str = "wg0",
    ) -> None:
        """Добавляет нового пира в работающий интерфейс WireGuard без перезапуска.

        Использует ``wg set`` вместо reload/restart, чтобы не обрывать
        уже установленные соединения других клиентов.
        """
        self._executor.run(
            f"wg set {interface} peer {public_key} allowed-ips {allowed_ips}"
        )

    async def delete_peer_live(
        self,
        *,
        public_key: str,
        interface: str = "wg0",
    ) -> None:
        """Удаляет пира из работающего интерфейса WireGuard без перезапуска."""

        self._executor.run(
            f"wg set {interface} peer {public_key} remove"
        )

