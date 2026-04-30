"""Утилиты: SSH-соединение, выполнение удалённых команд и отправка алёртов."""

import os
import traceback
from pathlib import Path
from typing import Optional

import paramiko  # pyright: ignore[reportMissingModuleSource]
from aiogram import Bot
from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]

# Корень проекта (рядом с .env)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


async def send_alert(bot: Bot, text: str, exception: Optional[BaseException] = None) -> None:
    """Отправляет алёрт администратору с трейсбэком если передано исключение."""
    if exception is not None:
        tb = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        body = f"{text}\n\n<pre>{tb[-3000:]}</pre>"
    else:
        body = text
    await bot.send_message(
        chat_id=os.getenv("ADMIN_ID"),
        text=body,
        parse_mode="HTML",
    )


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
