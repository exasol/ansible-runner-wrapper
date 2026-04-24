import logging
from pathlib import Path

from exasol.ansible.access import (
    Access,
    Event,
)
from exasol.ansible.facts import AnsibleFacts
from exasol.ansible.inventory import InventoryHost
from exasol.ansible.playbook import Playbook
from exasol.ds.sandbox.lib.logging import (
    LogType,
    get_status_logger,
)


LOG = get_status_logger(LogType.ANSIBLE)
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


class DurationHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__()
        self.setFormatter(logging.Formatter("%(message)s"))


class Runner:
    """
    Encapsulates invocation ansible access. It creates the inventory file,
    writing the host info, during run.
    """

    def __init__(self, ansible_access: Access, work_dir: Path):
        self._ansible_access = ansible_access
        self._work_dir = work_dir
        self._duration_logger = Runner.duration_logger()

    @classmethod
    def duration_logger(cls) -> logging.Logger:
        logger = logging.getLogger(f"{__name__}:{cls.__name__}")
        for handler in logger.handlers:
            if isinstance(handler, DurationHandler):
                return logger
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        logger.addHandler(DurationHandler())
        return logger

    def event_handler(self, event: Event) -> bool:
        if "event_data" not in event:
            return False

        event_data = event.get("event_data")
        duration = event_data.get("duration", 0)

        if duration > 1.5:
            self._duration_logger.debug(f"duration: {round(duration)} seconds")

        return True

    def run(
        self,
        playbook: Playbook,
        hosts: tuple[InventoryHost, ...] = (),
    ) -> AnsibleFacts:
        inventory_content = render_inventory(hosts)
        with open(self._work_dir / "inventory", "w") as file:
            file.write(inventory_content)

        event_handler = self.event_handler if LOG.isEnabledFor(logging.INFO) else None

        return self._ansible_access.run(
            str(self._work_dir),
            playbook,
            event_logger=LOG.debug,
            event_handler=event_handler,
        )
