from dataclasses import dataclass
from pathlib import Path

INVENTORY_GROUP = "arw_inventory"


@dataclass(frozen=True)
class Host:
    name: str
    ssh_private_key: Path | None = None

    @property
    def rendered(self) -> str:
        """Renders the current Host for inventory file."""
        if key := self.ssh_private_key_file:
            return f"{self.name} ansible_ssh_private_key_file={key}"
        return self.name


def render(hosts: tuple[Host, ...]) -> str:
    header = f"[{INVENTORY_GROUP}]\n\n"
    if not hosts:
        return header
    body = "\n".join(host.rendered for host in hosts)
    return f"{header}{body}\n\n"
