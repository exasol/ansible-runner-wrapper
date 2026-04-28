import logging
from pathlib import Path

from exasol.ansible.access import (
    Access,
    Event,
)
from exasol.ansible.facts import Facts
from exasol.ansible.playbook import Playbook

logger = logging.getLogger(__name__)


class Runner:
    """
    Encapsulates invocation ansible access.
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

    def run(self, playbook: Playbook) -> Facts:
        event_handler = (
            self.event_handler if logger.isEnabledFor(logging.INFO) else None
        )

        return self._ansible_access.run(
            str(self._work_dir),
            playbook,
            event_logger=logger.debug,
            event_handler=event_handler,
        )
