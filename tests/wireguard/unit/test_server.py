import pytest

from src.wireguard.server import WireguardServer
from src.wireguard.models import Interface

from .fixtures import sample_configs, sample_interface


class TestWireguardServer:
    def test_build_interface_config(
       self,
       sample_configs,
       sample_interface,
    ):
        interface_config = WireguardServer._build_interface_config(
            interface=sample_interface, configs=sample_configs
        )

        expected = (
            "[Interface]\n"
            f"Address = {sample_interface.address}\n"
            f"ListenPort = {sample_interface.listen_port}\n"
            f"PrivateKey = {sample_interface.private_key}\n"
            f"PostUp = {sample_interface.post_up}\n"
            f"PostDown = {sample_interface.post_down}\n"
            "\n"
            "# Client: client-beta\n"
            "[Peer]\n"
            "PublicKey = bCdEfGhIjKlMnOpQrStUvWxYz1234567890abcdefghiJ=\n"
            "AllowedIPs = 10.0.0.5/32\n"
            "\n"
            "# Client: client-alpha\n"
            "[Peer]\n"
            "PublicKey = aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890abcdefgh=\n"
            "AllowedIPs = 10.0.0.10/32\n"
            "\n"
            "# Client: client-gamma\n"
            "[Peer]\n"
            "PublicKey = cDeFgHiJkLmNoPqRsTuVwXyZ1234567890abcdefghijK=\n"
            "AllowedIPs = 10.0.0.20/32\n"
        )

        assert interface_config == expected

            


