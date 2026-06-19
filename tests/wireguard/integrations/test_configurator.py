import pytest 

from src.wireguard.configurator import WireguardConfiguretor
from src.wireguard.dataclasses import WireGuardKeys



class TestWireguardConfiguretor:
    async def test_create_client_keys(
        self,
        config_name: str = "test_config",
    ) -> None:
        configurator = WireguardConfiguretor.from_env()
        keys = await configurator.create_client_keys()
        assert type(keys) == WireGuardKeys 
        assert type(keys.private_key) == str
        assert type(keys.public_key) == str