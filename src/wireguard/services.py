"""Сервисные функции WireGuard."""
import asyncio
import io
import ipaddress
import paramiko

from typing import Optional
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.database import async_session_maker
from src.utils import RemoteCommandExecutor, SshConnection
from ..bot.models import User
from ..logger import Logger
from .models import Config


logger_wireguard = Logger.get_logger("wireguard")


async def insert_test_config(user_id: int = 1) -> int:
    """Добавляет тестовый конфиг в таблицу configs и возвращает его ID."""
    test_config = Config(
        config_file=(
            "[Interface]\n"
            "PrivateKey = test_private_key\n"
            "Address = 10.0.0.2/32\n"
            "\n"
            "[Peer]\n"
            "PublicKey = test_public_key\n"
            "Endpoint = 127.0.0.1:51820\n"
            "AllowedIPs = 0.0.0.0/0\n"
            "PersistentKeepalive = 20\n"
        ),
        alowed_ips="10.0.0.2/32",
        config_name="test_config",
        user_id=user_id,
    )

    async with async_session_maker() as session:
        try:
            session.add(test_config)
            await session.commit()
            await session.refresh(test_config)
            return test_config.config_id
        except IntegrityError as error:
            await session.rollback()
            raise ValueError(
                f"Не удалось добавить тестовый конфиг для user_id={user_id}. "
                "Проверьте, что пользователь существует."
            ) from error


class WireguardConfiguretor:
    """Генерирует ключи WireGuard на удалённом сервере через SSH."""

    def __init__(
        self, 
        executor: RemoteCommandExecutor, 
    ) -> None:
        self._executor = executor

    @classmethod
    def from_env(cls, test: bool = False) -> "WireguardConfiguretor":
        """Создаёт экземпляр WireguardConfiguretor, используя параметры SSH из .env."""
        if test:
            return cls(RemoteCommandExecutor())

        else:
            connection = SshConnection.from_env()
            client = connection.connect()
            executor = RemoteCommandExecutor(client)
            # Вызывающий обязан закрыть клиент через close().
            instance = cls(executor)
            instance._client = client  # type: ignore[attr-defined]
            return instance

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
        async with async_session_maker() as session:
            rows = await session.scalars(select(Config.alowed_ips))
            allowed_ips_values = rows.all()

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
        client_name: str = "goloburdin",
        user_id: int = 1,
    ) -> None:
        """
        Создаёт приватный и публичный ключи клиента WireGuard в /etc/wireguard.

        Приватный ключ:  /etc/wireguard/<client_name>_privatekey
        Публичный ключ:  /etc/wireguard/<client_name>_publickey

        После генерации ключей добавляет пира в wg0.conf и регистрирует его
        в работающем интерфейсе через ``wg set`` без перезапуска WireGuard.
        """
        private_path = f"/etc/wireguard/{client_name}_privatekey"
        public_path = f"/etc/wireguard/{client_name}_publickey"

        command = (
            f"cd /etc/wireguard && "
            f"wg genkey | tee {private_path} | wg pubkey | tee {public_path}"
        )
        self._executor.run(command)
        public_key = self._executor.run(f"cat {public_path}").strip()
        allowed_ips = await self._calc_next_allowed_ip()
        self._append_peer_to_wg0_conf(
            client_name=client_name,
            public_key=public_key,
            allowed_ips=allowed_ips,
        )
        # Регистрируем пира в живом интерфейсе без перезагрузки WireGuard,
        # чтобы не обрывать уже активные VPN-соединения других клиентов.
        self._add_peer_live(public_key=public_key, allowed_ips=allowed_ips)
        private_key = self._executor.run(f"cat {private_path}").strip()
        server_public_key = self._executor.run("wg show wg0 public-key").strip()
        client_config_text = self._build_client_config(
            private_key=private_key,
            allowed_ips=allowed_ips,
            server_public_key=server_public_key,
        )
        await self.save_config_to_db(
            config_file=client_config_text,
            allowed_ips=allowed_ips,
            config_name=client_name,
            user_id=user_id,
        )

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
            alowed_ips=allowed_ips,
            config_name=config_name,
            user_id=user_id,
        )

        async with async_session_maker() as session:
            try:
                # Добавляем и фиксируем конфиг, чтобы запись появилась в БД.
                session.add(config)
                await session.commit()
                await session.refresh(config)
                return config
            except IntegrityError as error:
                await session.rollback()
                raise ValueError(
                    "Не удалось сохранить конфигурацию WireGuard в базу данных."
                ) from error

    @staticmethod
    def _build_client_config(
        *,
        private_key: str,
        allowed_ips: str,
        server_public_key: str,
        endpoint: str = "127.0.0.1:51820",
        dns: str = "1.1.1.1",
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

    async def get_client_config(
        self,
        client_name: str,
    ) -> io.BytesIO:
        """
        Ищет готовый конфиг в БД по ``config_name`` и возвращает его
        содержимое как объект BytesIO.
        """
        async with async_session_maker() as session:
            stmt = select(Config).where(Config.config_name == client_name)
            config = await session.scalar(stmt)

        if config is None:
            raise ValueError(f"Конфиг с config_name='{client_name}' не найден в базе данных.")

        buffer = io.BytesIO(config.config_file.encode())
        buffer.name = f"{config.config_name}.conf"
        return buffer


class WireguardManager:
    """Управляет выдачей клиентского WireGuard-конфига из БД."""

    def __init__(self, configurator: WireguardConfiguretor | None = None) -> None:
        # Позволяет подменить зависимость в тестах, иначе берём SSH-настройки из env.
        self._configurator = configurator or WireguardConfiguretor.from_env()

    async def generate_client_config(self, client_name: str, telegram_id: int) -> io.BytesIO:
        """
        Возвращает клиентский .conf файл, найденный в БД по ``config_name``.
        """
        try:
            user_id = await self._get_user_id_by_telegram_id(telegram_id)
            await self._configurator.create_client_keys(
                client_name=client_name,
                user_id=user_id,
            )
            return await self._configurator.get_client_config(client_name=client_name)

        except Exception as e:
            logger_wireguard.error(f"Error generating client config for {client_name}: {e}", exc_info=True)
            raise e
            
        finally:
            # Всегда закрываем SSH-сессию после выполнения сценария.
            self._configurator.close()

    @staticmethod
    async def _get_user_id_by_telegram_id(telegram_id: int) -> int:
        """
        Возвращает внутренний user_id по telegram_id.
        """
        async with async_session_maker() as session:
            stmt = select(User.user_id).where(User.telegram_id == telegram_id)
            user_id = await session.scalar(stmt)
        if user_id is None:
            raise ValueError(
                f"Пользователь с telegram_id={telegram_id} не найден. "
                "Сначала добавьте пользователя в базу через /add_user."
            )
        return user_id


async def main():
    wg = WireguardManager()
    config_buffer = await wg.generate_client_config(
        client_name="test_config",
        telegram_id=123456789,
    )
    text = config_buffer.read().decode()
    print(text)

if __name__ == "__main__":
    asyncio.run(main())