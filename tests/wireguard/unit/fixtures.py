import ipaddress

import pytest

from unittest.mock import AsyncMock, MagicMock, Mock

from src.wireguard.models import Interface, Config
from src.wireguard.configurator import WireguardConfiguretor


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


@pytest.fixture
def mock_wireguard_configurator(request, base_network: str = "10.0.0.0/24"):
    network = ipaddress.ip_network(base_network, strict=False)
    
    all_ips = [f"{ip}/32" for ip in network.hosts()] 
    used_ips = all_ips[1:] 

    free_ips_count = request.param 

    if free_ips_count > 0:
        used_ips = used_ips[:-free_ips_count]

    mock_config_repo = AsyncMock()
    mock_config_repo.get_allowed_ips = AsyncMock(return_value=used_ips)

    mock_executor = MagicMock()
    mock_interface_repo = AsyncMock()
    
    configurator = WireguardConfiguretor(
        executor=mock_executor,
        repository=mock_config_repo,
        interface_repository=mock_interface_repo,
    )

    return configurator
