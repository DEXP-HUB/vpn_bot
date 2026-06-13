"""Утилиты: SSH-соединение, выполнение удалённых команд и отправка алёртов."""

import html
import io
import locale
import os
import subprocess
import traceback
import shlex

import qrcode
import paramiko  # pyright: ignore[reportMissingModuleSource]

from pathlib import Path
from typing import Optional

from aiogram import Bot
from aiogram.types import BufferedInputFile
from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]


# Корень проекта (рядом с .env)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
path = (_PROJECT_ROOT / ".env")
load_dotenv(path)



def build_qr_file(config_text: str, filename: str) -> BufferedInputFile:
    """Создаёт PNG QR-код из текста WireGuard-конфига."""
    image = qrcode.make(config_text)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    return BufferedInputFile(buffer.getvalue(), filename=filename)


async def send_alert(bot: Bot, text: str, exception: Optional[BaseException] = None) -> None:
    """Отправляет алёрт администратору с трейсбэком если передано исключение."""
    if exception is not None:
        tb = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        body = f"{html.escape(text)}\n\n<pre>{html.escape(tb[-3000:])}</pre>"
        
    else:
        body = html.escape(text)

    await bot.send_message(
        chat_id=os.getenv("ADMIN_ID"),
        text=body,
        parse_mode="HTML",
    )


class SshConnection:
    """
    Создаёт SSH-клиент Paramiko и устанавливает соединение с сервером.
    Поддерживает аутентификацию по приватному ключу.
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        timeout: int = 30,
        key_filename: str | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._timeout = timeout
        self._key_filename = key_filename

    @classmethod
    def from_env(cls, env_path: Path | None = None) -> "SshConnection":
        """
        Использует SSH_HOST, SSH_PORT, SSH_USERNAME,
        SSH_PRIVATE_KEY_PATH для последующего connect().
        """

        host = os.getenv("SSH_HOST")
        port_raw = os.getenv("SSH_PORT", "22")
        username = os.getenv("SSH_USERNAME")
        key_path = os.getenv("SSH_PRIVATE_KEY_PATH")

        if not host or not username:
            raise ValueError("В .env должны быть заданы SSH_HOST и SSH_USERNAME.")
        
        if not key_path:
            raise ValueError(
                "Необходимо указать SSH_PRIVATE_KEY_PATH в .env"
            )

        return cls(
            host=host,
            port=int(port_raw),
            username=username,
            key_filename=key_path,
        )

    def connect(self) -> paramiko.SSHClient:
        """Создаёт клиент, подключается к серверу; вызывающий обязан вызвать close()."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        connect_kwargs = {
            "hostname": self._host,
            "port": self._port,
            "username": self._username,
            "timeout": self._timeout,
        }
        
        if self._key_filename:
            connect_kwargs["key_filename"] = self._key_filename

        else:
            raise RuntimeError("Нет ключа для аутентификации")
        
        client.connect(**connect_kwargs)

        return client


class RemoteCommandExecutor:
    """
    Выполняет shell-команды либо через SSH-клиент Paramiko (если передан),
    либо напрямую в локальной системе через subprocess (если client=None).
    Второй режим используется когда бот запущен на том же сервере, что и VPN.
    """

    def __init__(self, client: Optional[paramiko.SSHClient] = None) -> None:
        self._client = client

    @staticmethod
    def _decode_bytes(data: bytes) -> str:
        """
        Декодирует вывод команды с учётом разных кодировок окружения.
        Это особенно важно для Windows, где stderr часто приходит в cp866/cp1251.
        """
        candidate_encodings: list[str] = ["utf-8"]
        system_encoding = locale.getpreferredencoding(False)

        if system_encoding:
            candidate_encodings.append(system_encoding)

        candidate_encodings.extend(["cp866", "cp1251"])

        checked_encodings: set[str] = set()

        for encoding in candidate_encodings:
            normalized = encoding.lower()

            if normalized in checked_encodings:
                continue

            checked_encodings.add(normalized)

            try:
                return data.decode(encoding)

            except UnicodeDecodeError:
                continue

        return data.decode("utf-8", errors="replace")

    def run(self, command: str) -> str:
        """
        Выполняет shell-команду, возвращает stdout (без завершающего \\n).
        При ненулевом коде выхода — RuntimeError с stderr.
        """
        if self._client is None:
            # Локальное выполнение
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
            )

            output = self._decode_bytes(result.stdout).rstrip("\n")
            err_text = self._decode_bytes(result.stderr).strip()

            if result.returncode != 0:
                raise RuntimeError(
                    f"Команда завершилась с кодом {result.returncode}. stderr: {err_text}"
                )

            return output

        _stdin, stdout, stderr = self._client.exec_command(command)

        out_bytes = stdout.read()
        err_bytes = stderr.read()

        exit_status = stdout.channel.recv_exit_status()

        output = self._decode_bytes(out_bytes).rstrip("\n")
        err_text = self._decode_bytes(err_bytes).strip()

        if exit_status != 0:
            raise RuntimeError(
                f"Команда завершилась с кодом {exit_status}. stderr: {err_text}"
            )

        return output

    def run_with_stdin(self, command: list, stdin_text: str) -> str:
        """
        Выполняет команду с данными на stdin (как у ``wg pubkey``), возвращает stdout.
        Команда передаётся списком аргументов (без shell=True).
        При ненулевом коде выхода — RuntimeError с stderr.
        """
        if self._client is None:
            # Локальное выполнение
            result = subprocess.run(
                command,
                input=stdin_text.encode(),
                capture_output=True,
            )

            output = self._decode_bytes(result.stdout).rstrip("\n")
            err_text = self._decode_bytes(result.stderr).strip()

            if result.returncode != 0:
                raise RuntimeError(
                    f"Команда завершилась с кодом {result.returncode}. stderr: {err_text}"
                )

            return output


        cmd_str = ' '.join(shlex.quote(arg) for arg in command)
        stdin, stdout, stderr = self._client.exec_command(cmd_str)
        stdin.write(stdin_text)
        stdin.channel.shutdown_write()

        out_bytes = stdout.read()
        err_bytes = stderr.read()
        exit_status = stdout.channel.recv_exit_status()

        output = self._decode_bytes(out_bytes).rstrip("\n")
        err_text = self._decode_bytes(err_bytes).strip()

        if exit_status != 0:
            raise RuntimeError(
                f"Команда завершилась с кодом {exit_status}. stderr: {err_text}"
            )
        
        return output