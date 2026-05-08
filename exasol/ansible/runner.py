import json
import logging
from pathlib import Path
from typing import (
    Any,
    NewType,
)

# import the real final ansible runner from
# https://pypi.org/project/ansible-runner/
# https://github.com/ansible/ansible-runner
# https://docs.ansible.com/projects/runner/en/latest/python_interface/
import ansible_runner  # type: ignore[import-untyped]

import exasol.ansible.inventory as inventory
from exasol.ansible.context import copy_files
from exasol.ansible.facts import Facts
from exasol.ansible.playbook import Playbook
from exasol.ansible.repository import Repository

logger = logging.getLogger(__name__)

Event = NewType("Event", dict[str, Any])


class AnsibleException(RuntimeError):
    pass


class Runner:
    def __init__(
        self,
        repositories: tuple[Repository, ...],
        work_dir: Path | None = None,
    ):
        self._repos = repositories
        self._path = work_dir

    def event_handler(self, event: Event) -> bool:
        duration = Facts(event).get("event_data", "duration")
        if type(duration) not in (int, float):
            return False  # nothing to process

        if duration > 1.5:
            logger.info("duration: %s seconds", round(duration))

        return True

    def run(
        self,
        playbook: Playbook,
        hosts: tuple[inventory.Host, ...] = (),
        retrieve_facts_from: str = "",
    ) -> dict[str, Any]:
        quiet = not logger.isEnabledFor(logging.INFO)
        event_handler = None if quiet else self.event_handler
        with copy_files(repositories=self._repos, work_dir=self._path) as work_dir:
            content = inventory.render(hosts)
            (work_dir / "inventory").write_text(content)
            result = ansible_runner.run(
                private_data_dir=str(work_dir),
                playbook=playbook.file,
                quiet=quiet,
                event_handler=event_handler,
                extravars=playbook.vars,
            )

            for event in result.events:
                logger.debug(json.dumps(event, indent=2))

            if result.rc != 0:
                raise AnsibleException(result.rc)

            if host := retrieve_facts_from:
                return result.get_fact_cache(host)
            else:
                return {}
