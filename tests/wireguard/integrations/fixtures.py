import pytest

from src.utils import SshConnection


@pytest.fixture
def ssh_connect():
    ssh = SshConnection.from_env()
    connect = ssh.connect()
    return connect
    