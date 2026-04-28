import logging
from pathlib import Path

from exasol.ansible.access import (
    Access,
    Event,
)
from exasol.ansible.facts import Facts
from exasol.ansible.inventory import InventoryHost
from exasol.ansible.playbook import Playbook

logger = logging.getLogger(__name__)
INVENTORY_GROUP_NAME = "test_targets"


def _inventory_line(inventory_host: InventoryHost) -> str:
    if inventory_host.ssh_private_key:
        return (
            f"{inventory_host.host_name} "
            f"ansible_ssh_private_key_file={inventory_host.ssh_private_key}"
        )
    return inventory_host.host_name


def render_inventory(hosts: tuple[InventoryHost, ...]) -> str:
    header = f"[{INVENTORY_GROUP_NAME}]\n\n"
    if not hosts:
        return header
    body = "\n".join(_inventory_line(host) for host in hosts)
    return f"{header}{body}\n\n"


class Runner:
    """
    Encapsulates invocation ansible access. It creates the inventory file,
    writing the host info, during run.
    """

    def __init__(self, ansible_access: Access, work_dir: Path):
        self._ansible_access = ansible_access
        self._work_dir = work_dir

    def event_handler(self, event: Event) -> bool:
        if "event_data" not in event:
            return False  # nothing to process

        event_data = event.get("event_data")
        if not isinstance(event_data, dict):
            return False
        duration = event_data.get("duration", 0)

        if duration > 1.5:
            logger.debug("duration: %s seconds", round(duration))

        return True

    def run(
        self,
        playbook: Playbook,
        hosts: tuple[InventoryHost, ...] = (),
    ) -> Facts:
        inventory_content = render_inventory(hosts)
        with open(self._work_dir / "inventory", "w", encoding="utf-8") as file:
            file.write(inventory_content)

        event_handler = (
            self.event_handler if logger.isEnabledFor(logging.INFO) else None
        )

        return self._ansible_access.run(
            str(self._work_dir),
            playbook,
            event_logger=logger.debug,
            event_handler=event_handler,
        )
