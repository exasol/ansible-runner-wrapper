import logging
from pathlib import Path
from typing import Any

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
        duration = Facts(event).get("event_data", "duration")
        if not type(duration) in (int, float):
            return False  # nothing to process

        if duration > 1.5:
            logger.info("duration: %s seconds", round(duration))

        return True

    def run(self, playbook: Playbook, retrieve_facts_from: str = "") -> dict[str, Any]:
        event_handler = (
            self.event_handler if logger.isEnabledFor(logging.INFO) else None
        )

        return self._ansible_access.run(
            str(self._work_dir),
            playbook,
            event_logger=logger.debug,
            event_handler=event_handler,
            retrieve_facts_from=retrieve_facts_from,
        )
