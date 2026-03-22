"""Сервисные функции: SSH и удалённые команды."""

import os
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


def ssh_run_ls() -> str:
    """
    Подключается к серверу по SSH (данные из .env), выполняет `ls`,
    возвращает стандартный вывод.
    """
    connection = SshConnection.from_env()
    client = connection.connect()
    try:
        executor = RemoteCommandExecutor(client)
        return executor.run("ls")
    finally:
        client.close()


print(ssh_run_ls())