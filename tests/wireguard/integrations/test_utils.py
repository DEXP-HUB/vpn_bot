import pytest 

from paramiko import SSHClient

from src.utils import SshConnection

from tests.wireguard.integrations.fixtures import ssh_connect



class TestUtils:
    def test_ssh_connection(self, ssh_connect: SSHClient):
        transport = ssh_connect.get_transport()
        status = transport.is_active()
        assert status is True