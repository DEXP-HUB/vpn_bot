"""Сервисные функции: SSH и удалённые команды."""

import os
import shlex
from pathlib import Path

import paramiko
from dotenv import load_dotenv

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


class WireGuard:
    """
    Подключается к серверу по SSH, держит RemoteCommandExecutor и через него
    добавляет peer на интерфейс WireGuard и собирает текст client.conf.

    Если WireGuard крутится в Docker, укажите ``docker_container`` — команды ``wg``
    будут выполняться как ``docker exec … wg …`` на удалённом хосте.
    """

    def __init__(
        self,
        connection: SshConnection,
        *,
        docker_container: str | None = None,
    ) -> None:
        self._connection = connection
        self._docker_container = docker_container.strip() if docker_container else None
        self._client: paramiko.SSHClient | None = None
        self._executor: RemoteCommandExecutor | None = None

    @classmethod
    def from_env(cls, env_path: Path | None = None) -> "WireGuard":
        """
        Загружает .env: SSH как у :class:`SshConnection`, опционально
        ``WIREGUARD_DOCKER_CONTAINER`` — имя контейнера с интерфейсом WireGuard.
        """
        path = env_path or (_PROJECT_ROOT / ".env")
        load_dotenv(path)
        conn = SshConnection.from_env(path)
        raw = os.getenv("WIREGUARD_DOCKER_CONTAINER", "").strip()
        container = raw or None
        return cls(conn, docker_container=container)

    def _wg(self, wg_args: str) -> str:
        """Собирает команду ``wg <wg_args>`` или ``docker exec … wg <wg_args>``."""
        if self._docker_container:
            c = shlex.quote(self._docker_container)
            return f"docker exec {c} wg {wg_args}"
        return f"wg {wg_args}"

    def _wg_pubkey_command(self) -> str:
        """Команда ``wg pubkey`` с stdin; в Docker нужен ``docker exec -i``."""
        if self._docker_container:
            c = shlex.quote(self._docker_container)
            return f"docker exec -i {c} wg pubkey"
        return "wg pubkey"

    def connect(self) -> None:
        """Открывает SSH-сессию и создаёт исполнитель удалённых команд."""
        if self._client is not None:
            return
        self._client = self._connection.connect()
        self._executor = RemoteCommandExecutor(self._client)

    def close(self) -> None:
        """Закрывает SSH-клиент."""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._executor = None

    def __enter__(self) -> "WireGuard":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    @property
    def executor(self) -> RemoteCommandExecutor:
        """Возвращает исполнитель команд после connect() или входа в контекст."""
        if self._executor is None:
            raise RuntimeError("Сначала вызовите connect() или используйте with WireGuard(...).")
        return self._executor

    def generate_client_config(
        self,
        *,
        client_address: str,
        endpoint: str,
        interface: str = "wg",
        allowed_ips: str = "0.0.0.0/0, ::/0",
        persistent_keepalive: int = 25,
        dns: str | None = None,
    ) -> str:
        """
        На сервере читает публичный ключ интерфейса, генерирует ключи клиента,
        регистрирует peer (wg set) и возвращает содержимое .conf для клиента.

        ``client_address`` — адрес клиента в туннеле, например ``10.8.0.10/32``.
        ``endpoint`` — как клиенту достучаться до сервера: ``host:51820``.
        """
        ex = self.executor
        server_public_key = ex.run(self._wg(f"show {interface} public-key"))
        client_private_key = ex.run(self._wg("genkey")).strip()
        client_public_key = ex.run_with_stdin(
            self._wg_pubkey_command(),
            client_private_key + "\n",
        ).strip()

        ex.run(
            self._wg(
                f"set {interface} peer {client_public_key} allowed-ips {client_address}"
            )
        )

        lines = [
            "[Interface]",
            f"PrivateKey = {client_private_key}",
            f"Address = {client_address}",
        ]
        if dns:
            lines.append(f"DNS = {dns}")
        lines.extend(
            [
                "",
                "[Peer]",
                f"PublicKey = {server_public_key}",
                f"Endpoint = {endpoint}",
                f"AllowedIPs = {allowed_ips}",
                f"PersistentKeepalive = {persistent_keepalive}",
            ]
        )
        return "\n".join(lines) + "\n"


def ssh_run_ls() -> str:
    with WireGuard(SshConnection.from_env()) as wg:
        conf = wg.generate_client_config(
            client_address="10.8.0.10/32",
            endpoint=f"{os.getenv('SSH_HOST')}:{os.getenv('VPN_PORT')}",
        )
        print(conf)


print(ssh_run_ls())