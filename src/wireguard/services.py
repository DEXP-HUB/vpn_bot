import io

import dotenv

from .configurator import WireguardConfiguretor
from .server import WireguardServer
from ..bot.repository import UserRepository
from ..logger import Logger


dotenv.load_dotenv()

logger_wireguard = Logger.get_logger("wireguard")


class WireguardManager:
    """Управляет выдачей клиентского WireGuard-конфига из БД."""

    def __init__(
        self,
        server: WireguardServer | None = None,
        configurator: WireguardConfiguretor | None = None,
        user_repository: UserRepository | None = None,
    ) -> None:
        # Позволяет подменить зависимость в тестах, иначе берём SSH-настройки из env.
        self._configurator = configurator or WireguardConfiguretor.from_env()
        self._server = server or WireguardServer.from_env()
        self._user_repository = user_repository


    async def generate_client_config(self, config_name: str, telegram_id: int) -> io.BytesIO:
        """
        Возвращает клиентский .conf файл, найденный в БД по ``config_name``.
        """
        try:
            keys = await self._configurator.create_client_keys(config_name=config_name)
            allowed_ips = await self._configurator.calc_next_allowed_ip()
            server_public_key = self._configurator.server_public_key
            user_id = await self._user_repository.get_user_id_by_telegram_id(telegram_id)

            if user_id is None:
                raise ValueError(f"Пользователь с telegram_id={telegram_id} не найден в базе данных.")

            self._server.add_peer_live(
                public_key=keys.public_key,
                allowed_ips=allowed_ips,
            )

            config_file = self._configurator.build_client_config(
                private_key=keys.private_key,
                allowed_ips=allowed_ips,
                server_public_key=server_public_key,
                endpoint=self._configurator.get_endpoint,
            )

            await self._configurator.save_config_to_db(
                config_file=config_file, 
                allowed_ips=allowed_ips, 
                config_name=config_name, 
                user_id=user_id,
                public_key=keys.public_key,
            )

            await self._server.rebuild_interface_config()

            config = io.BytesIO(config_file.encode())
            config.name = f"{config_name}.conf"

            return config

        except Exception as e:
            logger_wireguard.error(f"Error generating client config for {config_name}: {e}", exc_info=True)
            raise e
            
        finally:
            # Всегда закрываем SSH-сессию после выполнения сценария.
            self._configurator.close()
            self._server.close()

