from dataclasses import dataclass


@dataclass
class WireGuardKeys:
    private_key: str
    public_key: str