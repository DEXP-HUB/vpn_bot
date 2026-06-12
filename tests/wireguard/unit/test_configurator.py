import ipaddress
import pytest

from unittest.mock import AsyncMock, MagicMock

from src.wireguard.configurator import WireguardConfiguretor

from .fixtures import mock_wireguard_configurator

class TestWireguardConfigurator:
    @pytest.mark.parametrize(
        "private_key, allowed_ips, server_public_key, endpoint, dns, expected",
        [
            # Базовый случай: используются параметры по умолчанию для DNS
            (
                "kL/Zn7H4tJk8X9cVbNmA1s2dF3gH5jK6lP9oI0uY7tR=",
                "10.0.0.2/32",
                "S3rv3rPubK3y1234567890abcdefghijklmnopqrstuv==",
                "localhost:51820",
                None,  # означает, что будет использовано значение по умолчанию "1.1.1.1, 1.0.0.1"
                (
                    "[Interface]\n"
                    "PrivateKey = kL/Zn7H4tJk8X9cVbNmA1s2dF3gH5jK6lP9oI0uY7tR=\n"
                    "Address = 10.0.0.2/32\n"
                    "DNS = 1.1.1.1, 1.0.0.1\n"
                    "\n"
                    "[Peer]\n"
                    "PublicKey = S3rv3rPubK3y1234567890abcdefghijklmnopqrstuv==\n"
                    "Endpoint = localhost:51820\n"
                    "AllowedIPs = 0.0.0.0/0\n"
                    "PersistentKeepalive = 20\n"
                ),
            ),
        ],
    )
    def test_build_client_config(
        self, 
        private_key: str, 
        allowed_ips: str, 
        server_public_key: str, 
        endpoint: str, 
        dns: str | None,
        expected: str,
    ):
        # Если dns равен None, вызываем метод без явного dns (используем значение по умолчанию)
        result = WireguardConfiguretor.build_client_config(
            private_key=private_key,
            allowed_ips=allowed_ips,
            server_public_key=server_public_key,
            endpoint=endpoint,
        )

        assert result == expected

    @pytest.mark.asyncio
    @pytest.mark.parametrize("mock_wireguard_configurator, expected_exception, expected_ip", [
        (0, True, None),
        (1, False, "10.0.0.254/32"),
        (2, False, "10.0.0.253/32"),
    ], indirect=["mock_wireguard_configurator"])
    async def test_calc_next_allowed_ip(self, mock_wireguard_configurator, expected_exception, expected_ip):
        if expected_exception:
            with pytest.raises(RuntimeError, match="В подсети WireGuard не осталось свободных адресов AllowedIPs."):
                await mock_wireguard_configurator.calc_next_allowed_ip()
        else:
            assert await mock_wireguard_configurator.calc_next_allowed_ip() == expected_ip