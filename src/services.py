"""Сервисные функции: SSH и удалённые команды."""

import os
from pathlib import Path

import paramiko
from dotenv import load_dotenv

# Корень проекта (рядом с .env)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def ssh_run_ls() -> str:
    """
    Подключается к серверу по SSH, используя SSH_HOST, SSH_PORT, SSH_USERNAME,
    SSH_PASSWORD из .env, выполняет команду `ls` и возвращает её стандартный вывод.
    """
    load_dotenv(_PROJECT_ROOT / ".env")

    host = os.getenv("SSH_HOST")
    port_raw = os.getenv("SSH_PORT", "22")
    username = os.getenv("SSH_USERNAME")
    password = os.getenv("SSH_PASSWORD")

    if not host or not username or not password:
        raise ValueError(
            "В .env должны быть заданы SSH_HOST, SSH_USERNAME и SSH_PASSWORD."
        )

    port = int(port_raw)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            timeout=30,
        )
        _stdin, stdout, stderr = client.exec_command("ls")
        out_bytes = stdout.read()
        err_bytes = stderr.read()
        exit_status = stdout.channel.recv_exit_status()

        output = out_bytes.decode(errors="replace").rstrip("\n")
        err_text = err_bytes.decode(errors="replace").strip()

        if exit_status != 0:
            raise RuntimeError(
                f"Команда ls завершилась с кодом {exit_status}. stderr: {err_text}"
            )
        return output
    finally:
        client.close()
