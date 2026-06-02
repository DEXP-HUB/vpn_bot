import pytest

from unittest.mock import Mock

from src.wireguard.models import Interface, Config


@pytest.fixture
def sample_interface():
    interface = Mock()
    interface.address = "10.0.0.1/24"
    interface.listen_port = 51820
    interface.private_key = "oJkL9sDfG2hJkL3sDfG4hJkL9sDfG2hJkL3sDfG4hJk="
    interface.post_up = "iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE"
    interface.post_down = "iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE"
    return interface


@pytest.fixture
def sample_configs():
    config1 = Mock()
    config1.config_name = "client-alpha"
    config1.public_key = "aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890abcdefgh="
    config1.allowed_ips = "10.0.0.10/32"

    config2 = Mock()
    config2.config_name = "client-beta"
    config2.public_key = "bCdEfGhIjKlMnOpQrStUvWxYz1234567890abcdefghiJ="
    config2.allowed_ips = "10.0.0.5/32"

    config3 = Mock()
    config3.config_name = "client-gamma"
    config3.public_key = "cDeFgHiJkLmNoPqRsTuVwXyZ1234567890abcdefghijK="
    config3.allowed_ips = "10.0.0.20/32"

    return [config1, config2, config3]