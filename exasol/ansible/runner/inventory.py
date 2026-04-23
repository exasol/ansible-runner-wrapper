from dataclasses import dataclass


@dataclass(frozen=True)
class InventoryHost:
    host_name: str
    ssh_private_key: str | None = None
