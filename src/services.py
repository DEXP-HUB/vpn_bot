"""Сервисные функции: SSH и удалённые команды."""

import os
from pathlib import Path

import paramiko  # pyright: ignore[reportMissingModuleSource]
from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]

# Корень проекта (рядом с .env)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class SshConnection:
    """Создаёт SSH-клиент Paramiko и устанавливает соединение с сервером."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        *,
        timeout: int = 30,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._timeout = timeout

    @classmethod
    def from_env(cls, env_path: Path | None = None) -> "SshConnection":
        """
        Загружает .env и собирает параметры SSH_HOST, SSH_PORT, SSH_USERNAME,
        SSH_PASSWORD для последующего connect().
        """
        path = env_path or (_PROJECT_ROOT / ".env")
        load_dotenv(path)

        host = os.getenv("SSH_HOST")
        port_raw = os.getenv("SSH_PORT", "22")
        username = os.getenv("SSH_USERNAME")
        password = os.getenv("SSH_PASSWORD")

        if not host or not username or not password:
            raise ValueError(
                "В .env должны быть заданы SSH_HOST, SSH_USERNAME и SSH_PASSWORD."
            )  

        return cls(
            host=host,
            port=int(port_raw),
            username=username,
            password=password,
        ) 

    def connect(self) -> paramiko.SSHClient:
        """Создаёт клиент, подключается к серверу; вызывающий обязан вызвать close()."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=self._host,
            port=self._port,
            username=self._username,
            password=self._password,
            timeout=self._timeout,
        )
        return client


class RemoteCommandExecutor:
    """Выполняет команды на удалённом хосте через уже подключённый SSH-клиент."""

    def __init__(self, client: paramiko.SSHClient) -> None:
        self._client = client

    def run(self, command: str) -> str:
        """
        Выполняет shell-команду на сервере, возвращает stdout (без завершающего \\n).
        При ненулевом коде выхода — RuntimeError с stderr.
        """
        _stdin, stdout, stderr = self._client.exec_command(command)
        out_bytes = stdout.read()
        err_bytes = stderr.read()
        exit_status = stdout.channel.recv_exit_status()

        output = out_bytes.decode(errors="replace").rstrip("\n")
        err_text = err_bytes.decode(errors="replace").strip()

        if exit_status != 0:
            raise RuntimeError(
                f"Команда завершилась с кодом {exit_status}. stderr: {err_text}"
            )
        return output

    def run_with_stdin(self, command: str, stdin_text: str) -> str:
        """
        Выполняет команду с данными на stdin (как у ``wg pubkey``), возвращает stdout.
        При ненулевом коде выхода — RuntimeError с stderr.
        """
        stdin, stdout, stderr = self._client.exec_command(command)
        stdin.write(stdin_text)
        stdin.channel.shutdown_write()
        out_bytes = stdout.read()
        err_bytes = stderr.read()
        exit_status = stdout.channel.recv_exit_status()

        output = out_bytes.decode(errors="replace").rstrip("\n")
        err_text = err_bytes.decode(errors="replace").strip()

        if exit_status != 0:
            raise RuntimeError(
                f"Команда завершилась с кодом {exit_status}. stderr: {err_text}"
            )
        return output


class Wireguard:
    """Генерирует ключи WireGuard на удалённом сервере через SSH."""

    def __init__(self, executor: RemoteCommandExecutor) -> None:
        self._executor = executor

    @classmethod
    def from_env(cls) -> "Wireguard":
        """Создаёт экземпляр Wireguard, используя параметры SSH из .env."""
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

    def create_client_keys(self, client_name: str = "goloburdin") -> None:
        """
        Создаёт приватный и публичный ключи клиента WireGuard в /etc/wireguard.

        Приватный ключ:  /etc/wireguard/<client_name>_privatekey
        Публичный ключ:  /etc/wireguard/<client_name>_publickey
        """
        private_path = f"/etc/wireguard/{client_name}_privatekey"
        public_path = f"/etc/wireguard/{client_name}_publickey"

        command = (
            f"cd /etc/wireguard && "
            f"wg genkey | tee {private_path} | wg pubkey | tee {public_path}"
        )
        self._executor.run(command)
        public_key = self._executor.run(f"cat {public_path}")
        self._append_peer_to_wg0_conf(client_name=client_name, public_key=public_key)
        