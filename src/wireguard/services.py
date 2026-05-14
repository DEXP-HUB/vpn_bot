import io
import ipaddress
import os
import asyncio
import dotenv

from typing import Optional
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.database import async_session_maker
from src.utils import RemoteCommandExecutor, SshConnection
from .dataclasses import WireGuardKeys
from .models import Config
from .repository import ConfigRepository
from ..bot.models import User
from ..bot.repository import UserRepository
from ..logger import Logger



dotenv.load_dotenv()

logger_wireguard = Logger.get_logger("wireguard")


class WireguardConfiguretor:
    """Генерирует ключи WireGuard на удалённом сервере через SSH."""

    def __init__(
        self, 
        executor: RemoteCommandExecutor, 
        repository: ConfigRepository,
    ) -> None:
        self._executor = executor
        self._repository = repository

    @classmethod
    def from_env(cls, test: bool = True) -> "WireguardConfiguretor":
        """Создаёт экземпляр WireguardConfiguretor, используя параметры SSH из .env."""
        if test:
            connection = SshConnection.from_env()
            client = connection.connect()
            executor = RemoteCommandExecutor(client)
            # Вызывающий обязан закрыть клиент через close().
            instance = cls(executor, ConfigRepository(async_session_maker))
            instance._client = client  # type: ignore[attr-defined]
            return instance

        return cls(RemoteCommandExecutor(), ConfigRepository(async_session_maker))

    @staticmethod
    def _build_client_config(
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
            
    def _append_peer_to_wg0_conf(
        self,
        *,
        client_name: str,
        public_key: str,
        allowed_ips: str = "10.0.0.2/32",
        wg_conf_path: str = "/etc/wireguard/wg0.conf",
    ) -> None:
        """Добавляет секцию Peer в конец wg0.conf."""
        # Важно: heredoc должен содержать реальные переводы строк,
        # иначе "EOF" и отступы могут попасть в файл.
        peer_block = (
            "\n"
            f"# Client: {client_name}\n"
            "[Peer]\n"
            f"PublicKey = {public_key}\n"
            f"AllowedIPs = {allowed_ips}\n"
        )

        command = (
            "bash -lc '"
            f"cat >> \"{wg_conf_path}\" <<\"EOF\"\n"
            f"{peer_block}"
            "EOF\n"
            "'"
        )
        self._executor.run(command)
        
    async def _calc_next_allowed_ip(
        self,
        *,
        base_network: str = "10.0.0.0/24",
    ) -> str:
        """
        Вычисляет следующий свободный AllowedIPs для нового клиента на основе данных в БД.
        """
        network = ipaddress.ip_network(base_network, strict=False)
        used_ips: set[ipaddress.IPv4Address] = set()

        allowed_ips_values = await self._repository.get_allowed_ips()

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
        # self._append_peer_to_wg0_conf(
        #     client_name=client_name,
        #     public_key=public_key,
        #     allowed_ips=allowed_ips,
        # )
        # Регистрируем пира в живом интерфейсе без перезагрузки WireGuard,
        # чтобы не обрывать уже активные VPN-соединения других клиентов.
        # self._add_peer_live(public_key=public_key, allowed_ips=allowed_ips)
        return WireGuardKeys(private_key=private_key, public_key=public_key)

    def _add_peer_live(
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

    async def save_config_to_db(
        self,
        *,
        config_file: str,
        allowed_ips: str,
        config_name: str,
        user_id: int,
    ) -> Config:
        """
        Сохраняет клиентский WireGuard-конфиг в таблицу ``configs``.
        """
        config = Config(
            config_file=config_file,
            allowed_ips=allowed_ips,
            config_name=config_name,
            user_id=user_id,
        )
        await self._repository.add(config)

    async def get_client_config(
        self,
        client_name: str,
    ) -> io.BytesIO:
        """
        Ищет готовый конфиг в БД по ``config_name`` и возвращает его
        содержимое как объект BytesIO.
        """
        config = await self._repository.get_config_by_name(client_name)

        if config is None:
            raise ValueError(f"Конфиг с config_name='{client_name}' не найден в базе данных.")

        buffer = io.BytesIO(config.config_file.encode())
        buffer.name = f"{config.config_name}.conf"
        return buffer


class WireguardManager:
    """Управляет выдачей клиентского WireGuard-конфига из БД."""

    def __init__(
        self, 
        configurator: WireguardConfiguretor | None = None,
        user_repository: UserRepository | None = None,
    ) -> None:
        # Позволяет подменить зависимость в тестах, иначе берём SSH-настройки из env.
        self._configurator = configurator or WireguardConfiguretor.from_env()
        self._user_repository = user_repository


    async def generate_client_config(self, config_name: str, telegram_id: int) -> io.BytesIO:
        """
        Возвращает клиентский .conf файл, найденный в БД по ``config_name``.
        """
        try:
            keys = await self._configurator.create_client_keys(config_name=config_name)
            allowed_ips = await self._configurator._calc_next_allowed_ip()
            server_public_key = self._configurator.server_public_key
            user_id = await self._user_repository.get_user_id_by_telegram_id(telegram_id)

            if user_id is None:
                raise ValueError(f"Пользователь с telegram_id={telegram_id} не найден в базе данных.")

            self._configurator._append_peer_to_wg0_conf(
                client_name=config_name,
                public_key=keys.public_key,
                allowed_ips=allowed_ips,
            )

            self._configurator._add_peer_live(public_key=keys.public_key, allowed_ips=allowed_ips)

            config_file = self._configurator._build_client_config(
                private_key=keys.private_key,
                allowed_ips=allowed_ips,
                server_public_key=server_public_key,
                endpoint=self._configurator.get_endpoint,
            )

            await self._configurator.save_config_to_db(
                config_file=config_file, 
                allowed_ips=allowed_ips, 
                config_name=config_name, 
                user_id=user_id
            )

            config = io.BytesIO(config_file.encode())
            config.name = f"{config_name}.conf"
            
            return config

        except Exception as e:
            logger_wireguard.error(f"Error generating client config for {config_name}: {e}", exc_info=True)
            raise e
            
        finally:
            # Всегда закрываем SSH-сессию после выполнения сценария.
            self._configurator.close()


# async def main():
#     wg = WireguardManager.from_env(test=True)
#     config_file = await wg.generate_client_config(config_name="test_config", telegram_id=1234567890)
#     print(config_file)

# asyncio.run(main())